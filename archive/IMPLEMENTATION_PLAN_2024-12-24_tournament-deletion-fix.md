# Implementation Plan: Tournament Deletion Fix

**Date:** 2024-12-24
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2024-12-24_tournament-deletion-fix.md

---

## 1. Summary

**Feature:** Add tournament delete endpoint for CREATED status tournaments
**Approach:** Add `POST /{tournament_id}/delete` route following existing user deletion pattern from `admin.py:186-222`, using ORM cascade via `session.delete()` to properly delete categories and performers while preserving dancer profiles.

---

## 2. Affected Files

### Backend
**Models:**
- None (cascade already correctly configured in `Tournament.categories` relationship)

**Services:**
- None (simple CRUD operation, no business logic beyond status validation)

**Repositories:**
- `app/repositories/tournament.py`: Add `delete_with_cascade()` method (following `CategoryRepository` pattern at line 80-102)

**Routes:**
- `app/routers/tournaments.py`: Add `POST /{tournament_id}/delete` endpoint (following `admin.py:186-222` pattern)

**Validators:**
- None (status validation inline in route)

**Utils:**
- None

### Frontend
**Templates:**
- None (delete modal already correctly configured at `tournaments/list.html:147-155`)

**Components:**
- None (reusing existing `delete_modal.html` component)

**CSS:**
- None

### Database
**Migrations:**
- None (no schema changes)

### Tests
**New Test Files:**
- `tests/e2e/test_tournament_deletion.py`: E2E tests for tournament deletion

**Updated Test Files:**
- None

### Documentation
**Level 1:**
- None (VALIDATION_RULES.md already documents deletion rules at lines 454-462)

**Level 2:**
- None

**Level 3:**
- None

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:** None required.

**Cascade Configuration (Already Correct):**
```python
# app/models/tournament.py:110-114
categories: Mapped[List["Category"]] = relationship(
    "Category",
    back_populates="tournament",
    cascade="all, delete-orphan",  # ✅ Categories deleted when tournament deleted
)

# app/models/category.py (similar pattern)
performers: Mapped[List["Performer"]] = relationship(
    "Performer",
    back_populates="category",
    cascade="all, delete-orphan",  # ✅ Performers deleted when category deleted
)

# Performer.dancer_id has ondelete="CASCADE" which means:
# - Deleting DANCER cascades to Performer (not the reverse)
# - Deleting Tournament → Category → Performer does NOT delete Dancer ✅
```

### 3.2 Repository Changes

**Repository:** `TournamentRepository`
**New Method:**

```python
async def delete_with_cascade(self, id: uuid.UUID) -> bool:
    """Delete tournament using ORM to trigger cascade.

    Unlike base delete() which uses raw SQL, this method:
    1. Fetches the tournament object
    2. Uses session.delete() which triggers ORM cascade
    3. Properly deletes all child categories and performers

    This mirrors CategoryRepository.delete_with_cascade() pattern.

    Args:
        id: Tournament UUID

    Returns:
        True if deleted, False if not found
    """
    tournament = await self.get_by_id(id)
    if not tournament:
        return False
    await self.session.delete(tournament)
    await self.session.flush()
    return True
```

**Pattern Reference:** `app/repositories/category.py:80-102`

### 3.3 Route Changes

**Router:** `app/routers/tournaments.py`
**New Endpoint:**

```python
@router.post("/{tournament_id}/delete")
async def delete_tournament(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Delete a tournament (staff only, CREATED status only).

    Business Rules (BR-DEL-001):
    - Only CREATED status tournaments can be deleted
    - CASCADE deletes Categories and Performers
    - Dancer profiles are preserved

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        Redirect to /tournaments with success message
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        add_flash_message(request, "Invalid tournament ID", "error")
        return RedirectResponse(url="/tournaments", status_code=303)

    # Get tournament and validate status
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )

    # Validate CREATED status (BR-DEL-001)
    if tournament.status != TournamentStatus.CREATED:
        add_flash_message(
            request,
            f"Cannot delete tournament in {tournament.status.value.upper()} status. "
            "Only CREATED tournaments can be deleted.",
            "error"
        )
        return RedirectResponse(url="/tournaments", status_code=303)

    # Delete with cascade
    tournament_name = tournament.name  # Save for flash message
    deleted = await tournament_repo.delete_with_cascade(tournament_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )

    add_flash_message(request, "Tournament deleted successfully", "success")
    return RedirectResponse(url="/tournaments", status_code=303)
```

**Pattern Reference:** `app/routers/admin.py:186-222`

---

## 4. Frontend Implementation Plan

### 4.1 Components to Reuse

**From existing templates:**
- `delete_modal.html` - Already being used in `tournaments/list.html:147-155`

### 4.2 Template Changes

**None required.** The template at `tournaments/list.html:147-155` already:
1. Conditionally renders delete modal for CREATED status tournaments
2. Sets `delete_url` to `/tournaments/{id}/delete`
3. Shows warning message about permanent deletion

```html
{# Already implemented at tournaments/list.html:147-155 #}
{% for tournament in tournaments %}
    {% if tournament.status.value == 'created' %}
        {% set modal_id = "delete-tournament-" ~ tournament.id %}
        {% set item_name = tournament.name %}
        {% set delete_url = "/tournaments/" ~ tournament.id ~ "/delete" %}
        {% set warning_message = "This will permanently delete the tournament and all its data." %}
        {% include "components/delete_modal.html" %}
    {% endif %}
{% endfor %}
```

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**No updates required.** VALIDATION_RULES.md already documents the deletion rules at lines 454-462.

### Level 2: Derived

**No updates required.**

### Level 3: Operational

**No updates required.** Implementation follows existing patterns documented in ARCHITECTURE.md.

---

## 6. Testing Plan

### E2E Tests

**New File:** `tests/e2e/test_tournament_deletion.py`

```python
class TestTournamentDeletion:
    """Test tournament deletion functionality (BR-DEL-001)."""

    def test_delete_tournament_requires_auth(self, e2e_client):
        """POST /tournaments/{id}/delete requires authentication."""
        # Pattern from test_admin.py:330-345

    def test_delete_tournament_requires_staff(self, judge_client):
        """POST /tournaments/{id}/delete requires staff or admin role."""

    def test_delete_tournament_invalid_uuid(self, staff_client):
        """POST /tournaments/{id}/delete handles invalid UUID."""
        # Pattern from test_admin.py:364-382

    def test_delete_tournament_nonexistent_returns_404(self, staff_client):
        """POST /tournaments/{id}/delete returns 404 for non-existent tournament."""
        # Pattern from test_admin.py:384-404

    def test_delete_tournament_created_status_success(self, staff_client, create_e2e_tournament):
        """DELETE tournament with CREATED status succeeds.

        Gherkin:
            Given a tournament exists with status CREATED
            And the tournament has categories with performers
            When I POST to /tournaments/{id}/delete
            Then the tournament is deleted
            And I am redirected to /tournaments
            And I see success message
        """

    def test_delete_tournament_active_status_rejected(self, staff_client, create_e2e_tournament):
        """DELETE tournament with ACTIVE status is rejected.

        Gherkin:
            Given a tournament exists with status ACTIVE
            When I POST to /tournaments/{id}/delete
            Then I receive an error message
            And the tournament still exists
        """


class TestTournamentDeletionCascade:
    """Test cascade behavior for tournament deletion."""

    def test_delete_tournament_cascades_to_categories(self, staff_client, create_e2e_tournament):
        """Tournament deletion removes all categories.

        Gherkin:
            Given a tournament with 2 categories
            When the tournament is deleted
            Then both categories are deleted
        """

    def test_delete_tournament_cascades_to_performers(self, staff_client, create_e2e_tournament):
        """Tournament deletion removes all performers.

        Gherkin:
            Given a tournament with categories containing performers
            When the tournament is deleted
            Then all performers are deleted
        """

    def test_delete_tournament_preserves_dancers(self, staff_client, create_e2e_tournament):
        """Tournament deletion preserves linked dancer profiles.

        Gherkin:
            Given a tournament with performers linked to dancers
            When the tournament is deleted
            Then the dancer profiles still exist
            And those dancers can register for future tournaments
        """
```

**Test Patterns:** Following `tests/e2e/test_admin.py:327-404` and `tests/e2e/test_ux_issues_batch.py:98-174`

---

## 7. Technical POC

**Status:** Not required
**Reason:** Standard CRUD following existing patterns:
- Delete route pattern: `admin.py:186-222`
- ORM cascade pattern: `category.py:80-102`
- Cascade configuration: Already validated in feature spec (Section 5.2)

---

## 8. Risk Analysis

### Risk 1: ORM Cascade Not Triggering
**Concern:** Using `session.delete()` might not trigger cascade if relationships not loaded
**Likelihood:** Low (same pattern works in CategoryRepository)
**Impact:** Medium (orphaned records)
**Mitigation:**
- Use `session.delete(tournament)` which loads relationships via ORM
- Verify in E2E tests that categories/performers are deleted
- Pattern already proven in `CategoryRepository.delete_with_cascade()`

### Risk 2: Dancer Records Accidentally Deleted
**Concern:** Cascade might propagate to dancers
**Likelihood:** Very Low (FK direction is opposite)
**Impact:** High (data loss)
**Mitigation:**
- `ondelete="CASCADE"` on `performer.dancer_id` only cascades Dancer→Performer
- Add explicit E2E test `test_delete_tournament_preserves_dancers`
- Feature spec validates FK direction (Section 5.2)

### Risk 3: Deleting Non-CREATED Tournament
**Concern:** User might attempt to delete ACTIVE/COMPLETED tournament
**Likelihood:** Medium (UI already prevents, but direct POST possible)
**Impact:** Medium (workflow disruption)
**Mitigation:**
- Validate `tournament.status == TournamentStatus.CREATED` in route
- Return user-friendly error message with status info
- Template already only shows delete button for CREATED status

---

## 9. Implementation Order

**Recommended sequence (minimizes risk):**

1. **Repository** (~5 min)
   - Add `delete_with_cascade()` to `TournamentRepository`
   - Pattern: Copy from `CategoryRepository.delete_with_cascade()`

2. **Route** (~10 min)
   - Add `POST /{tournament_id}/delete` endpoint
   - Pattern: Follow `admin.py:186-222` (user deletion)
   - Include status validation for CREATED only

3. **E2E Tests** (~15 min)
   - Create `tests/e2e/test_tournament_deletion.py`
   - Test authentication, authorization, status validation
   - Test cascade behavior (categories, performers deleted; dancers preserved)

4. **Manual Verification** (~5 min)
   - Create CREATED tournament with categories/performers
   - Delete via UI modal
   - Verify redirect and flash message
   - Check database for cascade cleanup

**Total estimated implementation time: ~35 minutes**

---

## 10. Open Questions

All questions resolved during analysis:

- [x] Should delete use POST or DELETE method? → POST (matches modal form pattern, user delete pattern)
- [x] Is ORM cascade properly configured? → Yes (verified in feature spec Section 5.2)
- [x] Are dancers preserved after deletion? → Yes (FK direction is Dancer→Performer, not reverse)
- [x] What error message for non-CREATED status? → "Cannot delete tournament in X status. Only CREATED tournaments can be deleted."

---

## 11. Files to Create/Modify Summary

| File | Action | Lines Changed |
|------|--------|---------------|
| `app/repositories/tournament.py` | Add method | ~15 lines |
| `app/routers/tournaments.py` | Add endpoint | ~45 lines |
| `tests/e2e/test_tournament_deletion.py` | New file | ~120 lines |

**Total: ~180 lines of code**

---

## 12. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
