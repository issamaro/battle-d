# Implementation Plan: Complete Frontend Rebuild

**Date:** 2025-12-23
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-23_FRONTEND-REBUILD.md

---

## 1. Summary

**Feature:** Complete frontend rebuild applying Figma design system to all ~50 templates

**Approach:**
- **Remove PicoCSS entirely** - Build custom SCSS design system from scratch
- **Use Dart Sass** - Already installed (`sass` v1.59.3 via Homebrew)
- **Phased implementation** - Start with design system foundation, then components, then template migration

**CSS Build Command:**
```bash
# Development (watch mode)
sass --watch app/static/scss:app/static/css

# Production (compressed)
sass app/static/scss:app/static/css --style=compressed
```

---

## 2. Affected Files

### 2.1 SCSS Architecture (New)

```
app/static/scss/
│
├── main.scss                      # Entry point - imports everything
│
├── abstracts/                     # No CSS output - tools only
│   ├── _index.scss                # Forward all abstracts
│   ├── _variables.scss            # Design tokens (colors, spacing, fonts)
│   ├── _mixins.scss               # Reusable mixins (responsive, flex, etc.)
│   └── _functions.scss            # SCSS functions (if needed)
│
├── base/                          # Foundation styles - element defaults
│   ├── _index.scss                # Forward all base
│   ├── _reset.scss                # CSS reset/normalize
│   ├── _typography.scss           # h1-h6, p, links, lists, code
│   └── _global.scss               # html, body, *, focus states
│
├── layout/                        # Page structure - the skeleton
│   ├── _index.scss                # Forward all layout
│   ├── _grid.scss                 # CSS Grid utilities (.grid, .grid-cols-*)
│   ├── _sidebar.scss              # Sidebar navigation
│   ├── _header.scss               # Header + profile
│   ├── _footer.scss               # Footer
│   └── _containers.scss           # .container, .container-fluid, .main
│
├── components/                    # Reusable UI pieces
│   ├── _index.scss                # Forward all components
│   ├── _buttons.scss              # .btn, .btn-primary, .btn-create, etc.
│   ├── _badges.scss               # .badge, .badge-active, .badge-pending
│   ├── _cards.scss                # .card, .card-header, .card-body
│   ├── _tabs.scss                 # .tabs, .tab, .tab-active
│   ├── _modals.scss               # .modal, .modal-header, .modal-body
│   ├── _tables.scss               # .table, .table-responsive
│   ├── _forms.scss                # .form-group, .form-input, .form-label
│   ├── _flash.scss                # .flash-messages, .flash-success
│   ├── _empty-state.scss          # .empty-state
│   ├── _loading.scss              # .loading-spinner
│   └── _dropdown.scss             # .dropdown, .dropdown-menu
│
├── pages/                         # Page-specific styles (if needed)
│   ├── _index.scss                # Forward all pages
│   ├── _event-mode.scss           # Event command center specific
│   └── _registration.scss         # Registration two-panel layout
│
└── utilities/                     # Helper classes
    ├── _index.scss                # Forward all utilities
    ├── _spacing.scss              # .mt-4, .mb-2, .p-4, etc.
    ├── _display.scss              # .hidden, .block, .flex
    ├── _text.scss                 # .text-muted, .text-center, .font-bold
    └── _accessibility.scss        # .sr-only, .focus-visible
```

**Folder Purposes:**

| Folder | Purpose | Outputs CSS? |
|--------|---------|--------------|
| `abstracts/` | Variables, mixins, functions - tools only | No |
| `base/` | Reset + element defaults (h1, p, a, etc.) | Yes |
| `layout/` | Page structure (sidebar, header, grid) | Yes |
| `components/` | Reusable UI (buttons, cards, modals) | Yes |
| `pages/` | Page-specific overrides (event mode) | Yes |
| `utilities/` | Helper classes (.sr-only, .mt-4) | Yes |

**Output:** Single compiled `app/static/css/main.css`

### 2.2 CSS Files to Delete (After Migration)

| File | Reason |
|------|--------|
| `app/static/css/error-handling.css` | Migrated to SCSS partials |
| `app/static/css/battles.css` | Migrated to SCSS partials |
| `app/static/css/registration.css` | Migrated to SCSS partials |
| `app/static/css/event.css` | Migrated to SCSS partials |

### 2.3 Base Templates

| File | Changes |
|------|---------|
| `app/templates/base.html` | Remove PicoCSS CDN, link main.css, add logo, restructure header, remove inline styles |
| `app/templates/event_base.html` | Remove PicoCSS CDN, link main.css |

### 2.4 New Components

| File | Purpose |
|------|---------|
| `app/templates/components/tabs.html` | Tab navigation with count badges |
| `app/templates/components/card.html` | Tournament/content card with header, body, actions |
| `app/templates/components/form_modal.html` | Generic form modal wrapper |
| `app/templates/components/create_button.html` | Orange outline "+ Create" button |
| `app/templates/components/dropdown_menu.html` | 3-dot action menu |
| `app/templates/components/profile_header.html` | Name + role badge header |

### 2.5 Existing Components (Updates)

| File | Changes |
|------|---------|
| `app/templates/components/empty_state.html` | Use SVG icon, update classes |
| `app/templates/components/delete_modal.html` | Update button classes |
| `app/templates/components/flash_messages.html` | Update classes |
| `app/templates/components/loading.html` | Update classes |
| `app/templates/components/field_error.html` | Update classes |

### 2.6 Template Migrations (Priority Order)

**Phase 1: High-Traffic Pages**
| File | Changes |
|------|---------|
| `app/templates/tournaments/list.html` | Convert table to cards, add tabs |
| `app/templates/dancers/list.html` | Remove inline styles, use new classes |
| `app/templates/dashboard/index.html` | Update to match new layout |

**Phase 2: Forms → Modals**
| File | Changes |
|------|---------|
| `app/templates/tournaments/create.html` | Convert to modal |
| `app/templates/dancers/create.html` | Convert to modal with two-column layout |
| `app/templates/dancers/edit.html` | Convert to modal |
| `app/templates/admin/create_user.html` | Convert to modal |
| `app/templates/admin/edit_user.html` | Convert to modal |
| `app/templates/tournaments/add_category.html` | Convert to modal |

**Phase 3: Remaining Pages**
| File | Changes |
|------|---------|
| `app/templates/tournaments/detail.html` | Update styling |
| `app/templates/dancers/profile.html` | Update styling |
| `app/templates/admin/users.html` | Update table styling |
| `app/templates/registration/register.html` | Update panel styling |
| `app/templates/battles/detail.html` | Remove inline styles |
| `app/templates/battles/encode_*.html` | Standardize forms |
| `app/templates/pools/overview.html` | Update styling |
| `app/templates/auth/login.html` | Simple styling update |
| `app/templates/errors/*.html` | Update styling |

**Phase 4: Event Mode Pages**
| File | Changes |
|------|---------|
| `app/templates/event/command_center.html` | Update classes |
| `app/templates/event/_*.html` | Update partials |

### 2.7 Static Assets (New)

| File | Purpose |
|------|---------|
| `app/static/images/logo.svg` | Battle-D logo placeholder |
| `app/static/images/icons/` | Icon set (inline SVG) |

### 2.8 Documentation Updates

| File | Changes |
|------|---------|
| `FRONTEND.md` | Update to document SCSS architecture, remove PicoCSS references |

---

## 3. Backend Implementation Plan

### 3.1 No Database Changes Required

This is a visual-only rebuild. No schema changes needed.

### 3.2 Route Changes (Minimal)

**File:** `app/routers/tournaments.py`

Add HTMX-compatible filtering endpoint for tabs:
```python
@router.get("/tournaments/filter")
async def filter_tournaments(
    request: Request,
    status: Optional[str] = Query(None, regex="^(upcoming|completed)$"),
    ...
):
    """Filter tournaments for HTMX tab switching."""
    if status == "upcoming":
        tournaments = await tournament_service.get_upcoming()
    else:
        tournaments = await tournament_service.get_completed()

    return templates.TemplateResponse(
        "tournaments/_list.html",
        {"request": request, "tournaments": tournaments}
    )
```

### 3.3 Service Layer Changes

**File:** `app/services/tournament_service.py`

```python
async def get_upcoming(self) -> List[Tournament]:
    """Get tournaments in REGISTRATION/PRESELECTION/POOLS/FINALS phases."""
    return await self.tournament_repo.get_by_phases([
        TournamentPhase.REGISTRATION,
        TournamentPhase.PRESELECTION,
        TournamentPhase.POOLS,
        TournamentPhase.FINALS
    ])

async def get_completed(self) -> List[Tournament]:
    """Get tournaments in COMPLETED phase."""
    return await self.tournament_repo.get_by_phase(TournamentPhase.COMPLETED)
```

### 3.4 Repository Changes

**File:** `app/repositories/tournament_repository.py`

```python
async def get_by_phases(self, phases: List[TournamentPhase]) -> List[Tournament]:
    """Get tournaments matching any of the given phases."""
    query = select(Tournament).where(Tournament.phase.in_(phases))
    result = await self.session.execute(query)
    return result.scalars().all()
```

---

## 4. SCSS Design System

### 4.1 Variables (`_variables.scss`)

```scss
// ==============================================
// DESIGN TOKENS - Battle-D Design System
// ==============================================

// Colors - Primary (Orange from Figma)
$color-primary: #F97316;
$color-primary-light: #FED7AA;
$color-primary-hover: #EA580C;
$color-primary-dark: #C2410C;

// Colors - Semantic
$color-success: #22C55E;
$color-success-light: #DCFCE7;
$color-success-dark: #16A34A;

$color-warning: #F59E0B;
$color-warning-light: #FEF3C7;
$color-warning-dark: #D97706;

$color-danger: #EF4444;
$color-danger-light: #FEE2E2;
$color-danger-dark: #DC2626;

$color-neutral: #6B7280;
$color-neutral-light: #F3F4F6;
$color-neutral-dark: #4B5563;

// Colors - Surface (Light Mode)
$color-background: #FFFFFF;
$color-surface: #FFFFFF;
$color-surface-raised: #FFFFFF;
$color-border: #E5E7EB;
$color-border-light: #F3F4F6;

// Colors - Text
$color-text: #111827;
$color-text-secondary: #4B5563;
$color-text-muted: #6B7280;
$color-text-inverse: #FFFFFF;

// Spacing Scale (4px base)
$space-1: 0.25rem;   // 4px
$space-2: 0.5rem;    // 8px
$space-3: 0.75rem;   // 12px
$space-4: 1rem;      // 16px
$space-5: 1.25rem;   // 20px
$space-6: 1.5rem;    // 24px
$space-8: 2rem;      // 32px
$space-10: 2.5rem;   // 40px
$space-12: 3rem;     // 48px
$space-16: 4rem;     // 64px

// Border Radius
$radius-sm: 0.25rem;   // 4px
$radius-md: 0.5rem;    // 8px
$radius-lg: 0.75rem;   // 12px
$radius-xl: 1rem;      // 16px
$radius-full: 9999px;

// Shadows
$shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
$shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
$shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);

// Typography
$font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
$font-family-mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;

$font-size-xs: 0.75rem;    // 12px
$font-size-sm: 0.875rem;   // 14px
$font-size-base: 1rem;     // 16px
$font-size-lg: 1.125rem;   // 18px
$font-size-xl: 1.25rem;    // 20px
$font-size-2xl: 1.5rem;    // 24px
$font-size-3xl: 1.875rem;  // 30px
$font-size-4xl: 2.25rem;   // 36px

$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;

$line-height-tight: 1.25;
$line-height-normal: 1.5;
$line-height-relaxed: 1.75;

// Breakpoints
$breakpoint-sm: 640px;
$breakpoint-md: 768px;
$breakpoint-lg: 1024px;
$breakpoint-xl: 1280px;

// Layout
$sidebar-width: 250px;
$sidebar-width-collapsed: 200px;
$header-height: 64px;
$max-content-width: 1200px;

// Transitions
$transition-fast: 150ms ease;
$transition-normal: 200ms ease;
$transition-slow: 300ms ease;

// Z-index scale
$z-dropdown: 100;
$z-sticky: 200;
$z-modal-backdrop: 300;
$z-modal: 400;
$z-toast: 500;
```

### 4.2 Reset (`_reset.scss`)

```scss
// ==============================================
// CSS RESET - Modern Normalize
// ==============================================

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  min-height: 100vh;
  font-family: $font-family;
  font-size: $font-size-base;
  line-height: $line-height-normal;
  color: $color-text;
  background-color: $color-background;
}

img,
picture,
video,
canvas,
svg {
  display: block;
  max-width: 100%;
}

input,
button,
textarea,
select {
  font: inherit;
  color: inherit;
}

button {
  cursor: pointer;
  background: none;
  border: none;
}

a {
  color: inherit;
  text-decoration: none;
}

ul,
ol {
  list-style: none;
}

table {
  border-collapse: collapse;
  border-spacing: 0;
}

// Remove default focus styles, we'll add our own
:focus {
  outline: none;
}

// Visible focus for keyboard navigation
:focus-visible {
  outline: 2px solid $color-primary;
  outline-offset: 2px;
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 4.3 Base Elements (`_base.scss`)

```scss
// ==============================================
// BASE ELEMENT STYLES
// ==============================================

// Headings
h1, h2, h3, h4, h5, h6 {
  font-weight: $font-weight-semibold;
  line-height: $line-height-tight;
  color: $color-text;
}

h1 { font-size: $font-size-3xl; }
h2 { font-size: $font-size-2xl; }
h3 { font-size: $font-size-xl; }
h4 { font-size: $font-size-lg; }
h5 { font-size: $font-size-base; }
h6 { font-size: $font-size-sm; }

// Paragraphs
p {
  margin-bottom: $space-4;

  &:last-child {
    margin-bottom: 0;
  }
}

// Links
a {
  color: $color-primary;
  transition: color $transition-fast;

  &:hover {
    color: $color-primary-hover;
  }
}

// Small text
small {
  font-size: $font-size-sm;
  color: $color-text-muted;
}

// Strong
strong {
  font-weight: $font-weight-semibold;
}

// Code
code {
  font-family: $font-family-mono;
  font-size: 0.875em;
  padding: $space-1 $space-2;
  background-color: $color-neutral-light;
  border-radius: $radius-sm;
}

pre {
  font-family: $font-family-mono;
  font-size: $font-size-sm;
  padding: $space-4;
  background-color: $color-neutral-light;
  border-radius: $radius-md;
  overflow-x: auto;
}

// Horizontal rule
hr {
  border: none;
  border-top: 1px solid $color-border;
  margin: $space-6 0;
}

// Abbreviation
abbr[title] {
  text-decoration: underline dotted;
  cursor: help;
}
```

### 4.4 Layout (`_layout.scss`)

```scss
// ==============================================
// LAYOUT - Grid, Sidebar, Header, Footer
// ==============================================

// Main app layout (authenticated)
.app-layout {
  display: grid;
  grid-template-columns: $sidebar-width 1fr;
  grid-template-rows: auto 1fr auto;
  grid-template-areas:
    "sidebar header"
    "sidebar main"
    "sidebar footer";
  min-height: 100vh;

  @media (max-width: $breakpoint-md) {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "sidebar"
      "main"
      "footer";
  }
}

// Simple layout (unauthenticated)
.simple-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;

  .main {
    flex: 1;
    padding: $space-8;
  }
}

// ==============================================
// SIDEBAR
// ==============================================

.sidebar {
  grid-area: sidebar;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  background: $color-surface;
  border-right: 1px solid $color-border;
  display: flex;
  flex-direction: column;

  @media (max-width: $breakpoint-md) {
    position: static;
    height: auto;
    border-right: none;
    border-bottom: 1px solid $color-border;
  }
}

.sidebar-logo {
  padding: $space-6;
  border-bottom: 1px solid $color-border;

  img, svg {
    height: 32px;
    width: auto;
  }

  // Text fallback if no logo image
  .logo-text {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $color-primary;
  }
}

.sidebar-nav {
  flex: 1;
  padding: $space-4;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: $space-3 $space-4;
  border-radius: $radius-md;
  color: $color-text;
  transition: background-color $transition-fast;

  &:hover {
    background-color: $color-neutral-light;
  }

  // Active state (orange)
  &[aria-current="page"],
  &.is-active {
    background-color: $color-primary;
    color: $color-text-inverse;

    &:hover {
      background-color: $color-primary-hover;
    }
  }

  .nav-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
}

.nav-divider {
  border: none;
  border-top: 1px solid $color-border;
  margin: $space-4 0;
}

.nav-section-label {
  padding: $space-2 $space-4;
  font-size: $font-size-xs;
  font-weight: $font-weight-medium;
  color: $color-text-muted;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// ==============================================
// HEADER
// ==============================================

.header {
  grid-area: header;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $space-4 $space-8;
  background: $color-surface;
  border-bottom: 1px solid $color-border;
  min-height: $header-height;
}

.header-title {
  font-size: $font-size-xl;
  font-weight: $font-weight-semibold;
  margin: 0;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: $space-1;
}

.profile-name {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: $color-text;
}

.profile-role {
  display: inline-block;
  padding: $space-1 $space-2;
  font-size: $font-size-xs;
  font-weight: $font-weight-medium;
  background-color: $color-neutral-light;
  color: $color-neutral-dark;
  border-radius: $radius-sm;
  text-transform: capitalize;
}

// ==============================================
// MAIN CONTENT
// ==============================================

.main {
  grid-area: main;
  padding: $space-8;
  background: $color-background;

  @media (max-width: $breakpoint-md) {
    padding: $space-4;
  }
}

.container {
  max-width: $max-content-width;
  margin: 0 auto;
}

.container-fluid {
  width: 100%;
}

// Page header with title and actions
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-6;
  gap: $space-4;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
    align-items: flex-start;
  }
}

.page-title {
  font-size: $font-size-2xl;
  font-weight: $font-weight-semibold;
  margin: 0;
}

.page-subtitle {
  font-size: $font-size-sm;
  color: $color-text-muted;
  margin-top: $space-1;
}

// ==============================================
// FOOTER
// ==============================================

.footer {
  grid-area: footer;
  padding: $space-4 $space-8;
  background: $color-surface;
  border-top: 1px solid $color-border;
  text-align: center;

  p {
    margin: 0;
    font-size: $font-size-sm;
    color: $color-text-muted;
  }
}

// ==============================================
// GRID UTILITIES
// ==============================================

.grid {
  display: grid;
  gap: $space-4;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, 1fr);

  @media (max-width: $breakpoint-sm) {
    grid-template-columns: 1fr;
  }
}

.grid-cols-3 {
  grid-template-columns: repeat(3, 1fr);

  @media (max-width: $breakpoint-md) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: $breakpoint-sm) {
    grid-template-columns: 1fr;
  }
}
```

### 4.5 Forms (`_forms.scss`)

```scss
// ==============================================
// FORM ELEMENTS
// ==============================================

.form {
  max-width: 600px;
}

.form-group {
  margin-bottom: $space-4;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $space-4;

  @media (max-width: $breakpoint-sm) {
    grid-template-columns: 1fr;
  }
}

// Labels
.form-label {
  display: block;
  margin-bottom: $space-2;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $color-text;

  .required {
    color: $color-danger;
    margin-left: $space-1;
  }
}

// Text inputs, textareas, selects
.form-input,
.form-textarea,
.form-select {
  display: block;
  width: 100%;
  padding: $space-3 $space-4;
  font-size: $font-size-base;
  line-height: $line-height-normal;
  color: $color-text;
  background-color: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius-md;
  transition: border-color $transition-fast, box-shadow $transition-fast;

  &::placeholder {
    color: $color-text-muted;
  }

  &:hover {
    border-color: $color-neutral;
  }

  &:focus {
    border-color: $color-primary;
    box-shadow: 0 0 0 3px rgba($color-primary, 0.1);
  }

  &:disabled {
    background-color: $color-neutral-light;
    cursor: not-allowed;
    opacity: 0.6;
  }

  // Invalid state
  &[aria-invalid="true"],
  &.is-invalid {
    border-color: $color-danger;

    &:focus {
      box-shadow: 0 0 0 3px rgba($color-danger, 0.1);
    }
  }
}

.form-textarea {
  min-height: 120px;
  resize: vertical;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'%3E%3Cpath fill='%236B7280' d='M4.427 6.427l3.396 3.396a.25.25 0 00.354 0l3.396-3.396A.25.25 0 0011.396 6H4.604a.25.25 0 00-.177.427z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right $space-3 center;
  padding-right: $space-10;
}

// Checkbox and radio
.form-check {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-2;
}

.form-check-input {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  accent-color: $color-primary;
}

.form-check-label {
  font-size: $font-size-base;
  color: $color-text;
  cursor: pointer;
}

// Help text
.form-help {
  display: block;
  margin-top: $space-1;
  font-size: $font-size-sm;
  color: $color-text-muted;
}

// Error message
.form-error {
  display: block;
  margin-top: $space-1;
  font-size: $font-size-sm;
  color: $color-danger;
}

// Fieldset
.fieldset {
  border: 1px solid $color-border;
  border-radius: $radius-md;
  padding: $space-4;

  legend {
    padding: 0 $space-2;
    font-weight: $font-weight-medium;
  }
}

// Form actions
.form-actions {
  display: flex;
  gap: $space-3;
  margin-top: $space-6;

  @media (max-width: $breakpoint-sm) {
    flex-direction: column;
  }
}
```

### 4.6 Buttons (`_buttons.scss`)

```scss
// ==============================================
// BUTTONS
// ==============================================

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  padding: $space-2 $space-4;
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  line-height: $line-height-normal;
  text-align: center;
  text-decoration: none;
  border-radius: $radius-md;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all $transition-fast;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  // Icon inside button
  svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
  }
}

// Primary button (orange filled)
.btn-primary {
  background-color: $color-primary;
  border-color: $color-primary;
  color: $color-text-inverse;

  &:hover:not(:disabled) {
    background-color: $color-primary-hover;
    border-color: $color-primary-hover;
  }

  &:active:not(:disabled) {
    background-color: $color-primary-dark;
    border-color: $color-primary-dark;
  }
}

// Secondary button (gray outline)
.btn-secondary {
  background-color: transparent;
  border-color: $color-border;
  color: $color-text;

  &:hover:not(:disabled) {
    background-color: $color-neutral-light;
    border-color: $color-neutral;
  }
}

// Create button (orange outline) - Primary action for lists
.btn-create {
  background-color: transparent;
  border-color: $color-primary;
  color: $color-primary;

  &:hover:not(:disabled) {
    background-color: $color-primary-light;
  }
}

// Danger button (red filled)
.btn-danger {
  background-color: $color-danger;
  border-color: $color-danger;
  color: $color-text-inverse;

  &:hover:not(:disabled) {
    background-color: $color-danger-dark;
    border-color: $color-danger-dark;
  }
}

// Ghost button (no background)
.btn-ghost {
  background-color: transparent;
  border-color: transparent;
  color: $color-text;

  &:hover:not(:disabled) {
    background-color: $color-neutral-light;
  }
}

// Link button (looks like a link)
.btn-link {
  background-color: transparent;
  border-color: transparent;
  color: $color-primary;
  padding: 0;

  &:hover:not(:disabled) {
    color: $color-primary-hover;
    text-decoration: underline;
  }
}

// Size variants
.btn-sm {
  padding: $space-1 $space-3;
  font-size: $font-size-sm;
}

.btn-lg {
  padding: $space-3 $space-6;
  font-size: $font-size-lg;
}

// Full width
.btn-block {
  width: 100%;
}

// Button group
.btn-group {
  display: flex;
  gap: $space-2;
}
```

### 4.7 Badges (`_badges.scss`)

```scss
// ==============================================
// STATUS BADGES
// ==============================================

.badge {
  display: inline-flex;
  align-items: center;
  padding: $space-1 $space-2;
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  border-radius: $radius-sm;
  white-space: nowrap;
}

// Tournament/Battle status badges
.badge-pending {
  background-color: $color-neutral;
  color: $color-text-inverse;
}

.badge-active {
  background-color: $color-primary;
  color: $color-text-inverse;
}

.badge-completed {
  background-color: $color-success;
  color: $color-text-inverse;
}

.badge-cancelled {
  background-color: $color-warning;
  color: $color-text; // Dark text for better contrast on yellow
}

// Phase badges
.badge-registration {
  background-color: $color-neutral-light;
  color: $color-neutral-dark;
}

.badge-preselection {
  background-color: $color-primary-light;
  color: $color-primary-dark;
}

.badge-pools {
  background-color: $color-primary;
  color: $color-text-inverse;
}

.badge-finals {
  background-color: $color-success-light;
  color: $color-success-dark;
}

// Role badge
.badge-role {
  background-color: $color-neutral-light;
  color: $color-neutral-dark;
  text-transform: capitalize;
}

// Count badge (for tabs)
.badge-count {
  padding: $space-1 $space-2;
  font-size: $font-size-xs;
  background-color: $color-neutral-light;
  color: $color-neutral-dark;
  border-radius: $radius-full;
}
```

### 4.8 Cards (`_cards.scss`)

```scss
// ==============================================
// CARD COMPONENT
// ==============================================

.card {
  background: $color-surface;
  border: 1px solid $color-border;
  border-radius: $radius-lg;
  overflow: hidden;
  transition: box-shadow $transition-fast;

  &:hover {
    box-shadow: $shadow-md;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: $space-4;
  border-bottom: 1px solid $color-border;
  gap: $space-4;
}

.card-header-content {
  flex: 1;
  min-width: 0; // Allow text truncation
}

.card-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: $color-text;
  margin: 0;
}

.card-subtitle {
  font-size: $font-size-sm;
  color: $color-text-muted;
  margin: $space-1 0 0;
}

.card-header-actions {
  display: flex;
  align-items: center;
  gap: $space-2;
  flex-shrink: 0;
}

.card-body {
  padding: $space-4;
}

.card-footer {
  display: flex;
  gap: $space-3;
  padding: $space-4;
  border-top: 1px solid $color-border;
  background: $color-neutral-light;
}

// Card grid layout
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: $space-4;

  @media (max-width: $breakpoint-sm) {
    grid-template-columns: 1fr;
  }
}

// Card metadata (date, location, etc.)
.card-meta {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: $font-size-sm;
  color: $color-text-muted;

  svg {
    width: 16px;
    height: 16px;
  }
}
```

### 4.9 Tabs (`_tabs.scss`)

```scss
// ==============================================
// TAB NAVIGATION
// ==============================================

.tabs {
  display: flex;
  gap: $space-6;
  border-bottom: 1px solid $color-border;
  margin-bottom: $space-6;
  overflow-x: auto;

  // Hide scrollbar but allow scrolling
  scrollbar-width: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

.tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: $space-2;
  padding: $space-3 0;
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: $color-text-muted;
  background: none;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  transition: color $transition-fast;

  &:hover {
    color: $color-text;
  }

  // Active tab
  &[aria-selected="true"],
  &.is-active {
    color: $color-text;

    &::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      right: 0;
      height: 2px;
      background-color: $color-primary;
    }

    .badge-count {
      background-color: $color-primary-light;
      color: $color-primary-dark;
    }
  }
}
```

### 4.10 Modals (`_modals.scss`)

```scss
// ==============================================
// MODAL DIALOGS
// ==============================================

.modal {
  position: fixed;
  inset: 0;
  z-index: $z-modal;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $space-4;

  // Native dialog element
  &[open] {
    animation: modal-fade-in $transition-normal;
  }

  // Backdrop
  &::backdrop {
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
  }
}

@keyframes modal-fade-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-content {
  background: $color-surface;
  border-radius: $radius-lg;
  box-shadow: $shadow-xl;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  @media (max-width: $breakpoint-sm) {
    max-width: 95vw;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $space-4 $space-6;
  border-bottom: 1px solid $color-border;
}

.modal-title {
  font-size: $font-size-xl;
  font-weight: $font-weight-semibold;
  margin: 0;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  color: $color-text-muted;
  border-radius: $radius-sm;
  transition: background-color $transition-fast, color $transition-fast;

  &:hover {
    background-color: $color-neutral-light;
    color: $color-text;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-body {
  padding: $space-6;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: $space-3;
  padding: $space-4 $space-6;
  border-top: 1px solid $color-border;
  background-color: $color-neutral-light;
}

// Delete confirmation modal
.modal-danger {
  .modal-header {
    background-color: $color-danger-light;
    border-bottom-color: $color-danger;
  }

  .modal-title {
    color: $color-danger-dark;
  }
}

.modal-warning {
  padding: $space-3;
  background-color: $color-danger-light;
  border-left: 4px solid $color-danger;
  border-radius: $radius-sm;
  margin-bottom: $space-4;

  strong {
    color: $color-danger-dark;
  }
}
```

### 4.11 Tables (`_tables.scss`)

```scss
// ==============================================
// TABLES
// ==============================================

.table-wrapper {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: $font-size-sm;
}

.table th,
.table td {
  padding: $space-3 $space-4;
  text-align: left;
  border-bottom: 1px solid $color-border;
}

.table th {
  font-weight: $font-weight-semibold;
  color: $color-text-muted;
  background-color: $color-neutral-light;
  text-transform: uppercase;
  font-size: $font-size-xs;
  letter-spacing: 0.05em;
}

.table tbody tr {
  transition: background-color $transition-fast;

  &:hover {
    background-color: $color-neutral-light;
  }
}

// Responsive table (stacks on mobile)
@media (max-width: $breakpoint-md) {
  .table-responsive {
    thead {
      display: none;
    }

    tbody tr {
      display: block;
      padding: $space-4;
      border-bottom: 1px solid $color-border;

      &:hover {
        background-color: transparent;
      }
    }

    td {
      display: flex;
      justify-content: space-between;
      padding: $space-2 0;
      border-bottom: none;

      &::before {
        content: attr(data-label);
        font-weight: $font-weight-semibold;
        color: $color-text-muted;
      }
    }
  }
}
```

### 4.12 Main Entry Point (`main.scss`)

```scss
// ==============================================
// BATTLE-D DESIGN SYSTEM - Main Entry Point
// ==============================================
// Import order matters! Abstracts first, utilities last.

// 1. Abstracts (no CSS output - tools only)
@use 'abstracts' as *;

// 2. Base (reset + element defaults)
@use 'base';

// 3. Layout (page structure)
@use 'layout';

// 4. Components (reusable UI)
@use 'components';

// 5. Pages (page-specific styles)
@use 'pages';

// 6. Utilities (helper classes - last to override)
@use 'utilities';
```

**Each folder has an `_index.scss` that forwards its contents:**

```scss
// abstracts/_index.scss
@forward 'variables';
@forward 'mixins';
@forward 'functions';

// components/_index.scss
@forward 'buttons';
@forward 'badges';
@forward 'cards';
@forward 'tabs';
@forward 'modals';
@forward 'tables';
@forward 'forms';
@forward 'flash';
@forward 'empty-state';
@forward 'loading';
@forward 'dropdown';
```

---

## 5. Documentation Update Plan

### FRONTEND.md Updates

1. **Remove PicoCSS references** - Document pure SCSS approach
2. **Add SCSS architecture section** - File structure, compilation
3. **Update design tokens** - Reference `_variables.scss`
4. **Update component library** - Document new components

---

## 6. Testing Plan

### Manual Testing Checklist

**SCSS Compilation:**
- [ ] `sass --watch` runs without errors
- [ ] Output CSS is valid
- [ ] No SCSS syntax errors

**Design System:**
- [ ] All colors render correctly in light mode
- [ ] All colors render correctly in dark mode
- [ ] Spacing is consistent
- [ ] Typography scale is correct

**Components:**
- [ ] Sidebar renders correctly
- [ ] Cards render correctly
- [ ] Tabs work with HTMX
- [ ] Modals open/close correctly
- [ ] Forms validate correctly

**Accessibility:**
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works

**Responsive:**
- [ ] Mobile layout (320px) works
- [ ] Tablet layout (768px) works
- [ ] Desktop layout (1024px+) works

---

## 7. Risk Analysis

### Risk 1: Full CSS Rewrite May Introduce Regressions

**Concern:** Removing PicoCSS completely means rewriting all styles
**Likelihood:** High
**Impact:** Medium
**Mitigation:**
- Phased migration (don't remove PicoCSS until new system is complete)
- Visual QA after each phase
- Keep PicoCSS as fallback initially

### Risk 2: SCSS Compilation Step Required

**Concern:** Developers must run `sass --watch` during development
**Likelihood:** Low (already using `brew install sass`)
**Impact:** Low
**Mitigation:**
- Document build process in README
- Consider adding to dev startup script

### Risk 3: Dark Mode Not Fully Tested

**Concern:** Custom dark mode may have contrast issues
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Test each component in both modes
- Use SCSS variables consistently
- Add dark mode section later if needed

---

## 8. Implementation Order

### Phase 1: SCSS Foundation (1-2 days)

1. **Create SCSS directory structure**
   ```bash
   mkdir -p app/static/scss/{abstracts,base,layout,components,pages,utilities}
   ```

2. **Create abstracts/ (no CSS output):**
   - `abstracts/_index.scss`
   - `abstracts/_variables.scss` - Design tokens
   - `abstracts/_mixins.scss` - Responsive breakpoints, etc.
   - `abstracts/_functions.scss` - (placeholder)

3. **Create base/ (element defaults):**
   - `base/_index.scss`
   - `base/_reset.scss` - CSS reset
   - `base/_typography.scss` - Headings, paragraphs, links
   - `base/_global.scss` - html, body, focus states

4. **Create main.scss** - Entry point with @use imports

5. **Start SCSS watch:**
   ```bash
   sass --watch app/static/scss:app/static/css
   ```

6. **Update base.html:**
   - Keep PicoCSS CDN temporarily (fallback)
   - Add link to `main.css`
   - Verify both load without conflicts

### Phase 2: Layout (1 day)

7. **Create layout/ (page structure):**
   - `layout/_index.scss`
   - `layout/_grid.scss` - Grid utilities
   - `layout/_sidebar.scss` - Sidebar navigation
   - `layout/_header.scss` - Header + profile
   - `layout/_footer.scss` - Footer
   - `layout/_containers.scss` - .container, .main

### Phase 3: Components (2-3 days)

8. **Create components/ (reusable UI):**
   - `components/_index.scss`
   - `components/_buttons.scss`
   - `components/_badges.scss`
   - `components/_cards.scss`
   - `components/_tabs.scss`
   - `components/_modals.scss`
   - `components/_tables.scss`
   - `components/_forms.scss`
   - `components/_flash.scss` (migrate from error-handling.css)
   - `components/_empty-state.scss` (migrate from error-handling.css)
   - `components/_loading.scss` (migrate from error-handling.css)
   - `components/_dropdown.scss`

### Phase 4: Utilities + Pages (1 day)

9. **Create utilities/ (helper classes):**
   - `utilities/_index.scss`
   - `utilities/_spacing.scss` - .mt-4, .mb-2, etc.
   - `utilities/_display.scss` - .hidden, .flex
   - `utilities/_text.scss` - .text-muted, .text-center
   - `utilities/_accessibility.scss` - .sr-only

10. **Create pages/ (page-specific):**
    - `pages/_index.scss`
    - `pages/_event-mode.scss`
    - `pages/_registration.scss`

### Phase 5: Jinja Components (1-2 days)

11. **Create Jinja template components:**
    - `tabs.html`
    - `card.html`
    - `form_modal.html`
    - `create_button.html`
    - `profile_header.html`

12. **Update existing Jinja components:**
    - `empty_state.html` - Use new classes
    - `delete_modal.html` - Use new classes
    - `flash_messages.html` - Use new classes

### Phase 6: Template Migration (3-5 days)

13. **Update base templates:**
    - `base.html` - Full restructure with new layout classes
    - `event_base.html` - Update classes

14. **Migrate high-priority templates:**
    - `tournaments/list.html` - Cards + tabs
    - `dancers/list.html` - New classes
    - `dashboard/index.html` - Profile header

15. **Convert forms to modals:**
    - `tournaments/create.html`
    - `dancers/create.html`
    - `dancers/edit.html`
    - `admin/create_user.html`
    - `admin/edit_user.html`

16. **Migrate remaining templates**

### Phase 7: Cleanup (1 day)

17. **Remove PicoCSS:**
    - Remove CDN link from base.html
    - Remove any PicoCSS-specific classes from templates

18. **Delete old CSS files:**
    - `error-handling.css`
    - `battles.css`
    - `registration.css`
    - `event.css`

19. **Update FRONTEND.md** - Document new SCSS architecture

---

## 9. Open Questions

- [x] Mobile navigation: Deferred to future phase
- [x] CSS approach: Dart Sass without npm
- [x] Dark mode: Deferred to future phase (light mode only initially)

---

## 10. User Approval Checklist

- [ ] User reviewed SCSS architecture
- [ ] User approved removing PicoCSS
- [ ] User confirmed Dart Sass approach
- [ ] User approved phased implementation
- [ ] User ready to start Phase 1
