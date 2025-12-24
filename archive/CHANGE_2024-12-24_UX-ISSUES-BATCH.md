# Workbench: UX Issues Batch Fix

**Date:** 2024-12-24
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix 6 UX inconsistencies + 1 harmonization task in the admin interface:
1. **Issue #1**: Three dots menu on tournament cards (View, Rename, Delete)
2. **Issue #2**: Empty state icon alignment
3. **Issue #3**: Category removal with CASCADE delete
4. **Issue #4**: Creation forms as modals (User + Dancer)
5. **Issue #5**: Modal centering fix
6. **Issue #6**: Phase advancement UI
7. **Issue #7**: Modal harmonization (HTMX pattern for all modals)

---

## Documentation Changes

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- [x] Section: Category Entity - Update deletion rule to allow CASCADE delete during REGISTRATION phase

### Level 3: Operational

**FRONTEND.md:**
- [x] Component Library: Document dropdown menu component
- [x] Component Library: Document rename modal component
- [x] HTMX Patterns: Document HTMX modal submission pattern with HX-Redirect

---

## Implementation Changes

### Phase 1: CSS Fixes
- [x] Modal centering (`margin: auto` in `_modals.scss`)
- [x] Empty state SVG (`display: block` in `_empty-state.scss`)

### Phase 2: Phase Advancement UI (Issue #6)
- [x] Add `POST /tournaments/{id}/advance` endpoint
- [x] Create `phase_advance_modal.html` component
- [x] Update `tournaments/detail.html` with advance button

### Phase 3: Category Removal (Issue #3)
- [x] Add `DELETE /tournaments/{id}/categories/{cat_id}` endpoint
- [x] Update `tournaments/detail.html` with remove button using HTMX

### Phase 3: Modal Harmonization (Issue #7)
- [x] Update `tournament_create_modal.html` to use HTMX
- [x] Create `tournament_create_form_partial.html`
- [x] Update `POST /tournaments/create` for HX-Redirect

### Phase 3: Creation Form Modals (Issue #4)
- [x] Create `user_create_modal.html` + form partial
- [x] Create `dancer_create_modal.html` + form partial
- [x] Update `admin/users.html` to use modal
- [x] Update `dancers/list.html` to use modal
- [x] Update backend endpoints for HX-Redirect

### Phase 4: Three Dots Menu (Issue #1)
- [x] Add dropdown structure to `tournaments/list.html`
- [x] Create `rename_modal.html` component
- [x] Add `POST /tournaments/{id}/rename` endpoint
- [x] Add JavaScript for dropdown toggle

### Phase 5: Testing
- [x] Create `tests/e2e/test_ux_issues_batch.py`

---

## Verification

**Grep checks performed:**
```bash
grep -r "margin: auto" app/static/scss/components/_modals.scss
grep -r "display: block" app/static/scss/components/_empty-state.scss
```

**Results:**
- [x] Modal centering CSS verified
- [x] Empty state SVG CSS verified
- [x] All new endpoints documented

---

## Files Modified

### New Files (8):
1. `app/templates/components/phase_advance_modal.html`
2. `app/templates/components/user_create_modal.html`
3. `app/templates/components/user_create_form_partial.html`
4. `app/templates/components/dancer_create_modal.html`
5. `app/templates/components/dancer_create_form_partial.html`
6. `app/templates/components/tournament_create_form_partial.html`
7. `app/templates/components/rename_modal.html`
8. `tests/e2e/test_ux_issues_batch.py`

### Modified Files - SCSS (2):
1. `app/static/scss/components/_modals.scss` - Added `margin: auto;`
2. `app/static/scss/components/_empty-state.scss` - Added `display: block;` to SVG

### Modified Files - Templates (5):
1. `app/templates/tournaments/list.html` - Added dropdown menu
2. `app/templates/tournaments/detail.html` - Added phase advance + category remove
3. `app/templates/admin/users.html` - Changed create to modal trigger
4. `app/templates/dancers/list.html` - Changed create to modal trigger
5. `app/templates/components/tournament_create_modal.html` - Converted to HTMX

### Modified Files - Backend (3):
1. `app/routers/tournaments.py` - Added category delete, rename, advance endpoints; updated create
2. `app/routers/admin.py` - Updated user create for HTMX
3. `app/routers/dancers.py` - Updated dancer create for HTMX

---

## Notes

- Used HTMX + HX-Redirect pattern for all modal form submissions
- Category removal uses hx-confirm for simple confirmation
- Dropdown menu uses vanilla JS for accessibility
- All tests passing after implementation

---

**End of Workbench**
