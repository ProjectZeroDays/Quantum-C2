"""Helper functions for post-exploitation modules."""

from __future__ import annotations

import base64
import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from quantum.core.artifacts import register_artifact, register_artifact_bytes
from quantum.core.ids import new_loot_id
from quantum.rat.registry import get_device


# Shell command helpers

def sh_escape(s: str) -> str:
    """Escape a string for safe shell usage."""
    return shlex.quote(s)


def sh_join(parts: List[str]) -> str:
    """Join command parts with proper escaping."""
    return " ".join(sh_escape(p) for p in parts)


def run_shell(cmd: str, timeout: int = 60, cwd: str = None) -> Tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def run_shell_streaming(cmd: str, timeout: int = 60, callback=None) -> Tuple[int, str, str]:
    """Run a shell command with streaming output."""
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Read stdout
        for line in process.stdout:
            stdout_lines.append(line)
            if callback:
                callback("stdout", line)
        
        # Read stderr
        for line in process.stderr:
            stderr_lines.append(line)
            if callback:
                callback("stderr", line)
        
        process.wait(timeout=timeout)
        return process.returncode, "".join(stdout_lines), "".join(stderr_lines)
        
    except subprocess.TimeoutExpired:
        process.kill()
        return -1, "".join(stdout_lines), "".join(stderr_lines) + f"\nTimed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


# ADB helpers

def adb_escape(s: str) -> str:
    """Escape a string for ADB shell."""
    # ADB shell uses a different escaping mechanism
    return s.replace("'", "'\\''").replace("$", "\\$").replace("`", "\\`")


def build_adb_cmd(serial: str, command: str, as_root: bool = False) -> str:
    """Build an ADB command for a specific device."""
    parts = ["adb"]
    if serial:
        parts.extend(["-s", serial])
    parts.append("shell")
    if as_root:
        parts.append("su -c")
        parts.append(sh_escape(command))
    else:
        parts.append(command)
    return " ".join(parts)


def run_adb(serial: str, command: str, timeout: int = 60, as_root: bool = False) -> Tuple[int, str, str]:
    """Run an ADB command on a device."""
    cmd = build_adb_cmd(serial, command, as_root)
    return run_shell(cmd, timeout)


def adb_push(serial: str, local: str, remote: str, timeout: int = 120) -> Tuple[int, str, str]:
    """Push a file to device via ADB."""
    parts = ["adb"]
    if serial:
        parts.extend(["-s", serial])
    parts.extend(["push", local, remote])
    return run_shell(" ".join(shlex.quote(p) for p in parts), timeout)


def adb_pull(serial: str, remote: str, local: str, timeout: int = 120) -> Tuple[int, str, str]:
    """Pull a file from device via ADB."""
    parts = ["adb"]
    if serial:
        parts.extend(["-s", serial])
    parts.extend(["pull", remote, local])
    return run_shell(" ".join(shlex.quote(p) for p in parts), timeout)


def adb_install(serial: str, apk_path: str, timeout: int = 120, flags: List[str] = None) -> Tuple[int, str, str]:
    """Install an APK via ADB."""
    parts = ["adb"]
    if serial:
        parts.extend(["-s", serial])
    parts.append("install")
    if flags:
        parts.extend(flags)
    parts.append(apk_path)
    return run_shell(" ".join(shlex.quote(p) for p in parts), timeout)


def adb_uninstall(serial: str, package: str, timeout: int = 30) -> Tuple[int, str, str]:
    """Uninstall a package via ADB."""
    parts = ["adb"]
    if serial:
        parts.extend(["-s", serial])
    parts.extend(["uninstall", package])
    return run_shell(" ".join(shlex.quote(p) for p in parts), timeout)


# Output parsing helpers

def parse_key_value(text: str, separator: str = ":", strip: bool = True) -> Dict[str, str]:
    """Parse key:value lines into a dictionary."""
    result = {}
    for line in text.splitlines():
        if separator in line:
            key, value = line.split(separator, 1)
            if strip:
                key = key.strip()
                value = value.strip()
            result[key] = value
    return result


def parse_table(text: str, header: bool = True) -> List[Dict[str, str]]:
    """Parse a whitespace-aligned table into list of dicts."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    # Find column boundaries
    if header:
        header_line = lines[0]
        # Detect columns by multiple spaces
        cols = re.split(r'\s{2,}', header_line)
        data_lines = lines[1:]
    else:
        # Assume first line defines columns
        cols = [f"col_{i}" for i in range(len(re.split(r'\s+', lines[0])))]
        data_lines = lines

    result = []
    for line in data_lines:
        values = re.split(r'\s{2,}', line)
        if len(values) == len(cols):
            result.append(dict(zip(cols, values)))
    return result


def parse_ps(text: str) -> List[Dict[str, str]]:
    """Parse ps output."""
    # Handle various ps formats
    lines = text.strip().splitlines()
    if not lines:
        return []

    # Try to detect header
    header_idx = 0
    for i, line in enumerate(lines):
        if "PID" in line and ("CMD" in line or "COMMAND" in line):
            header_idx = i
            break

    headers = re.split(r'\s+', lines[header_idx].strip())
    results = []

    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        parts = re.split(r'\s+', line.strip(), maxsplit=len(headers) - 1)
        if len(parts) >= len(headers):
            results.append(dict(zip(headers, parts)))

    return results


def parse_netstat(text: str) -> List[Dict[str, str]]:
    """Parse netstat/ss output."""
    lines = text.strip().splitlines()
    results = []

    for line in lines:
        if not line.strip() or line.startswith("Active") or line.startswith("Proto"):
            continue
        parts = re.split(r'\s+', line.strip())
        if len(parts) >= 5:
            results.append({
                "proto": parts[0],
                "local_addr": parts[3] if len(parts) > 3 else "",
                "foreign_addr": parts[4] if len(parts) > 4 else "",
                "state": parts[5] if len(parts) > 5 else "",
            })
    return results


def parse_df(text: str) -> List[Dict[str, str]]:
    """Parse df -h output."""
    lines = text.strip().splitlines()
    results = []

    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 6:
            results.append({
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "avail": parts[3],
                "use_pct": parts[4],
                "mounted_on": " ".join(parts[5:]),
            })
    return results


def parse_ls(text: str) -> List[Dict[str, str]]:
    """Parse ls -la output."""
    lines = text.strip().splitlines()
    results = []

    for line in lines:
        if not line.strip() or line.startswith("total"):
            continue
        # drwxr-xr-x 2 user group 4096 Jan 1 12:00 name
        match = re.match(
            r'([dlcbps-][rwxt-]{9})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+\s+\S+\s+\S+)\s+(.+)',
            line
        )
        if match:
            results.append({
                "perms": match.group(1),
                "links": match.group(2),
                "owner": match.group(3),
                "group": match.group(4),
                "size": match.group(5),
                "date": match.group(6),
                "name": match.group(7),
            })
    return results


# File handling helpers

def read_file_safe(path: str, max_size: int = 10*1024*1024) -> Optional[str]:
    """Safely read a file with size limit."""
    try:
        path_obj = Path(path)
        if path_obj.stat().st_size > max_size:
            return None
        return path_obj.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def read_file_bytes(path: str, max_size: int = 10*1024*1024) -> Optional[bytes]:
    """Safely read a file as bytes with size limit."""
    try:
        path_obj = Path(path)
        if path_obj.stat().st_size > max_size:
            return None
        return path_obj.read_bytes()
    except Exception:
        return None


def write_file_safe(path: str, content: Union[str, bytes], mode: int = 0o600) -> bool:
    """Safely write a file."""
    try:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            path_obj.write_text(content, encoding="utf-8")
        else:
            path_obj.write_bytes(content)
        path_obj.chmod(mode)
        return True
    except Exception:
        return False


def find_files(root: str, pattern: str = "*", max_depth: int = 5) -> List[str]:
    """Find files matching pattern."""
    root_path = Path(root)
    if not root_path.exists():
        return []

    results = []
    for path in root_path.rglob(pattern):
        if path.is_file():
            # Check depth
            depth = len(path.relative_to(root_path).parts)
            if depth <= max_depth:
                results.append(str(path))
    return results


# Encoding helpers

def b64_encode(data: Union[str, bytes]) -> str:
    """Base64 encode."""
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def b64_decode(data: str) -> bytes:
    """Base64 decode."""
    return base64.b64decode(data)


def hex_encode(data: bytes) -> str:
    """Hex encode."""
    return data.hex()


def hex_decode(data: str) -> bytes:
    """Hex decode."""
    return bytes.fromhex(data)


# Credential parsing helpers

def parse_credential_line(line: str) -> Optional[Dict[str, str]]:
    """Parse a credential line (various formats)."""
    # user:pass
    # user:pass:domain
    # domain\\user:pass
    # email:pass
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Try various formats
    patterns = [
        r'^([^:]+):([^:]+):([^:]+)$',  # user:pass:domain
        r'^(.+?\\\\(.+?)):([^:]+)$',   # domain\\user:pass
        r'^([^:]+):([^:]+)$',          # user:pass
    ]

    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return {"username": groups[0], "password": groups[1], "domain": groups[2]}
            elif len(groups) == 2:
                return {"username": groups[0], "password": groups[1]}

    return None


def extract_credentials(text: str) -> List[Dict[str, str]]:
    """Extract credentials from text."""
    creds = []
    for line in text.splitlines():
        parsed = parse_credential_line(line)
        if parsed:
            creds.append(parsed)
    return creds


# Hash parsing

def identify_hash_type(hash_str: str) -> List[str]:
    """Identify possible hash types based on length and format."""
    hash_str = hash_str.strip().lower()
    length = len(hash_str)

    # Remove common prefixes
    if hash_str.startswith("$"):
        # Modular crypt format
        parts = hash_str.split("$")
        if len(parts) >= 3:
            ident = parts[1]
            hash_map = {
                "1": "md5crypt",
                "2a": "bcrypt", "2b": "bcrypt", "2y": "bcrypt",
                "5": "sha256crypt",
                "6": "sha512crypt",
                "sha1": "sha1crypt",
            }
            return [hash_map.get(ident, "crypt")]

    # Length-based identification
    candidates = []
    if length == 32 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("md5")
    if length == 40 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("sha1")
    if length == 64 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("sha256")
    if length == 96 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("sha384")
    if length == 128 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("sha512")
    if length == 16 and re.match(r'^[a-f0-9]+$', hash_str):
        candidates.append("md4", "ntlm")
    if re.match(r'^\$[0-9a-z]+\$', hash_str):
        candidates.append("crypt")

    return candidates


# Network helpers

def is_private_ip(ip: str) -> bool:
    """Check if IP is private."""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except Exception:
        return False


def cidr_to_range(cidr: str) -> Tuple[str, str]:
    """Convert CIDR to start/end IP."""
    import ipaddress
    network = ipaddress.ip_network(cidr, strict=False)
    return str(network.network_address), str(network.broadcast_address)


def parse_ip_port(s: str) -> Tuple[str, int]:
    """Parse IP:port string."""
    if ":" in s:
        ip, port = s.rsplit(":", 1)
        return ip, int(port)
    return s, 0


# Time helpers

def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


def format_size(bytes_: int) -> str:
    """Format byte size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_ < 1024:
            return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}PB"


def format_timestamp(ts: float) -> str:
    """Format timestamp as ISO string."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def time_ago(ts: float) -> str:
    """Get human-readable time ago."""
    diff = time.time() - ts
    if diff < 60:
        return f"{int(diff)}s ago"
    elif diff < 3600:
        return f"{int(diff/60)}m ago"
    elif diff < 86400:
        return f"{int(diff/3600)}h ago"
    else:
        return f"{int(diff/86400)}d ago"


# Platform detection

def detect_platform() -> str:
    """Detect current platform."""
    import platform
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def get_arch() -> str:
    """Get architecture."""
    import platform
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    elif machine in ("aarch64", "arm64"):
        return "arm64"
    elif machine.startswith("arm"):
        return "arm"
    elif machine in ("i386", "i686"):
        return "x86"
    return machine


# Validation helpers

def validate_ip(ip: str) -> bool:
    """Validate IP address."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except Exception:
        return False


def validate_cidr(cidr: str) -> bool:
    """Validate CIDR notation."""
    import ipaddress
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except Exception:
        return False


def validate_port(port: int) -> bool:
    """Validate port number."""
    return 1 <= port <= 65535


def validate_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# JSON helpers

def json_loads_safe(text: str, default: Any = None) -> Any:
    """Safely parse JSON."""
    try:
        return json.loads(text)
    except Exception:
        return default


def json_dumps_safe(obj: Any, default: str = "") -> str:
    """Safely serialize to JSON."""
    try:
        return json.dumps(obj, default=str, separators=(",", ":"))
    except Exception:
        return default