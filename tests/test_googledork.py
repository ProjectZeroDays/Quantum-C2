"""Tests for quantum.recon.googledork (dork packs + engine URLs + methods).

No network: URL building and catalog validation only. Live results render
in a browser (APK in-app WebView), never scraped.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.recon import googledork as G  # noqa: E402


def test_catalog_validates_clean():
    assert G.validate() == []


def test_preset_ids_unique_and_queries_nonempty():
    ids = [p["id"] for p in G.PRESETS]
    assert len(ids) == len(set(ids)) >= 20
    for p in G.PRESETS:
        assert p["query"].strip()
        assert p["category"] in G.CATEGORIES


def test_every_category_has_presets():
    grouped = G.presets_by_category()
    for cat in G.CATEGORIES:
        assert grouped[cat], f"category {cat} is empty"


def test_get_preset_roundtrip():
    p = G.get_preset("sql-dumps")
    assert p is not None and "INSERT INTO" in p["query"]
    assert G.get_preset("no-such-id") is None


def test_search_url_encoding_and_engines():
    url = G.build_search_url('intitle:"index of"')
    assert url.startswith("https://www.google.com/search?q=")
    assert "index" in url and "%22" in url  # quotes encoded, not raw
    assert " " not in url
    bing = G.build_search_url("test", engine="bing")
    assert bing.startswith("https://www.bing.com/search?q=test")
    ddg = G.build_search_url("test", engine="duckduckgo")
    assert "duckduckgo.com" in ddg
    # unknown engine falls back to google honestly
    assert G.build_search_url("x", engine="nope").startswith(
        "https://www.google.com/search?q=")


def test_analyst_methods_are_generic_tradecraft():
    assert len(G.ANALYST_METHODS) >= 5
    banned = ("cia", "nsa", "classified", "top secret")
    for m in G.ANALYST_METHODS:
        text = (m["title"] + " " + m["body"] + " " +
                " ".join(m["steps"])).lower()
        for word in banned:
            assert word not in text, f"method {m['id']} mentions {word}"
        assert len(m["steps"]) >= 2


def test_operators_all_documented():
    expected = {"site:", "filetype:", "intitle:", "inurl:", "intext:",
                "cache:", "related:", "before:/after:", '""', "-",
                "OR / |", "*"}
    assert expected <= set(G.OPERATORS)
    for op, info in G.OPERATORS.items():
        assert info["desc"].strip() and info["example"].strip()
