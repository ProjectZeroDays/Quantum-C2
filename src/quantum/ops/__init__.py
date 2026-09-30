"""quantum.ops — real post-exploitation operator modules + compliance.

  evasion       — timestomp, masquerade, purge_logs, jitter (host-local)
  exfil         — DNS TXT tunnel, HTTPS POST, packaged envelopes
  persistence   — run keys, scheduled tasks, startup folder, cron, rc
  compliance_engine / compliance_controls_db — NIST/FedRAMP/etc.
  tools         — external tool catalog + detection

Ported from Quantum C2 (approved Tier-1 scope) with the
compliance_controls_db import fixed to a relative import.
"""
from . import compliance_engine, evasion, exfil, persistence, tools

__all__ = ["compliance_engine", "evasion", "exfil", "persistence", "tools"]
