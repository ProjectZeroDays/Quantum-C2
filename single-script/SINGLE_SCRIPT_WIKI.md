# QUANTUM-CLI FINAL V3.1 — Wiki

**Author: Trey A Smith — [github.com/projectzerodays](https://github.com/projectzerodays)**

Quantum-CLI is intended for **authorized engagements only** (pentests, red teams, CTFs, labs, networks you own).

---

## Table of Contents
1. [Introduction](#introduction)
2. [What's New in V3.1](#whats-new-in-v31)
3. [Quick Start](#quick-start-1)
4. [Camera Warfare (CAMWAR)](#camera-warfare-camwar)
5. [V3 Zero-Day Registry](#v3-zero-day-registry)
6. [Autonomous Pipeline](#autonomous-pipeline)
7. [Post-Exploitation Suite](#post-exploitation-suite)
8. [Kill-Switch & Footprint Wiping](#kill-switch--footprint-wiping)
9. [Reverse DoH Persistence (GHOSTFANG-DNS)](#reverse-doh-persistence-ghostfang-dns)
10. [Polymorphic Engine V3](#polymorphic-engine-v3)
11. [AI Bootstrap](#ai-bootstrap)
12. [Autonomous Modes](#autonomous-modes)
13. [BruteEngineV3](#bruteenginev3)
14. [CLI Reference](#cli-reference)
15. [Manual Console](#manual-console)
16. [C2 REST API](#c2-rest-api)
17. [QUANTUMDASH](#quantumdash)
18. [MITRE ATT&CK Mapping](#mitre-attck-mapping)
19. [Logging & Debugging](#logging--debugging)
20. [Troubleshooting](#troubleshooting)
21. [Glossary](#glossary)
22. [License](#license)

---

## Introduction

QUANTUM-CLI FINAL V3.1 is a **single-file, fully autonomous offensive framework**. With no arguments it:

1. Autodetects your local /24 (or uses `--scope`),
2. **Camera-first**: sweeps TCP ports **and** ONVIF WS-Discovery, fingerprints vendors (Hikvision, Dahua, Axis, Foscam, TP-Link/Tapo, generic ONVIF/RTSP), sprays vendor-default credentials, exfiltrates snapshots (GRAYFISH-sealed at rest), nudges PTZ,
3. Then runs the AI/QBrain decision loop: recon → risk scoring → matched CVE fire → **automatic post-exploitation** (persistence, keylogger staging, harvesting, LPE),
4. Keeps egress covert (Tor, DoH), serves the production-WSGI C2 + dashboard on :8443,
5. Retires cleanly on kill-switch or cycle budget — with footprint wiping.

Everything self-installs. Everything degrades gracefully: no AI key → local model; no local model → deterministic QBrain. No component is a single point of failure.

## What's New in V3.1

| Change | Detail |
|---|---|
| Registry 6 → 27 CVEs | 21 real CVEs added with uniform `weapon(ip, params, **kw)`; V3_HIGH weapons are protocol-level (Log4Shell with OOBcallback LDAP listener, Citrix Bleed token theft + session reuse, PAN-OS 3400 traversal injection with output exfil, Confluence OGNL, WebLogic 14882, IOS XE 20198, SambaCry, vCenter webshell, Dirty Pipe completely inline) |
| Autonomous post-exploitation | `post_exploit_auto()` runs after each successful fire: PERSISTX (schtasks + run key), KITLOGGER staging, GRAYFISH exfil prep |
| Covert kill-switch | `POST /kill` — wipe+die commands queue on every implant via its existing encrypted beacon pull; dashboard shows kill-switch state |
| Reverse DoH | `ghostdns --domain` agent: egress via DoH label encoding through public resolvers, tasks via TXT — **no port forwarding** |
| PolyMorph v3 | epoch HMAC key diversification, UTF-7 nil escape variants, junk filler |
| Production WSGI | waitress primary (added to auto-install list), gunicorn POSIX, dev-server last resort |
| QBrain V3 | appliance-aware deterministic CVE rules (vmware→21972, citrix→4966, confluence→26134, globalprotect→3400, weblogic→14882, cisco ios→20198, log4j→44228); the web-port default is now Log4Shell, not Follina |
| BruteEngineV3 | RTSP DESCRIBE auth brute for cameras; GetNPUsers roast handoff (`hashcat -m 18200`) |
| Validator V3 | +40 priority for appliance fingerprints feeding the new registry |
| Technique modules | FLASHFILL (file + registry variants), EMOJISMS (with `+ / =` mapping for base64 transport), MacReset, CAGEBREAK |
| Bug fixes | Dirty Pipe priming/offset math + kernel gate + anti-forensic restore; PAN-OS payload quoting; Citrix Bleed token regex; SambaCry share walk; `plan_attack` registry-membership validation; global wiring order verified |

## Quick Start

```bash
python quantum_cli.py                              # FULLY AUTONOMOUS (camera-first)
python quantum_cli.py --no-ai                      # deterministic QBrain mode
python quantum_cli.py --scope 10.0.5.0/24
python quantum_cli.py --camera-only
python quantum_cli.py --cycles 50                  # cap loop at 50 decisions
python quantum_cli.py --target 192.168.7.0/24     # external net, autonomous cam war
python quantum_cli.py --target 192.168.7.0/24 --manual
python quantum_cli.py --menu
python quantum_cli.py camwar -c 10.0.0.0/24
python quantum_cli.py zerocheck -t 172.16.1.10     # 9-CVE probe battery
python quantum_cli.py mshtmaldoc                   # forge CVE-2021-40444 doc
python quantum_cli.py ghostdns --domain your.tld   # DoH-egress agent (no inbound ports)
python quantum_cli.py serve                        # C2+dash only (waitress WSGI, :8443)
python quantum_cli.py deployai                      # (re)install local AI model
```

## Camera Warfare (CAMWAR)

- **Discovery:** 14-port TCP Sweep (incl. 554/37777/37778/8081/8899/34567/34571/34599/5000) **plus** ONVIF WS-Discovery multicast Probe (`239.255.255.250:3702`) for boxes invisible to port sweeps, HTTP banner/login.asp second-pass fingerprinting, RTSP `OPTIONS` server-header fingerprinting, out-of-scope WS devices merged, ONVIF GetDeviceInformation enrichment
- **Cracking:** vendor DIGEST/BASIC default-credential tables weight sane alternates (Hik: `888888/66668888`, Dahua: `888888:888888`) + alt login endpoints `/doc/page/login.asp`, `/onvif/device_service`
- **Control:** per-vendor snapshot paths first (Hik ISAPI ch101/1/Video-inputs, Dahua snapshot.cgi, Axis, Foscam), cross-vendor + 9 generic fallbacks; magic-byte verification (JPEG `FFD8`, PNG `8950`); PTZ nudge with Hik stop command
- **V3 brute:** `python quantum_cli.py brute -t <CAM_IP>` with `service=rtsp` — DESCRIBE-auth brute with Basic credentials
- **OPSEC:** snapshot sealed (AES-256-GCM) immediately; random pacing 0.3–1.5 s between attacks; per-network JSON report sealed into `loot/`
- **Priority:** validator adds +40/+50 camera weight — cameras win exploit priority

## V3 Zero-Day Registry

| CVE | Name | Type |
|---|---|---|
| CVE-2020-1472 | Zerologon | legacy |
| CVE-2017-0144 | EternalBlue | legacy |
| CVE-2021-1675 | PrintNightmare | legacy |
| CVE-2021-36942 | PetitPotam | legacy |
| CVE-2022-30190 | Follina MSDT | legacy |
| CVE-2021-26855 | ProxyLogon | legacy |
| **CVE-2021-44228** | Log4Shell JNDI | **V3_HIGH** — OOB callback LDAP listener on :1389 |
| **CVE-2024-3400** | PAN-OS GlobalProtect | **V3_HIGH** — traversal `seh` injection, output exfil |
| **CVE-2023-4966** | Citrix Bleed | **V3_HIGH** — token leak + session hijack |
| **CVE-2019-19781** | Citrix Path Traversal | **V3_HIGH** — `newbm.pl` template write |
| **CVE-2023-20198** | IOS XE Web UI | **V3_HIGH** — escaped-restconf admin creation |
| **CVE-2022-26134** | Confluence OGNL | **V3_HIGH** — URI path exec staging |
| **CVE-2020-14882** | WebLogic Console | **V3_HIGH** — traversal bypass confirmation |
| CVE-2017-7494 | EternalRed SambaCry | V3_MED — share walk, .so staging |
| CVE-2021-21972 | vCenter Upload | V3_MED — uploadova webshell |
| CVE-2023-34362 | MOVEit SQLi | V3_CHECK |
| **CVE-2022-0847** | Dirty Pipe | **V3_HIGH inline** — pipe priming, page-cache overwrite, `/etc/passwd`, anti-forensic restore |
| CVE-2016-5195 | Dirty COW | alias → dirtypipe path |
| CVE-2021-3156 | Baron Samedit | V3_CHECK — version detect |
| CVE-2021-4034 | PwnKit | V3_CHECK |
| CVE-2023-2640 | Overlayfs GameOver | V3_CHECK |
| CVE-2023-32233 / CVE-2024-1086 | nf_tables UAF / dbl-free | V3_CHECK |
| CVE-2019-3568 | WhatsApp VOIP zero-click | V3_CHECK — profile-select delivery staging |
| CVE-2023-4863 | libwebp BLASTPAST | V3_CHECK |
| CVE-2023-41064 | Apple ImageIO zero-click | V3_CHECK |
| CVE-2021-30858 | WebKit sandbox escape | V3_CHECK |
| **CVE-2021-40444** | MSHTML sandbox escape | **V3_HIGH** — real maldoc forge via `mshtmaldoc` command |
| CVE-2022-21894 | BootHole Secure-Boot bypass | V3_CHECK |

## Autonomous Pipeline

1. Scope autodetect → partnerships: C2 + dash spawn (production WSGI)
2. Camera-first: full CamWar pwn sweep of scoped subnet
3. Decision loop (AI-driven JSON, QBrain fallback when AI is dead/unparseable): `cam_war, cam_discover, cam_control, recon_scope, exploit, brute, phish, worm, harvest, router, osint, episcribe, mitre_report, rest`
4. On **every successful `exploit`**: `post_exploit_auto()` — PERSISTX persistence staging (schtasks + runkey), KITLOGGER keylogger task queued for the newly pawned host (delivered on its next beacon), exfil prep
5. Deduplication: worm hops via GodSupreme with network-aware jitter
6. Kill-switch or cycle budget or Ctrl-C triggers: footprint wipe → GRAYFISH seal → MITRE map → clean exit

## Post-Exploitation Suite

- **PERSISTX** (`persist / TASKQ`): schtasks `'qcli-svc'` 15-min + HKCU Run-key on operator box; MFP (UEFI) covers firmware-level
- **KITLOGGER** (`keylog`): SetWindowsHookEx WH_KEYBOARD_LL PowerShell payload, buffer → `%TEMP%\kl.klq`, auto-loaded via TURBINE tasking; files sealed at rest
- **Credential harvesting**: `auto_parse_loot` + pypykatz (msv/wdigest/tspkg/kerberos) parses lsass dumps on C2 drop
- **LPE**: Dirty Pipe (password-field blank on root line or `rootclone::0:0` uid-0 append), PwnKit/Baron-Samedit/nf_tables deterministic checks; verify via /etc/passwd read-back
- **CAGEBREAK** (`cagebreak`): VM/sandbox/cloud detection (Win32_ComputerSystem/BIOS, systemd-detect-virt) informing escape selection

## Kill-Switch & Footprint Wiping

```bash
# arm: wipes remote implants on their next beacon, stops Overlord loop
curl -X POST http://<c2>:8443/kill -d '{"arm":true,"wipe":true}'
# disarm
curl -X POST http://<c2>:8443/kill -d '{"arm":false}'
```

- **Covert delivery**: the wipe/die tasks ride each implant's **existing encrypted beacon** (no new channel, no new ports) — the kill command is indistinguishable from tasking traffic
- **FOOTPRINT**: selective — clears only PowerShell/WinPS event logs and agent residue/kl.klq; `schtasks /delete /tn qcli*`; POSIX `sed -i` history edits, `.gn-*` removal, `shred -u` of the agent, `pkill` self — same effect on Linux
- **Outcome**: when the C2 kill-switch arms, the Overlord stops issuing new decisions, all remote implants wipe their traces & die, the operator box wipes its own residue, then GRAYFISH-seals and MITRE-maps the engagement

## Reverse DoH Persistence (GHOSTFANG-DNS)

The user-requested "Reverse DNS over HTTPS" channel — **no port forwarding, no inbound sockets**:

- **Implant egress**: beacon data → base32 → subdomain labels (`qcli-fragment.your-domain.tld`) resolved via Cloudflare/Google DoH (**outbound 443 only** — looks like a browser's benign DoH cache miss)
- **Task intake**: implant queries TXT at `cmd.your-domain.tld`, parses `{"cmd":"..."}` JSON, executes
- **Generation**: `python quantum_cli.py ghostdns --domain your.tld` (or `.env` `QCLI_DOMAIN`) → `ghostdns.sh`
- **Self-cleanup**: `wipe`/`kill` verbs recognized in the TXT stream — the kill-switch works over DoH too
- **HQ-side check**: `doh_task_check(domain)` reads the operator's TXT record for confirmation
- **Persistence**: because egress is indistinguishable from recursive DNS, this survives even outbound-only NAT/firewall policies

## Polymorphic Engine V3

`PolyMorphEngineV3` (PAYLOADS in V3.1):
- **Per-beacon epoch keys**: raw random key wrapped via HMAC-SHA256 with an incrementing ep--och counter — the same payload key never appears on the wire twice
- **Variant encoding**: odd epochs serialize as **UTF-7** with a `|mode:utf7` marker; even epochs plain JSON — statistical per-flow signatures break
- **Junk filler**: random 0–64 bytes of `junk` per envelope
- **Cipher rotation** (inherited): AES-256-GCM / ChaCha20-Poly1305 / RC4-POLY
- **RTL**: decryptors share the epoch counter (class-level); TX side and RX side (FoxAcid, C2 drops) stay in sync
- **Honesty note**: this is "serious red-team parity". True nation-state parity additionally requires a per-sample compile chain (metamorphic compilation, register renaming, control-flow flattening per implant) — documented roadmap, not possible in a single file

## AI Bootstrap

1. Search `.env` and environment for `ABLITERATION_KEY`
2. Found → online Abliterated.ai primary, local fallback on failure
3. Not found → **5-second prompt** (unattended-safe; silence = "no")
4. If "y" → paste key (60 s window); saved to `.env`
5. If "n" → search script dir for model (`./models` with real blobs, or the daemon holds it); if missing, **install Ollama + download model into `./models`**
6. `--no-ai` / `QCLI_NO_AI=1` skips all of it — deterministic QBrain operation
7. Whole bootstrap journaled to `logs/ai_bootstrap.json`

Model: RAM-adaptive ≥16 GB → `whiterabbitneo/wrn-llama-3.1-8b:latest`, <16 GB → `huihui-ai/qwen3-1.7b-abliterated:Q4_K_M`; pin via `--model`.

## Autonomous Modes

- **Default (no flags):** autodetect /24 → C2 + dash → CamWar full sweep → AI/QBrain loop (decisions journaled; kill-switch/cycle budget aware; auto post-exploit stage on every fire)
- **`--no-ai`:** everything above, pure QBrain determinism, zero prompts, zero model downloads
- **`--target CIDR`:** external-net autonomous camera war (default); `--manual` → camera console instead
- **`--camera-only`:** loop restricted to `cam_war, cam_discover, cam_control, mitre_report, rest`
- **`--cycles N`:** decision-count cap; **`--aggression`:** balanced|aggressive|patient

Every mode: GRAYFISH seal + MITRE map at close; kill-switch triggers footprint wipe.

## BruteEngineV3

- -`service=smb` (default): classic SMB login beat with ThreadPoolExecutor(16); `--users`, `--passes`, or AI-tuned/QBrain wordlists with OSINT hints
- `service=rtsp`: DESCRIBE-auth brute (Basic credentials) per RTSP server; SSE on `admin/root/service/viewer` + tuned wordlist; logs `RTSP CRACKED ip: user:pass`
- `service=kerberoast|asreproast`: impacket GetNPUsers handoff; output ready for `hashcat -m 18200`
- Lockout etiquette: computing still spray-shape (small users × large passwords), not password-shape

## CLI Reference

`serve · foxacid · quantum · recon · osint · auto · dohc2 · icmp · trinity · camwar · cams · wifi · triage · mfp · pcap · camshot · router · worm · episcribe · cottonmouth · validator · tor · seal · unseal · brute · phish · keygen · deployai · zerologon · mitre · federation · posixagent · zerocheck · mshtmaldoc · flashfill · emoji · macreset · keylog · wipe · persist · ghostdns · cagebreak`

Flags: `--menu · --scope/-c · --target/-t · --manual · --camera-only · --no-ai · --cycles · --aggression {balanced|aggressive|patient} · --model · --kill · --domain · -g/--gateway · --iface · --peer · -dc-ip · -dc-name · -d · -f/--file · --force`

Notables:
| Command | Use |
|---|---|
| `zerocheck -t IP` | battery-fire Log4Shell/Citrix Bleed/Citrix Path/PAN-OS/Confluence/WebLogic/IOS XE/vCenter/MOVEit — great all-in-one recon |
| `ghostdns --domain your.tld` | DoH-egress agent (no port forwarding) |
| `flashfill` | storage exhaustion until volume-ready bootloop |
| `keylog` / `persist` / `wipe` | single-shot post-exploit staging at operator box |
| `mshtmaldoc` | forge real CVE-2021-40444 OOXML maldoc |
| `emoji` | demo of EMOJISMS emoji covert channel |
| `macreset` | recovery-mode password reset script |
| `cagebreak` | sandbox/VM/cloud environment assessment |

## Manual Console

`python quantum_cli.py --menu` — camera console (option `c`), scan/fingerprint/OSINT/validate, auto-exploit (gated/forced), BruteEngineV3, router takeover, harvest, Trinity audio, PCAP, worm hops, C2/FOXACID/QUANTUM/ICMP, zerocheck battery (29), **kill-switch arm/disarm (30)**, AI query, Tor, seal/unseal, deploy local AI, and mode 28 → fully autonomous.

## C2 REST API (port 8443, production WSGI)

| Route | Method | Purpose |
|---|---|---|
| `/s/<profile>` | GET | agent scripts (default OBSIDIAN ps1, linux/mac GHOSTFANG) |
| `/r` | POST | beacons (OBSIDIAN RSA-envelope, GHOSTFANG plain-JSON); TURBINE enroll; loot drop → auto-parse → seal |
| `/ai` | POST | full API dispatcher — incl. `zerocheck`, `flashfill`, `emojisms`, `rtspbrute`, `roast`, `macreset`, `mshtmaldoc`, `camwar/family` |
| `/kill` | POST | **kill-switch**: `{"arm":true,"wipe":true}` wipes+dies all implants on their beacons |
| `/federation/reg` | GET/POST | implant registry sync |
| `/federation/peer` | POST | peer-onion registration |
| `/dash`, `/dash/api/state` | GET | dashboard + state JSON (incl. `killswitch` field) |

**WSGI chain:** waitress (threads=16, channel_timeout=30) primary on every OS → gunicorn (workers=4) POSIX → Flask dev last resort. Waitress auto-installed.

## QUANTUMDASH

Auto-refresh (3 s) dark dashboard at `http://<box>:8443/dash`: AI decisions (with reasons), colored engagement log (camera events highlighted), live MITRE coverage, **kill-switch state**.

## MITRE ATT&CK Mapping

Keyword rules map `audit.jsonl` → `mitre_map.json`. V3.1 adds: Log4Shell/Citrix-Bleed/PAN-OS/Confluence → T1190; Dirty Pipe/PwnKit/Baron-Samedit → T1068; FLASHFILL → T1499; EMOJISMS → T1132.001; RTSP brute → T1110.003; zerocheck → T1595; MSHTML → T1203; BootHole → T1542.001. Auto-generated at engagement close, on `mitre` command, `/ai mitre`, and live on the dashboard.

## Logging & Debugging

- `logs/audit.jsonl` — every event
- `logs/decisions.jsonl` — each AI/QBrain choice + reason
- `logs/ai_bootstrap.json` — AI decision trail
- `logs/mitre_map.json` — ATT&CK coverage
- `logs/crash.log` — tracebacks if a fatal error occurs (script still exits cleanly)
- `loot/*.gfy` — GRAYFISH-sealed evidence (don't delete `logs/.lootkey`)

## Troubleshooting

| Symptom | Fix |
|---|---|
| Waitress missing | Auto-installed first run; `pip install waitress` |
| First run slow |_dependency + model download into `./models` (multi-GB on ≥16 GB RAM hosts) |
| Cameras found but never crack | Non-default creds; extend `CAMWAR.CREDS` or use `brute` with `service=rtsp` |
| Dirty Pipe reports "unlikely vulnerable" | Kernel ≥5.16.11/5.15.25/5.10.102 — patch version is safe; check with `uname -r` |
| `ghostdns` says no domain | `--domain your.tld` or `.env` `QCLI_DOMAIN`; you must control the zone for TXT tasking |
| `zerocheck` all say "probe fired" | Target isn't the appliance — or vendor non-standard install; check manual ports |
| Kill-switch not killing | Implant must beacon *after* arming (60 s default loop); check `TASKQ` in dash |
| `unseal fail` | Never delete `logs/.lootkey` |
| eBPF attach fails | Linux+root+BCC only; scapy QUANTUM is automatic fallback |

## Glossary

**CAMWAR** camera warfare engine · **Overlord** autonomous loop · **VALIDATOR** pre-fire risk scoring · **GFY** GRAYFISH-sealed file · **V3_HIGH/MED/CHECK** weapon confidence tier · **QBrain** deterministic fallback brain · **PERSISTX** persistence staging · **KITLOGGER** keylogger staging · **FOOTPRINT** selective trace wiping · **KILLSWITCH** covert wipe/die broadcast · **GHOSTFANG-DNS** DoH-egress agent · **EMOJISMS** emoji covert channel · **FLASHFILL** storage exhaustion · **CAGEBREAK** sandbox/VM/cloud escape assessment · **MacReset** recovery-mode credential reset · **PolyMorph v3** epoch-keyed polymorphic envelope · **waitress/gunicorn** production WSGI · **Bootstrap** .env→prompt→local-model AI chain

## License

MIT. © 2026 Trey A Smith. Use only against systems you own or are authorized to test.