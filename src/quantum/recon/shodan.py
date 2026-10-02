"""quantum.recon.shodan — Shodan integration with advanced preset search phrases.

Provides Shodan API integration with preset queries for various intents.
"""
from __future__ import annotations

import os
from datetime import datetime

from quantum.core.deps import requests
from quantum.core.logging import log

SHODAN_PRESET_QUERIES = {
    "cameras": {
        "name": "IP Cameras",
        "description": "Find exposed IP cameras",
        "queries": [
            "webcamxp",
            "netcam",
            "ipcam",
            "camera",
            "surveillance",
            "hikvision",
            "dahua",
            "axis",
            "foscam",
            "vivotek",
            "mobotix",
            "arecont",
            "pelco",
            "bosch",
            "hanwha",
            "uniview",
            "acti",
            "geovision",
            "march",
            "milestone",
            "exacq",
            "onssi",
            "videoiq",
        ],
    },
    "databases": {
        "name": "Databases",
        "description": "Find exposed databases",
        "queries": [
            "mongodb",
            "mysql",
            "postgresql",
            "redis",
            "elasticsearch",
            "cassandra",
            "couchdb",
            "memcached",
            "rabbitmq",
            "kafka",
            "zookeeper",
            "neo4j",
            "influxdb",
            "timescaledb",
            "clickhouse",
            "presto",
            "hive",
            "hbase",
            "solr",
            "sphinx",
        ],
    },
    "iot": {
        "name": "IoT Devices",
        "description": "Find exposed IoT devices",
        "queries": [
            "iot",
            "smart home",
            "smart tv",
            "smart fridge",
            "smart thermostat",
            "smart lock",
            "smart doorbell",
            "smart camera",
            "smart speaker",
            "smart watch",
            "smart band",
            "smart scale",
            "smart bulb",
            "smart plug",
            "smart switch",
            "smart outlet",
            "smart sensor",
            "smart meter",
            "smart gateway",
            "smart hub",
            "smart relay",
            "smart controller",
        ],
    },
    "industrial": {
        "name": "Industrial Control Systems",
        "description": "Find exposed ICS/SCADA systems",
        "queries": [
            "scada",
            "plc",
            "hmi",
            "rtu",
            "dcs",
            "ics",
            "industrial",
            "modbus",
            "dnp3",
            "bacnet",
            "profibus",
            "profinet",
            "ethernetip",
            "opcua",
            "s7",
            "siemens",
            "schneider",
            "allen bradley",
            "mitsubishi",
            "omron",
            "ge fanuc",
            "abb",
            "honeywell",
            "yokogawa",
            "emerson",
        ],
    },
    "vpn": {
        "name": "VPN Gateways",
        "description": "Find exposed VPN gateways",
        "queries": [
            "vpn",
            "openvpn",
            "ipsec",
            "l2tp",
            "pptp",
            "wireguard",
            "ssl vpn",
            "anyconnect",
            "fortinet",
            "palo alto",
            "checkpoint",
            "juniper",
            "cisco asa",
            "sonicwall",
            "watchguard",
            "sophos",
            "zywall",
            "dd-wrt",
            "openwrt",
            "pfsense",
            "opnsense",
        ],
    },
    "web_servers": {
        "name": "Web Servers",
        "description": "Find exposed web servers",
        "queries": [
            "apache",
            "nginx",
            "iis",
            "tomcat",
            "jetty",
            "lighttpd",
            "caddy",
            "traefik",
            "haproxy",
            "varnish",
            "squid",
            "cloudflare",
            "akamai",
            "fastly",
            "incapsula",
            "sucuri",
            "wordfence",
            "modsecurity",
            "fail2ban",
            "snort",
            "suricata",
            "zeek",
        ],
    },
    "remote_desktop": {
        "name": "Remote Desktop",
        "description": "Find exposed remote desktop services",
        "queries": [
            "rdp",
            "vnc",
            "teamviewer",
            "anydesk",
            "logmein",
            "gotoassist",
            "splashtop",
            "chrome remote desktop",
            "microsoft remote desktop",
            "apple remote desktop",
            "x11",
            "xrdp",
            "tigervnc",
            "realvnc",
            "ultravnc",
            "tightvnc",
            "remmina",
            "freerdp",
            "rdesktop",
            "vnc viewer",
        ],
    },
    "file_sharing": {
        "name": "File Sharing",
        "description": "Find exposed file sharing services",
        "queries": [
            "ftp",
            "sftp",
            "scp",
            "smb",
            "nfs",
            "afp",
            "webdav",
            "nextcloud",
            "owncloud",
            "seafile",
            "pydio",
            "filebrowser",
            "filerun",
            "krusader",
            "midnight commander",
            "filezilla",
            "winscp",
            "cyberduck",
            "transmit",
            "forklift",
            "mucommander",
            "double commander",
        ],
    },
    "email": {
        "name": "Email Servers",
        "description": "Find exposed email servers",
        "queries": [
            "smtp",
            "pop3",
            "imap",
            "exchange",
            "postfix",
            "sendmail",
            "exim",
            "dovecot",
            "courier",
            "zimbra",
            "roundcube",
            "squirrelmail",
            "horde",
            "rainloop",
            "afterlogic",
            "mailcow",
            "mailu",
            "maddy",
            "haraka",
            "zone mta",
        ],
    },
    "gaming": {
        "name": "Gaming Servers",
        "description": "Find exposed gaming servers",
        "queries": [
            "minecraft",
            "counter-strike",
            "team fortress",
            "left 4 dead",
            "garry's mod",
            "rust",
            "ark",
            "dayz",
            "arma",
            "squad",
            "insurgency",
            "killing floor",
            "payday",
            "borderlands",
            "destiny",
            "warframe",
            "elite dangerous",
            "star citizen",
            "eve online",
            "world of warcraft",
            "final fantasy",
        ],
    },
    "blockchain": {
        "name": "Blockchain Nodes",
        "description": "Find exposed blockchain nodes",
        "queries": [
            "bitcoin",
            "ethereum",
            "litecoin",
            "dogecoin",
            "monero",
            "zcash",
            "dash",
            "ripple",
            "cardano",
            "polkadot",
            "solana",
            "avalanche",
            "polygon",
            "chainlink",
            "uniswap",
            "aave",
            "compound",
            "maker",
            "synthetix",
            "yearn",
            "curve",
            "balancer",
        ],
    },
}


def list_shodan_presets() -> dict:
    """List all Shodan preset query categories."""
    return SHODAN_PRESET_QUERIES


def shodan_search(query: str, api_key: str = None, limit: int = 100) -> dict:
    """Search Shodan for the given query."""
    if not api_key:
        api_key = os.environ.get("SHODAN_API_KEY", "")
    if not api_key:
        return {"error": "Shodan API key not configured. Set SHODAN_API_KEY environment variable.",
                "query": query, "results": []}
    out = {
        "query": query,
        "searched_at": datetime.now().isoformat(),
        "results": [],
        "total": 0,
    }
    try:
        r = requests.get(
            "https://api.shodan.io/shodan/host/search",
            params={"key": api_key, "query": query, "limit": limit},
            timeout=30,
        )
        if r.ok:
            data = r.json()
            out["total"] = data.get("total", 0)
            for match in data.get("matches", []):
                out["results"].append({
                    "ip": match.get("ip_str"),
                    "port": match.get("port"),
                    "hostnames": match.get("hostnames", []),
                    "domains": match.get("domains", []),
                    "os": match.get("os"),
                    "product": match.get("product"),
                    "version": match.get("version"),
                    "banner": match.get("banner", "")[:500],
                    "timestamp": match.get("timestamp"),
                    "isp": match.get("isp"),
                    "org": match.get("org"),
                    "asn": match.get("asn"),
                    "location": match.get("location", {}),
                })
        else:
            out["error"] = r.text[:500]
    except Exception as exc:
        out["error"] = str(exc)
    log(f"Shodan search: {query}", "SHODAN")
    return out


def shodan_host_info(ip: str, api_key: str = None) -> dict:
    """Get Shodan information for a specific host."""
    if not api_key:
        api_key = os.environ.get("SHODAN_API_KEY", "")
    if not api_key:
        return {"error": "Shodan API key not configured. Set SHODAN_API_KEY environment variable.",
                "ip": ip, "info": {}}
    out = {
        "ip": ip,
        "queried_at": datetime.now().isoformat(),
        "info": {},
    }
    try:
        r = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key},
            timeout=30,
        )
        if r.ok:
            out["info"] = r.json()
        else:
            out["error"] = r.text[:500]
    except Exception as exc:
        out["error"] = str(exc)
    log(f"Shodan host info: {ip}", "SHODAN")
    return out


def shodan_dashboard_state() -> dict:
    """Return the full Shodan dashboard state for the UI."""
    return {
        "presets": SHODAN_PRESET_QUERIES,
        "api_key_configured": bool(os.environ.get("SHODAN_API_KEY")),
        "recent_searches": [],
        "generated_at": datetime.now().isoformat(),
    }
