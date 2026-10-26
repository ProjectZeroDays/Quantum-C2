"""Minimal /api/v1/devices endpoint — verified against registry."""
from __future__ import annotations
from flask import Blueprint, jsonify, request
from quantum.rat.registry import list_devices, get_device, create_device, get_device_summary
from quantum.core.db import init_db

bp = Blueprint("devices_api", __name__, url_prefix="/api/v1")

@bp.route("/devices", methods=["GET"])
def list_all():
    devices = list_devices(limit=100)
    return jsonify({"ok": True, "data": [d.to_dict() for d in devices]})

@bp.route("/devices/<device_id>", methods=["GET"])
def get_one(device_id):
    d = get_device(device_id)
    if not d:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "data": d.to_dict()})

@bp.route("/devices", methods=["POST"])
def create():
    data = request.get_json() or {}
    d = create_device(platform=data.get("platform",""), nickname=data.get("nickname",""), **data)
    return jsonify({"ok": True, "data": d.to_dict()})

@bp.route("/devices/<device_id>/telemetry", methods=["GET"])
def telemetry_window():
    # Placeholder: real telemetry_store.py needed
    return jsonify({"ok": True, "data": [], "note": "telemetry_store not implemented — needs ring buffer"})
