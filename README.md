# QUANTUM-C2

[![Release](https://img.shields.io/github/v/release/ProjectZeroDays/Quantum-C2?style=flat-square&color=268bee&label=release)](https://github.com/ProjectZeroDays/Quantum-C2/releases)
[![License](https://img.shields.io/badge/license-MIT-3fb950?style=flat-square)](https://github.com/ProjectZeroDays/Quantum-C2/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![CVE catalog](https://img.shields.io/badge/catalog-3%2C372%20CVEs-8957e5?style=flat-square)](https://github.com/ProjectZeroDays/Quantum-C2/tree/main/exploit_catalog)
[![Post-ex modules](https://img.shields.io/badge/post--ex-175%20modules-d29922?style=flat-square)](https://github.com/ProjectZeroDays/Quantum-C2/tree/main/src/quantum/rat/modules)
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

**## Platforms

- **Ships:** Windows (PyInstaller EXE), Linux, Android (APK built in CI)
- **Script only, no artifact committed:** macOS (`build/mac/build-dmg.sh`)
- **Not produced:** iOS (`.ipa` needs an Apple toolchain), `.deb`, `.snap`**
**One launcher. One engagement. Recon to sealed loot to MITRE report — with no operator in the loop.**

QUANTUM-C2 is an autonomous offensive security framework built for authorized penetration tests, lab ranges, and contracted engagements. Point it at a scope and the Overlord runs the loop itself: camera-first sweep, fingerprinting, validator-gated exploitation, post-exploitation staging, harvest, AES-256-GCM sealing, MITRE mapping. `Ctrl-C` seals the loot and exits clean.

It is not a wrapper around someone else's tooling. The C2, the implant transports, the exploit registry, the loot sealing, and the reporting layer are all in this repo and all run locally.

> **Authorized engagements only.** QUANTUM-C2 assumes written authorization for every network you point it at.

## What's in the box

| | |
| --- | --- |
| **Autonomous Overlord** | Unattended engagement loop with aggression postures, validator gating, and cycle caps. Runs deterministic (`--no-ai`) or AI-planned. |
| **Production C2** | Waitress-served WSGI C2 on `:8443` with a covert kill-switch that wipes and retires every beaconing implant. |
| **DoH egress implants** | GHOSTFANG-DNS beacons ride public DoH resolvers on 443/tcp as base32 subdomain labels. No inbound ports; tasking over DNS TXT. |
| **3,372-CVE catalog** | Indexed by CVE and by vendor across 95 vendors, with a tiered registry, a fire contract, and a daily auto-update workflow. |
| **175 post-ex modules** | 14 lanes: credentials, crypto, forensics, privesc, persistence, evasion, network, radio, exfil, control, accounts, OTP, MITM, abuse. |
| **Camera warfare** | TCP and WS-Discovery discovery, vendor fingerprinting, credential spray, snapshot and PTZ control. |
| **PolyMorph v3** | Per-beacon epoch-keyed HMAC keystreams with junk filler — identical plaintexts never produce identical wire bytes. |
| **Sealed loot** | Everything sealed at rest with AES-256-GCM. The sealing key is created once and never rewritten. |
| **Listener manager** | Unique port allocation per engagement; every listener serves and receives callbacks independently. |
| **Android operator app** | On-device dashboard, tasking, and telemetry against the same API. |

## What this is not

Read this before you file an issue.

**Not a Metasploit replacement.** The catalog indexes 3,372 CVEs. It does not fire 3,372 exploits. Catalogued means "known, referenced, and linked" — a much smaller set is weaponized into a module that actually runs, and an even smaller set is validator-gated. Check `exploit_catalog/` for what a given CVE actually is before assuming `auto` will land it.

**Not a Cobalt Strike clone.** There is a C2, malleable-enough transports, and a kill-switch. There is no team server, no multi-operator session sharing, no Malleable C2 profile language. One operator, one box, one engagement.

**Not a commercial spyware equivalent.** The Mobile RAT and Pegasus tabs document real technique categories — location, SMS, calls, media, contacts, OTP interception. The Pegasus material is *reference and technique mapping*, not an implementation of NSO's implant. No zero-click iMessage chain ships here.

**Not quiet.** Recon is a sweep. A default autonomous run on a /24 is loud, and `--aggression aggressive` is louder still. If the engagement has an IDS budget, plan for it.

**Not Windows-first.** A meaningful number of modules are POSIX-only or were developed against Linux targets. Windows coverage exists and is tested in CI, but the bias is toward Linux, routers, and cameras.

**Not an AV-evasion product.** PolyMorph changes wire bytes, not on-disk signatures. Nothing here guarantees a bypass against a current EDR.

**Not a hosted service.** Everything runs locally. No account, no telemetry, no license server, no phone-home. That also means no one is going to fix your environment for you.

**Not affiliated with the real thing.** The QUANTUM, FOXACID, and CAMWAR names are homage to the published TAO tooling. This is an independent reimplementation and shares no code with it.

**Not a supported product.** Single maintainer, best-effort, no SLA. Issues get read; not all of them get fixed.

## Quick start

```bash
git clone https://github.com/ProjectZeroDays/Quantum-C2
cd Quantum-C2
pip install -r requirements.txt

python quantum_cli.py                                  # autonomous, camera-first, local /24
python quantum_cli.py --target 203.0.113.0/24          # external scope
python quantum_cli.py --no-ai --cycles 5               # fully deterministic, no AI calls
python quantum_cli.py serve                            # C2 only, no autonomy
```

Python 3.9+. No arguments means fully autonomous — the Overlord starts the C2, sweeps scope, and loops. See [OPERATOR_SURFACE.md](OPERATOR_SURFACE.md) for every command and flag.

## Where to read next

- [docs/WIKI.md](docs/WIKI.md) — architecture, module map, MITRE mapping, REST API
- [docs/OPERATOR_MANUAL.md](docs/OPERATOR_MANUAL.md) — runbook
- [docs/ZERO_CLICK_AUDIT.md](docs/ZERO_CLICK_AUDIT.md) — payload audit and stated honesty boundaries
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — symptom to fix

MIT licensed.
