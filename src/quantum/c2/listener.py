"""quantum.c2.listener — unique listener deployment for exploit/payload engagements.

Each exploit or payload deployed from the Android app against a target gets its
own unique listener port. This allows simultaneous engagements against multiple
targets without port conflicts, and gives the operator per-engagement visibility
and control.

Architecture:
  - ListenerManager: allocates unique ports, tracks active listeners
  - Listener: individual HTTP/TCP listener for a specific engagement
  - Listeners are independent — stop one without affecting others
  - Each listener serves the deployed exploit/payload and receives callbacks
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from quantum.core.env import QCLI_DIR
from quantum.core.logging import log


class Listener:
    """A single unique listener for one exploit/payload engagement."""

    def __init__(self, port, name, target, exploit_type, payload_path=None):
        self.port = port
        self.name = name
        self.target = target
        self.exploit_type = exploit_type
        self.payload_path = payload_path
        self.created_at = datetime.now().isoformat()
        self._server = None
        self._thread = None
        self._running = False
        self._hits = []

    def start(self):
        """Start the listener in a background thread."""
        if self._running:
            return False
        try:
            self._server = HTTPServer(("0.0.0.0", self.port), self._make_handler())
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            self._running = True
            log(f"Listener '{self.name}' started on :{self.port} (target: {self.target}, exploit: {self.exploit_type})", "C2")
            return True
        except Exception as e:
            log(f"Listener '{self.name}' bind :{self.port} failed: {e}", "WARN")
            return False

    def stop(self):
        """Stop the listener."""
        if not self._running:
            return
        try:
            self._server.shutdown()
            self._server.server_close()
            self._running = False
            log(f"Listener '{self.name}' on :{self.port} stopped", "C2")
        except Exception as e:
            log(f"Listener '{self.name}' stop error: {e}", "WARN")

    def status(self):
        """Return listener status dict."""
        return {
            "port": self.port,
            "name": self.name,
            "target": self.target,
            "exploit_type": self.exploit_type,
            "payload_path": self.payload_path,
            "created_at": self.created_at,
            "running": self._running,
            "hits": len(self._hits),
        }

    def _make_handler(self):
        """Create the HTTP handler class for this listener."""
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                listener._hits.append({
                    "method": "GET",
                    "path": self.path,
                    "client": self.client_address[0],
                    "ts": datetime.now().isoformat(),
                })
                log(f"Listener '{listener.name}' hit: {self.client_address[0]} {self.path}", "C2")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                if self.path == "/":
                    self.wfile.write(b"<html><body>q</body></html>")
                elif listener.payload_path and self.path == "/payload":
                    try:
                        with open(listener.payload_path, "rb") as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/octet-stream")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    except Exception:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self.wfile.write(b"ok")

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
                listener._hits.append({
                    "method": "POST",
                    "path": self.path,
                    "client": self.client_address[0],
                    "body_len": len(body),
                    "ts": datetime.now().isoformat(),
                })
                log(f"Listener '{listener.name}' callback: {self.client_address[0]} POST {self.path} ({len(body)}B)", "C2")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, fmt, *args):
                pass

        return Handler


class ListenerManager:
    """Manages unique listeners for exploit/payload engagements.

    Allocates unique ports, tracks active listeners, and provides
    start/stop/status operations for each engagement.
    """

    # Port range for dynamic listener allocation
    PORT_RANGE = (9100, 9999)

    def __init__(self, state_file=None):
        self.state_file = state_file or os.path.join(QCLI_DIR, "listeners.json")
        self._listeners = {}
        self._next_port = self.PORT_RANGE[0]
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        """Load listener state from disk."""
        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            for port_str, info in data.items():
                port = int(port_str)
                listener = Listener(
                    port=port,
                    name=info.get("name", f"listener-{port}"),
                    target=info.get("target", "unknown"),
                    exploit_type=info.get("exploit", "unknown"),
                    payload_path=info.get("payload"),
                )
                self._listeners[port] = listener
            # Set next port to highest allocated + 1
            if self._listeners:
                self._next_port = max(self._listeners.keys()) + 1
        except Exception:
            pass

    def _save(self):
        """Save listener state to disk."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            data = {}
            for port, listener in self._listeners.items():
                info = listener.status()
                data[str(port)] = {
                    "name": info["name"],
                    "target": info["target"],
                    "exploit": info["exploit_type"],
                    "payload": info["payload_path"],
                }
            tmp = self.state_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp, self.state_file)
        except Exception as e:
            log(f"ListenerManager save failed: {e}", "WARN")

    def _allocate_port(self):
        """Allocate a unique port from the range."""
        with self._lock:
            port = self._next_port
            while port in self._listeners and port < self.PORT_RANGE[1]:
                port += 1
            if port >= self.PORT_RANGE[1]:
                raise RuntimeError("No available ports in range")
            self._next_port = port + 1
            return port

    def deploy(self, name, target, exploit_type, payload_path=None, port=None):
        """Deploy a new unique listener for an engagement.

        Args:
            name: Human-readable name for this engagement
            target: Target identifier (IP/hostname)
            exploit_type: Type of exploit (e.g., "badusb", "maldoc", "dohshell")
            payload_path: Optional path to payload file to serve
            port: Optional specific port (auto-allocated if None)

        Returns:
            Listener instance or None on failure
        """
        try:
            if port is None:
                port = self._allocate_port()
            else:
                port = int(port)
                if port in self._listeners:
                    log(f"Port {port} already in use, allocating new port", "WARN")
                    port = self._allocate_port()

            listener = Listener(port, name, target, exploit_type, payload_path)
            if listener.start():
                self._listeners[port] = listener
                self._save()
                return listener
            else:
                return None
        except Exception as e:
            log(f"Listener deploy failed: {e}", "WARN")
            return None

    def stop(self, port):
        """Stop a specific listener.

        Args:
            port: Port number of the listener to stop

        Returns:
            True if stopped, False if not found
        """
        listener = self._listeners.get(int(port))
        if listener:
            listener.stop()
            del self._listeners[int(port)]
            self._save()
            return True
        return False

    def stop_all(self):
        """Stop all active listeners."""
        for listener in self._listeners.values():
            listener.stop()
        self._listeners.clear()
        self._save()

    def get(self, port):
        """Get a specific listener by port.

        Args:
            port: Port number

        Returns:
            Listener instance or None
        """
        return self._listeners.get(int(port))

    def list_all(self):
        """List all listeners with their status.

        Returns:
            List of listener status dicts
        """
        return [listener.status() for listener in self._listeners.values()]

    def get_active(self):
        """Get only active (running) listeners.

        Returns:
            List of active listener status dicts
        """
        return [l.status() for l in self._listeners.values() if l.status()["running"]]

    def get_hits(self, port):
        """Get hit history for a specific listener.

        Args:
            port: Port number

        Returns:
            List of hit dicts
        """
        listener = self._listeners.get(int(port))
        if listener:
            return list(listener._hits)
        return []
