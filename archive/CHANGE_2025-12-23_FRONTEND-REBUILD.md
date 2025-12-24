# Workbench: Complete Frontend Rebuild

**Date:** 2025-12-23
**Author:** Claude
**Status:** In Progress (Phase 7 Complete, Template Migration Complete)

---

## Purpose

Complete frontend rebuild applying Figma design system to all templates. Remove PicoCSS entirely and build custom SCSS design system from scratch using Dart Sass.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes required (visual-only rebuild)

**VALIDATION_RULES.md:**
- No changes required (visual-only rebuild)

### Level 2: Derived
**ROADMAP.md:**
- No changes required (this is part of existing UI work)

### Level 3: Operational
**FRONTEND.md:**
- [x] Replace PicoCSS documentation with SCSS architecture
- [x] Update component library section with new classes
- [x] Add SCSS build commands
- [x] Document design tokens (v2.0 update)

---

## Verification

**SCSS Compilation:**
- [x] `sass app/static/scss/main.scss app/static/css/main.css` compiles without errors
- [x] Output: 2891 lines of CSS (up from 2646 with registration styles)

**Grep checks:**
```bash
grep -r "PicoCSS" app/templates/base.html  # No results (removed)
grep -r "main.css" app/templates/base.html  # Found (new system)
```

**Old CSS files deleted:**
- [x] `app/static/css/error-handling.css` - Deleted
- [x] `app/static/css/battles.css` - Deleted
- [x] `app/static/css/registration.css` - Deleted
- [x] `app/static/css/event.css` - Deleted

---

## Files Modified

### SCSS Architecture (NEW)

**Abstracts (no CSS output):**
- `app/static/scss/abstracts/_index.scss`
- `app/static/scss/abstracts/_variables.scss` - Design tokens
- `app/static/scss/abstracts/_mixins.scss` - Reusable mixins
- `app/static/scss/abstracts/_functions.scss` - Placeholder

**Base (element defaults):**
- `app/static/scss/base/_index.scss`
- `app/static/scss/base/_reset.scss` - CSS reset
- `app/static/scss/base/_typography.scss` - h1-h6, p, links
- `app/static/scss/base/_global.scss` - Scrollbar, selection

**Layout (page structure):**
- `app/static/scss/layout/_index.scss`
- `app/static/scss/layout/_grid.scss` - Grid utilities
- `app/static/scss/layout/_sidebar.scss` - Sidebar navigation
- `app/static/scss/layout/_header.scss` - Header + profile
- `app/static/scss/layout/_footer.scss` - Footer
- `app/static/scss/layout/_containers.scss` - .container, .main

**Components (reusable UI):**
- `app/static/scss/components/_index.scss`
- `app/static/scss/components/_buttons.scss` - .btn variants
- `app/static/scss/components/_badges.scss` - Status badges
- `app/static/scss/components/_cards.scss` - Card component
- `app/static/scss/components/_tabs.scss` - Tab navigation
- `app/static/scss/components/_modals.scss` - Modal dialogs
- `app/static/scss/components/_tables.scss` - Tables
- `app/static/scss/components/_forms.scss` - Form elements
- `app/static/scss/components/_flash.scss` - Flash messages
- `app/static/scss/components/_empty-state.scss` - Empty states
- `app/static/scss/components/_loading.scss` - Loading indicators
- `app/static/scss/components/_dropdown.scss` - Dropdown menus

**Pages (page-specific):**
- `app/static/scss/pages/_index.scss`
- `app/static/scss/pages/_event-mode.scss` - Event command center
- `app/static/scss/pages/_registration.scss` - Two-panel layout (updated with full registration styles)

**Utilities (helper classes):**
- `app/static/scss/utilities/_index.scss`
- `app/static/scss/utilities/_spacing.scss` - .mt-4, .mb-2, etc.
- `app/static/scss/utilities/_display.scss` - .hidden, .flex
- `app/static/scss/utilities/_text.scss` - .text-muted, etc.
- `app/static/scss/utilities/_accessibility.scss` - .sr-only

**Entry point:**
- `app/static/scss/main.scss` - Imports all modules

**Output:**
- `app/static/css/main.css` - Compiled CSS (2891 lines)

### Templates Updated (Phase 7)

**Base Templates:**
- `app/templates/base.html` - Updated to use new CSS classes, removed PicoCSS
- `app/templates/event_base.html` - Updated to use new CSS classes

**Components:**
- `app/templates/components/flash_messages.html` - Updated classes
- `app/templates/components/delete_modal.html` - Updated classes

**List Pages (High-Traffic):**
- `app/templates/tournaments/list.html` - New page-header, table classes, badge classes
- `app/templates/dancers/list.html` - New page-header, card for search, new classes
- `app/templates/dancers/_table.html` - New table-wrapper, btn-group classes
- `app/templates/dashboard/index.html` - New page-header, card, badge-role classes
- `app/templates/admin/users.html` - New page-header, card, table classes

**Auth:**
- `app/templates/auth/login.html` - New centered login card design with main.css

**Form Templates (Inline Styles Removed):**
- `app/templates/tournaments/create.html` - New form classes, card layout
- `app/templates/dancers/create.html` - New form classes, form-row for two-column layout
- `app/templates/dancers/edit.html` - New form classes, form-row for two-column layout
- `app/templates/admin/create_user.html` - New form classes
- `app/templates/admin/edit_user.html` - New form classes, card for actions

**Registration:**
- `app/templates/registration/register.html` - Removed old CSS reference (styles now in SCSS)

### Documentation Updated

- `FRONTEND.md` - Updated to v2.0 with SCSS architecture

---

## Next Steps

1. **Visual QA:** Test all pages in browser
   - Check layout on desktop and mobile
   - Verify all buttons, forms, tables render correctly
   - Test HTMX interactions still work

2. **Remaining Templates (if needed):**
   - Check tournament detail page
   - Check dancer profile page
   - Check error pages
   - Check event mode pages

---

## Notes

- PicoCSS CDN removed from base.html
- All inline styles removed from form templates
- Using Dart Sass for compilation (`sass --watch app/static/scss:app/static/css`)
- Orange (#F97316) is now the primary brand color
- Old CSS files deleted: error-handling.css, battles.css, registration.css, event.css
