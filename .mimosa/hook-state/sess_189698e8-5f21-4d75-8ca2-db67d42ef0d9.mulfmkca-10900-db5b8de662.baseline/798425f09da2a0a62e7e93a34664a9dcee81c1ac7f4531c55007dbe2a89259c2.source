#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QUANTUM-CLI V4 — thin launcher.

The single-file V3.1 spec is archived at dist/quantum-cli-v3.1-single.py;
this launcher imports the behavior-identical src/quantum/ package.
`python quantum_cli.py camwar -c 10.0.0.0/24` behaves identically to the spec.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from quantum import *  # noqa: F401,F403 — full API re-export (spec parity)
from quantum import __version__  # noqa: F401
from quantum.__main__ import camera_console, main, menu  # noqa: F401

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
