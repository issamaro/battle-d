# Feature Specification: Minimum Performer Formula Inconsistency

**Date:** 2025-12-17
**Status:** Awaiting Technical Design
**Type:** Bug Fix / Data Consistency

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

The minimum performer formula is implemented inconsistently across the codebase. The canonical formula `(groups_ideal × 2) + 1` is correctly implemented in the core utility (`tournament_calculations.py`) and phase validators, but several UI templates and services hardcode different formulas or use outdated `+2` instead of `+1`, causing users to see conflicting values (5 at creation, 6 after creation).

---

## 2. Executive Summary

### Scope
Analysis of all locations where minimum performer calculation is displayed or computed, to ensure system-wide consistency with the canonical business rule.

### What Works ✅
| Feature | Status | Location |
|---------|--------|----------|
| Core calculation function | Production Ready | `app/utils/tournament_calculations.py:41` |
| Adjusted minimum (with guests) | Production Ready | `app/utils/tournament_calculations.py:81` |
| Phase transition validation | Production Ready | `app/validators/phase_validators.py:80` |
| Registration router HTMX updates | Production Ready | `app/routers/registration.py:560,647,719,828,927` |
| Category schema computed property | Production Ready | `app/schemas/category.py:52` |
| Add category JS calculation | Production Ready | `app/templates/tournaments/add_category.html:101` |

### What's Broken 🚨
| Issue | Type | Location | Current Value | Expected Value |
|-------|------|----------|---------------|----------------|
| Tournament detail template | BUG | `app/templates/tournaments/detail.html:76` | `(groups_ideal * 2) + 2` | `+ 1` |
| Add category initial HTML | BUG | `app/templates/tournaments/add_category.html:62` | Hardcoded `6` | Hardcoded `5` |
| Add category formula text | BUG | `app/templates/tournaments/add_category.html:66` | `+ 2 elimination` | `+ 1 elimination` |
| Dashboard service | BUG | `app/services/dashboard_service.py:157` | `performers_ideal` | `(groups_ideal * 2) + 1` |
| Dashboard service comment | BUG | `app/services/dashboard_service.py:21` | "One full group minimum" | "Formula: (groups_ideal × 2) + 1" |

### Key Business Rules Defined
- **BR-MIN-001:** Minimum performers = `(groups_ideal × 2) + 1`
- **BR-MIN-002:** Adjusted minimum with guests = `max(2, (groups_ideal × 2) + 1 - guest_count)`

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 ADMIN: CREATE CATEGORY
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  User enters: Number of Pools = 2, Performers/Pool = 4                   │
  └──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  DISPLAY: add_category.html                                              │
  │                                                                          │
  │  🚨 BUG: Initial HTML shows "6" and "+ 2 elimination"                   │
  │  ✅ CORRECT: After JS runs, shows "5" and "+ 1 elimination"             │
  │                                                                          │
  │  User sees flicker from 6 → 5 on page load!                             │
  └──────────────────────────────────────────────────────────────────────────┘
                                    │
                    [User clicks "Add Category"]
                                    │
                                    ▼
═══════════════════════════════════════════════════════════════════════════════
 ADMIN: VIEW TOURNAMENT DETAIL
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  DISPLAY: tournaments/detail.html                                        │
  │                                                                          │
  │  🚨 BUG: Template calculates: (groups_ideal * 2) + 2 = 6                │
  │  ❌ Shows "Minimum Required: 6" (WRONG!)                                │
  │  ✅ Should show: 5                                                       │
  └──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  IMPACT:                                                                 │
  │  • User confused: was told minimum=5, now sees minimum=6                │
  │  • Ready/Not Ready badge logic WRONG (uses +2 formula)                  │
  │  • User may think they need 6 performers when only 5 required           │
  └──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 STAFF: DASHBOARD VIEW
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  DISPLAY: dashboard (via DashboardService)                               │
  │                                                                          │
  │  🚨 BUG: Uses performers_ideal (e.g., 4) as minimum                     │
  │  ❌ Shows "is_ready" when 4 registered (WRONG!)                         │
  │  ✅ Should require: 5 (formula result)                                   │
  └──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  IMPACT:                                                                 │
  │  • Category incorrectly shown as "Ready" with only 4 performers         │
  │  • Phase transition will FAIL when attempted (validators correct)       │
  │  • User frustration: "It said Ready but I can't advance!"               │
  └──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 PHASE TRANSITION VALIDATION (Correct - Source of Truth)
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  phase_validators.py uses calculate_minimum_performers()                 │
  │  ✅ Correctly calculates: (groups_ideal × 2) + 1 = 5                    │
  │  ✅ Correctly rejects if < 5 performers                                  │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Minimum Performer Formula

**Business Rule BR-MIN-001: Standard Minimum Performers**
> The minimum number of performers required to start a category is calculated as:
> `(groups_ideal × 2) + 1`
>
> This ensures:
> - At least 2 performers per pool (groups_ideal × 2)
> - At least 1 performer eliminated in preselection (+1)

**Acceptance Criteria:**
```gherkin
Feature: Consistent minimum performer display
  As an admin
  I want to see the same minimum performer count across all screens
  So that I can accurately plan my tournament registration

  Scenario: Add Category shows correct minimum
    Given I am creating a new category
    When I set Number of Pools to 2
    Then I should see "Minimum Required Performers: 5"
    And I should see formula "(2 pools × 2 minimum) + 1 elimination"

  Scenario: Tournament Detail shows correct minimum
    Given I have a category with groups_ideal=2
    When I view the tournament detail page
    Then the "Minimum Required" column should show "5"
    And the Ready badge should be GREEN when 5+ performers registered

  Scenario: Dashboard shows correct ready status
    Given I have a category with groups_ideal=2 and 4 performers
    When I view the dashboard
    Then the category should NOT be marked as "Ready"
    And it should show "Need 1 more"

  Scenario: Dashboard shows correct ready status with 5 performers
    Given I have a category with groups_ideal=2 and 5 performers
    When I view the dashboard
    Then the category should be marked as "Ready"
```

### 4.2 Adjusted Minimum with Guests

**Business Rule BR-MIN-002: Guest-Adjusted Minimum**
> When guests are registered, the minimum is reduced:
> `max(2, (groups_ideal × 2) + 1 - guest_count)`
>
> The floor of 2 ensures meaningful competition even with many guests.

**Acceptance Criteria:**
```gherkin
Feature: Guest-adjusted minimum display
  As an admin
  I want the minimum to reflect guest adjustments
  So that I know the true registration requirement

  Scenario: One guest reduces minimum
    Given I have a category with groups_ideal=2
    And 1 guest performer is registered
    When I view registration progress
    Then the minimum should show "4" (5 - 1 guest)

  Scenario: Minimum floors at 2
    Given I have a category with groups_ideal=2
    And 4 guest performers are registered
    When I view registration progress
    Then the minimum should show "2" (floor, not negative)
```

---

## 5. Current State Analysis

### 5.1 Source of Truth (Correct Implementation)

**Business Rule:** `(groups_ideal × 2) + 1`
**Implementation Status:** ✅ Correct
**Evidence:**

```python
# app/utils/tournament_calculations.py:41
return (groups_ideal * 2) + 1
```

**Test Coverage:**
- `tests/test_tournament_calculations.py` - Comprehensive tests for formula

### 5.2 Tournament Detail Template

**Business Rule:** Display should match source of truth
**Implementation Status:** ❌ WRONG
**Evidence:**

```jinja2
{# app/templates/tournaments/detail.html:76 #}
{% set minimum_required = (item.category.groups_ideal * 2) + 2 %}
```

**Impact:**
- Shows 6 instead of 5 for groups_ideal=2
- Ready/Not-Ready badge logic incorrect

### 5.3 Add Category Template

**Business Rule:** Display should match source of truth
**Implementation Status:** ⚠️ Partially Correct
**Evidence:**

```html
<!-- app/templates/tournaments/add_category.html:62 - WRONG initial value -->
<span id="min-display" style="font-size: 20px; color: #856404;">6</span>

<!-- app/templates/tournaments/add_category.html:66 - WRONG formula text -->
<strong>Formula:</strong> <span id="formula-display">(2 pools × 2 minimum) + 2 elimination</span>
```

```javascript
// app/templates/tournaments/add_category.html:101 - CORRECT calculation
const minimum = (groupsIdeal * 2) + 1;
```

**Impact:**
- Users see "6" flash to "5" on page load (visual glitch)
- Formula description misleading until JS runs

### 5.4 Dashboard Service

**Business Rule:** `minimum_required = (groups_ideal × 2) + 1`
**Implementation Status:** ❌ WRONG
**Evidence:**

```python
# app/services/dashboard_service.py:157
minimum_required = category.performers_ideal  # One full group - WRONG!
```

**Impact:**
- Dashboard shows categories as "Ready" prematurely
- For groups_ideal=2, performers_ideal=4: shows Ready at 4 (should be 5)
- Creates user frustration when phase transition fails

### 5.5 Registration Router (Correct)

**Business Rule:** Should use adjusted minimum
**Implementation Status:** ✅ Correct
**Evidence:**

```python
# app/routers/registration.py:560
"minimum_required": calculate_adjusted_minimum(category.groups_ideal, guest_count),
```

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Fix tournament detail template** (`app/templates/tournaments/detail.html:76`)
   - Change `+ 2` to `+ 1`
   - Consider using `calculate_minimum_performers()` via context

2. **Fix add category initial values** (`app/templates/tournaments/add_category.html`)
   - Line 62: Change hardcoded `6` to `5`
   - Line 66: Change `+ 2 elimination` to `+ 1 elimination`

3. **Fix dashboard service** (`app/services/dashboard_service.py:157`)
   - Import `calculate_minimum_performers` from `tournament_calculations`
   - Change to: `minimum_required = calculate_minimum_performers(category.groups_ideal)`
   - Update comment on line 21

### 6.2 Recommended

1. **Add minimum_performers_required property to Category model**
   - Centralize calculation in the ORM model
   - Templates can use `item.category.minimum_performers_required`
   - Prevents formula duplication

2. **Create E2E test for consistency**
   - Verify same minimum shown on add_category, detail, dashboard, registration
   - Catch future regressions

### 6.3 Nice-to-Have (Future)

1. **Consider Jinja2 global function**
   - Register `calculate_minimum_performers` as template global
   - Templates call function instead of inline math

---

## 7. Appendix: Reference Material

### 7.1 Pattern Scan Results

**Pattern searched:** Minimum performer calculation or display

**Search commands:**
```bash
grep -rn "groups_ideal.*\*.*2" app/
grep -rn "minimum.*required" app/templates/
grep -rn "+ 2" app/templates/ # Looking for wrong formula
```

**Results:**

| File | Line | Formula Used | Status |
|------|------|--------------|--------|
| `app/utils/tournament_calculations.py` | 41 | `(groups_ideal * 2) + 1` | ✅ Correct |
| `app/utils/tournament_calculations.py` | 47 | `max(2, (groups_ideal * 2) + 1 - guest_count)` | ✅ Correct |
| `app/schemas/category.py` | 61 | Uses `calculate_minimum_performers()` | ✅ Correct |
| `app/validators/phase_validators.py` | 80 | Uses `calculate_minimum_performers()` | ✅ Correct |
| `app/routers/registration.py` | 560+ | Uses `calculate_adjusted_minimum()` | ✅ Correct |
| `app/templates/tournaments/detail.html` | 76 | `(groups_ideal * 2) + 2` | ❌ WRONG |
| `app/templates/tournaments/add_category.html` | 62 | Hardcoded `6` | ❌ WRONG |
| `app/templates/tournaments/add_category.html` | 66 | `+ 2 elimination` text | ❌ WRONG |
| `app/templates/tournaments/add_category.html` | 101 | `(groupsIdeal * 2) + 1` (JS) | ✅ Correct |
| `app/services/dashboard_service.py` | 157 | `performers_ideal` | ❌ WRONG |

**Decision:**
- [x] Fix all in this feature (4 locations, all related to same business rule)

### 7.2 Formulas Reference

| Scenario | Formula | Example (groups_ideal=2) |
|----------|---------|--------------------------|
| Standard minimum | `(G × 2) + 1` | (2 × 2) + 1 = **5** |
| With 1 guest | `max(2, (G × 2) + 1 - 1)` | max(2, 5-1) = **4** |
| With 3 guests | `max(2, (G × 2) + 1 - 3)` | max(2, 5-3) = **2** |
| With 10 guests | `max(2, (G × 2) + 1 - 10)` | max(2, -5) = **2** (floor) |

### 7.3 Documentation References

- VALIDATION_RULES.md §3: Minimum Performer Requirements
- DOMAIN_MODEL.md §2: Tournament Configuration Constraints
- GLOSSARY.md: Minimum Performers Formula definition
- CHANGELOG.md [2025-11-19]: Formula change from +2 to +1

### 7.4 User Confirmation

- [x] User confirmed problem statement (inconsistent values 5 vs 6)
- [x] User validated root cause analysis scope (system-wide check)
- [ ] User to approve implementation plan

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-17 | Claude | Initial specification |
