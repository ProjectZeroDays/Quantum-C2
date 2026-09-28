package com.projectzerodays.quantumcli.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubble
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.PermanentDrawerSheet
import androidx.compose.material3.PermanentScaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberModalNavigationDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.projectzerodays.quantumcli.c2.C2State
import com.projectzerodays.quantumcli.ui.theme.Cyan
import com.projectzerodays.quantumcli.ui.theme.Muted
import com.projectzerodays.quantumcli.ui.theme.Panel
import com.projectzerodays.quantumcli.ui.theme.QuantumTypography
import com.projectzerodays.quantumcli.ui.theme.SoftCyan
import com.projectzerodays.quantumcli.ui.theme.Softest

/**
 * Root composable: a permanent sidebar drawer with the 7 page destinations,
 * bottom links (Star on GitHub, Report Bug, Contribute, Wiki) that collapse
 * into a top-bar icon for narrow windows, a chat floating-action button,
 * and the page host body. The sidebar uses the exact democ2.html theme.
 */
@Composable
fun QuantumUi() {
    val drawerState = rememberModalNavigationDrawerState()
    var selectedPage by rememberSaveable { mutableStateOf(Page.DASHBOARD) }
    val ctx = LocalContext.current

    val markdownLinks = listOf(
        DrawerLink("Star on GitHub", Icons.Outlined.Star,
            "https://github.com/projectzerodays/Quantum-CLI"),
        DrawerLink("Report a Bug", Icons.Outlined.ChatBubble,
            "https://github.com/projectzerodays/Quantum-CLI/issues"),
        DrawerLink("Contribute", Icons.Outlined.ChatBubble,
            "https://github.com/projectzerodays/Quantum-CLI/pulls"),
        DrawerLink("Wiki", Icons.Outlined.ChatBubble,
            "https://github.com/projectzerodays/Quantum-CLI/wiki"),
    )

    val navItems = Page.entries.map { NavItem(it.title, it.icon, it) }

    var showChat by rememberSaveable { mutableStateOf(false) }

    PermanentScaffold(
        permanentNavigationDrawer = {
            PermanentDrawerSheet(
                drawerState = drawerState,
                modifier = Modifier
                    .width(260.dp)
                    .background(Panel)
            ) {
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
                    Spacer(Modifier.height(8.dp))
                    navItems.forEach { item ->
                        NavRow(
                            icon = item.icon,
                            label = item.label,
                            selected = item.page == selectedPage,
                            onClick = { selectedPage = item.page },
                        )
                    }
                    Spacer(Modifier.height(24.dp))
                    Text(
                        "Project Links",
                        style = QuantumTypography.labelSmall,
                        color = Muted,
                        modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
                    )
                    markdownLinks.forEach { link ->
                        LinkRow(link, ctx)
                    }
                    Spacer(Modifier.height(16.dp))
                }
            }
        },
    ) { innerPadding ->
        val pageContent: @Composable (PaddingValues) -> Unit = { padding ->
            when (selectedPage) {
                Page.DASHBOARD -> DashboardPage(padding, selectedPage)
                Page.IMPLANTS -> ImplantsPage(padding, selectedPage)
                Page.CAMERAS -> CamerasPage(padding, selectedPage)
                Page.EXPLOITS -> ExploitsPage(padding, selectedPage)
                Page.LOOT -> LootPage(padding, selectedPage)
                Page.CHAT -> ChatPage(padding, selectedPage)
                Page.SETTINGS -> SettingsPage(padding, selectedPage)
            }
        }

        Box(Modifier.fillMaxSize()) {
            pageContent(innerPadding)

            // Chat FAB / overlay toggle in the top bar
            TopAppBar(
                title = { Text(selectedPage.title, style = QuantumTypography.titleMedium, color = Softest) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
                navigationIcon = {
                    IconButton(onClick = { /* drawer open handled by PermanentScaffold */ }) {
                        Icon(
                            Icons.Outlined.Star,
                            contentDescription = "Menu",
                            tint = Cyan,
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { showChat = !showChat }) {
                        val tint = if (showChat) Cyan else SoftCyan
                        Icon(Icons.Outlined.ChatBubble, contentDescription = "Chat", tint = tint)
                    }
                },
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .fillMaxWidth(),
            )

            if (showChat) {
                ChatOverlay(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .size(width = 360.dp, height = 480.dp),
                    onClose = { showChat = false },
                )
            }
        }
    }
}

private data class DrawerLink(
    val label: String,
    val icon: ImageVector,
    val url: String,
)

private data class NavItem(val label: String, val icon: ImageVector, val page: Page)

@Composable
private fun NavRow(
    icon: ImageVector,
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val bg = if (selected) Brush.horizontalGradient(listOf(Cyan.copy(0.12f), Color.Transparent))
    else Brush.horizontalGradient(listOf(Color.Transparent, Color.Transparent))
    Row(
        Modifier
            .fillMaxWidth()
            .background(bg)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = if (selected) Cyan else SoftCyan,
            modifier = Modifier.size(22.dp),
        )
        Spacer(Modifier.width(14.dp))
        Text(
            label,
            style = QuantumTypography.bodyLarge,
            color = if (selected) Cyan else Softest,
        )
    }
}

@Composable
private fun LinkRow(link: DrawerLink, ctx: android.content.Context) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable {
                val intent = android.content.Intent(android.content.Intent.ACTION_VIEW,
                    android.net.Uri.parse(link.url))
                ctx.startActivity(intent)
            }
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            imageVector = link.icon,
            contentDescription = link.label,
            tint = SoftCyan,
            modifier = Modifier.size(18.dp),
        )
        Spacer(Modifier.width(12.dp))
        Text(
            link.label,
            style = QuantumTypography.bodyMedium,
            color = Softest,
            fontSize = 13.sp,
            textAlign = TextAlign.Start,
        )
    }
}

/** Simple page shell: title + status cards sourced from live C2State. */
@Composable
fun DashboardPage(padding: PaddingValues, page: Page) {
    val state = C2State
    val implants by state.implants.collectAsState()
    val audit by state.audit.collectAsState()
    val decisions by state.decisions.collectAsState()
    val killswitch by state.killswitch.collectAsState()
    Column(
        Modifier
            .padding(padding)
            .padding(20.dp)
            .verticalScroll(rememberScrollState()),
    ) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        StatusCard("Implants", "${implants.size} active")
        StatusCard("Kill-switch", if (killswitch) "ARMED" else "safe")
        StatusCard("Decisions", "${decisions.size} total")
        StatusCard("Audit events", "${audit.size} logged")
    }
}

@Composable
fun ImplantsPage(padding: PaddingValues, page: Page) {
    val state = C2State
    val implants by state.implants.collectAsState()
    Column(Modifier.padding(padding).padding(20.dp)) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        if (implants.isEmpty()) {
            Text("No implants beaconed yet. They appear here on first check-in.", color = Muted)
        }
        implants.forEach { (host, beacon) ->
            StatusCard(host, "last seen ${beacon.lastSeen}  | beacons=${beacon.beacons}")
        }
    }
}

@Composable
fun CamerasPage(padding: PaddingValues, page: Page) {
    Column(Modifier.padding(padding).padding(20.dp)) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        Text("Camera discovery runs from Scan on this page or via the chat 'scan for cameras'.", color = Muted)
        Spacer(Modifier.height(8.dp))
        Text("CAM_PORTS: " + com.projectzerodays.quantumcli.ops.CamWar.CAM_PORTS.joinToString(","), color = SoftCyan)
    }
}

@Composable
fun ExploitsPage(padding: PaddingValues, page: Page) {
    val state = C2State
    val audit by state.audit.collectAsState()
    val covered by androidx.compose.runtime.derivedStateOf {
        com.projectzerodays.quantumcli.c2.MitreMapper.coverage(audit)
    }
    Column(Modifier.padding(padding).padding(20.dp)) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        Text("${covered.size} MITRE techniques covered in ledger.", color = Muted)
        Spacer(Modifier.height(8.dp))
        covered.take(8).forEach { tid ->
            StatusCard(tid, "covered")
        }
    }
}

@Composable
fun LootPage(padding: PaddingValues, page: Page) {
    val state = C2State
    val loot by state.loot.collectAsState()
    Column(Modifier.padding(padding).padding(20.dp)) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        if (loot.isEmpty()) {
            Text("Sealed loot appears when an implant exfiltrates via /r drop.", color = Muted)
        }
        loot.forEach { entry ->
            StatusCard(entry.host, "${entry.fileName} (${entry.bytes}B) ${entry.kind}")
        }
    }
}

@Composable
fun ChatPage(padding: PaddingValues, page: Page) {
    ChatOverlay(Modifier.fillMaxSize(), onClose = {})
}

@Composable
fun SettingsPage(padding: PaddingValues, page: Page) {
    Column(Modifier.padding(padding).padding(20.dp)) {
        Text(page.title, style = QuantumTypography.displaySmall, color = Cyan)
        Spacer(Modifier.height(16.dp))
        StatusCard("AI mode", "set in chat overlay / top-bar chat icon")
        StatusCard("C2 port", "8443")
        StatusCard("Endpoint", "https://api.abliteration.ai/v1")
    }
}

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
    Spacer(Modifier.height(8.dp))
}

/** Floating chat overlay driven by IntentParser (AI or deterministic). */
@Composable
fun ChatOverlay(modifier: Modifier, onClose: () -> Unit) {
    var text by rememberSaveable { mutableStateOf("") }
    val history = com.projectzerodays.quantumcli.ai.ChatController
    val msgs by history.messages.collectAsState()
    Column(
        modifier
            .background(Panel)
            .padding(14.dp),
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("chat", style = QuantumTypography.titleSmall, color = SoftCyan)
            IconButton(onClick = onClose) { Icon(Icons.Outlined.Close, contentDescription = "close", tint = SoftCyan) }
        }
        Spacer(Modifier.height(6.dp))
        Column(Modifier.weight(1f)) {
            msgs.forEach { msg ->
                Text(
                    "${if (msg.role == "user") ">" else ""} ${msg.content}",
                    style = QuantumTypography.bodySmall,
                    color = if (msg.role == "user") Cyan else Softest,
                )
                Spacer(Modifier.height(4.dp))
            }
        }
        Text(
            text,
            style = QuantumTypography.bodyLarge,
            color = Softest,
            modifier = Modifier
                .fillMaxWidth()
                .background(Cyan.copy(0.08f))
                .padding(8.dp),
        )
    }
}
