# TASKS — Implementation Reference

> **Created 2026-10-02** during consolidation. The legacy TASKS documents
> (`OFFENSIVE_DEVELOPMENT_CHECKLIST.md`, `TODO_LIST.md`, `TASK_CHECKLIST.md`, `SPRINT34.md`,
> `SPRINT_SUMMARY.md`, `chat.md`, `Quantum cli prompt.md`) were **deleted** after their tasks were
> merged into [`../TASKS_CHECKLIST.md`](../TASKS_CHECKLIST.md). This file preserves the
> implementation-relevant specifications, decisions, and reference material from those documents
> that support completing the checklist. Line references below point into the deleted originals
> only where the fact matters more than the location.

---

## 1. Source-file map (what was consolidated from where)

| Deleted file | Size | Nature | Notes |
|---|---|---|---|
| `Quantum cli prompt.md` | 39,814 lines | Master source document | ~2,040 headings; ~60% duplicated NS-agency agent prompts + Kotlin sprint program; TASK_CHECKLIST.md §1 contained the authoritative ~90-request-cluster extraction of it |
| `TASK_CHECKLIST.md` | 413 lines | Extraction + phased task tables | ~90 request clusters (§1) + Phase 0–9/Hardware/Settings tables (§2) — both now merged into the master checklist |
| `TODO_LIST.md` | 9,475 lines | Addendum list + master plan Sprints 0–32 | Heavily duplicated; **Sprints 16 (v2.1 fileless/RDoh), 23 (evasion craft), 25 are referenced by the ledger but their sections are absent from every source file** |
| `OFFENSIVE_DEVELOPMENT_CHECKLIST.md` | 3,036 lines | Stale concatenated checklist | Title+content duplicated wholesale from line 1519; 1,576 unchecked / 0 checked; prose under items often claimed completion while boxes stayed unchecked — treated as unresolved |
| `SPRINT_SUMMARY.md` | 3,214 lines | Chat export + per-sprint tail | Strict superset of SPRINT34.md (diff = 87-line "list all Sprint 1–34 features" tail); nothing lost by deleting both |
| `SPRINT34.md` | 3,127 lines | Chat export | v3.8 trunk files + Sprint 33/34 delivery; ~50% internally duplicated |
| `chat.md` | 2,964 lines | WhatsApp export | Same content as SPRINT34 (re-paste at 10:00:31 AM ≈ 50% dup); adds decision/constraint provenance; contains OCR corruption in Sprint 34 fragments — corrected rendering was used |

---

## 2. Security flags (values redacted — act on the fact, not the value)

- **Exposed API keys:** 3 Agnes keys and 1 Abliterated.ai key were pasted in plaintext across
  TODO_LIST.md, OFFENSIVE_DEVELOPMENT_CHECKLIST.md and the master prompt doc. All those files are
  now deleted from the working tree. **Rotation is still required** (master checklist Phase 0) —
  treat the values as compromised. Store replacements in `.env` only.
- **Hardcoded admin bypass PIN** (9-digit, specified for `AdminBypass.ADMIN_PIN`) — the legacy doc
  itself admitted it is RE-discoverable in shipped bytecode. **Excluded from tasks** (Appendix B of
  the master checklist); auth goes through the documented auth-methods manager instead.
- **Hardcoded USDC paywall receiver address** (Ethereum, baked into LICENSE + paywall code in the
  legacy spec) — **excluded from tasks**; monetization is a separate explicit product decision.

---

## 3. Design system — "Quantum Dark"

- Material 3 dark, accent `#00E5FF` (cyber blue); JetBrains Mono for hex/log output.
- Universal state colors: GREY / GREEN / AMBER / RED / BLUE; danger = outline button + consequence
  confirmation sheet.
- Widget anatomy: title bar (icon + name + ℹ️ tooltip + overflow ⋮ menu) → content → status footer.
- Dense-data pattern: compact rows, swipe actions, sticky headers, filter chips, FTS always visible.
- Masked secrets: tap-reveal (biometric) + auto-re-mask; `MaskedSecretCell` + `CopyChip`;
  clipboard auto-clear via `ClipboardGuard.armClear` (`credentials.clipboard_clear_sec`, default 30 s).
- Bottom-sheets-first for secondary flows; ONE shared streaming-text composable (terminal/chat/
  keylog/pcap); empty states must teach; shared `JobCard` for every job ≥3 s; 48dp touch targets.
- Navigation tree: Home / AI (Chat·Agents·Tasks·Skills·OpenCode) / Recon / Exploitation / Control /
  Post-Exploit / Social / Markets / System; cross-link "target chips" deep-link to the world-map drawer.

---

## 4. Architecture references

### 4.1 v5.0 "Omni" proposed structure (most complete tree in the legacy docs)
- `quantum_cli.py` thin launcher + `dist/` builds.
- Python core: `src/quantum/{core,ai,recon,camwar,weapons,postexploit,c2,overlord,reporting}`.
- Android: `android/app/src/main/java/dev/qcli/` with ~70 Kotlin packages (core/db, settings,
  widgetengine, education, selfhealing, toolbridge, telemetry, modelmanager, resourcemgr, providers,
  agents, sldr, nsagency, workflows, playbooks, learning, catalogs, exploitgen, knowledge, rat, adb,
  qrcampaign, phishing, messaging, socialeng, wifi, mitm, pcap, sdr, rf, bt, nfc, brute, osint,
  creds, cookies, postexploit, fuzz, sandbox, drones, nanoswarm, scada, iot, cameras, darkweb,
  evasion, spoofing, mobilewrap, builder, opencode, xkit, media, ddns, wallets, billing, auth,
  admin, integrity, fleet, team, swarmmesh, fusion, reporting, operator, ops, incidentresponse,
  training, unconventional, hw, autonomy, skills, integrations, terminal, wizard, profiles, bugs,
  dashboards). `[+]`/`[S#]` annotations in the source mark new vs sprint-designed files.
- Structural rule (binding): **one PR = module + widget + settings + tooltip + docs-delta + tests.**

### 4.2 v4.3.1-substrate missing-files checklist (P0–P4)
- P0: settings-schema trio, ModelDownloadManager, scan/cam wiring, ExploitDropdown + CatalogSyncEngine.
- P1: Registry100 / CustomProviderFlow / ChatScreen / FloatingChatBubble / AgentRunner / AiSwarm.
- P2: WidgetShell / DashboardScaffold / JobCard / MaskedSecretCell.
- P3: DatabaseModule / HealingDaemon / TooltipRegistry / gen_migrations.py.
- (Layer flow: UI → widget engine → domain → providers → toolbridge → 3-DB SQLCipher → self-healing
  + update channels.)

### 4.3 Three-DB SQLCipher schema
- DBs: `quantum_app` / `quantum_intel` / `quantum_secrets` (SQLCipher, WAL).
- Keys: StrongBox MasterKey → HKDF per-DB derivation; BLOB envelope encryption (files/, AES-256-GCM);
  per-row HMAC on critical plaintexts; zeroize paths; encrypted export (age/AES); backup exclusions;
  weekly snapshots; migration fixtures in CI.
- Key tables (intel side): Targets+provenance, Loot, OsintFindings, CellObservation, PcapSession,
  WifiAudit, NfcCardRecord/SectorDump, MifareKeyRing, KeylogEntry, HwPayloadCatalog/DeviceRegistry,
  QrCampaign, AdbTargetExploit, SwarmRun, Playbook.

---

## 5. Platform component contracts (v3.8 trunk + v3.10 agent tier)

### 5.1 v3.8 trunk files (all delivered per SPRINT34; verify presence in `android/`)
- `core/QuantumApplication.kt` — @HiltAndroidApp; CrashLoopGuard (3 boot fails → safe mode); Hilt
  multibound `BootPhase` set; boot order: content load → registry load → catalog open → provider
  probe → beacon start → schedulers arm.
- `widgetengine/WidgetGrid.kt` — LazyVerticalGrid, GridCells.Adaptive 320dp, long-press drag
  reorder, layout persisted via DataStore.
- `education/ContentRegistry.kt` — signed tooltip/walkthrough hot-fix from `$CONTENT_CHANNEL/manifest.json`,
  signature-verified, staged-swap rollback, fail-closed.
- `education/WalkthroughEngine.kt` — hands-on `advanceOn` semantic triggers via SharedFlow (buffer 16);
  `general.walkthroughs_enabled`.
- `selfhealing/FeatureRegistry.kt` — health mesh: GREEN >80, AMBER >50 (heal hint), else RED; GREY for
  remote-killed/disabled; crash-decay 0.05; signed KillSwitchPack; `dim()`.
- `ops/DoctrineCodex.kt` — `Rule(id, GateClass HUMAN_GATE|AUTO_IF|NOTIFY|SILENT, Envelope,
  EvidenceClass NONE|LOG|BUNDLE|SIGNED_BUNDLE)`; unknown rule = violation; policy may widen/narrow but
  never create; evidence breach = P1. Seeded rules: release.ship, payload.deploy, exfil.push, wipe.*,
  ics.write, remediation.apply, provider.registry.patch, triage.p0, maintenance.window,
  backlog.reconcile, federation.consume (+ Sprint 34: mission.launch, mission.disrupt, zero.spend,
  craft.ransom.build, campaign.passive_only/access/dwell/loot/effects).
- `widgetengine/components/JobCard.kt`; `MaskedSecretCell.kt` + `CopyChip.kt`.
- `docs/LedgerBindings.kt` — CI lint parses `docs/ledger.md` claims vs FeatureRegistry; claim without
  a live module = build failure (invoked from ci.yml after tests).
- `ops/MaintenanceScheduler.kt` — pattern-scored windows, BatteryGate, `horizon()` gated on
  `ops.maintenance.warn_lead_days`.
- Test: `DoctrineCodexTest` (4 tests — every autonomy call site resolves to a rule; policy never
  creates rules; evidence breach → P1; unknown rule = violation).

### 5.2 v3.10 agent tier (delivered per SPRINT34; verify in `android/`)
- `agent/core/AgentRuntime.kt` — AgentDefinition (id, doctrineBlock, reasonClass
  CHAT|PLAN|SUPERVISED_ACT|AUTONOMOUS_ACT, toolset, autonomy, widgetIds, subordinates, modelProfile);
  `converse()` → `codex.verdict("agent.reason")` → ProviderRouter.complete → ToolEngine.dispatch.
  **No-fabrication invariant:** outputs graded [REASONED] vs [EXECUTED]; tool receipts required.
- `sldr/MissionEngine.kt` — SLDR kill chain (RECON→ANALYZE→STRIKE→ESCALATE&MOVE→LOOT→DISRUPT→AAR);
  interrupts HOLD/ABORT/RESUME/ADJUST; RoE guard outcomes: Pass | EscalateToOperator (mission-critical
  only) | LogAsPivot. Codex rules mission.launch / mission.disrupt.
- `sldr/AutonomyLevels.kt` — L0 HUMAN_GATE / L1 SUPERVISED / L2 PHASE-GATED / L3 MISSION-AUTONOMOUS /
  L4 SILENT; default L4; operator may narrow per-mission, never widen without a new Codex rule.
- `nsagency/AgencyGraph.kt` — 33-agent tree: SLDR; NS-COMMAND; NS-INTEL; NS-CRAFT (+ BOTNET, TROJAN,
  RAT, RANSOM, ADWARE, VIRUS, WORM, ROOTKIT, LOADER, CRYPTER); NS-BREACH (+ ZERO, ZEROCLICK,
  HARDWARE, IOS, ANDROID, WEB, CLOUD, SCM); NS-DEPLOY (phases STAGE→ACCESS→FOOTHOLD→EXPAND→
  CONSOLIDATE→ACHIEVE→WITHDRAW); NS-FORGE; NS-SENSOR; NS-SCRIBE. VIRUS/WORM/ROOTKIT/SCM hard-registered L3.
- `nsagency/SensorGate.kt` — verdicts [V-GREEN]/[V-YELLOW]/[V-RED]; quality gates G1 CODE→G5
  WEAPONIZATION; **no G5 without V-GREEN (standing veto)**.
- `nsagency/OpLog.kt` — Room `OpEntry(n, at, phase, agentId, toolReceipts, reasonDigest, decisions,
  prevHash)` hash-chained tamper-evident. NOTE: the transcribed entity used illegal Kotlin syntax
  (`val at: Instant`, misplaced `@Entity`) — legalize when transcribing.
- `nsagency/ScribeAgent.kt` — 6-block AAR attached to Cycle view.
- `sldr/AgentDrill.kt` — earned autonomy; doctrine breach = automatic downgrade; failures land as P1s.
- Tests: `SldrMissionEngineTest` (5) + `AgencyGraphTest` (4) = 15 new tests in v3.10; CI structural
  lint: agent sources OPLOG-verified via receipts.
- Settings deltas: v3.9 `ops.duty.mode` (DEPLOYED/STANDBY default/OFF) + `ops.duty.handoff_targets`;
  v3.10 `agents.sldr.enabled=true`, `agents.ns.enabled=false`, `agents.default_autonomy=4`,
  `agents.duty_integration=true`, `mission.gates.vp-required=true`, `agent.runtime.backing`.

---

## 6. AI provider configuration

### 6.1 Registry100 (providers-as-data)
- Only 3 wire protocols as code: OPENAI_COMPAT (`/v1/chat/completions`), ANTHROPIC_COMPAT
  (`/v1/messages`), GEMINI_COMPAT (`streamGenerateContent`).
- `ProviderSpec(id, displayName, protocol, baseUrl, authStyle BEARER|X_API_KEY|QUERY_KEY, models,
  capabilities TEXT|VISION|IMAGE_GEN|VIDEO_GEN|TOOLS|AUTONOMY, keyUrl, notes)`.
- Exemplar rows (real base URLs from the legacy spec): openai, anthropic, google, xai, mistral,
  deepseek `https://api.deepseek.com/v1`, qwen (dashscope), zhipu bigmodel (glm-4.x), moonshot
  (kimi), minimax, groq `https://api.groq.com/openai/v1`, cerebras, sambanova, together, fireworks,
  nvidia-nim, replicate, openrouter `https://openrouter.ai/api/v1`, venice, agnes, abliteratus,
  portkey/litellm/helicone, regional (sakura, ncloud-clova, siliconflow, tencent-hunyuan),
  local-gguf/mlc. Providers are data rows, hot-fixable via channel-3 catalog push.

### 6.2 Specific providers
- **Agnes:** base `https://apihub.agnes-ai.com/v1`, model `Agnes-2.0-Flash`, 3-key rotation for
  rate limits. Keys were chat-transmitted → **rotate** (checklist Phase 0), store in `.env`/SecretStore.
- **Abliterated.ai:** OpenAI-compatible merge into existing config; `ABLITERATION_KEY` via `.env`;
  402/429 = "provider works, billing check needed" semantics.
- **KeyRotator/QuotaTracker** (rotakey pattern): generic quota-aware round-robin + failover under
  every OpenAI-compatible provider.
- **OmniRoute:** MIT gateway, ~340 providers/90+ free, quota-aware fallback — adapter + registry
  data source.
- **kimi-k3-in-c:** 2.78T-param C99, 8.24 GB peak RAM, Apache-2.0; GREY on ≤8 GB phones, GREEN ≥12 GB
  via Termux or remote-agent; arm64 build `scripts/build_kimi_arm64.sh`.
- **Local models:** RAM-adaptive — `whiterabbitneo/wrn-llama-3.1-8b` (≥16 GB) vs
  `huihui-ai/qwen3-1.7b-abliterated:Q4_K_M` (Ollama, `OLLAMA_MODELS=./models`); llama.cpp params
  `use_mlock`, `n_batch=512`, thread pinning; llama-server OpenAI-compatible loopback; catalog:
  Qwen2.5-Coder-3B-Q4_K_M, Llama-3.2-3B, Phi-3.5-mini; per-target n-gram wordlist tuner models.

### 6.3 Provider-bot GitHub automation (custom provider wizard)
- Bot PRs target `app/src/main/assets/content/providers/*.json`; branch `providers/custom/<slug>-<ts>`;
  labels `qc-sync`, `provider-sync`; flow: admin notification → auto branch → commit provider JSON →
  PR → squash auto-merge → branch deletion → nightly stale-branch janitor. Repo: `ProjectZeroDays/Quantum-CLI`.

---

## 7. Driver / dependency matrix

- **Gradle:** SQLCipher (net.zetetic) + Room(+FTS4), Coroutines/Flow, Hilt, DataStore, OkHttp/Retrofit,
  kotlinx.serialization, SSHJ, dnsjava, dadb, libtelnet-kt, usb-serial-for-android, libusb/JabLibUsb,
  ZXing, RootBeer, BiometricPrompt/Security-crypto/StrongBox, Vico, osmdroid/Mapbox, Coil, WorkManager.
- **Hardware drivers:** RTL-SDR RTL2832U (librtlsdr arm64 .so, gr-gsm-lite), HackRF One (libhackrf),
  BladeRF, USB WiFi RTL8812AU / ath9k_htc (monitor mode, rooted kernel drivers), Proxmark3/RDV4
  (pm3 v3 JSON-over-USB), ACR122U/OMNIKEY (PC/SC-over-CCID via libusb), Chameleon Mini/RevG (serial
  USB-OTG/BT), OMG Cable/Elite (USB mass-storage + USB-serial + WiFi HTTP API), Hak5 family
  (Ducky/Bunny/Croc/SharkJack/Turtle/Squirrel — PID/VID registry, mass-storage detection & write),
  Wi-Fi Pineapple (REST), plus Ubertooth, CC2531, Crazyradio PA, Flipper Zero, ELM327/OBD-II,
  RockBLOCK Iridium, Cactus WHID, Facedancer, USB Ninja.
- **Termux packages per module:** nmap, arp-scan, wifite, aircrack-ng, reaver, bully, pixiewps,
  hcxtools/hcxdumptool, hashcat, hydra, john (zip2john/pdf2john/crypt), 7zip, crunch, rockyou,
  tshark, tcpdump, sox, rtpbreak, steghide, zsteg, ffmpeg, pdfid/pdf-parser, llama.cpp, opencode,
  thefatrat, tor, cryptsetup, apktool, apksigner, zipalign, snap7, pymodbus, liboqs, openssh/autossh.
- **External APIs:** Abliteratus/OpenRouter/Venice/Agnes, Google CSE/SerpAPI, Shodan REST/Stream,
  IPQS/NumLookup/NumVerify/HIBP/GreyNoise, Blockchair/Blockstream (default OFF), GitHub OAuth device
  flow, Twilio/SendGrid, Proton (rclone)/Google, Project Zero RSS, exploit-db/PAT/Hak5 repos, DoH.
- **C2 backends:** Sliver (primary), msfvenom/MSF, Merlin; Cobalt Strike/Armitage referenced-only.
- **Engines (app-internal):** DashboardScaffold, WidgetShell, JobCard, HealingDaemon (8 failure
  classes incl. crash-loop safe mode after 3 boots), ToolBridge (~240 tools: root/Termux/USB-hw/REST),
  Provider PDL, ModelDownloadManager, QR Campaign Engine, auto-doc pipeline.

---

## 8. Sprint program & version ladder (historical map)

| Sprint | Version | Scope highlights |
|---|---|---|
| S0 / S0.5 | — | Stabilize / foundation: 3-DB SQLCipher, SettingDefinition schema, DashboardScaffold/WidgetShell/RecoveryBoundary, HealingDaemon, ToolBridge, tooltip pilot, TooltipLinter — THE TRUNK |
| S1–S9 | — | shell/widgets → AI core → recon-OSINT → exploitation → control-C2 → social → network → breadth+Dx → polish |
| S12 / S13 / S14 | v1.0 / v1.1 / v1.2 | polish release / OpenCode completion + active IMSI + bundle catalog / playbooks, team ops, on-device fine-tuning |
| S15 | v1.3 | Reporting Studio, Operator agent, device swarm + crack pool |
| S17 | v1.5→1.6 | 12 tracks: drone, SCADA/ICS, IoT zoo, RF, camera/AV, history-parity, USB kit, spoofing, exfil/API-hunt/media, hw catalog, autonomy matrix, docs |
| S18–S20 | v1.7–1.8 | GPS spoof, forensics, wallets (+USDC paywall — **excluded**, see §2), auth wizard, admin console, hardening (R8/native/anti-RE) |
| S21–S22 | v1.9–2.0 | formal verification, adversarial watcher, 4 benches, docs kingdom, legacy zero-day catalog, dark-web crawler, wrapping module (**excluded**) |
| S24 | v2.2 | APK fusion studio (**store-app trojanization excluded**; benign joiner/downloader tooling only), learning core, OpenCode tool-call library (80+), subagent swarm |
| v2.3–v3.0 | — | expert corpus FM-1…FM-12; audit remediation R1–R19 closing G1–G20 |
| S26–S28 | v3.2–3.4 | full-band deauth, rogue-APN MITM, Gmail transport, live docs sync, 100+ provider registry, custom provider wizard + GitHub bot, audit harness |
| S29–S30 | v3.5–3.6 | live-validation grid, load campaign, Triage Officer, Release Conductor, Maintenance Scheduler, Review Bench, Doctrine Codex |
| S32–S34 | v3.8–3.10 | Backlog Zero trunk closure; Sprint 33 "First Light" (Cycle 01, duty modes, Academy Cohort 01); Sprint 34 "The Arsenal" (agent tier) |
| v4.x (actual repo) | v4.0.0→v4.5 | package revision of single-file V3.1; APK CI `android-apk.yml`; v4.2.0, v4.3.0, v4.3.1 hotfix, v4.5 modules (RAT, ransomware, botnet, DDoS, messaging, stego, router, APN, EXIF, darkweb, dorks, shodan, map2d, phantomdroid) |

---

## 9. CI & test gates

- Per-PR four gates: evidence-chained, doctrine-cited, one-PR discipline, all gates green ("the train").
- CI jobs: build, unit, Detekt, screenshot truth-state matrix (empty/degraded/live/error/safe-mode-grey),
  DB migration fixtures, per-provider contract tests, safe-mode synthetic test, tooltip + settings
  lint gates. Golden rule: **no test disabled to pass CI.**
- `db/schema.yaml` + `scripts/gen_migrations.py`: "regenerate must be no-op diff" CI gate.
- Tooltip `_registry.json` linter v2: every widget ID must have a tooltip entry.
- Sprint-28 audit harness: `scripts/audit_repo.sh` + `endpoint_census.py` + placeholder census —
  exit criterion: zero placeholders, zero uncatalogued hosts; no literal-keys regex lint.
- LedgerBindings lint: `docs/ledger.md` claims vs FeatureRegistry (claim without live module = build failure).
- Opt-in nightly live contract tests (OpenRouter + Shodan, GREY-skip when keys absent).
- Python side: `pytest tests/` is the entry point; faceoffs checks: import, menu, no-AI 3-cycle
  autonomy, registry, C2, WSGI curl 200, emoji roundtrip, camwar graceful zero.

---

## 10. Naming, content & release conventions

- One PR = module + widget + settings + tooltip + docs-delta + tests.
- Doctrine text ships as **signed content packs** `content/ns/*.txt` validated by manifest lint
  (prompt typos fail the build).
- Skills marketplace format: signed portable `.qcbundle` (Ed25519 + sha256 pins), author-key trust.
- Ship card convention ("CARBON"-style) per sprint: settings delta, ledger/doctrine deltas, test count.
- Release artifacts: `dist/` single-script builds; APK via `.github/workflows/android-apk.yml`;
  release line v4.0.0 → v4.5.
- Repos: `github.com/projectzerodays/quantum-cli` (this repo) and `github.com/projectzerodays/quantum` (C2).
- Android package root: `dev.qcli`.

## 11. Android build gotchas

- Stale Gradle incremental state produces **phantom test failures** — do a clean build before
  diagnosing.
- Assets require the **subdirectory layout** (e.g., `assets/content/tooltips/...`).
- Use **FlowRow, not LazyVerticalGrid, inside scrollable pages**.

## 12. Decisions worth keeping (from the SLDR/NS-agency doctrine)

- RoE is absolute: operate only in authorized scope; out-of-scope findings become logged "pivot
  opportunities"; mission-critical exceptions escalate to the operator.
- No-fabrication is structural: `[REASONED]` vs `[EXECUTED]` grading + tool receipts + OPLOG lint.
- Escalation-of-force ladder (passive → effects); DISRUPT/effects need explicit authorization
  (Codex rules mission.disrupt / zero.spend = HUMAN_GATE + SIGNED_BUNDLE).
- C2/infra hygiene: no infra reuse across campaigns; burn on compromise.
- Self-propagating payloads require hard-coded kill date/stop-list; cleanroom builds per operation.
- Remote kill switches are user-sovereign — surfaced for opt-out, never silent.
- Capability engineering: modularity (stage-plugin loader), stealth-by-default, ≥2 persistence
  mechanisms for long-dwell, remote kill-switch + intel-wipe path.

---

## 13. Implementation plan — full feature integration (GUI & app flow)

This is the execution blueprint for the master checklist. It defines how every feature integrates
into a single, state-of-the-art, uniform user experience.

### 13.1 Guiding principles
1. **Masked-tool uniformity** — user space never sees raw tool chrome. Every integration (Termux,
   root exec, hardware drivers, REST, CLI binaries) surfaces exactly four things: GUI controls,
   telemetry, charts/visual output, and an optional collapsible log stream. Uniformity beats power-user
   exposure; raw output lives in the Loot/log viewers.
2. **Progressive disclosure, deny-by-default** — features without credentials/hardware render
   disabled with a reason ("see more" link into the in-app wiki), never hidden and never broken.
3. **One-PR discipline** (§10) and the widget exemplar pattern (sampler → Repository → ViewModel →
   widget → settings entry → tooltip → tests, proven with `home.net.speed`).
4. **Everything through ToolBridge** — no UI layer calls exec/hardware/REST directly; domain layer
   only; ViewModels expose immutable `UiState`.

### 13.2 App flow
- **Cold start:** splash (Quantum mark) → `OnboardingGate`:
  - **First run — onboarding wizard:** (1) welcome + authorization notice → (2) auth setup: mandatory
    9–11 digit PIN, optional extra factors (§13.3) → (3) admin account setup (Phase 15 PIN selection)
    → (4) optional credentials/API keys (skip ⇒ those modules grey out) → (5) dashboard tour via
    WalkthroughEngine (first-visit spotlights, hands-on `advanceOn` steps).
  - **Returning:** LockScreen with the configured factor chain.
- **LockScreen:** renders factors in configured order (biometric → PIN / password / FIDO2);
  exponential backoff on failures; **"I forgot my auth info?"** → recovery wipe flow (§13.3).
- **Main shell:** `Scaffold` = `ClassificationBar` (top) + sidebar (modal drawer on compact,
  persistent rail on medium, two-pane on expanded) + content `NavHost` + `ClassificationBar`
  (bottom) + JobCard/snackbar host for background jobs.
- **Sidebar:** scrollable with hidden scrollbar; header block = logo 160 dp (1 in) square, equal
  16 dp padding, `HorizontalDivider`, then collapsible nav groups with live-count badges; GitHub
  link icon at the group footer.
- **Deep links:** target chips → world-map drawer; every widget title bar ⋮ → `settings/<widgetId>`.

### 13.3 Authentication architecture
| Factor | Mechanism | Storage |
|---|---|---|
| PIN (9–11 digits, mandatory) | Custom PIN field + Keystore gate | Argon2id (or PBKDF2-HMAC-SHA256 ≥600k iters) hash in `quantum_secrets` — never plaintext |
| Password (12–25 digits) | Same hasher | Same |
| Face / fingerprint | `BiometricPrompt` (Class 3) | TEE-gated; nothing stored app-side |
| FIDO2 NFC/USB | Credential Manager `createPublicKeyCredential` (roaming authenticator) | Credential IDs only |

- **Policy engine `auth.policy`:** mode enum `PIN_ONLY` (default) · `BIOMETRIC_PIN` ·
  `BIOMETRIC_PASSWORD` · `PASSWORD_ONLY` · `FIDO2_ONLY` · `BIOMETRIC_FIDO2`; configurable in
  Settings → Security → Authentication while unlocked; admin can enforce an org floor; factor
  changes require re-auth with the current chain.
- **Lockout:** 5 failures → 30 s backoff doubling (cap 15 min); counters in encrypted DataStore;
  no reset path except the wipe flow.
- **Forgot-auth flow:** LockScreen button → confirm face/finger + device PIN (per spec) →
  `WipeService`: cancel jobs → drop the 3 DBs → clear DataStore/prefs → delete Keystore alias →
  relaunch into onboarding. App data only — device data untouched; the Python-side
  `logs/.lootkey` is out of scope (AGENTS.md rule 4).

### 13.4 GUI system & responsiveness
- **WindowSizeClass:** compact <600 dp (drawer nav, single column) · medium 600–840 dp (persistent
  rail) · expanded ≥840 dp (two-pane). Grids: `GridCells.Adaptive(320dp)`; FlowRow inside scrollable
  pages; ≥48 dp touch targets; font-scale tested to 200%.
- **Uniform widget anatomy:** `WidgetShell` = title bar (icon · name · ℹ️ tooltip · ⋮ settings) →
  content → status footer. Every widget gets a generated `settings/<widgetId>` route from its
  SettingDefinition group; long-press drag reorder with per-page lock; `RecoveryBoundary` per widget
  (crash → grey card + heal hint, never a white screen).
- **Masked-tool pattern (per 13.1):** controls + telemetry + charts + optional log stream; the
  four-surface contract is enforced in code review and by the tooltip linter (a widget ID without
  tooltip/settings fails CI).
- **Motion & polish:** `animateContentSize` on grid changes, shared-element transitions for target
  chips, skeleton loaders while tools warm up, empty states teach, haptic confirmation on
  DoctrineCodex HUMAN_GATE actions.
- **ClassificationBar:** thin (24 dp compact / 28 dp expanded), centered monospace caption,
  top AND bottom of the main Scaffold; text is a theme constant
  `classification_banner_text` = `CLASSIFIED // TS // SI-G // TK // HCS // SAP-ALPHA // NOFORN`.

### 13.5 Branding pipeline (done 2026-10-02, reproducible)
- Source of truth: `android/art/quantum_logo.png`; regenerate everything with
  `python scripts/gen_icons.py <image>`.
- Launcher: `mipmap-anydpi-v26/ic_launcher.xml` = background `@color/ic_launcher_background`
  (#02040A) + `drawable-xxxhdpi/ic_launcher_foreground.png` (432 px, logo inside the 66 dp safe
  zone) + `ic_launcher_monochrome.png` (luminance→white-alpha themed-icon layer); legacy
  `mipmap-{mdpi..xxxhdpi}/ic_launcher{,_round}.png` cover pre-26 devices.
- Sidebar: 160 dp square (`with(LocalDensity) { 1.inch.toDp() }`), equal padding, divider below;
  default asset `assets/brand/sidebar_logo_cia.png` (operator-supplied seal, transparent,
  square-padded) with Quantum-mark fallback `assets/brand/sidebar_logo.png`; runtime-overridable in
  settings. Legal caveat on file: official US-agency insignia implies affiliation — keep the app
  private/internal or swap in an original mark.

### 13.6 Milestones (aligned to the checklist priority order)
- **M1 — Security & shell foundation:** auth system (§13.3), ClassificationBar top+bottom, sidebar
  rework (logo block + divider + scroll), startup-credential greying, dead-button fixes. *Exit:*
  auth instrumentation tests green; screenshot truth matrix for the shell.
- **M2 — Dashboard framework + P0 ops dashboards:** WidgetShell settings-icon wiring and drag-drop
  verified on every page; OSINT/recon/C2/botnet/RAT/social/phishing/brute/DDoS/sabotage dashboards.
- **M3 — Hardware integrations:** NRSuite P0 capabilities with chip gating (Appendix A) + Stryker
  OSS ports.
- **M4 — Intelligence layer:** providers (Registry100, failover chain, KeyRotator) + admin console
  and paywall (Phase 15).
- **M5 — Offensive suites:** catalog/exploitation, control/C2/loot, network offense.
- **M6 — Breadth & polish:** hardware P2, reporting studio, Kodachi anonymity suite, agent tier →
  publish (Phase 5 step 8).
- Every milestone exits through the Phase 5 PASS gate (tests + lint + no-AI purity + build).

### 13.7 Verification gates
- **Auth:** instrumentation tests for setup, unlock, backoff, forgot-auth wipe, factor reconfiguration.
- **Screenshots:** truth-state matrix (empty / loading / live / error / safe-mode-grey) per widget
  at compact + expanded sizes.
- **Responsiveness:** small phone, large phone, 7″ + 10″ tablets, landscape, 200% font scale.
- **CI:** tooltip linter (every widget ID), settings lint (defaults + tooltip per setting),
  LedgerBindings claim-vs-module lint, no-AI purity, no literal-secrets regex lint.
- **UX acceptance:** every tool masked to the four-surface contract; every widget has a settings
  route; drag-drop + per-page lock verified; classification banners visible on every screen.
