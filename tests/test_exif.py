"""Tests for quantum.recon.exif — EXIF analysis."""
from quantum.recon.exif import (
    exif_dashboard_state,
    analyze_exif,
)


class TestExifDashboardState:
    def test_returns_dict(self):
        result = exif_dashboard_state()
        assert isinstance(result, dict)

    def test_has_images(self):
        result = exif_dashboard_state()
        assert "images" in result


class TestAnalyzeExif:
    def test_returns_dict(self):
        result = analyze_exif("nonexistent.jpg")
        assert isinstance(result, dict)

    def test_has_image_path_field(self):
        result = analyze_exif("nonexistent.jpg")
        assert result["image_path"] == "nonexistent.jpg"

    def test_nonexistent_file_handled(self):
        result = analyze_exif("nonexistent.jpg")
        assert "error" in result or "gps" in result or "camera" in result
