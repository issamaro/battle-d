# Implementation Plan: Service Integration Tests

**Date:** 2025-12-07
**Phase:** 3.5 (Integration Testing Implementation)
**Status:** Ready for Implementation

---

## Summary

Add service integration tests following the updated methodology. Tests use real repositories and database to catch bugs like invalid enum references, signature mismatches, and relationship issues.

---

## Coverage Analysis

### Current State

| Service | Coverage | Statements | Missing | Priority |
|---------|----------|------------|---------|----------|
| `dancer_service.py` | **0%** | 72 | 72 | Critical |
| `performer_service.py` | **0%** | 56 | 56 | Critical |
| `tournament_service.py` | **32%** | 75 | 51 | Critical |
| `event_service.py` | **78%** | 130 | 28 | High |
| `battle_results_encoding_service.py` | **72%** | 119 | 33 | Medium |
| `battle_service.py` | **94%** | 179 | 10 | Low |
| `tiebreak_service.py` | **88%** | 137 | 16 | Low |
| `pool_service.py` | **96%** | 82 | 3 | Low |

### Target State

All services at **90%+ coverage** with **integration tests** (not mocked unit tests).

---

## Implementation Order

### Phase 1: Critical Services (0% Coverage)

#### 1.1 `dancer_service.py` - 0% → 90%+

**Methods to Test:**

| Method | Lines | Test Scenarios |
|--------|-------|----------------|
| `create_dancer()` | 28-86 | Success, duplicate email, age < 10, age > 100, IntegrityError |
| `update_dancer()` | 88-163 | Success, not found, email change, age validation |
| `search_dancers()` | 165-177 | With query, empty query, no results |
| `get_dancer_by_id()` | 179-194 | Success, not found |

**Test File:** `tests/test_dancer_service_integration.py`

**Fixtures Needed:**
- `async_session_maker` (exists in conftest.py)
- Helper to create test dancers

**Estimated Tests:** 12-15 tests

---

#### 1.2 `performer_service.py` - 0% → 90%+

**Methods to Test:**

| Method | Lines | Test Scenarios |
|--------|-------|----------------|
| `register_performer()` | 38-140 | Solo success, duo success, category not found, wrong tournament, solo in duo category, duo in solo category, dancer not found, already registered, partner not found, partner already registered, self as partner |
| `unregister_performer()` | 142-164 | Success, not found |
| `get_performers_by_category()` | 166-175 | With performers, empty |
| `get_performers_by_tournament()` | 177-186 | With performers, empty |

**Test File:** `tests/test_performer_service_integration.py`

**Fixtures Needed:**
- Test tournament
- Test categories (solo + duo)
- Test dancers

**Estimated Tests:** 15-18 tests

---

#### 1.3 `tournament_service.py` - 32% → 90%+

**Untested Lines:** 81-117, 134-138, 153-183, 199-247

**Methods to Test:**

| Method | Lines | Test Scenarios |
|--------|-------|----------------|
| `advance_tournament_phase()` | 57-117 | REGISTRATION → PRESELECTION success, validation failure, another tournament active, auto-activation |
| `get_phase_validation()` | 119-138 | Success for each phase, tournament not found |
| `_validate_phase_advance()` | 140-183 | Each phase transition validation |
| `_execute_phase_transition_hooks()` | 185-247 | REGISTRATION hook (generates battles), PRESELECTION hook (creates pools + battles), POOLS hook (generates finals) |

**Test File:** `tests/test_tournament_service_integration.py`

**Fixtures Needed:**
- Test tournament in each phase
- Categories with performers
- Battle service mock (for hook tests) OR full integration

**Critical Tests:**
1. `test_advance_from_registration_generates_preselection_battles`
2. `test_advance_from_preselection_creates_pools_and_battles`
3. `test_advance_from_pools_generates_finals`
4. `test_cannot_advance_with_validation_errors`
5. `test_auto_activates_tournament_on_first_advance`

**Estimated Tests:** 15-20 tests

---

### Phase 2: High Priority Services

#### 2.1 `event_service.py` - 78% → 90%+

**Untested Lines:** 135-142, 208, 221, 239-254, 275, 293-298

**Methods to Test:**

| Method | Lines | Test Scenarios |
|--------|-------|----------------|
| `get_command_center_context()` | 103-161 | With current battle, without current battle, with queue, empty queue |
| `_get_battle_queue()` | 210-264 | With battles, with category filter, empty |
| `_get_performer_display_name()` | 280-298 | Solo performer, duo performer, null performer |

**Known Bugs to Fix First:**
- Lines 137-142: `performer1_id`/`performer2_id` don't exist on Battle model
- Line 230: `battle_order` should be `sequence_order`

**Test File:** `tests/test_event_service_integration.py`

**Estimated Tests:** 10-12 tests

---

### Phase 3: Medium Priority Services

#### 3.1 `battle_results_encoding_service.py` - 72% → 90%+

**Untested Lines:** 130-139, 181, 185, 240-249, 279, 283, 333, 337, 344, 396, 403-421

Most untested lines are edge cases in existing tested methods. Add:
- Error path tests for invalid battle states
- Edge cases for score validation

**Test File:** Extend `tests/test_battle_results_encoding_service.py`

**Estimated Tests:** 8-10 additional tests

---

### Phase 4: Low Priority Services (Already High Coverage)

| Service | Current | Target | Tests Needed |
|---------|---------|--------|--------------|
| `battle_service.py` | 94% | 95%+ | 2-3 |
| `tiebreak_service.py` | 88% | 90%+ | 3-4 |
| `pool_service.py` | 96% | 98%+ | 1-2 |

---

## Test Infrastructure

### Fixtures to Create/Verify

```python
# tests/conftest.py additions

@pytest.fixture
async def create_test_tournament(async_session_maker):
    """Create a test tournament with default settings."""
    async def _create(name="Test Tournament", phase=TournamentPhase.REGISTRATION):
        async with async_session_maker() as session:
            tournament_repo = TournamentRepository(session)
            tournament = Tournament(
                name=name,
                date=date.today(),
                location="Test Location",
                phase=phase,
                status=TournamentStatus.CREATED,
            )
            # Use repo create method
            ...
    return _create


@pytest.fixture
async def create_test_category(async_session_maker, create_test_tournament):
    """Create a test category in a tournament."""
    async def _create(tournament_id, name="Test Category", is_duo=False, groups_ideal=2):
        ...
    return _create


@pytest.fixture
async def create_test_dancer(async_session_maker):
    """Create a test dancer with unique email."""
    async def _create(email=None, first_name="Test", last_name="Dancer"):
        if email is None:
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        ...
    return _create


@pytest.fixture
async def create_test_performer(async_session_maker, create_test_dancer):
    """Register a test performer in a category."""
    async def _create(tournament_id, category_id, dancer_id=None):
        ...
    return _create
```

---

## Test File Structure

```
tests/
├── conftest.py                              # Add fixtures
├── test_dancer_service_integration.py       # NEW: 12-15 tests
├── test_performer_service_integration.py    # NEW: 15-18 tests
├── test_tournament_service_integration.py   # NEW: 15-20 tests
├── test_event_service_integration.py        # NEW: 10-12 tests
├── test_battle_results_encoding_service.py  # EXTEND: 8-10 tests
├── test_battle_service.py                   # Existing (mostly good)
├── test_tiebreak_service.py                 # Minor additions
├── test_pool_service.py                     # Minor additions
└── ...
```

---

## Implementation Steps

### Step 1: Fix Known Bugs First

Before writing tests, fix bugs that would cause test failures:

1. **event_service.py lines 137-142, 241-246:**
   - `performer1_id` / `performer2_id` → use `performers` list

2. **event_service.py line 230:**
   - `battle_order` → `sequence_order`

### Step 2: Create Test Fixtures

Add factory fixtures to `conftest.py` for:
- Tournaments (in various phases)
- Categories (solo and duo)
- Dancers
- Performers

### Step 3: Write Integration Tests (Priority Order)

1. `test_dancer_service_integration.py` (~1 hour)
2. `test_performer_service_integration.py` (~1.5 hours)
3. `test_tournament_service_integration.py` (~2 hours)
4. `test_event_service_integration.py` (~1 hour)
5. Extend existing test files (~1 hour)

### Step 4: Run Full Test Suite

```bash
pytest --cov=app/services --cov-report=term-missing
```

Target: All services at 90%+ coverage.

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Fix event_service.py bugs | 30 min |
| Create/update test fixtures | 45 min |
| test_dancer_service_integration.py | 1 hour |
| test_performer_service_integration.py | 1.5 hours |
| test_tournament_service_integration.py | 2 hours |
| test_event_service_integration.py | 1 hour |
| Extend existing test files | 1 hour |
| **Total** | ~8 hours |

---

## Success Criteria

| Service | Current | Target | Status |
|---------|---------|--------|--------|
| dancer_service.py | 0% | 90%+ | Pending |
| performer_service.py | 0% | 90%+ | Pending |
| tournament_service.py | 32% | 90%+ | Pending |
| event_service.py | 78% | 90%+ | Pending |
| battle_results_encoding_service.py | 72% | 90%+ | Pending |
| Overall Services | 68% | 90%+ | Pending |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Test database pollution | Use transaction rollback or clean fixtures |
| Circular dependencies (tournament ↔ battle service) | Use dependency injection, test in isolation where possible |
| Slow tests | Keep integration tests focused, parallelize where possible |

---

## Quality Gate

Before marking complete:
- [ ] All services at 90%+ coverage
- [ ] All new tests use real repositories (not mocks)
- [ ] All tests create real data with real enum values
- [ ] No regressions in existing tests
- [ ] event_service.py bugs fixed

