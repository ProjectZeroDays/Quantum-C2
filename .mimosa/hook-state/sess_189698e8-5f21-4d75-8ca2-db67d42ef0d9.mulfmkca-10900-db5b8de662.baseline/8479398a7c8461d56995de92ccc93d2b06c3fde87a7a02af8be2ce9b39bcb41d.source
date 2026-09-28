"""quantum.weapons.techniques.cagebreak — sandbox/VM/cloud escape assessment."""
from __future__ import annotations

from quantum.core.env import OS_NAME
from quantum.core.logging import log
from quantum.core.opsec import run


def cagebreak():
    """CAGEBREAK: sandbox / VM / cloud-escape environment assessment.
    Enumerates the signals that matter for picking the right escape, includes
    real CVE-based escape staging (MSHTML 40444 forge elsewhere in registry)."""
    env = {}
    if OS_NAME == "Windows":
        try:
            comp = run("powershell -NoProfile -Command (Get-WmiObject Win32_ComputerSystem).Manufacturer; "
                       "(Get-WmiObject Win32_ComputerSystem).Model").stdout
            blob = (comp or "").lower()
            env["vm"] = any(m in blob for m in ("vmware", "virtual", "kvm", "qemu", "xen", "hyper-v", "innotek"))
            env["sandbox"] = any(s in blob for s in ("sandbox", "sandboxie")) or \
                             _isdir(r"C:\Sandbox")
            blob2 = (run("powershell -NoProfile -Command (Get-WmiObject Win32_BIOS).SerialNumber").stdout or "").lower()
            dev = any(t is not None for t in [
                "amazon" in blob2, "google" in blob2, "azure" in blob2 and "cloud" in blob2])
            env["cloud"] = dev
        except Exception as e:
            env["probe_error"] = str(e)
    else:
        blob = (run("SYSTEMD_ALLOW_RESULT=1 systemd-detect-virt 2>/dev/null || dmesg 2>/dev/null | head -50").stdout or "").lower()
        env["vm"] = any(m in blob for m in ("kvm", "vmware", "xen", "qemu", "virtualbox", "microsoft"))
        env["cloud"] = any(m in blob for m in ("amazon", "ec2", "openstack")) or _isdir("/var/lib/cloud")
    log(f"CAGEBREAK env: {env}", "TAO")
    return env


def _isdir(p):
    import os
    return os.path.isdir(p)
