# QUANTUM-C2

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
