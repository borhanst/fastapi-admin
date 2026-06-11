# FastAPI Admin — UI Design System

> The visual language for every surface in the admin panel. All color, type,
> spacing, component, and motion decisions live here. Implement nothing that
> contradicts this document.

---

## Design Brief

**Product:** A developer-facing admin panel embedded inside existing FastAPI applications.

**Audience:** Developers and internal business operators — people who live in terminals,
IDEs, and dashboards. They value precision, information density, and speed over
decoration. They notice when spacing is inconsistent. They do not want to be impressed
by the UI — they want to get work done and leave.

**The page's single job:** Let the operator find, read, create, edit, and delete records
with minimum friction. Every surface is a working surface, not a homepage.

**Aesthetic direction:** Dense data-forward UI. Think code editor meets financial
terminal. Clean without being sterile. Dark-first but light mode equally first-class.
The signature element is the use of a **monospaced accent** — all record IDs, counts,
status codes, timestamps, and numeric values are always set in a mono face. This
creates a clear visual grammar: prose is readable, data is scannable. It is the one
element that should be immediately recognisable as this admin's own.

**What to avoid:** Generic SaaS purple. Rounded-everything "friendly" admin panels
(Retool, Forest Admin). Pastel cards. Excessive whitespace that wastes vertical space
on dense tables.

---

## 1. Color Tokens

### Palette

Four named roles. Two neutrals, one primary, one semantic set.

```
--surface-base       #0F1117   Dark bg — page background
--surface-raised     #181B23   Slightly lifted — sidebar, cards, modals
--surface-overlay    #1E2230   Highest layer — dropdowns, tooltips, popovers
--surface-border     #2A2F3F   All borders and dividers

--text-primary       #E8EAF0   Main text on dark bg
--text-secondary     #8B90A0   Labels, metadata, help text
--text-disabled      #454A5A   Placeholder, inactive
--text-inverse       #0F1117   Text on light (primary-filled) surfaces

--primary-500        #5865F2   Indigo — primary actions, active states, links
--primary-400        #7B86F5   Hover state for primary
--primary-600        #4350D4   Active / pressed state
--primary-100        #1A1F3D   Tinted background for selected rows, active nav

--success-500        #22C55E
--success-100        #0D2818
--warning-500        #F59E0B
--warning-100        #2A1F0A
--danger-500         #EF4444
--danger-100         #2A1010
--info-500           #3B82F6
--info-100           #0D1A2F

--mono-accent        #A6E3A1   Catppuccin green — used ONLY for mono-face data values
```

### Light Mode Overrides

```
--surface-base       #F8F9FC
--surface-raised     #FFFFFF
--surface-overlay    #FFFFFF
--surface-border     #E2E5EE

--text-primary       #111827
--text-secondary     #6B7280
--text-disabled      #9CA3AF
--text-inverse       #FFFFFF

--primary-100        #EEF0FE
--success-100        #F0FDF4
--warning-100        #FFFBEB
--danger-100         #FEF2F2
--info-100           #EFF6FF

--mono-accent        #166534   Green that reads on light bg
```

Apply light mode via `[data-theme="light"]` on `<html>`. Dark is the default — no
attribute needed.

### Usage Rules

- `--surface-raised` for the sidebar, topbar, and all card-like containers.
- `--surface-overlay` for anything that floats above content: dropdowns, menus,
  modals, tooltips.
- Never put two different surfaces adjacent with no `--surface-border` between them.
- `--primary-100` as the background of the active sidebar nav item, selected table
  row, and focused tab. Not as a fill for any block larger than a row.
- Semantic colors (success/warning/danger/info) only for status badges, toast borders,
  and inline validation messages. Not for decorative blocks or headings.

---

## 2. Typography

### Typefaces

**Display / UI:** `Inter` — the workhorse. Every label, heading, button, body copy.
Set at 400 and 500 weight only in most contexts. 600 for headings and emphasis.
Never 700+ in the admin — bold is for terminal logs, not admin panels.

**Monospaced:** `JetBrains Mono` — for every numeric value, ID, timestamp, status
code, JSON, code, slug, and filter value. This is the signature element. It must
appear on nearly every screen. Weight 400 only.

Load both from Google Fonts or self-host. Do not use system fonts for either role —
consistency across OS is non-negotiable in a tool product.

### Type Scale

```
--text-xs     11px / 1.5  / Inter 400      — table metadata, timestamps, sub-labels
--text-sm     13px / 1.5  / Inter 400      — table cell content, form help text
--text-base   14px / 1.6  / Inter 400      — body, default UI text
--text-md     15px / 1.5  / Inter 500      — section headings, form labels
--text-lg     18px / 1.4  / Inter 600      — page titles
--text-xl     22px / 1.3  / Inter 600      — dashboard stat numbers

--text-mono   12px / 1.5  / JetBrains Mono 400   — all data values
--text-mono-sm 11px / 1.5 / JetBrains Mono 400   — compact table cells
```

### Application Rules

- Page titles (`<h1>`): `--text-lg`, Inter 600, `--text-primary`.
- Section dividers / fieldset titles: `--text-xs`, Inter 500, `--text-secondary`,
  uppercase, letter-spacing 0.06em. Example: `GENERAL INFORMATION`.
- Table column headers: `--text-xs`, Inter 500, `--text-secondary`, uppercase,
  letter-spacing 0.04em.
- Table cell content: `--text-sm`, Inter 400.
- All IDs, PKs, counts, prices, dates, times, percentages, codes: `--text-mono`,
  `--mono-accent` color.
- Form labels: `--text-sm`, Inter 500, `--text-primary`.
- Help text: `--text-sm`, Inter 400, `--text-secondary`.
- Buttons: `--text-sm`, Inter 500. Never uppercase in buttons.
- Nav labels: `--text-sm`, Inter 400 (inactive), Inter 500 (active).
- Toast messages: `--text-sm`, Inter 400.

---

## 3. Spacing System

Base unit: `4px`. All spacing is a multiple of 4.

```
--space-1    4px
--space-2    8px
--space-3    12px
--space-4    16px
--space-5    20px
--space-6    24px
--space-8    32px
--space-10   40px
--space-12   48px
--space-16   64px
```

### Layout Dimensions

```
--sidebar-width         240px
--sidebar-collapsed     56px      (icon-only, < 1024px)
--topbar-height         52px      (compact — not 64px; data tools are dense)
--content-padding       24px      (left/right padding on content area)
--content-max-width     1320px
--form-max-width        860px     (forms should never stretch full width)
```

### Density Rules

Admin panels are high-density tools. Do not apply generous whitespace in the name of
"breathing room." Use this table for vertical rhythm in components:

| Component | Vertical padding |
|---|---|
| Table row | 10px top / 10px bottom |
| Form field wrapper | 16px bottom (between fields) |
| Button | 7px top / 7px bottom |
| Input | 7px top / 7px bottom |
| Sidebar nav item | 8px top / 8px bottom |
| Card / section | 20px all sides |
| Modal | 24px all sides |
| Dropdown item | 8px top / 8px bottom |

---

## 4. Border & Radius

```
--radius-sm    4px    — inputs, badges, tags
--radius-md    6px    — buttons, cards, dropdowns
--radius-lg    8px    — modals, panels
--radius-full  9999px — pill badges, toggles

--border-width     1px
--border-color     var(--surface-border)
--border-focus     var(--primary-500)
--border-error     var(--danger-500)
--border-success   var(--success-500)
```

**Rule:** Use `--radius-sm` by default. Only use `--radius-md` for primary action
buttons and card containers. Modals use `--radius-lg`. Never round a table.

---

## 5. Elevation & Shadow

```
--shadow-sm    0 1px 2px rgba(0,0,0,0.3)             — raised inputs, subtle cards
--shadow-md    0 4px 12px rgba(0,0,0,0.4)             — dropdowns, select menus
--shadow-lg    0 8px 24px rgba(0,0,0,0.5)             — modals, command palette
--shadow-focus 0 0 0 3px rgba(88,101,242,0.35)        — keyboard focus ring
```

Shadow in light mode uses lower opacity:
```
--shadow-sm    0 1px 3px rgba(0,0,0,0.08)
--shadow-md    0 4px 12px rgba(0,0,0,0.12)
--shadow-lg    0 8px 24px rgba(0,0,0,0.16)
--shadow-focus 0 0 0 3px rgba(88,101,242,0.25)
```

---

## 6. Layout Structure

### Shell

```
┌──────────────────────────────────────────────────────────┐
│  TOPBAR (52px, --surface-raised, border-bottom)          │
├──────────┬───────────────────────────────────────────────┤
│          │                                               │
│ SIDEBAR  │  CONTENT AREA                                 │
│ 240px    │  padding: 24px                                │
│          │  max-width: 1320px                            │
│ fixed    │  scrollable                                   │
│ left     │                                               │
│          │                                               │
└──────────┴───────────────────────────────────────────────┘
```

**Topbar** — `--surface-raised`, 1px bottom border `--surface-border`. Contains:
left-side logo + app name, center breadcrumb, right-side: search trigger, dark mode
toggle, user avatar dropdown.

**Sidebar** — `--surface-raised`, 1px right border `--surface-border`, fixed position,
full-height minus topbar. Contains: grouped nav sections with section labels,
user-accessible model links (only models they can view), system section at the bottom
(Audit Log, Roles, Agent, Settings).

**Content area** — `--surface-base` background. Scrolls independently. Has a 24px
padding on all sides. Content is constrained to `--content-max-width`.

### Responsive

- **< 1280px:** Content padding reduces to 16px.
- **< 1024px:** Sidebar collapses to 56px icon-only. Nav labels hidden. Hover tooltip
  shows the label.
- **< 768px:** Sidebar becomes a drawer (off-canvas). Hamburger in topbar opens it.
  Overlay backdrop closes it.

---

## 7. Components

### Buttons

Four variants. Each has default, hover, active, disabled, and loading states.

**Primary** — `--primary-500` fill, `--text-inverse` text. Use for the main action on
a page (Save, Create). One per page section maximum.

**Secondary** — transparent fill, `--surface-border` border, `--text-primary` text.
Use for secondary actions (Cancel, Export, Duplicate).

**Danger** — `--danger-500` fill on hover/active; shows as secondary style until
hovered. Use only for Delete. The fill should only appear on hover — not by default —
to prevent accidental clicks.

**Ghost** — no fill, no border, `--text-secondary` text. Hover adds a subtle
`--surface-overlay` background. Use for icon buttons, inline row actions.

```
Height:     32px (default), 28px (sm), 36px (md — form save bar only)
Padding:    0 12px (default), 0 8px (sm), 0 16px (md)
Gap:        6px between icon and label
Icon size:  16px (default), 14px (sm)
```

Loading state: replace label with a 14px spinner (CSS animation, not GIF). Keep
button width stable — do not let it shrink when the label disappears.

### Inputs & Form Controls

All form controls share the same height (34px) and base style:
`--surface-raised` background, `--surface-border` border, `--radius-sm`, `--text-sm`
text. On focus: `--border-focus` border + `--shadow-focus` ring. On error:
`--border-error` border, no focus ring.

**Text input:** Standard. Padding: 0 10px.

**Textarea:** Min-height 80px. Resizable vertically only. Same base style.

**Select:** Custom styled — hide native arrow, add Heroicon chevron-down at 14px.
Same height as input.

**Toggle / Checkbox:**

The toggle is the signature boolean control. It is a 36×20px pill. Track:
`--surface-border` (off) or `--primary-500` (on). Thumb: white circle, 16px, 2px
margin. Transition: 150ms ease for thumb position and track color. Do not use a
native checkbox for boolean fields — always use the toggle.

For multiple checkboxes (permission matrix, bulk select): use custom 16×16px squares
with `--radius-sm`, `--primary-500` fill when checked, checkmark SVG inside.

**Number input:** Same as text input. Right-align the value. Show `--text-secondary`
step arrows on hover only.

**Date / datetime:** Use native `<input type="date">` and `<input type="datetime-local">`
with custom CSS to reset the native appearance, then restyle consistently with other
inputs.

**JSON editor:** Render as a bordered container wrapping a CodeMirror 6 instance.
Container: `--surface-base` background (slightly darker than inputs to signal "code
zone"), `--radius-sm`, 1px border. Use the `material-darker` CodeMirror theme as a
base in dark mode, customised to match the palette.

### Badge

Compact inline label for statuses, counts, and tags.

```
Height:     20px
Padding:    0 6px
Font:       --text-xs, Inter 500
Radius:     --radius-sm
```

Variants:
- `neutral` — `--surface-overlay` bg, `--text-secondary` text
- `success` — `--success-100` bg, `--success-500` text
- `warning` — `--warning-100` bg, `--warning-500` text
- `danger` — `--danger-100` bg, `--danger-500` text
- `info` — `--info-100` bg, `--info-500` text
- `primary` — `--primary-100` bg, `--primary-500` text

Count badges (record counts, user counts in roles list): always use JetBrains Mono,
`neutral` variant.

### Table

The table is the most-used component in the admin. Every pixel matters.

```
Background:       --surface-raised
Border:           1px --surface-border, --radius-md (container only — not the table itself)
Header row:       --surface-overlay background, 10px vertical padding
Data row:         --surface-raised background (even), --surface-base (odd — 2% lighter)
Row hover:        --primary-100 background
Selected row:     --primary-100 background + left border 2px --primary-500
Row height:       40px (data rows), 36px (header row)
Cell padding:     0 12px
Column separator: none (no vertical borders between cells)
```

Header text: `--text-xs`, Inter 500, `--text-secondary`, uppercase, letter-spacing
0.04em. Sortable columns show a sort icon (Heroicons `arrows-up-down`, `chevron-up`,
or `chevron-down`) at 12px, `--text-disabled`, which becomes `--primary-500` when
active.

The bulk-select column (if permission allows) is 40px wide. The actions column is
right-aligned, auto-width to content, `--text-secondary` ghost links separated by
`·` divider.

All numeric values, IDs, and dates in table cells: JetBrains Mono, `--mono-accent`
color, `--text-mono-sm` size.

Long text values are truncated to one line with an ellipsis. Show full value on hover
in a tooltip.

### Empty State

When a table or list has no records:

- Centered vertically in the table container (or 120px top padding minimum)
- A Heroicons SVG illustration at 48px, `--text-disabled` color
- A short heading: `--text-md`, `--text-secondary`
- A subheading sentence: `--text-sm`, `--text-disabled`
- A primary button if the user has create permission

Do not use third-party illustration libraries. The Heroicons icon at 48px with a
subtle shadow is intentional — it fits the product's own visual language.

### Toast / Flash Messages

Position: top-right, 16px from edge. Stack upward (newest at bottom of stack).

```
Width:        320px
Padding:      12px 16px
Radius:       --radius-md
Shadow:       --shadow-md
Border-left:  3px solid (semantic color matching variant)
Background:   --surface-overlay
```

Auto-dismiss after 4000ms with a 300ms fade-out. Show a thin progress bar at the
bottom of the toast indicating time remaining (optional but adds perceived polish).
Include an `✕` close button at top-right (Ghost size sm).

### Modal / Dialog

```
Backdrop:   rgba(0,0,0,0.6), blur(2px)
Container:  --surface-raised, --radius-lg, --shadow-lg
Width:      480px (sm), 640px (default), 800px (lg), 100vw - 32px (mobile)
Max-height: 90vh, scrollable body
Header:     24px padding, --text-lg heading, close button top-right
Body:       24px padding, --text-base
Footer:     16px 24px padding, border-top --surface-border, right-aligned buttons
```

Confirm modals (delete confirmation): use the `sm` width variant. Danger variant:
the confirm button is the Danger button style. Never use `window.confirm()`.

### Dropdown Menu

```
Background:   --surface-overlay
Border:       1px --surface-border
Shadow:       --shadow-md
Radius:       --radius-md
Min-width:    160px
Max-height:   320px (scrollable if more items)
```

Menu item: 32px height, 8px vertical padding, 12px horizontal padding, `--text-sm`,
`--text-primary`. Hover: `--primary-100` background. Destructive items:
`--danger-500` text.

Section dividers: 1px `--surface-border`, 4px vertical margin.

### Sidebar Nav

```
Nav item height:     36px
Nav item padding:    0 12px
Nav item radius:     --radius-sm (inside sidebar)
Icon size:           16px
Icon-label gap:      10px
Section label:       --text-xs, uppercase, letter-spacing 0.06em, --text-disabled,
                     12px padding-left, 16px top margin, 6px bottom margin
```

Active item: `--primary-100` background, `--primary-500` text + icon.
Inactive: `--text-secondary` text + icon. Hover: `--surface-overlay` background.

Active indicator: 2px left border `--primary-500` on the active item. Do not use
a bold font change for active — the left border + color is enough.

### Form Layout

Forms are constrained to `--form-max-width` (860px). Fields are arranged in a
responsive grid — not a rigid two-column layout. The grid uses CSS Grid with
`auto-fill` and a 280px minimum column width. Wide fields (textarea, JSON, rich text,
relationship pickers) always span full width.

Fieldset sections have a heading (`--text-xs`, uppercase, `--text-secondary`) and a
1px top border `--surface-border`. Section heading sits inline in the border (like
a `<legend>` style). Sections are collapsible — default state is set per-section.

The save bar is sticky at the bottom of the content area, not the viewport. It sits
inside the scrolling content container. It has a `--surface-raised` background, 1px
top border, and contains the action buttons plus any dirty-state indicators.

### Pagination

Inline with the table. Not centered — left-aligned showing "Showing 1–20 of 143",
right-aligned with Previous / page numbers / Next.

```
Page button:  28px square, --radius-sm
Active page:  --primary-500 bg, --text-inverse text
Text:         --text-sm, JetBrains Mono for numbers
```

Show at most 7 page buttons. Use ellipsis (`…`) for large ranges.

---

## 8. Icons

Use Heroicons outline style exclusively. Size: 16px in all UI contexts (nav, buttons,
table actions, form controls). 20px only in empty states or when used alone without
text context. 12px for sort indicators and compact metadata.

Icon color always inherits from parent text color. Never set a separate icon color
unless the icon represents a semantic state (green check for success, red X for error).

Load as an SVG sprite (`heroicons.svg`) with `<use>` references. Do not inline
individual SVGs in templates — it inflates HTML and makes global icon updates painful.

---

## 9. Motion & Animation

**Philosophy:** Fast, functional, invisible. Transitions signal state changes — they
do not entertain. Every animation should finish before the user can notice it was
running.

```
--duration-instant   50ms    — checkbox toggle, toggle switch
--duration-fast      100ms   — button hover, badge appear
--duration-base      150ms   — dropdown open, tooltip appear, row highlight
--duration-slow      200ms   — modal appear, sidebar expand, toast slide-in
--easing-default     cubic-bezier(0.16, 1, 0.3, 1)   — everything opening
--easing-in          cubic-bezier(0.4, 0, 1, 1)       — everything closing
```

**What gets animated:**
- Dropdown / menu: opacity 0→1, translateY(-4px)→0 on open. Reverse on close.
- Modal: opacity 0→1, scale(0.97)→1 on open. Duration: `--duration-slow`.
- Toast: translateX(100%)→0 on enter. Opacity fade on dismiss.
- Sidebar expand/collapse: width transition `--duration-slow`.
- Table row delete: height→0 + opacity→0 + the row above shifts down. `--duration-base`.
- Toggle switch: thumb position + track color. `--duration-instant`.
- Loading bar (HTMX indicator): width 0→100% with indeterminate shimmer.

**What does not get animated:**
- Page navigation (full page loads)
- Table row hover
- Input focus (only the ring appears instantly)
- Anything inside a table cell

**Reduced motion:** All transitions and animations must be wrapped in
`@media (prefers-reduced-motion: no-preference)`. Default: no animation.

---

## 10. Dark Mode Implementation

Dark mode is the default. Light mode is an opt-in via the topbar toggle.

The toggle writes `data-theme="light"` to `<html>` and saves to `localStorage` key
`admin-theme`. On page load, read `localStorage` before render to avoid flash of
wrong theme (set in a `<script>` in `<head>`, before any CSS loads).

All color tokens are defined as CSS custom properties on `:root` (dark values) and
overridden in `[data-theme="light"]`. Components use only token variables — no
hardcoded hex values anywhere in component CSS.

The dark/light toggle icon: moon icon when in dark mode (clicking switches to light),
sun icon when in light mode (clicking switches to dark). 20px, Ghost button variant,
no label.

---

## 11. Loading & Skeleton States

### HTMX Loading Bar

A 2px bar at the very top of the `<body>` (above topbar). Uses `--primary-500` fill.
Shown/hidden automatically by HTMX via the `htmx-indicator` class. Uses a shimmer
animation while loading (keyframe that moves a lighter highlight left to right).

### Skeleton Rows

On initial table load, render 8 skeleton rows before HTMX replaces with real data.
Each skeleton row has the same height (40px) as a real row. Cells contain a
`<div class="skeleton">` — a `--surface-overlay` rectangle with a shimmer animation.
Width of skeleton cells: vary per column type to look realistic (60% for name, 15%
for price, 10% for status, etc.). Do not use the same width for all cells.

### Button Loading State

When a form is submitting, the submit button shows a 14px spinner (CSS-only, two
semi-circles rotating) and becomes disabled. The button width is locked via
`min-width` set to the button's default width before submission starts.

---

## 12. Agent Chat Panel

The agent panel deserves its own component spec since it is a different interaction
mode from the rest of the admin.

### Panel Container

```
Width:           420px
Position:        fixed right, below topbar
Height:          calc(100vh - 52px)
Background:      --surface-raised
Border-left:     1px --surface-border
Shadow:          --shadow-lg (left side only)
Z-index:         40 (above content, below modals)
```

The panel slides in from the right (translateX transition, `--duration-slow`). A
backdrop overlay does NOT appear — the agent panel is non-modal. The main content
remains interactive with the panel open.

### Conversation Thread

Message bubbles:
- **User messages:** right-aligned, `--primary-100` background, `--radius-md`,
  max-width 80%, `--text-sm`.
- **Agent messages:** left-aligned, `--surface-overlay` background, `--radius-md`,
  max-width 85%, `--text-sm`. Markdown rendered (bold, code, lists, tables).
- **Tool call indicators:** between messages. A compact row showing the tool name
  and a loading/done indicator: `⚙ Querying products...` → `✓ Found 42 records`.
  `--text-xs`, JetBrains Mono, `--text-secondary`.
- **Agent data tables:** when the agent returns tabular data, render it using the
  same table component styles (condensed variant, no checkboxes).

### Input Area

Fixed at the bottom of the panel.

```
Padding:     12px
Textarea:    auto-grow, 1–5 lines, same input style as form textarea
Send button: 32px square, primary variant, Heroicons `paper-airplane` icon
Shortcut:    Ctrl+Enter sends, Shift+Enter newline
```

Below the input: `--text-xs`, `--text-disabled` text showing the current model name.

### Streaming Indicator

While the agent is thinking/streaming: show a pulsing `●●●` at `--primary-500` color,
16px, inside a `--surface-overlay` bubble on the left (agent side). Each dot pulses
with a 200ms stagger.

---

## 13. Dashboard Specific

### Stat Cards

```
Layout:       CSS Grid, auto-fill, min 200px per card
Background:   --surface-raised
Border:       1px --surface-border
Radius:       --radius-md
Padding:      20px

Label:        --text-xs, uppercase, letter-spacing 0.06em, --text-secondary
Value:        --text-xl, Inter 600, --text-primary  ← the big number
Change:       --text-xs, JetBrains Mono, success/danger color
Icon:         20px, top-right of card, --text-disabled
```

The "big number" value must always be set in Inter 600 at `--text-xl`. If the value
has a unit (%, $, items), separate it from the number with a small `--text-sm` unit
label in `--text-secondary`.

### Recent Activity Feed

Narrow column (max 480px) on the right side of the dashboard. Each entry:

```
Height:       auto
Layout:       icon left (24px circle bg), content right, timestamp far right
Icon circle:  --success-100 / --warning-100 / --danger-100 bg, 24px diameter
Timestamp:    --text-mono, --text-secondary, right-aligned
Content:      --text-sm, --text-primary
Divider:      1px --surface-border between entries (not below last)
```

---

## 14. Accessibility Baseline

These are requirements, not suggestions.

- All interactive elements have a visible focus style: `--shadow-focus` ring.
  Never `outline: none` without a replacement.
- Color is never the only indicator of meaning. Status badges have text labels, not
  just color fills. Error states have text messages, not just a red border.
- All icon-only buttons have `aria-label` or a visually-hidden `<span>`.
- All form inputs have `<label>` elements associated by `for`/`id`.
- The toggle switch uses `role="switch"` and `aria-checked`.
- Modals trap focus within themselves when open. Return focus to the trigger on close.
- Keyboard navigation: all dropdowns, modals, and menus must be dismissible with
  `Escape`.
- The sidebar nav uses `<nav aria-label="Main navigation">`.
- Table checkboxes in the list view use `aria-label="Select {record_name}"`.

---

## 15. CSS Architecture

### File Structure

```
static/css/
├── tokens.css          # All CSS custom properties (this file is the source of truth)
├── reset.css           # Minimal reset (box-sizing, margin, padding normalization)
├── base.css            # Body, html, root typography defaults
├── layout.css          # Shell: topbar, sidebar, content area
├── components/
│   ├── button.css
│   ├── input.css
│   ├── table.css
│   ├── badge.css
│   ├── toast.css
│   ├── modal.css
│   ├── dropdown.css
│   ├── nav.css
│   ├── form.css
│   ├── pagination.css
│   ├── skeleton.css
│   └── agent-panel.css
└── utilities.css       # Single-purpose helpers (sr-only, truncate, etc.)
```

### Naming Convention

BEM-style but flat where possible:

```
.table                    — block
.table__header            — element
.table__row               — element
.table__row--selected     — modifier
.table__cell              — element
.table__cell--mono        — modifier (for data cells using JetBrains Mono)

.btn                      — block
.btn--primary             — modifier
.btn--sm                  — modifier
.btn--loading             — state modifier

.badge                    — block
.badge--success           — modifier
```

No Tailwind utility classes in component files. Tailwind utility classes are permitted
only in template files for layout-level one-offs (margins, widths, flex). Component
styles must come from component CSS files. This separation makes theming and overrides
predictable.

### Specificity Rules

- Component selectors: class-only, one level deep. `.table__row`, not `table tr`.
- Never use `!important` in component CSS.
- State modifiers (`--selected`, `--error`, `--loading`) are co-located with their
  component class, not in a separate utilities file.
- Tailwind's `@layer` is not used — the CSS is hand-authored to avoid Tailwind's
  purge complexity in a distributed package.

---

## 16. Token Quick Reference

For implementation: every value in this document is derived from these tokens.
Nothing else should be hardcoded.

```css
:root {
  /* Surfaces */
  --surface-base:     #0F1117;
  --surface-raised:   #181B23;
  --surface-overlay:  #1E2230;
  --surface-border:   #2A2F3F;

  /* Text */
  --text-primary:     #E8EAF0;
  --text-secondary:   #8B90A0;
  --text-disabled:    #454A5A;
  --text-inverse:     #0F1117;

  /* Primary */
  --primary-100:      #1A1F3D;
  --primary-400:      #7B86F5;
  --primary-500:      #5865F2;
  --primary-600:      #4350D4;

  /* Semantic */
  --success-100:      #0D2818;
  --success-500:      #22C55E;
  --warning-100:      #2A1F0A;
  --warning-500:      #F59E0B;
  --danger-100:       #2A1010;
  --danger-500:       #EF4444;
  --info-100:         #0D1A2F;
  --info-500:         #3B82F6;

  /* Signature */
  --mono-accent:      #A6E3A1;

  /* Typography */
  --font-ui:          'Inter', system-ui, sans-serif;
  --font-mono:        'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;

  /* Radius */
  --radius-sm:    4px;
  --radius-md:    6px;
  --radius-lg:    8px;
  --radius-full:  9999px;

  /* Animation */
  --duration-instant: 50ms;
  --duration-fast:    100ms;
  --duration-base:    150ms;
  --duration-slow:    200ms;
  --easing-default:   cubic-bezier(0.16, 1, 0.3, 1);
  --easing-in:        cubic-bezier(0.4, 0, 1, 1);

  /* Shadows */
  --shadow-sm:    0 1px 2px rgba(0,0,0,0.3);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.5);
  --shadow-focus: 0 0 0 3px rgba(88,101,242,0.35);

  /* Layout */
  --sidebar-width:      240px;
  --sidebar-collapsed:  56px;
  --topbar-height:      52px;
  --content-padding:    24px;
  --content-max-width:  1320px;
  --form-max-width:     860px;
}

[data-theme="light"] {
  --surface-base:    #F8F9FC;
  --surface-raised:  #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border:  #E2E5EE;
  --text-primary:    #111827;
  --text-secondary:  #6B7280;
  --text-disabled:   #9CA3AF;
  --text-inverse:    #FFFFFF;
  --primary-100:     #EEF0FE;
  --success-100:     #F0FDF4;
  --warning-100:     #FFFBEB;
  --danger-100:      #FEF2F2;
  --info-100:        #EFF6FF;
  --mono-accent:     #166534;
  --shadow-sm:       0 1px 3px rgba(0,0,0,0.08);
  --shadow-md:       0 4px 12px rgba(0,0,0,0.12);
  --shadow-lg:       0 8px 24px rgba(0,0,0,0.16);
  --shadow-focus:    0 0 0 3px rgba(88,101,242,0.25);
}
```