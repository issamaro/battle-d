# Workbench: Fix Repository create() Method

**Date:** 2025-12-07
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix `TypeError: BaseRepository.create() takes 1 positional argument but 2 were given` that occurs when advancing tournament from REGISTRATION to PRESELECTION phase.

**Root Cause:** Services call `repo.create(model_instance)` but `BaseRepository.create()` expects `**kwargs`.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- N/A - No entity changes

**VALIDATION_RULES.md:**
- N/A - No validation rule changes

### Level 2: Derived
**ROADMAP.md:**
- N/A - Bug fix, not new feature

### Level 3: Operational
**ARCHITECTURE.md:**
- N/A - Using existing repository pattern (override `create()` for model instance support)

**FRONTEND.md:**
- N/A - No frontend changes

---

## Verification

**This is a bug fix with no documentation impact.** The pattern of overriding `create()` in repositories is already established in the codebase architecture.

---

## Files Modified

**Code:**
- [x] app/repositories/battle.py: Added `create()` override (lines 22-37)
- [x] app/repositories/pool.py: Added `create()` override (lines 22-37)

**Tests:**
- All 46 tests pass (test_battle_service.py: 39, test_repositories.py: 7)

---

## Test Results

```
pytest tests/test_battle_service.py tests/test_repositories.py -v
======================= 46 passed, 21 warnings in 1.33s ========================
```

---

## Notes

- Fixed latent bug in PoolRepository proactively (would fail on PRESELECTION -> POOLS transition)
- Pattern: Override `create()` to accept model instance when relationships need to be set before persisting
