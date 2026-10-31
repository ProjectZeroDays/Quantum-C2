#!/usr/bin/env python3
"""Build .deb package — requires Linux host with dpkg."""
# Not verified on Windows; requires Linux build VM per AGENTS.md auth rules.
import subprocess, sys, os
print(".deb script: requires dpkg/alien; documented limitation only — not run against real package")