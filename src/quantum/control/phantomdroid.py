"""quantum.control.phantomdroid — PhantomDroid ADB wireless and USB controls.

Provides full front-end controls for all PhantomDroid features to access
Android devices via ADB wireless and USB through the dashboard.
"""
from __future__ import annotations

import subprocess
from datetime import datetime

from quantum.core.logging import log

PHANTOMDROID_FEATURES = {
    "device_info": {
        "name": "Device Information",
        "description": "Get detailed device information",
        "commands": ["getprop", "dumpsys", "pm list packages"],
    },
    "screen_capture": {
        "name": "Screen Capture",
        "description": "Capture screenshots from the device",
        "commands": ["screencap", "screenrecord"],
    },
    "file_manager": {
        "name": "File Manager",
        "description": "Browse and manage files on the device",
        "commands": ["ls", "pull", "push", "rm", "mkdir"],
    },
    "app_manager": {
        "name": "App Manager",
        "description": "List, install, uninstall, and manage apps",
        "commands": ["pm list", "pm install", "pm uninstall", "pm enable", "pm disable"],
    },
    "process_manager": {
        "name": "Process Manager",
        "description": "List and manage running processes",
        "commands": ["ps", "top", "kill"],
    },
    "network_info": {
        "name": "Network Information",
        "description": "Get network configuration and status",
        "commands": ["ifconfig", "netstat", "ip route", "iwconfig"],
    },
    "battery_info": {
        "name": "Battery Information",
        "description": "Get battery status and health",
        "commands": ["dumpsys battery"],
    },
    "sensor_data": {
        "name": "Sensor Data",
        "description": "Access device sensors (accelerometer, gyroscope, etc.)",
        "commands": ["dumpsys sensorservice"],
    },
    "location": {
        "name": "Location",
        "description": "Get device GPS location",
        "commands": ["dumpsys location"],
    },
    "clipboard": {
        "name": "Clipboard",
        "description": "Access and modify clipboard content",
        "commands": ["am broadcast -a clipper.get", "am broadcast -a clipper.set"],
    },
    "notifications": {
        "name": "Notifications",
        "description": "Read and manage notifications",
        "commands": ["dumpsys notification"],
    },
    "sms": {
        "name": "SMS",
        "description": "Read and send SMS messages",
        "commands": ["content query --uri content://sms", "am broadcast -a android.intent.action.SENDTO"],
    },
    "calls": {
        "name": "Call Log",
        "description": "Read call history and manage calls",
        "commands": ["content query --uri content://call_log/calls"],
    },
    "contacts": {
        "name": "Contacts",
        "description": "Read and manage contacts",
        "commands": ["content query --uri content://contacts/people"],
    },
    "camera": {
        "name": "Camera",
        "description": "Capture photos and videos",
        "commands": ["am start -a android.media.action.IMAGE_CAPTURE"],
    },
    "microphone": {
        "name": "Microphone",
        "description": "Record audio from microphone",
        "commands": ["am start -a android.media.action.RECORD_SOUND"],
    },
    "screen_stream": {
        "name": "Screen Stream",
        "description": "Stream device screen in real-time",
        "commands": ["screenrecord --output-format=h264 -"],
    },
    "remote_shell": {
        "name": "Remote Shell",
        "description": "Execute shell commands on the device",
        "commands": ["adb shell"],
    },
    "port_forwarding": {
        "name": "Port Forwarding",
        "description": "Forward ports between device and host",
        "commands": ["adb forward", "adb reverse"],
    },
    "wifi_control": {
        "name": "WiFi Control",
        "description": "Control WiFi settings and scan networks",
        "commands": ["svc wifi enable", "svc wifi disable", "dumpsys wifi"],
    },
    "bluetooth_control": {
        "name": "Bluetooth Control",
        "description": "Control Bluetooth settings and scan devices",
        "commands": ["svc bluetooth enable", "svc bluetooth disable", "dumpsys bluetooth"],
    },
    "data_usage": {
        "name": "Data Usage",
        "description": "Monitor data usage statistics",
        "commands": ["dumpsys netstats"],
    },
    "storage_info": {
        "name": "Storage Information",
        "description": "Get storage usage and details",
        "commands": ["df", "dumpsys diskstats"],
    },
    "cpu_info": {
        "name": "CPU Information",
        "description": "Get CPU usage and information",
        "commands": ["top -n 1", "cat /proc/cpuinfo"],
    },
    "memory_info": {
        "name": "Memory Information",
        "description": "Get memory usage and details",
        "commands": ["cat /proc/meminfo", "dumpsys meminfo"],
    },
    "system_logs": {
        "name": "System Logs",
        "description": "Read system and application logs",
        "commands": ["logcat", "dmesg", "cat /proc/kmsg"],
    },
    "settings": {
        "name": "Settings",
        "description": "Read and modify system settings",
        "commands": ["settings get", "settings put"],
    },
    "security": {
        "name": "Security",
        "description": "Check security status and settings",
        "commands": ["dumpsys security", "getenforce"],
    },
    "accessibility": {
        "name": "Accessibility",
        "description": "Control accessibility services",
        "commands": ["settings get secure enabled_accessibility_services"],
    },
    "developer_options": {
        "name": "Developer Options",
        "description": "Control developer options",
        "commands": ["settings get global development_settings_enabled"],
    },
    "usb_debugging": {
        "name": "USB Debugging",
        "description": "Control USB debugging settings",
        "commands": ["settings get global adb_enabled"],
    },
    "unknown_sources": {
        "name": "Unknown Sources",
        "description": "Allow installation from unknown sources",
        "commands": ["settings get secure install_non_market_apps"],
    },
    "device_admin": {
        "name": "Device Admin",
        "description": "Manage device admin policies",
        "commands": ["dumpsys device_policy"],
    },
    "keyguard": {
        "name": "Keyguard",
        "description": "Control keyguard (lock screen)",
        "commands": ["dumpsys window policy"],
    },
    "power_management": {
        "name": "Power Management",
        "description": "Control power and sleep settings",
        "commands": ["dumpsys power"],
    },
    "vibration": {
        "name": "Vibration",
        "description": "Control vibration motor",
        "commands": ["am broadcast -a android.intent.action.VIBRATE"],
    },
    "nfc": {
        "name": "NFC",
        "description": "Control NFC settings",
        "commands": ["svc nfc enable", "svc nfc disable"],
    },
    "usb_connection": {
        "name": "USB Connection",
        "description": "Control USB connection mode",
        "commands": ["settings get global usb_configuration"],
    },
}


def list_phantomdroid_features() -> dict:
    """List all PhantomDroid features."""
    return PHANTOMDROID_FEATURES


def discover_adb_devices() -> list:
    """Discover connected ADB devices."""
    devices = []
    try:
        result = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        device = {
                            "serial": parts[0],
                            "status": parts[1],
                            "details": " ".join(parts[2:]) if len(parts) > 2 else "",
                        }
                        devices.append(device)
    except FileNotFoundError:
        log("ADB not found. Install Android SDK Platform Tools.", "ADB")
    except Exception as exc:
        log(f"ADB discovery error: {exc}", "ADB")
    return devices


def connect_adb_wireless(ip: str, port: int = 5555) -> dict:
    """Connect to an ADB device wirelessly."""
    out = {
        "ip": ip,
        "port": port,
        "connected": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "connect", f"{ip}:{port}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            out["connected"] = "connected" in result.stdout.lower()
            out["output"] = result.stdout.strip()
        else:
            out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB wireless connect: {ip}:{port}", "ADB")
    return out


def disconnect_adb(ip: str, port: int = 5555) -> dict:
    """Disconnect from an ADB device."""
    out = {
        "ip": ip,
        "port": port,
        "disconnected": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "disconnect", f"{ip}:{port}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            out["disconnected"] = True
            out["output"] = result.stdout.strip()
        else:
            out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB disconnect: {ip}:{port}", "ADB")
    return out


def adb_shell(serial: str, command: str) -> dict:
    """Execute a shell command on an ADB device."""
    out = {
        "serial": serial,
        "command": command,
        "output": "",
        "error": None,
        "returncode": -1,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", command],
            capture_output=True, text=True, timeout=30
        )
        out["output"] = result.stdout.strip()
        out["error"] = result.stderr.strip()
        out["returncode"] = result.returncode
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB shell: {serial} -> {command}", "ADB")
    return out


def adb_pull(serial: str, remote_path: str, local_path: str) -> dict:
    """Pull a file from an ADB device."""
    out = {
        "serial": serial,
        "remote": remote_path,
        "local": local_path,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "pull", remote_path, local_path],
            capture_output=True, text=True, timeout=60
        )
        out["success"] = result.returncode == 0
        out["output"] = result.stdout.strip()
        out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB pull: {serial} -> {remote_path}", "ADB")
    return out


def adb_push(serial: str, local_path: str, remote_path: str) -> dict:
    """Push a file to an ADB device."""
    out = {
        "serial": serial,
        "local": local_path,
        "remote": remote_path,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "push", local_path, remote_path],
            capture_output=True, text=True, timeout=60
        )
        out["success"] = result.returncode == 0
        out["output"] = result.stdout.strip()
        out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB push: {serial} -> {remote_path}", "ADB")
    return out


def adb_screencap(serial: str, output_path: str) -> dict:
    """Capture a screenshot from an ADB device."""
    out = {
        "serial": serial,
        "output": output_path,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "exec-out", "screencap", "-p"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            with open(output_path, "wb") as f:
                f.write(result.stdout)
            out["success"] = True
        else:
            out["error"] = result.stderr.decode("utf-8", errors="replace")
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB screencap: {serial} -> {output_path}", "ADB")
    return out


def adb_screenrecord(serial: str, output_path: str, duration: int = 10) -> dict:
    """Record the screen of an ADB device."""
    out = {
        "serial": serial,
        "output": output_path,
        "duration": duration,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "screenrecord", "--time-limit", str(duration), "/sdcard/screenrecord.mp4"],
            capture_output=True, text=True, timeout=duration + 10
        )
        if result.returncode == 0:
            pull_result = adb_pull(serial, "/sdcard/screenrecord.mp4", output_path)
            out["success"] = pull_result["success"]
            out["error"] = pull_result["error"]
        else:
            out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB screenrecord: {serial} -> {output_path}", "ADB")
    return out


def adb_install(serial: str, apk_path: str) -> dict:
    """Install an APK on an ADB device."""
    out = {
        "serial": serial,
        "apk": apk_path,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "install", "-r", apk_path],
            capture_output=True, text=True, timeout=60
        )
        out["success"] = result.returncode == 0
        out["output"] = result.stdout.strip()
        out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB install: {serial} -> {apk_path}", "ADB")
    return out


def adb_uninstall(serial: str, package_name: str) -> dict:
    """Uninstall an app from an ADB device."""
    out = {
        "serial": serial,
        "package": package_name,
        "success": False,
        "error": None,
    }
    try:
        result = subprocess.run(
            ["adb", "-s", serial, "uninstall", package_name],
            capture_output=True, text=True, timeout=30
        )
        out["success"] = result.returncode == 0
        out["output"] = result.stdout.strip()
        out["error"] = result.stderr.strip()
    except FileNotFoundError:
        out["error"] = "ADB not found. Install Android SDK Platform Tools."
    except Exception as exc:
        out["error"] = str(exc)
    log(f"ADB uninstall: {serial} -> {package_name}", "ADB")
    return out


def adb_list_packages(serial: str) -> dict:
    """List installed packages on an ADB device."""
    return adb_shell(serial, "pm list packages")


def adb_get_device_info(serial: str) -> dict:
    """Get detailed device information."""
    out = {
        "serial": serial,
        "info": {},
    }
    commands = {
        "model": "getprop ro.product.model",
        "brand": "getprop ro.product.brand",
        "manufacturer": "getprop ro.product.manufacturer",
        "android_version": "getprop ro.build.version.release",
        "sdk_version": "getprop ro.build.version.sdk",
        "build_id": "getprop ro.build.id",
        "build_fingerprint": "getprop ro.build.fingerprint",
        "serial_number": "getprop ro.serialno",
        "imei": "service call iphonesubinfo 1",
        "battery": "dumpsys battery",
        "cpu": "cat /proc/cpuinfo",
        "memory": "cat /proc/meminfo",
        "storage": "df",
        "network": "ifconfig",
        "wifi": "dumpsys wifi",
        "bluetooth": "dumpsys bluetooth",
        "location": "dumpsys location",
        "sensors": "dumpsys sensorservice",
    }
    for key, cmd in commands.items():
        result = adb_shell(serial, cmd)
        out["info"][key] = result.get("output", "")
    log(f"ADB device info: {serial}", "ADB")
    return out


def phantomdroid_dashboard_state() -> dict:
    """Return the full PhantomDroid dashboard state for the UI."""
    return {
        "features": PHANTOMDROID_FEATURES,
        "connected_devices": discover_adb_devices(),
        "generated_at": datetime.now().isoformat(),
    }
