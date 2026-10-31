"""Accessibility audit — basic ARIA + contrast checks."""
import sys, os
html = ""
for root, dirs, files in os.walk("src/quantum/web"):
    for f in files:
        if f.endswith(".html"):
            with open(os.path.join(root, f)) as fh: html += fh.read()
checks = 0
if not 'role=' in html or 'aria-' not in html:
    print("WARNING: insufficient ARIA attributes"); checks += 1
if 'tabindex' not in html:
    print("WARNING: no keyboard focus indicators"); checks += 1
if errors := sum(1 for c in ['high', 'low'] if c not in html):
    print("WARNING: insufficient contrast info"); checks += 1
print(f"Accessibility checks: {len(checks)} warning(s)")
