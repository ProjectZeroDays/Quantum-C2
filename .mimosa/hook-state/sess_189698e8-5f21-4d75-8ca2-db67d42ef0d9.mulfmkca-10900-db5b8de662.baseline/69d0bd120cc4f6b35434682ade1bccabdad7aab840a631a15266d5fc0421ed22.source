#!/bin/bash
cd "/c/Projects/Quantum CLI"
rm -f logs/mitre_map.json logs/decisions.jsonl
python quantum_cli.py --no-ai --cycles 3 --camera-only --scope 127.0.0.0/29 > /tmp/f3b.txt 2>&1
echo "rc=$?"
echo "decisions=$(wc -l < logs/decisions.jsonl)"
echo "mitre_map=$(test -f logs/mitre_map.json && echo YES || echo NO)"
echo "fatal_count=$(grep -c fatal /tmp/f3b.txt)"
tail -2 /tmp/f3b.txt
