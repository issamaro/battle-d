# Workbench: Fix BattleRepository.create_battle() Lazy Loading

**Date:** 2025-12-08
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix the `create_battle()` method in `BattleRepository` to prevent `MissingGreenlet` errors by assigning performers BEFORE persisting the battle, following the established pattern used in `BattleService`.

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
- [x] No changes required (pattern already documented in "Common Pitfalls #6")

**FRONTEND.md:**
- [x] No changes required (backend-only fix)

**TESTING.md:**
- [x] No changes required (test patterns unchanged)

---

## Verification

**Grep checks performed:**
```bash
grep -rn "selectinload(Battle.performers)" app/repositories/
grep -rn "\.performers =" app/services/
```

**Results:**
- All BattleService methods already use correct pattern: `battle.performers = [...]` before `repo.create()`
- Pattern documented in ARCHITECTURE.md "Common Pitfalls #6: Don't Forget Chained Eager Loading"

---

## Files Modified

**Code:**
- `app/repositories/battle.py`: Refactored `create_battle()` method (lines 159-202)
  - Now loads all performers FIRST
  - Creates Battle instance (not yet persisted)
  - Assigns `battle.performers = performers` (avoids lazy loading)
  - Then calls `self.create(battle)` with performers already assigned

**Tests:**
- `tests/test_repositories.py`: Added `test_battle_repository_create_battle_with_performer_ids`
  - Verifies `create_battle()` works without MissingGreenlet errors
  - Tests that performers are correctly linked to the battle

**Documentation:**
- None required (pattern already documented)

---

## Implementation Progress

- [x] Documentation verified (no changes needed)
- [x] BattleRepository.create_battle() refactored
- [x] Integration test added
- [x] All tests passing (460 passed, 8 skipped)

---

## Test Results

```
460 passed, 8 skipped in 20.23s
```

---

## Notes

- This is a minimal bug fix following an established pattern
- The pattern is proven in 10 locations in BattleService
- No schema changes, no new fields, no API changes
- The fix follows BR-ASYNC-003: Performers assigned before persist
