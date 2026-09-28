"""quantum.core.grayfish — sealed-loot at rest (AES-256-GCM).

logs/.lootkey is created once; deleting it breaks every sealed file —
treat as immutable.
"""
from __future__ import annotations

import hashlib
import os

from quantum.core.deps import AESGCM
from quantum.core.env import LOG_DIR
from quantum.core.logging import log
from quantum.core.opsec import rand_hex


class GrayFish:
    """Seal/unseal loot. The key at logs/.lootkey is created once."""

    def __init__(self, lootkey_path=None):
        self.lootkey_path = lootkey_path or os.path.join(LOG_DIR, ".lootkey")
        self._key = None

    @property
    def key(self):
        if self._key is None:
            os.makedirs(LOG_DIR, exist_ok=True)
            if not os.path.isfile(self.lootkey_path):
                with open(self.lootkey_path, "w", encoding="utf-8") as fh:
                    fh.write(rand_hex(32))
            with open(self.lootkey_path, "r", encoding="utf-8") as fh:
                self._key = hashlib.sha256(fh.read().strip().encode()).digest()
        return self._key

    def _seal_bytes(self, data):
        nonce = os.urandom(12)
        ct = nonce + AESGCM(self.key).encrypt(nonce, data, b"grayfish")
        return ct

    def _unseal_bytes(self, blob):
        return AESGCM(self.key).decrypt(blob[:12], blob[12:], b"grayfish")

    def seal(self, path):
        """Encrypt file -> <path>.gfy; returns the sealed path."""
        if path.endswith(".gfy"):
            return path
        with open(path, "rb") as fh:
            data = fh.read()
        sealed = path + ".gfy"
        with open(sealed, "wb") as fh:
            fh.write(self._seal_bytes(data))
        os.remove(path)
        return sealed

    def unseal(self, sealed_path):
        if not sealed_path.endswith(".gfy"):
            return sealed_path
        with open(sealed_path, "rb") as fh:
            data = self._unseal_bytes(fh.read())
        out = sealed_path[:-4]
        with open(out, "wb") as fh:
            fh.write(data)
        os.remove(sealed_path)
        return out

    def seal_dir(self, directory=None):
        """Seal every plaintext file in the loot dir."""
        from quantum.core.env import LOOT_DIR
        directory = directory or LOOT_DIR
        sealed = []
        for root, _dirs, files in os.walk(directory):
            for fn in files:
                p = os.path.join(root, fn)
                if not p.endswith(".gfy"):
                    try:
                        sealed.append(self.seal(p))
                    except Exception as exc:
                        log(f"seal {p}: {exc}", "WARN")
        if sealed:
            log(f"GRAYFISH: sealed {len(sealed)} loot file(s)", "OPSEC")
        return sealed

    def unseal_dir(self, directory=None):
        from quantum.core.env import LOOT_DIR
        directory = directory or LOOT_DIR
        unsealed = []
        for root, _dirs, files in os.walk(directory):
            for fn in files:
                p = os.path.join(root, fn)
                if p.endswith(".gfy"):
                    try:
                        unsealed.append(self.unseal(p))
                    except Exception as exc:
                        log(f"unseal fail {p} (lootkey intact?): {exc}", "ERR")
        return unsealed


GRAYFISH = GrayFish()
