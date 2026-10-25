"""Device state machine with lifecycle transitions and guards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set
import time

from quantum.core.db import execute, execute_one, execute_write, transaction
from quantum.core.ids import new_device_id, correlation_id
from quantum.core.bus import BUS, publish_device_event


class DeviceState(str, Enum):
    """Device lifecycle states."""
    DISCOVERED = "DISCOVERED"      # Initial detection
    ENUMERATED = "ENUMERATED"      # Basic info gathered
    FINGERPRINTED = "FINGERPRINTED" # Deep fingerprint complete
    SCANNING = "SCANNING"          # Vuln scan in progress
    SCAN_COMPLETE = "SCAN_COMPLETE" # Scan done, exploits ranked
    EXPLOITING = "EXPLOITING"      # Exploit execution in progress
    COMPROMISED = "COMPROMISED"    # Exploit successful, shell obtained
    PERSISTED = "PERSISTED"        # Persistence installed
    POST_EX = "POST_EX"            # Post-exploitation modules running
    HARVESTING = "HARVESTING"      # Data harvesting in progress
    PIVOTING = "PIVOTING"          # Lateral movement in progress
    GHOST = "GHOST"                # Silent mode (killswitch ghost)
    DEAD = "DEAD"                  # Killswitch hard/scorched executed
    STALE = "STALE"                # No beacon for extended period


# Valid state transitions
VALID_TRANSITIONS: Dict[DeviceState, Set[DeviceState]] = {
    DeviceState.DISCOVERED: {DeviceState.ENUMERATED, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.ENUMERATED: {DeviceState.FINGERPRINTED, DeviceState.SCANNING, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.FINGERPRINTED: {DeviceState.SCANNING, DeviceState.EXPLOITING, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.SCANNING: {DeviceState.SCAN_COMPLETE, DeviceState.FINGERPRINTED, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.SCAN_COMPLETE: {DeviceState.EXPLOITING, DeviceState.FINGERPRINTED, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.EXPLOITING: {DeviceState.COMPROMISED, DeviceState.FINGERPRINTED, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.COMPROMISED: {DeviceState.PERSISTED, DeviceState.POST_EX, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.PERSISTED: {DeviceState.POST_EX, DeviceState.GHOST, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.POST_EX: {DeviceState.HARVESTING, DeviceState.PIVOTING, DeviceState.GHOST, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.HARVESTING: {DeviceState.POST_EX, DeviceState.PIVOTING, DeviceState.GHOST, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.PIVOTING: {DeviceState.POST_EX, DeviceState.GHOST, DeviceState.STALE, DeviceState.DEAD},
    DeviceState.GHOST: {DeviceState.ENUMERATED, DeviceState.DEAD},
    DeviceState.DEAD: set(),  # Terminal state
    DeviceState.STALE: {DeviceState.ENUMERATED, DeviceState.DEAD},
}


@dataclass
class StateTransition:
    """Record of a state transition."""
    device_id: str
    from_state: DeviceState
    to_state: DeviceState
    reason: str
    ts: float = time.time()
    correlation_id: str = ""


class StateMachine:
    """Manages device state transitions with validation and event emission."""

    def __init__(self):
        self._device_states: Dict[str, DeviceState] = {}
        self._load_states()

    def _load_states(self) -> None:
        """Load current states from database."""
        rows = execute("SELECT id, state FROM devices")
        for row in rows:
            try:
                self._device_states[row["id"]] = DeviceState(row["state"])
            except ValueError:
                self._device_states[row["id"]] = DeviceState.DISCOVERED

    def get_state(self, device_id: str) -> DeviceState:
        """Get current state of a device."""
        return self._device_states.get(device_id, DeviceState.DISCOVERED)

    def can_transition(self, device_id: str, to_state: DeviceState) -> bool:
        """Check if a transition is valid."""
        current = self.get_state(device_id)
        return to_state in VALID_TRANSITIONS.get(current, set())

    def transition(
        self,
        device_id: str,
        to_state: DeviceState,
        reason: str = "",
        corr_id: Optional[str] = None
    ) -> bool:
        """Attempt a state transition."""
        current = self.get_state(device_id)

        if not self.can_transition(device_id, to_state):
            return False

        cid = corr_id or correlation_id()

        # Record transition in database
        with transaction() as conn:
            conn.execute(
                """INSERT INTO transitions (device_id, from_state, to_state, reason, ts)
                   VALUES (?, ?, ?, ?, ?)""",
                (device_id, current.value, to_state.value, reason, time.time())
            )
            conn.execute(
                "UPDATE devices SET state = ?, updated = ? WHERE id = ?",
                (to_state.value, time.time(), device_id)
            )

        # Update cache
        self._device_states[device_id] = to_state

        # Emit event
        publish_device_event(device_id, "state_change", {
            "from_state": current.value,
            "to_state": to_state.value,
            "reason": reason,
            "correlation_id": cid,
        })

        return True

    def force_transition(
        self,
        device_id: str,
        to_state: DeviceState,
        reason: str = "forced",
        corr_id: Optional[str] = None
    ) -> bool:
        """Force a state transition (bypasses validation)."""
        current = self.get_state(device_id)
        cid = corr_id or correlation_id()

        with transaction() as conn:
            conn.execute(
                """INSERT INTO transitions (device_id, from_state, to_state, reason, ts)
                   VALUES (?, ?, ?, ?, ?)""",
                (device_id, current.value, to_state.value, reason, time.time())
            )
            conn.execute(
                "UPDATE devices SET state = ?, updated = ? WHERE id = ?",
                (to_state.value, time.time(), device_id)
            )

        self._device_states[device_id] = to_state

        publish_device_event(device_id, "state_change", {
            "from_state": current.value,
            "to_state": to_state.value,
            "reason": reason,
            "correlation_id": cid,
            "forced": True,
        })

        return True

    def get_history(self, device_id: str, limit: int = 50) -> List[StateTransition]:
        """Get state transition history for a device."""
        rows = execute(
            """SELECT from_state, to_state, reason, ts FROM transitions
               WHERE device_id = ? ORDER BY ts DESC LIMIT ?""",
            (device_id, limit)
        )
        return [
            StateTransition(
                device_id=device_id,
                from_state=DeviceState(r["from_state"]),
                to_state=DeviceState(r["to_state"]),
                reason=r["reason"],
                ts=r["ts"]
            )
            for r in rows
        ]

    def get_devices_in_state(self, state: DeviceState) -> List[str]:
        """Get all device IDs in a given state."""
        return [did for did, s in self._device_states.items() if s == state]

    def mark_stale(self, device_id: str, threshold_seconds: int = 3600) -> bool:
        """Mark a device as stale if it hasn't been seen recently."""
        row = execute_one(
            "SELECT last_seen FROM devices WHERE id = ?", (device_id,)
        )
        if not row:
            return False

        last_seen = row["last_seen"]
        if time.time() - last_seen > threshold_seconds:
            return self.transition(device_id, DeviceState.STALE, "beacon timeout")
        return False

    def check_all_stale(self, threshold_seconds: int = 3600) -> int:
        """Check all devices for staleness. Returns count marked stale."""
        count = 0
        for device_id in list(self._device_states.keys()):
            if self.mark_stale(device_id, threshold_seconds):
                count += 1
        return count


# Global state machine instance (lazy initialization)
_STATE_MACHINE: Optional[StateMachine] = None


def get_state_machine() -> StateMachine:
    """Get or create the global state machine instance."""
    global _STATE_MACHINE
    if _STATE_MACHINE is None:
        _STATE_MACHINE = StateMachine()
    return _STATE_MACHINE


# Backward compatibility - STATE_MACHINE will be initialized on first access
class _StateMachineProxy:
    """Proxy that lazily initializes the state machine."""
    
    def __getattr__(self, name):
        return getattr(get_state_machine(), name)
    
    def __setattr__(self, name, value):
        if name == "_STATE_MACHINE":
            super().__setattr__(name, value)
        else:
            setattr(get_state_machine(), name, value)


STATE_MACHINE = _StateMachineProxy()


# Guard functions for state-dependent operations

def require_state(device_id: str, *allowed_states: DeviceState) -> bool:
    """Check if device is in one of the allowed states."""
    current = STATE_MACHINE.get_state(device_id)
    return current in allowed_states


def require_not_state(device_id: str, *forbidden_states: DeviceState) -> bool:
    """Check if device is NOT in any of the forbidden states."""
    current = STATE_MACHINE.get_state(device_id)
    return current not in forbidden_states


def require_compromised(device_id: str) -> bool:
    """Check if device is compromised or beyond."""
    current = STATE_MACHINE.get_state(device_id)
    return current in {
        DeviceState.COMPROMISED, DeviceState.PERSISTED,
        DeviceState.POST_EX, DeviceState.HARVESTING, DeviceState.PIVOTING
    }


def require_persisted(device_id: str) -> bool:
    """Check if device has persistence installed."""
    current = STATE_MACHINE.get_state(device_id)
    return current in {
        DeviceState.PERSISTED, DeviceState.POST_EX,
        DeviceState.HARVESTING, DeviceState.PIVOTING
    }


def require_alive(device_id: str) -> bool:
    """Check if device is not dead or ghost."""
    current = STATE_MACHINE.get_state(device_id)
    return current not in {DeviceState.DEAD, DeviceState.GHOST}


def require_root(device_id: str) -> bool:
    """Check if device has root (from database)."""
    row = execute_one("SELECT root FROM devices WHERE id = ?", (device_id,))
    return bool(row and row["root"])


# State-based operation routing

OPERATION_STATE_REQUIREMENTS = {
    "scan": [DeviceState.ENUMERATED, DeviceState.FINGERPRINTED, DeviceState.SCAN_COMPLETE],
    "exploit": [DeviceState.FINGERPRINTED, DeviceState.SCAN_COMPLETE],
    "persist": [DeviceState.COMPROMISED],
    "postex": [DeviceState.PERSISTED, DeviceState.POST_EX],
    "harvest": [DeviceState.PERSISTED, DeviceState.POST_EX, DeviceState.HARVESTING],
    "pivot": [DeviceState.PERSISTED, DeviceState.POST_EX, DeviceState.PIVOTING],
    "control": [DeviceState.COMPROMISED, DeviceState.PERSISTED, DeviceState.POST_EX,
                DeviceState.HARVESTING, DeviceState.PIVOTING],
    "killswitch": list(DeviceState),  # Always allowed
}


def can_perform_operation(device_id: str, operation: str) -> bool:
    """Check if an operation can be performed on a device in its current state."""
    allowed = OPERATION_STATE_REQUIREMENTS.get(operation, [])
    if not allowed:
        return True  # No restriction
    return STATE_MACHINE.get_state(device_id) in allowed