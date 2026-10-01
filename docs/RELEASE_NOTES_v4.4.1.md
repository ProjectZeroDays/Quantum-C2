# QUANTUM-CLI v4.4.1 — Production Hardening

Patch release: closes every finding from the production-readiness gap
analysis. No new capabilities — bug fixes, CI hardening, and test depth.

## Highlights

- **CI now green on all 7 required checks** (lint + Ubuntu/Windows × Python
  3.9/3.11/3.13), enforced by branch protection on `main`.
- **7 real bugs fixed** found during the hardening pass:
  1. `c2/app.py` FEDERATION.pull: `json.dump()` missing file argument
  2. `quantum_android.py` cert generation: `datetime.timedelta` under a
     from-import (AttributeError)
  3. `persistence.win_run_key`: Run key absent on hardened hosts →
     `CreateKeyEx` (opens-or-creates)
  4. dist `exploit_dirtypipe`: missing `kernel`/`kernel_fixed` honesty fields
  5. menu-thread closure late binding over `agents` (src + dist)
  6. `harvest.control_camera`: dead `identify()` call
  7. CI workflow YAML: unquoted colon killed the workflow
- **dist/ single-file is now parity-enforced**: synced with src (64-entry
  registry, payload-folder dispatch); `tests/test_dist_parity.py` fails CI
  on any future drift.
- **Silent failures eliminated**: 7 `except Exception: pass` sites now log;
  ADB reader bare `except:` tightened.
- **Android test depth**: ExploitDb CSV parse/search (12 JVM tests) +
  QcliApi dispatcher contract (13 tests); real `org.json` on the test
  classpath; `CatalogSync` URL parity test.
- **Timestamps**: 28 `datetime.utcnow()` deprecations → tz-aware
  `now(timezone.utc)` (same `Z` output).
- **Hygiene**: `requirements.txt` (was: deps only in ci.yml), ruff lint
  gate in CI (F-class errors + unused imports, zero findings), `.gitattributes`
  LF normalization, mojibake fix in the APK wrapper help.

## What is verified vs. needs a live target

Unchanged from v4.4.0 — see `docs/ZERO_CLICK_AUDIT.md`. Catalogs (Exploit-DB
seed 47k+, PayloadsAllTheThings, BadUSB, KEV) are locally verified; weapon
fire against live targets is operator-verified per engagement.

## APKs

- `app-full-release.apk` — root/full operator suite
- `app-limited-release.apk` — no-root variant

Both built by CI from tag `v4.4.1` (commit fc4309d), unit tests green.
