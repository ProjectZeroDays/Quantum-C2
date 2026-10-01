"""Tests for the persistent DoH reverse channel (ghostdns hardening).

All network calls are faked at the module boundary — no live resolvers are
touched. End-to-end operation against a live DoH resolver still requires a
live target (stated in the class docstring).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import pytest  # noqa: E402

from quantum.c2.agents import ghostdns as G  # noqa: E402


def test_backoff_grows_exponentially_and_caps():
    # attempt 1 -> base, attempt 4 -> base * 2^3, attempt 20 -> capped
    assert G.backoff_seconds(1, base=2, cap=300, rand=lambda: 1.0) == 2.0
    assert G.backoff_seconds(4, base=2, cap=300, rand=lambda: 1.0) == 16.0
    assert G.backoff_seconds(20, base=2, cap=300, rand=lambda: 1.0) == 300.0
    # half-jitter floor: rand()=0 -> 50% of the raw backoff
    assert G.backoff_seconds(4, base=2, cap=300, rand=lambda: 0.0) == 8.0
    # never below the 0.5s floor
    assert G.backoff_seconds(0, base=0.1, cap=1, rand=lambda: 0.0) == 0.5


def _channel(tmp_path, **kw):
    return G.PersistentDoHChannel(
        "hq", "example.test", state_file=str(tmp_path / "state.json"), **kw)


def test_cycle_success_resets_attempt_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "doh_reverse_beacon",
                        lambda h, d, dom: {"beacon_bytes": 1, "chunks": 1})
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch = _channel(tmp_path)
    out = ch.cycle(data=b"hello")
    assert out["ok"] is True
    assert out["attempt"] == 0
    assert out["sleep"] == ch.interval
    state = json.loads(open(ch.state_file, encoding="utf-8").read())
    assert state["attempt"] == 0
    assert state["cycles"] == 1


def test_egress_failure_drives_backoff_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "doh_reverse_beacon",
                        lambda h, d, dom: {"error": "resolver down"})
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch = _channel(tmp_path, interval=60.0, max_backoff=300.0)
    out = ch.cycle(data=b"x")
    assert out["ok"] is False
    assert out["attempt"] == 1
    # failure never sleeps the full interval — it uses backoff (2..4s band)
    assert 0.5 <= out["sleep"] < 60.0
    state = json.loads(open(ch.state_file, encoding="utf-8").read())
    assert state["attempt"] == 1
    assert state["fails"] == 1
    assert state["last_fail"] is not None


def test_task_poll_outage_counts_even_without_egress(tmp_path, monkeypatch):
    def boom(domain, host_id="hq", errors="swallow"):
        raise RuntimeError("all 3 resolvers failed")
    monkeypatch.setattr(G, "doh_task_check", boom)
    ch = _channel(tmp_path)
    out = ch.cycle()
    assert out["ok"] is False
    assert "task_error" in out
    assert out["attempt"] == 1


def test_no_task_is_not_a_failure(tmp_path, monkeypatch):
    # None = task queue empty (healthy), distinct from a resolver outage
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch = _channel(tmp_path)
    out = ch.cycle()
    assert out["ok"] is True
    assert out["task"] is None


def test_state_survives_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "doh_reverse_beacon",
                        lambda h, d, dom: {"error": "down"})
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch1 = _channel(tmp_path)
    ch1.cycle(data=b"x")
    ch1.cycle(data=b"x")
    # fresh instance (simulated process restart) reads the same state file
    ch2 = _channel(tmp_path)
    assert ch2.state["attempt"] == 2
    assert ch2.state["fails"] == 2


def test_run_loop_honors_backoff_and_max_cycles(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "doh_reverse_beacon",
                        lambda h, d, dom: {"error": "down"})
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch = _channel(tmp_path, interval=60.0)
    sleeps = []
    last = ch.run(data_fn=lambda: b"tick", max_cycles=3,
                  sleep_fn=sleeps.append)
    assert last is not None
    # one sleep between each pair of cycles (the loop exits instead of
    # sleeping after the final cycle)
    assert len(sleeps) == 2
    # attempts climbed 1,2 -> backoff grows monotonically (with jitter
    # bounded inside each doubling band)
    assert sleeps[0] <= sleeps[1]
    # and no sleep ever exceeds the configured cap
    assert all(s <= ch.max_backoff for s in sleeps)


def test_run_loop_stops_via_stop_fn(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "doh_task_check",
                        lambda dom, host_id="hq", errors="swallow": None)
    ch = _channel(tmp_path)
    calls = {"n": 0}
    def stop():
        return calls["n"] >= 2
    orig = ch.cycle
    def counted(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)
    ch.cycle = counted
    sleeps = []
    ch.run(max_cycles=100, sleep_fn=sleeps.append, stop_fn=stop)
    assert calls["n"] <= 2  # stopped promptly, not the full 100


def test_doh_task_check_reraises_when_asked(monkeypatch):
    class FakeDoH:
        def resolve(self, *a, **k):
            raise RuntimeError("net down")
    monkeypatch.setattr(G, "DoH", lambda: FakeDoH())
    # swallow mode (default): returns None, never raises
    assert G.doh_task_check("example.test") is None
    # raise mode: propagates so the channel can count a failed cycle
    with pytest.raises(RuntimeError):
        G.doh_task_check("example.test", errors="raise")
