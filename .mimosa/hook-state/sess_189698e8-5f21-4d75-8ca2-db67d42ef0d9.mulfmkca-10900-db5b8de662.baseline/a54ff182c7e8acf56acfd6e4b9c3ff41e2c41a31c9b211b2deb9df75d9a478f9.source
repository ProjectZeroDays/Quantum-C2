# AGENTS.md — Standing Rules for AI Agents Working This Repo

QUANTUM-CLI V4: single-script launcher (`quantum_cli.py`) + `src/quantum/` package +
`agents/build/variant.py`. `exploit_payloads/` is being built in parallel by other agents —
treat it as existing work, do not clobber it. **Authorized engagements only.**

Non-negotiable rules for every agent touching this codebase:

1. **Never weaken a check to make a test pass.** If a test fails, the production code is wrong —
   fix the production code, not the test.

2. **`quantum_cli.py` (single-file, archived at `dist/quantum-cli-v3.1-single.py`) is THE SPEC.**
   Any behavioral divergence of `src/quantum/` is a bug in the package, not in the spec.

3. **The `--no-ai` deterministic path must never gain network/Ollama calls.** It sets
   `QCLI_NO_AI=1` and `AI_Supervisor.ai_dead = True`; QBrain plans everything, offline.

4. **`logs/.lootkey` is immutable.** Deleting or editing it breaks every sealed `.gfy` in
   `loot/`. Never delete, rotate, or regenerate it in code, tests, or cleanup routines.

5. **Keep camera-first ordering in `AutonomousOverlord.run()` exactly as-is** — the CAMWAR sweep
   (`pwn_network`) runs before the service-scan/decision loop. Do not reorder.

6. **No simulated code.** Every module must be real and functional — real techniques, real
   network/crypto/logic, no mocks or placeholder behavior shipped as capability.

7. **Authorized engagements only.** All work assumes penetration-test/lab/contracted-authorization
   contexts; keep tooling, docs, and tone aligned with that constraint.

House style: `pytest tests/` is the test entry point; new weapons join `ZERO_DAY_REGISTRY`
(see `docs/HOWTOs.md` §7); docs live in `docs/` and must stay grounded in real code.
