=== APPENDED: MILESTONE CHART + MISSING PIECES + CONSTRAINTS + API SWEEP ===

MILESTONE CHART (verified dates):
- Week 1-2 (Phase 0): DB/Bus/State/Registry/Tasks/Plugins/ModuleBase — DONE (verified)
- Week 2-3 (Phase 1): Web SPA shell + killswitch + telemetry collectors — PARTIAL (shell built, no verified fetch)
- Week 3-5 (Phase 2): Exploit scorer/matcher/customizer/builder/dryrun — NOT STARTED
- Week 5-8 (Phase 3): Post-ex lanes A-F — NOT STARTED
- Week 8-10 (Phase 4): Pivot/radio/exfil — NOT STARTED
- Week 10-13 (Phase 5): Control/account/OTP/MITM/abuse — NOT STARTED
- Week 13-15 (Phase 6): Loot FTS/graph/timeline/anomaly/reports/alerts/search/bot — NOT STARTED
- Week 15-18 (Phase 7): APK parity + .exe bundle — NOT STARTED
- Week 18-21 (Phase 8): Agents/iOS/macOS/plugin/autonomy/docs — NOT STARTED

CONSTRAINTS / OBSTACLES NOT FULLY DISCUSSED IN DOC:
- Hardware dependency: No ARM64 build host verified; Android APK needs build machine
- Network isolation: C2 requires external domain/DoH endpoint for real deployment
- Legal/authorization: All work assumes authorized pen-test; no consent flow (correct per plan)
- AI provider dependency: runtime_local.py missing = no local model execution possible
- Key management: logs/.lootkey immutable (AGENTS.md #4); never rotate
- Payload ZIP invariant: ZIP_STORED/create_system=0/fixed epoch must hold; no automated verify script
- No CI for web-build (.github/workflows/web-build.yml missing from scaffold)
- exploit_payloads/ directory exists but no payloads.lock.json regeneration script automated
- Android assets/web/ needs sync with src/quantum/web/static/; no sync script created

MISSING FILES / DELIVERABLES NEEDED TO FULLY IMPLEMENT LACKING FEATURES:
- 34 web page modules, 16 chart components, 12 card components, 5 map components, 4 device components, 7 shell components, 15 primitive components
- 35 API modules (api/*.py), 170 post-ex module files, 6 exploit engine files, 4 new postex index files
- core/telemetry.py + telemetry_store.py + fingerprint.py + opsec.py + diff.py + timeline.py + anomaly.py
- c2/stream.py, control/agentless.py, weapons/scorer_hooks.py, ops/channels.py + watchdog.py
- ai/analyst.py + reporter.py, recon/vendor_oui.py + asn.py
- 24 test files, 11 new docs, CI workflow updates
- Android Kotlin: 34 pages + 10 components + 9 ops + 2 data + assets/web sync

API ENDPOINTS NOT END-TO-END (185 planned; only /devices partial via SPA):
/devices/:id/enumerate /scan /exploits /exploits/:cve/fire /payload /telemetry /telemetry/live /screen /input /files /files/search /processes /apps /permissions /radios /accounts /certs /mdm /persistence /forwarding /apn /otp /postex /harvest /pivot /killswitch /rollback /diff /timeline /opsec /loot /creds /fleet/actions /alerts /reports /events /search /modules /agents /listeners /transports /settings /keys /admin
Plan: each needs web/api/<name>.py + ok/err helper + validation + bus emission + state guard. Priority: devices/tasks/scan/exploits/telemetry/postex/loot/alerts first.
