"""quantum.recon.wsdiscovery — ONVIF WS-Discovery probe + device info."""
from __future__ import annotations

import re
import socket
import time
import uuid

from quantum.core.deps import requests
from quantum.core.logging import log


def wsdiscovery_cameras(timeout=5.0):
    import uuid
    probe = (
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" '
        'xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
        '<s:Header>'
        '<a:MessageID>urn:uuid:' + str(uuid.uuid4()) + '</a:MessageID>'
        '<a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>'
        '<a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>'
        '</s:Header>'
        '<s:Body><d:Probe>'
        '<d:Types>dn:NetworkVideoTransmitter tds:Device</d:Types>'
        '<d:Scopes/>'
        '</d:Probe></s:Body></s:Envelope>'
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError:
        pass
    try:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    except OSError:
        pass
    s.settimeout(0.5)
    try:
        s.bind(("", 0))
    except OSError:
        pass
    try:
        s.sendto(probe.encode(), ("239.255.255.250", 3702))
    except OSError as e:
        log(f"WS-Discovery send failed: {e}", "CAM")
        s.close()
        return []
    found, end = {}, time.time() + timeout
    while time.time() < end:
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            txt = data.decode("utf-8", "ignore")
        except Exception:
            continue
        if "ProbeMatch" not in txt and "Types" not in txt:
            continue
        ip, port = None, 80
        xaddr = re.search(r':XAddrs>\s*([^<\s]+)', txt)
        if xaddr:
            try:
                from urllib.parse import urlparse
                u = urlparse(xaddr.group(1))
                if u.hostname:
                    ip, port = u.hostname, u.port or 80
            except Exception:
                pass
        if ip is None:
            ip = addr[0]          # device answered without XAddrs — sender IP is it
        ip = str(ip)
        rec = found.setdefault(ip, {"ip": ip, "onvif_port": port,
                                    "manufacturer": None, "model": None,
                                    "name": None, "ws": True})
        for attr, pat in (("manufacturer", r'onvif\.org/hardware/([^"\'<\s]+)'),
                          ("model",       r'onvif\.org/model/([^"\'<\s]+)'),
                          ("name",        r'onvif\.org/name/([^"\'<\s]+)')):
            m = re.search(pat, txt)
            if m and not rec.get(attr):
                rec[attr] = m.group(1)
        if re.search(r'onvif\.org/Profile/(Streaming|S|T|G)', txt):
            rec["onvif"] = True
    s.close()
    if found:
        log(f"WS-Discovery: {len(found)} ONVIF devices answered", "CAM")
    return list(found.values())


def onvif_device_info(ip, port=80):
    body = ('<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
            '<s:Body><GetDeviceInformation '
            'xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
            '</s:Body></s:Envelope>')
    try:
        r = requests.post(f"http://{ip}:{port}/onvif/device_service", data=body,
                          headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                          timeout=5)
        out = {}
        for k in ("Manufacturer", "Model", "FirmwareVersion", "SerialNumber"):
            m = re.search(k + r">([^<]+)", r.text)
            if m: out[k.lower()] = m.group(1)
        return out if out else None
    except Exception:
        return None
