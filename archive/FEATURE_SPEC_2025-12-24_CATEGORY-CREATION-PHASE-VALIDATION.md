# Feature Specification: Category Creation Phase Validation

**Date:** 2025-12-24
**Status:** Awaiting Technical Design
**Type:** Bug Fix

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

Categories can be created at any tournament phase/status, but should only be allowed when the tournament status is CREATED. This violates the tournament lifecycle where structural changes (adding categories) should only occur during initial setup.

---

## 2. Executive Summary

### Scope
Fix missing status validation in the category creation endpoint to prevent adding categories to ACTIVE or COMPLETED tournaments.

### What Works
| Feature | Status |
|---------|--------|
| Category deletion phase validation | Production Ready |
| Performer registration phase validation | Production Ready |
| Guest registration phase validation | Production Ready |
| Performer unregistration phase validation | Production Ready |

### What's Broken
| Issue | Type | Location |
|-------|------|----------|
| Category creation allows any status | BUG | `app/routers/tournaments.py:264` |

### Key Business Rules Defined
- **BR-CAT-001:** Categories can only be created when tournament status is CREATED

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════
 TOURNAMENT STATUS: CREATED                    [Phase: REGISTRATION]
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  ALLOWED ACTIONS:                                        │
  │  ✅ Create categories                                    │
  │  ✅ Delete categories                                    │
  │  ✅ Register performers                                  │
  │  ✅ Unregister performers                                │
  │  ✅ Add guests                                           │
  └──────────────────────────────────────────────────────────┘

  [ADMIN: Advance Phase] ────────────────────────────────────►

═══════════════════════════════════════════════════════════════
 TOURNAMENT STATUS: ACTIVE                     [Phase: PRESELECTION+]
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  ALLOWED ACTIONS:                                        │
  │  ❌ Create categories (BLOCKED - BR-CAT-001)             │
  │  ❌ Delete categories (BLOCKED)                          │
  │  ❌ Register performers (BLOCKED)                        │
  │  ❌ Unregister performers (BLOCKED)                      │
  │  ✅ Run battles                                          │
  │  ✅ Encode results                                       │
  └──────────────────────────────────────────────────────────┘

  🚨 BUG: Category creation is NOT blocked in ACTIVE status!

═══════════════════════════════════════════════════════════════
 TOURNAMENT STATUS: COMPLETED                  [Phase: COMPLETED]
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  ALLOWED ACTIONS:                                        │
  │  ❌ All modifications (read-only)                        │
  └──────────────────────────────────────────────────────────┘

  🚨 BUG: Category creation is NOT blocked in COMPLETED status!
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Category Creation Status Restriction

**Business Rule BR-CAT-001: Category Creation Status Restriction**
> Categories can only be created when the tournament status is CREATED. Once a tournament becomes ACTIVE or COMPLETED, no new categories can be added.

**Rationale:**
- Tournament structure (categories) is part of initial setup
- Once competition begins (ACTIVE), category structure is locked
- Prevents inconsistent tournament state during competition
- Aligns with existing patterns for performer registration validation

**Acceptance Criteria:**
```gherkin
Feature: Category Creation Status Validation
  As a staff member
  I want to be prevented from adding categories to active/completed tournaments
  So that tournament structure remains stable during competition

  Scenario: Create category when tournament is CREATED
    Given a tournament with status "CREATED"
    And the tournament is in "REGISTRATION" phase
    When I submit the add category form
    Then the category should be created successfully
    And I should see a success message

  Scenario: Attempt to create category when tournament is ACTIVE
    Given a tournament with status "ACTIVE"
    And the tournament is in "PRESELECTION" phase
    When I submit the add category form
    Then the category should NOT be created
    And I should see an error message "Categories can only be added when tournament is in CREATED status"

  Scenario: Attempt to create category when tournament is COMPLETED
    Given a tournament with status "COMPLETED"
    When I submit the add category form
    Then the category should NOT be created
    And I should see an error message "Categories can only be added when tournament is in CREATED status"

  Scenario: Add category form should not be accessible for non-CREATED tournaments
    Given a tournament with status "ACTIVE"
    When I navigate to the tournament detail page
    Then the "Add Category" button should not be visible
```

---

## 5. Current State Analysis

### 5.1 Category Creation Endpoint

**Business Rule:** Categories should only be created during tournament setup (status = CREATED)

**Implementation Status:** ❌ Missing validation

**Evidence:**
```python
# app/routers/tournaments.py:264-310
@router.post("/{tournament_id}/add-category")
async def add_category(
    request: Request,
    tournament_id: str,
    name: str = Form(...),
    is_duo: bool = Form(False),
    groups_ideal: int = Form(2),
    performers_ideal: int = Form(4),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repo),
):
    # ... UUID parsing ...

    # ❌ NO STATUS/PHASE VALIDATION HERE

    # Create category (always succeeds regardless of tournament status)
    await category_repo.create_category(...)
```

**Contrast with delete_category (correct implementation):**
```python
# app/routers/tournaments.py:360-364
if tournament.phase.value != "registration":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Categories can only be removed during REGISTRATION phase",
    )
```

### 5.2 Pattern Scan Results

**Pattern searched:** Operations that should be restricted by tournament status/phase

**Search command:**
`grep -rn "tournament.phase.*REGISTRATION\|TournamentPhase.REGISTRATION" app/`

**Results:**
| File | Line | Has Validation | Description |
|------|------|----------------|-------------|
| `app/routers/tournaments.py` | 264 | ❌ NO | `add_category` - BUG |
| `app/routers/tournaments.py` | 360 | ✅ YES | `delete_category` |
| `app/routers/registration.py` | 775 | ✅ YES | `register_guest_htmx` |
| `app/routers/registration.py` | 879 | ✅ YES | `convert_to_guest_htmx` |
| `app/services/performer_service.py` | 231 | ✅ YES | `register_performer` |
| `app/services/performer_service.py` | 319 | ✅ YES | `unregister_performer` |

**Decision:**
- [x] Fix reported bug only (category creation)
- [ ] Fix all in this feature (no other issues found)

### 5.3 UI Considerations

The "Add Category" button/link is likely visible on the tournament detail page regardless of status. This should also be addressed:

**Current state:** Button always visible
**Desired state:** Button hidden when tournament status is not CREATED

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Add status validation to `add_category` endpoint**
   - Location: `app/routers/tournaments.py:264`
   - Check `tournament.status == TournamentStatus.CREATED`
   - Return 400 error with clear message if not CREATED
   - Pattern: Follow existing `delete_category` validation style

2. **Hide "Add Category" button for non-CREATED tournaments**
   - Location: `app/templates/tournaments/detail.html`
   - Conditionally render button based on `tournament.status`

3. **Add E2E test for validation**
   - Test category creation blocked for ACTIVE tournament
   - Test category creation blocked for COMPLETED tournament
   - Test category creation succeeds for CREATED tournament

### 6.2 Recommended

1. **Update VALIDATION_RULES.md**
   - Add BR-CAT-001 documentation
   - Document under "Category Management" section

### 6.3 Nice-to-Have (Future)

1. Consider refactoring phase/status checks into a reusable decorator or dependency

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should we validate by phase (REGISTRATION) or status (CREATED)?
  - **A:** User confirmed: validate by **status = CREATED**. This is the correct approach because status represents the tournament lifecycle state, while phase is the current stage of competition.

### 7.2 Related Documentation

- **DOMAIN_MODEL.md:** Tournament status lifecycle (CREATED → ACTIVE → COMPLETED)
- **VALIDATION_RULES.md:** Phase transition validation rules

### 7.3 User Confirmation

- [x] User confirmed problem statement
- [x] User validated that status = CREATED is the correct validation criteria
- [x] User approved requirements (implicit by providing clarification)
