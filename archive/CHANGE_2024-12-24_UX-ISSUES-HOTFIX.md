# Workbench: UX Issues Hotfix

**Date:** 2024-12-24
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix 5 UI/UX bugs discovered during browser testing:
1. **Category deletion doesn't cascade to performers** (CRITICAL - dancer can't re-register)
2. Dropdown menu truncated by card overflow
3. Category deletion uses browser alert instead of styled modal
4. Empty state loupe icon not centered
5. User creation modal too narrow

---

## Documentation Changes

### Level 1: Source of Truth

No changes required - these are bug fixes, not new features or entity changes.

### Level 2: Derived

**ROADMAP.md:**
- No changes required - these are hotfixes, not a new phase

### Level 3: Operational

**ARCHITECTURE.md:**
- No changes required - following existing patterns (ORM delete, modals)

**FRONTEND.md:**
- No changes required - following existing component patterns

---

## Verification

**Pre-implementation checks:**
- [x] Category model has `cascade="all, delete-orphan"` on performers relationship
- [x] Base repository uses raw SQL delete (bypasses ORM cascade)
- [x] Current category deletion at `tournaments.py:366` uses `category_repo.delete()`

**Root cause confirmed:**
- `BaseRepository.delete()` uses raw SQL `delete(Model).where()` which bypasses ORM cascade
- ORM cascade only triggers when using `session.delete(object)`

---

## Files Modified

**Code:**
- app/repositories/category.py: Added `delete_with_cascade()` method
- app/routers/tournaments.py: Changed to use `delete_with_cascade()`
- app/static/scss/components/_cards.scss: Added overflow fix for tournament cards
- app/static/scss/components/_empty-state.scss: Added `.empty-state-content` centering
- app/static/css/main.css: Recompiled
- app/templates/components/user_create_modal.html: Added `modal-lg` class
- app/templates/components/user_create_form_partial.html: Added form-row layout
- app/templates/components/category_remove_modal.html: NEW - styled confirmation modal
- app/templates/tournaments/detail.html: Updated to use modal trigger

**Tests:**
- tests/e2e/test_ux_issues_batch.py: Added 2 new tests for cascade delete and styled modal

---

## Test Results

**All tests passing:** 555 passed, 9 skipped

---

## Notes

- ORM-level delete approach chosen over raw SQL for proper cascade handling
- Existing model relationships already have correct cascade settings (`cascade="all, delete-orphan"`)
- Fix ensures performers are deleted, allowing dancer to re-register
- New `delete_with_cascade()` method uses `session.delete()` to trigger ORM cascade

---

**End of Workbench File**
