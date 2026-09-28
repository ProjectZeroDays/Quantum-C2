package com.projectzerodays.quantumcli.ui.theme

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ------------------------------------------------------------------ palette
/** #020712 -> #020308 vertical gradient background. */
val QuantumBg0 = Color(0xFF020712)
val QuantumBg1 = Color(0xFF020308)

/** cyan accent #00e5ff. */
val Cyan = Color(0xFF00E5FF)

/** soft accents #9fd6ee / #cfefff. */
val SoftCyan = Color(0xFF9FD6EE)
val Softest = Color(0xFFCFEFFF)

/** muted #4f6f86. */
val Muted = Color(0xFF4F6F86)

/** danger #ff4b6b. */
val Danger = Color(0xFFFF4B6B)

/** card panels rgba(0,20,40,0.9). */
val Panel = Color(0xE6001428)

val PanelBright = Color(0xFF04182C)
val Ok = Color(0xFF3DFFA2)

private val DarkScheme = darkColorScheme(
    primary = Cyan,
    onPrimary = Color(0xFF00252B),
    primaryContainer = Color(0xFF04222E),
    onPrimaryContainer = Softest,
    secondary = SoftCyan,
    onSecondary = Color(0xFF06222F),
    secondaryContainer = Panel,
    onSecondaryContainer = Softest,
    tertiary = Softest,
    onTertiary = Color(0xFF06222F),
    background = QuantumBg1,
    onBackground = Softest,
    surface = QuantumBg1,
    onSurface = Softest,
    surfaceVariant = Panel,
    onSurfaceVariant = SoftCyan,
    outline = Muted,
    outlineVariant = Color(0xFF14324A),
    error = Danger,
    onError = Color(0xFF2B0710),
    errorContainer = Color(0xFF3A0E1A),
    onErrorContainer = Danger,
)

private val mono = FontFamily.Monospace

private fun monoStyle(size: Int, lineH: Int = size + 4, weight: Int? = null) = TextStyle(
    fontFamily = mono,
    fontSize = size.sp,
    lineHeight = lineH.sp,
    fontWeight = weight?.let { androidx.compose.ui.text.font.FontWeight(it) },
)

val QuantumTypography = Typography(
    displayLarge = monoStyle(48, 52),
    displayMedium = monoStyle(40, 44),
    displaySmall = monoStyle(32, 36),
    headlineLarge = monoStyle(26, 30),
    headlineMedium = monoStyle(22, 26),
    headlineSmall = monoStyle(18, 22),
    titleLarge = monoStyle(17, 22),
    titleMedium = monoStyle(15, 20),
    titleSmall = monoStyle(13, 18),
    bodyLarge = monoStyle(14),
    bodyMedium = monoStyle(13),
    bodySmall = monoStyle(11),
    labelLarge = monoStyle(13, 16),
    labelMedium = monoStyle(11, 14),
    labelSmall = monoStyle(10, 13),
)

@Composable
fun QuantumTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkScheme,
        typography = QuantumTypography,
        content = content
    )
}

// ------------------------------------------------------------- decorations
/** Full-screen dark gradient (#020712 -> #020308). */
fun Modifier.quantumBackground(): Modifier = drawBehind {
    drawRect(
        Brush.verticalGradient(
            listOf(QuantumBg0, QuantumBg1),
            startY = 0f,
            endY = size.height * 1.4f
        )
    )
}

/** Subtle cyan radial glow drawn behind the composable. */
fun Modifier.quantumGlow(
    color: Color = Cyan,
    alpha: Float = 0.16f,
): Modifier = drawBehind {
    val r = size.maxDimension
    drawCircle(
        brush = Brush.radialGradient(
            colors = listOf(color.copy(alpha = alpha), Color.Transparent),
            center = Offset(size.width / 2f, size.height / 4f),
            radius = r
        ),
        radius = r,
        center = Offset(size.width / 2f, size.height / 4f)
    )
}

/** Card panel on rgba(0,20,40,0.9) with a cyan hairline border + glow. */
fun Modifier.quantumPanel(shape: Shape = RoundedCornerShape(10.dp)): Modifier = this
    .clip(shape)
    .background(Panel, shape)
    .border(1.dp, Cyan.copy(alpha = 0.22f), shape)
    .quantumGlow(alpha = 0.07f)

@Composable
fun QCard(
    modifier: Modifier = Modifier,
    title: String? = null,
    contentPadding: PaddingValues = PaddingValues(14.dp),
    content: @Composable ColumnScope.() -> Unit,
) {
    androidx.compose.foundation.layout.Column(
        modifier = modifier
            .quantumPanel()
            .padding(contentPadding)
    ) {
        if (title != null) {
            androidx.compose.material3.Text(
                text = title,
                style = QuantumTypography.titleSmall,
                color = SoftCyan,
                modifier = Modifier
                    .padding(bottom = 8.dp)
                    .border(
                        Dp.Hairline,
                        Cyan.copy(alpha = 0.25f),
                        RoundedCornerShape(2.dp)
                    )
                    .padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
        content()
    }
}
