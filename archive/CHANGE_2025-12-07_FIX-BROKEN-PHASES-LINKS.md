# Workbench: Fix Broken Phases Navigation Links

**Date:** 2025-12-07
**Author:** Claude
**Status:** In Progress

---

## Purpose

Fix all broken navigation links related to tournament phases (7 broken links causing 404 errors). All templates incorrectly use `/phases/` prefix when the router uses `/tournaments/` prefix. Additionally, add test coverage for DashboardService and EventService which have 0% test coverage.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes needed (no entity changes)

**VALIDATION_RULES.md:**
- No changes needed (no validation rule changes)

### Level 2: Derived
**ROADMAP.md:**
- No changes needed (this is a bug fix, not a new feature)

### Level 3: Operational
**CHANGELOG.md:**
- [ ] Add bug fix entry for Phase 3.3 navigation fix

**ARCHITECTURE.md:**
- No changes needed

**FRONTEND.md:**
- No changes needed

---

## Template Changes Required

| # | File | Line | Current | Fixed |
|---|------|------|---------|-------|
| 1 | base.html | 183 | `/phases/{{ active_tournament.id }}/phase` | `/tournaments/{{ active_tournament.id }}/phase` |
| 2 | _registration_mode.html | 11 | `/phases/{{ dashboard.tournament.id }}/phase` | `/tournaments/{{ dashboard.tournament.id }}/phase` |
| 3 | _event_active.html | 13 | `/phases/{{ dashboard.tournament.id }}/phase` | `/tournaments/{{ dashboard.tournament.id }}/phase` |
| 4 | overview.html | 26 | `/phases/{{ active_tournament.id }}/phase` | `/tournaments/{{ active_tournament.id }}/phase` |
| 5 | overview.html | 43 | `/phases/{{ active_tournament.id }}/phase` | `/tournaments/{{ active_tournament.id }}/phase` |
| 6 | overview.html | 65 | `/phases/{{ active_tournament.id }}/phase` | `/tournaments/{{ active_tournament.id }}/phase` |
| 7 | phases/overview.html | 27-31 | Go Back form | REMOVE entirely |
| 8 | phases/overview.html | 33 | `/phases/advance` | `/tournaments/{{ tournament.id }}/advance` |

---

## Test Coverage To Add

### New Test Files
- tests/test_dashboard_service.py (7+ tests)
- tests/test_event_service.py (8+ tests)
- tests/test_phases_routes.py (6+ tests)

---

## Verification

**Grep checks performed:**
```bash
grep -r "/phases/" app/templates/
```

**Results:**
- ✅ No `/phases/` references remain in templates
- ✅ All links now use `/tournaments/` prefix
- ✅ Go Back form removed from phases/overview.html

---

## Files Modified

**Templates Fixed (6 files, 8 changes):**
- `app/templates/base.html:183` - Sidebar link fixed
- `app/templates/dashboard/_registration_mode.html:11` - Manage Phases button fixed
- `app/templates/dashboard/_event_active.html:13` - Phase Management button fixed
- `app/templates/overview.html:26,43,65` - 3 links fixed
- `app/templates/phases/overview.html:27-37` - Go Back removed, Advance form fixed

**Tests Created (3 files, 30 tests):**
- `tests/test_dashboard_service.py` - 16 tests for DashboardService
- `tests/test_event_service.py` - 9 tests for EventService
- `tests/test_phases_routes.py` - 5 tests for route verification

**Documentation Updated:**
- `CHANGELOG.md` - Bug fix entry added

---

## Test Results

**Before:** 209 passed, 8 skipped
**After:** 239 passed, 8 skipped (+30 new tests)

All tests passing. No regressions.
