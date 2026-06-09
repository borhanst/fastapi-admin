# FastAPI Admin — Build Phases

> Instructions only. No code. Each phase is a self-contained unit an agent can execute independently.
> Complete phases in order — later phases depend on earlier ones.

---

## Phase 1 — Project Scaffold & Dependencies

**Goal:** Create the package skeleton, install dependencies, and verify the project loads.

**Instructions:**

1. Create the top-level package directory `fastapi_admin/` with an `__init__.py` that exports nothing yet.
2. Create subdirectory stubs (empty `__init__.py` in each): `auth/`, `audit/`, `widgets/`, `views/`, `filters/`, `actions/`, `storage/`, `plugins/`, `dashboard/`, `nav/`, `form/`.
3. Create `pyproject.toml` (or `setup.py`) declaring the package name `fastapi-admin` and listing all required dependencies: `fastapi`, `sqlalchemy>=2.0`, `jinja2`, `python-multipart`, `itsdangerous`, `passlib[bcrypt]`, `aiofiles`, `pydantic-settings`, `slowapi`, `python-jose`. Mark optional extras for `s3` (aiobotocore) and `redis` (aioredis).
4. Create a `requirements-dev.txt` adding: `pytest`, `pytest-asyncio`, `httpx`, `alembic`, `uvicorn`.
5. Create `fastapi_admin/models/` subdirectory with a `base.py` that defines the SQLAlchemy `Base` (declarative base) and a `metadata` object that all admin tables will use. This base must be separate from the application's own base.
6. Create a top-level `static/` directory with placeholder subdirectories: `css/`, `js/`, `icons/`.
7. Create a top-level `templates/` directory with placeholder subdirectories matching the spec: `pages/`, `partials/`, `macros/`.
8. Verify the package is importable by running `python -c "import fastapi_admin"` with no errors.

**Acceptance:** `import fastapi_admin` succeeds. All subdirectory `__init__.py` files exist.

---

## Phase 2 — Core Data Structures (ColumnMeta, RelationMeta, FieldMeta)

**Goal:** Define the shared dataclasses that flow through inspection → widgets → forms. No logic yet, just the data shapes.

**Instructions:**

1. Create `fastapi_admin/types.py`. Define the following dataclasses (reference `fastapi_admin_core_spec.md` §1.4 and `FORM_WIDGET_SYSTEM.md` §2 for field lists):
   - `ColumnMeta` — holds `name`, `type` (SQLAlchemy type instance), `nullable`, `primary_key`, `foreign_keys`, `default`, `server_default`.
   - `RelationMeta` — holds `name`, `direction` (string), `target_model`, `uselist`, `back_populates`.
   - `FieldMeta` — holds `name`, `label`, `required`, `readonly`, `help_text`, `placeholder`, `extra` (dict). This is the form-layer view of a column.
   - `PermissionSet` — dataclass with four booleans: `can_view`, `can_create`, `can_edit`, `can_delete`.
   - `FieldsetSpec` — holds `title` (str or None), `fields` (list of str), `collapsed` (bool, default False).
2. All dataclasses must use `@dataclass` with type annotations. Use `field(default_factory=...)` for mutable defaults.
3. Import and re-export all of these from `fastapi_admin/__init__.py` so they are accessible as `fastapi_admin.ColumnMeta` etc.

**Acceptance:** All dataclasses importable. `ColumnMeta(name="id", type=None, nullable=False, primary_key=True, foreign_keys=[], default=None, server_default=None)` constructs without error.

---

## Phase 3 — Model Inspection

**Goal:** Given a SQLAlchemy model class, extract its columns and relationships into the `ColumnMeta` / `RelationMeta` structures from Phase 2.

**Instructions:**

1. Create `fastapi_admin/inspection.py`.
2. Implement `inspect_model(model: type) -> tuple[list[ColumnMeta], list[RelationMeta]]`. Use `sqlalchemy.inspect()` to get the mapper. Iterate `mapper.columns` for columns and `mapper.relationships` for relationships. Populate the dataclasses from Phase 2. Refer to `fastapi_admin_core_spec.md` §1.4 for the exact fields to extract.
3. Implement `is_abstract(model: type) -> bool` — returns True if the model has `__abstract__ = True`. Abstract models must be skipped during registration.
4. Implement `get_pk_field(model: type) -> str` — returns the name of the primary key column. If composite PKs exist, return a list of names instead and handle this case explicitly (do not silently pick one).
5. Implement `auto_label(name: str) -> str` — converts a column name to a human-readable label per the rules in `FORM_WIDGET_SYSTEM.md` §5: strip `_id` suffix, split camelCase, replace underscores with spaces, title-case.
6. Implement `is_required(col: ColumnMeta) -> bool` — per the rules in `FORM_WIDGET_SYSTEM.md` §5: not nullable, no default, no server_default, not a primary key.
7. Write unit tests in `tests/test_inspection.py` using a small in-memory SQLite model. Test: columns extracted correctly, relationships extracted, `auto_label` cases, `is_required` edge cases, abstract model detection.

**Acceptance:** All tests pass. Inspection of a model with a string, integer, boolean, FK, and a relationship returns the correct metadata.

---

## Phase 4 — Widget Registry & Built-in Widgets (Python Layer)

**Goal:** Build the `Widget` base class, all built-in widget implementations, and the `WidgetRegistry` that resolves which widget to use for a column.

**Instructions:**

1. Create `fastapi_admin/widgets/base.py`. Implement the `Widget` ABC as specified in `FORM_WIDGET_SYSTEM.md` §2: `macro_name` class attribute, `render_context(field, value) -> dict`, `parse(raw) -> Any`, `validate(value, field) -> list[str]`. Base `validate` checks required only.
2. Create `fastapi_admin/widgets/inputs.py`. Implement every built-in widget listed in `FORM_WIDGET_SYSTEM.md` §2: `TextInputWidget`, `TextareaWidget`, `NumberInputWidget`, `ToggleWidget`, `SelectWidget`, `DatePickerWidget`, `DateTimePickerWidget`, `TimePickerWidget`, `JsonEditorWidget`, `PasswordWidget`, `ReadOnlyWidget`, `HiddenWidget`. Also add: `EmailInputWidget`, `UrlInputWidget`, `PhoneInputWidget`, `ColorPickerWidget`, `SlugWidget`, `ImageUploadWidget`, `FileUploadWidget`, `TagInputWidget`.
3. Each widget's `macro_name` must exactly match the macro names listed in `FORM_WIDGET_SYSTEM.md` §6 binding table.
4. `PasswordWidget.render_context` must always set `value = ""` — never pre-fill.
5. `PasswordWidget.parse` must bcrypt-hash the raw value on parse. If raw is empty, return None (don't hash an empty string).
6. `ReadOnlyWidget.parse` must always return None — readonly fields are never updated from POST.
7. Create `fastapi_admin/widgets/relation.py`. Implement `RelationPickerWidget` and `MultiRelationWidget` as described in `FORM_WIDGET_SYSTEM.md` §10.
8. Create `fastapi_admin/widgets/registry.py`. Implement `WidgetRegistry` with `register_type`, `register_name`, and `resolve(col: ColumnMeta) -> Widget`. Resolution order: name patterns first, then FK check, then Enum check, then type map, then fallback to `TextInputWidget`. Instantiate a global `widget_registry` singleton and register all default bindings as listed in `FORM_WIDGET_SYSTEM.md` §3.
9. Export everything from `fastapi_admin/widgets/__init__.py`.
10. Write unit tests in `tests/test_widgets.py` covering: parse/validate for each widget type, PasswordWidget never pre-fills, ReadOnly always returns None, registry resolution order.

**Acceptance:** All tests pass. `widget_registry.resolve(col)` returns the correct widget for every SQLAlchemy type in the spec mapping table.

---

## Phase 5 — ModelAdmin Base Class & Registry

**Goal:** Build the `ModelAdmin` configuration class, the `AdminRegistry` singleton, and the `RegisteredModel` dataclass that ties them together.

**Instructions:**

1. Create `fastapi_admin/modeladmin.py`. Implement `ModelAdmin` base class with all optional configuration attributes from `fastapi_admin_core_spec.md` §1.2: `list_display`, `list_filter`, `search_fields`, `ordering`, `per_page`, `fields`, `exclude`, `readonly_fields`, `verbose_name`, `verbose_name_plural`, `icon`, `formfield_overrides`, `extra_fields`, `rbac_exempt`, `superuser_only`. Default all to None or sensible defaults.
2. Add stub lifecycle hook methods to `ModelAdmin`: `get_queryset`, `get_object`, `on_create`, `after_create`, `on_update`, `after_update`, `on_delete`, `after_delete`. All stubs do nothing (or return the session query for `get_queryset`).
3. Add stub validation methods: `validate` (returns empty dict) and the convention-based `validate_{field_name}` pattern is documented but not enforced at the base level.
4. Add `get_widget_for_field(field_name, obj, request) -> Widget | None` stub — returns None by default.
5. Create `fastapi_admin/registry.py`. Implement `AdminRegistry` with `register(model, admin_class=None)`, `get(table_name) -> RegisteredModel | None`, `all() -> list[RegisteredModel]`, and `auto_discover()`. On `register`: validate the model is a SQLAlchemy mapped class (not abstract), create a default `ModelAdmin` if none given, run `inspect_model`, resolve `verbose_name` and `verbose_name_plural` (auto-generate from class name if not set), build the `RegisteredModel`. Store keyed by `model.__tablename__`.
6. Define the `RegisteredModel` dataclass in `fastapi_admin/registry.py` (or `types.py`): `model`, `admin`, `table_name`, `verbose_name`, `verbose_name_plural`, `columns`, `relationships`, `pk_field`.
7. Add a method `RegisteredModel.get_widget(field_name: str) -> Widget` that checks `admin.formfield_overrides` first, then calls `widget_registry.resolve`.
8. Implement the `@admin.register` decorator pattern — `register` must work both as a direct call (`admin.register(Product)`) and as a decorator factory (`@admin.register(Product)`).
9. Write unit tests in `tests/test_registry.py`: register a model with no admin class, register with a partial override, verify `verbose_name` auto-generation, verify `get_widget` override precedence.

**Acceptance:** All tests pass. `admin.register(Product)` and `@admin.register(Product) class ProductAdmin(ModelAdmin): ...` both work.

---

## Phase 6 — Database Models (Admin Tables)

**Goal:** Define all SQLAlchemy models for the admin's own tables: users, roles, permissions, field permissions, and audit log.

**Instructions:**

1. Create `fastapi_admin/auth/models.py`. Define `AdminRole`, `AdminUser`, `AdminPermission`, `AdminFieldPermission` using the schemas in `AUTH_RBAC_SYSTEM.md` §2 and §7. Use the shared `Base` from Phase 1. All relationships must be defined bidirectionally.
2. `AdminUser` must have: `id`, `email` (unique), `hashed_password`, `full_name`, `role_id` (FK to `AdminRole`), `is_superuser`, `is_active`, `last_login`, `created_at`. Add a `role` relationship.
3. `AdminPermission` must have a unique constraint on `(role_id, table_name)`.
4. `AdminFieldPermission` must have a unique constraint on `(role_id, table_name, field_name)`.
5. Create `fastapi_admin/audit/models.py`. Define `AuditLog` using the schema in `fastapi_admin_core_spec.md` §2A.1. Include all indexes specified in the schema.
6. Create `fastapi_admin/auth/protocol.py`. Define the `AdminUserProtocol` using `typing.Protocol` as specified in `AUTH_RBAC_SYSTEM.md` §4. It requires: `id`, `email`, `is_active`, `is_superuser`, `role_id`.
7. Create `fastapi_admin/models/__init__.py` that imports and re-exports all admin models so migrations can find them via a single import.
8. Write a test in `tests/test_models.py` that creates all tables against an in-memory SQLite database and verifies they are created without error. Also verify `AdminUser` satisfies `AdminUserProtocol` at runtime using `isinstance`.

**Acceptance:** All tables create cleanly. `isinstance(AdminUser(), AdminUserProtocol)` returns True.

---

## Phase 7 — Auth Backend & Session

**Goal:** Implement the session cookie system and the built-in auth backend. No routes yet — just the pure logic.

**Instructions:**

1. Create `fastapi_admin/auth/session.py`. Implement the `SessionBackend` ABC with `encode(user_id) -> str`, `decode(token) -> int | str | None`, and `destroy(token) -> None`. Implement `SignedCookieSessionBackend` using `itsdangerous.TimestampSigner`. `decode` must return None for expired or tampered tokens without raising. Refer to `AUTH_RBAC_SYSTEM.md` §15 for the session payload structure.
2. Create `fastapi_admin/auth/backend.py`. Implement the `AuthBackend` ABC with `authenticate` and `get_user` abstract methods, plus optional `post_authenticate` and `on_logout` stubs. Implement `BuiltinAuthBackend` using bcrypt via passlib as shown in `AUTH_RBAC_SYSTEM.md` §5.
3. Create `fastapi_admin/auth/dependencies.py`. Implement:
   - `get_session` — FastAPI dependency that yields a SQLAlchemy session.
   - `get_current_admin_user(request, session) -> AdminUserProtocol` — reads the session cookie, decodes it, calls `auth_backend.get_user`. Raises HTTP 401 if missing or inactive.
   - `get_permission_checker(user, session) -> PermissionChecker` — instantiates `PermissionChecker` (implemented in Phase 8).
   - `require_permission(table_name, action)` — dependency factory that raises HTTP 403 if the permission check fails.
4. The `auth_backend` instance used by dependencies must be readable from `request.app.state.admin_auth_backend`. The `session_backend` must be readable from `request.app.state.admin_session_backend`.
5. Write unit tests in `tests/test_auth.py`: session encode/decode round-trip, expired token returns None, tampered token returns None, `BuiltinAuthBackend.authenticate` returns None for wrong password, returns user for correct password.

**Acceptance:** All tests pass. Session round-trip works. Wrong password returns None.

---

## Phase 8 — RBAC Permission Checker

**Goal:** Implement the `PermissionChecker` class that reads the permission tables and answers `has_permission` queries.

**Instructions:**

1. Create `fastapi_admin/auth/permissions.py`. Implement `PermissionChecker` as specified in `AUTH_RBAC_SYSTEM.md` §8.
2. `PermissionChecker.__init__` takes `session` and `user: AdminUserProtocol`. It must initialise an in-memory `_cache` dict.
3. `has_permission(table_name, action) -> bool`: superusers always return True. Check `_cache` first. If `user.role_id` is None, return False. Query `AdminPermission` for the `(role_id, table_name)` row and read the `can_{action}` column. Cache the result.
4. `get_allowed_fields(table_name, mode) -> set[str] | None`: superusers return None (no restrictions). If `role_id` is None, return empty set. Query all `AdminFieldPermission` rows for `(role_id, table_name)`. If no rows exist, return None (meaning all fields allowed). Otherwise return the set of field names where `can_view` or `can_edit` is True depending on `mode`.
5. `permission_set(table_name) -> PermissionSet`: calls `has_permission` for all four actions and returns a `PermissionSet` dataclass.
6. Write unit tests in `tests/test_permissions.py`: superuser always True, no role returns False, correct permission rows return correct results, `get_allowed_fields` returns None when no rows, returns correct set when rows exist, caching works (verify only one DB query per unique key).

**Acceptance:** All tests pass. Permission checks are correct and cached within a request.

---

## Phase 9 — Admin Class & Startup Wiring

**Goal:** Build the central `Admin` class that developers instantiate. It wires all components together at startup and exposes the `register` / `@register` API.

**Instructions:**

1. Create `fastapi_admin/admin.py`. Implement the `Admin` class. Its `__init__` must accept all config kwargs listed in `AUTH_RBAC_SYSTEM.md` §17 and `fastapi_admin_core_spec.md` §3.12 (branding, session_ttl, auth_model, auth_backend, seed_roles, etc.). Store all config on `self`.
2. Implement `Admin.setup()` (async). This method must: create all admin DB tables (using `Base.metadata.create_all`), seed default roles if none exist (per `AUTH_RBAC_SYSTEM.md` §13), store `auth_backend` and `session_backend` on `app.state`, mount the static files directory, initialise the Jinja2 template environment, register all plugin startup hooks, and call `registry.auto_discover()` if `auto_discover=True`.
3. Implement `Admin.register(model, admin_class=None)` that delegates to `AdminRegistry.register`. Support both decorator and direct-call usage.
4. Implement `Admin._build_router()` — iterates all registered models and mounts their auto-generated routers (built in Phase 12) under `/admin/{table_name}/`. Also mounts auth routes (Phase 10) and built-in pages (audit log, roles, dashboard).
5. `Admin.setup()` must be called via a FastAPI `lifespan` event. Provide a helper `Admin.lifespan(app)` context manager that developers can pass to `FastAPI(lifespan=admin.lifespan)`.
6. Validate at startup that any custom `auth_model` satisfies `AdminUserProtocol`. If not, raise `ConfigError` with a clear message listing the missing attributes.
7. Write integration tests in `tests/test_admin.py`: `Admin()` constructs, `setup()` runs without error against SQLite, default roles are created on first run, `auto_discover=False` skips auto-discovery.

**Acceptance:** `Admin(app=app, engine=engine, secret_key="test")` constructs. `await admin.setup()` creates tables and seeds roles.

---

## Phase 10 — Auth Routes (Login / Logout)

**Goal:** Implement the login and logout HTTP routes and wire them into the admin.

**Instructions:**

1. Create `fastapi_admin/auth/views.py`. Implement three route handlers:
   - `GET /admin/login` — renders `pages/login.html`. If user already has a valid session, redirect to `/admin/`.
   - `POST /admin/login` — reads `email` and `password` from form data, calls `auth_backend.authenticate`, calls `post_authenticate` hook, builds and signs session cookie, sets it on the response, updates `user.last_login`, redirects to `/admin/` (or `?next=` param). On failure, re-render login with a flash error. Refer to `AUTH_RBAC_SYSTEM.md` §15 for the full flow.
   - `POST /admin/logout` — deletes the session cookie, calls `auth_backend.on_logout`, redirects to `/admin/login`.
2. The `next` query parameter must be validated to be a relative URL only (prevent open redirect).
3. Create `fastapi_admin/auth/router.py`. Mount the three handlers on an `APIRouter` with prefix `/admin`.
4. Flash messages on login failure must use the flash system (Phase 14).
5. Write tests in `tests/test_auth_routes.py` using `httpx.AsyncClient` against a test FastAPI app: successful login sets cookie, wrong password re-renders with error, logout deletes cookie, `next` redirect works, open redirect is blocked.

**Acceptance:** All tests pass. Login sets a signed cookie. Logout clears it.

---

## Phase 11 — Audit Log Capture

**Goal:** Implement the SQLAlchemy event hooks that capture create/update/delete events and write them to `admin_audit_log` transparently.

**Instructions:**

1. Create `fastapi_admin/audit/context.py`. Define a `ContextVar` named `_current_audit_context` (default None). Implement `get_audit_context() -> dict | None` and `set_audit_context(data: dict) -> Token`. Implement `audit_context_middleware(request, call_next)` — an async middleware that reads `request.state.admin_user` (set by auth dependency), builds a context dict with `user`, `ip_address`, `user_agent`, sets the ContextVar, and resets it after the response.
2. Create `fastapi_admin/audit/diff.py`. Implement `snapshot(obj) -> dict` — iterates mapper columns and serialises each value using `serialize_value`. Implement `compute_diff(before, after) -> dict` — returns only changed fields with `before`/`after` keys. Implement `serialize_value(val) -> Any` — handles datetime, Decimal, UUID, bytes, Enum safely. Refer to `fastapi_admin_core_spec.md` §2A.2 and §2A.4.
3. Create `fastapi_admin/audit/listener.py`. Implement `attach_audit_listener(session_factory, registry)`. Use `@event.listens_for(session_factory, "before_flush")` to snapshot dirty objects before the flush (store on `obj._audit_before`). Use `@event.listens_for(session_factory, "after_flush")` to write `AuditLog` rows for new, dirty, and deleted objects. Only audit models that are registered in `AdminRegistry`. Use `get_audit_context()` to get user info.
4. The `write_audit` internal function must write an `AuditLog` row directly to the session. For UPDATE, only write if `compute_diff` returns a non-empty dict. For CREATE and DELETE, always write with `full_snapshot`.
5. `is_registered_model(obj, registry) -> bool` — checks whether the object's class is in the registry.
6. Write unit tests in `tests/test_audit.py`: create a model instance → audit log row written with action=CREATE, update a field → diff captured correctly, delete → action=DELETE, unchanged update → no audit row written.

**Acceptance:** All tests pass. Every registered-model DB write produces the correct audit row.

---

## Phase 12 — Form Pipeline & Route Factories

**Goal:** Build the form generation pipeline (field ordering, fieldset grouping, `FormContext` assembly) and the auto-generated route handler factories for list, create, edit, delete.

**Instructions:**

1. Create `fastapi_admin/form/pipeline.py`. Implement `build_form_context(registered, obj=None, values=None, errors=None, request=None) -> FormContext`. This function must: determine field order (respect `ModelAdmin.fields`, `ModelAdmin.exclude`, auto-order otherwise), skip PKs on create (use `HiddenWidget`) or make them readonly on edit, mark `readonly_fields` as `ReadOnlyWidget`, add `extra_fields` from `ModelAdmin`, apply `get_widget_for_field` dynamic override, call `widget.render_context(field_meta, value)` for each field, group into `FieldsetContext` blocks (use `ModelAdmin.fieldsets` if set, otherwise a single unnamed fieldset), and return a fully populated `FormContext` (see `FORM_WIDGET_SYSTEM.md` §14).
2. Create `fastapi_admin/validation.py`. Implement `FormValidator.run(registered, parsed, obj=None) -> dict[str, list[str]]`. Run Level 1 (widget validate), Level 2 (`validate_{field_name}` on ModelAdmin), Level 3 (`validate` on ModelAdmin). Level 3 only runs if Levels 1 and 2 produce no errors. Detect `async` validators by `_async` suffix and await them. Refer to `FORM_WIDGET_SYSTEM.md` §8.
3. Create `fastapi_admin/views/list.py`. Implement `list_view_factory(registered) -> Callable`. The generated handler must: call `ModelAdmin.get_queryset`, apply search (across `search_fields` using ilike), apply filter params, apply ordering, paginate by `per_page`, build a `ListContext`, and render `pages/list.html`.
4. Create `fastapi_admin/views/form.py`. Implement `create_form_factory`, `create_submit_factory`, `edit_form_factory`, `edit_submit_factory`. Follow the POST flows in `FORM_WIDGET_SYSTEM.md` §7 exactly: parse all non-readonly fields, validate, call lifecycle hooks, commit, flash, redirect. On error: re-render with 422 status and errors in context.
5. Create `fastapi_admin/views/delete.py`. Implement `delete_factory`. Call `ModelAdmin.on_delete` (catch `ValueError` to abort), delete, call `ModelAdmin.after_delete`, flash, redirect.
6. Create `fastapi_admin/views/bulk.py`. Implement `bulk_factory`. Reads `action` and `ids[]` from form. Routes to the correct `action_{name}` method on `ModelAdmin` or handles built-in `delete_selected`.
7. Create `fastapi_admin/router.py`. Implement `build_model_router(registered) -> APIRouter` — mounts all 8 routes from the spec (list, create GET/POST, edit GET/POST, delete, bulk, search) with the correct `require_permission` dependency injected on each. Also add `GET /validate-field` for HTMX partial validation.
8. Write integration tests in `tests/test_routes.py`: list returns 200, create POST with valid data redirects, create POST with invalid data returns 422 with errors, edit POST updates the record, delete removes the record, RBAC dependency blocks 403.

**Acceptance:** All CRUD routes work end-to-end against SQLite. Validation errors are returned correctly.

---

## Phase 13 — Audit Log & Role Management Routes

**Goal:** Build the admin UI routes for viewing the audit log and managing roles/permissions.

**Instructions:**

1. Create `fastapi_admin/views/audit.py`. Implement `audit_list_view` — queries `AuditLog` with optional filters (`model`, `user_id`, `action`, `from`, `to`, `object_id` via query params), paginates, renders `pages/audit_log.html`. Implement `audit_detail_view` — loads a single `AuditLog` entry, renders `pages/audit_detail.html` with the diff or snapshot.
2. Create `fastapi_admin/views/roles.py`. Implement four handlers:
   - `GET /admin/roles/` — lists all roles with user counts, renders `pages/roles.html`.
   - `GET /admin/roles/create` — empty role form.
   - `GET /admin/roles/{id}` — role edit form with the full permission matrix (one row per registered model, four checkboxes per row, expandable field-level section).
   - `POST /admin/roles/{id}` — processes the permission matrix POST body, upserts `AdminPermission` rows and `AdminFieldPermission` rows, redirects with flash.
   - `POST /admin/roles/{id}/delete` — deletes the role (refuse if users are assigned to it, or set `role_id` to NULL depending on config).
3. The role edit POST body format is specified in `AUTH_RBAC_SYSTEM.md` §14. Parse `perm[{table}][{action}]` and `field_perm[{table}][{field}][{mode}]` keys from the form data.
4. All role management routes must require `is_superuser=True` (not just a role permission) — use a dedicated `require_superuser` dependency.
5. Write tests in `tests/test_role_routes.py`: list roles, create role, save permission matrix, verify DB rows created correctly.

**Acceptance:** Role permission matrix saves correctly. Audit log filters work.

---

## Phase 14 — Flash Messages & Dashboard

**Goal:** Implement the flash message system and the dashboard page.

**Instructions:**

1. Create `fastapi_admin/flash.py`. Implement `add_flash(request, level, message)` — appends a flash dict to a signed session cookie key `admin_flash`. Implement `get_flash_messages(request) -> list[dict]` — reads and clears the flash cookie, returning a list of `{level, text}` dicts. Levels: `success`, `error`, `warning`, `info`.
2. Create `fastapi_admin/views/dashboard.py`. Implement the dashboard route handler. It must: query record counts for the top registered models, fetch the last 10 audit log entries for the recent activity feed, build a context dict, and render `pages/dashboard.html`.
3. The dashboard must respect the `dashboard_stat_cards` and `dashboard_charts` configuration from `Admin()` init. If custom stat cards are provided, call their `compute()` methods and pass results to the template. Built-in fallback: show record count for each registered model.
4. Write tests in `tests/test_dashboard.py`: dashboard returns 200, stat counts are correct, recent activity shows audit entries.

**Acceptance:** Dashboard renders with model counts and recent activity. Flash messages appear after redirect and are cleared on display.

---

## Phase 15 — Jinja2 Templates (Structure & Base)

**Goal:** Create all Jinja2 template files. This phase is HTML/Jinja2 only — no Python changes.

**Instructions:**

1. Create `templates/base.html`. Implement the two-column layout from `fastapi_admin_core_spec.md` §3.4: fixed sidebar (256px), top bar (64px), scrollable content area. Include: Tailwind CSS (CDN), HTMX, Alpine.js, Heroicons sprite, Inter font. Inject `extra_css` and `extra_js` from `admin_config`. Add `{% block content %}` for page content. Add `{% block head_extra %}` for page-specific head tags.
2. Create `templates/partials/sidebar.html`. Render nav links for all registered models (only those where `perm.can_view` is True). Include sections for Audit Log, Roles. Show active link highlight based on current path. Collapse to icons below 1024px.
3. Create `templates/partials/topbar.html`. Show breadcrumb, dark mode toggle button (Alpine.js), user menu dropdown (name, logout link).
4. Create `templates/partials/flash_messages.html`. Render flash messages as toast notifications using Alpine.js `x-show` with auto-dismiss after 4 seconds.
5. Create `templates/partials/pagination.html`. Reusable pagination component that renders prev/next and page number links.
6. Create `templates/pages/login.html`. Standalone page (no sidebar). Email + password form. Brand logo at top. Error message display.
7. Create `templates/pages/dashboard.html`. Stat cards row, recent activity feed, quick-create links.
8. Create `templates/pages/list.html`. Full list view per `fastapi_admin_core_spec.md` §3.5: search input with HTMX, filter dropdowns, sortable column headers, bulk-select checkboxes (if `can_delete`), Edit/Delete per-row actions (conditional on permissions), empty state, pagination.
9. Create `templates/pages/form.html`. Create/edit form per `fastapi_admin_core_spec.md` §3.6: fieldset sections (collapsible with Alpine.js), sticky save bar, Delete button (edit only, if `can_delete`), History tab stub, unsaved-changes warning.
10. Create `templates/pages/audit_log.html` and `templates/pages/audit_detail.html`. Timeline feed with color-coded action badges, expandable diff view.
11. Create `templates/pages/roles.html` and `templates/pages/role_form.html`. Permission matrix table with checkboxes and collapsible field-level sections.
12. All templates must use CSS variables from `variables.css` for colors. No hardcoded hex values in templates.

**Acceptance:** All template files exist and are valid Jinja2 (no syntax errors). `jinja2.Environment.parse()` succeeds on each file.

---

## Phase 16 — Form Field Macros

**Goal:** Implement all Jinja2 form field macros that widgets reference by `macro_name`.

**Instructions:**

1. Create `templates/macros/form_fields.html`. Implement the `render_field(field_ctx, model_name)` dispatcher macro that routes to the correct macro by `field_ctx.widget_macro`. Refer to `FORM_WIDGET_SYSTEM.md` §4 for the full dispatcher.
2. Implement each macro listed in the dispatcher. Every macro must: wrap in `<div class="field-wrapper" id="field-wrapper-{name}">`, render a `<label>`, render the input element, render `field-errors` list if errors exist, render `field-help` if `help_text` is set.
3. For all text-like input macros, add HTMX blur-validation attributes pointing to `/admin/{model_name}/validate-field` as specified in `FORM_WIDGET_SYSTEM.md` §4.
4. The `toggle` macro must render a styled toggle switch using a hidden checkbox + CSS, not a plain browser checkbox.
5. The `relation_picker` macro must render using Alpine.js with a hidden input for the FK value and a visible search input that fetches from `/admin/{related_table}/search`. Refer to `FORM_WIDGET_SYSTEM.md` §15.
6. The `multi_relation` macro must render tag chips for selected items with remove buttons and a search input for adding new ones.
7. The `json_editor` macro must render a `<textarea>` as fallback. Add a CodeMirror 6 initialisation script block that upgrades it to a proper editor if the JS library is loaded.
8. The `image_upload` macro must include the Alpine.js `imageUpload()` function for client-side preview as described in `FORM_WIDGET_SYSTEM.md` §11.
9. Create `templates/macros/table.html`. Macros for rendering the list table: `table_header(columns, ordering)`, `table_row(obj, columns, permissions)`, `table_cell(value, column)`.
10. Create `templates/macros/icons.html`. A single `icon(name, class="")` macro that renders the correct SVG from the Heroicons sprite.

**Acceptance:** All macros are valid Jinja2. The `render_field` dispatcher handles every `macro_name` defined in the widget binding table without falling through to the else branch.

---

## Phase 17 — Static Assets

**Goal:** Set up all static asset files (CSS variables, base styles, JS behaviour).

**Instructions:**

1. Create `static/css/variables.css`. Define all CSS custom properties from `fastapi_admin_core_spec.md` §3.2: primary colour scale, neutral greys, semantic colours (success, warning, danger, info), layout dimensions. Add a `[data-theme="dark"]` block with inverted grey values.
2. Create `static/css/admin.css`. Define base component styles using the CSS variables: `.form-input`, `.form-select`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-sm`, `.field-wrapper`, `.field-label`, `.field-errors`, `.field-help`, `.required-star`, `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger`, `.toggle-switch`, `.toast`, `.nav-link`, `.sidebar`, `.topbar`, `.table-wrapper`, `.tag-chip`, `.relation-picker-dropdown`.
3. Create `static/js/admin.js`. Implement: Alpine.js `theme` store for dark mode (reads/writes `localStorage`, sets `data-theme` on `documentElement`), `relationPicker(selectedId, selectedLabel, searchUrl)` Alpine component, `multiRelation(selectedIds, selectedLabels, searchUrl)` Alpine component, `slugWidget(sourceField)` Alpine component, `imageUpload(existing)` Alpine component, `jsonEditor(fieldId)` CodeMirror initialiser.
4. Create `static/js/htmx-config.js`. Configure HTMX globally: set `htmx.config.defaultSwapStyle = "outerHTML"`, add a `htmx:configRequest` event listener that injects the CSRF/HTMX header on every request.
5. Download or reference Heroicons SVG sprite. Create `static/icons/heroicons.svg` as an SVG sprite file with `<symbol>` definitions for at minimum: `home`, `users`, `document-text`, `chart-bar`, `cog-6-tooth`, `arrow-up-tray`, `trash`, `pencil`, `plus`, `magnifying-glass`, `chevron-left`, `chevron-right`, `moon`, `sun`, `x-mark`, `check`, `exclamation-triangle`, `information-circle`, `clock`, `archive-box`, `truck`, `currency-dollar`.
6. Mount the `static/` directory in the admin's FastAPI app using `StaticFiles`.

**Acceptance:** Static files are served at `/static/css/variables.css` etc. Dark mode toggle sets `data-theme="dark"` on the root element. HTMX requests include the custom header.

---

## Phase 18 — Relation Search Endpoint

**Goal:** Implement the HTMX-powered async search endpoint that FK and M2M pickers use.

**Instructions:**

1. In `fastapi_admin/router.py`, add the `GET /admin/{table_name}/search` route to each model's router. This route must: accept `?q=` (search term) and `?limit=` (default 20) query params, call `ModelAdmin.get_queryset` to get the base queryset, search across `search_fields` (or fall back to the first String column if none configured), return JSON `[{id: "...", label: "..."}]` where `label` is from `ModelAdmin.__str__(obj)`.
2. The search response must be JSON (not HTML) so Alpine.js can consume it directly.
3. The search must be protected by `require_permission(table_name, "view")`.
4. Handle the self-referential FK edge case: if `exclude_id` query param is provided, exclude that object from results (prevents a record from selecting itself as its own parent).
5. Write tests in `tests/test_search.py`: search returns matching results, empty query returns first N records, `exclude_id` removes the specified record, unauthorized returns 403.

**Acceptance:** FK picker search returns correct JSON. Self-referential exclusion works.

---

## Phase 19 — File Upload & Storage

**Goal:** Implement the storage backend system and wire file upload handling into the form submit pipeline.

**Instructions:**

1. Create `fastapi_admin/storage/base.py`. Implement the `StorageBackend` ABC with `save`, `delete`, `url`, and `sanitize_filename` methods as specified in `PLUGIN_SYSTEM.md` §12.1.
2. Create `fastapi_admin/storage/local.py`. Implement `LocalStorageBackend` — saves files to a local directory, serves them via a mounted `StaticFiles` route. `sanitize_filename` must prepend a UUID prefix to prevent collisions and strip path separators.
3. Update `fastapi_admin/views/form.py` to handle file fields in both create and edit submits. Detect `FileUploadWidget` and `ImageUploadWidget` instances. Handle the three actions: `keep` (do nothing), `replace` (save new file, update DB column), `clear` (delete old file, set DB column to None). Refer to `FORM_WIDGET_SYSTEM.md` §11.
4. The form template for file/image fields must include three hidden inputs: `{field}_action` (keep/replace/clear) and the file input itself. The image macro's Alpine.js component must set the `_action` value correctly.
5. Add `max_size_mb` validation to `FileUploadWidget` — reject files exceeding the limit before any storage write.
6. Write tests in `tests/test_storage.py`: save returns a path, url returns correct URL, delete removes the file, oversized file is rejected by validation.

**Acceptance:** File upload saves to disk. Image upload shows preview. Clearing a file nulls the DB column and deletes the file.

---

## Phase 20 — Plugin System

**Goal:** Implement the `AdminPlugin` base class and the plugin loading mechanism in `Admin.setup()`.

**Instructions:**

1. Create `fastapi_admin/plugins/base.py`. Implement the `AdminPlugin` ABC as specified in `PLUGIN_SYSTEM.md` §3 with all hook methods: `register_widgets`, `get_macro_files`, `get_template_dirs`, `get_static_files`, `get_css_urls`, `get_js_urls`, `get_nav_items`, `get_routes`, `on_startup`, `on_shutdown`, `get_dashboard_widgets`, `get_jinja2_globals`, `get_jinja2_filters`. All methods have no-op defaults.
2. Update `Admin.__init__` to accept `plugins: list[AdminPlugin] = []`.
3. Update `Admin.setup()` to call each plugin's methods in the correct order: `register_widgets` first (so widgets are available before routes are built), then collect `get_macro_files`, `get_template_dirs`, `get_static_files`, `get_css_urls`, `get_js_urls`, `get_nav_items`, `get_routes`, `get_jinja2_globals`, `get_jinja2_filters`. Call `on_startup` last.
4. Template directories from plugins must be prepended to the Jinja2 search path (before built-in templates). Macro files from plugins must be loaded and made available to the dispatcher macro.
5. Implement `strict_plugin_conflicts=False` option. When True, raise `ConfigError` at startup if two plugins register the same widget type or name pattern.
6. Create `fastapi_admin/nav/types.py`. Define `NavItem(label, url, icon)` and `NavSection(title, items)` dataclasses. Pass combined nav items to the sidebar template context.
7. Write tests in `tests/test_plugins.py`: plugin `register_widgets` is called at startup, plugin routes are mounted, plugin nav items appear in context, conflict detection raises error when `strict_plugin_conflicts=True`.

**Acceptance:** A test plugin that registers a widget and a route works correctly when added to `plugins=[]`.

---

## Phase 21 — Event Bus & Global Hooks

**Goal:** Implement the `AdminEventBus` for cross-cutting event subscriptions.

**Instructions:**

1. Create `fastapi_admin/events.py`. Implement `AdminEventBus` with `on(event, handler, model=None)` for registration and `emit(event, model, obj, request, **extra)` for dispatch. Support both sync and async handlers (detect with `asyncio.iscoroutinefunction` and await accordingly). Supported events: `create`, `update`, `delete`, `login`, `logout`, `bulk_delete`.
2. `on` must support being used as a decorator: `@event_bus.on("create")`.
3. `emit` must call all matching handlers: those registered for the specific model class and those registered with `model=None` (all models).
4. Handler exceptions must be caught and logged — a failing event handler must not break the request.
5. Update `fastapi_admin/views/form.py` to call `event_bus.emit("create", ...)` after `after_create`, `event_bus.emit("update", ...)` after `after_update`, `event_bus.emit("delete", ...)` after `after_delete`. Pass `diff` as an extra kwarg for update events.
6. Update auth views to emit `login` and `logout` events.
7. Create a module-level `event_bus` singleton in `fastapi_admin/events.py`. Accept `event_bus=` kwarg in `Admin()` to allow custom or pre-configured instances.
8. Write tests in `tests/test_events.py`: handler fires on create, model-specific handler fires only for the correct model, async handler is awaited, failing handler does not raise.

**Acceptance:** All tests pass. Global and model-specific handlers fire correctly.

---

## Phase 22 — Auth Model Extensibility

**Goal:** Implement support for all three auth modes: built-in, extend built-in, and bring-your-own model.

**Instructions:**

1. Update `Admin.__init__` to accept `auth_model=None` and `auth_backend=None`. When both are None, default to `AdminUser` and `BuiltinAuthBackend`.
2. At startup, validate the provided `auth_model` satisfies `AdminUserProtocol` using `isinstance(instance, AdminUserProtocol)` on a dummy instance (or inspect the class attributes). Raise `ConfigError` with the list of missing attributes if validation fails.
3. Ensure all auth dependencies (`get_current_admin_user`, `get_permission_checker`) read `auth_model` and `auth_backend` from `request.app.state` rather than importing directly — this allows the custom model/backend to be used transparently.
4. Test the "extend built-in" pattern from `AUTH_RBAC_SYSTEM.md` §3: a subclass of `AdminUser` with extra columns using `__table_args__ = {"extend_existing": True}` must work without any other changes.
5. Test the "bring your own model" pattern from `AUTH_RBAC_SYSTEM.md` §16 Example A: a completely separate `User` model with an `admin_role_id` column and a `role_id` property must work with a custom `AppAuthBackend`.
6. Add `superuser_emails: list[str] = []` config option — emails in this list are always treated as superusers regardless of DB `is_superuser` flag.
7. Write tests in `tests/test_custom_auth.py` covering all three modes.

**Acceptance:** All three auth modes work. `ConfigError` is raised for models missing required protocol attributes.

---

## Phase 23 — Default Role Seeding & Management

**Goal:** Implement the default role seeding logic and the `SeedRole` configuration object.

**Instructions:**

1. Create `fastapi_admin/seeding.py`. Implement `seed_default_roles(session, registered_models, seed_roles=None, overwrite=False)`. If no roles exist in the DB, create the four default roles (`SuperAdmin`, `Admin`, `Editor`, `Viewer`) with the permission sets from `AUTH_RBAC_SYSTEM.md` §13. If `seed_roles` is provided, create those roles instead (merged with defaults or replacing them based on `overwrite`). If `overwrite=True`, drop and recreate all role permissions on every startup.
2. Define the `SeedRole` dataclass: `name`, `description`, `permissions` (dict of `{table_name: {action: bool}}`).
3. The seeding function must be idempotent: running it twice with `overwrite=False` must not create duplicate roles.
4. For the `SuperAdmin` role, set permissions to `can_*=True` for all registered models. For `Viewer`, set only `can_view=True`. For `Admin` and `Editor`, apply the logic from the spec table.
5. Update `Admin.setup()` to call `seed_default_roles` after tables are created.
6. Write tests in `tests/test_seeding.py`: first run creates 4 roles, second run with `overwrite=False` does not change anything, second run with `overwrite=True` resets permissions, custom `seed_roles` are created correctly.

**Acceptance:** All tests pass. Default roles appear after first `Admin.setup()`.

---

## Phase 24 — End-to-End Integration Test & Demo App

**Goal:** Build a small demo application that exercises every major feature, and write end-to-end tests against it.

**Instructions:**

1. Create `demo/` directory with `demo/main.py`, `demo/models.py`, and `demo/seed.py`.
2. In `demo/models.py`, define at least three models covering all column types: a `Product` model (String, Text, Numeric, Boolean, Enum, DateTime, FK to Category, M2M with Tag), a `Category` model (String, nullable String), a `Tag` model (String). Use SQLite for the demo.
3. In `demo/main.py`, wire up `Admin` with the built-in auth model, register all three models with partial `ModelAdmin` overrides, and run `uvicorn`.
4. In `demo/seed.py`, create sample data and a superuser account.
5. Write end-to-end tests in `tests/test_e2e.py` using `httpx.AsyncClient`. Test the full flow: login → list products → create product → edit product (verify audit log) → delete product → view audit log → create role with permissions → verify non-superuser with Viewer role cannot create.
6. Verify HTMX search endpoint works for the Category FK picker.
7. Verify bulk delete action removes multiple records and writes audit entries.
8. Verify dark mode cookie persists across requests (Alpine.js localStorage is client-only; test the server-side theme config default).

**Acceptance:** End-to-end tests pass. The demo app starts and is fully navigable. All spec features are exercised by at least one test.

---

## Summary Table

| Phase | What Gets Built | Key Files |
|---|---|---|
| 1 | Scaffold & deps | `pyproject.toml`, package dirs |
| 2 | Core dataclasses | `types.py` |
| 3 | Model inspection | `inspection.py` |
| 4 | Widgets (Python) | `widgets/` |
| 5 | ModelAdmin + Registry | `modeladmin.py`, `registry.py` |
| 6 | DB models | `auth/models.py`, `audit/models.py` |
| 7 | Auth backend + session | `auth/session.py`, `auth/backend.py` |
| 8 | Permission checker | `auth/permissions.py` |
| 9 | Admin class + wiring | `admin.py` |
| 10 | Login/logout routes | `auth/views.py` |
| 11 | Audit log capture | `audit/` |
| 12 | Form pipeline + CRUD routes | `form/`, `views/`, `router.py` |
| 13 | Audit UI + Role management | `views/audit.py`, `views/roles.py` |
| 14 | Flash messages + Dashboard | `flash.py`, `views/dashboard.py` |
| 15 | Jinja2 templates | `templates/` |
| 16 | Form field macros | `templates/macros/` |
| 17 | Static assets | `static/` |
| 18 | Relation search endpoint | `router.py` (search route) |
| 19 | File upload + Storage | `storage/`, form update |
| 20 | Plugin system | `plugins/` |
| 21 | Event bus | `events.py` |
| 22 | Auth model extensibility | `admin.py`, `auth/` updates |
| 23 | Role seeding | `seeding.py` |
| 24 | E2E tests + demo app | `demo/`, `tests/test_e2e.py` |
