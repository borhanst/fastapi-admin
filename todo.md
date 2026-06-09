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

- [ ] 10.1 Create `fastapi_admin/auth/views.py` with GET `/admin/login`, POST `/admin/login`, POST `/admin/logout` handlers
- [ ] 10.2 GET login renders `pages/login.html`, redirects if already authenticated
- [ ] 10.3 POST login reads `email`/`password` from form, calls `auth_backend.authenticate`, sets signed session cookie, updates `last_login`, redirects to `?next=` or `/admin/`
- [ ] 10.4 POST login failure re-renders login with flash error message
- [ ] 10.5 Validate `next` query param is relative URL only (prevent open redirect)
- [ ] 10.6 POST logout deletes session cookie, calls `auth_backend.on_logout`, redirects to `/admin/login`
- [ ] 10.7 Create `fastapi_admin/auth/router.py` mounting three handlers on `APIRouter(prefix="/admin")`
- [ ] 10.8 Write tests in `tests/test_auth_routes.py`: successful login sets cookie, wrong password re-renders with error, logout deletes cookie, `next` redirect works, open redirect is blocked

---

## Phase 11 — Audit Log Capture

**References:** `fastapi_admin_core_spec.md` §2A.2, §2A.4

- [ ] 11.1 Create `fastapi_admin/audit/context.py` with `ContextVar` `_current_audit_context`
- [ ] 11.2 Implement `get_audit_context()`, `set_audit_context(data)` functions
- [ ] 11.3 Implement `audit_context_middleware` — reads `request.state.admin_user`, sets ContextVar with user/ip/user_agent, resets after response
- [ ] 11.4 Create `fastapi_admin/audit/diff.py` with `snapshot(obj)` — serialises all mapper columns
- [ ] 11.5 Implement `serialize_value(val)` — handles datetime, Decimal, UUID, bytes, Enum
- [ ] 11.6 Implement `compute_diff(before, after)` — returns changed fields only with before/after
- [ ] 11.7 Create `fastapi_admin/audit/listener.py` with `attach_audit_listener(session_factory, registry)`
- [ ] 11.8 Implement `before_flush` listener — snapshots dirty objects to `obj._audit_before`
- [ ] 11.9 Implement `after_flush` listener — writes `AuditLog` rows for create/update/delete on registered models
- [ ] 11.10 `write_audit` must skip UPDATE if `compute_diff` returns empty dict
- [ ] 11.11 Implement `is_registered_model(obj, registry)` check
- [ ] 11.12 Write tests in `tests/test_audit.py`: create → audit CREATE, update → diff captured, delete → audit DELETE, unchanged update → no audit row

---

## Phase 12 — Form Pipeline & Route Factories

**References:** `FORM_WIDGET_SYSTEM.md` §7, §8, §14

- [ ] 12.1 Create `fastapi_admin/form/pipeline.py` with `build_form_context(registered, obj, values, errors, request)`
- [ ] 12.2 Determine field order: respect `fields`, `exclude`, auto-order; skip PK on create (HiddenWidget), readonly on edit
- [ ] 12.3 Mark `readonly_fields` as `ReadOnlyWidget`, add `extra_fields`, apply `get_widget_for_field` override
- [ ] 12.4 Call `widget.render_context()` for each field, group into `FieldsetContext` blocks
- [ ] 12.5 Create `fastapi_admin/validation.py` with `FormValidator.run(registered, parsed, obj)`
- [ ] 12.6 Implement Level 1 (widget validate), Level 2 (`validate_{field_name}`), Level 3 (`validate`); detect async validators
- [ ] 12.7 Create `fastapi_admin/views/list.py` — `list_view_factory(registered)`: search, filter, order, paginate, render `pages/list.html`
- [ ] 12.8 Create `fastapi_admin/views/form.py` — `create_form_factory`, `create_submit_factory`, `edit_form_factory`, `edit_submit_factory`: parse, validate, lifecycle hooks, commit, flash, redirect
- [ ] 12.9 Create `fastapi_admin/views/delete.py` — `delete_factory`: call `on_delete`, delete, `after_delete`, flash, redirect
- [ ] 12.10 Create `fastapi_admin/views/bulk.py` — `bulk_factory`: reads `action`/`ids[]`, routes to `action_{name}` or built-in `delete_selected`
- [ ] 12.11 Create `fastapi_admin/router.py` — `build_model_router(registered)`: mounts list, create GET/POST, edit GET/POST, delete, bulk, search, validate-field with `require_permission` dependencies
- [ ] 12.12 Write tests in `tests/test_routes.py`: list 200, create valid redirect, create invalid 422 with errors, edit updates, delete removes, RBAC 403

---

## Phase 13 — Audit Log & Role Management Routes

**References:** `AUTH_RBAC_SYSTEM.md` §14

- [ ] 13.1 Create `fastapi_admin/views/audit.py` — `audit_list_view`: query `AuditLog` with filters (model, user_id, action, from, to, object_id), paginate, render `pages/audit_log.html`
- [ ] 13.2 Implement `audit_detail_view` — load single entry, render diff/snapshot in `pages/audit_detail.html`
- [ ] 13.3 Create `fastapi_admin/views/roles.py` — `GET /admin/roles/`: list roles with user counts
- [ ] 13.4 `GET /admin/roles/create`: empty role form
- [ ] 13.5 `GET /admin/roles/{id}`: edit form with permission matrix (one row per model, four checkboxes, expandable field-level)
- [ ] 13.6 `POST /admin/roles/{id}`: parse `perm[{table}][{action}]` and `field_perm[{table}][{field}][{mode}]`, upsert `AdminPermission` and `AdminFieldPermission` rows
- [ ] 13.7 `POST /admin/roles/{id}/delete`: delete role (refuse if users assigned, or set NULL per config)
- [ ] 13.8 All role routes require `is_superuser=True` via `require_superuser` dependency
- [ ] 13.9 Write tests in `tests/test_role_routes.py`: list, create, save permission matrix, verify DB rows

---

## Phase 14 — Flash Messages & Dashboard

**References:** `fastapi_admin_core_spec.md` §3.12

- [ ] 14.1 Create `fastapi_admin/flash.py` — `add_flash(request, level, message)`: appends to signed session cookie key `admin_flash`
- [ ] 14.2 Implement `get_flash_messages(request)`: reads and clears flash cookie, returns `[{level, text}]`
- [ ] 14.3 Levels: `success`, `error`, `warning`, `info`
- [ ] 14.4 Create `fastapi_admin/views/dashboard.py` — query record counts for top models, fetch last 10 audit entries
- [ ] 14.5 Respect `dashboard_stat_cards` and `dashboard_charts` config from `Admin()` init
- [ ] 14.6 Built-in fallback: show record count for each registered model
- [ ] 14.7 Render `pages/dashboard.html` with stat cards, recent activity, quick-create links
- [ ] 14.8 Write tests in `tests/test_dashboard.py`: dashboard 200, stat counts correct, recent activity shows audit entries
