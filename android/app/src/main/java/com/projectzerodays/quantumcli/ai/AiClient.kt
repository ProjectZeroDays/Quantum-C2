package com.projectzerodays.quantumcli.ai

import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.projectzerodays.quantumcli.QuantumApp
import com.projectzerodays.quantumcli.c2.C2State
import com.projectzerodays.quantumcli.data.QuantSettings
import com.projectzerodays.quantumcli.ops.Net
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * AI brains for the chat window:
 *  - Online: Abliterated.ai-compatible /chat/completions endpoint (URL + key
 *    from settings; default https://api.abliteration.ai/v1 with model
 *    abliterated-model-large-v2).
 *  - Local: MediaPipe LLM Inference API over a .task model in the app files
 *    dir; disabled with a hint when no model is present.
 */
object AiClient {

    const val MODE_ONLINE = "online"
    const val MODE_LOCAL = "local"
    const val MODE_DETERMINISTIC = "deterministic"

    const val SYSTEM_PROMPT =
        "You are QUANTUM-CLI's red-team commander running inside an authorized " +
            "security-lab C2 app on Android. Answer concisely in a terminal tone. " +
            "When asked to choose a next action, reply as strict JSON: " +
            "{\"action\": \"...\", \"target\": \"ip-or-domain-or-blank\", \"reason\": \"one sentence\"}."

    // ---------------------------------------------------------------- online
    /** POST /chat/completions; returns choices[0].message.content or null. */
    fun onlineChat(
        messages: List<Pair<String, String>>,
        timeoutMs: Int = 60_000,
    ): String? {
        val s = QuantSettings.state.value
        if (s.apiUrl.isBlank() || s.apiKey.isBlank()) return null
        val url = s.apiUrl.trimEnd('/') + "/chat/completions"
        val arr = JSONArray()
        for ((role, content) in messages) {
            arr.put(JSONObject().put("role", role).put("content", content))
        }
        val body = JSONObject().put("model", s.model).put("messages", arr).toString()
        val r = Net.httpPost(
            url,
            body.toByteArray(Charsets.UTF_8),
            mapOf(
                "Authorization" to "Bearer ${s.apiKey}",
                "Content-Type" to "application/json"
            ),
            timeoutMs
        )
        if (r.error != null) {
            C2State.audit("AI", "online chat failed: ${r.error}")
            return null
        }
        return try {
            val parsed = JSONObject(r.text())
            parsed
                .getJSONArray("choices")
                .getJSONObject(0)
                .getJSONObject("message")
                .getString("content")
        } catch (e: Exception) {
            C2State.audit("AI", "online reply parse failed: ${r.text(120)}")
            null
        }
    }

    // ----------------------------------------------------------------- local
    @Volatile
    private var inference: LlmInference? = null

    @Volatile
    private var loadedPath: String? = null

    fun localAvailable(): Boolean = localModelFile() != null

    fun localModelFile(): File? = QuantSettings.localModelFile()

    fun localHint(): String {
        val f = localModelFile()
        return if (f != null) {
            "Local model loaded from files/${f.name}"
        } else {
            "No .task model found — drop a MediaPipe LLM .task file into the app files dir to enable local AI"
        }
    }

    /** MediaPipe LLM Inference API — generateResponse on the .task model. */
    fun localChat(prompt: String): String? {
        val f = localModelFile() ?: return null
        val inf = ensureInference(f) ?: return null
        return try {
            inf.generateResponse(prompt)
        } catch (e: Exception) {
            C2State.audit("AI", "local inference failed: ${e.message}")
            null
        }
    }

    private fun ensureInference(f: File): LlmInference? {
        if (inference != null && loadedPath == f.absolutePath) return inference
        closeLocal()
        return try {
            val options = LlmInference.LlmInferenceOptions.builder()
                .setModelPath(f.absolutePath)
                .setMaxTokens(1024)
                .build()
            val engine = LlmInference.createFromOptions(QuantumApp.ctx, options)
            inference = engine
            loadedPath = f.absolutePath
            engine
        } catch (e: Throwable) {
            C2State.audit("AI", "local model load failed: ${e.message}")
            null
        }
    }

    fun closeLocal() {
        val inf = inference ?: return
        try {
            inf.close()
        } catch (e: Exception) {
            // engine already closed
        }
        inference = null
        loadedPath = null
    }
}
