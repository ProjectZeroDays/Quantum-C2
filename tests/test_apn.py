"""Tests for quantum.exploits.apn — APN attack methods & hardware."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.exploits.apn import (
    apn_dashboard_state,
    list_apn_hardware,
    list_apn_attack_methods,
    scan_beacons,
    generate_apn_attack_config,
)


class TestApnDashboardState:
    def test_returns_dict(self):
        result = apn_dashboard_state()
        assert isinstance(result, dict)

    def test_has_hardware(self):
        result = apn_dashboard_state()
        assert "hardware" in result
        assert isinstance(result["hardware"], dict)


class TestListApnHardware:
    def test_returns_dict(self):
        result = list_apn_hardware()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_apn_hardware()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_apn_hardware()
        for key, h in result.items():
            assert "name" in h

    def test_known_hardware_present(self):
        result = list_apn_hardware()
        names = [h["name"].lower() for h in result.values()]
        assert any("hackrf" in n for n in names)
        assert any("pineapple" in n for n in names)


class TestListApnAttackMethods:
    def test_returns_dict(self):
        result = list_apn_attack_methods()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_apn_attack_methods()
        assert len(result) > 0

    def test_known_methods_present(self):
        result = list_apn_attack_methods()
        names = [m["name"].lower() for m in result.values()]
        assert any("evil twin" in n for n in names)


class TestScanBeacons:
    def test_returns_dict(self):
        result = scan_beacons("wlan0")
        assert isinstance(result, dict)

    def test_has_interface_field(self):
        result = scan_beacons("wlan0")
        assert result["interface"] == "wlan0"

    def test_has_beacons(self):
        result = scan_beacons("wlan0")
        assert "beacons" in result
        assert isinstance(result["beacons"], list)


class TestGenerateApnAttackConfig:
    def test_returns_dict(self):
        result = generate_apn_attack_config("evil_twin", "wifi_pineapple", "TestAPN")
        assert isinstance(result, dict)

    def test_has_method_field(self):
        result = generate_apn_attack_config("evil_twin", "wifi_pineapple", "TestAPN")
        assert result["method"] == "evil_twin"

    def test_has_hardware(self):
        result = generate_apn_attack_config("evil_twin", "wifi_pineapple", "TestAPN")
        assert result["hardware"] == "wifi_pineapple"

    def test_invalid_method_returns_error(self):
        result = generate_apn_attack_config("invalid_method", "wifi_pineapple", "TestAPN")
        assert isinstance(result, dict)
        assert "error" in result
