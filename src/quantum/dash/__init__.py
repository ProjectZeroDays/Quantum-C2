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
  <button onclick="showModule('listeners')">Listeners</button>
  <button onclick="showModule('vendors')">OSINT Vendors</button>
  <button onclick="showModule('crack')">Crack</button>
  <button onclick="showModule('console')">Console</button>
  <button onclick="showModule('ai')">AI</button>
  <button onclick="showModule('lifecycle')">Lifecycle</button>
  <button onclick="showModule('loot')">Loot</button>
  <button onclick="showModule('iot')">IoT</button>
  <button onclick="showModule('openfable')">OpenFable</button>
  <button onclick="showModule('autoconfig')">Auto-Config</button>
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

<div id="listeners" class="module">
  <div class="grid">
    <div class="card"><h2>Active Listeners</h2><pre id="listeners-active">…</pre></div>
    <div class="card"><h2>Deploy Listener</h2><pre id="listeners-deploy">…</pre></div>
    <div class="card"><h2>Hit Log</h2><pre id="listeners-hits">…</pre></div>
    <div class="card"><h2>Statistics</h2><pre id="listeners-stats">…</pre></div>
  </div>
</div>

<div id="vendors" class="module">
  <div class="grid">
    <div class="card"><h2>Intelligence X</h2><pre id="vendors-intelx">…</pre></div>
    <div class="card"><h2>ShadowDragon</h2><pre id="vendors-shadowdragon">…</pre></div>
    <div class="card"><h2>DarkOwl Vision</h2><pre id="vendors-darkowl">…</pre></div>
    <div class="card"><h2>Vendor search (POST /api/osint/&lt;vendor&gt;/…)</h2><pre id="vendors-help">intelx: POST /api/osint/intelx/search {query}
phonebook: POST /api/osint/intelx/phonebook {value}
plan: POST /api/osint/shadowdragon/plan {subject_type, subject_value}
darkowl: POST /api/osint/darkowl/search {query}</pre></div>
  </div>
</div>

<div id="crack" class="module">
  <div class="grid">
    <div class="card"><h2>Hash formats</h2><pre id="crack-formats">…</pre></div>
    <div class="card"><h2>Hash crack (POST /api/crack/hash {targets, wordlist, fmt})</h2><pre id="crack-hash">…</pre></div>
    <div class="card"><h2>Vault / archive (POST /api/crack/vault {target, password, kind})</h2><pre id="crack-vault">…</pre></div>
    <div class="card"><h2>Services + recent runs</h2><pre id="crack-services">…</pre></div>
  </div>
</div>

<div id="console" class="module">
  <div class="grid">
    <div class="card"><h2>Agents</h2><pre id="console-agents">…</pre></div>
    <div class="card"><h2>Skills</h2><pre id="console-skills">…</pre></div>
    <div class="card"><h2>Workflows</h2><pre id="console-workflows">…</pre></div>
    <div class="card"><h2>Commands / tasks / events</h2><pre id="console-commands">…</pre></div>
  </div>
</div>

<div id="ai" class="module">
  <div class="grid">
    <div class="card"><h2>Providers (key status)</h2><pre id="ai-providers">…</pre></div>
    <div class="card"><h2>Get API key</h2><div id="ai-keys">…</div></div>
    <div class="card"><h2>Free models</h2><pre id="ai-models">…</pre></div>
    <div class="card"><h2>Uncensored models</h2><pre id="ai-uncensored">…</pre></div>
  </div>
</div>

<div id="lifecycle" class="module">
  <div class="grid">
    <div class="card"><h2>7-phase chain</h2><pre id="lifecycle-chain">…</pre></div>
    <div class="card"><h2>Phase agents</h2><pre id="lifecycle-agents">…</pre></div>
    <div class="card"><h2>Loot inventory</h2><pre id="lifecycle-loot">…</pre></div>
    <div class="card"><h2>Run (POST /api/lifecycle/run {scope, variables})</h2><pre id="lifecycle-runs">…</pre></div>
  </div>
</div>

<div id="loot" class="module">
  <div class="grid">
    <div class="card"><h2>Cookie hosts</h2><pre id="loot-cookies">…</pre></div>
    <div class="card"><h2>Replay (POST /api/cookies/&lt;host&gt;/replay {url})</h2><pre id="loot-replay">POST a jar via /api/cookies/&lt;host&gt; {cookies|text}, then replay it against an in-scope URL to validate the session.</pre></div>
  </div>
</div>

<div id="iot" class="module">
  <div class="grid">
    <div class="card"><h2>Exploit catalog</h2><pre id="iot-exploits">…</pre></div>
    <div class="card"><h2>Device families</h2><pre id="iot-families">…</pre></div>
    <div class="card"><h2>Discovered devices (POST /api/iot/discover {cidr})</h2><pre id="iot-devices">…</pre></div>
    <div class="card"><h2>CVE feed + whitepaper (GET /api/iot/cve?q= · POST /api/iot/whitepaper {id})</h2><pre id="iot-cve">…</pre></div>
    <div class="card"><h2>Payload generator (POST /api/iot/payload {kind, params})</h2><pre id="iot-payload">…</pre></div>
    <div class="card"><h2>Drones + cameras + map</h2><pre id="iot-drones">…</pre></div>
  </div>
</div>

<div id="autoconfig" class="module">
  <h2>Auto-Config (Host-Aware Defaults)</h2>
  <p>Real OS/detection + dependency/network check sets best defaults per tool.</p>
  <div class="card"><h3>Host Profile</h3><pre id="autoconfig-host">Detecting...</pre></div>
  <div class="card"><h3>Tool Defaults</h3><pre id="autoconfig-defaults">Botnet → HTTPS / IoT / C2 proxy chain; Crypto → real file paths; ADB → USB debug; Pivot → subnet based on net_hint; DDOS → tcp/80</pre></div>
  <button onclick="fetch('/api/autoconfig/dashboard').then(r=>r.json()).then(d=>document.getElementById('autoconfig-host').textContent=JSON.stringify(d.host_profile,null,2))">Refresh</button>
</div>

<div id="openfable" class="module">
  <div class="grid">
    <div class="card"><h2>OpenFable mode</h2><div id="of-mode"><b>OpenFable is available — how do you want to work with it?</b></div></div>
    <div class="card"><h2>Install + headless server</h2><pre id="of-server">…</pre>
      <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
        <button onclick="ofStartServer()">Start server</button>
        <button onclick="ofStopServer()">Stop server</button>
        <button onclick="ofTerminal()">Launch TUI</button>
      </div>
    </div>
    <div class="card"><h2>GUI chat widget</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px">
        <select id="of-model-select" onchange="OF.model=this.value" style="max-width:280px"><option value="">model… (Load models)</option></select>
        <button onclick="ofLoadModels()">Load models</button>
        <button onclick="ofNewSession()">New session</button>
        <button onclick="ofAbort()">Abort turn</button>
      </div>
      <div id="of-chat-log" style="max-height:260px;overflow:auto;background:#0b0f14;border:1px solid #1e2a36;border-radius:6px;padding:8px;white-space:pre-wrap;min-height:80px">No session yet — pick a mode or press New session.</div>
      <div style="display:flex;gap:6px;margin-top:6px">
        <input id="of-input" placeholder="message to OpenFable…" style="flex:1" onkeydown="if(event.key==='Enter'){ofSend();}">
        <button onclick="ofSend()">Send</button>
      </div>
      <div id="of-chat-status" style="color:#9fb0c0;min-height:16px"></div>
    </div>
    <div class="card"><h2>Models (GET /api/openfable/models)</h2><pre id="of-models">…</pre></div>
    <div class="card"><h2>Sessions (GET /api/openfable/sessions)</h2><pre id="of-sessions">…</pre></div>
    <div class="card"><h2>One-shot run (POST /api/openfable/run {message})</h2><pre id="of-run">Runs openfable headless via the CLI and returns its real output.</pre>
      <div style="display:flex;gap:6px;margin-top:6px">
        <input id="of-run-input" placeholder="one-shot message…" style="flex:1">
        <button onclick="ofRun()">Run</button>
      </div>
    </div>
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

// ---- OpenFable widget (terminal TUI / GUI chat) ----
const OF = {sid: null, model: '', log: []};

function ofEsc(t) {
  return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function ofRenderChat() {
  const el = document.getElementById('of-chat-log');
  if (!el) return;
  if (!OF.log.length) { el.textContent = 'No session yet — pick a mode or press New session.'; return; }
  el.innerHTML = OF.log.slice(-40).map(m =>
    '<div style="margin:3px 0"><b style="color:' + (m.who === 'you' ? '#00e5ff' : m.who === 'error' ? '#ff5252' : m.who === 'system' ? '#9fb0c0' : '#76ff03') + '">' +
    ofEsc(m.who) + ':</b> ' + ofEsc(m.text) + '</div>').join('');
  el.scrollTop = el.scrollHeight;
}

function ofModeChoice(s) {
  const el = document.getElementById('of-mode');
  if (!el) return;
  el.innerHTML = '<div style="margin:4px 0 8px">' + ofEsc(s.prompt || 'OpenFable is available — how do you want to work with it?') + '</div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
    '<button onclick="ofTerminal()">&#128421; Terminal (OpenFable TUI)</button>' +
    '<button onclick="ofGui()">&#128172; GUI chat widget</button></div>' +
    '<div id="of-mode-result" style="color:#9fb0c0;margin-top:6px;min-height:16px"></div>';
}

async function ofPost(url, body) {
  return fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'},
                     body: JSON.stringify(body || {})}).then(r => r.json());
}

async function ofRefresh() {
  try {
    const s = await fetch('/api/openfable/state').then(r => r.json());
    document.getElementById('of-server').textContent = JSON.stringify(
      {found: s.found, path: s.path, version: s.version, server: s.server, note: s.note}, null, 1).slice(0, 4000);
    document.getElementById('of-sessions').textContent = JSON.stringify(s.sessions || [], null, 1).slice(0, 4000);
    ofModeChoice(s);
    return s;
  } catch (e) {
    document.getElementById('of-server').textContent = 'state fetch failed: ' + e;
    return null;
  }
}

async function ofTerminal() {
  const r = await ofPost('/api/openfable/terminal');
  const el = document.getElementById('of-mode-result');
  if (!el) return;
  el.textContent = r.launched
    ? 'TUI launched in a new console window (pid ' + r.pid + ').'
    : (r.error || 'launch failed') + (r.command ? ' — run: ' + r.command.join(' ') : '');
}

async function ofGui() {
  const el = document.getElementById('of-mode-result');
  const s = await ofRefresh();
  if (s && s.server && s.server.running) {
    if (el) el.textContent = 'Server already running at ' + s.server.url + ' — loading models…';
  } else {
    if (el) el.textContent = 'Starting headless openfable serve… (takes a few seconds)';
    const st = await ofPost('/api/openfable/server/start', {});
    if (el) el.textContent = st.started
      ? 'Server up at ' + st.url + (st.already ? ' (adopted)' : '') + ' — loading models…'
      : 'Server start failed: ' + (st.error || JSON.stringify(st));
    await ofRefresh();
  }
  await ofLoadModels();
  if (!OF.sid) await ofNewSession(true);
  ofRenderChat();
}

async function ofStartServer() {
  const el = document.getElementById('of-mode-result');
  if (el) el.textContent = 'Starting headless openfable serve…';
  const st = await ofPost('/api/openfable/server/start', {});
  if (el) el.textContent = st.started ? 'Server up at ' + st.url : 'Failed: ' + (st.error || JSON.stringify(st));
  await ofRefresh();
}

async function ofStopServer() {
  const st = await ofPost('/api/openfable/server/stop', {});
  const el = document.getElementById('of-mode-result');
  if (el) el.textContent = st.stopped ? 'Server stopped.' : 'Not stopped: ' + (st.error || 'unknown');
  await ofRefresh();
}

async function ofLoadModels() {
  try {
    const s = await fetch('/api/openfable/models').then(r => r.json());
    document.getElementById('of-models').textContent = s.error
      ? s.error : (s.count + ' models across providers (cached=' + s.cached + ')' +
        JSON.stringify((s.models || []).slice(0, 15), null, 1).slice(0, 3000));
    const sel = document.getElementById('of-model-select');
    if (sel && s.models && s.models.length) {
      sel.innerHTML = s.models.slice(0, 500).map(m =>
        '<option value="' + ofEsc(m.id || (m.provider + '/' + m.model)) + '">' + ofEsc(m.label || m.id) + '</option>').join('');
      OF.model = sel.value;
    }
  } catch (e) {
    document.getElementById('of-models').textContent = 'models fetch failed: ' + e;
  }
}

async function ofNewSession(silent) {
  const r = await ofPost('/api/openfable/sessions', {});
  if (r.session_id) {
    OF.sid = r.session_id;
    if (!silent || !OF.log.length) OF.log.push({who: 'system', text: 'session ' + r.session_id + (r.title ? ' — ' + r.title : '')});
  } else {
    OF.log.push({who: 'error', text: r.error || 'session create failed (server down?)'});
  }
  ofRenderChat();
}

async function ofSend() {
  const inp = document.getElementById('of-input');
  const text = (inp && inp.value || '').trim();
  if (!text) return;
  if (!OF.sid) { OF.log.push({who: 'error', text: 'no session — start the server / create a session first'}); ofRenderChat(); return; }
  inp.value = '';
  OF.log.push({who: 'you', text});
  ofRenderChat();
  const st = document.getElementById('of-chat-status');
  if (st) st.textContent = 'waiting for reply… (model: ' + (OF.model || 'default') + ')';
  try {
    const sel = document.getElementById('of-model-select');
    const r = await ofPost('/api/openfable/chat',
      {session_id: OF.sid, text, model: (sel && sel.value) || '', timeout: 120});
    if (st) st.textContent = '';
    if (r.reply) OF.log.push({who: 'fable', text: r.reply});
    else OF.log.push({who: 'error', text: r.error || r.warning || 'no reply (timeout or provider error)'});
  } catch (e) {
    if (st) st.textContent = '';
    OF.log.push({who: 'error', text: 'chat failed: ' + e});
  }
  ofRenderChat();
}

async function ofAbort() {
  if (!OF.sid) return;
  const r = await ofPost('/api/openfable/abort', {session_id: OF.sid});
  OF.log.push({who: 'system', text: r.aborted ? 'turn aborted' : ('abort failed: ' + (r.error || ''))});
  ofRenderChat();
}

async function ofRun() {
  const inp = document.getElementById('of-run-input');
  const msg = (inp && inp.value || '').trim();
  if (!msg) return;
  const el = document.getElementById('of-run');
  el.textContent = 'running…';
  try {
    const r = await ofPost('/api/openfable/run', {message: msg, model: OF.model, timeout: 180});
    el.textContent = JSON.stringify({ok: r.ok, exit: r.exit, elapsed_s: r.elapsed_s,
      output: (r.output || '').slice(0, 3500), error: r.error || r.stderr || null}, null, 1).slice(0, 4000);
    if (inp) inp.value = '';
  } catch (e) {
    el.textContent = 'run failed: ' + e;
  }
}

async function loadModuleData(name) {
  try {
    if (name === 'vendors') {
      const [ix, sd, dl] = await Promise.all([
        fetch('/api/osint/intelx/state').then(r => r.json()),
        fetch('/api/osint/shadowdragon/state').then(r => r.json()),
        fetch('/api/osint/darkowl/state').then(r => r.json()),
      ]);
      document.getElementById('vendors-intelx').textContent = JSON.stringify(ix, null, 1).slice(0, 4000);
      document.getElementById('vendors-shadowdragon').textContent = JSON.stringify(sd, null, 1).slice(0, 4000);
      document.getElementById('vendors-darkowl').textContent = JSON.stringify(dl, null, 1).slice(0, 4000);
      return;
    }
    if (name === 'crack') {
      const s = await fetch('/api/crack/state').then(r => r.json());
      document.getElementById('crack-formats').textContent = JSON.stringify(s.hashes.formats || {}, null, 1).slice(0, 4000);
      document.getElementById('crack-hash').textContent = JSON.stringify({engines: s.hashes.engines, hashcat: s.hashes.hashcat_installed, john: s.hashes.john_installed, runs: (s.hash_runs || []).slice(-5)}, null, 1).slice(0, 4000);
      document.getElementById('crack-vault').textContent = JSON.stringify({engines: s.vaults.engines, runs: (s.vault_runs || []).slice(-5)}, null, 1).slice(0, 4000);
      document.getElementById('crack-services').textContent = JSON.stringify(s.services, null, 1).slice(0, 4000);
      return;
    }
    if (name === 'console') {
      const s = await fetch('/api/console/state').then(r => r.json());
      const ev = await fetch('/api/console/events?limit=10').then(r => r.json());
      document.getElementById('console-agents').textContent = JSON.stringify(s.agents, null, 1).slice(0, 4000);
      document.getElementById('console-skills').textContent = JSON.stringify(s.skills, null, 1).slice(0, 4000);
      document.getElementById('console-workflows').textContent = JSON.stringify(s.workflows, null, 1).slice(0, 4000);
      document.getElementById('console-commands').textContent = JSON.stringify({commands: s.commands, tasks: s.tasks, events: ev}, null, 1).slice(0, 4000);
      return;
    }
    if (name === 'ai') {
      const s = await fetch('/api/ai/state').then(r => r.json());
      document.getElementById('ai-providers').textContent = JSON.stringify(s.providers, null, 1).slice(0, 4000);
      document.getElementById('ai-keys').innerHTML = s.providers.filter(p => p.key_url).map(p =>
        '<div>🔑 <b>' + p.label + '</b> ' + (p.key_found ? '<span class="ok">key set</span>' : '<span class="kill">no key</span>') +
        ' <a href="' + p.key_url + '" target="_blank" rel="noopener" style="color:#00e5ff">Get API Key</a>' +
        (p.key_guide ? '<br><small>' + p.key_guide + '</small>' : '') + '</div>').join('') || 'No key pages configured';
      document.getElementById('ai-models').textContent = JSON.stringify(s.free_models, null, 1).slice(0, 4000);
      document.getElementById('ai-uncensored').textContent = JSON.stringify(s.uncensored, null, 1).slice(0, 4000);
      return;
    }
    if (name === 'lifecycle') {
      const s = await fetch('/api/lifecycle/state').then(r => r.json());
      document.getElementById('lifecycle-chain').textContent = s.chain + '\\n\\n' + JSON.stringify(s.phases.map(p => ({id: p.id, name: p.name, tools: p.tools})), null, 1).slice(0, 3000);
      document.getElementById('lifecycle-agents').textContent = JSON.stringify(s.agents, null, 1).slice(0, 4000);
      document.getElementById('lifecycle-loot').textContent = JSON.stringify(s.loot, null, 1).slice(0, 4000);
      document.getElementById('lifecycle-runs').textContent = JSON.stringify((s.recent || []).slice(-10), null, 1).slice(0, 4000);
      return;
    }
    // Generic live-fetcher: every dashboard module tries its own
    // /api/<module>/state and dumps it into its cards.
    // (IoT and OpenFable get dedicated splits below.)
    if (name === 'openfable') {
      await ofRefresh();
      return;
    }
    if (name === 'iot') {
      const s = await fetch('/api/iot/state').then(r => r.json());
      document.getElementById('iot-exploits').textContent = JSON.stringify(s.exploits, null, 1).slice(0, 4000);
      document.getElementById('iot-families').textContent = JSON.stringify(s.families, null, 1).slice(0, 4000);
      document.getElementById('iot-payload').textContent = 'kinds: ' + (s.payload_kinds || []).join(', ') + '\\nnote: ' + (s.note || '');
      try {
        const [dr, cam] = await Promise.all([
          fetch('/api/iot/drones').then(r => r.json()),
          fetch('/api/iot/cameras').then(r => r.json()),
        ]);
        document.getElementById('iot-drones').textContent = JSON.stringify({drones: dr, cameras: (cam.cameras || []).length, mavlink: s.mavlink}, null, 1).slice(0, 4000);
      } catch (e) {
        document.getElementById('iot-drones').textContent = 'drones/cameras: query failed';
      }
      return;
    }
    try {
      const resp = await fetch('/api/' + name + '/state');
      if (resp.ok) {
        const s = await resp.json();
        document.querySelectorAll('#' + name + ' pre').forEach(el => {
          el.textContent = JSON.stringify(s, null, 1).slice(0, 4000);
        });
        return;
      }
    } catch (e) {}
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
