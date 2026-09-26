"""test_polymorph — PolyMorphEngineV3 epoch/junk envelopes + UTF-7 round trip."""
import quantum_cli as q


def test_double_encrypt_same_data_differs():
    pm = q.PolyMorphEngineV3()
    a = pm.encrypt(b"same plaintext")
    b = pm.encrypt(b"same plaintext")
    assert a != b, "epoch+junk must make identical plaintexts differ on the wire"


def test_encrypt_decrypt_roundtrip():
    pm = q.PolyMorphEngineV3()
    for payload in (b"hello quantum", b"", bytes(range(256)),
                   "unicode \u00e9\u4e2d\u6587".encode("utf-8")):
        blob = pm.encrypt(payload)
        assert blob.startswith(b"PM3\x01")
        assert pm.decrypt(blob) == payload


def test_two_instances_share_epoch_counter():
    pm1 = q.PolyMorphEngineV3()
    pm2 = q.PolyMorphEngineV3()
    a = pm1.encrypt(b"x")
    b = pm2.encrypt(b"x")
    assert a != b
    assert pm2.decrypt(a) == b"x"
    assert pm1.decrypt(b) == b"x"


def test_bad_magic_rejected():
    pm = q.PolyMorphEngineV3()
    try:
        pm.decrypt(b"XXXX" + b"\x00" * 32)
    except ValueError:
        pass
    else:
        raise AssertionError("bad magic must raise ValueError")


def test_polymorphize_roundtrips_utf7():
    pm = q.PolyMorphEngineV3()
    for text in ("ping", "operator + command", "\u00e9\u4e2d\u6587 utf7 \u2603"):
        wire = pm.polymorphize(text)
        assert wire.startswith("J:") or wire.startswith("P:")
        assert pm.depolymorphize(wire) == text


def test_polymorphize_junk_varies():
    pm = q.PolyMorphEngineV3()
    a = pm.polymorphize("same")
    b = pm.polymorphize("same")
    assert a != b
    assert pm.depolymorphize(a) == "same" == pm.depolymorphize(b)
