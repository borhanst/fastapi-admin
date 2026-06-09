# FastAPI Admin — Agent Guide

## What This Project Is

A drop-in admin panel for FastAPI + SQLAlchemy apps. Register a model, get full CRUD UI, auth, permissions, and audit logging — no manual form or view definitions required.

## Spec Documents

| File | Covers |
|---|---|
| `fastapi_admin_core_spec.md` | The 3 core bets: auto-discovery, audit log + RBAC, modern UI. Start here. |
| `AUTH_RBAC_SYSTEM.md` | Auth model extensibility (built-in / extend / BYO), session flow, RBAC permission tables and checks |
| `FORM_WIDGET_SYSTEM.md` | Widget class layer → Jinja2 macro layer, form pipeline, validation, relationship widgets |
| `PLUGIN_SYSTEM.md` | Every extension point: widgets, hooks, routes, auth, storage, audit sinks, dashboard, UI |

## Architecture in One Paragraph

On startup, `Admin()` inspects every registered SQLAlchemy model, maps column types to widgets, and auto-generates CRUD routes under `/admin/{table}/`. Each request hits an auth middleware (session cookie → `AuthBackend.get_user`), then a `PermissionChecker` that reads `admin_permissions` rows keyed by `user.role_id`. Forms are rendered via `Widget.render_context()` → Jinja2 macros (Tailwind + HTMX + Alpine.js). Every DB write fires SQLAlchemy session events that write to `admin_audit_log`. Everything is replaceable via protocols.

## Key Concepts

- **RegisteredModel** — central dataclass holding the model class, its `ModelAdmin` config, inspected columns/relationships, and resolved widgets
- **Widget** — two-layer: Python class (parse + validate) + Jinja2 macro (HTML). Override either independently
- **PermissionChecker** — instantiated per request; checks `admin_permissions` table; superusers bypass all checks
- **AuthBackend** — two methods: `authenticate()` on login, `get_user()` on every request
- **AdminPlugin** — bundles widgets, macros, routes, nav items, hooks into a distributable package
- **AuditLog** — written via SQLAlchemy `after_flush` event; stores full snapshot + diff for UPDATEs

## Project Structure (key paths)

```
fastapi_admin/
├── admin.py          # Admin class, public API, wires everything at init
├── registry.py       # AdminRegistry singleton
├── inspection.py     # SQLAlchemy model → ColumnMeta / RelationMeta
├── field_types.py    # Column type → widget name mapping
├── router.py         # Auto-route generation per registered model
├── auth/             # AuthBackend, PermissionChecker, session, dependencies
├── audit/            # AuditLog model, SQLAlchemy event listener, diff, context
├── widgets/          # Widget base class, all built-in widgets, WidgetRegistry
├── views/            # Route handler factories (list, form, delete, roles, dashboard)
├── templates/        # Jinja2: base.html, pages/, partials/, macros/
└── static/           # Tailwind CSS, HTMX, Alpine.js, Heroicons
```

## Tech Stack

FastAPI · SQLAlchemy 2.x · Jinja2 · Tailwind CSS · HTMX · Alpine.js · itsdangerous · passlib/bcrypt . uv

## What to Build (suggested order)

1. `inspection.py` + `field_types.py` — model inspection and type→widget mapping
2. `registry.py` + `admin.py` — registration API and `ModelAdmin` base
3. `auth/` — models, session, `AuthBackend`, `PermissionChecker`, dependencies
4. `audit/` — listener, diff, `AuditLog` model
5. `widgets/` — base class, built-in widgets, `WidgetRegistry`
6. `views/` + `router.py` — route factories, form pipeline
7. `templates/` — Jinja2 templates and macros
8. `plugins/` — `AdminPlugin` base, plugin registration
