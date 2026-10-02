# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260812-001] best_practice

**Logged**: 2026-08-12T09:30:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Module location matters for import paths in FastAPI projects

### Details
- `device_profiles_routes.py` is in `app/api/` not `app/routers/`
- Router init imports must match actual file locations
- Circular imports occur when mixing api/ and routers/ in same init

### Suggested Action
Always verify module location before adding to __init__.py imports. Use separate import paths for api/ vs routers/ modules.

### Metadata
- Source: error
- Related Files: backend/app/routers/__init__.py, backend/app/api/device_profiles_routes.py
- Tags: import, fastapi, architecture
- Pattern-Key: best.import_module_location

---

## [LRN-20260812-002] best_practice

**Logged**: 2026-08-12T09:35:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
RouterVulnType enum values must match all usages

### Details
- router_gateway.py referenced `RouterVulnType.INJECTION` but enum only has `OSP夫_INJECTION` and `ROUTE_INJECTION`
- Always verify enum values exist before referencing them
- Use IDE/linter to catch undefined enum attributes

### Suggested Action
Run `python -m py_compile` on all modified files before committing
Add linting step to CI/CD pipeline

### Metadata
- Source: error
- Related Files: backend/app/gateways/router_exploit/router_gateway.py
- Tags: enum, validation, linting
- Pattern-Key: best.verify_enum_values

---

## [LRN-20260812-003] insight

**Logged**: 2026-08-12T09:40:00Z
**Priority**: low
**Status**: pending
**Area**: devops

### Summary
PowerShell requires different syntax than bash for command chaining

### Details
- `&&` chaining doesn't work in PowerShell 5.1
- Use `;` for sequential execution or run commands separately
- This caused confusion when switching between bash and PowerShell contexts

### Suggested Action
Document PowerShell syntax differences in project README
Use cross-platform command patterns

### Metadata
- Source: error
- Tags: powershell, syntax, cross-platform

---

## [LRN-20260812-004] knowledge_gap

**Logged**: 2026-08-12T09:45:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Not all routers need to be in __init__.py — selective imports prevent circular dependencies

### Details
- Added too many imports to routers/__init__.py causing circular import errors
- Some modules (device_profiles) belong in api/ not routers/
- Main.py can import directly without going through __init__.py

### Suggested Action
Review __init__.py imports periodically
Use lazy imports for optional modules
Consider splitting routers into subpackages

### Metadata
- Source: user_feedback
- Related Files: backend/app/routers/__init__.py, backend/app/main.py
- Tags: architecture, imports, circular-dependency

---

## [LRN-20260812-005] best_practice

**Logged**: 2026-08-12T09:50:00Z
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
Production readiness assessment should be systematic and documented

### Details
- Created comprehensive production checklist (PRODUCTION_CHECKLIST.md)
- Identified 78% production readiness with specific gaps
- 10 remaining items to address for 100% readiness

### Suggested Action
Run production_check.py before any deployment
Update checklist as items are completed
Track progress in tasks/QUEUE.md

### Metadata
- Source: conversation
- Related Files: PRODUCTION_CHECKLIST.md, scripts/production_check.py
- Tags: production, checklist, readiness

---

## [LRN-20260817-001] best_practice

**Logged**: 2026-08-17T15:30:00Z
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
Duplicate keyword arguments in FastAPI dependency injection cause SyntaxError

### Details
When adding multiple Depends() to FastAPI route functions, duplicate parameter names (e.g., user=Depends(...)) cause Python SyntaxError. The agent_api_routes.py file had 51 instances of duplicate user=Depends arguments.

### Suggested Action
Use only one Depends() per parameter name. Combine requirements into a single dependency or use separate parameter names.

### Metadata
- Source: error
- Related Files: backend/app/api/agent_api_routes.py
- Tags: fastapi, syntax, dependency-injection
