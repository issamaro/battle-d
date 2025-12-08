# Workbench: Fix MissingGreenlet Error in Event Service

**Date:** 2025-12-08
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix the 500 MissingGreenlet error on the Event Command Center page (`/event/{tournament_id}`) by adding chained eager loading for `Performer.dancer` relationship in BattleRepository methods.

**Root Cause:** `EventService._get_performer_display_name()` accesses `performer.dancer.blaze` but `BattleRepository` only loads `Battle.performers`, not the nested `Performer.dancer` relationship. SQLAlchemy async cannot lazy-load, causing MissingGreenlet error.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- [x] No changes required (no entity changes)

**VALIDATION_RULES.md:**
- [x] No changes required (no validation rule changes)

### Level 2: Derived
**ROADMAP.md:**
- [x] No changes required (bug fix, not new feature)

### Level 3: Operational
**ARCHITECTURE.md:**
- [x] Section: Common Pitfalls - Added #6 about chained eager loading for async

**FRONTEND.md:**
- [x] No changes required (backend-only fix)

**TESTING.md:**
- [x] No changes required (test patterns unchanged)

---

## Verification

**Grep checks performed:**
```bash
grep -rn "selectinload(Battle.performers)" app/repositories/
grep -rn "\.dancer\." app/services/
```

**Results:**
- All 9 locations in battle.py now have chained eager loading
- event_service.py accesses performer.dancer.blaze (works with fix)

**Files Updated:**
- `app/repositories/battle.py`: Add chained eager loading for Performer.dancer
- `ARCHITECTURE.md`: Add note about chained eager loading pattern
- `tests/test_event_service_integration.py`: Add 2 tests for performer names loading

---

## Files Modified

**Code:**
- `app/repositories/battle.py`:
  - Added `from app.models.performer import Performer` import (line 8)
  - Updated 9 methods with `.selectinload(Performer.dancer)` chained loading:
    - `get_by_category` (line 52)
    - `get_by_category_and_status` (line 75)
    - `get_by_phase` (line 99)
    - `get_by_status` (line 120)
    - `get_active_battle` (line 135)
    - `get_with_performers` (line 153)
    - `get_by_tournament` (line 216)
    - `get_by_tournament_and_status` (line 241)
    - `get_pending_battles_ordered` (line 292)

**Tests:**
- `tests/test_event_service_integration.py`:
  - Added `test_get_command_center_context_with_performer_names` (verifies fix for active battle)
  - Added `test_get_battle_queue_with_performer_names` (verifies fix for battle queue)

**Documentation:**
- `ARCHITECTURE.md`: Added section "6. Don't Forget Chained Eager Loading for Nested Relationships (Async SQLAlchemy)"

---

## Implementation Progress

- [x] Documentation updated (ARCHITECTURE.md)
- [x] BattleRepository updated (9 methods)
- [x] Integration tests added (2 tests)
- [x] All tests passing (14 event service integration tests)

---

## Test Results

```
tests/test_event_service_integration.py: 14 passed
tests/test_battle_service.py: 39 passed
tests/test_battle_results_encoding_integration.py: 5 passed
```

---

## Next Steps

1. Deploy to production
2. Verify `/event/{tournament_id}` page loads without error
3. Verify performer names display correctly
