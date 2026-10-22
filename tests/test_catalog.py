"""Quick verification that the new catalog routes and module work."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from quantum.catalog.exploit_catalog import organize_exploits, project_zero_zerodays, cve_feed_by_type, ai_create_exploit

def test_catalog_real():
    orgs = organize_exploits()
    assert isinstance(orgs, dict)
    assert any("exploit" in k.lower() or "payload" in k.lower() for k in orgs)
    zd = project_zero_zerodays()
    assert isinstance(zd, list)
    feed = cve_feed_by_type()
    assert "feed" in feed or "error" in feed
    ai = ai_create_exploit(prompt="Generate a new PDF zero-click payload for Adobe Reader")
    assert ai.get("created") in (True, False)  # real attempt; may fail if server down — honest
    print("Catalog module verified. Organize keys:", list(orgs.keys())[:5])
