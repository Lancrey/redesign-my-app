# Review heuristics, severity scale and contrast check

Everything in Step 2 must trace back to a named heuristic or guideline, with evidence (a capture, a file:line, or a computed number). This file is the checklist. Cite the source next to each finding in the review; the URLs below are the canonical references.

## Contents
- [Severity scale](#severity-scale)
- [A. Nielsen's usability heuristics](#a-nielsens-usability-heuristics)
- [B. WCAG 2.2 AA — what to check](#b-wcag-22-aa--what-to-check)
- [C. Platform guidelines](#c-platform-guidelines)
- [D. Craft checks](#d-craft-checks)
- [E. Contrast computation](#e-contrast-computation)
- [F. Comparable-product research](#f-comparable-product-research)

---

## Severity scale

Adapted from Nielsen's severity ratings (https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/). Rate on frequency × impact × persistence.

| Score | Label | Meaning | Typical examples |
|---|---|---|---|
| 1 | Cosmetic | Noticed by few, no task impact | 1 px misalignment, inconsistent icon stroke |
| 2 | Minor | Slows some users, easily recovered | Unclear secondary label, inconsistent spacing between sections |
| 3 | Major | Blocks or misleads many users on a common task | Primary action not distinguishable, contrast below 4.5:1 on body text, form errors not shown |
| 4 | Critical | Task cannot be completed, or legal/accessibility exposure | Keyboard trap, no focus indicator anywhere, essential control below 24 px, unreadable text |

List findings sorted by severity, then by number of screens affected.

---

## A. Nielsen's usability heuristics

Source: Nielsen, J. (1994, updated 2024), "10 Usability Heuristics for User Interface Design", https://www.nngroup.com/articles/ten-usability-heuristics/

| # | Heuristic | What to look for in the captures and code |
|---|---|---|
| 1 | Visibility of system status | Loading indicators, progress, saved/unsaved state, active nav item, selection state |
| 2 | Match between system and real world | Labels in user vocabulary, icons with conventional meaning, natural ordering |
| 3 | User control and freedom | Undo, cancel, back, close on every modal/sheet, escape routes from flows |
| 4 | Consistency and standards | Same action → same control, same term; platform conventions respected; one button style per role |
| 5 | Error prevention | Confirmation for destructive actions, constraints on inputs, sensible defaults |
| 6 | Recognition rather than recall | Options visible, recently used items, labels on icons, breadcrumbs |
| 7 | Flexibility and efficiency | Shortcuts, bulk actions, remembered preferences |
| 8 | Aesthetic and minimalist design | Every element earns its place; no competing emphasis; whitespace |
| 9 | Help users recognise, diagnose, recover from errors | Error messages in plain language, located near the problem, with a fix |
| 10 | Help and documentation | Contextual help, empty states that teach, onboarding where needed |

---

## B. WCAG 2.2 AA — what to check

Source: W3C Web Content Accessibility Guidelines 2.2, Recommendation of 5 October 2023 (updated 12 December 2024), https://www.w3.org/TR/WCAG22/. Native apps are not formally covered by WCAG but Apple and Google both point to the same criteria; apply them.

| SC | Level | Requirement | How to check |
|---|---|---|---|
| 1.4.1 Use of Color | A | Color is not the only means of conveying information | Error states, links, chart series, required fields |
| 1.4.3 Contrast (Minimum) | AA | Text ≥ 4.5:1; large text (≥ 24 px, or ≥ 18.66 px bold) ≥ 3:1 | Compute for every text/background token pair (section E) |
| 1.4.4 Resize Text | AA | Readable at 200 % zoom without loss | Fixed heights, `px` font sizes on root, overflow hidden on text |
| 1.4.10 Reflow | AA | No 2-D scrolling at 320 CSS px width | Mobile captures; tables, fixed widths |
| 1.4.11 Non-text Contrast | AA | UI component boundaries and states, icons ≥ 3:1 | Input borders, focus rings, icon-only buttons, toggles |
| 1.4.12 Text Spacing | AA | Survives line-height 1.5, paragraph 2×, letter 0.12 em, word 0.16 em | Clipped containers, `overflow:hidden` on text |
| 1.4.13 Content on Hover/Focus | AA | Tooltips dismissible, hoverable, persistent | Tooltip/popover implementation |
| 2.1.1 Keyboard | A | All functionality operable by keyboard | Custom controls (`div` with `onClick`), drag-only interactions |
| 2.1.2 No Keyboard Trap | A | Focus can always leave | Modals, embedded widgets |
| 2.4.3 Focus Order | A | Focus order matches reading order | DOM order vs visual order (CSS `order`, `flex-direction: row-reverse`) |
| 2.4.6 Headings and Labels | AA | Descriptive headings/labels | Heading hierarchy, placeholder-only inputs |
| 2.4.7 Focus Visible | AA | Visible focus indicator | `outline: none` without replacement; focus ring contrast |
| 2.4.11 Focus Not Obscured (Minimum) | AA (new in 2.2) | Focused element not entirely hidden by sticky headers/footers | Sticky bars + scroll-into-view |
| 2.5.3 Label in Name | A | Visible label text is in the accessible name | Icon buttons with mismatched `aria-label` |
| 2.5.7 Dragging Movements | AA (new in 2.2) | Drag actions have a single-pointer alternative | Sliders, reorderable lists, swipe-to-delete |
| 2.5.8 Target Size (Minimum) | AA (new in 2.2) | Targets ≥ 24 × 24 CSS px, or spaced so a 24 px circle fits | Icon buttons, pagination, close buttons, table row actions |
| 3.2.3 Consistent Navigation | AA | Navigation repeated in the same order | Nav components across screens |
| 3.2.4 Consistent Identification | AA | Same function → same label/icon | Edit/delete/share icons across screens |
| 3.2.6 Consistent Help | A (new in 2.2) | Help mechanisms in the same place | Help links, chat widgets |
| 3.3.1 Error Identification | A | Errors identified in text | Form validation |
| 3.3.2 Labels or Instructions | A | Inputs have labels/instructions | Placeholder-as-label pattern |
| 3.3.7 Redundant Entry | A (new in 2.2) | Don't ask again for info already given in the same process | Multi-step forms |
| 3.3.8 Accessible Authentication (Minimum) | AA (new in 2.2) | No cognitive-function test without alternative | CAPTCHAs, memorised-secret-only logins |
| 2.3.3 Animation from Interactions | AAA (recommended) | Motion can be disabled | `prefers-reduced-motion` handling |

Report WCAG findings in their own section with SC numbers; developers and auditors look for them that way.

---

## C. Platform guidelines

- **Apple Human Interface Guidelines** — https://developer.apple.com/design/human-interface-guidelines/. Check: minimum hit target 44 × 44 pt (Layout → "Give controls a hit target of at least 44x44 pt"); Dynamic Type support (text styles rather than fixed sizes); system colors and materials for dark mode; navigation patterns (tab bar ≤ 5 items, navigation bar titles); SF Symbols weight matching text; safe-area respect.
- **Material Design 3** — https://m3.material.io/. Check: touch targets 48 × 48 dp; 8 dp spacing grid (4 dp for small adjustments); color roles (`primary`, `on-primary`, `surface`, `surface-container-*`) rather than raw palette; type scale roles (`display`, `headline`, `title`, `body`, `label`); dark theme uses tonal surfaces, not pure black; elevation via tonal color + shadow; state layers (hover 8 %, focus 10 %, pressed 10 %).
- **Web**: both of the above inform expectations; additionally the WCAG target-size minimum (24 px) is the legal floor, 44 px the comfortable norm for touch.
- **Windows Fluent** (if a Windows desktop app is in scope) — https://learn.microsoft.com/windows/apps/design/.

Record which guideline the app claims to follow (from the interview or from the component library) and judge consistency against that one; do not penalise an iOS app for not looking Material.

---

## D. Craft checks

These are not standards; they are the practices a good design reviewer applies. Cite them as "craft" with a short rationale in the finding; where a source exists, it is given.

**Typography**
- A defined type scale (5–8 sizes) with a consistent ratio; body text ≥ 16 px on web (browser default; smaller sizes reduce legibility and trigger iOS Safari input zoom below 16 px).
- Line-height 1.4–1.6 for body, tighter (1.1–1.25) for headings; line length 45–75 characters for reading text (Bringhurst, *The Elements of Typographic Style*, §2.1.2).
- At most two typefaces; weights used purposefully (≤ 4).
- Hierarchy visible from a squint test: title → section → body → caption distinguishable by size *and* weight or color.

**Spacing and layout**
- One spacing scale (commonly 4/8-based) used everywhere; count distinct padding/margin values in the literal list — more than ~12 is a smell.
- Consistent container widths and gutters; alignment to a grid; related items closer than unrelated (Gestalt proximity).
- Responsive: content reflows rather than shrinks; no horizontal scroll at 320–390 px; tables become cards or scroll within their own container.

**Color**
- Semantic roles (brand, accent, neutral scale, success/warning/danger/info, surfaces, borders, text levels) rather than a flat palette; each role has a dark-mode counterpart.
- Rule of thumb for emphasis distribution: roughly 60 % neutral surfaces, 30 % secondary, 10 % accent (interior-design heuristic widely used in UI; not a standard).
- Accent used for the primary action and little else per screen.
- Dark mode: surfaces are dark greys, not `#000`; saturated colors are lightened/desaturated; shadows replaced by surface tone (Material 3 dark theme guidance).

**Components and states**
- Every interactive component covers: default, hover (pointer devices), focus-visible, active/pressed, disabled, loading, and selected/checked where relevant.
- Every data view covers: loading (skeleton or spinner), empty (with guidance and an action), error (with retry), partial/degraded.
- One implementation per role (one button, one input, one card); variants via props, not copies.
- Icons from one set, one stroke weight, one optical size; labels on icon-only controls.

**Feedback and motion**
- Transitions 100–300 ms for small elements, up to ~500 ms for large surfaces (Material 3 motion guidance: https://m3.material.io/styles/motion/overview); easing curves consistent; `prefers-reduced-motion` respected.
- Immediate feedback on every action (optimistic UI or indicator within 100 ms; progress for > 1 s).

**Content**
- Buttons are verbs ("Save changes", not "OK"); destructive actions named ("Delete project"); error messages say what happened and what to do.
- Empty states and onboarding teach the product's core value.

---

## E. Contrast computation

Do not estimate contrast by eye. Compute it for every text color / background pair in the token set, light and dark, and for icon/border colors against their surfaces (3:1 rule). Formula from WCAG 2.2 (https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio and #dfn-relative-luminance):

```python
def _lin(c):                      # sRGB channel 0–255 → linear
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3: h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def contrast(fg, bg):
    l1, l2 = sorted((luminance(fg), luminance(bg)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)

# thresholds: 4.5 normal text, 3.0 large text and UI components/icons, 7.0 AAA normal text
```

Colors with alpha must be composited onto their actual background first (`result = alpha*fg + (1-alpha)*bg` per channel). For `oklch()`/`hsl()` values convert to sRGB first (Python: `colorsys` for HSL; for OKLCH use the conversion in https://www.w3.org/TR/css-color-4/#color-conversion-code). Report the pair, the ratio, the threshold that applies and pass/fail.

APCA (the candidate algorithm for WCAG 3) is not yet normative; mention it only if the user asks.

---

## F. Comparable-product research

Purpose: ground recommendations in patterns the app's users already know, and avoid reinventing solved problems. Not purpose: copying.

1. Start from the products the user named in the interview; add 1–3 found by web search (`"<category> app" design`, `best <category> apps 2026`, and the product's own marketing/docs/design-system pages — many publish them: GitHub Primer, Shopify Polaris, Atlassian, GOV.UK, Stripe docs).
2. For each, note with a URL: navigation model, information density, how they handle the specific problems found in the review (onboarding, empty states, data tables, settings organisation, mobile adaptation).
3. Prefer published design systems and documentation over screenshots of marketing pages; prefer sources dated within the last two years.
4. In the review, phrase as "X solves this with …" and derive a recommendation adapted to this app's audience; never "make it look like X".
