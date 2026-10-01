"""Tests for quantum.brute.crunch (crunch-compatible wordlist generation).

Pure combinatorics + file I/O — no network, no system crunch required
(system-backend paths are tested with a faked binary presence/probe).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import pytest  # noqa: E402

from quantum.brute import crunch as C  # noqa: E402


def test_charset_expansion_dedupes_and_preserves_order():
    assert C.expand_charset("bbaac") == "bac"
    assert C.expand_charset("abc123") == "abc123"
    with pytest.raises(ValueError):
        C.expand_charset("")


def test_placeholders_resolve_to_full_classes():
    assert C.PLACEHOLDERS["@"] == "abcdefghijklmnopqrstuvwxyz"
    assert C.PLACEHOLDERS[","] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert C.PLACEHOLDERS["%"] == "0123456789"
    assert len(C.PLACEHOLDERS["^"]) == len(C.SYMBOLS) > 0


def test_parse_pattern_slots_and_escapes():
    assert C.parse_pattern("ab") == [("lit", "a"), ("lit", "b")]
    assert C.parse_pattern("@%") == [("class", "@"), ("class", "%")]
    assert C.parse_pattern(r"\@") == [("lit", "@")]
    assert C.parse_pattern(r"a\\b") == [("lit", "a"), ("lit", "\\"), ("lit", "b")]
    with pytest.raises(ValueError):
        C.parse_pattern("")
    with pytest.raises(ValueError):
        C.parse_pattern("ab\\")


def test_estimate_count_plain_mode():
    # charset "ab", lengths 1-2 -> 2 + 4 = 6
    assert C.estimate_count(1, 2, charset="ab") == 6
    assert C.estimate_count(2, 2, charset="ab") == 4
    # default charset is lowercase: 26^1
    assert C.estimate_count(1, 1) == 26
    with pytest.raises(ValueError):
        C.estimate_count(0, 2, charset="ab")
    with pytest.raises(ValueError):
        C.estimate_count(3, 2, charset="ab")
    with pytest.raises(ValueError):
        C.estimate_count(1, 1, charset="")


def test_estimate_count_pattern_mode():
    # "@%" -> 26 * 10 = 260
    assert C.estimate_count(2, 2, pattern="@%") == 260
    # literals contribute x1: "a@" with min=max=2 -> 26
    assert C.estimate_count(2, 2, pattern="a@") == 26
    with pytest.raises(ValueError):
        C.estimate_count(1, 2, pattern="@%")  # length mismatch


def test_estimate_size_counts_newlines():
    assert C.estimate_size(1, 1, charset="ab") == {"entries": 2, "bytes": 4}
    # "@%" -> 260 entries of len 2 + newline = 780 bytes
    assert C.estimate_size(2, 2, pattern="@%") == {"entries": 260, "bytes": 780}


def test_generate_plain_order_and_completeness():
    got = list(C.generate(1, 2, charset="ab"))
    assert got == ["a", "b", "aa", "ab", "ba", "bb"]


def test_generate_pattern_odometer_order():
    got = list(C.generate(2, 2, pattern="a%"))
    assert got == ["a" + d for d in "0123456789"]
    # leftmost slot varies slowest
    got2 = list(C.generate(2, 2, charset="ab", pattern=None))
    assert got2 == ["aa", "ab", "ba", "bb"]


def test_generate_resume_and_limit_compose():
    full = list(C.generate(1, 1, charset="abcd"))
    assert full == ["a", "b", "c", "d"]
    assert list(C.generate(1, 1, charset="abcd", resume_from="c")) == ["c", "d"]
    assert list(C.generate(1, 1, charset="abcd", limit=2)) == ["a", "b"]
    # skip first, then cap — like `crunch ... -s c -c 1`
    assert list(C.generate(1, 1, charset="abcd", resume_from="c", limit=1)) == ["c"]
    with pytest.raises(ValueError):
        list(C.generate(1, 1, charset="ab", limit=-1))


def test_charset_from_file(tmp_path):
    f = tmp_path / "charset.lst"
    f.write_text("# comment\n\nmix = abc123\nupper = ABC\n", encoding="utf-8")
    assert C.charset_from_file(str(f), name="mix") == "abc123"
    with pytest.raises(ValueError) as e:
        C.charset_from_file(str(f), name="nope")
    assert "available" in str(e.value)
    with pytest.raises(ValueError):
        C.charset_from_file(str(f))  # ambiguous without a name
    single = tmp_path / "single.lst"
    single.write_text("xyz\n", encoding="utf-8")
    assert C.charset_from_file(str(single)) == "xyz"


def test_write_wordlist_embedded_roundtrip(tmp_path):
    out = str(tmp_path / "words.txt")
    seen = []
    res = C.write_wordlist(out, 1, 2, charset="ab",
                           backend="embedded", progress=seen.append)
    assert res["backend"] == "embedded"
    assert res["entries"] == 6
    assert res["path"] == out
    lines = open(out, encoding="utf-8").read().splitlines()
    assert lines == ["a", "b", "aa", "ab", "ba", "bb"]
    assert res["bytes"] == os.path.getsize(out)
    assert seen and seen[-1] == 6  # progress ends on the final count


def test_write_wordlist_pattern_mode(tmp_path):
    out = str(tmp_path / "pin.txt")
    res = C.write_wordlist(out, 2, 2, pattern="9%", backend="embedded")
    assert res["entries"] == 10
    lines = open(out, encoding="utf-8").read().splitlines()
    assert lines[0] == "90" and lines[-1] == "99"


def test_write_wordlist_cap_refuses_huge_job(tmp_path):
    with pytest.raises(ValueError) as e:
        C.write_wordlist(str(tmp_path / "huge.txt"), 1, 8, backend="embedded")
    assert "over the" in str(e.value) and "allow_huge" in str(e.value)
    # explicit opt-in works (kept small via limit)
    res = C.write_wordlist(str(tmp_path / "ok.txt"), 1, 8, backend="embedded",
                           limit=5, allow_huge=True)
    assert res["entries"] == 5


def test_write_wordlist_system_backend(tmp_path, monkeypatch):
    out = str(tmp_path / "sys.txt")
    if C.detect_crunch() is None:
        # honest missing-binary error when backend is forced
        with pytest.raises(ValueError) as e:
            C.write_wordlist(out, 1, 1, charset="ab",
                             backend="system", cap=10)
        assert "crunch" in str(e.value).lower()
    else:
        # crunch present: passthrough must produce identical content
        res = C.write_wordlist(out, 1, 2, charset="ab", backend="system")
        assert res["backend"] == "system"
        assert res["entries"] == 6
        assert open(out, encoding="utf-8").read().splitlines() == \
            ["a", "b", "aa", "ab", "ba", "bb"]


def test_write_wordlist_system_forced_missing(monkeypatch, tmp_path):
    # forced system backend with no binary -> honest error (faked absence)
    monkeypatch.setattr(C, "detect_crunch", lambda: None)
    with pytest.raises(ValueError) as e:
        C.write_wordlist(str(tmp_path / "x.txt"), 1, 1, charset="ab",
                         backend="system", cap=10)
    assert "no `crunch` binary" in str(e.value)


def test_system_argv_shape():
    argv = C._system_argv(4, 4, "abcd", None, "o.txt", None, None)
    assert argv == ["crunch", "4", "4", "abcd", "-o", "o.txt"]
    argv = C._system_argv(6, 6, "ignored-charset", "@@@@%%", "o.txt", "ab12", 10)
    # pattern mode: charset deliberately NOT forwarded (fixed classes)
    assert argv == ["crunch", "6", "6", "-t", "@@@@%%",
                    "-s", "ab12", "-c", "10", "-o", "o.txt"]


def test_detect_crunch_returns_path_or_none():
    res = C.detect_crunch()
    assert res is None or isinstance(res, str)


def test_root_exports_match_module():
    import quantum
    assert quantum.crunch_estimate(1, 1, charset="ab") == 2
    assert list(quantum.crunch_generate(1, 1, charset="ab")) == ["a", "b"]
    assert "NOT bundled" in " ".join(quantum.CRUNCH_NOTE.split())
