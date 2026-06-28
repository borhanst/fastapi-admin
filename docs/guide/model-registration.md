# Model Registration

Register your SQLAlchemy models with the admin to get automatic CRUD UIs.

## Basic Registration

### Pattern A — Zero Config

Register a model with no configuration:

```python
from fastapi_console import Admin

admin = Admin(app, engine, secret_key="...")
admin.register(Product)
```

This gives you:

- List view at `/admin/products/`
- Create form at `/admin/products/create`
- Edit form at `/admin/products/{id}`
- Delete at `/admin/products/{id}/delete`

### Pattern B — Partial Override

Override specific settings while keeping defaults for the rest:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price", "stock"]
    search_fields = ["name", "sku"]
    list_filter = ["category", "is_active"]
```

### Pattern C — Full Override

Control every aspect of the admin view:

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

## ModelAdmin Options

### List View

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `list_display` | `list[str]` | All columns | Columns to show in list view |
| `list_filter` | `list[str]` | `None` | Fields to filter by (sidebar) |
| `search_fields` | `list[str]` | `None` | Fields to search across |
| `ordering` | `list[str]` | `None` | Default sort order |
| `per_page` | `int` | `20` | Rows per page |

### Form View

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fields` | `list[str]` | All fields | Fields to show in form |
| `exclude` | `list[str]` | `None` | Fields to hide from form |
| `readonly_fields` | `list[str]` | `None` | Fields shown but not editable |

### Labels

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `verbose_name` | `str` | Auto | Human-readable name (e.g., "Product") |
| `verbose_name_plural` | `str` | Auto | Plural name (e.g., "Products") |
| `icon` | `str` | `None` | Sidebar icon (Heroicon name) |

## Auto-Discovery

When you register a model, the system automatically:

1. **Inspects columns** — Detects all column types
2. **Maps to widgets** — Maps SQLAlchemy types to UI components
3. **Generates routes** — Creates list, create, edit, delete routes
4. **Handles relationships** — Renders FK dropdowns and relationship pickers

### Column Type Mapping

| SQLAlchemy Type | UI Widget |
|-----------------|-----------|
| `String`, `VARCHAR` | Text input |
| `Text` | Textarea |
| `Integer`, `BigInteger` | Number input |
| `Float`, `Numeric` | Number input (step=0.01) |
| `Boolean` | Toggle switch |
| `Date` | Date picker |
| `DateTime` | Datetime picker |
| `Enum` | Select dropdown |
| `JSON` | JSON editor |
| `ForeignKey` | Searchable dropdown |

## Override Hooks

Customize behavior at specific lifecycle points:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    
    def get_queryset(self, session, request):
        """Filter records globally"""
        return session.query(self.model).filter_by(is_deleted=False)
    
    def get_object(self, session, id):
        """Custom PK lookup"""
        return session.get(self.model, id)
    
    def on_create(self, obj, request):
        """Called before INSERT"""
        obj.created_by = request.state.admin_user.id
    
    def after_create(self, obj, request):
        """Called after INSERT commit"""
        send_notification(f"New product: {obj.name}")
    
    def on_update(self, obj, data, request):
        """Called before UPDATE"""
        pass
    
    def after_update(self, obj, request):
        """Called after UPDATE commit"""
        pass
    
    def on_delete(self, obj, request):
        """Called before DELETE"""
        pass
    
    def after_delete(self, obj, request):
        """Called after DELETE commit"""
        pass
```

## Custom Actions

Add bulk actions to the list view:

```python
from fastapi_console.actions import Action

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    
    def get_actions(self):
        return [
            Action(name="activate", label="Activate Selected"),
            Action(name="deactivate", label="Deactivate Selected"),
        ]
    
    def perform_activate(self, session, selected_ids):
        """Bulk activate products"""
        session.query(Product).filter(Product.id.in_(selected_ids)).update(
            {Product.is_active: True}, synchronize_session=False
        )
    
    def perform_deactivate(self, session, selected_ids):
        """Bulk deactivate products"""
        session.query(Product).filter(Product.id.in_(selected_ids)).update(
            {Product.is_active: False}, synchronize_session=False
        )
```

## Customizing Built-in Admin Models

FastAPI Console ships with default admin classes for built-in models (users, roles, audit logs, etc.). You can customize these by inheriting from the default classes.

### Available Built-in Admin Classes

| Class | Model | Icon | Description |
|-------|-------|------|-------------|
| `AdminUserAdmin` | `AdminUser` | `group` | Admin user management |
| `AdminRoleAdmin` | `AdminRole` | `shield-check` | Role management |
| `AdminRefreshTokenAdmin` | `AdminRefreshToken` | `key` | Refresh tokens |
| `AdminPermissionAdmin` | `AdminPermission` | `lock` | Table permissions |
| `AdminFieldPermissionAdmin` | `AdminFieldPermission` | `lock` | Field-level permissions |
| `AuditLogAdmin` | `AuditLog` | `clock` | Audit trail |
| `AdminUserTOTPAdmin` | `AdminUserTOTP` | `lock` | 2FA tokens |
| `AdminLoginAttemptAdmin` | `AdminLoginAttempt` | `clock` | Login attempts |

### Method 1 — Register Before Setup

Define your custom class and register it before calling `admin.setup()`:

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi_console import Admin
from fastapi_console.auth.models import AdminUser
from fastapi_console.admin.builtin_models import AdminUserAdmin

# Inherit from the default class
class MyAdminUserAdmin(AdminUserAdmin):
    list_display = ["id", "email", "full_name", "is_active"]
    search_fields = ["email", "full_name"]
    list_filter = ["is_active", "is_superuser"]

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///./db.sqlite")
admin = Admin(app=app, engine=engine, secret_key="...")

# Register your custom class (before setup)
admin.register(AdminUser, MyAdminUserAdmin)

# Setup will skip the default registration
@app.on_event("startup")
async def startup():
    await admin.setup(app)
```

### Method 2 — Unregister and Re-register

If you need to change the admin class after setup, use `unregister()`:

```python
from fastapi_console.auth.models import AdminUser, AdminRole
from fastapi_console.admin.builtin_models import AdminUserAdmin, AdminRoleAdmin

class MyAdminUserAdmin(AdminUserAdmin):
    list_display = ["id", "email", "full_name"]
    verbose_name = "Team Member"
    verbose_name_plural = "Team Members"

class MyAdminRoleAdmin(AdminRoleAdmin):
    list_display = ["id", "name", "description"]
    search_fields = ["name"]

# Unregister then re-register
admin.unregister(AdminUser)
admin.register(AdminUser, MyAdminUserAdmin)

admin.unregister(AdminRole)
admin.register(AdminRole, MyAdminRoleAdmin)
```

### Inheriting Defaults

When you subclass a built-in admin class, you inherit all defaults:

- `tag` — Sidebar group (default: `"admin"`)
- `icon` — Sidebar icon (inherited from parent)
- `verbose_name` / `verbose_name_plural` — Display names
- `list_display` — Columns shown in list view
- `search_fields` — Searchable fields
- `exclude` — Hidden fields

Override only what you need:

```python
class MyAdminUserAdmin(AdminUserAdmin):
    # Only override what you want to change
    list_display = ["id", "email", "is_active"]
    # Everything else (tag, icon, verbose_name, etc.) stays the same
```

## Relationship Handling

### ForeignKey (Many-to-One)

Automatically rendered as a searchable dropdown:

```python
class Product(Base):
    __tablename__ = "products"
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category")
```

The dropdown shows all categories and allows searching by name.

### One-to-Many

Related records shown as a sub-table below the main form.

### Many-to-Many

Rendered as a multi-select with search and removable tags.

## Edge Cases

### Composite Primary Keys

```python
class OrderItem(Base):
    __tablename__ = "order_items"
    order_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, primary_key=True)
    quantity = Column(Integer)
```

The system detects composite PKs and uses all fields in route params.

### Abstract Base Models

```python
class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Product(TimestampMixin, Base):
    __tablename__ = "products"
    # ...
```

Abstract models (with `__abstract__ = True`) are skipped during auto-discovery.

### Password Fields

Columns named `password` or `*_password` automatically:

- Render as masked inputs
- Hash values with bcrypt on save
- Never display in list view

### Auto Timestamps

Columns with `server_default=func.now()` are automatically set to readonly.

## Next Steps

- [Authentication & RBAC](auth-rbac.md) — Set up roles and permissions
- [Widgets & Forms](widgets-forms.md) — Customize form fields
- [Plugins](plugins.md) — Extend the admin with plugins
