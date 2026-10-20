# Deliverable templates

Use these structures as given. Headings are fixed so that readers (and Step 4) can find sections reliably; the content under them is yours. Replace `<…>` placeholders. All deliverables start with the signature block and end with the signature footer (see SKILL.md › Pluristack signature).

## Contents
- [00-brief.md](#00-briefmd)
- [01-design-inventory.md](#01-design-inventorymd)
- [02-design-review.md](#02-design-reviewmd)
- [03-claude-design-brief.md](#03-claude-design-briefmd)
- [Design-spec export format (what Claude Design must return)](#design-spec-export-format)
- [README-for-Claude-Design.md](#readme-for-claude-designmd)
- [04-implementation-plan.md](#04-implementation-planmd)

---

## 00-brief.md

```markdown
<signature block — Step 0 — Project brief>

# <App name> — Project brief

## Source
- Repository: <URL or path> · branch `<name>` · commit `<sha>` · <date>
- Detected stack: <platform / framework / styling / UI libraries> (confirmed by user: yes/no)

## Product
- What it does: <one paragraph>
- Users and context: <who, where, device mix, frequency of use>
- Platforms in scope: <web desktop / web mobile / iOS / Android / …>

## Why redesign
<the user's own words, lightly edited>

## Brand constraints
- Must keep: <logo, colors, fonts, tone, …>
- Must change: <…>
- Brand assets found in repo: <paths>

## Scope
- Screens / flows in scope: <list or "all">
- Off-limits: <list>
- Dark mode: required / nice-to-have / not needed

## References
- Admired: <product — why (user's reason)>
- Disliked: <product — why>

## How the UI can be observed
- Local run: <command> / not possible because <reason>
- Deployed URL: <url> / none
- Screenshots: provided by user / to be captured

## Open questions
- <anything the user could not answer; revisit at Step 2>

<signature footer>
```

---

## 01-design-inventory.md

```markdown
<signature block — Step 1 — Design inventory>

# <App name> — Design inventory

## 1. Stack summary
<platform, framework, styling approach, UI libraries with versions, dark-mode mechanism, where design lives (folders). Library defaults vs app overrides.>

## 2. Design tokens
### 2.1 Color
| ID | Name in code | Light | Dark | Role | Used (count) | Source |
### 2.2 Typography
| ID | Name | Family | Size | Weight | Line-height | Role | Source |
<plus: font files/loading method; type scale ratio if one exists>
### 2.3 Spacing
<scale as found; distinct values count; grid base if any>
### 2.4 Radius · 2.5 Shadow/elevation · 2.6 Motion · 2.7 Breakpoints · 2.8 Z-index · 2.9 Borders/opacity
<same table shape, only the sections that exist>

## 3. Global styles and resets
<reset/normalize, base element styles, root font size, scroll/selection styles, global dark-mode switch>

## 4. Layout system
| ID | Name | Regions | Responsive behaviour | Used by | Source |

## 5. Component catalogue
Grouped by family (navigation · actions · inputs · data display · feedback · overlays · media · layout primitives · misc). One entry per component:

### `cmp.<family>.<name>` — <Human name>
- **Source**: `<file:line>` (styles: `<file>`)
- **What it does**: <one or two sentences>
- **Appearance props/params**: <list>
- **Variants**: <list>
- **States covered**: <list> · **missing**: <list>
- **Tokens used**: <IDs> · **hard-coded**: <values with file:line>
- **Used in**: <screen/component IDs> (<count>)
- **Responsive**: <behaviour>
- **Accessibility notes**: <role, labels, focus, keyboard>
- **Notes**: <duplicates, quirks, tech debt>

## 6. Screen catalogue
One entry per screen, in navigation order:

### `scr.<name>` — <Title> (`<route>`)
- **Source**: `<file>` · **Layout**: `<lay.id>`
- **Purpose** / **Primary action**
- **Composes**: <component IDs in visual order, top to bottom>
- **States**: <loading/empty/error/… — covered or missing>
- **Capture**: `screens/<file>` (or "not captured")
- **Notes**

## 7. Assets
| ID | Kind | Source | Format | Size | Used in |
<icon set(s) and consistency; images; fonts; illustrations>

## 8. Interaction patterns
| ID | Pattern | Implementation | Used in |
<navigation model, forms & validation, feedback (toast/snackbar/inline), overlays (modal/sheet/drawer/popover), lists (pagination/infinite), transitions>

## 9. Inconsistencies and hazards
| ID | Kind | Summary | Elements | Evidence |
<duplicates, missing states, token drift between light/dark, a11y gaps visible in code, dead styles>

### 9.1 Hard-coded literals
| Value | Closest token | `<file A>` | `<file B>` | … | Total | First occurrences (file:line) |
<one column per file so each count has a clear scope; the command that produced the counts goes under the table>

### 9.2 Design guards and existing documentation
| Path | Kind (test / doc / lint rule) | What it locks or describes | Current? |
<tests that fail if colours, contrast, CSS structure or icons change; design docs and audits in the repo, with a note when they are stale>

## 10. Coverage
- Files scanned / design-relevant / described: <n / n / n>
- Excluded: <path — reason>
- Confidence notes: <anything inferred rather than read>

<signature footer>
```

---

## 02-design-review.md

```markdown
<signature block — Step 2 — Design review>

# <App name> — Design review

## 1. Method and evidence
- Captures: <option used (local run / URL / user screenshots / none)>, <n> screens × <viewports> × <schemes>, in `screens/`
- Not captured: <screens and why>
- Heuristics applied: Nielsen (NN/g), WCAG 2.2 AA, <Apple HIG / Material 3>, craft checks (see references)
- Confidence: findings marked **observed** (seen in a capture) or **inferred** (from code only)

## 2. Executive summary
<five sentences max: the state of the design in one line, then the five highest-impact changes>

## 3. Findings
| ID | Where | Heuristic / SC | Sev | Evidence | Recommendation |
|---|---|---|---|---|---|
| R-001 | `scr.home`, `cmp.button.primary` | WCAG 1.4.3 | 3 | 3.1:1 (`tok.color.brand.500` on `tok.color.surface`), `screens/home--desktop--light.png` | … |
<sorted by severity desc; IDs are referenced from later sections and from Step 3>

## 4. Screen walkthrough
### `scr.<name>` — <Title>
<capture(s) embedded with ![](screens/…) · what works · what doesn't (finding IDs) · narrow-viewport notes · dark-mode notes>

## 5. Design-system recommendations
- **Tokens**: proposed structure (semantic color roles with light/dark, type scale, spacing scale, radius, elevation, motion) — mapped from current tokens where possible
- **Components**: consolidation plan (merge X and Y; add missing states; extract Z)
- **Layout**: grid/containers/breakpoints
- **Dark mode**: parity gaps

## 6. Accessibility report
- Contrast table (all pairs computed; pass/fail per threshold)
- Target sizes, focus visibility, keyboard, labels, reflow, motion — per WCAG SC with finding IDs

## 7. Comparable products
| Product | URL | Pattern worth noting | Relevance to this app |
<2–4 rows; sourced>

## 8. Questions for the user
<decisions needed before Step 3, numbered>

## 9. Decisions
<filled after the user answers: accepted / rejected / modified per finding ID>

<signature footer>
```

---

## 03-claude-design-brief.md

```markdown
<signature block — Step 3 — Claude Design brief>

# <App name> — Redesign brief for Claude Design

> Prepared by RedesignMyApp (Pluristack). Read this document fully before designing. Keep every element ID (`tok.*`, `cmp.*`, `scr.*`) in your output — they are how the design will be mapped back to the code.

## 1. Product context
<from 00-brief: purpose, users, platforms, brand constraints, keep/kill, references with URLs>

## 2. Design goals
<numbered; each goal cites the review finding IDs it addresses; phrased as outcomes ("primary action identifiable within 2 s on every screen"), not solutions>

## 3. Constraints
- Must keep: <…> · Must not: <…>
- Accessibility floor: WCAG 2.2 AA (4.5:1 text, 3:1 UI, 24 px targets, visible focus)
- Platform conventions: <HIG / Material / web>
- Technical: <framework and styling approach — so proposals are implementable; e.g. "Tailwind v4, tokens as CSS custom properties">

## 4. Current design system (reference, not a constraint)
### Tokens
<table from 01 §2, condensed: ID · value light · value dark · role>
### Components
<table: ID · human name · variants · states · used-in count>
### Screens in scope
<table: ID · title · route · primary action · capture file>

## 5. Screen briefs
### `scr.<name>` — <Title>
- Purpose · Primary action · Secondary actions
- Must contain: <content elements, in priority order>
- States to design: <list>
- Current capture: `screens/<file>`
- Known problems: <finding IDs with one-line summaries>

## 6. Deliverables requested
1. **Three directions** (A/B/C) for `scr.<key screen>` at desktop and mobile — each with a one-paragraph rationale and a mood/tone label. Keep one direction close to the current brand; let one be bolder.
2. After the user picks a direction: **full screen set** for every screen in §5 (desktop + mobile; light + dark if in scope), **token sheet**, **component sheet** with all states listed in §4.
3. **Design-spec export** in the exact format in §8, as the final message, so it can be implemented automatically.

## 7. Prompt to paste into Claude Design
```
I am redesigning <App name>. The attached package (RedesignMyApp by Pluristack) contains the brief (03-claude-design-brief.md), the current design tokens (tokens.json), screenshots of the current UI (screens/), and brand assets. Read the brief completely. Propose three directions for the key screen as described in §6, wait for my choice, then produce the full screen set, token sheet and component sheet. Keep all element IDs from the brief. Finish with the design-spec export in the format given in §8 of the brief.
```

## 8. Design-spec export format
<copy the block from "Design-spec export format" below>

<signature footer>
```

---

## Design-spec export format

Claude Design is asked to end with this block. Step 4 parses it; if Claude Design deviates, Step 4 still works from the prose but takes longer.

````markdown
## DESIGN SPEC EXPORT — <App name> — direction <A/B/C> — <date>

### Tokens
```json
{
  "color": {"tok.color.brand.500": {"light": "#…", "dark": "#…", "role": "…"}, "...": {}},
  "typography": {"tok.font.body": {"family": "…", "size": "16px", "weight": 400, "lineHeight": 1.5}, "...": {}},
  "space": {"tok.space.1": "4px", "...": "…"},
  "radius": {}, "shadow": {}, "motion": {}, "breakpoints": {}
}
```
(Tokens that replace an existing one keep its ID; new tokens get new IDs; removed tokens are listed under `"removed": []`.)

### Components
| ID | Status (keep/modify/replace/new/remove) | Appearance spec (tokens, sizes, radius, borders) | States | Notes |

### Screens
| ID | Layout | Component order (top→bottom) | Changes vs current | Mobile notes |

### Patterns
| ID | Change |

### Assets
| ID | Status | New asset description or file |
````

---

## README-for-Claude-Design.md

```markdown
# Package contents — RedesignMyApp by Pluristack

- `03-claude-design-brief.md` — the brief. Start here.
- `tokens.json` — current design tokens (machine-readable).
- `screens/` — screenshots of the current UI, named `<screen>--<viewport>--<scheme>.png`.
- `brand/` — the app's own logo and brand files found in the repository (if any).
- `assets/` — Pluristack signature logos used by the documents' header (not part of the app's brand).
- `inventory-summary.md` — condensed component and screen tables for quick reference.

Element IDs (`tok.*`, `cmp.*`, `scr.*`) must be preserved in all outputs.
www.pluristack.com
```

---

## 04-implementation-plan.md

```markdown
<signature block — Step 4 — Implementation plan>

# <App name> — Implementation plan for Claude Code

## 1. Summary
- Direction implemented: <A/B/C — name> · Source: <Claude Design export file(s)>
- Scope: <n> tokens changed, <n> components modified, <n> new, <n> removed, <n> screens
- Estimated batches: <n> (see §5)

## 2. Conflicts between the design and the code
| ID | Conflict | Evidence (file:line, test, count) | Default resolution | Decision needed from user |
<theme count, removed tokens with consumers, "remove" on features or persisted data, test-enforced policies, screens drawn unlike the code, new values failing WCAG (with computed ratio and the passing replacement)>

## 3. Mapping table
| Design element (Claude Design) | Inventory ID | Status | Code location |
<every element in the export; unmatched ones flagged; inventory elements absent from the design listed with the user's decision>

## 4. Token migration
### 4.1 New token sheet (in the repo's format)
```css
/* or tailwind theme / ThemeData / ColorScheme — ready to paste */
```
### 4.2 Replacement map
| Old (ID / literal) | New (ID / value) | Occurrences | Files |

### 4.3 Checks run on the token sheet
<command(s) and the relevant output lines, e.g. the repo's contrast/CSS guard tests run against the new sheet; or "not run — <reason>". Never state a result without its command and output.>

## 5. Change list (ordered)
Batch 1 — Tokens and globals
### C-001 — <title>
- **Files**: `<path>`
- **Current**: <what it is now, with values>
- **Target**: <exact spec from the design: tokens, sizes, states>
- **Affects**: <screen IDs>
- **Acceptance**: <checkable statements: "renders with `--color-primary`; contrast 4.6:1 on surface; focus ring visible">
- **Notes**: <risks, dependencies>

Batch 2 — Primitives (buttons, inputs, typography components)
Batch 3 — Composite components
Batch 4 — Screens and layouts
Batch 5 — Cleanup (remove dead styles, duplicates, old tokens)

## 6. Risks and rollback
<breaking changes, visual regressions to expect, feature flags or branch strategy>

## 7. Verification
- Screenshot every screen in §3 at <viewports> × <schemes> and compare with the Claude Design screens
- Re-run the contrast table; check target sizes and focus visibility
- <stack-specific: Storybook stories to update, golden tests to re-record, snapshot tests>

## 8. Prompt for Claude Code
```
Implement the UI redesign described in redesign/04-implementation-plan.md. Work through §5 in order, one batch at a time; after each batch run the app, verify the acceptance criteria listed for each change, and commit with the message "redesign: batch N — <title>". Do not skip states (hover, focus-visible, disabled, loading, empty, error). Replace every hard-coded value listed in §4.2 with its token. Respect the decisions in §2 and the repository's own contribution rules (CLAUDE.md, tests). Run the test suite after each batch. Stop and ask if a change conflicts with existing behaviour not covered by the plan.
```

<signature footer>
```
