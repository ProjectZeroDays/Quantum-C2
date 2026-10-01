"""quantum.control.map2d — 2D map widget for displaying device beacons.

Provides a full-width 2D map for displaying beacons for all devices currently
connected, with real-time tracking and historical trails.
"""
from __future__ import annotations

import math
from datetime import datetime

from quantum.core.logging import log


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_map_data(beacons: list) -> dict:
    """Generate 2D map data for the given beacons."""
    out = {
        "generated_at": datetime.now().isoformat(),
        "beacons": [],
        "bounds": {
            "min_lat": -90,
            "max_lat": 90,
            "min_lon": -180,
            "max_lon": 180,
        },
        "center": {
            "lat": 0,
            "lon": 0,
        },
        "zoom": 2,
        "total_beacons": len(beacons),
    }
    if not beacons:
        return out
    lats = [b.get("lat", 0) for b in beacons if b.get("lat") is not None]
    lons = [b.get("lon", 0) for b in beacons if b.get("lon") is not None]
    if lats and lons:
        out["bounds"]["min_lat"] = min(lats)
        out["bounds"]["max_lat"] = max(lats)
        out["bounds"]["min_lon"] = min(lons)
        out["bounds"]["max_lon"] = max(lons)
        out["center"]["lat"] = (min(lats) + max(lats)) / 2
        out["center"]["lon"] = (min(lons) + max(lons)) / 2
        lat_span = max(lats) - min(lats)
        lon_span = max(lons) - min(lons)
        max_span = max(lat_span, lon_span)
        if max_span > 0:
            out["zoom"] = max(1, min(18, int(360 / max_span)))
    for beacon in beacons:
        out["beacons"].append({
            "id": beacon.get("id", ""),
            "lat": beacon.get("lat", 0),
            "lon": beacon.get("lon", 0),
            "alt": beacon.get("alt", 0),
            "speed": beacon.get("speed", 0),
            "heading": beacon.get("heading", 0),
            "timestamp": beacon.get("timestamp", ""),
            "device_type": beacon.get("device_type", "unknown"),
            "status": beacon.get("status", "unknown"),
            "battery": beacon.get("battery", 0),
            "signal": beacon.get("signal", 0),
            "accuracy": beacon.get("accuracy", 0),
            "label": beacon.get("label", ""),
            "trail": beacon.get("trail", []),
        })
    log(f"2D map data generated: {len(beacons)} beacons", "MAP2D")
    return out


def add_beacon(beacons: list, beacon_id: str, lat: float, lon: float,
               device_type: str = "unknown", **kwargs) -> list:
    """Add a new beacon to the list."""
    beacon = {
        "id": beacon_id,
        "lat": lat,
        "lon": lon,
        "alt": kwargs.get("alt", 0),
        "speed": kwargs.get("speed", 0),
        "heading": kwargs.get("heading", 0),
        "timestamp": datetime.now().isoformat(),
        "device_type": device_type,
        "status": kwargs.get("status", "active"),
        "battery": kwargs.get("battery", 100),
        "signal": kwargs.get("signal", 100),
        "accuracy": kwargs.get("accuracy", 0),
        "label": kwargs.get("label", ""),
        "trail": [],
    }
    beacons.append(beacon)
    return beacons


def update_beacon(beacons: list, beacon_id: str, **kwargs) -> list:
    """Update an existing beacon."""
    for beacon in beacons:
        if beacon["id"] == beacon_id:
            old_lat = beacon.get("lat", 0)
            old_lon = beacon.get("lon", 0)
            for key, value in kwargs.items():
                beacon[key] = value
            beacon["timestamp"] = datetime.now().isoformat()
            if "lat" in kwargs or "lon" in kwargs:
                beacon["trail"].append({
                    "lat": old_lat,
                    "lon": old_lon,
                    "timestamp": datetime.now().isoformat(),
                })
                if len(beacon["trail"]) > 100:
                    beacon["trail"] = beacon["trail"][-100:]
            break
    return beacons


def remove_beacon(beacons: list, beacon_id: str) -> list:
    """Remove a beacon from the list."""
    return [b for b in beacons if b["id"] != beacon_id]


def get_beacon_distance(beacons: list, id1: str, id2: str) -> float:
    """Get the distance between two beacons in km."""
    b1 = next((b for b in beacons if b["id"] == id1), None)
    b2 = next((b for b in beacons if b["id"] == id2), None)
    if not b1 or not b2:
        return -1
    return haversine_distance(b1["lat"], b1["lon"], b2["lat"], b2["lon"])


def map2d_dashboard_state() -> dict:
    """Return the full 2D map dashboard state for the UI."""
    return {
        "beacons": [],
        "total_beacons": 0,
        "center": {"lat": 0, "lon": 0},
        "zoom": 2,
        "generated_at": datetime.now().isoformat(),
    }
