# Sidebar Tag & Group System

> **Scope:** How to assign tags to registered models so the sidebar nav groups them
> into collapsible sections — like API tags in OpenAPI/Swagger. Covers the data model,
> registration API, sidebar rendering, RBAC interaction, ordering, custom groups,
> and all edge cases.

---

## Table of Contents

1. [Goal & Mental Model](#1-goal--mental-model)
2. [What It Looks Like](#2-what-it-looks-like)
3. [Tag Data Model](#3-tag-data-model)
4. [How to Assign Tags](#4-how-to-assign-tags)
   - 4.1 [On ModelAdmin (per model)](#41-on-modeladmin-per-model)
   - 4.2 [On Admin init (global tag config)](#42-on-admin-init-global-tag-config)
   - 4.3 [Zero-config fallback](#43-zero-config-fallback)
5. [NavGroup Data Model](#5-navgroup-data-model)
6. [Sidebar Builder — How Groups Are Assembled](#6-sidebar-builder--how-groups-are-assembled)
7. [Sidebar Template](#7-sidebar-template)
8. [Ordering — Groups and Items Within Groups](#8-ordering--groups-and-items-within-groups)
9. [Icons Per Group](#9-icons-per-group)
10. [Collapsible State (Alpine.js)](#10-collapsible-state-alpinejs)
11. [RBAC Interaction](#11-rbac-interaction)
12. [Active State Highlighting](#12-active-state-highlighting)
13. [Custom (Non-Model) Nav Items Inside Groups](#13-custom-non-model-nav-items-inside-groups)
14. [Ungrouped Models Fallback](#14-ungrouped-models-fallback)
15. [Full Registration Examples](#15-full-registration-examples)
16. [SidebarBuilder Protocol (Pluggable)](#16-sidebarbuilder-protocol-pluggable)
17. [Edge Cases](#17-edge-cases)

---

## 1. Goal & Mental Model

Think of it exactly like OpenAPI/Swagger tags. In FastAPI you write:

```python
@app.get("/products/", tags=["Catalogue"])
@app.get("/orders/",   tags=["Orders"])
```

And Swagger UI groups routes under collapsible tag sections.

The admin sidebar works the same way. You assign a `tag` (or `tags`) to each
`ModelAdmin`. The sidebar builder collects all registered models, groups them by
tag, and renders each group as a collapsible section.

```
Without tags (flat list):         With tags (grouped):
─────────────────────             ─────────────────────────────
  • Products                        ▾ CATALOGUE
  • Categories                          • Products
  • Orders                              • Categories
  • OrderItems                          • Brands
  • Users                           ▾ ORDERS
  • Roles                               • Orders
                                        • Order Items
                                    ► USERS  (collapsed)
                                        • Users
                                        • Roles
```

---

## 2. What It Looks Like

Full sidebar layout with tag groups:

```
┌─────────────────────────────┐
│  🏢  Acme Admin             │
├─────────────────────────────┤
│  📊  Dashboard              │
│                             │
│  ▾ CATALOGUE                │  ← group heading (tag label)
│      📦  Products           │  ← model nav item
│      🗂️  Categories         │
│      🏷️  Brands             │
│                             │
│  ▾ ORDERS                   │
│      🛒  Orders             │
│      📋  Order Items        │
│      🔄  Returns            │
│                             │
│  ► USERS                    │  ← collapsed group
│                             │
│  ▾ CONTENT                  │
│      📝  Articles           │
│      💬  Comments           │
│                             │
│  ─────────────────          │  ← divider before system items
│  🔍  Audit Log              │
│  🛡️  Roles                  │
│  ⚙️  Settings               │
└─────────────────────────────┘
```

---

## 3. Tag Data Model

A tag is a simple string label attached to a `ModelAdmin`. The sidebar builder reads all
tags and constructs `NavGroup` objects at startup.

```python
# fastapi_admin/nav.py

from dataclasses import dataclass, field

@dataclass
class NavGroup:
    """One collapsible section in the sidebar."""
    tag: str                            # the tag string, e.g. "Catalogue"
    label: str                          # display label; defaults to tag.title()
    icon: str | None = None             # Heroicon name for the group heading
    order: int = 999                    # sort order; lower = higher in sidebar
    collapsed_by_default: bool = False  # initial collapsed state
    items: list["NavItem"] = field(default_factory=list)  # populated by builder


@dataclass
class NavItem:
    """One model link inside a group (or at top level if ungrouped)."""
    label: str                          # display label
    url: str                            # href
    icon: str | None = None             # Heroicon name
    order: int = 999                    # sort order within the group
    badge: str | None = None            # optional count badge e.g. "12"
    badge_color: str = "primary"        # "primary" | "danger" | "warning"
    permission_table: str | None = None # table_name to check can_view for
    children: list["NavItem"] = field(default_factory=list)  # nested items (depth 1 only)
```

---

## 4. How to Assign Tags

### 4.1 On ModelAdmin (per model)

The simplest and most common approach. Add `tag` (single) or `tags` (multiple):

```python
# Single tag
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "cube"                # icon for this model's nav item
    verbose_name_plural = "Products"


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "tag"


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "building-storefront"
    nav_order = 3               # position within the "Catalogue" group


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    tag = "Orders"
    icon = "shopping-cart"


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    tag = "Orders"
    icon = "list-bullet"
    nav_order = 2


@admin.register(User)
class UserAdmin(ModelAdmin):
    tag = "Users"
    icon = "user"
    superuser_only = True       # still works — just hidden from non-superusers


@admin.register(Role)
class RoleAdmin(ModelAdmin):
    tag = "Users"
    icon = "shield-check"
```

**Multiple tags** — model appears in more than one group:

```python
@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    tags = ["Marketing", "Orders"]   # appears in both groups
    icon = "ticket"
```

**Zero config (no ModelAdmin class)**:

```python
admin.register(Product, tag="Catalogue", icon="cube")
# or using the decorator with just tag:
@admin.register(Product, tag="Catalogue", icon="cube")
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price"]
```

---

### 4.2 On Admin init (global tag config)

Define all groups upfront, with their display labels, icons, and ordering, separately
from the model registration. This separates nav structure from model config:

```python
from fastapi_admin.nav import NavGroupConfig

admin = Admin(
    app=app,
    engine=engine,
    nav_groups=[
        NavGroupConfig(
            tag="Catalogue",
            label="Catalogue",          # display label (defaults to tag.title())
            icon="cube",                # Heroicon for the group heading
            order=1,                    # position in sidebar
            collapsed_by_default=False,
        ),
        NavGroupConfig(
            tag="Orders",
            label="Order Management",   # different label from tag name
            icon="shopping-cart",
            order=2,
            collapsed_by_default=False,
        ),
        NavGroupConfig(
            tag="Users",
            label="Users & Roles",
            icon="users",
            order=3,
            collapsed_by_default=True,  # collapsed by default
        ),
        NavGroupConfig(
            tag="Marketing",
            label="Marketing",
            icon="megaphone",
            order=4,
        ),
        NavGroupConfig(
            tag="Content",
            label="Content",
            icon="document-text",
            order=5,
        ),
    ],
)
```

Models that have `tag = "Catalogue"` are automatically placed into the `NavGroupConfig`
with matching tag. Group config and model tag assignment are fully independent — you
can define groups without models (empty group, hidden) or have models with tags that
don't have a group config (auto-created with defaults).

---

### 4.3 Zero-config fallback

If a developer registers a model with no tag at all, it lands in an auto-created
**"Other"** group at the bottom of the sidebar. This ensures nothing is ever lost:

```python
admin.register(SomeModel)    # no tag → appears in "Other"
```

To disable the "Other" group and force all models to have explicit tags:

```python
admin = Admin(
    app=app,
    engine=engine,
    require_tags=True,        # raises ConfigError at startup for untagged models
)
```

---

## 5. NavGroup Data Model

Full internal representation built by `SidebarBuilder` at startup:

```python
# fastapi_admin/nav.py

@dataclass
class BuiltNavGroup:
    """Resolved group, ready for template rendering."""
    tag: str
    label: str
    icon: str | None
    order: int
    collapsed_by_default: bool
    items: list[BuiltNavItem]           # sorted, RBAC-filtered at render time


@dataclass
class BuiltNavItem:
    label: str
    url: str
    icon: str | None
    order: int
    badge_fn: Callable | None          # called at render time to get badge count
    permission_table: str | None       # table_name; checked against user's permissions
    children: list["BuiltNavItem"]
```

---

## 6. Sidebar Builder — How Groups Are Assembled

The `SidebarBuilder` runs once at startup (not per-request) to produce the static
group structure. Per-request, only RBAC filtering and badge computation run.

```python
# fastapi_admin/nav.py

class SidebarBuilder:

    def build(
        self,
        registry: AdminRegistry,
        nav_group_configs: list[NavGroupConfig],
    ) -> list[BuiltNavGroup]:
        """
        Called once at startup. Returns the full sidebar structure
        (before RBAC filtering — that happens at render time).
        """

        # Step 1: index NavGroupConfigs by tag (case-insensitive)
        group_index: dict[str, NavGroupConfig] = {
            cfg.tag.lower(): cfg for cfg in nav_group_configs
        }

        # Step 2: bucket each registered model into its tag(s)
        buckets: dict[str, list[BuiltNavItem]] = {}
        for registered in registry.all():
            tags = self._get_tags(registered)
            for tag in tags:
                if tag not in buckets:
                    buckets[tag] = []
                buckets[tag].append(BuiltNavItem(
                    label=registered.verbose_name_plural,
                    url=f"/admin/{registered.table_name}/",
                    icon=registered.admin.icon,
                    order=getattr(registered.admin, "nav_order", 999),
                    badge_fn=getattr(registered.admin, "get_nav_badge", None),
                    permission_table=registered.table_name,
                    children=[],
                ))

        # Step 3: build BuiltNavGroup for each bucket
        groups: list[BuiltNavGroup] = []
        all_tags = set(buckets.keys())

        for tag in all_tags:
            cfg = group_index.get(tag.lower())
            groups.append(BuiltNavGroup(
                tag=tag,
                label=cfg.label if cfg else tag.title(),
                icon=cfg.icon if cfg else None,
                order=cfg.order if cfg else 999,
                collapsed_by_default=cfg.collapsed_by_default if cfg else False,
                items=sorted(buckets[tag], key=lambda x: (x.order, x.label)),
            ))

        # Step 4: sort groups by order, then alpha
        groups.sort(key=lambda g: (g.order, g.label))

        return groups

    def _get_tags(self, registered: RegisteredModel) -> list[str]:
        """Extract tag(s) from a registered model's admin config."""
        admin = registered.admin
        if hasattr(admin, "tags") and admin.tags:
            return admin.tags
        if hasattr(admin, "tag") and admin.tag:
            return [admin.tag]
        return ["Other"]   # ungrouped fallback
```

---

## 7. Sidebar Template

The sidebar template iterates `nav_groups` from the Jinja2 context. Each group is a
collapsible section. RBAC filtering happens here at render time.

```jinja2
{# templates/partials/sidebar.html #}

<nav class="sidebar-nav">

  {# Dashboard — always at top, no group #}
  <a href="/admin/"
     class="nav-item {% if request.url.path == '/admin/' %}nav-item-active{% endif %}">
    {% call icon("squares-2x2") %}{% endcall %}
    <span>Dashboard</span>
  </a>

  {# Tag groups — auto-generated from registered models #}
  {% for group in nav_groups %}

    {# Collect items this user can see (RBAC filter) #}
    {% set visible_items = [] %}
    {% for item in group.items %}
      {% if item.permission_table is none
         or permissions_map[item.permission_table].can_view %}
        {% do visible_items.append(item) %}
      {% endif %}
    {% endfor %}

    {# Skip group entirely if user can't see any of its models #}
    {% if visible_items %}
      <div
        class="nav-group"
        x-data="navGroup('{{ group.tag | slugify }}', {{ 'true' if group.collapsed_by_default else 'false' }})"
      >
        {# Group heading — clickable to toggle #}
        <button
          class="nav-group-heading"
          @click="toggle()"
          :aria-expanded="!collapsed"
        >
          {% if group.icon %}
            {% call icon(group.icon, class="nav-group-icon") %}{% endcall %}
          {% endif %}
          <span class="nav-group-label">{{ group.label | upper }}</span>
          <svg class="nav-group-chevron" :class="{'rotate-180': !collapsed}"
               xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd"
                  d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
                  clip-rule="evenodd"/>
          </svg>
        </button>

        {# Group items — shown/hidden by Alpine #}
        <div x-show="!collapsed" x-collapse>
          {% for item in visible_items %}
            {% set is_active = request.url.path.startswith(item.url) %}
            <a
              href="{{ item.url }}"
              class="nav-item nav-item-child {% if is_active %}nav-item-active{% endif %}"
            >
              {% if item.icon %}
                {% call icon(item.icon, class="nav-item-icon") %}{% endcall %}
              {% endif %}
              <span>{{ item.label }}</span>

              {# Optional badge (e.g. pending count) #}
              {% if item.badge %}
                <span class="nav-badge nav-badge-{{ item.badge_color }}">
                  {{ item.badge }}
                </span>
              {% endif %}
            </a>

            {# Nested children (depth 1 only) #}
            {% for child in item.children %}
              {% if child.permission_table is none
                 or permissions_map[child.permission_table].can_view %}
                <a href="{{ child.url }}"
                   class="nav-item nav-item-grandchild
                          {% if request.url.path.startswith(child.url) %}nav-item-active{% endif %}">
                  {{ child.label }}
                </a>
              {% endif %}
            {% endfor %}

          {% endfor %}
        </div>
      </div>
    {% endif %}

  {% endfor %}

  {# System section — always at bottom #}
  <div class="nav-divider"></div>
  <a href="/admin/audit-log/" class="nav-item">
    {% call icon("magnifying-glass") %}{% endcall %}
    <span>Audit Log</span>
  </a>
  {% if current_user.is_superuser %}
    <a href="/admin/roles/" class="nav-item">
      {% call icon("shield-check") %}{% endcall %}
      <span>Roles</span>
    </a>
  {% endif %}

</nav>
```

---

## 8. Ordering — Groups and Items Within Groups

### Group order

Groups are sorted by `NavGroupConfig.order` (ascending). Groups without a config
default to `order=999` and sort alphabetically among themselves.

```python
nav_groups=[
    NavGroupConfig(tag="Catalogue", order=1),
    NavGroupConfig(tag="Orders",    order=2),
    NavGroupConfig(tag="Users",     order=3),
    # Any unrecognised tags auto-created with order=999
]
```

### Item order within a group

Items within a group are sorted by `ModelAdmin.nav_order` (ascending), then alphabetically
by `verbose_name_plural`. The `nav_order` attribute is an integer you set on `ModelAdmin`:

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    tag = "Orders"
    nav_order = 1          # first in the Orders group


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    tag = "Orders"
    nav_order = 2          # second


@admin.register(Return)
class ReturnAdmin(ModelAdmin):
    tag = "Orders"
    nav_order = 3          # third
```

If no `nav_order` is set, items sort alphabetically. No two items need the same order
value — gaps are fine (`1, 5, 10, 20` is equivalent to `1, 2, 3, 4`).

---

## 9. Icons Per Group

Icons are set separately for the group heading and for each model item:

```python
# Group heading icon — set in NavGroupConfig
NavGroupConfig(tag="Catalogue", icon="cube", order=1)

# Model item icon — set in ModelAdmin
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "archive-box"       # Heroicon name (outline variant)
```

If no icon is set on a model, no icon renders (text only). If no icon is set on a group,
the group heading renders text only with the chevron.

### Available Heroicon names (examples)

Group-level icons that work well: `cube`, `shopping-cart`, `users`, `document-text`,
`chart-bar`, `cog-6-tooth`, `megaphone`, `building-office`, `globe-alt`, `shield-check`.

Model-level icons: `archive-box`, `list-bullet`, `tag`, `ticket`, `user`,
`building-storefront`, `truck`, `currency-dollar`, `photo`, `link`, `calendar`.

Full list at https://heroicons.com — use the outline variant name.

---

## 10. Collapsible State (Alpine.js)

Each group is independently collapsible. State persists in `localStorage` so the
sidebar remembers which groups were open across page loads.

```javascript
// static/js/admin.js

function navGroup(tag, defaultCollapsed) {
  return {
    collapsed: false,

    init() {
      // Restore state from localStorage
      const saved = localStorage.getItem(`admin-nav-group:${tag}`);
      if (saved !== null) {
        this.collapsed = saved === "1";
      } else {
        this.collapsed = defaultCollapsed;
      }

      // Auto-expand if a child item is active (current page is in this group)
      const hasActive = this.$el.querySelector(".nav-item-active");
      if (hasActive) {
        this.collapsed = false;    // always expand if active child
      }
    },

    toggle() {
      this.collapsed = !this.collapsed;
      localStorage.setItem(`admin-nav-group:${tag}`, this.collapsed ? "1" : "0");
    }
  }
}
```

**Rules for collapsed state:**

1. First visit (no localStorage): use `collapsed_by_default` from `NavGroupConfig`.
2. Subsequent visits: restore from localStorage.
3. If the current page is a child of this group: always expand, regardless of stored state.
4. Toggle by clicking the group heading row.

The `x-collapse` Alpine directive provides a smooth height animation. It requires the
`@alpinejs/collapse` plugin:

```html
<script src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
```

---

## 11. RBAC Interaction

RBAC filtering of sidebar items happens at render time (per request), not at build time.
The `SidebarBuilder` produces all groups and items. The template filters them by
checking `permissions_map[item.permission_table].can_view`.

### Context variable: `permissions_map`

The base view injects a `permissions_map` dict into every template context:

```python
# fastapi_admin/views/base.py

def build_sidebar_context(request: Request, checker: PermissionChecker,
                           nav_groups: list[BuiltNavGroup]) -> dict:
    """
    Build the sidebar context for every admin page.
    Called in every route handler's get_template_context().
    """
    # Build a permissions map for every registered table
    permissions_map = {
        group_item.permission_table: checker.permission_set(group_item.permission_table)
        for group in nav_groups
        for group_item in group.items
        if group_item.permission_table
    }
    return {
        "nav_groups": nav_groups,
        "permissions_map": permissions_map,
        "current_user": request.state.admin_user,
    }
```

### What gets hidden

- A **model nav item** is hidden if `permissions_map[table_name].can_view == False`.
- A **group heading** is hidden if ALL items inside it are hidden (user can't see any model in the group).
- A group with **zero visible items** does not render at all — no empty section headers.
- System items (Audit Log, Roles) have their own hardcoded permission checks.

### Example

```
User role: Editor (can view Catalogue and Content, cannot view Orders or Users)

Sidebar renders:
  ▾ CATALOGUE          ← visible (has accessible models)
      • Products
      • Categories
  ▾ CONTENT            ← visible
      • Articles
  [Orders group hidden — no view permission on any Orders model]
  [Users group hidden — no view permission on User or Role]
```

---

## 12. Active State Highlighting

A nav item is "active" if `request.url.path` starts with the item's URL:

```jinja2
{% set is_active = request.url.path.startswith(item.url) %}
<a href="{{ item.url }}" class="nav-item {% if is_active %}nav-item-active{% endif %}">
```

This means `/admin/products/create`, `/admin/products/42`, and `/admin/products/`
all highlight the Products nav item. The group containing the active item is always
expanded (see §10).

**CSS for active state:**

```css
.nav-item-active {
  background-color: var(--color-primary-50);
  color: var(--color-primary-700);
  font-weight: 600;
  border-left: 3px solid var(--color-primary-500);
}

[data-theme="dark"] .nav-item-active {
  background-color: rgba(99, 102, 241, 0.15);
  color: var(--color-primary-300);
}
```

---

## 13. Custom (Non-Model) Nav Items Inside Groups

You can add custom nav items (links to custom pages, reports, external tools) into
any tag group — not just model links:

```python
from fastapi_admin.nav import NavGroupConfig, NavItemConfig

admin = Admin(
    app=app,
    engine=engine,
    nav_groups=[
        NavGroupConfig(
            tag="Orders",
            label="Order Management",
            icon="shopping-cart",
            order=2,
            extra_items=[
                NavItemConfig(
                    label="Revenue Report",
                    url="/admin/reports/revenue",
                    icon="chart-bar",
                    order=100,                   # after model links
                    permission="view_reports",   # custom permission key, or None for all
                ),
                NavItemConfig(
                    label="Export Orders",
                    url="/admin/orders/export",
                    icon="arrow-down-tray",
                    order=101,
                ),
            ],
        ),
    ],
)
```

Or attach custom nav items directly on the `ModelAdmin`:

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    tag = "Orders"
    nav_children = [
        NavItemConfig(
            label="Pending Orders",
            url="/admin/orders/?status=pending",
            icon="clock",
        ),
        NavItemConfig(
            label="Export CSV",
            url="/admin/orders/export",
            icon="arrow-down-tray",
        ),
    ]
```

These render as indented child links under the Orders model link:

```
  ▾ ORDERS
      🛒  Orders
          ⏰  Pending Orders     ← child nav item
          ⬇  Export CSV         ← child nav item
      📋  Order Items
```

---

## 14. Ungrouped Models Fallback

Models with no tag are placed in an auto-created "Other" group that renders after all
tagged groups. Within "Other", items sort alphabetically.

```python
# These have no tag — land in "Other"
admin.register(SomeUtilityModel)
admin.register(AnotherModel)
```

```
Sidebar:
  ▾ CATALOGUE
  ▾ ORDERS
  ▾ OTHER          ← auto-created, always last
      • AnotherModel
      • SomeUtilityModel
```

You can rename or reorder the "Other" group by including a config entry for it:

```python
NavGroupConfig(
    tag="Other",
    label="Miscellaneous",
    icon="ellipsis-horizontal",
    order=99,
    collapsed_by_default=True,
)
```

To suppress it entirely and force explicit tagging:

```python
admin = Admin(app=app, engine=engine, require_tags=True)
# Raises ConfigError at startup if any model has no tag
```

---

## 15. Full Registration Examples

### Example A — E-commerce admin

```python
from fastapi_admin.nav import NavGroupConfig

admin = Admin(
    app=app,
    engine=engine,
    nav_groups=[
        NavGroupConfig(tag="Catalogue",  label="Catalogue",      icon="cube",          order=1),
        NavGroupConfig(tag="Orders",     label="Orders",         icon="shopping-cart", order=2),
        NavGroupConfig(tag="Customers",  label="Customers",      icon="users",         order=3),
        NavGroupConfig(tag="Marketing",  label="Marketing",      icon="megaphone",     order=4),
        NavGroupConfig(tag="Settings",   label="Settings",       icon="cog-6-tooth",   order=5,
                       collapsed_by_default=True),
    ],
)


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "archive-box"
    nav_order = 1
    list_display = ["name", "price", "stock", "is_active"]

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "tag"
    nav_order = 2

@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    tag = "Catalogue"
    icon = "building-storefront"
    nav_order = 3

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    tag = "Orders"
    icon = "shopping-cart"
    nav_order = 1

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    tag = "Orders"
    icon = "list-bullet"
    nav_order = 2

@admin.register(Return)
class ReturnAdmin(ModelAdmin):
    tag = "Orders"
    icon = "arrow-uturn-left"
    nav_order = 3

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    tag = "Customers"
    icon = "user"
    nav_order = 1

@admin.register(Address)
class AddressAdmin(ModelAdmin):
    tag = "Customers"
    icon = "map-pin"
    nav_order = 2

@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    tags = ["Marketing", "Orders"]   # appears in both groups
    icon = "ticket"

@admin.register(EmailCampaign)
class EmailCampaignAdmin(ModelAdmin):
    tag = "Marketing"
    icon = "envelope"

@admin.register(TaxRate)
class TaxRateAdmin(ModelAdmin):
    tag = "Settings"
    icon = "percent-badge"

@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    tag = "Settings"
    icon = "globe-alt"
```

Resulting sidebar:

```
📊  Dashboard

▾ CATALOGUE
    📦  Products
    🏷️  Categories
    🏬  Brands

▾ ORDERS
    🛒  Orders
    📋  Order Items
    ↩️  Returns
    🎟️  Coupons

▾ CUSTOMERS
    👤  Customers
    📍  Addresses

▾ MARKETING
    📧  Email Campaigns
    🎟️  Coupons

► SETTINGS  (collapsed by default)
    💱  Tax Rates
    🌍  Shipping Zones

────────────────
🔍  Audit Log
🛡️  Roles
```

---

### Example B — SaaS admin with minimal config

When you just want grouping without defining `NavGroupConfig`:

```python
# No NavGroupConfig at all — groups auto-created from tags used on ModelAdmin

@admin.register(Workspace)
class WorkspaceAdmin(ModelAdmin):
    tag = "Account"
    icon = "building-office"

@admin.register(Member)
class MemberAdmin(ModelAdmin):
    tag = "Account"
    icon = "user-group"

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    tag = "Billing"
    icon = "credit-card"

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    tag = "Billing"
    icon = "document-text"

@admin.register(ApiKey)
class ApiKeyAdmin(ModelAdmin):
    tag = "Developers"
    icon = "key"

@admin.register(Webhook)
class WebhookAdmin(ModelAdmin):
    tag = "Developers"
    icon = "arrow-path"
```

Sidebar (groups ordered alphabetically since no `order` given):

```
📊  Dashboard

▾ ACCOUNT
    🏢  Workspaces
    👥  Members

▾ BILLING
    💳  Subscriptions
    📄  Invoices

▾ DEVELOPERS
    🔑  API Keys
    🔃  Webhooks

────────────────
🔍  Audit Log
🛡️  Roles
```

---

## 16. SidebarBuilder Protocol (Pluggable)

The `SidebarBuilder` itself is swappable. Implement the protocol to build the sidebar
from any source (database-driven groups, external config, feature flags, etc.):

```python
# fastapi_admin/nav.py

class SidebarBuilder(Protocol):
    def build(
        self,
        registry: AdminRegistry,
        nav_group_configs: list[NavGroupConfig],
    ) -> list[BuiltNavGroup]:
        ...
```

### Example — database-driven group order

```python
class DBDrivenSidebarBuilder:
    """
    Reads group order from a `admin_nav_groups` table so
    non-developers can reorder groups via a UI.
    """

    def build(self, registry, nav_group_configs) -> list[BuiltNavGroup]:
        # Get order from DB (sync call at startup is fine)
        db_groups = {
            row.tag: row.order
            for row in db.execute("SELECT tag, display_order FROM admin_nav_groups").all()
        }

        # Merge DB order into configs
        for cfg in nav_group_configs:
            if cfg.tag in db_groups:
                cfg.order = db_groups[cfg.tag]

        # Fall through to default logic
        return DefaultSidebarBuilder().build(registry, nav_group_configs)


admin = Admin(
    app=app,
    engine=engine,
    sidebar_builder=DBDrivenSidebarBuilder(),
)
```

### Example — feature-flag driven groups

```python
class FeatureFlagSidebarBuilder:
    """Hides entire groups when their feature flag is disabled."""

    def __init__(self, flags: dict[str, bool]):
        # flags = {"Developers": True, "BetaFeatures": False}
        self.flags = flags

    def build(self, registry, nav_group_configs) -> list[BuiltNavGroup]:
        groups = DefaultSidebarBuilder().build(registry, nav_group_configs)
        return [g for g in groups if self.flags.get(g.tag, True)]


admin = Admin(
    app=app,
    engine=engine,
    sidebar_builder=FeatureFlagSidebarBuilder(flags=feature_flags.all()),
)
```

---

## 17. Edge Cases

| Scenario | Handling |
|---|---|
| Model has `tag` and `tags` both set | `tags` wins; `tag` is ignored |
| Two models in the same tag with same `nav_order` | Both render; tie-broken alphabetically by label |
| `NavGroupConfig` defined for a tag with no models | Empty group; not rendered in sidebar (no visible items) |
| Model tag doesn't match any `NavGroupConfig` | Auto-created `NavGroup` with `label=tag.title()`, `order=999`, default icon |
| All models in a group are hidden by RBAC | Group heading not rendered at all |
| Model appears in multiple groups (`tags = [...]`) | Appears in each group independently; active state highlights both groups' parents |
| User has no permissions on any model | Only Dashboard, Audit Log (if permitted) rendered in sidebar |
| `require_tags=True` and an untagged model | `ConfigError` raised at startup listing the offending models |
| `collapsed_by_default=True` but current page is in the group | Group auto-expands (active child overrides default) |
| `nav_order` not set on any model in a group | All items sorted alphabetically |
| Two models with same `verbose_name_plural` in same group | Both render; distinguished only by URL |
| Model registered with zero-config (`admin.register(X)`) and tag kwarg | `admin.register(Product, tag="Catalogue")` sets tag on auto-created `ModelAdmin` |
| Icon name that doesn't exist in Heroicons sprite | No icon renders; no error — `<use>` simply produces nothing |
| Group with only `extra_items` (no model links) | Renders the group with those items; no model links |
| `nav_children` defined on ModelAdmin | Rendered as indented sub-links under the model's nav item (depth 1 only) |
| Sidebar badge (`get_nav_badge`) raises exception | Badge silently omitted; exception logged; page still renders |