# Configuration

Customize the admin panel to fit your needs.

## Admin Initialization

```python
from fastapi_console import Admin

admin = Admin(
    app=app,
    engine=engine,
    secret_key="your-secret-key",
    # ... other options
)
```

## Configuration Options

### Branding

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | `str` | `"Admin"` | Admin panel title |
| `logo_url` | `str` | `None` | URL to logo image |
| `favicon_url` | `str` | `None` | URL to favicon |
| `primary_color` | `str` | `"#6366f1"` | Primary brand color (CSS) |
| `primary_color_dark` | `str` | `"#4f46e5"` | Primary color for dark mode |

### Behavior

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `admin_path` | `str` | `"/admin"` | URL prefix for admin |
| `per_page_default` | `int` | `20` | Default rows per page |
| `session_ttl` | `int` | `28800` | Session lifetime in seconds (8 hours) |
| `dark_mode_default` | `bool` | `False` | Start in dark mode |

### Audit Logging

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `audit_retention_days` | `int` | `None` | Days to keep audit logs (None = forever) |
| `audit_enabled` | `bool` | `True` | Enable/disable audit logging |

### Dashboard

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dashboard_stats` | `list[str]` | `None` | Models to show stats for |
| `dashboard_charts` | `bool` | `False` | Enable activity charts |

## Example Configuration

```python
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    
    # Branding
    title="Acme Corp Admin",
    logo_url="/static/acme-logo.svg",
    primary_color="#0ea5e9",
    primary_color_dark="#0284c7",
    
    # Behavior
    admin_path="/admin",
    per_page_default=25,
    session_ttl=28800,
    
    # Audit
    audit_retention_days=365,
    
    # Dashboard
    dashboard_stats=["products", "orders", "users"],
    dashboard_charts=True,
)
```

## Environment Variables

Store sensitive values in environment variables:

```python
import os

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
)
```

Set in your shell:

```bash
export SECRET_KEY="your-super-secret-key"
```

Or use a `.env` file with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## HTTPS in Production

When deploying behind a reverse proxy (nginx, Caddy):

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Or trust specific hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["admin.example.com"])
```

## Next Steps

- [Model Registration](../guide/model-registration.md) — Configure individual models
- [Authentication & RBAC](../guide/auth-rbac.md) — Set up roles and permissions
