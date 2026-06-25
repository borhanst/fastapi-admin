### 6. Fix Permission Enforcement Gap in View Context

**Files:** `fastapi_admin/views/context.py:296-301`, `fastapi_admin/views/context.py:332-334`, `fastapi_admin/views/context.py:351-353`

**Problem:** `ViewContextBuilder` hardcodes `PermissionSet(can_view=True, can_create=True, can_edit=True, can_delete=True)` in `build_list_context()`, `build_form_context()`, and `build_delete_context()`. Route-level `require_permission()` works, but template context never reflects actual user permissions — UI shows buttons the user cannot use.

**Solution:** Thread `PermissionChecker` through `ViewContextBuilder` to compute actual `PermissionSet` from the user's role.

#### Phase 1: Update ViewContextBuilder

- [ ] 1.1 Add `PermissionChecker` parameter to `build_list_context()`
  - Accept `checker: PermissionChecker` or `user: AdminUserProtocol`
  - Call `checker.permission_set(table_name)` instead of hardcoded values

- [ ] 1.2 Add `PermissionChecker` parameter to `build_form_context()`
  - Accept `checker: PermissionChecker`
  - Call `checker.permission_set(table_name)` instead of hardcoded values

- [ ] 1.3 Add `PermissionChecker` parameter to `build_delete_context()`
  - Accept `checker: PermissionChecker`
  - Call `checker.permission_set(table_name)` instead of hardcoded values

#### Phase 2: Update ViewFactory Callers

- [ ] 2.1 Update `fastapi_admin/views/factory.py`
  - Pass `PermissionChecker` from dependency injection to context builder

- [ ] 2.2 Update `fastapi_admin/views/roles.py`
  - Pass `PermissionChecker` to context builder methods

#### Phase 3: Tests

- [ ] 3.1 Create tests in `tests/test_view_context_permissions.py`
  - Test list context with different permission sets
  - Test form context with different permission sets
  - Test delete context with different permission sets
  - Test superuser bypass
  - Test viewer role (read-only) context

### 7. Resolve Sync/Async Mismatch in Auth Backend

**Files:** `fastapi_admin/auth/backend.py:54-76`, `fastapi_admin/auth/dependencies.py:33-52`

**Problem:** `BuiltinAuthBackend` declared `async` but uses synchronous `session.query()`. `auth/dependencies.py` creates sync engine from async engine URL. Interface promises async but implementation blocks.

**Solution:** Use `AsyncSession` with `await session.execute()` throughout for true async I/O.

#### Phase 1: Update AuthBackend Interface

- [ ] 1.1 Update `fastapi_admin/auth/backend.py`
  - Change `BuiltinAuthBackend.authenticate()` to use `AsyncSession`
  - Replace `session.query()` with `await session.execute(select(...))`
  - Change `BuiltinAuthBackend.get_user()` to use `AsyncSession`

#### Phase 2: Update Dependencies

- [ ] 2.1 Update `fastapi_admin/auth/dependencies.py`
  - Remove `_get_sync_engine()` function
  - Update `_get_db_session()` to yield `AsyncSession`
  - Use `app.state.admin_db_session` (already async) directly

- [ ] 2.2 Update `fastapi_admin/auth/permissions.py`
  - Change `PermissionChecker.__init__()` to accept `AsyncSession`
  - Update `has_permission()` to use `await session.execute()`
  - Update `get_allowed_fields()` to use `await session.execute()`

#### Phase 3: Tests

- [ ] 3.1 Update `tests/test_auth.py`
  - Test async auth backend with `AsyncSession`
  - Test permission checker with async queries

### 8. Replace app.state with Typed AdminState

**Files:** `fastapi_admin/admin/core.py`, `fastapi_admin/auth/dependencies.py:20-52`

**Problem:** Over a dozen items stored on `app.state` with no type safety. Components communicate by reading arbitrary attributes. Typos or missing attributes fail silently at runtime.

**Solution:** Create typed `AdminState` dataclass, store as single `app.state.admin` attribute.

#### Phase 1: Create AdminState Dataclass

- [ ] 1.1 Create `fastapi_admin/admin/state.py` with `AdminState` class
  - Fields: `engine`, `session_backend`, `auth_backend`, `storage`, `registry`, `db_session`, `config`, `jinja_env`, `admin_instance`
  - Add type annotations for all fields
  - Add `@classmethod from_app_state(cls, app_state)` factory method

#### Phase 2: Update Admin Setup

- [ ] 2.1 Update `fastapi_admin/admin/core.py`
  - Create `AdminState` instance during `setup()`
  - Store as single `app.state.admin` attribute
  - Remove individual attribute assignments

#### Phase 3: Update All Consumers

- [ ] 3.1 Update `fastapi_admin/auth/dependencies.py`
  - Replace `request.app.state.admin_*` with `request.app.state.admin.*`
  - Use typed fields instead of `getattr()` with defaults

- [ ] 3.2 Update `fastapi_admin/views/dashboard.py`
  - Replace `request.app.state.admin_*` with `request.app.state.admin.*`

- [ ] 3.3 Update `fastapi_admin/views/context.py`
  - Replace `request.app.state.admin_db_session` with `request.app.state.admin.db_session`

#### Phase 4: Tests

- [ ] 4.1 Create tests in `tests/test_admin_state.py`
  - Test `AdminState` construction
  - Test `from_app_state()` factory
  - Test type safety (missing attributes raise clear errors)

### 9. Remove Duplicate Inspection Code

**Files:** `fastapi_admin/inspection.py` (101 lines), `fastapi_admin/inspection/__init__.py` (101 lines)

**Problem:** Two files contain identical `inspect_model()` function. Root-level `inspection.py` is a legacy artifact. Understanding which is authoritative requires comparing both.

**Solution:** Delete root-level duplicate, ensure all imports point to package.

#### Phase 1: Remove Duplicate

- [ ] 1.1 Delete `fastapi_admin/inspection.py`
  - Verify no imports depend on root-level module
  - Update any imports that reference `fastapi_admin.inspection` (root) to `fastapi_admin.inspection` (package)

#### Phase 2: Verify Imports

- [ ] 2.1 Search codebase for `from fastapi_admin.inspection import`
  - Ensure all imports work correctly
  - Run test suite to verify no breakage

### 10. Create API Layer for External Frontend Apps

**Files:** New module `fastapi_admin/api/`

**Problem:** Admin serves only HTML via Jinja2 templates. No JSON API for external frontend apps (React, Vue, mobile). User wants "api to use external."

**Solution:** Create `fastapi_admin/api/` module with JSON endpoints sharing same RBAC system.

#### Phase 1: API Router

- [ ] 1.1 Create `fastapi_admin/api/__init__.py` with `AdminAPIRouter` class
  - Fields: `registry`, `permission_checker`, `auth_backend`
  - Methods: `build_api_router()`, `register_model_routes()`

- [ ] 1.2 Create `fastapi_admin/api/auth.py` with token-based authentication
  - JWT or API key authentication for external clients
  - Reuse `AuthBackend` protocol for user loading
  - Endpoint: `POST /api/auth/token` to obtain token

#### Phase 2: CRUD Endpoints

- [ ] 2.1 Create `fastapi_admin/api/crud.py` with JSON CRUD handlers
  - `GET /api/{model}/` — list with pagination, search, filters
  - `POST /api/{model}/` — create
  - `GET /api/{model}/{id}` — retrieve
  - `PUT /api/{model}/{id}` — update
  - `DELETE /api/{model}/{id}` — delete
  - All endpoints use `require_permission()` dependency

- [ ] 2.2 Create `fastapi_admin/api/schemas.py` with Pydantic models
  - Request/response schemas for each model
  - Pagination schema
  - Error response schema

#### Phase 3: Integration

- [ ] 3.1 Update `fastapi_admin/admin/core.py`
  - Add `api_router` parameter to `Admin.__init__()`
  - Mount API router alongside HTML admin router
  - Configurable API path (default: `/api`)

#### Phase 4: Tests

- [ ] 4.1 Create tests in `tests/test_api.py`
  - Test token authentication
  - Test CRUD operations with permissions
  - Test pagination and filtering
  - Test error responses (401, 403, 404)

### 11. Clean Up or Implement Shallow Placeholder Modules

**Files:** `fastapi_admin/filters/__init__.py`, `fastapi_admin/actions/__init__.py`, `fastapi_admin/plugins/__init__.py`, `fastapi_admin/dashboard/__init__.py`

**Problem:** Four empty modules (just `__init__.py`). Deleting any provides no benefit — they have no complexity. But they also provide no leverage.

**Solution:** Remove empty placeholders or implement them.

#### Phase 1: Remove Unused Placeholders

- [ ] 1.1 Delete `fastapi_admin/plugins/__init__.py`
  - No current use case
  - Can be re-added when plugin system is designed

- [ ] 1.2 Delete `fastapi_admin/dashboard/__init__.py`
  - Dashboard logic already in `fastapi_admin/views/dashboard.py`
  - Empty module adds no value

#### Phase 2: Implement Filters Module

- [ ] 2.1 Create `fastapi_admin/filters/base.py` with `Filter` ABC
  - Methods: `apply(query, value)`, `get_choices(session)`

- [ ] 2.2 Create `fastapi_admin/filters/registry.py` with `FilterRegistry`
  - Register custom filters per model
  - Auto-generate filters from column types

#### Phase 3: Implement Actions Module

- [ ] 3.1 Create `fastapi_admin/actions/base.py` with `Action` ABC
  - Methods: `execute(objects, request)`, `get_confirmation_message()`

- [ ] 3.2 Create `fastapi_admin/actions/registry.py` with `ActionRegistry`
  - Register custom actions per model
  - Auto-generate bulk actions (delete, export)