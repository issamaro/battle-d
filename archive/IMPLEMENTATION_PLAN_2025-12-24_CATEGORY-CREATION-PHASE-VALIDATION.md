# Implementation Plan: Category Creation Phase Validation

**Date:** 2025-12-24
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-24_CATEGORY-CREATION-PHASE-VALIDATION.md

---

## 1. Summary

**Feature:** Add status validation to category creation endpoint (BR-CAT-001)
**Approach:** Follow existing delete_category pattern - add status check before category creation, hide UI button when not allowed

---

## 2. Affected Files

### Backend
**Routes:**
- `app/routers/tournaments.py:264-310`: Add status validation to `add_category()` endpoint
- `app/routers/tournaments.py:216-260`: Add status validation to `add_category_form()` GET endpoint

### Frontend
**Templates:**
- `app/templates/tournaments/detail.html:54-58`: Conditionally show "Add Category" button based on tournament status
- `app/templates/tournaments/add_category.html`: Add status check warning/redirect (defense in depth)

### Database
**Migrations:** None required - no schema changes

### Tests
**New Test File:**
- `tests/e2e/test_category_phase_validation.py`: E2E tests for category creation validation

### Documentation
**Level 1:**
- `VALIDATION_RULES.md`: Add BR-CAT-001 documentation

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Status:** None required

### 3.2 Route Changes

**Route 1: `add_category()` POST endpoint**

**Location:** `app/routers/tournaments.py:264`

**Current code (lines 289-305):**
```python
user = require_staff(current_user)

# Parse UUID
try:
    tournament_uuid = uuid.UUID(tournament_id)
except ValueError:
    add_flash_message(request, "Invalid tournament ID", "error")
    return RedirectResponse(url="/tournaments", status_code=303)

# Create category
await category_repo.create_category(...)
```

**Required change - add between UUID parse and create:**
```python
# Get tournament and verify status (BR-CAT-001)
tournament = await tournament_repo.get_by_id(tournament_uuid)
if not tournament:
    add_flash_message(request, "Tournament not found", "error")
    return RedirectResponse(url="/tournaments", status_code=303)

if tournament.status != TournamentStatus.CREATED:
    add_flash_message(
        request,
        "Categories can only be added when tournament is in CREATED status",
        "error"
    )
    return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=303)
```

**Dependencies needed:**
- Add `TournamentStatus` import (already imported via `from app.models.tournament import TournamentStatus`)
- Add `tournament_repo: TournamentRepository = Depends(get_tournament_repo)` parameter

---

**Route 2: `add_category_form()` GET endpoint**

**Location:** `app/routers/tournaments.py:216`

**Current code (lines 245-260):**
```python
# Get tournament
tournament = await tournament_repo.get_by_id(tournament_uuid)
if not tournament:
    raise HTTPException(...)

return templates.TemplateResponse(...)
```

**Required change - add after tournament fetch:**
```python
# Verify tournament status allows category creation (BR-CAT-001)
if tournament.status != TournamentStatus.CREATED:
    add_flash_message(
        request,
        "Categories can only be added when tournament is in CREATED status",
        "error"
    )
    return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=303)
```

---

## 4. Frontend Implementation Plan

### 4.1 Template Changes

**Template 1: `tournaments/detail.html`**

**Current code (lines 54-58):**
```html
<p>
    <a href="/tournaments/{{ tournament.id }}/add-category" role="button">
        + Add Category
    </a>
</p>
```

**Required change - wrap in status conditional:**
```html
{% if tournament.status.value == 'created' %}
<p>
    <a href="/tournaments/{{ tournament.id }}/add-category" role="button">
        + Add Category
    </a>
</p>
{% endif %}
```

**Rationale:** Follow existing pattern used for delete button (lines 98-105)

---

**Template 2: `tournaments/add_category.html` (optional, defense in depth)**

No changes required - the backend validation will redirect before this template is rendered.

---

### 4.2 Accessibility

No new accessibility requirements - existing button pattern is already accessible.

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**VALIDATION_RULES.md**

**Section to add:** After "Deletion Rules" section (~line 461)

**Content:**
```markdown
### Category Creation Rules

**BR-CAT-001: Category Creation Status Restriction**

Categories can only be created when the tournament status is CREATED.

**Validation:**
```python
if tournament.status != TournamentStatus.CREATED:
    raise ValidationError("Categories can only be added when tournament is in CREATED status")
```

**Rationale:**
- Tournament structure (categories) is part of initial setup
- Once competition begins (ACTIVE), category structure is locked
- Prevents inconsistent tournament state during competition

**Error Message:**
```
Categories can only be added when tournament is in CREATED status
```
```

---

## 6. Testing Plan

### E2E Tests

**New file:** `tests/e2e/test_category_phase_validation.py`

**Test cases:**
```python
class TestCategoryCreationPhaseValidation:
    """Test BR-CAT-001: Category creation status restriction."""

    async def test_create_category_allowed_when_created(self, client, db_session):
        """Category creation succeeds when tournament status is CREATED."""
        # Given: Tournament with status=CREATED
        # When: POST to add-category
        # Then: 303 redirect, category created, success flash

    async def test_create_category_blocked_when_active(self, client, db_session):
        """Category creation fails when tournament status is ACTIVE."""
        # Given: Tournament with status=ACTIVE
        # When: POST to add-category
        # Then: 303 redirect to detail, error flash, no category created

    async def test_create_category_blocked_when_completed(self, client, db_session):
        """Category creation fails when tournament status is COMPLETED."""
        # Given: Tournament with status=COMPLETED
        # When: POST to add-category
        # Then: 303 redirect to detail, error flash, no category created

    async def test_add_category_form_blocked_when_active(self, client, db_session):
        """Add category form redirects when tournament is ACTIVE."""
        # Given: Tournament with status=ACTIVE
        # When: GET add-category form
        # Then: 303 redirect to detail, error flash

    async def test_add_category_button_hidden_when_active(self, client, db_session):
        """Add Category button not shown for ACTIVE tournaments."""
        # Given: Tournament with status=ACTIVE
        # When: GET tournament detail
        # Then: No "Add Category" link in response
```

---

## 7. Risk Analysis

### Risk 1: Missing Dependency Import
**Concern:** `add_category()` doesn't currently import TournamentRepository
**Likelihood:** Low (easy to add)
**Impact:** Low (compile-time error)
**Mitigation:** Add `tournament_repo` parameter to function signature

### Risk 2: Flash Message Not Showing
**Concern:** Flash message may not display on redirect
**Likelihood:** Low (existing pattern works)
**Impact:** Low (operation still blocked, just no feedback)
**Mitigation:** Follow existing delete_category pattern exactly

---

## 8. Implementation Order

**Recommended sequence (minimize risk):**

1. **Backend - POST endpoint** (Core fix)
   - Add status validation to `add_category()`
   - Add `tournament_repo` dependency
   - Test with curl

2. **Backend - GET endpoint** (Defense in depth)
   - Add status validation to `add_category_form()`
   - Test in browser

3. **Frontend - Detail template** (UX)
   - Hide "Add Category" button for non-CREATED tournaments
   - Visual verification

4. **Tests** (Verification)
   - Create `test_category_phase_validation.py`
   - Run tests to verify all scenarios

5. **Documentation** (Record)
   - Update VALIDATION_RULES.md with BR-CAT-001

---

## 9. Technical POC

**Status:** Not required
**Reason:** Standard validation pattern following existing `delete_category` implementation

---

## 10. Open Questions

- [x] Should we validate by phase (REGISTRATION) or status (CREATED)?
  → **Answer:** Status = CREATED (confirmed in feature spec)

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks acceptable
- [ ] User approved implementation order
