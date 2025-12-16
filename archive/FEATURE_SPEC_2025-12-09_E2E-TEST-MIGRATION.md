# Feature Specification: E2E Test Migration with Methodology Compliance

**Date:** 2025-12-09
**Status:** User Approved - Ready for Technical Design

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

E2E tests (151 tests, 94.7%) lack methodology compliance: no Gherkin docstrings with requirement traceability as defined in Phase 3.8. Additionally, 143 sync tests use a workaround pattern (`asyncio.get_event_loop().run_until_complete()`) that creates session isolation, limiting testability of fixture-created data. This migration will bring all E2E tests to compliance while adding coverage for any missing user flows.

---

## 2. Executive Summary

### Scope
Full migration of E2E tests to Phase 3.8 methodology compliance, including:
1. Add Gherkin docstrings with "Validates:" references to all 143 non-compliant tests
2. Migrate sync tests to async pattern (session sharing)
3. Create new E2E tests for coverage gaps in Event Mode, Registration, Admin, and other areas

### What Works ✅

| Feature | Status | Evidence |
|---------|--------|----------|
| Async E2E pattern established | Production Ready | `tests/e2e/test_event_mode_async.py` (8 tests with Gherkin) |
| Authenticated client fixtures | Production Ready | `tests/e2e/conftest.py` (admin, staff, mc, judge clients) |
| Data factory fixtures | Production Ready | `tests/e2e/async_conftest.py` (tournament scenarios) |
| HTMX test helpers | Production Ready | `tests/e2e/__init__.py` (is_partial_html, htmx_headers) |
| Phase 3.8 methodology defined | Complete | TESTING.md §E2E Test Docstring Standard |

### What's Broken 🚨

| Issue | Type | Affected | Location |
|-------|------|----------|----------|
| No Gherkin docstrings | COMPLIANCE | 143 tests (94.7%) | All test_*.py except test_event_mode_async.py |
| Sync session isolation | TECHNICAL | 143 tests | Uses `asyncio.get_event_loop().run_until_complete()` |
| No "Validates:" field | COMPLIANCE | 143 tests | Cannot trace test → requirement |
| Missing Event Mode coverage | GAP | ~15 scenarios | Battle start/encode/workflow |
| Missing Registration coverage | GAP | ~10 scenarios | Bulk operations, edge cases |
| Missing Admin coverage | GAP | ~8 scenarios | User management workflows |

### Key Business Rules Defined

- **BR-E2E-001:** All E2E tests MUST have Gherkin docstrings (BLOCKING)
- **BR-E2E-002:** All E2E tests MUST reference feature-spec scenarios via "Validates:" field
- **BR-E2E-003:** E2E tests requiring fixture data MUST use async pattern with session sharing
- **BR-E2E-004:** Coverage gaps in critical flows MUST be filled before feature is complete

---

## 3. User Flow Diagram

This diagram shows the E2E test migration workflow:

```
═══════════════════════════════════════════════════════════════
 PHASE 1: MIGRATE EXISTING TESTS (Compliance + Async Pattern)
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  FILE: tests/e2e/test_admin.py (37 tests)               │
  │  ─────────────────────────────────────────────────────── │
  │  CURRENT STATE:                                          │
  │  • ❌ No Gherkin docstrings                             │
  │  • ❌ Sync pattern (session isolation)                  │
  │  • ✅ Good coverage of admin workflows                  │
  │                                                          │
  │  ACTIONS:                                                │
  │  1. Add Gherkin docstring to each test                  │
  │  2. Add "Validates: feature-spec.md Scenario X"         │
  │  3. Convert sync → async where fixture data needed      │
  │  4. Keep sync for tests that create data via HTTP POST  │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  FILE: tests/e2e/test_registration.py (41 tests)        │
  │  ─────────────────────────────────────────────────────── │
  │  CURRENT STATE:                                          │
  │  • ❌ No Gherkin docstrings                             │
  │  • ❌ Sync with run_until_complete() workaround         │
  │  • ⚠️ Session isolation limits testability              │
  │                                                          │
  │  ACTIONS:                                                │
  │  1. Add Gherkin docstrings to all 41 tests              │
  │  2. Convert fixture-dependent tests to async pattern    │
  │  3. Validate against FEATURE_SPEC scenarios             │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  FILE: tests/e2e/test_dancers.py (21 tests)             │
  │  ─────────────────────────────────────────────────────── │
  │  ACTIONS:                                                │
  │  1. Add Gherkin docstrings                              │
  │  2. Migrate to async where needed                       │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  FILE: tests/e2e/test_event_mode.py (17 tests)          │
  │  ─────────────────────────────────────────────────────── │
  │  ACTIONS:                                                │
  │  1. Add Gherkin docstrings                              │
  │  2. Migrate to async (already have async_conftest)      │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  FILE: tests/e2e/test_tournament_management.py (15)     │
  │  FILE: tests/e2e/test_htmx_interactions.py (10)         │
  │  ─────────────────────────────────────────────────────── │
  │  ACTIONS:                                                │
  │  1. Add Gherkin docstrings                              │
  │  2. Migrate to async where fixture data needed          │
  └──────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
 PHASE 2: ADD NEW E2E TESTS (Coverage Gaps)
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  NEW: Event Mode Gap Coverage                           │
  │  ─────────────────────────────────────────────────────── │
  │  Reference: FEATURE_SPEC_2025-12-08_E2E-TESTING.md      │
  │                                                          │
  │  Missing Scenarios:                                      │
  │  • Start a battle (PENDING → ACTIVE)                    │
  │  • Encode preselection scores (all performers)          │
  │  • Encode pool results with winner                      │
  │  • Encode pool results with draw                        │
  │  • Validation error preserves form                      │
  │  • Progress bar updates after encoding                  │
  │  • Battle queue shows next pending                      │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  NEW: Registration Gap Coverage                         │
  │  ─────────────────────────────────────────────────────── │
  │  Missing Scenarios:                                      │
  │  • Bulk dancer registration                             │
  │  • Duplicate dancer rejection                           │
  │  • Category capacity warnings                           │
  │  • Duo partner validation (2v2 categories)              │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  NEW: Admin Gap Coverage                                │
  │  ─────────────────────────────────────────────────────── │
  │  Missing Scenarios:                                      │
  │  • Complete user lifecycle (create → login → delete)    │
  │  • Role assignment and modification                     │
  │  • Magic link generation and validation                 │
  └──────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
 PHASE 3: VERIFY TRACEABILITY
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────┐
  │  VALIDATION: Test-to-Requirement Mapping                │
  │  ─────────────────────────────────────────────────────── │
  │  Per BR-TEST-001 from Phase 3.8:                        │
  │                                                          │
  │  Create mapping table:                                   │
  │  • Gherkin Scenario → Test(s) that validate it         │
  │  • Flag scenarios without tests                         │
  │  • Flag tests without scenarios (scope creep)           │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  QUALITY GATE: All Tests Pass                           │
  │  ─────────────────────────────────────────────────────── │
  │  ✅ 151+ tests passing                                  │
  │  ✅ All E2E tests have Gherkin docstrings               │
  │  ✅ All E2E tests have "Validates:" field               │
  │  ✅ Coverage gaps filled                                │
  │  ✅ No test-to-requirement orphans                      │
  └──────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 E2E Test Docstring Standard (BLOCKING)

**Business Rule BR-E2E-001: Gherkin Docstrings Required**
> Every E2E test function MUST include a Gherkin scenario in its docstring, formatted with Given/When/Then structure.

**Acceptance Criteria:**
```gherkin
Feature: E2E Test Methodology Compliance
  As a developer
  I want all E2E tests to have Gherkin docstrings
  So that tests are traceable to documented requirements

  Scenario: Test includes Gherkin docstring
    Given an E2E test function exists
    When I read the test docstring
    Then the docstring includes "Gherkin:" section
    And the Gherkin has Given/When/Then structure
    And the docstring includes "Validates:" reference

  Scenario: Test migrated from sync to async
    Given a sync E2E test uses fixture-created data
    When I migrate the test
    Then the test uses @pytest.mark.asyncio decorator
    And the test uses async_client_factory fixture
    And the test can access fixture-created data
```

**Example Compliant Test:**
```python
@pytest.mark.asyncio
async def test_create_user_success(self, async_client_factory, async_e2e_session):
    """Admin can create a new user with valid data.

    Validates: FEATURE_SPEC_2025-12-08_E2E-TESTING.md Scenario "Create new user"
    Gherkin:
        Given I am authenticated as admin
        When I submit the create user form with valid data
        Then a new user is created in the database
        And I am redirected to the users list
    """
    # Given
    async with async_client_factory("admin") as client:
        # When
        response = await client.post(
            "/admin/users/create",
            data={"email": "newuser@test.com", "first_name": "New", "role": "staff"},
            follow_redirects=False,
        )

    # Then
    assert response.status_code == 303
    assert "/admin/users" in response.headers.get("location", "")
```

---

### 4.2 Event Mode Coverage

**Business Rule BR-E2E-002: Event Mode Critical Path Tested**
> All critical Event Mode workflows must have E2E test coverage.

**Acceptance Criteria:**
```gherkin
Feature: Event Mode E2E Coverage
  As an MC
  I want comprehensive E2E tests for tournament day workflow
  So that critical paths are validated before production

  Scenario: Start a battle
    Given a tournament in PRESELECTION phase with pending battles
    And I am authenticated as MC
    When I POST to /battles/{battle_id}/start
    Then the battle status changes to ACTIVE
    And I am redirected to the battle view

  Scenario: Encode preselection scores
    Given a battle is ACTIVE with PRESELECTION phase
    And I am authenticated as Staff
    When I submit valid scores for all performers
    Then the battle status changes to COMPLETED
    And performer.preselection_score is updated for each performer

  Scenario: Encode pool results with winner
    Given a battle is ACTIVE with POOL phase
    When I select a winner and submit
    Then the battle status changes to COMPLETED
    And the winner has pool_wins incremented
    And the loser has pool_losses incremented

  Scenario: Encode pool results with draw
    Given a battle is ACTIVE with POOL phase
    When I mark the battle as a draw and submit
    Then the battle status changes to COMPLETED
    And both performers have pool_draws incremented

  Scenario: Validation error preserves form data
    Given a battle is ACTIVE
    When I submit incomplete scores
    Then I see a validation error message
    And the form retains my entered values
    And the battle status remains ACTIVE
```

---

### 4.3 Registration Coverage

**Business Rule BR-E2E-003: Registration Workflows Tested**
> All registration workflows must have E2E test coverage.

**Acceptance Criteria:**
```gherkin
Feature: Registration E2E Coverage
  As Staff
  I want comprehensive E2E tests for dancer registration
  So that registration workflows are validated

  Scenario: Register single dancer to category
    Given a tournament in REGISTRATION phase
    And I am viewing the registration page for a category
    When I search for a dancer and click register
    Then a performer record is created
    And the dancer appears in the registered list

  Scenario: Reject duplicate dancer registration
    Given a dancer is already registered in this tournament
    When I try to register them in another category
    Then I see an error "Dancer already registered in this tournament"
    And no new performer record is created

  Scenario: Category capacity warning
    Given a category has groups_ideal=2 and performers_ideal=4
    And the category has 9 registered performers (above ideal)
    When I view the category
    Then I see a warning about excess performers

  Scenario: Duo partner validation
    Given a 2v2 category
    When I register two different dancers as partners
    Then both performers have duo_partner_id set to each other
    And both dancers appear in the registered list
```

---

### 4.4 Admin Coverage

**Business Rule BR-E2E-004: Admin Workflows Tested**
> All admin user management workflows must have E2E test coverage.

**Acceptance Criteria:**
```gherkin
Feature: Admin E2E Coverage
  As Admin
  I want comprehensive E2E tests for user management
  So that admin workflows are validated

  Scenario: Create user with magic link
    Given I am authenticated as admin
    When I create a user with "send magic link" checked
    Then a new user is created
    And a magic link email is sent (mocked)
    And I see success message

  Scenario: Edit user role
    Given an existing user with role "staff"
    When I change their role to "mc"
    Then the user's role is updated in the database
    And I am redirected back to user list

  Scenario: Delete user
    Given an existing user
    When I click delete and confirm
    Then the user is removed from the database
    And I see success message
```

---

## 5. Current State Analysis

### 5.1 E2E Test File Inventory

| File | Tests | Gherkin | Async | Compliance |
|------|-------|---------|-------|------------|
| test_admin.py | 37 | ❌ 0% | ❌ Sync | Non-compliant |
| test_dancers.py | 21 | ❌ 0% | ❌ Sync | Non-compliant |
| test_event_mode.py | 17 | ❌ 0% | ❌ Sync | Non-compliant |
| test_event_mode_async.py | 8 | ✅ 100% | ✅ Async | **Compliant** |
| test_registration.py | 41 | ❌ 0% | ❌ Sync | Non-compliant |
| test_tournament_management.py | 15 | ❌ 0% | ❌ Sync | Non-compliant |
| test_htmx_interactions.py | 10 | ❌ 0% | ❌ Sync | Non-compliant |
| test_session_isolation_fix.py | 2 | ❌ 0% | ✅ Async | Partial |
| **TOTAL** | **151** | **5.3%** | **6.6%** | **~5% compliant** |

### 5.2 Pattern Analysis

**Sync Pattern (Current - Non-compliant):**
```python
def test_registration_page_loads_with_data(self, staff_client, create_e2e_tournament):
    """GET /registration/{t_id}/{c_id} loads with valid tournament/category."""
    import asyncio
    data = asyncio.get_event_loop().run_until_complete(
        create_e2e_tournament(num_categories=1)
    )
    tournament = data["tournament"]
    # ... test continues
```

**Async Pattern (Target - Compliant):**
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
    data = await create_async_tournament_scenario(num_categories=1)
    tournament = data["tournament"]
    category = data["categories"][0]

    # When
    async with async_client_factory("staff") as client:
        response = await client.get(f"/registration/{tournament.id}/{category.id}")

    # Then
    assert response.status_code == 200
    assert category.name in response.text
```

### 5.3 Coverage Gap Analysis

**Event Mode (from FEATURE_SPEC_2025-12-08_E2E-TESTING.md):**

| Gherkin Scenario | Test Exists | Status |
|------------------|-------------|--------|
| Start a battle | No | ⚠️ Gap |
| Encode preselection scores | No | ⚠️ Gap |
| Encode pool results with winner | No | ⚠️ Gap |
| Validation error preserves form | No | ⚠️ Gap |
| View command center | Yes (async) | ✅ Covered |
| Battle queue returns partial | Yes (async) | ✅ Covered |

**Registration:**

| Gherkin Scenario | Test Exists | Status |
|------------------|-------------|--------|
| Page loads with data | Yes | ⚠️ Needs Gherkin |
| Register single dancer | Partial | ⚠️ Needs Gherkin |
| Duplicate rejection | Partial | ⚠️ Needs Gherkin |
| Duo partner validation | No | ⚠️ Gap |

**Admin:**

| Gherkin Scenario | Test Exists | Status |
|------------------|-------------|--------|
| Users list loads | Yes | ⚠️ Needs Gherkin |
| Create user success | Yes | ⚠️ Needs Gherkin |
| Create user with magic link | Yes | ⚠️ Needs Gherkin |
| Delete user | Partial | ⚠️ Needs Gherkin |
| Edit user role | No | ⚠️ Gap |

---

## 6. Implementation Recommendations

### 6.1 Critical (Must Complete)

1. **Migrate test_admin.py (37 tests)**
   - Add Gherkin docstrings to all 37 tests
   - Add "Validates:" references
   - Convert fixture-dependent tests to async
   - Keep sync for HTTP-only tests (create via POST)

2. **Migrate test_registration.py (41 tests)**
   - Add Gherkin docstrings to all 41 tests
   - Convert all tests using `run_until_complete()` to async
   - Add "Validates:" references

3. **Migrate test_dancers.py (21 tests)**
   - Add Gherkin docstrings
   - Convert to async where needed

4. **Migrate test_event_mode.py (17 tests)**
   - Add Gherkin docstrings
   - Merge with test_event_mode_async.py pattern

5. **Migrate test_tournament_management.py (15 tests)**
   - Add Gherkin docstrings
   - Convert to async

6. **Migrate test_htmx_interactions.py (10 tests)**
   - Add Gherkin docstrings
   - Convert to async

### 6.2 Recommended (New Tests)

7. **Add Event Mode gap tests (~7 new tests)**
   - test_start_battle_changes_status
   - test_encode_preselection_scores
   - test_encode_pool_winner
   - test_encode_pool_draw
   - test_validation_error_preserves_form
   - test_progress_bar_updates
   - test_battle_queue_shows_next

8. **Add Registration gap tests (~4 new tests)**
   - test_bulk_dancer_registration
   - test_duo_partner_validation
   - test_category_capacity_warning
   - test_unregister_cascade_duo

9. **Add Admin gap tests (~3 new tests)**
   - test_edit_user_role
   - test_complete_user_lifecycle
   - test_magic_link_flow

### 6.3 Nice-to-Have (Future)

10. **Pre-commit hook for E2E docstrings**
    - Warn if E2E test lacks "Validates:" in docstring
    - Enforce Gherkin format

11. **Automated traceability report**
    - Parse feature-spec.md for Gherkin scenarios
    - Parse test docstrings for "Validates:" references
    - Generate coverage report

---

## 7. Appendix: Reference Material

### 7.1 Feature Spec References

Tests should reference these feature specs:

| Feature Spec | Location | Scenarios |
|--------------|----------|-----------|
| E2E Testing Framework | `archive/FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md` | Event Mode, Tournament Management, HTMX |
| Tournament Validation | `archive/FEATURE_SPEC_2025-12-04_TOURNAMENT-ORGANIZATION-VALIDATION.md` | Phase transitions, validations |
| Test Traceability | `archive/FEATURE_SPEC_2025-12-09_TEST-REQUIREMENT-TRACEABILITY.md` | Docstring standard |
| Battle Encoding | `VALIDATION_RULES.md` | Preselection, Pool, Tiebreak, Finals encoding |

### 7.2 Files to Modify

| File | Action | Estimated Tests |
|------|--------|-----------------|
| tests/e2e/test_admin.py | Add Gherkin + Async | 37 |
| tests/e2e/test_registration.py | Add Gherkin + Async | 41 |
| tests/e2e/test_dancers.py | Add Gherkin + Async | 21 |
| tests/e2e/test_event_mode.py | Add Gherkin + Async | 17 |
| tests/e2e/test_tournament_management.py | Add Gherkin + Async | 15 |
| tests/e2e/test_htmx_interactions.py | Add Gherkin + Async | 10 |
| tests/e2e/test_session_isolation_fix.py | Add Gherkin | 2 |
| **NEW tests** | Create with Gherkin | ~14 |
| **TOTAL** | | ~157 tests |

### 7.3 Open Questions & Answers

- **Q:** Should all 143 tests be migrated to async pattern?
  - **A:** No. Tests that create data via HTTP POST (not fixtures) can remain sync. Only tests requiring fixture-created data need async.

- **Q:** What feature-spec should tests reference if no spec exists?
  - **A:** Reference `DOMAIN_MODEL.md` for domain rules, `VALIDATION_RULES.md` for validation rules, or create a "derived scenario" note in the docstring.

- **Q:** How strictly should Gherkin format be enforced?
  - **A:** Given/When/Then structure required. Full Gherkin syntax (Feature:, Scenario:) in docstring is recommended but optional.

### 7.4 User Confirmation

- [x] User confirms problem statement is accurate
- [x] User validates acceptance criteria match their vision
- [x] User approves migration approach (compliance + **selective** async)
- [x] User confirms all gaps identified should be addressed

**User Decision:** Selective async conversion - only convert tests that need fixture-created data to async. Tests that create data via HTTP POST can remain sync.

---

**Summary:** This migration will bring 143 E2E tests (94.7%) into Phase 3.8 methodology compliance by adding Gherkin docstrings with requirement traceability, selectively migrating to async pattern where needed (tests requiring fixture data), and filling coverage gaps with ~14 new tests. The result will be a fully traceable, maintainable E2E test suite.
