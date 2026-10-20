# Capturing the current UI

Step 2 needs to *see* the interface. Try the options in order; stop at the first that works; record in `02-design-review.md` which one was used and what could not be captured. Save everything to `redesign/screens/` named `<screen-id-without-prefix>--<viewport>--<scheme>.png` (e.g. `settings-billing--mobile--dark.png`) so the review and the Claude Design brief can reference captures by screen ID.

## Option 1 — Run the app locally and capture it

### Web
1. Find the dev command: `package.json` scripts (`dev`, `start`, `serve`), `README`, `Makefile`, `docker-compose.yml`. Install dependencies (`npm ci` / `pnpm i` / `yarn`). If `.env.example` exists, copy it to `.env` with placeholder values; many UIs render without a real backend.
2. Start it in the background and wait for the port:
   ```bash
   (npm run dev > redesign/dev.log 2>&1 &) ; sleep 8; tail -20 redesign/dev.log
   ```
3. Capture with the bundled script (needs Playwright + Chromium; install once with `pip install playwright && python -m playwright install chromium`, or `npm i -D playwright && npx playwright install chromium`):
   ```bash
   node <skill-path>/scripts/capture_screens.js \
     --base http://localhost:5173 \
     --routes redesign/routes.txt \
     --out redesign/screens \
     --viewports mobile,tablet,desktop \
     --schemes light,dark \
     --crawl 2
   ```
   `routes.txt` is one path per line; generate it from `inventory.json` screens (the script accepts `--inventory redesign/inventory.json` instead). `--crawl N` follows same-origin links N levels deep to catch routes the inventory missed. Default viewports: mobile 390×844, tablet 834×1194, desktop 1440×900.
4. Authenticated screens: if a login form exists, pass `--login-url /login --user … --pass …` only with credentials the user provided for a local/test instance; otherwise capture what is reachable and list the rest as "not captured — requires auth".
5. The script also writes `screens/manifest.json` (route, viewport, scheme, file, HTTP status, console errors) and, with `--styles`, a `computed-styles.json` sample per page (font sizes, colors and spacings actually rendered — useful to confirm tokens).

### Browser extensions (Chrome / Edge / Firefox MV2–MV3)
Extension pages (new tab, popup, options, side panel) depend on the `chrome.*` / `browser.*` APIs; served from a plain HTTP server they render an error state, which is not the real UI. Load the unpacked extension instead:
```bash
node <skill-path>/scripts/capture_screens.js --extension <repo-or-dist-dir-with-manifest.json> \
  --routes redesign/routes.txt --out redesign/screens --viewports mobile,desktop --schemes light,dark
```
`routes.txt` lists the page files (`/newtab.html`, `/popup.html`, `/options.html`); the scanner puts the manifest's entry pages into `inventory.json`, so `--inventory redesign/inventory.json` also works. The script launches a persistent Chromium profile with the extension loaded and captures `chrome-extension://<id>/<page>`. Popups are captured at full page size — for the real popup footprint, add a viewport matching the popup's CSS width (e.g. `--viewports mobile`) and note it in the review. If the extension is built from `src/` (bundler), build first and point `--extension` at the output directory. Firefox-only extensions: use `web-ext run` and capture by hand, or test the Chromium build if one exists.

### iOS (SwiftUI / UIKit)
Requires macOS with Xcode. Build and run on a simulator, then:
```bash
xcrun simctl list devices booted
xcrun simctl io booted screenshot redesign/screens/home--iphone--light.png
# dark mode:
xcrun simctl ui booted appearance dark
```
Navigate between screens by hand (or with XCUITest if the project has UI tests — `xcodebuild test` with a screenshot-taking test is the most reliable). In Claude.ai with a connected Mac, computer-use tools can drive the simulator; in a cloud sandbox this option is unavailable — go to option 2/3.

### Android (Compose / XML)
Requires Android SDK and an emulator or device:
```bash
adb devices
adb exec-out screencap -p > redesign/screens/home--phone--light.png
adb shell "cmd uimode night yes"   # dark mode; "no" to revert
adb shell am start -n <package>/<activity>   # open a specific screen
```
Compose projects with Paparazzi or Roborazzi tests can render composables without an emulator (`./gradlew recordPaparazziDebug`) — check `build.gradle` for these plugins first; they are the fastest path.

### Flutter
```bash
flutter devices
flutter run -d <device>            # then in the running session: press 's' to screenshot
flutter screenshot -d <device> -o redesign/screens/home--phone--light.png
```
Flutter web target (`flutter run -d chrome --web-port 8080`) allows the Playwright script to be used instead, which is far easier for multi-viewport capture; design parity with mobile is imperfect but hierarchy and color are preserved. Golden tests (`matchesGoldenFile`) in `test/` already contain rendered PNGs — use them.

### React Native / Expo
`expo start --web` plus the Playwright script is the cheapest route for layout and color; for native rendering use the iOS/Android commands above. Storybook for RN (`.ondevice`) enumerates components if present.

## Option 2 — Capture a deployed URL
Same Playwright command with `--base https://staging.example.com`. Respect robots/auth; never attempt to bypass a login. Mark captures from production as such in the review (data and content may differ from local).

## Option 3 — User-provided screenshots
Ask for: each main screen, at least one mobile and one desktop capture (web), light and dark if the app supports it, and one example each of an empty state, a loading state and an error state if they exist. Rename files to the naming convention and note in the manifest that they were supplied.

## Option 4 — Code-only review
State at the top of `02-design-review.md`: "No rendered captures were available; visual findings are inferred from source." Then compensate: compute contrast ratios from the token values (see `heuristics.md`), reconstruct the spacing scale from the literal list, and describe hierarchy from the type scale and layout code. Be explicit about confidence for each finding (`observed` vs `inferred`).

## Reading captures
Use the image-reading tool on each capture (Read on a PNG renders it). Look at every capture at least once; do not review only the first viewport. For each screen note: what draws the eye first, whether the primary action is obvious, alignment and spacing consistency, text legibility, contrast, crowding, and anything that breaks at the narrow viewport (overflow, truncation, overlapping).
