# QUANTUM-CLI V4 — Troubleshooting

Symptom → fix table for the most common issues on **authorized engagements**. Every entry is
grounded in the code's actual behavior and log lines.

## Quick table

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'/'requests'/'Crypto'/...` at startup | Missing deps — install the full set: `pip install flask requests waitress pycryptodome impacket pysmb colorama` (Python 3.9+). `quantum.core.deps` keeps imports soft, so some commands still run — install anyway before an engagement. |
| AI log: `[AI] credits/rate — billing check needed` (HTTP 402/429) | The provider is reachable but out of credits or rate-limited. Top up the Abliterated.ai account behind `ABLITERATION_KEY`. Planning already fell back to deterministic QBrain — the run continues; verify your key/credits before the next AI-guided engagement. |
| C2 log: `waitress/gunicorn missing — falling back to Flask dev server (NOT production-recommended...)` | Install the production WSGI server: `pip install waitress`. The C2 chain is waitress → gunicorn (POSIX) → Flask dev; you want waitress for real engagements. |
| Cameras discovered but none cracked (`controlled` stays false) | Default credential tables were exhausted for that vendor. Try single-IP mode (camera console options 5/6, or `camshot -t <ip>`), confirm RTSP `:554` is actually open (`rtsp_probe`), run OSINT first so `tune_brute_wordlist` can add hints, and check vendor identification — a `generic` classification means no vendor-specific endpoints will be tried. |
| Dirty Pipe probe reports not vulnerable on a Linux host | Expected on modern kernels: CVE-2022-0847 affects kernel ≥5.8 and below the fixed releases (5.16.11, 5.15.25, 5.10.102). If `uname -r` shows a patched kernel, the host is simply not a Dirty Pipe candidate — try PwnKit / Baron Samedit / overlayfs / nf_tables checks instead (`registry.fire("CVE-2021-4034", ip)` etc.). |
| `ghostdns` prints only the usage line (`usage: quantum_cli.py ghostdns --domain ...`) | No domain given. Pass `--domain yourdomain.tld` or set `QCLI_DOMAIN=yourdomain.tld` in `.env`. Remember: the domain must be one you control, with TXT records at `cmd.<domain>` (or `<host_id>.cmd.<domain>`) for tasking. |
| Kill-switch armed but implants are still alive | The kill-switch is **pull-based**: `kill_all_implants` only queues wipe/die tasks; each implant executes them on its **next beacon to `/r`**. An implant that has stopped beaconing cannot be killed by the switch — wait for its interval, or use `wipe` on a reachable host. Verify with the dash (`/dash/api/state` → `killswitch: true`). |
| `unseal` logs `unseal fail ... (lootkey intact?)` | `logs/.lootkey` was deleted, edited, or restored from the wrong engagement. The key is created once and is immutable — restore the exact `.lootkey` from the engagement backup; without it the `.gfy` files are unrecoverable (AES-256-GCM). |
| Garbled emoji/box characters on the Windows console | Run `chcp 65001` to switch the console to UTF-8 (or use Windows Terminal). `quantum.core.env` already reconfigures stdout/stderr to UTF-8 with `errors="replace"`, so output stays readable — glyphs may still look wrong in legacy code pages. |
| Startup bind error on `:8443` / `:8081` / `:5353` | Another listener owns the port: C2 = 8443, FOXACID = 8081, DoH beacon server = 5353. Find and stop the other service (`netstat -ano | findstr :8443` on Windows, `ss -ltnp | grep 8443` on POSIX) — or stop the earlier QUANTUM instance (a menu `19` C2 plus an Overlord C2 both bind 8443; run one). |
| First run is slow | Normal: first run generates the implant keypair (`keygen`), optionally searches for/deployes a local AI model into `models/`, and performs the full-scope camera + service discovery before any decision cycles. Subsequent cycles are faster (state is warm, keys exist). Use `--no-ai` to skip all AI/model work deterministically. |
| `ImportError`/`ModuleNotFoundError` mentioning `impacket` or `smb` | Optional Windows-tier dependencies. `pip install impacket pysmb`. Without them the legacy Windows checks (Zerologon, EternalBlue, PrintNightmare, PetitPotam, ProxyLogon) degrade gracefully — the rest of the framework keeps working. |

## Escalation path

1. Reproduce with the smallest command (`zerocheck -t <ip>`, `--menu` option by option).
2. Read `logs/audit.jsonl` (structured, one JSON event per line) — every action is logged there.
3. A launcher crash writes a full traceback to `logs/crash.log`.
4. Confirm environment: Python 3.9+, the six pip packages, `.env` contents (`ABLITERATION_KEY`,
   `QCLI_DOMAIN`), free ports.
5. Still stuck? Check the deterministic path first (`--no-ai`) — if that works, the issue is in
   the AI/provider layer (key, credits, model pinning).

Related: [WIKI.md](WIKI.md) (architecture + C2 REST API), [OPERATOR_MANUAL.md](OPERATOR_MANUAL.md)
(runbook + emergency procedures), [HOWTOs.md](HOWTOs.md).
