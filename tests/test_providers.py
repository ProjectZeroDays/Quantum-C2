"""Tests for quantum.ai.providers — free-model catalogs + resolution."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.ai.providers import (  # noqa: E402
    PROVIDERS,
    free_models,
    provider_dashboard_state,
    provider_status,
    resolve_provider,
    sync_openrouter_models,
    uncensored_models,
)


def test_ten_providers_registered():
    assert len(PROVIDERS) == 10
    for pid in ("openrouter", "zai", "xiaomi", "gemini", "groq",
                "pollinations"):
        assert PROVIDERS[pid]["free"] is True


def test_key_urls_present_where_verified():
    urls = {p["id"]: p["key_url"] for p in provider_status()}
    assert urls["openrouter"] == "https://openrouter.ai/keys"
    assert urls["groq"] == "https://console.groq.com/keys"
    assert urls["gemini"] == "https://aistudio.google.com/apikey"
    assert urls["zai"] == \
        "https://docs.z.ai/guides/overview/quick-start"
    assert urls["xiaomi"] == "https://platform.xiaomimimo.com/"


def test_openrouter_free_snapshot_shape():
    snap = free_models("openrouter")
    assert snap["synced"] and len(snap["models"]) >= 10
    assert "openrouter/free" in snap["models"]
    assert not any("lyria" in m for m in snap["models"])


def test_uncensored_catalog():
    u = uncensored_models()
    assert any(e["model"] == "venice/uncensored" for e in u)


def test_resolve_explicit_provider(monkeypatch):
    monkeypatch.setenv("QCLI_AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    pid, p, key = resolve_provider()
    assert pid == "groq" and key == "k"


def test_resolve_unknown_falls_back(monkeypatch):
    for var in ("QCLI_AI_PROVIDER", "ABLITERATION_KEY",
                "OPENROUTER_API_KEY", "VENICE_API_KEY", "AGNES_API_KEY",
                "OPENCODE_API_KEY", "ZAI_API_KEY", "XIAOMI_API_KEY",
                "GEMINI_API_KEY", "GROQ_API_KEY",
                "POLLINATIONS_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    pid, _, key = resolve_provider(env={"QCLI_AI_PROVIDER": ""})
    assert pid == "abliteration" and key == ""


def test_sync_honest_error_on_bad_host():
    r = sync_openrouter_models(url="http://127.0.0.1:9/nope",
                               timeout=3)
    assert r["models"] == [] and r.get("error")


def test_dashboard_state_shape():
    s = provider_dashboard_state()
    assert len(s["providers"]) == 10
    assert "openrouter" in s["free_models"]
    assert s["uncensored"]
    assert "key_url" in s["providers"][0]


def _client():
    from quantum.c2.app import make_c2
    return make_c2({"default": "# agent"}).test_client()


def test_ai_routes():
    c = _client()
    assert len(c.get("/api/ai/providers").get_json()) == 10
    assert "openrouter" in c.get("/api/ai/models").get_json()
    assert c.get("/api/ai/uncensored").get_json()
    st = c.get("/api/ai/state").get_json()
    assert len(st["providers"]) == 10
    keys = [p for p in st["providers"] if p["key_url"]]
    assert len(keys) >= 5
    assert b"Get API Key" in c.get("/dash").data
