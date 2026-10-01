"""Tests for quantum.recon.trackers — IP/IMEI/phone tracking."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.recon.trackers import (
    track_ip_downloads,
    track_imei,
    track_phone_location,
)


class TestTrackIPDownloads:
    def test_returns_dict(self):
        result = track_ip_downloads("8.8.8.8")
        assert isinstance(result, dict)

    def test_has_ip_field(self):
        result = track_ip_downloads("8.8.8.8")
        assert result["ip"] == "8.8.8.8"

    def test_has_sources(self):
        result = track_ip_downloads("8.8.8.8")
        assert "sources" in result
        assert isinstance(result["sources"], list)

    def test_sources_non_empty(self):
        result = track_ip_downloads("8.8.8.8")
        assert len(result["sources"]) > 0

    def test_source_entries_have_name(self):
        result = track_ip_downloads("8.8.8.8")
        for src in result["sources"]:
            assert "name" in src

    def test_invalid_ip_still_returns_dict(self):
        result = track_ip_downloads("not-an-ip")
        assert isinstance(result, dict)
        assert result["ip"] == "not-an-ip"


class TestTrackIMEI:
    def test_returns_dict(self):
        result = track_imei("356720123456789")
        assert isinstance(result, dict)

    def test_has_imei_field(self):
        result = track_imei("356720123456789")
        assert result["imei"] == "356720123456789"

    def test_has_device_info(self):
        result = track_imei("356720123456789")
        assert "device" in result

    def test_known_tac(self):
        result = track_imei("356720123456789")
        assert result["device"] is not None

    def test_unknown_tac(self):
        result = track_imei("000000000000000")
        assert isinstance(result, dict)


class TestTrackPhoneLocation:
    def test_returns_dict(self):
        result = track_phone_location("+1234567890")
        assert isinstance(result, dict)

    def test_has_phone_field(self):
        result = track_phone_location("+1234567890")
        assert result["phone"] == "+1234567890"

    def test_has_sources(self):
        result = track_phone_location("+1234567890")
        assert "sources" in result
        assert isinstance(result["sources"], list)
