"""test_emoji — EMOJISMS round trip incl. the + / = base64 alphabet."""
import base64

import quantum_cli as q


def test_roundtrip_simple():
    assert q.emoji_decode(q.emoji_encode("ping")) == "ping"


def test_roundtrip_plus_slash_equals_alphabet():
    # payloads whose base64 uses every alphabet corner: +, / and = padding
    payloads = [
        "a",                                   # YQ==  (padding)
        "ma",                                  # bWE=  (padding + letters)
        bytes([0xFB, 0xFF, 0xBE, 0xEF]).decode("latin-1"),  # +/ dense
        bytes([0xFF, 0xFF, 0xFF]).decode("latin-1"),         # ////
        bytes([0xFB, 0xFB]).decode("latin-1"),               # ++++
        "quantum-cli v3.1 \u00e9\u4e2d\u6587",
        "",
    ]
    for text in payloads:
        encoded = q.emoji_encode(text)
        # every glyph must come from the map (proves + / = are mapped)
        for ch in encoded:
            assert ch in q.EMOJI_REVERSE, f"unmapped glyph for {text!r}"
        assert q.emoji_decode(encoded) == text, f"roundtrip failed for {text!r}"


def test_alphabet_covers_65_glyphs():
    import string
    alphabet = string.ascii_uppercase + string.ascii_lowercase \
        + string.digits + "+/"
    for ch in alphabet + "=":
        assert ch in q.EMOJI_MAP
    assert len(q.EMOJI_MAP) == 65
    assert len(q.EMOJI_REVERSE) == 65


def test_decode_skips_unknown_glyphs():
    encoded = q.emoji_encode("ok")
    noisy = "X" + encoded + "!"
    assert q.emoji_decode(noisy) == "ok"


def test_known_encoding_shape():
    # base64("ping") == "cGluZw==" — must map through the emoji alphabet
    raw = base64.b64encode(b"ping").decode()
    assert q.emoji_encode("ping") == "".join(q.EMOJI_MAP[c] for c in raw)
