# QUANTUM-CLI — Master Task Checklist (v4.5)

**Executed by:** `/tasks` — runs this file end-to-end in autonomous mode (`/never-ask` + `/swarm` + `/goal`).
**Scope banner:** Authorized engagements only (AGENTS.md rule 7). Every module ships real, functional code — no simulated capabilities (rule 6).
**Consolidation note (2026-10-02):** this is now the SINGLE task list for the repo. It merges the slash-command program, the APK build-out, the Stryker OSS + NRSuite integrations, and every open task from the legacy `TASKS/` documents (OFFENSIVE_DEVELOPMENT_CHECKLIST.md, TODO_LIST.md, TASK_CHECKLIST.md, SPRINT34.md, SPRINT_SUMMARY.md, chat.md, "Quantum cli prompt.md" — now deleted). Implementation detail extracted from them lives in `TASKS/IMPLEMENTATION_REFERENCE.md`.

**Standing gates that apply to every phase:**
1. Never weaken a check to make a test pass — fix production code, not tests (rule 1).
2. `quantum_cli.py` (archived at `dist/quantum-cli-v3.1-single.py`) is THE SPEC; package divergence is a bug (rule 2).
3. `--no-ai` deterministic path never gains network/Ollama calls (rule 3).
4. `logs/.lootkey` is immutable — never delete, rotate, or regenerate it (rule 4).
5. Camera-first ordering in `AutonomousOverlord.run()` stays exactly as-is (rule 5).

**Legend:** `[ ]` open · `[x]` done · **P0** blocking / **P1** high / **P2** later · **(verify)** = confirm against live code first — several legacy asks may already be shipped in v4.0–v4.5 · **DoD** = definition of done.

## Execution priority order (most critical → least)

1. **Tier 1 — Critical path:** Phase 0 preconditions (incl. secret rotation) → Phase 6 authentication & access → Phase 6 bug fixes → branding & chrome (app icon, sidebar logo + divider, classification banners) → Phase 5 pipeline skeleton (its gates run continuously from here on)
2. **Tier 2 — Core product:** Phase 2 P0 dashboards → Phase 4 NRSuite P0 capabilities → Phase 3 Stryker OSS → Phase 7 providers P0 → Phase 15 admin/paywall P0 → remaining Phase 1 commands (`/docs`, `/github.io`, `/auto`)
3. **Tier 3 — Feature depth:** remaining P1 items across Phases 6–11 (widget engine, providers, catalog/exploitation, control/C2/loot, network offense) → Phase 13 docs/CI P1 → Phase 12 hardware start
4. **Tier 4 — Later:** all remaining P2 items (expansion programs, reporting studio, Kodachi anonymity suite, hardware expansion, agent-tier follow-ups) → Phase 5 publish → Definition-of-Done sweep

---

## Phase 0 — Preconditions (run once, before any other task)

- [ ] **P0** **Secret rotation**: Agnes (×3 keys) and Abliterated.ai API keys were pasted in plaintext inside the legacy TASKS documents (now deleted from the working tree). Treat them as compromised: rotate at each provider, store replacements in `.env` only, never in docs or code. (Keys are redacted everywhere in this checklist and in `TASKS/IMPLEMENTATION_REFERENCE.md`.)
- [ ] **P0** **Reconcile shipped state**: sweep legacy asks against the v4.0.0→v4.5 release line (many may already be implemented); flip `(verify)` items to done or open as you go.
- [ ] **P0** Record baseline: current commit SHA, `pytest tests/` result, Android unit-test result (28/28 baseline), working-tree inventory (many untracked `agents/`, `ops/` files — confirm which are intentional before `git add`).
- [ ] **P0** Verify the repo has a remote and it points at `https://github.com/projectzerodays/quantum-cli`. If not initialized/connected, STOP — repo bootstrap is a user decision handled in Phase 5 step 8.
- [ ] **P0** Read `C:\Projects\Stryker OSS` docs in full before any porting work (prerequisite for Phase 3).
- [ ] **P0** Read the NRSuite-Android release notes and docs for tag `1.0.0-beta.2` (https://github.com/7wp81x/NRSuite-Android) before any integration work (prerequisite for Phase 4).

---

## Phase 1 — Slash-command suite

Create one command definition per entry (repo-level command files). `/swarm` must reuse the existing SWARM skill (`~/.zcode/skills/swarm`) rather than rebuild it.

| # | Command | Spec | DoD (acceptance criteria) |
|---|---------|------|---------------------------|
| 1.1 | **P1** `/quantumapk` | Open the Quantum CLI repo in the default browser: `https://github.com/projectzerodays/quantum-cli` | URL correct; opens on invocation |
| 1.2 | **P1** `/quantum` | Open the Quantum C2 repo: `https://github.com/projectzerodays/quantum` | URL correct; opens on invocation |
| 1.3 | **P1** `/swarm` | Spawn a SWARM of persistent AI subagents working simultaneously in parallel on a task set — efficient, effective, thorough, highest quality | Parallel spawn; work partitioned; results merged on disk; failures retried/escalated; wired to existing SWARM skill |
| 1.4 | **P1** `/auto` | Auto-choose the AI model; rotate on rate-limit; **verify connectivity before every switch** | Rotation on 429/quota; pre-switch check passes; failed switch falls back; events logged |
| 1.5 | **P1** `/docs` | Generate the full documentation suite (deliverables in §1.5) | All deliverables exist, grounded in real code, badges resolve, banner committed |
| 1.6 | **P1** `/github.io` | Generate and push a GitHub Pages website | Landing page mirrors README; deployed via Actions/`gh-pages`; live URL verified; linked from README |
| 1.7 | **P0** `/tasks` | Execute this checklist autonomously — pipeline in **Phase 5** | Phase 5 completes end-to-end; final report produced |
| 1.8 | **P2** `/anonymous` | Privatize platform + network queries via DNS-over-HTTPS (configure OS support if unavailable); encrypt the current session | DoH active and verified (no plaintext DNS); session encrypted |
| 1.9 | **P2** `/kill-switch` | Cut all network to/from device → copy logs to Desktop → dump platform conversations to a Desktop folder with system logs → clear platform logs/conversations (**never the backups**, never `logs/.lootkey`) → if a local LLM is reachable (LM Studio / llama.cpp / similar), analyze the dumped logs and produce a full report | Network verified severed; dumps verified (count/size); wipe verified with backups intact; local-LLM report written if model available |
| 1.10 | **P2** `/systemhealth` | Deep posture scan (device, network, permissions, vulnerabilities, firewall, outgoing connections, anomalous processes; sweeps for viruses/malware/adware/malicious cookies/trojans/RATs) → ranked report → **ask the user** before remediating → fix thoroughly + re-scan to verify | Report with severity ratings and evidence; no remediation without approval; post-fix re-scan confirms |

### 1.5 `/docs` deliverables

- [ ] **P1** `README.md` — badges (CI, tests, license, version, platforms), intro, feature overview, per-OS installation, usage, screenshots, AI-generated banner (best available model) at top, authorization notice, links
- [ ] **P1** Wiki — enterprise grade: architecture, per-module reference, operator guides, RoE/compliance, FAQ
- [ ] **P1** `LICENSE` — confirm/choose and apply consistently
- [ ] **P1** `CONTRIBUTING.md` — dev setup, branch/PR conventions, house style (`pytest tests/`, AGENTS.md rules, new weapons join `ZERO_DAY_REGISTRY` per `docs/HOWTOs.md` §7), review checklist
- [ ] **P1** API docs — C2 routes (`src/quantum/c2/routes.py`), dashboard API, CLI surface; versioned with code
- [ ] **P1** `TROUBLESHOOTING.md` — install failures, Android build gotchas (stale Gradle → phantom failures; asset subdirectory layout; FlowRow in scrollable pages), common runtime errors
- [ ] **P1** `DEVELOPER_CHECKLIST.md` — pre-PR gates: tests green, no-AI purity, lootkey untouched, camera-first intact, no simulated code
- [ ] **P1** `FUTURE_UPDATES.md` — roadmap (11 empty + 3 partial `exploit_payloads/` CVE dirs as expansion targets)
- [ ] **P2** `CHANGELOG.md` — keep-a-changelog format, backfilled from release history

---

## Phase 2 — Android APK dashboards

Material3 dashboards, each wired to its real backend ops module (no simulated code), registered in content registry/navigation, covered by updated unit tests. Widgets follow house style (FlowRow, not LazyVerticalGrid, inside scrollable pages).

**Ops dashboards:**
- [ ] **P0** OSINT dashboard (backend `ops/Osint.kt`) — plus username-enumeration aggregator (~40 sites), breach-check consolidation, IP download tracking, IMEI tracking, phone-number→location, tracking-link tool → map pin
- [ ] **P0** Recon dashboard — passive (whois/DNS/crt.sh) + active presets
- [ ] **P0** C2 dashboard (backend `c2/`)
- [ ] **P0** Botnet dashboard (backend `ops/Botnet.kt`) — server + client (verify parity)
- [ ] **P0** RAT control dashboard (verify parity of existing suite)
- [ ] **P0** Social engineering dashboard — voice clone (audio→speech), face clone (video→deepfake), craft+send flows (authorized corpora only)
- [ ] **P0** Phishing dashboard — templates, embedded credential listener, tunnel layer, QR campaign type
- [x] **P0** Brute-force / cracking dashboard — hydra/hashcat/john front-ends, zip/rar/pdf, hashes, vault containers *(2026-10-08: Python backend + QUANTUMDASH webcard shipped — `brute/hashes.py`, `services.py`, `vaults.py`, 44 `/api/crack/*` routes, 21 tests; Android-native page still open)*
- [ ] **P0** DDoS / death / jamming dashboard (backend `ops/Ddos.kt`) — layer-honest taxonomy
- [ ] **P0** Sabotage / disruption dashboard — in-scope authorized targets only, authorization gate in UI; extended DDoS tool set wired to `ops/Ddos.kt` (layer-honest vectors, rate/amplification controls)
- [x] **P1** Dark web browser dashboard (verify — v4.5 shipped darkweb module) — home page with preset onion search engines; leak-site/marketplace monitoring bookmarks (threat-intel watchlists, breach-monitoring sources; see Appendix B for excluded dump/purchase facilitation)
- [x] **P1** Ransomware dashboard (verify — v4.5 shipped module)
- [x] **P1** Google Dorks page + queries capture (verify — dorks module shipped)

**Platform dashboards:**
- [x] **P0** Agents dashboard — CRUD + SDLC preset suite + red-team presets *(2026-10-08: `ai/console.py` + `/api/console/agents*` routes + webcard; 12 agents incl. SDLC + NS org presets; Android-native page still open)*
- [ ] **P0** Tasks dashboard — DAG workflow editor + run engine + run history
- [x] **P0** Skills dashboard — PROMPT/TOOL/SCRIPT kinds + skill packs *(2026-10-08: kinds verified in registry, 49 skills, `/api/console/skills*` + webcard; Android-native page still open)*
- [ ] **P1** Integrations dashboard — API keys/accounts: Twilio, SendGrid, GitHub, Shodan
- [ ] **P1** Diagnostics dashboard — feature health matrix, provider chain viz, heal history, update history
- [ ] **P1** Subscriptions dashboard — current tier, monthly amount, due date, wallet-address management, options for future tiers
- [ ] **P2** Engagement Reporting Studio — audit-trail→report, evidence chains, AI exec summary, branded PDF

**DoD per dashboard:** registered + nav; house-style widgets; every control wired to a real ops call; Android tests updated and green; walkthrough updated.

---

## Phase 3 — Stryker OSS capability integration

- [ ] **P0** Read `C:\Projects\Stryker OSS` docs **thoroughly** (Phase 0 gate) — no porting before this.
- [ ] **P0** Capability inventory → map each to an existing Quantum module or a new one; record mapping here.
- [ ] **P0** Port capability-by-capability with parity tests.
- [ ] **P1** Do not clobber parallel work in `exploit_payloads/` (other agents build it concurrently).

---

## Phase 4 — NRSuite-Android integration (hardware ops suite)

Integrate the full feature set of https://github.com/7wp81x/NRSuite-Android (tag `1.0.0-beta.2`) with GUI components per capability.

| # | Capability | Behavior spec | GUI component | Chip support | Prio |
|---|-----------|---------------|---------------|--------------|------|
| 4.1 | WiFi scan | Active scan → SSID, BSSID, channel, RSSI, security type | Scan list + detail cards | all | P0 |
| 4.2 | Packet sniffing | Fixed-channel or hopping promiscuous capture; `.pcap` output; live stream via FIFO | Capture console + pcap export | all | P0 |
| 4.3 | EAPOL capture | Passive handshake capture; optional BSSID/client filtering | Handshake list + filters | all | P0 |
| 4.4 | Deauthentication | Standalone deauth, or combined with sniffing to trigger-and-capture a handshake | Deauth panel + combo toggle | all | P0 |
| 4.5 | Captive portal / AP mode | Start/stop/status; custom SSID + channel; custom HTML upload; optional auto-EAPOL against target BSSID | Portal wizard | all | P0 |
| 4.6 | BLE HID (BadBLE) | Advertise as BLE keyboard; run DuckyScript payload against paired host | DuckyScript runner + pairing UI | C3, S3, classic | P0 |
| 4.7 | BLE HID (realtime keyboard) | Live keystroke passthrough from terminal to paired BLE host | Live keyboard view | C3, S3, classic | P1 |
| 4.8 | USB Mass Storage | Expose onboard flash as real USB drive; list/read/write/delete over bridge without MSC mode | Bridge file browser | S2, S3 | P0 |
| 4.9 | BadUSB | DuckyScript over native USB HID, optional simultaneous mass-storage exposure | Payload runner + MSC toggle | S2, S3 | P0 |
| 4.10 | Heartbeat | Uptime + free heap every 5 s | Live status card | all | P0 |
| 4.11 | Beacon broadcasting | Beacon spam, custom/hidden SSIDs (≤32), fixed channel, stable or random BSSIDs | Beacon builder | all | P1 |
| 4.12 | Multi-device select | Several nrsuite devices; `-d`/`--device` selection | Device picker (CLI + APK) | all | P1 |
| 4.13 | BLE scan/advertise/discovery/spam | BLE scanning, advertising, device discovery, BLE spam | BLE ops panel | C3, S3, classic | P1 |
| 4.14 | Hardware expansion | IR, NRF24, CC1101 modules | Expansion slots | external wiring | P2 |

**DoD:** GUI auto-detects board model; unsupported capabilities render **disabled with reason shown**; behavior matches NRSuite spec; test per capability. Chip matrix in **Appendix A**.

---

## Phase 5 — Autonomous completion pipeline (the `/tasks` contract)

Run `/never-ask` + `/swarm` + `/goal` over this checklist. The **only** step permitted to prompt the user is 8a; everything else runs unattended and halts only on irreparable failure.

1. [ ] **P0** **Plan** — parse open items into work packages; spawn swarm with per-phase assignments; merge results on disk.
2. [ ] **P0** **Error sweep** — import-compile everything, run full suites, triage every failure; fix production code (rule 1).
3. [ ] **P0** **Vulnerability scan of the codebase itself** — static analysis (bandit/semgrep/ruff), dependency audit, secret scan (`.env` keys never committed); correct every finding.
4. [ ] **P0** **Refactor pass** — dead code, duplication, house style; behavior-identical, spec parity verified against `quantum_cli.py` (rule 2).
5. [ ] **P0** **Test & debug** — as thorough as possible: `pytest tests/` green; Android unit tests green; faceoffs script passes; WSGI smoke (curl 200).
6. [ ] **P0** **PASS gate** — "all systems PASS inspection": tests + lint + imports + no-AI purity + build success all green. Irreducible failure halts with full report.
7. [ ] **P0** **Docs & site** — run `/docs` then `/github.io` (§1.5–1.6) against final state.
8. [ ] **P0** **Publish** — 8a. If repo not initialized/connected: **ask the user** — (a) create new repo (name it), or (b) accept existing repo URL + GitHub PAT. No other user interaction. 8b. Push everything to `main`. 8c. If no release exists: create one with artifacts for **every available architecture and OS** (Android APK per ABI, single-file script build, wheel/sdist).
9. [ ] **P0** **Final report** — shipped changes, test matrix, vulnerability findings + fixes, release URL, checklist completion state.

---

## Phase 6 — APK platform, shell & UX

**Bug fixes (legacy Phase 0):**
- [ ] **P0** Fix save-settings and apply/restart buttons (no-op)
- [ ] **P0** Fix Scan Net button — real ARP/nmap sweep feeding Services/OpenPorts + ADB-5555 flagging (verify)
- [ ] **P0** Fix Cam Sweep button — ONVIF/RTSP discovery → Targets (verify)
- [ ] **P0** Fix local model download error → ModelDownloadManager (OkHttp resumable, sha256, per-error diagnostics) (verify)

**Shell & widgets:**
- [ ] **P1** Sidebar: hidden-scrollbar swipeable, groups collapse, live-count badges, GitHub link icon
- [ ] **P1** Terminal: VT shell, SSH/SFTP/Telnet/DNS/`adb://` profiles — accessible from dashboard and chat
- [ ] **P1** Chat icons: copy, download (SAF, any extension/media MIME), paperclip (files), photo (vision providers); settings icon (local model ↔ external providers); terminal icon
- [ ] **P1** Floating chat bubble (shared ChatViewModel) + "Ask AI" context priming
- [ ] **P1** Home status widgets: root, VPN+IP, MAC, proxy+IP, DNSCrypt+resolvers, DoH RDNS, net-speed sparkline, CPU, local-model status, provider grid
- [ ] **P1** Drag-drop widgets + per-page lock icon; telemetry/charts on every dashboard
- [ ] **P1** App lock (face/fingerprint/PIN/password) + auth-methods manager (documented methods only — see Appendix B)
- [ ] **P1** Sidebar and all dashboard pages scrollable
- [ ] **P1** Startup credential prompts — tools/APIs requiring logins (e.g., EFT Pro, Shodan, Twilio) request credentials at first startup; if not provided, the dependent modules/widgets are disabled and greyed out
- [ ] **P1** Network identity panel — IPv4/IPv6 address + geolocation for the device and for the active VPN/proxy; user-configurable proxy chain, VPN info, SOCKS5 proxy, custom root CA
- [ ] **P1** Optional app + data encryption using an app-generated root CA (or user-supplied CA) and an advanced cipher suite — integrates with the 3-DB SQLCipher split
- [ ] **P2** Kodachi-9-grade anonymity suite — DoH/DoT, optional Tor routing, firewall-hardening profiles, MAC randomization (root), leak prevention (DNS/WebRTC/IPv6), connection kill-switch — while maintaining persistent C2 keepalive connections
- [ ] **P0** Auto-update + intelligent dependency updates: GitHub Releases poll, signature-verified, blacklist-aware block policies; **update-deps button** — automated dependency bumps validated by build+test gate (never ship breaking updates), pre-update snapshot, **automatic rollback** when issues occur, then push to GitHub → hotfix release → push notification → user installs in-app
- [ ] **P2** Three-DB SQLCipher split (`quantum_app`/`quantum_intel`/`quantum_secrets`) + StrongBox/HKDF + AES-256-GCM blob envelopes + per-row HMAC + zeroize + encrypted export + weekly snapshots (verify — spec in reference doc §4)
- [ ] **P2** Widget-engine completeness: DashboardScaffold, WidgetShell, RecoveryBoundary, JobCard, TooltipRegistry, WalkthroughEngine, HealingDaemon, ToolBridge (verify — v3.8/v3.9 trunk may already cover; spec in reference doc §5)
- [ ] **P2** Publish `docs/requirements-matrix.md` (85 consolidated requirements → file map)

**Authentication & access (P0 security foundation):**
- [ ] **P0** Mandatory 9–11 digit PIN at first use — set during onboarding, hashed (Argon2id or PBKDF2-HMAC-SHA256, high iterations) into `quantum_secrets`; unlock gate on every launch
- [ ] **P0** Optional multi-factor modes, user-configurable when logged in (Security → Authentication): face+PIN · finger+PIN · face/finger+12–25-digit password · 12–25-digit password alone · FIDO2 NFC/USB alone · face/finger+FIDO2 NFC/USB (BiometricPrompt Class 3 + Credential Manager / FIDO2 roaming authenticators)
- [ ] **P0** "I forgot my auth info" on the initial access page — confirms via face/finger + device PIN, then wipes ALL app data (3 DBs, DataStore/prefs, keystore alias) and relaunches into first-run onboarding (face/finger auth + device PIN). App data only — never other device data
- [ ] **P0** Brute-force defense — exponential backoff on repeated failures; no recovery path outside the forgot-auth wipe flow

**Branding & chrome (P0):**
- [x] **P0** App icon — Quantum mark wired through adaptive + legacy launcher icons (done 2026-10-02: source at `android/art/quantum_logo.png`; mipmap PNGs square+round, adaptive foreground + monochrome layers generated by `scripts/gen_icons.py`; `mipmap-anydpi-v26/ic_launcher.xml` rewired)
- [ ] **P0** Sidebar logo — rendered 1 in × 1 in (160dp), equal padding on all sides, divider below separating it from the nav links; asset slot `assets/brand/sidebar_logo_cia.png` (CIA seal fetched 2026-10-02 from the operator-supplied link, transparent, square-padded; Quantum-mark fallback at `assets/brand/sidebar_logo.png`) — legal caveat: official US-agency insignia implies government affiliation; keep the app internal/private or substitute an original seal-style mark
- [ ] **P0** Classification banners — thin horizontal bar pinned at the very top AND bottom of the app, centered text `CLASSIFIED // TS // SI-G // TK // HCS // SAP-ALPHA // NOFORN` (single `ClassificationBar` composable in the main Scaffold; decorative marking for the operator's own app — do not present the app as an actual government system in public/commercial materials)
- [ ] **P0** GUI quality bar — state-of-the-art throughout: every widget drag-and-drop enabled with a settings icon in its title bar; 100% responsive across all screen sizes (WindowSizeClass compact/medium/expanded); every tool integration fully masked (GUI controls + telemetry/charts/visual output only — no raw tool chrome in user space). Full spec: `TASKS/IMPLEMENTATION_REFERENCE.md` §13

---

## Phase 7 — AI providers & agents

- [ ] **P0** `ChatProvider` interface + capability gating (TEXT/VISION/IMAGE_GEN/VIDEO_GEN/TOOLS) + health()/failover chain + incident cards
- [ ] **P0** Adapters: OpenRouter, Venice.ai, Agnes, OpenCode/OpenFable, Abliterated, local GGUF (llama.cpp server, app as client)
- [ ] **P1** Registry100: providers-as-data rows (3 wire protocols as code: OpenAI/Anthropic/Gemini-compatible), real endpoints/model IDs, hot-fixable catalog push — spec in reference doc §6
- [ ] **P1** Custom provider wizard: auto-probe protocol + self-test round-trip + admin notification + GitHub bot automation (branch → commit provider JSON → PR → squash-merge → branch janitor) targeting `ProjectZeroDays/Quantum-CLI`
- [ ] **P1** KeyRotator: quota-aware round-robin/failover under every OpenAI-compatible provider (rotakey pattern)
- [ ] **P2** OmniRoute adapter + registry ingestion
- [ ] **P2** kimi-k3-in-c: arm64 Termux build script (`scripts/build_kimi_arm64.sh`), RAM tiering (GREY ≤8 GB, GREEN ≥12 GB)
- [ ] **P2** Local model tiering: RAM-adaptive model selection, llama.cpp params (`use_mlock`, `n_batch=512`, thread pinning), per-target wordlist tuner (n-gram) feeding CrackEngine
- [ ] **P1** Autonomy Matrix config page — per-capability MANUAL/SUGGEST/AUTO_APPROVAL/AUTO_NOTIFY/SILENT_AUTO policy grid
- [ ] **P2** Night researcher loop — autonomous 0-day PoC generation, default-on, quiet sync

---

## Phase 8 — Recon, OSINT & exploitation

**Catalog & pipeline:**
- [ ] **P0** exploit-db + PayloadsAllTheThings catalog sync (pinned tags, mirrors, quarantine, stale badges)
- [ ] **P0** Exploit dropdown on exploit dashboard (catalog-fed, filter/search, CVE preview)
- [ ] **P1** Target-profile exploit matching: nmap → NVD cpe2cve → searchsploit
- [ ] **P1** AI PoC generation from catalog context → OpenCode hand-off → payload factory (test-before-release gate)
- [ ] **P1** Project Zero RSS zero-day loop → generated-exploit cards
- [ ] **P1** Named modules: BlueBorne DB entries, BlackBED, router exploit suite (default-creds + CVE sigs + hydra), OTP-bypass suite
- [ ] **P1** Cookie management dashboard — view/edit harvested cookie data from authorized target devices, session replay/hijack for OTP-bypass validation, cookie crafting/modification (authorized engagements only)
- [ ] **P1** Device PIN-cracking tools via ADB and fastboot (authorized lab devices); EFT Pro Online integration (FRP bypass and associated tools) — service login requested at startup, feature greyed out if absent
- [ ] **P1** Technique templates: buffer overflow / heap spray / ROP / format-string, LoTL scripts
- [x] **P1** Injection/stego: PDF embed, image stego, AV spectrogram stego, messenger auto-parse share chain *(2026-10-08: `exploits/steganography.py` covers all four + `/api/stego/*` + webcard; Android-native page still open)*
- [ ] **P1** Zenmap-level scan controls (NSE picker, T0–T5 timing, profile save/load)
- [ ] **P2** OSINT completion: reverse image/video search (Lens/Bing/TinEye/Yandex), EXIF editor (write-back), `api.hunt` reverse engineering (PCAP→endpoints→stubs→fuzz)

**Advanced programs (P2):**
- [ ] FuzzLab dashboard (targets/engines/campaigns/findings; boofuzz/radamsa/AFL++ presets)
- [ ] IDS engine (Suricata `eve.json` rules, alert wall)
- [ ] **P1** AI malware-analysis sandbox (virtualized-by-default, network-restricted, static→behavioral→AI verdict) with a sandbox dashboard to view, interact with, and detonate samples
- [ ] Formal-verification ladder for generated exploits (compile → differential-mock → sandboxed behavior observation)
- [ ] Adversarial-aware watcher — run own IDS against own emissions pre-deploy
- [ ] Legacy zero-day/zero-click catalog (publicly-cited 5-year set) as signed bundle with reliability filter
- [ ] Contactless zero-click facet `zc.*` (NFC/BT/RFID/QR) with interaction-level/citation labels
- [ ] Expansion counts from legacy docs (50 improvements / 50 CVE variants / 100 updates) — **verify** what shipped; continue in `ZERO_DAY_REGISTRY` + fill the 11 empty + 3 partial `exploit_payloads/` CVE dirs
- [ ] AVALON v16 merge with the 4 corrections (relabel media fuzzers CHECK-ONLY, drop false PQ claim on AES-GCM/HKDF, vendor CVE-2022-0847 PoC instead of hand-rolled DirtyPipe shellcode, remove checklist inflation)

---

## Phase 9 — Control, C2, post-exploit & credentials

- [ ] **P0** World map widget (full-width pins) + target drawer (identifiers/services/vulns/elapsed) + target-chip deep links
- [ ] **P0** C2 listener manager: Sliver (primary) + MSF multi-handler + Merlin (verify)
- [ ] **P0** ADB Hunter: discovery + dadb connect + pairing-QR + 6-digit brute + **PhantomDroid front-end** for ADB wireless/USB control of all features
- [ ] **P1** QR Control Gateway Modes W/P/V + campaign wizard + analytics
- [ ] **P1** RAT control suite parity (verify); RemoteViewer chips (VNC/RDP/TeamViewer/AnyDesk)
- [ ] **P1** RAT/C2 dialer OTP-capture module — enable/disable conditional SMS + call forwarding to an operator-entered number via the target's dialer (in-scope authorized targets only), one-tap on/off toggles, plus the most covert available variant (telephony/CarrierConfig API path instead of visible dialer codes)
- [ ] **P1** Exfil engine + loot tables/charts; export formats CSV/JSON/KeePass/cookies.txt/PDF + encrypted destinations; loot page adds view/edit/delete/wipe for all media and file types; loot data shared cross-dashboard (hashes → cracking, usernames/emails/passwords/passkeys → brute-force, cookies → session tools)
- [ ] **P1** Credentials & Vault dashboard; harvest adapters (Chrome/Firefox/Samsung browser decrypt)
- [ ] **P1** Memory analysis dashboard (root dump → secrets extraction)
- [ ] **P2** Local target DB shared across the exploitation lifecycle (verify)
- [ ] **P2** Forensic extraction tiers (logical/filesystem/physical) + host self-exploitation root chain (own device)
- [ ] **P1** Crypto key/seed discovery + collector (wallet addresses, private keys, recovery phrases found on authorized systems) as a post-exploitation module, with loot visualization charts
- [ ] **P2** GPS spoofing (host-side mock locations; target-side only against in-scope lab devices)
- [ ] **P2** Background PCAP auto-analysis agent (scheduled capture → decode → promote hits)

---

## Phase 10 — Social engineering, phishing & messaging

- [ ] **P1** Messaging transports (ExfilTransport abstraction): SMS/MMS (native + Twilio), WhatsApp(+Biz), Telegram, Snapchat, iMessage, SendGrid email — per-transport flags, agent send-tools (in-scope, authorized recipients only)
- [ ] **P2** Spoofing suite: SPF/DKIM-aware email builder + homoglyph engine, SMS/UDH shaping, voicemail probing (authorized accounts only), clone-source collection (diarization) from authorized corpora
- [ ] **P1** AI social-engineering agent for scripted in-scope engagements

---

## Phase 11 — Network offense dashboards (Android-native)

- [ ] **P0** WiFite GUI (3 interface modes: native/OTG/remote-agent; AP grid; attack chooser; handshake manager → cracker)
- [ ] **P0** PCAP/tshark dashboard (display-filter grammar, dissection tree, hex pane, stream reassembly, EAPOL export; tshark live capture; VoIP SIP/RTP → .wav per-leg mixdown)
- [ ] **P1** SDR/IMSI dashboard (RTL-SDR OTG, HackRF TX, FFT/waterfall, cell discovery, IMSI sniffer — root)
- [ ] **P1** Bluetooth dashboard (classic + BLE scanners, BlueBorne probes, GATT fuzzer) (verify vs `ops/BleRecon.kt`)
- [ ] **P1** Contactless Lab (MIFARE Classic/Ultra/DESFire, NTAG, FeliCa, EMV, CAC/PIV slots, LF125 HID/EM4100; Proxmark3 front-end, Chameleon clone wizard, hardnested, masked-PAN panel)
- [ ] **P1** APN / Evil-Twin (hostapd/airbase-ng + tun MITM; session → IDS/PCAP pipe)
- [ ] **P2** Full-band WiFi deauth (2.4/5/6 GHz honesty table, PMF/802.11w probing) — authorized lab targets
- [ ] **P2** Rogue-AP MITM completion (campaign-scoped TLS re-sign proxy, surgical host/SNI rules, post-campaign CA audit) — authorized engagements only

---

## Phase 12 — Hardware & drivers

- [ ] **P2** Driver ports: `librtlsdr` arm64 .so (JNI over libusb), `libhackrf` arm64 .so, USB WiFi RTL8812AU / ath9k_htc monitor mode (rooted kernel drivers)
- [ ] **P2** Readers: Proxmark3/RDV4 (pm3 v3 JSON-over-USB), ACR122U/OMNIKEY (PC/SC-over-CCID), Chameleon Mini/RevG (serial over USB-OTG/BT)
- [ ] **P2** HID/implant hardware: OMG Cable/Elite (mass-storage + USB-serial + WiFi API), Hak5 family (PID/VID registry, mass-storage detection/write), Wi-Fi Pineapple (REST)
- [ ] **P2** OMG/Hak5 payloads dashboard: catalog sync, HwDeviceRegistry, visual DuckyScript-DS3 builder, stager gallery (SSH-tunnel / Sliver-MSF-TCP / HTTP-pull / DNS-exfil / msfvenom-inline-b64)
- [ ] **P2** Expansion devices: Cactus WHID, Facedancer, USB Ninja; multi-locale HID stagers; firmware flasher module (DFU profiles, sha256 checks); unknown-USB fingerprinter
- [ ] **P2** Driver & hardware catalog DB (vendor/model/driver/link/purchase rows) + `hw.tune` per-SoC tuning dashboard
- [ ] **P2** Vehicle DoIP/ISO-13400 **read-only diagnostics** added to CAN/UDS module (actuation excluded — Appendix B)

---

## Phase 13 — Docs, CI & governance

- [ ] **P1** Backlog import: `scripts/github-project.yaml` (epics E-A…E-O, phase-0…9 labels) + `scripts/sync-issues.sh` (idempotent)
- [ ] **P1** Declarative DB schema: `db/schema.yaml` single edit point + `scripts/gen_migrations.py` (CI fails on hand-edited migrations / non-no-op regen)
- [ ] **P1** Tooltip linter + content pilot: tooltip `_registry.json` as linter source of truth; "empty dashboard must teach" content rule per dashboard
- [ ] **P1** Repo audit harness: `scripts/audit_repo.sh`, `endpoint_census.py`, placeholder census — CI gates (zero placeholders, zero uncatalogued hosts)
- [ ] **P2** Auto-doc pipeline (feature registry → docs/tooltips/manual on release tags) + live docs sync (docs-delta per PR)
- [ ] **P2** Continuous live-validation grid (nightly chains) + load campaign (perf-budget gates) + fleet analytics v2 + resilience pass
- [ ] **P2** One-PR discipline enforcement: module + widget + settings + tooltip + docs-delta + tests per PR; ledger/docs bound to live code (CI-enforced)

---

## Phase 14 — Agent tier follow-ups (v3.10 state)

- [ ] **P2** Launch the first SLDR mission — ledger shows `missions 0 launched (OPLOG empty)`; MissionEngine is live but unexercised
- [ ] **P2** Ship NS-agency first-install opt-in flow (`agents.ns.enabled` ships OFF)
- [ ] **P2** Author the Zcode-ready config registering all 33 agents wired into the hierarchy (open offer from Sprint 34)
- [ ] **P2** Deep-dive one subagent prompt (e.g., NS-BREACH-IOS or NS-CRAFT-RANSOM) (open offer)

---

## Phase 15 — Admin console, subscriptions & monetization

**Security rule for everything in this phase: no credential literals in code.** The admin master code and special-user bypass codes are supplied by the operator out-of-band, configured at first-run/deployment, and stored **hashed** in the SecretStore — never committed to the repo or compiled into the APK (shipped bytecode is trivially reversible, and the admin master code value that appeared in legacy docs is already considered compromised — **rotate it**, do not reuse it).

- [ ] **P0** Admin account — created during the first-run setup wizard when the user selects PIN access; the admin PIN is chosen by the operator at setup, hashed, stored in SecretStore; admin surface gated to that account only
- [ ] **P0** Master access codes — admin master code (unlocks admin features + bypasses the paywall) and special-user bypass codes ("gifted" free access), configured at deployment and **admin-moderable** (create/revoke/modify) from the console; stored hashed, never literals
- [ ] **P1** Admin console — user roster, account activation/deletion, account + activity monitoring, audit log, license/feature grants, force-update, remote app-data wipe per account and universal kill switch (the app's own data only)
- [ ] **P1** Remote access control — block/disable users by IP/CIDR, MAC, DNS identity, device identifiers (Android ID / integrity attestation); recommended primary enforcement: device attestation + token revocation, network identifiers as secondary layers
- [ ] **P1** Paywall — $99/month USDC subscription gating app use; wallet address stored in settings (deployment-configured, not a code constant); on-chain payment verification with an offline-grace policy
- [ ] **P2** In-app crypto wallet (major coins) on the subscriptions page, with kycnot.me directory integration for payment-provider discovery
- [ ] **P1** Update push pipeline — admin-triggered update build → GitHub hotfix release → push notification → user installs in-app (wired to Phase 6 auto-update)

---

## Appendix A — Chip compatibility matrix (NRSuite, hard constraints)

| Capability | ESP32-C3 | ESP32-S2 | ESP32-S3 | classic ESP32 | Reason |
|------------|----------|----------|----------|---------------|--------|
| WiFi suite (4.1–4.5, 4.10–4.12) | ✓ | ✓ | ✓ | ✓ | — |
| BLE HID BadBLE + realtime keyboard (4.6–4.7) | ✓ | ✗ | ✓ | ✓ | Requires a Bluetooth radio; S2 has none |
| USB MSC + BadUSB (4.8–4.9) | ✗ | ✓ | ✓ | ✗ | Requires native USB-OTG; C3 and classic devkits lack it |
| BLE scan/advertising/spam (4.13) | ✓ | ✗ | ✓ | ✓ | Requires a Bluetooth radio |

---

## Appendix B — Explicitly out of scope (do not implement)

Carried forward from the legacy docs and deliberately **excluded** — they destroy or surveil uninvolved third parties, outside the authorized-engagement scope (AGENTS.md rule 7) and the repo's own RoE doctrine:

- ❌ **WhatsApp / `wa_crasher`-style image-delivered exploits that fill a target's storage until crash/bootloop** — destruction of uninvolved consumer devices (DoS/bricking). Media-bomb "fill engine" variants aimed at device destruction share this exclusion; the sabotage/disruption dashboard covers in-scope authorized targets only.
- ❌ **Third-party critical-infrastructure / life-safety actuation** — SCADA/ICS ladder-logic register writes ("grid-down" presets), vehicle CAN/UDS/DoIP actuation chips, hospital/HL7 device control, RF jamming and cellular-crypto downgrade against third-party spectrum, drone takeover incl. jamming near airports, baby-monitor/ATM/LPR plate-feed camera capture. (Read-only/assessment counterparts in authorized scopes remain in-scope — e.g., Phase 12 DoIP read-only diagnostics.)
- ❌ **Covert surveillance of the product's own users** — hidden beacons on end-user installs, silent telemetry/monitoring; Play-Store/App-Store wrapping or APK-fusion trojanization of store apps. (Overt, disclosed admin access-control over app accounts — Phase 15 — is not surveillance.)
- ❌ **Compiled-in credential literals (backdoor PINs, wallet addresses as code constants)** — access codes and payment addresses must be deployment-configured and stored hashed (SecretStore/`.env`), never constants in shipped code; the admin master code exposed in legacy docs is compromised and must be rotated. The subscription paywall itself **is** approved (Phase 15).
- ❌ **Crypto wallet drainer** — active theft of funds from victims' wallets has no authorized-engagement application. (Discovery of wallet addresses/keys/recovery phrases on authorized systems stays in-scope — Phase 9.)
- ❌ **Facilitating access to stolen-data markets** — the dark web browser ships monitoring/intel bookmarks only (onion search engines, leak-site watchlists, exploit advisories); no curated bookmarks or flows for credential/CC dumps or exploit purchase.

---

## Definition of Done — whole checklist

Every checkbox above is `[x]`, Phase 5's PASS gate is green, docs + wiki + GitHub Pages are live, a release exists with per-arch/per-OS artifacts attached, this file's statuses are accurate, and the supporting specs live in `TASKS/IMPLEMENTATION_REFERENCE.md`.
