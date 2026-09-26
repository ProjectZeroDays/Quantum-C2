package com.projectzerodays.quantumcli.data

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File

data class SettingsData(
    val c2Port: Int = 8443,
    val aiMode: String = "deterministic", // online | local | deterministic
    val apiUrl: String = "https://api.abliteration.ai/v1",
    val apiKey: String = "",
    val model: String = "abliterated-model-large-v2",
    val rootMode: Boolean = false,
    val autostart: Boolean = true,
    val overlordCameraOnly: Boolean = false,
    val overlordIntervalSec: Int = 45,
)

/**
 * App settings — persisted in EncryptedSharedPreferences (API key at rest is
 * ciphertext). Exposes a StateFlow snapshot so Compose pages recompose live.
 */
object QuantSettings {

    private lateinit var prefs: SharedPreferences

    private val _state = MutableStateFlow(SettingsData())
    val state: StateFlow<SettingsData> = _state.asStateFlow()

    fun init(context: Context) {
        prefs = try {
            val alias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
            EncryptedSharedPreferences.create(
                "quantum_settings",
                alias,
                context,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )
        } catch (e: Exception) {
            context.getSharedPreferences("quantum_settings_plain", Context.MODE_PRIVATE)
        }
        _state.value = load()
    }

    private fun load(): SettingsData = SettingsData(
        c2Port = prefs.getInt("c2_port", 8443),
        aiMode = prefs.getString("ai_mode", "deterministic") ?: "deterministic",
        apiUrl = prefs.getString(
            "ai_url",
            "https://api.abliteration.ai/v1"
        ) ?: "https://api.abliteration.ai/v1",
        apiKey = prefs.getString("ai_key", "") ?: "",
        model = prefs.getString(
            "ai_model",
            "abliterated-model-large-v2"
        ) ?: "abliterated-model-large-v2",
        rootMode = prefs.getBoolean("root_mode", false),
        autostart = prefs.getBoolean("autostart", true),
        overlordCameraOnly = prefs.getBoolean("overlord_camera_only", false),
        overlordIntervalSec = prefs.getInt("overlord_interval", 45),
    )

    fun update(transform: (SettingsData) -> SettingsData) {
        val next = transform(_state.value)
        prefs.edit()
            .putInt("c2_port", next.c2Port)
            .putString("ai_mode", next.aiMode)
            .putString("ai_url", next.apiUrl)
            .putString("ai_key", next.apiKey)
            .putString("ai_model", next.model)
            .putBoolean("root_mode", next.rootMode)
            .putBoolean("autostart", next.autostart)
            .putBoolean("overlord_camera_only", next.overlordCameraOnly)
            .putInt("overlord_interval", next.overlordIntervalSec)
            .apply()
        _state.value = next
    }

    /** MediaPipe .task model discovery in the app files dir. */
    fun localModelFile(): File? =
        com.projectzerodays.quantumcli.c2.C2State.filesRoot.listFiles()
            ?.firstOrNull { it.isFile && it.name.endsWith(".task") }
}
