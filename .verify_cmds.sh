#!/bin/bash
# TASK 2 verification: run every choices= command with a 10s timeout each.
cd "/c/Projects/Quantum CLI"
T=tests/_cmdlist_results.txt
: > "$T"
run_cmd() {
  local label="$1"; shift
  timeout 10 python quantum_cli.py "$@" > /tmp/cmd_out.txt 2>&1
  local rc=$?
  local tb=$(grep -c Traceback /tmp/cmd_out.txt)
  echo "[$label] rc=$rc tracebacks=$tb" >> "$T"
  if [ "$tb" != "0" ]; then echo "--- $label traceback ---" >> "$T"; head -15 /tmp/cmd_out.txt >> "$T"; fi
}
run_cmd serve serve
run_cmd foxacid foxacid
run_cmd quantum quantum -t 127.0.0.1
run_cmd recon recon -t 127.0.0.1
run_cmd osint osint -t example.com
run_cmd auto auto -t 127.0.0.1
run_cmd dohc2 dohc2
run_cmd icmp icmp
run_cmd trinity trinity
run_cmd camwar camwar -c 127.0.0.0/29
run_cmd cams cams -c 127.0.0.0/29
run_cmd wifi wifi
run_cmd triage triage
run_cmd mfp mfp
run_cmd pcap pcap -f /nonexistent.pcap
run_cmd camshot camshot -t 127.0.0.1
run_cmd router router -t 127.0.0.1
run_cmd worm worm -t 127.0.0.1
run_cmd episcribe episcribe -t 127.0.0.1
run_cmd cottonmouth cottonmouth -t 127.0.0.1
run_cmd validator validator -t 127.0.0.1
run_cmd tor tor
run_cmd seal seal
run_cmd unseal unseal
run_cmd brute brute -t 127.0.0.1
run_cmd phish phish -t ops@example.com
run_cmd keygen keygen
run_cmd deployai deployai
run_cmd zerologon zerologon -dc-ip 127.0.0.1 -dc-name dc1
run_cmd mitre mitre
run_cmd federation federation
run_cmd posixagent posixagent
run_cmd zerocheck zerocheck -t 127.0.0.1
run_cmd mshtmaldoc mshtmaldoc
run_cmd flashfill flashfill
run_cmd emoji emoji
run_cmd macreset macreset
run_cmd keylog keylog
run_cmd wipe wipe
run_cmd persist persist
run_cmd ghostdns ghostdns --domain example.com
run_cmd cagebreak cagebreak
rm -rf /c/Users/.qcli_flash 2>/dev/null
echo "=== cleanup done ==="
cat "$T"
