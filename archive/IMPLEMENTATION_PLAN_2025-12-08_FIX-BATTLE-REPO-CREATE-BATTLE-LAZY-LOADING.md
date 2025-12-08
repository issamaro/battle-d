# Implementation Plan: Fix BattleRepository.create_battle() Lazy Loading

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_FIX-BATTLE-REPO-CREATE-BATTLE-LAZY-LOADING.md

---

## 1. Summary

**Feature:** Fix lazy loading bug in `BattleRepository.create_battle()` method
**Approach:** Refactor method to assign performers BEFORE persisting, following the established pattern used in `BattleService`

---

## 2. Affected Files

### Backend
**Models:**
- No changes needed

**Services:**
- No changes needed (already using correct pattern)

**Repositories:**
- `app/repositories/battle.py`: Refactor `create_battle()` method (lines 159-198)

**Routes:**
- No changes needed

**Validators:**
- No changes needed

**Utils:**
- No changes needed

### Frontend
**Templates:**
- No changes needed

**Components:**
- No changes needed

**CSS:**
- No changes needed

### Database
**Migrations:**
- No changes needed (no schema changes)

### Tests
**New Test Files:**
- None needed

**Updated Test Files:**
- `tests/test_battle_repository.py`: Add test for `create_battle()` with performers

### Documentation
**Level 1:**
- No changes needed

**Level 2:**
- No changes needed

**Level 3:**
- No changes needed (pattern already documented in ARCHITECTURE.md)

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:** None required

**Data Migration:** None required

### 3.2 Repository Changes

**Repository:** BattleRepository
**Method to Refactor:** `create_battle()`

**Current Implementation (BROKEN):**
```python
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
    battle = await self.create(battle_instance)  # ← Persisted FIRST

    # Add performers (need to load them from DB)
    from app.models.performer import Performer

    for performer_id in performer_ids:
        result = await self.session.execute(
            select(Performer).where(Performer.id == performer_id)
        )
        performer = result.scalar_one()
        battle.performers.append(performer)  # ← TRIGGERS LAZY LOADING!

    await self.session.flush()
    await self.session.refresh(battle)
    return battle
```

**New Implementation (FIXED):**
```python
async def create_battle(
    self,
    category_id: uuid.UUID,
    phase: BattlePhase,
    outcome_type: BattleOutcomeType,
    performer_ids: List[uuid.UUID],
) -> Battle:
    """Create a new battle with performers.

    Args:
        category_id: Category UUID
        phase: Battle phase
        outcome_type: Type of outcome
        performer_ids: List of performer UUIDs in this battle

    Returns:
        Created battle instance

    Note:
        Follows BR-ASYNC-003: Performers assigned before persist to avoid
        lazy loading in async context.
    """
    # Step 1: Load all performers FIRST
    performers = []
    for performer_id in performer_ids:
        result = await self.session.execute(
            select(Performer).where(Performer.id == performer_id)
        )
        performer = result.scalar_one()
        performers.append(performer)

    # Step 2: Create Battle instance (not yet persisted)
    battle = Battle(
        category_id=category_id,
        phase=phase,
        status=BattleStatus.PENDING,
        outcome_type=outcome_type,
    )

    # Step 3: Assign performers BEFORE persisting (avoids lazy loading)
    battle.performers = performers

    # Step 4: Persist battle WITH performers
    return await self.create(battle)
```

**Key Changes:**
1. Load all performers into a list first
2. Create Battle instance (in memory, not attached to session)
3. Assign `battle.performers = performers` (no lazy loading - just assignment)
4. Call `self.create(battle)` which handles flush and refresh

### 3.3 Service Layer Changes

**No service changes required.** All service methods already use the correct pattern.

### 3.4 Route Changes

**No route changes required.**

---

## 4. Frontend Implementation Plan

**No frontend changes required.** This is a backend-only bug fix.

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- No changes required (no entity changes)

**VALIDATION_RULES.md:**
- No changes required (no validation rule changes)

### Level 2: Derived

**ROADMAP.md:**
- No changes required (bug fix, not new feature)

### Level 3: Operational

**ARCHITECTURE.md:**
- No changes required (pattern already documented in "Common Pitfalls #6")

**FRONTEND.md:**
- No changes required (backend-only fix)

**TESTING.md:**
- No changes required (test patterns unchanged)

---

## 6. Testing Plan

### Unit Tests

**test_battle_repository.py:**
```python
@pytest.mark.asyncio
async def test_create_battle_with_performers():
    """Test create_battle() creates battle with performers without lazy loading."""
    async with async_session_maker() as session:
        # Setup: Create tournament, category, dancers, performers
        tournament = Tournament(name="Test", date=date.today())
        session.add(tournament)
        await session.flush()

        category = Category(tournament_id=tournament.id, name="Breaking")
        session.add(category)
        await session.flush()

        dancer1 = Dancer(blaze="B-Boy Test1")
        dancer2 = Dancer(blaze="B-Boy Test2")
        session.add_all([dancer1, dancer2])
        await session.flush()

        performer1 = Performer(dancer_id=dancer1.id, category_id=category.id)
        performer2 = Performer(dancer_id=dancer2.id, category_id=category.id)
        session.add_all([performer1, performer2])
        await session.flush()

        # Test: Call create_battle()
        repo = BattleRepository(session)
        battle = await repo.create_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            outcome_type=BattleOutcomeType.SCORED,
            performer_ids=[performer1.id, performer2.id],
        )

        # Verify: Battle created with performers
        assert battle.id is not None
        assert len(battle.performers) == 2
        assert {p.id for p in battle.performers} == {performer1.id, performer2.id}
```

### Integration Tests

**No additional integration tests needed.** The bug was discovered during integration testing of another feature.

### Accessibility Tests

**Skipped:** Backend-only fix, no UI changes.

### Responsive Tests

**Skipped:** Backend-only fix, no UI changes.

---

## 7. Risk Analysis

### Risk 1: Breaking Existing Code Using create_battle()
**Concern:** Changing the method might break callers
**Likelihood:** Low - method signature unchanged
**Impact:** Low - method is underused (service layer handles most battle creation)
**Mitigation:**
- Keep method signature identical
- Method returns same type (Battle)
- Add test to verify behavior

### Risk 2: Performance Regression
**Concern:** Loading performers one at a time might be slow
**Likelihood:** Low - typically 2-3 performers per battle
**Impact:** Low - same number of queries as before, just ordered differently
**Mitigation:**
- Could batch load with `select(Performer).where(Performer.id.in_(performer_ids))`
- Keep simple for now, optimize if needed

### Risk 3: Session State Issues
**Concern:** Changing when objects are added to session might cause issues
**Likelihood:** Very Low - following proven pattern from BattleService
**Impact:** Medium - could cause subtle bugs
**Mitigation:**
- Pattern proven in 10 locations in codebase
- Test verifies correct behavior

---

## 8. Technical POC

**Status:** Not required
**Reason:** Standard refactoring following existing patterns. The correct pattern is already proven in 10 locations throughout the codebase (all in BattleService).

---

## 9. Implementation Order

**Recommended sequence:**

1. **Code Fix** (~5 minutes)
   - Refactor `BattleRepository.create_battle()` method
   - Follow the established pattern from BattleService

2. **Add Test** (~10 minutes)
   - Add integration test for `create_battle()`
   - Verify method works without MissingGreenlet error

3. **Run Full Test Suite** (~5 minutes)
   - Verify all 459+ tests still pass
   - Confirm no regressions

4. **Commit** (~2 minutes)
   - Commit with descriptive message

---

## 10. Open Questions

- [x] Should we deprecate `create_battle()` in favor of service layer? → No, keep it as a utility for tests and simple use cases
- [x] Should we batch-load performers for performance? → No, keep simple. 2-3 performers is typical.
- [x] Is the Performer import at module level OK? → Yes, already imported at top of file

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
