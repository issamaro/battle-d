# Feature Specification: UX Issues Hotfix

**Date:** 2024-12-24
**Status:** Awaiting Implementation
**Based on:** Browser testing of UX Issues Batch Fix

---

## 1. Problem Statement

The UX Issues Batch Fix implementation (2024-12-24) failed browser testing with 6 critical issues:
1. Dropdown menu truncated by card overflow
2. Category deletion breaks dancer search in registration
3. Browser alert used instead of modal for category removal confirmation
4. Empty state loupe icon still not centered
5. User creation modal too narrow (inconsistent with dancer modal)
6. Overall: CSS and data integrity issues not caught by automated tests

---

## 2. Executive Summary

### Scope
Fix 5 UI/UX bugs + 1 data integrity issue discovered during browser testing.

### What Works ✅
| Feature | Status |
|---------|--------|
| Dropdown menu JavaScript logic | Working |
| Category removal backend (CASCADE) | Working |
| Dancer modal width | Production Ready |
| Phase advancement UI | Working |
| Rename modal | Working |

### What's Broken 🚨
| Issue | Type | Root Cause |
|-------|------|------------|
| Dropdown truncated | CSS BUG | `.card` has `overflow: hidden` (line 11 of _cards.scss) |
| **Category removal breaks registration** | **DATA BUG** | **`BaseRepository.delete()` uses raw SQL DELETE, bypassing ORM cascade** |
| Browser alert for confirmation | UX BUG | Using `hx-confirm` instead of modal |
| Loupe icon not centered | CSS BUG | Missing `.empty-state-content` flex centering |
| User modal too narrow | CSS BUG | Missing `.modal-lg` class on user modal |

### Key Business Rules Defined
- **BR-FIX-001:** Dropdown menus must escape parent overflow
- **BR-FIX-002:** Category deletion must properly cascade and refresh UI
- **BR-FIX-003:** All destructive actions use styled modal confirmation
- **BR-FIX-004:** Empty state icons must be visually centered
- **BR-FIX-005:** Modal widths must be consistent across similar forms

---

## 3. Five Whys Analysis

**Who is affected?** Staff and Admin users

**What broke?**
1. CSS overflow clipping dropdown
2. Session/commit issue causing stale data
3. Wrong confirmation pattern used
4. SVG centering not working
5. Inconsistent modal sizing

**When?** During browser testing of UX batch fix

**Where?**
- Tournament list page (dropdown)
- Tournament detail → Registration (category delete)
- Tournament detail (confirmation)
- Dancers page (empty state)
- Admin users page (modal)

**Why does this matter?** These bugs make the app appear broken and cause data confusion.

---

## 4. Pattern Scan Results

### Pattern 1: overflow: hidden on cards
**Search:** `overflow: hidden` in _cards.scss
**Result:** Line 11 - `.card { overflow: hidden; }`
**Impact:** Any dropdown inside a card will be clipped

### Pattern 2: hx-confirm usage
**Search:** `hx-confirm` in templates
**Results:**
| File | Line | Description |
|------|------|-------------|
| registration/_registered_list.html | 37, 47 | Guest/Unregister buttons |
| tournaments/detail.html | 102 | Category removal |

**Decision:** Fix category removal to use modal; keep registration confirms (less destructive)

### Pattern 3: Modal widths
**Search:** `modal-lg` and `modal` classes
**Results:**
- `tournament_create_modal.html` - No size class (500px default)
- `user_create_modal.html` - No size class (500px) - TOO NARROW
- `dancer_create_modal.html` - No size class (500px) - CORRECT
- `delete_modal.html` - No size class (500px) - CORRECT

**Decision:** User modal should match dancer modal pattern

### Pattern 4: 🚨 CRITICAL - Raw SQL DELETE Bypassing ORM Cascade

**Search:** `grep -rn "\.delete\(" app/`

**Root Cause Found:**
```python
# app/repositories/base.py lines 105-117
async def delete(self, id: uuid.UUID) -> bool:
    result = await self.session.execute(
        delete(self.model).where(self.model.id == id)  # RAW SQL!
    )
    return result.rowcount > 0
```

This uses SQLAlchemy Core `delete()` which bypasses ORM cascade relationships.

**Models with `cascade="all, delete-orphan"` that are AFFECTED:**
| Parent Model | Child Relationship | Cascade Setting |
|--------------|-------------------|-----------------|
| `Category` | `performers` | `cascade="all, delete-orphan"` |
| `Category` | `pools` | `cascade="all, delete-orphan"` |
| `Category` | `battles` | `cascade="all, delete-orphan"` |
| `Tournament` | `categories` | `cascade="all, delete-orphan"` |
| `Dancer` | `performers` | `cascade="all, delete-orphan"` |

**All `.delete()` usages in routers:**
| File | Line | Entity Deleted | Has Child Cascade? | Status |
|------|------|----------------|-------------------|--------|
| `tournaments.py` | 366 | Category | YES (performers, pools, battles) | 🚨 **BROKEN** |
| `registration.py` | 420 | Performer | No children | ✅ OK |
| `registration.py` | 695 | Performer | No children | ✅ OK |
| `admin.py` | 214 | User | No children | ✅ OK |

**Why Category delete is broken but others are OK:**
- `Performer` and `User` have no child relationships with cascade
- `Category` has 3 child relationships that need cascade deletion
- When `category_repo.delete()` runs, it deletes the Category row but **Performers remain orphaned**
- The orphaned Performer still has `tournament_id` set, so `dancer_registered_in_tournament()` returns `True`

**Decision:** Fix Category deletion to use ORM-level delete (fetch + `session.delete()`)

---

## 5. Business Rules & Acceptance Criteria

### 5.1 Dropdown Escape Overflow (BR-FIX-001)

**Business Rule BR-FIX-001: Dropdown Menu Visibility**
> Dropdown menus must be fully visible when opened, regardless of parent container overflow settings.

**Root Cause:** `.card` has `overflow: hidden` to prevent content overflow, but this clips absolutely positioned dropdowns.

**Solution:** Add `overflow: visible` override to `.tournament-card .card-body` or use `position: static` on dropdown parent.

**Acceptance Criteria:**
```gherkin
Scenario: Dropdown menu fully visible
  Given I am on the tournaments list page
  And a tournament card is visible
  When I click the three dots menu button
  Then the dropdown menu is fully visible
  And no options are cut off or hidden
```

### 5.2 Category Deletion Cascade (BR-FIX-002)

**Business Rule BR-FIX-002: Category Deletion Data Consistency**
> When a category is deleted, associated performers must be deleted AND the dancer must immediately be available for re-registration in the SAME tournament.

**Symptom:**
- Dancer "Storm" registered in category "hh" in Tournament A
- Category "hh" deleted
- Storm can register in OTHER tournaments ✅
- Storm CANNOT re-register in Tournament A 🚨

**Root Cause Analysis:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  BaseRepository.delete() uses RAW SQL DELETE                       │
│                                                                     │
│  delete(self.model).where(self.model.id == id)  ← Core SQL!        │
│                                                                     │
│  This BYPASSES SQLAlchemy ORM cascade relationships.               │
│  The Category row is deleted, but Performers remain ORPHANED.      │
│                                                                     │
│  Orphaned Performer still has:                                      │
│    - tournament_id = Tournament A                                   │
│    - dancer_id = Storm                                              │
│    - category_id = NULL (or dangling reference)                     │
│                                                                     │
│  So dancer_registered_in_tournament(Storm, TournamentA) → TRUE     │
└─────────────────────────────────────────────────────────────────────┘
```

**Solution:** Use ORM-level delete in CategoryRepository:
```python
async def delete_with_cascade(self, id: uuid.UUID) -> bool:
    """Delete category using ORM to trigger cascade."""
    category = await self.get_by_id(id)
    if not category:
        return False
    await self.session.delete(category)  # ORM delete triggers cascade
    await self.session.flush()
    return True
```

**Acceptance Criteria:**
```gherkin
Scenario: Dancer available after category deletion in same tournament
  Given I have Tournament "Battle 2024" with category "hh"
  And dancer "Storm" is registered in category "hh"
  When I remove category "hh"
  And I create a new category "breaking"
  And I go to the registration page for "breaking"
  And I search for "Storm"
  Then "Storm" appears in the available dancers list
  And "Storm" can be registered in "breaking"
```

### 5.3 Modal Confirmation for Destructive Actions (BR-FIX-003)

**Business Rule BR-FIX-003: Styled Confirmation Modals**
> All destructive actions (delete, remove) must use styled modal confirmations, not browser alerts.

**Current State:** Category removal uses `hx-confirm` which triggers a browser alert.

**Solution:** Create a category removal confirmation modal similar to `delete_modal.html`.

**Acceptance Criteria:**
```gherkin
Scenario: Category removal shows styled modal
  Given I am on the tournament detail page
  And a category exists with registered performers
  When I click the "Remove" button for the category
  Then a styled modal appears with:
    | Element | Content |
    | Title | "Remove Category" |
    | Warning | Shows performer count being removed |
    | Cancel button | Closes modal |
    | Confirm button | Red "Remove" button |
  And no browser alert appears
```

### 5.4 Empty State Icon Centering (BR-FIX-004)

**Business Rule BR-FIX-004: Centered Empty State Display**
> Empty state icons and text must be visually centered within their container.

**Root Cause:** The template wraps content in `.empty-state-content` but CSS only styles `.empty-state`.

**Evidence from screenshot:** The loupe icon appears left-aligned, not centered.

**Solution:** Add flex centering to `.empty-state-content` or ensure the icon container has proper centering.

**Acceptance Criteria:**
```gherkin
Scenario: Empty state icon is centered
  Given I am on the dancers page
  When I search for a non-existent dancer
  Then the empty state is displayed
  And the loupe icon is horizontally centered
  And the text is horizontally centered below the icon
```

### 5.5 Consistent Modal Layout (BR-FIX-005)

**Business Rule BR-FIX-005: Consistent Modal Layout Pattern**
> Similar forms (User create, Dancer create) must use consistent layout patterns.

**Current State:**
- Dancer modal: `class="modal modal-lg"` (700px) + uses `.form-row` for two-column layout
- User modal: `class="modal"` (500px) + all fields stacked in single column

**Root Cause Analysis:**
The dancer modal uses:
1. `modal-lg` class → 700px width
2. `.form-row` wrapper → two fields side-by-side (First Name + Last Name, Country + City)

The user modal uses:
1. No size class → 500px default width
2. No `.form-row` → all fields stacked vertically

This is NOT a perception issue. The user modal is objectively narrower (500px vs 700px) AND lacks the two-column layout pattern.

**Solution:**
1. Add `modal-lg` class to user modal (`class="modal modal-lg"`)
2. Wrap Email + First Name in a `.form-row` for two-column layout
3. Role selector takes full width below (spans two columns visually)
4. Checkbox stays full width at bottom

**Acceptance Criteria:**
```gherkin
Scenario: User modal matches dancer modal layout pattern
  Given I am on the admin users page
  When I click "+ Create User"
  Then the modal appears at 700px width (modal-lg)
  And Email and First Name fields are side-by-side
  And Role selector spans full width below
  And the layout matches the dancer create modal pattern
```

---

## 6. Implementation Recommendations

### 6.1 Critical (Must Fix)

1. **🚨 Category deletion CASCADE fix** (CategoryRepository)
   - Add `delete_with_cascade()` method using ORM-level delete
   - Update `tournaments.py` to use new method
   - This is the ROOT CAUSE of the re-registration bug
   ```python
   async def delete_with_cascade(self, id: uuid.UUID) -> bool:
       category = await self.get_by_id(id)
       if not category:
           return False
       await self.session.delete(category)
       await self.session.flush()
       return True
   ```

2. **Dropdown overflow fix** (_cards.scss)
   - Add `overflow: visible` to `.tournament-card` variant
   - Only affects tournament cards, not all cards

3. **Category removal modal**
   - Create `category_remove_modal.html` based on `delete_modal.html`
   - Remove `hx-confirm` from the button
   - Add modal trigger instead

### 6.2 Recommended

4. **Empty state centering**
   - Add styles for `.empty-state-content` in _empty-state.scss

5. **User modal layout**
   - Add `modal-lg` class to `user_create_modal.html` dialog element
   - Wrap Email + First Name in `.form-row` div

### 6.3 Verification

After fixes:
- Browser test all 5 issues
- **Critical test:** Delete category → Verify dancer can re-register in same tournament
- Run automated tests to ensure no regressions
- Screenshot evidence for each fix

---

## 7. Appendix

### 7.1 File Changes Required

| File | Change | Priority |
|------|--------|----------|
| `app/repositories/category.py` | Add `delete_with_cascade()` method | 🚨 CRITICAL |
| `app/routers/tournaments.py` | Use `delete_with_cascade()` instead of `delete()` | 🚨 CRITICAL |
| `app/static/scss/components/_cards.scss` | Add overflow override for dropdown | HIGH |
| `app/static/scss/components/_empty-state.scss` | Add `.empty-state-content` styles | MEDIUM |
| `app/templates/tournaments/detail.html` | Remove hx-confirm, add modal trigger | HIGH |
| `app/templates/components/category_remove_modal.html` | NEW - create confirmation modal | HIGH |
| `app/templates/components/user_create_modal.html` | Add `modal-lg` class to dialog | MEDIUM |
| `app/templates/components/user_create_form_partial.html` | Add `.form-row` for Email + First Name | MEDIUM |

### 7.2 Open Questions

- **Q:** Is the dancer disappearing a caching issue or commit issue?
  - **A:** ✅ RESOLVED - It's a CASCADE issue. `BaseRepository.delete()` uses raw SQL DELETE which bypasses ORM cascade. Performers are orphaned, not deleted.

- **Q:** Should we fix `BaseRepository.delete()` globally?
  - **A:** No. Only Category needs cascade. Performer and User deletes work fine (no child relationships). Adding a specific `delete_with_cascade()` to CategoryRepository is safer and more explicit.

### 7.3 User Confirmation

- [x] User reported 6 issues from browser testing
- [x] User classified implementation as "90% failed"
- [ ] User to confirm fix priorities
- [ ] User to accept fix approach

---

**End of Feature Specification**
