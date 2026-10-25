/** Quantum CLI SPA router and store */
const ROUTES = {
  "#/fleet": () => renderFleet(),
  "#/device/": () => renderDevice(),
  "#/postex": () => renderPostEx(),
  "#/scan": () => renderScan(),
  "#/telemetry": () => renderTelemetry(),
  "#/control": () => renderControl(),
  "#/loot": () => renderLoot(),
  "#/settings": () => renderSettings(),
};

function router() {
  const hash = location.hash || "#/fleet";
  const match = Object.keys(ROUTES).find(r => hash.startsWith(r));
  if (match) ROUTES[match]();
}

function renderFleet() {
  document.getElementById("device-detail").style.display = "none";
  document.getElementById("fleet-grid").style.display = "block";
  fetch("/api/v1/devices").then(r => r.json()).then(data => {
    const tbody = document.querySelector("#fleet-table tbody");
    tbody.innerHTML = "";
    data.data?.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${d.id?.slice(0,12)}</td><td>${d.nickname||d.model||"?"}</td><td>${d.platform||"?"}</td><td>${d.state||"DISCOVERED"}</td><td>${d.root?"✓":"✗"}</td><td>${d.last_seen ? Math.round((Date.now()/1000-d.last_seen)) + "s" : "?"}</td><td>--</td><td><a href="#/device/">MANAGE</a></td>`;
      tbody.appendChild(tr);
    });
    document.getElementById("fleet-kpi").textContent = (data.data?.length || 0) + " devices";
  }).catch(() => { document.getElementById("fleet-kpi").textContent = "offline"; });
}

function renderDevice() { document.getElementById("fleet-grid").style.display = "none"; document.getElementById("device-detail").style.display = "block"; }
function renderPostEx() { document.getElementById("fleet-grid").style.display = "none"; document.getElementById("device-detail").style.display = "none"; document.querySelector("main h1").textContent = "Post-Ex Dashboard"; }
function renderScan() { document.getElementById("fleet-grid").style.display = "none"; document.querySelector("main h1").textContent = "Vuln Scan"; }
function renderTelemetry() { document.getElementById("fleet-grid").style.display = "none"; document.querySelector("main h1").textContent = "Telemetry"; }
function renderControl() { document.getElementById("fleet-grid").style.display = "none"; document.querySelector("main h1").textContent = "Device Control"; }
function renderLoot() { document.getElementById("fleet-grid").style.display = "none"; document.querySelector("main h1").textContent = "Loot / Harvest"; }
function renderSettings() { document.getElementById("fleet-grid").style.display = "none"; document.querySelector("main h1").textContent = "Settings"; }

window.addEventListener("hashchange", router);
window.addEventListener("load", () => { router(); setInterval(() => { fetch("/api/v1/devices").then(r=>r.json()).then(d=>{ document.getElementById("online-count").textContent = "Online: " + (d.data?.filter(x=>x.state!="DEAD"&&x.state!="STALE").length||0); document.getElementById("bus-status").textContent = "BUS: OK"; }).catch(()=>{ document.getElementById("bus-status").textContent = "BUS: --"; }); }, 3000); });
