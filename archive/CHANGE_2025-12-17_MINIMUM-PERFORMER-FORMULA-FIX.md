# Workbench: Minimum Performer Formula Fix

**Date:** 2025-12-17
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix inconsistent minimum performer formula across UI and services. The canonical formula `(groups_ideal × 2) + 1` is correct in the source of truth (`tournament_calculations.py`) but 4 locations use wrong values.

---

## Documentation Changes

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- [x] No changes needed - formula already correctly documented

**VALIDATION_RULES.md:**
- [x] No changes needed - formula already correctly documented as `(groups_ideal × 2) + 1`

### Level 2: Derived

**ROADMAP.md:**
- [ ] Not needed - bug fix, not new feature

### Level 3: Operational

**ARCHITECTURE.md:**
- [ ] Not needed - no new patterns

**FRONTEND.md:**
- [ ] Not needed - no new components

---

## Verification

**Grep checks performed:**
```bash
grep -rn "groups_ideal.*\*.*2" app/
grep -rn "minimum.*required" app/templates/
```

**Results:**
- Verified formula is correct in `tournament_calculations.py`
- Found 4 bugs to fix (detail.html, add_category.html x2, dashboard_service.py)

---

## Files Modified

**Code:**
- `app/services/dashboard_service.py`:
  - Line 11: Added import for `calculate_minimum_performers`
  - Line 22: Updated comment from "performers_ideal" to formula reference
  - Line 158: Changed `category.performers_ideal` to `calculate_minimum_performers(category.groups_ideal)`
- `app/models/category.py`:
  - Line 7: Added import for `calculate_minimum_performers`
  - Lines 104-117: Added `minimum_performers_required` property
- `app/templates/tournaments/detail.html`:
  - Line 76: Changed to use `item.category.minimum_performers_required` property
- `app/templates/tournaments/add_category.html`:
  - Line 62: Changed hardcoded `6` to `5`
  - Line 66: Changed `+ 2 elimination` to `+ 1 elimination`

**Tests:**
- `tests/test_dashboard_service.py`:
  - Line 263: Changed expected minimum from 4 to 5
  - Line 291: Updated comment
  - Lines 307-318: Changed to 6 performers (clearly exceeds minimum of 5)
- `tests/e2e/test_minimum_formula_consistency.py`: New E2E test (3 test cases)

---

## Test Results

- 517 tests passed
- 1 pre-existing failure (test_ux_consistency style audit - unrelated)
- 9 skipped

Key tests verified:
- `tests/test_dashboard_service.py`: 15 passed
- `tests/test_tournament_calculations.py`: 36 passed
- `tests/e2e/test_minimum_formula_consistency.py`: 3 passed

---

## Notes

- No database migration needed (computed property only)
- All changes are simple value fixes
- Source of truth (`tournament_calculations.py`) was already correct
- Added `minimum_performers_required` property to Category model for DRY principle
