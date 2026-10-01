"""Tests for quantum.control.ransomware — ransomware dashboard."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.control.ransomware import (
    ransomware_dashboard_state,
    list_ransomware_tools,
    list_deployment_modules,
    generate_ransomware_config,
)


class TestRansomwareDashboardState:
    def test_returns_dict(self):
        result = ransomware_dashboard_state()
        assert isinstance(result, dict)

    def test_has_tools(self):
        result = ransomware_dashboard_state()
        assert "tools" in result
        assert isinstance(result["tools"], dict)

    def test_has_deployment_modules(self):
        result = ransomware_dashboard_state()
        assert "deployment_modules" in result
        assert isinstance(result["deployment_modules"], dict)


class TestListRansomwareTools:
    def test_returns_dict(self):
        result = list_ransomware_tools()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_ransomware_tools()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_ransomware_tools()
        for key, tool in result.items():
            assert "name" in tool

    def test_known_tools_present(self):
        result = list_ransomware_tools()
        names = [t["name"].lower() for t in result.values()]
        assert any("lockbit" in n for n in names)
        assert any("wannacry" in n for n in names)


class TestListDeploymentModules:
    def test_returns_dict(self):
        result = list_deployment_modules()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_deployment_modules()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_deployment_modules()
        for key, mod in result.items():
            assert "name" in mod


class TestGenerateRansomwareConfig:
    def test_returns_dict(self):
        result = generate_ransomware_config("lockbit", "Windows")
        assert isinstance(result, dict)

    def test_has_tool_field(self):
        result = generate_ransomware_config("lockbit", "Windows")
        assert result["tool"] == "lockbit"

    def test_has_target_os(self):
        result = generate_ransomware_config("lockbit", "Windows")
        assert result["target_os"] == "Windows"

    def test_has_encryption(self):
        result = generate_ransomware_config("lockbit", "Windows")
        assert "encryption" in result

    def test_invalid_tool_returns_error(self):
        result = generate_ransomware_config("invalid_tool", "Windows")
        assert isinstance(result, dict)
        assert "error" in result
