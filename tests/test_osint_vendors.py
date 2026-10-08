"""Tests for the OSINT vendor modules (no network — honest offline paths)."""
import base64
import hashlib
import hmac
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.recon.darkowl import (  # noqa: E402
    darkowl_dashboard_state,
    darkowl_auth_header,
    darkowl_entity,
    darkowl_search,
    darkowl_test,
)
from quantum.recon.intelx import (  # noqa: E402
    intelx_build_search_url,
    intelx_dashboard_state,
    intelx_tools,
)
from quantum.recon.shadowdragon import (  # noqa: E402
    shadowdragon_dashboard_state,
    shadowdragon_license_status,
    shadowdragon_products,
    shadowdragon_query_plan,
    shadowdragon_source_matrix,
)


def test_intelx_search_without_key_is_honest():
    # force the no-key path regardless of ambient env
    import quantum.recon.intelx as ix
    old = os.environ.pop("INTELX_API_KEY", None)
    old2 = os.environ.pop("INTELX_KEY", None)
    try:
        r = ix.intelx_search("test@example.com")
    finally:
        if old is not None:
            os.environ["INTELX_API_KEY"] = old
        if old2 is not None:
            os.environ["INTELX_KEY"] = old2
    assert r["hits"] == [] and "error" in r and "request" in r


def test_intelx_phonebook_without_key_is_honest():
    import quantum.recon.intelx as ix
    old = os.environ.pop("INTELX_API_KEY", None)
    old2 = os.environ.pop("INTELX_KEY", None)
    try:
        r = ix.intelx_phonebook("test@example.com")
    finally:
        if old is not None:
            os.environ["INTELX_API_KEY"] = old
        if old2 is not None:
            os.environ["INTELX_KEY"] = old2
    assert r["related"] == [] and "error" in r


def test_intelx_search_url_shape():
    url = intelx_build_search_url("evil.com")
    assert url.startswith("https://intelx.io/api/?") and "query=evil.com" \
        in url and "key" not in url


def test_intelx_state_and_tools():
    s = intelx_dashboard_state()
    assert s["service"] == "Intelligence X" and s["selector_types"]
    assert intelx_tools()


def test_shadowdragon_plan_structure():
    plan = shadowdragon_query_plan("email", "a@b.c")
    assert plan["subject"] == {"type": "email", "value": "a@b.c"}
    assert plan["steps"] and plan["pivot_chain"]
    assert len(plan["steps"]) == len(plan["families"])


def test_shadowdragon_catalogs():
    assert shadowdragon_source_matrix() and shadowdragon_products()
    lic = shadowdragon_license_status()
    assert lic["free_api"] is False
    st = shadowdragon_dashboard_state()
    assert "products" in st and "families" in st


def test_darkowl_auth_header_vector():
    auth, date = darkowl_auth_header("GET", "/api/v1/test", "priv", "pub",
                                     date_stamp="Wed, 08 Oct 2026 00:00:00 GMT")
    expect = base64.b64encode(hmac.new(
        b"priv", b"GET/api/v1/testWed, 08 Oct 2026 00:00:00 GMT",
        hashlib.sha1).digest()).decode()
    assert auth == "OWL pub:" + expect
    assert date == "Wed, 08 Oct 2026 00:00:00 GMT"


def test_darkowl_without_keys_is_honest(monkeypatch):
    monkeypatch.delenv("DARKOWL_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("DARKOWL_PRIVATE_KEY", raising=False)
    assert "error" in darkowl_search("q")
    assert darkowl_test()["ok"] is False
    assert "error" in darkowl_entity("email", "a@b.c")


def test_darkowl_entity_rejects_bad_type():
    r = darkowl_entity("hostname", "x", public_key="p", private_key="k")
    assert "error" in r


def test_darkowl_state_shape():
    s = darkowl_dashboard_state()
    assert s["service"] == "DarkOwl Vision"
    assert s["test_response"] == {"answer": "hoot"}
