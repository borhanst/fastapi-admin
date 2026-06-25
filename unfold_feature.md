# Plan: Add UnfoldAdmin Features + Improve Existing Code

## Phase 1: Custom Actions System + Improved Filters
**Goal:** Replace the minimal action system with a full Unfold-style action system and upgrade filters.

### 1A. Custom Actions
**Files to modify:**
- `fastapi_admin/actions/base.py` — Expand `Action` ABC with `icon`, `variant`, `permissions`, `location` (list/detail/row/submit)
- `fastapi_admin/actions/__init__.py` — Add `@action` decorator (like Unfold's `@action(description=, icon=, variant=, permissions=)`)
- `fastapi_admin/modeladmin.py` — Add `actions_list`, `actions_row`, `actions_detail`, `actions_submit_line`, `actions_list_hide_default` attributes
- `fastapi_admin/views/factory.py` — Add `create_row_action_view()`, `create_detail_action_view()`, `create_submit_action_view()` methods
- `fastapi_admin/views/context.py` — Pass row actions + list actions into list template context
- `fastapi_admin/router.py` — Register action routes: `/{model}/action/{action_name}/{id}` for row/detail, `/{model}/action/{action_name}` for list-level
- `templates/pages/list.html` — Render action buttons above table (list actions) and per-row (row actions) with icons and color variants
- `templates/pages/form.html` — Render detail actions at top, submit-line actions at bottom near save

### 1B. Improved Filters
**Files to modify:**
- `fastapi_admin/filters/base.py` — Add `NumericFilter` (gte/lte), `DateRangeFilter` (from/to), `DatetimeRangeFilter`, `AutocompleteFilter`
- `fastapi_admin/modeladmin.py` — Add `list_filter_options` dict (label overrides, horizontal mode) matching Unfold's pattern
- `fastapi_admin/views/context.py` — Support range filter params (`filter_field__gte`, `filter_field__lte`) in `build_list_context`
- `templates/pages/list.html` — Render date/datetime as range (from/to inputs), numeric as range, horizontal layout option

---

## Phase 2: Changelist Tabs + Expandable Sections + Sortable
**Goal:** Add tab navigation, expandable rows, and drag-and-drop sorting.

### 2A. Changelist Tabs
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `list_tabs: list[TabConfig]` attribute
- `fastapi_admin/types.py` — Add `TabConfig` dataclass (`title`, `url`, `permission`)
- `templates/pages/list.html` — Render tab bar above the table, active tab highlighting
- `templates/partials/tabs.html` — New partial template for tab rendering

### 2B. Expandable Sections (list_sections)
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `list_sections: list` attribute
- `fastapi_admin/types.py` — Add `TableSection`, `TemplateSection` base classes
- `fastapi_admin/views/context.py` — Build section context for each list item
- `templates/pages/list.html` — Add expand/collapse button per row, section content area with HTMX lazy-load
- New `templates/partials/section_table.html` — Render section table content
- New `templates/partials/section_template.html` — Render custom template sections

### 2C. Sortable Changelist
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `ordering_field: str | None`, `hide_ordering_field: bool = False`
- `fastapi_admin/router.py` — Add `POST /{model}/sort` endpoint for drag-drop updates
- `templates/pages/list.html` — Add drag handles, SortableJS CDN, sortable row behavior
- `fastapi_admin/static/js/admin.js` — Initialize SortableJS when ordering_field is set

---

## Phase 3: Conditional Fields + Form Improvements
**Goal:** Add smart form features from Unfold.

### 3A. Conditional Fields
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `conditional_fields: dict[str, dict]` (field_name → {show_when: field, values: [...]})
- `templates/pages/form.html` — Add Alpine.js x-show/x-if logic per conditional field
- `templates/macros/form_fields.html` — Wrap conditional fields with Alpine.js data binding

### 3B. Form UX Improvements
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `warn_unsaved_form: bool = True`, `compressed_fields: bool = True`, `change_form_show_cancel_button: bool = True`
- `templates/pages/form.html` — Add `beforeunload` event listener for unsaved changes warning, compressed layout mode, cancel button toggle
- `fastapi_admin/views/context.py` — Pass new config flags to form template context

---

## Phase 4: UI/Config Enhancements + Sidebar Fix
**Goal:** Add missing Unfold config options and fix sidebar to use nav_groups.

### 4A. UIConfig Upgrades
**Files to modify:**
- `fastapi_admin/config/ui.py` — Add: `site_url`, `site_symbol`, `show_history`, `show_view_on_site`, `show_back_button`, `environment`, `environment_callback`, `custom_styles: list`, `custom_scripts: list`, `border_radius`
- `fastapi_admin/admin/core.py` — Wire new UIConfig options to template context, support custom styles/scripts loading in base.html
- `templates/base.html` — Load custom CSS/JS from config, render environment label in header, optional border-radius override

### 4B. Topbar Enhancements
**Files to modify:**
- `templates/partials/topbar.html` — Add: environment label badge, site dropdown, "View on site" link, "History" link, "Back" button on changeform
- `fastapi_admin/admin/admin_template.py` — Pass new config flags to topbar context

### 4C. Sidebar Fix — Use nav_groups
**Files to modify:**
- `templates/partials/sidebar.html` — **Rewrite** to use `nav_groups` (BuiltNavGroup/BuiltNavItem) instead of `registered_models`. Support: collapsible groups, icons, badges, nested children, permission filtering, group labels
- `fastapi_admin/views/sidebar.py` — Ensure inject_sidebar_context passes built nav_groups

### 4D. Dashboard Improvements
**Files to modify:**
- `fastapi_admin/config/behavior.py` — Add `dashboard_callback: str | None` (dotted path to callback function)
- `fastapi_admin/views/dashboard.py` — Call dashboard_callback if configured, support custom data injection
- `fastapi_admin/config/nav.py` — Add site_dropdown config

---

## Phase 5: Advanced Widgets + Autocomplete
**Goal:** Add rich widget types.

### 5A. WysiwygWidget
**Files to modify:**
- `fastapi_admin/widgets/inputs.py` — Add `WysiwygWidget` class (macro_name: "wysiwyg")
- `templates/macros/form_fields.html` — Add `wysiwyg` macro with Quill.js or TinyMCE integration
- `templates/base.html` — Load Wysiwyg CSS/JS (e.g. Quill CDN)

### 5B. ArrayWidget
**Files to modify:**
- `fastapi_admin/widgets/inputs.py` — Add `ArrayWidget` class (macro_name: "array_input")
- `templates/macros/form_fields.html` — Add `array_input` macro with dynamic add/remove items

### 5C. Autocomplete Fields
**Files to modify:**
- `fastapi_admin/widgets/relation.py` — Upgrade `RelationPickerWidget` to support autocomplete search
- `fastapi_admin/router.py` — Add `GET /{model}/autocomplete/?q=...` endpoint for search-as-you-type
- `templates/macros/form_fields.html` — Render relation picker with HTMX-powered autocomplete dropdown

---

## Phase 6: Dashboard Components + Final Polish
**Goal:** Add Unfold-style dashboard component system.

### 6A. Dashboard Components
**Files to modify:**
- New `fastapi_admin/dashboard/components.py` — Component classes: `CardComponent`, `ChartComponent`, `TableComponent`, `ProgressComponent`, `LinkComponent`, `ButtonComponent`
- New `fastapi_admin/dashboard/registry.py` — Component registry for dashboard
- `templates/pages/dashboard.html` — Render components in grid layout
- New `templates/partials/components/` — Individual component templates (card.html, chart.html, table.html, progress.html)
- `fastapi_admin/config/behavior.py` — Add `dashboard_components: list` config

### 6B. Sortable Inlines (if time permits)
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `sortable_inline_field: str | None` for inline ordering
- `templates/macros/form_fields.html` — Add drag handles to inline rows

### 6C. Final Improvements
**Files to modify:**
- `fastapi_admin/modeladmin.py` — Add `readonly_preprocess_fields: dict` (Unfold feature for preprocessing readonly field display)
- `templates/pages/list.html` — Fix column picker dropdown (currently button exists but no panel), add record count display
- `fastapi_admin/views/context.py` — Support custom `list_display` callables (like Unfold's @display decorator)

---

## Verification Plan

1. **After Phase 1:** Run `pytest` — ensure all existing tests pass. Manually verify actions appear in list view and detail view. Test filter range inputs.
2. **After Phase 2:** Verify tabs render in list view. Test expandable sections show related data. Test drag-and-drop sorting persists order.
3. **After Phase 3:** Test conditional fields toggle visibility. Test unsaved changes warning on form navigation.
4. **After Phase 4:** Verify sidebar uses nav_groups with proper grouping. Check custom styles/scripts load. Verify environment label displays. Check "View on site" link works.
5. **After Phase 5:** Test Wysiwyg editor loads and saves rich text. Test array widget add/remove. Test autocomplete search on foreign key fields.
6. **After Phase 6:** Verify dashboard components render with sample data. Run full test suite.

**Commands to run after each phase:**
```bash
cd /home/borhan/Desktop/test/fastapi-admin
python -m pytest tests/ -v
ruff check fastapi_admin/
```

---

## Implementation Order Summary

| Phase | Features | Est. Files Modified | Priority |
|-------|----------|-------------------|----------|
| 1 | Actions + Filters | 8 files | Critical |
| 2 | Tabs + Sections + Sortable | 7 files | High |
| 3 | Conditional Fields + Form UX | 4 files | High |
| 4 | UI Config + Sidebar Fix + Dashboard | 7 files | Medium |
| 5 | Wysiwyg + Array + Autocomplete | 5 files | Medium |
| 6 | Dashboard Components + Polish | 8 files | Lower |
