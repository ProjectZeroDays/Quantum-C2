"""quantum.weapons.polymorph — PolyMorphEngineV3 (epoch keys, UTF-7, junk).

Per-beacon epoch HMAC key diversification + UTF-7 nil-escape variants + junk
filler. Identical plaintexts never produce identical wire bytes.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import random
import threading

from quantum.core.opsec import rand_hex


class PolyMorphEngineV3:
    MAGIC = b"PM3\x01"
    _EPOCH = [random.randint(1, 2 ** 40)]
    _LOCK = threading.Lock()

    @classmethod
    def _next_epoch(cls):
        with cls._LOCK:
            cls._EPOCH[0] += 1
            return cls._EPOCH[0] ^ int.from_bytes(os.urandom(4), "big")

    @staticmethod
    def _keystream(epoch, length):
        out = bytearray()
        counter = 0
        while len(out) < length:
            block = hmac.new(b"pm3-v3", epoch.to_bytes(8, "big") + b":" +
                            counter.to_bytes(8, "big"), hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    @staticmethod
    def _utf7_variant(epoch, data):
        # odd epochs serialize as UTF-7 with a |mode marker; even epochs plain.
        # Binary payloads that are not valid UTF-8 ship plain (junk+epoch still
        # diversify the wire bytes).
        if isinstance(data, str):
            data = data.encode("utf-8")
        if epoch % 2:
            try:
                return data.decode("utf-8").encode("utf-7") + b"|mode:utf7"
            except UnicodeDecodeError:
                return data
        return data

    @staticmethod
    def _strip_variant(blob):
        if blob.endswith(b"|mode:utf7"):
            return blob[:-len(b"|mode:utf7")].decode("utf-7").encode("utf-8")
        return blob

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        epoch = self._next_epoch()
        junk = os.urandom(random.randint(8, 64))
        payload = self._utf7_variant(epoch, data)
        ks = self._keystream(epoch, len(payload))
        body = bytes(a ^ b for a, b in zip(payload, ks))
        tag = hmac.new(b"pm3-tag", body, hashlib.sha256).digest()[:16]
        return (self.MAGIC + epoch.to_bytes(8, "big")
                + len(junk).to_bytes(2, "big") + junk + body + tag)

    def decrypt(self, blob):
        if not blob.startswith(self.MAGIC):
            raise ValueError("bad PM3 magic")
        off = len(self.MAGIC)
        epoch = int.from_bytes(blob[off:off + 8], "big")
        off += 8
        junk_len = int.from_bytes(blob[off:off + 2], "big")
        off += 2 + junk_len
        tag = blob[-16:]
        body = blob[off:-16]
        if not hmac.compare_digest(
                hmac.new(b"pm3-tag", body, hashlib.sha256).digest()[:16], tag):
            raise ValueError("PM3 tag mismatch")
        ks = self._keystream(epoch, len(body))
        payload = bytes(a ^ b for a, b in zip(body, ks))
        return self._strip_variant(payload)

    def polymorphize(self, text):
        """Morph text into junk-padded UTF-7 wire form (round-trips via
        depolymorphize). Junk lines vary per call; the P: payload does not."""
        payload = base64.b64encode(str(text).encode("utf-7")).decode("ascii")
        lines = ["J:" + rand_hex(8) for _ in range(random.randint(1, 5))]
        lines.append("P:" + payload)
        return "\n".join(lines)

    def depolymorphize(self, wire):
        payload = None
        for ln in str(wire).splitlines():
            if ln.startswith("P:"):
                payload = ln[2:]
        if payload is None:
            raise ValueError("no P: payload line in polymorph wire")
        return base64.b64decode(payload).decode("utf-7")
