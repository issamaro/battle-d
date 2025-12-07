# Implementation Plan: Fix Repository create() Method Signature

**Date:** 2025-12-07
**Status:** Ready for Implementation
**Type:** Bug Fix

---

## 1. Summary

**Bug:** `TypeError: BaseRepository.create() takes 1 positional argument but 2 were given`

**Root Cause:** Services call `repo.create(model_instance)` but `BaseRepository.create()` expects `**kwargs`.

**Fix:** Override `create()` in `BattleRepository` and `PoolRepository` to accept model instances.

---

## 2. Affected Files

### Backend

**Repositories (need modification):**
- `app/repositories/battle.py`: Add `create()` override to accept Battle instance
- `app/repositories/pool.py`: Add `create()` override to accept Pool instance

**Services (no changes needed - these are working as intended):**
- `app/services/battle_service.py`: Calls `create(battle)` in 8 places (lines 79, 95, 108, 150, 190, 414, 429, 442)
- `app/services/tiebreak_service.py`: Calls `create(battle)` in 1 place (line 155)
- `app/services/pool_service.py`: Calls `create(pool)` in 1 place (line 116)

### Tests

**Existing Test Files (verify they pass):**
- `tests/test_battle_service.py`
- `tests/test_repositories.py`

---

## 3. Architectural Pattern

### Current Pattern in Codebase

The codebase has two patterns for creating entities:

**Pattern A: Domain-specific method (e.g., `create_battle()`):**
```python
# In repository
async def create_battle(self, category_id, phase, ...) -> Battle:
    return await self.create(category_id=category_id, phase=phase, ...)
```

**Pattern B: Direct model instance (what services are doing):**
```python
# In service
battle = Battle(category_id=..., phase=...)
battle.performers = [performer1, performer2]  # Set relationships
created_battle = await self.battle_repo.create(battle)  # Pass instance
```

### The Problem

Pattern B is used when relationships need to be set before persisting, but `BaseRepository.create(**kwargs)` doesn't support it.

### The Solution

Override `create()` in repositories that need Pattern B:

```python
async def create(self, instance: Battle) -> Battle:
    """Create a battle from an existing instance.

    Overrides BaseRepository.create() to accept a Battle object
    with pre-assigned relationships (e.g., performers).
    """
    self.session.add(instance)
    await self.session.flush()
    await self.session.refresh(instance)
    return instance
```

---

## 4. Backend Implementation Plan

### 4.1 BattleRepository Changes

**File:** `app/repositories/battle.py`

**Add after `__init__` method (around line 20):**

```python
async def create(self, instance: Battle) -> Battle:
    """Create a battle from an existing Battle instance.

    Overrides BaseRepository.create() to accept a Battle object
    with pre-assigned performers relationship.

    Args:
        instance: Battle instance to persist

    Returns:
        Created battle with ID and timestamps populated
    """
    self.session.add(instance)
    await self.session.flush()
    await self.session.refresh(instance)
    return instance
```

### 4.2 PoolRepository Changes

**File:** `app/repositories/pool.py`

**Add after `__init__` method (around line 20):**

```python
async def create(self, instance: Pool) -> Pool:
    """Create a pool from an existing Pool instance.

    Overrides BaseRepository.create() to accept a Pool object
    with pre-assigned performers relationship.

    Args:
        instance: Pool instance to persist

    Returns:
        Created pool with ID and timestamps populated
    """
    self.session.add(instance)
    await self.session.flush()
    await self.session.refresh(instance)
    return instance
```

---

## 5. Testing Plan

### Manual Verification

1. Advance tournament from REGISTRATION to PRESELECTION
2. Verify no error occurs
3. Verify battles are created correctly with performers

### Automated Tests

Run existing tests to ensure no regressions:
```bash
pytest tests/test_battle_service.py -v
pytest tests/test_repositories.py -v
```

---

## 6. Risk Analysis

### Risk 1: Breaking existing `create(**kwargs)` calls
**Concern:** Other code might call `battle_repo.create(category_id=..., phase=...)`
**Likelihood:** Low - grep shows no such usage
**Impact:** High if it exists
**Mitigation:** Search verified no kwargs-style calls exist for these repositories

### Risk 2: Relationship not properly loaded after create
**Concern:** `session.refresh()` might not load relationships
**Likelihood:** Low - standard SQLAlchemy pattern
**Impact:** Medium
**Mitigation:** Manual testing verifies performers loaded correctly

### Risk 3: Pool creation also broken (latent bug)
**Concern:** Same bug exists for pools but hasn't been triggered yet
**Likelihood:** Confirmed - pool_service.py line 116 has same pattern
**Impact:** High when PRESELECTION to POOLS transition is triggered
**Mitigation:** Fix both repositories now

---

## 7. Implementation Order

1. **BattleRepository** - Add `create()` override
2. **PoolRepository** - Add `create()` override
3. **Test** - Run existing tests
4. **Verify** - Manual test phase transition

**Estimated time:** 5 minutes

---

## 8. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
