#!/usr/bin/env pwsh
# Quantum CLI git wrapper — always removes stale index.lock first
Remove-Item -Path ".git/index.lock" -Force -ErrorAction SilentlyContinue
Invoke-Expression $args
