#!/usr/bin/env python3
"""CVE-2023-32233 (nf_tables use-after-free) - authorized-lab local privesc deploy.

Kernel-range gate (5.5-6.3, per the registry convention) plus a live
liveness probe: in a forked child inside fresh user+net namespaces the
launcher performs a real nfnetlink batch (NEWTABLE + DELTABLE) over
NETLINK_NETFILTER, proving the vulnerable subsystem is reachable and
writable for an unprivileged user - the exact precondition the public
exploit chain requires. Outside the range (or non-Linux / unreachable
subsystem) the launcher returns a clean check-only result.
"""
import argparse
import ctypes
import json
import os
import platform
import re
import socket
import struct
import sys

CVE = "CVE-2023-32233"
LO, HI = (5, 5), (6, 3)
CLONE_NEWUSER = 0x10000000
CLONE_NEWNET = 0x40000000
NETLINK_NETFILTER = 12
NFNL_SUBSYS_NFTABLES = 10
NFT_MSG_NEWTABLE = 0
NFT_MSG_DELTABLE = 2
NFT_MSG_BATCH_BEGIN = 16
NFT_MSG_BATCH_END = 17
NFTA_TABLE_NAME = 1
NLM_F_REQUEST = 0x01
NLM_F_ACK = 0x04
NLM_F_CREATE = 0x400
TABLE = "qcli32233"


def _kernel_release():
    m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", platform.release())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def _nlattr(tp, payload, nested=False):
    if nested:
        tp |= 0x8000
    pad = (-len(payload)) % 4
    return struct.pack("<HH", 4 + len(payload) + pad, tp) + payload + b"\x00" * pad


def _nlmsg(tp, flags, seq, payload):
    out = struct.pack("<IHHII", 16 + len(payload), tp, flags, seq, 0) + payload
    return out + b"\x00" * ((-len(out)) % 4)


def _nfgen(family=2, res_id=0):
    return struct.pack("<BBH", family, 0, res_id)


def _build_batch():
    seq = 1
    batch = _nlmsg(NFT_MSG_BATCH_BEGIN, NLM_F_REQUEST, seq, _nfgen(0, socket.htons(NFNL_SUBSYS_NFTABLES)))
    seq += 1
    name = _nlattr(NFTA_TABLE_NAME, TABLE.encode() + b"\x00")
    batch += _nlmsg((NFNL_SUBSYS_NFTABLES << 8) | NFT_MSG_NEWTABLE,
                   NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE, seq, _nfgen() + name)
    seq += 1
    batch += _nlmsg((NFNL_SUBSYS_NFTABLES << 8) | NFT_MSG_DELTABLE,
                   NLM_F_REQUEST | NLM_F_ACK, seq, _nfgen() + name)
    seq += 1
    batch += _nlmsg(NFT_MSG_BATCH_END, NLM_F_REQUEST, seq, _nfgen(0, socket.htons(NFNL_SUBSYS_NFTABLES)))
    return batch


def _write(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)


def _probe_child(report_fd):
    """Forked child: userns+netns, then NEWTABLE+DELTABLE over netlink."""
    report = {}
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.unshare.argtypes = [ctypes.c_int]
        libc.unshare.restype = ctypes.c_int
        if libc.unshare(CLONE_NEWUSER) != 0:
            report["error"] = "unshare(CLONE_NEWUSER) failed: errno %d" % ctypes.get_errno()
            os.write(report_fd, json.dumps(report).encode())
            os._exit(3)
        _write("/proc/self/setgroups", "deny")
        _write("/proc/self/uid_map", "0 %d 1\n" % os.getuid())
        _write("/proc/self/gid_map", "0 %d 1\n" % os.getgid())
        if libc.unshare(CLONE_NEWNET) != 0:
            report["error"] = "unshare(CLONE_NEWNET) failed: errno %d" % ctypes.get_errno()
            os.write(report_fd, json.dumps(report).encode())
            os._exit(4)

        sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_NETFILTER)
        sock.settimeout(4)
        addr = (socket.AF_NETLINK, 0, 0)  # pid 0 = kernel
        sock.bind((socket.AF_NETLINK, 0, 0))
        sock.sendto(_build_batch(), addr)
        data, _ = sock.recvfrom(8192)
        # parse NLMSG_ERROR entries; the batch ACKs carry error == 0 on success
        netlink_error = None
        off = 0
        while off + 16 <= len(data):
            nlmsg_len, nlmsg_type, _, _, _ = struct.unpack_from("<IHHII", data, off)
            if nlmsg_len < 16 or nlmsg_len > len(data) - off:
                break
            if nlmsg_type == 2:  # NLMSG_ERROR
                err = struct.unpack_from("<i", data, off + 16)[0]
                if err != 0:
                    netlink_error = err
            off += (nlmsg_len + 3) & ~3
        sock.close()
        if netlink_error is not None:
            report["error"] = "nfnetlink batch rejected: errno %d" % netlink_error
        else:
            report["nft_netlink"] = True
            report["ok"] = True
        os.write(report_fd, json.dumps(report).encode())
        os._exit(0)
    except Exception as exc:
        report["error"] = "%s: %s" % (type(exc).__name__, exc)
        try:
            os.write(report_fd, json.dumps(report).encode())
        except OSError:
            pass
        os._exit(5)


def run(args):
    maj, minr, patch = _kernel_release()
    linux = sys.platform.startswith("linux")
    result = {
        "cve": CVE,
        "target": "local",
        "vulnerable": False,
        "verified_by": None,
        "kernel": "%d.%d.%d" % (maj, minr, patch),
        "platform": sys.platform,
        "in_range": linux and LO <= (maj, minr) <= HI,
        "nft_netlink": False,
        "userns": False,
        "error": None,
    }
    if not linux:
        result["error"] = "check-only: not Linux"
        return result
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        result["error"] = "already root (chain expects an unprivileged user)"
        result["vulnerable"] = None
        return result
    if not result["in_range"]:
        result["error"] = ("check-only: kernel %s outside the vulnerable 5.5-6.3 range"
                           % result["kernel"])
        return result
    if args.check_only:
        result["error"] = "check-only requested"
        return result

    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        _probe_child(write_fd)
        os._exit(9)
    os.close(write_fd)
    chunks = b""
    try:
        while True:
            chunk = os.read(read_fd, 65536)
            if not chunk:
                break
            chunks += chunk
        _, status = os.waitpid(pid, 0)
        exitcode = os.waitstatus_to_exitcode(status)
    finally:
        os.close(read_fd)

    probe = {}
    if chunks:
        try:
            probe = json.loads(chunks.decode("utf-8", "replace"))
        except ValueError:
            probe = {"raw": chunks.decode("utf-8", "replace")[:500]}
    probe["child_exit"] = exitcode
    result["userns"] = "unshare" not in (probe.get("error") or "")
    result["nft_netlink"] = bool(probe.get("nft_netlink"))

    if probe.get("ok"):
        result["vulnerable"] = True
        result["verified_by"] = ("vulnerable kernel range + unprivileged nftables "
                                "netlink write access confirmed (anonymous-set UAF "
                                "chain preconditions present)")
    else:
        result["error"] = probe.get("error") or "probe failed"
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2023-32233 nf_tables UAF authorized-lab deploy")
    p.add_argument("--check-only", action="store_true",
                   help="report kernel range only; do not probe")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:  # defensive: deploy must never crash the operator console
        result = {"cve": CVE, "target": "local", "vulnerable": False,
                  "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    if result.get("vulnerable") is None:
        return 0
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
