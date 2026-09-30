"""test_registry — every weapon string in ZERO_DAY_REGISTRY resolves to a
callable via registry.fire(cve, ip, params). Never weaken a check to pass:
if this fails, the production code is wrong.
"""
import quantum_cli as q


def test_registry_has_entries():
    assert len(q.ZERO_DAY_REGISTRY) >= 25


def test_every_weapon_string_resolves_and_fires():
    import os
    for cve in q.ZERO_DAY_REGISTRY:
        entry = q.ZERO_DAY_REGISTRY[cve]
        if "folder" in entry:
            # folder weapon: exploit_payloads/<folder>/deploy.py must exist
            d = os.path.join("exploit_payloads", entry["folder"])
            assert os.path.isfile(os.path.join(d, "deploy.py")), \
                f"{cve}: folder weapon {entry['folder']!r} has no deploy.py"
        else:
            assert isinstance(entry["weapon"], str), cve
            assert callable(q.resolve_weapon(entry["weapon"])), \
                f"{cve}: weapon {entry['weapon']!r} does not resolve to a callable"
        res = q.registry.fire(cve, "127.0.0.1", {})
        assert isinstance(res, dict), f"{cve}: fire() returned {type(res)}"
        assert "status" in res or "error" in res or "cve" in res, cve


def test_fire_never_raises_on_unreachable_target():
    for cve in q.ZERO_DAY_REGISTRY:
        res = q.registry.fire(cve, "192.0.2.99", {"timeout": 0.1})
        assert isinstance(res, dict)


def test_unknown_cve_raises_keyerror():
    try:
        q.registry.fire("CVE-0000-0000", "127.0.0.1", {})
    except KeyError:
        pass
    else:
        raise AssertionError("unknown CVE must raise KeyError")


def test_qbrain_plan_attack_returns_registry_cve():
    recon = {"ports": [445], "smb": {"domain": "x"}}
    cve = q.QBrain.plan_attack(recon)
    assert cve in q.ZERO_DAY_REGISTRY, f"{cve} not in registry"


def test_qbrain_plan_attack_empty_recon():
    cve = q.QBrain.plan_attack({})
    assert cve in q.ZERO_DAY_REGISTRY
