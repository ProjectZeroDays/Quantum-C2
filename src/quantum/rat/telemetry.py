"""Telemetry collector + ring buffer — Phase 1 minimal."""
from __future__ import annotations
from collections import deque
from typing import Dict, List
import time

class TelemetryRing:
    """Ring buffer: 60s @ 1Hz default."""
    def __init__(self, window_s=60, interval=1.0):
        self.buf = deque(maxlen=int(window_s/interval)+1)
    def append(self, metric: str, value: float, src: str = "v"):
        self.buf.append({"metric": metric, "value": value, "ts": time.time(), "src": src})
    def window(self, metric: str, window_s=60):
        cutoff = time.time() - window_s
        return [r for r in self.buf if r["metric"]==metric and r["ts"]>=cutoff]

TELEMETRY = TelemetryRing()
