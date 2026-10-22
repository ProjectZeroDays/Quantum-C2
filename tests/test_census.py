#!/usr/bin/env python3
"""Contract tests for the two standing censuses.

The censuses are the build-failing gates that make the repo's "no
simulated code" rule structural. A gate that does not fire is worse
than no gate, so each one is checked against a fixture that must fail
and one that must pass.
"""
import json
import os
import subprocess
import sys
import tempfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
PLACEHOLDER = os.path.join(SCRIPTS, "placeholder_census.py")
ENDPOINT = os.path.join(SCRIPTS, "endpoint_census.py")


def _run(script, args=()):
    return subprocess.run([sys.executable, script] + list(args),
                          capture_output=True, text=True, timeout=300,
                          cwd=ROOT)


# ---- the production tree is clean ---------------------------------------

def test_placeholder_census_passes_on_the_production_tree():
    proc = _run(PLACEHOLDER)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert "[PASS]" in proc.stdout


def test_endpoint_census_passes_on_the_production_tree():
    proc = _run(ENDPOINT)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert "[PASS]" in proc.stdout


# ---- each gate must actually fire --------------------------------------

def test_placeholder_census_detects_the_patterns():
    """A file with each pattern must be reported."""
    sys.path.insert(0, SCRIPTS)
    import placeholder_census as pc

    fixtures = {
        "todo-call": "def f():\n    TODO()\n",
        "not-implemented": "def f():\n    raise NotImplementedError\n",
        "ellipsis-body": "def f():\n    ...\n",
        "pass-body": "def f():\n    pass\n",
        "simulated-literal": "def f():\n    return {'simulated': True}\n",
        "placeholder-host": "def f():\n    return 'https://api.example.com/x'\n",
    }
    for kind, source in fixtures.items():
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mod.py")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(source)
            tree = __import__("ast").parse(source)
            findings = []
            pc._scan_python("mod.py", source, tree, findings)
            assert findings, "%s was not detected" % kind
            assert any(f.kind == kind for f in findings), \
                "%s: got %s" % (kind, [f.kind for f in findings])


def test_placeholder_census_ignores_prose():
    """A module that documents the rule must not be a finding."""
    sys.path.insert(0, SCRIPTS)
    import ast
    import placeholder_census as pc

    source = ('"""This module has no fake entries and no placeholder '
              'values."""\n'
              'def f():\n'
              '    # never a mock, never a stub\n'
              '    return {"note": "no fake entries"}\n')
    tree = ast.parse(source)
    findings = []
    pc._scan_python("mod.py", source, tree, findings)
    assert not findings, [str(f) for f in findings]


def test_placeholder_census_allows_a_documented_no_op_override():
    """http.server's log_message is empty on purpose."""
    sys.path.insert(0, SCRIPTS)
    import ast
    import placeholder_census as pc

    source = ("class H(BaseHTTPRequestHandler):\n"
              "    def log_message(self, fmt, *args):\n"
              "        pass\n")
    tree = ast.parse(source)
    findings = []
    pc._scan_python("mod.py", source, tree, findings)
    assert not findings, [str(f) for f in findings]


def test_endpoint_census_detects_an_invented_host():
    """A host nobody can resolve must be reported."""
    sys.path.insert(0, SCRIPTS)
    import endpoint_census as ec

    assert ec._is_reserved("api.my-invented-service.invalid")
    assert ec._is_reserved("example.com")
    assert ec._is_reserved("proxy.local")
    assert not ec._is_reserved("github.com")
    assert ec._is_private("127.0.0.1")
    assert ec._is_private("192.168.1.10")
    assert ec._is_private("169.254.169.254")
    assert not ec._is_private("github.com")


def test_endpoint_census_classifies_the_manifest():
    """Every host in the manifest must be recognised as catalogued."""
    sys.path.insert(0, SCRIPTS)
    import endpoint_census as ec

    catalogued, runtime, example = ec._manifest()
    assert catalogued, "the manifest is empty"
    assert "github.com" in catalogued
    assert "127.0.0.1" in runtime
    assert "attacker.com" in example


def test_endpoint_manifest_has_no_duplicate_hosts():
    """A host in two families would make the manifest ambiguous."""
    with open(os.path.join(SCRIPTS, "endpoint_manifest.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    seen = {}
    for family, hosts in data["families"].items():
        for host in hosts:
            assert host not in seen, "%s is in %s and %s" % (host, seen.get(host), family)
            seen[host] = family
    for host in data.get("runtime", []):
        assert host not in seen, "%s is both runtime and catalogued" % host
    for host in data.get("example_only", []):
        assert host not in seen, "%s is both example-only and catalogued" % host


# ---- the gates must fire end to end -------------------------------------

PROBE = os.path.join(ROOT, "src", "quantum", "ops", "__census_probe__.py")


def _with_probe(source, script):
    """Write a violating file, run the census, remove the file."""
    with open(PROBE, "w", encoding="utf-8") as fh:
        fh.write(source)
    try:
        return _run(script)
    finally:
        if os.path.exists(PROBE):
            os.remove(PROBE)


def test_placeholder_gate_fires_on_a_simulated_literal():
    """A simulated literal in a production file must fail the gate."""
    proc = _with_probe(
        'def probe():\n    return {"simulated": True}\n', PLACEHOLDER)
    assert proc.returncode == 1, proc.stdout[-1500:]
    assert "simulated-literal" in proc.stdout


def test_placeholder_gate_fires_on_a_placeholder_host():
    """A documentation-only host must fail the gate."""
    proc = _with_probe(
        'def probe():\n    return "https://api.example.com/x"\n', PLACEHOLDER)
    assert proc.returncode == 1
    assert "placeholder-host" in proc.stdout


def test_endpoint_gate_fires_on_an_invented_host():
    """A host nobody can resolve must fail the gate."""
    proc = _with_probe(
        'def probe():\n    return "https://api.my-invented-service.invalid/x"\n',
        ENDPOINT)
    assert proc.returncode == 1, proc.stdout[-1500:]
    assert "my-invented-service.invalid" in proc.stdout


def test_gates_pass_once_the_probe_is_removed():
    """The gates must be green again once the violation is gone."""
    for script in (PLACEHOLDER, ENDPOINT):
        proc = _run(script)
        assert proc.returncode == 0, proc.stdout[-1500:]
