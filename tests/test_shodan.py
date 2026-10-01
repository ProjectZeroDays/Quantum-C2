"""Tests for quantum.recon.shodan — Shodan presets & search."""
from quantum.recon.shodan import (
    shodan_dashboard_state,
    list_shodan_presets,
    shodan_search,
    shodan_host_info,
)


class TestShodanDashboardState:
    def test_returns_dict(self):
        result = shodan_dashboard_state()
        assert isinstance(result, dict)

    def test_has_presets(self):
        result = shodan_dashboard_state()
        assert "presets" in result
        assert isinstance(result["presets"], dict)


class TestListShodanPresets:
    def test_returns_dict(self):
        result = list_shodan_presets()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_shodan_presets()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_shodan_presets()
        for key, p in result.items():
            assert "name" in p

    def test_entries_have_queries(self):
        result = list_shodan_presets()
        for key, p in result.items():
            assert "queries" in p
            assert isinstance(p["queries"], list)
            assert len(p["queries"]) > 0


class TestShodanSearch:
    def test_returns_dict(self):
        result = shodan_search("webcamxp", limit=10)
        assert isinstance(result, dict)

    def test_has_query_field(self):
        result = shodan_search("webcamxp", limit=10)
        assert result["query"] == "webcamxp"

    def test_has_results_field(self):
        result = shodan_search("webcamxp", limit=10)
        assert "results" in result
        assert isinstance(result["results"], list)


class TestShodanHostInfo:
    def test_returns_dict(self):
        result = shodan_host_info("8.8.8.8")
        assert isinstance(result, dict)

    def test_has_ip_field(self):
        result = shodan_host_info("8.8.8.8")
        assert result["ip"] == "8.8.8.8"
