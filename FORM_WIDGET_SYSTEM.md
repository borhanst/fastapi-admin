# Form & Widget Generation System

> **Scope:** How forms are generated end-to-end — from SQLAlchemy model inspection
> to HTML on the page. Covers both the Python widget class layer and the raw HTML
> output layer, plus how developers override either independently.

---

## Table of Contents

1. [Two Output Modes](#1-two-output-modes)
2. [Widget Class — Python Layer](#2-widget-class--python-layer)
3. [Widget Registry](#3-widget-registry)
4. [HTML Output — Jinja2 Macro Layer](#4-html-output--jinja2-macro-layer)
5. [Form Generation Pipeline](#5-form-generation-pipeline)
6. [Widget ↔ HTML Macro Binding](#6-widget--html-macro-binding)
7. [Server-Side Form Handling](#7-server-side-form-handling)
8. [Validation](#8-validation)
9. [HTMX Partial Validation](#9-htmx-partial-validation)
10. [Relationship Widgets](#10-relationship-widgets)
11. [File Upload Widgets](#11-file-upload-widgets)
12. [Developer Override Paths](#12-developer-override-paths)
13. [Custom Widget — Full Example](#13-custom-widget--full-example)
14. [FormContext Reference](#14-formcontext-reference)
15. [Complete HTML Output Examples](#15-complete-html-output-examples)
16. [Edge Cases](#16-edge-cases)

---

## 1. Two Output Modes

The form system has **two independently overridable layers**:

```
SQLAlchemy Model
      │
      ▼
┌─────────────────────────────────────────┐
│  LAYER 1 — Python Widget Class          │
│  Knows how to: parse, validate,         │
│  and produce render_context()           │
└─────────────────────┬───────────────────┘
                      │ produces context dict
                      ▼
┌─────────────────────────────────────────┐
│  LAYER 2 — Jinja2 Macro (HTML)          │
│  Renders the HTML using the context.    │
│  You can replace just this layer        │
│  without touching the Python widget.    │
└─────────────────────────────────────────┘
```

This means:

| What you override | What changes |
|---|---|
| Widget class only | Parse logic + validation changes; existing macro still renders |
| Macro only | HTML output changes; Python parse/validate untouched |
| Both | Completely custom field |
| Neither | Zero config — auto-detected from column type |

---

## 2. Widget Class — Python Layer

### Base Interface

```python
# fastapi_admin/widgets/base.py

from dataclasses import dataclass, field
from typing import Any
from abc import ABC

@dataclass
class FieldMeta:
    name: str                        # column name, e.g. "price"
    label: str                       # human label, e.g. "Price"
    required: bool                   # True if NOT NULL and no default
    readonly: bool                   # True if in ModelAdmin.readonly_fields
    help_text: str | None = None
    placeholder: str | None = None
    extra: dict = field(default_factory=dict)  # widget-specific options


class Widget(ABC):
    macro_name: str = "text_input"   # which Jinja2 macro renders this widget

    def render_context(self, field: FieldMeta, value: Any) -> dict:
        """
        Variables injected into the Jinja2 macro.
        Override to add widget-specific variables.
        """
        return {
            "field": field,
            "value": value,
            "id": f"field-{field.name}",
            "name": field.name,
        }

    def parse(self, raw: str | list | None) -> Any:
        """
        Convert raw FormData string → typed Python value.
        Called on every form POST before validation.
        """
        if raw is None or raw == "":
            return None
        return raw

    def validate(self, value: Any, field: FieldMeta) -> list[str]:
        """
        Returns a list of error messages. Empty = valid.
        Base checks required only.
        """
        errors = []
        if field.required and (value is None or value == ""):
            errors.append(f"{field.label} is required.")
        return errors
```

### Built-in Widget Classes

```python
# fastapi_admin/widgets/inputs.py

class TextInputWidget(Widget):
    macro_name = "text_input"

    def __init__(self, maxlength: int | None = None):
        self.maxlength = maxlength

    def render_context(self, field, value):
        ctx = super().render_context(field, value)
        ctx["maxlength"] = self.maxlength
        return ctx

    def validate(self, value, field):
        errors = super().validate(value, field)
        if value and self.maxlength and len(value) > self.maxlength:
            errors.append(f"{field.label} must be {self.maxlength} characters or fewer.")
        return errors


class TextareaWidget(Widget):
    macro_name = "textarea"

    def __init__(self, rows: int = 5):
        self.rows = rows

    def render_context(self, field, value):
        ctx = super().render_context(field, value)
        ctx["rows"] = self.rows
        return ctx


class NumberInputWidget(Widget):
    macro_name = "number_input"

    def __init__(self, step: str = "1", min: str | None = None, max: str | None = None):
        self.step = step
        self.min = min
        self.max = max

    def render_context(self, field, value):
        ctx = super().render_context(field, value)
        ctx.update({"step": self.step, "min": self.min, "max": self.max})
        return ctx

    def parse(self, raw):
        if raw is None or raw == "":
            return None
        try:
            return int(raw) if "." not in str(raw) else float(raw)
        except ValueError:
            return raw  # validator catches it

    def validate(self, value, field):
        errors = super().validate(value, field)
        if value is not None:
            try:
                float(value)
            except (TypeError, ValueError):
                errors.append(f"{field.label} must be a number.")
        return errors


class ToggleWidget(Widget):
    macro_name = "toggle"

    def parse(self, raw):
        # HTML checkbox sends "on" when checked, nothing when unchecked
        return raw in ("on", "true", "1", "yes", True)

    def validate(self, value, field):
        return []  # always valid


class SelectWidget(Widget):
    macro_name = "select"

    def __init__(self, choices: list[tuple[str, str]] | None = None):
        # choices: [(value, label), ...]
        # If None, auto-populated from Enum column values
        self.choices = choices or []

    def render_context(self, field, value):
        ctx = super().render_context(field, value)
        ctx["choices"] = self.choices
        return ctx

    def validate(self, value, field):
        errors = super().validate(value, field)
        if value and self.choices:
            valid = {c[0] for c in self.choices}
            if value not in valid:
                errors.append(f"'{value}' is not a valid choice for {field.label}.")
        return errors


class DatePickerWidget(Widget):
    macro_name = "date_picker"

    def parse(self, raw):
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return raw

    def validate(self, value, field):
        errors = super().validate(value, field)
        if value is not None and not isinstance(value, date):
            errors.append(f"{field.label} must be a valid date.")
        return errors


class DateTimePickerWidget(Widget):
    macro_name = "datetime_picker"

    def parse(self, raw):
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)  # HTML sends "2024-01-15T14:30"
        except ValueError:
            return raw

    def validate(self, value, field):
        errors = super().validate(value, field)
        if value is not None and not isinstance(value, datetime):
            errors.append(f"{field.label} must be a valid date and time.")
        return errors


class JsonEditorWidget(Widget):
    macro_name = "json_editor"

    def parse(self, raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw  # validator catches it

    def validate(self, value, field):
        errors = super().validate(value, field)
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError as e:
                errors.append(f"{field.label} contains invalid JSON: {e}")
        return errors


class PasswordWidget(Widget):
    macro_name = "password_input"

    def render_context(self, field, value):
        ctx = super().render_context(field, value)
        ctx["value"] = ""  # NEVER pre-fill passwords
        return ctx

    def parse(self, raw):
        if not raw:
            return None
        return bcrypt.hash(raw)  # always hash on parse


class ReadOnlyWidget(Widget):
    macro_name = "readonly"

    def parse(self, raw):
        return None  # readonly fields are never updated from POST

    def validate(self, value, field):
        return []


class HiddenWidget(Widget):
    macro_name = "hidden"
```

---

## 3. Widget Registry

The registry resolves which widget class to use for a given column. Resolution order is fixed and cannot be short-circuited:

```
1. Exact field name pattern  →  e.g. "password" → PasswordWidget
2. FK column present         →  RelationPickerWidget
3. Enum type                 →  SelectWidget
4. SQLAlchemy type match     →  via _type_map dict
5. Fallback                  →  TextInputWidget
```

```python
# fastapi_admin/widgets/registry.py

class WidgetRegistry:
    def __init__(self):
        self._type_map: dict[type, type[Widget]] = {}
        self._name_patterns: list[tuple[str, type[Widget]]] = []

    def register_type(self, sa_type: type, widget_cls: type[Widget]):
        self._type_map[sa_type] = widget_cls

    def register_name(self, pattern: str, widget_cls: type[Widget]):
        """Pattern is a substring match on field name (case-insensitive)."""
        self._name_patterns.append((pattern.lower(), widget_cls))

    def resolve(self, col: ColumnMeta) -> Widget:
        # 1. Name patterns
        for pattern, widget_cls in self._name_patterns:
            if pattern in col.name.lower():
                return widget_cls()

        # 2. FK
        if col.foreign_keys:
            return RelationPickerWidget()

        # 3. Enum
        if isinstance(col.type, sa_types.Enum):
            choices = [(v, v.replace("_", " ").title()) for v in col.type.enums]
            return SelectWidget(choices=choices)

        # 4. Type hierarchy
        for sa_type, widget_cls in self._type_map.items():
            if isinstance(col.type, sa_type):
                # Auto-configure Number widget step based on type
                if widget_cls == NumberInputWidget:
                    step = "0.01" if isinstance(col.type, (sa_types.Float, sa_types.Numeric)) else "1"
                    return NumberInputWidget(step=step)
                # Auto-configure Text max length
                if widget_cls == TextInputWidget and hasattr(col.type, "length") and col.type.length:
                    return TextInputWidget(maxlength=col.type.length)
                return widget_cls()

        # 5. Fallback
        return TextInputWidget()


# Global singleton — importable anywhere
widget_registry = WidgetRegistry()

# Default bindings
widget_registry.register_type(sa_types.String,     TextInputWidget)
widget_registry.register_type(sa_types.Text,        TextareaWidget)
widget_registry.register_type(sa_types.Integer,     NumberInputWidget)
widget_registry.register_type(sa_types.BigInteger,  NumberInputWidget)
widget_registry.register_type(sa_types.Float,       NumberInputWidget)
widget_registry.register_type(sa_types.Numeric,     NumberInputWidget)
widget_registry.register_type(sa_types.Boolean,     ToggleWidget)
widget_registry.register_type(sa_types.Date,        DatePickerWidget)
widget_registry.register_type(sa_types.DateTime,    DateTimePickerWidget)
widget_registry.register_type(sa_types.Time,        TimePickerWidget)
widget_registry.register_type(sa_types.JSON,        JsonEditorWidget)
widget_registry.register_type(sa_types.LargeBinary, FileUploadWidget)
widget_registry.register_type(sa_types.Uuid,        TextInputWidget)

# Name-pattern bindings (checked before type map)
widget_registry.register_name("password",    PasswordWidget)
widget_registry.register_name("email",       EmailInputWidget)
widget_registry.register_name("url",         UrlInputWidget)
widget_registry.register_name("phone",       PhoneInputWidget)
widget_registry.register_name("color",       ColorPickerWidget)
widget_registry.register_name("image",       ImageUploadWidget)
widget_registry.register_name("slug",        SlugWidget)
```

---

## 4. HTML Output — Jinja2 Macro Layer

Each widget class maps to a Jinja2 macro by `macro_name`. The macro lives in
`templates/macros/form_fields.html`. The macro receives the `render_context()` dict
from the widget class directly.

### Macro Dispatcher

```jinja2
{# templates/macros/form_fields.html #}

{% macro render_field(field_ctx, model_name) %}
  {% set m = field_ctx.widget_macro %}
  {% if   m == "text_input"      %} {{ text_input(field_ctx, model_name) }}
  {% elif m == "textarea"        %} {{ textarea(field_ctx, model_name) }}
  {% elif m == "number_input"    %} {{ number_input(field_ctx, model_name) }}
  {% elif m == "password_input"  %} {{ password_input(field_ctx, model_name) }}
  {% elif m == "email_input"     %} {{ email_input(field_ctx, model_name) }}
  {% elif m == "toggle"          %} {{ toggle(field_ctx) }}
  {% elif m == "select"          %} {{ select(field_ctx, model_name) }}
  {% elif m == "date_picker"     %} {{ date_picker(field_ctx) }}
  {% elif m == "datetime_picker" %} {{ datetime_picker(field_ctx) }}
  {% elif m == "json_editor"     %} {{ json_editor(field_ctx) }}
  {% elif m == "file_upload"     %} {{ file_upload(field_ctx) }}
  {% elif m == "image_upload"    %} {{ image_upload(field_ctx) }}
  {% elif m == "relation_picker" %} {{ relation_picker(field_ctx) }}
  {% elif m == "multi_relation"  %} {{ multi_relation(field_ctx) }}
  {% elif m == "readonly"        %} {{ readonly_field(field_ctx) }}
  {% elif m == "hidden"          %} {{ hidden_field(field_ctx) }}
  {% else %}                        {{ text_input(field_ctx, model_name) }}
  {% endif %}
{% endmacro %}
```

### HTMX Partial Validation Hook (shared by all text-like inputs)

Every field that can be validated on blur includes these HTMX attributes:

```
hx-post="/admin/{model_name}/validate-field"
hx-trigger="blur"
hx-target="#field-wrapper-{field.name}"
hx-swap="outerHTML"
hx-vals='{"field_name": "{field.name}"}'
```

The server responds with a replacement `<div class="field-wrapper ...">` fragment that
includes inline error messages or a success indicator.

---

## 5. Form Generation Pipeline

```
GET /admin/products/create  (or /admin/products/42 for edit)
            │
            ▼
  1. Load RegisteredModel from registry
            │
            ▼
  2. Determine field order
     ├─ If ModelAdmin.fieldsets set → use defined order
     ├─ Elif ModelAdmin.fields set  → use that list
     └─ Else → all inspected columns
                  └─ exclude: PKs (create), readonly (shown read-only),
                              ModelAdmin.exclude list
            │
            ▼
  3. For each field:
     a. Get ColumnMeta
     b. Check formfield_overrides → use override widget if present
     c. Else resolve widget via WidgetRegistry
     d. Build FieldMeta (label, required, readonly, help_text)
     e. If edit: get current value from DB object
     f. widget.render_context(field_meta, value) → context dict
     g. Build FieldRenderContext(meta, widget_macro, widget_context, errors=[])
            │
            ▼
  4. Group into FieldsetContexts (sections)
  5. Append relationship fields (RelationPicker / MultiRelation)
  6. Append extra_fields from ModelAdmin (computed/non-model fields)
            │
            ▼
  7. Build FormContext (see §14)
  8. Render pages/form.html with FormContext
```

### Field Label Auto-Generation

```python
def auto_label(name: str) -> str:
    # "category_id"  → "Category"  (strips _id)
    # "is_active"    → "Is Active"
    # "created_at"   → "Created At"
    # "skuCode"      → "Sku Code"   (camelCase split)
    if name.endswith("_id"):
        name = name[:-3]
    name = re.sub(r"([A-Z])", r" \1", name)   # split camelCase
    return name.replace("_", " ").strip().title()
```

### Required Field Detection

```python
def is_required(col: ColumnMeta) -> bool:
    return (
        not col.nullable
        and col.default is None
        and col.server_default is None
        and not col.primary_key
    )
```

---

## 6. Widget ↔ HTML Macro Binding

Complete mapping from column type → widget class → macro name → HTML rendered:

| Column type | Widget class | `macro_name` | HTML output |
|---|---|---|---|
| `String` / `VARCHAR` | `TextInputWidget` | `text_input` | `<input type="text">` |
| `Text` | `TextareaWidget` | `textarea` | `<textarea>` |
| `Integer` / `BigInteger` | `NumberInputWidget` step=1 | `number_input` | `<input type="number" step="1">` |
| `Float` / `Numeric` | `NumberInputWidget` step=0.01 | `number_input` | `<input type="number" step="0.01">` |
| `Boolean` | `ToggleWidget` | `toggle` | `<input type="checkbox">` styled as switch |
| `Date` | `DatePickerWidget` | `date_picker` | `<input type="date">` |
| `DateTime` / `TIMESTAMP` | `DateTimePickerWidget` | `datetime_picker` | `<input type="datetime-local">` |
| `Time` | `TimePickerWidget` | `time_picker` | `<input type="time">` |
| `Enum` | `SelectWidget` | `select` | `<select>` with options |
| `JSON` / `JSONB` | `JsonEditorWidget` | `json_editor` | CodeMirror editor |
| `LargeBinary` | `FileUploadWidget` | `file_upload` | `<input type="file">` |
| `UUID` | `TextInputWidget` | `text_input` | `<input type="text">` (readonly on edit) |
| FK column | `RelationPickerWidget` | `relation_picker` | HTMX async searchable select |
| Many-to-many rel | `MultiRelationWidget` | `multi_relation` | Tag-style multi-select |
| name contains "password" | `PasswordWidget` | `password_input` | `<input type="password">` never pre-filled |
| name contains "email" | `EmailInputWidget` | `email_input` | `<input type="email">` |
| name contains "url" | `UrlInputWidget` | `url_input` | `<input type="url">` |
| PK on create | `HiddenWidget` | `hidden` | `<input type="hidden">` |
| PK on edit / `readonly_fields` | `ReadOnlyWidget` | `readonly` | `<span>` no input |

---

## 7. Server-Side Form Handling

### POST Flow (Create)

```python
# fastapi_admin/views/form.py

async def create_submit_handler(request, registered: RegisteredModel, session):
    form_data = await request.form()
    parsed: dict[str, Any] = {}
    errors: dict[str, list[str]] = {}

    for field_meta in registered.form_fields:
        if field_meta.readonly:
            continue

        widget = registered.get_widget(field_meta.name)
        raw = form_data.get(field_meta.name)

        # Step 1 — parse raw string → typed Python value
        value = widget.parse(raw)

        # Step 2 — validate
        field_errors = widget.validate(value, field_meta)
        if field_errors:
            errors[field_meta.name] = field_errors
        else:
            parsed[field_meta.name] = value

    # Step 3 — run object-level validators (only if no field errors)
    if not errors:
        validator = FormValidator()
        errors = validator.run_object_level(registered, parsed, obj=None)

    if errors:
        # Re-render with errors; 422 so browser does NOT redirect
        return templates.TemplateResponse("pages/form.html", {
            "request": request,
            "form_context": build_form_context(registered, values=parsed, errors=errors),
            "is_create": True,
        }, status_code=422)

    # Step 4 — create DB object
    obj = registered.model(**parsed)
    registered.admin.on_create(obj, request)
    session.add(obj)
    await session.commit()
    registered.admin.after_create(obj, request)

    add_flash(request, "success", f"{registered.verbose_name} created.")
    return RedirectResponse(url=list_url(registered), status_code=303)
```

### POST Flow (Edit)

Readonly fields are skipped. Only changed fields are written (partial update pattern):

```python
async def edit_submit_handler(request, registered, session, obj_id):
    obj = await session.get(registered.model, obj_id)
    if not obj:
        raise HTTPException(404)

    form_data = await request.form()
    parsed = {}
    errors = {}

    for field_meta in registered.form_fields:
        if field_meta.readonly:
            continue  # NEVER update readonly from POST
        widget = registered.get_widget(field_meta.name)
        raw = form_data.get(field_meta.name)
        value = widget.parse(raw)
        field_errors = widget.validate(value, field_meta)
        if field_errors:
            errors[field_meta.name] = field_errors
        else:
            parsed[field_meta.name] = value

    if not errors:
        errors = FormValidator().run_object_level(registered, parsed, obj=obj)

    if errors:
        return templates.TemplateResponse("pages/form.html", {
            "request": request,
            "form_context": build_form_context(registered, obj=obj, values=parsed, errors=errors),
            "is_create": False,
        }, status_code=422)

    registered.admin.on_update(obj, parsed, request)
    for key, value in parsed.items():
        setattr(obj, key, value)
    await session.commit()
    registered.admin.after_update(obj, request)

    add_flash(request, "success", f"{registered.verbose_name} updated.")
    return RedirectResponse(url=list_url(registered), status_code=303)
```

---

## 8. Validation

Three levels run in order:

### Level 1 — Widget built-in (automatic)

Every widget's `validate()` runs for its field. Covers: required check, type coercion
verification, max length, enum membership, JSON parse check.

### Level 2 — Field-level developer validator

Naming convention: `validate_{field_name}` method on `ModelAdmin`. Auto-discovered.

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):

    def validate_price(self, value, obj=None) -> str | None:
        if value is not None and value < 0:
            return "Price cannot be negative."

    def validate_sku(self, value, obj=None) -> str | None:
        if value and not value.isupper():
            return "SKU must be uppercase letters only."
```

### Level 3 — Object-level (cross-field) validator

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):

    def validate(self, data: dict, obj=None) -> dict[str, str]:
        """Runs only after all field validators pass."""
        errors = {}
        if data.get("sale_price") and data.get("price"):
            if data["sale_price"] >= data["price"]:
                errors["sale_price"] = "Sale price must be less than regular price."
        return errors
```

### Validation Runner

```python
# fastapi_admin/validation.py

class FormValidator:
    def run(self, registered: RegisteredModel, parsed: dict, obj=None) -> dict[str, list[str]]:
        errors = {}

        for field_meta in registered.form_fields:
            if field_meta.readonly:
                continue
            widget = registered.get_widget(field_meta.name)
            value = parsed.get(field_meta.name)

            # Level 1
            widget_errors = widget.validate(value, field_meta)
            if widget_errors:
                errors[field_meta.name] = widget_errors
                continue  # skip L2 if L1 fails

            # Level 2
            validator_fn = getattr(registered.admin, f"validate_{field_meta.name}", None)
            if validator_fn:
                err = validator_fn(value, obj=obj)
                if err:
                    errors[field_meta.name] = [err]

        # Level 3 — only if no field errors yet
        if not errors and hasattr(registered.admin, "validate"):
            object_errors = registered.admin.validate(parsed, obj=obj)
            for fname, err in object_errors.items():
                errors[fname] = [err] if isinstance(err, str) else err

        return errors
```

---

## 9. HTMX Partial Validation

Fields validate themselves on `blur` without a full page reload.

**Endpoint:**

```
POST /admin/{table_name}/validate-field
Body: field_name=price&price=abc
Response: HTML fragment — replacement <div class="field-wrapper">
```

**Handler:**

```python
@router.post("/{table_name}/validate-field")
async def validate_field_endpoint(table_name: str, request: Request):
    form = await request.form()
    field_name = form.get("field_name")
    raw_value = form.get(field_name)

    registered = registry.get(table_name)
    field_meta = registered.get_field_meta(field_name)
    widget = registered.get_widget(field_name)

    parsed = widget.parse(raw_value)
    errors = widget.validate(parsed, field_meta)

    # Also run level-2 validator
    validator_fn = getattr(registered.admin, f"validate_{field_name}", None)
    if validator_fn and not errors:
        err = validator_fn(parsed)
        if err:
            errors = [err]

    return templates.TemplateResponse("partials/field_wrapper.html", {
        "request": request,
        "field": field_meta,
        "value": raw_value,
        "errors": errors,
        "widget_macro": widget.macro_name,
        "model_name": table_name,
    })
```

---

## 10. Relationship Widgets

### RelationPickerWidget — ForeignKey (many-to-one)

**Data flow:**

```
User types in search box
    → hx-get="/admin/{related_table}/search?q={text}&limit=20"
    → Server queries related model, applies search_fields or first String column
    → Returns JSON: [{id: "3", label: "Shoes"}, ...]
    → Alpine.js renders dropdown
    → User clicks item → hidden <input name="{field.name}" value="{id}"> updated
    → Form POST submits the FK id as a plain string
```

**Parse:**

```python
class RelationPickerWidget(Widget):
    macro_name = "relation_picker"

    def __init__(self, related_table: str, related_verbose: str):
        self.related_table = related_table
        self.related_verbose = related_verbose

    def parse(self, raw: str | None) -> int | str | None:
        if not raw:
            return None
        # FK might be int or UUID — try int first
        try:
            return int(raw)
        except ValueError:
            return raw

    def validate(self, value, field):
        errors = super().validate(value, field)
        # Note: we do NOT validate that the FK exists in DB here —
        # the DB constraint handles that, and the FK search only returns valid IDs
        return errors
```

### MultiRelationWidget — Many-to-Many

```python
class MultiRelationWidget(Widget):
    macro_name = "multi_relation"

    def parse(self, raw) -> list[str]:
        # HTML sends: tags[]=1&tags[]=2&tags[]=5
        # FastAPI returns list for repeated keys
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(v) for v in raw if v]
        return [str(raw)]

    def validate(self, value, field):
        # Many-to-many is never required in the traditional sense
        return []
```

**Saving Many-to-Many** (handled in edit_submit_handler, not in the widget):

```python
# After commit of the parent object:
if field_meta.is_many_to_many:
    relationship_attr = getattr(obj, field_meta.name)
    related_model = registered.get_related_model(field_meta.name)
    new_ids = set(int(i) for i in parsed.get(field_meta.name, []))
    existing_ids = {getattr(r, r.__class__.__mapper__.primary_key[0].name) for r in relationship_attr}

    # Add new
    for id_ in new_ids - existing_ids:
        relationship_attr.append(session.get(related_model, id_))
    # Remove old
    for id_ in existing_ids - new_ids:
        relationship_attr.remove(next(r for r in relationship_attr if getattr(r, ...) == id_))
```

---

## 11. File Upload Widgets

### Parse Strategy

File fields receive `UploadFile` objects from FastAPI's multipart form parser.

```python
class FileUploadWidget(Widget):
    macro_name = "file_upload"
    max_size_mb: float = 10.0
    allowed_extensions: list[str] = []  # empty = all

    def parse(self, raw) -> UploadFile | str | None:
        # raw can be:
        #   UploadFile  — new file selected
        #   ""          — no file selected (keep existing)
        #   None        — field cleared
        return raw

    def validate(self, value, field):
        errors = super().validate(value, field)
        if isinstance(value, UploadFile):
            if self.allowed_extensions:
                ext = Path(value.filename).suffix.lower().lstrip(".")
                if ext not in self.allowed_extensions:
                    errors.append(f"Allowed file types: {', '.join(self.allowed_extensions)}")
        return errors
```

### Handling in Submit Handler

```python
# In create/edit submit, after validation passes:
for field_meta in registered.form_fields:
    widget = registered.get_widget(field_meta.name)
    if not isinstance(widget, FileUploadWidget):
        continue

    action = form_data.get(f"{field_meta.name}_action", "keep")
    upload = form_data.get(field_meta.name)

    if action == "replace" and isinstance(upload, UploadFile) and upload.filename:
        contents = await upload.read()
        filename = sanitize_filename(upload.filename)
        path = await admin.storage.save(filename, contents)
        parsed[field_meta.name] = path

    elif action == "clear":
        # Delete old file from storage if exists
        old_path = getattr(obj, field_meta.name, None)
        if old_path:
            await admin.storage.delete(old_path)
        parsed[field_meta.name] = None

    # action == "keep": don't touch the field at all
```

### Image Preview (Alpine.js, client-side)

The image widget renders a preview that updates instantly on file selection without
a server round-trip:

```javascript
// Injected inline by image_upload macro
function imageUpload(existing) {
  return {
    preview: existing || null,
    action: "keep",
    onFileSelect(e) {
      const file = e.target.files[0];
      if (!file) return;
      this.action = "replace";
      this.preview = URL.createObjectURL(file);
    },
    clear() {
      this.preview = null;
      this.action = "clear";
    }
  }
}
```

---

## 12. Developer Override Paths

### Path A — Override widget for a specific field

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    formfield_overrides = {
        "description": RichTextWidget(toolbar="full"),
        "price": NumberInputWidget(step="0.01", min="0", max="99999"),
        "status": SelectWidget(choices=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ]),
    }
```

### Path B — Override widget globally for a column type

```python
# In your app startup — replaces Text widget everywhere
from fastapi_admin.widgets import widget_registry
widget_registry.register_type(sa_types.Text, RichTextWidget)

# Or for a field name pattern
widget_registry.register_name("description", RichTextWidget)
widget_registry.register_name("content", RichTextWidget)
widget_registry.register_name("body", RichTextWidget)
```

### Path C — Replace only the HTML macro (keep Python widget)

Create your macro file and register it:

```python
admin = Admin(
    app=app,
    engine=engine,
    extra_macro_files=["myapp/templates/macros/overrides.html"],
)
```

Your macro file can define any macro with the same name as a built-in to override it,
or new names for custom widgets:

```jinja2
{# myapp/templates/macros/overrides.html #}

{# Override the built-in textarea with a rich text editor #}
{% macro textarea(ctx, model_name) %}
<div class="field-wrapper" id="field-wrapper-{{ ctx.meta.name }}">
  <label class="field-label">{{ ctx.meta.label }}</label>
  <div
    id="editor-{{ ctx.meta.name }}"
    x-data="richText('{{ ctx.widget_context.value | e }}')"
  >
    <div x-ref="editor" class="rich-text-editor"></div>
    <input type="hidden" name="{{ ctx.meta.name }}" :value="content">
  </div>
</div>
{% endmacro %}
```

### Path D — Add non-model fields to the form

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    extra_fields = [
        ExtraField(
            name="notify_subscribers",
            label="Notify subscribers on save",
            widget=ToggleWidget(),
            default=False,
            required=False,
        )
    ]

    def after_create(self, obj, request):
        data = request.state.parsed_form
        if data.get("notify_subscribers"):
            send_product_notification.delay(obj.id)
```

### Path E — Dynamic field list (per-request)

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):

    def get_form_fields(self, obj=None, request=None) -> list[FieldMeta]:
        fields = super().get_form_fields(obj, request)
        user = request.state.admin_user
        if not user.is_superuser:
            fields = [f for f in fields if f.name != "cost_price"]
        return fields
```

### Path F — Custom form template

```python
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form_template = "myapp/product_form.html"
```

The custom template still receives the `form_context` object and can use built-in
macros or write raw HTML.

---

## 13. Custom Widget — Full Example

Building a `SlugWidget` that auto-generates from a `title` field:

### Python class

```python
# myapp/widgets.py

from fastapi_admin.widgets.base import Widget, FieldMeta
import re

class SlugWidget(Widget):
    macro_name = "slug_input"

    def __init__(self, source_field: str = "title"):
        self.source_field = source_field

    def render_context(self, field: FieldMeta, value) -> dict:
        ctx = super().render_context(field, value)
        ctx["source_field"] = self.source_field
        return ctx

    def parse(self, raw: str | None) -> str | None:
        if not raw:
            return None
        return re.sub(r"[^a-z0-9-]", "", raw.lower().replace(" ", "-"))

    def validate(self, value, field: FieldMeta) -> list[str]:
        errors = super().validate(value, field)
        if value and not re.match(r"^[a-z0-9-]+$", value):
            errors.append(f"{field.label} may only contain lowercase letters, numbers, and hyphens.")
        return errors
```

### Register it

```python
# Register by name pattern — any field named "slug"
widget_registry.register_name("slug", SlugWidget)

# Or register on a specific model field only
@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    formfield_overrides = {
        "slug": SlugWidget(source_field="title"),
    }
```

### Jinja2 macro

```jinja2
{# myapp/templates/macros/my_widgets.html #}

{% macro slug_input(ctx, model_name) %}
<div
  class="field-wrapper {% if ctx.errors %}has-error{% endif %}"
  id="field-wrapper-{{ ctx.meta.name }}"
  x-data="slugWidget('{{ ctx.widget_context.source_field }}')"
>
  <label for="field-{{ ctx.meta.name }}" class="field-label">
    {{ ctx.meta.label }}
    {% if ctx.meta.required %}<span class="required-star">*</span>{% endif %}
  </label>

  <div class="slug-input-row">
    <input
      type="text"
      id="field-{{ ctx.meta.name }}"
      name="{{ ctx.meta.name }}"
      :value="slug"
      @input="onManualEdit($event.target.value)"
      class="form-input {% if ctx.errors %}form-input-error{% endif %}"
    >
    <button type="button" @click="regenerate()" class="btn-secondary btn-sm">
      ↺ Regenerate
    </button>
  </div>

  {% if ctx.errors %}
    <ul class="field-errors">
      {% for err in ctx.errors %}<li>{{ err }}</li>{% endfor %}
    </ul>
  {% endif %}
</div>

<script>
function slugWidget(sourceField) {
  return {
    slug: document.querySelector(`[name="{{ ctx.meta.name }}"]`)?.value || "",
    manuallyEdited: false,

    init() {
      // Watch source field for changes
      const src = document.querySelector(`[name="${sourceField}"]`);
      if (src) {
        src.addEventListener("input", (e) => {
          if (!this.manuallyEdited) this.slug = this.toSlug(e.target.value);
        });
      }
    },

    toSlug(text) {
      return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    },

    onManualEdit(val) {
      this.slug = this.toSlug(val);
      this.manuallyEdited = true;
    },

    regenerate() {
      const src = document.querySelector(`[name="${sourceField}"]`);
      if (src) this.slug = this.toSlug(src.value);
      this.manuallyEdited = false;
    }
  }
}
</script>
{% endmacro %}
```

### Register the macro file

```python
admin = Admin(
    app=app,
    engine=engine,
    extra_macro_files=["myapp/templates/macros/my_widgets.html"],
)
```

---

## 14. FormContext Reference

```python
@dataclass
class FormContext:
    model_name: str                      # table name, e.g. "products"
    verbose_name: str                    # human name, e.g. "Product"
    is_create: bool                      # True = create form, False = edit
    obj: Any | None                      # existing DB object (edit only, None on create)
    fieldsets: list[FieldsetContext]     # fields grouped into sections
    errors: dict[str, list[str]]        # all validation errors keyed by field name
    values: dict[str, Any]              # current field values (parsed or from DB object)
    action_url: str                      # form POST URL
    list_url: str                        # "Back to list" URL
    can_delete: bool                     # show delete button (RBAC-driven)
    permissions: PermissionSet           # full permission flags for template conditionals


@dataclass
class FieldsetContext:
    title: str | None                    # section heading; None = no heading rendered
    collapsed: bool                      # Alpine.js initial collapsed state
    fields: list[FieldRenderContext]


@dataclass
class FieldRenderContext:
    meta: FieldMeta                      # name, label, required, readonly, help_text
    widget_macro: str                    # Jinja2 macro name to call
    widget_context: dict                 # variables from widget.render_context()
    errors: list[str]                    # validation errors for this specific field
```

---

## 15. Complete HTML Output Examples

### Text input (with validation error)

```html
<div class="field-wrapper has-error" id="field-wrapper-name">
  <label for="field-name" class="field-label">
    Name <span class="required-star">*</span>
  </label>
  <input
    type="text"
    id="field-name"
    name="name"
    value="x"
    maxlength="255"
    required
    class="form-input form-input-error"
    hx-post="/admin/products/validate-field"
    hx-trigger="blur"
    hx-target="#field-wrapper-name"
    hx-swap="outerHTML"
    hx-vals='{"field_name": "name"}'
  >
  <ul class="field-errors">
    <li>Name must be at least 3 characters.</li>
  </ul>
</div>
```

### Toggle (Boolean)

```html
<div class="field-wrapper" id="field-wrapper-is_active">
  <label class="field-label">Is Active</label>
  <label class="toggle-switch">
    <input type="checkbox" name="is_active" value="on" checked class="toggle-input">
    <span class="toggle-slider"></span>
  </label>
</div>
```

### Select (Enum)

```html
<div class="field-wrapper" id="field-wrapper-status">
  <label for="field-status" class="field-label">
    Status <span class="required-star">*</span>
  </label>
  <select id="field-status" name="status" required class="form-select">
    <option value="">— Select —</option>
    <option value="draft">Draft</option>
    <option value="published" selected>Published</option>
    <option value="archived">Archived</option>
  </select>
</div>
```

### DateTime picker

```html
<div class="field-wrapper" id="field-wrapper-published_at">
  <label for="field-published_at" class="field-label">Published At</label>
  <input
    type="datetime-local"
    id="field-published_at"
    name="published_at"
    value="2024-01-15T14:30"
    class="form-input"
    hx-post="/admin/articles/validate-field"
    hx-trigger="blur"
    hx-target="#field-wrapper-published_at"
    hx-swap="outerHTML"
    hx-vals='{"field_name": "published_at"}'
  >
</div>
```

### Relation picker (FK)

```html
<div
  class="field-wrapper"
  id="field-wrapper-category_id"
  x-data="relationPicker('3', 'Shoes', '/admin/categories/search')"
>
  <label class="field-label">Category</label>

  <!-- Hidden input carries the FK value submitted with the form -->
  <input type="hidden" name="category_id" :value="selectedId">

  <div class="relation-picker-input">
    <input
      type="text"
      :value="selectedLabel"
      @input.debounce.300ms="search($event.target.value)"
      @focus="open = true"
      @blur.outside="open = false"
      placeholder="Search categories..."
      class="form-input"
    >
    <button type="button" x-show="selectedId" @click="clear()" class="clear-btn">✕</button>
  </div>

  <div x-show="open && results.length" class="relation-picker-dropdown">
    <template x-for="item in results" :key="item.id">
      <div @click="select(item)" x-text="item.label" class="relation-picker-option"></div>
    </template>
    <div x-show="loading" class="relation-picker-loading">Searching...</div>
  </div>
</div>
```

### Multi-relation (many-to-many tags)

```html
<div
  class="field-wrapper"
  id="field-wrapper-tags"
  x-data="multiRelation([1,4], ['Python','Backend'], '/admin/tags/search')"
>
  <label class="field-label">Tags</label>

  <div class="selected-tags">
    <template x-for="(tag, i) in selected" :key="tag.id">
      <span class="tag-chip">
        <span x-text="tag.label"></span>
        <!-- Hidden inputs — FastAPI collects repeated keys as a list -->
        <input type="hidden" name="tags[]" :value="tag.id">
        <button type="button" @click="remove(i)" class="tag-remove">✕</button>
      </span>
    </template>
  </div>

  <input
    type="text"
    @input.debounce.300ms="search($event.target.value)"
    placeholder="Add tag..."
    class="form-input tag-search-input"
  >

  <div x-show="results.length" class="relation-picker-dropdown">
    <template x-for="item in results">
      <div @click="add(item)" x-text="item.label" class="relation-picker-option"></div>
    </template>
  </div>
</div>
```

### Read-only field (e.g. created_at)

```html
<div class="field-wrapper" id="field-wrapper-created_at">
  <label class="field-label">Created At</label>
  <span class="readonly-value">Jan 15, 2024, 2:30 PM</span>
  <!-- No <input>; value is never submitted -->
</div>
```

### JSON editor

```html
<div class="field-wrapper" id="field-wrapper-metadata">
  <label for="field-metadata" class="field-label">Metadata</label>
  <div
    id="json-editor-metadata"
    x-data="jsonEditor('field-metadata')"
    class="json-editor-wrapper"
  >
    <div x-ref="editorContainer"></div>
    <textarea id="field-metadata" name="metadata" class="sr-only">
      {"key": "value"}
    </textarea>
  </div>
</div>
```

---

## 16. Edge Cases

| Scenario | Handling |
|---|---|
| PK column on create form | `HiddenWidget` — not shown, not editable |
| PK column on edit form | `ReadOnlyWidget` — displayed, never in POST body |
| `created_at` / `updated_at` with `server_default` | Auto-added to `readonly_fields`; displayed as `ReadOnlyWidget` |
| Column named `password` or `*_hash` | `PasswordWidget`; `render_context` always sets `value=""` so it's never pre-filled |
| `Enum` column with zero values defined | Falls back to `TextInputWidget` with warning logged at startup |
| `JSON` column with invalid existing data | Editor pre-fills raw string; validation flags parse error |
| File field — no new file selected | `_action=keep` hidden input; existing DB value untouched |
| File field — user clicks Remove | `_action=clear`; DB column set to `None`; old file deleted from storage |
| FK to a model not registered with admin | `RelationPickerWidget` falls back to `NumberInputWidget` (enters raw FK id) |
| Self-referential FK (e.g. `parent_id`) | `RelationPickerWidget` — search endpoint excludes current object |
| Nullable Boolean | Three-state `SelectWidget`: Yes / No / — (None) instead of toggle |
| `ARRAY` column (PostgreSQL) | `TagInputWidget` — add/remove string tags; parsed to Python `list` |
| Form submitted with extra unknown keys | Silently ignored; only registered fields processed |
| Composite PK model | All PK fields included as `HiddenWidget` on create; `ReadOnlyWidget` on edit |
| `abstract = True` model | Skipped during auto-discovery; cannot be manually registered |
| File too large (exceeds `max_size_mb`) | Validated in `FileUploadWidget.validate()`; error shown before DB write |
