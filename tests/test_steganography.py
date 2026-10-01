"""Tests for quantum.exploits.steganography — stego methods & PDF exploits."""
from quantum.exploits.steganography import (
    steganography_dashboard_state,
    list_steganography_methods,
    list_pdf_exploit_methods,
    list_messenger_parse_chains,
)


class TestSteganographyDashboardState:
    def test_returns_dict(self):
        result = steganography_dashboard_state()
        assert isinstance(result, dict)

    def test_has_methods(self):
        result = steganography_dashboard_state()
        assert "methods" in result
        assert isinstance(result["methods"], dict)


class TestListSteganographyMethods:
    def test_returns_dict(self):
        result = list_steganography_methods()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_steganography_methods()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_steganography_methods()
        for key, m in result.items():
            assert "name" in m

    def test_known_methods_present(self):
        result = list_steganography_methods()
        names = [m["name"].lower() for m in result.values()]
        assert any("lsb" in n for n in names)


class TestListPdfExploitMethods:
    def test_returns_dict(self):
        result = list_pdf_exploit_methods()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_pdf_exploit_methods()
        assert len(result) > 0


class TestListMessengerParseChains:
    def test_returns_dict(self):
        result = list_messenger_parse_chains()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_messenger_parse_chains()
        assert len(result) > 0
