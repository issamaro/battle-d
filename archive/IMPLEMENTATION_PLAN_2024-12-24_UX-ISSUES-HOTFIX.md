# Implementation Plan: UX Issues Hotfix

**Date:** 2024-12-24
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2024-12-24_UX-ISSUES-HOTFIX.md

---

## 1. Summary

**Feature:** Fix 5 UI/UX bugs discovered during browser testing.

**Issues to Fix:**
1. **Category deletion doesn't cascade to performers** (dancer can't re-register to same tournament) - 🚨 CRITICAL
2. Dropdown menu truncated by card overflow
3. Category deletion uses browser alert instead of styled modal
4. Empty state loupe icon not centered
5. User creation modal too narrow (inconsistent with dancer modal)

**Approach:** ORM-level cascade fix + CSS fixes + new confirmation modal component + template updates.

---

## 2. Affected Files

### Backend (CASCADE Fix)

| File | Change |
|------|--------|
| `app/repositories/category.py` | Add `delete_with_cascade()` method using ORM-level delete |
| `app/routers/tournaments.py` | Use `delete_with_cascade()` instead of `delete()` |

### Frontend

**SCSS:**
| File | Change |
|------|--------|
| `app/static/scss/components/_cards.scss` | Add overflow override for dropdown visibility |
| `app/static/scss/components/_empty-state.scss` | Add `.empty-state-content` centering styles |

**Templates:**
| File | Change |
|------|--------|
| `app/templates/tournaments/detail.html` | Replace `hx-confirm` with modal trigger, add row IDs |
| `app/templates/components/category_remove_modal.html` | **NEW** - Create category removal confirmation modal |
| `app/templates/components/user_create_modal.html` | Add `modal-lg` class to dialog element |
| `app/templates/components/user_create_form_partial.html` | Add `.form-row` for Email + First Name side-by-side |

**CSS (Compiled):**
| File | Action |
|------|--------|
| `app/static/css/main.css` | Recompile from SCSS after changes |

### Tests

| File | Change |
|------|--------|
| `tests/e2e/test_ux_issues_batch.py` | Add test for cascade delete behavior |

---

## 3. Implementation Details

### 3.1 Category Deletion CASCADE Fix (BR-FIX-002) 🚨 CRITICAL

**Problem:** `BaseRepository.delete()` uses raw SQL DELETE which bypasses ORM cascade.

**Root Cause:**
```python
# app/repositories/base.py lines 105-117
async def delete(self, id: uuid.UUID) -> bool:
    result = await self.session.execute(
        delete(self.model).where(self.model.id == id)  # RAW SQL - no ORM cascade!
    )
    return result.rowcount > 0
```

When Category is deleted:
- Category row is deleted ✅
- Performers remain ORPHANED (not deleted) 🚨
- `dancer_registered_in_tournament()` still returns `True`
- Dancer cannot re-register in same tournament

**Solution:** Add ORM-level delete method to CategoryRepository.

**Code Change in `app/repositories/category.py`:**
```python
async def delete_with_cascade(self, id: uuid.UUID) -> bool:
    """Delete category using ORM to trigger cascade.

    Unlike base delete() which uses raw SQL, this method:
    1. Fetches the category object
    2. Uses session.delete() which triggers ORM cascade
    3. Properly deletes all child performers, pools, battles

    Args:
        id: Category UUID

    Returns:
        True if deleted, False if not found
    """
    category = await self.get_by_id(id)
    if not category:
        return False
    await self.session.delete(category)
    await self.session.flush()
    return True
```

**Code Change in `app/routers/tournaments.py` (line 366):**
```python
# Before
deleted = await category_repo.delete(category_uuid)

# After
deleted = await category_repo.delete_with_cascade(category_uuid)
```

---

### 3.2 Dropdown Overflow Fix (BR-FIX-001)

**Problem:** `.card` has `overflow: hidden` which clips dropdowns.

**Code Change in `_cards.scss`:**
```scss
// Add after line 135 (after .tournament-card-actions)
// Override overflow for tournament cards with dropdowns
.tournament-card {
  overflow: visible;

  .card-body {
    overflow: visible;
  }
}
```

---

### 3.3 Category Removal Modal (BR-FIX-003)

**Problem:** Uses `hx-confirm` which shows browser alert.

**New File: `app/templates/components/category_remove_modal.html`**
```html
{#
  Category Remove Modal Component (HTMX-enabled)

  Usage:
    {% set modal_id = "remove-category-" ~ item.category.id %}
    {% set category = item.category %}
    {% set performer_count = item.performer_count %}
    {% set tournament_id = tournament.id %}
    {% include "components/category_remove_modal.html" %}
#}

<dialog id="{{ modal_id }}" class="modal modal-danger" aria-labelledby="{{ modal_id }}-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="{{ modal_id }}-title" class="modal-title">Remove Category</h3>
      <button type="button" class="modal-close" aria-label="Close"
              onclick="document.getElementById('{{ modal_id }}').close()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="modal-body">
      <p>Are you sure you want to remove <strong>{{ category.name }}</strong>?</p>
      {% if performer_count > 0 %}
      <div class="modal-warning" role="alert">
        <strong>Warning:</strong> This will also remove {{ performer_count }} registered performer{{ 's' if performer_count != 1 else '' }}.
      </div>
      {% endif %}
      <p class="text-muted text-sm">This action cannot be undone.</p>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-secondary"
              onclick="document.getElementById('{{ modal_id }}').close()">
        Cancel
      </button>
      <button type="button" class="btn btn-danger"
              hx-delete="/tournaments/{{ tournament_id }}/categories/{{ category.id }}"
              hx-target="#category-row-{{ category.id }}"
              hx-swap="delete"
              onclick="document.getElementById('{{ modal_id }}').close()">
        Remove
      </button>
    </div>
  </div>
</dialog>

<script>
  document.getElementById('{{ modal_id }}').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') this.close();
  });
</script>
```

**Update `tournaments/detail.html`:**
1. Add `id="category-row-{{ item.category.id }}"` to `<tr>`
2. Replace button with modal trigger
3. Include modals after table

---

### 3.4 Empty State Icon Centering (BR-FIX-004)

**Code Change in `_empty-state.scss`:**
```scss
// Add after .empty-state block (around line 15)
.empty-state-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
```

---

### 3.5 User Modal Layout Fix (BR-FIX-005)

**Update `user_create_modal.html` line 13:**
```html
<dialog id="create-user-modal" class="modal modal-lg" aria-labelledby="create-user-title">
```

**Update `user_create_form_partial.html`:**
```html
<div class="form-row">
  <div class="form-group">
    <label for="email" class="form-label">Email <span class="required">*</span></label>
    <input type="email" id="email" name="email" required
           class="form-input {% if errors and errors.email %}is-invalid{% endif %}"
           value="{{ email|default('', true) }}" autofocus>
  </div>
  <div class="form-group">
    <label for="first_name" class="form-label">First Name <span class="required">*</span></label>
    <input type="text" id="first_name" name="first_name" required
           class="form-input" value="{{ first_name|default('', true) }}">
  </div>
</div>

<div class="form-group">
  <label for="role" class="form-label">Role <span class="required">*</span></label>
  <select id="role" name="role" required class="form-select">
    {% for r in roles %}
    <option value="{{ r }}" {% if role == r %}selected{% endif %}>{{ r }}</option>
    {% endfor %}
  </select>
</div>

<div class="form-check mb-4">
  <input type="checkbox" name="send_magic_link" value="true" checked
         class="form-check-input" id="send_magic_link">
  <label for="send_magic_link" class="form-check-label">Send magic link email to user</label>
</div>
```

---

## 4. Implementation Order

| Step | Task | Files | Risk |
|------|------|-------|------|
| 1 | **Backend: CASCADE fix** | `category.py`, `tournaments.py` | 🚨 CRITICAL |
| 2 | CSS: Dropdown overflow fix | `_cards.scss` | Low |
| 3 | CSS: Empty state centering | `_empty-state.scss` | Low |
| 4 | Compile SCSS | `main.css` | Low |
| 5 | Template: User modal width | `user_create_modal.html` | Low |
| 6 | Template: User form layout | `user_create_form_partial.html` | Low |
| 7 | Component: Category remove modal | `category_remove_modal.html` (NEW) | Medium |
| 8 | Template: Tournament detail update | `tournaments/detail.html` | Medium |
| 9 | Browser testing all fixes | - | - |
| 10 | Update automated tests | `test_ux_issues_batch.py` | Low |

---

## 5. Testing Plan

### 5.1 Critical Test: CASCADE Delete

```python
async def test_dancer_can_reregister_after_category_deletion():
    """BR-FIX-002: Dancer available after category deletion in same tournament."""
    # Setup
    tournament = create_tournament()
    category = create_category(tournament)
    dancer = create_dancer("Storm")
    register_dancer(dancer, category)

    # Verify registered
    assert dancer_registered_in_tournament(dancer, tournament) == True

    # Delete category
    await category_repo.delete_with_cascade(category.id)

    # Verify dancer is now available
    assert dancer_registered_in_tournament(dancer, tournament) == False
```

### 5.2 Manual Browser Testing

| Issue | Test | Expected |
|-------|------|----------|
| CASCADE | Delete category with dancer → Re-register same dancer | Dancer appears in available list |
| Dropdown | Open dropdown on tournament card | Menu fully visible |
| Modal | Click Remove on category | Styled modal, not browser alert |
| Empty state | Search non-existent dancer | Loupe icon centered |
| User modal | Click "+ Create User" | 700px wide, fields side-by-side |

---

## 6. Acceptance Criteria Summary

| Issue | Acceptance Criteria |
|-------|---------------------|
| **BR-FIX-002** | Dancer can re-register in same tournament after category deletion |
| **BR-FIX-001** | Dropdown menu fully visible when opened on tournament card |
| **BR-FIX-003** | Category removal shows styled modal, no browser alert |
| **BR-FIX-004** | Empty state icon is horizontally centered |
| **BR-FIX-005** | User modal is 700px wide with Email/First Name side-by-side |

---

## 7. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved ORM-only CASCADE solution
- [ ] User approved implementation order

---

**End of Implementation Plan**
