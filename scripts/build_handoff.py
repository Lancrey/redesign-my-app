#!/usr/bin/env python3
"""
build_handoff.py — assemble the Claude Design package for RedesignMyApp (Pluristack).

Usage:
  python3 build_handoff.py <redesign-dir> --skill-path <path-to-skill> [--repo <repo-root>] [--assets-only]

What it does:
  1. Copies the Pluristack signature assets into <redesign-dir>/assets/ (safe at any step; --assets-only stops here).
  2. Derives tokens.json from inventory.json.
  3. Writes inventory-summary.md (condensed component and screen tables).
  4. Collects the app's own brand files (logo*, favicon*, brand/*) from the repo into brand/.
  5. Writes README-for-Claude-Design.md.
  6. Zips brief + tokens + summary + screens + brand + pluristack assets into claude-design-package.zip.
Standard library only.
"""
import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import date

BRAND_FILES = ["pluristack-logo-small.svg", "pluristack-logo-small-white.svg", "pluristack-logo.svg",
               "pluristack-logo-white.svg", "pluristack-favicon.svg"]

README = """# Package contents — RedesignMyApp by Pluristack

- `03-claude-design-brief.md` — the brief. Start here.
- `tokens.json` — current design tokens (machine-readable), with per-theme values and data palettes when the app has them.
- `inventory-summary.md` — condensed component, screen, layout, palette, pattern and issue tables.
- `00-brief.md`, `02-design-review.md` — project interview and design review (the user's decisions are in the review's Decisions section).
- `screens/` — screenshots of the current UI, named `<screen>--<viewport>--<scheme>.png`.
- `brand/` — the app's own logo, icons and brand files found in the repository (if any); keep them.
- `assets/` — Pluristack signature logos used by the documents' header (not part of the app's brand).

Element IDs (`tok.*`, `cmp.*`, `scr.*`) must be preserved in all outputs.
Generated {today} — www.pluristack.com
"""


def copy_brand_assets(skill_path, redesign):
    src = os.path.join(skill_path, "assets", "brand")
    dst = os.path.join(redesign, "assets")
    os.makedirs(dst, exist_ok=True)
    copied = []
    for name in BRAND_FILES:
        s = os.path.join(src, name)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(dst, name))
            copied.append(name)
    return copied


def derive_tokens(inventory):
    tokens = {"meta": {"generated": str(date.today()), "source": "RedesignMyApp inventory.json", "ids": "keep these IDs in the redesign"},
              "color": {}, "typography": {}, "space": {}, "radius": {}, "shadow": {}, "motion": {}, "breakpoints": {}, "z": {}, "other": {}}
    group_map = {"color": "color", "font": "typography", "type-scale": "typography", "space": "space", "radius": "radius",
                 "shadow": "shadow", "motion": "motion", "bp": "breakpoints", "z": "z"}
    for t in inventory.get("tokens", []):
        bucket = group_map.get(t.get("group"), "other")
        entry = {"name": t.get("name"), "value": t.get("value"), "source": t.get("source")}
        if t.get("value_dark"): entry["dark"] = t["value_dark"]
        if t.get("values_by_theme"): entry["themes"] = t["values_by_theme"]
        if t.get("role"): entry["role"] = t["role"]
        if t.get("usage_count") is not None: entry["usage_count"] = t["usage_count"]
        tokens[bucket][t["id"]] = entry
    themes = (inventory.get("stack") or {}).get("themes")
    if themes:
        tokens["meta"]["themes"] = themes
        tokens["meta"]["themes_note"] = ("'themes' gives a token's value per theme; a missing theme inherits the light value. "
                                         "The redesign must give a value for every theme or propose dropping it.")
    if inventory.get("palettes"):
        tokens["palettes"] = {p.get("id", f"palette-{i}"): {k: v for k, v in p.items() if k != "id"}
                              for i, p in enumerate(inventory["palettes"])}
    cands = inventory.get("token_candidates", {}) or {}
    tokens["observed_values"] = {
        "font_families": cands.get("font_families", []),
        "breakpoints": cands.get("breakpoints", []),
        "radii": cands.get("radii", []),
        "shadows": cands.get("shadows", []),
        "spacing_values": cands.get("spacing_values", []),
        "z_indices": cands.get("z_indices", []),
        "durations": cands.get("durations", []),
    }
    tokens["hardcoded_literals"] = [
        {"value": l["value"], "kind": l["kind"], "occurrences": l["occurrences"], "closest_token": l.get("closest_token")}
        for l in inventory.get("literals", [])[:80]
    ]
    return tokens


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = ", ".join(str(x) for x in v)
    elif isinstance(v, dict):
        v = json.dumps(v, ensure_ascii=False)
    return str(v).replace("|", "\\|").replace("\n", " ")


def _captures_for(screen_id, screens_dir):
    """Match screens/<slug>--<viewport>--<scheme>.png to scr.<slug with dots as hyphens>."""
    if not os.path.isdir(screens_dir):
        return []
    slug = screen_id.split(".", 1)[-1].replace(".", "-")
    return sorted(fn for fn in os.listdir(screens_dir) if fn.startswith(slug + "--"))


def summary_md(inventory, screens_dir):
    st = inventory.get("stack", {}) or {}
    L = ["# Inventory summary (condensed)\n",
         f"Stack: {st.get('platform')} / {st.get('framework')} / {', '.join(st.get('styling', []))}"
         + (f" · themes: {', '.join(map(str, st['themes']))}" if st.get("themes") else "") + "\n",
         f"Counts: {len(inventory.get('tokens', []))} tokens · {len(inventory.get('components', []))} components · "
         f"{len(inventory.get('screens', []))} screens · {len(inventory.get('layouts', []))} layouts · "
         f"{len(inventory.get('patterns', []))} patterns · {len(inventory.get('issues', []))} issues. Full token data: `tokens.json`.\n",
         "## Components\n",
         "| ID | Name | Family | Description | Variants / props | States | Missing states | Used in | Source |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in inventory.get("components", []):
        used = c.get("used_in") or c.get("usage_count")
        L.append(f"| `{c.get('id')}` | {_cell(c.get('name'))} | {_cell(c.get('family'))} | {_cell(c.get('description'))} | "
                 f"{_cell(c.get('variants') or c.get('props_affecting_appearance'))} | {_cell(c.get('states'))} | "
                 f"{_cell(c.get('states_missing'))} | {_cell(used)} | `{_cell(c.get('source'))}` |")
    L += ["\n## Screens\n", "| ID | Title | Route / state | Layout | Primary action | Components | Captures |",
          "|---|---|---|---|---|---|---|"]
    for sc in inventory.get("screens", []):
        caps = _captures_for(sc.get("id", ""), screens_dir) or ([sc["screenshot"]] if sc.get("screenshot") else [])
        L.append(f"| `{sc.get('id')}` | {_cell(sc.get('name'))} | `{_cell(sc.get('route'))}` | `{_cell(sc.get('layout'))}` | "
                 f"{_cell(sc.get('primary_action'))} | {_cell(sc.get('components'))} | {_cell(caps) or 'not captured'} |")
    if inventory.get("layouts"):
        L += ["\n## Layouts\n", "| ID | Regions | Used by | Source |", "|---|---|---|---|"]
        for l in inventory["layouts"]:
            L.append(f"| `{l.get('id')}` | {_cell(l.get('regions'))} | {_cell(l.get('used_by'))} | `{_cell(l.get('source'))}` |")
    if inventory.get("palettes"):
        L += ["\n## Data and feature palettes\n", "| ID | Role | Size / values | Source | Hazard |", "|---|---|---|---|---|"]
        for p in inventory["palettes"]:
            L.append(f"| `{p.get('id')}` | {_cell(p.get('role'))} | {_cell(p.get('count') or p.get('values'))} | "
                     f"`{_cell(p.get('source'))}` | {_cell(p.get('hazard'))} |")
    L += ["\n## Patterns\n"]
    for p in inventory.get("patterns", []):
        L.append(f"- `{p.get('id')}` — {p.get('description')}" + (f" (`{_cell(p.get('source'))}`)" if p.get("source") else ""))
    L += ["\n## Known issues\n"]
    for i in inventory.get("issues", []):
        L.append(f"- **{i.get('id')}** ({i.get('kind')}): {i.get('summary')}"
                 + (f" — evidence: {_cell(i.get('evidence'))}" if i.get("evidence") else ""))
    L += ["\n---", "*Generated with RedesignMyApp by Pluristack — www.pluristack.com*"]
    return "\n".join(L) + "\n"


def collect_app_brand(repo, dst, keep=()):
    if not repo or not os.path.isdir(repo):
        return []
    found = []
    # files the inventory names as brand (e.g. brand.keep) and icons declared in a web/extension manifest
    explicit = [k for k in keep if isinstance(k, str) and os.path.isfile(os.path.join(repo, k))]
    for mf in ("manifest.json", "public/manifest.json", "src/manifest.json", "manifest.webmanifest", "public/manifest.webmanifest"):
        mp = os.path.join(repo, mf)
        if os.path.isfile(mp):
            try:
                m = json.load(open(mp, encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            icons = m.get("icons")
            paths = list(icons.values()) if isinstance(icons, dict) else [i.get("src") for i in icons or [] if isinstance(i, dict)]
            for ip in paths:
                if ip and os.path.isfile(os.path.join(os.path.dirname(mp), ip)):
                    explicit.append(os.path.relpath(os.path.join(os.path.dirname(mp), ip), repo))
    for rel in dict.fromkeys(explicit):
        os.makedirs(dst, exist_ok=True)
        name = rel.replace(os.sep, "__")
        shutil.copy2(os.path.join(repo, rel), os.path.join(dst, name))
        found.append(name)
    # word-boundary match so "logout.svg" is not taken for a logo
    rx = re.compile(r"(^|[^a-z])(logo|favicon|brand|wordmark|app-?icon|apple-touch-icon|icon-?(16|32|48|64|128|192|256|512))([^a-z]|$)", re.I)
    skip = {".git", "node_modules", "dist", "build", ".next", "redesign", "vendor", "Pods"}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in files:
            if rx.search(fn) and fn.lower().endswith((".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico")):
                src = os.path.join(root, fn)
                try:
                    if os.path.getsize(src) > 3_000_000: continue
                except OSError:
                    continue
                os.makedirs(dst, exist_ok=True)
                rel = os.path.relpath(src, repo).replace(os.sep, "__")
                if rel in found: continue
                shutil.copy2(src, os.path.join(dst, rel))
                found.append(rel)
                if len(found) >= 25: return found
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("redesign_dir")
    ap.add_argument("--skill-path", required=True)
    ap.add_argument("--repo", default=None, help="repo root, to collect the app's own brand files")
    ap.add_argument("--assets-only", action="store_true")
    args = ap.parse_args()

    redesign = os.path.abspath(args.redesign_dir)
    os.makedirs(redesign, exist_ok=True)
    copied = copy_brand_assets(os.path.abspath(args.skill_path), redesign)
    print(f"Pluristack assets copied to {os.path.join(redesign, 'assets')}: {copied}")
    if args.assets_only:
        return

    inv_path = os.path.join(redesign, "inventory.json")
    if not os.path.exists(inv_path):
        sys.exit("inventory.json not found — run Step 1 first")
    with open(inv_path, encoding="utf-8") as f:
        inventory = json.load(f)

    tokens = derive_tokens(inventory)
    with open(os.path.join(redesign, "tokens.json"), "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    with open(os.path.join(redesign, "inventory-summary.md"), "w", encoding="utf-8") as f:
        f.write(summary_md(inventory, os.path.join(redesign, "screens")))
    with open(os.path.join(redesign, "README-for-Claude-Design.md"), "w", encoding="utf-8") as f:
        f.write(README.format(today=date.today()))

    repo = args.repo or os.path.dirname(redesign)
    brand_dir = os.path.join(redesign, "brand")
    if os.path.isdir(brand_dir):
        shutil.rmtree(brand_dir)  # rebuilt from scratch each run
    keep = ((inventory.get("brand") or {}).get("keep") or []) if isinstance(inventory.get("brand"), dict) else []
    brand = collect_app_brand(repo, brand_dir, keep)
    print(f"App brand files collected: {len(brand)}")

    brief = os.path.join(redesign, "03-claude-design-brief.md")
    if not os.path.exists(brief):
        print("WARNING: 03-claude-design-brief.md not found; the package will be built without it. Write the brief, then re-run.")

    zip_path = os.path.join(redesign, "claude-design-package.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("03-claude-design-brief.md", "tokens.json", "inventory-summary.md", "README-for-Claude-Design.md", "00-brief.md", "02-design-review.md"):
            p = os.path.join(redesign, name)
            if os.path.exists(p): z.write(p, name)
        screens = os.path.join(redesign, "screens")
        if os.path.isdir(screens):
            for fn in sorted(os.listdir(screens)):
                if fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".json")):
                    z.write(os.path.join(screens, fn), f"screens/{fn}")
        if os.path.isdir(brand_dir):
            for fn in sorted(os.listdir(brand_dir)):
                z.write(os.path.join(brand_dir, fn), f"brand/{fn}")
        for name in copied:
            z.write(os.path.join(redesign, "assets", name), f"assets/{name}")
    size = os.path.getsize(zip_path)
    print(f"Package written: {zip_path} ({size/1024:.0f} KB)")
    if size > 45 * 1024 * 1024:
        print("WARNING: package is large; consider reducing screenshots (fewer viewports) before uploading.")


if __name__ == "__main__":
    main()
