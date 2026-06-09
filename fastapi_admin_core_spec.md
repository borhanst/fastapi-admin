# FastAPI Admin — Core Feature Specification

> **Purpose:** This document is the authoritative specification for the 3 core differentiating features of the FastAPI Admin project. It is written for use with a coding agent. Each section contains architecture decisions, data models, implementation steps, file structure, and edge cases.

---

## Table of Contents

1. [Core Bet 1 — Zero-Config Auto-Discovery](#core-bet-1--zero-config-auto-discovery)
2. [Core Bet 2 — Built-in Audit Log + RBAC](#core-bet-2--built-in-audit-log--rbac)
3. [Core Bet 3 — Modern UI](#core-bet-3--modern-ui)
4. [How the 3 Features Connect](#how-the-3-features-connect)
5. [Project Folder Structure](#project-folder-structure)
6. [Tech Stack Summary](#tech-stack-summary)

---

## Core Bet 1 — Zero-Config Auto-Discovery

### Goal

When a developer registers a SQLAlchemy/SQLModel model with the admin, the system must:

- Inspect all columns and their types automatically
- Map each column type to the correct UI form element
- Auto-generate list, create, edit, and delete routes
- Require zero manual form or view definitions to get a working CRUD UI
- Still allow full override when needed, without fighting the framework

---

### 1.1 Model Registration API

The public API for registering models must support three usage patterns:

#### Pattern A — Zero config (fully automatic)
```python
admin.register(Product)
```

#### Pattern B — Partial override (change only what you need)
```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price", "stock"]
    search_fields = ["name", "sku"]
    list_filter = ["category", "is_active"]
```

#### Pattern C — Full override (custom everything)
```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price", "stock", "created_at"]
    search_fields = ["name", "sku", "description"]
    readonly_fields = ["created_at", "updated_at"]
    list_filter = ["category", "is_active", "brand"]
    ordering = ["-created_at"]
    per_page = 25
```

---

### 1.2 ModelAdmin Base Class

The `ModelAdmin` base class holds all default configuration. All fields are optional — unset fields fall back to auto-detected values.

```python
class ModelAdmin:
    # List view config
    list_display: list[str] | None = None       # columns to show; auto = all non-relationship columns
    list_filter: list[str] | None = None        # sidebar filter fields
    search_fields: list[str] | None = None      # fields to search across
    ordering: list[str] | None = None           # default sort e.g. ["-created_at"]
    per_page: int = 20                          # rows per page

    # Form config
    fields: list[str] | None = None             # fields to show in create/edit form
    exclude: list[str] | None = None            # fields to hide from form
    readonly_fields: list[str] | None = None    # shown but not editable

    # Labels and display
    verbose_name: str | None = None             # human name e.g. "Product"
    verbose_name_plural: str | None = None      # plural e.g. "Products"
    icon: str | None = None                     # sidebar icon name (Heroicon)

    # Object display
    def __str__(self, obj) -> str:              # how to display an object in dropdowns/links
        return str(getattr(obj, "name", None) or getattr(obj, "title", None) or f"#{obj.id}")
```

---

### 1.3 Model Registry

The registry is a singleton that holds all registered models and their admin configurations.

```python
# Location: fastapi_admin/registry.py

class AdminRegistry:
    _models: dict[str, RegisteredModel] = {}

    def register(self, model: type, admin_class: type[ModelAdmin] | None = None):
        # 1. Validate model is a SQLAlchemy mapped class
        # 2. If admin_class is None, create a default ModelAdmin instance
        # 3. Run auto-inspection (see 1.4)
        # 4. Store in _models keyed by model.__tablename__

    def get(self, table_name: str) -> RegisteredModel | None: ...

    def all(self) -> list[RegisteredModel]: ...

    def auto_discover(self):
        # Scan all subclasses of DeclarativeBase
        # Register any that haven't been manually registered
        from sqlalchemy.orm import DeclarativeBase
        for mapper in DeclarativeBase.registry.mappers:
            cls = mapper.class_
            if cls.__tablename__ not in self._models:
                self.register(cls)
```

**RegisteredModel dataclass:**
```python
@dataclass
class RegisteredModel:
    model: type                         # the SQLAlchemy model class
    admin: ModelAdmin                   # admin config (auto or user-provided)
    table_name: str                     # model.__tablename__
    verbose_name: str                   # human-readable name
    verbose_name_plural: str
    columns: list[ColumnMeta]           # auto-inspected column metadata
    relationships: list[RelationMeta]   # auto-inspected relationships
    pk_field: str                       # primary key field name
```

---

### 1.4 Auto-Inspection via SQLAlchemy Inspector

When a model is registered, the system inspects it to extract metadata.

```python
# Location: fastapi_admin/inspection.py

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty

def inspect_model(model: type) -> tuple[list[ColumnMeta], list[RelationMeta]]:
    mapper = inspect(model)
    columns = []
    relationships = []

    for col in mapper.columns:
        columns.append(ColumnMeta(
            name=col.key,
            type=col.type,
            nullable=col.nullable,
            primary_key=col.primary_key,
            foreign_keys=list(col.foreign_keys),
            default=col.default,
        ))

    for rel in mapper.relationships:
        relationships.append(RelationMeta(
            name=rel.key,
            direction=rel.direction.name,       # MANYTOONE, ONETOMANY, MANYTOMANY
            target_model=rel.mapper.class_,
            uselist=rel.uselist,
            back_populates=rel.back_populates,
        ))

    return columns, relationships
```

---

### 1.5 Column Type → UI Component Mapping

This mapping is the core of auto-discovery. Every SQLAlchemy type maps to a Jinja2 macro name.

| SQLAlchemy Type | UI Component Macro | Notes |
|---|---|---|
| `String`, `VARCHAR` | `text_input` | `maxlength` from column length |
| `Text` | `textarea` | rows=5 default |
| `Integer`, `BigInteger` | `number_input` | step=1 |
| `Float`, `Numeric`, `Decimal` | `number_input` | step=0.01 |
| `Boolean` | `toggle` | renders as toggle switch |
| `Date` | `date_picker` | HTML5 date input |
| `DateTime`, `TIMESTAMP` | `datetime_picker` | HTML5 datetime-local |
| `Time` | `time_picker` | HTML5 time input |
| `Enum` | `select` | options from enum values |
| `JSON`, `JSONB` | `json_editor` | CodeMirror or textarea with JSON validation |
| `LargeBinary` | `file_upload` | size limit warning |
| `UUID` | `text_input` | read-only if primary key |
| `ARRAY` | `tag_input` | add/remove tags |
| ForeignKey column | `relation_picker` | searchable async dropdown |
| `relationship()` uselist=True | `multi_relation_picker` | multi-select with search |
| `relationship()` uselist=False | `relation_picker` | single searchable dropdown |

**Implementation — the macro resolver:**
```python
# Location: fastapi_admin/field_types.py

from sqlalchemy import types as sa_types

COLUMN_TYPE_MAP = {
    sa_types.String: "text_input",
    sa_types.Text: "textarea",
    sa_types.Integer: "number_input",
    sa_types.BigInteger: "number_input",
    sa_types.Float: "number_input",
    sa_types.Numeric: "number_input",
    sa_types.Boolean: "toggle",
    sa_types.Date: "date_picker",
    sa_types.DateTime: "datetime_picker",
    sa_types.Enum: "select",
    sa_types.JSON: "json_editor",
    sa_types.LargeBinary: "file_upload",
    sa_types.Uuid: "text_input",
}

def resolve_widget(col: ColumnMeta) -> str:
    if col.foreign_keys:
        return "relation_picker"
    for sa_type, widget in COLUMN_TYPE_MAP.items():
        if isinstance(col.type, sa_type):
            return widget
    return "text_input"  # safe fallback
```

---

### 1.6 Auto-Generated Routes

For every registered model, these routes are created automatically under `/admin/{table_name}/`:

| Method | Path | Handler | Description |
|---|---|---|---|
| `GET` | `/admin/{model}/` | `list_view` | Paginated list of records |
| `GET` | `/admin/{model}/create` | `create_form` | Empty create form |
| `POST` | `/admin/{model}/create` | `create_submit` | Handle form POST, redirect |
| `GET` | `/admin/{model}/{id}` | `edit_form` | Populated edit form |
| `POST` | `/admin/{model}/{id}` | `edit_submit` | Handle form POST, redirect |
| `POST` | `/admin/{model}/{id}/delete` | `delete_submit` | Delete record, redirect |
| `POST` | `/admin/{model}/bulk` | `bulk_action` | Bulk delete or custom action |
| `GET` | `/admin/{model}/search` | `relation_search` | HTMX endpoint for FK dropdowns |

**Route registration:**
```python
# Location: fastapi_admin/router.py

def build_model_router(registered: RegisteredModel) -> APIRouter:
    router = APIRouter(prefix=f"/{registered.table_name}")
    
    router.add_api_route("/", list_view_factory(registered), methods=["GET"])
    router.add_api_route("/create", create_form_factory(registered), methods=["GET"])
    router.add_api_route("/create", create_submit_factory(registered), methods=["POST"])
    router.add_api_route("/{id}", edit_form_factory(registered), methods=["GET"])
    router.add_api_route("/{id}", edit_submit_factory(registered), methods=["POST"])
    router.add_api_route("/{id}/delete", delete_factory(registered), methods=["POST"])
    router.add_api_route("/bulk", bulk_factory(registered), methods=["POST"])
    router.add_api_route("/search", search_factory(registered), methods=["GET"])
    
    return router
```

---

### 1.7 Relationship Handling

#### ForeignKey (many-to-one)
- Rendered as a searchable `<select>` powered by HTMX
- On page load: show current value
- On user type: `GET /admin/{related_model}/search?q=...` returns `<option>` HTML fragments
- Display value: calls `__str__` on the related object

#### One-to-Many (inline editing)
- Show related records as a sub-table below the main form
- Each row has edit/delete actions
- "Add row" button appends a new empty inline form row
- Saves inline records on the parent form's POST

#### Many-to-Many
- Rendered as a multi-select with search
- Selected items shown as removable tags
- HTMX-powered search for options

---

### 1.8 Override Hooks

These methods on `ModelAdmin` can be overridden for custom behavior:

```python
class ModelAdmin:
    # Query hooks
    def get_queryset(self, session, request) -> Query:
        """Override to filter records globally (e.g. soft-delete filter)"""
        return session.query(self.model)

    def get_object(self, session, id) -> Any:
        """Override for custom PK lookup"""
        return session.get(self.model, id)

    # Form hooks
    def on_create(self, obj, request): pass    # called before INSERT
    def after_create(self, obj, request): pass  # called after INSERT commit
    def on_update(self, obj, data, request): pass
    def after_update(self, obj, request): pass
    def on_delete(self, obj, request): pass
    def after_delete(self, obj, request): pass

    # Custom actions
    def get_actions(self) -> list[Action]:
        return [Action(name="delete_selected", label="Delete Selected")]
```

---

### 1.9 Edge Cases to Handle

- **Composite primary keys** — detect, use all PK fields in route params
- **Abstract base models** — skip models where `__abstract__ = True`
- **Self-referential FKs** — detect when FK points to same table, use tree picker
- **Soft-delete fields** — if model has `deleted_at` column, offer filter toggle
- **Auto timestamps** — `created_at`, `updated_at` with `server_default` → auto readonly
- **Password fields** — if column name contains "password", render as masked input and hash on save
- **Large text fields** — if `Text` column, offer rich text editor toggle (off by default)

---

---

## Core Bet 2 — Built-in Audit Log + RBAC

---

## Part A: Audit Log

### Goal

Every create, update, and delete action performed through the admin is automatically recorded. No developer action required — it works out of the box for all registered models.

---

### 2A.1 Audit Log Database Schema

```sql
CREATE TABLE admin_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    user_email      VARCHAR(255),               -- denormalized for display after user deletion
    action          VARCHAR(10) NOT NULL,        -- CREATE | UPDATE | DELETE
    model_name      VARCHAR(255) NOT NULL,       -- e.g. "Product"
    table_name      VARCHAR(255) NOT NULL,       -- e.g. "products"
    object_id       VARCHAR(255) NOT NULL,       -- PK as string (handles UUID + int)
    object_repr     VARCHAR(500),               -- human label at time of action
    changes         JSONB,                       -- diff (null for CREATE/DELETE)
    full_snapshot   JSONB,                       -- full object state at time of action
    ip_address      VARCHAR(45),                -- IPv4 or IPv6
    user_agent      TEXT,
    timestamp       TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_audit_model ON admin_audit_log(model_name, table_name);
CREATE INDEX idx_audit_user ON admin_audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON admin_audit_log(timestamp DESC);
CREATE INDEX idx_audit_object ON admin_audit_log(table_name, object_id);
```

**SQLAlchemy model:**
```python
# Location: fastapi_admin/models/audit.py

class AuditLog(Base):
    __tablename__ = "admin_audit_log"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    user_email = Column(String(255))
    action = Column(String(10), nullable=False)   # "CREATE" | "UPDATE" | "DELETE"
    model_name = Column(String(255), nullable=False)
    table_name = Column(String(255), nullable=False)
    object_id = Column(String(255), nullable=False)
    object_repr = Column(String(500))
    changes = Column(JSON)
    full_snapshot = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

---

### 2A.2 Change Diff Format

For UPDATE actions, the `changes` field stores a structured before/after diff:

```json
{
  "price": {
    "before": 99.99,
    "after": 149.99
  },
  "stock": {
    "before": 10,
    "after": 0
  },
  "name": {
    "before": "Nike Air Max 90",
    "after": "Nike Air Max 90 (2024)"
  }
}
```

Only changed fields are included. Unchanged fields are omitted.

**Diff computation:**
```python
# Location: fastapi_admin/audit/diff.py

def compute_diff(before: dict, after: dict) -> dict:
    """Returns only fields that changed, with before/after values."""
    diff = {}
    all_keys = set(before.keys()) | set(after.keys())
    for key in all_keys:
        b = before.get(key)
        a = after.get(key)
        if b != a:
            diff[key] = {"before": serialize_value(b), "after": serialize_value(a)}
    return diff

def serialize_value(val) -> any:
    """Make values JSON-safe."""
    if isinstance(val, datetime): return val.isoformat()
    if isinstance(val, Decimal): return float(val)
    if isinstance(val, UUID): return str(val)
    if isinstance(val, bytes): return "<binary>"
    return val
```

---

### 2A.3 Capture Strategy — SQLAlchemy Event Hooks

Use SQLAlchemy's session events to capture changes transparently.

```python
# Location: fastapi_admin/audit/listener.py

from sqlalchemy import event
from sqlalchemy.orm import Session

def attach_audit_listener(session_factory, get_current_user_fn):
    """
    Call once at startup. Attaches hooks to the session.
    get_current_user_fn: a callable that returns the current admin user
    from context (e.g. a ContextVar set by middleware).
    """

    @event.listens_for(session_factory, "before_flush")
    def before_flush(session: Session, flush_context, instances):
        # Capture state of dirty objects BEFORE flush (for before-diff)
        for obj in session.dirty:
            if is_registered_model(obj):
                # Store snapshot of current (pre-flush) state
                obj._audit_before = snapshot(obj)

    @event.listens_for(session_factory, "after_flush")
    def after_flush(session: Session, flush_context):
        user = get_current_user_fn()

        for obj in session.new:
            if is_registered_model(obj):
                write_audit(session, user, "CREATE", obj, None, snapshot(obj))

        for obj in session.dirty:
            if is_registered_model(obj):
                before = getattr(obj, "_audit_before", {})
                after = snapshot(obj)
                diff = compute_diff(before, after)
                if diff:
                    write_audit(session, user, "UPDATE", obj, diff, after)

        for obj in session.deleted:
            if is_registered_model(obj):
                write_audit(session, user, "DELETE", obj, None, snapshot(obj))
```

**Context variable for current user (set by middleware):**
```python
# Location: fastapi_admin/audit/context.py

from contextvars import ContextVar
from fastapi import Request

_current_admin_user: ContextVar = ContextVar("current_admin_user", default=None)

def get_audit_user():
    return _current_admin_user.get()

# Middleware sets this on every admin request
async def audit_context_middleware(request: Request, call_next):
    user = request.state.admin_user  # set by auth middleware earlier
    token = _current_admin_user.set(user)
    try:
        response = await call_next(request)
    finally:
        _current_admin_user.reset(token)
    return response
```

---

### 2A.4 Snapshot Function

```python
def snapshot(obj) -> dict:
    """Convert a SQLAlchemy object to a JSON-safe dict."""
    mapper = inspect(type(obj))
    result = {}
    for col in mapper.columns:
        val = getattr(obj, col.key, None)
        result[col.key] = serialize_value(val)
    return result
```

---

### 2A.5 Audit Log UI

**Route:** `GET /admin/audit-log/`

**Page features:**
- Timeline-style feed sorted by timestamp descending
- Color coding: green = CREATE, yellow = UPDATE, red = DELETE
- Each entry shows: timestamp, user email, action badge, model name, object repr
- Click any entry → expand to see full diff or full snapshot
- Diff view: two-column before/after table, changed fields highlighted

**Filters (all via query params + HTMX):**
- `?model=Product` — filter by model
- `?user_id=5` — filter by admin user
- `?action=UPDATE` — filter by action type
- `?from=2024-01-01&to=2024-12-31` — date range
- `?object_id=42` — history of one specific record

**Per-object history:**
On every edit form, show a "History" tab that lists all audit log entries for that specific `(table_name, object_id)` — this is the Django LogEntry equivalent.

---

### 2A.6 Audit Log Retention

- Add a management command / scheduled task to purge logs older than N days
- Configurable at init time: `Admin(app, engine, audit_retention_days=365)`
- Default: keep forever (no purge)

---

---

## Part B: Role-Based Access Control (RBAC)

### Goal

Fine-grained, database-driven permissions. Each admin user has a role. Each role has a matrix of permissions per model and per action. The UI adapts to show only what the user is allowed to do.

---

### 2B.1 Database Schema

```sql
-- Admin users (separate from app users, or linked via user_id)
CREATE TABLE admin_users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role_id         INTEGER REFERENCES admin_roles(id),
    is_superuser    BOOLEAN DEFAULT FALSE,    -- bypasses all permission checks
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Roles
CREATE TABLE admin_roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,   -- e.g. "Editor", "Support", "Viewer"
    description TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Permission matrix: one row per (role, model, action)
CREATE TABLE admin_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    table_name  VARCHAR(255) NOT NULL,          -- matches RegisteredModel.table_name
    can_view    BOOLEAN DEFAULT FALSE,
    can_create  BOOLEAN DEFAULT FALSE,
    can_edit    BOOLEAN DEFAULT FALSE,
    can_delete  BOOLEAN DEFAULT FALSE,
    UNIQUE(role_id, table_name)
);

-- Optional: field-level permissions
CREATE TABLE admin_field_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    table_name  VARCHAR(255) NOT NULL,
    field_name  VARCHAR(255) NOT NULL,
    can_view    BOOLEAN DEFAULT TRUE,
    can_edit    BOOLEAN DEFAULT TRUE,
    UNIQUE(role_id, table_name, field_name)
);
```

---

### 2B.2 Permission Check Logic

```python
# Location: fastapi_admin/auth/permissions.py

class PermissionChecker:

    def __init__(self, session):
        self.session = session
        self._cache = {}  # cache per request

    def has_permission(self, user: AdminUser, table_name: str, action: str) -> bool:
        """action: 'view' | 'create' | 'edit' | 'delete'"""
        if user.is_superuser:
            return True

        cache_key = (user.id, table_name, action)
        if cache_key in self._cache:
            return self._cache[cache_key]

        perm = self.session.query(AdminPermission).filter_by(
            role_id=user.role_id,
            table_name=table_name,
        ).first()

        if not perm:
            result = False
        else:
            result = getattr(perm, f"can_{action}", False)

        self._cache[cache_key] = result
        return result

    def get_allowed_field_names(self, user: AdminUser, table_name: str, mode: str) -> set[str] | None:
        """
        Returns set of allowed field names for 'view' or 'edit'.
        Returns None if no field restrictions exist (all allowed).
        """
        if user.is_superuser:
            return None

        field_perms = self.session.query(AdminFieldPermission).filter_by(
            role_id=user.role_id,
            table_name=table_name,
        ).all()

        if not field_perms:
            return None  # no restrictions

        attr = "can_view" if mode == "view" else "can_edit"
        return {fp.field_name for fp in field_perms if getattr(fp, attr)}
```

---

### 2B.3 FastAPI Dependency for Route Protection

```python
# Location: fastapi_admin/auth/dependencies.py

from fastapi import Depends, HTTPException, status

def require_permission(table_name: str, action: str):
    """
    Dependency factory. Use in route definitions.
    
    Usage:
        @router.get("/products/")
        async def list_products(
            _=Depends(require_permission("products", "view"))
        ):
    """
    async def checker(
        request: Request,
        user: AdminUser = Depends(get_current_admin_user),
        checker: PermissionChecker = Depends(get_permission_checker),
    ):
        if not checker.has_permission(user, table_name, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to {action} {table_name}."
            )
        return user
    return checker
```

Auto-generated routes inject this dependency automatically:
```python
# In route factory (router.py)
router.add_api_route(
    "/",
    list_view_factory(registered),
    methods=["GET"],
    dependencies=[Depends(require_permission(registered.table_name, "view"))]
)
```

---

### 2B.4 UI Adapts to Permissions

The Jinja2 templates receive a `permissions` context object and conditionally render elements:

```jinja2
{# list.html #}
{% if permissions.can_create %}
    <a href="{{ url_for('admin_create', model=model_name) }}" class="btn-primary">
        + New {{ verbose_name }}
    </a>
{% endif %}

{% if permissions.can_delete %}
    <th><input type="checkbox" id="select-all"></th>  {# bulk select column #}
{% endif %}

{# In each row #}
{% if permissions.can_edit %}
    <a href="{{ url_for('admin_edit', model=model_name, id=obj.id) }}">Edit</a>
{% endif %}
{% if permissions.can_delete %}
    <button hx-post="{{ url_for('admin_delete', model=model_name, id=obj.id) }}">Delete</button>
{% endif %}
```

---

### 2B.5 Default Roles (Seeded on First Run)

| Role | view | create | edit | delete |
|---|---|---|---|---|
| `SuperAdmin` | ✅ all | ✅ all | ✅ all | ✅ all |
| `Admin` | ✅ all | ✅ all | ✅ all | ✅ (except users) |
| `Editor` | ✅ all | ✅ content | ✅ content | ❌ |
| `Viewer` | ✅ all | ❌ | ❌ | ❌ |

These are defaults only. All roles and permissions are editable at runtime via the Role Management UI.

---

### 2B.6 Role Management UI

**Route:** `GET /admin/roles/`

Features:
- List all roles with user count
- Create / edit / delete roles
- Permission matrix editor: a table where rows = registered models, columns = actions (view/create/edit/delete), cells = checkboxes
- "Save all" saves the entire matrix in one POST

---

### 2B.7 Authentication Flow

```
POST /admin/login
    → validate email + bcrypt password
    → create signed session cookie (using itsdangerous.TimestampSigner)
    → set cookie: HttpOnly=True, SameSite=Lax, Secure=True (prod)
    → redirect to /admin/

GET /admin/* (any protected route)
    → SessionMiddleware reads cookie
    → Decode + verify session signature
    → Load AdminUser from DB
    → Inject into request.state.admin_user
    → PermissionChecker validates action
```

**Session token structure (signed, not encrypted):**
```json
{ "user_id": 5, "issued_at": 1710000000 }
```
Signed with `SECRET_KEY` using `itsdangerous`. Expires after `SESSION_TTL` (default: 8 hours).

---

---

## Core Bet 3 — Modern UI

### Goal

The admin UI must be visually impressive, feel fast, and be genuinely usable. It should look like something a professional SaaS company would build — not like an open-source admin afterthought.

---

### 3.1 Technology Stack

| Concern | Technology | Reason |
|---|---|---|
| CSS | Tailwind CSS (CDN or compiled) | Utility-first, consistent, dark mode built-in |
| Interactivity | HTMX | Server-driven, works with Jinja2, no JS framework |
| Micro-interactions | Alpine.js | Dropdowns, toggles, modals with minimal JS |
| Icons | Heroicons (SVG sprites) | Tailwind-native, clean, free |
| Charts | Chart.js | Lightweight, enough for dashboard |
| Code/JSON editor | CodeMirror 6 | For JSON fields in forms |
| Templating | Jinja2 | FastAPI native via Starlette |
| Fonts | Inter (Google Fonts or self-hosted) | Clean sans-serif, industry standard for admin UIs |

---

### 3.2 Color System (CSS Variables)

All colors are defined as CSS variables so themes and white-labeling work by changing one block.

```css
/* Location: static/css/variables.css */

:root {
  /* Brand (configurable via Admin init) */
  --color-primary-50:  #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-500: #6366f1;   /* indigo-500 default */
  --color-primary-600: #4f46e5;
  --color-primary-700: #4338ca;

  /* Neutral */
  --color-gray-50:  #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-500: #6b7280;
  --color-gray-700: #374151;
  --color-gray-900: #111827;

  /* Semantic */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger:  #ef4444;
  --color-info:    #3b82f6;

  /* Layout */
  --sidebar-width: 256px;
  --topbar-height: 64px;
  --content-max-width: 1280px;
}

/* Dark mode */
[data-theme="dark"] {
  --color-gray-50:  #111827;
  --color-gray-100: #1f2937;
  --color-gray-200: #374151;
  --color-gray-500: #9ca3af;
  --color-gray-700: #d1d5db;
  --color-gray-900: #f9fafb;
  /* etc. */
}
```

**White-labeling injection (in base template):**
```jinja2
<style>
  :root {
    --color-primary-500: {{ admin_config.primary_color | default('#6366f1') }};
    --color-primary-600: {{ admin_config.primary_color_dark | default('#4f46e5') }};
  }
</style>
```

---

### 3.3 Template Structure

```
fastapi_admin/
└── templates/
    ├── base.html                   # master layout: sidebar + topbar + content slot
    ├── partials/
    │   ├── sidebar.html            # nav links, logo, user menu
    │   ├── topbar.html             # breadcrumb, search, dark mode toggle
    │   ├── flash_messages.html     # success/error toast banners
    │   ├── pagination.html         # reusable pagination component
    │   └── confirm_modal.html      # delete confirmation modal
    ├── pages/
    │   ├── login.html              # login page (standalone, no sidebar)
    │   ├── dashboard.html          # home page with stats + recent activity
    │   ├── list.html               # model list view
    │   ├── form.html               # create + edit form (shared)
    │   ├── delete_confirm.html     # delete confirmation page
    │   ├── audit_log.html          # audit log timeline page
    │   ├── audit_detail.html       # single audit entry with full diff
    │   ├── roles.html              # role list page
    │   └── role_form.html          # role edit + permission matrix
    └── macros/
        ├── form_fields.html        # all field type macros (text_input, select, toggle, etc.)
        ├── table.html              # list table macros
        └── icons.html              # SVG icon macro
```

---

### 3.4 Base Layout (base.html)

```
┌─────────────────────────────────────────────────────┐
│  TOPBAR: [☰ Logo]  Breadcrumb           [🌙] [User▾] │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│   SIDEBAR    │         CONTENT AREA                 │
│              │                                      │
│  Dashboard   │   {% block content %}{% endblock %}  │
│  ─────────   │                                      │
│  Models:     │                                      │
│  • Products  │                                      │
│  • Orders    │                                      │
│  • Users     │                                      │
│  ─────────   │                                      │
│  Audit Log   │                                      │
│  Roles       │                                      │
│  Settings    │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

Sidebar collapses to icon-only at `< 1024px`. Full hamburger at `< 768px`.

---

### 3.5 List View Page

**Layout:**
```
[Page Title: Products]                          [+ New Product]

Search: [___________________]  Filters: [Category ▾] [Active ▾]

☐  Name          Price    Stock    Category    Created        Actions
─────────────────────────────────────────────────────────────────────
☐  Nike Air Max  $149.99  12       Shoes       2024-01-15     Edit | Del
☐  Adidas Stan   $89.99   0        Shoes       2024-01-10     Edit | Del
...
─────────────────────────────────────────────────────────────────────
Showing 1–20 of 143    [◀ Prev]  1  2  3 ... 8  [Next ▶]
```

**HTMX behaviors:**
- Search input: `hx-get="/admin/{model}/?search={val}"` with `hx-trigger="keyup delay:300ms"` replaces `#table-body`
- Column header click: sorts by that column, replaces `#table-body`
- Filter change: replaces `#table-body`
- Pagination click: replaces `#table-wrapper` (includes pagination controls)
- Delete button: `hx-confirm` dialog, then replaces the `<tr>` with empty on success
- Bulk action: standard form POST on selected checkboxes

**Empty state:**
When no records match, show a centered illustration + message + "Create your first X" button.

---

### 3.6 Create / Edit Form Page

**Layout:**
```
[← Back to Products]

Edit Product: Nike Air Max 90
─────────────────────────────────────────────────────
  GENERAL INFORMATION
  ┌─────────────────────┬──────────────────────┐
  │ Name                │ SKU                  │
  │ [________________]  │ [________________]   │
  └─────────────────────┴──────────────────────┘
  Description
  [_________________________________________]
  [_________________________________________]

  PRICING & INVENTORY
  ┌─────────┬────────────┬──────────────────┐
  │ Price   │ Sale Price │ Stock            │
  │ [____]  │ [________] │ [______________] │
  └─────────┴────────────┴──────────────────┘

  RELATIONSHIPS
  Category:   [Shoes ▾ search...]
  Tags:       [Running ✕] [Summer ✕] [Add tag...]

─────────────────────────────────────────────────────
[Save and continue]   [Save and return to list]   [Delete]
```

**Behavior notes:**
- Section headings are collapsible (Alpine.js)
- Sticky save bar at bottom — always visible on long forms
- Inline validation: on blur, validate field via HTMX partial, show error below field
- FK picker: on type, fetch `/admin/{related_model}/search?q=x` and show dropdown
- File upload: show preview thumbnail after selection (image types)
- Unsaved changes warning: Alpine.js tracks form dirty state, warns on navigation away
- "History" tab on edit form: shows audit log for this specific record

---

### 3.7 Form Field Macros (macros/form_fields.html)

Each macro accepts a `field` object and renders the appropriate HTML.

```jinja2
{# Usage in form.html #}
{% from "macros/form_fields.html" import render_field %}
{% for field in form_fields %}
    {{ render_field(field, value=obj[field.name], errors=errors.get(field.name)) }}
{% endfor %}

{# Macro definitions #}
{% macro text_input(field, value, errors) %}
<div class="field-wrapper">
  <label for="{{ field.name }}">{{ field.label }}</label>
  <input
    type="text"
    id="{{ field.name }}"
    name="{{ field.name }}"
    value="{{ value or '' }}"
    {% if field.required %}required{% endif %}
    {% if field.readonly %}readonly{% endif %}
    class="form-input {% if errors %}border-red-500{% endif %}"
  >
  {% if errors %}<p class="field-error">{{ errors | join(', ') }}</p>{% endif %}
</div>
{% endmacro %}

{# toggle, select, textarea, date_picker, relation_picker macros follow same pattern #}
```

---

### 3.8 Dashboard Page

**Components:**

1. **Stat cards row** (4 cards)
   - Total records per top-4 most registered models
   - Or: user-configured via `Admin(dashboard_stats=[...])`

2. **Recent activity feed**
   - Last 10 audit log entries with icon, text summary, timestamp
   - Pulls from AuditLog table — no extra work needed

3. **Quick access**
   - Links to create new record for each registered model

4. **Optional chart area**
   - If `dashboard_charts=True` in Admin config
   - Chart.js line chart: records created per day for the last 30 days
   - Queries `COUNT(*) GROUP BY DATE(created_at)` for each major model

---

### 3.9 Dark Mode

```javascript
// Alpine.js store for theme
document.addEventListener('alpine:init', () => {
  Alpine.store('theme', {
    dark: localStorage.getItem('admin-theme') === 'dark' ||
          (!localStorage.getItem('admin-theme') &&
           window.matchMedia('(prefers-color-scheme: dark)').matches),
    toggle() {
      this.dark = !this.dark;
      localStorage.setItem('admin-theme', this.dark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    },
    init() {
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    }
  });
});
```

Toggle button in topbar:
```jinja2
<button @click="$store.theme.toggle()" class="topbar-icon-btn">
  <span x-show="!$store.theme.dark">🌙</span>
  <span x-show="$store.theme.dark">☀️</span>
</button>
```

---

### 3.10 Flash Messages (Toast Notifications)

```python
# Set in route handler after a successful action
from fastapi_admin.flash import add_flash

async def create_submit(...):
    # ... create the object
    add_flash(request, "success", f"{verbose_name} created successfully.")
    return RedirectResponse(url=list_url, status_code=303)
```

```jinja2
{# partials/flash_messages.html — included in base.html #}
{% for msg in get_flash_messages(request) %}
<div
  x-data="{ show: true }"
  x-init="setTimeout(() => show = false, 4000)"
  x-show="show"
  x-transition
  class="toast toast-{{ msg.type }}"
>
  {{ msg.text }}
</div>
{% endfor %}
```

Flash messages are stored in a signed session cookie, consumed on next render.

---

### 3.11 Loading & Performance Feel

**Skeleton loaders:**
On initial list load, render skeleton rows (gray animated bars) while HTMX fetches data. Remove once data arrives.

**HTMX loading indicator:**
```jinja2
<div id="loading-bar" class="htmx-indicator fixed top-0 left-0 w-full h-1 bg-primary-500"></div>
```
Automatically shown/hidden by HTMX during any request.

**Debounced search:**
```html
<input
  hx-get="/admin/products/"
  hx-trigger="keyup changed delay:300ms"
  hx-target="#table-wrapper"
  hx-include="[name='search']"
  name="search"
  placeholder="Search products..."
>
```

**Optimistic delete:**
On delete, immediately remove the `<tr>` from the DOM (Alpine.js), then confirm server success. On error, re-add the row with an error message.

---

### 3.12 White-Labeling Config

Full configuration available at `Admin()` init:

```python
admin = Admin(
    app=app,
    engine=engine,

    # Branding
    title="Acme Corp Admin",
    logo_url="/static/acme-logo.svg",
    favicon_url="/static/favicon.ico",
    primary_color="#0ea5e9",        # injected as CSS variable
    primary_color_dark="#0284c7",

    # Behavior
    dark_mode_default=False,        # or True to force dark
    per_page_default=25,
    session_ttl=28800,              # 8 hours in seconds
    audit_retention_days=365,

    # Dashboard
    dashboard_stats=["products", "orders", "users"],
    dashboard_charts=True,

    # Security
    admin_path="/admin",            # change to "/secret-panel" etc.
    secret_key=os.environ["SECRET_KEY"],
)
```

---

---

## How the 3 Features Connect

```
Developer registers a model
        │
        ▼
[AUTO-DISCOVERY]
Inspector scans model → builds ColumnMeta + RelationMeta
Auto-generates routes + forms
        │
        ▼
Admin user visits /admin/products/
        │
[RBAC CHECK]
require_permission("products", "view") dependency fires
→ loads AdminUser from session cookie
→ checks admin_permissions table
→ 403 if denied, continues if allowed
→ template receives permission flags (can_create, can_edit, can_delete)
        │
        ▼
[MODERN UI]
list.html renders using Jinja2 + Tailwind
HTMX powers search + filter + pagination without full reloads
Alpine.js handles toggles, modals, form dirty state
        │
        ▼
Admin user submits create/edit/delete form
        │
[AUDIT LOG]
SQLAlchemy after_flush event fires
→ computes diff (for UPDATE)
→ writes AuditLog row with user context, IP, changes JSON
→ visible immediately in /admin/audit-log/ and in the record's History tab
```

---

---

## Project Folder Structure

```
fastapi_admin/
├── __init__.py                     # Admin class, public API
├── admin.py                        # Admin class definition + init
├── registry.py                     # AdminRegistry singleton
├── inspection.py                   # SQLAlchemy model inspection
├── field_types.py                  # Column type → widget mapping
├── router.py                       # Auto-route generation
│
├── auth/
│   ├── __init__.py
│   ├── models.py                   # AdminUser, AdminRole SQLAlchemy models
│   ├── dependencies.py             # require_permission, get_current_admin_user
│   ├── permissions.py              # PermissionChecker class
│   ├── session.py                  # Session cookie helpers (itsdangerous)
│   └── views.py                    # Login, logout route handlers
│
├── audit/
│   ├── __init__.py
│   ├── models.py                   # AuditLog SQLAlchemy model
│   ├── listener.py                 # SQLAlchemy event hooks
│   ├── context.py                  # ContextVar for current user
│   ├── diff.py                     # compute_diff, serialize_value, snapshot
│   └── views.py                    # Audit log list + detail route handlers
│
├── views/
│   ├── __init__.py
│   ├── dashboard.py                # Dashboard route handler
│   ├── list.py                     # List view handler factory
│   ├── form.py                     # Create + edit form handler factories
│   ├── delete.py                   # Delete handler factory
│   └── roles.py                    # Role management route handlers
│
├── templates/
│   ├── base.html
│   ├── partials/                   # (see 3.3)
│   ├── pages/                      # (see 3.3)
│   └── macros/                     # (see 3.3)
│
├── static/
│   ├── css/
│   │   ├── variables.css           # CSS custom properties (see 3.2)
│   │   └── admin.css               # Base component styles
│   ├── js/
│   │   ├── admin.js                # Alpine.js stores, global behavior
│   │   └── htmx-config.js          # HTMX global config (CSRF header etc.)
│   └── icons/
│       └── heroicons.svg           # SVG sprite sheet
│
└── models/
    ├── __init__.py
    └── base.py                     # Base, metadata for admin tables
```

---

---

## Tech Stack Summary

| Layer | Technology | Version |
|---|---|---|
| Web framework | FastAPI | 0.111+ |
| ASGI server | Uvicorn | latest |
| ORM | SQLAlchemy | 2.x |
| Migrations | Alembic | latest |
| Templating | Jinja2 | 3.x (via Starlette) |
| CSS | Tailwind CSS | 3.x |
| Interactivity | HTMX | 1.9+ |
| Micro-JS | Alpine.js | 3.x |
| Icons | Heroicons | 2.x |
| Charts | Chart.js | 4.x |
| JSON editor | CodeMirror | 6.x |
| Auth sessions | itsdangerous | 2.x |
| Password hashing | passlib + bcrypt | latest |
| Settings | pydantic-settings | 2.x |
| Rate limiting | slowapi | latest |

---

*End of specification. This document covers all architectural decisions for the 3 core features. Implementation should follow the order: Auto-Discovery → Auth/RBAC → Audit Log → UI, as each layer depends on the previous.*
