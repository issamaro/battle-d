# Implementation Plan: Fix MissingGreenlet Error in Event Service

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_FIX-MISSING-GREENLET-ERROR.md

---

## 1. Summary

**Feature:** Fix 500 MissingGreenlet error on Event Command Center page
**Approach:** Add chained eager loading for `Performer.dancer` relationship in all BattleRepository methods that load performers

---

## 2. Affected Files

### Backend

**Models:**
- None (no model changes required)

**Services:**
- None (service code is correct, only needs proper data loading)

**Repositories:**
- `app/repositories/battle.py`: Update 9 methods to chain-load `Performer.dancer`

**Routes:**
- None (routes don't need changes)

**Validators:**
- None

**Utils:**
- None

### Frontend

**Templates:**
- None

**Components:**
- None

**CSS:**
- None

### Database

**Migrations:**
- None (no schema changes)

### Tests

**Updated Test Files:**
- `tests/test_event_service_integration.py`: Add test with performers+dancers to verify fix

### Documentation

**Level 1:**
- None (no domain model changes)

**Level 2:**
- None

**Level 3:**
- `ARCHITECTURE.md`: Consider adding note about chained eager loading pattern (optional)

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:** None required

**Data Migration:** None required

### 3.2 Repository Changes

**Repository:** `app/repositories/battle.py`

**Change Type:** Update eager loading options in 9 methods

**Pattern Before:**
```python
.options(selectinload(Battle.performers))
```

**Pattern After:**
```python
.options(
    selectinload(Battle.performers).selectinload(Performer.dancer)
)
```

**Methods to Update:**

| Line | Method | Change |
|------|--------|--------|
| 50 | `get_by_category` | Add `.selectinload(Performer.dancer)` |
| 71 | `get_by_category_and_status` | Add `.selectinload(Performer.dancer)` |
| 93 | `get_by_phase` | Add `.selectinload(Performer.dancer)` |
| 112 | `get_by_status` | Add `.selectinload(Performer.dancer)` |
| 125 | `get_active_battle` | Add `.selectinload(Performer.dancer)` |
| 141 | `get_with_performers` | Add `.selectinload(Performer.dancer)` |
| 202 | `get_by_tournament` | Add `.selectinload(Performer.dancer)` |
| 225 | `get_by_tournament_and_status` | Add `.selectinload(Performer.dancer)` |
| 274 | `get_pending_battles_ordered` | Add `.selectinload(Performer.dancer)` |

**Required Import:**
```python
# Add to imports at top of file (line ~7)
from app.models.performer import Performer
```

**Example Change (get_by_category):**

```python
# Before (line 48-53)
async def get_by_category(self, category_id: uuid.UUID) -> List[Battle]:
    result = await self.session.execute(
        select(Battle)
        .options(selectinload(Battle.performers))
        .where(Battle.category_id == category_id)
    )
    return list(result.scalars().all())

# After
async def get_by_category(self, category_id: uuid.UUID) -> List[Battle]:
    result = await self.session.execute(
        select(Battle)
        .options(
            selectinload(Battle.performers).selectinload(Performer.dancer)
        )
        .where(Battle.category_id == category_id)
    )
    return list(result.scalars().all())
```

### 3.3 Service Layer Changes

**No changes required.** The `EventService._get_performer_display_name()` method is correct - it just needs the dancer relationship to be eagerly loaded by the repository.

---

## 4. Frontend Implementation Plan

**No frontend changes required.** This is a backend data-loading fix only.

---

## 5. Testing Plan

### 5.1 New Integration Test

**File:** `tests/test_event_service_integration.py`
**Add Test:** Verify performer names are loaded correctly

```python
@pytest.mark.asyncio
async def test_get_command_center_context_with_performer_names():
    """Test command center context loads performer names (blazes) correctly.

    This test verifies the fix for MissingGreenlet error by ensuring
    the Performer.dancer relationship is eagerly loaded.
    """
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create dancers
        dancer1 = await create_dancer(session, "dancer1@test.com", "B-Boy Flash")
        dancer2 = await create_dancer(session, "dancer2@test.com", "PopMaster")

        # Register performers
        performer1 = await register_performer(session, tournament.id, category.id, dancer1.id)
        performer2 = await register_performer(session, tournament.id, category.id, dancer2.id)

        # Create battle with performers
        battle_repo = BattleRepository(session)
        battle = Battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            status=BattleStatus.ACTIVE,
            sequence_order=1,
            outcome_type=BattleOutcomeType.SCORED,
        )
        battle = await battle_repo.create(battle)

        # Link performers to battle
        performer_repo = PerformerRepository(session)
        p1 = await performer_repo.get_by_id(performer1.id)
        p2 = await performer_repo.get_by_id(performer2.id)
        battle.performers = [p1, p2]
        await session.flush()

        # Advance tournament phase
        tournament_repo = TournamentRepository(session)
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        # This should NOT raise MissingGreenlet error
        context = await service.get_command_center_context(tournament.id)

        # Verify performer names are correctly loaded
        assert context.current_battle is not None
        assert context.current_battle_performer1 == "B-Boy Flash"
        assert context.current_battle_performer2 == "PopMaster"
```

### 5.2 Existing Tests

**Run all existing tests to ensure no regression:**
```bash
pytest tests/test_event_service_integration.py -v
pytest tests/test_battle_service.py -v
pytest tests/test_battle_results_encoding_integration.py -v
```

### 5.3 Manual Testing

**After deployment, verify on production:**
1. Navigate to `/event/{tournament_id}` with active battles
2. Verify page loads without 500 error
3. Verify performer names are displayed (not "Unknown" or "TBD")
4. Check battle queue shows performer names

---

## 6. Risk Analysis

### Risk 1: Performance Impact from Additional Eager Loading

**Concern:** Loading dancer for each performer adds database queries
**Likelihood:** Low
**Impact:** Low (selectinload is efficient, one query per relationship)
**Mitigation:**
- `selectinload` batches all performers in one query + all dancers in one query
- Only adds 1 additional query regardless of performer count
- Monitor query performance after deployment

### Risk 2: Breaking Existing Tests

**Concern:** Tests might not expect dancer relationship to be loaded
**Likelihood:** Very Low
**Impact:** Low
**Mitigation:**
- Run all tests after change
- Tests don't mock at the query level, so changes should be transparent
- Existing tests create battles without performers, so no impact

### Risk 3: Missing a Method

**Concern:** Some repository method might be missed
**Likelihood:** Low
**Impact:** Medium (another MissingGreenlet error in different flow)
**Mitigation:**
- Comprehensive list of 9 methods identified via grep
- Add test that exercises all battle loading paths
- Search for any other `selectinload(Battle.performers)` patterns

### Risk 4: Circular Import

**Concern:** Importing Performer model might cause circular import
**Likelihood:** Low
**Impact:** Medium (application won't start)
**Mitigation:**
- `from app.models.performer import Performer` is already used in the file (line 174)
- Move to top of imports section for consistency

---

## 7. Technical POC

**Status:** Not required
**Reason:** Standard SQLAlchemy pattern (chained selectinload). This pattern is already used successfully in `PerformerRepository.get_by_category` (line 67-68):
```python
.options(
    selectinload(Performer.dancer),
    selectinload(Performer.duo_partner).selectinload(Performer.dancer),
)
```

---

## 8. Implementation Order

**Recommended sequence:**

1. **Update Repository** (5 min)
   - Add Performer import to top of file
   - Update all 9 methods with chained eager loading
   - Use search-and-replace for consistency

2. **Run Existing Tests** (2 min)
   - `pytest tests/test_event_service_integration.py -v`
   - `pytest tests/test_battle_service.py -v`
   - Verify no regressions

3. **Add New Test** (5 min)
   - Add `test_get_command_center_context_with_performer_names`
   - Run new test to verify fix

4. **Manual Verification** (3 min)
   - Start local server
   - Navigate to event page with battles
   - Verify no error and names display correctly

5. **Deploy to Production** (5 min)
   - Commit changes
   - Push to trigger deployment
   - Verify on production URL

---

## 9. Open Questions

- [x] **Should we also load `duo_partner.dancer`?**
  → Not for this fix. The `_get_performer_display_name` method handles duo differently (line 288-294) and doesn't access duo_partner.dancer. Can be added later if needed.

- [x] **Should we create a reusable constant for the loading options?**
  → Recommended for future (see feature-spec section 6.2), but not required for this fix. Keep it simple.

---

## 10. User Approval

- [x] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order

---

## 11. Verification Checklist

After implementation, verify:

- [ ] All 9 methods in `battle.py` updated
- [ ] Import for `Performer` added at top of file
- [ ] All existing tests pass
- [ ] New integration test passes
- [ ] Local manual test shows performer names
- [ ] Production deployment successful
- [ ] Production event page loads without error
