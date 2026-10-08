# Android GUI Design — Native & Hybrid Best Practices (v4.5.0)

This guide covers the design system used by the Quantum CLI Android build (`android/app/src/main`). It applies to:

- **Native Compose** (`Theme.kt`, `QuantumUi.kt`) — current primary path.
- **Native XML / classic Java** (`activity_quantum_native.xml`, legacy `NativeGuiPattern`) — for devices that disable Compose or for Java-only integrations.
- **Hybrid (Web + native bridge)** (`HybridBridgePattern.kt`) — runs the web dashboard (`DASH_HTML`) inside a `WebView` with native navigation chrome, pull-to-refresh, and a native status bar.

Requirements: Material Design 3, dark-first (deep-space palette `#050810`), glass cards (`Panel` gradient), hairline cyan borders (`Hairline`), mono typography, responsive to 320 dp–720 dp width.

---

## 1. Native Compose (primary path)

### Theme (`Theme.kt`)
- `MaterialTheme(colorScheme = DarkScheme, typography = QuantumTypography, shapes = QuantumShapes)` — the single source of truth.
- `DarkScheme`: dark-first with `Cyan` primary (`#00E5FF`) and `Violet` tertiary (`#7C4DFF`).
- `QuantumTypography`: mono (`monoStyle`) with letter-spaced labels (`labelMedium` 11sp, 0.8sp), tight body (`bodyMedium` 13sp, 0.1sp).
- `QuantumShapes`: `RoundedCornerShape` at 14dp (`medium`) as the default card radius; 20dp for hero cards.

### Glass card (`quantumPanel` modifier)
Every module card uses `Modifier.quantumPanel()` which applies:
1. `Brush.verticalGradient` surface (`0xF20D1E33` -> `0xE6081322`).
2. `border` with vertical gradient cyan hairline (`0.34f` top -> `0.07f` bottom).
3. `quantumGlow(alpha = 0.06f)` ambient cyan radial glow.
4. `clip(RoundedCornerShape(16.dp))` standard card radius.

The background is `quantumBackground()` — deep vertical gradient plus two radial light fields (cyan top-left, violet bottom-right). No flat fills.

### Card component (`QCard`)
Built from:
- `Row` with 2dp accent bar (`verticalGradient(Cyan, Violet)`) + `labelLarge` title.
- `Column` content with `PaddingValues(14.dp)`.
- Always on `Modifier.quantumPanel()`.

This ensures every widget has consistent spacing, typography, and lighting regardless of which screen creates it.

---

## 2. Native XML / Java (alternate path)

When Compose is unavailable or a Java-only module is needed, the equivalent visual system is expressed in XML:

### Layout (`activity_quantum_native.xml`)
- Root: `androidx.coordinatorlayout.widget.CoordinatorLayout` with deep background (`#050810`).
- App bar: `com.google.android.material.appbar.MaterialToolbar` (`ThemeOverlay.MaterialComponents.Dark.ActionBar`) using cyan `surfaceTint`.
- Bottom navigation: `BottomNavigationView` with `MaterialComponents.BottomNavigationView` style; 4 items mapped to main pages (`Dashboard`, `Ops`, `AI`, `Settings`).
- Content: `NestedScrollView` containing `LinearLayout(vertical)` with `MaterialCardView` cards. Each card uses:
  - `cardBackgroundColor`: `#0F141A` (equivalent to `Panel`).
  - `cardCornerRadius`: 14dp.
  - `cardElevation`: 2dp (soft shadow, never hard).
  - `strokeColor`: `#00e5ff` at 20% alpha, `strokeWidth`: 1dp — the hairline.
  - `rippleColor`: cyan 10%.
- Typography: `TextAppearance.Material3.LabelLarge` for labels (`monoSpace=monospace` via `fontFamily`), `TextAppearance.Material3.BodyMedium` for body.

### Structured Kotlin / Java (`NativeGuiPattern.kt`, `.java`)
Native code follows clean architecture regardless of UI framework:

1. **Presentation layer** (`Activity` / `Fragment`): owns view references (via ViewBinding or Compose), listens to events, calls ViewModel.
2. **Domain layer** (`ViewModel` with `LiveData` or `StateFlow`): exposes `UiState<T>` sealed class (`Idle`, `Loading`, `Success`, `Error`).
3. **Data layer** (`Repository` interface): abstracts the REST source (local `openfable` server, `/api/openfable/*`) from the UI.

The `NativeGuiPattern` demonstrates a `MaterialToolbar` + card-based screen with `StateFlow` observation:
```kotlin
viewModel.uiState.collect(this) { state ->
  when (state) { is UiState.Success -> render(state.data)
                 is UiState.Loading -> showProgress()
                 is UiState.Error -> showSnackbar(state.message) }
}
```
This pattern is framework-agnostic: it works with Compose (`LazyColumn`) and XML (`RecyclerView`) without changing domain logic.

---

## 3. Hybrid (Web + native bridge)

### Hybrid design (`HybridBridgePattern.kt`)
When the web dashboard (`DASH_HTML`) is embedded in Android:

- Native chrome (toolbar, bottom nav, pull-to-refresh, native status bar) remains native.
- Web content is loaded via `WebView` inside a `NestedScrollView` or `Compose AndroidView` (`AndroidView(factory = { ctx -> WebView(ctx) })`).
- A `NativeBridge` JavaScript interface (`HybridBridge`) exposes real functions (not stubs):
  - `openfableState()` -> fetches `/api/openfable/state` and returns JSON.
  - `openfableChat()` -> calls `/api/openfable/chat`.
  - `startServer(port)` -> `POST /api/openfable/server/start`.
- The native side provides `JavaScriptInterface` as a Kotlin `object` annotated `@JavascriptInterface`. Every method is a real function backed by the real server or binary, not a mock.
- Accessibility: the WebView uses `settings.setLoadWithOverviewMode` and `settings.defaultTextEncodingName` for responsive text; native `ContentDescription` is set on the `WebView` container.
- Hybrid cards follow the same `quantumPanel()` rules in Compose (or `MaterialCardView` rules in XML) — the web content is just another data source.

---

## 4. Design rules (non-negotiable)

1. **No flat fills.** Every surface uses a gradient (`Panel` vertical, `quantumBackground` radial). Flat `Color(0xFF...)` surfaces are forbidden.
2. **Every interactive element has ripple.** `ButtonDefaults.buttonColors(containerColor = ...)` must include `rippleColor` (`Cyan.copy(alpha = 0.12f)`).
3. **Typography is mono.** `fontFamily = mono` on all labels and body. Only hero/display titles use `FontWeight.Bold` with negative letter-spacing.
4. **No simulated UI.** Buttons must call real `ViewModel` functions; `WebView` interfaces must call real `/api/*` routes; `NativeBridge` methods must call `openfable_dashboard_state()` / `start_server()` / `run_once()` — never return hardcoded strings as capabilities.
5. **Responsive minimum width.** Layouts must work at 320 dp (small phone) and 720 dp (tablet). Use `Modifier.fillMaxWidth()` with `weight(1f)` for column splits; never hardcode pixel widths for cards.
6. **Accessibility.** Every interactive element has `contentDescription` (Compose) or `contentDescription` / `focusableInTouchMode` (XML). Contrast ratios meet AA (`Muted` on `Panel` gives ~4.5:1).
7. **Dark-first only.** No light theme override. `Window` flags ensure no light system bar (`FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS`).

---

## 5. File references

- Theme / colors: `Theme.kt` / `colors.xml`
- Native Compose layout: `QuantumUi.kt`, `Page.kt`, `OpsPages.kt`
- Native XML layout: `res/layout/activity_quantum_native.xml`
- Hybrid WebView: `HybridBridgePattern.kt`
- Native clean architecture: `NativeGuiPattern.kt`, `NativeGuiPattern.java`
- Design rules / best practices: this doc (`docs/ANDROID_GUI_DESIGN.md`)
