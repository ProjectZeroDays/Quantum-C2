"""Tests for quantum.control.map2d — 2D map widget."""
import pytest
from quantum.control.map2d import (
    map2d_dashboard_state,
    generate_map_data,
)


class TestMap2dDashboardState:
    def test_returns_dict(self):
        result = map2d_dashboard_state()
        assert isinstance(result, dict)

    def test_has_beacons(self):
        result = map2d_dashboard_state()
        assert "beacons" in result


class TestGenerateMapData:
    def test_returns_dict(self):
        result = generate_map_data([])
        assert isinstance(result, dict)

    def test_empty_beacons(self):
        result = generate_map_data([])
        assert isinstance(result, dict)

    def test_with_beacons(self):
        beacons = [
            {"id": "a", "lat": 40.7128, "lon": -74.0060, "name": "NYC"},
            {"id": "b", "lat": 34.0522, "lon": -118.2437, "name": "LA"},
        ]
        result = generate_map_data(beacons)
        assert isinstance(result, dict)
        assert "center" in result
        assert "bounds" in result

    def test_center_is_avg(self):
        beacons = [
            {"id": "a", "lat": 0.0, "lon": 0.0},
            {"id": "b", "lat": 10.0, "lon": 10.0},
        ]
        result = generate_map_data(beacons)
        center = result["center"]
        assert center["lat"] == pytest.approx(5.0)
        assert center["lon"] == pytest.approx(5.0)
