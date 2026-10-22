#!/usr/bin/env python3
"""endpoint_census — the build-failing gate for invented endpoints.

Extracts every outbound URL from the production tree and classifies the
host it names:

  runtime      a loopback, private or link-local address the code may
               legitimately name
  templated    an interpolated host (the f-string builds it at runtime)
  example      a host that only appears while documenting the shape of a
               request
  catalogued   a host listed in scripts/endpoint_manifest.json, with
               the API family it belongs to
  invented     anything else — a host nobody can resolve, or one that
               is reserved for documentation

An invented host fails the build. That is the point of the census: a
module cannot ship a capability that points at a service that does not
exist.

  python scripts/endpoint_census.py            # report and exit non-zero
  python scripts/endpoint_census.py --report   # report only

Exit code 0 means every outbound host in the production tree is
accounted for.

Authorized engagements / lab work only.
"""
from __future__ import annotations

import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The production trees the census covers.
PRODUCTION_ROOTS = [
    os.path.join("src", "quantum"),
    os.path.join("agents", "specialized"),
    os.path.join("agents", "build"),
    "quantum_cli.py",
]

SKIP_DIRS = {"__pycache__", ".git", "node_modules", "build", "out",
             "dist", ".mimosa", ".pytest_cache", "site-packages"}

#: Hosts reserved for documentation — never a real service.
RESERVED_TLDS = {
    "example", "example.com", "example.org", "example.net", "invalid",
    "local", "localhost.localdomain", "test",
}

#: A host that is a documentation-only name.
RESERVED_SUFFIXES = (".example", ".example.com", ".example.org",
                      ".example.net", ".invalid", ".local", ".test")

#: A URL that documents the shape of a request rather than being called.
EXAMPLE_MARKERS = ("example", "attacker", "public-proxy", "placeholder",
                   "sample", "yourdomain", "your-host", "changeme")

_URL = re.compile(r"https?://([^\s\"'`)\]}<>]+)")


def _manifest():
    path = os.path.join(ROOT, "scripts", "endpoint_manifest.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    families = data.get("families", {})
    catalogued = {}
    for family, hosts in families.items():
        for host in hosts:
            catalogued[host.lower()] = family
    runtime = {h.lower() for h in data.get("runtime", [])}
    example = {h.lower() for h in data.get("example_only", [])}
    return catalogued, runtime, example


def _host_of(url):
    rest = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", url)
    rest = rest.split("/", 1)[0].split("?", 1)[0]
    if "@" in rest:
        rest = rest.rsplit("@", 1)[1]
    if rest.startswith("["):
        return rest.split("]", 1)[0] + "]"
    return rest.split(":", 1)[0].lower()


def _is_ip(host):
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)) or \
        host.startswith("[") or ":" in host


def _is_private(host):
    """True for a loopback, private or link-local address."""
    if host in ("localhost", "0.0.0.0", "::1", "::"):
        return True
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", host)
    if not m:
        return False
    a, b = int(m.group(1)), int(m.group(2))
    if a == 127 or a == 0:
        return True
    if a == 10:
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 169 and b == 254:
        return True
    return False


def _is_templated(host):
    return any(ch in host for ch in "{}$%")


def _is_example(host, url):
    low = url.lower()
    if any(marker in low for marker in EXAMPLE_MARKERS):
        return True
    return False


def _is_reserved(host):
    if host in RESERVED_TLDS:
        return True
    for suffix in RESERVED_SUFFIXES:
        if host == suffix.lstrip(".") or host.endswith(suffix):
            return True
    return False


def _walk_files():
    for entry in PRODUCTION_ROOTS:
        path = os.path.join(ROOT, entry)
        if os.path.isfile(path):
            yield entry
            continue
        if not os.path.isdir(path):
            continue
        for base, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if name.endswith((".py", ".kt", ".java")):
                    full = os.path.join(base, name)
                    yield os.path.relpath(full, ROOT).replace("\\", "/")


def census():
    """Classify every host. Returns (findings, counts)."""
    catalogued, runtime, example = _manifest()
    findings = []
    counts = {"runtime": 0, "templated": 0, "example": 0, "catalogued": 0,
              "invented": 0}
    seen = set()

    for rel_path in _walk_files():
        full = os.path.join(ROOT, rel_path)
        try:
            source = open(full, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            for url in _URL.findall(line):
                host = _host_of(url)
                if not host:
                    continue
                key = (host, rel_path, i)
                if key in seen:
                    continue
                seen.add(key)

                if _is_templated(host):
                    counts["templated"] += 1
                elif _is_private(host) or host in runtime:
                    counts["runtime"] += 1
                elif _is_example(host, url) or host in example:
                    counts["example"] += 1
                elif host in catalogued:
                    counts["catalogued"] += 1
                elif _is_reserved(host):
                    counts["invented"] += 1
                    findings.append((rel_path, i, host,
                                     "reserved for documentation — it is not "
                                     "a real service"))
                elif _is_ip(host):
                    counts["runtime"] += 1
                else:
                    counts["invented"] += 1
                    findings.append((rel_path, i, host,
                                     "not in the endpoint manifest and not a "
                                     "runtime address"))
    return findings, counts


def main() -> int:
    ap = argparse.ArgumentParser(prog="endpoint_census")
    ap.add_argument("--report", action="store_true",
                    help="print the findings but always exit 0")
    args = ap.parse_args()

    findings, counts = census()
    print("endpoint census:")
    for kind in ("catalogued", "runtime", "templated", "example", "invented"):
        print("  %-11s %5d" % (kind, counts[kind]))
    if not findings:
        print("[PASS] every outbound host in the production tree is "
              "accounted for")
        return 0

    print()
    print("[FAIL] %d invented host(s):" % len(findings))
    for rel_path, line, host, why in findings:
        print("   %s:%d  %s  (%s)" % (rel_path, line, host, why))
    if args.report:
        return 0
    print()
    print("An invented host means a shipped module points at a service "
          "that does not exist.")
    print("Point it at a real endpoint, or add the family to "
          "scripts/endpoint_manifest.json.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
