# weapons/poc — vendored kernel-tier PoC sources

Vendored, credit-preserving C PoCs for the kernel/local-privilege-escalation
tier of the Quantum CLI exploit payload library. Consumed by the matching
`exploit_payloads/*` deploy.py launchers and by
`src/quantum/weapons/kernel_v3.py::_poc_attempt()` (which compiles
`src/<CVE>/*.c` into `bin/<CVE>` on non-root Linux when `cc` is present).

Layout (one directory per CVE id, mirroring the registry):

| Path                                  | Payload                                            |
|---------------------------------------|----------------------------------------------------|
| `src/CVE-2021-4034/pwnkit.c`          | PwnKit (polkit pkexec) one-file LPE (ly4k/Qualys)  |
| `src/CVE-2021-3156/baron_samedit.c`    | Baron Samedit (sudo heap overflow) launcher (blasty)|
| `src/CVE-2021-3156/lib.c`              | Baron Samedit NSS root payload (blasty)            |
| `src/CVE-2024-1086/nftables.c`        | nf_tables double-free PoC (Notselwyn technique)   |

## Build

```bash
make            # builds everything into bin/
make pwnkit     # individual targets available
```

Each payload is also built ad-hoc by its `exploit_payloads/<cve>/deploy.py`
launcher (which applies the exact compile flags each PoC needs), so a manual
`make` is not a prerequisite for deploying.

## Provenance / licensing

- CVE-2021-4034: adapted from https://github.com/ly4k/PwnKit (itself based
  on the Qualys advisory technique; see the file header).
- CVE-2021-3156: adapted from https://github.com/blasty/CVE-2021-3156
  (hax.c + lib.c, "sudo-hax-me-i-am-famous"; see file headers).
- CVE-2024-1086: single-file stdlib-only reimplementation of the technique
  published at https://github.com/Notselwyn/CVE-2024-1086.

Authorized security-lab use only.
