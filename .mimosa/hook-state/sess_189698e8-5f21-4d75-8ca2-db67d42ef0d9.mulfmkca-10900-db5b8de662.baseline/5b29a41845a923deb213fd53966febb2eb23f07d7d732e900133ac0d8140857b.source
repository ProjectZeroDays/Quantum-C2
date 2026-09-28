"""Tests for agents/build/variant.py (QUANTUM-CLI V4 OBSIDIAN variant builder)."""

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "build" / "variant.py"


def _load_variant():
    # sys.path may not include agents/build, so load the module from its file.
    spec = importlib.util.spec_from_file_location("variant_under_test", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


variant = _load_variant()


def test_same_target_and_epoch_is_byte_identical(tmp_path):
    first = variant.build_variant("10.0.0.5", epoch=7, out_dir=tmp_path / "a")
    second = variant.build_variant("10.0.0.5", epoch=7, out_dir=tmp_path / "b")

    assert Path(first).exists()
    assert Path(second).exists()
    assert Path(first).read_bytes() == Path(second).read_bytes()


def test_different_targets_differ_bytewise(tmp_path):
    first = variant.build_variant("10.0.0.5", epoch=0, out_dir=tmp_path / "a")
    second = variant.build_variant("10.0.0.6", epoch=0, out_dir=tmp_path / "b")

    assert Path(first).read_bytes() != Path(second).read_bytes()


def test_different_epochs_differ_bytewise(tmp_path):
    first = variant.build_variant("10.0.0.5", epoch=0, out_dir=tmp_path / "a")
    second = variant.build_variant("10.0.0.5", epoch=1, out_dir=tmp_path / "b")

    assert Path(first).read_bytes() != Path(second).read_bytes()


def test_output_is_powershell_with_beacon_url(tmp_path):
    c2 = "http://127.0.0.1:8443/r"
    path = variant.build_variant("10.0.0.5", epoch=0, out_dir=tmp_path, c2=c2)
    script = Path(path).read_text(encoding="utf-8")

    assert script.strip()
    assert str(path).endswith(".ps1")
    assert c2 in script
    assert "10.0.0.5" in script
    assert "Invoke-RestMethod" in script
    assert "while ($true)" in script
    assert "act = 'hb'" in script
