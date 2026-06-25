# Authentication & RBAC

Set up user authentication and role-based access control.

## Authentication

### Built-in Auth (Default)

The admin ships with a complete auth system. No configuration needed:

```python
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
)
```

This creates:

- `admin_users` table
- `admin_roles` table
- `admin_permissions` table
- Login page at `/admin/login/`
- Session-based authentication

### Default Credentials

On first run, a superuser is created:

- **Email:** admin@example.com
- **Password:** admin

!!! warning
    Change the default password immediately in production!

### Authentication Flow

```
POST /admin/login/
    → Validate email + bcrypt password
    → Create signed session cookie
    → Redirect to /admin/

GET /admin/*
    → Read session cookie
    → Verify signature
    → Load AdminUser from DB
    → Inject into request.state.admin_user
```

### Session Configuration

```python
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    session_ttl=28800,  # 8 hours in seconds
)
```

## Extending the Built-in Model

### Add Extra Columns

```python
from fastapi_console.auth.models import AdminUser as _AdminUser

class AdminUser(_AdminUser):
    __tablename__ = "admin_users"  # Same table
    
    department = Column(String(100))
    avatar_url = Column(String(500))
    phone = Column(String(20))
```

### Replace with Your Own Model

```python
from fastapi_console.auth import AuthBackend

class MyUserBackend(AuthBackend):
    
    async def authenticate(self, email: str, password: str, session: Session):
        user = session.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_user(self, user_id: int, session: Session):
        return session.query(User).get(user_id)

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    auth_backend=MyUserBackend(),
)
```

## Role-Based Access Control (RBAC)

### How It Works

Every admin user has a role. Each role has permissions per model:

```
User → Role → Permissions → {model: {can_view, can_create, can_edit, can_delete}}
```

### Permission Tables

```sql
-- Roles
CREATE TABLE admin_roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Permissions per role per model
CREATE TABLE admin_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id),
    table_name  VARCHAR(255) NOT NULL,
    can_view    BOOLEAN DEFAULT FALSE,
    can_create  BOOLEAN DEFAULT FALSE,
    can_edit    BOOLEAN DEFAULT FALSE,
    can_delete  BOOLEAN DEFAULT FALSE
);
```

### Permission Checker

```python
from fastapi_console.auth.permissions import PermissionChecker

checker = PermissionChecker(session)

# Check if user can view products
if checker.has_permission(user, "products", "view"):
    # Show list view
    pass

# Check if user can edit products
if checker.has_permission(user, "products", "edit"):
    # Show edit form
    pass
```

### Superuser Bypass

Users with `is_superuser=True` bypass all permission checks:

```python
def has_permission(self, user, table_name, action):
    if user.is_superuser:
        return True
    # ... check permissions table
```

## Default Roles

| Role | View | Create | Edit | Delete |
|------|------|--------|------|--------|
| SuperAdmin | All | All | All | All |
| Admin | All | All | All | All (except users) |
| Editor | All | Content | Content | None |
| Viewer | All | None | None | None |

## FastAPI Dependencies

Use dependencies to protect routes:

```python
from fastapi_console.auth.dependencies import require_permission

@router.get("/products/")
async def list_products(
    _=Depends(require_permission("products", "view"))
):
    # Only users with view permission can access
    pass

@router.post("/products/")
async def create_product(
    _=Depends(require_permission("products", "create"))
):
    # Only users with create permission can access
    pass
```

## UI Adapts to Permissions

The admin UI automatically hides elements based on permissions:

```jinja2
{# Show create button only if user has permission #}
{% if permissions.can_create %}
    <a href="{{ url_for('admin_create', model=model_name) }}">
        + New {{ verbose_name }}
    </a>
{% endif %}

{# Show edit button only if user has permission #}
{% if permissions.can_edit %}
    <a href="{{ url_for('admin_edit', model=model_name, id=obj.id) }}">
        Edit
    </a>
{% endif %}

{# Show delete button only if user has permission #}
{% if permissions.can_delete %}
    <button hx-post="{{ url_for('admin_delete', model=model_name, id=obj.id) }}">
        Delete
    </button>
{% endif %}
```

## Role Management UI

Access the role management interface at `/admin/roles/`:

- List all roles with user counts
- Create new roles
- Edit role permissions
- Delete roles

### Permission Matrix Editor

The UI shows a table where:

- **Rows** = registered models
- **Columns** = actions (view, create, edit, delete)
- **Cells** = checkboxes

Check/uncheck permissions and click "Save" to update.

## Field-Level Permissions

Restrict access to specific fields:

```sql
CREATE TABLE admin_field_permissions (
    id          SERIAL PRIMARY KEY,
    role_id     INTEGER REFERENCES admin_roles(id),
    table_name  VARCHAR(255) NOT NULL,
    field_name  VARCHAR(255) NOT NULL,
    can_view    BOOLEAN DEFAULT TRUE,
    can_edit    BOOLEAN DEFAULT TRUE
);
```

### Check Field Permissions

```python
checker = PermissionChecker(session)

# Get allowed fields for viewing
allowed_fields = checker.get_allowed_field_names(user, "products", "view")

# Returns None if no restrictions (all allowed)
# Returns set of field names if restricted
```

## Custom Auth Backend

Implement your own authentication:

```python
from fastapi_console.auth import AuthBackend
from fastapi import HTTPException

class MyAuthBackend(AuthBackend):
    
    async def authenticate(self, email: str, password: str, session: Session):
        """Validate credentials and return user"""
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    async def get_user(self, user_id: int, session: Session):
        """Load user by ID from session"""
        return session.query(User).get(user_id)
    
    def get_user_id(self, user):
        """Extract user ID for session"""
        return user.id

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    auth_backend=MyAuthBackend(),
)
```

## Security Notes

### HTTPS in Production

Always use HTTPS in production:

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

### Secret Key

Use a strong, random secret key:

```python
import secrets
secret_key = secrets.token_urlsafe(32)
```

Store in environment variables, never in code.

### Session Security

Sessions are signed cookies, not encrypted. The payload is visible but tamper-proof:

```json
{ "user_id": 5, "issued_at": 1710000000 }
```

## Next Steps

- [Widgets & Forms](widgets-forms.md) — Customize form fields
- [Audit Logging](audit-logging.md) — Track all changes
- [Plugins](plugins.md) — Extend with custom plugins
