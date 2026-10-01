"""quantum.recon.googledork — Google dorking query packs + engine URLs.

Search-engine dorking (advanced-operator reconnaissance) for the operator
console: a curated pack of well-known PUBLIC dork patterns (GHDB-style
categories, written here as standard operator combinations), the operator
reference, multi-engine search URLs, and a methods section describing
publicly-documented analyst tradecraft (scoping, chaining, date filters,
iterative narrowing, triage discipline).

Scope notes (honest):
* this module builds QUERY STRINGS and search URLs only — no requests are
  ever sent, nothing is scraped, no CAPTCHAs are fought. Live results
  render in a browser (the APK opens them in its in-app WebView).
* the "analyst methods" are generic public OSINT methodology, NOT
  attributed to any agency or classified source. There is no such
  attribution anywhere in this file.
* dorks find EXPOSED data; accessing anything you are not authorized for
  is covered by the same authorization rules as every other module here.

JSON-safe: every public function returns plain data and never raises on
bad input (validate() reports problems instead).
"""
from __future__ import annotations

import urllib.parse

# operator -> {desc, example}
OPERATORS = {
    "site:": {
        "desc": "Restrict results to one domain or TLD.",
        "example": "site:example.com filetype:pdf",
    },
    "filetype:": {
        "desc": "Only files of this extension (alias: ext:).",
        "example": "filetype:xls password",
    },
    "intitle:": {
        "desc": "Term must appear in the page title.",
        "example": 'intitle:"index of"',
    },
    "inurl:": {
        "desc": "Term must appear in the URL.",
        "example": "inurl:admin.php",
    },
    "intext:": {
        "desc": "Term must appear in the page body.",
        "example": "intext:password",
    },
    "cache:": {
        "desc": "Show Google's cached copy of a URL.",
        "example": "cache:example.com/page",
    },
    "related:": {
        "desc": "Pages Google considers similar.",
        "example": "related:example.com",
    },
    "before:/after:": {
        "desc": "Date-range filter (YYYY-MM-DD).",
        "example": "breach after:2023-01-01",
    },
    "\"\"": {
        "desc": "Exact-phrase anchor — kills stemming/synonyms.",
        "example": '"db_password ="',
    },
    "-": {
        "desc": "Exclude a term (no space after the minus).",
        "example": "router -site:vendor.com",
    },
    "OR / |": {
        "desc": "Either term may match (uppercase OR).",
        "example": "inurl:login OR inurl:signin",
    },
    "*": {
        "desc": "Wildcard for whole words inside a phrase.",
        "example": '"password * changed"',
    },
}

ENGINES = {
    "google": "https://www.google.com/search?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
    "startpage": "https://www.startpage.com/sp/search?query={q}",
}

CATEGORIES = (
    "exposed-files",
    "login-portals",
    "cameras",
    "directories",
    "errors",
    "devices",
    "documents",
)

# Well-known public dork patterns (standard operator combinations).
# {id, title, category, query, note}
PRESETS = [
    {
        "id": "env-exposed",
        "title": "Exposed environment files",
        "category": "exposed-files",
        "query": 'filename:.env "DB_PASSWORD"',
        "note": "Config files indexed with credentials. Verify ownership before touching.",
    },
    {
        "id": "sql-dumps",
        "title": "SQL database dumps",
        "category": "exposed-files",
        "query": 'filetype:sql "INSERT INTO" password',
        "note": "Dump files left on web roots.",
    },
    {
        "id": "key-files",
        "title": "Private key material",
        "category": "exposed-files",
        "query": 'filetype:pem "PRIVATE KEY"',
        "note": "PEM/PPK keys. Report, do not use.",
    },
    {
        "id": "config-bak",
        "title": "Backup / old config copies",
        "category": "exposed-files",
        "query": 'filetype:bak inurl:conf',
        "note": "Editor and admin backup copies.",
    },
    {
        "id": "git-exposed",
        "title": "Exposed .git directories",
        "category": "exposed-files",
        "query": 'inurl:.git/HEAD "ref:"',
        "note": "Full repo history is often reconstructible.",
    },
    {
        "id": "login-generic",
        "title": "Login pages",
        "category": "login-portals",
        "query": 'inurl:login OR inurl:signin intitle:login',
        "note": "Baseline portal discovery; scope with site:.",
    },
    {
        "id": "admin-panels",
        "title": "Admin panels",
        "category": "login-portals",
        "query": 'intitle:"admin panel" OR intitle:"control panel"',
        "note": "Admin interfaces. Default-creds testing needs authorization.",
    },
    {
        "id": "wp-login",
        "title": "WordPress logins",
        "category": "login-portals",
        "query": 'inurl:wp-login.php',
        "note": "Pair with version dorks for targeting notes.",
    },
    {
        "id": "ip-cameras",
        "title": "Network cameras (generic viewers)",
        "category": "cameras",
        "query": 'inurl:view/view.shtml',
        "note": "Unauthenticated camera viewers. Viewing private feeds needs authorization.",
    },
    {
        "id": "webcam-xp",
        "title": "webcamXP-style pages",
        "category": "cameras",
        "query": 'intitle:"webcamXP"',
        "note": "Classic exposed-cam pattern.",
    },
    {
        "id": "index-of",
        "title": "Open directory listings",
        "category": "directories",
        "query": 'intitle:"index of"',
        "note": "The starting point for manual browsing; scope by target.",
    },
    {
        "id": "index-of-backup",
        "title": "Directory listings with archives",
        "category": "directories",
        "query": 'intitle:"index of" (zip OR tar OR bak)',
        "note": "Listings that already advertise interesting files.",
    },
    {
        "id": "ftp-listings",
        "title": "FTP directory indexes",
        "category": "directories",
        "query": 'intitle:"FTP root" OR intitle:"FTP directory"',
        "note": "Anonymous FTP roots indexed by crawlers.",
    },
    {
        "id": "sql-errors",
        "title": "SQL error messages",
        "category": "errors",
        "query": 'intext:"SQL syntax" OR intext:"mysql_fetch"',
        "note": "Verbose errors that confirm injectable endpoints.",
    },
    {
        "id": "php-errors",
        "title": "PHP warnings / stack traces",
        "category": "errors",
        "query": 'intext:"Fatal error" intext:".php" "on line"',
        "note": "Path disclosure + version hints.",
    },
    {
        "id": "router-pages",
        "title": "Router / gateway admin",
        "category": "devices",
        "query": 'intitle:"router" intitle:"login" -site:vendor.com',
        "note": "Exclude vendor docs with the minus operator.",
    },
    {
        "id": "printer-panels",
        "title": "Printer / MFP panels",
        "category": "devices",
        "query": 'intitle:"printer" inurl:status',
        "note": "Device panels; often no auth at all.",
    },
    {
        "id": "iot-dashboards",
        "title": "IoT dashboards",
        "category": "devices",
        "query": 'intitle:dashboard inurl:status temperature',
        "note": "Sensor dashboards left open.",
    },
    {
        "id": "confidential-docs",
        "title": "Confidential documents",
        "category": "documents",
        "query": 'filetype:pdf confidential OR "internal use only"',
        "note": "Leaked paperwork. Handle per engagement rules.",
    },
    {
        "id": "spreadsheets",
        "title": "Public spreadsheets with secrets",
        "category": "documents",
        "query": 'filetype:xls OR filetype:xlsx password',
        "note": "Credential tables in indexed sheets.",
    },
    {
        "id": "slides-internal",
        "title": "Internal slide decks",
        "category": "documents",
        "query": 'filetype:ppt OR filetype:pptx "internal only"',
        "note": "Roadmaps, creds in screenshots, architecture.",
    },
    {
        "id": "paste-dumps",
        "title": "Paste-site credential dumps",
        "category": "exposed-files",
        "query": 'site:pastebin.com password',
        "note": "Combo lists and configs mirrored to pastes.",
    },
    {
        "id": "cisco-configs",
        "title": "Network device configs",
        "category": "devices",
        "query": 'filetype:cfg "hostname" "enable password"',
        "note": "Switch/router configs with hashes.",
    },
    {
        "id": "jenkins-open",
        "title": "Open CI consoles",
        "category": "login-portals",
        "query": 'intitle:"Dashboard [Jenkins]"',
        "note": "Unauthenticated build consoles = RCE-shaped.",
    },
]

# Public analyst tradecraft: how professionals work a dork list
# methodically. Generic OSINT methodology — no agency attribution.
ANALYST_METHODS = [
    {
        "id": "scope-first",
        "title": "Scope before you search",
        "body": "Start every engagement query with site:target.tld (or a quoted "
                "unique string from the target, like a product codename). An "
                "unscoped dork returns the whole internet; a scoped one returns "
                "your target. Widen only after the scoped pass is exhausted.",
        "steps": [
            "Run the preset with site:target.tld appended.",
            "If zero hits, drop one operator and re-run.",
            "Only then remove site: to see the global pattern.",
        ],
    },
    {
        "id": "chain-operators",
        "title": "Chain operators to cut noise",
        "body": "Each added operator is a filter. The professional pattern is "
                "broad → narrow: begin with one operator, inspect 2 pages of "
                "hits, then add the operator that removes the dominant false "
                "positive class (usually -term or a second inurl:/intitle:).",
        "steps": [
            "Baseline: one operator, note the junk pattern.",
            "Add the exclusion or second anchor that kills the junk.",
            "Freeze the final query in your notes with the hit count.",
        ],
    },
    {
        "id": "anchor-phrases",
        "title": "Anchor on exact phrases",
        "body": "Quoted strings defeat stemming and synonym expansion. Error "
                "messages, banner strings, and default titles (\"Warning: "
                "mysql_connect()\") are the highest-signal anchors because "
                "only real deployments emit them verbatim.",
        "steps": [
            "Harvest 2–3 verbatim strings from a known-good hit.",
            "Re-query each string quoted, scoped to the target.",
            "Pivot: quoted string + filetype: for the artifact class.",
        ],
    },
    {
        "id": "date-boxing",
        "title": "Date-box to find fresh exposure",
        "body": "after:/before: (YYYY-MM-DD) split a dork into 'always existed' "
                "vs 'newly indexed'. New exposures are the ones worth immediate "
                "triage — re-run high-value dorks monthly with after:<last run>.",
        "steps": [
            "Run the dork unbounded, note total hits.",
            "Re-run with after:<your last review date>.",
            "Triage only the delta; log the date for next time.",
        ],
    },
    {
        "id": "filetype-pivot",
        "title": "Pivot across filetypes",
        "body": "One finding implies siblings: a leaked .pdf suggests .xls/.ppt/.bak "
                "in the same directory tree. Re-run the same anchor with each "
                "filetype: in turn, then intitle:\"index of\" on the parent path.",
        "steps": [
            "Take the directory path from the first hit.",
            "Repeat the anchor per filetype.",
            "Close with an index-of query on the parent directory.",
        ],
    },
    {
        "id": "triage-discipline",
        "title": "Triage like an analyst, not a collector",
        "body": "Log every query, hit count, and verdict (true/false positive, "
                "authorized finding, out of scope). A dork list without a log "
                "is re-run forever; a logged one compounds. Never interact "
                "beyond read-only retrieval without written authorization.",
        "steps": [
            "Record query + engine + date + hits + verdict.",
            "Mark false-positive patterns to auto-exclude next run.",
            "Escalate true findings through the engagement channel, not DMs.",
        ],
    },
]


def build_search_url(query, engine="google"):
    """Search URL for [query] on [engine]; unknown engines fall back to google."""
    template = ENGINES.get(engine, ENGINES["google"])
    return template.format(q=urllib.parse.quote_plus(query or ""))


def presets_by_category():
    """{category: [preset, ...]} preserving catalog order."""
    grouped = {cat: [] for cat in CATEGORIES}
    for preset in PRESETS:
        grouped.setdefault(preset["category"], []).append(preset)
    return grouped


def get_preset(preset_id):
    """Preset dict by id, or None."""
    for preset in PRESETS:
        if preset["id"] == preset_id:
            return preset
    return None


def validate():
    """Catalog self-check: returns a list of problem strings (empty = clean)."""
    problems = []
    seen = set()
    for preset in PRESETS:
        pid = preset.get("id", "")
        if not pid:
            problems.append("preset missing id")
            continue
        if pid in seen:
            problems.append(f"duplicate preset id {pid}")
        seen.add(pid)
        if not preset.get("query", "").strip():
            problems.append(f"preset {pid} has empty query")
        if not preset.get("title", "").strip():
            problems.append(f"preset {pid} has empty title")
        if preset.get("category") not in CATEGORIES:
            problems.append(f"preset {pid} has unknown category")
    for op, info in OPERATORS.items():
        if not info.get("desc") or not info.get("example"):
            problems.append(f"operator {op} missing desc/example")
    for method in ANALYST_METHODS:
        if not method.get("title") or not method.get("body"):
            problems.append(f"method {method.get('id')} missing title/body")
        if not method.get("steps"):
            problems.append(f"method {method.get('id')} has no steps")
    return problems
