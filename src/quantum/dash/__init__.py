"""quantum.dash — QUANTUMDASH operator dashboard (dark, cyan, 3s refresh)."""
from __future__ import annotations

DASH_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>QUANTUMDASH</title>
<style>
  body { background:#02040a; color:#00e5ff; font-family:'Cascadia Mono',monospace;
        margin:0; padding:24px; }
  h1 { font-size:20px; letter-spacing:2px; border-bottom:1px solid #00e5ff;
       padding-bottom:8px; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
  .card { background:#050b18; border:1px solid #123; padding:12px; border-radius:6px; }
  .card h2 { color:#7fdbff; font-size:14px; margin:0 0 8px 0; }
  pre { white-space:pre-wrap; font-size:12px; color:#9ad; max-height:300px;
       overflow:auto; }
  .kill { color:#ff5370; font-weight:bold; }
  .ok { color:#3aff9e; }
  .nav { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0; }
  .nav button { background:#0a1628; color:#00e5ff; border:1px solid #1a3a5c;
               padding:6px 12px; border-radius:4px; cursor:pointer; font-size:12px; }
  .nav button:hover { background:#0d2240; }
  .nav button.active { background:#0d2240; border-color:#00e5ff; }
  .module { display:none; }
  .module.active { display:block; }
  .status-bar { display:flex; gap:16px; margin:8px 0; font-size:11px; }
  .status-item { display:flex; align-items:center; gap:4px; }
  .status-dot { width:8px; height:8px; border-radius:50%; }
  .status-green { background:#3aff9e; }
  .status-red { background:#ff5370; }
  .status-amber { background:#ffb86c; }
  .status-grey { background:#666; }
  .status-blue { background:#00e5ff; }
  table { width:100%; border-collapse:collapse; font-size:11px; }
  th, td { text-align:left; padding:4px 8px; border-bottom:1px solid #1a3a5c; }
  th { color:#7fdbff; }
  .badge { display:inline-block; padding:2px 6px; border-radius:3px; font-size:10px; }
  .badge-green { background:#0a2a1a; color:#3aff9e; }
  .badge-red { background:#2a0a0a; color:#ff5370; }
  .badge-amber { background:#2a1a0a; color:#ffb86c; }
  .badge-grey { background:#1a1a1a; color:#666; }
  .badge-blue { background:#0a1a2a; color:#00e5ff; }
</style></head>
<body>
<h1>QUANTUMDASH — Operator Console</h1>
<div class="kill" id="killswitch">killswitch: …</div>
<div class="status-bar">
  <div class="status-item"><span class="status-dot status-green" id="status-c2"></span>C2</div>
  <div class="status-item"><span class="status-dot status-green" id="status-ai"></span>AI</div>
  <div class="status-item"><span class="status-dot status-green" id="status-tor"></span>Tor</div>
  <div class="status-item"><span class="status-dot status-green" id="status-vpn"></span>VPN</div>
  <div class="status-item"><span class="status-dot status-green" id="status-dns"></span>DNS</div>
  <div class="status-item"><span class="status-dot status-green" id="status-model"></span>Model</div>
</div>
<div class="nav">
  <button class="active" onclick="showModule('home')">Home</button>
  <button onclick="showModule('osint')">OSINT</button>
  <button onclick="showModule('rat')">RAT</button>
  <button onclick="showModule('ransomware')">Ransomware</button>
  <button onclick="showModule('botnet')">Botnet</button>
  <button onclick="showModule('ddos')">DDoS</button>
  <button onclick="showModule('messaging')">Messaging</button>
  <button onclick="showModule('stego')">Stego</button>
  <button onclick="showModule('router')">Router</button>
  <button onclick="showModule('apn')">APN</button>
  <button onclick="showModule('exif')">EXIF</button>
  <button onclick="showModule('darkweb')">Dark Web</button>
  <button onclick="showModule('dorks')">Dorks</button>
  <button onclick="showModule('shodan')">Shodan</button>
  <button onclick="showModule('map2d')">2D Map</button>
  <button onclick="showModule('phantomdroid')">PhantomDroid</button>
  <button onclick="showModule('dohshell')">DoH Shell</button>
</div>

<div id="home" class="module active">
  <div class="grid">
    <div class="card"><h2>Decisions</h2><pre id="decisions">…</pre></div>
    <div class="card"><h2>Engagement log</h2><pre id="audit">…</pre></div>
    <div class="card"><h2>MITRE coverage</h2><pre id="mitre">…</pre></div>
    <div class="card"><h2>Implants</h2><pre id="implants">…</pre></div>
  </div>
</div>

<div id="osint" class="module">
  <div class="grid">
    <div class="card"><h2>IP Download Tracking</h2><pre id="osint-ip">…</pre></div>
    <div class="card"><h2>IMEI Tracking</h2><pre id="osint-imei">…</pre></div>
    <div class="card"><h2>Phone Location</h2><pre id="osint-phone">…</pre></div>
    <div class="card"><h2>EXIF Analysis</h2><pre id="osint-exif">…</pre></div>
  </div>
</div>

<div id="rat" class="module">
  <div class="grid">
    <div class="card"><h2>RAT Repositories</h2><pre id="rat-repos">…</pre></div>
    <div class="card"><h2>mSpy Features</h2><pre id="rat-features">…</pre></div>
    <div class="card"><h2>Messaging Apps</h2><pre id="rat-messaging">…</pre></div>
    <div class="card"><h2>Server Status</h2><pre id="rat-status">…</pre></div>
  </div>
</div>

<div id="ransomware" class="module">
  <div class="grid">
    <div class="card"><h2>Ransomware Tools</h2><pre id="ransomware-tools">…</pre></div>
    <div class="card"><h2>Deployment Modules</h2><pre id="ransomware-modules">…</pre></div>
    <div class="card"><h2>Active Deployments</h2><pre id="ransomware-deployments">…</pre></div>
    <div class="card"><h2>Statistics</h2><pre id="ransomware-stats">…</pre></div>
  </div>
</div>

<div id="botnet" class="module">
  <div class="grid">
    <div class="card"><h2>Botnet Types</h2><pre id="botnet-types">…</pre></div>
    <div class="card"><h2>Capabilities</h2><pre id="botnet-capabilities">…</pre></div>
    <div class="card"><h2>Active Bots</h2><pre id="botnet-bots">…</pre></div>
    <div class="card"><h2>Server Status</h2><pre id="botnet-status">…</pre></div>
  </div>
</div>

<div id="ddos" class="module">
  <div class="grid">
    <div class="card"><h2>DDoS Tools</h2><pre id="ddos-tools">…</pre></div>
    <div class="card"><h2>Techniques</h2><pre id="ddos-techniques">…</pre></div>
    <div class="card"><h2>Active Attacks</h2><pre id="ddos-attacks">…</pre></div>
    <div class="card"><h2>Statistics</h2><pre id="ddos-stats">…</pre></div>
  </div>
</div>

<div id="messaging" class="module">
  <div class="grid">
    <div class="card"><h2>Platforms</h2><pre id="messaging-platforms">…</pre></div>
    <div class="card"><h2>Social Engineering</h2><pre id="messaging-techniques">…</pre></div>
    <div class="card"><h2>Voice Clone</h2><pre id="messaging-voice">…</pre></div>
    <div class="card"><h2>Face Clone</h2><pre id="messaging-face">…</pre></div>
  </div>
</div>

<div id="stego" class="module">
  <div class="grid">
    <div class="card"><h2>Steganography Methods</h2><pre id="stego-methods">…</pre></div>
    <div class="card"><h2>PDF Exploits</h2><pre id="stego-pdf">…</pre></div>
    <div class="card"><h2>Messenger Chains</h2><pre id="stego-messenger">…</pre></div>
    <div class="card"><h2>Active Operations</h2><pre id="stego-ops">…</pre></div>
  </div>
</div>

<div id="router" class="module">
  <div class="grid">
    <div class="card"><h2>Vulnerabilities</h2><pre id="router-vulns">…</pre></div>
    <div class="card"><h2>Default Credentials</h2><pre id="router-creds">…</pre></div>
    <div class="card"><h2>Attack Methods</h2><pre id="router-methods">…</pre></div>
    <div class="card"><h2>Active Attacks</h2><pre id="router-attacks">…</pre></div>
  </div>
</div>

<div id="apn" class="module">
  <div class="grid">
    <div class="card"><h2>Hardware</h2><pre id="apn-hardware">…</pre></div>
    <div class="card"><h2>Attack Methods</h2><pre id="apn-methods">…</pre></div>
    <div class="card"><h2>Discovered Beacons</h2><pre id="apn-beacons">…</pre></div>
    <div class="card"><h2>Active Attacks</h2><pre id="apn-attacks">…</pre></div>
  </div>
</div>

<div id="exif" class="module">
  <div class="grid">
    <div class="card"><h2>Analyzed Images</h2><pre id="exif-images">…</pre></div>
    <div class="card"><h2>GPS Coordinates</h2><pre id="exif-gps">…</pre></div>
    <div class="card"><h2>Camera Info</h2><pre id="exif-camera">…</pre></div>
    <div class="card"><h2>Hidden Data</h2><pre id="exif-hidden">…</pre></div>
  </div>
</div>

<div id="darkweb" class="module">
  <div class="grid">
    <div class="card"><h2>Search Engines</h2><pre id="darkweb-search">…</pre></div>
    <div class="card"><h2>Marketplaces</h2><pre id="darkweb-markets">…</pre></div>
    <div class="card"><h2>Forums</h2><pre id="darkweb-forums">…</pre></div>
    <div class="card"><h2>Email Services</h2><pre id="darkweb-email">…</pre></div>
  </div>
</div>

<div id="dorks" class="module">
  <div class="grid">
    <div class="card"><h2>Camera Dorks</h2><pre id="dorks-cameras">…</pre></div>
    <div class="card"><h2>Directory Dorks</h2><pre id="dorks-dirs">…</pre></div>
    <div class="card"><h2>Sensitive Files</h2><pre id="dorks-files">…</pre></div>
    <div class="card"><h2>Vulnerable Servers</h2><pre id="dorks-servers">…</pre></div>
  </div>
</div>

<div id="shodan" class="module">
  <div class="grid">
    <div class="card"><h2>Preset Queries</h2><pre id="shodan-presets">…</pre></div>
    <div class="card"><h2>Recent Searches</h2><pre id="shodan-searches">…</pre></div>
    <div class="card"><h2>API Status</h2><pre id="shodan-status">…</pre></div>
    <div class="card"><h2>Results</h2><pre id="shodan-results">…</pre></div>
  </div>
</div>

<div id="map2d" class="module">
  <div class="grid">
    <div class="card"><h2>Beacons</h2><pre id="map2d-beacons">…</pre></div>
    <div class="card"><h2>Map Center</h2><pre id="map2d-center">…</pre></div>
    <div class="card"><h2>Bounds</h2><pre id="map2d-bounds">…</pre></div>
    <div class="card"><h2>Statistics</h2><pre id="map2d-stats">…</pre></div>
  </div>
</div>

<div id="phantomdroid" class="module">
  <div class="grid">
    <div class="card"><h2>Connected Devices</h2><pre id="phantomdroid-devices">…</pre></div>
    <div class="card"><h2>Features</h2><pre id="phantomdroid-features">…</pre></div>
    <div class="card"><h2>Device Info</h2><pre id="phantomdroid-info">…</pre></div>
    <div class="card"><h2>Screen Capture</h2><pre id="phantomdroid-screen">…</pre></div>
  </div>
</div>

<div id="dohshell" class="module">
  <div class="grid">
    <div class="card"><h2>Active Targets</h2><pre id="dohshell-targets">…</pre></div>
    <div class="card"><h2>Agent Generator</h2><pre id="dohshell-agent">…</pre></div>
    <div class="card"><h2>Task Queue</h2><pre id="dohshell-tasks">…</pre></div>
    <div class="card"><h2>C2 Config</h2><pre id="dohshell-config">…</pre></div>
  </div>
</div>

<script>
function showModule(name) {
  document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
  document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  event.target.classList.add('active');
  loadModuleData(name);
}

async function loadModuleData(name) {
  try {
    const r = await fetch('/dash/api/state');
    const s = await r.json();
    if (name === 'home') {
      document.getElementById('killswitch').textContent = 'killswitch: ' + (s.killswitch ? 'ARMED' : 'disarmed');
      document.getElementById('decisions').textContent = JSON.stringify(s.decisions || [], null, 1).slice(0, 4000);
      document.getElementById('audit').textContent = JSON.stringify(s.audit || [], null, 1).slice(-4000);
      document.getElementById('mitre').textContent = JSON.stringify(s.mitre || [], null, 1);
      document.getElementById('implants').textContent = JSON.stringify(s.implants || {}, null, 1);
    }
  } catch (e) {}
}

async function tick() {
  try {
    const r = await fetch('/dash/api/state');
    const s = await r.json();
    document.getElementById('killswitch').textContent = 'killswitch: ' + (s.killswitch ? 'ARMED' : 'disarmed');
    document.getElementById('decisions').textContent = JSON.stringify(s.decisions || [], null, 1).slice(0, 4000);
    document.getElementById('audit').textContent = JSON.stringify(s.audit || [], null, 1).slice(-4000);
    document.getElementById('mitre').textContent = JSON.stringify(s.mitre || [], null, 1);
    document.getElementById('implants').textContent = JSON.stringify(s.implants || {}, null, 1);
  } catch (e) {}
}
setInterval(tick, 3000); tick();
</script>
</body></html>
"""
