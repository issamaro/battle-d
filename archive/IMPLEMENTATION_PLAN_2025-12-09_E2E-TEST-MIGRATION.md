# Implementation Plan: E2E Test Migration with Methodology Compliance

**Date:** 2025-12-09
**Status:** Ready for Implementation
**Based on:** workbench/FEATURE_SPEC_2025-12-09_E2E-TEST-MIGRATION.md

---

## 1. Summary

**Feature:** Migrate 143 E2E tests to Phase 3.8 methodology compliance and add ~14 new tests for coverage gaps.

**Approach:**
1. Add Gherkin docstrings with "Validates:" references to ALL E2E tests
2. Selectively migrate sync tests to async pattern ONLY where they use `asyncio.get_event_loop().run_until_complete()` (fixture-dependent tests)
3. Keep sync tests for HTTP-only tests (access patterns, role checks, 404s)
4. Create new async E2E tests for identified coverage gaps

---

## 2. Affected Files

### Test Files to Modify

| File | Tests | Action | Migration Type |
|------|-------|--------|----------------|
| tests/e2e/test_admin.py | 37 | Add Gherkin | Selective async (3 tests use fixtures) |
| tests/e2e/test_registration.py | 41 | Add Gherkin + async | Most tests use `run_until_complete()` |
| tests/e2e/test_dancers.py | 21 | Add Gherkin | Selective async |
| tests/e2e/test_event_mode.py | 17 | Add Gherkin | Keep sync (no fixture data) |
| tests/e2e/test_tournament_management.py | 15 | Add Gherkin + async | Uses fixtures |
| tests/e2e/test_htmx_interactions.py | 10 | Add Gherkin + async | Uses fixtures |
| tests/e2e/test_session_isolation_fix.py | 2 | Add Gherkin | Already async |

### Test Files to Create

| File | New Tests | Purpose |
|------|-----------|---------|
| tests/e2e/test_event_mode_async.py | ~7 | Add gap tests (encoding, validation) |
| tests/e2e/test_registration.py | ~4 | Add gap tests (duo validation) |
| tests/e2e/test_admin.py | ~3 | Add gap tests (edit role lifecycle) |

### Infrastructure Files (No Changes Needed)

- `tests/e2e/async_conftest.py` - Already complete with all needed fixtures
- `tests/e2e/conftest.py` - Keep for sync tests
- `tests/e2e/__init__.py` - Already has helpers

### Documentation Files to Update

| File | Change |
|------|--------|
| TESTING.md | Add test-to-requirement mapping table after migration |

---

## 3. Test Migration Patterns

### 3.1 Pattern 1: Sync Tests (No Fixture Data) - Keep Sync, Add Docstring Only

**Current Pattern:**
```python
def test_battle_list_loads(self, staff_client):
    """GET /battles loads battle list page."""
    response = staff_client.get("/battles")
    assert_status_ok(response)
```

**Target Pattern:**
```python
def test_battle_list_loads(self, staff_client):
    """GET /battles loads battle list page.

    Validates: DOMAIN_MODEL.md Battle entity access
    Gherkin:
        Given I am authenticated as staff
        When I navigate to /battles
        Then the page loads successfully (200)
    """
    # Given (authenticated via staff_client fixture)
    # When
    response = staff_client.get("/battles")

    # Then
    assert_status_ok(response)
```

**Applicable to:**
- All access pattern tests (requires_auth, requires_admin, etc.)
- All 404 tests (nonexistent_returns_404)
- Tests that don't need pre-created data

### 3.2 Pattern 2: Tests Using `run_until_complete()` - Convert to Async

**Current Pattern:**
```python
def test_registration_page_loads_with_data(self, staff_client, create_e2e_tournament):
    """GET /registration/{t_id}/{c_id} loads with valid tournament/category."""
    import asyncio
    data = asyncio.get_event_loop().run_until_complete(
        create_e2e_tournament(num_categories=1, performers_per_category=0)
    )
    tournament = data["tournament"]
    category = data["categories"][0]

    response = staff_client.get(f"/registration/{tournament.id}/{category.id}")
    assert_status_ok(response)
```

**Target Pattern:**
```python
@pytest.mark.asyncio
async def test_registration_page_loads_with_data(
    self,
    async_client_factory,
    create_async_tournament_scenario,
):
    """GET /registration/{t_id}/{c_id} loads with valid tournament/category.

    Validates: FEATURE_SPEC_2025-12-08_E2E-TESTING.md Scenario "Load registration page"
    Gherkin:
        Given a tournament in REGISTRATION phase with 1 category
        When I navigate to /registration/{tournament_id}/{category_id}
        Then the page loads successfully (200)
        And I see the category name
    """
    # Given
    data = await create_async_tournament_scenario(
        num_categories=1,
        performers_per_category=0
    )
    tournament = data["tournament"]
    category = data["categories"][0]

    # When
    async with async_client_factory("staff") as client:
        response = await client.get(f"/registration/{tournament.id}/{category.id}")

    # Then
    assert response.status_code == 200
    assert category.name in response.text
```

**Applicable to:**
- All tests using `asyncio.get_event_loop().run_until_complete()`
- All tests that need fixture-created data visible to HTTP routes

### 3.3 Pattern 3: New Gap Coverage Tests - Async with Full Compliance

**Example New Test:**
```python
@pytest.mark.asyncio
async def test_encode_preselection_scores_success(
    self,
    async_e2e_session,
    async_client_factory,
    create_async_tournament_scenario,
    create_async_battle,
):
    """Staff can encode preselection scores for all performers.

    Validates: VALIDATION_RULES.md Preselection Battle Encoding
    Gherkin:
        Given a battle is ACTIVE with PRESELECTION phase
        And I am authenticated as Staff
        When I submit valid scores for all performers
        Then the battle status changes to COMPLETED
        And each performer.preselection_score is updated
    """
    # Given
    data = await create_async_tournament_scenario(
        phase=TournamentPhase.PRESELECTION,
        num_categories=1,
        performers_per_category=4,
    )
    category = data["categories"][0]
    performers = data["performers"]

    battle = await create_async_battle(
        category_id=category.id,
        phase=BattlePhase.PRESELECTION,
        performer_ids=[p.id for p in performers],
        status=BattleStatus.ACTIVE,
    )

    # Prepare scores data
    scores_data = {
        f"scores[{p.id}]": "8.5" for p in performers
    }

    # When
    async with async_client_factory("staff") as client:
        response = await client.post(
            f"/battles/{battle.id}/encode",
            data=scores_data,
            follow_redirects=False,
        )

    # Then
    assert response.status_code == 303  # Redirect on success

    # Verify battle completed
    from app.repositories.battle import BattleRepository
    battle_repo = BattleRepository(async_e2e_session)
    updated_battle = await battle_repo.get_by_id(battle.id)
    assert updated_battle.status == BattleStatus.COMPLETED
```

---

## 4. File-by-File Migration Plan

### 4.1 test_admin.py (37 tests)

**Analysis:**
- 34 tests are HTTP-only (access patterns, 404s, form submissions) - **Keep sync**
- 3 tests use `asyncio.get_event_loop().run_until_complete()` - **Convert to async**

**Tests to Convert to Async:**
1. `test_fix_active_missing_selection` (line 343-362)
2. Any others using `create_e2e_tournament`

**Action Plan:**
1. Add Gherkin docstrings to all 37 tests
2. Convert fixture-dependent tests to async
3. Keep remaining tests as sync with authenticated clients

**Reference Specs for Docstrings:**
- `DOMAIN_MODEL.md` User entity
- `VALIDATION_RULES.md` Magic Link Authentication

### 4.2 test_registration.py (41 tests)

**Analysis:**
- ~30 tests use `asyncio.get_event_loop().run_until_complete()` - **Convert to async**
- ~11 tests are HTTP-only - **Keep sync**

**Action Plan:**
1. Add Gherkin docstrings to all 41 tests
2. Convert all tests using `run_until_complete()` to async pattern
3. Keep access pattern tests as sync

**Reference Specs for Docstrings:**
- `DOMAIN_MODEL.md` Performer entity
- `VALIDATION_RULES.md` Performer Registration Validation
- `VALIDATION_RULES.md` One Dancer Per Tournament Rule
- `VALIDATION_RULES.md` Duo Registration Validation

### 4.3 test_dancers.py (21 tests)

**Analysis:**
- Most tests create data via HTTP POST - **Keep sync**
- Review for fixture usage

**Action Plan:**
1. Add Gherkin docstrings to all 21 tests
2. Selective async conversion if needed

**Reference Specs for Docstrings:**
- `DOMAIN_MODEL.md` Dancer entity
- `VALIDATION_RULES.md` UI Field Validation

### 4.4 test_event_mode.py (17 tests)

**Analysis:**
- All tests are HTTP-only access patterns - **Keep sync**
- No fixture data used (explicitly noted in comments)

**Action Plan:**
1. Add Gherkin docstrings to all 17 tests
2. Keep all tests sync

**Reference Specs for Docstrings:**
- `DOMAIN_MODEL.md` Battle entity
- `VALIDATION_RULES.md` Battle Encoding Validation

### 4.5 test_tournament_management.py (15 tests)

**Analysis:**
- Review for fixture usage

**Action Plan:**
1. Add Gherkin docstrings to all 15 tests
2. Convert fixture-dependent tests to async

**Reference Specs for Docstrings:**
- `DOMAIN_MODEL.md` Tournament entity
- `VALIDATION_RULES.md` Phase Transition Validation

### 4.6 test_htmx_interactions.py (10 tests)

**Analysis:**
- HTMX-specific tests
- Review for fixture usage

**Action Plan:**
1. Add Gherkin docstrings to all 10 tests
2. Convert fixture-dependent tests to async

**Reference Specs for Docstrings:**
- `FRONTEND.md` HTMX Patterns

### 4.7 test_session_isolation_fix.py (2 tests)

**Analysis:**
- Already async, lacks Gherkin docstrings

**Action Plan:**
1. Add Gherkin docstrings to both tests

---

## 5. New Gap Coverage Tests

### 5.1 Event Mode Gap Tests (Add to test_event_mode_async.py)

| Test Name | Validates | Priority |
|-----------|-----------|----------|
| test_encode_preselection_scores_success | VALIDATION_RULES.md Preselection | Critical |
| test_encode_preselection_validation_error | VALIDATION_RULES.md Score Range | Critical |
| test_encode_pool_winner_success | VALIDATION_RULES.md Pool Battle | Critical |
| test_encode_pool_draw_success | VALIDATION_RULES.md Pool Battle | Critical |
| test_encode_tiebreak_no_draw_allowed | VALIDATION_RULES.md Tiebreak | High |
| test_validation_error_preserves_form | UX requirement | High |
| test_progress_bar_updates_after_encode | UX requirement | Medium |

### 5.2 Registration Gap Tests (Add to test_registration.py)

| Test Name | Validates | Priority |
|-----------|-----------|----------|
| test_duo_partner_mutual_linking | VALIDATION_RULES.md Duo Validation | Critical |
| test_duo_same_dancer_rejected | VALIDATION_RULES.md Duo Validation | High |
| test_category_minimum_performers_warning | VALIDATION_RULES.md Min Performers | Medium |
| test_unregister_performer_success | Performer lifecycle | Medium |

### 5.3 Admin Gap Tests (Add to test_admin.py)

| Test Name | Validates | Priority |
|-----------|-----------|----------|
| test_edit_user_role_success | User management | High |
| test_edit_user_preserves_email | User management | Medium |
| test_user_lifecycle_create_login_delete | Integration | Medium |

---

## 6. Technical POC

**Status:** Not required

**Reason:**
- Async E2E pattern already proven in `test_event_mode_async.py` (8 tests passing)
- Session sharing via dependency override is established
- `async_conftest.py` fixtures are production-ready
- No new technical patterns needed, just applying existing patterns to more tests

---

## 7. Testing Plan

### Test Execution Strategy

**Phase 1: Migrate Existing Tests**
1. Migrate one file at a time
2. Run tests after each file migration
3. Ensure no regressions

**Phase 2: Add New Tests**
1. Add gap coverage tests
2. Run full E2E suite
3. Verify all tests pass

**Commands:**
```bash
# Run specific E2E test file
.venv/bin/python -m pytest tests/e2e/test_admin.py -v

# Run all E2E tests
.venv/bin/python -m pytest tests/e2e/ -v

# Run with coverage
.venv/bin/python -m pytest tests/e2e/ -v --cov=app --cov-report=term-missing
```

### Verification Checklist

**Per-File Verification:**
- [ ] All tests have Gherkin docstring
- [ ] All tests have "Validates:" reference
- [ ] Tests using fixtures converted to async
- [ ] Tests pass

**Global Verification:**
- [ ] All 151+ tests pass
- [ ] No regressions in existing functionality
- [ ] New gap tests cover identified scenarios
- [ ] Test-to-requirement mapping created

---

## 8. Risk Analysis

### Risk 1: Session Isolation in Partially Migrated Tests
**Concern:** Mixing sync and async tests in same file might cause issues
**Likelihood:** Low (pytest handles this)
**Impact:** Medium (test failures)
**Mitigation:**
- Keep sync and async tests in separate test classes
- Import async fixtures explicitly where needed
- Test incrementally

### Risk 2: Breaking Existing Tests During Migration
**Concern:** Refactoring docstrings or signatures might break tests
**Likelihood:** Medium
**Impact:** High (test failures, blocked development)
**Mitigation:**
- Migrate one test class at a time
- Run tests after each class migration
- Use version control to rollback if needed
- DO NOT change test logic, only add docstrings and async wrapper

### Risk 3: Inconsistent Docstring Format
**Concern:** Different developers might write docstrings differently
**Likelihood:** Medium
**Impact:** Low (readability, not functionality)
**Mitigation:**
- Follow exact template from test_event_mode_async.py
- Include "Validates:" on its own line
- Include "Gherkin:" with indented Given/When/Then
- Use # Given / # When / # Then comments in code

### Risk 4: Orphaned "Validates:" References
**Concern:** Tests reference feature-specs that don't exist
**Likelihood:** Medium
**Impact:** Low (misleading documentation)
**Mitigation:**
- Reference existing docs (DOMAIN_MODEL.md, VALIDATION_RULES.md)
- For tests without spec, use "Validates: [Derived] HTTP access pattern"
- Create test-to-requirement mapping to catch orphans

---

## 9. Implementation Order

**Recommended sequence:**

### Phase 1: Migration (Compliance + Selective Async)

| Step | File | Tests | Est. Time |
|------|------|-------|-----------|
| 1 | test_event_mode.py | 17 | Quick (sync only, add docstrings) |
| 2 | test_session_isolation_fix.py | 2 | Quick (add docstrings only) |
| 3 | test_admin.py | 37 | Medium (mostly sync, 3 async) |
| 4 | test_dancers.py | 21 | Medium (review for async needs) |
| 5 | test_tournament_management.py | 15 | Medium (review for async needs) |
| 6 | test_htmx_interactions.py | 10 | Medium (review for async needs) |
| 7 | test_registration.py | 41 | Longer (many async conversions) |

### Phase 2: New Tests (Gap Coverage)

| Step | File | New Tests |
|------|------|-----------|
| 8 | test_event_mode_async.py | ~7 encoding/validation tests |
| 9 | test_registration.py | ~4 duo/capacity tests |
| 10 | test_admin.py | ~3 role lifecycle tests |

### Phase 3: Verification

| Step | Task |
|------|------|
| 11 | Run full E2E test suite |
| 12 | Create test-to-requirement mapping table |
| 13 | Update TESTING.md with mapping |

---

## 10. Docstring Template

**Standard Format for ALL E2E Tests:**

```python
def test_action_scenario(self, client_fixture, ...):
    """One-line description of what the test validates.

    Validates: [DOC_NAME.md] Section or Scenario Name
    Gherkin:
        Given [initial state/context]
        And [additional context if needed]
        When [action taken]
        Then [expected outcome]
        And [additional assertions if needed]
    """
    # Given
    # ... setup code with comments ...

    # When
    response = client.action(...)

    # Then
    assert expected_condition
```

**"Validates:" Reference Options:**
1. `DOMAIN_MODEL.md [Entity] entity` - for entity access tests
2. `VALIDATION_RULES.md [Section Title]` - for validation tests
3. `FRONTEND.md [Component/Pattern]` - for UI tests
4. `[Derived] HTTP access pattern` - for auth/403/404 tests without explicit spec

---

## 11. Open Questions & Answers

- **Q:** Should we merge test_event_mode.py and test_event_mode_async.py?
  - **A:** No. Keep separate. test_event_mode.py has sync access tests, test_event_mode_async.py has async workflow tests.

- **Q:** What about tests that create data via HTTP POST (not fixtures)?
  - **A:** Keep sync. The "selective async" rule only applies to tests using `run_until_complete()` or async fixture factories.

- **Q:** Should we add type hints to test functions?
  - **A:** Not in scope. Focus on docstrings and async migration only.

---

## 12. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order

---

## Summary

This implementation plan migrates 143 E2E tests to Phase 3.8 compliance by:

1. **Adding Gherkin docstrings** with "Validates:" references to ALL tests
2. **Selectively converting to async** only tests that use `run_until_complete()`
3. **Creating ~14 new tests** to fill coverage gaps
4. **Following existing patterns** from test_event_mode_async.py

**No new infrastructure needed** - all fixtures and patterns already exist.

**Estimated scope:** ~157 tests when complete (143 migrated + ~14 new)
