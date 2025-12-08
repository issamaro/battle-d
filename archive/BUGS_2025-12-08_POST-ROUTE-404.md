# Bug Report: POST Routes Return 303 Instead of 404

**Date:** 2025-12-08
**Severity:** Medium
**Status:** Resolved

---

## Summary

POST routes for battle operations return HTTP 303 (See Other) redirect instead of HTTP 404 (Not Found) when the requested resource doesn't exist. This is inconsistent with GET routes (which correctly return 404) and violates REST/HTTP semantics.

---

## Affected Routes

| Route | Method | Current Behavior | Expected Behavior |
|-------|--------|------------------|-------------------|
| `/battles/{id}/start` | POST | 303 redirect to `/battles` | 404 Not Found |
| `/battles/{id}/encode` | POST | 303 redirect to `/battles` | 404 Not Found |
| `/battles/{id}/reorder` | POST | 303 redirect to `/battles` | 404 Not Found |

---

## Root Cause

The routes use flash messages with redirects for error handling:

```python
# Current (INCORRECT)
if not battle:
    add_flash_message(request, "Battle not found", "error")
    return RedirectResponse(
        url="/battles",
        status_code=status.HTTP_303_SEE_OTHER
    )
```

Compare to GET routes which correctly use HTTPException:

```python
# GET routes (CORRECT)
if not battle:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Battle not found"
    )
```

---

## Impact

1. **HTTP Semantics**: 303 indicates successful processing, not an error
2. **Monitoring**: 3xx responses aren't flagged as errors in monitoring tools
3. **API Clients**: Clients can't distinguish between success-redirect and not-found
4. **Inconsistency**: GET returns 404, POST returns 303 for same condition

---

## Recommended Fix

Change POST routes to return 404 HTTPException for non-existent resources:

```python
# Recommended fix
if not battle:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Battle not found"
    )
```

---

## Files to Modify

- `app/routers/battles.py` - Lines 139-143, 237-241, 395-399

---

## Additional Notes

Similar pattern may exist in other routers (admin.py). A codebase-wide audit should be performed after this fix is verified.

---

## References

- RFC 7231 §6.5.4 (404 Not Found)
- RFC 7231 §6.4.4 (303 See Other)
