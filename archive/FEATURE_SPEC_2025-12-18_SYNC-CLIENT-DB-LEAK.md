# Feature Specification: Sync Client Database Leak Fix

**Date:** 2025-12-18
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Business Rules & Acceptance Criteria](#3-business-rules--acceptance-criteria)
4. [Current State Analysis](#4-current-state-analysis)
5. [Implementation Recommendations](#5-implementation-recommendations)
6. [Appendix: Reference Material](#6-appendix-reference-material)

---

## 1. Problem Statement

Despite implementing test database isolation in commit 6af038a, the development database (`./data/battle_d.db`) is still being polluted with test data when running pytest. This defeats the purpose of the isolation fix and corrupts the development environment with entries like "HTTP Test e1cfa17f" and "Cat Test 4a0c475d".

---

## 2. Executive Summary

### Scope
Analysis of why test data leaked into dev database after the "Test database isolation" fix.

### What Works ✅
| Feature | Status |
|---------|--------|
| In-memory test database engine | Production Ready |
| `test_session_maker` export from conftest.py | Production Ready |
| `e2e_client` fixture with `get_db` override | Production Ready |
| 13 test files updated to use isolated session | Production Ready |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| `sync_client` fixture missing `get_db` override | BUG | `tests/e2e/test_session_isolation_fix.py:275-288` |
| `client` fixture missing `get_db` override | BUG | `tests/test_crud_workflows.py:59-75` |
| `client` fixture missing `get_db` override | BUG | `tests/test_auth.py:63-79` |
| `client` fixture missing `get_db` override | BUG | `tests/test_permissions.py:10-13` |

### Key Business Rules Defined
- **BR-TEST-001:** All test fixtures MUST override `get_db` dependency
- **BR-TEST-002:** Tests MUST NOT create data in `./data/battle_d.db`

---

## 3. Business Rules & Acceptance Criteria

### 3.1 Test Database Isolation

**Business Rule BR-TEST-001: Complete Database Override**
> Every test fixture that creates a TestClient or AsyncClient MUST override the `get_db` dependency to use the isolated in-memory test database.

**Acceptance Criteria:**
```gherkin
Feature: Test Database Isolation
  As a Developer
  I want tests to use an isolated database
  So that my development data is never affected by test runs

  Scenario: Sync client uses isolated database
    Given the test_session_isolation_fix.py test file
    And the sync_client fixture is used
    When tests create tournaments via HTTP POST
    Then the data should be created in the in-memory test database
    And the dev database (./data/battle_d.db) should remain unchanged

  Scenario: Dev database unchanged after full test suite
    Given the development database has known state
    When I run the full pytest suite
    Then the development database should have identical state
    And no test entries should exist (HTTP Test, Cat Test, etc.)

  Scenario: Pattern scan finds all TestClient usages
    Given I search for TestClient instantiation
    When I check each occurrence
    Then each must have app.dependency_overrides[get_db] set
```

---

## 4. Current State Analysis

### 4.1 The Missed Override

**Business Rule:** All test clients must use isolated database
**Implementation Status:** ❌ INCOMPLETE
**Evidence:**

File: `tests/e2e/test_session_isolation_fix.py:275-288`
```python
@pytest.fixture
def sync_client(self):
    """Sync TestClient with mocked email."""
    mock_email = MockEmailProvider()

    def get_mock_email_service():
        return EmailService(mock_email)

    app.dependency_overrides[get_email_service] = get_mock_email_service
    # ⚠️ BUG: Missing get_db override!

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
```

**Correct Pattern** (from `tests/e2e/conftest.py:122-154`):
```python
@pytest.fixture
def e2e_client(mock_email_provider):
    async def get_test_db():
        async with _test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_email_service] = get_mock_email_service
    app.dependency_overrides[get_db] = get_test_db  # ✅ CORRECT

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

### 4.2 Timeline of Events

| Time | Event |
|------|-------|
| 16:12:37 | `HTTP Test e1cfa17f` created in dev DB |
| 16:12:37 | `Cat Test 4a0c475d` created in dev DB |
| 16:16:35 | More test entries created |
| 16:18:22 | Additional pollution |
| 16:30:37 | Commit 6af038a pushed (fix was incomplete) |

### 4.3 Pattern Scan Results

**Pattern searched:** TestClient instantiation without `get_db` override

**Search commands:**
```bash
# Find all TestClient instantiations
grep -rn "TestClient(" tests/

# Find all get_db overrides
grep -rn "dependency_overrides\[get_db\]" tests/

# Find all POST operations in tests
grep -rn "\.post\(" tests/e2e/*.py tests/*.py

# List all test files
find tests -name "test_*.py" | wc -l  # 28 test files total
```

**Complete Test File Inventory (28 files):**

| Category | File | TestClient? | get_db Override? | Risk |
|----------|------|-------------|------------------|------|
| **conftest** | tests/conftest.py | No | N/A (in-memory engine) | ✅ Safe |
| **conftest** | tests/e2e/conftest.py | Yes (line 151) | ✅ Yes (line 149) | ✅ Safe |
| **conftest** | tests/e2e/async_conftest.py | AsyncClient | ✅ Yes (line 135) | ✅ Safe |
| **E2E** | tests/e2e/test_admin.py | Uses `e2e_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_dancers.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_event_mode.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_event_mode_advance.py | Uses `admin_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_event_mode_async.py | AsyncClient | ✅ Via async_conftest | ✅ Safe |
| **E2E** | tests/e2e/test_htmx_interactions.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_minimum_formula_consistency.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_registration.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_tournament_management.py | Uses `staff_client` | ✅ Inherited | ✅ Safe |
| **E2E** | tests/e2e/test_ux_consistency.py | No HTTP client | N/A (file scanning) | ✅ Safe |
| **E2E** | tests/e2e/test_session_isolation_fix.py | Yes (line 285) | ❌ **NO** | 🚨 **CRITICAL** |
| **Unit** | tests/test_crud_workflows.py | Yes (line 71) | ❌ **NO** | 🚨 **CRITICAL** |
| **Unit** | tests/test_auth.py | Yes (line 73) | ❌ **NO** | ⚠️ Medium |
| **Unit** | tests/test_permissions.py | Yes (line 13) | ❌ **NO** | ⚠️ Medium |
| **Unit** | tests/test_phases_routes.py | Yes (line 16) | ❌ NO | ✅ Safe (404 tests) |
| **Unit** | tests/test_flash_messages.py | Yes (line 40) | N/A (uses `test_app`) | ✅ Safe |
| **Integration** | tests/test_models.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_repositories.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_dancer_service_integration.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_event_service_integration.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_performer_service_integration.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_tournament_service_integration.py | No | Uses `test_session_maker` | ✅ Safe |
| **Integration** | tests/test_battle_results_encoding_integration.py | No | Uses `test_session_maker` | ✅ Safe |
| **Service** | tests/test_event_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_battle_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_battle_encoding_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_battle_results_encoding_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_pool_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_tiebreak_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_dashboard_service.py | No | Pure unit (mocks) | ✅ Safe |
| **Service** | tests/test_tournament_calculations.py | No | Pure unit (mocks) | ✅ Safe |
| **Email** | tests/test_gmail_provider.py | No | Pure unit (mocks) | ✅ Safe |
| **Email** | tests/test_brevo_provider.py | No | Pure unit (mocks) | ✅ Safe |
| **Email** | tests/test_email_templates.py | No | Pure unit (mocks) | ✅ Safe |

**Summary by Risk Level:**

**🚨 CRITICAL - Actively polluting dev DB (2 files):**
1. `tests/e2e/test_session_isolation_fix.py:285` - `sync_client` fixture missing `get_db` override
   - Creates: "HTTP Test {uuid}", "Cat Test {uuid}"
2. `tests/test_crud_workflows.py:71` - `client` fixture missing `get_db` override
   - Creates: "Category Test", "Duo Test", "Reg Test", tournaments, users

**⚠️ MEDIUM - Potential pollution (2 files):**
3. `tests/test_auth.py:73` - `client` fixture missing `get_db` override
   - POSTs to: `/auth/request-magic-link` (may create magic link records)
4. `tests/test_permissions.py:13` - `client` fixture missing `get_db` override
   - POSTs to: `/phases/advance`, `/phases/go-back` (legacy routes, may hit DB)

**✅ SAFE - Properly isolated (24+ files):**
- All E2E tests using fixtures from `tests/e2e/conftest.py` (inherit `get_db` override)
- All integration tests using `test_session_maker` directly
- All pure unit tests using mocks
- `test_phases_routes.py` - tests 404 responses only
- `test_flash_messages.py` - uses separate `test_app`, not main app

**Decision:**
- [x] Fix all 4 affected files immediately

---

## 5. Implementation Recommendations

### 5.1 Critical (Before Production)

1. **Fix 4 test files with missing `get_db` override:**
   - `tests/e2e/test_session_isolation_fix.py:275-288` - Add `get_db` override to `sync_client`
   - `tests/test_crud_workflows.py:59-75` - Add `get_db` override to `client`
   - `tests/test_auth.py:63-79` - Add `get_db` override to `client`
   - `tests/test_permissions.py:10-13` - Add `get_db` override to `client`

2. **Clean dev database** - Remove polluted test entries:
   ```sql
   DELETE FROM tournaments WHERE name LIKE 'HTTP Test%';
   DELETE FROM tournaments WHERE name LIKE 'Cat Test%';
   DELETE FROM tournaments WHERE name LIKE 'Test Tournament%';
   DELETE FROM tournaments WHERE name LIKE 'Category Test%';
   DELETE FROM tournaments WHERE name LIKE 'Duo Test%';
   DELETE FROM tournaments WHERE name LIKE 'Reg Test%';
   ```

3. **Verify fix works** - Run the full test suite and confirm no new entries in dev DB

### 5.2 Recommended

1. **Add automated check** - Create a test that verifies dev DB is unchanged after test run
2. **Update TESTING.md** - Add warning about TestClient fixtures requiring `get_db` override
3. **Consider centralized fixture** - Move all TestClient fixtures to use `e2e_client` from `tests/e2e/conftest.py`

### 5.3 Nice-to-Have (Future)

1. **Refactor test_session_isolation_fix.py** - Consider if this prototype file is still needed, or if the patterns are now standard in conftest.py
2. **Add pre-commit hook** - Scan for TestClient without get_db override

---

## 6. Appendix: Reference Material

### 6.1 Open Questions & Answers

- **Q:** Why wasn't this caught in the original fix?
  - **A:** The `test_session_isolation_fix.py` file was a prototype exploring approaches. The "HTTP-only" approach was intentionally minimal but the oversight was not catching that it still needed `get_db` override.

- **Q:** Are there other TestClient usages that might be affected?
  - **A:** Yes! Pattern scan found **4 files** with missing `get_db` override. The original fix only addressed repository/service tests that use `test_session_maker` directly, but missed TestClient-based HTTP tests.

### 6.2 Affected Test Methods

**From `test_session_isolation_fix.py` (TestHTTPOnlyApproach class):**
1. `test_create_and_view_tournament_via_http` (line 306) - Creates "HTTP Test {uuid}"
2. `test_create_tournament_with_category_via_http` (line 345) - Creates "Cat Test {uuid}"

**From `test_crud_workflows.py`:**
3. Multiple tests create "Category Test", "Duo Test", "Reg Test" tournaments (lines 229, 268, etc.)

**From `test_auth.py`:**
4. Tests POST to `/auth/request-magic-link` - may create session data

**From `test_permissions.py`:**
5. Tests POST to `/phases/advance` and `/phases/go-back` - legacy routes (may still hit DB)

### 6.3 User Confirmation

- [x] Problem statement confirmed (user provided screenshot evidence)
- [x] Root cause identified (missing get_db override)
- [ ] User approval for fix pending
