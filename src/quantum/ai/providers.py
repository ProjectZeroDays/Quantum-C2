"""quantum.ai.providers — pluggable chat/LLM provider registry.

Every provider speaks an OpenAI-compatible /chat/completions dialect
(or a thin adapter is applied in query()). Selection order:

  1. QCLI_AI_PROVIDER env var (or .env)
  2. legacy ABLITERATION_KEY presence  -> abliteration
  3. "local" (QBrain deterministic fallback)

Providers: abliteration, openrouter, venice, agnes, opencode,
zai (Zhipu GLM free tier), xiaomi (MiMo), gemini (AI Studio free),
groq (free tier), pollinations (keyless free).

Free-model catalogs are static snapshots (with sync dates) plus a live
OpenRouter refresh (keyless /models endpoint). Anything unverified is
marked as such — never presented as live inventory.
"""
from __future__ import annotations

import os

from quantum.core.env import load_env_file

PROVIDERS = {
    "abliteration": {
        "label": "Abliteration.ai",
        "url": "https://api.abliteration.ai/v1",
        "model": "abliterated-model-large-v2",
        "key_env": "ABLITERATION_KEY",
        "openai_compatible": True,
        "key_url": None,
        "free": False,
    },
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1",
        "model": "openrouter/auto",
        "key_env": "OPENROUTER_API_KEY",
        "openai_compatible": True,
        "key_url": "https://openrouter.ai/keys",
        "key_guide": "Sign in -> Keys -> Create (free models work on a "
                     "no-credit key within rate limits).",
        "free": True,
    },
    "venice": {
        "label": "Venice.ai",
        "url": "https://api.venice.ai/api/v1",
        "model": "venice/uncensored",
        "key_env": "VENICE_API_KEY",
        "openai_compatible": True,
        "key_url": None,
        "free": False,
    },
    "agnes": {
        "label": "Agnes",
        "url": "https://inference.agnes.ai/v1",
        "model": "agnes/agi-1",
        "key_env": "AGNES_API_KEY",
        "openai_compatible": True,
        "key_url": None,
        "free": False,
    },
    "opencode": {
        "label": "OpenCode",
        "url": "http://127.0.0.1:4096/v1",
        "model": "opencode/grok-code",
        "key_env": "OPENCODE_API_KEY",
        "openai_compatible": True,
        "key_url": None,
        "free": False,
    },
    "zai": {
        "label": "Z.ai (Zhipu GLM)",
        "url": "https://api.z.ai/api/paas/v4/",
        "model": "glm-4.7-flash",
        "key_env": "ZAI_API_KEY",
        "openai_compatible": True,
        "key_url": "https://docs.z.ai/guides/overview/quick-start",
        "key_guide": "Open Platform -> register/login -> API Keys "
                     "management page -> create key (GLM Flash models "
                     "are free).",
        "free": True,
    },
    "xiaomi": {
        "label": "Xiaomi MiMo",
        "url": "https://platform.xiaomimimo.com",
        "model": "mimo-v2-flash",
        "key_env": "XIAOMI_API_KEY",
        "openai_compatible": True,
        "key_url": "https://platform.xiaomimimo.com/",
        "key_guide": "Create an account in the console and generate an "
                     "API key; set QCLI_AI_URL to the OpenAI-compatible "
                     "base URL shown in your console.",
        "free": True,
        "api_base_note": "Base URL is per-console docs (OpenAI + "
                         "Anthropic protocols); override via QCLI_AI_URL.",
    },
    "gemini": {
        "label": "Google AI Studio (Gemini)",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-flash",
        "key_env": "GEMINI_API_KEY",
        "openai_compatible": True,
        "key_url": "https://aistudio.google.com/apikey",
        "key_guide": "Sign in -> Get API Key -> create in a project "
                     "(free tier with rate limits).",
        "free": True,
    },
    "groq": {
        "label": "Groq",
        "url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
        "openai_compatible": True,
        "key_url": "https://console.groq.com/keys",
        "key_guide": "Log in -> API Keys -> Create (generous free tier).",
        "free": True,
    },
    "pollinations": {
        "label": "Pollinations.ai",
        "url": "https://text.pollinations.ai/openai",
        "model": "openai",
        "key_env": "POLLINATIONS_API_KEY",
        "openai_compatible": True,
        "key_url": None,
        "key_guide": "Keyless — no account needed. Set "
                     "QCLI_AI_PROVIDER=pollinations to use it.",
        "free": True,
        "keyless": True,
    },
}

#: Free models per provider (static snapshots — dates marked; use the
#: OpenRouter live sync for current OpenRouter inventory).
FREE_MODELS = {
    "openrouter": {
        "synced": "2026-10-08",
        "source": "GET https://openrouter.ai/api/v1/models "
                  "(pricing.prompt == 0 and pricing.completion == 0)",
        "models": [
            "apodex/apodex-1.1-mini:free",
            "cohere/north-mini-code:free",
            "dots-studio/dots-3-note-preview:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "inclusionai/ling-3.0-flash-sante:free",
            "inclusionai/ling-3.1-flash",
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "openrouter/free",
            "poolside/laguna-s-2.1:free",
            "poolside/laguna-xs-2.1:free",
            "thinkingmachines/inkling-small:free",
            "thinkingmachines/inkling:free",
        ],
        "excluded_note": "google/lyria-3-*-preview are free but music "
                         "models, not chat — excluded from this list.",
    },
    "zai": {
        "synced": "2026-10-08",
        "source": "z.ai price table (Free on all columns)",
        "models": ["glm-4.7-flash", "glm-4.5-flash",
                   "glm-4.6v-flash"],
    },
    "xiaomi": {
        "synced": "2026-10-08",
        "source": "mimo.mi.com docs (representative list — console "
                  "lists current models)",
        "models": ["mimo-v2-flash", "mimo-v2.6-flash",
                   "mimo-v2.6-pro"],
    },
    "gemini": {
        "synced": "2026-10-08",
        "source": "AI Studio free tier (representative list)",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash",
                   "gemini-2.0-flash-lite"],
    },
    "groq": {
        "synced": "2026-10-08",
        "source": "Groq console (representative free-tier list)",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                   "openai/gpt-oss-120b", "openai/gpt-oss-20b",
                   "moonshotai/kimi-k2-instruct"],
    },
    "pollinations": {
        "synced": "2026-10-08",
        "source": "text.pollinations.ai (keyless; model list varies)",
        "models": ["openai"],
    },
}

#: Uncensored-model catalog. Honest boundaries: Venice serves a real
#: uncensored endpoint (keyed); OpenRouter's free inventory rotates —
#: sync it and look for dolphin/uncensored-suffixed ids.
UNCENSORED = [
    {"model": "venice/uncensored", "via": "venice",
     "needs_key": True,
     "note": "Venice uncensored endpoint (keyed)."},
    {"model": "abliterated-model-large-v2", "via": "abliteration",
     "needs_key": True,
     "note": "Abliterated (uncensored-leaning) model."},
    {"model": "openrouter/free", "via": "openrouter",
     "needs_key": True,
     "note": "Free router — uncensored community endpoints "
             "(e.g. dolphin-uncensored) appear and disappear; "
             "sync the catalog and pin a live id."},
]


def free_models(provider_id):
    """Static free-model snapshot for one provider (or {})."""
    return dict(FREE_MODELS.get(provider_id, {}))


def uncensored_models():
    """Uncensored-model catalog (static, boundary-noted)."""
    return [dict(u) for u in UNCENSORED]


def sync_openrouter_models(url="https://openrouter.ai/api/v1/models",
                           timeout=20):
    """Live refresh of the OpenRouter free-model list (keyless).

    Returns {"models": [...], "total": n, "synced": utc} or an honest
    {"error": ...} — never raises, never fabricates.
    """
    import datetime
    try:
        from quantum.core.deps import requests
        r = requests.get(url, timeout=timeout)
        if getattr(r, "status_code", 200) != 200:
            return {"models": [], "total": 0,
                    "error": f"openrouter models HTTP "
                             f"{getattr(r, 'status_code', '?')}"}
        data = r.json()
    except Exception as exc:  # noqa: BLE001 — honest error
        return {"models": [], "total": 0,
                "error": f"openrouter sync failed: {exc}"}
    items = data.get("data", []) if isinstance(data, dict) else []
    free = []
    for m in items:
        try:
            pricing = m.get("pricing", {})
            if float(pricing.get("prompt") or 0) == 0 and \
                    float(pricing.get("completion") or 0) == 0:
                mid = m.get("id", "")
                if "lyria" in mid:
                    continue
                free.append(mid)
        except (TypeError, ValueError):
            continue
    return {"models": sorted(free), "total": len(free),
            "synced": datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y-%m-%d")}


def resolve_provider(env=None):
    """Return (provider_id, provider_dict, api_key) for the active selection.

    Never touches the network. Falls back to abliteration when a legacy
    ABLITERATION_KEY is present but no provider was chosen explicitly.
    """
    env = env or load_env_file()
    def _get(name):
        return os.environ.get(name) or env.get(name) or ""

    pid = _get("QCLI_AI_PROVIDER").strip().lower()
    if pid and pid not in PROVIDERS:
        pid = ""
    if not pid:
        for cand_id, cand in PROVIDERS.items():
            if _get(cand["key_env"]):
                pid = cand_id
                break
    if not pid:
        pid = "abliteration"

    p = PROVIDERS[pid]
    key = _get(p["key_env"])
    # Explicit URL/model overrides win over the preset.
    p = dict(p)
    url = _get("QCLI_AI_URL")
    if url:
        p["url"] = url
    model = _get("QCLI_PINNED_MODEL")
    if model:
        p["model"] = model
    return pid, p, key


def provider_status(env=None):
    """Health-style listing for UIs: which providers have keys configured."""
    env = env or load_env_file()
    def _get(name):
        return os.environ.get(name) or env.get(name) or ""

    return [
        {
            "id": pid,
            "label": p["label"],
            "url": p["url"],
            "model": p["model"],
            "key_env": p.get("key_env"),
            "key_found": bool(_get(p["key_env"])) if p.get("key_env")
            else False,
            "keyless": bool(p.get("keyless", False)),
            "key_url": p.get("key_url"),
            "key_guide": p.get("key_guide"),
            "free": bool(p.get("free", False)),
            "free_models": len(FREE_MODELS.get(pid, {}).get("models", [])),
        }
        for pid, p in PROVIDERS.items()
    ]


def provider_dashboard_state():
    """Webcard state for the AI dashboard: providers, free models,
    uncensored catalog, key buttons."""
    return {
        "providers": provider_status(),
        "free_models": {pid: free_models(pid) for pid in FREE_MODELS},
        "uncensored": uncensored_models(),
        "active": resolve_provider()[0],
        "note": "Free-model lists are snapshots (dates marked); POST "
                "/api/ai/providers/sync refreshes OpenRouter live. "
                "key_url buttons lead to each provider's key page.",
    }
