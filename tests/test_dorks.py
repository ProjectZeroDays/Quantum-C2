"""Tests for quantum.recon.dorks — Google dork categories."""
from quantum.recon.dorks import (
    dorks_dashboard_state,
    list_dork_categories,
    DORK_CATEGORIES,
)


class TestDorksDashboardState:
    def test_returns_dict(self):
        result = dorks_dashboard_state()
        assert isinstance(result, dict)

    def test_has_categories(self):
        result = dorks_dashboard_state()
        assert "categories" in result
        assert isinstance(result["categories"], dict)

    def test_has_total_dorks(self):
        result = dorks_dashboard_state()
        assert "total_dorks" in result
        assert result["total_dorks"] > 0


class TestListDorkCategories:
    def test_returns_list(self):
        result = list_dork_categories()
        assert isinstance(result, list)

    def test_non_empty(self):
        result = list_dork_categories()
        assert len(result) > 0

    def test_entries_are_strings(self):
        result = list_dork_categories()
        for cat in result:
            assert isinstance(cat, str)


class TestDorkCategoriesData:
    def test_categories_dict_not_empty(self):
        assert len(DORK_CATEGORIES) > 0

    def test_all_categories_have_dorks(self):
        for key, cat in DORK_CATEGORIES.items():
            assert "dorks" in cat
            assert len(cat["dorks"]) > 0

    def test_all_dorks_are_strings(self):
        for key, cat in DORK_CATEGORIES.items():
            for d in cat["dorks"]:
                assert isinstance(d, str)
                assert len(d) > 0

    def test_all_dorks_are_non_empty(self):
        for key, cat in DORK_CATEGORIES.items():
            for d in cat["dorks"]:
                assert len(d) > 0, f"Empty dork in category: {key}"
