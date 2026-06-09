# Plugin & Extension System

> **Scope:** Complete reference for every pluggable extension point in the FastAPI Admin
> framework. Covers how to customise widgets, form rendering, validation, routes, hooks,
> auth, RBAC, storage, middleware, dashboard, list views, audit log, sidebar, and the
> Admin init config itself. Designed for coding agents and senior developers building
> on top of the framework.

---

## Table of Contents

1.  [Architecture Overview](#1-architecture-overview)
2.  [Extension Point Map](#2-extension-point-map)
3.  [Plugin Registration API](#3-plugin-registration-api)
4.  [Widget Plugins](#4-widget-plugins)
    - 4.1 [New Widget Class](#41-new-widget-class)
    - 4.2 [Override Built-in Widget by Type](#42-override-built-in-widget-by-type)
    - 4.3 [Override Built-in Widget by Field Name Pattern](#43-override-built-in-widget-by-field-name-pattern)
    - 4.4 [Override HTML Macro Only](#44-override-html-macro-only)
    - 4.5 [Per-Model Widget Override](#45-per-model-widget-override)
    - 4.6 [Dynamic Widget Selection](#46-dynamic-widget-selection)
5.  [Form Pipeline Plugins](#5-form-pipeline-plugins)
    - 5.1 [Custom Field Label Resolver](#51-custom-field-label-resolver)
    - 5.2 [Custom Required Detector](#52-custom-required-detector)
    - 5.3 [Custom Field Ordering](#53-custom-field-ordering)
    - 5.4 [Fieldset Builder](#54-fieldset-builder)
    - 5.5 [Extra (Non-Model) Fields](#55-extra-non-model-fields)
    - 5.6 [Form Context Middleware](#56-form-context-middleware)
6.  [Validation Plugins](#6-validation-plugins)
    - 6.1 [Field Validator Method](#61-field-validator-method)
    - 6.2 [Object-Level Validator](#62-object-level-validator)
    - 6.3 [Global Validator Hook](#63-global-validator-hook)
    - 6.4 [Async Validator](#64-async-validator)
7.  [Lifecycle Hook Plugins](#7-lifecycle-hook-plugins)
    - 7.1 [Per-Model Hooks](#71-per-model-hooks)
    - 7.2 [Global Hooks via Event System](#72-global-hooks-via-event-system)
    - 7.3 [Hook Execution Order](#73-hook-execution-order)
8.  [Route Plugins](#8-route-plugins)
    - 8.1 [Add Custom Routes to a Model](#81-add-custom-routes-to-a-model)
    - 8.2 [Add Global Admin Routes](#82-add-global-admin-routes)
    - 8.3 [Override Auto-Generated Route Handlers](#83-override-auto-generated-route-handlers)
    - 8.4 [Custom Bulk Actions](#84-custom-bulk-actions)
9.  [List View Plugins](#9-list-view-plugins)
    - 9.1 [Custom Columns](#91-custom-columns)
    - 9.2 [Custom Filters](#92-custom-filters)
    - 9.3 [Custom Search Logic](#93-custom-search-logic)
    - 9.4 [Row Actions](#94-row-actions)
    - 9.5 [List View Template Override](#95-list-view-template-override)
10. [Auth Plugins](#10-auth-plugins)
    - 10.1 [Custom Auth Backend](#101-custom-auth-backend)
    - 10.2 [Custom Session Backend](#102-custom-session-backend)
    - 10.3 [Multi-Factor Auth Hook](#103-multi-factor-auth-hook)
    - 10.4 [OAuth / SSO Integration](#104-oauth--sso-integration)
11. [RBAC Plugins](#11-rbac-plugins)
    - 11.1 [Custom Permission Checker](#111-custom-permission-checker)
    - 11.2 [Attribute-Based Access Control (ABAC)](#112-attribute-based-access-control-abac)
    - 11.3 [Custom Permission Actions](#113-custom-permission-actions)
    - 11.4 [Row-Level Permissions](#114-row-level-permissions)
12. [Storage Plugins](#12-storage-plugins)
    - 12.1 [Storage Backend Protocol](#121-storage-backend-protocol)
    - 12.2 [Local Storage (Built-in)](#122-local-storage-built-in)
    - 12.3 [S3 / Object Storage](#123-s3--object-storage)
    - 12.4 [Custom Storage Backend](#124-custom-storage-backend)
13. [Middleware Plugins](#13-middleware-plugins)
    - 13.1 [Admin Request Middleware](#131-admin-request-middleware)
    - 13.2 [Audit Context Middleware](#132-audit-context-middleware)
    - 13.3 [Rate Limiting Middleware](#133-rate-limiting-middleware)
14. [Audit Log Plugins](#14-audit-log-plugins)
    - 14.1 [Custom Audit Writer](#141-custom-audit-writer)
    - 14.2 [Custom Snapshot Serializer](#142-custom-snapshot-serializer)
    - 14.3 [Audit Log Sink (external)](#143-audit-log-sink-external)
15. [Dashboard Plugins](#15-dashboard-plugins)
    - 15.1 [Custom Stat Cards](#151-custom-stat-cards)
    - 15.2 [Custom Charts](#152-custom-charts)
    - 15.3 [Custom Dashboard Widgets](#153-custom-dashboard-widgets)
    - 15.4 [Full Dashboard Override](#154-full-dashboard-override)
16. [UI & Template Plugins](#16-ui--template-plugins)
    - 16.1 [Custom Template Directory](#161-custom-template-directory)
    - 16.2 [Override Individual Templates](#162-override-individual-templates)
    - 16.3 [Inject Custom CSS / JS](#163-inject-custom-css--js)
    - 16.4 [Custom Sidebar Sections](#164-custom-sidebar-sections)
    - 16.5 [Custom Jinja2 Globals & Filters](#165-custom-jinja2-globals--filters)
17. [Inspector Plugins](#17-inspector-plugins)
    - 17.1 [Custom Column Type Inspector](#171-custom-column-type-inspector)
    - 17.2 [Custom Relationship Inspector](#172-custom-relationship-inspector)
18. [First-Party Plugin Packages](#18-first-party-plugin-packages)
19. [Third-Party Plugin Contract](#19-third-party-plugin-contract)
20. [Plugin Load Order & Conflicts](#20-plugin-load-order--conflicts)
21. [Complete Plugin Example — Rich Text Editor Plugin](#21-complete-plugin-example--rich-text-editor-plugin)
22. [Complete Plugin Example — Tenant Isolation Plugin](#22-complete-plugin-example--tenant-isolation-plugin)

---

## 1. Architecture Overview

The admin is built as a layered stack of replaceable components. Every layer exposes a
protocol (ABC or `Protocol` class). You plug in by implementing the protocol and
registering your implementation — nothing is monkey-patched.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin Init                               │
│  Admin(app, engine, plugins=[...], **overrides)                 │
│  Wires together all layers at startup                           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  Plugin Registry                       │
│  Collects all registered plugins       │
│  Resolves conflicts; last-write-wins   │
└────────────┬───────────────────────────┘
             │ provides to each layer
             ▼
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  Inspector Layer │   │   Auth Layer     │   │   RBAC Layer     │
  │  Column/Rel meta │   │  Backend/Session │   │  Checker/Rules   │
  └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
           │                      │                       │
           ▼                      ▼                       ▼
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  Widget Registry │   │  Hook/Event Bus  │   │  Route Factory   │
  │  Type→Widget map │   │  before/after    │   │  Auto-generated  │
  └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
           │                      │                       │
           ▼                      ▼                       ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Form Pipeline                                               │
  │  Fields → Widgets → FormContext → Template Render            │
  └──────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Template Layer (Jinja2)                                     │
  │  base.html → page templates → macros                        │
  └──────────────────────────────────────────────────────────────┘
           │
           ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Storage Layer          │  Audit Layer                       │
  │  LocalStorage / S3 / …  │  Writer / Serializer / Sinks      │
  └──────────────────────────────────────────────────────────────┘
```

Every arrow in the diagram is a protocol boundary — a place where you can insert your
own implementation.

---

## 2. Extension Point Map

Quick reference for finding the right extension point:

| What you want to change | Extension point | Section |
|---|---|---|
| Add a new form widget type | `Widget` subclass + `widget_registry.register_*` | §4.1 |
| Change HTML for existing widget | Override Jinja2 macro in custom template file | §4.4 |
| Change widget for specific field name | `widget_registry.register_name()` | §4.3 |
| Change widget for all columns of a type | `widget_registry.register_type()` | §4.2 |
| Change widget for one model's field | `ModelAdmin.formfield_overrides` | §4.5 |
| Add non-DB field to a form | `ModelAdmin.extra_fields` | §5.5 |
| Custom field labels | `LabelResolver` protocol | §5.1 |
| Field-level validation | `ModelAdmin.validate_{name}()` | §6.1 |
| Cross-field validation | `ModelAdmin.validate()` | §6.2 |
| Validate all models globally | `GlobalValidatorHook` | §6.3 |
| Run code before/after save | `ModelAdmin.on_create/after_create` etc. | §7.1 |
| React to any model change globally | `AdminEventBus.on("create", ...)` | §7.2 |
| Add routes to one model | `ModelAdmin.extra_routes` | §8.1 |
| Add global admin pages | `AdminPlugin.routes` | §8.2 |
| Replace a generated route handler | `ModelAdmin.list_view / create_view` etc. | §8.3 |
| Add bulk action | `ModelAdmin.get_actions()` | §8.4 |
| Custom list column (computed) | `ModelAdmin.list_display` + `get_{name}()` | §9.1 |
| Custom list filter | `ListFilter` subclass | §9.2 |
| Custom search logic | `ModelAdmin.get_search_results()` | §9.3 |
| Custom row actions | `ModelAdmin.row_actions` | §9.4 |
| Replace login/session | `AuthBackend` subclass | §10.1 |
| Custom session storage (Redis etc.) | `SessionBackend` subclass | §10.2 |
| MFA / 2FA hook | `AuthBackend.post_authenticate()` | §10.3 |
| OAuth / SSO | `OAuthPlugin` | §10.4 |
| Custom permission logic | `PermissionChecker` subclass | §11.1 |
| Attribute-based access | `ABACPermissionChecker` | §11.2 |
| Custom bulk action permission | `custom_actions` with `permission=` | §11.3 |
| Per-row visibility rules | `ModelAdmin.get_queryset()` | §11.4 |
| Custom file storage | `StorageBackend` subclass | §12.1 |
| Admin request middleware | `AdminMiddleware` protocol | §13.1 |
| Custom audit log destination | `AuditWriter` subclass | §14.1 |
| Custom JSON serialization for audit | `SnapshotSerializer` subclass | §14.2 |
| Send audit events to Datadog etc. | `AuditSink` | §14.3 |
| Dashboard stat cards | `StatCard` classes | §15.1 |
| Dashboard charts | `ChartWidget` classes | §15.2 |
| Full dashboard override | `Admin(dashboard_view=...)` | §15.4 |
| Override page template | Custom template directory + same filename | §16.2 |
| Inject CSS / JS | `Admin(extra_css=[], extra_js=[])` | §16.3 |
| Custom sidebar nav sections | `AdminPlugin.nav_items` | §16.4 |
| Jinja2 globals / filters | `Admin(jinja2_globals={}, jinja2_filters={})` | §16.5 |

---

## 3. Plugin Registration API

There are two ways to register plugins: **inline at init** (for small, project-specific
customisation) and **plugin packages** (for reusable, distributable plugins).

### Inline registration

```python
# main.py

from fastapi_admin import Admin
from fastapi_admin.widgets import widget_registry
from myapp.widgets import RichTextWidget
from myapp.storage import R2StorageBackend
from myapp.auth import AppAuthBackend
from myapp.models import User

# Register widgets globally BEFORE Admin() is constructed
widget_registry.register_name("content", RichTextWidget)
widget_registry.register_name("body", RichTextWidget)

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],

    # Auth
    auth_model=User,
    auth_backend=AppAuthBackend(),

    # Storage
    storage=R2StorageBackend(account_id="...", bucket="media"),

    # UI
    extra_css=["/static/myapp/admin-overrides.css"],
    extra_js=["/static/myapp/rich-text.js"],
    extra_macro_files=["myapp/templates/macros/my_widgets.html"],
)
```

### Plugin package registration

For reusable plugins that bundle widgets, macros, routes, hooks, and nav items together:

```python
# fastapi_admin/plugins/base.py

class AdminPlugin(ABC):
    """
    Base class for a self-contained admin plugin package.
    Implement any subset of the hook methods below.
    """

    name: str = "unnamed_plugin"        # unique identifier
    version: str = "0.1.0"

    # ── Widget registration ──────────────────────────────────────────
    def register_widgets(self, registry: WidgetRegistry) -> None:
        """Called once at startup. Register widgets here."""
        pass

    # ── Template resources ───────────────────────────────────────────
    def get_macro_files(self) -> list[str]:
        """Return list of macro template file paths to include."""
        return []

    def get_template_dirs(self) -> list[str]:
        """Return list of Jinja2 template directories to prepend."""
        return []

    def get_static_files(self) -> list[StaticMount]:
        """Return extra static file mounts."""
        return []

    def get_css_urls(self) -> list[str]:
        """URLs injected into <head> in base.html."""
        return []

    def get_js_urls(self) -> list[str]:
        """URLs injected before </body> in base.html."""
        return []

    # ── Navigation ───────────────────────────────────────────────────
    def get_nav_items(self) -> list[NavItem]:
        """Sidebar nav items added by this plugin."""
        return []

    # ── Routes ───────────────────────────────────────────────────────
    def get_routes(self) -> APIRouter | None:
        """
        Return an APIRouter with additional admin routes.
        Mounted under /admin/ automatically.
        """
        return None

    # ── Event hooks ──────────────────────────────────────────────────
    def on_startup(self, admin: "Admin") -> None:
        """Called after all setup is complete."""
        pass

    def on_shutdown(self, admin: "Admin") -> None:
        pass

    # ── Dashboard contribution ───────────────────────────────────────
    def get_dashboard_widgets(self) -> list["DashboardWidget"]:
        return []

    # ── Jinja2 extensions ───────────────────────────────────────────
    def get_jinja2_globals(self) -> dict:
        return {}

    def get_jinja2_filters(self) -> dict:
        return {}
```

**Registering a plugin package:**

```python
from fastapi_admin_rich_text import RichTextPlugin
from fastapi_admin_s3 import S3Plugin

admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    plugins=[
        RichTextPlugin(toolbar="full", cdn="cloudflare"),
        S3Plugin(bucket="my-bucket", region="us-east-1"),
    ],
)
```

The admin calls each plugin's methods at the correct point during startup.
Plugin order in the list matters only when two plugins register the same thing
(last plugin wins).

---

## 4. Widget Plugins

### 4.1 New Widget Class

The minimum implementation for a custom widget:

```python
# myapp/widgets/currency.py

from fastapi_admin.widgets.base import Widget, FieldMeta
from decimal import Decimal, InvalidOperation


class CurrencyWidget(Widget):
    """
    Renders an amount input with a currency symbol prefix.
    Parses to Python Decimal. Validates min/max bounds.
    """
    macro_name = "currency_input"   # must match a Jinja2 macro

    def __init__(self, currency: str = "USD", symbol: str = "$",
                 min_value: Decimal | None = None,
                 max_value: Decimal | None = None):
        self.currency = currency
        self.symbol = symbol
        self.min_value = min_value
        self.max_value = max_value

    def render_context(self, field: FieldMeta, value) -> dict:
        ctx = super().render_context(field, value)
        ctx.update({
            "currency": self.currency,
            "symbol": self.symbol,
            "min_value": str(self.min_value) if self.min_value else None,
            "max_value": str(self.max_value) if self.max_value else None,
            # Format value for display (2 decimal places)
            "display_value": f"{value:.2f}" if value is not None else "",
        })
        return ctx

    def parse(self, raw: str | None) -> Decimal | None:
        if not raw or raw.strip() == "":
            return None
        # Strip currency symbols, commas (user might paste "$1,234.50")
        cleaned = raw.strip().lstrip("$£€¥").replace(",", "").strip()
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return raw  # validator catches it

    def validate(self, value, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value is not None:
            if not isinstance(value, Decimal):
                try:
                    value = Decimal(str(value))
                except InvalidOperation:
                    errors.append(f"{field.label} must be a valid amount.")
                    return errors
            if self.min_value is not None and value < self.min_value:
                errors.append(f"{field.label} must be at least {self.symbol}{self.min_value}.")
            if self.max_value is not None and value > self.max_value:
                errors.append(f"{field.label} must not exceed {self.symbol}{self.max_value}.")
        return errors
```

**Jinja2 macro** (in your extra macro file):

```jinja2
{% macro currency_input(ctx, model_name) %}
<div class="field-wrapper {% if ctx.errors %}has-error{% endif %}"
     id="field-wrapper-{{ ctx.meta.name }}">
  <label for="field-{{ ctx.meta.name }}" class="field-label">
    {{ ctx.meta.label }}
    {% if ctx.meta.required %}<span class="required-star">*</span>{% endif %}
  </label>

  <div class="currency-input-wrap">
    <span class="currency-symbol">{{ ctx.widget_context.symbol }}</span>
    <input
      type="number"
      id="field-{{ ctx.meta.name }}"
      name="{{ ctx.meta.name }}"
      value="{{ ctx.widget_context.display_value }}"
      step="0.01"
      {% if ctx.widget_context.min_value %}min="{{ ctx.widget_context.min_value }}"{% endif %}
      {% if ctx.widget_context.max_value %}max="{{ ctx.widget_context.max_value }}"{% endif %}
      {% if ctx.meta.required %}required{% endif %}
      {% if ctx.meta.readonly %}readonly{% endif %}
      class="form-input currency-field {% if ctx.errors %}form-input-error{% endif %}"
      hx-post="/admin/{{ model_name }}/validate-field"
      hx-trigger="blur"
      hx-target="#field-wrapper-{{ ctx.meta.name }}"
      hx-swap="outerHTML"
      hx-vals='{"field_name": "{{ ctx.meta.name }}"}'
    >
    <span class="currency-code">{{ ctx.widget_context.currency }}</span>
  </div>

  {% if ctx.meta.help_text %}
    <p class="field-help">{{ ctx.meta.help_text }}</p>
  {% endif %}
  {% if ctx.errors %}
    <ul class="field-errors">
      {% for err in ctx.errors %}<li>{{ err }}</li>{% endfor %}
    </ul>
  {% endif %}
</div>
{% endmacro %}
```

**Register:**

```python
widget_registry.register_name("price", CurrencyWidget)
widget_registry.register_name("amount", CurrencyWidget)
widget_registry.register_name("cost", CurrencyWidget)
```

---

### 4.2 Override Built-in Widget by Type

Replace the widget used for ALL columns of a SQLAlchemy type:

```python
from sqlalchemy import types as sa_types
from fastapi_admin.widgets import widget_registry

# Replace all Text columns with a rich text editor
widget_registry.register_type(sa_types.Text, RichTextWidget)

# Replace all JSON columns with a custom tree editor
widget_registry.register_type(sa_types.JSON, JsonTreeWidget)

# Replace all Boolean columns with a three-way select (True/False/None)
widget_registry.register_type(sa_types.Boolean, NullableBooleanWidget)
```

Registrations call `register_type()` after the built-in defaults, so your call
overwrites the built-in mapping. The type hierarchy check means subclasses also match:
registering `sa_types.Numeric` covers `DECIMAL`, `MONEY`, `NUMERIC` columns.

---

### 4.3 Override Built-in Widget by Field Name Pattern

```python
# Any field whose name contains these substrings gets this widget
widget_registry.register_name("password",     PasswordWidget)
widget_registry.register_name("secret",       PasswordWidget)
widget_registry.register_name("token",        PasswordWidget)
widget_registry.register_name("api_key",      MaskedTextWidget)
widget_registry.register_name("description",  RichTextWidget)
widget_registry.register_name("content",      RichTextWidget)
widget_registry.register_name("body",         RichTextWidget)
widget_registry.register_name("notes",        TextareaWidget)
widget_registry.register_name("color",        ColorPickerWidget)
widget_registry.register_name("hex",          ColorPickerWidget)
widget_registry.register_name("latitude",     NumberInputWidget(step="0.000001"))
widget_registry.register_name("longitude",    NumberInputWidget(step="0.000001"))
widget_registry.register_name("slug",         SlugWidget)
widget_registry.register_name("image",        ImageUploadWidget)
widget_registry.register_name("thumbnail",    ImageUploadWidget)
widget_registry.register_name("avatar",       ImageUploadWidget)
widget_registry.register_name("phone",        PhoneInputWidget)
widget_registry.register_name("mobile",       PhoneInputWidget)
widget_registry.register_name("website",      UrlInputWidget)
widget_registry.register_name("homepage",     UrlInputWidget)
```

Pattern matching is substring (case-insensitive). The first match in registration order
wins. Name patterns are checked before type map, so they always take priority.

---

### 4.4 Override HTML Macro Only

Change only the HTML rendered for a widget without touching its Python parse/validate
logic. Create a macro with the same name as the built-in one in a custom file:

```jinja2
{# myapp/templates/macros/overrides.html #}

{# Override built-in toggle — render as pill-style switch instead of checkbox #}
{% macro toggle(ctx) %}
<div class="field-wrapper" id="field-wrapper-{{ ctx.meta.name }}">
  <div class="toggle-row">
    <label class="field-label">{{ ctx.meta.label }}</label>
    <label
      class="pill-toggle"
      x-data="{ on: {{ 'true' if ctx.widget_context.value else 'false' }} }"
    >
      <input
        type="checkbox"
        name="{{ ctx.meta.name }}"
        value="on"
        x-model="on"
        class="sr-only"
      >
      <span class="pill-track" :class="{'bg-primary-500': on, 'bg-gray-300': !on}">
        <span class="pill-thumb" :class="{'translate-x-5': on}"></span>
      </span>
      <span class="pill-label" x-text="on ? 'Yes' : 'No'"></span>
    </label>
  </div>
</div>
{% endmacro %}
```

Register the file:

```python
admin = Admin(
    app=app,
    engine=engine,
    extra_macro_files=["myapp/templates/macros/overrides.html"],
)
```

The macro dispatcher checks your files before the built-in file, so your macro
definition takes precedence. If you define only some macros, the rest fall through to
built-ins.

---

### 4.5 Per-Model Widget Override

Override the widget for a specific field on a specific model only. Does not affect other
models that have columns with the same name or type:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    formfield_overrides = {
        # Override by field name
        "description":  RichTextWidget(toolbar="full"),
        "price":        CurrencyWidget(currency="USD", min_value=Decimal("0")),
        "cost_price":   CurrencyWidget(currency="USD", min_value=Decimal("0")),
        "sale_price":   CurrencyWidget(currency="USD", min_value=Decimal("0")),
        "status":       SelectWidget(choices=[
                            ("draft", "Draft"),
                            ("published", "Published"),
                            ("archived", "Archived"),
                        ]),
        "tags":         TagInputWidget(separator=","),
        "meta_robots":  CheckboxGroupWidget(choices=[
                            ("noindex", "No Index"),
                            ("nofollow", "No Follow"),
                            ("noarchive", "No Archive"),
                        ]),
    }
```

---

### 4.6 Dynamic Widget Selection

Select a widget based on runtime conditions (e.g. the object's current state):

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):

    def get_widget_for_field(self, field_name: str, obj=None, request=None) -> Widget | None:
        """
        Override to dynamically select widgets at request time.
        Return None to fall back to the normal resolution chain.
        """
        if field_name == "tracking_number":
            # Show tracking number as editable only when order is shipped
            if obj and obj.status == "shipped":
                return TextInputWidget()
            return ReadOnlyWidget()

        if field_name == "refund_reason":
            # Only show refund reason on refunded orders
            if obj and obj.status == "refunded":
                return TextareaWidget(rows=3)
            return HiddenWidget()

        return None  # use normal resolution
```

---

## 5. Form Pipeline Plugins

### 5.1 Custom Field Label Resolver

Change how field names become human-readable labels globally:

```python
# fastapi_admin/form/labels.py

class LabelResolver(Protocol):
    def resolve(self, field_name: str, model: type) -> str:
        """Return a human-readable label for the field."""
        ...


class DefaultLabelResolver:
    def resolve(self, field_name: str, model: type) -> str:
        name = field_name
        if name.endswith("_id"):
            name = name[:-3]
        name = re.sub(r"([A-Z])", r" \1", name)
        return name.replace("_", " ").strip().title()
```

**Custom resolver — read labels from a translation file:**

```python
class I18nLabelResolver:
    def __init__(self, labels: dict[str, dict[str, str]], locale: str = "en"):
        # labels = {"products": {"name": "Product Name", "sku": "SKU Code"}}
        self.labels = labels
        self.locale = locale

    def resolve(self, field_name: str, model: type) -> str:
        table = getattr(model, "__tablename__", "")
        return self.labels.get(table, {}).get(field_name) \
               or DefaultLabelResolver().resolve(field_name, model)

# Register
admin = Admin(
    app=app,
    engine=engine,
    label_resolver=I18nLabelResolver(labels=load_labels("labels/en.json")),
)
```

---

### 5.2 Custom Required Detector

Override the logic that decides whether a field is required on the form:

```python
class RequiredDetector(Protocol):
    def is_required(self, col: ColumnMeta, model_admin: ModelAdmin) -> bool:
        ...


class StrictRequiredDetector:
    """
    Treats any non-nullable column without a default as required,
    including UUID primary keys (so user must provide them).
    """
    def is_required(self, col: ColumnMeta, model_admin: ModelAdmin) -> bool:
        if col.name in (model_admin.readonly_fields or []):
            return False
        return not col.nullable and col.default is None and col.server_default is None


class RelaxedRequiredDetector:
    """
    Never marks a field as required — form can be submitted partially.
    Useful for draft-saving workflows.
    """
    def is_required(self, col: ColumnMeta, model_admin: ModelAdmin) -> bool:
        return False


admin = Admin(
    app=app,
    engine=engine,
    required_detector=StrictRequiredDetector(),
)
```

---

### 5.3 Custom Field Ordering

Control the default order fields appear in forms when no `fields` or `fieldsets` is set:

```python
class FieldOrderer(Protocol):
    def order(self, columns: list[ColumnMeta], relationships: list[RelationMeta]) -> list[str]:
        """Return ordered list of field names."""
        ...


class SemanticFieldOrderer:
    """
    Groups fields semantically: identifiers first, content middle,
    timestamps last.
    """
    IDENTITY_PATTERNS = {"name", "title", "label", "slug", "sku", "code"}
    TIMESTAMP_PATTERNS = {"created_at", "updated_at", "deleted_at", "published_at"}

    def order(self, columns, relationships) -> list[str]:
        identity, content, timestamps, pks = [], [], [], []
        for col in columns:
            if col.primary_key:
                pks.append(col.name)
            elif any(p in col.name for p in self.TIMESTAMP_PATTERNS):
                timestamps.append(col.name)
            elif any(p in col.name for p in self.IDENTITY_PATTERNS):
                identity.append(col.name)
            else:
                content.append(col.name)
        rel_names = [r.name for r in relationships]
        return identity + content + rel_names + timestamps + pks


admin = Admin(app=app, engine=engine, field_orderer=SemanticFieldOrderer())
```

---

### 5.4 Fieldset Builder

Auto-generate fieldset groupings from column metadata without requiring each
`ModelAdmin` to define `fieldsets` manually:

```python
class FieldsetBuilder(Protocol):
    def build(self, columns: list[ColumnMeta], relationships: list[RelationMeta],
              model_admin: ModelAdmin) -> list[FieldsetSpec]:
        ...


class TimestampSeparatingFieldsetBuilder:
    """
    Puts all timestamp columns into a collapsed "Metadata" section automatically.
    Everything else goes into a "General" section.
    """
    TIMESTAMP_NAMES = {"created_at", "updated_at", "deleted_at", "modified_at"}

    def build(self, columns, relationships, model_admin) -> list[FieldsetSpec]:
        # If model_admin has explicit fieldsets, honour them
        if model_admin.fieldsets:
            return model_admin.fieldsets

        main_fields = [c.name for c in columns
                       if c.name not in self.TIMESTAMP_NAMES and not c.primary_key]
        main_fields += [r.name for r in relationships]
        ts_fields = [c.name for c in columns if c.name in self.TIMESTAMP_NAMES]

        fieldsets = [FieldsetSpec(title=None, fields=main_fields, collapsed=False)]
        if ts_fields:
            fieldsets.append(FieldsetSpec(title="Metadata", fields=ts_fields, collapsed=True))
        return fieldsets


admin = Admin(app=app, engine=engine, fieldset_builder=TimestampSeparatingFieldsetBuilder())
```

---

### 5.5 Extra (Non-Model) Fields

Add fields to a form that have no corresponding database column. Values are available
in lifecycle hooks but not written to the model directly:

```python
from fastapi_admin.form import ExtraField

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    extra_fields = [
        ExtraField(
            name="notify_subscribers",
            label="Email subscribers on publish",
            widget=ToggleWidget(),
            default=False,
            required=False,
            help_text="Sends an announcement email when the product is published.",
            position="after",       # "before" (top of form) | "after" (bottom of form)
            show_on_create=True,
            show_on_edit=True,
        ),
        ExtraField(
            name="change_reason",
            label="Reason for change",
            widget=TextareaWidget(rows=2),
            default="",
            required=False,
            show_on_create=False,   # only on edit forms
            show_on_edit=True,
            help_text="Logged in the audit trail for this change.",
        ),
    ]

    def after_create(self, obj, request):
        data = request.state.parsed_form
        if data.get("notify_subscribers") and obj.status == "published":
            tasks.send_product_announcement.delay(obj.id)

    def after_update(self, obj, request):
        data = request.state.parsed_form
        reason = data.get("change_reason", "")
        if reason:
            # Append change reason to the audit log entry
            AuditLog.append_note(
                table_name=obj.__tablename__,
                object_id=obj.id,
                note=reason,
            )
```

Extra field values are stored temporarily on `request.state.parsed_form` (a plain dict)
during the request. They are never written to `obj` automatically — the developer
handles them in lifecycle hooks.

---

### 5.6 Form Context Middleware

Mutate or enrich the `FormContext` object before it reaches the template. Useful for
injecting additional context from external sources (feature flags, config, etc.):

```python
class FormContextMiddleware(Protocol):
    def process(self, context: FormContext, request: Request) -> FormContext:
        ...


class FeatureFlagFormMiddleware:
    """Hides fields gated by feature flags."""

    def __init__(self, flags_client):
        self.flags = flags_client

    def process(self, context: FormContext, request: Request) -> FormContext:
        if not self.flags.is_enabled("product_cost_tracking"):
            for fieldset in context.fieldsets:
                fieldset.fields = [
                    f for f in fieldset.fields
                    if f.meta.name not in ("cost_price", "margin")
                ]
        return context


admin = Admin(
    app=app,
    engine=engine,
    form_context_middlewares=[FeatureFlagFormMiddleware(flags_client=flags)],
)
```

---

## 6. Validation Plugins

### 6.1 Field Validator Method

Convention-based. Define `validate_{field_name}` on `ModelAdmin`. Auto-discovered:

```python
@admin.register(User)
class UserAdmin(ModelAdmin):

    def validate_email(self, value: str | None, obj=None) -> str | None:
        """Return an error string or None."""
        if not value:
            return None  # required check is handled by widget
        from email_validator import validate_email, EmailNotValidError
        try:
            validate_email(value, check_deliverability=False)
        except EmailNotValidError as e:
            return str(e)
        # Check uniqueness (excluding current object on edit)
        existing = db.query(User).filter_by(email=value).first()
        if existing and (obj is None or existing.id != obj.id):
            return "This email address is already in use."
        return None

    def validate_username(self, value: str | None, obj=None) -> str | None:
        if not value:
            return None
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", value):
            return "Username must be 3–30 characters: letters, numbers, and underscores only."
        return None
```

### 6.2 Object-Level Validator

Runs after all field validators pass. Receives the full parsed data dict:

```python
@admin.register(Event)
class EventAdmin(ModelAdmin):

    def validate(self, data: dict, obj=None) -> dict[str, str]:
        """Return {field_name: error} for cross-field validation errors."""
        errors = {}

        start = data.get("start_datetime")
        end   = data.get("end_datetime")
        if start and end and end <= start:
            errors["end_datetime"] = "End time must be after start time."

        capacity = data.get("capacity")
        min_cap  = data.get("min_capacity")
        if capacity and min_cap and min_cap > capacity:
            errors["min_capacity"] = "Minimum capacity cannot exceed total capacity."

        return errors
```

### 6.3 Global Validator Hook

A validator that runs for every registered model. Useful for cross-cutting rules
(e.g. soft-delete guard, audit completeness checks):

```python
# fastapi_admin/validation.py

class GlobalValidatorHook(Protocol):
    def validate(self, model: type, data: dict, obj, action: str) -> dict[str, list[str]]:
        """
        action: "create" | "update"
        Return {field_name: [errors]} — merged with model-level errors.
        """
        ...


class SoftDeleteGuardValidator:
    """
    Prevents editing soft-deleted records.
    Works for any model that has a `deleted_at` column.
    """
    def validate(self, model, data, obj, action) -> dict[str, list[str]]:
        if action == "update" and obj is not None:
            if getattr(obj, "deleted_at", None) is not None:
                return {"__all__": ["This record has been deleted and cannot be edited."]}
        return {}


admin = Admin(
    app=app,
    engine=engine,
    global_validators=[SoftDeleteGuardValidator()],
)
```

### 6.4 Async Validator

When validation requires an async operation (external API call, async DB query):

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):

    async def validate_barcode_async(self, value: str | None, obj=None) -> str | None:
        """
        Async variant — suffix _async is detected by the validation runner.
        Can use httpx, databases, async SQLAlchemy, etc.
        """
        if not value:
            return None
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://barcode-api.example.com/verify/{value}")
            if resp.status_code == 404:
                return f"Barcode '{value}' was not found in the product database."
        return None
```

The validation runner detects `*_async` suffix and awaits these validators in an
`asyncio.gather` call alongside synchronous validators.

---

## 7. Lifecycle Hook Plugins

### 7.1 Per-Model Hooks

All hooks available on `ModelAdmin`. Override any subset:

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):

    # ── CREATE ──────────────────────────────────────────────────────
    def on_create(self, obj: Order, request: Request) -> None:
        """Called BEFORE the INSERT. obj is not yet in DB. Raise ValueError to abort."""
        obj.order_number = generate_order_number()
        obj.created_by_ip = request.client.host

    def after_create(self, obj: Order, request: Request) -> None:
        """Called AFTER successful commit. obj.id is now available."""
        tasks.send_order_confirmation.delay(obj.id)
        inventory.reserve_stock(obj.id)

    # ── UPDATE ──────────────────────────────────────────────────────
    def on_update(self, obj: Order, data: dict, request: Request) -> None:
        """Called BEFORE the UPDATE. data = validated form data dict."""
        if "status" in data and data["status"] != obj.status:
            obj._previous_status = obj.status  # stash for after_update

    def after_update(self, obj: Order, request: Request) -> None:
        prev = getattr(obj, "_previous_status", None)
        if prev and prev != obj.status:
            tasks.handle_status_change.delay(obj.id, prev, obj.status)

    # ── DELETE ──────────────────────────────────────────────────────
    def on_delete(self, obj: Order, request: Request) -> None:
        """Called BEFORE the DELETE. Raise ValueError to abort deletion."""
        if obj.status == "processing":
            raise ValueError("Cannot delete an order that is currently being processed.")

    def after_delete(self, obj: Order, request: Request) -> None:
        inventory.release_reserved_stock(obj.id)
        tasks.notify_order_cancelled.delay(obj.id)

    # ── QUERYSET HOOK (list + relation search) ───────────────────────
    def get_queryset(self, session, request) -> Query:
        """Filter records shown to the current user."""
        qs = super().get_queryset(session, request)
        # Non-superusers only see their own region's orders
        user = request.state.admin_user
        if not user.is_superuser and hasattr(user, "region_id"):
            qs = qs.filter(Order.region_id == user.region_id)
        return qs
```

### 7.2 Global Hooks via Event System

React to events across all models from a central place:

```python
# fastapi_admin/events.py

class AdminEventBus:
    """
    Global event pub/sub. Decouples cross-cutting concerns
    (notifications, search indexing, cache invalidation) from ModelAdmin.
    """

    def on(self, event: str, handler: Callable, model: type | None = None):
        """
        event:  "create" | "update" | "delete" | "login" | "logout" | "bulk_delete"
        model:  if given, handler fires only for this model class
        """
        ...

    def emit(self, event: str, model: type, obj, request: Request, **extra):
        """Called by the framework automatically. No need to call this yourself."""
        ...
```

**Usage:**

```python
from fastapi_admin.events import event_bus

# React to any model creation
@event_bus.on("create")
def on_any_create(model: type, obj, request: Request):
    search_index.index(model.__tablename__, obj.id, snapshot(obj))

# React to Product updates only
@event_bus.on("update", model=Product)
def on_product_update(model, obj, request, diff=None):
    cache.invalidate(f"product:{obj.id}")
    if "price" in (diff or {}):
        price_tracker.record_change(obj.id, diff["price"])

# React to any deletion
@event_bus.on("delete")
def on_any_delete(model, obj, request):
    search_index.remove(model.__tablename__, str(obj.id))

# React to login events
@event_bus.on("login")
def on_login(user, request: Request):
    security_log.record_login(user.email, request.client.host)

# Register the bus with admin
admin = Admin(app=app, engine=engine, event_bus=event_bus)
```

**Async event handlers:**

```python
@event_bus.on("create", model=Product)
async def on_product_create(model, obj, request):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://webhooks.example.com/product-created",
            json={"id": obj.id, "name": obj.name},
        )
```

### 7.3 Hook Execution Order

When both `ModelAdmin` hooks and `event_bus` listeners are registered, execution order is:

```
POST /admin/products/create
    │
    ▼ validation passes
    │
    ▼ ModelAdmin.on_create(obj, request)       ← model-level, can abort
    │
    ▼ session.add(obj) → session.commit()
    │
    ▼ SQLAlchemy after_flush event             ← audit log writes here
    │
    ▼ ModelAdmin.after_create(obj, request)    ← model-level
    │
    ▼ event_bus.emit("create", ...)            ← global listeners
    │
    ▼ Flash message → Redirect
```

---

## 8. Route Plugins

### 8.1 Add Custom Routes to a Model

Add routes scoped to a specific model's prefix (`/admin/{model}/`):

```python
from fastapi import APIRouter
from fastapi_admin.auth.dependencies import require_permission

@admin.register(Product)
class ProductAdmin(ModelAdmin):

    @property
    def extra_routes(self) -> APIRouter:
        router = APIRouter()

        @router.get("/export", dependencies=[Depends(require_permission("products", "view"))])
        async def export_products(request: Request, format: str = "csv",
                                  session=Depends(get_session)):
            products = session.query(Product).all()
            if format == "csv":
                return StreamingResponse(
                    generate_csv(products),
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=products.csv"},
                )
            raise HTTPException(400, "Unsupported format")

        @router.post("/{id}/duplicate", dependencies=[Depends(require_permission("products", "create"))])
        async def duplicate_product(id: int, request: Request, session=Depends(get_session)):
            original = session.get(Product, id)
            if not original:
                raise HTTPException(404)
            clone = Product(**snapshot(original))
            clone.id = None
            clone.name = f"Copy of {original.name}"
            clone.slug = None
            session.add(clone)
            session.commit()
            add_flash(request, "success", f"Duplicated as #{clone.id}")
            return RedirectResponse(url=f"/admin/products/{clone.id}", status_code=303)

        return router
```

Routes are automatically mounted under `/admin/products/` alongside the auto-generated ones.

### 8.2 Add Global Admin Routes

For new admin pages that aren't tied to a specific model (reports, settings, import tools):

```python
# myapp/admin_routes.py
from fastapi import APIRouter
from fastapi_admin.auth.dependencies import get_current_admin_user

router = APIRouter()

@router.get("/import")
async def import_page(request: Request, user=Depends(get_current_admin_user)):
    return templates.TemplateResponse("myapp/import.html", {
        "request": request, "user": user,
    })

@router.post("/import")
async def import_submit(request: Request, file: UploadFile = File(...),
                         user=Depends(get_current_admin_user)):
    # ... process CSV import
    add_flash(request, "success", f"Imported {count} records.")
    return RedirectResponse("/admin/import", status_code=303)


# Register with admin
admin = Admin(
    app=app,
    engine=engine,
    extra_routers=[router],
)
```

Or via a `AdminPlugin`:

```python
class ImportPlugin(AdminPlugin):
    name = "import_plugin"

    def get_routes(self) -> APIRouter:
        return router   # same router as above

    def get_nav_items(self) -> list[NavItem]:
        return [NavItem(label="Import Data", url="/admin/import", icon="arrow-up-tray")]
```

### 8.3 Override Auto-Generated Route Handlers

Replace specific auto-generated view handlers with your own while keeping the rest:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):

    async def list_view(self, request: Request, session) -> Response:
        """Override the default list view entirely."""
        # Custom queryset with joins
        products = (
            session.query(Product)
            .join(Category)
            .options(joinedload(Product.category))
            .order_by(Product.created_at.desc())
            .all()
        )
        # Use custom template
        return templates.TemplateResponse("myapp/product_list.html", {
            "request": request,
            "products": products,
            "page_title": "Product Catalogue",
        })

    # create_form, create_submit, edit_form, edit_submit, delete_submit
    # can all be overridden the same way
```

### 8.4 Custom Bulk Actions

```python
from fastapi_admin.actions import Action

@admin.register(Product)
class ProductAdmin(ModelAdmin):

    def get_actions(self) -> list[Action]:
        return [
            Action(
                name="delete_selected",
                label="Delete Selected",
                permission="delete",
                confirm_message="Are you sure you want to delete the selected products?",
            ),
            Action(
                name="mark_featured",
                label="Mark as Featured",
                permission="edit",
                confirm_message=None,   # no confirmation dialog
            ),
            Action(
                name="export_selected",
                label="Export to CSV",
                permission="view",
                redirect_url=None,      # handled via response, not redirect
            ),
            Action(
                name="send_to_review",
                label="Send to Review",
                permission="custom:review",  # custom permission key
                confirm_message="Send selected products to the review queue?",
            ),
        ]

    async def action_mark_featured(self, ids: list[int], request: Request, session) -> None:
        """Handler for the 'mark_featured' action. Method name = action_{name}."""
        session.query(Product).filter(Product.id.in_(ids)).update(
            {"is_featured": True}, synchronize_session=False
        )
        session.commit()
        add_flash(request, "success", f"Marked {len(ids)} products as featured.")

    async def action_export_selected(self, ids: list[int], request: Request, session) -> Response:
        """Return a Response to override the default redirect."""
        products = session.query(Product).filter(Product.id.in_(ids)).all()
        return StreamingResponse(generate_csv(products), media_type="text/csv",
                                  headers={"Content-Disposition": "attachment; filename=export.csv"})
```

---

## 9. List View Plugins

### 9.1 Custom Columns

Add computed columns to the list view that don't correspond to DB columns:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price", "stock", "margin_pct", "is_low_stock", "created_at"]

    def get_margin_pct(self, obj: Product) -> str:
        """Computed column — method name = get_{column_name}."""
        if obj.cost_price and obj.price:
            pct = ((obj.price - obj.cost_price) / obj.price) * 100
            return f"{pct:.1f}%"
        return "—"

    # Mark column as sortable (optional — requires a valid DB expression)
    margin_pct_sortable = False
    margin_pct_label = "Margin"         # optional: override column header label
    margin_pct_html = False             # True: render as raw HTML (escape=False)

    def get_is_low_stock(self, obj: Product) -> str:
        """Return raw HTML for badge rendering."""
        if obj.stock == 0:
            return '<span class="badge badge-danger">Out of Stock</span>'
        if obj.stock < 5:
            return '<span class="badge badge-warning">Low Stock</span>'
        return '<span class="badge badge-success">In Stock</span>'

    is_low_stock_html = True            # render as raw HTML
    is_low_stock_label = "Stock Status"
```

### 9.2 Custom Filters

Add sidebar or dropdown filters beyond simple field equality:

```python
from fastapi_admin.filters import ListFilter, FilterSpec

class PriceRangeFilter(ListFilter):
    """
    Custom filter: dropdown of price ranges.
    Adds to the filter sidebar on the product list.
    """
    parameter_name = "price_range"
    title = "Price Range"

    def lookups(self) -> list[tuple[str, str]]:
        return [
            ("0_50",    "Under $50"),
            ("50_100",  "$50 – $100"),
            ("100_500", "$100 – $500"),
            ("500_plus","$500+"),
        ]

    def apply(self, queryset, value: str):
        ranges = {
            "0_50":    (0, 50),
            "50_100":  (50, 100),
            "100_500": (100, 500),
            "500_plus":(500, 999999),
        }
        low, high = ranges.get(value, (0, 999999))
        return queryset.filter(Product.price.between(low, high))


class StockStatusFilter(ListFilter):
    parameter_name = "stock_status"
    title = "Stock Status"

    def lookups(self):
        return [("in", "In Stock"), ("low", "Low Stock"), ("out", "Out of Stock")]

    def apply(self, queryset, value):
        if value == "in":    return queryset.filter(Product.stock > 5)
        if value == "low":   return queryset.filter(Product.stock.between(1, 5))
        if value == "out":   return queryset.filter(Product.stock == 0)
        return queryset


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_filter = [
        "category",             # built-in: FK dropdown filter
        "is_active",            # built-in: boolean filter
        PriceRangeFilter(),     # custom filter instance
        StockStatusFilter(),    # custom filter instance
    ]
```

### 9.3 Custom Search Logic

Override how search queries are built:

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    search_fields = ["name", "sku", "description"]  # default: ilike on these fields

    def get_search_results(self, queryset, search_term: str, session):
        """
        Override to implement full-text search, multi-field weighting,
        or external search integration (Elasticsearch, Typesense, etc.).
        """
        if not search_term:
            return queryset

        # Option A: PostgreSQL full-text search
        from sqlalchemy import func, text
        ts_query = func.plainto_tsquery("english", search_term)
        return queryset.filter(
            func.to_tsvector("english",
                func.concat_ws(" ", Product.name, Product.description, Product.sku)
            ).op("@@")(ts_query)
        )

    def get_search_results(self, queryset, search_term: str, session):
        """Option B: External search engine (Typesense/Elasticsearch)"""
        if not search_term:
            return queryset
        ids = typesense_client.search("products", search_term)
        return queryset.filter(Product.id.in_(ids))
```

### 9.4 Row Actions

Per-row action links/buttons beyond the default Edit and Delete:

```python
from fastapi_admin.actions import RowAction

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    row_actions = [
        RowAction(
            name="view_invoice",
            label="Invoice",
            icon="document-text",
            url_pattern="/admin/orders/{id}/invoice",  # {id} = object pk
            permission="view",
            open_in="new_tab",      # "same_tab" | "new_tab" | "modal"
        ),
        RowAction(
            name="mark_shipped",
            label="Mark Shipped",
            icon="truck",
            url_pattern="/admin/orders/{id}/ship",
            permission="edit",
            method="POST",
            confirm_message="Mark this order as shipped?",
            condition="obj.status == 'processing'",   # Python expression evaluated per row
        ),
    ]
```

### 9.5 List View Template Override

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_template = "myapp/product_list.html"   # your Jinja2 template path
    # Still receives the same list_context object as built-in list.html
```

---

## 10. Auth Plugins

### 10.1 Custom Auth Backend

Full documentation in `AUTH_RBAC_SYSTEM.md`. Summary of the interface:

```python
class AuthBackend(ABC):

    @abstractmethod
    async def authenticate(self, email: str, password: str, session) -> AdminUserProtocol | None:
        """Verify credentials. None = denied."""
        ...

    @abstractmethod
    async def get_user(self, user_id: int | str, session) -> AdminUserProtocol | None:
        """Load user by PK for session validation on every request."""
        ...

    # Optional hooks
    async def post_authenticate(self, user: AdminUserProtocol, request: Request) -> None:
        """Called after successful password check, before session is written.
        Raise HTTPException to abort login (e.g. require MFA verification)."""
        pass

    async def on_logout(self, user: AdminUserProtocol, request: Request) -> None:
        """Called just before session cookie is deleted."""
        pass
```

### 10.2 Custom Session Backend

Replace the default signed-cookie session with Redis or database sessions:

```python
# fastapi_admin/auth/session.py

class SessionBackend(ABC):

    @abstractmethod
    def encode(self, user_id: int | str) -> str:
        """Produce the session token string stored in the cookie."""
        ...

    @abstractmethod
    def decode(self, token: str | None) -> int | str | None:
        """Decode and verify token. Return user_id or None if invalid/expired."""
        ...

    @abstractmethod
    async def destroy(self, token: str) -> None:
        """Invalidate a session (e.g. on logout or password change)."""
        ...


class SignedCookieSessionBackend(SessionBackend):
    """Default — uses itsdangerous.TimestampSigner. Stateless."""

    def __init__(self, secret_key: str, ttl_seconds: int = 28800):
        self.signer = TimestampSigner(secret_key)
        self.ttl = ttl_seconds

    def encode(self, user_id) -> str:
        payload = json.dumps({"user_id": user_id})
        return self.signer.sign(payload).decode()

    def decode(self, token) -> int | None:
        if not token:
            return None
        try:
            payload = self.signer.unsign(token, max_age=self.ttl).decode()
            return json.loads(payload)["user_id"]
        except (SignatureExpired, BadSignature):
            return None

    async def destroy(self, token: str) -> None:
        pass  # stateless — cookie deletion handled by response


class RedisSessionBackend(SessionBackend):
    """Server-side sessions. Enables instant revocation."""

    def __init__(self, redis_url: str, ttl_seconds: int = 28800):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl_seconds

    def encode(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        # Store synchronously during login (or use asyncio.run)
        asyncio.get_event_loop().run_until_complete(
            self.redis.setex(f"admin_session:{token}", self.ttl, str(user_id))
        )
        return token

    def decode(self, token) -> int | None:
        if not token:
            return None
        user_id = asyncio.get_event_loop().run_until_complete(
            self.redis.get(f"admin_session:{token}")
        )
        return int(user_id) if user_id else None

    async def destroy(self, token: str) -> None:
        await self.redis.delete(f"admin_session:{token}")


# Register:
admin = Admin(
    app=app,
    engine=engine,
    secret_key=os.environ["SECRET_KEY"],
    session_backend=RedisSessionBackend(redis_url=os.environ["REDIS_URL"]),
)
```

### 10.3 Multi-Factor Auth Hook

Add MFA/2FA as a `post_authenticate` hook on your `AuthBackend`:

```python
class MFAAuthBackend(AppAuthBackend):

    async def post_authenticate(self, user: User, request: Request) -> None:
        """
        Called after password verifies but BEFORE session is created.
        Raise HTTPException(status_code=302) to redirect to MFA page.
        """
        if user.mfa_enabled:
            # Store pending user_id in a short-lived temporary token
            temp_token = mfa_store.create_pending(user.id, ttl_seconds=300)
            raise HTTPException(
                status_code=302,
                headers={"Location": f"/admin/mfa?token={temp_token}"}
            )


# MFA verification route (add via extra_routers):
@router.post("/mfa")
async def mfa_verify(request: Request, token: str = Form(...), code: str = Form(...)):
    pending_user_id = mfa_store.get_pending(token)
    if not pending_user_id:
        raise HTTPException(400, "MFA session expired.")
    user = session.get(User, pending_user_id)
    if not totp.verify(user.mfa_secret, code):
        return templates.TemplateResponse("pages/mfa.html", {
            "request": request, "token": token, "error": "Invalid code."
        })
    mfa_store.consume(token)
    # Write actual session cookie now
    response = RedirectResponse("/admin/", status_code=303)
    session_backend.write_cookie(response, user.id)
    return response
```

### 10.4 OAuth / SSO Integration

```python
class GoogleSSOPlugin(AdminPlugin):
    name = "google_sso"

    def __init__(self, client_id: str, client_secret: str, allowed_domains: list[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self.allowed_domains = allowed_domains

    def get_routes(self) -> APIRouter:
        router = APIRouter()

        @router.get("/login/google")
        async def google_login(request: Request):
            redirect_uri = request.url_for("google_callback")
            return await oauth.google.authorize_redirect(request, redirect_uri)

        @router.get("/login/google/callback", name="google_callback")
        async def google_callback(request: Request, session=Depends(get_session)):
            token = await oauth.google.authorize_access_token(request)
            email = token["userinfo"]["email"]
            domain = email.split("@")[1]
            if domain not in self.allowed_domains:
                raise HTTPException(403, "Your email domain is not permitted.")
            user = session.query(User).filter_by(email=email).first()
            if not user:
                raise HTTPException(403, "No admin account for this email.")
            response = RedirectResponse("/admin/", status_code=303)
            write_admin_session(response, user.id)
            return response

        return router

    def get_jinja2_globals(self) -> dict:
        return {"google_sso_enabled": True}   # used by login.html to show Google button
```

---

## 11. RBAC Plugins

### 11.1 Custom Permission Checker

Replace the database-driven permission checker entirely:

```python
class PermissionChecker(ABC):

    @abstractmethod
    def has_permission(self, table_name: str, action: str) -> bool: ...

    @abstractmethod
    def get_allowed_fields(self, table_name: str, mode: str) -> set[str] | None: ...

    def permission_set(self, table_name: str) -> PermissionSet:
        return PermissionSet(
            can_view=self.has_permission(table_name, "view"),
            can_create=self.has_permission(table_name, "create"),
            can_edit=self.has_permission(table_name, "edit"),
            can_delete=self.has_permission(table_name, "delete"),
        )


class HardcodedPermissionChecker(PermissionChecker):
    """
    Permissions defined in code rather than database.
    Useful for simple projects or when permissions are managed externally.
    """
    RULES = {
        "support_role": {
            "orders":   {"view": True,  "create": False, "edit": True,  "delete": False},
            "products": {"view": True,  "create": False, "edit": False, "delete": False},
            "users":    {"view": False, "create": False, "edit": False, "delete": False},
        }
    }

    def __init__(self, user):
        self.user = user

    def has_permission(self, table_name: str, action: str) -> bool:
        if self.user.is_superuser:
            return True
        role_name = getattr(self.user.role, "name", None)
        return self.RULES.get(role_name, {}).get(table_name, {}).get(action, False)

    def get_allowed_fields(self, table_name, mode):
        return None  # no field-level restrictions


# Register the custom checker factory:
admin = Admin(
    app=app,
    engine=engine,
    permission_checker_factory=lambda user, session: HardcodedPermissionChecker(user),
)
```

### 11.2 Attribute-Based Access Control (ABAC)

For complex rules where permissions depend on object attributes (not just model type):

```python
class ABACPermissionChecker(PermissionChecker):
    """
    Example: Users can only edit products in their own department.
    view=all, edit=same department only, delete=superuser only.
    """

    def __init__(self, user, session):
        self.user = user
        self.session = session

    def has_permission(self, table_name: str, action: str) -> bool:
        if self.user.is_superuser:
            return True
        # Basic model-level check first (falls back to DB permissions)
        base = PermissionChecker(self.session, self.user)
        return base.has_permission(table_name, action)

    def has_object_permission(self, table_name: str, action: str, obj) -> bool:
        """
        Called by edit/delete route handlers to check per-object access.
        Must be called explicitly in ModelAdmin.get_object() override.
        """
        if self.user.is_superuser:
            return True
        if table_name == "products" and action in ("edit", "delete"):
            return obj.department_id == self.user.department_id
        return self.has_permission(table_name, action)


@admin.register(Product)
class ProductAdmin(ModelAdmin):

    def get_object(self, session, id, request):
        obj = session.get(Product, id)
        checker = request.state.permission_checker
        if not checker.has_object_permission("products", "edit", obj):
            raise HTTPException(403, "You can only edit products in your department.")
        return obj
```

### 11.3 Custom Permission Actions

Add new permission dimensions beyond view/create/edit/delete:

```python
# In your migration (or admin setup):
# ALTER TABLE admin_permissions ADD COLUMN can_export BOOLEAN DEFAULT FALSE;
# ALTER TABLE admin_permissions ADD COLUMN can_approve BOOLEAN DEFAULT FALSE;

class ExtendedAdminPermission(AdminPermission):
    __tablename__ = "admin_permissions"
    __table_args__ = {"extend_existing": True}
    can_export  = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)


class ExtendedPermissionChecker(PermissionChecker):
    def has_permission(self, table_name: str, action: str) -> bool:
        if action in ("export", "approve"):
            # Handle custom actions
            perm = self.session.query(ExtendedAdminPermission).filter_by(
                role_id=self.user.role_id, table_name=table_name
            ).first()
            return bool(perm and getattr(perm, f"can_{action}", False))
        return super().has_permission(table_name, action)


admin = Admin(
    app=app,
    engine=engine,
    permission_checker_factory=lambda user, session: ExtendedPermissionChecker(session, user),
)
```

### 11.4 Row-Level Permissions

Restrict the records a user sees in list views (most common RBAC extension):

```python
@admin.register(Article)
class ArticleAdmin(ModelAdmin):

    def get_queryset(self, session, request):
        qs = super().get_queryset(session, request)
        user = request.state.admin_user

        # Editors see only their own drafts + all published articles
        if hasattr(user, "role") and user.role and user.role.name == "Editor":
            from sqlalchemy import or_
            qs = qs.filter(
                or_(Article.author_id == user.id, Article.status == "published")
            )
        return qs
```

---

## 12. Storage Plugins

### 12.1 Storage Backend Protocol

```python
# fastapi_admin/storage/base.py

class StorageBackend(ABC):

    @abstractmethod
    async def save(self, filename: str, contents: bytes,
                   content_type: str | None = None) -> str:
        """Save file. Return stored path/key (used to construct URL)."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file by path/key."""
        ...

    @abstractmethod
    def url(self, path: str) -> str:
        """Return public URL for a stored path/key."""
        ...

    def sanitize_filename(self, filename: str) -> str:
        """Override to customise filename sanitisation."""
        name = Path(filename).name
        name = re.sub(r"[^\w.\-]", "_", name)
        return f"{uuid4().hex[:8]}_{name}"
```

### 12.2 Local Storage (Built-in)

```python
class LocalStorageBackend(StorageBackend):
    def __init__(self, upload_dir: str = "uploads", base_url: str = "/uploads"):
        self.upload_dir = Path(upload_dir)
        self.base_url = base_url.rstrip("/")

    async def save(self, filename, contents, content_type=None) -> str:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        safe = self.sanitize_filename(filename)
        (self.upload_dir / safe).write_bytes(contents)
        return safe

    async def delete(self, path: str) -> None:
        target = self.upload_dir / path
        if target.exists():
            target.unlink()

    def url(self, path: str) -> str:
        return f"{self.base_url}/{path}"
```

### 12.3 S3 / Object Storage

```python
class S3StorageBackend(StorageBackend):
    """
    AWS S3 / Cloudflare R2 / MinIO / DigitalOcean Spaces.
    Any S3-compatible API works.
    """
    def __init__(self, bucket: str, region: str = "us-east-1",
                 prefix: str = "admin-uploads/",
                 endpoint_url: str | None = None,       # for R2, MinIO, etc.
                 public_base_url: str | None = None):
        self.bucket = bucket
        self.region = region
        self.prefix = prefix
        self.endpoint_url = endpoint_url
        self.public_base_url = public_base_url or f"https://{bucket}.s3.{region}.amazonaws.com"

    async def save(self, filename: str, contents: bytes, content_type=None) -> str:
        safe = self.sanitize_filename(filename)
        key = f"{self.prefix}{safe}"
        async with aiobotocore.get_session().create_client(
            "s3", region_name=self.region, endpoint_url=self.endpoint_url
        ) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=contents,
                ContentType=content_type or "application/octet-stream",
            )
        return key

    async def delete(self, path: str) -> None:
        async with aiobotocore.get_session().create_client("s3", ...) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=path)

    def url(self, path: str) -> str:
        return f"{self.public_base_url}/{path}"


# Register
admin = Admin(
    app=app,
    engine=engine,
    storage=S3StorageBackend(
        bucket="my-media",
        region="us-east-1",
        prefix="admin-uploads/",
    ),
)
```

### 12.4 Custom Storage Backend

```python
class CloudinaryStorageBackend(StorageBackend):
    """Upload to Cloudinary, store public_id, return CDN URL."""

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

    async def save(self, filename: str, contents: bytes, content_type=None) -> str:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: cloudinary.uploader.upload(
            contents, resource_type="auto", use_filename=True, unique_filename=True,
        ))
        return result["public_id"]

    async def delete(self, path: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: cloudinary.uploader.destroy(path))

    def url(self, path: str) -> str:
        return cloudinary.CloudinaryImage(path).build_url(secure=True)
```

---

## 13. Middleware Plugins

### 13.1 Admin Request Middleware

Runs on every request to the admin. Use for logging, header injection, timing, etc.:

```python
# fastapi_admin/middleware.py

class AdminMiddleware(ABC):

    @abstractmethod
    async def __call__(self, request: Request, call_next) -> Response:
        ...


class RequestTimingMiddleware(AdminMiddleware):
    async def __call__(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Admin-Request-Time"] = f"{duration:.3f}s"
        metrics.histogram("admin.request.duration", duration,
                          tags=[f"path:{request.url.path}"])
        return response


class DatadogAPMMiddleware(AdminMiddleware):
    async def __call__(self, request: Request, call_next) -> Response:
        with ddtrace.tracer.trace("fastapi_admin.request") as span:
            span.set_tag("http.url", str(request.url))
            user = getattr(request.state, "admin_user", None)
            if user:
                span.set_tag("admin.user_id", user.id)
            return await call_next(request)


admin = Admin(
    app=app,
    engine=engine,
    middlewares=[
        RequestTimingMiddleware(),
        DatadogAPMMiddleware(),
    ],
)
```

### 13.2 Audit Context Middleware

Injects request metadata into the audit capture context. Built-in, but replaceable:

```python
class AuditContextMiddleware(AdminMiddleware):
    """
    Default implementation — sets ContextVar so audit listener can read user + IP.
    Override to add extra metadata (tenant_id, session_id, etc.).
    """
    async def __call__(self, request: Request, call_next) -> Response:
        user = getattr(request.state, "admin_user", None)
        token = _current_audit_context.set({
            "user": user,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            # Add your own fields:
            "tenant_id": getattr(user, "tenant_id", None),
            "session_id": request.cookies.get("admin_session", "")[:8],
        })
        try:
            return await call_next(request)
        finally:
            _current_audit_context.reset(token)
```

### 13.3 Rate Limiting Middleware

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

class RateLimitMiddleware(AdminMiddleware):
    def __init__(self, login_limit: str = "5/minute", api_limit: str = "200/minute"):
        self.login_limit = login_limit
        self.api_limit = api_limit

    async def __call__(self, request: Request, call_next) -> Response:
        # Apply strict limit to login endpoint
        if request.url.path.endswith("/login") and request.method == "POST":
            # slowapi handles via decorator; this is a manual implementation example
            key = get_remote_address(request)
            if rate_store.is_limited(key, "login", "5/minute"):
                return Response("Too many login attempts. Try again later.", status_code=429)
        return await call_next(request)
```

---

## 14. Audit Log Plugins

### 14.1 Custom Audit Writer

Replace how audit log entries are persisted:

```python
# fastapi_admin/audit/writer.py

class AuditWriter(ABC):

    @abstractmethod
    def write(self, entry: AuditEntry) -> None:
        """
        Called after_flush for every registered-model change.
        Must be synchronous (runs inside SQLAlchemy flush context).
        """
        ...


@dataclass
class AuditEntry:
    action: str          # "CREATE" | "UPDATE" | "DELETE"
    model_name: str
    table_name: str
    object_id: str
    object_repr: str
    changes: dict | None          # UPDATE diff
    full_snapshot: dict | None    # full object state
    user_id: int | str | None
    user_email: str | None
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime


class DatabaseAuditWriter(AuditWriter):
    """Default — writes to admin_audit_log table."""
    def write(self, entry: AuditEntry, session) -> None:
        session.add(AuditLog(**asdict(entry)))


class FileAuditWriter(AuditWriter):
    """Write audit log to JSONL file (append-only)."""
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, entry: AuditEntry, session=None) -> None:
        with open(self.filepath, "a") as f:
            f.write(json.dumps(asdict(entry), default=str) + "\n")


class MultiAuditWriter(AuditWriter):
    """Fan-out to multiple writers."""
    def __init__(self, writers: list[AuditWriter]):
        self.writers = writers

    def write(self, entry: AuditEntry, session=None) -> None:
        for writer in self.writers:
            writer.write(entry, session)


admin = Admin(
    app=app,
    engine=engine,
    audit_writer=MultiAuditWriter([
        DatabaseAuditWriter(),
        FileAuditWriter("/var/log/admin-audit.jsonl"),
    ]),
)
```

### 14.2 Custom Snapshot Serializer

Control how model objects are serialised into the audit log's JSON:

```python
class SnapshotSerializer(ABC):

    @abstractmethod
    def serialize(self, obj) -> dict:
        """Convert a SQLAlchemy model instance to a JSON-safe dict."""
        ...

    @abstractmethod
    def serialize_value(self, val) -> Any:
        """Make a single value JSON-safe."""
        ...


class DefaultSnapshotSerializer(SnapshotSerializer):
    def serialize(self, obj) -> dict:
        mapper = inspect(type(obj))
        return {col.key: self.serialize_value(getattr(obj, col.key)) for col in mapper.columns}

    def serialize_value(self, val) -> Any:
        if isinstance(val, datetime): return val.isoformat()
        if isinstance(val, Decimal):  return float(val)
        if isinstance(val, UUID):     return str(val)
        if isinstance(val, bytes):    return "<binary>"
        if isinstance(val, Enum):     return val.value
        return val


class RedactingSnapshotSerializer(DefaultSnapshotSerializer):
    """Redacts sensitive fields from audit snapshots."""
    REDACT_PATTERNS = {"password", "secret", "token", "api_key", "ssn", "credit_card"}

    def serialize(self, obj) -> dict:
        result = super().serialize(obj)
        for key in list(result.keys()):
            if any(p in key.lower() for p in self.REDACT_PATTERNS):
                result[key] = "***REDACTED***"
        return result


admin = Admin(
    app=app,
    engine=engine,
    snapshot_serializer=RedactingSnapshotSerializer(),
)
```

### 14.3 Audit Log Sink (external)

Send audit events to external systems asynchronously (does not block the request):

```python
class AuditSink(ABC):
    """
    Receives audit events after the DB write.
    Runs asynchronously in a background task — failures do not affect the request.
    """
    @abstractmethod
    async def send(self, entry: AuditEntry) -> None: ...


class DatadogAuditSink(AuditSink):
    async def send(self, entry: AuditEntry) -> None:
        datadog.api.Event.create(
            title=f"Admin {entry.action}: {entry.model_name}",
            text=json.dumps(asdict(entry), default=str),
            tags=[f"action:{entry.action.lower()}", f"model:{entry.model_name}"],
            alert_type="info",
        )


class SlackAuditSink(AuditSink):
    def __init__(self, webhook_url: str, alert_on: list[str] = None):
        self.webhook_url = webhook_url
        self.alert_on = alert_on or ["DELETE"]  # alert only on deletes by default

    async def send(self, entry: AuditEntry) -> None:
        if entry.action not in self.alert_on:
            return
        async with httpx.AsyncClient() as client:
            await client.post(self.webhook_url, json={
                "text": f"🗑️ *{entry.user_email}* deleted a `{entry.model_name}` "
                        f"(#{entry.object_id}: {entry.object_repr})"
            })


class WebhookAuditSink(AuditSink):
    def __init__(self, url: str, secret: str):
        self.url = url
        self.secret = secret

    async def send(self, entry: AuditEntry) -> None:
        payload = json.dumps(asdict(entry), default=str)
        sig = hmac.new(self.secret.encode(), payload.encode(), "sha256").hexdigest()
        async with httpx.AsyncClient() as client:
            await client.post(self.url, content=payload, headers={
                "Content-Type": "application/json",
                "X-Admin-Signature": sig,
            })


admin = Admin(
    app=app,
    engine=engine,
    audit_sinks=[
        DatadogAuditSink(),
        SlackAuditSink(webhook_url=os.environ["SLACK_WEBHOOK"], alert_on=["DELETE"]),
    ],
)
```

---

## 15. Dashboard Plugins

### 15.1 Custom Stat Cards

```python
from fastapi_admin.dashboard import StatCard

class RevenueStatCard(StatCard):
    title = "Revenue (30 days)"
    icon = "currency-dollar"
    color = "success"

    async def compute(self, session, request) -> str:
        from sqlalchemy import func
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = session.query(func.sum(Order.total)).filter(
            Order.created_at >= thirty_days_ago,
            Order.status == "completed",
        ).scalar()
        return f"${result or 0:,.2f}"

    async def compute_change(self, session, request) -> str | None:
        """Optional: return a % change string like '+12.3%' or '-5.1%'."""
        # Compare to previous 30 days
        ...
        return "+8.4%"


class PendingOrdersStatCard(StatCard):
    title = "Pending Orders"
    icon = "clock"
    color = "warning"
    link_url = "/admin/orders/?status=pending"   # clicking card navigates here

    async def compute(self, session, request) -> str:
        count = session.query(Order).filter_by(status="pending").count()
        return str(count)


admin = Admin(
    app=app,
    engine=engine,
    dashboard_stat_cards=[
        RevenueStatCard(),
        PendingOrdersStatCard(),
        # Built-in stat card for a registered model:
        ModelStatCard(model=Product, label="Total Products"),
    ],
)
```

### 15.2 Custom Charts

```python
from fastapi_admin.dashboard import ChartWidget

class SalesByDayChart(ChartWidget):
    title = "Sales (Last 30 Days)"
    chart_type = "line"         # "line" | "bar" | "doughnut" | "radar"
    height = 300                # pixels

    async def get_data(self, session, request) -> dict:
        """
        Return Chart.js data object.
        """
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        rows = (
            session.query(
                func.date(Order.created_at).label("day"),
                func.sum(Order.total).label("revenue"),
                func.count(Order.id).label("count"),
            )
            .filter(Order.created_at >= thirty_days_ago)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )
        labels = [str(r.day) for r in rows]
        revenues = [float(r.revenue or 0) for r in rows]
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Revenue",
                    "data": revenues,
                    "borderColor": "rgb(99, 102, 241)",
                    "backgroundColor": "rgba(99, 102, 241, 0.1)",
                    "tension": 0.4,
                }
            ],
        }


admin = Admin(
    app=app,
    engine=engine,
    dashboard_charts=[SalesByDayChart()],
)
```

### 15.3 Custom Dashboard Widgets

Arbitrary HTML widgets in the dashboard — embed third-party status pages, notices,
or custom summaries:

```python
from fastapi_admin.dashboard import DashboardWidget

class SystemStatusWidget(DashboardWidget):
    title = "System Status"
    width = "full"      # "full" | "half" | "third"
    position = "bottom" # "top" | "middle" | "bottom"

    async def render(self, request, session) -> str:
        """Return raw HTML string."""
        services = await check_all_services()
        rows = "".join(
            f'<tr><td>{s.name}</td>'
            f'<td><span class="badge badge-{"success" if s.healthy else "danger"}">'
            f'{"OK" if s.healthy else "DOWN"}</span></td></tr>'
            for s in services
        )
        return f"""
        <table class="admin-table">
          <thead><tr><th>Service</th><th>Status</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """


admin = Admin(
    app=app,
    engine=engine,
    dashboard_widgets=[SystemStatusWidget()],
)
```

### 15.4 Full Dashboard Override

Replace the entire dashboard view:

```python
from fastapi.responses import HTMLResponse

async def my_dashboard(request: Request, session=Depends(get_session)):
    return templates.TemplateResponse("myapp/dashboard.html", {
        "request": request,
        "stats": await get_my_stats(session),
    })


admin = Admin(
    app=app,
    engine=engine,
    dashboard_view=my_dashboard,
)
```

---

## 16. UI & Template Plugins

### 16.1 Custom Template Directory

Prepend a directory to the Jinja2 template search path. Files with the same name as
built-in templates override them; new files are simply available:

```python
admin = Admin(
    app=app,
    engine=engine,
    template_dirs=["myapp/templates/admin"],  # searched BEFORE built-in templates
)
```

Resolution order:
1. Your `template_dirs` entries (first listed = highest priority)
2. Plugin template directories (in plugin list order)
3. Built-in `fastapi_admin/templates/`

### 16.2 Override Individual Templates

Create a file with the same path as the built-in template. The built-in template is
no longer rendered:

```
myapp/templates/admin/
├── pages/
│   ├── dashboard.html          ← overrides built-in dashboard
│   └── login.html              ← custom branded login page
└── partials/
    └── sidebar.html            ← custom sidebar
```

Your templates receive the same context variables as the built-in ones. You can
`{% extends "base.html" %}` to keep the layout and only override `{% block content %}`.

### 16.3 Inject Custom CSS / JS

```python
admin = Admin(
    app=app,
    engine=engine,

    # CSS injected in <head> after built-in styles
    extra_css=[
        "/static/myapp/admin-branding.css",
        "https://cdn.example.com/component-library.css",
    ],

    # JS injected before </body> after Alpine.js and HTMX
    extra_js=[
        "/static/myapp/rich-text-editor.js",
        "/static/myapp/custom-widgets.js",
    ],
)
```

The base template renders these via:

```jinja2
{% for css in admin_config.extra_css %}
  <link rel="stylesheet" href="{{ css }}">
{% endfor %}
```

### 16.4 Custom Sidebar Sections

Add nav items from a plugin or at init time:

```python
from fastapi_admin.nav import NavItem, NavSection

admin = Admin(
    app=app,
    engine=engine,
    extra_nav_items=[
        NavSection(
            title="Reports",
            items=[
                NavItem(label="Revenue Report", url="/admin/reports/revenue", icon="chart-bar"),
                NavItem(label="Inventory Report", url="/admin/reports/inventory", icon="archive-box"),
                NavItem(label="User Activity", url="/admin/reports/activity", icon="users"),
            ],
        ),
        NavItem(label="Import Data", url="/admin/import", icon="arrow-up-tray"),
        NavItem(label="System Settings", url="/admin/settings", icon="cog-6-tooth"),
    ],
)
```

Or from a plugin's `get_nav_items()` method. Nav items appear after the auto-generated
model nav links and before the built-in Audit Log / Roles / Settings links.

### 16.5 Custom Jinja2 Globals & Filters

Make values and functions available in all templates:

```python
import humanize

admin = Admin(
    app=app,
    engine=engine,

    jinja2_globals={
        "company_name": "Acme Corp",
        "support_email": "support@acme.com",
        "feature_flags": get_feature_flags(),
    },

    jinja2_filters={
        # {{ value | naturaltime }}
        "naturaltime": humanize.naturaltime,
        # {{ price | currency("USD") }}
        "currency": lambda val, code="USD": f"{code} {val:,.2f}",
        # {{ obj.status | status_badge }}
        "status_badge": lambda status: (
            f'<span class="badge badge-success">{status}</span>'
            if status == "active"
            else f'<span class="badge badge-danger">{status}</span>'
        ),
    },
)
```

---

## 17. Inspector Plugins

### 17.1 Custom Column Type Inspector

Control how SQLAlchemy column metadata is extracted — useful for custom column types
or non-SQLAlchemy ORMs:

```python
class ColumnInspector(ABC):

    @abstractmethod
    def inspect(self, model: type) -> list[ColumnMeta]:
        """Extract column metadata from a model class."""
        ...


class SQLAlchemyColumnInspector(ColumnInspector):
    """Default implementation."""
    def inspect(self, model: type) -> list[ColumnMeta]:
        mapper = sa_inspect(model)
        return [
            ColumnMeta(
                name=col.key,
                type=col.type,
                nullable=col.nullable,
                primary_key=col.primary_key,
                foreign_keys=list(col.foreign_keys),
                default=col.default,
                server_default=col.server_default,
            )
            for col in mapper.columns
        ]


class PydanticModelInspector(ColumnInspector):
    """
    Inspect Pydantic models instead of SQLAlchemy.
    Useful for document databases (MongoDB via Beanie etc.)
    """
    def inspect(self, model: type) -> list[ColumnMeta]:
        columns = []
        for field_name, field_info in model.model_fields.items():
            columns.append(ColumnMeta(
                name=field_name,
                type=self._map_pydantic_type(field_info.annotation),
                nullable=not field_info.is_required(),
                primary_key=(field_name == "id"),
                foreign_keys=[],
                default=field_info.default,
                server_default=None,
            ))
        return columns

    def _map_pydantic_type(self, annotation) -> Any:
        # Map Python types → SQLAlchemy-compatible type objects for widget resolution
        ...


admin = Admin(
    app=app,
    engine=engine,
    column_inspector=PydanticModelInspector(),
)
```

### 17.2 Custom Relationship Inspector

```python
class RelationshipInspector(ABC):

    @abstractmethod
    def inspect(self, model: type) -> list[RelationMeta]:
        ...


class SQLAlchemyRelationshipInspector(RelationshipInspector):
    """Default."""
    def inspect(self, model: type) -> list[RelationMeta]:
        mapper = sa_inspect(model)
        return [
            RelationMeta(
                name=rel.key,
                direction=rel.direction.name,
                target_model=rel.mapper.class_,
                uselist=rel.uselist,
                back_populates=rel.back_populates,
            )
            for rel in mapper.relationships
        ]
```

---

## 18. First-Party Plugin Packages

These are plugins maintained by the framework team and available as separate pip packages:

| Package | What it adds |
|---|---|
| `fastapi-admin-rich-text` | TipTap/Quill rich text widget for Text columns |
| `fastapi-admin-s3` | S3/R2/MinIO storage backend with image resize |
| `fastapi-admin-import-export` | CSV/Excel bulk import and export for any model |
| `fastapi-admin-charts` | Extended chart widgets (heat maps, funnels, scatter) |
| `fastapi-admin-translations` | i18n for admin UI labels and messages |
| `fastapi-admin-2fa` | TOTP-based two-factor authentication plugin |
| `fastapi-admin-tenancy` | Multi-tenant row isolation and per-tenant RBAC |
| `fastapi-admin-versioning` | Model history / version restore (requires PostgreSQL) |
| `fastapi-admin-notifications` | Email + Slack notifications on admin actions |

Install and register any of them:

```python
from fastapi_admin_rich_text import RichTextPlugin
from fastapi_admin_s3 import S3Plugin
from fastapi_admin_import_export import ImportExportPlugin

admin = Admin(
    app=app,
    engine=engine,
    plugins=[
        RichTextPlugin(cdn="cloudflare"),
        S3Plugin(bucket="my-bucket", region="us-east-1"),
        ImportExportPlugin(export_formats=["csv", "xlsx"]),
    ],
)
```

---

## 19. Third-Party Plugin Contract

If you're publishing an open-source plugin for this admin, follow this contract so it
works predictably:

### Package structure

```
fastapi_admin_myplugin/
├── __init__.py                # exports: MyPlugin class
├── plugin.py                  # AdminPlugin subclass
├── widgets.py                 # widget classes (if any)
├── models.py                  # DB models (if any)
├── templates/
│   ├── macros/
│   │   └── my_widgets.html    # Jinja2 macros matching widget macro_name values
│   └── pages/
│       └── my_page.html       # plugin-specific page templates
└── static/
    └── myplugin/
        ├── plugin.css
        └── plugin.js
```

### Required attributes

```python
class MyPlugin(AdminPlugin):
    name = "my_plugin"         # unique, slug-style
    version = "1.0.0"
    min_admin_version = "0.5.0"    # minimum compatible admin version

    def register_widgets(self, registry: WidgetRegistry) -> None:
        registry.register_name("my_field_pattern", MyWidget)

    def get_macro_files(self) -> list[str]:
        return [str(Path(__file__).parent / "templates/macros/my_widgets.html")]

    def get_static_files(self) -> list[StaticMount]:
        return [StaticMount(
            path="/static/myplugin",
            directory=str(Path(__file__).parent / "static/myplugin"),
        )]

    def get_css_urls(self) -> list[str]:
        return ["/static/myplugin/plugin.css"]

    def get_js_urls(self) -> list[str]:
        return ["/static/myplugin/plugin.js"]
```

### Naming conventions

- Widget `macro_name` values: prefix with your plugin slug → `myplugin_rich_text`
  to avoid collisions with built-ins and other plugins.
- Nav item URLs: `/admin/myplugin/*`
- DB table names (if any): `admin_myplugin_*`
- CSS class names: prefix with `ap-` (admin plugin) → `.ap-myplugin-editor`

---

## 20. Plugin Load Order & Conflicts

### Load order

```
1. Built-in widget defaults          (type map + name patterns)
2. Admin init kwargs                 (auth_model, storage, etc.)
3. Plugins (in list order)           (each plugin's register_widgets, routes, etc.)
4. inline widget_registry calls      (in your main.py, after Admin() construction)
5. ModelAdmin.formfield_overrides    (per-model, highest priority)
```

Last registration wins for widgets (both `register_type` and `register_name`).

### Conflict resolution

| Conflict type | Resolution |
|---|---|
| Two plugins register same type | Last plugin in `plugins=[]` list wins |
| Two plugins define same macro name | Last `extra_macro_files` entry wins (earliest in file) |
| Two plugins add nav item with same URL | Both render; no deduplication |
| Two plugins add same route path | FastAPI raises a startup error |
| Plugin + inline `register_type` | Inline wins (runs after plugin setup) |
| `formfield_overrides` vs plugin widget | `formfield_overrides` always wins |

### Detecting conflicts at startup

```python
admin = Admin(
    app=app,
    engine=engine,
    plugins=[PluginA(), PluginB()],
    strict_plugin_conflicts=True,  # raise ConfigError on any widget type conflict
)
```

With `strict_plugin_conflicts=True`, admin raises `ConfigError` at startup if two plugins
or init kwargs register the same type or name pattern, listing what conflicts and which
packages are responsible.

---

## 21. Complete Plugin Example — Rich Text Editor Plugin

A self-contained plugin that swaps all `textarea` / `Text` columns to a TipTap editor:

```python
# fastapi_admin_rich_text/plugin.py

class RichTextPlugin(AdminPlugin):
    name = "rich_text"
    version = "1.0.0"

    def __init__(self, toolbar: str = "minimal", cdn: str = "cloudflare",
                 field_patterns: list[str] = None):
        """
        toolbar:        "minimal" | "standard" | "full"
        cdn:            "cloudflare" | "unpkg" | "self-hosted"
        field_patterns: list of field name patterns to apply (default: all Text columns)
        """
        self.toolbar = toolbar
        self.cdn = cdn
        self.field_patterns = field_patterns or []

    def register_widgets(self, registry: WidgetRegistry) -> None:
        widget = RichTextWidget(toolbar=self.toolbar)

        if self.field_patterns:
            # Apply only to specific field name patterns
            for pattern in self.field_patterns:
                registry.register_name(pattern, type("_W", (RichTextWidget,), {})())
        else:
            # Replace all Text columns globally
            registry.register_type(sa_types.Text, widget)

    def get_macro_files(self) -> list[str]:
        return [str(Path(__file__).parent / "templates/macros/rich_text.html")]

    def get_js_urls(self) -> list[str]:
        cdn_urls = {
            "cloudflare": "https://cdnjs.cloudflare.com/ajax/libs/tiptap/2.1.0/tiptap.min.js",
            "unpkg":      "https://unpkg.com/@tiptap/core@2.1.0/dist/index.umd.js",
            "self-hosted": "/static/rich_text/tiptap.min.js",
        }
        return [cdn_urls[self.cdn], "/static/rich_text/rich_text_widget.js"]

    def get_css_urls(self) -> list[str]:
        return ["/static/rich_text/rich_text_widget.css"]

    def get_static_files(self) -> list[StaticMount]:
        return [StaticMount(
            path="/static/rich_text",
            directory=str(Path(__file__).parent / "static"),
        )]


class RichTextWidget(Widget):
    macro_name = "rich_text"

    def __init__(self, toolbar: str = "minimal"):
        self.toolbar = toolbar

    def render_context(self, field: FieldMeta, value) -> dict:
        ctx = super().render_context(field, value)
        ctx["toolbar"] = self.toolbar
        ctx["initial_html"] = value or ""
        return ctx

    def parse(self, raw: str | None) -> str | None:
        # TipTap submits HTML; sanitise it
        if not raw or raw.strip() in ("", "<p></p>"):
            return None
        return bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

    def validate(self, value, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value and len(strip_tags(value)) > 50000:
            errors.append(f"{field.label} is too long (max 50,000 characters).")
        return errors
```

**Usage:**

```python
from fastapi_admin_rich_text import RichTextPlugin

admin = Admin(
    app=app,
    engine=engine,
    plugins=[
        RichTextPlugin(toolbar="full", field_patterns=["description", "content", "body"]),
    ],
)
```

---

## 22. Complete Plugin Example — Tenant Isolation Plugin

A plugin that enforces multi-tenant row isolation across all registered models:

```python
# fastapi_admin_tenancy/plugin.py

class TenancyPlugin(AdminPlugin):
    """
    Adds tenant isolation to the admin.
    Assumes:
      - Every registered model has a `tenant_id` column
      - The admin user model has a `tenant_id` attribute
      - Superusers see all tenants (with a tenant switcher in topbar)
    """
    name = "tenancy"

    def __init__(self, tenant_model: type, tenant_id_field: str = "tenant_id"):
        self.tenant_model = tenant_model
        self.tenant_id_field = tenant_id_field

    def on_startup(self, admin: "Admin") -> None:
        # Patch every registered ModelAdmin's get_queryset
        for registered in admin.registry.all():
            self._patch_queryset(registered)

    def _patch_queryset(self, registered: RegisteredModel) -> None:
        tenant_field = self.tenant_id_field
        original_get_queryset = registered.admin.get_queryset

        def tenanted_queryset(session, request):
            qs = original_get_queryset(session, request)
            user = request.state.admin_user

            # Superusers: respect tenant switcher cookie
            if user.is_superuser:
                active_tenant = request.cookies.get("admin_active_tenant")
                if active_tenant:
                    qs = qs.filter(getattr(registered.model, tenant_field) == int(active_tenant))
                return qs

            # Non-superusers: always filter to their tenant
            user_tenant_id = getattr(user, tenant_field, None)
            if user_tenant_id:
                qs = qs.filter(getattr(registered.model, tenant_field) == user_tenant_id)
            return qs

        registered.admin.get_queryset = tenanted_queryset

    def on_startup(self, admin: "Admin") -> None:
        # Also patch on_create to auto-set tenant_id
        for registered in admin.registry.all():
            self._patch_queryset(registered)
            self._patch_on_create(registered)

    def _patch_on_create(self, registered: RegisteredModel) -> None:
        tenant_field = self.tenant_id_field
        original_on_create = registered.admin.on_create

        def tenanted_on_create(obj, request):
            original_on_create(obj, request)
            user = request.state.admin_user
            if not user.is_superuser:
                setattr(obj, tenant_field, getattr(user, tenant_field))

        registered.admin.on_create = tenanted_on_create

    def get_routes(self) -> APIRouter:
        router = APIRouter()

        @router.post("/switch-tenant")
        async def switch_tenant(tenant_id: int, request: Request,
                                user=Depends(get_current_admin_user)):
            if not user.is_superuser:
                raise HTTPException(403, "Only superusers can switch tenants.")
            response = RedirectResponse(request.headers.get("referer", "/admin/"), status_code=303)
            response.set_cookie("admin_active_tenant", str(tenant_id), httponly=True)
            return response

        @router.post("/clear-tenant")
        async def clear_tenant(user=Depends(get_current_admin_user)):
            if not user.is_superuser:
                raise HTTPException(403)
            response = RedirectResponse("/admin/", status_code=303)
            response.delete_cookie("admin_active_tenant")
            return response

        return router

    def get_nav_items(self) -> list[NavItem]:
        return []  # Tenant switcher is in topbar, not sidebar

    def get_jinja2_globals(self) -> dict:
        return {"tenancy_plugin_active": True}  # used by topbar.html to show switcher

    def get_macro_files(self) -> list[str]:
        return [str(Path(__file__).parent / "templates/macros/tenant_switcher.html")]


# Usage
from fastapi_admin_tenancy import TenancyPlugin
from myapp.models import Tenant

admin = Admin(
    app=app,
    engine=engine,
    plugins=[TenancyPlugin(tenant_model=Tenant, tenant_id_field="tenant_id")],
)
```
