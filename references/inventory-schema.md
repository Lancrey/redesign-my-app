# Inventory schema and canonical IDs

The inventory exists in two forms that must stay in sync: `01-design-inventory.md` (for humans and for Claude Design) and `inventory.json` (for `build_handoff.py` and for Step 4). The scanner writes a first `inventory.json`; you enrich it while reading the code. Keep the structure below so the scripts and the later steps can rely on it.

## Canonical IDs

Every element gets a stable ID that survives the trip to Claude Design and back. Claude Design is told to keep these IDs in its output; Step 4 uses them to map new designs onto old files.

| Prefix | Element type | Pattern | Examples |
|---|---|---|---|
| `tok.` | design token | `tok.<group>.<name>[.<variant>]` | `tok.color.brand.500`, `tok.font.body`, `tok.space.4`, `tok.radius.md`, `tok.shadow.card`, `tok.bp.md`, `tok.z.modal` |
| `cmp.` | component | `cmp.<family>.<name>` | `cmp.button.primary`, `cmp.input.text`, `cmp.card.product`, `cmp.nav.sidebar` |
| `scr.` | screen / route / page | `scr.<name>` (nested with dots) | `scr.home`, `scr.settings.billing`, `scr.auth.login` |
| `lay.` | layout / template | `lay.<name>` | `lay.app-shell`, `lay.marketing` |
| `ast.` | asset | `ast.<kind>.<name>` | `ast.icon.search`, `ast.img.hero`, `ast.font.inter` |
| `pat.` | interaction pattern | `pat.<name>` | `pat.toast`, `pat.confirm-dialog`, `pat.infinite-scroll` |

Rules: lowercase, hyphens inside names, dots only as separators, no spaces. Derive from the code name when one exists (`PrimaryButton` → `cmp.button.primary`; `/settings/billing` → `scr.settings.billing`). When the code has no name (an inline `<div class="card">`), invent a descriptive one and record where it lives.

## `inventory.json` structure

```json
{
  "meta": {
    "generated": "2026-10-20",
    "repo": "owner/name or path",
    "commit": "abc1234",
    "tool": "RedesignMyApp by Pluristack"
  },
  "stack": {
    "platform": "web | ios | android | flutter | react-native | multi",
    "framework": "react | next | vue | nuxt | svelte | sveltekit | angular | html | swiftui | uikit | compose | xml-views | flutter | react-native",
    "styling": ["tailwind", "css-modules", "styled-components", "emotion", "scss", "plain-css", "mui", "chakra", "shadcn", "bootstrap", "swiftui-modifiers", "compose-theme", "flutter-theme"],
    "ui_libraries": ["@mui/material", "lucide-react"],
    "design_dirs": ["src/styles", "src/components/ui"],
    "dark_mode": "none | class | media | system | both",
    "notes": "free text"
  },
  "files": [
    {"path": "src/styles/tokens.css", "kind": "tokens | stylesheet | component | screen | layout | theme | asset | config", "lines": 120}
  ],
  "tokens": [
    {
      "id": "tok.color.brand.500",
      "group": "color | font | type-scale | space | radius | shadow | motion | bp | z | opacity | border",
      "name": "--color-brand-500",
      "value": "#2563EB",
      "value_dark": "#60A5FA",
      "source": "src/styles/tokens.css:14",
      "usage_count": 23,
      "role": "primary action background, link color"
    }
  ],
  "literals": [
    {"value": "#3B82F6", "kind": "color", "occurrences": 7, "files": ["src/components/Badge.tsx:12", "..."], "closest_token": "tok.color.brand.500"}
  ],
  "components": [
    {
      "id": "cmp.button.primary",
      "name": "PrimaryButton",
      "family": "button",
      "source": "src/components/Button.tsx:8",
      "styles_source": "src/components/Button.module.css",
      "description": "Main call-to-action button",
      "props_affecting_appearance": ["size: sm|md|lg", "variant: primary|secondary|ghost", "icon"],
      "states": ["default", "hover", "focus-visible", "active", "disabled", "loading"],
      "states_missing": ["focus-visible"],
      "tokens_used": ["tok.color.brand.500", "tok.radius.md"],
      "literals_used": ["#1D4ED8"],
      "used_in": ["scr.home", "scr.checkout", "cmp.card.product"],
      "usage_count": 31,
      "responsive": "full-width below tok.bp.sm",
      "a11y": "has aria-busy when loading; no visible focus ring",
      "duplicates": ["cmp.button.legacy"]
    }
  ],
  "screens": [
    {
      "id": "scr.settings.billing",
      "name": "Billing settings",
      "route": "/settings/billing",
      "source": "src/pages/settings/billing.tsx",
      "layout": "lay.app-shell",
      "purpose": "Manage plan and payment method",
      "primary_action": "Update payment method",
      "components": ["cmp.nav.sidebar", "cmp.card.plan", "cmp.form.payment"],
      "states": ["loading", "empty (no plan)", "error"],
      "screenshot": "screens/settings-billing--desktop--light.png",
      "notes": "table overflows at 390px"
    }
  ],
  "layouts": [
    {"id": "lay.app-shell", "source": "src/layouts/AppShell.tsx", "regions": ["sidebar 240px", "topbar 56px", "content"], "used_by": ["scr.home", "..."]}
  ],
  "assets": [
    {"id": "ast.icon.search", "kind": "icon | image | font | lottie | video", "source": "src/assets/icons/search.svg", "format": "svg", "size_bytes": 812, "used_in": ["cmp.input.search"]}
  ],
  "patterns": [
    {"id": "pat.toast", "description": "Bottom-right toast, 4s auto-dismiss", "source": "src/components/Toast.tsx", "used_in": ["scr.*"]}
  ],
  "issues": [
    {"id": "inv-001", "kind": "duplicate | hardcoded | missing-state | inconsistency | a11y | dead-code", "summary": "Two button implementations", "elements": ["cmp.button.primary", "cmp.button.legacy"], "evidence": "src/components/Button.tsx vs src/legacy/Btn.jsx"}
  ],
  "coverage": {
    "files_scanned": 212,
    "files_design_relevant": 61,
    "files_described": 61,
    "excluded": [{"path": "src/legacy/", "reason": "unreferenced since v2"}]
  }
}
```

Fields the scanner cannot fill (`description`, `states`, `used_in`, `role`, `purpose`, `a11y`, `issues`) are yours to add while reading. Leave a field out rather than guessing; an absent field is honest, a wrong one misleads Claude Design.

## Native app equivalents

| Web concept | SwiftUI / UIKit | Jetpack Compose / XML | Flutter |
|---|---|---|---|
| token file | `Color.xcassets`, `Theme.swift`, `Font+App.swift` | `Color.kt`, `Theme.kt`, `Type.kt`, `colors.xml`, `dimens.xml` | `ThemeData`, `ColorScheme`, `TextTheme` in `theme.dart` |
| component | `struct X: View`, `UIView` subclass | `@Composable fun X`, custom `View` | `class X extends StatelessWidget/StatefulWidget` |
| screen | `NavigationStack` destination, `UIViewController` | `NavHost` destination, `Activity`/`Fragment` | route in `MaterialApp.routes` / `GoRouter` |
| layout | `HStack/VStack/ZStack`, `TabView` | `Scaffold`, `Row/Column/Box` | `Scaffold`, `Row/Column/Stack` |
| state | `.disabled()`, `.opacity()`, `isPressed` | `enabled`, `interactionSource` | `enabled`, `onPressed == null` |
| breakpoint | size classes (`horizontalSizeClass`) | `WindowSizeClass` | `MediaQuery`, `LayoutBuilder` |
| icon | SF Symbols name, `Image("…")` | `Icons.*`, `painterResource` | `Icons.*`, `Image.asset` |
| dark mode | `colorScheme` environment | `isSystemInDarkTheme()` | `ThemeMode`, `brightness` |

Record the native form in the same JSON fields (`name` = the Swift/Kotlin/Dart identifier, `source` = file:line).
