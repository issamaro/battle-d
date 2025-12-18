# Workbench: Screen Consolidation

**Date:** 2024-12-18
**Author:** Claude
**Status:** ✅ Complete

---

## Purpose

Remove redundant/broken screens (Battles list, Phases overview) and consolidate phase management into Event Mode. This eliminates the "Frankenstein app" effect where multiple paths existed to the same functionality.

**Feature Spec:** FEATURE_SPEC_2024-12-18_SCREEN-CONSOLIDATION.md
**Implementation Plan:** IMPLEMENTATION_PLAN_2024-12-18_SCREEN-CONSOLIDATION.md

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes required (no entity changes)

**VALIDATION_RULES.md:**
- No changes required (phase validation rules unchanged, just moved)

### Level 2: Derived
**ROADMAP.md:**
- [x] Added Phase 3.11: Screen Consolidation entry

### Level 3: Operational
**ARCHITECTURE.md:**
- No changes required (patterns unchanged)

**FRONTEND.md:**
- No changes required (components unchanged)

---

## Verification

**Grep checks performed:**
```bash
grep -r "/battles" app/templates/  # Check for broken links
grep -r "/tournaments/.*/phase" app/templates/  # Check for old phase links
grep -r "phases" app/routers/  # Verify phases router removed
```

**Results:**
- ✅ No broken links to /battles in templates
- ✅ No broken links to /tournaments/{id}/phase in templates
- ✅ Phases router removed from app/main.py
- ✅ Event Mode advance route functional

---

## Files Modified

### Deleted
- `app/routers/phases.py` - Entire router removed
- `app/templates/phases/` - Directory removed (overview.html, confirm_advance.html, validation_errors.html)
- `app/templates/battles/list.html` - Battles list template removed

### Code Modified
**app/routers/event.py:**
- Added `POST /event/{id}/advance` route
- Added imports: `Form`, `require_admin`, `get_tournament_service`, `ValidationError`, `add_flash_message`
- Two-step advance process: validate → confirm → execute

**app/routers/battles.py:**
- Removed `list_battles` route (lines 33-87)
- Added documentation comment explaining removal

**app/main.py:**
- Removed `phases` from router imports
- Removed `app.include_router(phases.router)` line

**app/templates/base.html:**
- Updated sidebar navigation (lines 179-186)
- Removed Battles and Phases links
- Added Event Mode link under active tournament section

**Dashboard templates updated:**
- `app/templates/dashboard/index.html` - Removed broken links
- `app/templates/dashboard/admin_controls.html` - Updated navigation
- `app/templates/dashboard/category_tab.html` - Updated links
- `app/templates/dashboard/tournament_section.html` - Updated links

### Templates Added
- `app/templates/event/_confirm_advance.html` - HTMX partial for confirmation dialog
- `app/templates/event/_validation_errors.html` - HTMX partial for validation errors

### Tests Modified
**tests/e2e/test_event_mode.py:**
- Updated `TestBattleListAccess` to expect 404 for removed route

**tests/e2e/test_htmx_interactions.py:**
- Updated `test_battles_list_full_page` → `test_battles_list_route_removed` (expects 404)

**tests/e2e/test_tournament_management.py:**
- Updated `TestPhaseOverview` tests to expect 404
- Updated `TestPhaseAdvancement` tests to expect 404

**tests/test_phases_routes.py:**
- Completely rewritten to test that removed routes return 404
- Added tests for new `/event/{id}/advance` route

### Tests Added
**tests/e2e/test_event_mode_advance.py:** (NEW - 9 tests)
- `TestEventModeAdvanceAccess` (3 tests)
  - `test_advance_requires_authentication`
  - `test_advance_requires_admin_role`
  - `test_advance_nonexistent_tournament_returns_404`
- `TestEventModeAdvanceValidation` (2 tests)
  - `test_advance_shows_validation_errors`
  - `test_advance_validation_returns_partial_html`
- `TestEventModeAdvanceExecution` (1 test)
  - `test_advance_with_confirmation_redirects`
- `TestRemovedPhasesRoutes` (2 tests)
  - `test_old_phases_route_returns_404`
  - `test_old_advance_route_returns_404`
- `TestRemovedBattlesListRoute` (1 test)
  - `test_battles_list_route_returns_404`

---

## Business Rules Validated

| Rule | Description | Test Coverage |
|------|-------------|---------------|
| BR-NAV-001 | Single path to functions | `test_battles_list_route_returns_404`, `test_old_phases_route_returns_404` |
| BR-UX-001 | No dead ends in navigation | Template updates, sidebar navigation tests |
| BR-WF-001 | Event Mode is primary workflow | `test_event_advance_requires_auth`, advance route tests |

---

## Test Results

**Full Suite:** 526 passed, 1 failed (pre-existing), 0 skipped
**New Tests:** 15 tests added, all passing
**Coverage:** 41% (E2E test scope)

See: `workbench/TEST_RESULTS_2024-12-18_SCREEN-CONSOLIDATION.md`

---

## Notes

- The single pre-existing failure (`test_no_inline_styles_in_templates`) is unrelated to this feature
- Phase advancement now uses two-step confirmation via HTMX partials
- All navigation paths now funnel through Event Mode for phase management
- Battle detail/encoding routes preserved (only list route removed)
