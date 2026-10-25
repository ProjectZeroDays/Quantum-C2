"""Device lifecycle states and transitions."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set

from quantum.core.state import DeviceState, VALID_TRANSITIONS


# Re-export for convenience
__all__ = [
    "DeviceState",
    "VALID_TRANSITIONS",
    "TERMINAL_STATES",
    "ACTIVE_STATES",
    "COMPROMISED_STATES",
    "state_description",
    "state_priority",
]


# State categories
TERMINAL_STATES = {DeviceState.DEAD}
ACTIVE_STATES = {
    DeviceState.ENUMERATED,
    DeviceState.FINGERPRINTED,
    DeviceState.SCANNING,
    DeviceState.SCAN_COMPLETE,
    DeviceState.EXPLOITING,
    DeviceState.COMPROMISED,
    DeviceState.PERSISTED,
    DeviceState.POST_EX,
    DeviceState.HARVESTING,
    DeviceState.PIVOTING,
}
COMPROMISED_STATES = {
    DeviceState.COMPROMISED,
    DeviceState.PERSISTED,
    DeviceState.POST_EX,
    DeviceState.HARVESTING,
    DeviceState.PIVOTING,
}


# Human-readable descriptions
STATE_DESCRIPTIONS = {
    DeviceState.DISCOVERED: "Device detected, awaiting enumeration",
    DeviceState.ENUMERATED: "Basic information gathered",
    DeviceState.FINGERPRINTED: "Deep fingerprint complete, vulnerabilities identified",
    DeviceState.SCANNING: "Vulnerability scan in progress",
    DeviceState.SCAN_COMPLETE: "Scan complete, exploits ranked and ready",
    DeviceState.EXPLOITING: "Exploit execution in progress",
    DeviceState.COMPROMISED: "Exploit successful, shell/access obtained",
    DeviceState.PERSISTED: "Persistence installed, surviving reboots",
    DeviceState.POST_EX: "Post-exploitation modules running",
    DeviceState.HARVESTING: "Data harvesting in progress",
    DeviceState.PIVOTING: "Lateral movement / pivoting in progress",
    DeviceState.GHOST: "Silent mode - beacon stopped, persistence retained",
    DeviceState.DEAD: "Killswitch executed - implant removed",
    DeviceState.STALE: "No beacon received for extended period",
}


def state_description(state: DeviceState) -> str:
    """Get human-readable description of a state."""
    return STATE_DESCRIPTIONS.get(state, "Unknown state")


# Priority for sorting (higher = more critical/advanced)
STATE_PRIORITY = {
    DeviceState.DEAD: 0,
    DeviceState.STALE: 1,
    DeviceState.DISCOVERED: 2,
    DeviceState.ENUMERATED: 3,
    DeviceState.FINGERPRINTED: 4,
    DeviceState.SCANNING: 5,
    DeviceState.SCAN_COMPLETE: 6,
    DeviceState.EXPLOITING: 7,
    DeviceState.COMPROMISED: 8,
    DeviceState.PERSISTED: 9,
    DeviceState.POST_EX: 10,
    DeviceState.HARVESTING: 11,
    DeviceState.PIVOTING: 12,
    DeviceState.GHOST: 13,
}


def state_priority(state: DeviceState) -> int:
    """Get priority value for a state (for sorting)."""
    return STATE_PRIORITY.get(state, 0)


# State colors for UI
STATE_COLORS = {
    DeviceState.DISCOVERED: "#6b7280",      # gray
    DeviceState.ENUMERATED: "#3b82f6",      # blue
    DeviceState.FINGERPRINTED: "#8b5cf6",   # purple
    DeviceState.SCANNING: "#f59e0b",        # amber
    DeviceState.SCAN_COMPLETE: "#10b981",   # emerald
    DeviceState.EXPLOITING: "#ef4444",      # red
    DeviceState.COMPROMISED: "#dc2626",     # red-600
    DeviceState.PERSISTED: "#7c2d12",       # orange-900
    DeviceState.POST_EX: "#991b1b",         # red-800
    DeviceState.HARVESTING: "#b91c1c",      # red-700
    DeviceState.PIVOTING: "#be123c",        # rose-700
    DeviceState.GHOST: "#6366f1",           # indigo
    DeviceState.DEAD: "#1f2937",            # gray-900
    DeviceState.STALE: "#9ca3af",           # gray-400
}


def state_color(state: DeviceState) -> str:
    """Get color for a state."""
    return STATE_COLORS.get(state, "#6b7280")


# State icons for UI
STATE_ICONS = {
    DeviceState.DISCOVERED: "🔍",
    DeviceState.ENUMERATED: "📋",
    DeviceState.FINGERPRINTED: "🔬",
    DeviceState.SCANNING: "🔎",
    DeviceState.SCAN_COMPLETE: "✅",
    DeviceState.EXPLOITING: "💥",
    DeviceState.COMPROMISED: "🎯",
    DeviceState.PERSISTED: "🔒",
    DeviceState.POST_EX: "📦",
    DeviceState.HARVESTING: "💾",
    DeviceState.PIVOTING: "🔄",
    DeviceState.GHOST: "👻",
    DeviceState.DEAD: "💀",
    DeviceState.STALE: "💤",
}


def state_icon(state: DeviceState) -> str:
    """Get icon for a state."""
    return STATE_ICONS.get(state, "❓")


# Valid next actions per state
STATE_ACTIONS = {
    DeviceState.DISCOVERED: ["enumerate", "scan", "fingerprint"],
    DeviceState.ENUMERATED: ["fingerprint", "scan", "exploit"],
    DeviceState.FINGERPRINTED: ["scan", "exploit", "persist"],
    DeviceState.SCANNING: ["wait", "cancel"],
    DeviceState.SCAN_COMPLETE: ["exploit", "re-scan", "customize_payload"],
    DeviceState.EXPLOITING: ["wait", "cancel"],
    DeviceState.COMPROMISED: ["persist", "postex", "harvest", "pivot", "control"],
    DeviceState.PERSISTED: ["postex", "harvest", "pivot", "control", "ghost"],
    DeviceState.POST_EX: ["harvest", "pivot", "control", "ghost", "killswitch"],
    DeviceState.HARVESTING: ["pivot", "control", "ghost", "killswitch"],
    DeviceState.PIVOTING: ["postex", "control", "ghost", "killswitch"],
    DeviceState.GHOST: ["wake", "killswitch"],
    DeviceState.DEAD: [],
    DeviceState.STALE: ["reconnect", "killswitch"],
}


def get_available_actions(state: DeviceState) -> list:
    """Get available actions for a state."""
    return STATE_ACTIONS.get(state, [])


# Transition validation
def is_valid_transition(from_state: DeviceState, to_state: DeviceState) -> bool:
    """Check if a transition is valid."""
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_valid_transitions(from_state: DeviceState) -> Set[DeviceState]:
    """Get all valid transitions from a state."""
    return VALID_TRANSITIONS.get(from_state, set())


# State groups for UI filtering
STATE_GROUPS = {
    "new": [DeviceState.DISCOVERED, DeviceState.ENUMERATED],
    "active": [DeviceState.FINGERPRINTED, DeviceState.SCANNING, DeviceState.SCAN_COMPLETE,
               DeviceState.EXPLOITING, DeviceState.COMPROMISED, DeviceState.PERSISTED,
               DeviceState.POST_EX, DeviceState.HARVESTING, DeviceState.PIVOTING],
    "special": [DeviceState.GHOST],
    "inactive": [DeviceState.STALE, DeviceState.DEAD],
}


def get_state_group(state: DeviceState) -> str:
    """Get the group a state belongs to."""
    for group, states in STATE_GROUPS.items():
        if state in states:
            return group
    return "unknown"