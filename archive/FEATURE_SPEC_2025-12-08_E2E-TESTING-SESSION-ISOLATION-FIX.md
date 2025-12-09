# Feature Specification: E2E Testing Session Isolation Fix

**Date:** 2025-12-08
**Status:** Awaiting Technical Design

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

**User's exact words:** "There is a recurring problem that is the way we test. Due to session isolation principle which I don't know a lot about (not a async or db master), we can't make proper E2E tests, which has as a consequence gherkin scenarios that are actually never really tested."

**Root cause:** Async test fixtures create database records in one session, but the synchronous TestClient uses a different session when making HTTP requests. Due to SQLAlchemy's transaction isolation, data committed in the fixture session is not visible to the TestClient's request session.

**Business impact:** Gherkin acceptance criteria defined in feature specs cannot be validated through automated E2E tests, reducing confidence in feature correctness and increasing reliance on manual testing.

---

## 2. Executive Summary

### Scope
Investigate and fix the database session isolation problem that prevents E2E tests from accessing fixture-created data.

### What Works ✅
| Feature | Status |
|---------|--------|
| Authentication via session cookies | Production Ready |
| HTTP-only workflows (create then verify in same request context) | Production Ready |
| HTMX partial response detection | Production Ready |
| Service integration tests (async throughout) | Production Ready |
| 460 tests, 69% coverage | Production Ready |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| Async fixture data invisible to TestClient | ARCHITECTURE | `tests/e2e/conftest.py` |
| Cannot test pre-existing data scenarios | GAP | All E2E tests |
| Gherkin scenarios not truly validated | GAP | Feature specs |

### Key Business Rules Defined
- **BR-TEST-001:** E2E tests must be able to verify application behavior with pre-populated database state
- **BR-TEST-002:** Gherkin acceptance criteria must have corresponding automated tests

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 CURRENT FLOW: Async Fixture + Sync TestClient (BROKEN)
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  STEP 1: setup_test_database() [autouse, async]                          │
  │  • await drop_db() - Clear tables                                        │
  │  • await init_db() - Create tables                                       │
  │  Result: Fresh empty database                                            │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  STEP 2: e2e_test_users() fixture [async]                                │
  │  • async with async_session_maker() as session:                          │
  │      └─ Create users (admin, staff, mc, judge)                           │
  │      └─ await session.commit()                                           │
  │  • Session CLOSES after yield                                            │
  │  🚨 PROBLEM: Data committed but in isolated transaction                  │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  STEP 3: create_e2e_tournament() factory [async]                         │
  │  • async with async_session_maker() as session:                          │
  │      └─ Create tournament, categories, dancers, performers               │
  │      └─ await session.commit()                                           │
  │  • Returns data objects                                                  │
  │  🚨 PROBLEM: This session also closes, data isolation continues          │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  STEP 4: TestClient makes HTTP request [sync]                            │
  │  • client.get(f"/tournaments/{tournament.id}")                           │
  │  • Route calls get_db() dependency                                       │
  │  • get_db() creates NEW async session                                    │
  │  🚨 RESULT: Returns 404 - tournament not found!                          │
  │                                                                          │
  │  Why? The route's session cannot see data committed in fixture sessions  │
  └──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 DESIRED FLOW: All Test Operations Share Session (TO BE IMPLEMENTED)
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  OPTION A: Use httpx.AsyncClient with Shared Session                     │
  │                                                                          │
  │  @pytest.mark.asyncio                                                    │
  │  async def test_tournament_view(async_session):                          │
  │      async with async_session() as session:                              │
  │          # Create data                                                   │
  │          tournament = await create_tournament(session)                   │
  │          await session.commit()                                          │
  │                                                                          │
  │          # Override get_db to return same session                        │
  │          app.dependency_overrides[get_db] = lambda: session              │
  │                                                                          │
  │          async with AsyncClient(app=app) as client:                      │
  │              response = await client.get(f"/tournaments/{tournament.id}")│
  │              assert response.status_code == 200  ✅ WORKS!               │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  OPTION B: Use Factory Fixtures That Create Via HTTP                     │
  │                                                                          │
  │  def test_tournament_view(staff_client):                                 │
  │      # Create via HTTP (uses route's session)                            │
  │      response = staff_client.post("/tournaments/create", data={...})     │
  │      tournament_id = extract_id_from_redirect(response)                  │
  │                                                                          │
  │      # Verify via HTTP (same session context)                            │
  │      response = staff_client.get(f"/tournaments/{tournament_id}")        │
  │      assert response.status_code == 200  ✅ WORKS!                       │
  │                                                                          │
  │  🚨 LIMITATION: Can only test what HTTP endpoints allow                  │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  OPTION C: Async TestClient with lifespan/startup Event                  │
  │                                                                          │
  │  Use pytest-asyncio with proper async test setup that:                   │
  │  1. Creates shared database session at test start                        │
  │  2. Overrides get_db() to return that session                            │
  │  3. Uses httpx.AsyncClient for requests                                  │
  │  4. All operations happen in same transaction                            │
  │  5. Rollback at end (no actual commit to DB)                             │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 E2E Tests Must Access Pre-Created Data

**Business Rule BR-TEST-001: Fixture Data Visibility**
> Test fixtures that create database records must make that data visible to subsequent TestClient HTTP requests within the same test.

**Acceptance Criteria:**
```gherkin
Feature: E2E tests can access fixture-created data
  As a developer
  I want E2E tests to see data created in fixtures
  So that I can test scenarios with pre-existing database state

Scenario: Test can view tournament created in fixture
  Given a tournament "Summer Battle 2024" exists in PRESELECTION phase
  And the tournament has 2 categories with 8 performers each
  When I make an HTTP GET request to /tournaments/{tournament_id}
  Then the response status should be 200
  And the response should contain "Summer Battle 2024"

Scenario: Test can view battle queue with real battles
  Given a tournament in PRESELECTION phase
  And 4 pending battles exist in the queue
  When I navigate to /event/{tournament_id}/queue via HTTP
  Then the response should contain 4 battle cards
  And each battle card should show performer names

Scenario: Test can start a pre-existing battle
  Given a battle exists with status PENDING
  And I am authenticated as MC
  When I POST to /battles/{battle_id}/start
  Then the battle status should change to ACTIVE
  And the response should redirect to command center
```

### 4.2 Gherkin Scenarios Must Have Automated Tests

**Business Rule BR-TEST-002: Acceptance Criteria Coverage**
> Every Gherkin scenario defined in a feature specification should have a corresponding automated test that validates it.

**Acceptance Criteria:**
```gherkin
Feature: Gherkin scenarios are actually tested
  As a project stakeholder
  I want acceptance criteria to be verified automatically
  So that I have confidence features work as specified

Scenario: Feature spec scenarios map to tests
  Given a feature specification with Gherkin scenarios
  When the feature is implemented
  Then each scenario should have a corresponding test function
  And the test should validate the Given/When/Then conditions

Scenario: Tests prove scenarios pass
  Given a Gherkin scenario: "Given tournament in PRESELECTION, When MC views command center, Then page loads"
  When the automated test runs
  Then it should create the tournament in PRESELECTION
  And it should authenticate as MC
  And it should make HTTP request to command center
  And it should verify page loads successfully (200 status)
```

---

## 5. Current State Analysis

### 5.1 Session Isolation Mechanism

**The Technical Problem:**

SQLAlchemy async sessions have transaction isolation. When you:
1. Create a session, add data, commit, and close the session
2. Create a NEW session and query

The second session may not immediately see the first session's data due to:
- **Transaction isolation level** (default: READ COMMITTED in PostgreSQL/SQLite)
- **Connection pooling** (different connections may have different snapshots)
- **Async context** (each `async with async_session_maker()` creates isolated context)

**Current Implementation in `tests/e2e/conftest.py`:**

```python
# Fixture creates data in Session A
@pytest_asyncio.fixture(scope="function")
async def e2e_test_users():
    async with async_session_maker() as session:  # Session A
        user_repo = UserRepository(session)
        await user_repo.create_user(...)
        await session.commit()  # Commits in Session A
    yield  # Session A is CLOSED

# TestClient uses Session B (via get_db())
@pytest.fixture
def admin_client(e2e_client, e2e_test_users):
    # e2e_client makes requests
    # Each request calls get_db() which creates Session B
    # Session B cannot see Session A's committed data!
```

### 5.2 Why Authentication Works But Data Doesn't

**Authentication works** because `get_session_cookie()`:
1. Generates a magic link token (no DB lookup)
2. Calls `/auth/verify?token=...`
3. The verify route creates/finds the user IN ITS OWN SESSION
4. Returns a session cookie

The user IS created in the fixture, but the `/auth/verify` route also creates/upserts the user if needed, so it appears to work.

**Pre-created data doesn't work** because:
- Tournament created in fixture session
- Route queries for tournament in different session
- Tournament not visible = 404

### 5.3 Current Workarounds

**Workaround 1: HTTP-based creation (used in `test_crud_workflows.py`)**
```python
# Create via HTTP - works because creation and verification use same route session
response = client.post("/tournaments/create", data={...})
response = client.get("/tournaments")  # Can see it!
```

**Workaround 2: Service integration tests (bypass HTTP)**
```python
# All async, all same session
async with async_session_maker() as session:
    service = TournamentService(TournamentRepository(session))
    tournament = await service.create_tournament(...)
    result = await service.get_tournament(tournament.id)  # Works!
```

### 5.4 Tests Removed Due to This Limitation

From `tests/e2e/test_event_mode.py:183-187`:
```python
# NOTE: Tests with real battle data (TestBattleWorkflowWithRealData,
# TestEventModeWithRealTournament) removed due to database session isolation.
# Data created in async fixtures is not visible to TestClient.
# These code paths are covered by service integration tests instead
```

**What we CANNOT test currently:**
- View pre-created tournament in command center
- Start a pre-created battle
- Encode results for pre-created battle
- See real performer data in battle cards
- Multi-step workflows on pre-existing data

---

## 6. Implementation Recommendations

### 6.1 Critical (Required for Proper E2E Testing)

1. **Implement httpx.AsyncClient with Session Override**

   Replace sync TestClient with async httpx.AsyncClient and override `get_db()` to return the test's session:

   ```python
   @pytest.mark.asyncio
   async def test_view_tournament(async_session):
       async with async_session() as session:
           # Create data in THIS session
           repo = TournamentRepository(session)
           tournament = await repo.create_tournament("Test")
           await session.flush()  # Make visible within transaction

           # Override get_db to return THIS session
           async def get_test_db():
               yield session

           app.dependency_overrides[get_db] = get_test_db

           try:
               async with AsyncClient(app=app, base_url="http://test") as client:
                   response = await client.get(f"/tournaments/{tournament.id}")
                   assert response.status_code == 200
           finally:
               app.dependency_overrides.clear()
   ```

   **Pros:**
   - Fixture data is visible to routes
   - Can test any scenario
   - Proper async throughout

   **Cons:**
   - Requires rewriting E2E test fixtures
   - Tests become async
   - Need to manage session lifecycle carefully

2. **Create Shared Session Fixture**

   ```python
   @pytest_asyncio.fixture
   async def db_session():
       """Provide a shared session for the entire test."""
       async with async_session_maker() as session:
           yield session
           await session.rollback()  # Clean up without committing
   ```

### 6.2 Recommended

1. **Add Test for Session Isolation Fix**

   Create a test that specifically validates the fix works:
   ```python
   @pytest.mark.asyncio
   async def test_fixture_data_visible_to_client():
       """Verify fixture-created data is accessible via HTTP."""
       # This test should pass after the fix is implemented
   ```

2. **Document the Pattern in TESTING.md**

   Add section explaining:
   - Why session isolation happens
   - How to write E2E tests with pre-created data
   - When to use sync vs async test patterns

3. **Migrate Critical E2E Tests**

   Priority tests to migrate:
   - Event mode command center with real tournament
   - Battle workflow with pre-created battles
   - Phase advancement with real performer data

### 6.3 Nice-to-Have (Future)

1. **Transaction Rollback Pattern**

   Use transactions that rollback at test end instead of committing:
   ```python
   async with async_session_maker() as session:
       async with session.begin():
           # All test operations
           # Rollback happens automatically - faster cleanup
   ```

2. **Pytest Plugin for Async E2E**

   Create a custom pytest plugin that handles session management automatically.

3. **Gherkin-to-Test Mapper**

   Tool that extracts Gherkin scenarios from feature specs and generates test stubs.

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Why does authentication work if session isolation is the problem?
  - **A:** Authentication generates a token (no DB) and the verify route creates/upserts the user in its own session. The magic link system doesn't depend on seeing fixture-created users.

- **Q:** Can we just use `asyncio.run()` in sync fixtures?
  - **A:** Partial solution. `asyncio.run()` can call async code but doesn't solve the session isolation - you'd still create data in one session and query in another.

- **Q:** What about using `scope="module"` for fixtures?
  - **A:** Doesn't help. Session isolation is per-session, not per-fixture-scope. Even module-scoped fixtures create isolated sessions.

- **Q:** Can we disable transaction isolation?
  - **A:** Not recommended. Transaction isolation exists for data integrity. Better to design tests to work within the isolation model.

### 7.2 Technical References

**SQLAlchemy Async Session Docs:**
- Sessions are not thread-safe and should not be shared across async contexts
- Each `async with async_session_maker()` creates a new session with its own transaction

**FastAPI TestClient:**
- TestClient is synchronous (uses Starlette's TestClient)
- Uses `requests` library internally
- Not designed for async database patterns

**httpx.AsyncClient:**
- Async HTTP client
- Works naturally with async test fixtures
- Recommended for testing async FastAPI apps

### 7.3 Example Implementation (Reference)

**Working E2E test pattern with AsyncClient:**
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.dependencies import get_db
from app.db.database import async_session_maker

@pytest.fixture
async def test_session():
    """Shared session for test and routes."""
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            # Rollback happens automatically

@pytest.mark.asyncio
async def test_tournament_workflow(test_session: AsyncSession):
    """E2E test with fixture-created data."""
    # Override get_db to use test session
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create test data
        from app.repositories.tournament import TournamentRepository
        repo = TournamentRepository(test_session)
        tournament = await repo.create_tournament("E2E Test Tournament")
        await test_session.flush()

        # Make HTTP request - will use same session!
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/tournaments/{tournament.id}")
            assert response.status_code == 200
            assert b"E2E Test Tournament" in response.content
    finally:
        app.dependency_overrides.clear()
```

### 7.4 Prototype Test Results

Both approaches were prototyped in `tests/e2e/test_session_isolation_fix.py`:

**Results:**
```
TestAsyncClientApproach::test_fixture_data_visible_via_session_override PASSED
TestAsyncClientApproach::test_can_query_fixture_created_performers FAILED (404 - route doesn't exist)
TestHTTPOnlyApproach::test_create_and_view_tournament_via_http PASSED
TestHTTPOnlyApproach::test_create_tournament_with_category_via_http FAILED (wrong endpoint URL)
TestCompareApproaches::test_async_approach_can_create_complex_scenario PASSED
```

**Key Findings:**

1. **AsyncClient + Session Override WORKS**
   - `test_fixture_data_visible_via_session_override`: Tournament created in fixture is visible to HTTP request
   - `test_async_approach_can_create_complex_scenario`: Can create tournament in PRESELECTION phase and access Event Mode command center

2. **HTTP-only Approach WORKS**
   - `test_create_and_view_tournament_via_http`: Create tournament via POST, then GET shows it

3. **Failures are implementation details, not architecture issues:**
   - One failed because the performer page route doesn't exist at that URL
   - Other failed because category creation endpoint URL is different

**Recommendation:** AsyncClient approach is more flexible and allows testing complex scenarios (like Event Mode with pre-created battles) that HTTP-only cannot achieve.

### 7.5 User Confirmation

- [ ] User confirmed problem statement
- [ ] User validated scenarios match their vision
- [ ] User approved requirements
- [ ] User prefers implementation approach (A, B, or C from diagram)
