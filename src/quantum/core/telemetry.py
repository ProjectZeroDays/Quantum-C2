"""quantum.core.telemetry — Telemetry collector dispatch + ring buffers.

Collects device metrics over WS/SSE with windowed queries (60s / 1h / 24h).
"""
from __future__ import annotations

import asyncio
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional


@dataclass
class TelemetrySample:
    """A single telemetry sample from a device."""
    device_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cpu_total: Optional[float] = None
    cpu_per_core: Dict[str, float] = field(default_factory=dict)
    memory_total: Optional[float] = None
    memory_used: Optional[float] = None
    memory_available: Optional[float] = None
    gpu_temp: Optional[float] = None
    battery_level: Optional[float] = None
    battery_temp: Optional[float] = None
    battery_health: Optional[str] = None
    storage_total: Optional[float] = None
    storage_used: Optional[float] = None
    network_rx: Optional[float] = None
    network_tx: Optional[float] = None
    active_connections: Optional[int] = None
    signal_dbm: Optional[float] = None
    wifi_rssi: Optional[float] = None
    bluetooth_rssi: Optional[float] = None
    disk_iops: Optional[float] = None
    packet_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "cpu_total": self.cpu_total,
            "cpu_per_core": self.cpu_per_core,
            "memory_total": self.memory_total,
            "memory_used": self.memory_used,
            "memory_available": self.memory_available,
            "gpu_temp": self.gpu_temp,
            "battery_level": self.battery_level,
            "battery_temp": self.battery_temp,
            "battery_health": self.battery_health,
            "storage_total": self.storage_total,
            "storage_used": self.storage_used,
            "network_rx": self.network_rx,
            "network_tx": self.network_tx,
            "active_connections": self.active_connections,
            "signal_dbm": self.signal_dbm,
            "wifi_rssi": self.wifi_rssi,
            "bluetooth_rssi": self.bluetooth_rssi,
            "disk_iops": self.disk_iops,
            "packet_rate": self.packet_rate,
        }


class TelemetryStore:
    """Ring buffer telemetry store per device."""

    def __init__(self, max_samples: int = 1440):  # 24h at 1-minute interval
        self._buffers: Dict[str, Deque[TelemetrySample]] = {}
        self._lock = threading.RLock()
        self._max_samples = max_samples

    def add(self, sample: TelemetrySample):
        """Add a telemetry sample to the ring buffer."""
        device_id = sample.device_id
        with self._lock:
            if device_id not in self._buffers:
                self._buffers[device_id] = deque(maxlen=self._max_samples)
            self._buffers[device_id].append(sample)

    def get_window(self, device_id: str, minutes: int) -> List[TelemetrySample]:
        """Get samples within the last N minutes for a device."""
        if minutes < 1:
            minutes = 1
        since = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            buffer = self._buffers.get(device_id)
            if buffer is None:
                return []
            
            result = []
            for sample in buffer:
                try:
                    ts = datetime.fromisoformat(sample.timestamp)
                    if ts >= since:
                        result.append(sample)
                except (ValueError, TypeError):
                    continue
            return result

    def get_latest(self, device_id: str) -> Optional[TelemetrySample]:
        """Get the latest sample for a device."""
        with self._lock:
            buffer = self._buffers.get(device_id)
            if buffer and len(buffer) > 0:
                return buffer[-1]
        return None

    def get_all_devices(self) -> List[str]:
        """Get all device IDs with telemetry."""
        with self._lock:
            return list(self._buffers.keys())

    def clear_device(self, device_id: str):
        """Clear telemetry for a device."""
        with self._lock:
            self._buffers.pop(device_id, None)


# Global telemetry store instance
_telemetry_store = TelemetryStore()


def get_telemetry_store() -> TelemetryStore:
    """Get global telemetry store."""
    return _telemetry_store


# Async telemetry collector dispatch

class TelemetryCollector:
    """Dispatch telemetry collection to connected devices."""

    def __init__(self, telemetry_store: TelemetryStore, event_bus=None):
        self.store = telemetry_store
        self.event_bus = event_bus
        self._collectors: Dict[str, Any] = {}
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

    def register_collector(self, device_id: str, collector_fn):
        """Register a telemetry collector function for a device."""
        self._collectors[device_id] = collector_fn

    async def start(self, interval: float = 60.0):
        """Start periodic telemetry collection loop."""
        self._running = True
        while self._running:
            await self.collect_all()
            await asyncio.sleep(interval)

    async def stop(self):
        """Stop telemetry collection."""
        self._running = False

    async def collect_all(self):
        """Collect telemetry from all registered devices."""
        for device_id, collector_fn in list(self._collectors.items()):
            try:
                if asyncio.iscoroutinefunction(collector_fn):
                    sample = await collector_fn()
                else:
                    sample = collector_fn()
                
                if sample:
                    if not isinstance(sample, TelemetrySample):
                        sample = TelemetrySample(device_id=device_id, **sample)
                    else:
                        sample.device_id = device_id
                    
                    self.store.add(sample)
                    
                    if self.event_bus:
                        await self.event_bus.publish(
                            topic=f"telemetry/{device_id}",
                            data=sample.to_dict(),
                        )
            except Exception as e:
                # Log error but don't crash the collector
                import logging
                logging.getLogger("quantum.core.telemetry").warning(
                    f"Telemetry collection failed for {device_id}: {e}"
                )


# Singleton
_collector: Optional[TelemetryCollector] = None


def get_collector(event_bus=None) -> TelemetryCollector:
    """Get global telemetry collector."""
    global _collector
    if _collector is None:
        _collector = TelemetryCollector(_telemetry_store, event_bus)
    return _collector
