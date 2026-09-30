"""Tests for quantum.catalog: Exploit-DB, PayloadsAllTheThings, BadUSB."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.catalog import badusb, exploitdb, payloads_all  # noqa: E402


# ------------------------------------------------------------------ exploitdb
def test_exploitdb_seed_loads_and_stats():
    st = exploitdb.stats()
    assert st["ok"] is True
    assert st["rows"] > 40000, st


def test_exploitdb_cve_search_finds_log4shell():
    r = exploitdb.search("CVE-2021-44228", limit=5)
    assert r["total_matches"] >= 1
    edb = r["results"][0]
    assert edb["id"] and edb["description"]
    assert "CVE-2021-44228" in edb["codes"]


def test_exploitdb_keyword_and_platform_filters():
    r = exploitdb.search("wordpress", limit=3, platform="php")
    assert r["total_matches"] >= 1
    for x in r["results"]:
        assert "php" in x["platform"].lower()


def test_exploitdb_get_by_id_roundtrip():
    r = exploitdb.search("CVE-2024-3400", limit=1)
    assert r["results"], "CVE-2024-3400 should be indexed"
    g = exploitdb.get(r["results"][0]["id"])
    assert g["ok"] is True
    assert g["id"] == r["results"][0]["id"]
    assert g["file"].startswith("exploits/")


def test_exploitdb_get_missing_id_clean_error():
    g = exploitdb.get("999999999")
    assert g["ok"] is False and g["error"]


def test_exploitdb_search_empty_query_returns_rows():
    r = exploitdb.search("", limit=5)
    assert r["total_matches"] > 0
    assert len(r["results"]) <= 5


# ------------------------------------------------------------- payloads_all
def test_payloads_all_index_present():
    st = payloads_all.stats()
    assert st["ok"] is True
    assert st["sections"] >= 50
    assert st["documents"] >= 200


def test_payloads_all_sections_listing():
    secs = payloads_all.sections()
    assert isinstance(secs, list) and len(secs) >= 50
    names = {s["section"] for s in secs}
    assert "SQL Injection" in names
    assert "XXE Injection" in names


def test_payloads_all_search():
    r = payloads_all.search("sql")
    assert r["total_matches"] >= 1
    assert any(x["section"] == "SQL Injection" for x in r["results"])


def test_payloads_all_get_payload_without_sync_clean_error():
    # point at a non-existent zip to force the not-synced path
    orig = payloads_all.ZIP_PATH
    try:
        payloads_all.ZIP_PATH = os.path.join(
            os.path.dirname(orig), "definitely-not-here.zip")
        g = payloads_all.get_payload("SQL Injection")
        assert g["ok"] is False and "sync" in g["error"].lower()
    finally:
        payloads_all.ZIP_PATH = orig


def test_payloads_all_get_payload_when_synced(tmp_path):
    if not payloads_all.is_synced():
        pytest.skip("payloads_all repo zip not synced on this machine")
    g = payloads_all.get_payload("SQL Injection", "MySQL Injection.md")
    assert g["ok"] is True
    assert "SELECT" in g["content"].upper() or len(g["content"]) > 1000


# -------------------------------------------------------------------- badusb
def test_badusb_catalog_stats():
    st = badusb.stats()
    assert st["ok"] is True
    assert st["payloads"] >= 20
    assert st["by_device"].get("duckyscript", 0) >= 10


def test_badusb_get_and_script_structure():
    for pid in ("win-reverse-shell", "mac-reverse-shell",
                "linux-reverse-shell", "flipper-demo"):
        p = badusb.get(pid)
        assert p["ok"] is True, pid
        lines = p["script"].strip().splitlines()
        assert lines, pid
        # every script is non-empty DuckyScript with at least one DELAY or
        # ATTACKMODE directive
        assert any(("DELAY" in l) or ("ATTACKMODE" in l) for l in lines), pid


def test_badusb_search_and_filter():
    r = badusb.search("exfil")
    assert r["total_matches"] >= 3
    listing = badusb.list_payloads(os_filter="linux")
    assert listing["count"] >= 3
    for p in listing["payloads"]:
        assert p["os"] == "linux"


def test_badusb_get_missing_clean_error():
    p = badusb.get("not-a-payload")
    assert p["ok"] is False and p["error"]
    assert "win-reverse-shell" in p["available"]


def test_badusb_export_writes_file(tmp_path):
    out = tmp_path / "shell.txt"
    r = badusb.export("win-reverse-shell", str(out))
    assert r["ok"] is True and r["bytes"] > 0
    text = out.read_text(encoding="utf-8")
    assert "DELAY" in text and "GUI r" in text
