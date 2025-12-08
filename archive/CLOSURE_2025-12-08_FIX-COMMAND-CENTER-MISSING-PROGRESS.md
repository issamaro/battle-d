# Feature Closure: Fix Command Center Missing Progress Variable

**Date:** 2025-12-08
**Status:** Complete

---

## Summary

Fixed the 500 Server Error on Event Command Center page (`/event/{tournament_id}`) by adding the missing `progress` and `queue` variables to the template context in the `command_center()` route.

---

## Problem

The Event Command Center page crashed with `UndefinedError: 'progress' is undefined` because:
- `command_center.html` includes `_phase_progress.html` which expects `progress`
- `command_center.html` includes `_battle_queue.html` which expects `queue`
- The route didn't pass these variables to the template

---

## Solution

Added two service calls in `command_center()` route:
```python
# Get phase progress for progress bar
progress = await event_service.get_phase_progress(tournament_uuid)

# Get battle queue
queue = await event_service.get_battle_queue(tournament_uuid, category_uuid)
```

And added both to the template context:
```python
context={
    ...
    "progress": progress,
    "queue": queue,
}
```

---

## Files Changed

| File | Change |
|------|--------|
| `app/routers/event.py` | Added `progress` and `queue` to `command_center()` context (lines 95-99, 114-115) |

---

## Tests

- **460 tests passed** (no new tests needed - existing service tests cover the methods)
- **0 failures**
- **No regressions**

---

## Documentation Updated

- `CHANGELOG.md`: Added entry for this bug fix

---

## Archived Workbench Files

- `FEATURE_SPEC_2025-12-08_FIX-COMMAND-CENTER-MISSING-PROGRESS.md`
- `IMPLEMENTATION_PLAN_2025-12-08_FIX-COMMAND-CENTER-MISSING-PROGRESS.md`
- `CHANGE_2025-12-08_FIX-COMMAND-CENTER-MISSING-PROGRESS.md`

---

## Why Tests Didn't Catch This

No E2E test loads the command center with a REAL tournament in an event phase. Tests with real battle data were removed due to database session isolation issues between async fixtures and TestClient. The existing E2E test only tests with a non-existent tournament ID (returns 404 before template renders).

---

## Technical Note

The HTMX partial routes (`/event/{id}/progress`, `/event/{id}/queue`) were already working correctly - they passed the required variables. Only the main page load route was missing the context variables.
