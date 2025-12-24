# Workbench: Navigation Streamlining

**Date:** 2025-12-23
**Author:** Claude
**Status:** Complete

---

## Purpose

Remove redundant Dashboard page and streamline navigation to reduce clicks to Event Mode. The Dashboard page has been replaced by the Tournaments list as the primary landing page.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes needed (no entity changes)

**VALIDATION_RULES.md:**
- No changes needed (no validation rule changes)

### Level 2: Derived
**ROADMAP.md:**
- No changes needed (not a new roadmap phase, this is UX polish)

### Level 3: Operational
**FRONTEND.md:**
- Updated sidebar navigation example (removed /overview, /phases)
- Updated "Multi-Column Layouts" reference (Dashboard → Tournaments list)
- Updated event_base.html exit link (/overview → /tournaments)
- Replaced Pattern 9 "Context-Aware Smart Dashboard" with "Event Mode Navigation"

---

## Verification

**Grep checks performed:**
```bash
grep -rn "/overview" app/  # Verified only route definition remains
grep -rn "Dashboard" tests/  # Updated all test references
```

**Results:**
- All /overview references in templates/routers updated to /tournaments
- All Dashboard references in tests updated appropriately
- No orphaned references remain

---

## Files Modified

**Backend Routes:**
- `app/routers/dashboard.py`: Simplified to redirect-only (removed template rendering)
- `app/routers/auth.py`: Updated post-login redirects (lines 112, 171)
- `app/routers/admin.py`: Updated fix-active tournaments redirect
- `app/routers/event.py`: Updated redirect for non-event phases
- `app/main.py`: Updated /dashboard redirect comment and target

**Frontend Templates:**
- `app/templates/base.html`: Complete sidebar navigation rewrite
  - Removed "Dashboard" nav item
  - Tournaments is now first item
  - Removed "Tournament Name" section with "Tournament Details" link
  - Added prominent "Event Mode" button with lightning bolt icon
- `app/templates/tournaments/list.html`: Added Event Mode button to active tournament cards
- `app/templates/event_base.html`: Updated exit link (/overview → /tournaments)
- `app/templates/battles/detail.html`: Updated back link
- `app/templates/battles/encode_preselection.html`: Updated breadcrumb
- `app/templates/pools/overview.html`: Updated back links
- `app/templates/errors/401.html`: Updated "Go to Overview" → "Go to Tournaments"
- `app/templates/errors/403.html`: Updated "Go to Overview" → "Go to Tournaments"
- `app/templates/errors/404.html`: Updated "Go to Overview" → "Go to Tournaments"
- `app/templates/errors/500.html`: Updated "Go to Overview" → "Go to Tournaments"

**SCSS Styles:**
- `app/static/scss/layout/_sidebar.scss`: Added `.nav-item-event-mode` style
- `app/static/scss/components/_cards.scss`: Added `.tournament-card-actions` style
- `app/static/css/main.css`: Recompiled

**Tests Updated:**
- `tests/test_auth.py`: Updated redirect assertions (/overview → /tournaments)
- `tests/test_permissions.py`: Updated to expect 302 redirects, not 200
- `tests/e2e/test_ux_consistency.py`: Updated dashboard tests
- `tests/e2e/test_htmx_interactions.py`: Updated /overview test
- `tests/e2e/test_admin.py`: Updated redirect assertion

**Documentation:**
- `FRONTEND.md`: Updated navigation examples and patterns

**Files Deleted:**
- `app/templates/dashboard/index.html`
- `app/templates/dashboard/_no_tournament.html`
- `app/templates/dashboard/_registration_mode.html`
- `app/templates/dashboard/_event_active.html`
- `app/templates/dashboard/` directory

---

## Test Results

**Full test suite:** 536 passed, 9 skipped

Key tests validated:
- `/overview` redirects to `/tournaments` (302)
- Post-login redirects to `/tournaments` (303)
- Sidebar navigation shows Tournaments first
- Event Mode button appears in sidebar for MC/Admin
- Event Mode button appears on active tournament cards

---

## Notes

- Using 302 redirect (temporary) for easy rollback
- DashboardService kept for potential future use (no changes to service layer)
- No database changes required
- All existing functionality preserved through redirects
