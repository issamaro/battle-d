# Feature Specification: Integration Testing Methodology Improvement

**Date:** 2025-12-07
**Status:** Awaiting User Confirmation

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Methodology Gap Analysis](#3-methodology-gap-analysis)
4. [Root Cause Analysis](#4-root-cause-analysis)
5. [Business Rules & Acceptance Criteria](#5-business-rules--acceptance-criteria)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

**The development methodology actively encourages testing patterns that hide production bugs.**

Production bugs like `BattleStatus.IN_PROGRESS` (doesn't exist) and `BaseRepository.create()` signature mismatches pass all tests because the methodology prescribes mocked unit tests that validate test setup rather than actual code behavior.

---

## 2. Executive Summary

### Scope
This is a **methodology improvement**, not just a "add more tests" task. The slash commands, TESTING.md, and README.md methodology all need updating.

### What's Broken 🚨

| Issue | Location | Impact |
|-------|----------|--------|
| `/implement-feature` shows mocked service tests | `.claude/commands/implement-feature.md:685-699` | Developers follow the pattern, bugs slip through |
| TESTING.md best practice: "Mock external services" | `TESTING.md:556` | Encourages over-mocking |
| No "service integration test" category exists | `TESTING.md` | Gap between unit tests and route tests |
| `/verify-feature` doesn't require DB integration tests | `.claude/commands/verify-feature.md` | Quality gate doesn't catch integration bugs |
| README.md test examples use mocks | `.claude/README.md:2496-2563` | Methodology teaches wrong pattern |

### What Works ✅

| Feature | Status |
|---------|--------|
| Repository integration tests pattern | Exists in `test_repositories.py` |
| Route integration tests with AsyncClient | Documented in TESTING.md |
| Test database setup | Working in conftest.py |

### Key Gap
**Missing**: Service Integration Tests - tests that use real repositories with real DB, but without HTTP layer.

```
Current Test Pyramid (BROKEN):
┌─────────────────────────┐
│   Route Integration     │  ← Uses mocked services OR full HTTP
│   (test_*_routes.py)    │
├─────────────────────────┤
│   Service Unit Tests    │  ← Uses mocked repos → HIDES BUGS
│   (test_*_service.py)   │
├─────────────────────────┤
│   Repository Integration│  ← Uses real DB → CATCHES BUGS
│   (test_repositories.py)│
└─────────────────────────┘

Desired Test Pyramid (FIXED):
┌─────────────────────────┐
│   Route Integration     │  ← Full HTTP stack
├─────────────────────────┤
│ **Service Integration** │  ← NEW: Real repos, real DB
├─────────────────────────┤
│   Service Unit Tests    │  ← Mocked repos (for isolated logic)
├─────────────────────────┤
│   Repository Integration│  ← Real DB
└─────────────────────────┘
```

---

## 3. Methodology Gap Analysis

### 3.1 Current Methodology Teaches Wrong Pattern

**Location:** `.claude/commands/implement-feature.md` Step 13.1

**Current Pattern (WRONG):**
```python
@pytest.mark.asyncio
async def test_filter_battles_by_encoding_status_pending(battle_service, battle_repo):
    """Test filtering battles by pending encoding status."""
    # Setup - MOCK THE REPO!
    battle_repo.get_by_filters.return_value = [mock_battle_1, mock_battle_2]

    # Execute
    result = await battle_service.filter_battles(encoding_status='pending')

    # Verify
    assert len(result) == 2
    battle_repo.get_by_filters.assert_called_once_with(...)
```

**Why It's Wrong:** This tests that the service CALLS the repo, not that the integration WORKS. If `mock_battle_1` uses `BattleStatus.IN_PROGRESS` (which doesn't exist), the test passes.

**Desired Pattern (CORRECT):**
```python
@pytest.mark.asyncio
async def test_filter_battles_by_encoding_status_pending(async_session):
    """Integration test: filter battles with real DB."""
    # Setup - USE REAL REPOS
    battle_repo = BattleRepository(async_session)
    category_repo = CategoryRepository(async_session)
    service = BattleService(battle_repo, category_repo)

    # Create REAL test data with REAL enum values
    battle = Battle(
        status=BattleStatus.ACTIVE,  # If this doesn't exist, test fails!
        ...
    )
    await battle_repo.create(battle)

    # Execute against REAL DB
    result = await service.filter_battles(encoding_status='pending')

    # Verify ACTUAL behavior
    assert len(result) == expected_count
```

### 3.2 TESTING.md Gaps

**Location:** `TESTING.md`

**Missing Section:** "Service Integration Tests"

**Current Categories:**
- Unit Tests (Phase 0)
- Integration Tests (Planned - Phase 1+) - but only mentions "Database operations"
- HTMX Interaction Tests
- End-to-End Tests (Planned - Phase 4+)

**Missing Category:**
```markdown
### Service Integration Tests

Service integration tests verify that services work correctly with real
repositories and the actual database. Unlike unit tests with mocked repos,
these catch bugs like:
- Invalid enum references (BattleStatus.IN_PROGRESS)
- Repository method signature mismatches
- Lazy loading issues
- Transaction/session management bugs

**Pattern:**
- Use real async_session_maker()
- Instantiate real repositories
- Test service methods with real data
- Verify database state after operations
```

### 3.3 Quality Gate Gaps

**Location:** `.claude/commands/verify-feature.md`

**Current Quality Gate:**
```markdown
**Automated Testing:**
- [ ] All existing tests pass (no regressions)
- [ ] All new tests pass
- [ ] Coverage meets targets (≥90% overall, ≥95% new code)
```

**Missing Quality Gate:**
```markdown
**Integration Testing:**
- [ ] Service integration tests exist for new service methods
- [ ] Integration tests use real repositories (not mocks)
- [ ] Integration tests verify actual database state
```

### 3.4 `/implement-feature` Quality Gate

**Location:** `.claude/commands/implement-feature.md` line 784

**Missing Checkbox:**
```markdown
- [ ] Service integration tests written (real repos, real DB)
```

---

## 4. Root Cause Analysis

### 4.1 Why `BattleStatus.IN_PROGRESS` Bug Wasn't Caught

**In test_event_service.py:**
```python
# The test mocks the entire repo
battle_repo.get_by_category.return_value = []  # Empty list!

# So this code never executes with REAL data:
in_progress = [b for b in all_battles if b.status == BattleStatus.IN_PROGRESS]
#                                                     ^^^^^^^^^^^^^^^^
#                                                     Never validated!
```

**The Problem:** When you mock the repo to return an empty list, the filtering code runs but never validates that `BattleStatus.IN_PROGRESS` is a real enum value.

### 4.2 Why `BaseRepository.create()` Bug Wasn't Caught

**In service tests:**
```python
# Service creates Battle with performers
battle = Battle(...)
battle.performers = [performer1, performer2]

# Test mocks the repo.create() call
battle_repo.create.return_value = battle  # Just returns input!
```

**The Problem:** The mock doesn't validate that `create()` can accept a model instance. The real `BaseRepository.create()` only accepts `**kwargs`.

### 4.3 Pattern: Tests Validate Test Setup, Not Code

When tests mock all dependencies, they become tests of:
- "Did I set up the mock correctly?"
- "Did the code call the mock?"

Instead of:
- "Does the code work with real components?"
- "Are all values valid?"

---

## 5. Business Rules & Acceptance Criteria

### BR-TEST-001: Service Integration Test Requirement

**Business Rule:**
> All new service methods that interact with repositories MUST have integration tests that use real repositories and the test database.

**Acceptance Criteria:**
```gherkin
Feature: Service Integration Tests Prevent Production Bugs
  As a developer
  I want service integration tests with real repositories
  So that integration bugs are caught before production

Scenario: Invalid enum reference caught by tests
  Given I write code using BattleStatus.INVALID_VALUE
  When I run the test suite
  Then the tests fail with a clear error message
  And the bug never reaches production

Scenario: Repository signature mismatch caught
  Given I call a repository method with wrong arguments
  When I run the integration tests
  Then the tests fail because real repository is used
  And the bug never reaches production

Scenario: Phase transition tested with real data
  Given a tournament in REGISTRATION phase in the test database
  When I run the phase advance integration test
  Then it tests the actual advance_tournament_phase() method
  And catches any bugs in the transition logic
```

### BR-TEST-002: Methodology Documentation Update

**Business Rule:**
> The development methodology (slash commands, README.md, TESTING.md) MUST prescribe service integration tests as the primary test pattern for services.

**Acceptance Criteria:**
```gherkin
Scenario: /implement-feature prescribes integration tests
  Given a developer runs /implement-feature
  When they reach the testing section
  Then they see integration test examples with real repos
  And the quality gate requires integration tests

Scenario: /verify-feature checks for integration tests
  Given a developer runs /verify-feature
  When they review the quality gate
  Then they see checkbox for service integration tests
  And cannot pass without integration tests

Scenario: TESTING.md documents service integration pattern
  Given a developer reads TESTING.md
  When they look for service testing guidance
  Then they find "Service Integration Tests" section
  And the examples use real repositories
```

### BR-TEST-003: Test Pyramid Balance

**Business Rule:**
> Each service method should have:
> 1. Integration test (primary) - real repos, real DB
> 2. Unit test (secondary) - only for complex isolated logic

**Acceptance Criteria:**
```gherkin
Scenario: Developer writes service tests
  Given a developer creates a new service method
  When they write tests following the methodology
  Then they write an integration test first (required)
  And optionally write unit test for complex logic (optional)
  And the integration test is the gate for correctness
```

---

## 6. Implementation Recommendations

### 6.1 Critical (Methodology Changes - Before More Tests)

| Task | File | Change |
|------|------|--------|
| 1. Update `/implement-feature` | `.claude/commands/implement-feature.md` | Replace mocked test example with integration test example |
| 2. Update `/verify-feature` | `.claude/commands/verify-feature.md` | Add integration test quality gate |
| 3. Add service integration section | `TESTING.md` | New section with patterns and examples |
| 4. Update README.md test examples | `.claude/README.md` | Change example patterns |

### 6.2 Recommended (Add Missing Tests)

| Service | Coverage | Priority |
|---------|----------|----------|
| `tournament_service.py` | 32% | Critical - phase transitions |
| `event_service.py` | 78% | Critical - current battle lookup |
| `dancer_service.py` | 0% | High - no tests at all |
| `performer_service.py` | 0% | High - no tests at all |

### 6.3 Nice-to-Have (Future)

| Task | Benefit |
|------|---------|
| Add mypy for static type checking | Catch enum errors at compile time |
| Add pre-commit hooks | Run tests before commits |
| CI/CD test gate | Block deploys on test failures |

---

## 7. Appendix: Reference Material

### 7.1 Files To Modify (Methodology)

| File | Section | Change Type |
|------|---------|-------------|
| `.claude/commands/implement-feature.md` | Step 13 | Update test examples |
| `.claude/commands/implement-feature.md` | Quality Gate | Add integration test checkbox |
| `.claude/commands/verify-feature.md` | Quality Gate | Add integration test checkbox |
| `TESTING.md` | Test Categories | Add new section |
| `.claude/README.md` | Test Templates | Update examples |

### 7.2 Test Files With Issues

| File | Problem |
|------|---------|
| `test_event_service.py` | 100% mocked, misses real bugs |
| `test_battle_results_encoding_service.py` | Over-mocked |
| `test_battle_service.py` | Over-mocked |

### 7.3 Good Example: test_repositories.py

This file shows the CORRECT pattern we should follow:
```python
@pytest.mark.asyncio
async def test_battle_repository_create_with_instance(
    async_session_maker,
    create_test_tournament,
    create_test_category,
    create_test_performers
):
    """Test creating a battle with a model instance (not kwargs)."""
    async with async_session_maker() as session:
        # Real repositories
        battle_repo = BattleRepository(session)

        # Real model with real enum
        battle = Battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            status=BattleStatus.PENDING,  # Real enum!
            battle_type=BattleType.PRESELECTION,
        )
        battle.performers = performers  # Real relationship!

        # Real database operation
        created = await battle_repo.create(battle)

        # Verify real state
        assert created.id is not None
```

### 7.4 Current Coverage Gaps

| File | Coverage | Lines Uncovered |
|------|----------|-----------------|
| `tournament_service.py` | 32% | Phase transitions (81-117, 153-183) |
| `event_service.py` | 78% | Current battle lookup (135-142) |
| `registration.py` router | 16% | Most endpoints |
| `battles.py` router | 22% | Battle management |
| `phases.py` router | 40% | Phase advance |
| `dancer_service.py` | 0% | Everything |
| `performer_service.py` | 0% | Everything |

### 7.5 Open Questions

- **Q:** Should we require integration tests for ALL service methods?
  - **Recommendation:** Yes, for any method that touches the database

- **Q:** When are mocked unit tests appropriate?
  - **Recommendation:** Only for pure logic that doesn't involve repositories (e.g., calculation functions)

- **Q:** Should we add a CI gate?
  - **Recommendation:** Yes, after methodology is fixed

---

## 8. User Confirmation Required

Before proceeding with implementation, please confirm:

1. **Scope:** Is this the right framing - fixing the methodology, not just adding tests?

2. **Priority:**
   - Option A: Fix methodology first, then add tests following new patterns
   - Option B: Add critical tests now, fix methodology later

3. **Acceptance:** Do the BDD scenarios match your vision for preventing future bugs?

