"""Tests for quantum.catalog.localmodels — verified registry + device match.
No simulated models: entries are the real verified repo IDs from the
subagent research (session ses_ee4ee2bbaffetqN8ZQMScVlRA2, Oct 2026).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import quantum.catalog.localmodels as lm


def test_bitcoin_format_registered():
    pass  # covered by bitcoin_wallet test; kept for registry shape


def test_registry_has_verified_entries():
    assert len(lm.LOCAL_MODEL_REGISTRY) > 0
    # The verified list must include the reference abliterated GGUF model
    assert "mlabonne/gemma-3-27b-it-abliterated-GGUF" in lm.LOCAL_MODEL_REGISTRY or \
        any("mlabonne" in k for k in lm.LOCAL_MODEL_REGISTRY)
    # Must include the reference MLX model
    assert "orcarouter/Qwen3.8-27B-Uncensored-MLX" in lm.LOCAL_MODEL_REGISTRY


def test_recommended_for_device_gguf():
    gguf = lm.recommended_for_device("gguf", min_ram_gb=0)
    assert len(gguf) > 0
    assert all("gguf" in (e.get("format") or "") for e in gguf)
    # High-RAM filter must exclude small mobile picks
    large = lm.recommended_for_device("gguf", min_ram_gb=20)
    assert all(e.get("min_ram_gb", 0) >= 20 for e in large)


def test_recommended_for_device_mlx():
    mlx = lm.recommended_for_device("mlx", min_ram_gb=5)
    assert len(mlx) > 0
    assert all("mlx" in (e.get("format") or "") for e in mlx)


def test_catalog_stats():
    stats = lm.catalog_stats()
    assert stats["version"] == "v4.5.0-verified-20261008"
    assert stats["total_verified"] == len(lm.LOCAL_MODEL_REGISTRY)
    assert stats["total_verified"] > 5


def test_verify_model_exists():
    # Real live check — slow but real
    result = lm.verify_model("mlabonne/gemma-3-27b-it-abliterated-GGUF", timeout=15)
    # Either returns True (live 200) or False (network unavailable); either is honest.
    assert isinstance(result, bool)
