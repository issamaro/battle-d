# Workbench: Tournament Deletion Fix

**Date:** 2024-12-24
**Author:** Claude
**Status:** Complete

---

## Purpose

Add tournament delete endpoint for CREATED status tournaments. Uses ORM cascade via `session.delete()` to properly delete categories and performers while preserving dancer profiles.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- [x] No changes needed (Tournament entity already documented)

**VALIDATION_RULES.md:**
- [x] No changes needed (Deletion rules already at lines 454-462: "Tournament | Status = CREATED | Status = ACTIVE or COMPLETED")

### Level 2: Derived
**ROADMAP.md:**
- [x] No changes needed (bug fix, not new feature)

### Level 3: Operational
**ARCHITECTURE.md:**
- [x] No changes needed (follows existing patterns)

**FRONTEND.md:**
- [x] No changes needed (uses existing delete_modal.html component)

---

## Verification

**Grep checks performed:**
```bash
grep -r "BR-DEL-001" *.md
grep -r "delete.*tournament" VALIDATION_RULES.md
```

**Results:**
- ✅ VALIDATION_RULES.md line 460: "Tournament | Status = CREATED | Status = ACTIVE or COMPLETED"
- ✅ delete_modal.html already used at tournaments/list.html:147-155
- ✅ Cascade correctly configured in Tournament.categories relationship

---

## Files to Modify

**Code:**
- app/repositories/tournament.py: Add `delete_with_cascade()` method
- app/routers/tournaments.py: Add `POST /{tournament_id}/delete` endpoint

**Tests:**
- tests/e2e/test_tournament_deletion.py: New E2E tests

---

## Implementation Notes

- Pattern Reference: `admin.py:186-222` (user deletion)
- ORM Pattern: `category.py:80-102` (delete_with_cascade)
- Template already configured at `tournaments/list.html:147-155`

---

## Files Modified

**Code:**
- `app/repositories/tournament.py`: Added `delete_with_cascade()` method (~22 lines)
- `app/routers/tournaments.py`: Added `POST /{tournament_id}/delete` endpoint (~70 lines)

**Tests:**
- `tests/e2e/test_tournament_deletion.py`: New file with 11 E2E tests (~220 lines)

---

## Test Results

```
tests/e2e/test_tournament_deletion.py - 11 passed
tests/e2e/test_tournament_management.py - 15 passed (no regressions)
```

**Test Coverage:**
- Authentication requirements (401/302/303)
- Staff role authorization (403)
- Invalid UUID handling (303 redirect)
- Non-existent tournament (404)
- CREATED status deletion (success with 303)
- ACTIVE status rejection (303 with error)
- COMPLETED status rejection (303 with error)
- Cascade to categories
- Cascade to performers
- Dancer preservation
- HTMX HX-Redirect header
