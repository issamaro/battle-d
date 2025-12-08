# Workbench: Bug Fix - POST Routes Return 303 Instead of 404

**Date:** 2025-12-08
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix POST routes that return HTTP 303 (redirect) instead of HTTP 404 (not found) when the requested resource doesn't exist. This violates HTTP semantics and creates inconsistency with GET routes.

**Reference:** workbench/BUGS_2025-12-08_POST-ROUTE-404.md

---

## Documentation Changes

### Level 1: Source of Truth
- No changes needed (no domain model or validation rule changes)

### Level 2: Derived
- No changes needed (no roadmap changes)

### Level 3: Operational
- No changes needed (this follows existing patterns in ARCHITECTURE.md)

---

## Code Changes

### Backend Routes (10 fixes total)

**app/routers/battles.py (3 locations):**
- [x] Line 149-154: `start_battle` - Replace redirect with HTTPException(404)
- [x] Line 251-256: `encode_battle` - Replace redirect with HTTPException(404)
- [x] Line 414-419: `reorder_battle` - Replace redirect with HTTPException(404)

**app/routers/admin.py (3 locations):**
- [x] Line 185-191: `delete_user` - Replace redirect with HTTPException(404)
- [x] Line 283-286: `update_user` - Replace redirect with HTTPException(404)
- [x] Line 337-340: `resend_magic_link` - Replace redirect with HTTPException(404)

**app/routers/registration.py (4 locations):**
- [x] Line 151-154: `register_dancer` tournament check - Replace redirect with HTTPException(404)
- [x] Line 157-160: `register_dancer` category check - Replace redirect with HTTPException(404)
- [x] Line 163-169: `register_dancer` dancer check - Replace redirect with HTTPException(404)
- [x] Line 415-418: `unregister_dancer` - Replace redirect with HTTPException(404)

### Test Updates

**tests/e2e/test_event_mode.py:**
- [x] `test_start_battle_nonexistent_returns_404`: Updated assertion to `404`
- [x] `test_encode_submit_nonexistent_returns_404`: Updated assertion to `404`
- [x] `test_reorder_nonexistent_battle_returns_404`: Updated assertion to `404`

**tests/e2e/test_admin.py:**
- [x] `test_delete_user_nonexistent_returns_404`: Updated assertion to `404`
- [x] `test_update_user_nonexistent_returns_404`: Updated assertion to `404`
- [x] `test_resend_nonexistent_user_returns_404`: Updated assertion to `404`

**tests/e2e/test_registration.py:**
- [x] `test_register_dancer_nonexistent_dancer_returns_404`: Updated assertion to `404`
- [x] `test_unregister_nonexistent_performer_returns_404`: Updated assertion to `404`

---

## Verification

**Test Results:**
- All 457 tests pass
- 8 skipped (expected)
- No regressions

**Grep verification:**
```bash
grep -r "HTTP_303_SEE_OTHER" app/routers/*.py
# Remaining 303 usages are for valid redirects after successful operations
```

---

## Files Modified

**Backend:**
- `app/routers/battles.py`: 3 fixes
- `app/routers/admin.py`: 3 fixes
- `app/routers/registration.py`: 4 fixes

**Tests:**
- `tests/e2e/test_event_mode.py`: 3 assertion updates
- `tests/e2e/test_admin.py`: 3 assertion updates
- `tests/e2e/test_registration.py`: 2 assertion updates

**Templates:**
- `app/templates/errors/404.html`: Added conditional `detail` display for specific error messages

**Documentation:**
- `workbench/BUGS_2025-12-08_POST-ROUTE-404.md`: Status updated to Resolved

---

## Quality Gate

- [x] All 10 POST route fixes applied
- [x] All E2E test assertions updated
- [x] All tests pass (457 tests)
- [x] Bug tracking document updated
- [x] No regressions in coverage
- [x] 404 template displays specific error messages (detail from HTTPException)

---

## UX Note

The fix preserves user experience by displaying specific error messages:
- **Browser requests** (Accept: text/html): Render 404.html template with `detail` (e.g., "Battle not found")
- **API/HTMX requests**: Return JSON `{"detail": "Battle not found"}`

The `http_exception_handler` in `app/main.py` routes HTTPException(404) to the template with the detail message.
