"""Tests for quantum.markets.darkweb — dark web directory."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.markets.darkweb import (
    darkweb_dashboard_state,
    list_onion_services,
)


class TestDarkwebDashboardState:
    def test_returns_dict(self):
        result = darkweb_dashboard_state()
        assert isinstance(result, dict)

    def test_has_services_count(self):
        result = darkweb_dashboard_state()
        assert "services" in result

    def test_services_non_zero(self):
        result = darkweb_dashboard_state()
        assert result["services"] > 0


class TestListOnionServices:
    def test_returns_list(self):
        result = list_onion_services()
        assert isinstance(result, list)

    def test_non_empty(self):
        result = list_onion_services()
        assert len(result) > 0

    def test_entries_have_key(self):
        result = list_onion_services()
        for svc in result:
            assert "key" in svc

    def test_entries_have_nested_services(self):
        result = list_onion_services()
        for svc in result:
            for key, info in svc.items():
                if key == "key":
                    continue
                assert "name" in info
                assert "url" in info
                assert "type" in info

    def test_urls_are_onion_or_clearnet(self):
        result = list_onion_services()
        for svc in result:
            for key, info in svc.items():
                if key == "key":
                    continue
                # Most are .onion; some legacy services use clearnet URLs
                assert ".onion" in info["url"] or info["url"].startswith("http")

    def test_known_services_present(self):
        result = list_onion_services()
        all_names = []
        for svc in result:
            for key, info in svc.items():
                if key == "key":
                    continue
                all_names.append(info["name"].lower())
        assert any("ahmia" in n for n in all_names)
        assert any("dread" in n for n in all_names)
