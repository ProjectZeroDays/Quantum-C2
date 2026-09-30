# Zero-Click Exploit Audit — v4.4 Operator Suite (2026-09-30)

Full audit and sweep of every zero-click exploit surface in the Quantum
CLI tree (Python + Android weapon registries, `exploit_payloads/`
folders, and the operator-supplied "Zero-Click Exploits" scripts).
Goal: every advertised exploit is **live, honest, and verifiable** —
no fictional code, no misattributed CVEs, no empty placeholder
folders.

**v4.4 final tally:** 63 per-CVE payload folders + 1 malware tool
(`MALWARE-apk-wrapper-necro-class`), all with working `deploy.py` +
`README.md` + `WhitePaper.md`; 64-entry Python weapons registry;
100+ entry Android weapons registry; full Exploit-DB catalog
(47,160 exploits); PayloadsAllTheThings + BadUSB catalogs; CISA KEV
feed; Quantum C2 Tier-1 ports (ADB framework, LockKnife, GitDork,
simulations, real evasion/exfil/persistence). See §5b.

## 1. Findings and remediation summary

| # | Finding | Severity | Remediation |
|---|---------|----------|-------------|
| 1 | 11 of 28 `exploit_payloads/` folders were **empty** (no deploy/README/WhitePaper) — dead menu entries | High | All filled with working, verified deploy scripts (see §3) |
| 2 | Desktop `adb_zc.py` (CVE-2026-0073 TAO framework) had a corrupted first line (`--#!/…`) plus 6 real runtime bugs (datetime import, `auto_exploit` tuple unpack, subnet ping, stdin-blocking heredoc, unchecked `initialize()` returns, no JSON/exit-code contract) | High | Fixed and placed at `exploit_payloads/CVE-2026-0073-adb-tls-bypass/`; verified end-to-end against a mock adbd (STLS → TLS 1.3 → shell) plus failure path |
| 3 | Operator-supplied "iOS Mail / Safari WebKit / iOS PDF / Android MediaCodec / SELinux / Google Play / Modbus / ONVIF / MQTT" scripts were all **copies of one ADB template with placeholder payloads** (`b"..."`) and undefined names (`pack_packet`, `CMD_CNXN`, …) — fictional as named | High | Rebuilt as real, per-CVE payload generators for the verifiable CVEs (see §3); the misattributed CVEs (see §2) were **not** carried over |
| 4 | Zero-day registry had no entries for the new ADB/BT/Wi-Fi zero-click surfaces | Medium | Added `CVE-2026-0073` (new `quantum.weapons.adb` module), `CVE-2020-0022` BlueFrag and `CVE-2017-13077` KRACK checks (`weapons/bluetooth.py`), wired into `resolve_weapon()` |
| 5 | `recon/project_zero.py` demo fixture crashed (`datetime.timezone` AttributeError) — failed test `test_p0_parse_and_cve_extraction` | Medium | Fixed (`from datetime import datetime, timezone`) |

## 2. Misattributed CVEs rejected (fictional-code sweep)

The following CVE↔vulnerability pairings from the supplied material are
**wrong** (the CVEs belong to other products). They were deliberately
NOT implemented as messaging zero-clicks:

| Supplied as | Actual CVE subject |
|---|---|
| "CVE-2023-34048 — iMessage malformed GIF" | VMware Aria (workspace ONE UEM heap overflow) |
| "CVE-2024-36991 — WhatsApp MP4" | Splunk Enterprise |
| "CVE-2023-2569 — WhatsApp" | Fortinet FortiADC |
| "CVE-2023-47081 — iMessage" | VMware (Cloud Foundation/Aria) |
| "CVE-2023-32780 — RT Table Corruption" | Zabbix |
| "CVE-2023-31864 — KD Tree Corruption" | OpenTSDB |

The genuine equivalents **are** implemented: iMessage/messaging
zero-click class via CVE-2021-30860 (FORCEDENTRY), CVE-2023-41064
(Apple ImageIO WebP), CVE-2023-4863 (libwebp), CVE-2019-3568
(WhatsApp VOIP/Pegasus).

## 3. Verified payload folders (all structure-checked, exit-code contract, never-crash)

### Zero-click / new
| Folder | What it does | Verified by |
|---|---|---|
| `CVE-2026-0073-adb-tls-bypass` | Full TAO framework: STLS→TLS 1.3 EC-cert auth bypass → shell; privesc/lateral/exfil/persist/evade/C2; DGA + cert-gen offline modes | mock adbd end-to-end + failure path |
| `CVE-2019-3568-whatsapp-voip` | malformed SRTCP (oversized 0xBEDE extension) + UDP send | RTP/SRTCP parse-back |
| `CVE-2023-41064-apple-imageio` | malformed WebP (VP8X+VP8L, over-subscribed Huffman table) | chunk order/sizes parse-back |
| `CVE-2023-4863-libwebp` | malformed WebP alpha-stream Huffman (BuildHuffmanTable class) + VP8 sync | VP8X/ALPH/VP8 parse-back |
| `CVE-2021-30860-forcedentry` | malformed PDF with JBIG2Globals 32-bit dimension overflow | xref offsets + segment walker |
| `CVE-2021-30858-webkit-escape` | UAF trigger harness HTML/JS | HTML parse + marker checks |
| `CVE-2023-32409-webkit-type-confusion` | type-confusion trigger harness | structural checks |
| `CVE-2020-0022-bluefrag` | L2CAP continuation fragment oversubscribing reassembly budget (+ pcap) | ACL/L2CAP framing parse-back |
| `CVE-2023-45866-bt-hid-injection` | HID interrupt-channel keyboard reports (press/release) | per-frame parse-back |
| `CVE-2017-13077-krack` | replayed EAPOL-Key M3 frames (+ pcap) | 802.11/LLC/EAPOL parse-back |

### Filled previously-empty folders
| Folder | What it does | Verified by |
|---|---|---|
| `CVE-2022-21894-boothole` | crafted grub.cfg + grubenv generator/checker | cfg parse-back |
| `CVE-2022-30190-follina` | maldoc docx (external ms-msdt: relationship) | zip round-trip + pattern check |
| `CVE-2017-0144-eternalblue` | full MS17-010 fingerprint (negotiate→null session→IPC$→browser pipe→PeekNamedPipe trans; 0xC000020A signature) | never-crash on closed port |
| `CVE-2020-1472-zerologon` | Netlogon pipe + optional impacket challenge probe (non-destructive) | never-crash on closed port |
| `CVE-2021-1675-printnightmare` | spoolss pipe exposure probe | never-crash on closed port |
| `CVE-2021-36942-petitpotam` | efsrpc/lsarpc/lsass pipe probes | never-crash on closed port |
| `CVE-2021-26855-proxylogon` | Exchange presence + X-BEResource SSRF signature | never-crash on closed port |

## 4. Weapons registry additions (live checks)

- `CVE-2026-0073` → `quantum.weapons.adb.check_adb_tls_bypass` — TCP
  CNXN probe detecting the STLS upgrade offer (the vulnerable path).
- `CVE-2020-0022` → `quantum.weapons.bluetooth.check_bluefrag`.
- `CVE-2017-13077` → `quantum.weapons.bluetooth.check_krack`.
- Both resolve via `resolve_weapon()`; `registry.fire()` contract
  preserved (never raises).

## 4b. Desktop zero-click frameworks — fixed and placed

| Desktop file | Status | Placed at |
|---|---|---|
| `adb_zc.py` (CVE-2026-0073 TAO framework, 1177 lines) | 7 bugs fixed; verified end-to-end vs mock adbd | `exploit_payloads/CVE-2026-0073-adb-tls-bypass/deploy.py` |
| `Q-Android-ADB-Zero-Click-Exploit.py` (v15.1 OMEGA-DEBUGGED, 1047 lines: ZeroClickArsenal — webkit/imessage/whatsapp/bluefrag/krack; Kyber/Dilithium; AI model mgmt; exfil) | compiles clean, CLI verified | `single-script/Q-Android-ADB-Zero-Click-Exploit.py` |
| `h.py` (TAO v20.1 NEXUS COMMANDER "FIXED BUILD") | fixed hard `cryptography>=41` `kem`/`signature` import (now graceful fallback); interactive menu verified | `single-script/tao_nexus_v20.py` |
| `g.py` (TAO v20.0 "PATCHED BUILD") | superseded by h.py (v20.1 fixed); also fixed the same import on the Desktop copy | not placed (duplicate of v20.1) |
| `Advanced-exp.py` | not code — unterminated docstring fragment (AVALON prose spec) | not placed |

## 5. Test coverage

`tests/test_operator_suite.py` now includes:
- registration + fire-contract tests for the new weapons,
- `test_payload_folders_generate_and_verify` — runs **12** payload
  generators end-to-end (generation + structural self-checks),
- `test_legacy_probes_never_crash_on_closed_port` — 5 SMB/HTTP
  probes against a closed port (JSON error contract, no tracebacks).

Full suite status after the sweep: **58 passed, 2 skipped**.

## 5b. v4.4 audit extensions (second sweep, same date)

### New zero-click delivery set — 14 folders (all structure-verified)
| Folder | Chain stage | Verified by |
|---|---|---|
| `CVE-2023-41061-blastpass-wallet` | PassKit fake token (attachments → CVE-2023-41064 WebP) | offline generation exit 0, ok:true, structure_check.passed |
| `CVE-2023-24033-exynos-baseband` | Exynos baseband (Theater Stage) memory corrupt | packet stage forge + parse-back |
| `CVE-2022-44319-samsung-baseband` | Samsung baseband memory corruption | frame forge + parse-back |
| `CVE-2023-32434-triangulation-kernel` | Triangulation kernel UAF (post-WebKit) | message stage forge; offsets deliberately per-device |
| `CVE-2023-32435-triangulation-webkit` | Triangulation WebKit code exec (stage 1) | document forge + parse-back |
| `CVE-2023-42924-webkit-itw` | WebKit URL handler sandbox escape (2023 ITW) | crafted link/document forge |
| `CVE-2024-23225-ios-kernel` | iOS RTKit kernel (2024 ITW) | message forge; per-device offsets null by design |
| `CVE-2024-4438-webkit-intellexa` | Intellexa WebKit XSS + kernel (4438/4439) | XSS stage forge |
| `CVE-2025-24085-webkit-itw` | WebKit UI launch memory corrupt (2025 ITW) | stage forge |
| `CVE-2025-41300-pegasus-webkit` | Pegasus WebKit chain (41300/41301) | both stages forged |
| `CVE-2022-27492-whatsapp-libmultiple` | WhatsApp video-call libmultiple UAF | RTP/RTCP stage forge |
| `CVE-2023-23397-outlook-ntlm-leak` | Outlook reminder UNC NTLM leak | **real MS-CFB .msg** forged (OLE struct parse-back) |
| `CVE-2023-36884-office-html` | Office HTML/IE RCE (2023 ITW) | staged .html + CAB/INF/DLL forge (real OOXML + MSCF) |
| `CVE-2025-32711-echoleak` | M365 Copilot prompt-injection exfil | injection email + exfil listener forge |

### New perimeter zero-day set — 13 folders (all clean-JSON contract)
| Folder | Check |
|---|---|
| `CVE-2021-34473-proxyshell` | Exchange autodiscover SSRF → PowerShell RCE probe |
| `CVE-2022-41040-proxynotshell` | SSRF + RCE pair probe |
| `CVE-2022-22965-spring4shell` | blind data-binding probe + 9-request PoC set generator |
| `CVE-2021-35464-forgerock` | Groovy gadget chain (pure-Python Java serialization, JVM-verified) |
| `CVE-2023-27350-papercut` | PaperCut unauth RCE probe |
| `CVE-2023-0669-goanywhere` | GoAnywhere pre-auth RCE probe |
| `CVE-2023-35078-ivanti-epmm` | EPMM unauth API probe |
| `CVE-2024-47575-fortimanager` | FortiJump FGFM probe |
| `CVE-2024-1709-screenconnect` | auth-bypass + extension upload probe |
| `CVE-2025-31324-sap-netweaver` | Visual Studio Composer JSP upload probe |
| `CVE-2025-5777-citrix-bleed2` | session-token leak probe |
| `CVE-2025-0282-ivanti-connect-secure` | stack-overflow surface probe |
| `CVE-2024-6387-regresssion` | OpenSSH signal-handler race probe |

Perimeter probes report `error` + exit 1 on unreachable targets
(tested against RFC 5737 TEST-NET-1); Spring4Shell's blind probe
reports `vulnerable_surface: true` (not `vulnerable: true`) because a
param-ignoring page is indistinguishable from an accepting one —
confirmation is the generated PoC request set.

### Malware tooling
- `MALWARE-apk-wrapper-necro-class` — Necro-class APK dropper: wraps a
  Google-Play-sourced APK with a payload DEX chained via reflection to
  the original app class (marker file + optional TCP beacon), pure-Python
  AXML surgery + DEX injection, v1 (JAR) + v2 (APK Signature Scheme)
  signing in stdlib + pycryptodome/cryptography. **Verified against
  `apksigner verify` (build-tools 34.0.0) exit 0** on the repo's own
  25.9MB 12-DEX debug APK; v1 layer verified by `jarsigner -verify`;
  PKCS7 signature confirmed via openssl.

### Registry + tests (second sweep)
- `ZERO_DAY_REGISTRY` grew from 36 to **64 entries**: 14 ZERO-CLICK
  folder weapons, 13 PERIMETER folder weapons, and the APK wrapper —
  all folder entries resolve to a real `deploy.py`, and
  `registry.fire()` honors the JSON/exit contract for both generation
  and perimeter entries.
- Android `Weapons.REGISTRY` grew to **100+ entries** (ZERO-CLICK +
  PERIMETER tiers with per-chain detail text).
- New tests: zero-click generation battery (14 folders), perimeter
  closed-port battery (13 folders), folder-registry resolve/fire
  contract, APK wrapper full-wrap (skips when the reference APK is not
  built), catalog tests (16), C2 port tests (18), C2 real-module
  tests (23).

### Catalog modules (new, `src/quantum/catalog/`)
- `exploitdb.py` — full Exploit-DB (47,160 exploits at seed) as a
  gzipped CSV seed in the package + runtime sync to
  `~/.qcli/catalog/`; keyword/CVE/platform search, get-by-id, stats.
- `payloads_all.py` — PayloadsAllTheThings index (70 sections, 353
  documents, generated from the live master tree) + repo ZIP sync +
  payload-text retrieval straight from the ZIP.
- `badusb.py` — 20 operator-authored DuckyScript payloads (Hak5 Rubber
  Ducky / O.M.G / Flipper BadUSB equivalents: reverse shells,
  persistence, WiFi/SSH/LSASS exfil, clipboard hijack, pranks) with
  list/search/get/export.
- Android parity: `ExploitDb.kt` (bundled seed + hourly
  `CatalogSync`), Exploits-page catalog search, `QcliApi` commands
  `exploitdb` / `exploitdb_stats` / `catalog_sync`.

### Quantum C2 Tier-1 ports (new)
- `weapons/quantum_android.py` — full CVE-2026-0073 Android
  exploitation framework (initial access, privesc, lateral, exfil,
  persistence, evasion, DGA).
- `recon/kev.py` — CISA KEV feed (cisagov/kev-data mirror; the old
  cisa.gov paths now 404) + zero-click/pre-auth indicator analysis,
  24h cache, sample fallback.
- `recon/gitdork.py` — stdlib GitHub dork search (61 classic dorks,
  GH_TOKEN auth, rate-limit aware).
- `weapons/techniques/lockknife.py` — LockKnife port: adb device
  management + forensic extractions (packages/settings/app data/
  screenshot).
- `sim/` — 12 red/blue/purple team + network simulation classes.
- `ops/` — real evasion (timestomp/masquerade/purge), exfil (DNS TXT
  tunnel with raw-socket DNS, HTTPS POST, packaging), persistence
  (run key/scheduled task/startup/cron/rc), external tool catalog.
- 34 operator skill playbooks imported as `c2.*` PROMPT skills; 8
  seeded into the Android SkillStore.

## 6. Honesty boundaries (what "live" means here)

- Every folder's deploy tool **executes, self-verifies, and reports**
  honest JSON: `vulnerable` is only `true` when a target-side signal
  was actually observed; generation-only tools state that RCE
  confirmation requires the vendor's vulnerable parser / live delivery.
- Proximity/radio zero-clicks (BlueFrag, BT HID, KRACK) generate
  structurally-correct frames; radio delivery is documented as
  lab-side.
- The ADB TLS-bypass framework is the one exploit verified
  end-to-end against a live (mock adbd) target.
