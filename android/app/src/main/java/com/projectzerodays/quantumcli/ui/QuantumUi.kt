package com.projectzerodays.quantumcli.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Build
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ChatBubble
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Menu
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Send
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material.icons.outlined.Stop
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.projectzerodays.quantumcli.QuantumApp
import com.projectzerodays.quantumcli.ai.AiClient
import com.projectzerodays.quantumcli.ai.AiModelDownloader
import com.projectzerodays.quantumcli.ai.ChatController
import com.projectzerodays.quantumcli.ai.IntentParser
import com.projectzerodays.quantumcli.c2.AuditEvent
import com.projectzerodays.quantumcli.c2.CameraHit
import com.projectzerodays.quantumcli.c2.C2State
import com.projectzerodays.quantumcli.c2.Grayfish
import com.projectzerodays.quantumcli.c2.QcliApi
import com.projectzerodays.quantumcli.c2.QuantServerManager
import com.projectzerodays.quantumcli.c2.UpdateChecker
import com.projectzerodays.quantumcli.data.QuantSettings
import com.projectzerodays.quantumcli.ops.CamWar
import com.projectzerodays.quantumcli.ops.Net
import com.projectzerodays.quantumcli.ops.NetDiag
import com.projectzerodays.quantumcli.ops.Overlord
import com.projectzerodays.quantumcli.ui.theme.Cyan
import com.projectzerodays.quantumcli.ui.theme.Danger
import com.projectzerodays.quantumcli.ui.theme.Muted
import com.projectzerodays.quantumcli.ui.theme.Ok
import com.projectzerodays.quantumcli.ui.theme.Panel
import com.projectzerodays.quantumcli.ui.theme.QuantumTypography
import com.projectzerodays.quantumcli.ui.theme.SoftCyan
import com.projectzerodays.quantumcli.ui.theme.Softest
import com.projectzerodays.quantumcli.ui.theme.quantumPanel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

/** Command dispatcher shared by every manual control — 1:1 with the /ai API. */
private val c2Api = QcliApi()

/**
 * AI readiness — the single gate behind Chat, the chat FAB and Auto Run.
 * Ready means: online mode with a non-blank key, or local mode with a
 * downloaded on-device model. Deterministic mode never unlocks Auto Run.
 */
object AiGate {
    fun ready(): Boolean {
        val s = QuantSettings.state.value
        return when (s.aiMode) {
            AiClient.MODE_ONLINE -> s.apiKey.isNotBlank()
            AiClient.MODE_LOCAL -> AiClient.localAvailable()
            else -> false
        }
    }

    fun modeLabel(): String {
        val s = QuantSettings.state.value
        return when (s.aiMode) {
            AiClient.MODE_ONLINE -> if (s.apiKey.isNotBlank()) "online (abliteration.ai)" else "online — KEY MISSING"
            AiClient.MODE_LOCAL -> if (AiClient.localAvailable()) "local (on-device)" else "local — MODEL MISSING"
            else -> "manual (no AI)"
        }
    }
}

/**
 * Auto Run — the user-facing handle for the Overlord decision loop.
 * Deliberately refused while no AI brain is configured (chat intents can
 * still start the deterministic loop explicitly in No-AI mode).
 */
object AutoRun {
    fun start(cameraOnly: Boolean, intervalSec: Int): Boolean {
        if (!AiGate.ready()) {
            C2State.audit(
                "AI",
                "Auto Run refused — finish Setup first (Abliteration.ai key or local fallback model)"
            )
            return false
        }
        Overlord.start(QuantumApp.appScope, cameraOnly, intervalSec) { aiDecide() }
        return true
    }

    private suspend fun aiDecide(): String? {
        val s = QuantSettings.state.value
        val prompt = "Choose the next action. Reply as strict JSON " +
            "{\"action\":\"...\",\"target\":\"ip-or-blank\",\"reason\":\"one sentence\"}. " +
            "Allowed actions: " + Overlord.ACTIONS.joinToString(",") + ". " +
            "State: cameras=" + C2State.cameras.value.size +
            ", implants=" + C2State.implants.value.size +
            ", killswitch=" + C2State.killswitch.value + "."
        return when (s.aiMode) {
            AiClient.MODE_ONLINE ->
                AiClient.onlineChat(listOf("system" to AiClient.SYSTEM_PROMPT, "user" to prompt))
            AiClient.MODE_LOCAL ->
                AiClient.localChat(AiClient.SYSTEM_PROMPT + "\n\n" + prompt)
            else -> null
        }
    }
}

/** Run a manual control off the UI thread; outcome lands in the audit console. */
private fun ioOp(tag: String, block: () -> Any?) {
    QuantumApp.appScope.launch(Dispatchers.IO) {
        try {
            val r = block()
            C2State.audit(tag, (r?.toString() ?: "done").take(400))
        } catch (e: Exception) {
            C2State.audit("ERR", "$tag failed: ${e.message}")
        }
    }
}

/** Cross-page navigation + dialog handles provided via CompositionLocal. */
class UiActions(
    val navigate: (Page) -> Unit = {},
    val openWizard: () -> Unit = {},
    val openManual: () -> Unit = {},
    val onChatAction: (IntentParser.ChatAction) -> Unit = {},
)

val LocalUiActions = staticCompositionLocalOf { UiActions() }

private fun openUrl(ctx: android.content.Context, url: String) {
    try {
        ctx.startActivity(
            android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url))
        )
    } catch (e: Exception) {
        C2State.audit("UI", "no app can open $url")
    }
}

// ---------------------------------------------------------------------------
// Root — toggleable drawer + scaffold + top bar + overlays
// ---------------------------------------------------------------------------

/**
 * Root composable: a hamburger-toggleable sidebar (8 page destinations,
 * App Manual, Setup wizard, project links), a top bar with menu + chat
 * buttons, the page host body and the floating chat overlay. First open
 * auto-launches the Setup wizard and the local-AI fallback download.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QuantumUi() {
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Open)
    var selectedPage by rememberSaveable { mutableStateOf(Page.DASHBOARD) }
    var showChat by rememberSaveable { mutableStateOf(false) }
    var showWizard by rememberSaveable { mutableStateOf(false) }
    var showManual by rememberSaveable { mutableStateOf(false) }

    val settings by QuantSettings.state.collectAsState()
    val dlActive by AiModelDownloader.downloading.collectAsState()
    val aiReady = remember(settings.aiMode, settings.apiKey, dlActive) { AiGate.ready() }

    // First open: step-by-step setup + local AI fallback auto-download.
    LaunchedEffect(Unit) {
        if (!QuantSettings.state.value.wizardDone) showWizard = true
        runCatching { AiModelDownloader.maybeAutoDownload() }
            .onFailure { C2State.audit("ERR", "startup model check failed: ${it.message}") }
    }

    val uiActions = UiActions(
        navigate = { selectedPage = it },
        openWizard = { showWizard = true },
        openManual = { showManual = true },
        onChatAction = { a ->
            when (a) {
                is IntentParser.ChatAction.OpenPage -> selectedPage = a.page
                is IntentParser.ChatAction.StartCameraScan -> {
                    UiBus.cameraScanRequest.value = a.cidr
                    selectedPage = Page.CAMERAS
                }
                is IntentParser.ChatAction.StartOverlord ->
                    AutoRun.start(a.cameraOnly, settings.overlordIntervalSec)
                is IntentParser.ChatAction.StopOverlord -> Overlord.stop()
                is IntentParser.ChatAction.ArmKillswitch ->
                    if (a.arm) C2State.killAll(true) else C2State.disarmKillswitch()
                is IntentParser.ChatAction.RunAiCommand -> Unit // dispatched in ChatController
            }
        },
    )

    CompositionLocalProvider(LocalUiActions provides uiActions) {
        ModalNavigationDrawer(
            drawerState = drawerState,
            drawerContent = {
                ModalDrawerSheet(
                    modifier = Modifier.width(280.dp).background(Panel),
                ) {
                    DrawerContent(
                        selected = selectedPage,
                        onNavigate = { selectedPage = it },
                        aiReady = aiReady,
                        onOpenWizard = { showWizard = true },
                        onOpenManual = { showManual = true },
                        ctx = ctx,
                    )
                }
            },
        ) {
            Scaffold(
                containerColor = Color.Transparent,
                topBar = {
                    TopAppBar(
                        title = {
                            Text(
                                selectedPage.title,
                                style = QuantumTypography.titleMedium,
                                color = Softest,
                            )
                        },
                        colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
                        navigationIcon = {
                            IconButton(onClick = {
                                scope.launch {
                                    if (drawerState.isClosed) drawerState.open() else drawerState.close()
                                }
                            }) {
                                Icon(Icons.Outlined.Menu, contentDescription = "Toggle menu", tint = Cyan)
                            }
                        },
                        actions = {
                            if (aiReady) {
                                IconButton(onClick = { showChat = !showChat }) {
                                    Icon(
                                        Icons.Outlined.ChatBubble,
                                        contentDescription = "Chat",
                                        tint = if (showChat) Cyan else SoftCyan,
                                    )
                                }
                            }
                        },
                    )
                },
            ) { innerPadding ->
                Box(Modifier.fillMaxSize().padding(innerPadding)) {
                    when (selectedPage) {
                        Page.DASHBOARD -> DashboardPage()
                        Page.IMPLANTS -> ImplantsPage()
                        Page.CAMERAS -> CamerasPage()
                        Page.NETWORK -> NetworkPage()
                        Page.EXPLOITS -> ExploitsPage()
                        Page.LOOT -> LootPage()
                        Page.CHAT -> ChatPage()
                        Page.SETTINGS -> SettingsPage()
                    }

                    if (showChat && aiReady) {
                        ChatOverlay(
                            modifier = Modifier
                                .align(Alignment.BottomEnd)
                                .fillMaxWidth(0.95f)
                                .height(470.dp),
                            onClose = { showChat = false },
                            onAction = uiActions.onChatAction,
                        )
                    }
                }
            }
        }
    }

    if (showWizard) SetupWizard(onDismiss = { showWizard = false })
    if (showManual) ManualDialog(onDismiss = { showManual = false })
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

@Composable
private fun DrawerContent(
    selected: Page,
    onNavigate: (Page) -> Unit,
    aiReady: Boolean,
    onOpenWizard: () -> Unit,
    onOpenManual: () -> Unit,
    ctx: android.content.Context,
) {
    val dl by AiModelDownloader.downloading.collectAsState()
    val progress by AiModelDownloader.progress.collectAsState()

    val links = listOf(
        Triple("Star on GitHub", Icons.Outlined.Star, "https://github.com/projectzerodays/Quantum-CLI"),
        Triple("Report a Bug", Icons.Outlined.ChatBubble, "https://github.com/projectzerodays/Quantum-CLI/issues"),
        Triple("Contribute", Icons.Outlined.ChatBubble, "https://github.com/projectzerodays/Quantum-CLI/pulls"),
        Triple("Wiki", Icons.Outlined.ChatBubble, "https://github.com/projectzerodays/Quantum-CLI/wiki"),
    )

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
    ) {
        Spacer(Modifier.height(16.dp))
        Text(
            "QUANTUM CLI",
            style = QuantumTypography.headlineSmall,
            color = Cyan,
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp),
        )
        Spacer(Modifier.height(4.dp))

        Page.entries.forEach { p ->
            val locked = p == Page.CHAT && !aiReady
            NavRow(
                icon = p.icon,
                label = if (locked) "Chat (setup required)" else p.title,
                selected = p == selected,
                locked = locked,
                onClick = { if (locked) onOpenWizard() else onNavigate(p) },
            )
        }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 8.dp))

        NavRow(
            icon = Icons.Outlined.MenuBook,
            label = "App manual",
            selected = false,
            onClick = onOpenManual,
        )
        NavRow(
            icon = Icons.Outlined.Build,
            label = "Setup wizard",
            selected = false,
            onClick = onOpenWizard,
        )

        if (dl) {
            Text(
                "downloading local model… ${(progress * 100).toInt()}%",
                style = QuantumTypography.labelSmall,
                color = Muted,
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
            )
        }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 8.dp))
        Text(
            "Project Links",
            style = QuantumTypography.labelSmall,
            color = Muted,
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
        )
        links.forEach { (label, icon, url) ->
            LinkRow(label, icon, url, ctx)
        }
        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun NavRow(
    icon: ImageVector,
    label: String,
    selected: Boolean,
    locked: Boolean = false,
    onClick: () -> Unit,
) {
    val bg = if (selected) Brush.horizontalGradient(listOf(Cyan.copy(0.12f), Color.Transparent))
    else Brush.horizontalGradient(listOf(Color.Transparent, Color.Transparent))
    val tint = when {
        locked -> Muted
        selected -> Cyan
        else -> SoftCyan
    }
    Row(
        Modifier
            .fillMaxWidth()
            .background(bg)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = if (locked) Icons.Outlined.Lock else icon,
            contentDescription = label,
            tint = tint,
            modifier = Modifier.size(22.dp),
        )
        Spacer(Modifier.width(14.dp))
        Text(
            label,
            style = QuantumTypography.bodyLarge,
            color = if (locked) Muted else if (selected) Cyan else Softest,
        )
    }
}

@Composable
private fun LinkRow(label: String, icon: ImageVector, url: String, ctx: android.content.Context) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable { openUrl(ctx, url) }
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = SoftCyan,
            modifier = Modifier.size(18.dp),
        )
        Spacer(Modifier.width(12.dp))
        Text(
            label,
            style = QuantumTypography.bodyMedium,
            color = Softest,
            fontSize = 13.sp,
            textAlign = TextAlign.Start,
        )
    }
}

// ---------------------------------------------------------------------------
// Setup wizard (step-by-step: cloud key · local fallback model · skip)
// ---------------------------------------------------------------------------

@Composable
fun SetupWizard(onDismiss: () -> Unit) {
    val settings by QuantSettings.state.collectAsState()
    var step by rememberSaveable { mutableStateOf(0) } // 0 choose · 1 online · 2 local
    var apiUrl by rememberSaveable { mutableStateOf(settings.apiUrl) }
    var apiKey by rememberSaveable { mutableStateOf(settings.apiKey) }
    var model by rememberSaveable { mutableStateOf(settings.model) }
    val dl by AiModelDownloader.downloading.collectAsState()
    val progress by AiModelDownloader.progress.collectAsState()
    val dlErr by AiModelDownloader.error.collectAsState()
    val localReady = AiClient.localAvailable()

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Panel,
        title = {
            Text("QUANTUM-CLI setup", style = QuantumTypography.titleLarge, color = Cyan)
        },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                when (step) {
                    0 -> {
                        Text(
                            "Configure an AI brain for Chat and Auto Run — or skip and drive " +
                                "every function manually from the dashboard pages.",
                            style = QuantumTypography.bodyMedium,
                            color = Muted,
                        )
                        Spacer(Modifier.height(12.dp))
                        WizardOption(
                            "1 · Abliteration.ai (cloud)",
                            "Paste your API key — chat and Auto Run use the remote endpoint.",
                        ) { step = 1 }
                        Spacer(Modifier.height(8.dp))
                        WizardOption(
                            "2 · Local model (on-device)",
                            "Auto-downloads the Gemma-2B int4 fallback (~1.4 GB) in the " +
                                "background; fully offline afterwards.",
                        ) {
                            QuantSettings.update {
                                it.copy(
                                    aiMode = AiClient.MODE_LOCAL,
                                    autoDownload = true,
                                )
                            }
                            if (!localReady) AiModelDownloader.start()
                            step = 2
                        }
                        Spacer(Modifier.height(8.dp))
                        WizardOption(
                            "3 · Skip — run everything manually",
                            "No AI. Every dashboard control, the kill switch and all scans " +
                                "stay fully available.",
                        ) {
                            QuantSettings.update {
                                it.copy(aiMode = AiClient.MODE_DETERMINISTIC, wizardDone = true)
                            }
                            onDismiss()
                        }
                    }
                    1 -> {
                        OutlinedTextField(
                            value = apiUrl,
                            onValueChange = { apiUrl = it },
                            label = { Text("API URL") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = apiKey,
                            onValueChange = { apiKey = it },
                            label = { Text("Abliteration.ai API key") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(
                            value = model,
                            onValueChange = { model = it },
                            label = { Text("Model") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Text(
                            "Stored encrypted on-device. Never leaves the device except as " +
                                "the Authorization header to the endpoint above.",
                            style = QuantumTypography.labelSmall,
                            color = Muted,
                            modifier = Modifier.padding(top = 8.dp),
                        )
                    }
                    else -> {
                        if (localReady) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Outlined.CheckCircle, null, tint = Ok)
                                Spacer(Modifier.width(8.dp))
                                Text(
                                    "Model ready: ${AiClient.localModelFile()?.name}",
                                    color = Softest,
                                    style = QuantumTypography.bodyMedium,
                                )
                            }
                            Text(
                                AiClient.localHint(),
                                style = QuantumTypography.labelSmall,
                                color = Muted,
                                modifier = Modifier.padding(top = 6.dp),
                            )
                        } else if (dl) {
                            Text(
                                "Downloading fallback model… ${(progress * 100).toInt()}%",
                                style = QuantumTypography.bodyMedium,
                                color = Softest,
                            )
                            LinearProgressIndicator(
                                progress = { progress },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 8.dp),
                            )
                            Text(
                                "Runs in the background — closing this dialog will not stop it. " +
                                    "Chat and Auto Run unlock the moment the model lands.",
                                style = QuantumTypography.labelSmall,
                                color = Muted,
                            )
                        } else {
                            Text(
                                "Download problem: ${dlErr ?: "not started"}",
                                style = QuantumTypography.bodySmall,
                                color = Danger,
                            )
                            Spacer(Modifier.height(8.dp))
                            Button(onClick = { AiModelDownloader.start() }) {
                                Text("Retry download")
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            when (step) {
                1 -> Button(
                    enabled = apiKey.isNotBlank(),
                    onClick = {
                        QuantSettings.update {
                            it.copy(
                                aiMode = AiClient.MODE_ONLINE,
                                apiUrl = apiUrl.trim(),
                                apiKey = apiKey.trim(),
                                model = model.trim(),
                                wizardDone = true,
                            )
                        }
                        C2State.audit("AI", "setup wizard: online mode configured (${model.trim()})")
                        onDismiss()
                    },
                ) { Text("Save & finish") }
                2 -> Button(
                    enabled = localReady,
                    onClick = {
                        QuantSettings.update {
                            it.copy(aiMode = AiClient.MODE_LOCAL, wizardDone = true)
                        }
                        onDismiss()
                    },
                ) { Text("Finish") }
                else -> {}
            }
        },
        dismissButton = {
            if (step == 0) {
                TextButton(onClick = {
                    QuantSettings.update { it.copy(wizardDone = true) }
                    onDismiss()
                }) { Text("Not now") }
            } else {
                TextButton(onClick = { step = 0 }) { Text("Back") }
            }
        },
    )
}

@Composable
private fun WizardOption(title: String, desc: String, onClick: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .quantumPanel()
            .clickable(onClick = onClick)
            .padding(12.dp),
    ) {
        Text(title, style = QuantumTypography.titleSmall, color = Cyan)
        Text(desc, style = QuantumTypography.bodySmall, color = Muted)
    }
}

// ---------------------------------------------------------------------------
// Dashboard — manual controls, kill switch, auto run, log console
// ---------------------------------------------------------------------------

@Composable
fun DashboardPage() {
    val implants by C2State.implants.collectAsState()
    val audit by C2State.audit.collectAsState()
    val decisions by C2State.decisions.collectAsState()
    val killswitch by C2State.killswitch.collectAsState()
    val overlordRunning by Overlord.running.collectAsState()
    val serverRunning by QuantServerManager.running.collectAsState()
    var showAutoRunDlg by remember { mutableStateOf(false) }
    var armConfirm by remember { mutableStateOf(false) }
    val aiReady = AiGate.ready()

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Dashboard", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))

        // ---- autonomous control -------------------------------------------
        Button(
            onClick = { if (overlordRunning) Overlord.stop() else showAutoRunDlg = true },
            enabled = overlordRunning || aiReady,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(
                if (overlordRunning) Icons.Outlined.Stop else Icons.Outlined.PlayArrow,
                contentDescription = null,
            )
            Spacer(Modifier.width(8.dp))
            Text(if (overlordRunning) "STOP AUTO RUN" else "AUTO RUN")
        }
        if (!aiReady && !overlordRunning) {
            Text(
                "Auto Run is locked until the Abliteration.ai key or the local fallback " +
                    "model is configured — open the Setup wizard in the sidebar.",
                style = QuantumTypography.labelSmall,
                color = Muted,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
        if (overlordRunning) {
            Text(
                "Overlord cycle running" +
                    if (Overlord.cameraOnly) " (camera-only)" else " (full act whitelist)",
                style = QuantumTypography.labelSmall,
                color = Ok,
                modifier = Modifier.padding(top = 4.dp),
            )
        }

        Spacer(Modifier.height(8.dp))

        // ---- quick manual ops ---------------------------------------------
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilledTonalButton(
                onClick = { ioOp("RECON") { c2Api.handle("scan") } },
                modifier = Modifier.weight(1f),
            ) { Text("SCAN NET") }
            FilledTonalButton(
                onClick = { ioOp("CAM") { c2Api.handle("camwar") } },
                modifier = Modifier.weight(1f),
            ) { Text("CAM SWEEP") }
        }
        Spacer(Modifier.height(8.dp))

        // ---- kill switch ----------------------------------------------------
        KillSwitchCard(armed = killswitch, onArm = { armConfirm = true }, onDisarm = {
            ioOp("OPSEC") { C2State.disarmKillswitch(); "kill-switch disarmed" }
        })
        if (armConfirm) {
            AlertDialog(
                onDismissRequest = { armConfirm = false },
                containerColor = Panel,
                title = { Text("Arm kill switch?", color = Danger) },
                text = {
                    Text(
                        "A wipe/die task is queued on every known implant and further " +
                            "autonomous actions halt. Queued wipe tasks cannot be recalled.",
                        color = Softest,
                        style = QuantumTypography.bodyMedium,
                    )
                },
                confirmButton = {
                    Button(onClick = {
                        armConfirm = false
                        ioOp("OPSEC") {
                            val hosts = C2State.killAll(true)
                            "KILLSWITCH engaged — ${hosts.size} implant(s) queued"
                        }
                    }) { Text("ARM", color = Danger) }
                },
                dismissButton = {
                    TextButton(onClick = { armConfirm = false }) { Text("Cancel") }
                },
            )
        }

        Spacer(Modifier.height(8.dp))

        // ---- live stats ------------------------------------------------------
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Column(Modifier.weight(1f)) {
                StatusCard("Implants", "${implants.size} active")
                StatusCard("Decisions", "${decisions.size} total")
                StatusCard("C2 server", if (serverRunning) "running :${QuantServerManager.boundPort}" else "stopped")
            }
            Column(Modifier.weight(1f)) {
                StatusCard("Kill-switch", if (killswitch) "ARMED" else "safe")
                StatusCard("Audit events", "${audit.size} logged")
                StatusCard("AI", AiGate.modeLabel())
            }
        }

        // ---- verbose console -------------------------------------------------
        LogConsole(audit)
        Spacer(Modifier.height(16.dp))
    }

    if (showAutoRunDlg) {
        AutoRunDialog(
            initialCameraOnly = QuantSettings.state.value.overlordCameraOnly,
            initialInterval = QuantSettings.state.value.overlordIntervalSec,
            onDismiss = { showAutoRunDlg = false },
        )
    }
}

@Composable
private fun KillSwitchCard(armed: Boolean, onArm: () -> Unit, onDisarm: () -> Unit) {
    Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Kill switch", style = QuantumTypography.titleSmall, color = SoftCyan)
                Text(
                    if (armed) "ARMED — implants queued to wipe/die, overlord halting"
                    else "safe — implants keep beaconing",
                    style = QuantumTypography.bodySmall,
                    color = if (armed) Danger else Muted,
                )
            }
            Button(
                onClick = { if (armed) onDisarm() else onArm() },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (armed) Ok.copy(alpha = 0.2f) else Danger.copy(alpha = 0.25f),
                    contentColor = if (armed) Ok else Danger,
                ),
            ) {
                Text(if (armed) "DISARM" else "ARM")
            }
        }
    }
}

@Composable
private fun AutoRunDialog(
    initialCameraOnly: Boolean,
    initialInterval: Int,
    onDismiss: () -> Unit,
) {
    var cameraOnly by remember { mutableStateOf(initialCameraOnly) }
    var interval by remember { mutableStateOf(initialInterval.toFloat()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Panel,
        title = { Text("Auto Run — Overlord cycle", color = Cyan) },
        text = {
            Column {
                Text(
                    "The autonomous loop decides one action per interval (AI-driven, " +
                        "QBrain deterministic fallback) and journals every decision to " +
                        "this dashboard.",
                    style = QuantumTypography.bodySmall,
                    color = Muted,
                )
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Camera-only acts", color = Softest, modifier = Modifier.weight(1f))
                    Switch(checked = cameraOnly, onCheckedChange = { cameraOnly = it })
                }
                Text(
                    "Restricts the whitelist to cam_war / cam_discover / cam_control / " +
                        "mitre_report / rest.",
                    style = QuantumTypography.labelSmall,
                    color = Muted,
                )
                Spacer(Modifier.height(12.dp))
                Text("Interval: ${interval.toInt()}s", color = Softest)
                Slider(
                    value = interval,
                    onValueChange = { interval = it },
                    valueRange = 10f..300f,
                    steps = 57,
                )
            }
        },
        confirmButton = {
            Button(onClick = {
                val ok = AutoRun.start(cameraOnly, interval.toInt())
                QuantSettings.update {
                    it.copy(overlordCameraOnly = cameraOnly, overlordIntervalSec = interval.toInt())
                }
                if (ok) onDismiss()
            }) { Text("Start") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

@Composable
fun LogConsole(audit: List<AuditEvent>) {
    var autoScroll by rememberSaveable { mutableStateOf(true) }
    val listState = rememberLazyListState()
    val visible = audit.takeLast(150)
    LaunchedEffect(visible.size, autoScroll) {
        if (autoScroll && visible.isNotEmpty()) listState.animateScrollToItem(visible.size - 1)
    }
    Column(Modifier.fillMaxWidth().quantumPanel().padding(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("console", style = QuantumTypography.titleSmall, color = SoftCyan)
            Spacer(Modifier.weight(1f))
            Text("auto-scroll", style = QuantumTypography.labelSmall, color = Muted)
            Switch(checked = autoScroll, onCheckedChange = { autoScroll = it })
            IconButton(onClick = { C2State.clearAuditUi() }) {
                Icon(Icons.Outlined.Delete, contentDescription = "Clear console", tint = Muted)
            }
        }
        LazyColumn(state = listState, modifier = Modifier.fillMaxWidth().height(230.dp)) {
            items(visible) { ev ->
                val color = when {
                    ev.tag == "ERR" -> Danger
                    ev.tag == "ATK" || ev.tag == "CAM" -> Cyan
                    ev.tag == "OPSEC" -> Ok
                    else -> SoftCyan
                }
                Text(
                    "[${ev.ts.substringAfter('T', ev.ts)}] ${ev.tag}: ${ev.msg}",
                    style = QuantumTypography.bodySmall,
                    color = color,
                    fontSize = 10.sp,
                    lineHeight = 13.sp,
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Implants — registry + per-host task controls
// ---------------------------------------------------------------------------

@Composable
fun ImplantsPage() {
    val implants by C2State.implants.collectAsState()
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Implants", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(4.dp))
        Text(
            "Beacons appear on first check-in. Queue persistence or artifact-wipe " +
                "tasks per host; implants pull them on the next beacon.",
            style = QuantumTypography.bodySmall,
            color = Muted,
        )
        Spacer(Modifier.height(12.dp))
        if (implants.isEmpty()) {
            Text("No implants beaconed yet.", color = Muted)
        }
        implants.forEach { (host, beacon) ->
            Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
                Text(host, style = QuantumTypography.titleSmall, color = Cyan)
                Text(
                    buildString {
                        append("first ${beacon.firstSeen} · last ${beacon.lastSeen} · beacons=${beacon.beacons}")
                        beacon.os?.let { append(" · $it") }
                    },
                    style = QuantumTypography.bodySmall,
                    color = SoftCyan,
                )
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilledTonalButton(onClick = {
                        ioOp("C2") {
                            c2Api.handle("persistx", JSONObject().put("host", host))
                        }
                    }) { Text("PERSIST") }
                    OutlinedButton(onClick = {
                        ioOp("OPSEC") {
                            c2Api.handle("footprint", JSONObject().put("host", host))
                        }
                    }) { Text("WIPE ARTIFACTS") }
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(16.dp))
    }
}

// ---------------------------------------------------------------------------
// Cameras — discovery, brute, snapshots
// ---------------------------------------------------------------------------

@Composable
fun CamerasPage() {
    val cameras by C2State.cameras.collectAsState()
    val scanReq by UiBus.cameraScanRequest.collectAsState()
    val scope = rememberCoroutineScope()
    var cidr by rememberSaveable { mutableStateOf(Net.localScope()) }
    var scanning by remember { mutableStateOf(false) }

    // Chat-driven sweeps land here via UiBus.
    LaunchedEffect(scanReq) {
        val req = scanReq ?: return@LaunchedEffect
        UiBus.cameraScanRequest.value = null
        req.let { cidr = it }
        scanning = true
        withContext(Dispatchers.IO) {
            C2State.setCameras(CamWar.discover(cidr, bruteCreds = true))
            C2State.audit("CAM", "camera sweep $cidr complete")
        }
        scanning = false
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Cameras", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = cidr,
            onValueChange = { cidr = it },
            label = { Text("CIDR scope") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = {
                    scanning = true
                    scope.launch {
                        withContext(Dispatchers.IO) {
                            C2State.setCameras(CamWar.discover(cidr, bruteCreds = true))
                            C2State.audit(
                                "CAM",
                                "manual sweep $cidr: ${C2State.cameras.value.size} camera(s)"
                            )
                        }
                        scanning = false
                    }
                },
                enabled = !scanning,
            ) { Text(if (scanning) "SWEEPING…" else "DISCOVER + BRUTE") }
            OutlinedButton(
                onClick = { ioOp("CAM") { c2Api.handle("camwar", JSONObject().put("cidr", cidr)) } },
                enabled = !scanning,
            ) { Text("VIA /AI API") }
        }
        if (scanning) {
            LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical = 8.dp))
        }
        Text(
            "CAM_PORTS: " + CamWar.CAM_PORTS.joinToString(","),
            style = QuantumTypography.labelSmall,
            color = Muted,
            modifier = Modifier.padding(vertical = 4.dp),
        )
        Spacer(Modifier.height(8.dp))

        if (cameras.isEmpty()) {
            Text("No cameras discovered yet — run a sweep.", color = Muted)
        }
        cameras.forEach { cam ->
            CameraCard(cam)
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun CameraCard(cam: CameraHit) {
    Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                cam.ip,
                style = QuantumTypography.titleSmall,
                color = Cyan,
                modifier = Modifier.weight(1f),
            )
            Text(
                if (cam.creds != null) "CONTROLLED" else "discovered",
                style = QuantumTypography.labelSmall,
                color = if (cam.creds != null) Ok else Muted,
            )
        }
        Text(
            buildString {
                append("vendor=${cam.vendor} · via ${cam.source}")
                cam.model?.let { append(" · $it") }
            },
            style = QuantumTypography.bodySmall,
            color = SoftCyan,
        )
        Text(
            "ports: " + cam.ports.joinToString(",") + (cam.creds?.let { " · creds=$it" } ?: ""),
            style = QuantumTypography.bodySmall,
            color = Muted,
        )
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilledTonalButton(onClick = {
                ioOp("CAM") {
                    c2Api.handle(
                        "camshot",
                        JSONObject()
                            .put("ip", cam.ip)
                            .put("vendor", cam.vendor)
                            .put("creds", cam.creds ?: ""),
                    )
                }
            }) { Text("SNAPSHOT") }
            OutlinedButton(onClick = {
                ioOp("CAM") {
                    val creds = CamWar.checkCreds(cam.ip, cam.vendor)
                    if (creds != null) {
                        C2State.setCameras(
                            C2State.cameras.value.map {
                                if (it.ip == cam.ip) it.copy(creds = creds) else it
                            }
                        )
                        "brute CRACKED ${cam.ip} ($creds)"
                    } else {
                        "brute ${cam.ip}: no default creds"
                    }
                }
            }) { Text("BRUTE CREDS") }
        }
    }
}

// ---------------------------------------------------------------------------
// Network — interfaces, MAC, VPN/proxy, DNS, geolocation
// ---------------------------------------------------------------------------

@Composable
fun NetworkPage() {
    val scope = rememberCoroutineScope()
    var snap by remember { mutableStateOf<NetDiag.Snapshot?>(null) }
    var loading by remember { mutableStateOf(false) }
    var dnsHost by rememberSaveable { mutableStateOf("") }
    var dnsResults by remember { mutableStateOf<List<Pair<String, NetDiag.GeoInfo?>>>(emptyList()) }
    var dnsBusy by remember { mutableStateOf(false) }

    fun load() {
        loading = true
        scope.launch {
            snap = withContext(Dispatchers.IO) { NetDiag.snapshot() }
            loading = false
        }
    }

    LaunchedEffect(Unit) { load() }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Network", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))

        Button(onClick = { load() }, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Outlined.Refresh, contentDescription = null)
            Spacer(Modifier.width(6.dp))
            Text(if (loading) "SCANNING…" else "REFRESH")
        }
        Spacer(Modifier.height(8.dp))

        val s = snap
        if (s != null) {
            StatusCard("VPN / proxy", buildString {
                append(if (s.vpnActive) "VPN ACTIVE" else "no VPN tunnel detected")
                append(" · proxy: ")
                append(s.proxy ?: "none")
            })
            StatusCard("Gateway", s.gateway ?: "unknown")
            StatusCard(
                "Public egress",
                buildString {
                    append(s.publicIp ?: "unresolvable")
                    s.geo?.line()?.let { append(" — $it") }
                },
            )
        }

        Spacer(Modifier.height(8.dp))

        // ---- DNS lookup + per-address location -----------------------------
        Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
            Text("DNS lookup", style = QuantumTypography.titleSmall, color = SoftCyan)
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = dnsHost,
                onValueChange = { dnsHost = it },
                label = { Text("hostname or IP") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = {
                    dnsBusy = true
                    scope.launch {
                        val host = dnsHost
                        dnsResults = withContext(Dispatchers.IO) {
                            NetDiag.dnsLookup(host).map { addr ->
                                addr to if (NetDiag.isPublicIp(addr)) NetDiag.geolocate(addr) else null
                            }
                        }
                        dnsBusy = false
                    }
                },
                enabled = !dnsBusy && dnsHost.isNotBlank(),
            ) { Text(if (dnsBusy) "RESOLVING…" else "RESOLVE") }
            dnsResults.forEach { (addr, geo) ->
                Text(
                    addr + (geo?.let { " — ${it.line()}" } ?: " — private/LAN (no external lookup)"),
                    style = QuantumTypography.bodySmall,
                    color = SoftCyan,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
        }
        Spacer(Modifier.height(8.dp))

        // ---- interfaces -----------------------------------------------------
        Text("Interfaces", style = QuantumTypography.titleSmall, color = SoftCyan)
        Spacer(Modifier.height(8.dp))
        (s?.ifaces ?: emptyList()).forEach { f ->
            Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        f.name,
                        style = QuantumTypography.titleSmall,
                        color = Cyan,
                        modifier = Modifier.weight(1f),
                    )
                    val tags = buildList {
                        if (!f.up) add("down")
                        if (f.loopback) add("loopback")
                        if (f.vpn) add("VPN")
                        if (f.up && !f.loopback && !f.vpn) add("active")
                    }
                    Text(tags.joinToString(" · "), style = QuantumTypography.labelSmall, color = Muted)
                }
                Text("IPv4: ${f.ipv4 ?: "—"}", style = QuantumTypography.bodySmall, color = SoftCyan)
                Text("IPv6: ${f.ipv6 ?: "—"}", style = QuantumTypography.bodySmall, color = SoftCyan)
                Text("MAC:  ${f.mac ?: "n/a"}", style = QuantumTypography.bodySmall, color = SoftCyan)
            }
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(16.dp))
    }
}

// ---------------------------------------------------------------------------
// Exploits — fingerprint, zero-check, fire + MITRE coverage
// ---------------------------------------------------------------------------

@Composable
fun ExploitsPage() {
    val audit by C2State.audit.collectAsState()
    val scope = rememberCoroutineScope()
    var target by rememberSaveable { mutableStateOf("") }
    var cve by rememberSaveable { mutableStateOf("CVE-2017-0144") }
    var lastResult by remember { mutableStateOf("results of the last operation appear here") }
    var busy by remember { mutableStateOf(false) }

    fun run(label: String, block: () -> JSONObject) {
        busy = true
        scope.launch {
            val out = withContext(Dispatchers.IO) {
                try {
                    block().toString(2)
                } catch (e: Exception) {
                    """{"error": "${e.message}"}"""
                }
            }
            lastResult = out
            C2State.audit(label, out.take(300))
            busy = false
        }
    }

    val covered = remember(audit) {
        com.projectzerodays.quantumcli.c2.MitreMapper.coverage(audit)
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Exploits", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = target,
            onValueChange = { target = it },
            label = { Text("Target IP") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = cve,
            onValueChange = { cve = it },
            label = { Text("CVE / weapon id (ZERO_DAY_REGISTRY)") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                onClick = { run("RECON") { c2Api.handle("fingerprint", JSONObject().put("ip", target)) } },
                enabled = !busy && target.isNotBlank(),
            ) { Text("FINGERPRINT") }
            OutlinedButton(
                onClick = { run("RECON") { c2Api.handle("zerocheck", JSONObject().put("ip", target)) } },
                enabled = !busy && target.isNotBlank(),
            ) { Text("ZERO-CHECK") }
        }
        Spacer(Modifier.height(8.dp))
        Button(
            onClick = {
                run("ATK") {
                    c2Api.handle(
                        "fire",
                        JSONObject().put("cve", cve).put("ip", target),
                    )
                }
            },
            enabled = !busy && target.isNotBlank() && cve.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) { Text(if (busy) "WORKING…" else "FIRE $cve") }

        Spacer(Modifier.height(12.dp))
        Text("Last result", style = QuantumTypography.titleSmall, color = SoftCyan)
        Column(
            Modifier
                .fillMaxWidth()
                .quantumPanel()
                .padding(10.dp)
                .height(200.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            Text(lastResult, style = QuantumTypography.bodySmall, color = Softest, fontSize = 11.sp)
        }

        Spacer(Modifier.height(12.dp))
        Text("${covered.size} MITRE techniques covered in the ledger.", color = Muted)
        covered.take(8).forEach { tid ->
            StatusCard(tid, "covered")
        }
        Spacer(Modifier.height(16.dp))
    }
}

// ---------------------------------------------------------------------------
// Loot — sealed vault management
// ---------------------------------------------------------------------------

@Composable
fun LootPage() {
    val loot by C2State.loot.collectAsState()
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Loot", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))
        FilledTonalButton(onClick = { ioOp("OK") {
            C2State.scanLoot()
            "${C2State.loot.value.size} sealed item(s) indexed"
        } }) { Text("REFRESH VAULT") }
        Spacer(Modifier.height(8.dp))
        if (loot.isEmpty()) {
            Text("Sealed loot appears when an implant exfiltrates via /r drop.", color = Muted)
        }
        loot.forEach { entry ->
            Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
                Text(entry.fileName, style = QuantumTypography.titleSmall, color = Cyan)
                Text(
                    "host=${entry.host} · ${entry.bytes} B · ${entry.kind} · ${entry.ts}",
                    style = QuantumTypography.bodySmall,
                    color = SoftCyan,
                )
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilledTonalButton(onClick = {
                        ioOp("LOOT") {
                            val out = Grayfish.unseal(File(entry.sealedPath))
                            C2State.scanLoot()
                            out?.let { "unsealed -> ${it.name}" } ?: "unseal failed (key mismatch?)"
                        }
                    }) { Text("UNSEAL") }
                    OutlinedButton(onClick = {
                        ioOp("LOOT") {
                            val f = File(entry.sealedPath)
                            val ok = f.delete()
                            C2State.scanLoot()
                            if (ok) "deleted ${entry.fileName}" else "delete failed ${entry.fileName}"
                        }
                    }) { Text("DELETE") }
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(16.dp))
    }
}

// ---------------------------------------------------------------------------
// Chat — gated page + overlay with real input
// ---------------------------------------------------------------------------

@Composable
fun ChatPage() {
    val actions = LocalUiActions.current
    if (!AiGate.ready()) {
        Column(
            Modifier
                .fillMaxSize()
                .padding(20.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                Icons.Outlined.Lock,
                contentDescription = null,
                tint = Muted,
                modifier = Modifier.size(48.dp),
            )
            Spacer(Modifier.height(12.dp))
            Text("Chat is locked", style = QuantumTypography.titleLarge, color = Cyan)
            Text(
                "Configure the Abliteration.ai API key or download the local fallback " +
                    "model to enable the AI chat. Manual mode keeps every dashboard " +
                    "control available.",
                style = QuantumTypography.bodyMedium,
                color = Muted,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(vertical = 8.dp),
            )
            Button(onClick = actions.openWizard) { Text("Open setup wizard") }
            TextButton(onClick = actions.openManual) { Text("Read the manual") }
        }
    } else {
        ChatOverlay(
            Modifier
                .fillMaxSize()
                .padding(20.dp),
            onClose = {},
            onAction = actions.onChatAction,
        )
    }
}

@Composable
fun ChatOverlay(
    modifier: Modifier,
    onClose: () -> Unit,
    onAction: (IntentParser.ChatAction) -> Unit = {},
) {
    var text by rememberSaveable { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()
    val msgs by ChatController.messages.collectAsState()
    val busy by ChatController.busy.collectAsState()
    val mode = AiGate.modeLabel()

    LaunchedEffect(msgs.size) {
        if (msgs.isNotEmpty()) listState.animateScrollToItem(msgs.size - 1)
    }

    Column(modifier.background(Panel).padding(14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("chat · $mode", style = QuantumTypography.titleSmall, color = SoftCyan)
            Spacer(Modifier.weight(1f))
            IconButton(onClick = { ChatController.clear() }) {
                Icon(Icons.Outlined.Delete, contentDescription = "Clear chat", tint = Muted)
            }
            IconButton(onClick = onClose) {
                Icon(Icons.Outlined.Close, contentDescription = "Close", tint = SoftCyan)
            }
        }
        LazyColumn(state = listState, modifier = Modifier.weight(1f)) {
            items(msgs) { msg ->
                Text(
                    (if (msg.role == "user") "> " else "") + msg.content,
                    style = QuantumTypography.bodySmall,
                    color = if (msg.role == "user") Cyan else Softest,
                )
                Spacer(Modifier.height(4.dp))
            }
            if (busy) {
                item {
                    Text("…", style = QuantumTypography.bodySmall, color = Muted)
                }
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("message or /ai command", style = QuantumTypography.bodySmall) },
                singleLine = true,
            )
            IconButton(
                onClick = {
                    val t = text
                    text = ""
                    ChatController.send(t, scope, onAction)
                },
                enabled = !busy && text.isNotBlank(),
            ) {
                Icon(Icons.Outlined.Send, contentDescription = "Send", tint = Cyan)
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Settings — AI, server, overlord defaults, updates, manual
// ---------------------------------------------------------------------------

@Composable
fun SettingsPage() {
    val actions = LocalUiActions.current
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val settings by QuantSettings.state.collectAsState()
    val serverRunning by QuantServerManager.running.collectAsState()
    var c2Port by rememberSaveable { mutableStateOf(settings.c2Port.toString()) }
    var apiUrl by rememberSaveable { mutableStateOf(settings.apiUrl) }
    var apiKey by rememberSaveable { mutableStateOf(settings.apiKey) }
    var model by rememberSaveable { mutableStateOf(settings.model) }
    var updateResult by remember { mutableStateOf<UpdateChecker.Result?>(null) }
    var checking by remember { mutableStateOf(false) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Text("Settings", style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(12.dp))

        // ---- AI ---------------------------------------------------------
        Text("AI brain", style = QuantumTypography.titleSmall, color = SoftCyan)
        Spacer(Modifier.height(4.dp))
        listOf(
            AiClient.MODE_ONLINE to "Abliteration.ai (cloud)",
            AiClient.MODE_LOCAL to "Local on-device model",
            AiClient.MODE_DETERMINISTIC to "Manual / no AI",
        ).forEach { (mode, label) ->
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                RadioButton(
                    selected = settings.aiMode == mode,
                    onClick = { QuantSettings.update { it.copy(aiMode = mode) } },
                )
                Text(label, color = Softest, style = QuantumTypography.bodyMedium)
            }
        }
        if (settings.aiMode == AiClient.MODE_LOCAL && !AiClient.localAvailable()) {
            Button(
                onClick = { AiModelDownloader.start() },
                modifier = Modifier.padding(vertical = 4.dp),
            ) { Text("Download local fallback model") }
        }
        OutlinedTextField(
            value = apiUrl, onValueChange = { apiUrl = it },
            label = { Text("API URL") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(6.dp))
        OutlinedTextField(
            value = apiKey, onValueChange = { apiKey = it },
            label = { Text("API key") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(6.dp))
        OutlinedTextField(
            value = model, onValueChange = { model = it },
            label = { Text("Model") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(8.dp))
        Button(onClick = {
            QuantSettings.update {
                it.copy(apiUrl = apiUrl.trim(), apiKey = apiKey.trim(), model = model.trim())
            }
            C2State.audit("AI", "settings saved (endpoint ${apiUrl.trim()}, model ${model.trim()})")
        }) { Text("SAVE AI SETTINGS") }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 12.dp))

        // ---- C2 server ----------------------------------------------------
        Text("C2 server", style = QuantumTypography.titleSmall, color = SoftCyan)
        Spacer(Modifier.height(4.dp))
        Text(
            "status: " + (if (serverRunning) "running" else "stopped") +
                (if (serverRunning) " at http://${c2Api.c2HostPort()}/dash" else ""),
            style = QuantumTypography.bodySmall,
            color = if (serverRunning) Ok else Muted,
        )
        OutlinedTextField(
            value = c2Port,
            onValueChange = { c2Port = it.filter { c -> c.isDigit() } },
            label = { Text("C2 port") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(Modifier.padding(vertical = 6.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                val port = c2Port.toIntOrNull() ?: settings.c2Port
                QuantSettings.update { it.copy(c2Port = port) }
                ioOp("C2") {
                    if (QuantServerManager.start(port)) "C2 restarted on :$port"
                    else "C2 start failed on :$port"
                }
            }) { Text("APPLY / RESTART") }
            OutlinedButton(onClick = { ioOp("C2") { QuantServerManager.stop(); "C2 stopped" } }) {
                Text("STOP")
            }
        }
        SettingSwitch(
            "Auto-start C2 server on app open",
            settings.autostart,
        ) { QuantSettings.update { it.copy(autostart = it.autostart.not()) } }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 12.dp))

        // ---- overlord defaults ---------------------------------------------
        Text("Overlord defaults", style = QuantumTypography.titleSmall, color = SoftCyan)
        Spacer(Modifier.height(4.dp))
        SettingSwitch(
            "Camera-only acts",
            settings.overlordCameraOnly,
        ) { QuantSettings.update { it.copy(overlordCameraOnly = it.overlordCameraOnly.not()) } }
        Text(
            "Interval: ${settings.overlordIntervalSec}s",
            color = Softest,
            style = QuantumTypography.bodySmall,
        )
        Slider(
            value = settings.overlordIntervalSec.toFloat(),
            onValueChange = { QuantSettings.update { s -> s.copy(overlordIntervalSec = it.toInt()) } },
            valueRange = 10f..300f,
            steps = 57,
        )
        SettingSwitch(
            "Auto-download local AI fallback on app open",
            settings.autoDownload,
        ) { QuantSettings.update { it.copy(autoDownload = it.autoDownload.not()) } }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 12.dp))

        // ---- updates --------------------------------------------------------
        Text("Updates", style = QuantumTypography.titleSmall, color = SoftCyan)
        Spacer(Modifier.height(4.dp))
        Text(
            "installed: v${com.projectzerodays.quantumcli.BuildConfig.VERSION_NAME} " +
                "(${com.projectzerodays.quantumcli.BuildConfig.FLAVOR})",
            style = QuantumTypography.bodySmall,
            color = Muted,
        )
        Spacer(Modifier.height(8.dp))
        Button(
            onClick = {
                checking = true
                scope.launch {
                    updateResult = withContext(Dispatchers.IO) { UpdateChecker.check() }
                    updateResult?.let { C2State.audit("C2", it.headline()) }
                    checking = false
                }
            },
            enabled = !checking,
        ) { Text(if (checking) "CHECKING…" else "CHECK FOR UPDATES") }
        updateResult?.let { r ->
            Column(Modifier.fillMaxWidth().quantumPanel().padding(12.dp)) {
                Text(r.headline(), style = QuantumTypography.bodyMedium, color = Softest)
                r.notes?.let {
                    Text(
                        it,
                        style = QuantumTypography.bodySmall,
                        color = Muted,
                        modifier = Modifier.padding(top = 6.dp),
                    )
                }
                r.url?.let {
                    Text(
                        "Open release page →",
                        style = QuantumTypography.bodySmall,
                        color = Cyan,
                        modifier = Modifier
                            .padding(top = 6.dp)
                            .clickable { openUrl(ctx, it) },
                    )
                }
            }
        }

        HorizontalDivider(color = Cyan.copy(0.18f), modifier = Modifier.padding(vertical = 12.dp))

        // ---- wizard / manual --------------------------------------------------
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = actions.openWizard, modifier = Modifier.weight(1f)) {
                Text("SETUP WIZARD")
            }
            OutlinedButton(onClick = actions.openManual, modifier = Modifier.weight(1f)) {
                Text("APP MANUAL")
            }
        }
        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun SettingSwitch(label: String, checked: Boolean, onToggle: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            label,
            color = Softest,
            style = QuantumTypography.bodyMedium,
            modifier = Modifier.weight(1f),
        )
        Switch(checked = checked, onCheckedChange = { onToggle() })
    }
}

// ---------------------------------------------------------------------------
// App manual — how-to + troubleshooting
// ---------------------------------------------------------------------------

@Composable
fun ManualDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Panel,
        title = { Text("QUANTUM-CLI manual", color = Cyan) },
        text = {
            Column(
                Modifier
                    .verticalScroll(rememberScrollState())
                    .fillMaxWidth(),
            ) {
                ManualSection("HOW TO") {
                    M("1. Setup — sidebar → Setup wizard. Choose Abliteration.ai (paste your key), Local model (auto-downloads the on-device fallback once), or Skip for manual-only mode.")
                    M("2. Auto Run — Dashboard → AUTO RUN. Unlocks once AI is configured. Camera-only restricts the act whitelist to camera operations; the interval slider controls the decision cadence.")
                    M("3. Manual ops — every page has controls. Implants: queue PERSIST / WIPE tasks per host. Cameras: DISCOVER + BRUTE, per-camera SNAPSHOT. Exploits: FINGERPRINT, ZERO-CHECK, FIRE. Loot: UNSEAL / DELETE.")
                    M("4. Chat — natural language ('scan for cameras', 'start background job', 'kill-switch') or bare /ai commands ('run task fingerprint 10.0.0.5'). Locked until AI is configured.")
                    M("5. Kill switch — Dashboard → ARM queues wipe/die tasks on every implant and halts the overlord. DISARM stops further wipes.")
                    M("6. Network — device interfaces (IPv4/IPv6/MAC), VPN and proxy status, gateway, public egress with location, and DNS resolution with per-address location. Private addresses are never sent to external geo services.")
                    M("7. Web C2 — while the server runs, a browser dashboard is served at http://<device-ip>:<port>/dash.")
                    M("8. Updates — Settings → CHECK FOR UPDATES compares your build with the latest GitHub release and flags patch/minor bumps as safe.")
                }
                Spacer(Modifier.height(8.dp))
                ManualSection("TROUBLESHOOTING") {
                    M("Chat locked → finish the Setup wizard; verify the key in Settings, or wait for the local model download (progress shows in the Dashboard console).")
                    M("Auto Run greyed → no AI configured. Open the wizard and pick cloud or local.")
                    M("Camera sweep empty → device and cameras must share the LAN (/24); adjust the CIDR field. WS-Discovery needs multicast-enabled Wi-Fi.")
                    M("Snapshot fails → the vendor is unrecognized; run BRUTE CREDS first to obtain credentials, then retry.")
                    M("FIRE returns an error → verify the CVE id exists in the ZERO_DAY registry and the target passes ZERO-CHECK.")
                    M("Update check fails → the network or VPN blocks api.github.com; retry from an unrestricted network.")
                    M("Unseal fails → logs/.lootkey is immutable by design; if it was deleted, previously sealed loot cannot be decrypted.")
                    M("Kill-switch armed by accident → press DISARM. Already-queued wipe tasks on implants cannot be recalled.")
                    M("Model download stalls → it retries on next app open; check free storage (needs ~1.5 GB) and retry from Settings.")
                }
            }
        },
        confirmButton = { Button(onClick = onDismiss) { Text("Close") } },
    )
}

@Composable
private fun ManualSection(title: String, content: @Composable () -> Unit) {
    Text(title, style = QuantumTypography.titleSmall, color = Cyan)
    Spacer(Modifier.height(6.dp))
    content()
}

@Composable
private fun M(text: String) {
    Text(
        text,
        style = QuantumTypography.bodySmall,
        color = Softest,
        modifier = Modifier.padding(vertical = 3.dp),
    )
}

// ---------------------------------------------------------------------------
// Shared widgets
// ---------------------------------------------------------------------------

@Composable
fun StatusCard(label: String, value: String) {
    Column(
        Modifier
            .fillMaxWidth()
            .quantumPanel()
            .padding(12.dp),
    ) {
        Text(label, style = QuantumTypography.labelMedium, color = SoftCyan)
        Text(value, style = QuantumTypography.bodyMedium, color = Softest)
    }
}
