# Quantum CLI v4.4.0 — Operator Suite

The zero-click audit release: every advertised exploit is live, honest,
and verifiable — plus the operator suite (providers, agents, skills,
workflows, Project Zero feed) on both Python and Android.

## Highlights

### Zero-click exploit audit (docs/ZERO_CLICK_AUDIT.md)
- **CVE-2026-0073 — adbd TLS auth bypass (EC-cert vs stored RSA key)**:
  the full TAO framework — STLS negotiation, TLS 1.3 with ephemeral
  EC P-256 client cert, post-TLS shell via 32 MB delayed-ack window,
  plus privilege escalation, lateral movement (WiFi/BT/contacts/SMS/
  GPS), DNS/ICMP/HTTPS exfiltration, persistence, evasion, and DGA
  C2. Verified end-to-end against a mock adbd.
- **21 payload folders verified** (11 previously-empty folders filled +
  10 new): BlueFrag (CVE-2020-0022), BT HID injection
  (CVE-2023-45866), KRACK (CVE-2017-13077), BootHole (CVE-2022-21894),
  Follina (CVE-2022-30190), FORCEDENTRY (CVE-2021-30860), WebKit UAF
  (CVE-2021-30858) + type confusion (CVE-2023-32409), Apple ImageIO
  (CVE-2023-41064), libwebp (CVE-2023-4863), WhatsApp VOIP
  (CVE-2019-3568), EternalBlue, Zerologon, PrintNightmare, PetitPotam,
  ProxyLogon, and more. Every deploy tool: JSON output, exit-code
  contract, never crashes, structural self-verification.
- **Misattributed CVEs rejected** — the supplied "iMessage
  CVE-2023-34048"-class pairings (actually VMware/Splunk/Fortinet
  CVEs) were not carried over as fiction.

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
  into the 35-entry ZERO_DAY_REGISTRY fire contract.

### Operator suite (Android)
- Boot spine: 8-phase isolated boot, crash-loop guard, healing daemon,
  safe mode (SafeModeActivity), health mesh, signed education content
  (tooltips/walkthroughs, ECDSA-verified hotfix channel).
- Provider presets for the AI client (Abliteration.ai/OpenRouter/
  Venice.ai/Agnes/opencode) with per-provider keys.
- Agents/Skills/Terminal pages, agent + skill + workflow stores.
- Searchable exploit dropdown over the weapon registry.
- Chat enhancements: per-message copy/download, attachments, floating
  chat FAB.
- Dashboard status chips (root/VPN/IP/MAC/DNS/proxy) + Project Zero
  feed card + GitHub sidebar link.
- Local model downloader: mirror fallbacks + resume + size sanity.

## Testing
- Python: 58 passed, 2 skipped (12 payload generators run end-to-end
  in CI; 5 SMB/HTTP probes verified against closed ports).
- Android: unit tests for crash-loop guard, ledger bindings, content
  signing, doctrine codex, widget layout; full + limited APK builds.

## Docs
- `docs/ZERO_CLICK_AUDIT.md` — the audit (findings, remediation,
  honesty boundaries).
- `docs/SLDR_AGENT_PROMPT.md` — SLDR/NS-org agent doctrine.
- `docs/ROADMAP_TASKS.md` — operator task list / master roadmap.

Authorized engagements only. See README for usage.
