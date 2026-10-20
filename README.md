<img src="assets/brand/pluristack-logo-small-white.svg" alt="Pluristack" width="180">

# RedesignMyApp — by Pluristack

A Claude skill that takes an existing app from its source code to a redesigned interface, in four steps:

| Step | Output | What it contains |
|---|---|---|
| 0 | `00-brief.md` | Project context from a short interview |
| 1 | `01-design-inventory.md`, `inventory.json` | Every design element — tokens, styles, components, screens, assets, patterns — with names, `file:line` locations, usage and states |
| 2 | `02-design-review.md`, `screens/` | Visual and heuristic review (Nielsen, WCAG 2.2 AA, Apple HIG, Material 3, comparable products) with severity-rated findings and recommendations |
| 3 | `03-claude-design-brief.md`, `claude-design-package.zip` | Handoff package for Claude Design to produce several new interface directions |
| 4 | `04-implementation-plan.md` | Claude Design's output mapped back onto the code: conflicts, token sheet in the repo's format, ordered change list with acceptance criteria, and a ready-to-paste Claude Code prompt |

Works on web apps (React, Next, Vue, Svelte, Angular, plain HTML, browser extensions; Tailwind, CSS Modules, CSS-in-JS, SCSS…) and native apps (SwiftUI/UIKit, Jetpack Compose/XML, Flutter, React Native).

## Contents

```
SKILL.md                     the skill
references/
  inventory-schema.md        element schema and canonical IDs (tok.*, cmp.*, scr.*, …)
  stack-guides.md            where design lives in each stack
  capture-visuals.md         how to screenshot each kind of app
  heuristics.md              review checklist, severity scale, contrast formula, sources
  templates.md               templates for every deliverable and the Claude Design export format
scripts/
  inventory_scan.py          stack detection and raw design inventory (Python 3.9+, stdlib only)
  capture_screens.js         Playwright screenshots of web apps and browser extensions
  build_handoff.py           tokens.json + Claude Design package
assets/brand/                Pluristack signature logos
```

## Install

Save `SKILL.md` as a skill in Claude. When the scripts and references are not installed next to it, the skill fetches them from this repository at the start of a run.

Playwright (`npm i -D playwright && npx playwright install chromium`) is needed only for web screenshots.

---
© Pluristack — <https://www.pluristack.com>
