
param([string[]]$Paths)
Remove-Item -Path ".git/index.lock" -Force -ErrorAction SilentlyContinue
echo "Lock cleared"
$safe = @("docs/RELEASE_NOTES_v4.6.5.md","FEATURE_PARITY_PLAN.md","build_zips.py","build_exploit_index.py",
  ".github/workflows/catalog-auto-update.yml","src/quantum/core/bus.py","src/quantum/core/tasks.py",
  "src/quantum/core/telemetry.py","src/quantum/control/registry.py","src/quantum/c2/dashboard.py",
  "exploit_catalog/","release/v4.6.5/")
if($Paths) { $safe = $Paths }
$safe = $safe | Where-Object { $_ -notmatch "whitepapers" }
git add -f $safe
echo "Added explicit paths only (no LFS bulk)"

