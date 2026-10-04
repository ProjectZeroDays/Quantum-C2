"""Tests for quantum.c2.listener — unique listener deployment."""
import pytest
from quantum.c2.listener import Listener, ListenerManager


class TestListener:
    def test_create_listener(self):
        listener = Listener(9100, "test-engagement", "192.168.1.100", "badusb")
        assert listener.port == 9100
        assert listener.name == "test-engagement"
        assert listener.target == "192.168.1.100"
        assert listener.exploit_type == "badusb"

    def test_listener_status(self):
        listener = Listener(9101, "test", "target", "maldoc")
        status = listener.status()
        assert status["port"] == 9101
        assert status["name"] == "test"
        assert status["running"] is False

    def test_listener_start_stop(self):
        listener = Listener(9102, "test", "target", "badusb")
        assert listener.start() is True
        assert listener._running is True
        listener.stop()
        assert listener._running is False

    def test_listener_payload_path(self):
        listener = Listener(9103, "test", "target", "dohshell", payload_path="/tmp/payload.bin")
        assert listener.payload_path == "/tmp/payload.bin"
        status = listener.status()
        assert status["payload_path"] == "/tmp/payload.bin"


class TestListenerManager:
    def test_create_manager(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        assert isinstance(mgr, ListenerManager)

    def test_deploy_listener(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        listener = mgr.deploy("test-engagement", "192.168.1.100", "badusb")
        assert listener is not None
        assert listener.port >= 9100
        assert listener.name == "test-engagement"
        assert listener.target == "192.168.1.100"
        assert listener.exploit_type == "badusb"
        assert listener._running is True
        mgr.stop_all()

    def test_deploy_multiple_unique_ports(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        l1 = mgr.deploy("engagement-1", "192.168.1.100", "badusb")
        l2 = mgr.deploy("engagement-2", "192.168.1.101", "maldoc")
        l3 = mgr.deploy("engagement-3", "192.168.1.102", "dohshell")
        assert l1 is not None
        assert l2 is not None
        assert l3 is not None
        ports = {l1.port, l2.port, l3.port}
        assert len(ports) == 3  # All unique
        mgr.stop_all()

    def test_stop_listener(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        listener = mgr.deploy("test", "target", "badusb")
        assert listener is not None
        port = listener.port
        assert mgr.stop(port) is True
        assert mgr.get(port) is None

    def test_stop_all(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        mgr.deploy("e1", "t1", "badusb")
        mgr.deploy("e2", "t2", "maldoc")
        mgr.deploy("e3", "t3", "dohshell")
        mgr.stop_all()
        assert mgr.list_all() == []

    def test_list_all(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        mgr.deploy("e1", "t1", "badusb")
        mgr.deploy("e2", "t2", "maldoc")
        all_listeners = mgr.list_all()
        assert len(all_listeners) == 2
        mgr.stop_all()

    def test_get_active(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        mgr.deploy("e1", "t1", "badusb")
        mgr.deploy("e2", "t2", "maldoc")
        active = mgr.get_active()
        assert len(active) == 2
        mgr.stop_all()

    def test_get_hits(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        listener = mgr.deploy("test", "target", "badusb")
        assert listener is not None
        hits = mgr.get_hits(listener.port)
        assert isinstance(hits, list)
        mgr.stop_all()

    def test_port_allocation_range(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        listener = mgr.deploy("test", "target", "badusb")
        assert listener is not None
        assert 9100 <= listener.port <= 9999
        mgr.stop_all()

    def test_deploy_with_specific_port(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        listener = mgr.deploy("test", "target", "badusb", port=9500)
        assert listener is not None
        assert listener.port == 9500
        mgr.stop_all()

    def test_deploy_conflict_allocates_new(self):
        mgr = ListenerManager(state_file="/tmp/test_listeners.json")
        l1 = mgr.deploy("e1", "t1", "badusb", port=9500)
        l2 = mgr.deploy("e2", "t2", "maldoc", port=9500)
        assert l1 is not None
        assert l2 is not None
        assert l1.port != l2.port
        mgr.stop_all()
