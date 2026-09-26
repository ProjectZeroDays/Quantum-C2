# QUANTUM-CLI V4 — Wiki

Full technical reference for the QUANTUM-CLI V4 package (`src/quantum/`), the split of the V3.1
single-file spec (`dist/quantum-cli-v3.1-single.py` — THE SPEC; any behavioral divergence of the
package is a bug in the package).

Everything here is for **authorized engagements only** — penetration tests, labs, and contracted work.

---

## 1. Architecture

```
                          ┌──────────────────────────────┐
                          │   quantum_cli.py (launcher)   │
                          └──────────────┬───────────────┘
                                         │ python -m quantum
        ┌────────────────────────────────┴─────────────────────────────────┐
        │                     src/quantum/ package map                      │
        ├────────────┬────────────┬────────────┬────────────┬─────────────┤
        │   core/    │    ai/     │   recon/   │  camwar/   │  weapons/   │
        │ env, log,  │ supervisor │ scan,      │ engine,    │ registry,   │
        │ opsec,     │ + bootstrap│ validator, │ vendors,   │ tiers,      │
        │ GRAYFISH,  │ (Abliterated│ osint, DoH,│ rtsp,      │ PolyMorph,  │
        │ QBrain,    │ .ai or     │ wsdiscovery │ brute/phish │ techniques  │
        │ deps,      │ local)     │            │ v3          │             │
        ├────────────┴────────────┴────────────┴────────────┴─────────────┤
        │   postexploit/          │     c2/            │    overlord/      │
        │ persistx, kitlogger,    │ app, routes,       │ Autonomous-      │
        │ killswitch, harvest,    │ wsgi (waitress),  │ Overlord, decide,│
        │ footprint               │ transport, agents │ engines           │
        ├─────────────────────────┴────────────────────┴──────────────────┤
        │                         dash/ (live ops dashboard at /dash)      │
        └───────────────────────────────────────────────────────────────────┘
```

### Package map

| Package | Modules | Role |
|---|---|---|
| `quantum.core` | `env.py`, `logging.py`, `opsec.py`, `grayfish.py`, `jurgen.py`, `deps.py` | Platform/paths, audit log + MITRE mapper, OPSEC primitives, sealed loot, deterministic AI (QBrain), graceful deps. |
| `quantum.ai` | `supervisor.py`, `bootstrap.py` | AI_Supervisor (Abliterated.ai primary, local fallback), local-model deployment (DM). |
| `quantum.recon` | `scan.py`, `fingerprint.py`, `osint.py`, `doh.py`, `wsdiscovery.py` | Network scanning, fingerprinting + target validation, OSINT, DNS-over-HTTPS, WS-Discovery/ONVIF. |
| `quantum.camwar` | `engine.py`, `vendors.py`, `rtsp.py`, `brute_v3.py` | Camera warfare engine, vendor tables, RTSP probing, credential spray + phish engines. |
| `quantum.weapons` | `registry.py`, `kernel_v3.py`, `remote_v3.py`, `media_v3.py`, `legacy.py`, `polymorph.py`, `techniques/` | 29-CVE registry + fire contract, Linux kernel LPE, remote appliance, media/maldoc, Windows legacy, PolyMorph v3, named techniques. |
| `quantum.postexploit` | `persistx.py`, `kitlogger.py`, `killswitch.py`, `harvest.py`, `footprint.py` | Persistence, keylogger staging, kill-switch + task queues, data harvesting, footprint wiping. |
| `quantum.c2` | `app.py`, `routes.py`, `wsgi.py`, `transport.py`, `agents/ghostfang.py`, `agents/ghostdns.py` | Flask C2 app + REST routes, production WSGI chain, covert transports (FOXACID, QUANTUM insert, ICMP, DoH), implant agents. |
| `quantum.overlord` | `autonomous.py`, `decide.py`, `engines.py` | AutonomousOverlord engagement loop, decision policy, named engagement engines. |
| `quantum.dash` | `__init__.py` (DASH_HTML) | Live ops dashboard served at `/dash`. |

---

## 2. Every module explained

### quantum.core

- **`env.py`** — Paths and platform constants. `QCLI_DIR=qcli/`, `LOG_DIR=logs/`,
  `LOOT_DIR=loot/`, `MODELS_DIR=models/`, `KEYS_DIR=qcli/keys`, `PRIV`/`PUB` (implant crypto keys),
  `AGENT=qcli/obsidian.ps1`. Reconfigures stdout/stderr to UTF-8 (Windows console safe).
  `load_env_file()` parses `.env` (KEY=VALUE, no interpolation). `local_ip()` (UDP-connect trick),
  `local_scope()` (autodetected local /24), `no_ai_mode()` (`--no-ai` / `QCLI_NO_AI=1`).
- **`logging.py`** — `log()` writes structured JSONL to `logs/audit.jsonl` plus a console line.
  `MitreMapper.map_audit()` scans the audit log against keyword rules and writes
  `logs/mitre_map.json` (coverage, counts, events_scanned). `_tail_jsonl()` helper.
- **`opsec.py`** — OPSEC object (Tor management via `ensure_tor()`, hardened web fetches `web()`),
  `tcp_probe()`, `run()`, `network_aware_jitter()` (pauses that respect network conditions),
  `rand_hex()`.
- **`grayfish.py`** — `GrayFish` / `GRAYFISH`: AES-256-GCM sealed loot. See §5.
- **`jurgen.py`** — `QBrain`, the deterministic planner used as AI fallback (and exclusively under
  `--no-ai`). `QBrain.plan_attack(fp)` picks a CVE from the registry from a fingerprint.
- **`deps.py`** — Graceful optional-dependency imports (`Fore`/colorama, `requests`, Flask pieces,
  `AESGCM`/pycryptodome) plus `check_deps()`; keeps import failures soft so degraded runs work.

### quantum.ai

- **`supervisor.py`** — `AI_Supervisor`: OpenAI-compatible chat against Abliterated.ai
  (key from env `ABLITERATION_KEY` or `.env`; base URL `QCLI_AI_URL`; model
  `abliterated-model-large-v2` or `QCLI_PINNED_MODEL`). `query()` returns `None` under
  `--no-ai`, without a key, or after a failure — callers fall back to QBrain. HTTP `402`/`429`
  marks the provider "alive but billing-limited" and trips the same fallback. `plan_attack(fp)`
  asks the model for exactly one registry CVE and verifies it; falls back to `QBrain.plan_attack`.
  `tune_brute_wordlist()` builds per-service wordlists with OSINT hints.
- **`bootstrap.py`** — `DM` (deployment manager): `deploy_local_ai()` searches for / deploys a
  local model into `models/` and returns its identifier. No network calls on the `--no-ai` path.

### quantum.recon

- **`scan.py`** — `ReconModule`: `scan(cidr)` (TCP sweep → live hosts), `fingerprint(ip)` (port and
  service banner profile), `osint(domain)` (public-record lookup).
- **`fingerprint.py`** — `Validator` / `VALIDATOR`: `score(ip, fingerprint)` → target-value verdict;
  `decision == "high_value"` gates auto-exploitation.
- **`osint.py`** — `osint_lookup`: passive OSINT record lookup.
- **`doh.py`** — `DoH`: DNS-over-HTTPS resolver (`resolve(name, rtype=)`), the transport under
  both recon and GHOSTFANG-DNS egress.
- **`wsdiscovery.py`** — `wsdiscovery_cameras()` (WS-Discovery probe for network cameras) and
  `onvif_device_info()` (ONVIF device-info pull) — the second discovery leg of CAMWAR.

### quantum.camwar

- **`engine.py`** — `CamWarEngine` / `CAMWAR` singleton. Camera ports
  (80, 443, 554, 37777, 37778, 8000, 8001, 8080, 8081, 8899, 34567, 34571, 34599, 5000), vendor
  hints (Hikvision, Dahua, Axis, Foscam, TP-Link, generic), per-vendor default credentials, info
  endpoints (e.g. `/ISAPI/System/deviceInfo`), snapshot endpoints (e.g.
  `/ISAPI/Streaming/channels/101/picture`), PTZ control, `discover(cidr)`, `attack_cam(cam)`,
  `control_cam(cam, ptz=)`, `identify(ip)`, `one_shot(ip)`, `pwn_network(cidr)`.
- **`vendors.py`** — `vendor_from_str()`: banner → vendor classification.
- **`rtsp.py`** — `rtsp_probe()` / `parse_rtsp_header()`: RTSP (554) server identification.
- **`brute_v3.py`** — `BruteEngine` / `BruteEngineV3` (credential spray, OSINT-hinted wordlists) and
  `PhishEngine` (phishing launch).

### quantum.weapons

- **`registry.py`** — `ZERO_DAY_REGISTRY` (29 CVEs, tiers `legacy` / `V3_HIGH` / `V3_MED` /
  `V3_CHECK`), `resolve_weapon()` (name → callable, searched tier-by-tier across the weapon
  modules), the `registry` object (`registry.fire(cve, ip, params)` — never raises), and
  `ExploitOrchestrator` (validator-gated `auto_exploit(ip, force=)`, AI/QBrain planning, and a
  deterministic registry-march fallback keyed on fingerprint ports).
- **`kernel_v3.py`** — Linux kernel LPE checks/exploits: Dirty Pipe (`v3_dirtypipe`, also covers
  Dirty COW probing), PwnKit, Baron Samedit, Overlayfs GameOver, nf_tables UAF and double-free,
  BootHole.
- **`remote_v3.py`** — Remote/appliance weapon tier: Log4Shell, Citrix Bleed, Citrix path
  traversal, PAN-OS GlobalProtect command, Confluence OGNL, WebLogic console, IOS XE web-UI admin,
  vCenter upload, MOVEit probe, SambaCry.
- **`media_v3.py`** — Media/client tier: MSHTML maldoc builder (`v3_mshtml_maldoc`,
  CVE-2021-40444), WhatsApp VOIP, libwebp BLASTPAST, Apple ImageIO, WebKit escape checks.
- **`legacy.py`** — Windows classics: Zerologon (check + exploit + DC dump), EternalBlue
  (MS17-010), PrintNightmare, PetitPotam, Follina MSDT, ProxyLogon.
- **`polymorph.py`** — `PolyMorphEngineV3`. See §6.
- **`techniques/`** — Named tradecraft: `cagebreak.py` (sandbox cage escape), `flashfill.py`
  (FlashFill staged fill), `macreset.py` (`macos_recovery_reset()` script generator),
  `emojisms.py` (EMOJI_MAP, `emoji_encode`/`emoji_decode` covert channel).

### quantum.postexploit

- **`persistx.py`** — `persistx()`: stealth persistence staging (PERSISTX).
- **`kitlogger.py`** — `stage_keylogger()`: stages the keylogger; its buffer (`*.klq`) is pulled on
  the next beacon via the task queue.
- **`killswitch.py`** — `TASKQ` (per-implant task queues), `KILLSWITCH` (global flag), and
  `kill_all_implants(wipe_first=True)`. See §7.
- **`harvest.py`** — `DataHarvester`: `harvest_host(label)`, `analyze_pcap(file)`,
  `auto_parse_loot(host, zip)` (auto-extract creds/secrets from beacon drops).
- **`footprint.py`** — `footprint_wipe_windows()` / `footprint_wipe_posix()`: artifact removal
  (event-log and temp-file cleanup on Windows; `/var/tmp/.gn-*`, shell-history trim on POSIX).

### quantum.c2

- **`app.py`** — `make_c2(agents)` builds the Flask app; `keygen()` generates implant crypto keys
  (`qcli/keys/priv.pem`, `pub.xml`); `decrypt_beacon()`; `QCLI_API` / `Turbine` (implant registry,
  heartbeat enrollment); `FEDERATION` (Tor hidden-service peer sync).
- **`routes.py`** — Every REST route. See §4.
- **`wsgi.py`** — `run_c2()`: production WSGI chain — waitress (all OS, 16 threads, `:8443`) →
  gunicorn (POSIX) → Flask dev server as a logged-warning last resort.
- **`transport.py`** — `FoxAcid` (watering-hole server, `:8081`), `QuantumInsert` (ARP poison +
  injection), `SwitchboardICMP` (ICMP covert channel listener), `DoHC2BeaconServer`
  (HTTPServer on `:5353` for DoH beacons).
- **`agents/ghostfang.py`** — `OBSIDIAN_PS1` (PowerShell stager), `generate_posix_agent(host)`
  (writes `qcli/ghostfang.sh`), `CottonMouth` (payload staging).
- **`agents/ghostdns.py`** — GHOSTFANG-DNS. See §8.

### quantum.overlord

- **`autonomous.py`** — `AutonomousOverlord`. See §9. Camera-first ordering is a standing rule.
- **`decide.py`** — `decide(overlord)`: the decision policy that maps overlord state (targets,
  fired, creds, cams) to the next action from `ACTIONS = ["cam_war", "cam_discover",
  "cam_control", "recon_scope", "exploit", "brute", "phish", "worm", "harvest", "router",
  "osint", "episcribe", "mitre_report", "rest"]`.
- **`engines.py`** — Named engagement engines: `GODSUPREME` (worm/hop propagation), `EpiScribe`
  (selector watch), `MFP` (persistence), `Somberknight` (wireless sweep), `Trinity` (memory
  capture), `UnitedDrake` (router attack), `Wildfire` (triage).

### quantum.dash

- `DASH_HTML` — the single-page live ops dashboard served at `/dash`; reads `/dash/api/state`
  (decisions, audit tail, MITRE coverage, kill-switch status).

---

## 3. MITRE mapping table

`MitreMapper.map_audit()` scans `logs/audit.jsonl` (last 2000 events) for keywords and counts
ATT&CK technique coverage into `logs/mitre_map.json`.

| Audit keyword(s) | ATT&CK technique |
|---|---|
| `cam war`, `camwar` | T1595.002 — Vulnerability Scanning |
| `log4shell`, `citrix`, `pan-os`, `panos`, `confluence`, `weblogic` | T1190 — Exploit Public-Facing Application |
| `dirtypipe`, `dirty pipe`, `pwnkit`, `baron samedit`, `samedit`, `nf_tables` | T1068 — Exploitation for Privilege Escalation |
| `flashfill` | T1499 — Endpoint Denial of Service |
| `emojism`, `emoji` | T1132.001 — Data Encoding: Standard Encoding |
| `rtsp`, `brute` | T1110.003 — Password Cracking: Password Spraying |
| `zerocheck` | T1595 — Active Scanning |
| `mshtml` | T1203 — Exploitation for Client Execution |
| `boothole` | T1542.001 — System Firmware |
| `beacon`, `c2` | T1071 — Application Layer Protocol |
| `killswitch`, `wipe` | T1485 — Data Destruction |
| `keylogger` | T1056.001 — Input Capture: Keylogging |
| `persistx` | T1547 — Boot or Logon Autostart Execution |
| `registry` | T1112 — Modify Registry |
| `snapshot`, `seal` | T1560 — Archive Collected Data |
| `ghostdns`, `doh` | T1071.004 — DNS |
| `worm` | T1021 — Remote Services |
| `phish` | T1566 — Phishing |
| `harvest` | T1005 — Data from Local System |

Regenerate on demand with `python quantum_cli.py mitre`; the Overlord also regenerates it
automatically when it pauses/exits.

---

## 4. C2 REST API reference

The C2 is a Flask app served by **waitress** on `0.0.0.0:8443` (production WSGI; gunicorn on
POSIX if waitress is missing; Flask dev server only as a logged fallback).

| Route | Method | Purpose |
|---|---|---|
| `/s` | GET | Serve the default agent profile (`default`). |
| `/s/<profile>` | GET | Serve an agent profile — `default` (OBSIDIAN PowerShell), `linux` / `mac` (ghostfang POSIX; run `posixagent` first). 404 on unknown profile. |
| `/r` | POST | Implant beacon + loot delivery + task pull (see below). |
| `/ai` | POST | `{"cmd": ..., "params": {...}}` → `QCLI_API.handle` — query the planner/executor. |
| `/kill` | POST | Kill-switch. `{"arm": true, "wipe": true}` arms with wipe-first (defaults); `{"arm": false}` disarms. See §7. |
| `/federation/reg` | GET/POST | GET: implant registry + our onion. POST: merge a peer's `{"implants": {...}}` into the Turbine registry. |
| `/federation/peer` | POST | `{"onion": "<peer>.onion"}` — register a federation peer (persisted to `logs/federation/peers.json`). |
| `/dash` | GET | Live ops dashboard (HTML). |
| `/dash/api/state` | GET | Dashboard JSON: `decisions` (last 100 of `decisions.jsonl`), `audit` (last 200 of `audit.jsonl`), `mitre` coverage, `killswitch` flag. |

### POST /r — the beacon contract

An implant POSTs JSON. Three shapes are handled:

1. **POSIX drop** — `{"host": ..., "data": <base64>, "k": absent}`: payload is written to
   `loot/<host>/posix_drop_<ts>.txt`, sealed by GRAYFISH (`.gfy`), and the queued task is returned.
2. **Heartbeat** — `{"host": ..., "act": "hb"}`: enrolls the host in the Turbine registry and
   returns its queued task (or `{"act": "none"}`).
3. **Encrypted beacon** — everything else: `decrypt_beacon()` decrypts the blob, it is written to
   `loot/<host>/drop_<ts>.zip`, auto-parsed by `auto_parse_loot()` (creds/secrets extracted),
   then sealed. The queued task is returned.

Task delivery is **pull-only**: an implant only learns about a task (keylogger pull, wipe, die)
when it beacons `/r` next.

---

## 5. GRAYFISH sealed loot

`GRAYFISH` (`quantum.core.grayfish`) seals loot at rest with **AES-256-GCM**:

- The sealing key lives at **`logs/.lootkey`**, created once (random 32-byte hex, SHA-256-derived
  key). **Deleting it breaks every sealed file — treat it as immutable.**
- `seal(path)` → encrypts to `<path>.gfy` (12-byte nonce + AESGCM ciphertext, AAD `"grayfish"`)
  and removes the plaintext. `unseal(path)` reverses it.
- `seal_dir()` seals every plaintext file under `loot/`; `unseal_dir()` reverses.
- Beacon drops (`/r`), POSIX drops, camera snapshots, and the harvest pipeline all seal
  automatically. The Overlord seals the whole loot dir on pause/exit, and `Ctrl-C` on the
  launcher seals before exiting.

Manual: `python quantum_cli.py seal` / `python quantum_cli.py unseal`, or menu options 25/26.

---

## 6. PolyMorph v3

`PolyMorphEngineV3` (`quantum.weapons.polymorph`) guarantees **identical plaintexts never produce
identical wire bytes**:

- Every `encrypt()` draws a fresh **epoch** (monotonic counter XOR random) and derives an HMAC
  keystream (`SHA-256`, key `pm3-v3`) from `epoch:counter`.
- **UTF-7 variants**: odd epochs serialize as UTF-7 with a `|mode:utf7` marker, even epochs plain.
- **Junk filler**: 8–64 random bytes prepend the body; a 16-byte HMAC tag (`pm3-tag`) closes it.
- Wire format: `PM3\x01` magic + 8-byte epoch + 2-byte junk length + junk + body + tag.
- `polymorphize(text)` / `depolymorphize(wire)` provide the line-based wire form (`J:` junk lines,
  one `P:` payload line) used for stager morphing.

---

## 7. Kill-switch flow

The kill-switch is **covert and pull-based** — no direct connection to implants is opened.

```
operator            C2 (:8443)                        implants
   │  POST /kill {"arm":true}                          │
   ├────────────────────► kill_all_implants(wipe_first=True)
   │                     TASKQ[host] = wipe task       │
   │                     KILLSWITCH["on"] = True       │
   │                                                   │ (implant beacons /r)
   │                     ◄─────────────────────────────┤
   │                     task returned in beacon reply ─┤ implant wipes + dies
   │  Overlord loop sees KILLSWITCH on:                │
   │   footprint wipe → seal loot → MITRE map → pause   │
```

- Arm: menu option **30**, or `POST /kill` with `{"arm": true, "wipe": true}` (both default true).
- Disarm: `POST /kill {"arm": false}` or menu 30 with `n`.
- Wipe task: Windows — `wevtutil cl 'Windows PowerShell'` + temp-artifact removal; POSIX —
  `rm -f /var/tmp/.gn-* ~/.bash_history.tmp` + self-kill.
- **An implant only dies when it beacons after arming** — there is no push channel.
- If the Overlord is running, it checks `KILLSWITCH` each cycle, then retires: footprint wipe,
  `GRAYFISH.seal_dir()`, `MitreMapper().map_audit()`.

---

## 8. DoH egress (GHOSTFANG-DNS)

`quantum.c2.agents.ghostdns` — for implants behind outbound-only firewalls:

- **Beacon**: data is base32-encoded, chunked into ≤60-char labels, and resolved as
  `<host_id>.<chunk>.<domain>` through **public DoH resolvers** (cloudflare-dns.com / dns.google,
  443/tcp). To any observer it is a cache-miss DNS lookup. `doh_reverse_beacon(host_id, data,
  domain)` is the programmatic form.
- **Tasking**: the operator sets a DNS **TXT record** at `cmd.<domain>` (or `<host_id>.cmd.<domain>`)
  containing a JSON task `{"cmd": "..."}`; `doh_task_check(domain)` reads it HQ-side, the agent
  reads it beacon-side. Special TXT values: `wipe`, `kill`.
- **Agent generation**: `python quantum_cli.py ghostdns --domain yourdomain.tld` writes
  `qcli/ghostdns.sh` (POSIX sh, 60 s default interval) and prints a live task-check result.
  The domain can also come from `.env` (`QCLI_DOMAIN`).
- The `dohc2` command runs `DoHC2BeaconServer` on `:5353` for direct DoH beacon collection.

---

## 9. The autonomous pipeline

`AutonomousOverlord.run()` — one engagement, no operator:

```
 1. C2 up        keygen (if needed) + waitress C2 on :8443 (background thread)
 2. camwar       pwn_network(scope) — CAMERA SWEEP FIRST (standing rule: before any service scan)
 3. loop         each cycle: check KILLSWITCH → decide() → execute → jittered rest
                 actions: cam_war / cam_discover / cam_control / recon_scope / exploit /
                          brute / phish / worm / harvest / router / osint / episcribe /
                          mitre_report / rest
    └─ exploit:  recon → VALIDATE → plan (AI or QBrain) → fire (registry)
                 → post_exploit_auto (persistx + keylogger staging + task-queue pulls)
                 → harvest → seal
 4. finish       footprint wipe (if kill-switch engaged) → GRAYFISH.seal_dir()
                 → MitreMapper().map_audit() → pause report
```

**Stage detail — recon > validate > plan > fire > post-exploit > harvest > seal > mitre map:**

1. **Recon** — `ReconModule().fingerprint(ip)` (or `scan(cidr)` to enumerate targets).
2. **Validate** — `Validator().score(ip, fp)`; `decision == "high_value"` (or `--aggression
   aggressive` / `force=True`) opens the gate.
3. **Plan** — `AI_Supervisor.plan_attack(fp)` (Abliterated.ai picks exactly one registry CVE) with
   deterministic `QBrain.plan_attack` fallback; a registry-march fallback fires on fingerprint
   ports if no dedicated match resolves.
4. **Fire** — `ExploitOrchestrator.fire(cve, ip)` through the 29-CVE `ZERO_DAY_REGISTRY`.
5. **Post-exploit** — `post_exploit_auto()`: `persistx()` persistence, `stage_keylogger()`, and a
   keylogger-buffer pull task queued per fired target.
6. **Harvest** — `DataHarvester.harvest_host(label)` over fired targets.
7. **Seal** — every drop was sealed on arrival; `GRAYFISH.seal_dir()` seals the remainder.
8. **MITRE map** — `MitreMapper().map_audit()` writes `logs/mitre_map.json`.

Controls: `--scope/-c`, `--cycles N`, `--aggression balanced|aggressive|patient`,
`--camera-only`, `--no-ai` (fully deterministic, no network to AI providers), `--model` pinning.

---

## 10. Camera warfare deep-dive (CAMWAR)

Cameras are the **primary objective** of the Overlord — but one stage of many (recon, exploit,
harvest, seal all still run).

- **Discovery (two legs)**: TCP sweep of `CAM_PORTS` (554 RTSP, 80/443 web, plus vendor ports
  37777/37778 Dahua, 8899, 34567/34571/34599, 8000/8001, 5000) **and** WS-Discovery with ONVIF
  device-info pulls.
- **Identification**: banner/vendor hints (`vendor_from_str`, `VENDOR_HINTS`, `rtsp_probe`) →
  Hikvision, Dahua, Axis, Foscam, TP-Link, or generic.
- **Attack**: per-vendor default credential spray (e.g. Hikvision `admin/admin`, `admin/12345`,
  `admin/888888`, …; Dahua, Axis, Foscam, TP-Link, generic tables) with digest/basic auth as the
  vendor requires. OSINT-hinted wordlists via `AI_Supervisor.tune_brute_wordlist`.
- **Control**: `control_cam(cam, ptz=)` — snapshot via vendor endpoints (`/ISAPI/Streaming/
  channels/101/picture`, `/cgi-bin/snapshot.cgi`, `/axis-cgi/jpg/image.cgi`, …) and PTZ nudge.
  Snapshots are sealed into `loot/` as `.gfy`.
- **Entry points**: `camwar -c <cidr>` (pwn_network — discover+attack+control), `cams` (step-through),
  `camshot -t <ip>` (one-shot), menu `c` / `11`, and first phase of every autonomous run.
- **Camera console** (`--menu` → `c`, or `--target <cidr> --manual`): 1 discover, 2 attack all,
  3 snapshot all cracked, 4 PTZ nudge all cracked, 5 attack+snapshot+PTZ single IP, 6 one-shot
  single IP, 7 list state, 0 back.

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` at start | `pip install flask requests waitress pycryptodome impacket pysmb colorama` |
| AI log "credits/rate — billing check needed" (402/429) | Provider reachable, credits exhausted — top up Abliterated.ai; QBrain fallback is already active. |
| C2 logs "falling back to Flask dev server" | `pip install waitress` for the production WSGI chain. |
| Cameras found but not cracked | Defaults exhausted — try single-IP attack (console 5/6, `camshot -t`), verify 554 open, OSINT-hint the wordlist. |
| Dirty Pipe probe "not vulnerable" | CVE-2022-0847 hits only kernel ≥5.8 and < the fixed sets (5.16.11 / 5.15.25 / 5.10.102); modern kernels are simply patched. |
| `ghostdns` prints usage line | Pass `--domain yourdomain.tld` or set `QCLI_DOMAIN` in `.env`. |
| Kill-switch armed, implants alive | Pull-based — wait for each implant's next beacon to `/r`. |
| `unseal` fails / "lootkey intact?" | `logs/.lootkey` changed or deleted — restore from backup; it is immutable. |
| Garbled console glyphs on Windows | `chcp 65001`; `env.py` already forces UTF-8 with replacement. |
| C2/FOXACID bind errors | Free `:8443` (C2), `:8081` (FOXACID), `:5353` (dohc2) or stop the other listener. |
| Slow first run | First-run keygen + model search/deploy + full-scope discovery — normal; later cycles are faster. |
| `impacket`/`smb` import errors | Optional Windows-tier deps — `pip install impacket pysmb`; legacy checks degrade gracefully without them. |

Full runbook: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 12. Glossary

| Term | Meaning |
|---|---|
| **CAMWAR** | Camera warfare engine — discovery, credential spray, snapshot/PTZ control. |
| **GRAYFISH** | AES-256-GCM sealed-loot system (`.gfy` files, `logs/.lootkey`). |
| **GHOSTFANG** | POSIX implant family (`ghostfang.sh`); GHOSTFANG-DNS is the DoH-egress variant. |
| **OBSIDIAN** | PowerShell stager (`qcli/obsidian.ps1`); per-target variants from `agents/build/variant.py`. |
| **FOXACID** | Watering-hole server on `:8081`. |
| **QUANTUM (insert)** | ARP-poison + injection transport. |
| **Switchboard** | ICMP covert-channel listener. |
| **Trinity** | Memory capture engine. |
| **UnitedDrake** | Router attack engine. |
| **GODSUPREME** | Worm/hop propagation engine. |
| **EpiScribe** | Selector watch engine. |
| **MFP** | Persistence engine. |
| **Somberknight** | Wireless sweep engine. |
| **Wildfire** | Triage engine. |
| **QBrain** | Deterministic planner (`quantum.core.jurgen`) — AI fallback and `--no-ai` brain. |
| **Overlord** | `AutonomousOverlord` — the full autonomous engagement loop. |
| **TASKQ** | Per-implant task queue on the C2 (host → task dict), drained on each beacon. |
| **KILLSWITCH** | Global armed flag + wipe/die task broadcast to every implant queue. |
| **Turbine** | C2 implant registry (heartbeat enrollment, federation merge). |
| **FEDERATION** | Tor hidden-service peer sync of implant registries. |
| **zerocheck** | 9-probe remote-CVE battery (log4shell, citrixbleed, citrix path, PAN-OS, Confluence, WebLogic, IOS XE, vCenter, MOVEit). |
| **EMOJISMS** | Emoji covert-channel codec (`emoji_encode`/`emoji_decode`). |
| **PolyMorph v3** | Epoch-keyed polymorphic encryption (UTF-7 variants + junk). |
| **PERSISTX** | Persistence staging. |
| **FlashFill** | Staged-fill technique. |
| **CageBreak** | Sandbox cage escape technique. |
| **`.gfy`** | A GRAYFISH-sealed file. |
| **dash** | Live ops dashboard at `/dash`. |
