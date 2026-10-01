"""Autonomous defense triggers module.

Evaluates security events and triggers automated defensive responses.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from dataclasses import dataclass
from enum import Enum


class TriggerType(str, Enum):
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DATA_EXFIL = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALWARE_DETECTED = "malware_detected"
    ANOMALY_SCORE = "anomaly_score"
    THREAT_INTEL_HIT = "threat_intel_hit"


@dataclass
class TriggerRule:
    trigger_type: TriggerType
    threshold: float
    action: str
    enabled: bool = True
    description: str = ""


class AutonomousDefenseTriggers:
    """Manages and evaluates autonomous defense trigger rules."""

    DEFAULT_TRIGGERS: list[TriggerRule] = [
        TriggerRule(TriggerType.PORT_SCAN, threshold=50, action="block_ip",
                     description="More than 50 unique ports scanned in 5 minutes"),
        TriggerRule(TriggerType.BRUTE_FORCE, threshold=10, action="lock_account",
                     description="More than 10 failed login attempts in 2 minutes"),
        TriggerRule(TriggerType.DATA_EXFIL, threshold=100, action="alert_security",
                     description="More than 100MB data egress to unknown destination"),
        TriggerRule(TriggerType.LATERAL_MOVEMENT, threshold=5, action="isolate_network_segment",
                     description="5+ failed lateral movement attempts detected"),
        TriggerRule(TriggerType.PRIVILEGE_ESCALATION, threshold=3, action="terminate_session",
                     description="Multiple privilege escalation attempts detected"),
        TriggerRule(TriggerType.MALWARE_DETECTED, threshold=1, action="quarantine_endpoint",
                     description="Malware signature detected on endpoint"),
        TriggerRule(TriggerType.ANOMALY_SCORE, threshold=85, action="investigate_alert",
                     description="Anomaly score above 85 requires investigation"),
        TriggerRule(TriggerType.THREAT_INTEL_HIT, threshold=1, action="block_indicator",
                     description="Known malicious indicator matched in threat intel feed"),
    ]

    def __init__(self, config_path: str | None = None):
        self.triggers = list(self.DEFAULT_TRIGGERS)
        self._triggered: list[dict[str, Any]] = []
        self.config_path = config_path or os.path.expanduser("~/.quantum/triggers.json")

    def get_trigger_status(self) -> dict[str, Any]:
        """Return current trigger configuration status."""
        return {
            "total_triggers": len(self.triggers),
            "active_triggers": sum(1 for t in self.triggers if t.enabled),
            "disabled_triggers": sum(1 for t in self.triggers if not t.enabled),
            "triggered_events": len(self._triggered),
            "triggers": [
                {
                    "type": t.trigger_type.value,
                    "threshold": t.threshold,
                    "action": t.action,
                    "enabled": t.enabled,
                    "description": t.description,
                }
                for t in self.triggers
            ],
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def evaluate_event(self, event: dict[str, Any]) -> list[str]:
        """Evaluate a single event against all triggers.

        Returns list of actions that should be taken.
        """
        actions: list[str] = []
        event_type = event.get("event_type", "")
        confidence = event.get("confidence", 0)
        unique_ports = event.get("unique_ports", 0)
        source_ip = event.get("source_ip", "unknown")
        unique_ips = event.get("unique_source_ips", 0)

        for trigger in self.triggers:
            if not trigger.enabled:
                continue

            triggered = False

            if trigger.trigger_type == TriggerType.PORT_SCAN:
                if unique_ports >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.BRUTE_FORCE:
                if unique_ips >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.DATA_EXFIL:
                if event_type == "data_exfiltration" and confidence >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.LATERAL_MOVEMENT:
                if event_type == "lateral_movement" and unique_ports >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.PRIVILEGE_ESCALATION:
                if event_type == "privilege_escalation" and confidence >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.MALWARE_DETECTED:
                if event_type == "malware_detected":
                    triggered = True

            elif trigger.trigger_type == TriggerType.ANOMALY_SCORE:
                if confidence >= trigger.threshold:
                    triggered = True

            elif trigger.trigger_type == TriggerType.THREAT_INTEL_HIT:
                if event.get("threat_intel_match"):
                    triggered = True

            if triggered:
                actions.append(trigger.action)
                self._triggered.append({
                    "trigger_type": trigger.trigger_type.value,
                    "action": trigger.action,
                    "source_ip": source_ip,
                    "event": event,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "trigger_id": str(uuid.uuid4()),
                })

        return actions

    def enable_trigger(self, trigger_type: str) -> bool:
        """Enable a specific trigger type."""
        for trigger in self.triggers:
            if trigger.trigger_type.value == trigger_type:
                trigger.enabled = True
                return True
        return False

    def disable_trigger(self, trigger_type: str) -> bool:
        """Disable a specific trigger type."""
        for trigger in self.triggers:
            if trigger.trigger_type.value == trigger_type:
                trigger.enabled = False
                return True
        return False

    def update_threshold(self, trigger_type: str, new_threshold: float) -> bool:
        """Update the threshold for a specific trigger type."""
        for trigger in self.triggers:
            if trigger.trigger_type.value == trigger_type:
                trigger.threshold = new_threshold
                return True
        return False

    def get_triggered_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recently triggered events."""
        return self._triggered[-limit:]
