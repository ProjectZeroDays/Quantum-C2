# Quantum CLI — Task Queue

Status: done / doing / parked / todo. Update after every task. (Requested by user; `/swarm` drives this list.)

## Doing

- [ ] **Sprint 0.5 foundation package** (Artifacts A/B/C): the GitHub Project import
      yaml + sync script, three-DB SQLCipher module, SettingDefinition registry,
      DashboardScaffold/WidgetShell/RecoveryBoundary, HealingDaemon, ToolBridge,
      and tooltip/walkthrough pilot + TooltipLinter still need real implementations.

## Todo

- [ ] **Sprint 0.5 foundation package** (Artifacts A/B/C from master doc): GitHub Project
      import yaml + sync script, three-DB SQLCipher module, SettingDefinition registry,
      DashboardScaffold/WidgetShell/RecoveryBoundary, HealingDaemon, ToolBridge,
      tooltip/walkthrough content pilot + TooltipLinter.
- [ ] **Simplenote task list** — `http://simp.ly/p/2KNqlr` is login-walled (redirects to
      app.simplenote.com/login). Blocked on user pasting the note contents.
- [ ] Extended Zenmap NSE-style scan profiles (beyond T0–T5 + port ranges already shipped).

## Done

- [x] **RAT dashboard ("Remote Access", never product-labeled)** *(user request)* —
      Python `quantum.rat` (13 capabilities with honest `requires` tags, TASKQ
      dispatch, output exfil over the existing /r data channel, fleet snapshot,
      RAT agent-profile generator) + Flask round-trip test; Android
      `ops/RatControl.kt` (byte-identical protocol, 263-char parity-locked
      exfil wrapper) + RatPage (C2 start/stop, fleet with stale/pending badges,
      capability dispatch, loot viewer with PNG/text rendering). 9 + 8 tests.
- [x] **Google Dorking module** *(user request)* — Python `recon/googledork.py`
      (24 presets / 7 categories, 12 operators, 4 engines, 6 analyst-methods,
      URL builders only — never scraped) + Android `ops/GoogleDork.kt`
      (mirrored catalog) + DorkPage (packs, operator reference, methods,
      in-app WebView browser with nav controls). Analyst methods are generic
      public OSINT tradecraft — no agency attribution anywhere (tests enforce).
      7 + 4 tests.

- [x] **Crunch wordlist integration** *(user request)* — new `quantum.brute.crunch`
      package: crunch-compatible custom password list creation (`min/max`,
      literal charsets, `-t` patterns with `@` lower / `,` upper / `%` digit /
      `^` symbol placeholders + backslash escapes, odometer ordering identical
      to crunch). System `crunch` binary used as passthrough when installed
      (`detect_crunch`), pure-Python generator otherwise — never bundled, never
      faked (`CRUNCH_NOTE`, no fake flags). Exact `estimate_count`/`estimate_size`
      up front, `write_wordlist` refuses jobs over the entry cap unless
      `allow_huge=True`, resume (`-s`) + limit (`-c`) compose, minimal
      `charset.lst` support, root exports as `crunch_*`. 18 new tests.

- [x] **Honeypot dashboard** *(user request)* — `ops/Honeypot.kt` + `Page.HONEYPOT` +
      HoneypotPage.kt: 7 unprivileged presets (HTTP admin :8080, SSH :2222, FTP :2121,
      Telnet :2323, MQTT :1883, Redis :6379, MySQL :3306) with real banners + scripted
      replies (331/530, Password:), start/stop per service, live connection log
      (ip:port + captured first lines, newest first), clear + SAF JSON export,
      audit lines. 9 loopback unit tests (banner/capture/silent-scan/dup-start/
      privileged-port refusal/busy-port/json-escape). No-root ports only; root ports
      honestly refused instead of offered.
- [x] **ADB / PhantomDroid device-control dashboard** — `ops/AdbControl.kt` (dadb 1.2.9
      direct ADB protocol, released-API verified against the sources jar) + `Page.DEVICES`
      + DevicesPage.kt: LAN scan for :5555 (Net.cidrHosts + ZenScan), connect w/ app-local
      RSA key + shell probe, device info, tap/text/key injection, snapshot + 2 s live
      stills dialog, shell console, package list/uninstall, SAF APK install. USB (OTG)
      honestly marked unsupported on Android (USB_NOTE in UI). 7 pure-helper tests.

- [x] **ML dashboard** — `Page.ML` + MachineLearningPage.kt: KPI tiles, latency/throughput
      Canvas sparklines, model widget (download progress/unload/delete), inference controls
      (temperature/top-K/max-tokens/telemetry switch, APPLY & RELOAD ENGINE), test-inference
      card, engine-configuration summary. New `MlTelemetry` ring buffer fed by AiClient
      around real inferences; 6 JVM tests; SettingsData ml* fields persisted.
- [x] **Classification banner** — "CLASSIFIED // TOP SECRET // SI-G // TK // HCS //
      SAP-ALPHA // NOFORN" pinned top+bottom (`ClassificationFrame`), auto-fit font,
      matching status/nav bar colors, both MainActivity + SafeModeActivity.
- [x] **Console log buttons** — View (full-log dialog) / Download (SAF CreateDocument) /
      Clear on Terminal console AND Dashboard console.
- [x] **DoH persistent reverse channel** — `PersistentDoHChannel` (bidirectional egress+task
      poll, exponential backoff w/ jitter, on-disk state resume, never-give-up run loop),
      `backoff_seconds` pure fn, `doh_task_check(errors="raise")`, multi-resolver rotation
      in `recon/doh.py` (Cloudflare→Google→AliDNS), shell agent fast-retry loop.
      9 new tests; live-target verification stated as pending.
- [x] **Kodachi-style anonymous networking** — `quantum.anon` package: honest component
      detection (tor/dnscrypt/proxychains/obfs4/kodachi), generated proxychains+dnscrypt
      (DoH) configs, launch w/ honest errors, Tor-SOCKS anon_fetch (no clearnet fallback),
      `kodachi_bundled: False` always. 8 new tests.
- [x] **GUI redesign** — "Quantum Glass" Theme.kt (glass gradient panels, light-catch
      borders, ambient glow backdrop, weighted typography, modern shape scale).
- [x] **dadb dependency** (`dev.mobile:dadb:1.2.9`) + JUnit-5 runtime-scope exclusion
      fixing `mergeFullDebugJavaResource` (META-INF/LICENSE.md collisions).
- [x] **v4.4.3 released** — both APK assets, title fixed to "QUANTUM-CLI v4.4.3".
- [x] `.opencode/command/swarm.md` installed; camera thumbnails, Tasks page, floating chat,
      zenmap section, SAF attachments, sim/ removal, model-mirror fix — shipped earlier.
