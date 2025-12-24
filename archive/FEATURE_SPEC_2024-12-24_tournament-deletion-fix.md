# Feature Specification: Tournament Deletion Fix

**Date:** 2024-12-24
**Status:** Awaiting Technical Design

---

## 1. Problem Statement

Staff users cannot delete CREATED status tournaments - clicking "Delete" in the modal returns a 404 error because the endpoint `/tournaments/{id}/delete` does not exist.

---

## 4. Business Rules & Acceptance Criteria

### BR-DEL-001: Tournament Deletion (CREATED status only)

**Business Rule:**
> CREATED status tournaments can be hard deleted. This permanently removes the tournament and all related data (categories, performers) while preserving dancer profiles.

**Reference:** `VALIDATION_RULES.md` lines 454-462

**Acceptance Criteria:**
```gherkin
Feature: Tournament Deletion
  As a staff user
  I want to delete tournaments in CREATED status
  So that I can remove unused tournament setups

  Scenario: Delete tournament in CREATED status
    Given I am logged in as a staff user
    And a tournament "Test Event" exists with status "CREATED"
    And the tournament has 2 categories with 5 performers each
    When I click "Delete" on the tournament
    And I confirm the deletion in the modal
    Then the tournament should be deleted
    And all categories should be deleted
    And all performers should be deleted
    And the linked dancer profiles should still exist
    And I should see a success message "Tournament deleted successfully"
    And I should be redirected to /tournaments

  Scenario: Cascade preserves dancer profiles
    Given a tournament exists with performer registrations
    And the performers are linked to dancer profiles
    When the tournament is deleted
    Then the dancer profiles should still exist in the system
    And those dancers can register for future tournaments
```

---

## 5. Current State Analysis

### 5.1 Missing Delete Endpoint

**Business Rule:** Staff should be able to delete CREATED tournaments
**Implementation Status:** ❌ Not Implemented
**Evidence:**
- `app/routers/tournaments.py` has no delete route
- Template at `tournaments/list.html:151` references `/tournaments/{id}/delete`

### 5.2 Cascade Configuration

**Implementation Status:** ✅ Correctly Configured

| Relationship | Cascade Config | Result on Tournament Delete |
|--------------|----------------|----------------------------|
| Tournament → Category | `cascade="all, delete-orphan"` | Categories deleted |
| Category → Performer | `cascade="all, delete-orphan"` | Performers deleted |
| Performer.dancer_id | `ondelete="CASCADE"` (FK direction) | Dancer NOT deleted |

**Note:** The `ondelete="CASCADE"` on `performer.dancer_id` means deleting a Dancer cascades to Performer, not the reverse. Deleting a tournament/performer does NOT delete the dancer.

### 5.3 Reference Implementation

User deletion at `app/routers/admin.py:186-222` works correctly with same pattern.

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Add tournament delete endpoint** in `app/routers/tournaments.py`:
   - Route: `@router.post("/{tournament_id}/delete")`
   - Require staff authentication
   - Validate tournament exists
   - Validate tournament status is CREATED (return 400 if not)
   - Use ORM-based delete (`session.delete()`) to trigger cascade
   - Add flash message on success
   - Redirect to `/tournaments`

2. **Add `delete_with_cascade` method** to `TournamentRepository`:
   - Use `session.delete(tournament)` to trigger ORM cascades
   - Similar to `CategoryRepository.delete_with_cascade()`

### 6.2 Recommended

1. Add E2E test for tournament deletion flow
2. Add unit test verifying dancers are preserved after deletion

---

## 7. Appendix

### 7.1 User Confirmation

- [x] User confirmed problem statement (screenshot shows 404)
- [x] User validated: CREATED → hard delete, ACTIVE → cancel (soft delete)
- [x] User confirmed cascade requirements (categories, performers deleted; dancers preserved)

### 7.2 Files to Modify

| File | Change |
|------|--------|
| `app/routers/tournaments.py` | Add delete endpoint |
| `app/repositories/tournament.py` | Add `delete_with_cascade` method |
