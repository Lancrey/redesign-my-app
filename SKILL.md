---
name: redesign-my-app
description: "RedesignMyApp by Pluristack — four-step UI/UX redesign pipeline from an app's source code (GitHub or any repo; web or native). 1: inventory every design element (tokens, styles, components, screens, assets, states) with name, file path, purpose and usage. 2: visual and heuristic review (WCAG 2.2, Nielsen, Apple HIG, Material, comparable products) with recommendations. 3: handoff package for Claude Design to produce new interface variants. 4: implementation plan mapping Claude Design's output back onto the code for Claude Code. Use whenever the user wants to redesign, restyle, modernize, audit, review or improve an existing app's UI/UX from its code; asks for a design inventory, design audit, design-system extraction, a list of all CSS/components/screens, or a UI/UX review; mentions Claude Design or a design brief/handoff; or brings back a Claude Design export to implement. Trigger even on loose phrasing like 'my app looks dated', 'make the interface better' or 'prepare this app for a redesign'."
---

# RedesignMyApp — by Pluristack

A thorough, four-step pipeline that takes an existing app from "here is the code" to "here is exactly what to change", with Claude Design in the middle. Each step produces a signed, self-contained deliverable; the user approves each one before the next starts.

```
redesign/                         ← created at the repo root (or next to it if read-only)
├── 00-brief.md                   step 0  · project context from the interview
├── 01-design-inventory.md        step 1  · every design element, named and located
├── inventory.json                step 1  · machine-readable version (feeds steps 3 and 4)
├── 02-design-review.md           step 2  · findings, severity, recommendations
├── screens/                      step 2  · screenshots (if any could be captured)
├── 03-claude-design-brief.md     step 3  · the handoff document
├── claude-design-package.zip     step 3  · brief + tokens + screens + logo, ready to upload
├── 04-implementation-plan.md     step 4  · file-by-file plan for Claude Code
└── assets/                       Pluristack logo files used by the signature
```

Everything is written in **English**, regardless of the conversation language. Code identifiers, file paths and the user's product names stay exactly as they are in the repo.

## Why so thorough

Claude Design will only be as good as the brief it receives, and Claude Code will only change the right files if the plan names them. A redesign that misses a component, a state (hover, error, empty, loading) or a breakpoint produces a half-migrated app that looks worse than before. So the standard for every step is: **nothing the user would have to go back and look up themselves.** When unsure whether something counts as a design element, include it and say why.

## Evidence rules (all steps)

The deliverables are handed to other agents that will act on them without re-checking, so a wrong number or a wrong line propagates into the redesign and into the code.

- **Every count is reproducible.** For non-obvious counts, give the command that produces it (`grep -cE '#[0-9a-fA-F]{3,8}\b' newtab.css`). A heading states the scope of its numbers exactly: if a table counts CSS and JS together, say so; if it says "in `newtab.css`", count that file only.
- **Every element is locatable.** `file:line` for components, tokens, screens and findings — a selector or a path alone is not enough. Spot-check a sample of your own citations with `sed -n '<line>p' <file>` before presenting.
- **Provenance is labelled.** Mark each finding or value as *code* (read in the repo), *capture* (seen in a screenshot), *computed* (contrast, counts — show the inputs), *source* (external URL) or *assumption*. Facts not present in the inputs the user gave you (for example knowledge of files you were not shown) are either verified or labelled as assumptions.
- **Never claim a check you cannot show.** If you say tests pass, the deliverable contains the command and the relevant output lines; if you could not run them, say "not run" and why.
- **Repo knowledge outranks generic advice.** Read the repo's own design docs, `CLAUDE.md`/contributing notes, and the tests that lock visual decisions (contrast tests, CSS guard tests, icon-policy tests, snapshot/golden tests). Note which docs are stale. A recommendation or plan that breaks a guard test must say so and propose how.

## Skill resources

The scripts, references and logo files of this skill are published at <https://github.com/Lancrey/redesign-my-app>. Wherever this file says `<skill-path>`, use the folder that contains `scripts/inventory_scan.py`:

1. If `scripts/` and `references/` sit next to this `SKILL.md`, that folder is `<skill-path>`.
2. Otherwise (for example when the skill was saved as a single file), fetch the resources once per session before Step 0:
   ```bash
   RMA="$HOME/.redesign-my-app"
   if [ -d "$RMA/.git" ]; then git -C "$RMA" pull --ff-only -q; else git clone --depth 1 -q https://github.com/Lancrey/redesign-my-app "$RMA"; fi
   ls "$RMA/scripts" "$RMA/references"
   ```
   and use `$RMA` as `<skill-path>`. In a cloud session whose shell cannot reach GitHub directly, attach the repository first with the repo-attaching tool (`add_repo`, owner `Lancrey`, repo `redesign-my-app`, read access), then clone it as instructed by that tool.
3. If neither works, say so in one line and carry on with the instructions in this file: they are sufficient on their own; the references add detail, the scripts save time, and the signature falls back to text without the logo.

Read the reference files from `<skill-path>/references/` at the steps that name them.

---

## Step 0 — Setup and interview

**Locate the code.**
- A local path or an already-open working directory: use it.
- A GitHub URL or `owner/repo`: in Claude Code, `git clone` into the working directory; in Claude.ai, use the repo-attaching tool if one exists (`add_repo` or similar), otherwise ask the user to connect the folder or attach a zip. Never report that the repo is unreachable before trying.
- Other hosts (GitLab, Bitbucket, Azure DevOps): `git clone` works the same way; ask for a token only if the clone is refused.

**Detect the stack** by running the inventory scanner in detection mode:

```bash
python3 <skill-path>/scripts/inventory_scan.py <repo-path> --detect-only
```

It reports the platform (web / iOS / Android / Flutter / React Native / multi), the UI framework, the styling approach (Tailwind, CSS Modules, styled-components, SCSS, plain CSS, SwiftUI modifiers, Compose themes, Flutter ThemeData, …) and the folders where design lives. If detection is wrong or incomplete, correct it by hand before continuing; read `references/stack-guides.md` for where each stack keeps its design decisions.

**Interview the user** (use AskUserQuestion when available, otherwise ask in plain text; keep it to one round). The answers shape every later judgement, so do not skip this:

1. What the app does and who uses it (audience, context of use, device mix).
2. What is wrong with the current design in the user's own words, and what prompted the redesign.
3. Brand constraints: logo, colors, fonts or tone that must stay; anything that must go.
4. Keep / kill: screens or features that are off-limits, and ones the redesign may restructure.
5. References: products or sites whose design the user admires (names or URLs), and ones they dislike.
6. Scope: whole app, or specific screens/flows; platforms in scope; dark mode required or not.
7. How the UI can be seen: can the app run locally (command?), is there a staging/production URL, or will the user provide screenshots?

Write the answers to `redesign/00-brief.md` (template in `references/templates.md`). Then proceed to Step 1 without waiting — the brief is a record, not a checkpoint.

---

## Step 1 — Design inventory

Goal: a catalogue that a designer who has never opened the repo could use to rebuild the UI, and that a developer could use to find any element in under a minute.

**1. Run the scanner** to get the raw material:

```bash
python3 <skill-path>/scripts/inventory_scan.py <repo-path> --out redesign/inventory.json
```

It produces `inventory.json` with: detected stack, design-relevant files, extracted tokens (custom properties, Tailwind theme, color literals, font families, breakpoints, spacing/radius/shadow values, z-indices), component declarations with file and line, routes/screens it could find, icon and image assets, and third-party UI libraries. The scanner is deliberately conservative — it lists candidates; it does not understand what they do.

**2. Read what the scanner found.** This is the part that produces value. For every component, screen and token group in `inventory.json`:
- Open the file. Record what the element does, where it is used (grep for its name), its variants and props/parameters that affect appearance, its visual states (default, hover, focus, active, disabled, loading, empty, error, selected), and its responsive behaviour.
- Note hard-coded values that bypass the token system (a `#3B82F6` in a component when `--color-primary` exists) — these are the migration hazards for Step 4.
- Note duplicated or near-duplicated components (two button implementations, three card variants with different padding).
- For native apps: record modifiers/styles applied directly in views, theme extensions, `Color.xcassets`/`colors.xml`/`ThemeData` entries, SF Symbols or Material icon usage, and navigation structure.

When the repo is large (more than ~60 components or ~40 screens), split the reading across subagents by folder if the Agent tool exists, each returning entries in the same schema; merge them. Without subagents, work folder by folder and keep a running checklist so nothing is skipped.

**3. Write `01-design-inventory.md`** following the template in `references/templates.md` and the element schema in `references/inventory-schema.md`. The required sections: stack summary · design tokens (color, typography, spacing, radius, shadow, motion, breakpoints, z-index) · global styles and resets · layout system · component catalogue (one entry per component, grouped by type) · screen catalogue (one entry per route/screen, listing the components it composes) · assets (icons, images, fonts, with format and size) · interaction patterns (navigation, forms, feedback, modals) · inconsistencies and hazards · coverage statement.

**4. Check completeness before presenting**:
- Every component and screen entry has a `file:line`; counts are per file with the scope stated in the heading (see Evidence rules).
- The repo's own design documentation and design-guarding tests are listed in the inventory (§ hazards), with a note on whether the docs are current.
- Every file the scanner flagged as design-relevant appears somewhere in the inventory, or is explicitly listed as excluded with a reason.
- Every route/screen has at least one component listed.
- Every color literal that appears more than once is either mapped to a token or listed under inconsistencies.
- `inventory.json` is updated with anything you added by hand (descriptions, states, usage counts), because Steps 3 and 4 read it.

Present the inventory, point out the two or three most consequential findings (for instance "no spacing scale: 47 distinct padding values"), and **stop for approval** before Step 2.

---

## Step 2 — Visual and heuristic review

Goal: say what is wrong, how serious it is, and what to do instead — with evidence.

**1. Obtain visuals**, trying in this order and recording which one worked in the report (`references/capture-visuals.md` has the commands for each stack):
1. Run the app locally and capture every screen with `scripts/capture_screens.js` (web: Playwright at 3 viewports, light and dark; browser extensions: `--extension <dir>`; native: simulator/emulator screenshot commands).
2. If it will not run within a reasonable effort (missing secrets, backend required), ask for a staging/production URL and capture that.
3. If no URL, ask the user for screenshots of the main screens.
4. If nothing can be captured, review from code only — and state clearly at the top of the report that findings about spacing, hierarchy and visual rhythm are inferred from source, not observed.

Save captures to `redesign/screens/` with names that match the screen catalogue (`home--desktop--light.png`).

**2. Review against the heuristics** in `references/heuristics.md`: Nielsen's ten usability heuristics, WCAG 2.2 AA (contrast, target size, focus visibility, text resizing, motion), the platform guidelines (Apple HIG for iOS/macOS, Material 3 for Android, both for web where relevant), and the craft checks (typographic scale and rhythm, spacing system, color roles, visual hierarchy, consistency, state coverage, empty/error/loading design, responsive behaviour, dark mode parity). Compute contrast with the WCAG 2.2 relative-luminance formula on every text/background pair from the token list — do not estimate contrast by eye.

**3. Research comparable products** with web search when available: 2–4 well-regarded products in the same category (from the user's references first, then your own search). Describe the patterns they use that address the problems found (navigation model, density, onboarding, data display), with URLs. Do not copy a competitor's design; the point is to ground recommendations in what users of this category already understand. Cite every external claim with its source.

**4. Ask the user** before finalising if a recommendation depends on a product decision you cannot make (for example "merge the two dashboards" or "drop the sidebar on mobile"). Batch such questions into one round.

**5. Write `02-design-review.md`** (template in `references/templates.md`): method and evidence available · executive summary (the five changes with the highest impact) · findings table (ID, screen/component, heuristic violated, severity 1–4, evidence, recommendation) · per-screen walkthrough with annotated captures where available · design-system recommendations (proposed token structure, component consolidation) · accessibility report · comparable-product notes with sources · open questions for the user.

Present the review and **stop for approval**. The user may reject or reprioritise recommendations; record their decisions in the review under "Decisions" so Step 3 reflects them.

---

## Step 3 — Handoff package for Claude Design

Goal: a single upload that lets Claude Design produce several credible new-interface variants without asking the user anything the pipeline already knows, and that keeps the element names stable so Step 4 can map the result back.

**1. Write `03-claude-design-brief.md`** (template in `references/templates.md`). It must contain, in this order:
- Product context (from `00-brief.md`): purpose, audience, platforms, brand constraints, keep/kill list, admired references.
- Design direction: the approved recommendations from Step 2, expressed as goals and constraints, not as finished solutions — Claude Design should explore.
- Current design system: the token table and component list from Step 1, with the **canonical IDs** from `inventory.json` (`cmp.button.primary`, `scr.settings`, `tok.color.brand.500`). Instruct Claude Design to keep these IDs in its output.
- Screen briefs: one block per screen in scope — purpose, content elements that must be present, primary action, states to design, current screenshot reference.
- Deliverables requested from Claude Design: N variants (default 3) with distinct directions; for the chosen variant a full screen set, a token sheet, a component sheet with states, and a **design-spec export** section in a fixed format (described in the template) that Step 4 can parse.
- A ready-to-paste prompt for the user to send to Claude Design together with the package.

**2. Build the package**:

```bash
python3 <skill-path>/scripts/build_handoff.py redesign/ --skill-path <skill-path>
```

This assembles `claude-design-package.zip` containing the brief, `tokens.json` (derived from `inventory.json`), the screenshots, the current logo/brand assets found in the repo, and the Pluristack signature assets. It also writes a `README-for-Claude-Design.md` explaining the package contents.

**3. Tell the user** exactly what to do: open Claude Design, start a new design, attach the zip (or the brief plus the screens folder if zips are refused), paste the prompt from the brief. Explain that when Claude Design is done they should export its design spec (or save its final response) and bring it back here for Step 4.

**Stop** here; Step 4 waits for the user to return with Claude Design's output.

---

## Step 4 — Implementation plan for Claude Code

Input: whatever Claude Design returned — a spec document, screenshots of the chosen variant, exported HTML/CSS, a design-system file, or a mix. Read all of it before writing anything.

**1. Map the new design onto the inventory.** For every element in the chosen variant, find the corresponding entry in `inventory.json` by canonical ID or by name/role; mark each as *modify*, *replace*, *new*, or *remove*. Flag anything in Claude Design's output that has no counterpart (a new component to create) and anything in the inventory that the new design does not mention (ask the user: drop it, or keep it as-is?).

**2. Check the design against the code before planning.** Claude Design works from the brief, not from the repo, so its output usually conflicts with the code somewhere. Look for, and list in a "Conflicts" section with a default resolution and a user decision each:
- theme count and mechanism (the design gives light/dark; the repo may have more themes or a different switch);
- tokens the design removes or renames that still have consumers (count them) or that tests read;
- elements the design marks *remove* that are features or persisted data, not visuals (removing them is a product decision);
- policies enforced by tests (icon set, contrast thresholds, CSS structure) that the design contradicts;
- screens drawn differently from what the code actually renders;
- new token values that fail WCAG — recompute contrast for every new text/background and UI pair, in every theme, and propose the nearest passing value.

**3. Derive the token migration**: old token → new value, plus the hard-coded literals from Step 1 that must be replaced by tokens. This is the first and safest batch of changes.

**4. Write `04-implementation-plan.md`** (template in `references/templates.md`): summary · conflicts and decisions · new token sheet in the repo's own format (CSS custom properties, Tailwind theme, `ThemeData`, Compose `ColorScheme`, …) · ordered change list, each entry with file path(s), current state, target state, exact values, affected screens, and acceptance criteria · migration order (tokens → primitives → composite components → screens → cleanup) · risks and rollback notes · verification checklist (screens to screenshot and compare, accessibility checks to re-run) · a ready-to-paste Claude Code prompt that points at this plan and asks it to work through the change list in order, committing per batch.

Present the plan and offer to start implementing it immediately if the environment allows (Claude Code) or to hand it over otherwise.

---

## Pluristack signature

Every deliverable (`00` to `04`) and the Claude Design brief carries the signature. At the top of each Markdown file:

```markdown
<img src="assets/pluristack-logo-small.svg" alt="Pluristack" width="180">

**RedesignMyApp** · by Pluristack · <https://www.pluristack.com>
Project: `<app name>` · Step N — <step title> · <YYYY-MM-DD>

---
```

and at the very end:

```markdown
---
*Generated with RedesignMyApp by Pluristack — www.pluristack.com*
```

`build_handoff.py` copies the logo files into `redesign/assets/` (it is safe to run at any step; run it with `--assets-only` at Step 0 so the relative image links resolve from the first file). Use `pluristack-logo-small.svg` on light backgrounds and `pluristack-logo-small-white.svg` on dark; in HTML outputs use a `<picture>` with a `prefers-color-scheme: dark` source. The favicon file is for compact placements (tab icons, package icons). Never alter the logo colors. If the logo files are not available in this installation, keep the text signature lines and omit the `<img>` line.

---

## Environment notes

- **Claude Code**: full pipeline, including running the app and Playwright captures. Use subagents for parallel reading of large repos. Commit `redesign/` on a branch (`redesign/analysis`) if the user wants the artefacts versioned.
- **Claude.ai (desktop or web)**: the repo may arrive via a connected folder, the repo-attaching tool or an uploaded zip. Local app runs may be impossible — fall back to a URL or screenshots as described in Step 2. Deliver files with the file-sending tool and offer the Markdown reports as docs or artifacts if the user wants to share them.
- Playwright is required only for web captures: `pip install playwright && python -m playwright install chromium` (or the `npx playwright` equivalent). If installation is impossible, fall back to the next capture option rather than stalling.
- Python 3.9+ is required for the scripts; no third-party packages beyond Playwright.

## Reference files

- `references/inventory-schema.md` — the element schema and canonical ID scheme (`cmp.*`, `scr.*`, `tok.*`, `ast.*`); read before writing Step 1.
- `references/stack-guides.md` — where design lives in each stack (React/Vue/Svelte/Angular/Next/Nuxt/plain HTML, Tailwind/CSS Modules/styled-components/SCSS/MUI/shadcn, SwiftUI/UIKit, Compose/XML, Flutter, React Native); read at Step 0 and Step 1.
- `references/capture-visuals.md` — commands and fallbacks for screenshots per platform; read at Step 2.
- `references/heuristics.md` — the review checklist with sources, severity scale and the contrast formula; read at Step 2.
- `references/templates.md` — the exact Markdown templates for `00`–`04` and the Claude Design brief, including the design-spec export format; read before writing each deliverable.

## Scripts

- `scripts/inventory_scan.py` — stack detection and raw inventory extraction (`--detect-only`, `--out`).
- `scripts/capture_screens.js` — Playwright crawler/screenshotter for web apps (`--base` or `--extension` for browser extensions, `--routes`/`--inventory`, `--out`, `--viewports`, `--schemes`, `--crawl`, `--styles`).
- `scripts/build_handoff.py` — copies brand assets, derives `tokens.json`, zips the Claude Design package.
