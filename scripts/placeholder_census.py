#!/usr/bin/env python3
"""placeholder_census — the build-failing gate for simulated code.

The repo's rule is that no shipped module may claim a capability it did
not verify. That rule is only real if something enforces it, so this
census scans the production tree and fails on the patterns that mean
"not actually implemented":

  * ``TODO()`` / ``FIXME()`` calls
  * ``raise NotImplementedError`` and friends
  * a function body that is only ``...`` (the roadmap's marker for a
    scaffold that was never filled in)
  * invented hosts: ``*.example.com``, ``*.example.org``,
    ``api.<name>.test`` and other reserved-for-documentation names
  * a literal that marks itself as simulated: ``"simulated": True``,
    ``"fake": True``, ``"placeholder": True``
  * a function whose whole body is ``pass`` — a stub that answers
    nothing

The scan parses the source with ``ast``, so prose in comments and
docstrings is not a finding: a module that *documents* that it has no
fake entries is not the same as a module that *has* fake entries.

  python scripts/placeholder_census.py            # report and exit non-zero
  python scripts/placeholder_census.py --report   # report only

Exit code 0 means the production tree is clean.

Authorized engagements / lab work only.
"""
from __future__ import annotations

import argparse
import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The production trees the census covers.
PRODUCTION_ROOTS = [
    os.path.join("src", "quantum"),
    "agents",
    "quantum_cli.py",
]

#: Directories that never hold production code.
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "build", "out",
             "dist", ".mimosa", ".pytest_cache", "site-packages"}

#: The oldest Python the project supports (requirements.txt says 3.9+).
#: A production file that only parses on a newer interpreter breaks every
#: supported runtime, so the census parses with this version too.
MIN_PYTHON = (3, 9)

#: Hosts reserved for documentation - never a real service.
PLACEHOLDER_HOST_PATTERNS = [
    re.compile(r"^(?:[a-z0-9-]+\.)*example\.(?:com|org|net)$", re.I),
    re.compile(r"^(?:[a-z0-9-]+\.)*[^/]*\.test$", re.I),
    re.compile(r"^(?:[a-z0-9-]+\.)*invalid$", re.I),
    re.compile(r"^example$", re.I),
]

#: Dict keys that mark a literal as simulated.
SIMULATED_KEYS = ("simulated", "fake", "placeholder", "mocked", "stubbed")

#: A function whose body is only these is a stub.
STUB_BODY = (ast.Pass,)

#: Files allowed to contain the patterns above, with a reason.
#: Each entry is (path relative to the repo root, reason).
ALLOWLIST = [
    # protocol/abstract declarations: the body is intentionally empty and
    # the class documents the contract
    ("agents/specialized/ChainedZeroDay/chained_zero_day.py",
     "abstract contract methods"),
]

#: Functions whose empty body is correct: they override a base-class hook
#: that is documented to do nothing by default. http.server's
#: BaseHTTPRequestHandler.log_message is the canonical case - the
#: override silences the default stderr access log, so an empty body is
#: the intended behaviour and not a stub.
NO_OP_OVERRIDES = {
    "log_message": "http.server access-log override; an empty body is the "
                   "documented way to silence the default log",
    "log_request": "http.server request-log override",
    "log_error": "http.server error-log override",
    "handle_one_request": "http.server dispatch override",
    "verify_request": "ssl.SSLContext verification hook",
    "server_bind": "socketserver bind hook",
}


def _host_of(url):
    """The host part of a URL, without the scheme, port or path."""
    rest = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", url)
    rest = rest.split("/", 1)[0]
    rest = rest.split("?", 1)[0]
    if "@" in rest:
        rest = rest.rsplit("@", 1)[1]
    if rest.startswith("["):            # IPv6 literal
        return rest.split("]", 1)[0] + "]"
    return rest.split(":", 1)[0]


def _is_placeholder_host(url):
    """True when a URL points at a documentation-only host."""
    host = _host_of(url)
    if not host:
        return False
    for pattern in PLACEHOLDER_HOST_PATTERNS:
        if pattern.match(host):
            return True
    return False


def _docstring_nodes(tree):
    """The string constants that are docstrings (not real string values)."""
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and \
                    isinstance(first.value, ast.Constant) and \
                    isinstance(first.value.value, str):
                docs.add(id(first.value))
    return docs


class Finding:
    """One census finding."""

    __slots__ = ("path", "line", "kind", "detail")

    def __init__(self, path, line, kind, detail):
        self.path = path
        self.line = line
        self.kind = kind
        self.detail = detail

    def __str__(self):
        return "%s:%d  [%s] %s" % (self.path, self.line, self.kind,
                                    self.detail)


def _walk_files():
    """Every production source file, relative to the repo root."""
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


def _scan_python(rel_path, source, tree, findings):
    """Find the simulated-code patterns in one parsed file."""
    docs = _docstring_nodes(tree)
    allowed = any(rel_path == path for path, _reason in ALLOWLIST)

    for node in ast.walk(tree):
        # TODO() / FIXME()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("TODO", "FIXME", "todo", "fixme"):
            if not allowed:
                findings.append(Finding(rel_path, node.lineno, "todo-call",
                                        "%s() left in a production path"
                                        % node.func.id))
        # raise NotImplementedError
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            name = None
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                name = exc.func.id
            elif isinstance(exc, ast.Name):
                name = exc.id
            if name and name.startswith("NotImplemented"):
                if not allowed:
                    findings.append(Finding(
                        rel_path, node.lineno, "not-implemented",
                        "raise %s in a production path" % name))
        # a body that is only `...`
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # drop the docstring, keep everything else
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr) and
                            isinstance(n.value, ast.Constant) and
                            isinstance(n.value.value, str))]
            if len(body) == 1 and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    body[0].value.value is Ellipsis:
                if not allowed:
                    findings.append(Finding(
                        rel_path, node.lineno, "ellipsis-body",
                        "%s() is an unimplemented scaffold" % node.name))
        # a function whose whole body is `pass`
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr) and
                            isinstance(n.value, ast.Constant) and
                            isinstance(n.value.value, str))]
            if body and all(isinstance(n, ast.Pass) for n in body):
                if not allowed and node.name not in NO_OP_OVERRIDES:
                    findings.append(Finding(
                        rel_path, node.lineno, "pass-body",
                        "%s() has an empty body" % node.name))
        # dict literals that mark themselves simulated
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if not isinstance(key, ast.Constant) or \
                        not isinstance(key.value, str):
                    continue
                if key.value.lower() in SIMULATED_KEYS and \
                        isinstance(value, ast.Constant) and value.value is True:
                    if not allowed:
                        findings.append(Finding(
                            rel_path, node.lineno, "simulated-literal",
                            '"%s": True marks a literal as simulated'
                            % key.value))
        # invented hosts in real string values
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docs:
            for url in re.findall(r"https?://[^\s\"'`)\]}]+",
                                    node.value):
                if _is_placeholder_host(url) and not allowed:
                    findings.append(Finding(
                        rel_path, node.lineno, "placeholder-host",
                        "%s points at a documentation-only host" % url))


def _scan_text(rel_path, source, findings):
    """Find the patterns in a non-Python source (Kotlin / Java)."""
    for i, line in enumerate(source.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*") or \
                stripped.startswith("/*"):
            continue
        if re.search(r"\bTODO\s*\(\s*\)", line):
            findings.append(Finding(rel_path, i, "todo-call",
                                    "TODO() left in a production path"))
        if "NotImplementedError" in line:
            findings.append(Finding(rel_path, i, "not-implemented",
                                    "NotImplementedError in a production path"))
        for url in re.findall(r"https?://[^\s\"'`)\]}]+", line):
            if _is_placeholder_host(url):
                findings.append(Finding(rel_path, i, "placeholder-host",
                                        "%s points at a documentation-only "
                                        "host" % url))


def census():
    """Run the census. Returns the findings."""
    findings = []
    for rel_path in _walk_files():
        full = os.path.join(ROOT, rel_path)
        try:
            source = open(full, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if rel_path.endswith(".py"):
            try:
                tree = ast.parse(source, filename=rel_path)
            except SyntaxError as exc:
                findings.append(Finding(rel_path, exc.lineno or 0,
                                        "syntax-error", str(exc)))
                continue
            # The project supports Python 3.9+ (requirements.txt), so the
            # file must parse under 3.9 too. feature_version makes the
            # parser reject newer grammar.
            try:
                ast.parse(source, filename=rel_path,
                          feature_version=MIN_PYTHON)
            except SyntaxError as exc:
                findings.append(Finding(
                    rel_path, exc.lineno or 0, "unsupported-syntax",
                    "%s — this needs Python %d.%d or newer"
                    % (exc.msg, MIN_PYTHON[0], MIN_PYTHON[1])))
                continue
            # PEP 701 relaxed f-strings in 3.12: a backslash inside a
            # replacement field is legal there and a SyntaxError before
            # it, so the module would not import on a supported runtime.
            for node in ast.walk(tree):
                if not isinstance(node, ast.FormattedValue):
                    continue
                segment = ast.get_source_segment(source, node.value) or ""
                if "\\" in segment:
                    findings.append(Finding(
                        rel_path, node.lineno, "unsupported-syntax",
                        "f-string expression contains a backslash "
                        "(%s) — that needs Python 3.12 or newer"
                        % segment.strip()[:60]))
            _scan_python(rel_path, source, tree, findings)
        else:
            _scan_text(rel_path, source, findings)
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(prog="placeholder_census")
    ap.add_argument("--report", action="store_true",
                    help="print the findings but always exit 0")
    args = ap.parse_args()

    findings = census()
    if not findings:
        print("[PASS] placeholder census: the production tree is clean "
              "(no TODO(), no NotImplementedError, no invented hosts, no "
              "simulated literals, no stub bodies)")
        return 0

    print("[FAIL] placeholder census: %d finding(s) in the production tree"
          % len(findings))
    for f in findings:
        print("   ", f)
    if args.report:
        return 0
    print()
    print("These are the patterns that mean a shipped module claims a "
          "capability it does not have.")
    print("Fix the production code, or add the path to ALLOWLIST in "
          "scripts/placeholder_census.py with a reason.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
