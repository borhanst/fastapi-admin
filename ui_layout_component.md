# FastAPI Admin — Layout & Component Placement

> Where every component lives, how it is structured, what it contains, and how
> components relate to each other across every page. Read alongside
> `UI_DESIGN_SYSTEM.md` which owns all token values, sizes, and visual rules.
> This document owns placement, hierarchy, and page-by-page anatomy.

---

## Table of Contents

1. [Shell Layout](#1-shell-layout)
2. [Topbar](#2-topbar)
3. [Sidebar](#3-sidebar)
4. [Content Area](#4-content-area)
5. [List Page](#5-list-page)
6. [Search & Filter Bar](#6-search--filter-bar)
7. [Table & Actions](#7-table--actions)
8. [Bulk Action Bar](#8-bulk-action-bar)
9. [Create / Edit Form Page](#9-create--edit-form-page)
10. [Form Fieldsets](#10-form-fieldsets)
11. [Form Save Bar](#11-form-save-bar)
12. [Delete Confirmation](#12-delete-confirmation)
13. [Dashboard Page](#13-dashboard-page)
14. [Audit Log Page](#14-audit-log-page)
15. [Role Management Page](#15-role-management-page)
16. [Agent Chat Panel](#16-agent-chat-panel)
17. [Login Page](#17-login-page)
18. [Modals & Overlays](#18-modals--overlays)
19. [Responsive Behaviour](#19-responsive-behaviour)
20. [Page Transition & Loading States](#20-page-transition--loading-states)
21. [Component Placement Rules (Summary)](#21-component-placement-rules-summary)

---

## 1. Shell Layout

The shell is the persistent frame around every page. It never scrolls. Only the
content area scrolls.

```
┌─────────────────────────────────────────────────────────────────┐
│                         TOPBAR                                  │
│  52px height · --surface-raised · border-bottom                 │
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│    SIDEBAR       │            CONTENT AREA                     │
│                  │                                              │
│  240px · fixed   │  flex-1 · overflow-y: auto                  │
│  --surface-raised│  --surface-base background                  │
│  border-right    │  padding: 24px                              │
│                  │  max-width: 1320px (centered)               │
│                  │                                              │
│                  │                                              │
└──────────────────┴──────────────────────────────────────────────┘
```

**CSS structure:**

```
body
└── .admin-shell                        display: flex; flex-direction: column; height: 100vh
    ├── .admin-topbar                   height: var(--topbar-height); flex-shrink: 0
    └── .admin-body                     display: flex; flex: 1; overflow: hidden
        ├── .admin-sidebar              width: var(--sidebar-width); flex-shrink: 0; overflow-y: auto
        └── .admin-content              flex: 1; overflow-y: auto; padding: var(--content-padding)
```

The `overflow: hidden` on `.admin-body` is critical — it confines scrolling to
`.admin-content` only. The sidebar scrolls independently if nav items overflow.

---

## 2. Topbar

**Position:** Top of shell. Full width. Fixed height 52px.

```
┌──────────────────────────────────────────────────────────────────┐
│ [≡] [Logo · AppName]   [Breadcrumb]            [⌕] [◑] [Avatar▾]│
│ ←16px→                  ←flex grow→            ←──── right ────→│
└──────────────────────────────────────────────────────────────────┘
```

### Left zone

- **Collapse toggle** (≡) — 36px ghost icon button, 16px from left edge. Toggles
  sidebar between full and collapsed. On mobile, opens the sidebar drawer.
- **Logo** — 28px tall, max-width 120px, links to `/admin/`. If no logo configured,
  show the app `title` text in `--text-sm` Inter 600.
- Divider: 1px vertical `--surface-border`, 20px height, 12px horizontal margin.

### Center zone

- **Breadcrumb** — shows current page location. Format:
  `[Model Name] / [Action]` e.g. `Products / Edit #1042`. Separator: `/` in
  `--text-disabled`. Each segment except the last is a link. Last segment is plain
  `--text-secondary`. Font: `--text-sm` Inter 400.
- Breadcrumb takes all available horizontal space between left and right zones.

### Right zone

- **Search trigger** (⌕) — 36px ghost icon button. Opens the command palette overlay
  (global search). Tooltip: "Search (⌘K)". On desktop, also render a static
  `⌘K` badge next to the icon in `--text-xs --text-disabled`.
- **Theme toggle** (◑) — 36px ghost icon button. Moon icon in dark mode, sun in light.
- **User avatar** — 28px circle. Initials fallback if no avatar image. Clicking
  opens a dropdown: user name (non-clickable header), role badge, divider, Profile
  link, divider, Sign out button (danger text color).
- Spacing between right zone items: 4px.
- Right zone right edge: 16px from viewport edge.

### Topbar states

| State | Behaviour |
|---|---|
| Loading (HTMX) | 2px `--primary-500` bar appears at very top of topbar (above everything) |
| Agent panel open | Topbar full width unchanged — panel overlaps content only |

---

## 3. Sidebar

**Position:** Left of content area. Full height minus topbar. Fixed. 240px wide.

```
┌──────────────────────┐
│  SECTION LABEL        │  ← --text-xs, uppercase, --text-disabled
│  ─────────────────   │
│  ▪ Dashboard         │  ← nav item
│  ─────────────────   │
│  MODELS              │  ← section label
│  ─────────────────   │
│  □ Products      12  │  ← nav item with record count badge
│  □ Orders         3  │
│  □ Categories        │
│  □ Users             │
│  ─────────────────   │
│  SYSTEM              │  ← section label
│  ─────────────────   │
│  □ Audit Log         │
│  □ Roles             │
│  □ Agent             │  ← only if agent configured
│  □ API Keys          │  ← only if agent API keys enabled
│                      │
│  ────────────────────│  ← push remaining to bottom
│  □ Settings          │  ← bottom-anchored item
└──────────────────────┘
```

### Nav sections

Three fixed sections in this order:
1. **No label** — Dashboard only (single item, always first)
2. **MODELS** — All registered models the user can view, alphabetical within each
   group. Groups are defined by `ModelAdmin.nav_group` if set; otherwise all in one
   flat list.
3. **SYSTEM** — Audit Log, Roles (superuser only), Agent (if configured), API Keys
   (if configured).
4. **BOTTOM** (pushed to bottom via `margin-top: auto`) — Settings.

### Nav item anatomy

```
┌───────────────────────────────────────┐
│ [icon 16px] [label --text-sm]  [badge]│
│ ←12px pad                    12px→   │
└───────────────────────────────────────┘
  height: 36px
  border-radius: --radius-sm
```

- Icon: Heroicons outline 16px, inherits text color.
- Label: `--text-sm` Inter 400 (inactive) / Inter 500 (active).
- Badge: only on model items — shows live record count. `--text-mono-sm` JetBrains
  Mono, neutral badge variant. Only show if count > 0.
- Active state: `--primary-100` background, `--primary-500` text + icon,
  2px left border `--primary-500`.
- Hover state: `--surface-overlay` background.

### Section labels

`--text-xs` Inter 500, uppercase, letter-spacing 0.06em, `--text-disabled`.
Padding: 16px top, 12px left, 6px bottom. No border, no divider line (whitespace
is the separator).

### Collapsed sidebar (< 1024px)

Width: 56px. Labels hidden. Icons centered. Section labels hidden (no text to show).
On hover over any icon: tooltip appears to the right of the icon showing the nav label.
Tooltip: `--surface-overlay` background, `--shadow-md`, `--radius-sm`, `--text-sm`,
8px horizontal padding, 6px vertical, positioned `left: 64px`.

Active indicator in collapsed mode: 3px left border `--primary-500` only (no bg).

---

## 4. Content Area

Everything to the right of the sidebar. Scrolls vertically. Contains a max-width
wrapper for all actual content.

```
.admin-content
└── .admin-content__inner        max-width: 1320px; margin: 0 auto; padding: 24px
    ├── .page-header             page title row
    ├── .page-body               main content (table, form, etc.)
    └── (sticky .form-save-bar)  only on form pages
```

### Page header

Every page has a header row. It is the first element inside `.admin-content__inner`.
It is never sticky — it scrolls with the content.

```
┌─────────────────────────────────────────────────────────────┐
│ [Page Title --text-lg]                  [Primary Action Btn] │
│ [Subtitle --text-sm --text-secondary]                        │
└─────────────────────────────────────────────────────────────┘
  padding-bottom: 20px
  border-bottom: 1px --surface-border
  margin-bottom: 20px
```

- **Title:** `--text-lg` Inter 600 `--text-primary`. Examples: "Products",
  "Edit Product", "Roles".
- **Subtitle:** optional. `--text-sm` Inter 400 `--text-secondary`. For list pages:
  record count e.g. "143 records". For edit pages: object repr e.g. "Nike Air Max 90".
  Object repr in `--text-sm` JetBrains Mono if it contains an ID.
- **Primary action:** top-right of the header row. On list pages: "+ New {Model}"
  primary button. On edit pages: nothing (save is in the save bar). On dashboard: none.
- Only one primary action per page header. Secondary actions (Export, Import) go in
  the search/filter bar, not the page header.

---

## 5. List Page

The list page is the most common page. Its layout has four stacked zones.

```
┌─────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                    [+ New Product] │
│  Products · 143 records                                         │
├─────────────────────────────────────────────────────────────────┤
│  SEARCH & FILTER BAR                                            │
│  [🔍 Search products...]  [Category ▾] [Status ▾]  [Export ▾]  │
├─────────────────────────────────────────────────────────────────┤
│  TABLE                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☐  NAME         PRICE    STOCK   STATUS    CREATED      │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ ☐  Air Max 90   $149.99  12      ● Active   Jan 15 2024 │   │
│  │ ☐  Stan Smith   $89.99   0       ○ Draft    Jan 10 2024 │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  PAGINATION                                                     │
│  Showing 1–20 of 143               [◀ Prev] 1 2 3 … 8 [Next ▶] │
└─────────────────────────────────────────────────────────────────┘
```

Zone order is fixed. No component from a lower zone may appear in an upper zone.

---

## 6. Search & Filter Bar

**Position:** Directly below the page header border. Sticks to the top of the
content area when the user scrolls past the page header (position: sticky,
top: 0, z-index: 10, background: `--surface-base`).

```
┌─────────────────────────────────────────────────────────────────┐
│ [🔍 Search...]  [Filter 1 ▾] [Filter 2 ▾]  ·  [Clear filters]  │
│                                              →  [Export ▾]      │
└─────────────────────────────────────────────────────────────────┘
  height: 48px (single row)
  padding: 0 0 12px 0 (bottom gap before table)
  display: flex; align-items: center; gap: 8px
```

### Search input

**Leftmost element.** Takes up remaining space after all filter chips
(`flex: 1`, min-width: 200px, max-width: 360px).

```
Width:        flex 1, max 360px
Height:       34px
Placeholder:  "Search {verbose_name_plural}..."  in --text-disabled
Left icon:    Heroicons magnifying-glass 14px, --text-disabled, 10px left padding
Padding:      0 10px 0 32px  (left padding accounts for the icon)
```

HTMX behaviour: `hx-get="/admin/{table}/"` on `keyup` with `delay:300ms`. Replaces
`#table-wrapper` (table + pagination). Does not replace the search bar itself.

When search is active (value is non-empty): show a clear button (✕) inside the input
on the right. Clicking clears and re-fetches.

### Filter chips

Each filter is a compact dropdown button. Closed state:

```
Height:       34px
Padding:      0 10px
Border:       1px --surface-border
Radius:       --radius-sm
Font:         --text-sm Inter 400
Color:        --text-secondary (inactive) / --text-primary (active/has value)
Background:   --surface-raised (inactive) / --primary-100 (active)
Right icon:   Heroicons chevron-down 12px
```

When a filter has an active value: background becomes `--primary-100`, text becomes
`--text-primary`, and a count badge appears inside the button showing how many values
are selected. Example: `Category · 2`.

Clicking a filter opens a dropdown panel (not a modal):

```
Width:        220px (min) to 320px (max)
Position:     below the filter button, left-aligned
Background:   --surface-overlay
Border:       1px --surface-border
Shadow:       --shadow-md
Radius:       --radius-md
Padding:      6px
Max-height:   280px with internal scroll
```

Inside the dropdown: list of options with checkboxes. Selecting any applies
immediately (HTMX re-fetch). A "Clear" link at the bottom of the dropdown. Boolean
filters (is_active) show as a two-option radio (Yes / No / Any).

### Filter layout rules

- Show at most 4 filter chips before collapsing extras into a "+ N more" overflow
  button.
- Filter chips come from `ModelAdmin.list_filter`. They appear in the order defined.
- FK filters: the dropdown shows a search input at the top + paginated results
  (same HTMX search pattern as the relation picker).

### Right side of filter bar

Separated by a flexible spacer (`flex: 1`). Contains:

- **"Clear all filters"** text link — only visible when ≥ 1 filter is active.
  `--text-sm` `--text-secondary`, hover `--text-primary`.
- **Export dropdown** — secondary button style, `--text-sm`. Only if
  `ModelAdmin.enable_export = True`. Dropdown has options: "Export CSV",
  "Export XLSX". Each triggers a direct download link.
- **Column visibility** (optional) — ghost icon button (Heroicons `view-columns`).
  Opens a dropdown checklist of columns to show/hide. Preference saved in
  `localStorage`.

---

## 7. Table & Actions

**Position:** Below the search/filter bar. Full width of content area.

### Table container

```
Background:   --surface-raised
Border:       1px --surface-border
Radius:       --radius-md
Overflow:     hidden (clips the child table's straight corners)
```

The container has `border-radius` — the table itself (`<table>`) has none.

### Table structure

```html
<div id="table-wrapper">               ← HTMX swap target
  <table>
    <thead>
      <tr class="table__header-row">
        <th class="table__th table__th--checkbox">  ← bulk select
        <th class="table__th table__th--sortable">  ← data columns
        <th class="table__th table__th--actions">   ← row actions
      </tr>
    </thead>
    <tbody id="table-body">            ← inner HTMX swap target (search/filter)
      <tr class="table__row">
        <td class="table__cell table__cell--checkbox">
        <td class="table__cell">
        <td class="table__cell table__cell--actions">
      </tr>
    </tbody>
  </table>
  <div class="table__pagination">      ← always outside <table>
</div>
```

### Column header

Each `<th>` has:
- Text: `--text-xs` Inter 500, uppercase, letter-spacing 0.04em, `--text-secondary`.
- Padding: 10px 12px.
- Sortable columns: hover shows sort icon (arrows-up-down, 12px, `--text-disabled`).
  Active sort shows directional icon in `--primary-500`.
- Clicking a sortable column header: HTMX fetch with `?sort={col}&dir={asc|desc}`.
  Current sort state stored in URL params.

### Checkbox column

Width: 44px. Always leftmost. Only present if user has `can_delete` permission.
Header checkbox: selects all visible rows. When indeterminate (some selected): dash
icon. Drives the bulk action bar appearance.

### Data columns

- Padding: 10px 12px.
- Text values: `--text-sm` Inter 400, `--text-primary`, truncate to single line.
- Numeric / ID / date values: `--text-mono-sm` JetBrains Mono, `--mono-accent`.
- Boolean values: do not render true/false text. Render a 6px circle: `--success-500`
  (true) or `--surface-border` (false). Add an `aria-label` for screen readers.
- Status / enum values: render as badge (see badge component in design system).
- FK values: render as the related object's `__str__` representation, linked to that
  object's edit page.
- Long text: truncated with ellipsis. On hover: show a tooltip with the full value
  (tooltip component, max-width 280px).

### Actions column

Width: auto (content-width). Always rightmost. Never gets a column header label.

```
[Edit]  ·  [Delete]
```

- "Edit" — ghost text link `--text-sm` `--text-secondary`, links to edit page.
- Dot separator (·) — `--text-disabled`, 4px horizontal margin.
- "Delete" — ghost text link `--text-sm` `--text-secondary`. On hover: `--danger-500`.
  Clicking opens inline confirmation (not a modal — see below).

**Inline delete confirmation** replaces the action cell content:

```
Delete "[object name]"?  [Yes, delete]  [Cancel]
```

This replaces only the actions `<td>` via HTMX `hx-swap="innerHTML"`. "Yes, delete"
is a danger button (sm). "Cancel" is a ghost button (sm). If custom `row_actions` are
defined they appear between Edit and the dot separator.

### Row hover

`--primary-100` background on the entire `<tr>`. Transition: `--duration-fast`.

### Empty table

When no rows: render a single full-width `<tr>` containing the empty state (not a
`<div>` outside the table). Empty state has a 60px top/bottom padding:

```
  [inbox icon 40px, --text-disabled]
  No {verbose_name_plural} found
  [subtext if filters active: "Try clearing your filters"]
  [+ New {verbose_name} button if can_create]
```

---

## 8. Bulk Action Bar

**Position:** Replaces the search/filter bar when ≥ 1 row is selected. Animates in
with a height expand (150ms). Animates out when selection is cleared.

```
┌─────────────────────────────────────────────────────────────────┐
│ [✕] 3 selected      [Action ▾]                   [Delete (3)]  │
└─────────────────────────────────────────────────────────────────┘
  height: 48px
  background: --primary-100
  border: 1px --primary-500
  border-radius: --radius-md
  padding: 0 12px
```

- Left: ✕ button to deselect all (ghost sm), then "{N} selected" in `--text-sm`
  Inter 500 `--text-primary`.
- Center: Action dropdown button (secondary style). Contains all `get_actions()` items.
  Custom actions defined in `ModelAdmin.get_actions()` appear here.
- Right: "Delete ({N})" danger button — only if user has `can_delete`. Clicking opens
  a confirmation modal (not inline) since this is a bulk destructive action.

The bulk action bar occupies the same vertical space as the filter bar. When it
appears, the filter bar is hidden (not just covered — `display: none`). When
selection is cleared, the filter bar reappears.

---

## 9. Create / Edit Form Page

Form pages have three zones. Only the middle zone scrolls.

```
┌─────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                                    │
│  [← Products]  Edit Product  ·  Nike Air Max 90 #1042          │
├─────────────────────────────────────────────────────────────────┤
│  FORM BODY  (scrolls)                                           │
│  max-width: 860px                                               │
│                                                                 │
│  [Fieldset 1]                                                   │
│  [Fieldset 2]                                                   │
│  [Relationships]                                                 │
│  [Extra Fields]                                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SAVE BAR  (sticky bottom)                                      │
│  [Delete]        [Save & continue editing]  [Save & return]     │
└─────────────────────────────────────────────────────────────────┘
```

### Form page header

Same structure as list page header, but:
- Title: "New {Model}" for create, "Edit {Model}" for edit.
- Subtitle: Object repr + ID for edit. Nothing for create.
- Back link: `← {Model plural}` ghost text link, top-left before the title.
  Uses Heroicons `arrow-left` 14px inline. Not a button — plain `<a>` tag.
- Right side of header: on edit pages only — a "History" tab link
  (`--text-sm --text-secondary`, Heroicons `clock` 14px). Scrolls to the history
  section at the bottom of the form.
- No primary action button in the form page header — save is in the save bar.

### Form layout

```
.form-body
  max-width: var(--form-max-width)   (860px)
  display: flex
  flex-direction: column
  gap: 24px
```

Each fieldset is a visual card:

```
.fieldset
  background:   --surface-raised
  border:       1px --surface-border
  border-radius: --radius-md
  padding:      20px
```

Inside each fieldset, fields are arranged in a responsive CSS Grid:

```css
.fieldset__fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
```

Fields that should always span full width: textarea, JSON editor, rich text,
relationship pickers (multi), file upload, image upload. These use:
`grid-column: 1 / -1`.

---

## 10. Form Fieldsets

Each fieldset has a header and a body.

```
┌─────────────────────────────────────────────────────────────────┐
│  GENERAL INFORMATION                    [▾ collapse]           │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  [Name field]           [SKU field]                             │
│  [Description field — full width]                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fieldset header

```
display: flex; justify-content: space-between; align-items: center
padding-bottom: 14px
border-bottom: 1px --surface-border
margin-bottom: 16px
```

- **Title:** `--text-xs` Inter 500, uppercase, letter-spacing 0.06em, `--text-secondary`.
- **Collapse toggle:** ghost icon button, Heroicons `chevron-down` / `chevron-up` 14px,
  right-aligned. Collapse/expand uses Alpine.js `x-show` with `--duration-base`
  height transition. Toggle is accessible: `aria-expanded`, `aria-controls`.
- Unnamed fieldsets (title is None): no header rendered. The fieldset card has no
  top section, fields start immediately at the card padding.

### Field wrapper anatomy

Every form field is wrapped in `.field-wrapper`:

```
.field-wrapper
  display: flex
  flex-direction: column
  gap: 5px               (between label and input, and between input and error)
```

From top to bottom inside a field wrapper:

1. **Label row** — `<label>` in `--text-sm` Inter 500 `--text-primary`. If required,
   a `*` in `--danger-500` with 3px left margin. If readonly, a lock icon
   (Heroicons `lock-closed` 12px) in `--text-disabled` after the label.
2. **Input / control** — the widget-specific element.
3. **Help text** — optional. `--text-sm` Inter 400 `--text-secondary`. Only shown if
   `FieldMeta.help_text` is set.
4. **Error list** — `<ul>` with no bullets. Each `<li>` in `--text-sm` Inter 400
   `--danger-500`. Heroicons `exclamation-circle` 12px inline before the message.
   Appears only when field has errors.

---

## 11. Form Save Bar

**Position:** Sticky at the bottom of `.admin-content`. Not the viewport — sticky
within the scrollable content column. This means it appears fixed at the bottom
of the visible content area, not at the bottom of the screen if a sidebar or
other panels are present.

```
┌─────────────────────────────────────────────────────────────────┐
│ [Delete record]      [Save & continue editing]  [Save & return] │
└─────────────────────────────────────────────────────────────────┘
  position: sticky
  bottom: 0
  background: --surface-raised
  border-top: 1px --surface-border
  padding: 12px 24px
  z-index: 20
  display: flex
  align-items: center
```

### Save bar layout

- **Left:** "Delete record" — danger button style (shows secondary, turns danger on
  hover). Only on edit pages, only if user has `can_delete`. Clicking opens the
  delete confirmation modal. Never appears on create pages.
- **Right:** Two action buttons, right-aligned, gap 8px:
  - "Save & continue editing" — secondary button. Submits form, redirects back to
    the same edit page. After redirect: flash success toast.
  - "Save & return" — primary button. Submits form, redirects to list page.

### Dirty state

When the user has made changes to the form (Alpine.js `x-data` tracks `isDirty`):
- A dot badge `●` appears before "Save & continue editing" in `--warning-500`.
  `--text-xs` JetBrains Mono. Example: `● Save & continue editing`.
- If the user tries to navigate away with unsaved changes: a browser `beforeunload`
  warning. Do not use a custom modal — the native browser dialog is sufficient and
  more trustworthy.

### Submitting state

When either save button is clicked: that button shows a loading spinner (see button
loading state in design system). The other save button is also disabled. The delete
button remains enabled. The save bar gets a 50% opacity on non-loading elements.

---

## 12. Delete Confirmation

Two variants depending on context.

### Inline (single record from list row)

Replaces the actions cell in the table row. No modal. The row gets a subtle
`--danger-100` background tint while the confirmation is shown.

```
Delete "Nike Air Max 90"?  [Yes, delete]  [Cancel]
```

"Yes, delete" is `btn btn--danger btn--sm`. "Cancel" is `btn btn--ghost btn--sm`.
If the user clicks elsewhere, cancel automatically.

### Modal (delete from edit form save bar, or bulk delete)

Opens a `modal modal--sm` (480px):

- Header: "Delete {Model}?" in `--text-lg`. No icon — the danger button in the footer
  is the visual signal.
- Body: "This will permanently delete **{object repr}**. This cannot be undone."
  `--text-base`. Object repr in `<strong>`.
- Footer: right-aligned. "Cancel" ghost button, then "Delete" danger button.

For bulk delete modal, body changes to:
"This will permanently delete **{N} {model plural}**. This cannot be undone."

---

## 13. Dashboard Page

```
┌─────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                                    │
│  Dashboard                                                      │
├─────────────────────────────────────────────────────────────────┤
│  STAT CARDS ROW                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Products │ │  Orders  │ │  Users   │ │ Revenue  │          │
│  │   1,234  │ │    42    │ │   891    │ │ $12,400  │          │
│  │  +5.2%   │ │  -2 today│ │  +12 wk  │ │ +8.4%    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
├────────────────────────────────┬────────────────────────────────┤
│  CHART (if configured)         │  RECENT ACTIVITY               │
│                                │                                │
│  [Line chart / Bar chart]      │  [Activity feed items]         │
│                                │                                │
│  60% width                     │  40% width                     │
├────────────────────────────────┴────────────────────────────────┤
│  QUICK CREATE                                                   │
│  [+ New Product] [+ New Order] [+ New User]  (model shortcuts)  │
└─────────────────────────────────────────────────────────────────┘
```

### Stat cards row

CSS Grid: `repeat(auto-fill, minmax(200px, 1fr))`, gap 16px.

Each card is `.stat-card` (see design system §13 for internal structure). Cards are
clickable — link to the relevant model list page. Hover state: `--surface-overlay`
background, `--shadow-sm`.

### Chart + activity split

`display: flex; gap: 24px`. Chart is `flex: 3`. Activity is `flex: 2`.
Below 1024px: stack vertically.

### Recent activity feed

Shows last 10 audit log entries. Each entry:

```
┌───────────────────────────────────────────────────────┐
│ [●] [User email] [action badge] [model] #[id]   [time]│
└───────────────────────────────────────────────────────┘
  height: 44px
  display: flex; align-items: center; gap: 10px
  border-bottom: 1px --surface-border (except last)
```

- Colored dot (●): `--success-500` (CREATE), `--warning-500` (UPDATE), `--danger-500`
  (DELETE). 6px diameter.
- User email: `--text-sm` `--text-secondary`.
- Action badge: compact badge variant (success/warning/danger).
- Model name: `--text-sm` `--text-primary`.
- Record ID: JetBrains Mono `--mono-accent` `--text-mono`.
- Timestamp: JetBrains Mono `--text-secondary` `--text-mono`, right-aligned,
  relative time (e.g. "3 min ago"). Tooltip: absolute datetime.

"View full audit log →" link at the bottom of the feed. `--text-sm` `--primary-500`.

### Quick create row

`display: flex; gap: 8px; flex-wrap: wrap`. Each is a secondary button with a `+`
prefix. Only models the user has `can_create` permission on are shown. Max 6 buttons;
if more, truncate to 5 + "…more" link.

---

## 14. Audit Log Page

```
┌─────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                                    │
│  Audit Log  ·  4,821 entries                                   │
├─────────────────────────────────────────────────────────────────┤
│  FILTER BAR                                                     │
│  [Model ▾]  [Action ▾]  [User ▾]  [Date range]  [Clear]       │
├───────────────────────────────────────────────────────────────  │
│  TIMELINE                                                       │
│                                                                  │
│  TODAY  ──────────────────────────────────────────────────      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ● 14:32  admin@acme.com  UPDATE  Product #1042           │   │
│  │   price: $99.99 → $149.99                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ● 14:28  admin@acme.com  CREATE  Order #2891    [expand] │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  YESTERDAY  ──────────────────────────────────────────────      │
└─────────────────────────────────────────────────────────────────┘
```

### Filter bar

Same pattern as the list page filter bar but different filter options: Model
(registered model name), Action (CREATE/UPDATE/DELETE), User (admin user selector),
Date range (date-from + date-to inputs). No search input on audit log.

### Timeline

Entries are grouped by date. Date group headers:

```
font:     --text-xs uppercase letter-spacing 0.06em --text-disabled
display:  flex; align-items: center; gap: 12px
line:     flex:1 height:1px background:--surface-border on each side
margin:   20px 0 12px
```

Each audit entry card:

```
background:     --surface-raised
border:         1px --surface-border
border-left:    3px (--success-500 CREATE / --warning-500 UPDATE / --danger-500 DELETE)
border-radius:  --radius-md
padding:        12px 16px
margin-bottom:  8px
cursor:         pointer (whole card is clickable to expand)
```

Collapsed state (one line):

```
[● color dot]  [time JetBrains Mono]  [user email]  [action badge]  [model] [id mono]
                                                                      →  right  ←
```

Expanded state (click to toggle, Alpine.js `x-show`):
Shows the diff table for UPDATE, or the full snapshot JSON for CREATE/DELETE.

**Diff table (UPDATE only):**

```
┌────────────┬──────────────────┬──────────────────┐
│ FIELD      │ BEFORE           │ AFTER            │
│ price      │ $99.99 (mono)    │ $149.99 (mono)   │  ← row highlight --warning-100
│ stock      │ 12 (mono)        │ 5 (mono)         │  ← row highlight --warning-100
└────────────┴──────────────────┴──────────────────┘
```

Changed cells highlighted in `--warning-100`. Values in JetBrains Mono.

---

## 15. Role Management Page

### Role List (`/admin/roles/`)

Same list page structure (header + table) but without search or filters.
Table columns: Name, Description, Users (count in mono), Created, Actions (Edit · Delete).
"+ New Role" primary button in page header.

### Role Edit Page (`/admin/roles/{id}`)

```
┌─────────────────────────────────────────────────────────────────┐
│  PAGE HEADER                                                    │
│  [← Roles]  Edit Role: Editor                                  │
├─────────────────────────────────────────────────────────────────┤
│  ROLE DETAILS FIELDSET                                          │
│  [Name input]     [Description textarea — full width]           │
├─────────────────────────────────────────────────────────────────┤
│  PERMISSIONS MATRIX                                             │
│                                                                 │
│  MODEL            VIEW   CREATE   EDIT   DELETE                 │
│  ─────────────────────────────────────────────────              │
│  Products          ✅     ❌       ✅      ❌     [fields ▾]    │
│    └ name          view ✅  edit ✅                             │
│    └ price         view ✅  edit ❌                             │
│  Orders            ✅     ❌       ❌      ❌                   │
│  Users             ✅     ❌       ❌      ❌                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  SAVE BAR                                                       │
│  [Delete Role]                              [Save Permissions]  │
└─────────────────────────────────────────────────────────────────┘
```

### Permissions matrix

```
background:   --surface-raised
border:       1px --surface-border
border-radius: --radius-md
overflow:     hidden
```

Header row: `--surface-overlay` background. Columns: Model (auto), View (72px),
Create (72px), Edit (72px), Delete (72px), Fields (80px).

Each model row: 44px height. Alternating background (raised / base). Each permission
cell is centered. Checkbox: 18px custom checkbox (not a toggle — toggle is too wide
for a matrix grid).

**Fields expand** — clicking the "fields ▾" button in the last column expands a
sub-section inline below the model row. Sub-section shows two columns per field:
view checkbox + edit checkbox. Sub-section has `--surface-overlay` background,
4px left indent, 1px left border `--surface-border`. Field names in `--text-sm`
JetBrains Mono.

---

## 16. Agent Chat Panel

**Position:** Fixed right side panel. Sits outside the main shell layout.
Does not affect sidebar or content area widths — it overlaps the content area.

```
.agent-panel
  position: fixed
  right: 0
  top: var(--topbar-height)      (52px)
  height: calc(100vh - 52px)
  width: 420px
  transform: translateX(100%)    (hidden default)
  transition: transform 200ms cubic-bezier(0.16,1,0.3,1)

.agent-panel--open
  transform: translateX(0)
```

Opening the panel does NOT push the content area. The panel slides over it. A subtle
`box-shadow: -4px 0 20px rgba(0,0,0,0.4)` on the left edge of the panel creates
depth separation.

### Panel internal layout

```
┌─────────────────────────────┐
│  PANEL HEADER               │  52px · --surface-overlay · border-bottom
│  [✦ Agent]   [model name]  [✕]│
├─────────────────────────────┤
│  SESSION TABS               │  36px · session history dropdown
│  [Current] [History ▾]      │
├─────────────────────────────┤
│                             │
│  CONVERSATION THREAD        │  flex:1 · overflow-y: auto · padding: 16px
│  (scrollable)               │
│                             │
├─────────────────────────────┤
│  TOOL INDICATORS            │  auto height · only visible when tools running
│  ⚙ Querying products...     │
├─────────────────────────────┤
│  INPUT AREA                 │  auto height · max ~120px · border-top
│  [textarea]       [send →]  │
│  gpt-4o                     │  --text-xs --text-disabled model label
└─────────────────────────────┘
```

### Trigger button

When the agent panel is closed, a floating trigger button appears in the bottom-right
of the content area (not the viewport — inside `.admin-content`):

```
.agent-trigger
  position: sticky
  bottom: 24px
  float: right
  width: 44px; height: 44px
  border-radius: --radius-full
  background: --primary-500
  box-shadow: --shadow-md
  display: flex; align-items: center; justify-content: center
```

Heroicons `sparkles` icon 20px in `--text-inverse`. On hover: `--primary-400`
background. Tooltip: "Ask AI".

---

## 17. Login Page

The login page is standalone — no sidebar, no topbar. Full viewport.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                                                                  │
│              ┌────────────────────────────────┐                 │
│              │  [Logo]                         │                 │
│              │  Sign in to {App Name}          │                 │
│              │  ──────────────────────────     │                 │
│              │  Email                          │                 │
│              │  [input]                        │                 │
│              │  Password                       │                 │
│              │  [input]          [show/hide]   │                 │
│              │                                 │                 │
│              │  [error message if any]         │                 │
│              │                                 │                 │
│              │  [Sign in — primary btn full]   │                 │
│              └────────────────────────────────┘                 │
│                                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
  background: --surface-base
  card: --surface-raised, --radius-lg, --shadow-lg, width: 380px
  card padding: 32px
  vertically centered: min-height: 100vh, display: flex, align-items: center, justify-content: center
```

- Logo: centered, 36px height. Falls back to app name in `--text-lg` Inter 600.
- Title: `--text-md` Inter 500 `--text-secondary`. "Sign in to" in regular weight,
  app name in `--text-primary` Inter 600.
- Error message: full-width alert box inside the card, above the Sign in button.
  `--danger-100` background, `--danger-500` border-left 3px, `--text-sm`
  `--danger-500` text. Heroicons `exclamation-circle` 14px before message.
- Sign in button: full card width. Primary variant. `md` size (36px height).
- Show/hide password: ghost icon button inside the password input, right side.
  Heroicons `eye` / `eye-slash` 16px.

---

## 18. Modals & Overlays

### Backdrop

```
position: fixed; inset: 0
background: rgba(0,0,0,0.6)
backdrop-filter: blur(2px)
z-index: 50
```

Clicking the backdrop closes the modal (except confirm-delete modals — must click
a button).

### Modal container

```
position: fixed
top: 50%; left: 50%
transform: translate(-50%, -50%)
z-index: 51
background: --surface-raised
border: 1px --surface-border
border-radius: --radius-lg
box-shadow: --shadow-lg
width: 640px (default), 480px (sm), 800px (lg)
max-height: 90vh
display: flex; flex-direction: column
```

Entrance animation: `opacity: 0 → 1` + `scale(0.97) → scale(1)`, `--duration-slow`.

### Modal header

```
padding: 20px 24px
border-bottom: 1px --surface-border
display: flex; align-items: center; justify-content: space-between
```

Title: `--text-md` Inter 600 `--text-primary`. Close button (✕): ghost sm, top-right.

### Modal body

```
padding: 20px 24px
overflow-y: auto
flex: 1
```

### Modal footer

```
padding: 12px 24px
border-top: 1px --surface-border
display: flex; justify-content: flex-end; gap: 8px
```

### Command palette (⌘K)

Special full-screen overlay variant. No card container — the palette floats
centered with a different treatment:

```
width: 560px
max-height: 60vh
background: --surface-overlay
border: 1px --surface-border
border-radius: --radius-lg
box-shadow: --shadow-lg
position: fixed; top: 20%; left: 50%; transform: translateX(-50%)
z-index: 60
```

Search input at top (44px, borderless inside the palette). Results list below.
Used for global navigation search. Separate from the model-level search in the
filter bar.

---

## 19. Responsive Behaviour

| Breakpoint | What changes |
|---|---|
| `< 1280px` | Content padding: 24px → 16px |
| `< 1024px` | Sidebar: full → icon-only (56px). Content takes full remaining width |
| `< 768px` | Sidebar: off-canvas drawer. Hamburger in topbar. Overlay backdrop. Filter bar wraps to two rows. Table: columns collapse (show only primary column + actions) |
| `< 480px` | Login card: full width with 16px padding. Modal: full width bottom sheet (slides up from bottom, `border-radius` only top). Agent panel: full width |

**Table on mobile (< 768px):** Show only the first `list_display` column + the actions
column. Other columns are hidden. A "view" row action expands to show all field values
in a stacked card below the row (not a modal).

**Form on mobile:** Grid collapses to single column. Save bar becomes full-width
buttons stacked vertically. "Save & return" first (primary), "Save & continue" second,
"Delete" third (danger outline).

---

## 20. Page Transition & Loading States

### HTMX Loading Bar

```
position: fixed; top: 0; left: 0; right: 0; height: 2px
background: --primary-500
z-index: 100
opacity: 0
transition: opacity 100ms
```

Class `.htmx-request` on `<body>` (set by HTMX) triggers `opacity: 1`. A shimmer
keyframe animation runs on the bar while it's visible.

### HTMX swap target shimmer

When HTMX is replacing `#table-wrapper` (search/filter), don't blank the table.
Apply a `.loading` class to the wrapper that reduces opacity to 0.5 with a
transition. When the swap completes, the new content appears at full opacity.
This prevents the jarring "table disappears → table reappears" effect.

### Skeleton state (initial table load)

Only on the very first page load (not on filter/sort updates). Eight skeleton rows:
each 40px tall. Skeleton cells: `--surface-overlay` background, `--radius-sm`,
varying widths per column type. Shimmer animation: a gradient that moves left-to-right
over each skeleton cell on a 1.5s loop.

---

## 21. Component Placement Rules (Summary)

A quick reference for where each component belongs on each page type.

| Component | List page | Create page | Edit page | Dashboard | Audit Log | Roles |
|---|---|---|---|---|---|---|
| Page header | ✅ top | ✅ top | ✅ top | ✅ top | ✅ top | ✅ top |
| Back link | ❌ | ✅ in header | ✅ in header | ❌ | ❌ | ✅ in header |
| Primary action btn | ✅ header right | ❌ | ❌ | ❌ | ❌ | ✅ header right |
| Search input | ✅ filter bar | ❌ | ❌ | ❌ | ❌ | ❌ |
| Filter chips | ✅ filter bar | ❌ | ❌ | ❌ | ✅ filter bar | ❌ |
| Export btn | ✅ filter bar right | ❌ | ❌ | ❌ | ❌ | ❌ |
| Table | ✅ below filter bar | ❌ | ❌ | ❌ | ❌ | ✅ role list |
| Bulk action bar | ✅ replaces filter bar | ❌ | ❌ | ❌ | ❌ | ❌ |
| Pagination | ✅ below table | ❌ | ❌ | ❌ | ✅ | ✅ |
| Fieldsets | ❌ | ✅ form body | ✅ form body | ❌ | ❌ | ✅ |
| Save bar | ❌ | ✅ sticky bottom | ✅ sticky bottom | ❌ | ❌ | ✅ sticky bottom |
| Delete btn | in row actions | ❌ | ✅ save bar left | ❌ | ❌ | ✅ save bar left |
| History section | ❌ | ❌ | ✅ after fieldsets | ❌ | ❌ | ❌ |
| Stat cards | ❌ | ❌ | ❌ | ✅ below header | ❌ | ❌ |
| Chart | ❌ | ❌ | ❌ | ✅ below stat cards | ❌ | ❌ |
| Activity feed | ❌ | ❌ | ❌ | ✅ beside chart | ❌ | ❌ |
| Permission matrix | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ role edit |
| Flash toasts | ✅ top-right | ✅ top-right | ✅ top-right | ✅ top-right | ✅ top-right | ✅ top-right |
| Agent trigger btn | ✅ sticky bottom-right | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent panel | overlay right | overlay right | overlay right | overlay right | overlay right | overlay right |