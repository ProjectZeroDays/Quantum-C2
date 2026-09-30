"""quantum.recon.project_zero — Google Project Zero blog feed (zero-day loop).

Fetches and parses the Atom feed with no third-party dependency (stdlib
xml + requests). Used by the CLI (`p0feed`), the Android Recon page, and
the zero-day generation loop that turns new Project Zero write-ups into
exploit candidates against the current target classes.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEED_URL = "https://googleprojectzero.blogspot.com/feeds/posts/default"

_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(url=FEED_URL, timeout=15):
    """GET the raw Atom feed bytes; raises on HTTP failure."""
    from quantum.core.deps import requests
    r = requests.get(url, timeout=timeout,
                     headers={"User-Agent": "quantum-cli/p0feed"})
    r.raise_for_status()
    return r.content


def parse(atom_bytes):
    """Parse an Atom feed into entry dicts (title, link, published, summary,
    tags). Robust to missing fields; never raises on entry level."""
    entries = []
    try:
        root = ET.fromstring(atom_bytes)
    except ET.ParseError:
        return entries
    for e in root.findall("atom:entry", _NS):
        link = ""
        for l in e.findall("atom:link", _NS):
            if l.get("rel") in (None, "alternate"):
                link = l.get("href") or ""
                break
        published = (e.findtext("atom:published", default="", namespaces=_NS)
                     or "")[:19]
        categories = [c.get("term") or "" for c in
                      e.findall("atom:category", _NS)]
        summary = e.findtext("atom:summary", default="", namespaces=_NS) or ""
        entries.append({
            "title": e.findtext("atom:title", default="", namespaces=_NS) or "",
            "link": link,
            "published": published,
            "summary": _strip_html(summary)[:400],
            "tags": [t for t in categories if t],
        })
    return entries


def _strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def latest(n=10, url=FEED_URL, timeout=15):
    """Latest n entries; empty list (never raises) on any network problem."""
    try:
        return parse(fetch(url, timeout))[:n]
    except Exception:  # noqa: BLE001 — feed is best-effort
        return []


def extract_cves(entry_summary, entry_title=""):
    """CVE ids mentioned in an entry — the zero-day loop's first filter."""
    return sorted(set(re.findall(r"CVE-\d{4}-\d{4,7}",
                                 (entry_title or "") + " " + (entry_summary or ""))))


def zero_day_candidates(n=10, url=FEED_URL, timeout=15):
    """Feed entries that reference at least one CVE, with the CVE list."""
    out = []
    for e in latest(n=n, url=url, timeout=timeout):
        cves = extract_cves(e.get("summary", ""), e.get("title", ""))
        if cves:
            out.append({**e, "cves": cves})
    return out


def as_markdown(entries):
    """Render entries as a compact markdown list for reports/dashboards."""
    if not entries:
        return "_feed unavailable_"
    lines = []
    for e in entries:
        ts = e.get("published", "")
        lines.append(f"- **{e.get('title', '(untitled)')}**"
                      f"{' — ' + ts[:10] if ts else ''}"
                      f"\n  <{e.get('link', '')}>"
                      + (f"\n  `{', '.join(e['cves'])}`" if e.get("cves") else ""))
    return "\n".join(lines)


def _demo_feed_bytes():
    """Deterministic fixture used by the unit tests."""
    return f"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Project Zero</title>
  <entry>
    <title>Escalating privileges in the kernel</title>
    <link rel="alternate" href="https://googleprojectzero.blogspot.com/2026/01/demo1.html"/>
    <published>{datetime.now(timezone.utc).isoformat()}Z</published>
    <summary>&lt;p&gt;We discuss CVE-2026-1234 and the impact.&lt;/p&gt;</summary>
    <category term="kernel"/>
  </entry>
  <entry>
    <title>No CVE here</title>
    <link rel="alternate" href="https://googleprojectzero.blogspot.com/2026/02/demo2.html"/>
    <published>2026-02-01T00:00:00Z</published>
    <summary>plain summary</summary>
  </entry>
</feed>
""".encode()
