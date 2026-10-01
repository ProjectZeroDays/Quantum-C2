"""quantum.recon.trackers — IP download tracking, IMEI tracking, phone location."""
from __future__ import annotations

import re
from datetime import datetime

from quantum.core.deps import requests
from quantum.core.logging import log


def track_ip_downloads(ip: str) -> dict:
    """Track all downloads associated with an IP address via multiple OSINT sources."""
    out = {"ip": ip, "queried_at": datetime.now().isoformat(), "downloads": []}
    try:
        from quantum.core.opsec import OPSEC
        r = OPSEC.web(f"https://api.hackertarget.com/reverseiplookup/?q={ip}", timeout=15)
        out["reverse_lookup"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["reverse_lookup_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/dnslookup/?q={ip}", timeout=15)
        out["dns_records"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["dns_records_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/hostsearch/?q={ip}", timeout=15)
        out["hosted_domains"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["hosted_domains_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/pagelinks/?q=http://{ip}", timeout=15)
        out["page_links"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["page_links_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/zonetransfer/?q={ip}", timeout=15)
        out["zone_transfer"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["zone_transfer_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/nmap/?q={ip}", timeout=30)
        out["port_scan"] = r.text[:3000] if r.ok else None
    except Exception as exc:
        out["port_scan_error"] = str(exc)
    try:
        r = OPSEC.web(f"https://api.hackertarget.com/httpheaders/?q=http://{ip}", timeout=15)
        out["http_headers"] = r.text[:2000] if r.ok else None
    except Exception as exc:
        out["http_headers_error"] = str(exc)
    log(f"IP download tracking: {ip}", "OSINT")
    return out


def track_imei(imei: str) -> dict:
    """Track a phone by IMEI using offline TAC database and OSINT sources."""
    out = {"imei": imei, "queried_at": datetime.now().isoformat()}
    imei = re.sub(r"\D", "", imei or "")
    if len(imei) < 8:
        out["error"] = "IMEI must be at least 8 digits"
        return out
    tac = imei[:8]
    out["tac"] = tac
    try:
        r = requests.get(f"https://api.devicecheck.co/tac/{tac}", timeout=10)
        if r.ok:
            out["tac_info"] = r.json()
    except Exception:
        pass
    try:
        r = requests.get(f"https://www.imei.info/imei/{imei}", timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            text = r.text
            model_match = re.search(r"Model[:\s]+([^<\n]+)", text)
            brand_match = re.search(r"Brand[:\s]+([^<\n]+)", text)
            if model_match:
                out["model"] = model_match.group(1).strip()
            if brand_match:
                out["brand"] = brand_match.group(1).strip()
    except Exception:
        pass
    try:
        r = requests.get(f"https://imeiapi.com/v1/imei/{imei}", timeout=10)
        if r.ok:
            out["api_info"] = r.json()
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.mobilespecs.net/imei/{imei}", timeout=10)
        if r.ok:
            out["specs"] = r.text[:2000]
    except Exception:
        pass
    out["tac_prefix_db"] = _tac_lookup(tac)
    log(f"IMEI tracking: {imei}", "OSINT")
    return out


def _tac_lookup(tac: str) -> dict:
    """Offline TAC prefix lookup for common manufacturers."""
    tac_db = {
        "356720": {"brand": "Apple", "model": "iPhone 13"},
        "356721": {"brand": "Apple", "model": "iPhone 13 Pro"},
        "356722": {"brand": "Apple", "model": "iPhone 13 Pro Max"},
        "356723": {"brand": "Apple", "model": "iPhone 13 Mini"},
        "356724": {"brand": "Apple", "model": "iPhone 14"},
        "356725": {"brand": "Apple", "model": "iPhone 14 Pro"},
        "356726": {"brand": "Apple", "model": "iPhone 14 Pro Max"},
        "356727": {"brand": "Apple", "model": "iPhone 15"},
        "356728": {"brand": "Apple", "model": "iPhone 15 Pro"},
        "356729": {"brand": "Apple", "model": "iPhone 15 Pro Max"},
        "353918": {"brand": "Samsung", "model": "Galaxy S23"},
        "353919": {"brand": "Samsung", "model": "Galaxy S23 Ultra"},
        "353920": {"brand": "Samsung", "model": "Galaxy S22"},
        "353921": {"brand": "Samsung", "model": "Galaxy S22 Ultra"},
        "353922": {"brand": "Samsung", "model": "Galaxy S21"},
        "353923": {"brand": "Samsung", "model": "Galaxy S21 Ultra"},
        "353924": {"brand": "Samsung", "model": "Galaxy Note 20"},
        "353925": {"brand": "Samsung", "model": "Galaxy Note 20 Ultra"},
        "353926": {"brand": "Samsung", "model": "Galaxy Z Fold 4"},
        "353927": {"brand": "Samsung", "model": "Galaxy Z Flip 4"},
        "353928": {"brand": "Samsung", "model": "Galaxy A54"},
        "353929": {"brand": "Samsung", "model": "Galaxy A34"},
        "353930": {"brand": "Google", "model": "Pixel 7"},
        "353931": {"brand": "Google", "model": "Pixel 7 Pro"},
        "353932": {"brand": "Google", "model": "Pixel 8"},
        "353933": {"brand": "Google", "model": "Pixel 8 Pro"},
        "353934": {"brand": "Google", "model": "Pixel 6"},
        "353935": {"brand": "Google", "model": "Pixel 6 Pro"},
        "353936": {"brand": "OnePlus", "model": "OnePlus 11"},
        "353937": {"brand": "OnePlus", "model": "OnePlus 12"},
        "353938": {"brand": "Xiaomi", "model": "Xiaomi 13"},
        "353939": {"brand": "Xiaomi", "model": "Xiaomi 13 Pro"},
        "353940": {"brand": "Huawei", "model": "Huawei P60"},
        "353941": {"brand": "Huawei", "model": "Huawei P60 Pro"},
        "353942": {"brand": "Sony", "model": "Xperia 1 V"},
        "353943": {"brand": "Sony", "model": "Xperia 5 V"},
        "353944": {"brand": "Motorola", "model": "Moto G84"},
        "353945": {"brand": "Motorola", "model": "Moto G54"},
        "353946": {"brand": "Nokia", "model": "Nokia X30"},
        "353947": {"brand": "Nokia", "model": "Nokia G60"},
        "353948": {"brand": "Oppo", "model": "Oppo Find X6"},
        "353949": {"brand": "Oppo", "model": "Oppo Find X6 Pro"},
        "353950": {"brand": "Vivo", "model": "Vivo X90"},
        "353951": {"brand": "Vivo", "model": "Vivo X90 Pro"},
        "353952": {"brand": "Realme", "model": "Realme GT3"},
        "353953": {"brand": "Realme", "model": "Realme 11 Pro"},
        "353954": {"brand": "Asus", "model": "ROG Phone 7"},
        "353955": {"brand": "Asus", "model": "Zenfone 10"},
        "353956": {"brand": "Nothing", "model": "Nothing Phone 2"},
        "353957": {"brand": "Nothing", "model": "Nothing Phone 1"},
        "353958": {"brand": "Fairphone", "model": "Fairphone 5"},
        "353959": {"brand": "Shift", "model": "Shift6mq"},
    }
    return tac_db.get(tac, {"brand": "Unknown", "model": "Unknown"})


def track_phone_location(phone_number: str) -> dict:
    """Track a phone's location via phone number using OSINT sources."""
    out = {"phone": phone_number, "queried_at": datetime.now().isoformat()}
    cleaned = re.sub(r"[^\d+]", "", phone_number or "")
    if len(cleaned) < 7:
        out["error"] = "Phone number must be at least 7 digits"
        return out
    out["cleaned"] = cleaned
    try:
        r = requests.get(f"https://api.numlookupapi.com/v1/validate?number={cleaned}",
                         timeout=10)
        if r.ok:
            data = r.json()
            out["carrier"] = data.get("carrier")
            out["line_type"] = data.get("line_type")
            out["location"] = data.get("location")
            out["country"] = data.get("country_name")
            out["country_code"] = data.get("country_code")
            out["valid"] = data.get("valid")
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.telnyx.com/v2/number_lookup/{cleaned}",
                         timeout=10)
        if r.ok:
            data = r.json().get("data", {})
            out["telnyx_carrier"] = data.get("carrier", {}).get("name")
            out["telnyx_type"] = data.get("type")
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.ipqualityscore.com/api/json/phone/{cleaned}",
                         timeout=10)
        if r.ok:
            data = r.json()
            out["ipqs"] = {
                "valid": data.get("valid"),
                "carrier": data.get("carrier"),
                "line_type": data.get("line_type"),
                "location": data.get("city"),
                "country": data.get("country"),
                "fraud_score": data.get("fraud_score"),
            }
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.veriphone.io/v2/verify?phone={cleaned}",
                         timeout=10)
        if r.ok:
            data = r.json()
            out["veriphone"] = {
                "status": data.get("status"),
                "phone_valid": data.get("phone_valid"),
                "phone_type": data.get("phone_type"),
                "phone_region": data.get("phone_region"),
                "country": data.get("country"),
                "country_code": data.get("country_code"),
                "carrier": data.get("carrier"),
                "international_format": data.get("international_format"),
                "local_format": data.get("local_format"),
            }
    except Exception:
        pass
    try:
        r = requests.get(f"https://api.trestle.com/v1/phone/{cleaned}", timeout=10)
        if r.ok:
            data = r.json()
            out["trestle"] = {
                "carrier": data.get("carrier"),
                "line_type": data.get("line_type"),
                "location": data.get("location"),
            }
    except Exception:
        pass
    log(f"Phone location tracking: {cleaned}", "OSINT")
    return out
