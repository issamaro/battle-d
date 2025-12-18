# Feature Specification: Database Purge Bug Fix

**Date:** 2025-12-18
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)

---

## 1. Problem Statement

Every time the developer makes code changes, the local development database gets purged (all tables deleted), causing a 500 error "no such table: tournaments" and requiring manual database reset. This breaks the development workflow and wastes significant time.

---

## 2. Executive Summary

### Scope
Analysis of why the local SQLite database is repeatedly purged during development.

### What Works
| Feature | Status |
|---------|--------|
| Alembic migrations | Production Ready |
| Database schema | Production Ready |
| Seed script | Production Ready |

### What's Broken
| Issue | Type | Location |
|-------|------|----------|
| Tests purge production DB | BUG | `tests/conftest.py:20-36` |
| No test database isolation | GAP | Configuration |

### Key Business Rules Defined
- **BR-DEV-001:** Tests must never affect the development/production database
- **BR-DEV-002:** Local development data must persist across code changes

---

## 3. Root Cause Analysis

### The Bug: Tests Use Production Database

**File:** `tests/conftest.py:20-36`

```python
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """Setup and teardown test database for each test."""
    # Ensure clean state by dropping any existing tables
    await drop_db()        # <-- DROPS ALL TABLES FROM ./data/battle_d.db

    # Create all tables fresh
    await init_db()        # <-- Creates tables with SQLAlchemy (not alembic)

    yield

    # Clean up after test
    await drop_db()        # <-- DROPS ALL TABLES AGAIN
```

**Why this happens:**
1. `tests/conftest.py` imports `from app.db.database import init_db, drop_db`
2. `app/db/database.py` uses `settings.DATABASE_URL`
3. `settings.DATABASE_URL` resolves to `sqlite:///./data/battle_d.db` (production DB)
4. **There is NO test-specific database configuration**

### Flow Diagram: How Bug Manifests

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DEVELOPER WORKFLOW (BROKEN)                                             │
└─────────────────────────────────────────────────────────────────────────┘

  [Developer]
       │
       ▼
  ┌──────────────────────┐
  │ 1. Run app locally   │
  │ Uses: ./data/        │
  │        battle_d.db   │
  └──────────────────────┘
       │
       ▼
  ┌──────────────────────┐
  │ 2. Create data       │
  │ - Tournament         │
  │ - Categories         │
  │ - Dancers            │
  └──────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 3. Make code change (e.g., edit template)                │
  │    Some IDEs/tools auto-run tests on save                │
  │    OR developer runs: pytest tests/                      │
  └──────────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 4. TEST FIXTURE RUNS (autouse=True)                      │
  │                                                          │
  │    await drop_db()  <── PURGES ./data/battle_d.db !!!    │
  │    await init_db()  <── Creates tables (no alembic)      │
  │                                                          │
  │    [test runs]                                           │
  │                                                          │
  │    await drop_db()  <── PURGES AGAIN !!!                 │
  └──────────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 5. DATABASE STATE                                        │
  │                                                          │
  │    ./data/battle_d.db contains:                          │
  │    - alembic_version (only)                              │
  │    - NO other tables                                     │
  │                                                          │
  │    WHY? drop_db() uses Base.metadata.drop_all()          │
  │         This doesn't know about alembic migrations       │
  │         init_db() uses Base.metadata.create_all()        │
  │         But tables don't match alembic migrations        │
  └──────────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 6. Developer visits localhost:8000/overview              │
  │                                                          │
  │    500 Error: no such table: tournaments                 │
  └──────────────────────────────────────────────────────────┘
```

### Additional Factor: alembic_version Mismatch

Even if tables were created by `init_db()`, there's another problem:

1. `alembic_version` table says: `7d8616b32e9f` (latest migration)
2. But tables are created by `Base.metadata.create_all()` which:
   - Creates tables based on current SQLAlchemy models
   - Does NOT apply column additions from migrations
   - Does NOT create indexes from migrations

This causes schema mismatches if models differ from migration history.

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Test Database Isolation

**Business Rule BR-DEV-001: Test Isolation**
> Tests must run in a completely isolated database that never affects development or production data.

**Acceptance Criteria:**
```gherkin
Feature: Test Database Isolation
  As a developer
  I want tests to use a separate database
  So that my development data is never lost

  Scenario: Running tests does not affect dev database
    Given I have a development database with tournaments and dancers
    When I run the test suite
    Then my development database still contains all my data
    And tests use a separate in-memory or test-specific database

  Scenario: Tests start with clean state
    Given tests are configured to use an isolated database
    When a test suite runs
    Then each test starts with a fresh database
    And tests do not interfere with each other
```

### 4.2 Development Data Persistence

**Business Rule BR-DEV-002: Dev Data Persistence**
> Local development data must persist across code changes, restarts, and test runs.

**Acceptance Criteria:**
```gherkin
Feature: Development Data Persistence
  As a developer
  I want my test data to persist
  So that I don't waste time recreating test scenarios

  Scenario: Code changes preserve database
    Given I have seeded development data
    When I edit source code files
    Then my development database remains intact

  Scenario: App restart preserves database
    Given I have tournaments in my development database
    When I restart the FastAPI server
    Then all my tournaments are still there
```

---

## 5. Current State Analysis

### 5.1 Database Configuration

**Location:** `app/config.py:49-68`

**Current Implementation:**
- Single `DATABASE_URL` for all environments
- No test-specific configuration
- Default: `sqlite:///./data/battle_d.db`

**Issue:** No environment separation

### 5.2 Test Fixtures

**Location:** `tests/conftest.py:20-36`

**Current Implementation:**
- `autouse=True` - runs for EVERY test
- `scope="function"` - drops/creates DB for each test function
- Uses same database as production

**Issue:** Destructive operations on production database

### 5.3 Database Operations

**Location:** `app/db/database.py:50-69`

**Functions:**
- `init_db()` - `Base.metadata.create_all()` (SQLAlchemy, not alembic)
- `drop_db()` - `Base.metadata.drop_all()` (drops everything)

**Issue:** These are dangerous for production use

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Isolate test database using in-memory SQLite**
   - Modify `tests/conftest.py` to override `DATABASE_URL`
   - Use `sqlite+aiosqlite:///:memory:` for tests
   - OR use a separate file: `sqlite+aiosqlite:///./data/test_battle_d.db`

2. **Add environment detection to database.py**
   - Check if running in pytest context
   - Refuse to run `drop_db()` on production database

### 6.2 Recommended

1. **Add safety check to `drop_db()`**
   - Require explicit confirmation for non-test databases
   - Log warnings when dropping tables

2. **Use pytest-asyncio in-memory database pattern**
   ```python
   # tests/conftest.py
   @pytest.fixture(scope="session")
   def test_engine():
       return create_async_engine("sqlite+aiosqlite:///:memory:")
   ```

3. **Document database management**
   - Add section to CONTRIBUTING.md or TESTING.md
   - Explain how to reset database manually

### 6.3 Nice-to-Have (Future)

1. **Add database backup before test runs**
   - Automatic backup of `./data/battle_d.db`
   - Restore on failure

2. **Add CLI command for database reset**
   ```bash
   python -m app.cli db:reset  # Interactive confirmation
   python -m app.cli db:seed   # Run seed script
   ```

---

## 7. Appendix: Reference Material

### 7.1 Files Affected

| File | Line | Issue |
|------|------|-------|
| `tests/conftest.py` | 20-36 | Test fixture purges production DB |
| `tests/e2e/conftest.py` | - | Inherits from main conftest |
| `app/db/database.py` | 63-69 | `drop_db()` has no safety checks |
| `app/config.py` | 49-68 | No test database configuration |

### 7.2 Pattern Scan Results

**Pattern searched:** `drop_db`, `drop_all`, `create_all` usage without test isolation

**Search command:**
```bash
grep -rn "drop_db\|drop_all\|create_all" app/ tests/
```

**Results:**
| File | Line | Description |
|------|------|-------------|
| `app/db/database.py` | 60 | `Base.metadata.create_all` - used by init_db |
| `app/db/database.py` | 69 | `Base.metadata.drop_all` - DANGEROUS |
| `tests/conftest.py` | 28 | Calls `drop_db()` - PURGES PROD DB |
| `tests/conftest.py` | 31 | Calls `init_db()` - recreates without alembic |
| `tests/conftest.py` | 36 | Calls `drop_db()` again - PURGES PROD DB |

**Decision:**
- [x] Fix all in this feature - single root cause in test configuration

### 7.3 User Confirmation

- [ ] User confirmed problem statement
- [ ] User validated scenarios
- [ ] User approved requirements
