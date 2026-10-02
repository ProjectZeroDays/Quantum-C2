# Errors

Command failures and integration errors.

---

## [ERR-20260812-001] router_vuln_type_injection

**Logged**: 2026-08-12T09:15:00Z
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
RouterVulnType.INJECTION does not exist in router_gateway.py causing import failure

### Error
```
AttributeError: type object 'RouterVulnType' has no attribute 'INJECTION'
  File "backend/app/gateways/router_exploit/router_gateway.py", line 207
```

### Context
- Command: `python -c "from app.main import app"`
- The RouterVulnType enum was missing the INJECTION value
- Only OSPF_INJECTION and ROUTE_INJECTION exist

### Suggested Fix
Changed `RouterVulnType.INJECTION` to `RouterVulnType.ROUTE_INJECTION` in router_gateway.py

### Resolution
- **Resolved**: 2026-08-12T09:20:00Z
- **Commit**: 4f6f7a3d
- **Notes**: Fixed by replacing INJECTION with ROUTE_INJECTION

---

## [ERR-20260812-002] device_profiles_import_error

**Logged**: 2026-08-12T09:10:00Z
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
ImportError when importing device_profiles from app.routers

### Error
```
ImportError: cannot import name 'device_profiles' from 'app.routers'
```

### Context
- device_profiles module is in `app/api/` not `app/routers/`
- Adding it to routers/__init__.py caused circular import

### Suggested Fix
Remove device_profiles from routers/__init__.py and register it directly in main.py via api import

### Resolution
- **Resolved**: 2026-08-12T09:25:00Z
- **Commit**: 4f6f7a3d
- **Notes**: Removed from __init__.py, registered via direct import in main.py

---

## [ERR-20260812-003] powershell_chaining_syntax

**Logged**: 2026-08-12T09:00:00Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
PowerShell does not support && chaining syntax

### Error
```
The token '&&' is not a valid statement separator in this version.
```

### Context
- Attempted to chain git commands with &&
- PowerShell 5.1 requires semicolon or separate commands

### Suggested Fix
Use `;` instead of `&&` or run commands separately

### Metadata
- Reproducible: yes
- Related Files: .git/index.lock (stale lock file)

---

## [ERR-20260812-004] git_index_lock

**Logged**: 2026-08-12T09:05:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Git commit fails due to stale index.lock file

### Error
```
fatal: Unable to create 'C:/Projects/Quantum C2/.git/index.lock': File exists.
Another git process seems to be running in this repository, or the lock file may be stale
```

### Context
- Previous git process did not clean up properly
- Lock file persists after crash/timeout

### Suggested Fix
Remove the lock file: `Remove-Item .git/index.lock -Force`

### Resolution
- **Resolved**: 2026-08-12T09:06:00Z
- **Notes**: Removed lock file and retried commit

---

## [ERR-20260817-001] pytest_collection

**Logged**: 2026-08-17T15:30:00Z
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
pytest collection errors from missing BaseAgent import in test_agent_v63.py and test_mobsf_capfuzz.py

### Error
`
ImportError: cannot import name 'BaseAgent' from 'core' (unknown location)
`

### Context
Two test files import from backend.app.agents.system which has a circular import issue with core.BaseAgent

### Suggested Fix
Exclude these test files from collection or fix the import chain

### Metadata
- Reproducible: yes
- Related Files: backend/tests/test_agent_v63.py, backend/tests/test_mobsf_capfuzz.py
