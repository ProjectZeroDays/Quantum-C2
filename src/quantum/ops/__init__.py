"""quantum.ops — real post-exploitation operator modules.

  evasion       — timestomp, masquerade, purge_logs, jitter (host-local)
  exfil         — DNS TXT tunnel, HTTPS POST, packaged envelopes
  persistence   — run keys, scheduled tasks, startup folder, cron, rc
  tools         — external tool catalog + detection

Ported from Quantum C2 (approved Tier-1 scope).
"""
from . import evasion, exfil, persistence, tools

__all__ = ["evasion", "exfil", "persistence", "tools"]
