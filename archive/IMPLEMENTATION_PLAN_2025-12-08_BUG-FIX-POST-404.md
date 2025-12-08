# Implementation Plan: Fix POST Routes Returning 303 Instead of 404

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** workbench/BUGS_2025-12-08_POST-ROUTE-404.md

---

## 1. Summary

**Feature:** Bug fix - POST routes return 303 redirect instead of 404 for non-existent resources
**Approach:** Replace `add_flash_message + RedirectResponse(303)` with `HTTPException(404)` for resource-not-found errors in POST routes

---

## 2. Affected Files

### Backend

**Routes:**
- `app/routers/battles.py`: 3 locations (lines 149-154, 251-256, 414-419)
- `app/routers/admin.py`: 3 locations (lines 185-191, 283-286, 337-340)
- `app/routers/registration.py`: 4 locations (lines 151-154, 157-160, 163-169, 415-418)

### Tests

**Updated Test Files:**
- `tests/e2e/test_event_mode.py`: Update assertions from `[303, 404]` to `404`
- `tests/e2e/test_admin.py`: Update assertions from `303` to `404` where applicable
- `tests/e2e/test_registration.py`: Update assertions from `303` to `404` where applicable

### Documentation

**Level 1:**
- None (no domain model changes)

**Level 2:**
- None (no roadmap changes)

**Level 3:**
- `workbench/BUGS_2025-12-08_POST-ROUTE-404.md`: Update status to Resolved

---

## 3. Backend Implementation Plan

### 3.1 battles.py Changes

**Location 1: start_battle (lines 149-154)**
```python
# Current (INCORRECT):
battle = await battle_repo.get_by_id(battle_id)
if not battle:
    add_flash_message(request, "Battle not found", "error")
    return RedirectResponse(
        url="/battles",
        status_code=status.HTTP_303_SEE_OTHER
    )

# Fix:
battle = await battle_repo.get_by_id(battle_id)
if not battle:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Battle not found"
    )
```

**Location 2: encode_battle (lines 251-256)**
```python
# Same pattern - replace redirect with HTTPException(404)
```

**Location 3: reorder_battle (lines 414-419)**
```python
# Same pattern - replace redirect with HTTPException(404)
```

### 3.2 admin.py Changes

**Location 1: delete_user (lines 185-191)**
```python
# Current:
deleted = await user_repo.delete(user_uuid)
if not deleted:
    add_flash_message(request, "User not found", "error")
else:
    add_flash_message(request, "User deleted successfully", "success")
return RedirectResponse(url="/admin/users", status_code=303)

# Fix:
deleted = await user_repo.delete(user_uuid)
if not deleted:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
add_flash_message(request, "User deleted successfully", "success")
return RedirectResponse(url="/admin/users", status_code=303)
```

**Location 2: update_user (lines 283-286)**
```python
# Same pattern
```

**Location 3: resend_magic_link (lines 337-340)**
```python
# Same pattern
```

### 3.3 registration.py Changes

**Location 1: register_dancer - tournament (lines 151-154)**
```python
# Current:
tournament = await tournament_repo.get_by_id(tournament_uuid)
if not tournament:
    add_flash_message(request, "Tournament not found", "error")
    return RedirectResponse(url="/tournaments", status_code=303)

# Fix:
tournament = await tournament_repo.get_by_id(tournament_uuid)
if not tournament:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tournament not found"
    )
```

**Location 2: register_dancer - category (lines 157-160)**
```python
# Same pattern
```

**Location 3: register_dancer - dancer (lines 163-169)**
```python
# Same pattern
```

**Location 4: unregister_dancer (lines 415-418)**
```python
# Same pattern as delete_user in admin.py
```

---

## 4. Test Updates

### 4.1 test_event_mode.py

**TestBattleStartAccess.test_start_battle_nonexistent_returns_error:**
```python
# Current:
assert response.status_code in [303, 404]

# Fix:
assert response.status_code == 404
```

**TestBattleEncodingAccess.test_encode_submit_nonexistent_returns_error:**
```python
# Current:
assert response.status_code in [303, 404]

# Fix:
assert response.status_code == 404
```

**TestBattleReorderAccess.test_reorder_nonexistent_battle_returns_error:**
```python
# Current:
assert response.status_code in [303, 404]

# Fix:
assert response.status_code == 404
```

### 4.2 test_admin.py

**TestDeleteUser.test_delete_user_nonexistent:**
```python
# Current:
assert response.status_code == 303

# Fix:
assert response.status_code == 404
```

**TestUpdateUser.test_update_user_nonexistent:**
```python
# Current:
assert response.status_code == 303

# Fix:
assert response.status_code == 404
```

**TestResendMagicLink.test_resend_nonexistent_user:**
```python
# Current:
assert response.status_code == 303

# Fix:
assert response.status_code == 404
```

### 4.3 test_registration.py

Review and update assertions for:
- `test_register_dancer_nonexistent_tournament`
- `test_register_dancer_nonexistent_category`
- `test_register_dancer_nonexistent_dancer`
- `test_unregister_dancer_nonexistent`

---

## 5. Risk Analysis

### Risk 1: UI Flow Disruption
**Concern:** Users currently see flash message on redirect; now they'll see 404 error page
**Likelihood:** High (this is the expected behavior change)
**Impact:** Low (404 is correct HTTP behavior)
**Mitigation:**
- 404 error page should be user-friendly
- Message will say "Resource not found" which is clear

### Risk 2: Breaking HTMX Interactions
**Concern:** Some HTMX requests might expect redirect behavior
**Likelihood:** Low (checked code - HTMX requests handle success paths, not 404s)
**Impact:** Medium
**Mitigation:**
- Test HTMX flows manually
- E2E tests will catch regressions

### Risk 3: Test Assertions Need Updates
**Concern:** Tests currently accept both 303 and 404
**Likelihood:** Certain (this is why we're updating tests)
**Impact:** Low (test-only change)
**Mitigation:**
- Update all affected test assertions
- Run full test suite

---

## 6. Implementation Order

1. **battles.py** (3 fixes)
   - Most critical - this is the originally reported bug

2. **admin.py** (3 fixes)
   - Same pattern, found during audit

3. **registration.py** (4 fixes)
   - Same pattern, found during audit

4. **Test updates**
   - test_event_mode.py (3 assertions)
   - test_admin.py (3 assertions)
   - test_registration.py (review needed)

5. **Run full test suite**
   - Verify all 457 tests pass
   - No regressions

6. **Update bug tracking document**
   - Mark BUG-001 as resolved

---

## 7. Quality Gate

- [ ] All 10 POST route fixes applied
- [ ] All E2E test assertions updated
- [ ] All tests pass (457 tests)
- [ ] Bug tracking document updated
- [ ] No regressions in coverage

---

## 8. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved fixing all 10 occurrences (not just battles.py)
- [ ] User approved test assertion changes
