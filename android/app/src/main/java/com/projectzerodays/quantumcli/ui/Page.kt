package com.projectzerodays.quantumcli.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.BugReport
import androidx.compose.material.icons.outlined.Chat
import androidx.compose.material.icons.outlined.Code
import androidx.compose.material.icons.outlined.Dashboard
import androidx.compose.material.icons.outlined.Devices
import androidx.compose.material.icons.outlined.Extension
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material.icons.outlined.Videocam
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.ui.graphics.vector.ImageVector

/** Sidebar destination pages. */
enum class Page(val title: String, val icon: ImageVector) {
    DASHBOARD("Dashboard", Icons.Outlined.Dashboard),
    IMPLANTS("Implants", Icons.Outlined.Devices),
    CAMERAS("Cameras", Icons.Outlined.Videocam),
    NETWORK("Network", Icons.Outlined.Wifi),
    EXPLOITS("Exploits", Icons.Outlined.BugReport),
    LOOT("Loot", Icons.Outlined.Inventory2),
    CHAT("Chat", Icons.Outlined.Chat),
    AGENTS("Agents", Icons.Outlined.SmartToy),
    SKILLS("Skills", Icons.Outlined.Extension),
    TERMINAL("Terminal", Icons.Outlined.Code),
    SETTINGS("Settings", Icons.Outlined.Settings),
}
