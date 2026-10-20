#!/usr/bin/env python3
"""
inventory_scan.py — raw design inventory extractor for RedesignMyApp (Pluristack).

Walks a repository, detects the UI stack, lists design-relevant files and
extracts candidate tokens, literals, components, screens/routes and assets.
Standard library only.

Usage:
  python3 inventory_scan.py <repo> --detect-only
  python3 inventory_scan.py <repo> --out redesign/inventory.json [--summary redesign/inventory-summary.md]

The output is a *candidate list*. Descriptions, states, usage and roles are
added by reading the code (see SKILL.md, Step 1).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", ".svelte-kit", "out",
    "vendor", "Pods", "DerivedData", "__pycache__", "coverage", ".venv", "venv",
    ".turbo", ".cache", "target", ".gradle", ".idea", ".vscode", "tmp", ".dart_tool",
    "ios/build", "android/build", "redesign", ".expo", "storybook-static", "public/build",
}
MAX_FILE_BYTES = 3_000_000
# Directories that never hold design elements of the product itself (walked for stack detection, ignored for extraction)
NON_DESIGN_DIRS = {"tests", "test", "__tests__", "e2e", "cypress", "spec", "specs", "docs", "doc", "examples",
                   "example", "fixtures", "__mocks__", "mocks", "scripts", "tools", "benchmarks", "playwright-report"}


VENDOR_HINTS = ("/katex/", "/vendor/", "/vendors/", "/third_party/", "/third-party/", "/libs/", "/lib/", ".min.",
                "/prism", "highlight.js", "/codemirror", "fontawesome", "font-awesome", "bootstrap-icons", "/dist/",
                "normalize.css", "reset.css", "/pdfjs", "/pdf.js", "/mathjax", "/quill", "/tinymce", "/ckeditor", "/monaco")
NAMED_COLORS = {"white", "black", "transparent", "currentcolor", "red", "blue", "green", "gray", "grey", "orange",
                "yellow", "purple", "pink", "navy", "teal", "silver", "gold", "crimson", "tomato", "coral", "salmon"}


def in_non_design_dir(rel):
    parts = rel.replace("\\", "/").split("/")[:-1]
    return any(p in NON_DESIGN_DIRS for p in parts)


def is_vendored(rel):
    low = "/" + rel.replace("\\", "/").lower()
    return any(h in low for h in VENDOR_HINTS)

STYLE_EXT = {".css", ".scss", ".sass", ".less", ".styl", ".pcss"}
WEB_COMPONENT_EXT = {".jsx", ".tsx", ".vue", ".svelte", ".astro", ".js", ".ts", ".mjs", ".cjs"}
TEMPLATE_EXT = {".html", ".htm", ".ejs", ".hbs", ".handlebars", ".twig", ".njk", ".jinja", ".jinja2",
                ".erb", ".haml", ".slim", ".pug", ".liquid", ".mustache", ".php", ".cshtml", ".razor"}
NATIVE_EXT = {".swift", ".kt", ".kts", ".java", ".dart", ".xml", ".storyboard", ".xib", ".m"}
ASSET_EXT = {".svg": "icon", ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image",
             ".gif": "image", ".avif": "image", ".ico": "icon", ".woff": "font", ".woff2": "font",
             ".ttf": "font", ".otf": "font", ".lottie": "lottie", ".json": None, ".mp4": "video"}

HEX_RE = re.compile(r"(?<![\w-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
FUNC_COLOR_RE = re.compile(r"\b(?:rgba?|hsla?|oklch|oklab|lab|lch|color)\([^)]{1,80}\)")
CSS_VAR_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+?)\s*;")
SCSS_VAR_RE = re.compile(r"^\s*(\$[A-Za-z0-9_-]+)\s*:\s*([^;]+?)\s*(?:!default)?;", re.M)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;{}]+);", re.I)
MEDIA_RE = re.compile(r"@media[^{]*?\((?:min|max)-width\s*:\s*([0-9.]+(?:px|em|rem))\)")
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;{}]+);")
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;{}]+);")
ZINDEX_RE = re.compile(r"z-index\s*:\s*(-?\d+)")
SPACE_RE = re.compile(r"(?:^|[\s;{])(?:padding|margin|gap|row-gap|column-gap)(?:-[a-z]+)?\s*:\s*([^;{}]+);")
DURATION_RE = re.compile(r"\b(\d+(?:\.\d+)?)(ms|s)\b")
TW_ARBITRARY_RE = re.compile(r"\[(#[0-9a-fA-F]{3,8}|\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%))\]")
TW_THEME_BLOCK_RE = re.compile(r"@theme[^{]*\{([^}]*)\}", re.S)

REACT_CMP_RE = re.compile(
    r"^(?:export\s+(?:default\s+)?)?(?:function|const|let|class)\s+([A-Z][A-Za-z0-9_]*)\b", re.M)
STYLED_RE = re.compile(r"\b(?:const|let)\s+([A-Z][A-Za-z0-9_]*)\s*=\s*styled[.(]")
SWIFT_VIEW_RE = re.compile(r"\bstruct\s+([A-Z][A-Za-z0-9_]*)\s*:\s*[^{]*\bView\b")
SWIFT_MOD_RE = re.compile(r"\bstruct\s+([A-Z][A-Za-z0-9_]*)\s*:\s*[^{]*\b(?:ViewModifier|ButtonStyle|LabelStyle|TextFieldStyle|ToggleStyle)\b")
SWIFT_COLOR_RE = re.compile(r"Color\(\s*(?:red|hex|\"|#colorLiteral)[^)]*\)")
UIKIT_VC_RE = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\s*:\s*[^{]*\bUI(?:View|Table|Collection|Navigation|Tab)?(?:Controller|View)\b")
COMPOSE_RE = re.compile(r"@Composable\s*(?:\n\s*)?(?:(?:private|internal|public)\s+)?fun\s+([A-Z][A-Za-z0-9_]*)")
KOTLIN_COLOR_RE = re.compile(r"Color\(0x[0-9a-fA-F]{6,8}\)")
FLUTTER_WIDGET_RE = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\s+extends\s+(?:StatelessWidget|StatefulWidget|HookWidget|ConsumerWidget|ConsumerStatefulWidget)")
DART_COLOR_RE = re.compile(r"Color\(0x[0-9a-fA-F]{6,8}\)|Colors\.[a-z]+(?:\[\d+\])?")
XML_COLOR_RE = re.compile(r"<color\s+name=\"([^\"]+)\">([^<]+)</color>")
XML_DIMEN_RE = re.compile(r"<dimen\s+name=\"([^\"]+)\">([^<]+)</dimen>")
XML_STYLE_RE = re.compile(r"<style\s+name=\"([^\"]+)\"")
VUE_SVELTE_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)

ROUTE_PATTERNS = [
    ("react-router", re.compile(r"<Route\b[^>]*\bpath\s*=\s*[\"'{]([^\"'}]+)")),
    ("router-object", re.compile(r"\bpath\s*:\s*[\"'`]([^\"'`]+)[\"'`]")),
    ("express", re.compile(r"\b(?:app|router)\.(?:get|use)\(\s*[\"'`](/[^\"'`]*)")),
    ("flask", re.compile(r"@(?:app|bp|blueprint)\.route\(\s*[\"'](/[^\"']*)")),
    ("compose-nav", re.compile(r"composable\(\s*(?:route\s*=\s*)?[\"']([^\"']+)")),
    ("flutter-routes", re.compile(r"[\"'](/[A-Za-z0-9_/:-]*)[\"']\s*:\s*\(")),
    ("go-router", re.compile(r"GoRoute\(\s*path\s*:\s*[\"']([^\"']+)")),
]

UI_LIBS = ["@mui/material", "@chakra-ui/react", "antd", "@mantine/core", "@radix-ui", "@headlessui",
           "shadcn", "bootstrap", "bulma", "foundation-sites", "@shopify/polaris", "primereact", "primevue",
           "vuetify", "quasar", "element-plus", "naive-ui", "@nuxt/ui", "daisyui", "flowbite",
           "@angular/material", "primeng", "react-native-paper", "tamagui", "nativewind", "@shopify/restyle",
           "lucide-react", "@heroicons/react", "react-icons", "@tabler/icons", "phosphor", "@fortawesome",
           "framer-motion", "motion", "@react-spring", "gsap", "lottie"]
STYLING_LIBS = {"tailwindcss": "tailwind", "styled-components": "styled-components", "@emotion/react": "emotion",
                "@emotion/styled": "emotion", "@stitches/react": "stitches", "@vanilla-extract/css": "vanilla-extract",
                "sass": "scss", "sass-embedded": "scss", "less": "less", "stylus": "stylus", "postcss": "postcss",
                "@mui/material": "mui", "@chakra-ui/react": "chakra", "bootstrap": "bootstrap",
                "tailwind-variants": "tailwind", "class-variance-authority": "cva", "nativewind": "nativewind",
                "unocss": "unocss", "@linaria/core": "linaria", "@pandacss/dev": "panda"}


def read_text(path):
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return ""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def walk(repo):
    for root, dirs, files in os.walk(repo):
        rel_root = os.path.relpath(root, repo)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") or d in (".storybook",)]
        for fn in files:
            yield os.path.join(root, fn), (fn if rel_root == "." else os.path.join(rel_root, fn))


def git_commit(repo):
    try:
        return subprocess.check_output(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def load_json(path):
    try:
        return json.loads(read_text(path) or "{}")
    except json.JSONDecodeError:
        return {}


def detect_stack(repo, rel_files):
    s = {"platform": "unknown", "framework": "unknown", "styling": [], "ui_libraries": [],
         "design_dirs": [], "dark_mode": "none", "notes": [], "package_managers": []}
    names = set(rel_files)
    lower = [f.lower() for f in rel_files]

    pkg = {}
    for cand in ("package.json", "web/package.json", "app/package.json", "frontend/package.json", "client/package.json"):
        if cand in names:
            pkg = load_json(os.path.join(repo, cand))
            s["notes"].append(f"package.json at {cand}")
            break
    deps = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(pkg.get(k, {}) or {})

    fw = "unknown"
    if "next" in deps: fw = "next"
    elif "nuxt" in deps or "nuxt3" in deps: fw = "nuxt"
    elif "@sveltejs/kit" in deps: fw = "sveltekit"
    elif "svelte" in deps: fw = "svelte"
    elif "vue" in deps: fw = "vue"
    elif "@angular/core" in deps: fw = "angular"
    elif "astro" in deps: fw = "astro"
    elif "react-native" in deps or "expo" in deps: fw = "react-native"
    elif "react" in deps: fw = "react"
    elif "solid-js" in deps: fw = "solid"
    elif "@remix-run/react" in deps: fw = "remix"
    elif "@11ty/eleventy" in deps: fw = "eleventy"

    has_swift = any(f.endswith(".swift") for f in lower)
    has_xcode = any(f.endswith((".xcodeproj", ".xcworkspace", "package.swift")) or "/contents.json" in f and ".xcassets" in f for f in lower)
    has_kotlin = any(f.endswith((".kt", ".kts")) for f in lower)
    has_gradle = any(f.endswith(("build.gradle", "build.gradle.kts")) for f in lower)
    has_dart = "pubspec.yaml" in names or any(f.endswith(".dart") for f in lower)
    has_templates = any(os.path.splitext(f)[1] in TEMPLATE_EXT for f in lower)

    platforms = []
    if fw != "unknown" and fw != "react-native": platforms.append("web")
    if fw == "react-native": platforms.append("react-native")
    if has_swift and has_xcode: platforms.append("ios")
    if has_kotlin and has_gradle: platforms.append("android")
    if has_dart: platforms.append("flutter")
    if not platforms and has_templates: platforms.append("web")
    if not platforms and any(f.endswith((".html", ".css")) for f in lower): platforms.append("web")
    s["platform"] = "multi" if len(platforms) > 1 else (platforms[0] if platforms else "unknown")
    s["platforms"] = platforms

    # Browser extension?
    for cand in ("manifest.json", "src/manifest.json", "public/manifest.json", "extension/manifest.json"):
        if cand in names:
            mf = load_json(os.path.join(repo, cand))
            if "manifest_version" in mf:
                s["extension"] = {"manifest": cand, "manifest_version": mf.get("manifest_version"),
                                  "entry_pages": {k: v for k, v in {
                                      "newtab": (mf.get("chrome_url_overrides") or {}).get("newtab"),
                                      "popup": (mf.get("action") or mf.get("browser_action") or {}).get("default_popup"),
                                      "options": mf.get("options_page") or (mf.get("options_ui") or {}).get("page"),
                                      "sidepanel": (mf.get("side_panel") or {}).get("default_path"),
                                      "devtools": mf.get("devtools_page")}.items() if v}}
                if fw in ("unknown", "html"): fw = "browser-extension"
                if "web" not in platforms: platforms.append("web")
                s["platform"] = "multi" if len(platforms) > 1 else "web"
                s["platforms"] = platforms
                break

    if fw == "unknown":
        if "flutter" in platforms: fw = "flutter"
        elif "ios" in platforms:
            swift_src = "".join(read_text(os.path.join(repo, f)) for f in rel_files if f.endswith(".swift"))[:400000]
            fw = "swiftui" if "import SwiftUI" in swift_src else "uikit"
        elif "android" in platforms:
            kt_src = "".join(read_text(os.path.join(repo, f)) for f in rel_files if f.endswith(".kt"))[:400000]
            fw = "compose" if "@Composable" in kt_src else "xml-views"
        elif has_templates: fw = "server-templates"
        elif "web" in platforms: fw = "html"
    s["framework"] = fw

    styling = set()
    for d, label in STYLING_LIBS.items():
        if d in deps: styling.add(label)
    if any(f.startswith("tailwind.config") for f in [os.path.basename(x) for x in lower]): styling.add("tailwind")
    if any(".module.css" in f or ".module.scss" in f for f in lower): styling.add("css-modules")
    if any(f.endswith((".scss", ".sass")) for f in lower): styling.add("scss")
    if any(f.endswith(".css") for f in lower) and not styling: styling.add("plain-css")
    if "components.json" in names and any("/components/ui/" in f for f in lower): styling.add("shadcn")
    if fw == "swiftui": styling.add("swiftui-modifiers")
    if fw == "compose": styling.add("compose-theme")
    if fw == "flutter": styling.add("flutter-theme")
    if fw == "xml-views": styling.add("android-xml-styles")
    s["styling"] = sorted(styling)
    s["ui_libraries"] = sorted(d for d in deps if any(d.startswith(lib) for lib in UI_LIBS))
    if "pnpm-lock.yaml" in names: s["package_managers"].append("pnpm")
    if "yarn.lock" in names: s["package_managers"].append("yarn")
    if "package-lock.json" in names: s["package_managers"].append("npm")
    if "bun.lockb" in names or "bun.lock" in names: s["package_managers"].append("bun")
    if ".storybook" in {p.split("/")[0] for p in rel_files} or any(".stories." in f for f in lower):
        s["notes"].append("Storybook present — stories enumerate variants/states")

    dir_counter = Counter()
    for f in rel_files:
        if in_non_design_dir(f): continue
        ext = os.path.splitext(f)[1].lower()
        if ext in STYLE_EXT or "/components/" in f.lower() or "/ui/" in f.lower() or "theme" in f.lower() or "design" in f.lower():
            dir_counter[os.path.dirname(f)] += 1
    s["design_dirs"] = [d for d, _ in dir_counter.most_common(12) if d]
    return s, deps


def scan_tailwind(repo, rel_files):
    out = {"config_files": [], "theme_keys": [], "v4_theme_vars": []}
    for f in rel_files:
        base = os.path.basename(f)
        if base.startswith("tailwind.config"):
            out["config_files"].append(f)
            src = read_text(os.path.join(repo, f))
            out["theme_keys"] = sorted(set(re.findall(r"^\s{2,8}(colors|fontFamily|fontSize|spacing|borderRadius|boxShadow|screens|extend|animation|keyframes|zIndex|lineHeight|letterSpacing)\s*:", src, re.M)))
            m = re.search(r"darkMode\s*:\s*\[?\s*[\"']([^\"']+)", src)
            if m: out["darkMode"] = m.group(1)
        if f.endswith((".css", ".pcss")):
            src = read_text(os.path.join(repo, f))
            if "@import \"tailwindcss\"" in src or "@import 'tailwindcss'" in src or "@theme" in src:
                out["config_files"].append(f)
                for block in TW_THEME_BLOCK_RE.findall(src):
                    for name, val in CSS_VAR_RE.findall(block):
                        out["v4_theme_vars"].append({"name": name, "value": val.strip(), "source": f})
                m = re.search(r"@custom-variant\s+dark\s*\(([^)]*)\)", src)
                if m: out["darkMode"] = m.group(1).strip()
    return out


def classify(rel, ext, text):
    low = rel.lower()
    if ext in ASSET_EXT and ASSET_EXT[ext]:
        return "asset"
    if ext in STYLE_EXT:
        if any(k in low for k in ("token", "variable", "theme", "palette", "foundation")) or ":root" in text[:5000]:
            return "tokens"
        if any(k in low for k in ("reset", "normalize", "global", "base", "app.css", "index.css", "main.css", "styles.css")):
            return "stylesheet"
        return "stylesheet"
    if os.path.basename(low).startswith("tailwind.config") or os.path.basename(low) == "components.json":
        return "config"
    if ext in WEB_COMPONENT_EXT or ext in TEMPLATE_EXT or ext in NATIVE_EXT:
        if any(k in low for k in ("theme", "tokens", "designsystem", "design-system", "colors.", "color+", "font+", "typography", "palette", "dimens", "styles.xml", "themes.xml")):
            return "theme"
        if any(k in low for k in ("/layouts/", "/layout/", "layout.", "_app.", "_document.", "appshell", "app.vue", "+layout.")):
            return "layout"
        if any(k in low for k in ("/pages/", "/screens/", "/views/", "/routes/", "page.", "screen.", "/app/")) and ext not in (".xml",):
            return "screen"
        if any(k in low for k in ("/components/", "/ui/", "/widgets/", "/shared/", "/common/", "/elements/", "component", "/design/")):
            return "component"
        if ext in TEMPLATE_EXT:
            return "screen"
        if ext in (".swift", ".kt", ".dart", ".java", ".storyboard", ".xib"):
            if ext == ".storyboard" or ext == ".xib": return "screen"
            if re.search(r"\b(View|Screen|Page|Widget|Composable|Activity|Fragment)\b", text[:20000]):
                return "component"
        if ext == ".xml" and ("/res/layout" in low or "/res/values" in low or "/res/navigation" in low):
            return "theme" if "/values" in low else "screen"
        return None
    return None


def extract_from_css(text, rel, acc):
    for name, val in CSS_VAR_RE.findall(text):
        acc["css_vars"].append({"name": name, "value": val.strip(), "source": rel})
    for name, val in SCSS_VAR_RE.findall(text):
        acc["scss_vars"].append({"name": name, "value": val.strip(), "source": rel})
    for fam in FONT_FAMILY_RE.findall(text):
        fam = fam.strip()
        if fam.lower() in ("inherit", "initial", "unset", "revert") or fam.startswith("var("):
            continue
        acc["font_families"][fam] += 1
    for bp in MEDIA_RE.findall(text):
        acc["breakpoints"][bp] += 1
    for r in RADIUS_RE.findall(text):
        acc["radii"][r.strip()] += 1
    for sh in SHADOW_RE.findall(text):
        acc["shadows"][sh.strip()[:80]] += 1
    for z in ZINDEX_RE.findall(text):
        acc["z_indices"][z] += 1
    for sp in SPACE_RE.findall(text):
        for v in re.findall(r"-?\d*\.?\d+(?:px|rem|em)", sp):
            acc["spacing_values"][v] += 1
    for num, unit in DURATION_RE.findall(text):
        if "transition" in text or "animation" in text:
            acc["durations"][f"{num}{unit}"] += 1
    if "prefers-color-scheme: dark" in text: acc["dark_signals"]["media"] += 1
    if re.search(r"\.dark\b|\[data-theme=['\"]?dark", text): acc["dark_signals"]["class"] += 1
    if "prefers-reduced-motion" in text: acc["a11y_signals"]["reduced-motion"] += 1
    if "focus-visible" in text: acc["a11y_signals"]["focus-visible"] += 1
    if re.search(r"outline\s*:\s*(none|0)", text): acc["a11y_signals"]["outline-none"] += 1


CSS_CLASS_RE = re.compile(r"(?<![\w-])\.([a-zA-Z][\w-]*)(?=[\s,:.>+~\[{#])")
HTML_REGION_RE = re.compile(
    r"<(template|dialog|section|nav|header|aside|footer|main|form)\b[^>]*?(?:\bid=\"([^\"]+)\"|\bclass=\"([^\"]+)\")", re.I)
JS_UI_FN_RE = re.compile(r"\b(?:export\s+)?(?:async\s+)?function\s+((?:render|create|build|show|open|mount|draw|make)[A-Z]\w*)\s*\(")
JS_CLASS_RE = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b")


def extract_css_blocks(text, rel, acc):
    """Vanilla CSS 'components': group class selectors by BEM block / first hyphen segment."""
    for m in CSS_CLASS_RE.finditer(text):
        cls = m.group(1)
        if cls.startswith(("is-", "has-", "js-", "u-", "sr-", "no-")) or len(cls) < 3:
            continue
        block = cls.split("__")[0].split("--")[0]
        if "__" not in cls and "--" not in cls:
            block = cls.split("-")[0] if len(cls.split("-")[0]) >= 3 else cls
        line = text.count("\n", 0, m.start()) + 1
        entry = acc["css_blocks"][block]
        entry["count"] += 1
        entry["classes"].add(cls)
        if entry["source"] is None: entry["source"] = f"{rel}:{line}"


def extract_html_regions(text, rel, acc):
    for m in HTML_REGION_RE.finditer(text):
        tag, ident, cls = m.group(1).lower(), m.group(2), m.group(3)
        name = ident or (cls.split()[0] if cls else None)
        if not name: continue
        if (name, rel) in acc["html_region_seen"]: continue
        acc["html_region_seen"].add((name, rel))
        line = text.count("\n", 0, m.start()) + 1
        acc["components"].append({"name": name, "kind": f"html-{tag}", "source": f"{rel}:{line}"})


def collect_colors(text, rel, acc):
    for m in HEX_RE.finditer(text):
        acc["colors"][m.group(0).lower()].add(f"{rel}:{text.count(chr(10), 0, m.start()) + 1}")
    for m in FUNC_COLOR_RE.finditer(text):
        v = m.group(0)
        if "var(" in v or "url(" in v:  # skip color(var(--x)) and false positives
            continue
        acc["colors"][re.sub(r"\s+", "", v)].add(f"{rel}:{text.count(chr(10), 0, m.start()) + 1}")
    for m in TW_ARBITRARY_RE.finditer(text):
        acc["tw_arbitrary"][m.group(1).lower()] += 1


def extract_components(text, rel, ext, acc):
    def add(name, kind, line):
        acc["components"].append({"name": name, "kind": kind, "source": f"{rel}:{line}"})

    def line_of(m): return text.count("\n", 0, m.start()) + 1

    if ext in (".jsx", ".tsx"):
        for m in REACT_CMP_RE.finditer(text):
            add(m.group(1), "react-component", line_of(m))
        for m in STYLED_RE.finditer(text):
            add(m.group(1), "styled-component", line_of(m))
        if re.search(r"\bcva\(|\btv\(", text): acc["variant_defs"].append(rel)
    elif ext in (".js", ".ts", ".mjs"):
        if re.search(r"React\.|from ['\"]react['\"]|\bjsx\b", text):
            for m in REACT_CMP_RE.finditer(text):
                add(m.group(1), "react-component", line_of(m))
        elif re.search(r"document\.(?:createElement|querySelector|getElementById)|innerHTML|\.classList\.", text):
            for m in JS_UI_FN_RE.finditer(text): add(m.group(1), "js-ui-function", line_of(m))
            for m in JS_CLASS_RE.finditer(text): add(m.group(1), "js-ui-class", line_of(m))
        for m in STYLED_RE.finditer(text):
            add(m.group(1), "styled-component", line_of(m))
        if re.search(r"\bcva\(|\btv\(", text): acc["variant_defs"].append(rel)
        for block in re.findall(r"(?:innerHTML|insertAdjacentHTML\([^,]+,)\s*=?\s*`([^`]{40,4000})`", text):
            extract_html_regions(block, rel, acc)
    elif ext in (".vue", ".svelte", ".astro"):
        add(os.path.splitext(os.path.basename(rel))[0], f"{ext[1:]}-sfc", 1)
        for block in VUE_SVELTE_STYLE_RE.findall(text):
            extract_from_css(block, rel, acc)
    elif ext == ".swift":
        for m in SWIFT_VIEW_RE.finditer(text): add(m.group(1), "swiftui-view", line_of(m))
        for m in SWIFT_MOD_RE.finditer(text): add(m.group(1), "swiftui-style", line_of(m))
        for m in UIKIT_VC_RE.finditer(text): add(m.group(1), "uikit-class", line_of(m))
        for m in SWIFT_COLOR_RE.finditer(text):
            acc["native_color_literals"][m.group(0)[:60]].add(f"{rel}:{line_of(m)}")
        for m in re.finditer(r"\.padding\((\d+(?:\.\d+)?)\)|\.cornerRadius\((\d+)\)|\.font\(\.system\(size:\s*(\d+)", text):
            acc["native_magic_numbers"][m.group(0)] += 1
    elif ext in (".kt", ".kts", ".java"):
        for m in COMPOSE_RE.finditer(text): add(m.group(1), "composable", line_of(m))
        for m in KOTLIN_COLOR_RE.finditer(text):
            acc["native_color_literals"][m.group(0)].add(f"{rel}:{line_of(m)}")
        for m in re.finditer(r"\b(\d+)\.dp\b|\b(\d+)\.sp\b", text):
            acc["native_magic_numbers"][m.group(0)] += 1
    elif ext == ".dart":
        for m in FLUTTER_WIDGET_RE.finditer(text): add(m.group(1), "flutter-widget", line_of(m))
        for m in DART_COLOR_RE.finditer(text):
            acc["native_color_literals"][m.group(0)].add(f"{rel}:{line_of(m)}")
        for m in re.finditer(r"EdgeInsets\.(?:all|symmetric|only)\([^)]{1,40}\)|fontSize:\s*\d+", text):
            acc["native_magic_numbers"][m.group(0)[:50]] += 1
    elif ext == ".xml":
        for name, val in XML_COLOR_RE.findall(text):
            acc["css_vars"].append({"name": f"@color/{name}", "value": val, "source": rel})
        for name, val in XML_DIMEN_RE.findall(text):
            acc["css_vars"].append({"name": f"@dimen/{name}", "value": val, "source": rel})
        for name in XML_STYLE_RE.findall(text):
            add(name, "android-style", 1)
        if "/res/layout" in rel:
            add(os.path.splitext(os.path.basename(rel))[0], "android-layout", 1)
        for m in re.finditer(r"android:(?:textColor|background|tint)=\"(#[0-9a-fA-F]{6,8})\"", text):
            acc["colors"][m.group(1).lower()].add(f"{rel}:{line_of(m)}")
    elif ext in (".storyboard", ".xib"):
        for m in re.finditer(r"<viewController[^>]*customClass=\"([^\"]+)\"", text):
            add(m.group(1), "storyboard-scene", line_of(m))


def extract_routes(text, rel, ext, acc):
    for label, rx in ROUTE_PATTERNS:
        for m in rx.finditer(text):
            route = m.group(1)
            if route.startswith(("/", "*")) or label in ("compose-nav",):
                acc["routes"].append({"route": route, "via": label, "source": rel})


def file_based_routes(rel_files, acc):
    for f in rel_files:
        low = f.lower().replace("\\", "/")
        base = os.path.basename(low)
        # Next.js App Router
        if re.search(r"(^|/)app/.*page\.(tsx|jsx|js|ts|mdx)$", low):
            route = "/" + re.sub(r"(^|.*/)app/", "", os.path.dirname(low))
            route = re.sub(r"/\([^/]+\)", "", route).replace("//", "/") or "/"
            acc["routes"].append({"route": route, "via": "next-app", "source": f})
        elif re.search(r"(^|/)app/.*(layout|loading|error|not-found)\.(tsx|jsx)$", low):
            acc["route_states"].append({"kind": base.split(".")[0], "source": f})
        # Next.js Pages Router
        elif re.search(r"(^|/)pages/.*\.(tsx|jsx|js|ts|mdx)$", low) and not base.startswith(("_app", "_document", "_error")) and "/api/" not in low:
            route = "/" + re.sub(r"(^|.*/)pages/", "", os.path.splitext(low)[0])
            route = re.sub(r"/index$", "", route) or "/"
            acc["routes"].append({"route": route, "via": "next-pages", "source": f})
        # Nuxt
        elif re.search(r"(^|/)pages/.*\.vue$", low):
            route = "/" + re.sub(r"(^|.*/)pages/", "", os.path.splitext(low)[0])
            acc["routes"].append({"route": re.sub(r"/index$", "", route) or "/", "via": "nuxt-pages", "source": f})
        # SvelteKit
        elif re.search(r"(^|/)routes/.*\+page\.svelte$", low):
            route = "/" + re.sub(r"(^|.*/)routes/", "", os.path.dirname(low))
            acc["routes"].append({"route": re.sub(r"/\([^/]+\)", "", route) or "/", "via": "sveltekit", "source": f})
        # Expo Router
        elif re.search(r"(^|/)app/.*\.(tsx|jsx)$", low) and not base.startswith("_") and "page." not in base:
            pass  # handled by next-app pattern if page.*; expo files are plain route names
        # Astro
        elif re.search(r"(^|/)src/pages/.*\.(astro|md|mdx)$", low):
            route = "/" + re.sub(r"(^|.*/)src/pages/", "", os.path.splitext(low)[0])
            acc["routes"].append({"route": re.sub(r"/index$", "", route) or "/", "via": "astro", "source": f})
        # Android XML activities/fragments
        elif re.search(r"/res/layout/(activity|fragment)_[^/]+\.xml$", low):
            acc["routes"].append({"route": base.replace(".xml", ""), "via": "android-layout", "source": f})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default=None, help="write inventory.json here")
    ap.add_argument("--summary", default=None, help="write a Markdown summary here")
    ap.add_argument("--detect-only", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        sys.exit(f"not a directory: {repo}")

    all_files = list(walk(repo))
    rel_files = [r for _, r in all_files]
    stack, deps = detect_stack(repo, rel_files)
    tw = scan_tailwind(repo, rel_files)
    if tw["config_files"]:
        stack["tailwind"] = tw
        if "tailwind" not in stack["styling"]: stack["styling"].append("tailwind")

    if args.detect_only:
        print(json.dumps({"stack": stack, "files_total": len(rel_files)}, indent=2))
        return

    acc = {
        "css_vars": [], "scss_vars": [], "font_families": Counter(), "breakpoints": Counter(),
        "radii": Counter(), "shadows": Counter(), "z_indices": Counter(), "spacing_values": Counter(),
        "durations": Counter(), "colors": defaultdict(set), "tw_arbitrary": Counter(),
        "components": [], "variant_defs": [], "routes": [], "route_states": [],
        "native_color_literals": defaultdict(set), "native_magic_numbers": Counter(),
        "dark_signals": Counter(), "a11y_signals": Counter(),
        "css_blocks": defaultdict(lambda: {"count": 0, "classes": set(), "source": None}),
        "html_region_seen": set(),
    }
    design_files, assets = [], []

    for abs_path, rel in all_files:
        if in_non_design_dir(rel):
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext in ASSET_EXT and ASSET_EXT[ext]:
            if "/node_modules/" in rel: continue
            try: size = os.path.getsize(abs_path)
            except OSError: size = None
            assets.append({"id": f"ast.{ASSET_EXT[ext]}.{re.sub(r'[^a-z0-9]+', '-', os.path.splitext(os.path.basename(rel))[0].lower()).strip('-')}",
                           "kind": ASSET_EXT[ext], "source": rel, "format": ext[1:], "size_bytes": size})
            continue
        if ext not in STYLE_EXT | WEB_COMPONENT_EXT | TEMPLATE_EXT | NATIVE_EXT:
            continue
        text = read_text(abs_path)
        if not text: continue
        if is_vendored(rel):
            design_files.append({"path": rel, "kind": "vendored", "lines": text.count("\n") + 1})
            continue
        kind = classify(rel, ext, text)
        if ext in STYLE_EXT:
            extract_from_css(text, rel, acc)
            collect_colors(text, rel, acc)
            extract_css_blocks(text, rel, acc)
        elif ext in WEB_COMPONENT_EXT | TEMPLATE_EXT | NATIVE_EXT:
            if kind is None and not re.search(r"className|class=|style=|styled|@Composable|: View|Widget|<style", text):
                continue
            extract_components(text, rel, ext, acc)
            extract_routes(text, rel, ext, acc)
            collect_colors(text, rel, acc)
            if ext in TEMPLATE_EXT or ext in (".jsx", ".tsx", ".vue", ".svelte", ".astro"):
                # inline styles and style blocks
                for block in re.findall(r"<style[^>]*>(.*?)</style>", text, re.S):
                    extract_from_css(block, rel, acc)
                    extract_css_blocks(block, rel, acc)
                if ext in (".html", ".htm"):
                    extract_html_regions(text, rel, acc)
                    # a standalone HTML document is a screen (static site, extension page, template root)
                    if "<html" in text[:3000].lower():
                        acc["routes"].append({"route": "/" + rel.replace("\\", "/"), "via": "html-document", "source": rel})
                        kind = "screen"
            if kind is None: kind = "component"
        design_files.append({"path": rel, "kind": kind, "lines": text.count("\n") + 1})

    file_based_routes(rel_files, acc)
    for label, page in (stack.get("extension", {}).get("entry_pages") or {}).items():
        acc["routes"].insert(0, {"route": "/" + page.lstrip("/"), "via": f"extension-{label}", "source": stack["extension"]["manifest"]})

    # dark mode
    dm = "none"
    if stack.get("tailwind", {}).get("darkMode"): dm = stack["tailwind"]["darkMode"]
    elif acc["dark_signals"]["class"] and acc["dark_signals"]["media"]: dm = "both"
    elif acc["dark_signals"]["class"]: dm = "class"
    elif acc["dark_signals"]["media"]: dm = "media"
    if stack["framework"] in ("swiftui", "compose", "flutter", "uikit"): dm = "system (verify in theme code)"
    stack["dark_mode"] = dm

    # tokens from css/scss vars
    def group_of(name, value):
        n, v = name.lower(), value.lower()
        if HEX_RE.search(v) or re.search(r"\b(rgb|hsl|oklch|lab)", v) or "color" in n or v.strip() in NAMED_COLORS: return "color"
        if re.search(r"(^|-)(bg|background|fg|text|border|surface|accent|primary|brand)(-|$)", n) and not re.search(r"\d+(px|rem|em|%)", v): return "color"
        if "font" in n and ("family" in n or re.search(r"[A-Za-z]+,", v)): return "font"
        if "size" in n or "text-" in n or "leading" in n or "line-height" in n or "weight" in n: return "type-scale"
        if "space" in n or "spacing" in n or "gap" in n or "padding" in n: return "space"
        if "radius" in n or "rounded" in n: return "radius"
        if "shadow" in n or "elevation" in n: return "shadow"
        if "duration" in n or "ease" in n or "motion" in n or "transition" in n: return "motion"
        if "breakpoint" in n or "screen" in n or n.startswith("--bp"): return "bp"
        if "z-" in n or "zindex" in n or "z_" in n: return "z"
        if "opacity" in n: return "opacity"
        if "border" in n or "stroke" in n: return "border"
        return "other"

    tokens, seen = [], set()
    for v in acc["css_vars"] + acc["scss_vars"] + [{"name": x["name"], "value": x["value"], "source": x["source"]} for x in tw.get("v4_theme_vars", [])]:
        key = (v["name"], v["source"])
        if key in seen: continue
        seen.add(key)
        g = group_of(v["name"], v["value"])
        slug = re.sub(r"[^a-z0-9]+", "-", v["name"].lower().lstrip("-$@").replace("/", "-")).strip("-").replace("-", ".")
        tokens.append({"id": f"tok.{g}.{slug}", "group": g, "name": v["name"], "value": v["value"], "source": v["source"]})

    literals = []
    for val, locs in sorted(acc["colors"].items(), key=lambda kv: -len(kv[1])):
        literals.append({"value": val, "kind": "color", "occurrences": len(locs), "files": sorted(locs)[:25]})
    for val, locs in sorted(acc["native_color_literals"].items(), key=lambda kv: -len(kv[1])):
        literals.append({"value": val, "kind": "native-color", "occurrences": len(locs), "files": sorted(locs)[:25]})
    for val, n in acc["tw_arbitrary"].most_common():
        literals.append({"value": f"[{val}]", "kind": "tailwind-arbitrary", "occurrences": n, "files": []})

    # components: dedupe by name+source, drop obvious non-components
    comp_seen, components = set(), set()
    comps = []
    NOISE = {"App", "Main", "Index", "Default", "Props", "State", "Context", "Provider", "Component", "React", "Fragment"}
    # vanilla CSS blocks become component candidates when they are used more than a few times
    for block, info in sorted(acc["css_blocks"].items(), key=lambda kv: -kv[1]["count"])[:150]:
        if info["count"] < 3 or len(info["classes"]) < 2:
            continue
        acc["components"].append({"name": block, "kind": "css-block", "source": info["source"],
                                  "classes": sorted(info["classes"])[:40], "selector_count": info["count"]})
    for c in acc["components"]:
        if c["name"] in NOISE and c["kind"] == "react-component": continue
        if re.fullmatch(r"[A-Z0-9_]+", c["name"]): continue          # SCREAMING_CASE constants
        key = (c["name"], c["source"])
        if key in comp_seen: continue
        comp_seen.add(key)
        fam = "misc"
        n = c["name"].lower()
        for f, words in {"button": ["button", "btn", "cta", "fab"], "input": ["input", "field", "select", "checkbox", "radio", "switch", "toggle", "textarea", "form", "picker", "slider"],
                         "nav": ["nav", "menu", "sidebar", "tabbar", "tab", "header", "topbar", "appbar", "breadcrumb", "drawer", "footer"],
                         "card": ["card", "tile", "panel"], "list": ["list", "table", "grid", "row", "item", "feed"],
                         "feedback": ["toast", "snackbar", "alert", "banner", "notification", "progress", "spinner", "loader", "skeleton", "badge", "chip", "tag"],
                         "overlay": ["modal", "dialog", "sheet", "popover", "tooltip", "dropdown", "popup"],
                         "media": ["avatar", "image", "icon", "logo", "illustration", "thumbnail", "video"],
                         "typography": ["heading", "title", "text", "label", "caption", "paragraph"],
                         "layout": ["layout", "container", "stack", "box", "section", "divider", "spacer", "shell", "page", "screen", "view"]}.items():
            if any(w in n for w in words): fam = f; break
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"(?<!^)(?=[A-Z])", "-", c["name"]).lower()).strip("-")
        cid = f"cmp.{fam}.{slug}"
        if cid in components:
            n = 2
            while f"{cid}-{n}" in components: n += 1
            cid = f"{cid}-{n}"
        components.add(cid)
        entry = {"id": cid, "name": c["name"], "family": fam, "kind": c["kind"], "source": c["source"]}
        if c.get("classes"): entry["classes"] = c["classes"]; entry["selector_count"] = c["selector_count"]
        comps.append(entry)

    routes_seen, routes = set(), []
    for r in acc["routes"]:
        if r["route"] in routes_seen: continue
        routes_seen.add(r["route"])
        slug = re.sub(r"[^a-z0-9]+", ".", r["route"].lower().strip("/").replace("[", "").replace("]", "").replace(":", "")).strip(".") or "home"
        routes.append({"id": f"scr.{slug}", "route": r["route"], "via": r["via"], "source": r["source"]})

    inventory = {
        "meta": {"generated": str(date.today()), "repo": repo, "commit": git_commit(repo), "tool": "RedesignMyApp by Pluristack — inventory_scan.py"},
        "stack": stack,
        "files": design_files,
        "tokens": tokens,
        "token_candidates": {
            "font_families": acc["font_families"].most_common(),
            "breakpoints": acc["breakpoints"].most_common(),
            "radii": acc["radii"].most_common(20),
            "shadows": acc["shadows"].most_common(20),
            "z_indices": acc["z_indices"].most_common(),
            "spacing_values": acc["spacing_values"].most_common(40),
            "durations": acc["durations"].most_common(),
            "native_magic_numbers": acc["native_magic_numbers"].most_common(40),
            "tailwind": tw if tw["config_files"] else None,
        },
        "literals": literals,
        "components": comps,
        "variant_definition_files": sorted(set(acc["variant_defs"])),
        "screens": routes,
        "route_state_files": acc["route_states"],
        "layouts": [],
        "assets": assets,
        "patterns": [],
        "issues": [],
        "signals": {"dark_mode": dict(acc["dark_signals"]), "a11y": dict(acc["a11y_signals"])},
        "coverage": {"files_scanned": len(rel_files), "files_design_relevant": len(design_files), "files_described": 0, "excluded": []},
    }

    out = args.out or "inventory.json"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    summary = []
    summary.append(f"# Inventory scan summary\n")
    summary.append(f"- Repo: `{repo}` · commit `{inventory['meta']['commit']}` · {inventory['meta']['generated']}")
    summary.append(f"- Platform: **{stack['platform']}** · framework: **{stack['framework']}** · styling: {', '.join(stack['styling']) or '—'}")
    summary.append(f"- UI libraries: {', '.join(stack['ui_libraries']) or '—'} · dark mode: {stack['dark_mode']}")
    summary.append(f"- Design dirs: {', '.join(stack['design_dirs'][:8]) or '—'}")
    summary.append(f"- Files: {len(rel_files)} scanned, {len(design_files)} design-relevant ({Counter(d['kind'] for d in design_files).most_common()})")
    summary.append(f"- Tokens (declared variables): {len(tokens)} · color literals: {sum(1 for l in literals if l['kind']=='color')} distinct · tailwind arbitrary: {len(acc['tw_arbitrary'])}")
    summary.append(f"- Components (candidates): {len(comps)} · screens/routes: {len(routes)} · assets: {len(assets)}")
    summary.append(f"- Distinct spacing values: {len(acc['spacing_values'])} · radii: {len(acc['radii'])} · shadows: {len(acc['shadows'])} · z-indices: {len(acc['z_indices'])} · breakpoints: {dict(acc['breakpoints'])}")
    summary.append(f"- Font families: {[f for f, _ in acc['font_families'].most_common(6)]}")
    summary.append(f"- A11y signals: {dict(acc['a11y_signals'])}")
    summary.append("\n## Top color literals\n")
    for l in literals[:15]:
        summary.append(f"- `{l['value']}` × {l['occurrences']} — {', '.join(l['files'][:3])}")
    summary.append("\n## Components by family\n")
    fam_counter = Counter(c["family"] for c in comps)
    for fam, n in fam_counter.most_common():
        summary.append(f"- {fam}: {n} — " + ", ".join(c["name"] for c in comps if c["family"] == fam)[:300])
    summary.append("\n## Screens / routes\n")
    for r in routes[:80]:
        summary.append(f"- `{r['route']}` ({r['via']}) — {r['source']}")
    text = "\n".join(summary)
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
