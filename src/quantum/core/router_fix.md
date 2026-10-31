# Router Double-Prefix Fix (§12.4)
# Defect: routes may double-prefix (e.g., /api/v1/api/v1/devices)
# Fix: ensure url_prefix applied exactly once; no nested blueprints
# Verified: import all api modules; inspect url_prefix
