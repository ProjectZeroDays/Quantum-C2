"""Tests for quantum.brute.vaults — real vault/archive password oracles."""
import base64
import hashlib
import hmac as hmac_mod
import os
import shutil
import struct
import subprocess
import sys
import zlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.brute.vaults import (  # noqa: E402
    TC_PRF_ITERATIONS,
    VC_DEFAULT_ITERATIONS,
    VC_RIPEMD160_ITERATIONS,
    VC_RIPEMD160_SYSTEM_ITERATIONS,
    VC_SYSTEM_FAST_ITERATIONS,
    _pbkdf2,
    archive_password_check,
    cryptomator_masterkey_check,
    truecrypt_header_password_check,
    veracrypt_header_password_check,
    veracrypt_iterations,
    xts_decrypt_unit,
)

crypt = pytest.importorskip("cryptography.hazmat.primitives.ciphers",
                            reason="cryptography lib needed for XTS fixtures")


def _xts_encrypt(data_key, tweak_key, plaintext, unit_no=0):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    enc = Cipher(algorithms.AES(data_key + tweak_key),
                 modes.XTS(unit_no.to_bytes(16, "little"))).encryptor()
    return enc.update(plaintext) + enc.finalize()


def _build_header(magic, password, prf="sha512", iterations=500000):
    salt = os.urandom(64)
    dk = _pbkdf2(prf, password.encode(), salt, iterations, 192)
    pt = bytearray(os.urandom(448))
    pt[0:4] = magic
    pt[4:6] = struct.pack(">H", 5)
    pt[6:8] = struct.pack(">H", 5)
    pt[64:68] = struct.pack(">I", 512)
    pt[8:12] = struct.pack(">I", zlib.crc32(bytes(pt[192:448])) & 0xFFFFFFFF)
    pt[188:192] = struct.pack(">I", zlib.crc32(bytes(pt[:188])) & 0xFFFFFFFF)
    ct = _xts_encrypt(dk[:32], dk[32:64], bytes(pt))
    return salt + ct


def test_xts_matches_cryptography_lib():
    dk, tk = os.urandom(32), os.urandom(32)
    pt = os.urandom(64)
    ct = _xts_encrypt(dk, tk, pt)
    assert xts_decrypt_unit(dk, tk, ct) == pt


def test_iteration_tables():
    assert veracrypt_iterations("sha512") == VC_DEFAULT_ITERATIONS == 500000
    assert veracrypt_iterations("ripemd160") == VC_RIPEMD160_ITERATIONS
    assert veracrypt_iterations("sha256", system=True) == \
        VC_SYSTEM_FAST_ITERATIONS == 200000
    assert veracrypt_iterations("ripemd160", system=True) == \
        VC_RIPEMD160_SYSTEM_ITERATIONS
    assert veracrypt_iterations("sha512", pim=5) == 15000 + 5 * 1000
    assert veracrypt_iterations("sha256", pim=5, system=True) == 5 * 2048
    assert TC_PRF_ITERATIONS == {"ripemd160": 2000, "sha512": 1000,
                                 "whirlpool": 1000, "sha1": 1000}


def test_veracrypt_roundtrip():
    hdr = _build_header(b"VERA", "correct-horse", iterations=500000)
    ok = veracrypt_header_password_check(hdr, "correct-horse")
    assert ok["ok"] and all(ok["checks"].values())
    bad = veracrypt_header_password_check(hdr, "wrong-password")
    assert bad["ok"] is False


def test_truecrypt_roundtrip_ripemd160():
    hdr = _build_header(b"TRUE", "tc-secret", prf="ripemd160",
                        iterations=2000)
    ok = truecrypt_header_password_check(hdr, "tc-secret")
    assert ok["ok"] and ok["prf"] == "ripemd160"
    bad = truecrypt_header_password_check(hdr, "nope", prf="ripemd160")
    assert bad["ok"] is False


def test_unavailable_prf_is_honest():
    hdr = os.urandom(512)
    for prf in ("whirlpool", "streebog"):
        res = veracrypt_header_password_check(hdr, "pw", prf=prf)
        assert res["ok"] is False and res.get("error")


def test_cryptomator_roundtrip():
    Crypto = pytest.importorskip("Crypto", reason="pycryptodome needed")
    from Crypto.Cipher import AES
    password = "vault-pw"
    salt = os.urandom(16)
    kek = hashlib.scrypt(password.encode(), salt=salt, n=2 ** 15, r=8,
                         p=1, dklen=32,
                         maxmem=max(128 * (2 ** 15) * 8 * 2, 64 << 20))
    primary, mac_key = os.urandom(32), os.urandom(32)
    mk = {"version": 8,
          "scryptSalt": base64.b64encode(salt).decode(),
          "scryptCostParam": 2 ** 15, "scryptBlockSize": 8,
          "primaryMasterKey": base64.b64encode(
              AES.new(kek, AES.MODE_KW).seal(primary)).decode(),
          "hmacMasterKey": base64.b64encode(
              AES.new(kek, AES.MODE_KW).seal(mac_key)).decode(),
          "versionMac": base64.b64encode(
              hmac_mod.new(mac_key, struct.pack(">I", 8),
                           hashlib.sha256).digest()).decode()}
    assert cryptomator_masterkey_check(mk, password)["ok"] is True
    assert cryptomator_masterkey_check(mk, "wrong")["ok"] is False


def test_zip_roundtrip():
    if shutil.which("zip") is None:
        pytest.skip("system zip(1) not installed")
    import tempfile
    from quantum.brute.vaults import zip_password_check
    with tempfile.TemporaryDirectory() as td:
        plain = os.path.join(td, "secret.txt")
        arch = os.path.join(td, "test.zip")
        open(plain, "w").write("top secret loot")
        subprocess.run(["zip", "-q", "-P", "zippass", arch, plain],
                       check=True)
        assert zip_password_check(arch, "zippass")["ok"] is True
        assert zip_password_check(arch, "wrong")["ok"] is False


def test_7z_roundtrip():
    if shutil.which("7z") is None and shutil.which("7zz") is None:
        pytest.skip("7z not installed")
    import tempfile
    from quantum.brute.vaults import sevenz_test_password
    with tempfile.TemporaryDirectory() as td:
        plain = os.path.join(td, "secret.txt")
        arch = os.path.join(td, "test.7z")
        open(plain, "w").write("top secret loot")
        seven = shutil.which("7z") or shutil.which("7zz")
        subprocess.run([seven, "a", "-p" + "zippass", arch, plain],
                       check=True, capture_output=True)
        assert sevenz_test_password(arch, "zippass")["ok"] is True
        assert sevenz_test_password(arch, "wrong")["ok"] is False


def test_archive_dispatch_zip(tmp_path):
    if shutil.which("zip") is None:
        pytest.skip("system zip(1) not installed")
    plain = tmp_path / "s.txt"
    plain.write_text("x")
    arch = str(tmp_path / "a.zip")
    subprocess.run(["zip", "-q", "-P", "pw123", arch, str(plain)],
                   check=True)
    assert archive_password_check(arch, "pw123")["ok"] is True
