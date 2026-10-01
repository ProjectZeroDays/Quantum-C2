"""Tests for quantum.control.ddos — DDoS dashboard."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.control.ddos import (
    ddos_dashboard_state,
    list_ddos_tools,
    list_ddos_techniques,
    generate_ddos_config,
)


class TestDdosDashboardState:
    def test_returns_dict(self):
        result = ddos_dashboard_state()
        assert isinstance(result, dict)

    def test_has_tools(self):
        result = ddos_dashboard_state()
        assert "tools" in result
        assert isinstance(result["tools"], dict)

    def test_has_techniques(self):
        result = ddos_dashboard_state()
        assert "techniques" in result
        assert isinstance(result["techniques"], dict)


class TestListDdosTools:
    def test_returns_dict(self):
        result = list_ddos_tools()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_ddos_tools()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_ddos_tools()
        for key, tool in result.items():
            assert "name" in tool

    def test_known_tools_present(self):
        result = list_ddos_tools()
        names = [t["name"].lower() for t in result.values()]
        assert any("slowloris" in n for n in names)
        assert any("loic" in n for n in names)


class TestListDdosTechniques:
    def test_returns_dict(self):
        result = list_ddos_techniques()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_ddos_techniques()
        assert len(result) > 0


class TestGenerateDdosConfig:
    def test_returns_dict(self):
        result = generate_ddos_config("loris", "192.168.1.1", 80)
        assert isinstance(result, dict)

    def test_has_tool_field(self):
        result = generate_ddos_config("loris", "192.168.1.1", 80)
        assert result["tool"] == "loris"

    def test_has_target(self):
        result = generate_ddos_config("loris", "192.168.1.1", 80)
        assert result["target"] == "192.168.1.1"

    def test_has_port(self):
        result = generate_ddos_config("loris", "192.168.1.1", 80)
        assert result["port"] == 80

    def test_invalid_tool_returns_error(self):
        result = generate_ddos_config("invalid_tool", "192.168.1.1", 80)
        assert isinstance(result, dict)
        assert "error" in result
