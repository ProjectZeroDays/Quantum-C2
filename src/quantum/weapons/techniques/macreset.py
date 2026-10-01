"""quantum.weapons.techniques.macreset — recovery-mode credential reset."""
from __future__ import annotations

import os

from quantum.core.env import QCLI_DIR
from quantum.core.logging import log


def macos_recovery_reset():
    """MacReset: generates the recovery-mode credential reset script.
    Boot to macOS Recovery -> Terminal -> run this (user-requested 'reset mac
    password via terminal at boot in recovery')."""
    script = (
        "#!/bin/sh\n"
        "# QCLI MacReset — run from macOS Recovery Mode Terminal\n"
        "# List volumes to locate the system disk:\n"
        "diskutil list\n"
        "# Preferred (GUI, all recent macOS):\n"
        "open \"/System/Applications/Utilities/Reset Password.app\" 2>/dev/null || \\\n"
        "open \"/System/Library/CoreServices/Reset Password.app\" 2>/dev/null || \\\n"
        "resetpassword 2>/dev/null\n"
        "# CLI variant (Big Sur+):\n"
        "# launchctl load /System/Library/LaunchDaemons/com.apple.opensshd.plist\n"
        "# dscl . -create /Users/admin2 UniqueID 503 PrimaryGroupID 80 UserShell /bin/bash\n"
        "# dscl . -passwd /Users/admin2 'NewPass123!'\n"
        "# resetpassword alternative: use `resetpassword` on older,\n"
        "# or SysPrefs > Users & Groups after mount -uw /\n"
    )
    fn = os.path.join(QCLI_DIR, "macreset.sh")
    open(fn, "w").write(script)
    try: os.chmod(fn, 0o755)
    except OSError as e: log(f"macreset.sh chmod failed: {e}", "WARN")
    log("MacReset armed: macreset.sh (run from Recovery Terminal)", "ATK")
    return fn
