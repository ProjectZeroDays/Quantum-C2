"""Tests for quantum.control.botnet — botnet dashboard."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.control.botnet import (
    botnet_dashboard_state,
    list_botnet_types,
    list_botnet_capabilities,
    generate_botnet_config,
)


class TestBotnetDashboardState:
    def test_returns_dict(self):
        result = botnet_dashboard_state()
        assert isinstance(result, dict)

    def test_has_types(self):
        result = botnet_dashboard_state()
        assert "types" in result
        assert isinstance(result["types"], dict)

    def test_has_capabilities(self):
        result = botnet_dashboard_state()
        assert "capabilities" in result
        assert isinstance(result["capabilities"], dict)


class TestListBotnetTypes:
    def test_returns_dict(self):
        result = list_botnet_types()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_botnet_types()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_botnet_types()
        for key, t in result.items():
            assert "name" in t

    def test_known_types_present(self):
        result = list_botnet_types()
        names = [t["name"].lower() for t in result.values()]
        assert any("irc" in n for n in names)
        assert any("p2p" in n for n in names)


class TestListBotnetCapabilities:
    def test_returns_dict(self):
        result = list_botnet_capabilities()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_botnet_capabilities()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_botnet_capabilities()
        for key, cap in result.items():
            assert "name" in cap


class TestGenerateBotnetConfig:
    def test_returns_dict(self):
        result = generate_botnet_config("irc", "127.0.0.1", 6667)
        assert isinstance(result, dict)

    def test_has_type_field(self):
        result = generate_botnet_config("irc", "127.0.0.1", 6667)
        assert result["type"] == "irc"

    def test_has_c2_host(self):
        result = generate_botnet_config("irc", "127.0.0.1", 6667)
        assert result["c2_host"] == "127.0.0.1"

    def test_has_c2_port(self):
        result = generate_botnet_config("irc", "127.0.0.1", 6667)
        assert result["c2_port"] == 6667

    def test_invalid_type_returns_error(self):
        result = generate_botnet_config("invalid_type")
        assert isinstance(result, dict)
        assert "error" in result
