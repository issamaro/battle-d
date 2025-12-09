# Workbench: E2E Testing Session Isolation Fix

**Date:** 2025-12-08
**Author:** Claude
**Status:** Complete

---

## Purpose

Fix E2E testing session isolation so tests can access fixture-created database data. Replace sync TestClient approach with httpx.AsyncClient and session override pattern.

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes (not domain rules)

**VALIDATION_RULES.md:**
- No changes (not validation rules)

### Level 2: Derived
**ROADMAP.md:**
- No changes (infrastructure improvement, not feature)

### Level 3: Operational
**TESTING.md:**
- [x] Add "Async E2E Tests (Session Sharing Pattern)" section
- [x] Document new fixtures and usage
- [x] Explain when to use async vs sync patterns

---

## Verification

```
================ 473 passed, 8 skipped, 1155 warnings in 19.92s ================
```

All tests pass including:
- 8 new async E2E tests in `test_event_mode_async.py`
- 5 prototype tests in `test_session_isolation_fix.py`

---

## Files Modified

### New Files
- `tests/e2e/async_conftest.py` - Core async E2E fixtures with session sharing
- `tests/e2e/test_event_mode_async.py` - Example async E2E tests (8 tests)
- `tests/e2e/test_session_isolation_fix.py` - Prototype tests comparing approaches

### Modified Files
- `TESTING.md` - Added "Async E2E Tests (Session Sharing Pattern)" section

---

## Key Implementation Details

### Solution: AsyncClient + Session Override Pattern

The solution uses three components:

1. **Shared Session Fixture** (`async_e2e_session`):
   - Creates a single async session for the entire test
   - Uses `flush()` instead of `commit()` to keep data in transaction
   - Rolls back at end for automatic cleanup

2. **Dependency Override**:
   - Overrides `get_db` to return shared session
   - Routes use same session as fixtures
   - Data created in fixtures is visible to HTTP requests

3. **AsyncClient Factory** (`async_client_factory`):
   - Context manager for authenticated clients
   - Handles auth token generation and cookie management
   - Supports different roles: admin, staff, mc, judge

### Usage Pattern
```python
@pytest.mark.asyncio
async def test_with_fixture_data(async_client_factory, create_async_tournament):
    # Create data in shared session
    tournament = await create_async_tournament(name="Test")

    # Make HTTP request - sees fixture data!
    async with async_client_factory("staff") as client:
        response = await client.get(f"/tournaments/{tournament.id}")
        assert response.status_code == 200
```
