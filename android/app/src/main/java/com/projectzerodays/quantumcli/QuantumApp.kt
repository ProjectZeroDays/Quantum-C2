package com.projectzerodays.quantumcli

import android.app.Application
import android.content.Context
import com.projectzerodays.quantumcli.c2.C2State
import com.projectzerodays.quantumcli.c2.QuantServerManager
import com.projectzerodays.quantumcli.data.QuantSettings
import com.projectzerodays.quantumcli.ui.Notifications
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class QuantumApp : Application() {

    companion object {
        lateinit var ctx: Context
            private set

        val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    }

    override fun onCreate() {
        super.onCreate()
        ctx = this
        // Each step is isolated so a failure in one subsystem (keygen, keystore,
        // port bind) can never take the whole app down at launch.
        runCatching { C2State.init(filesDir) }
            .onFailure { android.util.Log.e("QuantumApp", "C2State.init failed", it) }
        runCatching { QuantSettings.init(this) }
            .onFailure { android.util.Log.e("QuantumApp", "QuantSettings.init failed", it) }
        runCatching { Notifications.createChannel(this) }
            .onFailure { android.util.Log.e("QuantumApp", "channel create failed", it) }
        if (QuantSettings.state.value.autostart) {
            val port = QuantSettings.state.value.c2Port
            if (QuantServerManager.start(port)) {
                Notifications.serverRunning(this, port)
            }
        }
        C2State.audit("C2", "QUANTUM-CLI ${C2State.VERSION} (android) initialized — flavor ${BuildConfig.FLAVOR}")
    }
}
