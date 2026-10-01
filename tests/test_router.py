"""Tests for quantum.exploits.router — router vulnerabilities & attacks."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.exploits.router import (
    router_dashboard_state,
    list_router_vulnerabilities,
    list_default_credentials,
    list_router_attack_methods,
    scan_router,
    generate_router_attack_config,
)


class TestRouterDashboardState:
    def test_returns_dict(self):
        result = router_dashboard_state()
        assert isinstance(result, dict)

    def test_has_vulns(self):
        result = router_dashboard_state()
        assert "vulnerabilities" in result
        assert isinstance(result["vulnerabilities"], dict)


class TestListRouterVulnerabilities:
    def test_returns_dict(self):
        result = list_router_vulnerabilities()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_router_vulnerabilities()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_router_vulnerabilities()
        for cve, v in result.items():
            assert "name" in v

    def test_known_cve_present(self):
        result = list_router_vulnerabilities()
        assert "CVE-2024-4577" in result


class TestListDefaultCredentials:
    def test_returns_dict(self):
        result = list_default_credentials()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_default_credentials()
        assert len(result) > 0

    def test_entries_are_lists(self):
        result = list_default_credentials()
        for vendor, passwords in result.items():
            assert isinstance(passwords, list)
            assert len(passwords) > 0


class TestListRouterAttackMethods:
    def test_returns_dict(self):
        result = list_router_attack_methods()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_router_attack_methods()
        assert len(result) > 0


class TestScanRouter:
    def test_returns_dict(self):
        result = scan_router("192.168.1.1", 80)
        assert isinstance(result, dict)

    def test_has_ip_field(self):
        result = scan_router("192.168.1.1", 80)
        assert result["ip"] == "192.168.1.1"

    def test_has_open_ports(self):
        result = scan_router("192.168.1.1", 80)
        assert "open_ports" in result
        assert isinstance(result["open_ports"], list)


class TestGenerateRouterAttackConfig:
    def test_returns_dict(self):
        result = generate_router_attack_config("default_creds", "192.168.1.1", 80)
        assert isinstance(result, dict)

    def test_has_method_field(self):
        result = generate_router_attack_config("default_creds", "192.168.1.1", 80)
        assert result["method"] == "default_creds"

    def test_has_target(self):
        result = generate_router_attack_config("default_creds", "192.168.1.1", 80)
        assert result["target"] == "192.168.1.1"
