# Exploit payload build harness
PYTHON   ?= python3
CC       ?= cc
CFLAGS   ?= -O2 -Wall -Wextra
DIST     := dist
EXPLOITS := exploits
LOCK     := payloads.lock.json

.PHONY: all payloads manifest dirtypipe verify test check census lock kernel tv tv-report clean help

all: payloads manifest dirtypipe

payloads:
	@$(PYTHON) run_all.py --exploits $(EXPLOITS) --outdir $(DIST) --no-manifest

manifest: payloads
	@$(PYTHON) run_all.py --exploits $(EXPLOITS) --outdir $(DIST)

dirtypipe: payloads
	@if [ -f $(DIST)/CVE-2022-0847.c ]; then \
		$(CC) $(CFLAGS) $(DIST)/CVE-2022-0847.c -o $(DIST)/dirtypipe && \
		echo "[+] built $(DIST)/dirtypipe"; \
	fi

verify:
	@$(PYTHON) run_all.py --outdir $(DIST) --verify

test:
	@$(PYTHON) -m pytest tests/ -q

# The standing audit gates: no simulated code and no invented endpoints in
# the production tree. The same two scripts run as the `census` CI job.
census:
	@$(PYTHON) scripts/placeholder_census.py
	@$(PYTHON) scripts/endpoint_census.py

check: manifest verify census test
	@echo "[+] all checks passed"

lock: manifest
	@cp $(DIST)/manifest.json $(LOCK)
	@echo "[+] lock -> $(LOCK)"

kernel: 
	@$(PYTHON) resolve_offsets.py $(if $(ADB),--adb,)
	@$(PYTHON) build_all_kernel.py --strict

tv:
	@$(PYTHON) run_all.py --exploits $(EXPLOITS) --outdir $(DIST) --no-manifest
	@ls -1 $(DIST)/CVE-202*.{html,mp4,wasm,ipk,jpg,mkv,bin,json} 2>/dev/null | wc -l \
		| xargs -I{} echo "[+] {} TV artifacts in $(DIST)/"

tv-report:
	@echo "=== network drivers (run against a live TV) ==="
	@grep -l "def exploit" $(EXPLOITS)/*.py | sed 's#$(EXPLOITS)/##;s#\.py##'

clean:
	rm -rf $(DIST)

help:
	@echo "make            build payloads + manifest + dirtypipe"
	@echo "make check      build + verify hashes + census + run smoke tests"
	@echo "make test       smoke tests only"
	@echo "make census     audit gates: no simulated code, no invented hosts"
	@echo "make verify     re-hash dist/ against manifest.json"
	@echo "make lock       regenerate committed $(LOCK)"
	@echo "make kernel     resolve offsets + compile-gate kernel exploits"
	@echo "make tv          build + count TV artifacts"
	@echo "make clean      remove dist/"
