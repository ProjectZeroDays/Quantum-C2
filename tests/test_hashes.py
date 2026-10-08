"""Tests for quantum.brute.hashes — real offline hash cracking."""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.brute.hashes import (  # noqa: E402
    brute_force_hashes,
    compute_hash,
    crack_hashes,
    cracking_dashboard_state,
    detect_hashcat,
    detect_john,
    hashcat_command,
    identify_hash,
    john_command,
    parse_hash_file,
    parse_pwdump,
)


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def test_md4_empty_vector():
    from quantum.brute.hashes import _md4
    assert _md4(b"").hex() == "31d6cfe0d16ae931b73c59d7e0c089c0"


def test_ntlm_known_vector():
    assert compute_hash("password", fmt="ntlm") == \
        "8846f7eaee8fb117ad06bdd830b7586c"


def test_compute_hash_roundtrip_all_plain_formats():
    for fmt in ("md5", "sha1", "sha256", "sha512", "ntlm"):
        h = compute_hash("s3cret!", fmt=fmt)
        res = crack_hashes([h], ["nope", "s3cret!"], fmt=fmt)
        assert res["hits"] and res["hits"][0]["password"] == "s3cret!"


def test_crack_miss_reports_tried():
    h = _md5("not-in-list")
    res = crack_hashes([h], ["a", "b"], fmt="md5")
    assert res["hits"] == [] and res["tried"] == 2


def test_brute_force_finds_short_password():
    h = _md5("ab")
    res = brute_force_hashes([h], fmt="md5", min_len=1, max_len=2,
                             charset="ab")
    assert res["hits"] and res["hits"][0]["password"] == "ab"


def test_identify_md5():
    assert "md5" in identify_hash("d" * 32)


def test_parse_pwdump():
    recs = parse_pwdump(
        "Administrator:500:aad3b435b51404eeaad3b435b51404ee:"
        "8846f7eaee8fb117ad06bdd830b7586c:::")
    assert recs and recs[0]["user"] == "Administrator"
    assert recs[0]["nt"] == "8846f7eaee8fb117ad06bdd830b7586c"
    assert recs[0]["lm_empty"] is True


def test_parse_hash_file_skips_blanks():
    recs = parse_hash_file("\n  \n" + "d" * 32 + "\n")
    assert [r["hash"] for r in recs] == ["d" * 32]
    assert recs[0]["fmt"] == "md5"


def test_hashcat_command_straight():
    argv = hashcat_command("h.txt", wordlist="w.txt", fmt="md5")
    assert argv[:5] == ["hashcat", "-m", "0", "-a", "0"]
    assert "h.txt" in argv and "w.txt" in argv


def test_john_command_format():
    argv = john_command("h.txt", wordlist="w.txt", fmt="ntlm")
    assert argv[0] == "john" and "--format=NT" in argv


def test_passthroughs_honest_when_absent():
    from quantum.brute.hashes import hashcat_run, john_run
    if detect_hashcat() is None:
        r = hashcat_run("h.txt", wordlist="w.txt", fmt="md5")
        assert r.get("error") and r.get("argv")
    if detect_john() is None:
        r = john_run("h.txt", wordlist="w.txt")
        assert r.get("error") and r.get("argv")


def test_dashboard_state_shape():
    s = cracking_dashboard_state()
    assert "md5" in s["formats"] and "ntlm" in s["formats"]
    assert s["attacks"]["sam_pwdump"] == "parse_pwdump()"
