"""quantum.camwar.rtsp — RTSP probing + response-head parsing."""
from __future__ import annotations

import socket


def parse_rtsp_header(data):
    """RTSP response head: {'status': int|None, 'headers': {...}}."""
    if isinstance(data, bytes):
        data = data.decode("latin-1", "ignore")
    lines = (data or "").replace("\r\n", "\n").split("\n")
    out = {"status": None, "headers": {}}
    if lines and lines[0].upper().startswith("RTSP/"):
        bits = lines[0].split(" ", 2)
        if len(bits) > 1 and bits[1].isdigit():
            out["status"] = int(bits[1])
    for ln in lines[1:]:
        if ":" in ln:
            k, _, v = ln.partition(":")
            out["headers"][k.strip().lower()] = v.strip()
    return out


def rtsp_probe(ip, port=554, timeout=3, user_agent="QCLI"):
    """OPTIONS probe against an RTSP endpoint -> raw response text."""
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.sendall(f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n"
                  f"User-Agent: {user_agent}\r\n\r\n".encode())
        data = s.recv(512)
        s.close()
        return data.decode("latin-1", "ignore")
    except Exception:
        return ""


def rtsp_alive(ip, port=554, timeout=3):
    return "RTSP" in rtsp_probe(ip, port, timeout)
