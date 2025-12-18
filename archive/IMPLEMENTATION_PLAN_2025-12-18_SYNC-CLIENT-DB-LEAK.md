# Implementation Plan: Sync Client Database Leak Fix

**Date:** 2025-12-18
**Status:** Ready for Implementation
**Based on:** workbench/FEATURE_SPEC_2025-12-18_SYNC-CLIENT-DB-LEAK.md

---

## 1. Summary

**Feature:** Fix remaining test database isolation leaks where TestClient fixtures are missing `get_db` override
**Approach:** Add `get_db` dependency override to 4 test files following the pattern from `tests/e2e/conftest.py:136-149`

---

## 2. Technical POC

**Status:** Not required
**Reason:** Standard fix following existing pattern already proven in `tests/e2e/conftest.py:122-155`

The correct pattern is already implemented and working in `e2e_client` fixture. This fix simply applies the same pattern to 4 other files that were missed.

---

## 3. Affected Files

### Test Files to Fix

| File | Line | Fixture Name | Risk Level |
|------|------|--------------|------------|
| `tests/e2e/test_session_isolation_fix.py` | 275-288 | `sync_client` | 🚨 CRITICAL |
| `tests/test_crud_workflows.py` | 58-75 | `client` | 🚨 CRITICAL |
| `tests/test_auth.py` | 63-79 | `client` | ⚠️ MEDIUM |
| `tests/test_permissions.py` | 10-13 | `client` | ⚠️ MEDIUM |

### No Changes Needed

- **Backend:** No changes
- **Frontend:** No changes
- **Database:** No schema changes
- **Documentation:** Minor update to TESTING.md (add warning)

---

## 4. Implementation Details

### 4.1 The Correct Pattern (Reference)

From `tests/e2e/conftest.py:122-155`:

```python
@pytest.fixture
def e2e_client(mock_email_provider):
    """Base test client with mocked email service and isolated test database."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    async def get_test_db():
        """Override database dependency to use test database."""
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
    app.dependency_overrides[get_db] = get_test_db  # <-- CRITICAL LINE

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()
```

### 4.2 Fix #1: `tests/e2e/test_session_isolation_fix.py`

**Current code (lines 275-288):**
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

**Fixed code:**
```python
@pytest.fixture
def sync_client(self):
    """Sync TestClient with mocked email and isolated test database."""
    mock_email = MockEmailProvider()

    def get_mock_email_service():
        return EmailService(mock_email)

    async def get_test_db():
        """Override database dependency to use test database."""
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_email_service] = get_mock_email_service
    app.dependency_overrides[get_db] = get_test_db  # ✅ FIX

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
```

**Additional imports needed:**
```python
from app.db.database import get_db  # Already imported at line 19
```

### 4.3 Fix #2: `tests/test_crud_workflows.py`

**Current code (lines 58-75):**
```python
@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    app.dependency_overrides[get_email_service] = get_mock_email_service

    # Use context manager to maintain cookies
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()
```

**Fixed code:**
```python
@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider and isolated test database.

    Note: Must use with statement to maintain cookies across requests.
    """

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    async def get_test_db():
        """Override database dependency to use test database."""
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_email_service] = get_mock_email_service
    app.dependency_overrides[get_db] = get_test_db  # ✅ FIX

    # Use context manager to maintain cookies
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()
```

**Additional imports needed:**
```python
from app.db.database import get_db  # ADD THIS
```

### 4.4 Fix #3: `tests/test_auth.py`

**Current code (lines 63-79):**
```python
@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    # Override the email service dependency
    app.dependency_overrides[get_email_service] = get_mock_email_service

    client = TestClient(app)

    yield client

    # Clean up after test
    app.dependency_overrides.clear()
    mock_email_provider.clear()
```

**Fixed code:**
```python
@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider and isolated test database."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    async def get_test_db():
        """Override database dependency to use test database."""
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Override dependencies
    app.dependency_overrides[get_email_service] = get_mock_email_service
    app.dependency_overrides[get_db] = get_test_db  # ✅ FIX

    with TestClient(app) as test_client:
        yield test_client

    # Clean up after test
    app.dependency_overrides.clear()
    mock_email_provider.clear()
```

**Additional imports needed:**
```python
from app.db.database import get_db  # ADD THIS
```

### 4.5 Fix #4: `tests/test_permissions.py`

**Current code (lines 10-13):**
```python
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)
```

**Fixed code:**
```python
@pytest.fixture
def client():
    """Create test client with isolated test database."""
    async def get_test_db():
        """Override database dependency to use test database."""
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = get_test_db  # ✅ FIX

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

**Additional imports needed:**
```python
from app.db.database import get_db  # ADD THIS
from tests.conftest import test_session_maker  # ADD THIS
```

---

## 5. Database Cleanup

After implementing fixes, clean dev database of polluted test entries:

```sql
-- Run against ./data/battle_d.db
DELETE FROM tournaments WHERE name LIKE 'HTTP Test%';
DELETE FROM tournaments WHERE name LIKE 'Cat Test%';
DELETE FROM tournaments WHERE name LIKE 'Test Tournament%';
DELETE FROM tournaments WHERE name LIKE 'Category Test%';
DELETE FROM tournaments WHERE name LIKE 'Duo Test%';
DELETE FROM tournaments WHERE name LIKE 'Reg Test%';
```

---

## 6. Documentation Update Plan

### TESTING.md Update

Add warning section about TestClient fixtures:

```markdown
## Database Isolation Warning

**CRITICAL:** Every test fixture that creates a `TestClient` or `AsyncClient` MUST override the `get_db` dependency to use the isolated test database.

### Required Pattern

```python
from app.db.database import get_db
from tests.conftest import test_session_maker

@pytest.fixture
def my_client():
    async def get_test_db():
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = get_test_db  # REQUIRED!

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
```

### Why This Matters

Without the `get_db` override, HTTP requests use the production database (`./data/battle_d.db`) instead of the in-memory test database. This pollutes development data with test entries.
```

---

## 7. Testing Plan

### 7.1 Verification Tests

After implementing fixes, run these tests to verify isolation works:

```bash
# Run the isolation test itself
pytest tests/e2e/test_session_isolation_fix.py -v

# Run CRUD workflow tests
pytest tests/test_crud_workflows.py -v

# Run auth tests
pytest tests/test_auth.py -v

# Run permission tests
pytest tests/test_permissions.py -v
```

### 7.2 Full Test Suite

```bash
# Run full test suite
pytest tests/ -v

# Check dev database for pollution (should return 0)
sqlite3 ./data/battle_d.db "SELECT COUNT(*) FROM tournaments WHERE name LIKE 'HTTP Test%' OR name LIKE 'Cat Test%';"
```

### 7.3 Manual Verification

1. Note tournament count in dev DB before running tests
2. Run full pytest suite
3. Verify tournament count is unchanged
4. Verify no "HTTP Test", "Cat Test" entries exist

---

## 8. Risk Analysis

### Risk 1: Async/Sync Mismatch
**Concern:** `get_test_db` is async but TestClient is sync
**Likelihood:** Low
**Impact:** High (tests would fail)
**Mitigation:**
- This pattern already works in `e2e_client` fixture
- FastAPI handles async->sync conversion automatically for dependency overrides
- No changes needed, just copy proven pattern

### Risk 2: Tests Start Failing
**Concern:** Some tests may depend on data from dev database
**Likelihood:** Low
**Impact:** Medium (tests need updating)
**Mitigation:**
- Any such tests are already incorrectly written
- They should create their own test data
- Existing `setup_*` fixtures already handle user creation

### Risk 3: Forgotten Future TestClient
**Concern:** Future developers might create TestClient without override
**Likelihood:** Medium
**Impact:** High (data pollution)
**Mitigation:**
- Add warning to TESTING.md
- Consider adding CI check (grep for TestClient without get_db override)

---

## 9. Implementation Order

**Recommended sequence:**

1. **Fix test files** (in order of risk)
   - `tests/e2e/test_session_isolation_fix.py` - CRITICAL, creates most pollution
   - `tests/test_crud_workflows.py` - CRITICAL, creates most pollution
   - `tests/test_auth.py` - MEDIUM risk
   - `tests/test_permissions.py` - MEDIUM risk (mostly skipped tests)

2. **Clean dev database**
   - Run SQL cleanup commands
   - Verify no test entries remain

3. **Run tests**
   - Run full pytest suite
   - Verify all tests pass
   - Verify dev DB unchanged

4. **Update documentation**
   - Add warning to TESTING.md
   - Update any relevant comments

5. **Commit**
   - Single commit with all fixes
   - Clear commit message explaining the fix

---

## 10. Open Questions

- [x] Why wasn't this caught in original fix? → Files were missed during pattern scan
- [x] Can we prevent future occurrences? → Add TESTING.md warning, consider CI check
- [x] Is the async/sync pattern safe? → Yes, proven in `e2e_client` fixture

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
