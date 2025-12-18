# Feature Closure: Registration Page Stale Status Display Fix

**Date:** 2025-12-18
**Status:** Complete

---

## Summary

Fixed the registration page where the "(Need X more)" status counter was not updating when dancers were added or removed via HTMX. Also removed the unclear "Ready" badge per user feedback.

---

## Problem

1. **Stale Counter:** Header showed "8/8 registered (Need 4 more)" even after adding dancers
2. **Unclear Badge:** "Ready" badge had no clear purpose and cluttered the UI
3. **Duplicate Count:** Panel header `<h3>Registered (X)</h3>` showed stale count

## Root Cause

The HTMX OOB swap only updated `#reg-count` (the "8/8" text), but the conditional "(Need X more)" / "Ready" logic was **outside** that span and never re-rendered.

## Solution

1. Created new partial `_registration_status.html` with full status logic
2. Wrapped header status in `#registration-status` element
3. Updated OOB swap to target `#registration-status` instead of `#reg-count`
4. Removed "Ready" badge entirely
5. Removed stale count from panel `<h3>`

---

## Files Modified

| File | Change |
|------|--------|
| `_registration_status.html` | NEW - Reusable status partial |
| `_registered_list.html` | Removed Ready badge, simplified conditional |
| `_registration_update.html` | Updated OOB target to `#registration-status` |
| `register.html` | Use partial with wrapper ID, removed stale h3 count |

---

## Pattern Scan Results

Searched for similar stale HTMX header patterns:

| File | Status |
|------|--------|
| `registration/register.html` | Fixed |
| `registration/_registered_list.html` | Fixed |
| `preselection/*.html` | No HTMX updates (not affected) |
| `pools/*.html` | No HTMX updates (not affected) |

---

## Verification

- Manually tested add/remove dancers - status updates correctly
- "(Need X more)" disappears when minimum reached
- No duplicate/conflicting status indicators

---

**Closed By:** Claude
**Closed Date:** 2025-12-18
