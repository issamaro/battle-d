# Feature Specification: Test Database Isolation Architecture

**Date:** 2025-12-18
**Status:** Awaiting User Approval
**Type:** Infrastructure Bug Fix + Methodology Update

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Impact Analysis](#4-impact-analysis)
5. [Business Rules & Acceptance Criteria](#5-business-rules--acceptance-criteria)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Methodology Updates Required](#7-methodology-updates-required)
8. [Appendix](#8-appendix)

---

## 1. Problem Statement

**Every time the developer runs tests, the local development database (`./data/battle_d.db`) gets purged**, causing a 500 error "no such table: tournaments". This is a recurring infrastructure bug that breaks the development workflow and wastes significant time on database resets.

**Root Cause:** 10+ test files directly import `async_session_maker` from `app.db.database` (production), bypassing the isolated test database configured in `tests/conftest.py`.

---

## 2. Executive Summary

### Scope
Complete reconfiguration of testing infrastructure to ensure **100% database isolation** between tests and development.

### What Works
| Component | Status |
|-----------|--------|
| Main conftest.py test isolation (`_test_session_maker`) | Partial - only used by E2E tests |
| E2E conftest.py database override | Production Ready |
| Async conftest.py session sharing | Production Ready |
| pytest.ini configuration | Production Ready |
| TESTING.md documentation | Needs Update |

### What's Broken
| Issue | Type | Affected Files |
|-------|------|----------------|
| Direct import of production `async_session_maker` | BUG | 10 test files |
| No centralized test database export | GAP | tests/conftest.py |
| Inconsistent session maker usage across tests | BUG | All integration tests |
| TESTING.md doesn't document isolation pattern | GAP | TESTING.md |

### Impact Summary
- **10 test files** directly import production `async_session_maker`
- **~2,500+ lines** of test code affected
- **Methodology docs** need updates (TESTING.md, slash commands)

---

## 3. Root Cause Analysis

### The Architecture Problem

```
CURRENT STATE (BROKEN)
══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  app/db/database.py                                             │
│  ─────────────────────                                          │
│  async_session_maker = ... (PRODUCTION - ./data/battle_d.db)    │
│                           ▲                                     │
│                           │ DIRECT IMPORT (BUG!)                │
└───────────────────────────┼─────────────────────────────────────┘
                            │
    ┌───────────────────────┼────────────────────────┐
    │                       │                        │
    ▼                       ▼                        ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│ test_repos   │    │ test_models  │    │ test_*_integration   │
│ .py          │    │ .py          │    │ .py (6 files)        │
│              │    │              │    │                      │
│ Uses PROD DB │    │ Uses PROD DB │    │ Uses PROD DB         │
└──────────────┘    └──────────────┘    └──────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │  tests/conftest.py                                       │
    │  ──────────────────                                      │
    │  _test_session_maker = ... (IN-MEMORY - isolated)        │
    │                           ▲                              │
    │                           │ ONLY used by E2E tests       │
    └───────────────────────────┼──────────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │ tests/e2e/*.py       │
                    │                      │
                    │ Uses ISOLATED DB     │
                    │ (CORRECT!)           │
                    └──────────────────────┘
```

### Files Directly Importing Production Database

| File | Line | Usage Pattern |
|------|------|---------------|
| `test_repositories.py` | 16 | `from app.db.database import async_session_maker` |
| `test_models.py` | 20 | `from app.db.database import async_session_maker` |
| `test_crud_workflows.py` | 7 | `from app.db.database import async_session_maker` |
| `test_auth.py` | 10 | `from app.db.database import async_session_maker` |
| `test_dancer_service_integration.py` | 15 | `from app.db.database import async_session_maker` |
| `test_event_service_integration.py` | 14 | `from app.db.database import async_session_maker` |
| `test_tournament_service_integration.py` | 16 | `from app.db.database import async_session_maker` |
| `test_performer_service_integration.py` | 15 | `from app.db.database import async_session_maker` |
| `test_battle_results_encoding_integration.py` | 16 | `from app.db.database import async_session_maker` |
| `tests/e2e/async_conftest.py` | 33 | `from app.db.database import async_session_maker` |

### Why Previous Fix Was Incomplete

The previous fix only updated:
1. `tests/conftest.py` - Created `_test_session_maker`
2. `tests/e2e/conftest.py` - Updated to use `_test_session_maker`

But **did NOT update**:
- 10 test files that directly import `async_session_maker`
- These files bypass the fixture entirely

---

## 4. Impact Analysis

### Test Files Requiring Changes

#### Tier 1: Core Integration Tests (HIGH IMPACT)
| File | Lines | Changes Required |
|------|-------|------------------|
| `test_repositories.py` | 369 | Replace import + all usages |
| `test_models.py` | ~180 | Replace import + all usages |
| `test_crud_workflows.py` | 316 | Replace import + fixture usage |

#### Tier 2: Service Integration Tests (MEDIUM IMPACT)
| File | Lines | Changes Required |
|------|-------|------------------|
| `test_dancer_service_integration.py` | ~110 | Replace import |
| `test_event_service_integration.py` | ~300 | Replace import |
| `test_tournament_service_integration.py` | ~200 | Replace import |
| `test_performer_service_integration.py` | ~110 | Replace import |
| `test_battle_results_encoding_integration.py` | 220 | Replace import |

#### Tier 3: Other Tests (LOW IMPACT)
| File | Lines | Changes Required |
|------|-------|------------------|
| `test_auth.py` | ~100 | Replace import |
| `tests/e2e/async_conftest.py` | 368 | Update imports |

### Documentation Requiring Updates

| Document | Section | Update Required |
|----------|---------|-----------------|
| `TESTING.md` | Database Fixtures | Add isolation pattern |
| `TESTING.md` | Quick Start | Add isolation warning |
| `TESTING.md` | Service Integration Tests | Update pattern |
| `.claude/commands/implement-*.md` | Testing sections | Add isolation guidance |

---

## 5. Business Rules & Acceptance Criteria

### 5.1 Test Database Isolation

**Business Rule BR-TEST-001: Complete Isolation**
> All tests must use a completely isolated in-memory database. No test operation may ever read from or write to the development database (`./data/battle_d.db`).

**Acceptance Criteria:**
```gherkin
Feature: Test Database Isolation
  As a developer
  I want tests to use an isolated database
  So that development data is never lost

  Scenario: Running full test suite preserves dev database
    Given I have a development database with 3 users and 40 dancers
    When I run "pytest tests/" (all tests)
    Then my development database still has 3 users and 40 dancers
    And no test data appears in the development database

  Scenario: Integration tests use isolated database
    Given test_repositories.py imports the test session maker
    When test_repositories.py runs
    Then it creates/drops tables only in the in-memory database
    And ./data/battle_d.db is never touched

  Scenario: Service integration tests use isolated database
    Given test_event_service_integration.py imports the test session maker
    When the test creates tournaments and battles
    Then all data exists only in the in-memory database
    And ./data/battle_d.db is never touched
```

### 5.2 Centralized Test Database Access

**Business Rule BR-TEST-002: Single Source of Truth**
> All test files must import database access from `tests/conftest.py`, never from `app/db/database.py`.

**Acceptance Criteria:**
```gherkin
Feature: Centralized Test Database Access
  As a developer
  I want one place to configure test database
  So that isolation is enforced consistently

  Scenario: Test file imports from conftest
    Given a new integration test file is created
    When the developer needs database access
    Then they import from "tests.conftest import test_session_maker"
    And NOT from "app.db.database import async_session_maker"

  Scenario: Grep for production imports finds zero
    Given all test files are updated
    When I run "grep -r 'from app.db.database import async_session_maker' tests/"
    Then the result is empty (no matches)
```

### 5.3 Documentation Accuracy

**Business Rule BR-TEST-003: Accurate Documentation**
> TESTING.md must document the isolation pattern and warn against direct production imports.

**Acceptance Criteria:**
- [ ] TESTING.md contains "Database Isolation" section
- [ ] TESTING.md contains BLOCKING warning about production imports
- [ ] Example patterns show correct import from conftest
- [ ] Anti-pattern section shows what NOT to do

---

## 6. Implementation Recommendations

### 6.1 Critical (BLOCKING - Before Any Other Work)

**Step 1: Export test session maker from conftest**

Update `tests/conftest.py` to export `test_session_maker` (without underscore) as public API:

```python
# tests/conftest.py

# Public API - use this in all test files
test_session_maker = _test_session_maker  # Alias for external use
```

**Step 2: Update all 10 test files**

Replace in each file:
```python
# BEFORE (BUG):
from app.db.database import async_session_maker

# AFTER (FIXED):
from tests.conftest import test_session_maker
```

And update usage:
```python
# BEFORE:
async with async_session_maker() as session:

# AFTER:
async with test_session_maker() as session:
```

**Step 3: Verify isolation**

```bash
# Before tests
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM dancers;"

# Run tests
pytest tests/

# After tests - counts should be identical
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM dancers;"
```

### 6.2 Recommended

**Step 4: Add safety check to app/db/database.py**

```python
# app/db/database.py

async def drop_db():
    """Drop all database tables.

    WARNING: This deletes all data! Only use for testing.
    SAFETY: Refuses to drop production database.
    """
    import os
    if os.getenv("PYTEST_CURRENT_TEST") is None:
        raise RuntimeError(
            "drop_db() called outside of pytest! "
            "This would delete your development database. "
            "Use alembic for migrations instead."
        )
    # ... existing implementation
```

**Step 5: Update TESTING.md**

Add new section after "Test Categories":

```markdown
## Database Isolation (BLOCKING)

**All tests MUST use the isolated test database. NEVER import from `app.db.database`.**

### Correct Pattern
```python
# tests/test_something.py
from tests.conftest import test_session_maker

@pytest.mark.asyncio
async def test_example():
    async with test_session_maker() as session:
        # Uses in-memory SQLite - never touches ./data/battle_d.db
        repo = SomeRepository(session)
        ...
```

### Anti-Pattern (DO NOT USE)
```python
# WRONG - This uses production database!
from app.db.database import async_session_maker  # <-- NEVER DO THIS IN TESTS

async def test_example():
    async with async_session_maker() as session:  # <-- PURGES YOUR DEV DATA!
        ...
```

### Why This Matters
Direct import from `app.db.database` bypasses test isolation and:
- Purges your development database on every test run
- Causes "no such table" errors after tests
- Wastes developer time on database resets

See: workbench/FEATURE_SPEC_2025-12-18_TEST-DATABASE-ISOLATION.md
```

### 6.3 Nice-to-Have (Future)

1. **Add pre-commit hook** to catch production imports
2. **Add CI check** that fails if production imports detected
3. **Create pytest plugin** that validates isolation

---

## 7. Methodology Updates Required

### 7.1 Slash Commands to Update

The following slash commands should be updated to include test isolation guidance:

| Command | File | Update |
|---------|------|--------|
| `/implement-feature` | `.claude/commands/implement-feature.md` | Add testing isolation section |
| `/implement-bug-fix` | `.claude/commands/implement-bug-fix.md` | Add testing isolation warning |
| `/analyze-feature` | `.claude/commands/analyze-feature.md` | Add pattern scan for test imports |

### 7.2 TESTING.md Updates

| Section | Current | Update To |
|---------|---------|-----------|
| Overview | No isolation mention | Add isolation as first principle |
| Service Integration Tests | Shows `async_session_maker` | Change to `test_session_maker` |
| Database Fixtures | Generic | Add specific isolation pattern |
| Best Practices | No isolation rule | Add as #1 practice |

### 7.3 New Conventions Document Section

Add to CONVENTIONS.md or TESTING.md:

```markdown
## Test Database Conventions

### DO:
- Import `test_session_maker` from `tests.conftest`
- Use in-memory SQLite for all tests
- Drop/create tables in fixture (autouse)

### DON'T:
- Import `async_session_maker` from `app.db.database` in tests
- Access `./data/battle_d.db` from tests
- Use `init_db()` or `drop_db()` from production code
```

---

## 8. Appendix

### 8.1 Pattern Scan Results

**Pattern searched:** `from app.db.database import async_session_maker`

**Command:**
```bash
grep -rn "from app.db.database import async_session_maker" tests/
```

**Results:**
| File | Line | Status |
|------|------|--------|
| tests/test_crud_workflows.py | 7 | NEEDS FIX |
| tests/test_battle_results_encoding_integration.py | 16 | NEEDS FIX |
| tests/test_performer_service_integration.py | 15 | NEEDS FIX |
| tests/e2e/async_conftest.py | 33 | NEEDS FIX |
| tests/test_repositories.py | 16 | NEEDS FIX |
| tests/e2e/test_session_isolation_fix.py | 18 | NEEDS FIX |
| tests/test_event_service_integration.py | 14 | NEEDS FIX |
| tests/test_dancer_service_integration.py | 15 | NEEDS FIX |
| tests/test_tournament_service_integration.py | 16 | NEEDS FIX |
| tests/test_auth.py | 10 | NEEDS FIX |
| tests/test_models.py | 20 | NEEDS FIX |

**Total: 11 files need updates**

### 8.2 Verification Commands

After implementation, verify with:

```bash
# 1. No production imports in tests
grep -r "from app.db.database import async_session_maker" tests/
# Expected: No output

# 2. Database preserved after test run
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users;"  # Before
pytest tests/ -v
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users;"  # After (same count)

# 3. All tests still pass
pytest tests/ -v --tb=short
```

### 8.3 User Confirmation

- [ ] User confirmed problem statement
- [ ] User validated scenarios match their vision
- [ ] User approved implementation approach
- [ ] User approved methodology updates

---

## Next Steps

1. **User reviews** this specification
2. **User approves** implementation approach
3. Run `/plan-implementation FEATURE_SPEC_2025-12-18_TEST-DATABASE-ISOLATION.md`
4. Implement changes across all 11 test files
5. Update TESTING.md documentation
6. Verify with full test suite + database preservation check
