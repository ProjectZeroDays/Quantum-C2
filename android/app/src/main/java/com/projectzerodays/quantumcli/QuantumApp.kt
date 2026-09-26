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
        C2State.init(filesDir)
        QuantSettings.init(this)
        Notifications.createChannel(this)
        if (QuantSettings.state.value.autostart) {
            val port = QuantSettings.state.value.c2Port
            if (QuantServerManager.start(port)) {
                Notifications.serverRunning(this, port)
            }
        }
        C2State.audit("C2", "QUANTUM-CLI ${C2State.VERSION} (android) initialized — flavor ${BuildConfig.FLAVOR}")
    }
}
