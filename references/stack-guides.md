# Stack guides — where design lives

Use this at Step 0 (to confirm detection) and Step 1 (to know what to open). Each section lists the files that define the design system, how components are declared, how screens/routes are declared, and the stack-specific traps that cause missed elements.

## Contents
- [Detection cues](#detection-cues)
- [Web: frameworks](#web-frameworks)
- [Web: styling approaches](#web-styling-approaches)
- [Web: component libraries](#web-component-libraries)
- [iOS / macOS](#ios--macos)
- [Android](#android)
- [Flutter](#flutter)
- [React Native](#react-native)
- [Server-rendered templates](#server-rendered-templates)

---

## Detection cues

| Cue | Meaning |
|---|---|
| `package.json` with `react` / `next` / `vue` / `nuxt` / `svelte` / `@angular/core` | web framework |
| `tailwind.config.{js,ts,cjs,mjs}` or `@import "tailwindcss"` / `@theme` in CSS | Tailwind (v3 config file; v4 CSS-first) |
| `*.module.css` / `*.module.scss` | CSS Modules |
| `styled-components`, `@emotion/*`, `@stitches/*`, `@vanilla-extract/*` in deps | CSS-in-JS |
| `components.json` + `src/components/ui/*` | shadcn/ui |
| `@mui/material`, `@chakra-ui/react`, `antd`, `@mantine/core`, `@radix-ui/*`, `@headlessui/*` | component library |
| `*.xcodeproj`, `*.xcworkspace`, `Package.swift`, `import SwiftUI` | iOS/macOS |
| `build.gradle(.kts)` with `androidx.compose`, `@Composable` | Android Compose |
| `res/layout/*.xml`, `res/values/colors.xml` | Android XML views |
| `pubspec.yaml`, `lib/main.dart` | Flutter |
| `react-native` in deps, `ios/` and `android/` folders, `app.json` with `expo` | React Native / Expo |
| `templates/*.html`, `*.ejs`, `*.hbs`, `*.twig`, `*.blade.php`, `*.njk`, `*.jinja` | server-rendered templates |
| `.storybook/`, `*.stories.*` | Storybook — read the stories: they enumerate variants and states |

Multi-platform repos (a `web/` and an `ios/` folder, or a monorepo with `apps/*`) get one inventory with a `stack.platform = "multi"` and per-platform sections.

---

## Web: frameworks

### React (Vite / CRA / custom)
- Components: `function Name(` / `const Name = (` / `export default function` in `.jsx|.tsx`, usually under `src/components`, `src/ui`, `src/features/*/components`.
- Screens: `react-router` — grep `<Route path=` and `createBrowserRouter`; TanStack Router — `routes/` folder; otherwise look at the top-level `App` switch.
- Layouts: components that render `<Outlet />` or accept `children` and define a shell.
- Trap: components defined inside other components; `forwardRef` wrappers; barrel files (`index.ts`) that re-export — follow them to the real file.

### Next.js
- App Router: `app/**/page.tsx` = screen, `app/**/layout.tsx` = layout, `app/**/loading.tsx` / `error.tsx` / `not-found.tsx` = states (record them — they are design elements). Route groups `(group)` do not appear in the URL.
- Pages Router: `pages/**/*.tsx` = screen; `_app.tsx` and `_document.tsx` hold global styles and fonts.
- `next/font` declarations define the typography tokens; `next.config` may set image domains.
- Metadata (`generateMetadata`) is not design; skip it.

### Vue / Nuxt
- Single-file components: `*.vue`; styles in `<style scoped>` blocks — scan them like CSS.
- Vue Router: `router/index.*`; Nuxt: `pages/**/*.vue` (file-based), `layouts/*.vue`, `app.vue`.
- `<script setup>` props with `variant`, `size`, `color` are the appearance props.

### Svelte / SvelteKit
- `*.svelte` with `<style>` blocks; SvelteKit routes in `src/routes/**/+page.svelte`, layouts in `+layout.svelte`, errors in `+error.svelte`.
- `export let variant` (Svelte 4) or `let { variant } = $props()` (Svelte 5) are the appearance props.

### Angular
- Components: `@Component({ selector, templateUrl, styleUrls })` — the template and stylesheet are separate files; read both.
- Routes: `*-routing.module.ts` or `app.routes.ts`.
- Angular Material: theme in `styles.scss` (`@include mat.theme(...)` / `mat.define-palette`).

### Plain HTML / static sites (Astro, Eleventy, Hugo, Jekyll)
- Screens = HTML files or templates; components = partials/includes (`_includes`, `partials/`, `src/components/*.astro`).
- CSS is usually global; the "component" is a class naming convention (BEM blocks). Treat each top-level BEM block (`.card`, `.nav`) as a component.

---

## Web: styling approaches

### Tailwind
- v3: `tailwind.config.*` → `theme` and `theme.extend` are the tokens (`colors`, `fontFamily`, `fontSize`, `spacing`, `borderRadius`, `boxShadow`, `screens`). Plugins (`@tailwindcss/forms`, `typography`) affect defaults.
- v4: tokens live in CSS under `@theme { --color-brand-500: … }`; `@custom-variant dark` defines dark mode.
- Arbitrary values (`bg-[#1d4ed8]`, `w-[373px]`) are hard-coded literals — the scanner extracts them; list them under inconsistencies.
- `@apply` blocks and `cva()` / `tailwind-variants` definitions enumerate variants — read them for the component catalogue.
- Dark mode: `dark:` prefix presence and the `darkMode` setting (`class`, `media`, `selector`).

### CSS Modules / SCSS / plain CSS
- Tokens: `:root { --x: … }`, SCSS `$variables`, `@use "tokens"` maps. Dark mode: `[data-theme="dark"]`, `.dark`, or `@media (prefers-color-scheme: dark)`.
- Breakpoints: `@media (min-width: …)` values; SCSS mixins named `respond`, `mq`, `breakpoint`.
- Resets: `normalize.css`, `reset.css`, `*{box-sizing}` blocks.

### styled-components / Emotion / vanilla-extract / Stitches
- Theme object passed to `ThemeProvider` is the token file (`theme.ts`); `createGlobalStyle` is the global stylesheet.
- Components are `styled.button`/`styled(Base)` declarations; variants via props (`${p => p.variant === …}`) or `variants:` maps (Stitches, vanilla-extract `recipe`).

### Bootstrap / Bulma / Foundation
- Tokens are the framework's SCSS variables overridden in a `_variables.scss` or `custom.scss`; everything not overridden is the framework default — say so in the inventory.

---

## Web: component libraries

| Library | Theme location | Variants declared in |
|---|---|---|
| MUI | `createTheme({ palette, typography, shape, components })` | `theme.components.MuiButton.variants`, `sx` props |
| Chakra | `extendTheme({ colors, fonts, components })` | `components.Button.variants` |
| shadcn/ui | `globals.css` custom properties (`--primary`, `--radius`), `components.json` | `cva()` in each `components/ui/*.tsx` |
| Mantine | `createTheme({ colors, primaryColor, radius })` | `theme.components.Button` |
| Ant Design | `ConfigProvider theme={{ token, components }}` | `token` and per-component overrides |
| Radix / Headless UI | none (unstyled) — styling is in the app's CSS | app-defined |

When a library is present, the inventory separates **library defaults used as-is**, **overridden tokens**, and **app-specific components**, because Claude Design and Claude Code will treat them differently.

---

## iOS / macOS

### SwiftUI
- Tokens: `Assets.xcassets/*.colorset` (light/dark values in `Contents.json`), `Color+App.swift` extensions, `Font+App.swift`, `Theme.swift`/`DesignSystem.swift`, `ShapeStyle` extensions.
- Components: `struct Name: View` in `Views/`, `Components/`, `DesignSystem/`; `ViewModifier` structs are reusable style units — inventory them as tokens or patterns; `ButtonStyle` / `LabelStyle` / `TextFieldStyle` conformances are the component variants.
- Screens: destinations of `NavigationStack`/`NavigationLink`, `TabView` tabs, `.sheet` / `.fullScreenCover` presentations, `App` body root.
- States: `.disabled`, `isPressed` in `ButtonStyle`, `redacted(reason: .placeholder)` (loading), `ContentUnavailableView` (empty), `.alert` (error).
- Traps: hard-coded `Color(red:green:blue:)`, `.padding(13)` magic numbers, `Font.system(size: 17)` instead of text styles, `.foregroundColor(.gray)`; `@Environment(\.colorScheme)` branches hide dark-mode logic.
- Adaptive layout: `horizontalSizeClass`, `ViewThatFits`, `GeometryReader`.

### UIKit
- Tokens: `UIColor` extensions, `UIFont` extensions, asset catalogs; appearance proxies (`UINavigationBar.appearance()`) are global styles.
- Components: `UIView`/`UIControl` subclasses, XIBs, storyboards (`*.storyboard` XML — scan for `<viewController>` to list screens and `<color>` for literals).
- Screens: `UIViewController` subclasses and storyboard scenes.

---

## Android

### Jetpack Compose
- Tokens: `ui/theme/Color.kt`, `Theme.kt` (`lightColorScheme`/`darkColorScheme`, `MaterialTheme`), `Type.kt` (`Typography`), `Shape.kt`; `dimens` sometimes in `Dimens.kt`.
- Components: `@Composable fun Name(` in `ui/components`; Material 3 components used directly (`Button`, `Card`) count as library defaults.
- Screens: `NavHost { composable("route") { … } }`, `Screen` sealed classes, `Activity` entry points.
- States: `enabled`, `isLoading` flags, `AnimatedVisibility`.
- Traps: `Color(0xFF2563EB)` literals outside `Color.kt`; `.padding(13.dp)` magic numbers; `Modifier` chains copied between composables (near-duplicate components).

### XML views
- Tokens: `res/values/colors.xml`, `dimens.xml`, `styles.xml`/`themes.xml` (`<style name="…" parent="…">`), `res/values-night/` for dark.
- Components: custom `View` classes, `<include>`/`<merge>` layouts, `res/layout/item_*.xml`.
- Screens: `res/layout/activity_*.xml`, `fragment_*.xml`; navigation graph `res/navigation/*.xml`.
- Traps: `android:textColor="#…"` inline literals; `sp`/`dp` magic numbers.

---

## Flutter

- Tokens: `ThemeData(colorScheme:, textTheme:, …)` usually in `lib/theme/` or `main.dart`; `ColorScheme.fromSeed`; extension classes (`ThemeExtension<T>`); `AppColors` static classes.
- Components: `class Name extends StatelessWidget/StatefulWidget` under `lib/widgets/` or `lib/components/`; `ButtonStyle` via `ElevatedButton.styleFrom`.
- Screens: `MaterialApp.routes`, `onGenerateRoute`, `GoRouter` routes, `Navigator.push` targets — grep for `Scaffold(` as a screen marker.
- States: `enabled`, `onPressed: null`, `Shimmer`/`Skeletonizer` (loading), custom empty widgets.
- Traps: `Color(0xFF…)` and `EdgeInsets.all(13)` literals; `TextStyle(fontSize: 17)` instead of `textTheme`.
- Dark mode: `darkTheme:` + `themeMode:` in `MaterialApp`.

---

## React Native

- Tokens: `theme.ts`/`tokens.ts`, `StyleSheet.create` files; libraries: NativeWind (Tailwind config applies), Tamagui (`tamagui.config.ts`), React Native Paper (`MD3LightTheme` overrides), Restyle (`createTheme`).
- Components: same as React; screens: React Navigation `createStackNavigator`/`createBottomTabNavigator` screen registrations, or Expo Router `app/**/*.tsx` (file-based like Next App Router).
- Traps: platform forks (`Platform.select`, `*.ios.tsx` / `*.android.tsx`) — both are design elements; `Dimensions.get('window')` hard-coded breakpoints.

---

## Server-rendered templates

- Templates (`*.html.erb`, `*.blade.php`, `*.twig`, `*.ejs`, `*.hbs`, `*.njk`, Django/Jinja `*.html`) are screens; partials/includes/components (`_partial`, `@include`, `{% include %}`, `<x-component>`) are components.
- Routes: `routes.rb`, `routes/web.php`, `urls.py`, Express `app.get(`, Flask `@app.route`.
- Styling is almost always global CSS or Tailwind — see the styling sections. Hotwire/HTMX attributes (`data-turbo-frame`, `hx-swap`) describe interaction patterns; record them under `patterns`.
