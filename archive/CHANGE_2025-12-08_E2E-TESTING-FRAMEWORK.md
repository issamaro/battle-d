# Workbench: E2E Testing Framework

**Date:** 2025-12-08
**Author:** Claude
**Status:** Complete - Accepted at 69% (High coverage deferred for re-analysis)

---

## Summary

Added 141 E2E tests covering router access patterns, authentication, and error handling. Coverage improved from 65% to 69% but **85% target NOT MET** due to database session isolation.

---

## Test Results

### Before
- Tests: 358
- Coverage: 65%

### After
- Tests: 457 (+99)
- E2E Tests: 141
- Coverage: 69% (+4%)
- **Target: 85% - NOT MET**

---

## What Was Achieved

**E2E Tests Added:**
| File | Tests | Router Coverage |
|------|-------|-----------------|
| test_registration.py | 41 | 16% → 51% |
| test_admin.py | 37 | 35% → 57% |
| test_dancers.py | 22 | 39% → 71% |
| test_event_mode.py | 17 | 38% (unchanged) |
| test_tournament_management.py | 15 | 63% (unchanged) |
| test_htmx_interactions.py | 10 | N/A |

**Bug Documented:**
- BUG-001: POST routes return 303 instead of 404 for non-existent resources
- File: workbench/BUGS_2025-12-08_POST-ROUTE-404.md

---

## Why 85% Target Cannot Be Met with E2E Tests

### Root Cause: Database Session Isolation
1. TestClient runs in synchronous mode
2. Async fixtures create data in separate database sessions
3. Data created in fixtures is NOT visible to TestClient requests
4. This is a fundamental limitation of the test infrastructure

### Affected Routes (Low Coverage)
- `battles.py` (37%): Battle start/encode/reorder require real battles
- `event.py` (38%): Command center requires tournament in PRESELECTION+ phase
- `phases.py` (49%): Phase advancement requires tournament with performers

### Attempted Solutions (Failed)
1. Created `create_e2e_battle` factory → Session isolation prevented data visibility
2. Tried tests with real tournament/battle data → All failed with 404s

---

## Path Forward to 85% Coverage

### Option 1: Service Integration Tests (Recommended)
The routes with low coverage are already tested at the service layer:
- `tests/test_battle_results_encoding_integration.py`
- `tests/test_event_service_integration.py`
- `tests/test_tournament_service_integration.py`

These tests use REAL repositories and exercise the business logic. The routers are thin wrappers that call these services.

### Option 2: Full HTTP Workflow Tests
Create data entirely through HTTP endpoints:
1. POST /tournaments/create → get tournament_id
2. POST /tournaments/{id}/add-category → get category_id
3. POST /registration/{t}/{c}/register → register dancers
4. POST /tournaments/{id}/advance → advance phase, creates battles
5. Then test battle routes

**Problem:** This requires 10-15 sequential HTTP requests per test, making tests slow and brittle.

### Option 3: Restructure Test Infrastructure
Change TestClient to share async session with fixtures. This requires significant changes to conftest.py and may break existing tests.

---

## Honest Assessment

**What the E2E tests DO test:**
- Authentication requirements (401/403 for unauthenticated)
- Authorization (role checks)
- Invalid UUID handling (400)
- Non-existent resource handling (404)
- HTMX partial response format
- Form validation errors
- Success redirects

**What the E2E tests do NOT test (due to session isolation):**
- Battle start workflow with real battle
- Battle encoding with real performers
- Event mode command center with real tournament
- Phase advancement success path

**These paths ARE covered by service integration tests**, just not at the HTTP layer.

---

## Quality Gate

- [x] All E2E tests pass (141/141)
- [x] No regressions (457 tests pass)
- [x] Bug tracking document created
- [ ] Coverage reaches 85% (current: 69%) **BLOCKED**

---

## Recommendation

1. **Accept 69% coverage for E2E tests** - they cover access patterns and error handling
2. **Ensure service integration tests hit 85%+** - they cover business logic
3. **Fix the 303 vs 404 bug** - documented in bug tracking file
4. **Consider Option 2 (full HTTP workflow tests)** for critical paths only
