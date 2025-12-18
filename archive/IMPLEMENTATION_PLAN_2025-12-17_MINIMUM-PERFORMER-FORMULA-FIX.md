# Implementation Plan: Minimum Performer Formula Consistency Fix

**Date:** 2025-12-17
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-17_MINIMUM-PERFORMER-FORMULA-INCONSISTENCY.md

---

## 1. Summary

**Feature:** Fix inconsistent minimum performer formula across UI and services
**Approach:** Update 4 locations to use correct formula `(groups_ideal × 2) + 1`, add model property to centralize calculation, update affected tests

---

## 2. Affected Files

### Backend

**Models:**
- `app/models/category.py`: Add `minimum_performers_required` property to centralize formula

**Services:**
- `app/services/dashboard_service.py`:
  - Line 21: Update comment
  - Line 157: Use `calculate_minimum_performers()` instead of `performers_ideal`

**Utils:**
- `app/utils/tournament_calculations.py`: No changes (source of truth - already correct)

### Frontend

**Templates:**
- `app/templates/tournaments/detail.html`:
  - Line 76: Change `+ 2` to `+ 1`

- `app/templates/tournaments/add_category.html`:
  - Line 62: Change hardcoded `6` to `5`
  - Line 66: Change `+ 2 elimination` to `+ 1 elimination`

### Tests

**Updated Test Files:**
- `tests/test_dashboard_service.py`:
  - Line 263: Change expected `minimum_required` from 4 to 5
  - Line 291: Update test assertion comment
  - Line 307-318: Update test for correct minimum (5 not 4)

**New Test File:**
- `tests/e2e/test_minimum_formula_consistency.py`: E2E test verifying same minimum shown across all screens

### Documentation

**No documentation updates needed** - VALIDATION_RULES.md and DOMAIN_MODEL.md already have the correct formula documented.

---

## 3. Technical POC

**Status:** Not required
**Reason:** Simple bug fix with direct value changes - no new patterns or integrations

---

## 4. Backend Implementation Plan

### 4.1 Category Model Enhancement

**File:** `app/models/category.py`
**Change:** Add computed property for minimum performers

```python
from app.utils.tournament_calculations import calculate_minimum_performers

@property
def minimum_performers_required(self) -> int:
    """Calculate minimum performers based on business rules.

    Formula: (groups_ideal * 2) + 1

    This ensures:
    - At least 2 performers per pool
    - At least 1 performer eliminated in preselection

    Returns:
        Minimum number of registered performers required
    """
    return calculate_minimum_performers(self.groups_ideal)
```

**Benefits:**
- Centralizes formula in model (DRY)
- Templates can use `item.category.minimum_performers_required`
- Consistent with existing `ideal_pool_capacity` property pattern

### 4.2 Dashboard Service Fix

**File:** `app/services/dashboard_service.py`

**Change 1:** Update import (line 1-10 area)
```python
from app.utils.tournament_calculations import calculate_minimum_performers
```

**Change 2:** Update comment (line 21)
```python
# Before:
minimum_required: int  # performers_ideal (one full group minimum)

# After:
minimum_required: int  # (groups_ideal × 2) + 1 per BR-MIN-001
```

**Change 3:** Fix calculation (line 157)
```python
# Before:
minimum_required = category.performers_ideal  # One full group

# After:
minimum_required = calculate_minimum_performers(category.groups_ideal)
```

---

## 5. Frontend Implementation Plan

### 5.1 Tournament Detail Template Fix

**File:** `app/templates/tournaments/detail.html`

**Change:** Line 76
```jinja2
{# Before: #}
{% set minimum_required = (item.category.groups_ideal * 2) + 2 %}

{# After - Option A (inline fix): #}
{% set minimum_required = (item.category.groups_ideal * 2) + 1 %}

{# After - Option B (use model property - preferred): #}
{% set minimum_required = item.category.minimum_performers_required %}
```

**Recommendation:** Use Option B if model property is added, otherwise Option A.

### 5.2 Add Category Template Fix

**File:** `app/templates/tournaments/add_category.html`

**Change 1:** Line 62 - Initial display value
```html
<!-- Before: -->
<span id="min-display" style="font-size: 20px; color: #856404;">6</span>

<!-- After: -->
<span id="min-display" style="font-size: 20px; color: #856404;">5</span>
```

**Change 2:** Line 66 - Formula description
```html
<!-- Before: -->
<span id="formula-display">(2 pools × 2 minimum) + 2 elimination</span>

<!-- After: -->
<span id="formula-display">(2 pools × 2 minimum) + 1 elimination</span>
```

**Note:** The JavaScript on line 101 is already correct (`(groupsIdeal * 2) + 1`).

---

## 6. Testing Plan

### 6.1 Unit Test Updates

**File:** `tests/test_dashboard_service.py`

**Test 1:** `test_category_stats_calculation` (line 236-263)
```python
# Before (line 263):
assert cat_stats.minimum_required == 4  # performers_ideal

# After:
assert cat_stats.minimum_required == 5  # (groups_ideal * 2) + 1
```

**Test 2:** `test_category_is_ready_flag` (line 265-291)
```python
# Before: Test creates category with 3 performers, expects not ready (3 < 4)
# After: Still not ready (3 < 5), but update comment
```

**Test 3:** `test_category_is_ready_when_meets_minimum` (line 293-318)
```python
# Before: 5 performers meets minimum of 4 (WRONG logic)
# After: 5 performers meets minimum of 5 (CORRECT)
# OR: Change to 6 performers to clearly exceed minimum
```

### 6.2 New E2E Consistency Test

**File:** `tests/e2e/test_minimum_formula_consistency.py`

```python
"""
E2E tests for minimum performer formula consistency across screens.

Verifies BR-MIN-001: Minimum performers = (groups_ideal × 2) + 1
"""
import pytest
from playwright.sync_api import Page, expect

class TestMinimumFormulaConsistency:
    """
    Feature: Consistent minimum performer display
      As an admin
      I want to see the same minimum performer count across all screens
      So that I can accurately plan my tournament registration
    """

    @pytest.fixture
    def setup_tournament_with_category(self, page: Page, login_as_admin):
        """Create tournament and category for testing."""
        # Create tournament
        page.goto("/tournaments/create")
        page.fill("#name", "Formula Test Tournament")
        page.click("button[type='submit']")

        # Navigate to add category
        page.click("text=Add Category")
        yield page

    def test_add_category_shows_correct_minimum(
        self, setup_tournament_with_category
    ):
        """
        Scenario: Add Category shows correct minimum
          Given I am creating a new category
          When I set Number of Pools to 2
          Then I should see "Minimum Required Performers: 5"
        """
        page = setup_tournament_with_category

        # Default is 2 pools
        min_display = page.locator("#min-display")
        expect(min_display).to_have_text("5")

        # Formula should show +1
        formula = page.locator("#formula-display")
        expect(formula).to_contain_text("+ 1 elimination")

    def test_tournament_detail_shows_correct_minimum(
        self, page: Page, login_as_admin, create_tournament_with_category
    ):
        """
        Scenario: Tournament Detail shows correct minimum
          Given I have a category with groups_ideal=2
          When I view the tournament detail page
          Then the "Minimum Required" column should show "5"
        """
        tournament_id = create_tournament_with_category
        page.goto(f"/tournaments/{tournament_id}")

        # Find minimum required column value
        min_cell = page.locator("table tbody tr td:nth-child(4)")
        expect(min_cell).to_have_text("5")

    def test_dashboard_shows_correct_ready_status(
        self, page: Page, login_as_admin,
        create_tournament_with_category_and_performers
    ):
        """
        Scenario: Dashboard shows correct ready status
          Given I have a category with groups_ideal=2 and 4 performers
          When I view the dashboard
          Then the category should NOT be marked as "Ready"
        """
        page.goto("/dashboard")

        # With 4 performers and minimum 5, should NOT be ready
        ready_badge = page.locator("mark:has-text('Ready')")
        expect(ready_badge).not_to_be_visible()

        # Should show "Need 1 more"
        need_more = page.locator("small:has-text('Need 1 more')")
        expect(need_more).to_be_visible()
```

### 6.3 Manual Testing Checklist

- [ ] Create new category with 2 pools - verify shows "5" minimum
- [ ] View tournament detail - verify "Minimum Required" column shows "5"
- [ ] Register 4 performers - verify NOT shown as "Ready"
- [ ] Register 5th performer - verify shown as "Ready"
- [ ] Try phase transition with 4 performers - verify correctly blocked
- [ ] Try phase transition with 5 performers - verify succeeds

---

## 7. Risk Analysis

### Risk 1: Test Failures After Fix
**Concern:** Existing tests use wrong expected values (4 instead of 5)
**Likelihood:** High (tests written with bug)
**Impact:** Low (tests fail, not production)
**Mitigation:** Update tests as part of this fix

### Risk 2: Dashboard Ready Status Changes
**Concern:** Categories previously shown as "Ready" will now show "Need X more"
**Likelihood:** High (expected behavior change)
**Impact:** Low (correct behavior, may surprise users)
**Mitigation:** None needed - this is the intended fix

### Risk 3: Model Import Cycle
**Concern:** Adding import in Category model could cause circular import
**Likelihood:** Low (tournament_calculations has no model imports)
**Impact:** Medium (app won't start)
**Mitigation:** Test import after adding property

---

## 8. Implementation Order

**Recommended sequence (10-15 minutes total):**

1. **Dashboard Service** (Core fix)
   - Add import for `calculate_minimum_performers`
   - Update comment on line 21
   - Fix calculation on line 157
   - Run: `pytest tests/test_dashboard_service.py -v`

2. **Dashboard Tests** (Fix expected values)
   - Update expected `minimum_required` from 4 to 5
   - Update test comments
   - Run: `pytest tests/test_dashboard_service.py -v`

3. **Category Model** (Enhancement)
   - Add `minimum_performers_required` property
   - Run: Quick import test

4. **Tournament Detail Template** (UI fix)
   - Change `+ 2` to `+ 1` (or use model property)
   - Manual verify in browser

5. **Add Category Template** (UI fix)
   - Change initial "6" to "5"
   - Change formula text "+ 2" to "+ 1"
   - Manual verify in browser

6. **E2E Test** (Regression prevention)
   - Create consistency test
   - Run: `pytest tests/e2e/test_minimum_formula_consistency.py -v`

---

## 9. Rollback Plan

If issues arise:

1. **Revert commits** - All changes are simple text edits
2. **No database changes** - No migration needed
3. **No API changes** - No external dependencies

---

## 10. Definition of Done

- [ ] Dashboard service uses `calculate_minimum_performers()`
- [ ] Tournament detail shows `(groups_ideal * 2) + 1`
- [ ] Add category initial values show "5" and "+ 1"
- [ ] All unit tests pass with correct expected values
- [ ] E2E consistency test passes
- [ ] Manual testing checklist completed

---

## 11. Open Questions

All resolved:
- [x] Should we add model property? → Yes, centralizes formula
- [x] Should templates use model property or inline fix? → Model property preferred
- [x] Database migration needed? → No, computed property only

---

## 12. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed implementation order acceptable
