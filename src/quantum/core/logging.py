"""quantum.core.logging — structured audit log + MITRE mapper."""
from __future__ import annotations

import json
import os
from datetime import datetime

from quantum.core.env import LOG_DIR


def log(msg, tag="INFO"):
    """Structured audit log: JSONL to logs/audit.jsonl + console line."""
    line = json.dumps({"ts": datetime.now().isoformat(), "tag": tag, "msg": str(msg)})
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "audit.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    try:
        print(f"[{tag}] {msg}")
    except Exception:
        pass
    return line


def _tail_jsonl(path, n=100):
    """Last n parseable JSON lines of a jsonl file."""
    out = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return out
    for raw in lines[-n:]:
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


class MitreMapper:
    """audit.jsonl -> mitre_map.json (keyword rules, auto at close)."""

    RULES = [
        ("cam war", "T1595.002"), ("camwar", "T1595.002"),
        ("log4shell", "T1190"), ("citrix", "T1190"), ("pan-os", "T1190"),
        ("panos", "T1190"), ("confluence", "T1190"), ("weblogic", "T1190"),
        ("dirtypipe", "T1068"), ("dirty pipe", "T1068"), ("pwnkit", "T1068"),
        ("baron samedit", "T1068"), ("samedit", "T1068"), ("nf_tables", "T1068"),
        ("flashfill", "T1499"), ("emojism", "T1132.001"), ("emoji", "T1132.001"),
        ("rtsp", "T1110.003"), ("brute", "T1110.003"), ("zerocheck", "T1595"),
        ("mshtml", "T1203"), ("boothole", "T1542.001"), ("beacon", "T1071"),
        ("c2", "T1071"), ("killswitch", "T1485"), ("wipe", "T1485"),
        ("keylogger", "T1056.001"), ("persistx", "T1547"),
        ("registry", "T1112"), ("snapshot", "T1560"), ("seal", "T1560"),
        ("ghostdns", "T1071.004"), ("doh", "T1071.004"),
        ("worm", "T1021"), ("phish", "T1566"), ("harvest", "T1005"),
    ]

    def map_audit(self):
        events = _tail_jsonl(os.path.join(LOG_DIR, "audit.jsonl"), 2000)
        hits = {}
        for ev in events:
            hay = json.dumps(ev, default=str).lower()
            for kw, tid in self.RULES:
                if kw in hay:
                    hits.setdefault(tid, 0)
                    hits[tid] += 1
        out = {"generated": datetime.now().isoformat(),
               "coverage": sorted(hits), "counts": hits,
               "events_scanned": len(events)}
        path = os.path.join(LOG_DIR, "mitre_map.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        return out
