"""quantum.ai.providers — pluggable chat/LLM provider registry.

Every provider speaks an OpenAI-compatible /chat/completions dialect
(or a thin adapter is applied in query()). Selection order:

  1. QCLI_AI_PROVIDER env var (or .env)
  2. legacy ABLITERATION_KEY presence  -> abliteration
  3. "local" (QBrain deterministic fallback)

Providers: abliteration, openrouter, venice, agnes, opencode.
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
    },
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1",
        "model": "openrouter/auto",
        "key_env": "OPENROUTER_API_KEY",
        "openai_compatible": True,
    },
    "venice": {
        "label": "Venice.ai",
        "url": "https://api.venice.ai/api/v1",
        "model": "venice/uncensored",
        "key_env": "VENICE_API_KEY",
        "openai_compatible": True,
    },
    "agnes": {
        "label": "Agnes",
        "url": "https://inference.agnes.ai/v1",
        "model": "agnes/agi-1",
        "key_env": "AGNES_API_KEY",
        "openai_compatible": True,
    },
    "opencode": {
        "label": "OpenCode",
        "url": "http://127.0.0.1:4096/v1",
        "model": "opencode/grok-code",
        "key_env": "OPENCODE_API_KEY",
        "openai_compatible": True,
    },
}


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
            "key_found": bool(_get(p["key_env"])),
        }
        for pid, p in PROVIDERS.items()
    ]
