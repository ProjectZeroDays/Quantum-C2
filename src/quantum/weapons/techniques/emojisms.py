"""quantum.weapons.techniques.emojisms — emoji covert channel.

base64 alphabet incl. + / = mapped to emoji glyphs.
"""
from __future__ import annotations

import base64
import string

_EMOJI_GLYPHS = [
    "\U0001F600", "\U0001F601", "\U0001F602", "\U0001F603", "\U0001F604",
    "\U0001F605", "\U0001F606", "\U0001F607", "\U0001F608", "\U0001F609",
    "\U0001F60A", "\U0001F60B", "\U0001F60C", "\U0001F60D", "\U0001F60E",
    "\U0001F60F", "\U0001F610", "\U0001F611", "\U0001F612", "\U0001F613",
    "\U0001F614", "\U0001F615", "\U0001F616", "\U0001F617", "\U0001F618",
    "\U0001F619", "\U0001F61A", "\U0001F61B", "\U0001F61C", "\U0001F61D",
    "\U0001F61E", "\U0001F61F", "\U0001F620", "\U0001F621", "\U0001F622",
    "\U0001F623", "\U0001F624", "\U0001F625", "\U0001F626", "\U0001F627",
    "\U0001F628", "\U0001F629", "\U0001F62A", "\U0001F62B", "\U0001F62C",
    "\U0001F62D", "\U0001F62E", "\U0001F62F", "\U0001F630", "\U0001F631",
    "\U0001F632", "\U0001F633", "\U0001F634", "\U0001F635", "\U0001F636",
    "\U0001F637", "\U0001F638", "\U0001F639", "\U0001F63A", "\U0001F63B",
    "\U0001F63C", "\U0001F63D", "\U0001F63E", "\U0001F923",
]
_B64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"

EMOJI_MAP = {ch: em for ch, em in zip(_B64_ALPHABET, _EMOJI_GLYPHS)}
EMOJI_MAP["="] = "\U0001F643"
EMOJI_REVERSE = {v: k for k, v in EMOJI_MAP.items()}


def emoji_encode(msg):
    """text -> utf-8 -> base64 -> one emoji glyph per base64 char."""
    blob = base64.b64encode(str(msg).encode("utf-8")).decode("ascii")
    return "".join(EMOJI_MAP[ch] for ch in blob)


def emoji_decode(emojis):
    """Reverse of emoji_encode — unknown glyphs skipped."""
    blob = "".join(EMOJI_REVERSE[ch] for ch in emojis if ch in EMOJI_REVERSE)
    pad = "=" * (-len(blob) % 4)
    return base64.b64decode(blob + pad).decode("utf-8")
