"""Tests for quantum.control.phantomdroid — ADB device controls."""
from quantum.control.phantomdroid import (
    phantomdroid_dashboard_state,
    discover_adb_devices,
    list_phantomdroid_features,
    connect_adb_wireless,
    adb_shell,
    adb_screencap,
    adb_get_device_info,
)


class TestPhantomdroidDashboardState:
    def test_returns_dict(self):
        result = phantomdroid_dashboard_state()
        assert isinstance(result, dict)

    def test_has_features(self):
        result = phantomdroid_dashboard_state()
        assert "features" in result
        assert isinstance(result["features"], dict)


class TestDiscoverAdbDevices:
    def test_returns_list(self):
        result = discover_adb_devices()
        assert isinstance(result, list)


class TestListPhantomdroidFeatures:
    def test_returns_dict(self):
        result = list_phantomdroid_features()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_phantomdroid_features()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_phantomdroid_features()
        for key, f in result.items():
            assert "name" in f


class TestConnectAdbWireless:
    def test_returns_dict(self):
        result = connect_adb_wireless("192.168.1.100", 5555)
        assert isinstance(result, dict)

    def test_has_ip_field(self):
        result = connect_adb_wireless("192.168.1.100", 5555)
        assert result["ip"] == "192.168.1.100"


class TestAdbShell:
    def test_returns_dict(self):
        result = adb_shell("test-serial", "ls")
        assert isinstance(result, dict)

    def test_has_serial_field(self):
        result = adb_shell("test-serial", "ls")
        assert result["serial"] == "test-serial"


class TestAdbScreencap:
    def test_returns_dict(self):
        result = adb_screencap("test-serial", "/tmp/test.png")
        assert isinstance(result, dict)

    def test_has_output_path(self):
        result = adb_screencap("test-serial", "/tmp/test.png")
        assert result["output"] == "/tmp/test.png"


class TestAdbGetDeviceInfo:
    def test_returns_dict(self):
        result = adb_get_device_info("test-serial")
        assert isinstance(result, dict)

    def test_has_serial_field(self):
        result = adb_get_device_info("test-serial")
        assert result["serial"] == "test-serial"
