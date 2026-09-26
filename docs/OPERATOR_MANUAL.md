# QUANTUM-CLI V4 — Operator Manual

Step-by-step runbook for running QUANTUM-CLI on **authorized engagements only** (penetration
tests, security labs, contracted assessments). Keep your authorization paperwork at hand — this
framework is real and fires real techniques at real targets.

---

## 1. Pre-engagement checklist

Run through every item before the first command:

- [ ] **Written authorization** — signed scope/rules-of-engagement covering the target network,
      camera devices, and any external networks you will point `--target` at.
- [ ] **Scope CIDR decided** — the exact network(s) you are authorized to test. The default scope
      is the autodetected local `/24` (`local_scope()`); override with `--scope/-c` or `--target`.
- [ ] **`.env` configured** (repo root):
      - `ABLITERATION_KEY=<key>` — Abliterated.ai API key for AI planning. Without it the
        framework runs on the deterministic QBrain planner (fully functional, just not AI-guided).
      - `QCLI_DOMAIN=ops.example.tld` — optional; your operator-controlled domain for GHOSTFANG-DNS
        DoH egress beacons (can also be passed with `ghostdns --domain`).
- [ ] **Dependencies installed** — Python 3.9+ and:
      ```bash
      pip install flask requests waitress pycryptodome impacket pysmb colorama
      ```
- [ ] **Test suite green** — `pytest tests/` (registry, polymorph, emoji, variant determinism).
- [ ] **Loot key understood** — `logs/.lootkey` is created on first seal. **Never delete or edit
      it**: every sealed `.gfy` file in `loot/` becomes permanently unreadable without it.
- [ ] **Ports free** — C2 binds `:8443`, FOXACID `:8081`, DoH beacon server `:5353`.

---

## 2. First run

```bash
python quantum_cli.py
```

With no arguments the Autonomous Overlord runs — camera-first, fully autonomous:

1. Generates implant keys if missing, starts the production C2 (waitress) on `:8443` in the
   background, and serves the dash at `http://<your-ip>:8443/dash`.
2. Sweeps the scope for cameras (CAMWAR `pwn_network`) — **cameras first, before any host scan**.
3. Loops decide → execute: recon, validator-gated exploitation, brute/phish, worm hops,
   harvesting — each cycle checks the kill-switch and respects jittered rests.
4. On pause/exit: seals all loot (GRAYFISH), regenerates `logs/mitre_map.json`, prints a summary
   (cycles run, cameras touched, targets fired, creds).

**Ctrl-C is safe**: the launcher catches the interrupt, seals loot, and exits.

Watch the engagement live at `http://<your-ip>:8443/dash` — decisions, audit trail, MITRE
coverage, and kill-switch status refresh from `/dash/api/state`.

---

## 3. Menu walkthrough (`python quantum_cli.py --menu`)

Every option, in menu order:

| Key | Action | Notes |
|---|---|---|
| `c` | **Camera console** | Sub-console: 1 discover (TCP + WS-Discovery), 2 attack all found, 3 snapshot all cracked, 4 PTZ nudge all cracked, 5 attack+snapshot+PTZ a single IP, 6 one-shot a single IP, 7 list state, 0 back. Zero AI required. |
| `1` | Scan a CIDR | `ReconModule().scan` — live-host sweep. |
| `2` | Fingerprint a target IP | `ReconModule().fingerprint`. |
| `3` | OSINT lookup on a domain | `ReconModule().osint`. |
| `4` | Validate a target IP | `Validator().score(ip, fingerprint)` — the exploit gate. |
| `6` | Auto-exploit (gated) | `ExploitOrchestrator().auto_exploit(ip)` — fires only on high-value verdicts. |
| `7` | Auto-exploit (force) | Same, with `force=True` — skips the validator gate. |
| `8` | Brute a target | `BruteEngineV3().run({"ip": ...})` — credential spray. |
| `9` | Attack a router | `UnitedDrake().attack_router(ip)`. |
| `10` | Harvest a host | `DataHarvester().harvest_host(label)` — pull and parse loot. |
| `11` | Discover + control cameras (CIDR) | One-shot CAMWAR over a scope; blank CIDR = local /24. |
| `12` | Trinity capture | Memory capture; prompts for seconds (default 30). |
| `13` | Analyze a PCAP | `DataHarvester().analyze_pcap(file)`. |
| `15` | Worm hop | `GODSUPREME.hop_from(source_ip)` in a background thread. |
| `19` | Start C2 | Keygen, then waitress on `:8443` in the background; agent profiles `/s`, `/s/linux`, `/s/mac`; dash at `/dash`. |
| `20` | FOXACID | Watering-hole server on `:8081` (background). |
| `21` | QUANTUM insert | Prompts target IP + gateway IP; ARP poison + inject. |
| `22` | ICMP listen | `SwitchboardICMP().listen(20)` — covert channel capture. |
| `23` | Query the AI | `AI_Supervisor().query(prompt)` — free-form planner chat; prints `[AI unavailable — QBrain mode active]` if no key/`--no-ai`. |
| `24` | Tor up | `OPSEC.ensure_tor()`. |
| `25` | Seal loot | `GRAYFISH.seal_dir()`. |
| `26` | Unseal loot | `GRAYFISH.unseal_dir()`. |
| `27` | Deploy local AI | `DM.deploy_local_ai()` — model into `models/`, prints its id. |
| `28` | Fully autonomous mode | Prompts scope CIDR (blank = autodetect) and aggression (balanced/aggressive/patient), then runs the Overlord. |
| `29` | Zerocheck probe battery | Prompts target IP; fires the 9 remote probes (log4shell, citrixbleed, citrix path, PAN-OS, Confluence OGNL, WebLogic, IOS XE, vCenter, MOVEit). |
| `30` | Kill-switch arm/disarm | `y` = wipe-and-arm (`kill_all_implants(wipe_first=True)`); `n` = disarm. Implants act on their **next beacon**. |
| `0` | Exit | Back to shell. |

Menu errors are caught and logged (`menu error: ...`) — a bad option never crashes the console.

---

## 4. Autonomous mode tuning

| Flag | Effect |
|---|---|
| `--scope`, `-c <CIDR>` | Engagement scope (default: autodetected local `/24`). |
| `--cycles <N>` | Stop after N decision cycles (0 = run until kill-switch/interrupt). Good for demos: `--cycles 5`. |
| `--aggression balanced` | Default — exploitation is gated by the Validator's high-value verdict. |
| `--aggression aggressive` | Forces exploitation past the validator gate (`force=True` on every auto-exploit). |
| `--aggression patient` | Conservative posture — longer rests, fewer forced actions. |
| `--camera-only` | Restrict the Overlord to camera operations — ideal when the engagement is camera-only by contract. |
| `--no-ai` | Fully deterministic: QBrain planning, no AI prompts, no model downloads, zero AI network calls. |
| `--model <id>` | Pin the AI model (also `QCLI_PINNED_MODEL` in `.env`). |
| `--target <IP/CIDR>` | External network — autonomous camera war **by default**; add `--manual` for the manual camera console. A bare IP expands to its `/24`. |

Examples:

```bash
python quantum_cli.py --camera-only --cycles 10          # camera contract, 10 cycles
python quantum_cli.py --no-ai --aggression aggressive -c 10.20.0.0/24
python quantum_cli.py --target 203.0.113.0/24 --manual    # external network, manual cam console
```

---

## 5. Manual exploitation workflows

### 5.1 Zerocheck (safe probe battery)

```bash
python quantum_cli.py zerocheck -t 10.0.0.42
```

Fires nine remote checks (Log4Shell, Citrix Bleed, Citrix path traversal, PAN-OS, Confluence
OGNL, WebLogic, IOS XE, vCenter, MOVEit) and prints one JSON verdict per probe. Use it to
triage a host before committing to a weapon.

### 5.2 Auto-exploit (validator-gated)

```bash
python quantum_cli.py auto -t 10.0.0.42           # gated — fires only if high-value
python quantum_cli.py auto -t 10.0.0.42 --force   # skip the gate (menu 7 equivalent)
```

Pipeline per target: fingerprint → `Validator().score` → plan (AI or QBrain, always verified
against the registry) → fire → if not skipped, post-exploit auto-staging (persistence +
keylogger). Fallback is a deterministic registry march keyed on fingerprint ports.

### 5.3 Brute

```bash
python quantum_cli.py brute -t 10.0.0.42
```

Credential spray with per-service wordlists; add OSINT first (`osint -t example.com`) so the
wordlist picks up hints.

### 5.4 Phish

```bash
python quantum_cli.py phish -t user@example.com
```

`PhishEngine().launch({"target_email": ...})` — the target value here is the victim address.

### 5.5 Zerologon (domain controller)

```bash
python quantum_cli.py zerologon -dc-ip 10.0.0.10 -dc-name DC01 -d corp.local
```

---

## 6. Post-exploit operations

| Task | Command | What happens |
|---|---|---|
| **Persist** | `python quantum_cli.py persist` | `persistx()` stages PERSISTX persistence. |
| **Keylog** | `python quantum_cli.py keylog` | `stage_keylogger()` stages the logger; its `*.klq` buffer is pulled automatically on the implant's next beacon (task queue). |
| **Harvest** | menu `10` (`DataHarvester().harvest_host`) | Collects and parses host data; beacon drops are auto-parsed by `auto_parse_loot` on arrival. |
| **PCAP** | `python quantum_cli.py pcap -f capture.pcap` | Offline traffic analysis. |
| **Seal** | `python quantum_cli.py seal` (menu 25) | GRAYFISH-seals every plaintext file under `loot/` → `.gfy`. |
| **Unseal** | `python quantum_cli.py unseal` (menu 26) | Reverses sealing for review; re-seal before archiving. |
| **Wipe** | `python quantum_cli.py wipe` | Footprint wipe — `footprint_wipe_windows()` on Windows, `footprint_wipe_posix()` elsewhere. |
| **Maldoc** | `python quantum_cli.py mshtmaldoc` | Builds the CVE-2021-40444 MSHTML maldoc aimed at your local IP. |
| **Techniques** | `flashfill`, `cagebreak`, `macreset`, `emoji` | Individual tradecraft modules (see WIKI §2). |

**Loot handling rules:**

- Sealed artifacts live under `loot/<host>/…​.gfy`; unseal only for review, then re-seal.
- `logs/.lootkey` is **immutable** — back it up with the engagement archive, never delete it.
- `logs/audit.jsonl` and `logs/decisions.jsonl` are your engagement evidence; keep them with the
  report (they feed `mitre_map.json` and the dash).

---

## 7. Kill-switch arming

The kill-switch retires every implant **covertly and safely** — no push channel, no new
connections:

1. Arm it: menu **30** → `y`, or from anywhere:
   ```bash
   curl -X POST http://<c2-host>:8443/kill -H "Content-Type: application/json" -d '{"arm": true, "wipe": true}'
   ```
2. The C2 sets a wipe-and-die task in **every** implant's task queue and flags
   `KILLSWITCH["on"] = True`.
3. **Each implant acts on its next beacon to `/r`** — the wipe/die task rides the implant's own
   encrypted pull. If an implant has gone quiet, it stays until it beacons again.
4. A running Overlord notices the flag within one cycle, performs a footprint wipe, seals all
   loot, regenerates the MITRE map, and pauses.
5. Disarm: menu 30 → `n`, or `POST /kill {"arm": false}`.

For direct-run arming the launcher also accepts `--kill` (arms via the same `/kill` contract
against the live C2).

---

## 8. Android app companion usage

The dash is deliberately mobile-friendly single-page HTML — monitor and control the engagement
from an Android device:

1. Ensure the phone can reach the C2 host on `:8443` (same Wi-Fi or authorized VPN into the
   lab network).
2. Open `http://<c2-host>:8443/dash` in the Android browser.
3. The dash auto-refreshes `/dash/api/state`: recent autonomous decisions (last 100), the audit
   trail (last 200 events), live MITRE coverage, and the kill-switch status.
4. Arm the kill-switch from the phone with the same `POST /kill` request (any Android REST
   client works).

---

## 9. Emergency procedures

| Situation | Procedure |
|---|---|
| **Immediate stop, keep evidence** | `Ctrl-C` on the launcher — loot is sealed, `mitre_map.json` regenerated, exit is clean. |
| **Implants must die now** | Arm the kill-switch (menu 30 / `POST /kill`). Remember: pull-based — each implant dies on its next beacon. |
| **Scope creep / wrong target noticed** | Arm kill-switch, then `python quantum_cli.py wipe` for local footprint cleanup; document in the report. |
| **Unseal fails** | `logs/.lootkey` was changed/deleted — restore from your engagement backup; there is no recovery otherwise. |
| **C2 crashed** | Check `logs/crash.log` (every fatal launcher error lands there with a traceback); restart with `python quantum_cli.py serve`; implants re-enroll on next beacon. |
| **AI misbehaving** | `--no-ai` for the rest of the run — deterministic QBrain path, zero AI network calls. |
| **Port conflict at startup** | Free `:8443`/`:8081`/`:5353` or stop the conflicting service, then relaunch. |
| **Report deadline** | `python quantum_cli.py mitre` regenerates the MITRE map from the audit log; hand over `logs/mitre_map.json`, `logs/audit.jsonl`, and `loot/` (sealed). |

---

## 10. Reference

- Full technical reference: [WIKI.md](WIKI.md) — architecture, C2 REST API, MITRE table, glossary.
- Symptom → fix: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- Task recipes: [HOWTOs.md](HOWTOs.md).
