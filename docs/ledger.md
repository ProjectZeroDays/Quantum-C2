# Operations Ledger — request-key → module bindings

The doc-that-cannot-lie. Every claim row maps a mission request-key to the
app modules that serve it. CI lints this file against
`FeatureRegistry.registered()` via `LedgerBindings.lintLedger` — a FULL
claim whose modules are not registered/live fails the build. Grades:

- **FULL** — every listed module is implemented, registered, and health-meshed.
- **BOUNDED** — listed modules are live; the claim is scoped to them.
- **PLANNED** — designed, not yet bound. Proves nothing.

| request-key | modules | grade | note |
|---|---|---|---|
| recon.sweep | c2.server, network | FULL | CAMWAR camera-first sweep lands in cameras |
| camera.warfare | cameras, c2.server | FULL | camera-first ordering is standing doctrine |
| brute.service | network | FULL | service brute/credential ops |
| overlord.autonomous | overlord, ai.client | FULL | camera-only + full-whitelist cycles |
| loot.seal | loot, c2.server | FULL | sealed .gfy via logs/.lootkey (immutable) |
| federation.mesh | federation, foxacid | FULL | cross-node task federation + landing server |
| ai.deterministic | ai.client | FULL | --no-ai offline path: QBrain only, no network |
| ops.journal | c2.server | FULL | audit/decision OPLOG, ATT&CK mapping |
| diagnostics.health | widgets, education | FULL | health mesh, walkthroughs, safe mode |
| dashboard.grid | widgets | FULL | drag/lock/arrange dashboard, persisted |
| maintenance.nightly | widgets | BOUNDED | windows scored, Overlord preempts |
| hotfix.channel | education | BOUNDED | signed channel, fail-closed, opt-in |
| ledger.lint | widgets | FULL | this file IS the lint target |
| exfil.push | loot | PLANNED | human-gated per DoctrineCodex; no auto path |
