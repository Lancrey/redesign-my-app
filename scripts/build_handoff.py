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
- `tokens.json` — current design tokens (machine-readable).
- `inventory-summary.md` — condensed component and screen tables for quick reference.
- `screens/` — screenshots of the current UI, named `<screen>--<viewport>--<scheme>.png`.
- `brand/` — the app's own logo and brand files found in the repository (if any).
- `pluristack/` — Pluristack signature assets (not part of the app's brand).

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
        if t.get("role"): entry["role"] = t["role"]
        if t.get("usage_count") is not None: entry["usage_count"] = t["usage_count"]
        tokens[bucket][t["id"]] = entry
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


def summary_md(inventory):
    lines = ["# Inventory summary (condensed)\n",
             f"Stack: {inventory.get('stack', {}).get('platform')} / {inventory.get('stack', {}).get('framework')} / {', '.join(inventory.get('stack', {}).get('styling', []))}\n",
             "## Components\n", "| ID | Name | Family | Variants | States | Used in | Source |", "|---|---|---|---|---|---|---|"]
    for c in inventory.get("components", []):
        lines.append(f"| `{c.get('id')}` | {c.get('name')} | {c.get('family')} | {', '.join(c.get('variants', []) or (c.get('props_affecting_appearance') or []))} | "
                     f"{', '.join(c.get('states', []))} | {c.get('usage_count', '')} | `{c.get('source')}` |")
    lines += ["\n## Screens\n", "| ID | Title | Route | Primary action | Components | Capture |", "|---|---|---|---|---|---|"]
    for s in inventory.get("screens", []):
        lines.append(f"| `{s.get('id')}` | {s.get('name', '')} | `{s.get('route', '')}` | {s.get('primary_action', '')} | "
                     f"{', '.join(s.get('components', []))} | {s.get('screenshot', '')} |")
    lines += ["\n## Patterns\n"]
    for p in inventory.get("patterns", []):
        lines.append(f"- `{p.get('id')}` — {p.get('description')}")
    lines += ["\n## Known issues\n"]
    for i in inventory.get("issues", []):
        lines.append(f"- {i.get('id')} ({i.get('kind')}): {i.get('summary')}")
    return "\n".join(lines) + "\n"


def collect_app_brand(repo, dst):
    if not repo or not os.path.isdir(repo):
        return []
    found = []
    rx = re.compile(r"(logo|favicon|brand|wordmark|icon-512|icon-192|app-icon|apple-touch-icon)", re.I)
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
        f.write(summary_md(inventory))
    with open(os.path.join(redesign, "README-for-Claude-Design.md"), "w", encoding="utf-8") as f:
        f.write(README.format(today=date.today()))

    repo = args.repo or os.path.dirname(redesign)
    brand_dir = os.path.join(redesign, "brand")
    brand = collect_app_brand(repo, brand_dir)
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
            z.write(os.path.join(redesign, "assets", name), f"pluristack/{name}")
    size = os.path.getsize(zip_path)
    print(f"Package written: {zip_path} ({size/1024:.0f} KB)")
    if size > 45 * 1024 * 1024:
        print("WARNING: package is large; consider reducing screenshots (fewer viewports) before uploading.")


if __name__ == "__main__":
    main()
