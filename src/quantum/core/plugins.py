"""Plugin loader for dynamic CLI commands, API routes, and UI cards."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from quantum.core.env import QCLI_DIR


PLUGINS_DIR = Path(QCLI_DIR) / "plugins"
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PluginCommand:
    """CLI command provided by a plugin."""
    name: str
    func: Callable
    help: str = ""
    args: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PluginRoute:
    """API route provided by a plugin."""
    path: str
    method: str
    handler: Callable
    auth_required: bool = True


@dataclass
class PluginCard:
    """UI card component provided by a plugin."""
    name: str
    component: str  # JavaScript component name
    lane: str  # Which dashboard lane/page
    config_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plugin:
    """Plugin metadata and exports."""
    name: str
    module: Any
    path: Path
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    commands: List[PluginCommand] = field(default_factory=list)
    routes: List[PluginRoute] = field(default_factory=list)
    cards: List[PluginCard] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    loaded: bool = False


class PluginManager:
    """Manages plugin discovery, loading, and registration."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._command_map: Dict[str, PluginCommand] = {}
        self._route_map: Dict[str, List[PluginRoute]] = {}  # path -> list of routes
        self._card_map: Dict[str, List[PluginCard]] = {}  # lane -> list of cards
        _loaded = False

    def discover(self) -> List[Path]:
        """Discover plugin files in the plugins directory."""
        plugins = []
        for path in PLUGINS_DIR.glob("*.py"):
            if path.name.startswith("_"):
                continue
            plugins.append(path)
        for path in PLUGINS_DIR.glob("*/__init__.py"):
            plugins.append(path.parent)
        return plugins

    def load_plugin(self, path: Path) -> Optional[Plugin]:
        """Load a single plugin from a file or directory."""
        if path.is_dir():
            module_path = path / "__init__.py"
            plugin_name = path.name
        else:
            module_path = path
            plugin_name = path.stem

        if not module_path.exists():
            return None

        # Load module
        spec = importlib.util.spec_from_file_location(f"quantum_plugin_{plugin_name}", module_path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"quantum_plugin_{plugin_name}"] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[plugin] Failed to load {plugin_name}: {e}")
            return None

        # Extract plugin metadata
        plugin = Plugin(
            name=plugin_name,
            module=module,
            path=path,
            version=getattr(module, "__version__", "1.0.0"),
            description=getattr(module, "__description__", ""),
            author=getattr(module, "__author__", ""),
            dependencies=getattr(module, "__dependencies__", []),
        )

        # Register commands
        if hasattr(module, "COMMANDS"):
            for cmd_def in module.COMMANDS:
                if isinstance(cmd_def, dict):
                    cmd = PluginCommand(
                        name=cmd_def["name"],
                        func=cmd_def["func"],
                        help=cmd_def.get("help", ""),
                        args=cmd_def.get("args", []),
                    )
                else:
                    # Assume it's a function with metadata attributes
                    func = cmd_def
                    cmd = PluginCommand(
                        name=getattr(func, "__command_name__", func.__name__),
                        func=func,
                        help=getattr(func, "__command_help__", ""),
                        args=getattr(func, "__command_args__", []),
                    )
                plugin.commands.append(cmd)
                self._command_map[cmd.name] = cmd

        # Register routes
        if hasattr(module, "ROUTES"):
            for route_def in module.ROUTES:
                route = PluginRoute(
                    path=route_def["path"],
                    method=route_def.get("method", "GET"),
                    handler=route_def["handler"],
                    auth_required=route_def.get("auth_required", True),
                )
                plugin.routes.append(route)
                if route.path not in self._route_map:
                    self._route_map[route.path] = []
                self._route_map[route.path].append(route)

        # Register cards
        if hasattr(module, "CARDS"):
            for card_def in module.CARDS:
                card = PluginCard(
                    name=card_def["name"],
                    component=card_def["component"],
                    lane=card_def.get("lane", "custom"),
                    config_schema=card_def.get("config_schema", {}),
                )
                plugin.cards.append(card)
                if card.lane not in self._card_map:
                    self._card_map[card.lane] = []
                self._card_map[card.lane].append(card)

        # Call init hook if present
        if hasattr(module, "plugin_init"):
            try:
                module.plugin_init()
            except Exception as e:
                print(f"[plugin] Init hook failed for {plugin_name}: {e}")

        self._plugins[plugin_name] = plugin
        plugin.loaded = True
        return plugin

    def load_all(self) -> List[Plugin]:
        """Load all discovered plugins."""
        loaded = []
        for path in self.discover():
            plugin = self.load_plugin(path)
            if plugin:
                loaded.append(plugin)
        return loaded

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]

        # Call cleanup hook
        if hasattr(plugin.module, "plugin_cleanup"):
            try:
                plugin.module.plugin_cleanup()
            except Exception:
                pass

        # Remove commands
        for cmd in plugin.commands:
            self._command_map.pop(cmd.name, None)

        # Remove routes
        for route in plugin.routes:
            if route.path in self._route_map:
                self._route_map[route.path] = [
                    r for r in self._route_map[route.path] if r.handler != route.handler
                ]
                if not self._route_map[route.path]:
                    del self._route_map[route.path]

        # Remove cards
        for card in plugin.cards:
            if card.lane in self._card_map:
                self._card_map[card.lane] = [
                    c for c in self._card_map[card.lane] if c.name != card.name
                ]
                if not self._card_map[card.lane]:
                    del self._card_map[card.lane]

        # Remove from sys.modules
        mod_name = f"quantum_plugin_{name}"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        del self._plugins[name]
        return True

    def get_command(self, name: str) -> Optional[PluginCommand]:
        """Get a command by name."""
        return self._command_map.get(name)

    def get_commands(self) -> List[PluginCommand]:
        """Get all registered commands."""
        return list(self._command_map.values())

    def get_routes(self, path: str) -> List[PluginRoute]:
        """Get routes for a path."""
        return self._route_map.get(path, [])

    def get_all_routes(self) -> List[PluginRoute]:
        """Get all registered routes."""
        routes = []
        for route_list in self._route_map.values():
            routes.extend(route_list)
        return routes

    def get_cards(self, lane: str) -> List[PluginCard]:
        """Get cards for a dashboard lane."""
        return self._card_map.get(lane, [])

    def get_all_cards(self) -> Dict[str, List[PluginCard]]:
        """Get all cards grouped by lane."""
        return dict(self._card_map)

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[Plugin]:
        """List all loaded plugins."""
        return list(self._plugins.values())

    def reload_plugin(self, name: str) -> Optional[Plugin]:
        """Reload a plugin."""
        if name in self._plugins:
            path = self._plugins[name].path
            self.unload_plugin(name)
            return self.load_plugin(path)
        return None


# Global plugin manager
PLUGIN_MANAGER = PluginManager()


# Decorators for plugin authors

def command(name: str = "", help: str = "", args: List[Dict] = None):
    """Decorator to mark a function as a CLI command."""
    def decorator(func: Callable) -> Callable:
        func.__command_name__ = name or func.__name__
        func.__command_help__ = help
        func.__command_args__ = args or []
        return func
    return decorator


def route(path: str, method: str = "GET", auth_required: bool = True):
    """Decorator to mark a function as an API route."""
    def decorator(func: Callable) -> Callable:
        func.__route_path__ = path
        func.__route_method__ = method
        func.__route_auth__ = auth_required
        return func
    return decorator


def card(name: str, component: str, lane: str = "custom", config_schema: Dict = None):
    """Decorator to mark a class/function as a UI card."""
    def decorator(obj: Any) -> Any:
        obj.__card_name__ = name
        obj.__card_component__ = component
        obj.__card_lane__ = lane
        obj.__card_config_schema__ = config_schema or {}
        return obj
    return decorator


# Plugin API that gets exposed to plugins

class PluginAPI:
    """API available to plugins for interacting with Quantum-CLI core."""

    def __init__(self):
        self.bus = None  # Set after bus starts
        self.db = None   # Set after DB init
        self.config = None
        self.state_machine = None

    def publish_event(self, topic: str, payload: Dict, device_id: str = None):
        """Publish an event to the bus."""
        if self.bus:
            self.bus.publish(topic, payload, device_id)

    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        if self.bus:
            return self.bus.subscribe(topic)
        return None

    def get_device(self, device_id: str):
        """Get device from registry."""
        if self.db:
            from quantum.rat.registry import get_device
            return get_device(device_id)
        return None

    def queue_task(self, device_id: str, module: str, args: Dict):
        """Queue a task for a device."""
        from quantum.rat.tasks import queue_task
        return queue_task(device_id, module, args)


# Singleton API instance
PLUGIN_API = PluginAPI()


def init_plugin_system(bus, db, config, state_machine):
    """Initialize the plugin system with core services."""
    PLUGIN_API.bus = bus
    PLUGIN_API.db = db
    PLUGIN_API.config = config
    PLUGIN_API.state_machine = state_machine
    PLUGIN_MANAGER.load_all()


def create_example_plugin():
    """Create an example plugin file."""
    example = PLUGINS_DIR / "example_plugin.py"
    if example.exists():
        return

    content = '''"""
Example Quantum-CLI Plugin

This plugin demonstrates how to extend Quantum-CLI with custom commands,
API routes, and UI cards.
"""

from quantum.core.plugins import command, route, card, PluginAPI


__version__ = "1.0.0"
__description__ = "Example plugin showing the plugin API"
__author__ = "Quantum-CLI Team"
__dependencies__ = []


@command(name="hello", help="Say hello from the plugin")
def hello_command(name: str = "Operator") -> dict:
    """Simple command that returns a greeting."""
    return {"message": f"Hello, {name}! This is from a plugin."}


@command(name="plugin-status", help="Show plugin system status")
def status_command() -> dict:
    """Show status of all loaded plugins."""
    from quantum.core.plugins import PLUGIN_MANAGER
    plugins = PLUGIN_MANAGER.list_plugins()
    return {
        "loaded_plugins": len(plugins),
        "plugins": [{"name": p.name, "version": p.version, "commands": len(p.commands)} for p in plugins]
    }


@route("/api/v1/plugin/example/echo", method="POST")
def echo_route(data: dict) -> dict:
    """Echo endpoint for testing."""
    return {"echo": data, "from": "plugin"}


@route("/api/v1/plugin/example/config", method="GET")
def config_route() -> dict:
    """Return plugin configuration."""
    return {"setting1": "value1", "setting2": "value2"}


@card(name="ExampleCard", component="ExampleCard", lane="custom", config_schema={"title": {"type": "string"}})
class ExampleCard:
    """Example UI card component."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def render(self) -> dict:
        """Return data for the card."""
        return {
            "title": self.config.get("title", "Example Plugin Card"),
            "content": "This card was loaded from a plugin!",
            "timestamp": __import__("time").time(),
        }


def plugin_init():
    """Called when plugin is loaded."""
    print("[example_plugin] Loaded successfully")


def plugin_cleanup():
    """Called when plugin is unloaded."""
    print("[example_plugin] Unloaded")
'''

    example.write_text(content)
    return example


# Auto-create example plugin on first run
if not (PLUGINS_DIR / "example_plugin.py").exists():
    create_example_plugin()