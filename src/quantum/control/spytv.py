"""quantum.control.spytv — SpyTV TV-exploitation console integration.

Drives a real SpyTV C2 (ThreadingHTTPServer API, default 127.0.0.1:8443
— configurable, since QUANTUMDASH itself defaults to :8443) through its
documented endpoints, and backs the TV Exploitation dashboard page:
one widget per SpyTV capability, each with its own settings.

When no SpyTV C2 is reachable every action returns an honest
{"error": ... + "c2": url} — the catalog, configs and layout still
work offline. Nothing is simulated.

Authorized engagements only: scan/exploit/patch actions hit real TVs;
the C2's own audit/authorization flow governs them.
"""
from __future__ import annotations

import json
import os
import time

from quantum.core.env import LOG_DIR

DEFAULT_C2 = {"host": "127.0.0.1", "port": 8443}

#: Widget catalog — one webcard per SpyTV capability. `endpoint` is the
#: SpyTV C2 path the widget reads; `config_keys` are the per-widget
#: settings editable through the gear icon.
SPYTV_WIDGETS = [
    {"id": "devices", "title": "Devices",
     "endpoint": "/api/devices", "method": "GET",
     "description": "Implant device grid + latest clips "
                    "(tvreaper.js register/poll).",
     "config_keys": ["refresh_s", "max_cards"]},
    {"id": "scan", "title": "Network Scan",
     "endpoint": "/api/scan", "method": "POST",
     "description": "CIDR scan (c2_ops.perform_scan) + check/exploit/"
                    "patch on targets.",
     "config_keys": ["cidr", "timeout_s"]},
    {"id": "payload", "title": "Payload Generator",
     "endpoint": "/api/payload", "method": "POST",
     "description": "Per-family payloads (tizen/webos/adb-net/roku/"
                    "vizio/chromecast/hisense/tcl/dlna).",
     "config_keys": ["family", "target_ip", "c2_ip"]},
    {"id": "cves", "title": "CVE Monitor",
     "endpoint": "/api/cves", "method": "GET",
     "description": "Known TV CVEs + NVD feed + whitepapers/artifacts.",
     "config_keys": ["severity", "limit"]},
    {"id": "exploits", "title": "Exploits",
     "endpoint": "/api/exploits", "method": "GET",
     "description": "Exploit catalog with CVE/type/severity/success "
                    "rate + live run.",
     "config_keys": ["family", "cve_id"]},
    {"id": "clips", "title": "Clips / Exfil",
     "endpoint": "/api/clips", "method": "GET",
     "description": "Exfiltrated audio/video clips (c2_data/clips).",
     "config_keys": ["kind", "limit"]},
    {"id": "fingerprint", "title": "Fingerprint",
     "endpoint": "/api/check", "method": "POST",
     "description": "SSDP+probe+OUI family/entry classification "
                    "(tizen/webos/roku/hisense/nettv/adb/vizio/cast).",
     "config_keys": ["target_ip", "deep"]},
    {"id": "audit", "title": "Audit & Patch",
     "endpoint": "/api/audit/status", "method": "GET",
     "description": "E-signed authorization engagements + patch-all "
                    "runs with PDF reports.",
     "config_keys": ["engagement", "auth_id"]},
    {"id": "server", "title": "Server Info",
     "endpoint": "/api/host_info", "method": "GET",
     "description": "C2 host info, gateway/subnet, uptime, "
                    "kill-connections.",
     "config_keys": ["refresh_s"]},
    {"id": "config", "title": "C2 Connection",
     "endpoint": "/api/providers", "method": "GET",
     "description": "Which SpyTV C2 this dashboard drives + AI "
                    "provider key status.",
     "config_keys": ["host", "port"]},
]


def _path(name):
    return os.path.join(LOG_DIR, name)


def get_c2_config():
    """SpyTV C2 connection {host, port} (persisted, defaults)."""
    cfg = dict(DEFAULT_C2)
    try:
        with open(_path("tv_config.json"), encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            cfg.update({k: loaded[k] for k in ("host", "port")
                        if k in loaded})
    except (OSError, ValueError):
        pass
    return cfg


def save_c2_config(host=None, port=None):
    """Persist the SpyTV C2 connection (validated)."""
    cfg = get_c2_config()
    if host:
        cfg["host"] = str(host)
    if port:
        cfg["port"] = int(port)
    if not 1 <= cfg["port"] <= 65535:
        return {"error": f"bad port {port!r}"}
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(_path("tv_config.json"), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    return cfg


def c2_base(cfg=None):
    """Base URL of the SpyTV C2."""
    cfg = cfg or get_c2_config()
    return f"http://{cfg['host']}:{int(cfg['port'])}"


def c2_get(path, timeout=15, cfg=None):
    """Real GET against the SpyTV C2 (honest error when unreachable)."""
    from quantum.core.deps import requests
    url = c2_base(cfg) + path
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return {"error": f"spytv C2 HTTP {r.status_code}",
                    "c2": url}
        try:
            return {"data": r.json(), "c2": url}
        except ValueError:
            return {"data": r.text[:4000], "c2": url}
    except Exception as exc:  # noqa: BLE001 — honest error
        return {"error": f"spytv C2 unreachable: {exc}", "c2": url}


def c2_post(path, body=None, timeout=60, cfg=None):
    """Real POST against the SpyTV C2 (honest error when unreachable)."""
    from quantum.core.deps import requests
    url = c2_base(cfg) + path
    try:
        r = requests.post(url, json=body or {}, timeout=timeout)
        if r.status_code != 200:
            return {"error": f"spytv C2 HTTP {r.status_code}",
                    "c2": url}
        try:
            return {"data": r.json(), "c2": url}
        except ValueError:
            return {"data": r.text[:4000], "c2": url}
    except Exception as exc:  # noqa: BLE001 — honest error
        return {"error": f"spytv C2 unreachable: {exc}", "c2": url}


def widget_catalog():
    """The 10 TV widgets (static catalog)."""
    return [dict(w) for w in SPYTV_WIDGETS]


def get_widget_settings():
    """Per-widget settings + layout order (persisted)."""
    try:
        with open(_path("tv_widgets.json"), encoding="utf-8") as fh:
            saved = json.load(fh)
        if isinstance(saved, dict):
            return saved
    except (OSError, ValueError):
        pass
    return {"order": [w["id"] for w in SPYTV_WIDGETS], "settings": {}}


def save_widget_settings(order=None, settings=None):
    """Persist widget layout order + per-widget settings (validated)."""
    ids = [w["id"] for w in SPYTV_WIDGETS]
    current = get_widget_settings()
    if order is not None:
        clean = [i for i in order if i in ids]
        clean += [i for i in ids if i not in clean]
        current["order"] = clean
    if settings is not None:
        if not isinstance(settings, dict):
            return {"error": "settings must be an object"}
        merged = current.get("settings", {})
        for wid, vals in settings.items():
            if wid in ids and isinstance(vals, dict):
                merged[wid] = vals
        current["settings"] = merged
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(_path("tv_widgets.json"), "w", encoding="utf-8") as fh:
        json.dump(current, fh, indent=2)
    return current


def spytv_dashboard_state():
    """Webcard state for the TV Exploitation dashboard page."""
    cfg = get_c2_config()
    widgets = widget_catalog()
    saved = get_widget_settings()
    order = saved.get("order", [w["id"] for w in widgets])
    by_id = {w["id"]: w for w in widgets}
    ordered = [by_id[i] for i in order if i in by_id]
    return {
        "c2": {"host": cfg["host"], "port": cfg["port"],
               "base": c2_base(cfg)},
        "widgets": ordered,
        "settings": saved.get("settings", {}),
        "families": ["tizen", "webos", "adb-net", "roku", "vizio",
                     "chromecast", "hisense", "tcl", "dlna"],
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime()),
        "note": "Widgets read the SpyTV C2 live; without one they "
                "report unreachable instead of fabricating. Gear icon "
                "per widget edits its settings.",
    }
