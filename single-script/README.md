<div align="center">



\# ⚛️ QUANTUM-CLI FINAL V3.1

\### Unified Autonomous Offensive Framework — Camera Dominance, 27-CVE Registry, Production WSGI C2

\## Files in this directory

| File | Purpose |
|---|---|
| `quantum-cli_Single-Version.py` | Single-file Quantum CLI (full framework) |
| `Q-Android-ADB-Zero-Click-Exploit.py` | Q-Android v15.1 ADB zero-click framework (ZeroClickArsenal: webkit/iMessage/WhatsApp/BlueFrag/KRACK; Kyber/Dilithium PQ crypto; AI model management; exfiltration) |
| `tao_nexus_v20.py` | TAO v20.1 NEXUS COMMANDER standalone (auto-exploitation, WebSocket C2, RDoH, PQ crypto, Bash Bunny payload generation) — interactive menu |

See `../docs/ZERO_CLICK_AUDIT.md` for the zero-click exploit audit that verified these frameworks.



\[!\[Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python\&logoColor=white)](https://python.org)

\[!\[Version](https://img.shields.io/badge/version-3.1-informational)](https://github.com/projectzerodays)

\[!\[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

\[!\[Platform](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)

\[!\[AI](https://img.shields.io/badge/AI-Abliterated%20%7C%20Ollama-ff69b4.svg)](#ai-bootstrap)

\[!\[No-AI](https://img.shields.io/badge/QBrain-Full%20No--AI%20Mode-blueviolet.svg)](#autonomous-modes)

\[!\[CAMWAR](https://img.shields.io/badge/CAMWAR-v3-red.svg)](#camera-warfare-camwar)

\[!\[Zero-Days](https://img.shields.io/badge/Registry-27%20CVEs-9cf.svg)](#v3-zero-day-registry)

\[!\[WSGI](https://img.shields.io/badge/C2-Waitress%20%2F%20Gunicorn-green.svg)](#c2-rest-api)

\[!\[Kill-Switch](https://img.shields.io/badge/KillSwitch-Covert%20%2F%20Wipe-critical.svg)]#kill-switch--footprint-wiping)

\[!\[MITRE](https://img.shields.io/badge/MITRE-Auto--mapped-orange.svg)](#mitre-attck-mapping)

\[!\[OPSEC](https://img.shields.io/badge/OPSEC-Tor%20%2B%20GRAYFISH%20%2B%20DoH-blueviolet.svg)](#opsec)

\[!\[PolyMorph](https://img.shields.io/badge/PolyMorph-V3%20Epoch%20Keys-e91e63.svg)](#polymorphic-engine-v3)

\[!\[Author](https://img.shields.io/badge/Author-Trey%20A%20Smith-purple.svg)](https://github.com/projectzerodays)



\*\*\[📘 Full Wiki](#wiki) · \[🚀 Quick Start](#quick-start) · \[🎥 Wiki (long form)](#part-b--wiki)\*\*



\*\*AUTHORIZED ENGAGEMENTS ONLY\*\* — pentests, red teams, CTFs, labs, networks you own.



</div>



\---



\## Quick Start



```bash

python quantum\_cli.py                        # fully autonomous, camera FIRST, local /24

python quantum\_cli.py --no-ai                # 100% deterministic (QBrain), zero AI, zero prompts

python quantum\_cli.py --scope 10.0.5.0/24   # autonomous on chosen scope

python quantum\_cli.py --camera-only          # cameras only, forever

python quantum\_cli.py --target 192.168.7.0/24          # autonomous camera war on EXTERNAL net (default)

python quantum\_cli.py --target 192.168.7.0/24 --manual # manual camera console on that net

python quantum\_cli.py --menu                 # interactive console

python quantum\_cli.py camwar -c 10.0.0.0/24 # one-shot camera takeover, JSON out

python quantum\_cli.py zerocheck -t 10.1.2.3 # V3: rapid 9-CVE probe battery

python quantum\_cli.py ghostdns --domain your.tld  # V3.1: DoH-egress agent (no port forwarding)

```

Live dashboard: \*\*http://127.0.0.1:8443/dash\*\*



Kill-switch: \*\*`curl -X POST http://127.0.0.1:8443/kill -d '{"arm":true,"wipe":true}'`\*\* — wipes \& retires every implant on its next beacon.



\## V3.1 Headliners



| Feature | What it does |

|---|---|

| \*\*27-CVE registry\*\* | Log4Shell (w/ OOB JNDI listener), Citrix Bleed, PAN-OS 3400, Confluence OGNL, WebLogic, IOS XE, SambaCry, vCenter, MOVEit, Dirty Pipe (inline), PwnKit, Baron Samedit, overlayfs/nf\_tables, WhatsApp VOIP zero-click, libwebp, Apple ImageIO, WebKit \& MSHTML escapes, BootHole + the 6 legacy weapons |

| \*\*Autonomous post-exploitation\*\* | After every successful fire: PERSISTX persistence, KITLOGGER keylogger staging, credential harvesting, Dirty Pipe LPE — all automatic |

| \*\*Covert kill-switch + footprint wipe\*\* | `POST /kill` queues wipe/die tasks down the implant's own encrypted beacon; event-log trimming, agent residue removal, schtasks cleanup |

| \*\*Reverse DoH persistence\*\* | GHOSTFANG-DNS agent — all egress is outbound 443 DoH lookups to Cloudflare/Google; \*\*zero inbound ports, zero port-forwarding\*\*; tasks retrieved as DNS TXT on your domain |

| \*\*PolyMorph v3\*\* | Per-beacon epoch HMAC key diversification, UTF-7 nil-escape variant encoding, junk filler — identical plaintexts never produce identical wire bytes |

| \*\*Production WSGI\*\* | Waitress primary (all OS), gunicorn (POSIX), Flask dev server as last resort only |

| \*\*QBrain V3\*\* | Deterministic CVE rules extended to the full new registry — `--no-ai` mode selects Log4Shell/Citrix/vCenter/PAN-OS/etc. from fingerprints with zero AI |

| \*\*BruteEngineV3\*\* | RTSP DESCRIBE auth brute, kerberoast/AS-REP roast (hashcat handoff) |

| \*\*FLASHFILL / EMOJISMS / MacReset / CAGEBREAK\*\* | storage-exhaustion (bootloop-style), emoji covert channel, recovery-mode password reset, sandbox/VM/cloud escape assessment |



\## Extended CLI



`serve · foxacid · quantum · recon · osint · auto · dohc2 · icmp · trinity · camwar · cams · wifi · triage · mfp · pcap · camshot · router · worm · episcribe · cottonmouth · validator · tor · seal · unseal · brute · phish · keygen · deployai · zerologon · mitre · federation · posixagent · zerocheck · mshtmaldoc · flashfill · emoji · macreset · keylog · wipe · persist · ghostdns · cagebreak`



Flags: `--menu · --scope/-c · --target/-t · --manual · --camera-only · --no-ai · --cycles · --aggression · --model · --kill · --domain · -g/--gateway · --iface · --peer · -dc-ip · -dc-name · -d · -f/--file · --force`



\## Self-Installing



Pip packages, system tools (Ollama, Tor, Waitress), and the AI model (into `./models`) install automatically on first run. Runs 100% of capabilities with zero API keys, zero AI (`--no-ai`), zero manual steps.



MIT © 2026 Trey A Smith. Use only against systems you own or are authorized to test.

&#x20;

