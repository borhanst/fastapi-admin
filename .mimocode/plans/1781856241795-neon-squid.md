# Plan: Make FastAPI Admin UI Fully Customizable & Configurable

## Vision
Transform the admin UI from a fixed "warm editorial brutalism" theme into a fully configurable design system where every visual aspect — colors, fonts, spacing, layout, motion — can be overridden via Python config. Support multiple theme presets and expose a runtime theme builder.

---

## Phase 1: Complete CSS Variable System + Theme Presets
**Goal:** Make every visual property configurable via CSS variables with sensible defaults.

### 1A. Expand Design Tokens
**File:** `fastapi_admin/static/css/tokens.css` (177 lines)

The file already defines core variables (`--surface-*`, `--text-*`, `--primary-*`, `--radius-*`, `--shadow-*`, `--duration-*`, `--easing-*`). We need to add `--admin-*` prefixed variables as the "user-overrideable" layer that sits on top.

**Changes:**
- After the existing `:root { ... }` block (line 123), add a new `:root` block with `--admin-*` variables that reference the existing tokens as defaults:
  ```css
  /* ── Admin-overrideable layer (set via Python ThemeConfig) ── */
  :root {
    --admin-font-display: var(--font-display);
    --admin-font-body: var(--font-body);
    --admin-font-mono: var(--font-mono);
    --admin-font-size-base: var(--text-base);
    --admin-font-size-sm: var(--text-sm);
    --admin-font-size-xs: var(--text-xs);
    --admin-topbar-height: var(--topbar-height);
    --admin-sidebar-width: var(--sidebar-width);
    --admin-sidebar-collapsed: var(--sidebar-collapsed);
    --admin-content-max-width: var(--content-max-width);
    --admin-content-padding: var(--content-padding);
    --admin-radius-sm: var(--radius-sm);
    --admin-radius-md: var(--radius-md);
    --admin-radius-lg: var(--radius-lg);
    --admin-shadow-xs: var(--shadow-xs);
    --admin-shadow-sm: var(--shadow-sm);
    --admin-shadow-md: var(--shadow-md);
    --admin-shadow-lg: var(--shadow-lg);
    --admin-shadow-focus: var(--shadow-focus);
    --admin-shadow-focus-error: var(--shadow-focus-error);
    --admin-duration-fast: var(--duration-fast);
    --admin-duration-base: var(--duration-base);
    --admin-duration-slow: var(--duration-slow);
    --admin-easing: var(--easing-out);
    --admin-easing-spring: var(--easing-spring);
    --admin-grain-opacity: 0.025;
    --admin-accent-line-opacity: 0.4;
  }
  ```
- Add CSS variables for the new semantic color tokens that don't exist yet:
  ```css
  :root {
    --admin-surface-base: var(--surface-base);
    --admin-surface-raised: var(--surface-raised);
    --admin-surface-overlay: var(--surface-overlay);
    --admin-surface-inset: var(--surface-inset);
    --admin-surface-border: var(--surface-border);
    --admin-text-primary: var(--text-primary);
    --admin-text-secondary: var(--text-secondary);
    --admin-text-disabled: var(--text-disabled);
    --admin-text-inverse: var(--text-inverse);
    --admin-primary-50: var(--primary-50);
    --admin-primary-100: var(--primary-100);
    --admin-primary-200: var(--primary-200);
    --admin-primary-300: var(--primary-300);
    --admin-primary-400: var(--primary-400);
    --admin-primary-500: var(--primary-500);
    --admin-primary-600: var(--primary-600);
    --admin-primary-700: var(--primary-700);
    --admin-primary-800: var(--primary-800);
    --admin-primary-900: var(--primary-900);
  }
  ```
- In the dark mode block (line 129–177), add corresponding `--admin-*` overrides for dark:
  ```css
  [data-theme="dark"] {
    --admin-surface-base: var(--surface-base);
    --admin-surface-raised: var(--surface-raised);
    --admin-surface-border: var(--surface-border);
    --admin-text-primary: var(--text-primary);
    --admin-text-secondary: var(--text-secondary);
    /* ... mirror the existing dark overrides */
  }
  ```

### 1B. Theme Preset System
**File:** `fastapi_admin/static/css/presets.css` (new file)

Create a new file with 6 named presets. Each preset defines the full color/light palette (light mode). Dark mode is handled by `[data-theme="dark"]` within each preset scope or by the existing dark mode block.

**Exact content:**
```css
/* ═══════════════════════════════════════════════════════════════════════════
   Theme Presets — named visual identities
   Applied via data-preset attribute on <html>
   ═══════════════════════════════════════════════════════════════════════════ */

/* Default: Warm Editorial Brutalism (current design) */
[data-preset="editorial"] {
  --surface-base: #FAF8F5;
  --surface-raised: #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border: #E8E4DE;
  --surface-inset: #F3F0EB;
  --text-primary: #1C1917;
  --text-secondary: #78716C;
  --text-disabled: #A8A29E;
  --text-inverse: #FAF8F5;
  --primary-50: #ECFDF5;
  --primary-100: #D1FAE5;
  --primary-200: #A7F3D0;
  --primary-300: #6EE7B7;
  --primary-400: #34D399;
  --primary-500: #059669;
  --primary-600: #047857;
  --primary-700: #065F46;
  --primary-800: #064E3B;
  --primary-900: #022C22;
  --font-display: 'Instrument Serif', Georgia, 'Times New Roman', serif;
  --font-body: 'DM Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  --radius-sm: 3px;
  --radius-md: 5px;
  --radius-lg: 8px;
  --shadow-xs: 0 1px 2px rgba(28, 25, 23, 0.04);
  --shadow-sm: 0 1px 3px rgba(28, 25, 23, 0.06), 0 1px 2px rgba(28, 25, 23, 0.04);
  --shadow-md: 0 4px 12px rgba(28, 25, 23, 0.08), 0 2px 4px rgba(28, 25, 23, 0.04);
  --shadow-lg: 0 12px 32px rgba(28, 25, 23, 0.12), 0 4px 8px rgba(28, 25, 23, 0.06);
  --admin-grain-opacity: 0.025;
  --admin-accent-line-opacity: 0.4;
}

/* Clean Modern — crisp whites, indigo accent, rounded corners */
[data-preset="modern"] {
  --surface-base: #F8FAFC;
  --surface-raised: #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border: #E2E8F0;
  --surface-inset: #F1F5F9;
  --text-primary: #0F172A;
  --text-secondary: #64748B;
  --text-disabled: #94A3B8;
  --text-inverse: #FFFFFF;
  --primary-50: #EEF2FF;
  --primary-100: #E0E7FF;
  --primary-200: #C7D2FE;
  --primary-300: #A5B4FC;
  --primary-400: #818CF8;
  --primary-500: #6366F1;
  --primary-600: #4F46E5;
  --primary-700: #4338CA;
  --primary-800: #3730A3;
  --primary-900: #312E81;
  --font-display: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  --admin-grain-opacity: 0;
  --admin-accent-line-opacity: 0;
}

/* Midnight — deep dark with violet accent */
[data-preset="midnight"] {
  --surface-base: #0B0F19;
  --surface-raised: #151B2B;
  --surface-overlay: #1E2538;
  --surface-border: #2A3248;
  --surface-inset: #111726;
  --text-primary: #E2E8F0;
  --text-secondary: #94A3B8;
  --text-disabled: #475569;
  --text-inverse: #0B0F19;
  --primary-50: #1E1B4B;
  --primary-100: #2E1065;
  --primary-200: #3B0764;
  --primary-300: #581C87;
  --primary-400: #7C3AED;
  --primary-500: #818CF8;
  --primary-600: #A78BFA;
  --primary-700: #C4B5FD;
  --primary-800: #DDD6FE;
  --primary-900: #EDE9FE;
  --font-display: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 10px;
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5), 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.6), 0 4px 8px rgba(0, 0, 0, 0.3);
  --admin-grain-opacity: 0;
  --admin-accent-line-opacity: 0.2;
}

/* Paper — warm off-white, emerald accent (matches current default) */
[data-preset="paper"] {
  --surface-base: #FAF8F5;
  --surface-raised: #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border: #E8E4DE;
  --surface-inset: #F3F0EB;
  --text-primary: #1C1917;
  --text-secondary: #78716C;
  --text-disabled: #A8A29E;
  --text-inverse: #FAF8F5;
  --primary-50: #ECFDF5;
  --primary-100: #D1FAE5;
  --primary-200: #A7F3D0;
  --primary-300: #6EE7B7;
  --primary-400: #34D399;
  --primary-500: #059669;
  --primary-600: #047857;
  --primary-700: #065F46;
  --primary-800: #064E3B;
  --primary-900: #022C22;
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius-sm: 3px;
  --radius-md: 5px;
  --radius-lg: 8px;
  --admin-grain-opacity: 0.025;
  --admin-accent-line-opacity: 0.4;
}

/* Forest — deep green, organic feel */
[data-preset="forest"] {
  --surface-base: #F0FDF4;
  --surface-raised: #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border: #BBF7D0;
  --surface-inset: #DCFCE7;
  --text-primary: #14532D;
  --text-secondary: #166534;
  --text-disabled: #86EFAC;
  --text-inverse: #F0FDF4;
  --primary-50: #F0FDF4;
  --primary-100: #DCFCE7;
  --primary-200: #BBF7D0;
  --primary-300: #86EFAC;
  --primary-400: #4ADE80;
  --primary-500: #22C55E;
  --primary-600: #16A34A;
  --primary-700: #15803D;
  --primary-800: #166534;
  --primary-900: #14532D;
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 10px;
  --admin-grain-opacity: 0.03;
  --admin-accent-line-opacity: 0.3;
}

/* Minimal — extreme simplicity, neutral tones */
[data-preset="minimal"] {
  --surface-base: #FFFFFF;
  --surface-raised: #FFFFFF;
  --surface-overlay: #FFFFFF;
  --surface-border: #E5E5E5;
  --surface-inset: #F5F5F5;
  --text-primary: #171717;
  --text-secondary: #737373;
  --text-disabled: #A3A3A3;
  --text-inverse: #FFFFFF;
  --primary-50: #F5F5F5;
  --primary-100: #E5E5E5;
  --primary-200: #D4D4D4;
  --primary-300: #A3A3A3;
  --primary-400: #737373;
  --primary-500: #404040;
  --primary-600: #262626;
  --primary-700: #171717;
  --primary-800: #0A0A0A;
  --primary-900: #000000;
  --font-display: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
  --radius-sm: 0px;
  --radius-md: 0px;
  --radius-lg: 0px;
  --shadow-xs: none;
  --shadow-sm: none;
  --shadow-md: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-lg: 0 4px 8px rgba(0,0,0,0.08);
  --admin-grain-opacity: 0;
  --admin-accent-line-opacity: 0;
}

/* Dark mode overrides per preset */
[data-preset="editorial"][data-theme="dark"] {
  --surface-base: #141210;
  --surface-raised: #1C1A17;
  --surface-overlay: #242220;
  --surface-border: #33302D;
  --surface-inset: #1A1816;
  --text-primary: #F5F0EB;
  --text-secondary: #9C9590;
  --text-disabled: #5C5752;
  --text-inverse: #141210;
}

[data-preset="modern"][data-theme="dark"] {
  --surface-base: #0F172A;
  --surface-raised: #1E293B;
  --surface-overlay: #334155;
  --surface-border: #334155;
  --surface-inset: #1E293B;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-disabled: #475569;
  --text-inverse: #0F172A;
}

[data-preset="paper"][data-theme="dark"] {
  --surface-base: #141210;
  --surface-raised: #1C1A17;
  --surface-overlay: #242220;
  --surface-border: #33302D;
  --surface-inset: #1A1816;
  --text-primary: #F5F0EB;
  --text-secondary: #9C9590;
  --text-disabled: #5C5752;
  --text-inverse: #141210;
}

[data-preset="forest"][data-theme="dark"] {
  --surface-base: #052E16;
  --surface-raised: #14532D;
  --surface-overlay: #166534;
  --surface-border: #166534;
  --surface-inset: #0D3320;
  --text-primary: #F0FDF4;
  --text-secondary: #86EFAC;
  --text-disabled: #22C55E;
  --text-inverse: #052E16;
}

[data-preset="minimal"][data-theme="dark"] {
  --surface-base: #0A0A0A;
  --surface-raised: #171717;
  --surface-overlay: #262626;
  --surface-border: #262626;
  --surface-inset: #171717;
  --text-primary: #F5F5F5;
  --text-secondary: #A3A3A3;
  --text-disabled: #525252;
  --text-inverse: #0A0A0A;
}
```

### 1C. Admin CSS Refactor
**File:** `fastapi_admin/static/css/admin.css` (2118 lines)

The CSS already uses `var(--*)` tokens extensively. The refactor needs:

1. **Grain texture** (line 38–46): Make opacity configurable
   - Change `opacity: 0.025;` to `opacity: var(--admin-grain-opacity, 0.025);`
   - Add `display: none` when opacity is 0

2. **Topbar accent line** (line 107–116): Make opacity configurable
   - Change `opacity: 0.4;` to `opacity: var(--admin-accent-line-opacity, 0.4);`

3. **Add layout modifier classes** (after utilities section, ~line 1922):
   ```css
   /* Table style variants */
   .table--striped tbody tr:nth-child(even) { background: var(--surface-inset); }
   .table--bordered { border: 1px solid var(--surface-border); }
   .table--bordered td, .table--bordered th { border: 1px solid var(--surface-border); }
   .table--compact th, .table--compact td { padding: var(--space-2) var(--space-3); font-size: var(--text-xs); }
   .table--relaxed th, .table--relaxed td { padding: var(--space-4) var(--space-5); }

   /* Form layout variants */
   .form--one-column .fieldset__fields { grid-template-columns: 1fr; }
   .form--compact .field-wrapper { gap: 4px; }
   .form--relaxed .field-wrapper { gap: 12px; }

   /* Sidebar style variants */
   .sidebar--compact .nav-link { padding: var(--space-1) var(--space-3); font-size: var(--text-xs); }
   .sidebar--minimal .nav-link__label { display: none; }
   .sidebar--minimal .nav-link { justify-content: center; padding: var(--space-2); }

   /* Dashboard grid variants */
   .dashboard--2col .stat-cards { grid-template-columns: repeat(2, 1fr); }
   .dashboard--3col .stat-cards { grid-template-columns: repeat(3, 1fr); }
   .dashboard--4col .stat-cards { grid-template-columns: repeat(4, 1fr); }
   .stat-card--outlined { background: transparent; border: 2px solid var(--surface-border); }
   .stat-card--flat { box-shadow: none; border: none; background: var(--surface-inset); }
   .stat-card--small .stat-card__value { font-size: var(--text-xl); }
   .stat-card--large .stat-card__value { font-size: 3.5rem; }

   /* Topbar style variants */
   .topbar--minimal { border-bottom: none; }
   .topbar--minimal::after { display: none; }
   .topbar--transparent { background: transparent; border-bottom: none; }
   .topbar--transparent::after { display: none; }

   /* Content width variants */
   .content--narrow .admin-content__inner { max-width: 800px; }
   .content--wide .admin-content__inner { max-width: 1600px; }
   .content--full .admin-content__inner { max-width: none; }

   /* Sidebar position */
   .sidebar--right .admin-body { flex-direction: row-reverse; }
   .sidebar--right .admin-sidebar { border-right: none; border-left: 1px solid var(--surface-border); }
   ```

4. **Update responsive section** (line 2020–2106):
   - Add responsive overrides that reference `--admin-*` variables:
     ```css
     @media (max-width: 1024px) {
       .admin-sidebar {
         width: var(--admin-sidebar-width, var(--sidebar-width));
       }
     }
     @media (max-width: 768px) {
       .admin-content__inner {
         padding: var(--space-5) var(--space-4);
       }
     }
     @media (max-width: 480px) {
       .admin-content__inner {
         padding: var(--space-4) var(--space-3);
       }
     }
     ```

---

## Phase 2: Python Config API for UI Customization
**Goal:** Expose all CSS variables through Python configuration.

### 2A. ThemeConfig Class
**File:** `fastapi_admin/config/theme.py` (new file)

```python
"""Theme configuration — maps to CSS custom properties."""


PRESET_DEFAULTS: dict[str, dict[str, str]] = {
    "editorial": {
        "surface_base": "#FAF8F5",
        "surface_raised": "#FFFFFF",
        "text_primary": "#1C1917",
        "text_secondary": "#78716C",
        "border_color": "#E8E4DE",
        "primary_color": "#059669",
        "font_display": "'Instrument Serif', Georgia, serif",
        "font_body": "'DM Sans', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "3px",
        "radius_md": "5px",
        "radius_lg": "8px",
    },
    "modern": {
        "surface_base": "#F8FAFC",
        "surface_raised": "#FFFFFF",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "border_color": "#E2E8F0",
        "primary_color": "#6366F1",
        "font_display": "'Inter', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', ui-monospace, monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "6px",
        "radius_md": "8px",
        "radius_lg": "12px",
    },
    "midnight": {
        "surface_base": "#0B0F19",
        "surface_raised": "#151B2B",
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "border_color": "#2A3248",
        "primary_color": "#818CF8",
        "font_display": "'Inter', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', ui-monospace, monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "4px",
        "radius_md": "6px",
        "radius_lg": "10px",
    },
    "paper": {
        "surface_base": "#FAF8F5",
        "surface_raised": "#FFFFFF",
        "text_primary": "#1C1917",
        "text_secondary": "#78716C",
        "border_color": "#E8E4DE",
        "primary_color": "#059669",
        "font_display": "'Instrument Serif', Georgia, serif",
        "font_body": "'DM Sans', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "3px",
        "radius_md": "5px",
        "radius_lg": "8px",
    },
    "forest": {
        "surface_base": "#F0FDF4",
        "surface_raised": "#FFFFFF",
        "text_primary": "#14532D",
        "text_secondary": "#166534",
        "border_color": "#BBF7D0",
        "primary_color": "#22C55E",
        "font_display": "'Instrument Serif', Georgia, serif",
        "font_body": "'DM Sans', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "4px",
        "radius_md": "6px",
        "radius_lg": "10px",
    },
    "minimal": {
        "surface_base": "#FFFFFF",
        "surface_raised": "#FFFFFF",
        "text_primary": "#171717",
        "text_secondary": "#737373",
        "border_color": "#E5E5E5",
        "primary_color": "#404040",
        "font_display": "'Inter', system-ui, sans-serif",
        "font_body": "'Inter', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', ui-monospace, monospace",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        "radius_sm": "0px",
        "radius_md": "0px",
        "radius_lg": "0px",
    },
}


class ThemeConfig:
    """Complete theme configuration — maps to CSS custom properties.

    When preset is set, its defaults are used. Any explicit attribute
    override takes precedence over the preset defaults.
    """

    def __init__(
        self,
        preset: str = "editorial",
        *,
        primary_color: str | None = None,
        surface_base: str | None = None,
        surface_raised: str | None = None,
        text_primary: str | None = None,
        text_secondary: str | None = None,
        border_color: str | None = None,
        font_display: str | None = None,
        font_body: str | None = None,
        font_mono: str | None = None,
        font_import_url: str | None = None,
        radius_sm: str | None = None,
        radius_md: str | None = None,
        radius_lg: str | None = None,
        shadow_sm: str | None = None,
        shadow_md: str | None = None,
        shadow_lg: str | None = None,
        topbar_height: str = "56px",
        sidebar_width: str = "248px",
        sidebar_collapsed_width: str = "60px",
        content_max_width: str = "1360px",
        content_padding: str = "32px",
        duration_fast: str = "100ms",
        duration_base: str = "180ms",
        duration_slow: str = "280ms",
        easing: str = "cubic-bezier(0.16, 1, 0.3, 1)",
        show_grain_texture: bool = True,
        show_accent_line: bool = True,
        compact_mode: bool = False,
    ):
        defaults = PRESET_DEFAULTS.get(preset, PRESET_DEFAULTS["editorial"])
        self.preset = preset
        self.primary_color = primary_color or defaults["primary_color"]
        self.surface_base = surface_base or defaults["surface_base"]
        self.surface_raised = surface_raised or defaults["surface_raised"]
        self.text_primary = text_primary or defaults["text_primary"]
        self.text_secondary = text_secondary or defaults["text_secondary"]
        self.border_color = border_color or defaults["border_color"]
        self.font_display = font_display or defaults["font_display"]
        self.font_body = font_body or defaults["font_body"]
        self.font_mono = font_mono or defaults["font_mono"]
        self.font_import_url = font_import_url or defaults["font_import_url"]
        self.radius_sm = radius_sm or defaults["radius_sm"]
        self.radius_md = radius_md or defaults["radius_md"]
        self.radius_lg = radius_lg or defaults["radius_lg"]
        self.shadow_sm = shadow_sm
        self.shadow_md = shadow_md
        self.shadow_lg = shadow_lg
        self.topbar_height = topbar_height
        self.sidebar_width = sidebar_width
        self.sidebar_collapsed_width = sidebar_collapsed_width
        self.content_max_width = content_max_width
        self.content_padding = content_padding
        self.duration_fast = duration_fast
        self.duration_base = duration_base
        self.duration_slow = duration_slow
        self.easing = easing
        self.show_grain_texture = show_grain_texture
        self.show_accent_line = show_accent_line
        self.compact_mode = compact_mode

    def to_css_variables(self) -> str:
        """Generate CSS :root{} block from config."""
        lines = [
            f"  --primary-500: {self.primary_color};",
            f"  --surface-base: {self.surface_base};",
            f"  --surface-raised: {self.surface_raised};",
            f"  --text-primary: {self.text_primary};",
            f"  --text-secondary: {self.text_secondary};",
            f"  --surface-border: {self.border_color};",
            f"  --font-display: {self.font_display};",
            f"  --font-body: {self.font_body};",
            f"  --font-mono: {self.font_mono};",
            f"  --topbar-height: {self.topbar_height};",
            f"  --sidebar-width: {self.sidebar_width};",
            f"  --sidebar-collapsed: {self.sidebar_collapsed_width};",
            f"  --content-max-width: {self.content_max_width};",
            f"  --content-padding: {self.content_padding};",
            f"  --radius-sm: {self.radius_sm};",
            f"  --radius-md: {self.radius_md};",
            f"  --radius-lg: {self.radius_lg};",
            f"  --duration-fast: {self.duration_fast};",
            f"  --duration-base: {self.duration_base};",
            f"  --duration-slow: {self.duration_slow};",
            f"  --easing-out: {self.easing};",
            f"  --admin-grain-opacity: {'0.025' if self.show_grain_texture else '0'};",
            f"  --admin-accent-line-opacity: {'0.4' if self.show_accent_line else '0'};",
        ]
        if self.shadow_sm:
            lines.append(f"  --shadow-sm: {self.shadow_sm};")
        if self.shadow_md:
            lines.append(f"  --shadow-md: {self.shadow_md};")
        if self.shadow_lg:
            lines.append(f"  --shadow-lg: {self.shadow_lg};")
        body = "\n".join(lines)
        return f":root {{\n{body}\n}}"

    def to_context(self) -> dict:
        """Return dict suitable for template context."""
        return {
            "theme": self,
            "theme_preset": self.preset,
            "theme_css": self.to_css_variables(),
            "theme_font_import_url": self.font_import_url,
            "theme_show_grain": self.show_grain_texture,
            "theme_show_accent_line": self.show_accent_line,
        }
```

### 2B. Wire ThemeConfig into UIConfig
**File:** `fastapi_admin/config/ui.py` (currently 36 lines → ~80 lines)

Replace entire file:
```python
"""UI configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi_admin.config.theme import ThemeConfig


class UIConfig:
    """UI configuration — wraps ThemeConfig + component-level options."""

    def __init__(
        self,
        title: str = "FastAPI Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        primary_color: str = "#0ea5e9",
        primary_color_dark: str = "#0284c7",
        dark_mode_default: bool = False,
        per_page_default: int = 25,
        # Theme
        theme: ThemeConfig | None = None,
        # Component config
        sidebar_style: str = "default",       # default | compact | minimal
        sidebar_show_icons: bool = True,
        sidebar_show_badges: bool = True,
        sidebar_group_style: str = "label",    # label | divider | card
        sidebar_position: str = "left",        # left | right
        table_style: str = "default",          # default | striped | bordered | compact
        table_hover_effect: bool = True,
        table_row_height: str = "normal",      # compact | normal | relaxed
        form_layout: str = "two-column",       # one-column | two-column | auto
        form_label_position: str = "top",      # top | left | placeholder
        form_spacing: str = "normal",          # compact | normal | relaxed
        form_card_style: bool = True,
        dashboard_grid: str = "auto",          # auto | 2col | 3col | 4col
        dashboard_card_style: str = "default", # default | outlined | flat
        dashboard_stat_size: str = "normal",   # small | normal | large
        content_width: str = "default",        # narrow | default | wide | full
        topbar_style: str = "default",         # default | minimal | transparent
        sticky_header: bool = True,
        # Custom injection
        custom_css: str = "",
        custom_css_url: str = "",
        custom_js: str = "",
        custom_js_url: str = "",
        # Feature toggles
        show_history: bool = True,
        show_view_on_site: bool = True,
        show_back_button: bool = False,
        environment_label: str | None = None,
        environment_color: str = "info",       # info | danger | warning | success
        site_url: str = "/",
        site_symbol: str | None = None,
        login_background_url: str | None = None,
        # Mobile
        mobile_sidebar: str = "overlay",       # overlay | drawer | hidden
        mobile_topbar_height: str = "48px",
        mobile_content_padding: str = "16px",
    ):
        self.title = title
        self.logo_url = logo_url
        self.favicon_url = favicon_url
        self.primary_color = primary_color
        self.primary_color_dark = primary_color_dark
        self.dark_mode_default = dark_mode_default
        self.per_page_default = per_page_default
        self.theme = theme
        self.sidebar_style = sidebar_style
        self.sidebar_show_icons = sidebar_show_icons
        self.sidebar_show_badges = sidebar_show_badges
        self.sidebar_group_style = sidebar_group_style
        self.sidebar_position = sidebar_position
        self.table_style = table_style
        self.table_hover_effect = table_hover_effect
        self.table_row_height = table_row_height
        self.form_layout = form_layout
        self.form_label_position = form_label_position
        self.form_spacing = form_spacing
        self.form_card_style = form_card_style
        self.dashboard_grid = dashboard_grid
        self.dashboard_card_style = dashboard_card_style
        self.dashboard_stat_size = dashboard_stat_size
        self.content_width = content_width
        self.topbar_style = topbar_style
        self.sticky_header = sticky_header
        self.custom_css = custom_css
        self.custom_css_url = custom_css_url
        self.custom_js = custom_js
        self.custom_js_url = custom_js_url
        self.show_history = show_history
        self.show_view_on_site = show_view_on_site
        self.show_back_button = show_back_button
        self.environment_label = environment_label
        self.environment_color = environment_color
        self.site_url = site_url
        self.site_symbol = site_symbol
        self.login_background_url = login_background_url
        self.mobile_sidebar = mobile_sidebar
        self.mobile_topbar_height = mobile_topbar_height
        self.mobile_content_padding = mobile_content_padding

    def apply_to_template_context(self) -> dict:
        """Apply UI configuration to template context."""
        ctx = {
            "title": self.title,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "primary_color": self.primary_color,
            "primary_color_dark": self.primary_color_dark,
            "dark_mode_default": self.dark_mode_default,
            "per_page_default": self.per_page_default,
            # Component config
            "sidebar_style": self.sidebar_style,
            "sidebar_show_icons": self.sidebar_show_icons,
            "sidebar_show_badges": self.sidebar_show_badges,
            "sidebar_group_style": self.sidebar_group_style,
            "sidebar_position": self.sidebar_position,
            "table_style": self.table_style,
            "table_hover_effect": self.table_hover_effect,
            "table_row_height": self.table_row_height,
            "form_layout": self.form_layout,
            "form_label_position": self.form_label_position,
            "form_spacing": self.form_spacing,
            "form_card_style": self.form_card_style,
            "dashboard_grid": self.dashboard_grid,
            "dashboard_card_style": self.dashboard_card_style,
            "dashboard_stat_size": self.dashboard_stat_size,
            "content_width": self.content_width,
            "topbar_style": self.topbar_style,
            "sticky_header": self.sticky_header,
            # Feature toggles
            "show_history": self.show_history,
            "show_view_on_site": self.show_view_on_site,
            "show_back_button": self.show_back_button,
            "environment_label": self.environment_label,
            "environment_color": self.environment_color,
            "site_url": self.site_url,
            "site_symbol": self.site_symbol,
            "login_background_url": self.login_background_url,
            # Mobile
            "mobile_sidebar": self.mobile_sidebar,
            "mobile_topbar_height": self.mobile_topbar_height,
            "mobile_content_padding": self.mobile_content_padding,
        }
        if self.theme:
            ctx.update(self.theme.to_context())
        return ctx
```

### 2C. Export ThemeConfig
**File:** `fastapi_admin/config/__init__.py`

Add `ThemeConfig` to imports and `__all__`:
```python
from fastapi_admin.config.theme import ThemeConfig

__all__ = [
    "AuthConfig",
    "AuditConfig",
    "UIConfig",
    "BehaviorConfig",
    "StorageConfig",
    "NavConfig",
    "ThemeConfig",
]
```

### 2D. Wire into Admin Core
**File:** `fastapi_admin/admin/core.py`

1. In `__init__` (line 114–197), add `theme` kwarg:
   - After `from fastapi_admin.config import (...)` add `ThemeConfig`
   - In `__init__` signature, add `theme: ThemeConfig | None = None`
   - In the `config = AdminConfig(...)` block, pass `theme=theme` to `UIConfig`

2. In `_wire_app_state` (line 504–560), add theme to admin_config dict:
   ```python
   if self.config.ui.theme:
       admin_config.update(self.config.ui.theme.to_context())
   admin_config["ui_config"] = self.config.ui.apply_to_template_context()
   ```

3. In `_init_jinja` (line 585–605), inject theme CSS globals:
   ```python
   if self.config.ui.theme:
       self._jinja_env.env.globals["theme_css"] = self.config.ui.theme.to_css_variables()
       self._jinja_env.env.globals["theme_font_import_url"] = self.config.ui.theme.font_import_url
   self._jinja_env.env.globals["ui_config"] = self.config.ui.apply_to_template_context()
   ```

### 2E. Update base.html Template
**File:** `templates/base.html` (86 lines)

Replace the `<head>` section (lines 1–39) with:
```html
<!DOCTYPE html>
<html lang="en" data-theme="{{ 'dark' if admin_config.dark_mode_default else 'light' }}"
      data-preset="{{ theme_preset | default('editorial') }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{{ title | default("Admin") }}{% endblock %}</title>
  <meta name="csrf-token" content="{{ get_csrf_token(request) }}">

  {# Favicon #}
  {% if admin_config.favicon_url %}
  <link rel="icon" href="{{ admin_config.favicon_url }}">
  {% endif %}

  {# Google Fonts — dynamic from theme config #}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  {% if theme_font_import_url | default('') %}
  <link href="{{ theme_font_import_url }}" rel="stylesheet">
  {% else %}
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  {% endif %}

  {# Core CSS #}
  <link rel="stylesheet" href="/static/css/tokens.css">
  <link rel="stylesheet" href="/static/css/presets.css">
  <link rel="stylesheet" href="/static/css/admin.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/dark.css">

  {# Core JS #}
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>

  {# Theme CSS variables from Python config #}
  {% if theme_css | default('') %}
  <style>{{ theme_css }}</style>
  {% endif %}

  {# Legacy primary color override (backward compat) #}
  <style>
    :root {
      --primary-500: {{ admin_config.primary_color | default('#6366f1') }};
      --primary-600: {{ admin_config.primary_color_dark | default('#4f46e5') }};
    }
  </style>

  {# Custom CSS injection #}
  {% if ui_config.custom_css_url | default('') %}
  <link rel="stylesheet" href="{{ ui_config.custom_css_url }}">
  {% endif %}
  {% if ui_config.custom_css | default('') %}
  <style>{{ ui_config.custom_css }}</style>
  {% endif %}

  {% block head_extra %}{% endblock %}

  {% for css_url in extra_css | default([]) %}
  <link rel="stylesheet" href="{{ css_url }}">
  {% endfor %}
  {% for js_url in extra_js | default([]) %}
  <script src="{{ js_url }}"></script>
  {% endfor %}
</head>
```

Replace the `<body>` tag (line 40–65) with:
```html
<body x-data="{
        sidebarOpen: false,
        sidebarCollapsed: localStorage.getItem('sidebarCollapsed') === 'true',
        init() {
          if (window.innerWidth < 1024) { this.sidebarCollapsed = true; }
          window.addEventListener('resize', () => {
            if (window.innerWidth < 1024) { this.sidebarCollapsed = true; this.sidebarOpen = false; }
          });
          this.$watch('sidebarCollapsed', val => { localStorage.setItem('sidebarCollapsed', val); });
        },
        toggleMobileSidebar() { this.sidebarOpen = !this.sidebarOpen; }
      }"
      class="font-sans antialiased"
      style="color: var(--text-primary); background-color: var(--surface-base);">

  <div class="admin-shell">
    {% include "partials/topbar.html" %}

    <div class="admin-body">
      {% include "partials/sidebar.html" %}

      <div class="admin-content {% if ui_config.content_width | default('default') != 'default' %}content--{{ ui_config.content_width }}{% endif %}"
           id="admin-content">
        {% include "partials/flash_messages.html" %}

        <div class="admin-content__inner">
          {% block content %}{% endblock %}
        </div>
      </div>
    </div>
  </div>

  {# Custom JS injection #}
  {% if ui_config.custom_js_url | default('') %}
  <script src="{{ ui_config.custom_js_url }}"></script>
  {% endif %}
  {% if ui_config.custom_js | default('') %}
  <script>{{ ui_config.custom_js }}</script>
  {% endif %}

  <script src="/static/js/htmx-config.js"></script>
  <script src="/static/js/admin.js"></script>
</body>
```

---

## Phase 3: Dynamic Theme Switching (Runtime)
**Goal:** Allow admin users to switch themes at runtime.

### 3A. Theme Switcher in Topbar
**File:** `templates/partials/topbar.html` (96 lines)

Add theme dropdown after the dark mode toggle button (after line 61). Insert before the user avatar div (line 64):
```html
{# Theme switcher #}
<div class="relative" x-data="{ open: false }">
  <button @click="open = !open" @click.outside="open = false"
          class="icon-btn" title="Change theme">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <use href="/static/icons/heroicons.svg#swatch"/>
    </svg>
  </button>
  <div x-show="open" @click.outside="open = false"
       x-transition:enter="transition ease-out duration-100"
       x-transition:enter-start="opacity-0 scale-95"
       x-transition:enter-end="opacity-100 scale-100"
       class="absolute right-0 mt-2 w-48 bg-[var(--surface-raised)] border border-[var(--surface-border)] rounded-lg shadow-lg z-50 py-1"
       style="display: none;">
    {% set presets = ["editorial", "modern", "midnight", "paper", "forest", "minimal"] %}
    {% for p in presets %}
    <button @click="$store.themes.apply('{{ p }}'); open = false"
            class="w-full text-left px-4 py-2 text-sm hover:bg-[var(--surface-inset)] flex items-center gap-2
                   {% if theme_preset | default('editorial') == p %}text-[var(--primary-500)] font-medium{% else %}text-[var(--text-primary)]{% endif %}">
      <span class="w-3 h-3 rounded-full border border-[var(--surface-border)]"
            style="background: var(--primary-500);"></span>
      {{ p | title }}
    </button>
    {% endfor %}
  </div>
</div>
```

### 3B. Theme Store in admin.js
**File:** `fastapi_admin/static/js/admin.js` (397 lines)

Add new Alpine store after the `theme` store (after line 49):
```javascript
/* ── Themes store (preset switching) ─────────────────── */

Alpine.store('themes', {
  preset: localStorage.getItem('admin_theme_preset') || 'editorial',

  apply(name) {
    this.preset = name;
    document.documentElement.setAttribute('data-preset', name);
    localStorage.setItem('admin_theme_preset', name);
    // Dispatch event for other components to react
    window.dispatchEvent(new CustomEvent('theme-change', { detail: { preset: name } }));
  },

  init() {
    const saved = localStorage.getItem('admin_theme_preset');
    if (saved) {
      document.documentElement.setAttribute('data-preset', saved);
      this.preset = saved;
    }
  },
});
```

### 3C. Custom Theme Builder Route (Optional — Phase 3B)
**File:** New `fastapi_admin/views/settings.py`

Add settings routes for theme management:
```python
"""Admin settings routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi_admin.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/theme", response_class=HTMLResponse)
async def theme_settings(request: Request, current_user=Depends(get_current_admin_user)):
    """Render theme builder page."""
    templates = request.app.state.admin_jinja_env
    context = {
        "request": request,
        "title": "Theme Settings",
        "admin_config": request.app.state.admin_config,
    }
    # Add sidebar context
    admin_instance = request.app.state.admin
    if hasattr(admin_instance, "build_sidebar_context"):
        context.update(admin_instance.build_sidebar_context(request, user=current_user))
    template = templates.get_template("pages/settings/theme.html")
    html = template.render(**context)
    return HTMLResponse(content=html)
```

**File:** New `templates/pages/settings/theme.html`

Visual theme builder with color pickers, font selector, and preview panel. Uses Alpine.js for live preview. Saves to localStorage.

### 3D. Dark Mode Enhancement
**File:** `fastapi_admin/static/css/tokens.css`

The dark mode block (line 129–177) already works. Enhance it:
- Use `color-mix()` for auto-generated dark variants where possible
- Each preset's `[data-preset="X"][data-theme="dark"]` block overrides the base dark tokens

---

## Phase 4: Component-Level Customization
**Goal:** Make individual UI components configurable.

### 4A. Sidebar Config
**File:** `templates/partials/sidebar.html`

Add CSS class based on `ui_config.sidebar_style`:
```html
<aside class="admin-sidebar sidebar--{{ ui_config.sidebar_style | default('default') }}"
       :class="{ 'open': sidebarOpen, 'collapsed': sidebarCollapsed }"
       :style="sidebarCollapsed ? 'width: var(--sidebar-collapsed)' : 'width: var(--sidebar-width)'"
       x-show="true">
```

For icons/badges visibility, use `x-show` directives:
```html
{% if ui_config.sidebar_show_icons | default(true) %}
<svg ...>...</svg>
{% endif %}
```

### 4B. Table Config
**File:** `templates/pages/list.html`

Apply table style classes:
```html
<table class="w-full table--{{ ui_config.table_style | default('default') }}
              {% if ui_config.table_row_height | default('normal') == 'compact' %}table--compact{% endif %}
              {% if ui_config.table_row_height | default('normal') == 'relaxed' %}table--relaxed{% endif %}">
```

### 4C. Form Config
**File:** `templates/pages/form.html`

Apply form layout class:
```html
<form method="post" class="space-y-6 form--{{ ui_config.form_layout | default('two-column') }}
                           form--{{ ui_config.form_spacing | default('normal') }}">
```

### 4D. Dashboard Config
**File:** `templates/pages/dashboard.html`

Apply dashboard grid and card style:
```html
<div class="stat-cards dashboard--{{ ui_config.dashboard_grid | default('auto') }}">
  {% for card in stat_cards %}
  <a href="{{ card.url }}" class="stat-card stat-card--{{ ui_config.dashboard_card_style | default('default') }}
                                  stat-card--{{ ui_config.dashboard_stat_size | default('normal') }}">
```

### 4E. Topbar Config
**File:** `templates/partials/topbar.html`

Apply topbar style:
```html
<header class="admin-topbar topbar--{{ ui_config.topbar_style | default('default') }}">
```

---

## Phase 5: Advanced Customization Features
**Goal:** Power-user customization options.

### 5A. Per-Model UI Overrides
**File:** `fastapi_admin/modeladmin.py`

Add new attributes after line 44:
```python
# Per-model UI overrides
list_style: str | None = None       # Override table_style for this model
form_style: str | None = None       # Override form_layout for this model
card_color: str | None = None       # Accent color for model's stat cards
```

### 5B. Custom Logo Dark Mode
**File:** `templates/partials/topbar.html`

Update logo section to support dark mode logo:
```html
{% if admin_config.logo_url %}
<img src="{{ admin_config.logo_url }}" alt="Logo" style="height: 28px; max-width: 120px;"
     x-show="!$store.theme.dark">
{% if admin_config.logo_dark_url | default('') %}
<img src="{{ admin_config.logo_dark_url }}" alt="Logo" style="height: 28px; max-width: 120px;"
     x-show="$store.theme.dark" style="display: none;">
{% endif %}
{% else %}
<span>{{ admin_config.title | default("Admin") }}</span>
{% endif %}
```

### 5C. Environment Label
**File:** `templates/partials/topbar.html`

Add environment badge in topbar right zone:
```html
{% if ui_config.environment_label | default('') %}
<span class="badge badge-{{ ui_config.environment_color | default('info') }}">
  {{ ui_config.environment_label }}
</span>
{% endif %}
```

### 5D. Site Dropdown
**File:** `templates/partials/topbar.html`

Add site dropdown if configured (Unfold-style):
```html
{% if ui_config.site_dropdown | default([]) %}
<div class="relative" x-data="{ open: false }">
  <button @click="open = !open" class="icon-btn">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <use href="/static/icons/heroicons.svg#globe-alt"/>
    </svg>
  </button>
  <div x-show="open" ... class="dropdown-menu">
    {% for item in ui_config.site_dropdown %}
    <a href="{{ item.link }}" target="_blank" class="dropdown-item">
      {% if item.icon %}<span class="icon">{{ item.icon }}</span>{% endif %}
      {{ item.title }}
    </a>
    {% endfor %}
  </div>
</div>
{% endif %}
```

---

## Phase 6: Responsive & Mobile Customization
**Goal:** Ensure customization works across devices.

### 6A. Responsive CSS Updates
**File:** `fastapi_admin/static/css/admin.css`

Update responsive section (line 2020–2106) to use `--admin-*` variables:
```css
@media (max-width: 1024px) {
  .admin-sidebar {
    width: var(--admin-sidebar-width, var(--sidebar-width));
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform var(--admin-duration-slow, var(--duration-slow)) var(--admin-easing, var(--easing-out));
  }
  .admin-sidebar.open { transform: translateX(0); }
}

@media (max-width: 768px) {
  .admin-content__inner {
    padding: var(--space-5) var(--admin-mobile-content-padding, var(--space-4));
  }
}

@media (max-width: 480px) {
  .admin-content__inner {
    padding: var(--admin-mobile-content-padding, var(--space-3));
  }
}
```

### 6B. Mobile Config in Templates
**File:** `templates/base.html`

Add mobile-specific meta and viewport configuration using `ui_config.mobile_*` values.

---

## Verification

1. **Phase 1:** Load admin → inspect `<html>` has `data-preset="editorial"` → verify all CSS variables present via DevTools
2. **Phase 2:** Create `Admin(theme=ThemeConfig(preset="modern", primary_color="#6366F1"))` → verify indigo accent renders everywhere
3. **Phase 3:** Click theme switcher → verify preset changes instantly → reload → verify localStorage persistence
4. **Phase 4:** Set `table_style="striped"` → verify striped rows → `form_layout="one-column"` → verify single-column
5. **Phase 5:** Set `custom_css="body { background: red !important; }"` → verify red background
6. **Phase 6:** Resize browser to <768px → verify mobile sidebar overlay works

**Commands:**
```bash
cd /home/borhan/Desktop/test/fastapi-admin
python -m pytest tests/ -v
ruff check fastapi_admin/
```

---

## Files Summary

| File | Action | Lines Changed |
|------|--------|--------------|
| `fastapi_admin/static/css/tokens.css` | Edit | Add ~40 lines (--admin-* variables) |
| `fastapi_admin/static/css/presets.css` | New | ~300 lines |
| `fastapi_admin/static/css/admin.css` | Edit | Add ~80 lines (modifier classes) + edit ~5 lines (grain/accent opacity) |
| `fastapi_admin/config/theme.py` | New | ~200 lines |
| `fastapi_admin/config/ui.py` | Rewrite | ~180 lines (was 36) |
| `fastapi_admin/config/__init__.py` | Edit | Add 2 lines (ThemeConfig export) |
| `fastapi_admin/admin/core.py` | Edit | Add ~15 lines (theme wiring) |
| `templates/base.html` | Rewrite | ~90 lines (was 86) |
| `templates/partials/topbar.html` | Edit | Add ~40 lines (theme switcher, env label, site dropdown) |
| `templates/partials/sidebar.html` | Edit | Add ~5 lines (style class) |
| `templates/pages/list.html` | Edit | Add ~3 lines (table style class) |
| `templates/pages/form.html` | Edit | Add ~3 lines (form layout class) |
| `templates/pages/dashboard.html` | Edit | Add ~5 lines (dashboard grid/card classes) |
| `fastapi_admin/static/js/admin.js` | Edit | Add ~20 lines (themes store) |
| `fastapi_admin/modeladmin.py` | Edit | Add ~5 lines (per-model UI attrs) |
| `templates/pages/settings/theme.html` | New | ~150 lines |
| `fastapi_admin/views/settings.py` | New | ~30 lines |
