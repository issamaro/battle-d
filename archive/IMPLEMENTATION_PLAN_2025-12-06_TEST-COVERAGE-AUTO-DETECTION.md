# Implementation Plan: Test Coverage for Auto-Detection Methods

**Date:** 2025-12-06
**Status:** Ready for Implementation
**Based on:** TEST_RESULTS_2025-12-06_TOURNAMENT-ORGANIZATION-VALIDATION.md

---

## 1. Summary

**Feature:** Add unit test coverage for new auto-detection and battle management methods
**Approach:** Add tests to existing test files following established patterns

---

## 2. Affected Files

### Tests (Only files being modified)

**tests/test_tiebreak_service.py:**
- Add tests for `detect_and_create_preselection_tiebreak()`
- Add tests for `detect_and_create_pool_winner_tiebreaks()`

**tests/test_battle_service.py:**
- Add tests for `generate_interleaved_preselection_battles()`
- Add tests for `reorder_battle()`

---

## 3. Test Implementation Plan

### 3.1 TiebreakService Tests (test_tiebreak_service.py)

#### New Test Class: TestDetectAndCreatePreselectionTiebreak

```python
class TestDetectAndCreatePreselectionTiebreak:
    """Tests for BR-TIE-001: Preselection tiebreak auto-detection."""

    # Required fixtures additions:
    # - category_repo (AsyncMock)
    # - tiebreak_service_with_category_repo (TiebreakService with all repos)

    async def test_creates_tiebreak_when_tie_at_boundary():
        """Test tiebreak created when performers tie at qualification boundary.

        Setup: 9 performers, 6 qualify to pools
        - Scores: 10.0, 9.0, 8.0, 7.8, 7.5, 7.5, 7.5, 6.0, 5.0
        - 3 performers at 7.5, only 2 spots → tiebreak needed
        Expected: Tiebreak battle created with 3 performers, winners_needed=2
        """

    async def test_no_tiebreak_when_clear_cutoff():
        """Test no tiebreak when all scores are unique at boundary.

        Setup: 8 performers with unique scores, 6 qualify
        Expected: Returns None (no tiebreak needed)
        """

    async def test_no_tiebreak_when_all_tied_fit():
        """Test no tiebreak when all tied performers fit in capacity.

        Setup: 5 performers, 5 qualify (all fit)
        - Scores: 10.0, 9.0, 8.0, 7.5, 7.5
        Expected: Returns None (both 7.5 performers qualify)
        """

    async def test_skips_if_pending_tiebreak_exists():
        """Test no duplicate tiebreak if one already exists.

        Setup: Pending tiebreak already exists for category
        Expected: Returns None (prevent duplicates)
        """

    async def test_raises_if_category_repo_missing():
        """Test raises ValidationError if category_repo not configured.

        Setup: TiebreakService without category_repo
        Expected: ValidationError raised
        """

    async def test_calculates_correct_winners_needed():
        """Test winners_needed calculation based on spots remaining.

        Setup: 10 performers, 8 qualify
        - Scores: 10, 9, 8, 7, 6.5, 6.5, 6.5, 6.5, 5, 4
        - 4 above boundary, 4 tied at 6.5, need 4 more spots
        Expected: winners_needed = 4
        """
```

#### New Test Class: TestDetectAndCreatePoolWinnerTiebreaks

```python
class TestDetectAndCreatePoolWinnerTiebreaks:
    """Tests for BR-TIE-002: Pool winner tiebreak auto-detection."""

    async def test_creates_tiebreaks_for_tied_pools():
        """Test tiebreak created when pool has tied top performers.

        Setup: 2 pools
        - Pool A: P1=9pts, P2=9pts, P3=6pts (tied winners)
        - Pool B: P4=10pts, P5=7pts (clear winner)
        Expected: 1 tiebreak for Pool A, Pool B winner_id set
        """

    async def test_sets_winner_on_clear_pools():
        """Test winner_id set on pools with clear winner.

        Setup: Pool with one clear winner (9pts vs 6pts vs 3pts)
        Expected: Pool.winner_id set to top scorer
        """

    async def test_no_tiebreaks_all_clear_winners():
        """Test no tiebreaks when all pools have clear winners.

        Setup: 2 pools, each with unique top scorer
        Expected: Empty list returned, winner_id set on both pools
        """

    async def test_skips_pools_with_existing_winner():
        """Test skips pools that already have winner_id set.

        Setup: Pool already has winner_id assigned
        Expected: Pool skipped (no duplicate processing)
        """

    async def test_multiple_tied_pools():
        """Test multiple tiebreak battles for multiple tied pools.

        Setup: 3 pools, 2 with ties
        Expected: 2 tiebreak battles created
        """

    async def test_handles_empty_pools():
        """Test gracefully handles pools with no performers.

        Setup: Category with empty pool
        Expected: Empty pool skipped without error
        """
```

### 3.2 BattleService Tests (test_battle_service.py)

#### New Test Class: TestGenerateInterleavedPreselectionBattles

```python
class TestGenerateInterleavedPreselectionBattles:
    """Tests for BR-SCHED-001: Battle queue interleaving."""

    # Required fixture additions:
    # - category_repo mock

    async def test_interleaves_across_categories():
        """Test battles interleaved round-robin across categories.

        Setup:
        - Category H (Hip-hop): 4 performers → 2 battles
        - Category K (K-pop): 6 performers → 3 battles
        Expected order: H1, K1, H2, K2, K3
        Expected sequence_order: 1, 2, 3, 4, 5
        """

    async def test_assigns_sequence_order():
        """Test sequence_order field assigned correctly.

        Setup: 2 categories with battles
        Expected: All battles have unique, sequential sequence_order
        """

    async def test_single_category():
        """Test works with single category.

        Setup: 1 category with 6 performers
        Expected: 3 battles with sequence_order 1, 2, 3
        """

    async def test_no_categories_raises_error():
        """Test raises error when no categories found.

        Setup: Tournament with no categories
        Expected: ValidationError raised
        """

    async def test_no_performers_raises_error():
        """Test raises error when no performers in any category.

        Setup: Categories exist but all empty
        Expected: ValidationError raised
        """

    async def test_unequal_category_sizes():
        """Test handles categories with different battle counts.

        Setup:
        - Category A: 2 performers → 1 battle
        - Category B: 10 performers → 5 battles
        Expected: Interleaved as A1, B1, B2, B3, B4, B5
        """
```

#### New Test Class: TestReorderBattle

```python
class TestReorderBattle:
    """Tests for BR-SCHED-002: Battle queue reordering constraints."""

    async def test_reorder_battle_success():
        """Test successfully reordering a battle.

        Setup: 5 pending battles, move battle #3 to position #5
        Expected: Battle moved, sequence_order updated
        """

    async def test_first_pending_battle_locked():
        """Test cannot move the "on deck" (first pending) battle.

        Setup: Try to move battle with lowest sequence_order
        Expected: ValidationError "Next battle is locked"
        """

    async def test_cannot_move_active_battle():
        """Test cannot move ACTIVE battle.

        Setup: Battle with status=ACTIVE
        Expected: ValidationError "Active battle cannot be moved"
        """

    async def test_cannot_move_completed_battle():
        """Test cannot move COMPLETED battle.

        Setup: Battle with status=COMPLETED
        Expected: ValidationError "Completed battles cannot be moved"
        """

    async def test_cannot_move_to_locked_position():
        """Test cannot move battle to position 1 (locked).

        Setup: Try new_position=1
        Expected: ValidationError "Cannot move battle to a locked position"
        """

    async def test_battle_not_found():
        """Test raises error for non-existent battle.

        Setup: Random UUID not in database
        Expected: ValidationError "Battle not found"
        """

    async def test_position_clamped_to_max():
        """Test position clamped to max available.

        Setup: 5 battles, try to move to position 10
        Expected: Moved to position 5 (max)
        """

    async def test_reindex_after_move():
        """Test sequence_order reindexed after move.

        Setup: Move battle, verify all battles have sequential order
        Expected: No gaps in sequence_order (1, 2, 3, 4, 5)
        """
```

---

## 4. Implementation Order

1. **Update test fixtures** (both files)
   - Add category_repo mock fixture
   - Add tiebreak_service_with_category_repo fixture
   - Add pool_repo mock fixture

2. **Add TiebreakService tests** (test_tiebreak_service.py)
   - TestDetectAndCreatePreselectionTiebreak class (6 tests)
   - TestDetectAndCreatePoolWinnerTiebreaks class (6 tests)

3. **Add BattleService tests** (test_battle_service.py)
   - TestGenerateInterleavedPreselectionBattles class (6 tests)
   - TestReorderBattle class (8 tests)

4. **Run tests and verify coverage**
   - All 26 new tests should pass
   - Coverage for tiebreak_service.py and battle_service.py should improve

---

## 5. Expected Outcome

**New Tests:** 26 tests
**Files Modified:** 2 (test_tiebreak_service.py, test_battle_service.py)
**Expected Coverage Improvement:**
- tiebreak_service.py: 60% → ~85%
- battle_service.py: 60% → ~85%

---

## 6. Risk Analysis

### Risk 1: Mock Complexity
**Concern:** Pool repository mocking for tiebreak tests
**Mitigation:** Use patch decorator to mock PoolRepository instantiation inside service methods

### Risk 2: Async Test Complexity
**Concern:** Tests involve multiple async operations
**Mitigation:** Use existing async test patterns in codebase, ensure proper await usage

---

## 7. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved test approach
- [ ] Ready for /implement-feature
