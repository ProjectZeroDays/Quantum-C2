"""quantum.recon.gitdork — GitHub dork search (Tier-1 port).

Ported from Quantum C2 `ADDED/github_dorks/github-dork.py` (itself the
techgaun/github-dorks tool) to stdlib-only: the GitHub Search API is
called directly via urllib, and the classic dork list is embedded.
Requires a GH_TOKEN (fine-grained PAT with code-search read) or
GH_USER/GH_PWD for authenticated search.

JSON-safe: every public function returns plain data and never raises.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

API = "https://api.github.com/search/code"

# classic dork set (from github-dorks.txt)
DORKS = [
    "filename:.npmrc _auth",
    "filename:.dockercfg auth",
    "extension:pem private",
    "extension:ppk private",
    "filename:id_rsa or filename:id_dsa",
    "extension:sql mysql dump",
    "extension:sql mysql dump password",
    "filename:credentials aws_access_key_id",
    "filename:.s3cfg",
    "filename:wp-config.php",
    "filename:.htpasswd",
    "filename:.env DB_USERNAME NOT homestead",
    "filename:.env MAIL_HOST=smtp.gmail.com",
    "filename:.git-credentials",
    "PT_TOKEN language:bash",
    "filename:.bashrc password",
    "filename:.bashrc mailchimp",
    "filename:.bash_profile aws",
    "rds.amazonaws.com password",
    "extension:json api.forecast.io",
    "extension:json mongolab.com",
    "extension:yaml mongolab.com",
    "jsforce extension:js conn.login",
    'SF_USERNAME "salesforce"',
    'filename:.tugboat NOT "_tugboat"',
    "HEROKU_API_KEY language:shell",
    "HEROKU_API_KEY language:json",
    "filename:.netrc password",
    "filename:_netrc password",
    "filename:hub oauth_token",
    "filename:robomongo.json",
    "filename:filezilla.xml Pass",
    "filename:recentservers.xml Pass",
    "filename:config.json auths",
    "filename:idea14.key",
    "filename:config irc_pass",
    "filename:connections.xml",
    "filename:express.conf path:.openshift",
    "filename:.pgpass",
    "filename:proftpdpasswd",
    "filename:ventrilo_srv.ini",
    "[WFClient] Password= extension:ica",
    "filename:server.cfg rcon password",
    "JEKYLL_GITHUB_TOKEN",
    "filename:.bash_history",
    "filename:.cshrc",
    "filename:.history",
    "filename:.sh_history",
    "filename:sshd_config",
    "filename:dhcpd.conf",
    'filename:prod.exs NOT "prod.secret.exs"',
    "filename:prod.secret.exs",
    "filename:configuration.php JConfig password",
    "filename:config.php dbpasswd",
    "filename:config.php pass",
    "path:sites databases password",
    "shodan_api_key language:python",
    "shodan_api_key language:shell",
    "shodan_api_key language:json",
    "shodan_api_key language:ruby",
    "filename:shadow path:etc",
]


def _auth():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": "Bearer %s" % token.strip()}, "token"
    user = os.environ.get("GH_USER")
    pwd = os.environ.get("GH_PWD")
    if user and pwd:
        import base64
        basic = base64.b64encode(
            ("%s:%s" % (user, pwd)).encode()).decode()
        return {"Authorization": "Basic %s" % basic}, "basic"
    return None, None


def search_dork(dork, repo=None, user=None, limit=10, timeout=30):
    """Run one GitHub code-search dork (optionally scoped to a repo or
    user/org). Returns {\"ok\", \"dork\", \"total\", \"results\"} or a
    clean error — never raises."""
    try:
        headers, _mode = _auth()
        if headers is None:
            return {"ok": False, "dork": dork,
                    "error": "no GitHub credentials (set GH_TOKEN)"}
        q = dork
        if repo:
            q += " repo:" + repo
        elif user:
            q += " user:" + user
        url = API + "?q=" + urllib.parse.quote(q) + \
            "&per_page=%d" % max(1, min(int(limit), 100))
        req = urllib.request.Request(
            url, headers={**headers,
                          "Accept": "application/vnd.github+json",
                          "User-Agent": "quantum-cli/4.4"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = [
            {"repo": (it.get("repository") or {}).get("full_name"),
             "path": it.get("path"),
             "html_url": it.get("html_url")}
            for it in (data.get("items") or [])
        ]
        return {"ok": True, "dork": q, "total": data.get("total_count", 0),
                "results": results}
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            return {"ok": False, "dork": dork,
                    "error": "rate limited (HTTP %d) — retry later" % exc.code}
        return {"ok": False, "dork": dork,
                "error": "HTTP %d: %s" % (exc.code, exc.reason)}
    except Exception as exc:
        return {"ok": False, "dork": dork,
                "error": "%s: %s" % (type(exc).__name__, exc)}


def scan(repo=None, user=None, dorks=None, limit_per_dork=5,
        max_dorks=None, timeout=30):
    """Run the (embedded or caller-supplied) dork list against a repo or
    user/org. Returns a JSON-safe report — never raises."""
    try:
        if not repo and not user:
            return {"ok": False, "error": "pass repo= or user= to scope "
                                          "the scan (an unscoped search "
                                          "burns the whole rate limit)"}
        dorks = dorks if dorks is not None else DORKS
        if max_dorks:
            dorks = dorks[:max_dorks]
        hits = []
        checked = 0
        for dork in dorks:
            r = search_dork(dork, repo=repo, user=user,
                            limit=limit_per_dork, timeout=timeout)
            checked += 1
            if r.get("ok") and r.get("total"):
                hits.append({"dork": dork, "total": r["total"],
                             "results": r["results"]})
            elif not r.get("ok") and "rate limited" in (r.get("error") or ""):
                return {"ok": True, "scope": repo or user,
                        "checked": checked, "hits": hits,
                        "stopped_early": True,
                        "error": r["error"]}
        return {"ok": True, "scope": repo or user, "checked": checked,
                "hits": hits, "hit_count": len(hits)}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def list_dorks():
    """The embedded dork list."""
    return {"ok": True, "count": len(DORKS), "dorks": list(DORKS)}
