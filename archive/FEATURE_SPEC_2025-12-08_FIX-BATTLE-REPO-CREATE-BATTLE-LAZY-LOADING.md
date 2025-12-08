# Feature Specification: Fix BattleRepository.create_battle() Lazy Loading

**Date:** 2025-12-08
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

`BattleRepository.create_battle()` method triggers lazy loading when appending performers to a newly created battle, causing a `MissingGreenlet` error in async SQLAlchemy contexts. This prevents the method from being used in integration tests and potentially in production code paths.

---

## 2. Executive Summary

### Scope
Fix the `create_battle()` method in `BattleRepository` to follow the established pattern used by `BattleService` - assigning performers before persisting the battle, not after.

### What Works ✅
| Feature | Status |
|---------|--------|
| `BattleService.generate_preselection_battles()` | Production Ready - assigns performers before create |
| `BattleService.generate_pool_battles()` | Production Ready - assigns performers before create |
| `BattleService.generate_finals_battles()` | Production Ready - assigns performers before create |
| `BattleRepository.create(instance)` | Production Ready - accepts pre-configured Battle |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| `create_battle()` appends performers after persist | BUG | `app/repositories/battle.py:194` |

### Key Business Rules Defined
- **BR-ASYNC-001:** All SQLAlchemy relationship access in async code must use eager loading
- **BR-ASYNC-003:** Performers must be assigned to Battle before persisting, not after

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 CURRENT FLOW (BROKEN): BattleRepository.create_battle()
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 1: Create Battle instance (no performers)                          │
  │  battle_instance = Battle(category_id=..., phase=..., ...)               │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 2: Persist Battle to database                                      │
  │  battle = await self.create(battle_instance)                             │
  │  - session.add(instance)                                                 │
  │  - await session.flush()                                                 │
  │  - await session.refresh(instance)  ← Battle now attached to session     │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 3: Try to append performers                                        │
  │  battle.performers.append(performer)                                     │
  │                                                                          │
  │  🚨 PROBLEM: Accessing battle.performers triggers lazy loading!          │
  │  SQLAlchemy tries to load existing performers from DB                    │
  │  In async context → MissingGreenlet error                                │
  └──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 CORRECT FLOW (WORKING): BattleService pattern
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 1: Create Battle instance (no performers yet)                      │
  │  battle = Battle(category_id=..., phase=..., ...)                        │
  │  - Battle object exists only in memory                                   │
  │  - battle.performers is empty list (no lazy loading needed)              │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 2: Assign performers BEFORE persisting                             │
  │  battle.performers = [performer1, performer2]                            │
  │                                                                          │
  │  ✅ Works because Battle not yet attached to session                     │
  │  No lazy loading - just assigning to empty list                          │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Step 3: Persist Battle WITH performers                                  │
  │  created_battle = await battle_repo.create(battle)                       │
  │                                                                          │
  │  ✅ SQLAlchemy persists both Battle AND performer associations           │
  │  junction table (battle_performers) populated automatically              │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Async-Safe Battle Creation

**Business Rule BR-ASYNC-003: Assign Performers Before Persist**
> When creating a Battle with performers in async context, performers must be assigned to the Battle instance BEFORE calling create/persist. Never append to `.performers` on an already-persisted Battle.

**Acceptance Criteria:**
```gherkin
Feature: Create battle with performers
  As a developer
  I want to create battles with performers reliably
  So that the application doesn't crash with MissingGreenlet errors

Scenario: Create battle with performers using repository
  Given I have performer IDs to add to a battle
  When I call BattleRepository.create_battle(category_id, phase, outcome_type, performer_ids)
  Then the battle should be created successfully
  And the performers should be linked to the battle
  And NO MissingGreenlet error should occur

Scenario: Use create_battle in integration tests
  Given a test creates performers
  When the test calls BattleRepository.create_battle()
  Then the method should succeed without lazy loading errors
```

---

## 5. Current State Analysis

### 5.1 BattleRepository.create_battle() Method

**Business Rule:** Create battles with performers atomically.

**Implementation Status:** ❌ Broken in async context

**Evidence:**
```python
# app/repositories/battle.py:159-198
async def create_battle(
    self,
    category_id: uuid.UUID,
    phase: BattlePhase,
    outcome_type: BattleOutcomeType,
    performer_ids: List[uuid.UUID],
) -> Battle:
    # Create Battle instance and persist it
    battle_instance = Battle(
        category_id=category_id,
        phase=phase,
        status=BattleStatus.PENDING,
        outcome_type=outcome_type,
    )
    battle = await self.create(battle_instance)  # ← Persists to DB

    # Add performers (need to load them from DB)
    from app.models.performer import Performer

    for performer_id in performer_ids:
        result = await self.session.execute(
            select(Performer).where(Performer.id == performer_id)
        )
        performer = result.scalar_one()
        battle.performers.append(performer)  # ← 🚨 TRIGGERS LAZY LOADING!

    await self.session.flush()
    await self.session.refresh(battle)
    return battle
```

**Test Coverage:** Method currently untested with real performers due to this bug.

### 5.2 Working Pattern: BattleService

**Evidence of correct pattern in `BattleService.generate_preselection_battles()`:**
```python
# app/services/battle_service.py:72-79
battle = Battle(
    category_id=category_id,
    phase=BattlePhase.PRESELECTION,
    status=BattleStatus.PENDING,
    outcome_type=BattleOutcomeType.SCORED,
)
battle.performers = performer_list  # ← Assigned BEFORE persist
created_battle = await self.battle_repo.create(battle)  # ← Then persisted
```

### 5.3 Similar Patterns in Codebase

**Pattern scan results - locations that assign performers:**

| File | Line | Pattern | Safe? |
|------|------|---------|-------|
| `battle_service.py` | 78 | `battle.performers = performer_list` before create | ✅ Safe |
| `battle_service.py` | 94 | `battle.performers = [p1, p2]` before create | ✅ Safe |
| `battle_service.py` | 107 | `battle.performers = performer_list[i:]` before create | ✅ Safe |
| `battle_service.py` | 149 | `battle.performers = [p1, p2]` before create | ✅ Safe |
| `battle_service.py` | 189 | `battle.performers = winners` before create | ✅ Safe |
| `battle_service.py` | 413 | `battle.performers = performer_list` before create | ✅ Safe |
| `battle_service.py` | 428 | `battle.performers = [p1, p2]` before create | ✅ Safe |
| `battle_service.py` | 441 | `battle.performers = performer_list[i:]` before create | ✅ Safe |
| `pool_service.py` | 113 | `pool.performers = qualified_performers[...]` before create | ✅ Safe |
| `tiebreak_service.py` | 146 | `battle.performers = tied_performers` before create | ✅ Safe |
| `battle.py` | 194 | `battle.performers.append(performer)` AFTER create | ❌ **BROKEN** |

**Decision:** Only `BattleRepository.create_battle()` needs fixing.

---

## 6. Implementation Recommendations

### 6.1 Critical (Must Fix)

1. **Refactor `BattleRepository.create_battle()` to assign performers before persist**
   - Load all performers first
   - Create Battle instance
   - Assign performers to battle
   - Call `create(battle)`
   - File: `app/repositories/battle.py`

### 6.2 Recommended

1. **Add integration test for `create_battle()`**
   - Test that verifies method works with real performers
   - Should catch any future regressions

### 6.3 Nice-to-Have (Future)

1. **Consider deprecating `create_battle()` in favor of service layer**
   - The method duplicates logic that should be in BattleService
   - All production code uses BattleService methods
   - `create_battle()` may only be used in tests

---

## 7. Appendix: Reference Material

### 7.1 Pattern Scan Results

**Pattern searched:** Assigning to `.performers` relationship

**Search command:**
```bash
grep -rn "\.performers\.append\|\.performers =" app/
```

**Results:**
- 10 safe locations (assign before persist)
- 1 broken location (append after persist)

### 7.2 SQLAlchemy Async Constraint

From SQLAlchemy documentation:
> In async mode, all relationship loading must be explicit. Accessing an unloaded relationship attribute will raise MissingGreenlet.

**Fix Pattern:**
```python
# ❌ BROKEN - append after persist triggers lazy loading
battle = await repo.create(battle_instance)
battle.performers.append(performer)

# ✅ CORRECT - assign before persist
battle = Battle(...)
battle.performers = [performer1, performer2]
battle = await repo.create(battle)
```

### 7.3 User Confirmation

- [x] User confirmed problem statement (discovered during previous fix)
- [x] User validated this is a bug worth fixing
- [ ] User approved requirements (pending review)
