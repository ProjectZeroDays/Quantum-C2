"""quantum.catalog.payloads_all — PayloadsAllTheThings catalog.

Indexes the swisskyrepo/PayloadsAllTheThings repository (72 technique
sections, 355 documents on master as of the 2026-09 seed): section
browse, keyword search, and payload-content retrieval.

- Offline: browse/search the embedded index (names + paths).
- `sync()` downloads the repository ZIP to ~/.qcli/catalog/ so
  `get_payload()` can return the actual payload text (read straight from
  the ZIP, no extraction needed).

JSON-safe: every public function returns plain data and never raises.
"""
from __future__ import annotations

import os
import zipfile
from datetime import datetime, timezone

REPO = "swisskyrepo/PayloadsAllTheThings"
BRANCH = "master"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".qcli", "catalog")
ZIP_PATH = os.path.join(DATA_DIR, "payloadsallthethings.zip")
ZIP_URL = ("https://github.com/%s/archive/refs/heads/%s.zip" % (REPO, BRANCH))
_ZIP_ROOT = "PayloadsAllTheThings-%s/" % BRANCH

# generated from github.com/swisskyrepo/PayloadsAllTheThings master tree
_INDEX = {
    "API Key Leaks": {
        "readme": True,
        "files": [
            "Files/MachineKeys.txt",
            "IIS-Machine-Keys.md",
        ],
    },
    "Account Takeover": {
        "readme": True,
        "files": [
            "mfa-bypass.md",
        ],
    },
    "Brute Force Rate Limit": {
        "readme": True,
        "files": [
        ],
    },
    "Business Logic Errors": {
        "readme": True,
        "files": [
        ],
    },
    "CONTRIBUTING.md": {
        "readme": None,
        "files": [
            "",
        ],
    },
    "CORS Misconfiguration": {
        "readme": True,
        "files": [
        ],
    },
    "CRLF Injection": {
        "readme": True,
        "files": [
            "Files/crlfinjection.txt",
        ],
    },
    "CSS Injection": {
        "readme": True,
        "files": [
        ],
    },
    "CSV Injection": {
        "readme": True,
        "files": [
        ],
    },
    "CVE Exploits": {
        "readme": True,
        "files": [
            "Log4Shell.md",
        ],
    },
    "Clickjacking": {
        "readme": True,
        "files": [
        ],
    },
    "Client Side Path Traversal": {
        "readme": True,
        "files": [
        ],
    },
    "Command Injection": {
        "readme": True,
        "files": [
            "Intruder/command-execution-unix.txt",
            "Intruder/command_exec.txt",
        ],
    },
    "Cross-Site Request Forgery": {
        "readme": True,
        "files": [
        ],
    },
    "DISCLAIMER.md": {
        "readme": None,
        "files": [
            "",
        ],
    },
    "DNS Rebinding": {
        "readme": True,
        "files": [
        ],
    },
    "DOM Clobbering": {
        "readme": True,
        "files": [
        ],
    },
    "Denial of Service": {
        "readme": True,
        "files": [
        ],
    },
    "Dependency Confusion": {
        "readme": True,
        "files": [
        ],
    },
    "Directory Traversal": {
        "readme": True,
        "files": [
            "Intruder/deep_traversal.txt",
            "Intruder/directory_traversal.txt",
            "Intruder/dotdotpwn.txt",
            "Intruder/traversals-8-deep-exotic-encoding.txt",
        ],
    },
    "Encoding Transformations": {
        "readme": True,
        "files": [
        ],
    },
    "External Variable Modification": {
        "readme": True,
        "files": [
        ],
    },
    "File Inclusion": {
        "readme": True,
        "files": [
            "Files/LFI2RCE.py",
            "Files/phpinfolfi.py",
            "Files/uploadlfi.py",
            "Intruders/BSD-files.txt",
            "Intruders/JHADDIX_LFI.txt",
            "Intruders/LFI-FD-check.txt",
            "Intruders/LFI-WindowsFileCheck.txt",
            "Intruders/Linux-files.txt",
            "Intruders/List_Of_File_To_Include.txt",
            "Intruders/List_Of_File_To_Include_NullByteAdded.txt",
            "Intruders/Mac-files.txt",
            "Intruders/Traversal.txt",
            "Intruders/Web-files.txt",
            "Intruders/Windows-files.txt",
            "Intruders/dot-slash-PathTraversal_and_LFI_pairing.txt",
            "Intruders/php-filter-iconv.txt",
            "Intruders/simple-check.txt",
            "LFI-to-RCE.md",
            "Wrappers.md",
        ],
    },
    "Google Web Toolkit": {
        "readme": True,
        "files": [
        ],
    },
    "GraphQL Injection": {
        "readme": True,
        "files": [
        ],
    },
    "HTTP Parameter Pollution": {
        "readme": True,
        "files": [
        ],
    },
    "Headless Browser": {
        "readme": True,
        "files": [
            "files/iframe.html",
            "files/window_location_js.html",
        ],
    },
    "Hidden Parameters": {
        "readme": True,
        "files": [
        ],
    },
    "Insecure Deserialization": {
        "readme": True,
        "files": [
            "DotNET.md",
            "Files/Ruby_universal_gadget_generate_verify.rb",
            "Files/node-serialize.js",
            "Files/ruby-serialize.yaml",
            "Java.md",
            "Node.md",
            "PHP.md",
            "Python.md",
            "Ruby.md",
        ],
    },
    "Insecure Direct Object References": {
        "readme": True,
        "files": [
        ],
    },
    "Insecure Management Interface": {
        "readme": True,
        "files": [
            "Intruder/springboot_actuator.txt",
        ],
    },
    "Insecure Randomness": {
        "readme": True,
        "files": [
        ],
    },
    "Insecure Source Code Management": {
        "readme": True,
        "files": [
            "Bazaar.md",
            "Files/github-dorks.txt",
            "Git.md",
            "Mercurial.md",
            "Subversion.md",
        ],
    },
    "JSON Web Token": {
        "readme": True,
        "files": [
        ],
    },
    "Java RMI": {
        "readme": True,
        "files": [
        ],
    },
    "LDAP Injection": {
        "readme": True,
        "files": [
            "Intruder/LDAP_FUZZ.txt",
            "Intruder/LDAP_FUZZ_SMALL.txt",
            "Intruder/LDAP_attributes.txt",
        ],
    },
    "LICENSE": {
        "readme": None,
        "files": [
            "",
        ],
    },
    "LaTeX Injection": {
        "readme": True,
        "files": [
        ],
    },
    "Mass Assignment": {
        "readme": True,
        "files": [
        ],
    },
    "Methodology and Resources": {
        "readme": None,
        "files": [
            "Active Directory Attack.md",
            "Bind Shell Cheatsheet.md",
            "Cloud - AWS Pentest.md",
            "Cloud - Azure Pentest.md",
            "Cobalt Strike - Cheatsheet.md",
            "Container - Docker Pentest.md",
            "Container - Kubernetes Pentest.md",
            "Escape Breakout.md",
            "HTML Smuggling.md",
            "Hash Cracking.md",
            "Initial Access.md",
            "Linux - Evasion.md",
            "Linux - Persistence.md",
            "Linux - Privilege Escalation.md",
            "MSSQL Server - Cheatsheet.md",
            "Metasploit - Cheatsheet.md",
            "Methodology and enumeration.md",
            "Network Discovery.md",
            "Network Pivoting Techniques.md",
            "Office - Attacks.md",
            "Powershell - Cheatsheet.md",
            "Reverse Shell Cheatsheet.md",
            "Source Code Management.md",
            "Vulnerability Reports.md",
            "Web Attack Surface.md",
            "Windows - AMSI Bypass.md",
            "Windows - DPAPI.md",
            "Windows - Defenses.md",
            "Windows - Download and Execute.md",
            "Windows - Mimikatz.md",
            "Windows - Persistence.md",
            "Windows - Privilege Escalation.md",
            "Windows - Using credentials.md",
        ],
    },
    "NoSQL Injection": {
        "readme": True,
        "files": [
            "Intruder/MongoDB.txt",
            "Intruder/NoSQL.txt",
        ],
    },
    "OAuth Misconfiguration": {
        "readme": True,
        "files": [
        ],
    },
    "ORM Leak": {
        "readme": True,
        "files": [
        ],
    },
    "Open Redirect": {
        "readme": True,
        "files": [
            "Intruder/Open-Redirect-payloads.txt",
            "Intruder/open_redirect_wordlist.txt",
            "Intruder/openredirects.txt",
        ],
    },
    "Prompt Injection": {
        "readme": True,
        "files": [
        ],
    },
    "Prototype Pollution": {
        "readme": True,
        "files": [
        ],
    },
    "README.md": {
        "readme": None,
        "files": [
            "",
        ],
    },
    "Race Condition": {
        "readme": True,
        "files": [
        ],
    },
    "Regular Expression": {
        "readme": True,
        "files": [
        ],
    },
    "Request Smuggling": {
        "readme": True,
        "files": [
        ],
    },
    "Reverse Proxy Misconfigurations": {
        "readme": True,
        "files": [
        ],
    },
    "SAML Injection": {
        "readme": True,
        "files": [
        ],
    },
    "SQL Injection": {
        "readme": True,
        "files": [
            "BigQuery Injection.md",
            "Cassandra Injection.md",
            "DB2 Injection.md",
            "Intruder/Auth_Bypass.txt",
            "Intruder/Auth_Bypass2.txt",
            "Intruder/FUZZDB_MSSQL-WHERE_Time.txt",
            "Intruder/FUZZDB_MSSQL.txt",
            "Intruder/FUZZDB_MSSQL_Enumeration.txt",
            "Intruder/FUZZDB_MYSQL.txt",
            "Intruder/FUZZDB_MySQL-WHERE_Time.txt",
            "Intruder/FUZZDB_MySQL_ReadLocalFiles.txt",
            "Intruder/FUZZDB_Oracle.txt",
            "Intruder/FUZZDB_Postgres_Enumeration.txt",
            "Intruder/Generic_ErrorBased.txt",
            "Intruder/Generic_Fuzz.txt",
            "Intruder/Generic_TimeBased.txt",
            "Intruder/Generic_UnionSelect.txt",
            "Intruder/SQL-Injection",
            "Intruder/SQLi_Polyglots.txt",
            "Intruder/payloads-sql-blind-MSSQL-INSERT",
            "Intruder/payloads-sql-blind-MSSQL-WHERE",
            "Intruder/payloads-sql-blind-MySQL-INSERT",
            "Intruder/payloads-sql-blind-MySQL-ORDER_BY",
            "Intruder/payloads-sql-blind-MySQL-WHERE",
            "MSSQL Injection.md",
            "MySQL Injection.md",
            "OracleSQL Injection.md",
            "PostgreSQL Injection.md",
            "SQLite Injection.md",
            "SQLmap.md",
        ],
    },
    "Server Side Include Injection": {
        "readme": True,
        "files": [
            "Files/ssi_esi.txt",
        ],
    },
    "Server Side Request Forgery": {
        "readme": True,
        "files": [
            "Files/ip.py",
            "Files/ssrf_ffmpeg.avi",
            "SSRF-Advanced-Exploitation.md",
            "SSRF-Cloud-Instances.md",
        ],
    },
    "Server Side Template Injection": {
        "readme": True,
        "files": [
            "ASP.md",
            "Elixir.md",
            "Intruder/ssti.fuzz",
            "Java.md",
            "JavaScript.md",
            "PHP.md",
            "Python.md",
            "Ruby.md",
        ],
    },
    "Tabnabbing": {
        "readme": True,
        "files": [
        ],
    },
    "Type Juggling": {
        "readme": True,
        "files": [
        ],
    },
    "Upload Insecure Files": {
        "readme": True,
        "files": [
            "CVE FFmpeg HLS/gen_avi_bypass.py",
            "CVE FFmpeg HLS/gen_xbin_avi.py",
            "CVE FFmpeg HLS/read_passwd.avi",
            "CVE FFmpeg HLS/read_passwd_bypass.mp4",
            "CVE FFmpeg HLS/read_shadow.avi",
            "CVE FFmpeg HLS/read_shadow_bypass.mp4",
            "CVE ZIP Symbolic Link/etc_passwd.zip",
            "CVE ZIP Symbolic Link/generate.sh",
            "CVE ZIP Symbolic Link/passwd",
            "Configuration Apache .htaccess/.htaccess",
            "Configuration Apache .htaccess/.htaccess_phpinfo",
            "Configuration Apache .htaccess/.htaccess_rce_files",
            "Configuration Apache .htaccess/.htaccess_shell",
            "Configuration Apache .htaccess/README.md",
            "Configuration IIS web.config/web.config",
            "Configuration Python __init__.py/python-admin-__init__.py.zip",
            "Configuration Python __init__.py/python-conf-__init__.py.zip",
            "Configuration Python __init__.py/python-config-__init__.py.zip",
            "Configuration Python __init__.py/python-controllers-__init__.py.zip",
            "Configuration Python __init__.py/python-generate-init.py",
            "Configuration Python __init__.py/python-login-__init__.py.zip",
            "Configuration Python __init__.py/python-models-__init__.py.zip",
            "Configuration Python __init__.py/python-modules-__init__.py.zip",
            "Configuration Python __init__.py/python-scripts-__init__.py.zip",
            "Configuration Python __init__.py/python-settings-__init__.py.zip",
            "Configuration Python __init__.py/python-tests-__init__.py.zip",
            "Configuration Python __init__.py/python-urls-__init__.py.zip",
            "Configuration Python __init__.py/python-utils-__init__.py.zip",
            "Configuration Python __init__.py/python-view-__init__.py.zip",
            "Configuration uwsgi.ini/uwsgi.ini",
            "EICAR/eicar.txt",
            "Extension ASP/extensions.lst",
            "Extension ASP/shell.asa",
            "Extension ASP/shell.ashx",
            "Extension ASP/shell.asmx",
            "Extension ASP/shell.asp",
            "Extension ASP/shell.aspx",
            "Extension ASP/shell.cer",
            "Extension ASP/shell.soap",
            "Extension ASP/shell.xamlx",
            "Extension HTML/xss.html",
            "Extension PHP/extensions.lst",
            "Extension PHP/php-script-tag.php",
            "Extension PHP/phpinfo.jpg.php",
            "Extension PHP/phpinfo.phar",
            "Extension PHP/phpinfo.php",
            "Extension PHP/phpinfo.php3",
            "Extension PHP/phpinfo.php4",
            "Extension PHP/phpinfo.php5",
            "Extension PHP/phpinfo.php7",
            "Extension PHP/phpinfo.php8",
            "Extension PHP/phpinfo.phpt",
            "Extension PHP/phpinfo.pht",
            "Extension PHP/phpinfo.phtml",
            "Extension PHP/shell.gif^shell.php",
            "Extension PHP/shell.jpeg.php",
            "Extension PHP/shell.jpg.php",
            "Extension PHP/shell.jpg^shell.php",
            "Extension PHP/shell.pgif",
            "Extension PHP/shell.phar",
            "Extension PHP/shell.php",
            "Extension PHP/shell.php3",
            "Extension PHP/shell.php4",
            "Extension PHP/shell.php5",
            "Extension PHP/shell.php7",
            "Extension PHP/shell.phpt",
            "Extension PHP/shell.pht",
            "Extension PHP/shell.phtml",
            "Extension PHP/shell.png.php",
            "Extension PHP/shell.png^shell.php",
            "Extension PHP/tiny.php",
            "Jetty RCE/JettyShell.xml",
            "Picture Compression/createBulletproofJPG.py",
            "Picture Compression/createCompressedPNG_110x110.php",
            "Picture Compression/createGIFwithGlobalColorTable.php",
            "Picture Compression/createPNGwithPLTE.php",
            "Picture ImageMagick/imagemagick_ghostscript_cmd_exec.pdf",
            "Picture ImageMagick/imagetragik1_payload_url_bind_shell_nc.mvg",
            "Picture ImageMagick/imagetragik1_payload_url_remote_connection.mvg",
            "Picture ImageMagick/imagetragik1_payload_url_reverse_shell_bash.mvg",
            "Picture ImageMagick/imagetragik1_payload_xml_reverse_shell_nctraditional.xml",
            "Picture ImageMagick/imagetragik1_payload_xml_reverse_shell_netcat_encoded.xml",
            "Picture Metadata/Build_image_to_LFI.py",
            "Server Side Include/exec.shtml",
            "Server Side Include/include.shtml",
            "Server Side Include/index.stm",
        ],
    },
    "Virtual Hosts": {
        "readme": True,
        "files": [
        ],
    },
    "Web Cache Deception": {
        "readme": True,
        "files": [
            "Intruders/param_miner_lowercase_headers.txt",
        ],
    },
    "Web Sockets": {
        "readme": True,
        "files": [
            "Files/ws-harness.py",
        ],
    },
    "XPATH Injection": {
        "readme": True,
        "files": [
        ],
    },
    "XS-Leak": {
        "readme": True,
        "files": [
        ],
    },
    "XSLT Injection": {
        "readme": True,
        "files": [
            "Files/enum-system-version-vendor.xsl",
            "Files/file-write.xsl",
            "Files/rce-dotnet-2.xsl",
            "Files/rce-dotnet.xsl",
            "Files/rce-java-1.xsl",
            "Files/rce-java-2.xsl",
            "Files/rce-php-assert.xsl",
            "Files/rce-php-file-create.xsl",
            "Files/rce-php-file-read.xsl",
            "Files/rce-php-meterpreter.xsl",
            "Files/rce-php-scandir.xsl",
            "Files/read-and-ssrf.xsl",
            "Files/system-properties.xml",
            "Files/system-properties.xsl",
            "Files/xxe.xsl",
        ],
    },
    "XSS Injection": {
        "readme": True,
        "files": [
            "1 - XSS Filter Bypass.md",
            "2 - XSS Polyglot.md",
            "3 - XSS Common WAF Bypass.md",
            "4 - CSP Bypass.md",
            "5 - XSS in Angular.md",
            "Files/InsecureFlashFile.swf",
            "Files/JupyterNotebookXSS.ipynb",
            "Files/SWF_XSS.swf",
            "Files/xml.xsd",
            "Files/xss.cer",
            "Files/xss.dtd",
            "Files/xss.htm",
            "Files/xss.html.demo",
            "Files/xss.hxt",
            "Files/xss.mno",
            "Files/xss.rdf",
            "Files/xss.svgz",
            "Files/xss.url.url",
            "Files/xss.vml",
            "Files/xss.wsdl",
            "Files/xss.xht",
            "Files/xss.xhtml",
            "Files/xss.xml",
            "Files/xss.xsd",
            "Files/xss.xsf",
            "Files/xss.xsl",
            "Files/xss.xslt",
            "Intruders/0xcela_event_handlers.txt",
            "Intruders/BRUTELOGIC-XSS-JS.txt",
            "Intruders/BRUTELOGIC-XSS-STRINGS.txt",
            "Intruders/IntrudersXSS.txt",
            "Intruders/JHADDIX_XSS.txt",
            "Intruders/MarioXSSVectors.txt",
            "Intruders/RSNAKE_XSS.txt",
            "Intruders/XSSDetection.txt",
            "Intruders/XSS_Polyglots.txt",
            "Intruders/jsonp_endpoint.txt",
            "Intruders/port_swigger_xss_cheatsheet_event_handlers.txt",
            "Intruders/xss_alert.txt",
            "Intruders/xss_alert_identifiable.txt",
            "Intruders/xss_payloads_quick.txt",
            "Intruders/xss_swf_fuzz.txt",
        ],
    },
    "XXE Injection": {
        "readme": True,
        "files": [
            "Files/Classic XXE - etc passwd.xml",
            "Files/Classic XXE B64 Encoded.xml",
            "Files/Classic XXE.xml",
            "Files/Deny Of Service - Billion Laugh Attack",
            "Files/XXE OOB Attack (Yunusov, 2013).xml",
            "Files/XXE PHP Wrapper.xml",
            "Intruders/XXE_Fuzzing.txt",
            "Intruders/xml-attacks.txt",
        ],
    },
    "Zip Slip": {
        "readme": True,
        "files": [
        ],
    },
    "custom.css": {
        "readme": None,
        "files": [
            "",
        ],
    },
    "mkdocs.yml": {
        "readme": None,
        "files": [
            "",
        ],
    },
}



# ---------------------------------------------------------------------------
def sections():
    """List of technique sections with document counts. Never raises."""
    try:
        return [{"section": s,
                 "documents": (1 if v["readme"] else 0) + len(v["files"]),
                 "readme": bool(v["readme"]),
                 "payload_files": len(v["files"])}
                for s, v in sorted(_INDEX.items())]
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, exc)}


def search(query, limit=25):
    """Keyword search over section names and file names. Never raises."""
    try:
        q = (query or "").lower().strip()
        out = []
        for s, v in sorted(_INDEX.items()):
            score = 0
            if q in s.lower():
                score += 10
            files = [f for f in v["files"] if q in f.lower()]
            score += len(files)
            if score:
                out.append({"section": s, "score": score, "files": files[:20]})
        out.sort(key=lambda r: -r["score"])
        return {"query": query, "total_matches": len(out),
                "results": out[:max(0, int(limit))]}
    except Exception as exc:
        return {"query": query, "total_matches": 0, "results": [],
                "error": "%s: %s" % (type(exc).__name__, exc)}


def is_synced():
    return os.path.isfile(ZIP_PATH)


def sync(timeout=120):
    """Download the repository ZIP so payload text can be read offline.
    Returns a status dict — never raises."""
    import urllib.request
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        req = urllib.request.Request(
            ZIP_URL, headers={"User-Agent": "quantum-cli/4.4"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        with zipfile.ZipFile(io_bytes(raw)) as z:      # validate the zip
            names = z.namelist()
        if len(names) < 100:
            raise ValueError("implausible repo zip (%d entries)" % len(names))
        tmp = ZIP_PATH + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(raw)
        os.replace(tmp, ZIP_PATH)
        return {"ok": True, "entries": len(names), "source": ZIP_PATH,
                "synced_at": datetime.now(tz=timezone.utc).isoformat()}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def io_bytes(b):
    import io
    return io.BytesIO(b)


def get_payload(section, rel_path=None):
    """Read payload text from the synced ZIP. `rel_path` None -> the
    section README. Returns {"ok", "section", "path", "content"} or an
    error dict — never raises."""
    try:
        if not is_synced():
            return {"ok": False,
                    "error": "not synced — call payloads_all.sync() first"}
        if section not in _INDEX:
            return {"ok": False, "error": "unknown section %r" % section}
        if rel_path is None:
            rel_path = "README.md"
        with zipfile.ZipFile(ZIP_PATH) as z:
            name = _ZIP_ROOT + section + "/" + rel_path
            if name not in z.namelist():
                close = [n for n in z.namelist()
                        if n.startswith(_ZIP_ROOT + section + "/")]
                return {"ok": False, "error": "path %r not in section" % rel_path,
                        "section": section, "available": close[:50]}
            content = z.read(name).decode("utf-8", "replace")
        return {"ok": True, "section": section, "path": rel_path,
                "content": content}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def stats():
    try:
        return {"ok": True, "repo": REPO, "branch": BRANCH,
                "sections": len(_INDEX),
                "documents": sum((1 if v["readme"] else 0) + len(v["files"])
                                 for v in _INDEX.values()),
                "synced": is_synced(),
                "zip_bytes": os.path.getsize(ZIP_PATH) if is_synced() else 0}
    except Exception as exc:
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
