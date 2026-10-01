# Quantum CLI — Task Queue

Status: done / doing / parked / todo. Update after every task. (Requested by user; `/swarm` drives this list.)

## Doing

- [ ] **ADB / PhantomDroid device-control dashboard** — wireless ADB (TCP 5555) via dadb:
      scan/connect, shell, screencap live view, input injection (tap/swipe/text/keyevent),
      app list/install/uninstall, push/pull, device info. USB (OTG host) mode behind
      hardware detection; honest "not supported on this device" state otherwise.
      Files: `ops/AdbControl.kt`, new `Page.DEVICES` + DevicesPage UI, unit tests, manual entry.
- [ ] **Honeypot dashboard** *(user request)* — embedded fake-service honeypot manager:
      service presets (HTTP admin panel, SSH banner, FTP, Telnet, MQTT, ADB-5555 decoy),
      per-service start/stop + port config, live inbound-connection log with
      source IP / payload capture, alert badge on new hit, JSON export of captured
      sessions. Honest scope: listeners run in-app on this device (no root needed
      for unprivileged ports); root-only ports marked.

## Todo

- [ ] **Sprint 0.5 foundation package** (Artifacts A/B/C from master doc): GitHub Project
      import yaml + sync script, three-DB SQLCipher module, SettingDefinition registry,
      DashboardScaffold/WidgetShell/RecoveryBoundary, HealingDaemon, ToolBridge,
      tooltip/walkthrough content pilot + TooltipLinter.
- [ ] **Simplenote task list** — `http://simp.ly/p/2KNqlr` is login-walled (redirects to
      app.simplenote.com/login). Blocked on user pasting the note contents.
- [ ] Extended Zenmap NSE-style scan profiles (beyond T0–T5 + port ranges already shipped).

## Done

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
