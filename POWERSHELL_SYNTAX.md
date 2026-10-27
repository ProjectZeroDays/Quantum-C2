# PowerShell 5.1 syntax rules for this repo
- Use Select-Object / Select-String instead of head/tail/grep
- Use Get-ChildItem instead of ls -la
- Use Remove-Item instead of rm -rf
- Use Test-Path instead of [ -f ]
- No && / || chaining; use ; or separate lines
- No /dev/null redirection; use Out-Null or redirect to $null
