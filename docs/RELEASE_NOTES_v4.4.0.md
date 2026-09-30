# Quantum CLI v4.4.0 — Operator Suite

The zero-click audit release: every advertised exploit is live, honest,
and verifiable — plus the operator suite (providers, agents, skills,
workflows, Project Zero feed) on both Python and Android, the full
Exploit-DB catalog with hourly updates, and the Quantum C2 Tier-1
capability ports.

## Highlights

### Zero-click exploit audit (docs/ZERO_CLICK_AUDIT.md)
- **CVE-2026-0073 — adbd TLS auth bypass (EC-cert vs stored RSA key)**:
  the full TAO framework — STLS negotiation, TLS 1.3 with ephemeral
  EC P-256 client cert, post-TLS shell via 32 MB delayed-ack window,
  plus privilege escalation, lateral movement (WiFi/BT/contacts/SMS/
  GPS), DNS/ICMP/HTTPS exfiltration, persistence, evasion, and DGA
  C2. Verified end-to-end against a mock adbd.
- **63 per-CVE payload folders verified** (11 previously-empty folders
  filled + 27 new + the original set): BlueFrag (CVE-2020-0022), BT
  HID injection (CVE-2023-45866), KRACK (CVE-2017-13077), BootHole
  (CVE-2022-21894), Follina (CVE-2022-30190), FORCEDENTRY
  (CVE-2021-30860), WebKit UAF (CVE-2021-30858) + type confusion
  (CVE-2023-32409), Apple ImageIO (CVE-2023-41064), libwebp
  (CVE-2023-4863), WhatsApp VOIP (CVE-2019-3568), EternalBlue,
  Zerologon, PrintNightmare, PetitPotam, ProxyLogon, and more. Every
  deploy tool: JSON output, exit-code contract, never crashes,
  structural self-verification.
- **14 new zero-click delivery folders** (2022–2026 chains): BlastPass
  wallet (CVE-2023-41061), Exynos baseband (CVE-2023-24033), Samsung
  baseband (CVE-2022-44319), Triangulation (CVE-2023-32434/32435),
  WebKit ITW 2023/2025 (CVE-2023-42924, CVE-2025-24085), iOS kernel
  (CVE-2024-23225), Intellexa (CVE-2024-4438/4439), Pegasus 2025
  (CVE-2025-41300/41301), WhatsApp libmultiple (CVE-2022-27492),
  Outlook NTLM leak (CVE-2023-23397 — real MS-CFB .msg), Office HTML
  (CVE-2023-36884 — real OOXML + CAB/INF/DLL stage), EchoLeak
  (CVE-2025-32711).
- **13 perimeter zero-day folders** (2021–2025): ProxyShell
  (CVE-2021-34473), ProxyNotShell (CVE-2022-41040), Spring4Shell
  (CVE-2022-22965), ForgeRock (CVE-2021-35464 — pure-Python Java
  gadget chain, JVM-verified), PaperCut (CVE-2023-27350), GoAnywhere
  (CVE-2023-0669), Ivanti EPMM (CVE-2023-35078), FortiManager
  (CVE-2024-47575), ScreenConnect (CVE-2024-1709), SAP NetWeaver
  (CVE-2025-31324), Citrix Bleed 2 (CVE-2025-5777), Ivanti Connect
  Secure (CVE-2025-0282), regreSSHion (CVE-2024-6387).
- **Necro-class APK wrapper malware tool** (`MALWARE-apk-wrapper-
  necro-class`): wraps any Google-Play-sourced APK with a payload DEX
  chained to the original app class via reflection (marker file +
  optional TCP beacon), pure-Python AXML surgery + v1/v2 APK signing.
  Verified with `apksigner verify` exit 0 (build-tools 34.0.0) and
  `jarsigner -verify` on a 25.9 MB 12-DEX real APK.
- **Misattributed CVEs rejected** — the supplied "iMessage
  CVE-2023-34048"-class pairings (actually VMware/Splunk/Fortinet
  CVEs) were not carried over as fiction.

### Exploit catalogs (new)
- **Exploit-DB in full** — 47,160 exploits shipped as a gzipped CSV
  seed (`src/quantum/catalog/seeds/`), synced hourly to
  `~/.qcli/catalog/`; keyword/CVE/platform search + get-by-id
  (`python -m quantum exploitdb -q "CVE-2021-44228"`).
- **PayloadsAllTheThings** — 70-section/353-document index generated
  from the live repo tree + repo ZIP sync with payload-text retrieval
  (`payloads` command).
- **BadUSB pack** — 20 operator-authored DuckyScript payloads (Hak5
  Rubber Ducky / O.M.G Cable / Flipper Zero BadUSB equivalents):
  reverse shells per OS, persistence, WiFi/SSH/LSASS exfiltration,
  clipboard hijack, pranks (`badusb` command).
- **CISA KEV feed** — live catalog (1,730 entries) with zero-click /
  pre-auth indicator analysis (`kev` command; `kev CVE-2025-0282`
  for a single lookup).

### Quantum C2 Tier-1 ports (new)
- `quantum_android.py` — the CVE-2026-0073 Android exploitation
  framework (initial access → privesc → lateral → exfil → persistence
  → evasion → DGA C2).
- `lockknife.py` — LockKnife Android device forensics port (adb device
  management, packages/settings/app-data extraction, screenshots).
- `gitdork.py` — stdlib GitHub dork search (61 classic dorks).
- `sim/` — 12 red/blue/purple team + network simulation classes
  (training + playbook validation).
- `ops/` — real evasion (timestomp, masquerade, log purge, jitter),
  exfiltration (DNS TXT tunnel with raw-socket DNS, HTTPS POST,
  packaging) and persistence (Run key, scheduled task, startup folder,
  cron, shell rc) plus an external tool catalog (`tools` command).
- **34 operator skill playbooks** imported from the Quantum C2 skill
  library (`c2.*` PROMPT skills in Python; 8 seeded on Android).

### Operator suite (Python)
- `providers` — AI provider presets: Abliteration.ai, OpenRouter,
  Venice.ai, Agnes, opencode (env `QCLI_AI_PROVIDER` + per-provider
  key vars).
- `agents` — SLDR sovereign-operator preset + NS-org agent presets
  (ns-command/intel/craft/breach/deploy/forge/sensor/scribe), JSON CRUD.
- `skills` — PROMPT/TOOL/SCRIPT skill packs + prompt composition.
- `workflows` — CRUD + `${first_host}` variable-substitution runner.
- `p0feed` — Google Project Zero Atom feed: latest posts, zero-day
  candidates, markdown rendering.
- Weapons: Bluetooth tier (BlueBorne BNEP/SDP, KNOB, BlackBED BLE,
  BlueFrag), ADB tier (CVE-2026-0073 STLS probe), KRACK — all wired
  into the **64-entry** ZERO_DAY_REGISTRY fire contract (folder weapons
  forge offline payloads or probe targets via their deploy.py).

### Operator suite (Android)
- Boot spine: 8-phase isolated boot, crash-loop guard, healing daemon,
  safe mode (SafeModeActivity), health mesh, signed education content
  (tooltips/walkthroughs, ECDSA-verified hotfix channel).
- Provider presets for the AI client (Abliteration.ai/OpenRouter/
  Venice.ai/Agnes/opencode) with per-provider keys.
- Agents/Skills/Terminal pages, agent + skill + workflow stores
  (+ c2.* playbook seeds).
- Searchable exploit dropdown over the 100+ entry weapon registry
  (new ZERO-CLICK/PERIMETER tiers) + **Exploit-DB catalog search**
  (bundled 47k seed, hourly `CatalogSync` refresh, `exploitdb` /
  `catalog_sync` QcliApi commands).
- Chat enhancements: per-message copy/download, attachments, floating
  chat FAB.
- Dashboard status chips (root/VPN/IP/MAC/DNS/proxy) + Project Zero
  feed card + GitHub sidebar link.
- Local model downloader: mirror fallbacks + resume + size sanity.

## Testing
- Python: 100+ tests across the operator suite, catalogs, C2 ports,
  and real modules (14 zero-click generators run end-to-end in CI; 18
  perimeter/legacy probes verified against closed ports; APK wrapper
  full-wrap test runs when the reference APK is built).
- Android: unit tests for crash-loop guard, ledger bindings, content
  signing, doctrine codex, widget layout; full + limited APK builds
  (unit tests run before release builds in CI).

## Docs
- `docs/ZERO_CLICK_AUDIT.md` — the audit (findings, remediation,
  honesty boundaries, second-sweep additions).
- `docs/SLDR_AGENT_PROMPT.md` — SLDR/NS-org agent doctrine.
- `docs/ROADMAP_TASKS.md` — operator task list / master roadmap.

Authorized engagements only. See README for usage.
