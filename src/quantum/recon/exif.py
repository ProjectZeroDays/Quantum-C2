"""quantum.recon.exif — Photo EXIF data analysis dashboard.

Extracts and analyzes EXIF data from photos including GPS coordinates,
camera info, timestamps, and hidden metadata.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

from quantum.core.logging import log


def analyze_exif(image_path: str) -> dict:
    """Analyze EXIF data from an image file."""
    if not os.path.isfile(image_path):
        return {"error": f"Image not found: {image_path}"}
    out = {
        "file": image_path,
        "file_size": os.path.getsize(image_path),
        "analyzed_at": datetime.now().isoformat(),
        "exif": {},
        "gps": None,
        "camera": {},
        "software": None,
        "timestamps": {},
        "hidden_data": [],
    }
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        img = Image.open(image_path)
        out["format"] = img.format
        out["mode"] = img.mode
        out["size"] = img.size
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
                    out["gps"] = _parse_gps(gps_data)
                elif tag == "Make":
                    out["camera"]["make"] = str(value)
                elif tag == "Model":
                    out["camera"]["model"] = str(value)
                elif tag == "Software":
                    out["software"] = str(value)
                elif tag == "DateTime":
                    out["timestamps"]["datetime"] = str(value)
                elif tag == "DateTimeOriginal":
                    out["timestamps"]["datetime_original"] = str(value)
                elif tag == "DateTimeDigitized":
                    out["timestamps"]["datetime_digitized"] = str(value)
                else:
                    out["exif"][tag] = str(value)
    except ImportError:
        out["error"] = "Pillow not installed. Run: pip install Pillow"
    except Exception as exc:
        out["error"] = str(exc)
    try:
        with open(image_path, "rb") as f:
            raw = f.read()
        out["hidden_data"] = _find_hidden_data(raw)
    except Exception:
        pass
    log(f"EXIF analysis: {image_path}", "EXIF")
    return out


def _parse_gps(gps_data: dict) -> dict:
    """Parse GPS EXIF data into coordinates."""
    out = {}
    try:
        if "GPSLatitude" in gps_data and "GPSLatitudeRef" in gps_data:
            lat = gps_data["GPSLatitude"]
            lat_ref = gps_data["GPSLatitudeRef"]
            lat_decimal = float(lat[0]) + float(lat[1]) / 60 + float(lat[2]) / 3600
            if lat_ref == "S":
                lat_decimal = -lat_decimal
            out["latitude"] = lat_decimal
        if "GPSLongitude" in gps_data and "GPSLongitudeRef" in gps_data:
            lon = gps_data["GPSLongitude"]
            lon_ref = gps_data["GPSLongitudeRef"]
            lon_decimal = float(lon[0]) + float(lon[1]) / 60 + float(lon[2]) / 3600
            if lon_ref == "W":
                lon_decimal = -lon_decimal
            out["longitude"] = lon_decimal
        if "GPSAltitude" in gps_data:
            out["altitude"] = float(gps_data["GPSAltitude"])
        if "GPSTimeStamp" in gps_data:
            out["timestamp"] = gps_data["GPSTimeStamp"]
        if "GPSDateStamp" in gps_data:
            out["date"] = gps_data["GPSDateStamp"]
    except Exception:
        pass
    return out


def _find_hidden_data(raw: bytes) -> list:
    """Find hidden data in image file."""
    hidden = []
    try:
        strings = re.findall(rb"[\x20-\x7e]{8,}", raw)
        for s in strings:
            text = s.decode("ascii", errors="ignore")
            if any(kw in text.lower() for kw in ["password", "secret", "key", "token", "user"]):
                hidden.append({"type": "string", "value": text[:200]})
        if b"tEXt" in raw:
            hidden.append({"type": "text_chunk", "value": "PNG text chunk found"})
        if b"iTXt" in raw:
            hidden.append({"type": "international_text", "value": "PNG international text chunk found"})
        if b"zTXt" in raw:
            hidden.append({"type": "compressed_text", "value": "PNG compressed text chunk found"})
        if b"eXIf" in raw:
            hidden.append({"type": "exif", "value": "EXIF data found"})
        if b"photoshop" in raw.lower():
            hidden.append({"type": "photoshop", "value": "Photoshop data found"})
        if b"adobe" in raw.lower():
            hidden.append({"type": "adobe", "value": "Adobe data found"})
        if b"icc_profile" in raw.lower():
            hidden.append({"type": "icc_profile", "value": "ICC profile found"})
        if b"xml" in raw.lower():
            hidden.append({"type": "xml", "value": "XML data found"})
        if b"<?php" in raw:
            hidden.append({"type": "php", "value": "PHP code found"})
        if b"<script" in raw.lower():
            hidden.append({"type": "script", "value": "Script found"})
        if b"eval(" in raw:
            hidden.append({"type": "eval", "value": "Eval function found"})
        if b"base64" in raw.lower():
            hidden.append({"type": "base64", "value": "Base64 data found"})
    except Exception:
        pass
    return hidden


def extract_gps_coordinates(image_path: str) -> dict:
    """Extract GPS coordinates from an image."""
    result = analyze_exif(image_path)
    return result.get("gps", {})


def get_camera_info(image_path: str) -> dict:
    """Extract camera information from an image."""
    result = analyze_exif(image_path)
    return result.get("camera", {})


def get_timestamps(image_path: str) -> dict:
    """Extract timestamps from an image."""
    result = analyze_exif(image_path)
    return result.get("timestamps", {})


def exif_dashboard_state() -> dict:
    """Return the full EXIF dashboard state for the UI."""
    return {
        "analyzed_images": [],
        "total_images": 0,
        "images_with_gps": 0,
        "images_with_hidden_data": 0,
        "generated_at": datetime.now().isoformat(),
    }
