# Feature Closure: Fix MissingGreenlet Error in Event Service

**Date:** 2025-12-08
**Status:** Complete
**Commit:** f00789b

---

## Summary

Fixed the 500 MissingGreenlet error on the Event Command Center page (`/event/{tournament_id}`) by adding chained eager loading for the `Performer.dancer` relationship in all `BattleRepository` methods.

---

## Problem

When accessing the Event Command Center page, users encountered a 500 Server Error:

> **MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?**

**Root Cause:** `EventService._get_performer_display_name()` accessed `performer.dancer.blaze`, but `BattleRepository` only loaded `Battle.performers` without the nested `Performer.dancer` relationship. SQLAlchemy async cannot lazy-load relationships, causing the MissingGreenlet error.

---

## Solution

Updated 9 methods in `app/repositories/battle.py` to use chained eager loading:

```python
# Before
.options(selectinload(Battle.performers))

# After
.options(selectinload(Battle.performers).selectinload(Performer.dancer))
```

**Methods Updated:**
1. `get_by_category`
2. `get_by_category_and_status`
3. `get_by_phase`
4. `get_by_status`
5. `get_active_battle`
6. `get_with_performers`
7. `get_by_tournament`
8. `get_by_tournament_and_status`
9. `get_pending_battles_ordered`

---

## Files Changed

| File | Change |
|------|--------|
| `app/repositories/battle.py` | Added Performer import, chained eager loading in 9 methods |
| `ARCHITECTURE.md` | Added documentation about chained eager loading pattern |
| `tests/test_event_service_integration.py` | Added 2 verification tests |

---

## Tests Added

| Test | Purpose |
|------|---------|
| `test_get_command_center_context_with_performer_names` | Verifies active battle performer names load correctly |
| `test_get_battle_queue_with_performer_names` | Verifies queue item performer names load correctly |

---

## Test Results

- **459 tests passed** (8 skipped - expected)
- **0 failures**
- **No regressions**

---

## Production Verification

After deployment, verify:
1. Navigate to `/event/{tournament_id}` on production
2. Confirm page loads without 500 error
3. Confirm performer names display correctly (not empty or "Unknown")

---

## Known Issues (Pre-existing, Not Introduced)

`BattleRepository.create_battle()` has a lazy loading issue when appending performers. This is tracked separately and was not introduced by this fix.

---

## Documentation Updated

- `ARCHITECTURE.md`: Added "Common Pitfalls #6: Don't Forget Chained Eager Loading for Nested Relationships (Async SQLAlchemy)"

---

## Archived Workbench Files

- `FEATURE_SPEC_2025-12-08_FIX-MISSING-GREENLET-ERROR.md`
- `IMPLEMENTATION_PLAN_2025-12-08_FIX-MISSING-GREENLET-ERROR.md`
- `CHANGE_2025-12-08_FIX-MISSING-GREENLET-ERROR.md`
- `TEST_RESULTS_2025-12-08_FIX-MISSING-GREENLET-ERROR.md`
