# FastAPI Admin — Build Phases 1-5 Todo

## Phase 1 — Project Scaffold & Dependencies

**References:** `fastapi_admin_core_spec.md` §5 (Project Folder Structure), §6 (Tech Stack Summary)

- [x] 1.1 Create `fastapi_admin/` package with `__init__.py`
- [x] 1.2 Create subdirectory stubs: `auth/`, `audit/`, `widgets/`, `views/`, `filters/`, `actions/`, `storage/`, `plugins/`, `dashboard/`, `nav/`, `form/`
- [x] 1.3 Create `pyproject.toml` with all dependencies
- [x] 1.4 Create `requirements-dev.txt`
- [x] 1.5 Create `fastapi_admin/models/base.py` with SQLAlchemy Base
- [x] 1.6 Create `static/` directory (`css/`, `js/`, `icons/`)
- [x] 1.7 Create `templates/` directory (`pages/`, `partials/`, `macros/`)
- [x] 1.8 Verify package importable with `python -c "import fastapi_admin"`

---

## Phase 2 — Core Data Structures (ColumnMeta, RelationMeta, FieldMeta)

**References:** `fastapi_admin_core_spec.md` §1.4, `FORM_WIDGET_SYSTEM.md` §2

- [x] 2.1 Create `fastapi_admin/types.py`
- [x] 2.2 Define `ColumnMeta` dataclass
- [x] 2.3 Define `RelationMeta` dataclass
- [x] 2.4 Define `FieldMeta` dataclass
- [x] 2.5 Define `PermissionSet` dataclass
- [x] 2.6 Define `FieldsetSpec` dataclass
- [x] 2.7 Re-export all from `fastapi_admin/__init__.py`

---

## Phase 3 — Model Inspection

**References:** `fastapi_admin_core_spec.md` §1.4, `FORM_WIDGET_SYSTEM.md` §5

- [x] 3.1 Create `fastapi_admin/inspection.py`
- [x] 3.2 Implement `inspect_model()` function
- [x] 3.3 Implement `is_abstract()` function
- [x] 3.4 Implement `get_pk_field()` function
- [x] 3.5 Implement `auto_label()` function
- [x] 3.6 Implement `is_required()` function
- [x] 3.7 Write tests in `tests/test_inspection.py`

---

## Phase 4 — Widget Registry & Built-in Widgets

**References:** `FORM_WIDGET_SYSTEM.md` §2, §3, §6, §10

- [x] 4.1 Create `fastapi_admin/widgets/base.py` with Widget ABC
- [x] 4.2 Create `fastapi_admin/widgets/inputs.py` with all built-in widgets
- [x] 4.3 Create `fastapi_admin/widgets/relation.py`
- [x] 4.4 Create `fastapi_admin/widgets/registry.py` with WidgetRegistry
- [x] 4.5 Export everything from `widgets/__init__.py`
- [x] 4.6 Write tests in `tests/test_widgets.py`

---

## Phase 5 — ModelAdmin Base Class & Registry

**References:** `fastapi_admin_core_spec.md` §1.2, §1.3

- [x] 5.1 Create `fastapi_admin/modeladmin.py` with ModelAdmin base class
- [x] 5.2 Add stub lifecycle hooks to ModelAdmin
- [x] 5.3 Add stub validation methods to ModelAdmin
- [x] 5.4 Create `fastapi_admin/registry.py` with AdminRegistry
- [x] 5.5 Define `RegisteredModel` dataclass
- [x] 5.6 Implement `@admin.register` decorator pattern
- [x] 5.7 Write tests in `tests/test_registry.py`

---

## Phase 6 — Database Models (Admin Tables)

**References:** `AUTH_RBAC_SYSTEM.md` §2, §7, `fastapi_admin_core_spec.md` §2A.1

- [x] 6.1 Create `fastapi_admin/auth/models.py` with `AdminRole`, `AdminUser`, `AdminPermission`, `AdminFieldPermission`
- [x] 6.2 Define `AdminUser` fields: `id`, `email` (unique), `hashed_password`, `full_name`, `role_id` (FK), `is_superuser`, `is_active`, `last_login`, `created_at`
- [x] 6.3 Add unique constraint on `AdminPermission(role_id, table_name)`
- [x] 6.4 Add unique constraint on `AdminFieldPermission(role_id, table_name, field_name)`
- [x] 6.5 Create `fastapi_admin/audit/models.py` with `AuditLog` model and indexes
- [x] 6.6 Create `fastapi_admin/auth/protocol.py` with `AdminUserProtocol`
- [x] 6.7 Create `fastapi_admin/models/__init__.py` re-exporting all admin models
- [x] 6.8 Write tests in `tests/test_models.py` (table creation + protocol check)

---

## Phase 7 — Auth Backend & Session

**References:** `AUTH_RBAC_SYSTEM.md` §5, §15

- [x] 7.1 Create `fastapi_admin/auth/session.py` with `SessionBackend` ABC
- [x] 7.2 Implement `SignedCookieSessionBackend` using `itsdangerous.TimestampSigner`
- [x] 7.3 Create `fastapi_admin/auth/backend.py` with `AuthBackend` ABC
- [x] 7.4 Implement `BuiltinAuthBackend` using bcrypt via passlib
- [x] 7.5 Create `fastapi_admin/auth/dependencies.py` with `get_session`, `get_current_admin_user`, `get_permission_checker`, `require_permission`
- [x] 7.6 Wire `auth_backend` and `session_backend` to `request.app.state`
- [x] 7.7 Write tests in `tests/test_auth.py` (session round-trip, auth backend)

---

## Phase 8 — RBAC Permission Checker

**References:** `AUTH_RBAC_SYSTEM.md` §8

- [x] 8.1 Create `fastapi_admin/auth/permissions.py` with `PermissionChecker`
- [x] 8.2 Implement `has_permission(table_name, action)` with superuser bypass and caching
- [x] 8.3 Implement `get_allowed_fields(table_name, mode)` with None/empty-set semantics
- [x] 8.4 Implement `permission_set(table_name)` returning `PermissionSet`
- [x] 8.5 Write tests in `tests/test_permissions.py` (superuser, no role, caching)

---

## Phase 9 — Admin Class & Startup Wiring

**References:** `AUTH_RBAC_SYSTEM.md` §17, `fastapi_admin_core_spec.md` §3.12

- [x] 9.1 Create `fastapi_admin/admin.py` with `Admin` class
- [x] 9.2 Implement `Admin.setup()` (async): create tables, seed roles, mount static, init Jinja2
- [x] 9.3 Implement `Admin.register(model, admin_class=None)` decorator pattern
- [x] 9.4 Implement `Admin._build_router()` mounting all model routers
- [x] 9.5 Implement `Admin.lifespan(app)` context manager
- [x] 9.6 Validate `auth_model` satisfies `AdminUserProtocol` at startup
- [x] 9.7 Write tests in `tests/test_admin.py` (construct, setup, default roles, auto_discover)

---

## Phase 10 — Auth Routes (Login / Logout)

**References:** `AUTH_RBAC_SYSTEM.md` §15

- [x] 10.2 GET login renders `pages/login.html`, redirects if already authenticated
- [x] 10.3 POST login reads `email`/`password` from form, calls `auth_backend.authenticate`, sets signed session cookie, updates `last_login`, redirects to `?next=` or `/admin/`
- [x] 10.4 POST login failure re-renders login with flash error message
- [ ] 10.1 Create `fastapi_admin/auth/views.py` with GET `/admin/login`, POST `/admin/login`, POST `/admin/logout` handlers
- [x] 10.5 Validate `next` query param is relative URL only (prevent open redirect)
- [x] 10.6 POST logout deletes session cookie, calls `auth_backend.on_logout`, redirects to `/admin/login`
- [x] 10.7 Create `fastapi_admin/auth/router.py` mounting three handlers on `APIRouter(prefix="/admin")`
- [ ] 10.8 Write tests in `tests/test_auth_routes.py`: successful login sets cookie, wrong password re-renders with error, logout deletes cookie, `next` redirect works, open redirect is blocked

---

## Phase 11 — Audit Log Capture

**References:** `fastapi_admin_core_spec.md` §2A.2, §2A.4

- [X] 11.1 Create `fastapi_admin/audit/context.py` with `ContextVar` `_current_audit_context`
- [X] 11.2 Implement `get_audit_context()`, `set_audit_context(data)` functions
- [X] 11.3 Implement `audit_context_middleware` — reads `request.state.admin_user`, sets ContextVar with user/ip/user_agent, resets after response
- [X] 11.4 Create `fastapi_admin/audit/diff.py` with `snapshot(obj)` — serialises all mapper columns
- [X] 11.5 Implement `serialize_value(val)` — handles datetime, Decimal, UUID, bytes, Enum
- [X] 11.6 Implement `compute_diff(before, after)` — returns changed fields only with before/after
- [X] 11.7 Create `fastapi_admin/audit/listener.py` with `attach_audit_listener(session_factory, registry)`
- [X] 11.8 Implement `before_flush` listener — snapshots dirty objects to `obj._audit_before`
- [X] 11.9 Implement `after_flush` listener — writes `AuditLog` rows for create/update/delete on registered models
- [X] 11.10 `write_audit` must skip UPDATE if `compute_diff` returns empty dict
- [X] 11.11 Implement `is_registered_model(obj, registry)` check
- [ ] 11.12 Write tests in `tests/test_audit.py`: create → audit CREATE, update → diff captured, delete → audit DELETE, unchanged update → no audit row

---

## Phase 12 — Form Pipeline & Route Factories

**References:** `FORM_WIDGET_SYSTEM.md` §7, §8, §14

- [x] 12.1 Create `fastapi_admin/form/pipeline.py` with `build_form_context(registered, obj, values, errors, request)`
- [x] 12.2 Determine field order: respect `fields`, `exclude`, auto-order; skip PK on create (HiddenWidget), readonly on edit
- [x] 12.3 Mark `readonly_fields` as `ReadOnlyWidget`, add `extra_fields`, apply `get_widget_for_field` override
- [x] 12.4 Call `widget.render_context()` for each field, group into `FieldsetContext` blocks
- [x] 12.5 Create `fastapi_admin/validation.py` with `FormValidator.run(registered, parsed, obj)`
- [x] 12.6 Implement Level 1 (widget validate), Level 2 (`validate_{field_name}`), Level 3 (`validate`); detect async validators
- [x] 12.7 Create `fastapi_admin/views/list.py` — `list_view_factory(registered)`: search, filter, order, paginate, render `pages/list.html`
- [x] 12.8 Create `fastapi_admin/views/form.py` — `create_form_factory`, `create_submit_factory`, `edit_form_factory`, `edit_submit_factory`: parse, validate, lifecycle hooks, commit, flash, redirect
- [x] 12.9 Create `fastapi_admin/views/delete.py` — `delete_factory`: call `on_delete`, delete, `after_delete`, flash, redirect
- [x] 12.10 Create `fastapi_admin/views/bulk.py` — `bulk_factory`: reads `action`/`ids[]`, routes to `action_{name}` or built-in `delete_selected`
- [x] 12.11 Create `fastapi_admin/router.py` — `build_model_router(registered)`: mounts list, create GET/POST, edit GET/POST, delete, bulk, search, validate-field with `require_permission` dependencies
- [ ] 12.12 Write tests in `tests/test_routes.py`: list 200, create valid redirect, create invalid 422 with errors, edit updates, delete removes, RBAC 403

---

## Phase 13 — Audit Log & Role Management Routes

**References:** `AUTH_RBAC_SYSTEM.md` §14

- [x] 13.1 Create `fastapi_admin/views/audit.py` — `audit_list_view`: query `AuditLog` with filters (model, user_id, action, from, to, object_id), paginate, render `pages/audit_log.html`
- [x] 13.2 Implement `audit_detail_view` — load single entry, render diff/snapshot in `pages/audit_detail.html`
- [x] 13.3 Create `fastapi_admin/views/roles.py` — `GET /admin/roles/`: list roles with user counts
- [x] 13.4 `GET /admin/roles/create`: empty role form
- [x] 13.5 `GET /admin/roles/{id}`: edit form with permission matrix (one row per model, four checkboxes, expandable field-level)
- [x] 13.6 `POST /admin/roles/{id}`: parse `perm[{table}][{action}]` and `field_perm[{table}][{field}][{mode}]`, upsert `AdminPermission` and `AdminFieldPermission` rows
- [x] 13.7 `POST /admin/roles/{id}/delete`: delete role (refuse if users assigned, or set NULL per config)
- [x] 13.8 All role routes require `is_superuser=True` via `require_superuser` dependency
- [x] 13.9 Write tests in `tests/test_role_routes.py`: list, create, save permission matrix, verify DB rows

---

## Phase 14 — Flash Messages & Dashboard

**References:** `fastapi_admin_core_spec.md` §3.12

- [x] 14.1 Create `fastapi_admin/flash.py` — `add_flash(request, level, message)`: appends to signed session cookie key `admin_flash`
- [x] 14.2 Implement `get_flash_messages(request)`: reads and clears flash cookie, returns `[{level, text}]`
- [x] 14.3 Levels: `success`, `error`, `warning`, `info`
- [x] 14.4 Create `fastapi_admin/views/dashboard.py` — query record counts for top models, fetch last 10 audit entries
- [x] 14.5 Respect `dashboard_stat_cards` and `dashboard_charts` config from `Admin()` init
- [x] 14.6 Built-in fallback: show record count for each registered model
- [x] 14.7 Render `pages/dashboard.html` with stat cards, recent activity, quick-create links
- [x] 14.8 Write tests in `tests/test_dashboard.py`: dashboard 200, stat counts correct, recent activity shows audit entries

---

## Phase 15 — Jinja2 Templates (Structure & Base)

**References:** `fastapi_admin_core_spec.md` §3.4, §3.5, §3.6

- [x] 15.1 Create `templates/base.html` — two-column layout (sidebar 256px, topbar 64px, scrollable content), include Tailwind CSS (CDN), HTMX, Alpine.js, Heroicons sprite, Inter font
- [x] 15.2 Inject `extra_css` and `extra_js` from `admin_config`
- [x] 15.3 Add `{% block content %}` and `{% block head_extra %}`
- [x] 15.4 Create `templates/partials/sidebar.html` — nav links for registered models (only where `perm.can_view` is True), Audit Log, Roles sections, active link highlight, collapse to icons below 1024px
- [x] 15.5 Create `templates/partials/topbar.html` — breadcrumb, dark mode toggle (Alpine.js), user menu dropdown (name, logout link)
- [x] 15.6 Create `templates/partials/flash_messages.html` — toast notifications using Alpine.js `x-show` with auto-dismiss after 4 seconds
- [x] 15.7 Create `templates/partials/pagination.html` — reusable prev/next and page number links
- [x] 15.8 Create `templates/pages/login.html` — standalone (no sidebar), email + password form, brand logo, error message display
- [x] 15.9 Create `templates/pages/dashboard.html` — stat cards row, recent activity feed, quick-create links
- [x] 15.10 Create `templates/pages/list.html` — search input with HTMX, filter dropdowns, sortable headers, bulk-select checkboxes, Edit/Delete per-row actions (conditional on permissions), empty state, pagination
- [x] 15.11 Create `templates/pages/form.html` — fieldset sections (collapsible with Alpine.js), sticky save bar, Delete button (edit only, if `can_delete`), unsaved-changes warning
- [x] 15.12 Create `templates/pages/audit_log.html` and `templates/pages/audit_detail.html` — timeline feed, color-coded action badges, expandable diff view
- [x] 15.13 Create `templates/pages/roles.html` and `templates/pages/role_form.html` — permission matrix table with checkboxes, collapsible field-level sections
- [x] 15.14 All templates must use CSS variables from `variables.css` — no hardcoded hex values

---

## Phase 16 — Form Field Macros

**References:** `FORM_WIDGET_SYSTEM.md` §4, §11, §15

- [x] 16.1 Create `templates/macros/form_fields.html` — `render_field(field_ctx, model_name)` dispatcher macro
- [x] 16.2 Implement each widget macro from the dispatcher: text_input, textarea, number_input, toggle, select, date_picker, datetime_picker, time_picker, json_editor, password, read_only, hidden, email_input, url_input, phone_input, color_picker, slug, image_upload, file_upload, tag_input, relation_picker, multi_relation
- [x] 16.3 Each macro wraps in `<div class="field-wrapper" id="field-wrapper-{name}">`, renders label, input, errors, help text
- [x] 16.4 All text-like inputs add HTMX blur-validation attributes to `/admin/{model_name}/validate-field`
- [x] 16.5 Toggle macro: styled toggle switch (hidden checkbox + CSS), not plain checkbox
- [x] 16.6 Relation picker macro: Alpine.js with hidden FK input + search input fetching from `/admin/{related_table}/search`
- [x] 16.7 Multi-relation macro: tag chips with remove buttons + search input
- [x] 16.8 JSON editor macro: textarea fallback + CodeMirror 6 init script block
- [x] 16.9 Image upload macro: Alpine.js `imageUpload()` for client-side preview
- [x] 16.10 Create `templates/macros/table.html` — `table_header(columns, ordering)`, `table_row(obj, columns, permissions)`, `table_cell(value, column)`
- [x] 16.11 Create `templates/macros/icons.html` — `icon(name, class="")` macro rendering SVG from Heroicons sprite

---

## Phase 17 — Static Assets

**References:** `fastapi_admin_core_spec.md` §3.2

- [x] 17.1 Create `static/css/variables.css` — CSS custom properties: primary colour scale, neutral greys, semantic colours (success, warning, danger, info), layout dimensions, `[data-theme="dark"]` block
- [x] 17.2 Create `static/css/admin.css` — component styles using CSS variables: `.form-input`, `.form-select`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-sm`, `.field-wrapper`, `.field-label`, `.field-errors`, `.field-help`, `.required-star`, `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger`, `.toggle-switch`, `.toast`, `.nav-link`, `.sidebar`, `.topbar`, `.table-wrapper`, `.tag-chip`, `.relation-picker-dropdown`
- [x] 17.3 Create `static/js/admin.js` — Alpine.js `theme` store (dark mode, reads/writes localStorage, sets `data-theme`), `relationPicker()` component, `multiRelation()` component, `slugWidget()` component, `imageUpload()` component, `jsonEditor()` CodeMirror init
- [x] 17.4 Create `static/js/htmx-config.js` — set `htmx.config.defaultSwapStyle = "outerHTML"`, add `htmx:configRequest` listener for CSRF/HTMX header injection
- [x] 17.5 Create `static/icons/heroicons.svg` — SVG sprite with `<symbol>` definitions: home, users, document-text, chart-bar, cog-6-tooth, arrow-up-tray, trash, pencil, plus, magnifying-glass, chevron-left, chevron-right, moon, sun, x-mark, check, exclamation-triangle, information-circle, clock, archive-box, truck, currency-dollar
- [x] 17.6 Mount `static/` directory in admin's FastAPI app using `StaticFiles`

---

## Phase 18 — Relation Search Endpoint

**References:** `FORM_WIDGET_SYSTEM.md` §15

- [x] 18.1 Add `GET /admin/{table_name}/search` route to each model's router in `fastapi_admin/router.py`
- [x] 18.2 Accept `?q=` (search term) and `?limit=` (default 20) query params
- [x] 18.3 Call `ModelAdmin.get_queryset` for base queryset, search across `search_fields` (fallback to first String column)
- [x] 18.4 Return JSON `[{id: "...", label: "..."}]` where label is from `ModelAdmin.__str__(obj)`
- [x] 18.5 Protect route with `require_permission(table_name, "view")`
- [x] 18.6 Handle self-referential FK: exclude object via `exclude_id` query param
- [x] 18.7 Write tests in `tests/test_search.py`: search returns results, empty query returns first N, `exclude_id` works, unauthorized returns 403

---

## Phase 19 — File Upload & Storage

**References:** `PLUGIN_SYSTEM.md` §12.1, `FORM_WIDGET_SYSTEM.md` §11

- [x] 19.1 Create `fastapi_admin/storage/base.py` with `StorageBackend` ABC (save, delete, url, sanitize_filename)
- [x] 19.2 Create `fastapi_admin/storage/local.py` with `LocalStorageBackend` — saves to local directory, serves via mounted `StaticFiles`
- [x] 19.3 `sanitize_filename` must prepend UUID prefix, strip path separators
- [x] 19.4 Update `fastapi_admin/views/form.py` to handle file fields: detect `FileUploadWidget`/`ImageUploadWidget`, handle keep/replace/clear actions
- [x] 19.5 Add `max_size_mb` validation to `FileUploadWidget`
- [x] 19.6 Write tests in `tests/test_storage.py`: save returns path, url returns correct URL, delete removes file, oversized file rejected

---

## Phase 20 — CSS Design Tokens & Variables

**References:** `ui_design_system.md` §1 (Shell Layout), `UI_DESIGN_SYSTEM.md` tokens

- [x] 20.1 Create `static/css/tokens.css` — all CSS custom properties: colour scales (primary, success, warning, danger, info), neutral greys, surface colours (`--surface-base`, `--surface-raised`, `--surface-overlay`, `--surface-border`), text colours (`--text-primary`, `--text-secondary`, `--text-disabled`, `--text-inverse`, `--mono-accent`)
- [x] 20.2 Define layout dimension tokens: `--topbar-height: 52px`, `--sidebar-width: 240px`, `--sidebar-collapsed-width: 56px`, `--content-padding: 24px`, `--form-max-width: 860px`
- [x] 20.3 Define radius tokens: `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full`
- [x] 20.4 Define shadow tokens: `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- [x] 20.5 Define typography tokens: `--text-xs`, `--text-sm`, `--text-base`, `--text-md`, `--text-lg`; font families (Inter, JetBrains Mono); font weights (400, 500, 600)
- [x] 20.6 Define duration tokens: `--duration-fast`, `--duration-base`, `--duration-slow`
- [x] 20.7 Add `[data-theme="dark"]` block overriding all surface/text/colour tokens for dark mode
- [x] 20.8 Verify existing `variables.css` is replaced/consolidated into `tokens.css` — single source of truth

---

## Phase 21 — Shell Layout (Topbar + Sidebar + Content Area)

**References:** `ui_design_system.md` §1, §2, §3, §4

- [x] 21.1 Update `templates/base.html` — implement `.admin-shell` (`display: flex; flex-direction: column; height: 100vh`), `.admin-topbar` (52px, `flex-shrink: 0`), `.admin-body` (`display: flex; flex: 1; overflow: hidden`)
- [x] 21.2 Implement `.admin-sidebar` — 240px fixed width, `overflow-y: auto`, `--surface-raised` background, right border
- [x] 21.3 Implement `.admin-content` — `flex: 1; overflow-y: auto; padding: 24px`, inner wrapper `max-width: 1320px; margin: 0 auto`
- [x] 21.4 Implement topbar left zone — collapse toggle (≡) 36px ghost icon, logo 28px tall, vertical divider
- [x] 21.5 Implement topbar center zone — breadcrumb `--text-sm`, separators in `--text-disabled`, last segment `--text-secondary`
- [x] 21.6 Implement topbar right zone — search trigger (⌘K badge), theme toggle, user avatar dropdown (28px circle, initials fallback)
- [x] 21.7 Implement user avatar dropdown — user name header, role badge, Profile link, Sign out button (danger text)
- [x] 21.8 Implement topbar loading bar — 2px `--primary-500` bar at very top during HTMX requests
- [x] 21.9 Update sidebar nav sections: unlabelled (Dashboard), MODELS (registered models with record count badges), SYSTEM (Audit Log, Roles, Agent, API Keys), BOTTOM (Settings, `margin-top: auto`)
- [x] 21.10 Implement nav item anatomy — 36px height, icon 16px, label `--text-sm`, badge `--text-mono-sm`, active state (`--primary-100` bg, `--primary-500` text, 2px left border), hover `--surface-overlay`
- [x] 21.11 Implement section labels — `--text-xs` uppercase, `--text-disabled`, 0.06em letter-spacing
- [x] 21.12 Write tests / visual verification for shell layout rendering

---

## Phase 22 — Collapsed Sidebar & Responsive Sidebar

**References:** `ui_design_system.md` §3 (collapsed sidebar), §19 (responsive)

- [x] 22.1 Implement collapsed sidebar state — width 56px, labels hidden, icons centered
- [x] 22.2 Implement nav icon tooltip on hover — `--surface-overlay` bg, `--shadow-md`, positioned `left: 64px`, `--text-sm`
- [x] 22.3 Active indicator in collapsed mode — 3px left border `--primary-500` only
- [x] 22.4 Implement sidebar collapse toggle — persists state in `localStorage`, animated width transition
- [x] 22.5 Mobile sidebar (< 768px) — off-canvas drawer with hamburger in topbar, overlay backdrop (`rgba(0,0,0,0.6)`), slide-in transition
- [x] 22.6 Breakpoint `< 1024px` — sidebar auto-collapses to icon-only
- [x] 22.7 Breakpoint `< 1280px` — content padding reduces to 16px

---

## Phase 23 — Page Header Component

**References:** `ui_design_system.md` §4 (page header)

- [x] 23.1 Implement `.page-header` component — title `--text-lg` Inter 600, optional subtitle `--text-sm` secondary
- [x] 23.2 Implement primary action button placement — top-right, only one per page (list pages: "+ New {Model}", edit pages: none)
- [x] 23.3 Implement form page header — back link `← {Model plural}` ghost text, title "New/Edit {Model}", subtitle with object repr + ID (JetBrains Mono for ID), History link on edit pages
- [x] 23.4 Ensure header is NOT sticky — scrolls with content
- [x] 23.5 Update all page templates to use the new `.page-header` component consistently

---

## Phase 24 — List Page: Search & Filter Bar

**References:** `ui_design_system.md` §6

- [x] 24.1 Implement search & filter bar container — sticky below page header (`position: sticky; top: 0; z-index: 10`), 48px height, flex layout with gap 8px
- [x] 24.2 Implement search input — `flex: 1`, max 360px, 34px height, magnifying-glass icon 14px, placeholder in `--text-disabled`, clear button (✕) when active
- [x] 24.3 Implement filter chips — 34px height, 1px border, `--radius-sm`, inactive: `--surface-raised` bg / `--text-secondary`, active: `--primary-100` bg / `--text-primary` + count badge
- [x] 24.4 Implement filter dropdown panel — 220–320px width, `--surface-overlay` bg, `--shadow-md`, checkbox list, "Clear" link at bottom, boolean filters as Yes/No/Any radio
- [x] 24.5 Implement "+ N more" overflow button when > 4 filters
- [x] 24.6 Implement right side — "Clear all filters" link (visible when ≥1 active), Export dropdown (if `enable_export`), column visibility toggle (ghost icon, localStorage preference)
- [x] 24.7 Wire HTMX `hx-get` on search `keyup` with `delay:300ms`, swap `#table-wrapper`

---

## Phase 25 — List Page: Table Component

**References:** `ui_design_system.md` §7

- [ ] 25.1 Implement table container — `--surface-raised` bg, 1px border, `--radius-md`, `overflow: hidden`
- [ ] 25.2 Implement column headers — `--text-xs` uppercase, 500 weight, `--text-secondary`, 10px/12px padding; sortable columns show sort icon on hover, active sort in `--primary-500`
- [ ] 25.3 Implement checkbox column — 44px width, header checkbox with indeterminate state, only shown if `can_delete`
- [ ] 25.4 Implement data cell rendering — text truncation, mono font for numeric/ID/date, boolean as 6px circle (`--success-500`/`--surface-border`), status as badge, FK as linked `__str__`, long text tooltip on hover
- [ ] 25.5 Implement actions column — rightmost, "Edit" ghost link, dot separator, "Delete" ghost link (hover: `--danger-500`)
- [ ] 25.6 Implement inline delete confirmation — replaces actions `<td>` content, "Delete {name}?" with Yes/Cancel buttons, `--danger-100` row tint
- [ ] 25.7 Implement row hover — `--primary-100` background, `--duration-fast` transition
- [ ] 25.8 Implement empty table state — centered within table row, icon, message, "Try clearing filters" if active, "+ New" button if `can_create`
- [ ] 25.9 Implement sortable column click — HTMX fetch with `?sort={col}&dir={asc|desc}`, URL param state

---

## Phase 26 — List Page: Bulk Action Bar

**References:** `ui_design_system.md` §8

- [ ] 26.1 Implement bulk action bar — replaces filter bar when ≥1 row selected, 48px height, `--primary-100` bg, `--primary-500` border, `--radius-md`
- [ ] 26.2 Implement deselect button (✕), "{N} selected" label, action dropdown (secondary style), "Delete (N)" danger button (if `can_delete`)
- [ ] 26.3 Animate bar in/out — height expand 150ms
- [ ] 26.4 Bulk delete opens confirmation modal (not inline)
- [ ] 26.5 Ensure filter bar is hidden (`display: none`) when bulk bar is visible, reappears when selection cleared

---

## Phase 27 — List Page: Pagination

**References:** `ui_design_system.md` §5 (list page pagination zone)

- [ ] 27.1 Implement pagination bar — "Showing 1–20 of 143" label, Prev/Next buttons, page number links
- [ ] 27.2 Pagination placed outside `<table>` inside `#table-wrapper`
- [ ] 27.3 Pagination swap target — updates via HTMX when search/filter/sort changes
- [ ] 27.4 Style pagination buttons — ghost style, active page highlighted with `--primary-100`
- [ ] 27.5 Ellipsis for large page counts (1 2 3 … 8)

---

## Phase 28 — Form Page: Fieldsets & Field Wrapper

**References:** `ui_design_system.md` §9, §10

- [ ] 28.1 Implement form body layout — `max-width: 860px`, flex column, gap 24px
- [ ] 28.2 Implement fieldset card — `--surface-raised` bg, 1px border, `--radius-md`, 20px padding
- [ ] 28.3 Implement fieldset header — flex space-between, title `--text-xs` uppercase secondary, collapse toggle (ghost icon chevron, Alpine.js `x-show` with height transition, `aria-expanded`/`aria-controls`)
- [ ] 28.4 Implement fieldset CSS Grid — `repeat(auto-fill, minmax(280px, 1fr))`, gap 16px; full-width fields (`grid-column: 1 / -1`): textarea, JSON editor, rich text, multi-relation, file/image upload
- [ ] 28.5 Implement `.field-wrapper` — flex column, gap 5px; label row (Inter 500, required `*` in `--danger-500`, readonly lock icon), input, help text, error list (no bullets, `--danger-500`, exclamation icon)
- [ ] 28.6 Update form macros to match field wrapper anatomy exactly

---

## Phase 29 — Form Page: Save Bar & Dirty State

**References:** `ui_design_system.md` §11

- [ ] 29.1 Implement save bar — sticky bottom of `.admin-content` (`position: sticky; bottom: 0`), `--surface-raised` bg, border-top, z-index 20, flex with space-between
- [ ] 29.2 Implement left side — "Delete record" danger-button-style (edit only, `can_delete`), opens delete confirmation modal
- [ ] 29.3 Implement right side — "Save & continue editing" (secondary, 8px gap) + "Save & return" (primary)
- [ ] 29.4 Implement dirty state tracking — Alpine.js `x-data` tracks `isDirty`, shows `●` dot badge before "Save & continue editing" in `--warning-500`
- [ ] 29.5 Implement `beforeunload` warning for unsaved changes (native browser dialog)
- [ ] 29.6 Implement submitting state — clicked button shows spinner, other save button disabled, 50% opacity on non-loading elements

---

## Phase 30 — Delete Confirmation Modal & Inline Delete

**References:** `ui_design_system.md` §12

- [ ] 30.1 Implement inline delete confirmation (single row) — replaces actions `<td>`, `--danger-100` row tint, "Yes, delete" danger btn sm, "Cancel" ghost btn sm, auto-cancel on click elsewhere
- [ ] 30.2 Implement delete modal — `modal--sm` (480px), header "Delete {Model}?", body with object repr in `<strong>`, footer with Cancel ghost + Delete danger buttons
- [ ] 30.3 Implement bulk delete modal — body "This will permanently delete **{N} {model plural}**. This cannot be undone."
- [ ] 30.4 Implement modal backdrop — `rgba(0,0,0,0.6)`, `backdrop-filter: blur(2px)`, z-index 50; click closes (except delete confirmations)
- [ ] 30.5 Implement modal entrance animation — `opacity: 0→1`, `scale(0.97)→scale(1)`, `--duration-slow`

---

## Phase 31 — Dashboard Page

**References:** `ui_design_system.md` §13

- [ ] 31.1 Implement stat cards row — CSS Grid `repeat(auto-fill, minmax(200px, 1fr))`, gap 16px; cards clickable (link to model list), hover: `--surface-overlay` bg + `--shadow-sm`
- [ ] 31.2 Implement chart + activity split — flex layout (chart `flex: 3`, activity `flex: 2`), stacks below 1024px
- [ ] 31.3 Implement recent activity feed — last 10 audit entries, each: coloured dot (CREATE `--success-500`, UPDATE `--warning-500`, DELETE `--danger-500`), user email, action badge, model + ID (mono), relative timestamp with absolute tooltip
- [ ] 31.4 Add "View full audit log →" link at feed bottom
- [ ] 31.5 Implement quick create row — flex wrap, secondary buttons with `+` prefix, only models with `can_create`, max 6 (truncate to 5 + "…more")

---

## Phase 32 — Audit Log Page

**References:** `ui_design_system.md` §14

- [ ] 32.1 Implement audit filter bar — Model, Action, User, Date range filters, "Clear" link; no search input
- [ ] 32.2 Implement timeline layout — entries grouped by date, date group headers (`--text-xs` uppercase, line on each side)
- [ ] 32.3 Implement audit entry card — `--surface-raised` bg, 1px border, 3px left border (colour per action), 12px/16px padding, cursor pointer
- [ ] 32.4 Implement collapsed state — one line: colour dot, time (JetBrains Mono), user email, action badge, model + ID
- [ ] 32.5 Implement expanded state (Alpine.js `x-show`) — diff table for UPDATE (FIELD/BEFORE/AFTER columns, changed rows highlighted `--warning-100`, values in mono), full snapshot JSON for CREATE/DELETE

---

## Phase 33 — Role Management Page

**References:** `ui_design_system.md` §15

- [ ] 33.1 Implement role list page — same list page structure, no search/filters, columns: Name, Description, Users (count mono), Created, Actions
- [ ] 33.2 Implement role edit page — Role Details fieldset (Name input, Description textarea full width)
- [ ] 33.3 Implement permissions matrix — `--surface-raised` bg, header row `--surface-overlay`, columns: Model (auto), View/Create/Edit/Delete (72px each), Fields (80px)
- [ ] 33.4 Implement permission checkboxes — 18px custom checkboxes (not toggles), centered, alternating row backgrounds
- [ ] 33.5 Implement fields expand — clicking "fields ▾" expands sub-section inline, two columns per field (view + edit checkbox), `--surface-overlay` bg, 4px left indent, field names in JetBrains Mono

---

## Phase 34 — Agent Chat Panel

**References:** `ui_design_system.md` §16

- [ ] 34.1 Implement panel container — fixed right, `top: 52px`, `height: calc(100vh - 52px)`, width 420px, `translateX(100%)` default, `translateX(0)` when open, 200ms cubic-bezier transition
- [ ] 34.2 Implement panel shadow — `box-shadow: -4px 0 20px rgba(0,0,0,0.4)` on left edge
- [ ] 34.3 Implement panel header — 52px, `--surface-overlay` bg, "✦ Agent" + model name + close button
- [ ] 34.4 Implement session tabs — 36px, "Current" + "History ▾" dropdown
- [ ] 34.5 Implement conversation thread — `flex: 1`, `overflow-y: auto`, 16px padding
- [ ] 34.6 Implement tool indicators — auto height, visible only when tools running (e.g. "⚙ Querying products...")
- [ ] 34.7 Implement input area — auto height, max ~120px, border-top, textarea + send button, model label (`--text-xs --text-disabled`)
- [ ] 34.8 Implement trigger button — sticky bottom-right inside `.admin-content`, 44px circle, `--primary-500` bg, `--shadow-md`, sparkles icon, "Ask AI" tooltip

---

## Phase 35 — Login Page

**References:** `ui_design_system.md` §17

- [ ] 35.1 Implement standalone login layout — full viewport, `--surface-base` bg, vertically centred (min-height 100vh, flex center)
- [ ] 35.2 Implement login card — `--surface-raised` bg, `--radius-lg`, `--shadow-lg`, width 380px, 32px padding
- [ ] 35.3 Implement logo — centred, 36px height, fallback to app name in `--text-lg` Inter 600
- [ ] 35.4 Implement title — "Sign in to {App Name}" in `--text-md` secondary, app name in primary 600
- [ ] 35.5 Implement error message — full-width alert box, `--danger-100` bg, 3px left border `--danger-500`, exclamation icon
- [ ] 35.6 Implement sign in button — full card width, primary, md size (36px)
- [ ] 35.7 Implement show/hide password toggle — ghost icon button inside password input, eye/eye-slash icons

---

## Phase 36 — Command Palette (⌘K Global Search)

**References:** `ui_design_system.md` §18 (command palette)

- [ ] 36.1 Implement command palette overlay — full-screen backdrop, palette floats at `top: 20%`, width 560px, max-height 60vh, `--surface-overlay` bg, `--shadow-lg`, z-index 60
- [ ] 36.2 Implement search input — 44px, borderless inside palette, auto-focus on open
- [ ] 36.3 Implement results list — scrollable, keyboard navigation (↑↓), enter to select
- [ ] 36.4 Wire ⌘K / Ctrl+K keyboard shortcut to open palette
- [ ] 36.5 Wire search trigger button in topbar to open palette

---

## Phase 37 — Responsive Design & Mobile

**References:** `ui_design_system.md` §19

- [ ] 37.1 Breakpoint `< 1280px` — content padding 24px → 16px
- [ ] 37.2 Breakpoint `< 1024px` — sidebar collapses to icon-only 56px, content takes full remaining width
- [ ] 37.3 Breakpoint `< 768px` — sidebar becomes off-canvas drawer, hamburger in topbar, overlay backdrop; filter bar wraps to two rows; table columns collapse (show only primary column + actions column)
- [ ] 37.4 Breakpoint `< 480px` — login card full width with 16px padding; modal becomes bottom sheet (full width, slides up, border-radius only top); agent panel full width
- [ ] 37.5 Implement mobile table "view" row action — expands to show all field values inline
- [ ] 37.6 Test all breakpoints in browser DevTools — verify no layout breaks

---

## Phase 38 — Page Transitions & Loading States

**References:** `ui_design_system.md` §20

- [ ] 38.1 Implement HTMX loading indicator — topbar progress bar (2px `--primary-500`) during requests
- [ ] 38.2 Implement page content fade-in on HTMX swap — `opacity: 0→1` transition
- [ ] 38.3 Implement skeleton loading states — for table rows (placeholder bars), stat cards, form fields
- [ ] 38.4 Implement button loading spinners — on form submit, action buttons show spinner and disable
- [ ] 38.5 Ensure all HTMX swaps have appropriate `hx-indicator` targets

---

## Phase 39 — Toast Notifications & Flash Messages (UI Polish)

**References:** `ui_design_system.md` §18 (modals), existing flash system

- [ ] 39.1 Implement toast container — fixed bottom-right, z-index 100, stack vertically with gap
- [ ] 39.2 Implement toast component — `--surface-raised` bg, 1px border, `--radius-md`, `--shadow-md`, 4s auto-dismiss with progress bar
- [ ] 39.3 Implement toast variants — success (`--success-500` left border), error (`--danger-500`), warning (`--warning-500`), info (`--info-500`)
- [ ] 39.4 Wire flash messages to render as toasts via Alpine.js `x-show` with enter/leave transitions
- [ ] 39.5 Implement toast close button (✕ ghost icon)

---

## Phase 40 — Final Integration & Visual QA

**References:** `ui_design_system.md` §21 (Component Placement Rules)

- [ ] 40.1 Verify zone ordering on all pages — no component from a lower zone appears in an upper zone
- [ ] 40.2 Verify sidebar nav matches spec — correct sections, correct order, record count badges, active state
- [ ] 40.3 Verify topbar — all three zones render correctly, dropdowns work, loading bar appears
- [ ] 40.4 Verify all list pages — search, filters, table, pagination, bulk actions, empty states
- [ ] 40.5 Verify all form pages — fieldsets, field wrapper, save bar, dirty state, delete confirmation
- [ ] 40.6 Verify dashboard — stat cards, activity feed, quick create
- [ ] 40.7 Verify audit log — timeline, expand/collapse, diff table
- [ ] 40.8 Verify role management — permissions matrix, field expand
- [ ] 40.9 Verify login page — standalone layout, error display, password toggle
- [ ] 40.10 Verify agent chat panel — open/close, conversation, input
- [ ] 40.11 Verify modals — backdrop, entrance animation, sizes (sm/default/lg)
- [ ] 40.12 Verify responsive behaviour at all breakpoints (1280, 1024, 768, 480)
- [ ] 40.13 Verify dark mode — all tokens switch correctly, no hardcoded colours
- [ ] 40.14 Run full test suite and fix any regressions
