"""Settings store and exploit scoring weights configuration."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from quantum.core.db import execute, execute_one, execute_write, transaction, get_conn
from quantum.core.env import QCLI_DIR


CONFIG_DIR = Path(QCLI_DIR) / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Default scoring weights (from the plan)
DEFAULT_SCORING_WEIGHTS = {
    "version_in_range": 0.30,
    "arch_match": 0.25,
    "service_match": 0.20,
    "mitigation_absent": 0.10,
    "reliability_prior": 0.10,
    "root_bonus": 0.05,
    "crash_prior_penalty": 0.15,
}

# Default settings
DEFAULT_SETTINGS = {
    "scoring_weights": DEFAULT_SCORING_WEIGHTS,
    "confidence_tiers": {
        "confirmed": 85,
        "likely": 60,
        "plausible": 35,
        "speculative": 0,
    },
    "transport_ladder": [
        "https",
        "doh",
        "dns",
        "tcp",
        "websocket",
        "dead_drop",
    ],
    "transport_timeouts": {
        "https": 10,
        "doh": 15,
        "dns": 20,
        "tcp": 10,
        "websocket": 15,
        "dead_drop": 60,
    },
    "beacon_interval": 60,
    "beacon_jitter": 0.15,
    "telemetry_interval": 1,
    "telemetry_retention_days": 30,
    "loot_retention_days": 90,
    "purge_after_days": {
        "telemetry": 30,
        "tasks": 90,
        "artifacts": 90,
        "events": 7,
        "loot_fts": 90,
    },
    "web_port": 8443,
    "web_host": "0.0.0.0",
    "web_ssl": True,
    "theme": "dark",
    "density": "normal",
    "opsec_profile": "balanced",
    "auto_persist": True,
    "auto_harvest": False,
    "auto_scan": False,
    "max_concurrent_tasks": 5,
    "task_timeout_default": 120,
    "kill_switch_modes": ["ghost", "hard", "scorched", "deferred", "dead_man"],
    "enable_web": True,
    "enable_api": True,
    "cors_origins": ["*"],
    "rate_limit": 100,
    "log_level": "INFO",
    "audit_log": True,
}


@dataclass
class ScoringWeights:
    """Exploit scoring weights - tunable at runtime."""
    version_in_range: float = 0.30
    arch_match: float = 0.25
    service_match: float = 0.20
    mitigation_absent: float = 0.10
    reliability_prior: float = 0.10
    root_bonus: float = 0.05
    crash_prior_penalty: float = 0.15

    def to_dict(self) -> Dict[str, float]:
        return {
            "version_in_range": self.version_in_range,
            "arch_match": self.arch_match,
            "service_match": self.service_match,
            "mitigation_absent": self.mitigation_absent,
            "reliability_prior": self.reliability_prior,
            "root_bonus": self.root_bonus,
            "crash_prior_penalty": self.crash_prior_penalty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "ScoringWeights":
        return cls(
            version_in_range=data.get("version_in_range", 0.30),
            arch_match=data.get("arch_match", 0.25),
            service_match=data.get("service_match", 0.20),
            mitigation_absent=data.get("mitigation_absent", 0.10),
            reliability_prior=data.get("reliability_prior", 0.10),
            root_bonus=data.get("root_bonus", 0.05),
            crash_prior_penalty=data.get("crash_prior_penalty", 0.15),
        )


class Config:
    """Thread-safe configuration manager with database backend."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._loaded = False
        self._scoring_weights = ScoringWeights()

    def load(self) -> None:
        """Load settings from database and file."""
        with self._lock:
            if self._loaded:
                return

            # Load from database
            rows = execute("SELECT k, v FROM settings")
            for row in rows:
                try:
                    self._cache[row["k"]] = json.loads(row["v"])
                except json.JSONDecodeError:
                    self._cache[row["k"]] = row["v"]

            # Load from file as fallback/override
            if SETTINGS_FILE.exists():
                try:
                    with open(SETTINGS_FILE) as f:
                        file_settings = json.load(f)
                        self._cache.update(file_settings)
                except Exception:
                    pass

            # Apply defaults for missing keys
            for key, default in DEFAULT_SETTINGS.items():
                if key not in self._cache:
                    self._cache[key] = default

            # Load scoring weights
            if "scoring_weights" in self._cache:
                self._scoring_weights = ScoringWeights.from_dict(self._cache["scoring_weights"])

            self._loaded = True

    def save(self) -> None:
        """Save all settings to database and file."""
        with self._lock:
            with transaction() as conn:
                for key, value in self._cache.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO settings (k, v) VALUES (?, ?)",
                        (key, json.dumps(value))
                    )

            # Also write to file for portability
            try:
                with open(SETTINGS_FILE, "w") as f:
                    json.dump(self._cache, f, indent=2)
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self._lock:
            if not self._loaded:
                self.load()
            return self._cache.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set a setting value."""
        with self._lock:
            if not self._loaded:
                self.load()
            self._cache[key] = value
            if persist:
                self.save()

    def get_scoring_weights(self) -> ScoringWeights:
        """Get current scoring weights."""
        with self._lock:
            if not self._loaded:
                self.load()
            return self._scoring_weights

    def set_scoring_weights(self, weights: ScoringWeights, persist: bool = True) -> None:
        """Update scoring weights."""
        with self._lock:
            self._scoring_weights = weights
            self._cache["scoring_weights"] = weights.to_dict()
            if persist:
                self.save()

    def get_confidence_tiers(self) -> Dict[str, int]:
        """Get confidence tier thresholds."""
        return self.get("confidence_tiers", DEFAULT_SETTINGS["confidence_tiers"])

    def get_transport_ladder(self) -> List[str]:
        """Get transport failover ladder."""
        return self.get("transport_ladder", DEFAULT_SETTINGS["transport_ladder"])

    def get_transport_timeout(self, transport: str) -> int:
        """Get timeout for a specific transport."""
        timeouts = self.get("transport_timeouts", DEFAULT_SETTINGS["transport_timeouts"])
        return timeouts.get(transport, 30)

    def get_purge_after_days(self, table: str) -> int:
        """Get purge-after-days for a table."""
        purges = self.get("purge_after_days", DEFAULT_SETTINGS["purge_after_days"])
        return purges.get(table, 90)

    def export(self) -> Dict[str, Any]:
        """Export all settings as a dictionary."""
        with self._lock:
            if not self._loaded:
                self.load()
            return dict(self._cache)

    def import_settings(self, settings: Dict[str, Any], persist: bool = True) -> None:
        """Import settings from a dictionary."""
        with self._lock:
            self._cache.update(settings)
            if "scoring_weights" in settings:
                self._scoring_weights = ScoringWeights.from_dict(settings["scoring_weights"])
            if persist:
                self.save()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        with self._lock:
            self._cache = dict(DEFAULT_SETTINGS)
            self._scoring_weights = ScoringWeights()
            self.save()


# Global config instance
CONFIG = Config()


# Convenience functions

def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting (shorthand)."""
    return CONFIG.get(key, default)


def set_setting(key: str, value: Any, persist: bool = True) -> None:
    """Set a setting (shorthand)."""
    CONFIG.set(key, value, persist)


def get_scoring_weights() -> ScoringWeights:
    """Get scoring weights (shorthand)."""
    return CONFIG.get_scoring_weights()


def set_scoring_weights(weights: ScoringWeights, persist: bool = True) -> None:
    """Set scoring weights (shorthand)."""
    CONFIG.set_scoring_weights(weights, persist)