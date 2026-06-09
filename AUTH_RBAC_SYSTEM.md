# Auth Model Extensibility & RBAC Configuration

> **Scope:** How the admin's built-in auth model works, how developers replace or extend
> it with their own User model, and how RBAC permissions bind to whichever model is active.
> This is a separate concern from the form system and should be read alongside the core spec.

---

## Table of Contents

1. [Design Goal](#1-design-goal)
2. [Built-in Auth Model (Default)](#2-built-in-auth-model-default)
3. [Extending the Built-in Model](#3-extending-the-built-in-model)
4. [Replacing With Your Own Model](#4-replacing-with-your-own-model)
5. [AuthBackend Protocol](#5-authbackend-protocol)
6. [RBAC — How It Binds to the Auth Model](#6-rbac--how-it-binds-to-the-auth-model)
7. [Permission Tables](#7-permission-tables)
8. [PermissionChecker](#8-permissionchecker)
9. [FastAPI Dependencies for Route Protection](#9-fastapi-dependencies-for-route-protection)
10. [RBAC Configuration Per Model](#10-rbac-configuration-per-model)
11. [Field-Level Permissions](#11-field-level-permissions)
12. [UI Adapts to Permissions](#12-ui-adapts-to-permissions)
13. [Default Roles & Seeding](#13-default-roles--seeding)
14. [Role Management UI](#14-role-management-ui)
15. [Authentication Flow](#15-authentication-flow)
16. [Custom Auth — Full Examples](#16-custom-auth--full-examples)
17. [Config Reference](#17-config-reference)
18. [Edge Cases & Security Notes](#18-edge-cases--security-notes)

---

## 1. Design Goal

The admin ships with a working, zero-config auth system out of the box. But real
projects always have their own user table. The system must support three modes without
requiring a rewrite of RBAC logic:

| Mode | When to use |
|---|---|
| **Built-in** | Greenfield project; no existing user model |
| **Extend built-in** | Want to add extra columns to admin users (department, avatar, etc.) |
| **Bring your own model** | Existing `User` table in your app; don't want two user tables |

In all three modes, the RBAC layer (roles, permissions, permission checks, UI
adaptation) works identically. RBAC is decoupled from the auth model via a protocol.

---

## 2. Built-in Auth Model (Default)

When you do not configure a custom auth model, the admin creates and uses these tables:

```sql
CREATE TABLE admin_users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role_id         INTEGER REFERENCES admin_roles(id) ON DELETE SET NULL,
    is_superuser    BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE admin_roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE admin_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    table_name  VARCHAR(255) NOT NULL,
    can_view    BOOLEAN DEFAULT FALSE,
    can_create  BOOLEAN DEFAULT FALSE,
    can_edit    BOOLEAN DEFAULT FALSE,
    can_delete  BOOLEAN DEFAULT FALSE,
    UNIQUE(role_id, table_name)
);

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

**SQLAlchemy models:**

```python
# fastapi_admin/auth/models.py

class AdminRole(Base):
    __tablename__ = "admin_roles"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    users       = relationship("AdminUser", back_populates="role")
    permissions = relationship("AdminPermission", back_populates="role", cascade="all, delete-orphan")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id              = Column(Integer, primary_key=True)
    email           = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255))
    role_id         = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)
    is_superuser    = Column(Boolean, default=False)
    is_active       = Column(Boolean, default=True)
    last_login      = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    role = relationship("AdminRole", back_populates="users")
```

**Zero config setup:**

```python
# main.py — admin creates its own tables; developer does nothing extra
from fastapi_admin import Admin

admin = Admin(app=app, engine=engine, secret_key=os.environ["SECRET_KEY"])
# Tables created automatically via admin.setup()
```

---

## 3. Extending the Built-in Model

Add extra columns without replacing the model. Use SQLAlchemy's single-table
inheritance or a simple subclass approach:

### Option A — Add columns directly (recommended)

```python
# myapp/admin_config.py

from fastapi_admin.auth.models import AdminUser as _AdminUser

class AdminUser(_AdminUser):
    """
    Extend the built-in AdminUser with extra columns.
    Must set __tablename__ to the SAME table ("admin_users") — this is
    a mixin extension, not a new table.
    """
    __tablename__ = "admin_users"           # same table
    __table_args__ = {"extend_existing": True}

    department   = Column(String(100))
    avatar_url   = Column(String(500))
    phone        = Column(String(50))
    timezone     = Column(String(50), default="UTC")


# Tell admin to use your extended model
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    auth_model=AdminUser,               # <-- your extended class
)
```

Your extended `AdminUser` works everywhere the built-in one does. RBAC,
audit logging, session handling — all use your class transparently.

### Option B — Add a linked profile table

Useful when you want the extra data in a separate table:

```python
class AdminUserProfile(Base):
    __tablename__ = "admin_user_profiles"

    id           = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, ForeignKey("admin_users.id"), unique=True)
    department   = Column(String(100))
    avatar_url   = Column(String(500))

    admin_user   = relationship("AdminUser", back_populates="profile")
```

The admin's auth system uses `AdminUser` directly; you manage the profile table yourself.

---

## 4. Replacing With Your Own Model

When your app already has a `users` table and you don't want a second user table.

### Step 1 — Implement the `AdminUserProtocol`

Your model must satisfy this protocol. It does not need to inherit from anything:

```python
# fastapi_admin/auth/protocol.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class AdminUserProtocol(Protocol):
    """
    Any user model passed as auth_model= must satisfy this interface.
    These are the only attributes the admin framework reads from the user object.
    """
    id: int | str                      # primary key (any type)
    email: str                         # used for audit log denormalization
    is_active: bool                    # inactive users are refused login
    is_superuser: bool                 # bypasses all permission checks if True

    # Role linkage — the admin reads this to look up permissions.
    # Must be either:
    #   (a) an integer FK to admin_roles.id  (simplest)
    #   (b) None — then the user has no role and all permissions default to False
    role_id: int | None
```

Your model may have hundreds of other columns — the admin only uses these five attributes.

### Step 2 — Implement `AuthBackend`

The auth backend handles login verification and user loading. This is where you bridge
your model's password scheme and lookup logic:

```python
# fastapi_admin/auth/backend.py — base class

class AuthBackend(ABC):

    @abstractmethod
    async def authenticate(self, email: str, password: str, session) -> AdminUserProtocol | None:
        """
        Verify credentials. Return user object if valid, None if not.
        Called on POST /admin/login.
        """
        ...

    @abstractmethod
    async def get_user(self, user_id: int | str, session) -> AdminUserProtocol | None:
        """
        Load user by PK. Called on every protected request.
        Return None if user doesn't exist or is_active=False.
        """
        ...
```

### Step 3 — Wire it up

```python
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    auth_model=User,                   # your SQLAlchemy model
    auth_backend=MyAuthBackend(),      # your AuthBackend implementation
)
```

The admin will use your model for everything. The RBAC tables (`admin_roles`,
`admin_permissions`, `admin_field_permissions`) are still created and managed by the
admin — they reference `role_id` from your user object without caring about the source table.

---

## 5. AuthBackend Protocol

### Built-in backend (default, no config needed)

```python
# fastapi_admin/auth/backends/builtin.py

class BuiltinAuthBackend(AuthBackend):
    """Used when auth_model is not configured — works with AdminUser."""

    async def authenticate(self, email: str, password: str, session) -> AdminUser | None:
        user = session.query(AdminUser).filter_by(email=email, is_active=True).first()
        if not user:
            return None
        if not bcrypt.verify(password, user.hashed_password):
            return None
        return user

    async def get_user(self, user_id: int, session) -> AdminUser | None:
        return session.query(AdminUser).filter_by(id=user_id, is_active=True).first()
```

### Example — custom backend for an existing app model

```python
# myapp/admin_auth.py

from passlib.context import CryptContext
from myapp.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AppUserAuthBackend(AuthBackend):

    async def authenticate(self, email: str, password: str, session) -> User | None:
        user = session.query(User).filter_by(
            email=email,
            is_active=True,
            is_staff=True,          # your app's "can access admin" flag
        ).first()
        if not user:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        return user

    async def get_user(self, user_id: int, session) -> User | None:
        return session.query(User).filter_by(
            id=user_id,
            is_active=True,
            is_staff=True,
        ).first()
```

### Example — OAuth / SSO backend (no password check)

```python
class SSOAuthBackend(AuthBackend):

    async def authenticate(self, email: str, password: str, session) -> User | None:
        # Password field is ignored — auth is done via SSO redirect
        # This method is called after SSO callback sets the email in session
        return session.query(User).filter_by(email=email, is_active=True).first()

    async def get_user(self, user_id: int, session) -> User | None:
        return session.query(User).filter_by(id=user_id).first()
```

---

## 6. RBAC — How It Binds to the Auth Model

RBAC uses exactly one thing from the user object: `user.role_id`.

```
Request arrives
    │
    ▼
Middleware reads session cookie → decodes user_id
    │
    ▼
AuthBackend.get_user(user_id, session) → user object
    │
    ├── user.is_superuser == True → skip all permission checks, allow everything
    │
    └── user.role_id → look up admin_permissions row for (role_id, table_name)
                    → check can_view / can_create / can_edit / can_delete
                    → 403 if denied
```

The admin does **not** care whether `user` is an `AdminUser`, your app's `User`, or any
other class — as long as it has `role_id`, `is_superuser`, `is_active`, and `email`.

The `admin_roles` and `admin_permissions` tables are always owned by the admin.
They reference `role_id` as a plain integer. Your user model stores that `role_id`
wherever you like — it's just an integer foreign key:

```python
# Your model — role_id can point to admin_roles even from your own users table
class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True)
    email        = Column(String(255))
    password_hash = Column(String(255))
    is_active    = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_staff     = Column(Boolean, default=False)  # your "can access admin" flag

    # This FK is what the admin RBAC reads
    admin_role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)

    @property
    def role_id(self):
        # Protocol requires attribute named "role_id"
        return self.admin_role_id
```

---

## 7. Permission Tables

```sql
-- Roles — editable via admin UI
CREATE TABLE admin_roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Model-level permissions (one row per role × registered model)
CREATE TABLE admin_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    table_name  VARCHAR(255) NOT NULL,     -- matches RegisteredModel.table_name
    can_view    BOOLEAN DEFAULT FALSE,
    can_create  BOOLEAN DEFAULT FALSE,
    can_edit    BOOLEAN DEFAULT FALSE,
    can_delete  BOOLEAN DEFAULT FALSE,
    UNIQUE(role_id, table_name)
);

-- Field-level permissions (optional, more granular)
CREATE TABLE admin_field_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    table_name  VARCHAR(255) NOT NULL,
    field_name  VARCHAR(255) NOT NULL,
    can_view    BOOLEAN DEFAULT TRUE,
    can_edit    BOOLEAN DEFAULT TRUE,
    UNIQUE(role_id, table_name, field_name)
);

-- Indexes
CREATE INDEX idx_perm_role_table ON admin_permissions(role_id, table_name);
CREATE INDEX idx_field_perm ON admin_field_permissions(role_id, table_name);
```

---

## 8. PermissionChecker

```python
# fastapi_admin/auth/permissions.py

class PermissionChecker:
    """
    Instantiated once per request (via Depends).
    Caches results in-memory for the lifetime of the request.
    """

    def __init__(self, session, user: AdminUserProtocol):
        self.session = session
        self.user = user
        self._cache: dict[tuple, bool] = {}

    def has_permission(self, table_name: str, action: str) -> bool:
        """
        action: "view" | "create" | "edit" | "delete"
        Returns True if allowed, False otherwise.
        Superusers always return True.
        """
        if self.user.is_superuser:
            return True

        cache_key = (self.user.role_id, table_name, action)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.user.role_id is None:
            self._cache[cache_key] = False
            return False

        perm = self.session.query(AdminPermission).filter_by(
            role_id=self.user.role_id,
            table_name=table_name,
        ).first()

        result = bool(perm and getattr(perm, f"can_{action}", False))
        self._cache[cache_key] = result
        return result

    def get_allowed_fields(self, table_name: str, mode: str) -> set[str] | None:
        """
        mode: "view" | "edit"
        Returns set of allowed field names, or None if no field-level restrictions.
        None means ALL fields are allowed (no restriction rows exist for this role+table).
        """
        if self.user.is_superuser:
            return None  # no restrictions

        if self.user.role_id is None:
            return set()  # no role → no fields

        rows = self.session.query(AdminFieldPermission).filter_by(
            role_id=self.user.role_id,
            table_name=table_name,
        ).all()

        if not rows:
            return None  # no field-level rules → all fields allowed

        attr = "can_view" if mode == "view" else "can_edit"
        return {r.field_name for r in rows if getattr(r, attr)}

    def permission_set(self, table_name: str) -> "PermissionSet":
        """Returns a PermissionSet dataclass for convenient template use."""
        return PermissionSet(
            can_view=self.has_permission(table_name, "view"),
            can_create=self.has_permission(table_name, "create"),
            can_edit=self.has_permission(table_name, "edit"),
            can_delete=self.has_permission(table_name, "delete"),
        )


@dataclass
class PermissionSet:
    can_view: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
```

---

## 9. FastAPI Dependencies for Route Protection

### `require_permission` — dependency factory

```python
# fastapi_admin/auth/dependencies.py

def require_permission(table_name: str, action: str):
    """
    Returns a FastAPI dependency that enforces a permission.

    Usage in route definition:
        @router.get("/")
        async def list_view(_=Depends(require_permission("products", "view"))):
            ...

    Usage in route factory (auto-generated routes):
        router.add_api_route(
            "/",
            list_view_factory(registered),
            methods=["GET"],
            dependencies=[Depends(require_permission(registered.table_name, "view"))]
        )
    """
    async def _check(
        request: Request,
        checker: PermissionChecker = Depends(get_permission_checker),
    ):
        if not checker.has_permission(table_name, action):
            raise HTTPException(
                status_code=403,
                detail=f"You do not have permission to {action} {table_name}."
            )

    return _check


async def get_current_admin_user(request: Request, session=Depends(get_session)) -> AdminUserProtocol:
    """Reads session cookie, decodes user_id, loads user from DB."""
    user_id = session_backend.decode(request.cookies.get("admin_session"))
    if not user_id:
        raise HTTPException(status_code=401)

    backend = request.app.state.admin_auth_backend
    user = await backend.get_user(user_id, session)
    if not user or not user.is_active:
        raise HTTPException(status_code=401)

    return user


async def get_permission_checker(
    user: AdminUserProtocol = Depends(get_current_admin_user),
    session=Depends(get_session),
) -> PermissionChecker:
    return PermissionChecker(session=session, user=user)
```

### Auto-wiring in route generation

Every auto-generated model route injects the correct permission dependency
automatically. Developers who write custom routes can use the same dependency:

```python
# Auto-generated (router.py)
router.add_api_route("/",       list_view,   methods=["GET"],  dependencies=[Depends(require_permission(tbl, "view"))])
router.add_api_route("/create", create_form, methods=["GET"],  dependencies=[Depends(require_permission(tbl, "create"))])
router.add_api_route("/create", create_post, methods=["POST"], dependencies=[Depends(require_permission(tbl, "create"))])
router.add_api_route("/{id}",   edit_form,   methods=["GET"],  dependencies=[Depends(require_permission(tbl, "edit"))])
router.add_api_route("/{id}",   edit_post,   methods=["POST"], dependencies=[Depends(require_permission(tbl, "edit"))])
router.add_api_route("/{id}/delete", delete, methods=["POST"], dependencies=[Depends(require_permission(tbl, "delete"))])

# Developer's custom route (manual)
@router.get("/products/export")
async def export_products(
    _=Depends(require_permission("products", "view")),
    user=Depends(get_current_admin_user),
):
    ...
```

---

## 10. RBAC Configuration Per Model

### Exclude a model from RBAC (always allow)

```python
@admin.register(PublicConfig)
class PublicConfigAdmin(ModelAdmin):
    rbac_exempt = True   # no permission checks — any logged-in user can access
```

### Restrict to superusers only

```python
@admin.register(AdminUser)
class AdminUserAdmin(ModelAdmin):
    superuser_only = True  # require is_superuser=True, not just a role permission
```

### Custom permission action names

By default the four actions are `view`, `create`, `edit`, `delete`. You can define
additional custom actions for bulk operations or special routes:

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    custom_actions = [
        Action(
            name="mark_shipped",
            label="Mark as Shipped",
            permission="edit",          # which base permission is required
            bulk=True,                  # appears in bulk action dropdown
        ),
        Action(
            name="refund",
            label="Issue Refund",
            permission="custom:refund", # custom permission — admin checks admin_permissions for this action name
            bulk=False,
        ),
    ]
```

Custom permissions with `custom:` prefix require a `can_custom_refund` boolean column
be added to `admin_permissions` via migration. Built-in actions (`view`, `create`,
`edit`, `delete`) are always present.

---

## 11. Field-Level Permissions

Field-level permissions restrict which form fields a role can see or edit. They are
optional — if no rows exist for a role+table combination, all fields are allowed.

### How they work

When the form renders, the admin calls:

```python
allowed_view = checker.get_allowed_fields(table_name, "view")
allowed_edit = checker.get_allowed_fields(table_name, "edit")
```

If `allowed_view` is `None` → all fields shown.
If `allowed_view` is a `set` → only those field names rendered in form/list.

Fields not in `allowed_edit` are rendered as `ReadOnlyWidget` even if they'd normally
be editable. Fields not in `allowed_view` are completely absent from the HTML.

### Configuring field permissions via code (seed)

```python
# Seed field permissions for the "Support" role
# Support can view all Product fields but cannot edit price or cost_price

support_role = session.query(AdminRole).filter_by(name="Support").first()

product_fields = inspect_model(Product).columns
for col in product_fields:
    can_edit = col.name not in ("price", "cost_price", "margin")
    session.add(AdminFieldPermission(
        role_id=support_role.id,
        table_name="products",
        field_name=col.name,
        can_view=True,
        can_edit=can_edit,
    ))
session.commit()
```

### Configuring via the Role Management UI

The role edit page shows a two-level permission matrix:

```
ROLE: Support
───────────────────────────────────────────────────────────
MODEL           VIEW   CREATE   EDIT   DELETE
───────────────────────────────────────────────────────────
Products         ✅      ❌       ✅      ❌
  ↳ Field-level permissions [expand]
     name          view ✅  edit ✅
     price         view ✅  edit ❌   ← greyed out input
     cost_price    view ✅  edit ❌
     stock         view ✅  edit ✅
Orders            ✅      ❌       ❌      ❌
Users             ✅      ❌       ❌      ❌
───────────────────────────────────────────────────────────
[Save All Permissions]
```

---

## 12. UI Adapts to Permissions

Templates receive a `permissions` object and conditionally show/hide elements.
The UI never shows a button the user can't use — it's not just a 403 fallback.

```jinja2
{# pages/list.html #}

{% if permissions.can_create %}
  <a href="{{ url_for('admin_create', model=model_name) }}" class="btn-primary">
    + New {{ verbose_name }}
  </a>
{% endif %}

{# Bulk-select column only if can_delete #}
{% if permissions.can_delete %}
  <th><input type="checkbox" id="select-all"></th>
{% endif %}

{# Per-row actions #}
{% if permissions.can_edit %}
  <a href="{{ url_for('admin_edit', model=model_name, id=obj.id) }}" class="action-link">Edit</a>
{% endif %}
{% if permissions.can_delete %}
  <button
    hx-post="{{ url_for('admin_delete', model=model_name, id=obj.id) }}"
    hx-confirm="Delete this {{ verbose_name }}?"
    class="action-link action-danger"
  >Delete</button>
{% endif %}
```

```jinja2
{# pages/form.html #}

{# Delete button only on edit form, only if can_delete #}
{% if not is_create and permissions.can_delete %}
  <button
    hx-post="{{ delete_url }}"
    hx-confirm="Permanently delete this {{ verbose_name }}?"
    class="btn-danger"
  >Delete</button>
{% endif %}

{# Readonly fields are rendered differently, not skipped #}
{% for field_ctx in all_field_contexts %}
  {% if field_ctx.meta.name in hidden_fields %}
    {# skip — no HTML at all #}
  {% else %}
    {{ render_field(field_ctx, model_name) }}
  {% endif %}
{% endfor %}
```

### Sidebar navigation

The sidebar only lists models the current user can view:

```jinja2
{# partials/sidebar.html #}
{% for model in registered_models %}
  {% set perm = current_user_permissions[model.table_name] %}
  {% if perm.can_view %}
    <a href="/admin/{{ model.table_name }}/" class="nav-link">
      {{ model.icon }} {{ model.verbose_name_plural }}
    </a>
  {% endif %}
{% endfor %}
```

---

## 13. Default Roles & Seeding

On first startup, `admin.setup()` creates these roles if no roles exist:

| Role | view | create | edit | delete | Notes |
|---|---|---|---|---|---|
| `SuperAdmin` | ✅ all | ✅ all | ✅ all | ✅ all | Equivalent to `is_superuser=True` |
| `Admin` | ✅ all | ✅ all | ✅ all | ✅ except `admin_users` | Protects user management |
| `Editor` | ✅ all | ✅ content models | ✅ content models | ❌ | Content models = non-system models |
| `Viewer` | ✅ all | ❌ | ❌ | ❌ | Read-only access |

These are starting defaults only. All roles and permissions can be freely edited
at runtime via the Role Management UI.

**Customising seed roles:**

```python
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    seed_roles=[
        SeedRole(
            name="Finance",
            description="Finance team — read invoices, edit payments",
            permissions={
                "invoices":  {"view": True, "create": False, "edit": False, "delete": False},
                "payments":  {"view": True, "create": True,  "edit": True,  "delete": False},
                "customers": {"view": True, "create": False, "edit": False, "delete": False},
            }
        ),
    ],
    seed_roles_overwrite=False,  # True = replace existing roles on every startup (dev only)
)
```

---

## 14. Role Management UI

**Route:** `GET /admin/roles/`

### Role list page

```
ROLES                                          [+ New Role]
──────────────────────────────────────────────────────────
Name         Description            Users    Actions
──────────────────────────────────────────────────────────
SuperAdmin   Full system access       1      Edit | Delete
Admin        Site administration      3      Edit | Delete
Editor       Content editing          8      Edit | Delete
Finance      Finance team access      2      Edit | Delete
Viewer       Read-only access         5      Edit | Delete
──────────────────────────────────────────────────────────
```

### Role edit page

Contains the permission matrix. Each row = a registered model. Each column = an action.
Field-level section is collapsible per model.

**POST body** on "Save All Permissions":

```
role_id=3
perm[products][view]=on
perm[products][edit]=on
perm[orders][view]=on
perm[orders][create]=on
perm[orders][edit]=on
field_perm[products][price][view]=on
field_perm[products][price][edit]=
```

Server processes: upserts one `AdminPermission` row per model in the matrix,
and one `AdminFieldPermission` row per field in the expanded field section.

---

## 15. Authentication Flow

### Login

```
POST /admin/login
  Body: email=..., password=...
      │
      ▼
  AuthBackend.authenticate(email, password, session)
      │
  ├── Returns None → flash "Invalid credentials", re-render login
      │
  └── Returns user object
          │
          ▼
      Build session payload: {"user_id": user.id, "issued_at": unix_timestamp}
      Sign with itsdangerous.TimestampSigner(SECRET_KEY)
          │
          ▼
      Set cookie:
        Name:      admin_session
        Value:     signed payload
        HttpOnly:  True
        SameSite:  Lax
        Secure:    True (if HTTPS)
        Max-Age:   SESSION_TTL (default 28800 = 8 hours)
          │
          ▼
      Update user.last_login = now()
      RedirectResponse → /admin/
```

### Protected Request

```
GET /admin/products/
    │
    ▼
SessionMiddleware reads "admin_session" cookie
    │
    ▼
itsdangerous verifies signature + expiry
    │
  ├── Invalid/expired → redirect to /admin/login?next=/admin/products/
    │
  └── Valid → extract user_id
        │
        ▼
    AuthBackend.get_user(user_id, session) → user object
        │
      ├── None or is_active=False → redirect to login
        │
      └── Valid user → request.state.admin_user = user
            │
            ▼
        require_permission("products", "view") dependency fires
            │
          ├── 403 if denied
          └── Continues → view handler runs
```

### Logout

```
POST /admin/logout
    │
    ▼
Delete "admin_session" cookie
RedirectResponse → /admin/login
```

---

## 16. Custom Auth — Full Examples

### Example A — App already has a User model, no new table

```python
# myapp/models.py (existing)
class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    email         = Column(String(255), unique=True)
    password_hash = Column(String(255))
    is_active     = Column(Boolean, default=True)
    is_staff      = Column(Boolean, default=False)   # gates admin access
    is_superuser  = Column(Boolean, default=False)
    admin_role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)

    @property
    def role_id(self):
        return self.admin_role_id
```

```python
# myapp/admin_auth.py
from fastapi_admin.auth.backend import AuthBackend
from passlib.context import CryptContext
from myapp.models import User

pwd = CryptContext(schemes=["bcrypt"])

class AppAuthBackend(AuthBackend):

    async def authenticate(self, email: str, password: str, session) -> User | None:
        user = session.query(User).filter_by(email=email, is_active=True, is_staff=True).first()
        if not user or not pwd.verify(password, user.password_hash):
            return None
        return user

    async def get_user(self, user_id: int, session) -> User | None:
        return session.query(User).filter_by(id=user_id, is_active=True, is_staff=True).first()
```

```python
# main.py
from fastapi_admin import Admin
from myapp.models import User
from myapp.admin_auth import AppAuthBackend

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    auth_model=User,
    auth_backend=AppAuthBackend(),
)
```

### Example B — SSO (no password, email from OAuth callback)

```python
# myapp/admin_auth.py

class SSOAuthBackend(AuthBackend):

    async def authenticate(self, email: str, password: str, session) -> User | None:
        # "password" is ignored — SSO flow sets email directly from OAuth token
        return session.query(User).filter_by(email=email, is_active=True).first()

    async def get_user(self, user_id: int, session) -> User | None:
        return session.query(User).filter_by(id=user_id, is_active=True).first()
```

```python
# SSO callback route (your code, outside admin)
@app.get("/auth/callback")
async def sso_callback(request: Request, code: str):
    token = await oauth.exchange(code)
    email = token["email"]
    # Set email in session so the admin login endpoint can read it
    request.session["sso_email"] = email
    return RedirectResponse("/admin/login")
```

The admin login page in SSO mode hides the password field and auto-submits using the
`sso_email` session value.

---

## 17. Config Reference

All auth and RBAC settings are passed to `Admin()`:

```python
admin = Admin(
    # Required
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],     # signs session cookies

    # Auth model (optional — defaults to built-in AdminUser)
    auth_model=User,                          # your SQLAlchemy model class
    auth_backend=AppAuthBackend(),            # your AuthBackend implementation

    # Session
    session_ttl=28800,                        # seconds; default = 8 hours
    session_cookie_name="admin_session",      # default
    session_secure=True,                      # set False for local HTTP dev

    # RBAC
    seed_roles=[...],                         # SeedRole list; applied on first run
    seed_roles_overwrite=False,               # True = re-seed on every startup

    # Admin path
    admin_path="/admin",                      # change to "/ops" etc. for obscurity

    # Superuser shortcut — bypass RBAC entirely for specific emails
    superuser_emails=["owner@example.com"],   # always treated as superuser
)
```

---

## 18. Edge Cases & Security Notes

| Scenario | Handling |
|---|---|
| User deleted while logged in | `get_user()` returns None → cookie invalidated, redirect to login |
| User's role deleted | `role_id` becomes NULL → all permissions default to False; user can log in but sees nothing |
| `is_active` set to False | `get_user()` returns None on next request; forced logout |
| `is_superuser` added to existing session | No re-login needed; `get_user()` loads fresh object each request |
| Permission rows missing for a model | Defaults to False for all actions (deny by default) |
| No roles defined at all | Only superusers can do anything; other users denied everywhere |
| Concurrent permission edits | Last-write-wins on the permission matrix; no transaction isolation issue because role permissions are low-write |
| Session secret key rotation | All existing sessions immediately invalidated; all users must re-login |
| Brute-force on login | Use `slowapi` rate limiter on `POST /admin/login`; default: 5 attempts/minute per IP |
| CSRF on state-changing POST routes | HTMX sends `HX-Request: true` header; validate it on all admin POSTs |
| Cookie theft (XSS) | `HttpOnly=True` prevents JS access; Content-Security-Policy header restricts script sources |
| `role_id` tampered in cookie | Not possible — cookie is signed with `SECRET_KEY`; any tamper invalidates signature |
| Superuser creating another superuser | Only existing superusers can set `is_superuser=True` on AdminUser create/edit form; enforced in `on_create` / `on_update` hook |
| FK to `admin_roles` from user's own table | Add a DB migration to add `admin_role_id` column; no admin migration needed |
| Custom auth model missing required Protocol attrs | Admin raises `ConfigError` at startup with a clear message listing missing attributes |
