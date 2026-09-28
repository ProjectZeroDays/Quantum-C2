"""quantum.camwar.vendors — camera vendor identification."""
from __future__ import annotations


CAM_VENDORS = {
    "hikvision": ["hikvision", "webcomponents", "doc/page/login", "www-uc",
                  "embedded_net_dvr", "netdvr", "hik-"],
    "dahua": ["dahua", "login_module.js", "netkeyboard", "dvrdvs", "dss"],
    "axis": ["axis", "axis-cgi"],
    "foscam": ["foscam", "cgi-bin/hi3510", "get_params.cgi", "ipcam"],
    "tplink": ["tapo", "tplink"],
    "generic": ["ipcamera", "netcam", "webcam", "rtsp"],
}


def vendor_from_str(s):
    """Camera vendor best-effort from any banner string."""
    low = (s or "").lower()
    if "hik" in low or "embedded_net_dvr" in low or "netdvr" in low:
        return "hikvision"
    if "dahua" in low or "dvrdvs" in low or "dss" in low:
        return "dahua"
    if "axis" in low:
        return "axis"
    if "foscam" in low:
        return "foscam"
    if "tapo" in low or "tplink" in low:
        return "tplink"
    if "vivotek" in low:
        return "vivotek"
    return "unknown"
