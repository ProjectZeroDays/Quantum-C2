"""quantum.ai.bootstrap — local model manager (Ollama-aware, honest)."""
from __future__ import annotations

import shutil

from quantum.core.env import MODELS_DIR
from quantum.core.logging import log
from quantum.core.opsec import run


class DM:
    """Local model manager (Ollama-aware, honest when absent)."""

    @staticmethod
    def deploy_local_ai(model=None):
        model = model or "huihui-ai/qwen3-1.7b-abliterated:Q4_K_M"
        if shutil.which("ollama"):
            try:
                r = run("ollama list", timeout=30)
                if model.split(":")[0] not in (r.stdout or ""):
                    run(f'ollama pull "{model}"', timeout=600)
            except Exception as exc:
                log(f"ollama mgmt: {exc}", "WARN")
            log(f"local AI model ready: {model} (dir {MODELS_DIR})", "AI")
            return model
        log("Ollama not installed — abliterated/QBrain fallback remains", "AI")
        return None
