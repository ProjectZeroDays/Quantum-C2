#!/bin/bash
cd "/c/Projects/Quantum CLI"
echo "=== FACEOFF 1: import silent ==="
python -c "import quantum_cli" 2>/tmp/f1.txt; rc=$?
OUT=$(cat /tmp/f1.txt)
echo "rc=$rc output_len=${#OUT}"

echo "=== FACEOFF 2: menu + 0 ==="
echo 0 | python quantum_cli.py --menu > /tmp/f2.txt 2>&1
echo "rc=$? tracebacks=$(grep -c Traceback /tmp/f2.txt)"

echo "=== FACEOFF 3: no-AI autonomy 3 cycles ==="
rm -f logs/mitre_map.json logs/decisions.jsonl
python quantum_cli.py --no-ai --cycles 3 --camera-only --scope 127.0.0.0/29 > /tmp/f3.txt 2>&1
echo "rc=$?"
echo "decisions=$(wc -l < logs/decisions.jsonl 2>/dev/null || echo 0)"
echo "mitre_map_exists=$(test -f logs/mitre_map.json && echo YES || echo NO)"
grep -c Traceback /tmp/f3.txt || echo "no tracebacks"

echo "=== FACEOFF 6: WSGI serve + curl /dash ==="
python quantum_cli.py serve > /tmp/f6s.txt 2>&1 &
SPID=$!
sleep 10
CODE=$(curl -s -o /tmp/dash.html -w "%{http_code}" http://127.0.0.1:8443/dash)
echo "dash_http=$CODE"
grep -c QUANTUMDASH /tmp/dash.html || echo "no dashboard html"
KILL=$(curl -s -X POST http://127.0.0.1:8443/kill -H "Content-Type: application/json" -d '{"arm":true}')
echo "kill_route=$KILL"
kill $SPID 2>/dev/null
sleep 2

echo "=== FACEOFF 8: carpet bomb ==="
timeout 60 python quantum_cli.py camwar -c 127.0.0.0/29 > /tmp/f8.txt 2>&1
echo "rc=$?"
grep -E '"found": ?0|0 found' /tmp/f8.txt || tail -3 /tmp/f8.txt
grep -c Traceback /tmp/f8.txt || echo "no tracebacks"
