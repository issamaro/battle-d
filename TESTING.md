# Testing Guide
**Level 3: Operational** | Last Updated: 2025-12-08

This document describes the testing strategy, setup, and practices for the Battle-D web application.

## Prerequisites

Before reading this document, familiarize yourself with:
- [ROADMAP.md](ROADMAP.md) - Development phases and testing milestones
- [ARCHITECTURE.md](ARCHITECTURE.md) - Service patterns and code organization

---

## Overview

The project uses pytest as the primary testing framework with support for async tests and code coverage reporting. As of Phase 1, we maintain 100% test pass rate (97+ tests passing, 8 skipped).

---

## Database Isolation (BLOCKING)

**All tests MUST use the isolated in-memory test database. NEVER import `async_session_maker` from `app.db.database` in test files.**

This is the most important testing rule. Violating it will **purge your development database** on every test run.

### Correct Pattern

```python
# tests/test_something.py
from tests.conftest import test_session_maker

@pytest.mark.asyncio
async def test_example():
    async with test_session_maker() as session:
        # Uses in-memory SQLite - NEVER touches ./data/battle_d.db
        repo = SomeRepository(session)
        result = await repo.create(...)
        assert result is not None
```

### Anti-Pattern (DO NOT USE)

```python
# WRONG - This uses production database!
from app.db.database import async_session_maker  # <-- NEVER DO THIS IN TESTS

@pytest.mark.asyncio
async def test_example():
    async with async_session_maker() as session:  # <-- PURGES YOUR DEV DATA!
        ...
```

### Why This Matters

Direct import from `app.db.database` bypasses test isolation and:
- **Purges your development database** on every test run
- Causes "no such table: tournaments" errors after tests
- Wastes developer time on database resets
- Can lose hours of manually created test data

### How It Works

The test isolation is configured in `tests/conftest.py`:

1. **In-memory SQLite database** - Created fresh for each test
2. **Automatic table creation** - `setup_test_database` fixture (autouse=True)
3. **Automatic cleanup** - Tables dropped after each test
4. **Zero impact on dev database** - `./data/battle_d.db` is never touched

### Verification

After running tests, verify your dev database is intact:

```bash
# Before tests
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM dancers;"

# Run tests
pytest tests/

# After tests - counts MUST be identical
sqlite3 data/battle_d.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM dancers;"
```

See: `workbench/FEATURE_SPEC_2025-12-18_TEST-DATABASE-ISOLATION.md` for technical details.

### TestClient Fixture Pattern (CRITICAL)

**Every TestClient fixture MUST override `get_db` to use the isolated test database.**

Without this override, HTTP requests from TestClient bypass the test database and write directly to the production database (`./data/battle_d.db`), polluting your development data.

**Required Pattern:**
```python
from app.db.database import get_db
from tests.conftest import test_session_maker

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

    app.dependency_overrides[get_db] = get_test_db  # REQUIRED!

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

**Why This Is Critical:**

TestClient creates its own event loop and session context. Even if your test file imports `test_session_maker`, HTTP requests through TestClient will use the production `get_db` dependency unless overridden.

```python
# ❌ WRONG - Missing get_db override
@pytest.fixture
def client():
    return TestClient(app)  # HTTP requests use production DB!

# ✅ CORRECT - get_db override ensures test DB isolation
@pytest.fixture
def client():
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**Symptoms of Missing Override:**
- Test entries appear in dev database (e.g., "HTTP Test", "Cat Test" tournaments)
- Tests pass but leave garbage data behind
- Development database gets polluted over time

## Test Structure

```
tests/
├── __init__.py                      # Test configuration and fixtures
├── test_auth.py                     # Authentication and magic link tests
├── test_permissions.py              # Role-based access control tests
├── test_models.py                   # Database model tests
├── test_repositories.py             # Repository layer tests
├── test_tournament_calculations.py  # Calculation utility tests (24 tests)
├── test_crud_workflows.py           # Integration CRUD tests
├── test_brevo_provider.py          # Brevo email provider tests
├── test_gmail_provider.py          # Gmail email provider tests
├── test_email_templates.py         # Email template tests
└── reports/                         # Generated test reports (gitignored)
    ├── coverage-html/               # HTML coverage reports
    └── test-report.html             # Test execution report
```

## Quick Start

### Running All Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Running Specific Test Files

```bash
# Test authentication only
pytest tests/test_auth.py

# Test permissions only
pytest tests/test_permissions.py

# Test tournament calculations only
pytest tests/test_tournament_calculations.py
```

### Running Specific Tests

```bash
# Run a specific test function
pytest tests/test_auth.py::test_login_page_renders

# Run tests matching a pattern
pytest -k "magic_link"
```

### Verbose Output

```bash
pytest -v
```

## Test Coverage

### Current Coverage Status

Phase 1 maintains high test coverage across core functionality:

**Phase 0 Tests:**
- **Authentication**: Magic link generation, validation, expiry (15 tests)
- **Permissions**: Role-based access control (Admin, Staff, MC, Judge) (11 tests)
- **Email Providers**: Brevo, Gmail, Resend, Console providers (13 tests)
- **Email Templates**: Template generation and validation (11 tests)

**Phase 1 Tests:**
- **Database Models**: User, Dancer, Tournament, Category, Performer models (14 tests)
- **Repositories**: CRUD operations for all entities
- **Tournament Calculations**: Min performers, pool distribution, capacity (24 tests)
- **CRUD Workflows**: Integration tests for dancer, tournament, registration flows (9 tests)
- **Validators**: Phase transition validation
- **Service Layer**: DancerService, TournamentService, PerformerService

### Viewing Coverage Reports

After running tests with coverage:

```bash
# Terminal summary
pytest --cov=app --cov-report=term

# Generate and open HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS
```

### Coverage Requirements

- **Minimum coverage**: Not enforced in Phase 0
- **Target for Phase 1+**: 90% coverage
- **Critical paths**: 100% coverage (auth, permissions, payment)

## Test Categories

### Unit Tests (For Isolated Logic Only)

Unit tests focus on individual components and functions in isolation.

**Use unit tests for:**
- Pure calculation functions (no DB)
- Complex branching logic worth isolating
- External API mocking

**Current test files:**
- `test_auth.py` - Authentication flows and token management
- `test_permissions.py` - Decorator-based access control
- `test_tournament_calculations.py` - Tournament capacity and pool calculations

**IMPORTANT:** Do NOT use mocked unit tests for service methods that interact with repositories. Use Service Integration Tests instead.

### Service Integration Tests (PRIMARY for Services)

**This is the PRIMARY test type for service methods.**

Service integration tests verify that services work correctly with REAL repositories and the actual database. Unlike mocked unit tests, integration tests catch bugs like:

- **Invalid enum references** (e.g., `BattleStatus.IN_PROGRESS` doesn't exist)
- **Repository method signature mismatches** (e.g., `create()` accepts `**kwargs` vs model instance)
- **Lazy loading and relationship issues**
- **Transaction/session management bugs**

**Why Integration Tests First (Not Mocked Unit Tests):**

Mocked unit tests only verify that code *calls* dependencies correctly:
```python
# BAD: This test passes even if BattleStatus.IN_PROGRESS doesn't exist!
battle_repo.get_by_category.return_value = []  # Mock returns empty list
# The filtering code never validates the enum value
```

Integration tests verify that code *works* with real components:
```python
# GOOD: This test FAILS if BattleStatus.IN_PROGRESS doesn't exist!
battle = Battle(status=BattleStatus.IN_PROGRESS, ...)  # Runtime error!
```

**Pattern:**
```python
from tests.conftest import test_session_maker  # IMPORTANT: Use isolated test DB!

@pytest.mark.asyncio
async def test_service_method_integration():
    """Integration test for service method."""
    async with test_session_maker() as session:
        # 1. Create REAL repositories (not mocks)
        battle_repo = BattleRepository(session)
        category_repo = CategoryRepository(session)
        service = BattleService(battle_repo, category_repo)

        # 2. Create REAL test data with REAL enum values
        battle = Battle(
            status=BattleStatus.PENDING,  # Real enum - validates at runtime!
            phase=BattlePhase.PRESELECTION,
            battle_type=BattleType.PRESELECTION,
            category_id=category.id,
        )
        await battle_repo.create(battle)

        # 3. Execute service method against REAL database
        result = await service.some_method(battle.id)

        # 4. Verify ACTUAL behavior and DB state
        assert result.success
        updated = await battle_repo.get_by_id(battle.id)
        assert updated.status == BattleStatus.COMPLETED
```

**When to Use Mocked Unit Tests Instead:**
- Pure calculation functions that don't touch the database
- Complex branching logic worth isolating
- External API calls (mock the external API, not the repository)

**Current Service Integration Test Files:**
- `test_repositories.py` - Repository integration tests (good pattern to follow)
- `tests/test_*_integration.py` - Service integration tests

### Route Integration Tests

Route integration tests verify HTTP endpoints work correctly:
- Request/response handling
- Authentication/authorization
- HTMX partial responses

### HTMX Interaction Tests

HTMX interactions require special testing patterns to verify partial updates, auto-refresh, and inline validation.

**Key Testing Requirements:**
- Test with `HX-Request` header to simulate HTMX requests
- Verify partial HTML responses (not full pages)
- Test auto-refresh polling endpoints
- Validate form preservation on errors

**Testing Auto-Refresh:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_battle_list_auto_refresh():
    """Test battle list auto-refresh returns partial HTML."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Simulate HTMX polling request
        response = await client.get(
            "/battles?category_id=test-uuid",
            headers={"HX-Request": "true"}
        )

    assert response.status_code == 200
    # Should return partial HTML (battle grid), not full page
    assert "<html>" not in response.text  # No full page wrapper
    assert "battle-grid" in response.text  # Just the grid content
```

**Testing Partial Updates:**
```python
@pytest.mark.asyncio
async def test_start_battle_returns_updated_card():
    """Test starting battle returns updated battle card HTML."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Simulate HTMX form submission
        response = await client.post(
            "/battles/test-battle-id/start",
            headers={"HX-Request": "true"}
        )

    assert response.status_code == 200
    # Should return updated battle card HTML
    assert 'id="battle-card-' in response.text
    assert 'badge-active' in response.text  # Status changed to ACTIVE
```

**Testing Inline Validation:**
```python
@pytest.mark.asyncio
async def test_encode_battle_validation_preserves_form_data():
    """Test validation errors preserve form data via partial update."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit incomplete scores
        response = await client.post(
            "/battles/test-battle-id/encode",
            data={
                "score_performer1": "8.5",
                # Missing score_performer2
            },
            headers={"HX-Request": "true"}
        )

    # Should return form with errors and preserved data
    assert response.status_code == 200
    assert 'value="8.5"' in response.text  # Form data preserved
    assert "Missing score" in response.text  # Error message shown
    assert 'aria-invalid="true"' in response.text  # Accessibility
```

**Testing Form Submission with Errors:**
```python
@pytest.mark.asyncio
async def test_htmx_form_error_returns_partial_html():
    """Test HTMX form errors return partial HTML, not redirect."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/battles/test-battle-id/encode",
            data={"invalid": "data"},
            headers={"HX-Request": "true"},
            follow_redirects=False  # Don't follow redirects
        )

    # HTMX should get partial HTML, not redirect
    assert response.status_code == 200  # Not 302
    assert "flash-error" in response.text  # Error in response
```

**Testing HTMX Response Headers:**
```python
@pytest.mark.asyncio
async def test_htmx_response_includes_triggers():
    """Test HTMX responses include appropriate triggers."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/battles/test-battle-id/start",
            headers={"HX-Request": "true"}
        )

    # Check for HTMX response headers (if using triggers/events)
    # Example: HX-Trigger header for client-side events
    # assert "HX-Trigger" in response.headers  # Optional
```

**HTMX Testing Patterns:**

| Pattern | Test Focus | Assertion |
|---------|-----------|-----------|
| Auto-refresh | Polling endpoint returns partial HTML | No `<html>` tag, contains target content |
| Partial update | Form submission returns fragment | Specific element ID, updated content |
| Inline validation | Errors preserve form data | Input values retained, `aria-invalid` set |
| Quick actions | Button click updates single card | Card HTML returned, status changed |

**Common HTMX Testing Mistakes:**

- ❌ **Testing without HX-Request header**: Server may return full page instead of partial
- ❌ **Expecting redirects**: HTMX should get HTML response, not 302 redirect
- ❌ **Not checking partial HTML**: Verify no full page wrapper (`<html>`, `<head>`, `<body>`)
- ❌ **Ignoring accessibility**: Check `aria-invalid`, `aria-describedby` on errors

**Integration with Battle Results Encoding Service:**
```python
@pytest.mark.asyncio
async def test_battle_results_encoding_service_integration():
    """Test battle encoding via HTMX integrates with service layer."""
    # This tests the full stack:
    # HTMX request → Router → Service → Repository → Response

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test battle and performers
        # ... setup code ...

        # Encode battle via HTMX
        response = await client.post(
            f"/battles/{battle_id}/encode",
            data={
                "score_performer1": "9.0",
                "score_performer2": "8.5"
            },
            headers={"HX-Request": "true"}
        )

    # Verify service layer was called
    assert response.status_code == 200
    # Verify database was updated (transaction committed)
    # Verify performers have updated scores
```

**Test Files:**
- `tests/test_battle_routes.py` - HTMX battle route tests
- `tests/test_htmx_interactions.py` - Generic HTMX pattern tests (future)

### End-to-End Tests (Phase 3.6)

E2E tests verify complete user workflows through the HTTP interface using TestClient with real database.

**Location:** `tests/e2e/`

**Test Structure:**
```
tests/e2e/
├── __init__.py           # E2E utilities (HTMX helpers, response validators)
├── conftest.py           # E2E fixtures (authenticated clients, test data factories)
├── test_event_mode.py    # Event Mode workflow tests (MC)
├── test_tournament_management.py  # Tournament setup tests (Admin/Staff)
└── test_htmx_interactions.py      # HTMX partial response tests
```

**What E2E Tests Cover:**
- Complete user flows (Event Mode, Tournament Management)
- HTTP-level request/response cycle
- HTMX partial responses vs full page responses
- Authentication and authorization at route level
- Form validation and error handling

**Running E2E Tests:**
```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific E2E test file
pytest tests/e2e/test_event_mode.py -v

# Run E2E tests with coverage
pytest tests/e2e/ --cov=app/routers --cov-report=term-missing
```

**E2E Test Pattern:**
```python
def test_complete_battle_workflow(mc_client, create_e2e_tournament, create_e2e_battle):
    """Test complete battle workflow: view → start → encode."""
    import asyncio
    from app.models.tournament import TournamentPhase
    from app.models.battle import BattlePhase, BattleStatus

    # Setup - Create tournament in PRESELECTION phase with battles
    data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
    battle = asyncio.run(create_e2e_battle(
        category_id=data["categories"][0].id,
        phase=BattlePhase.PRESELECTION,
        performers=data["performers"][:2],
    ))

    # Act - Start battle via HTTP
    response = mc_client.post(f"/battles/{battle.id}/start", follow_redirects=False)

    # Assert - Verify redirect (success)
    assert response.status_code == 303

    # Act - Encode results via HTTP
    form_data = {f"score_{p.id}": "8.5" for p in data["performers"][:2]}
    response = mc_client.post(
        f"/battles/{battle.id}/encode",
        data=form_data,
        follow_redirects=False,
    )

    # Assert
    assert response.status_code == 303
```

**Authenticated Client Fixtures:**

E2E tests use pre-authenticated clients for each role:

```python
@pytest.fixture
def admin_client(client, e2e_test_users):
    """Test client authenticated as admin."""
    cookie = get_session_cookie(client, "admin@e2e-test.com", "admin")
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return client

@pytest.fixture
def staff_client(client, e2e_test_users):
    """Test client authenticated as staff."""
    cookie = get_session_cookie(client, "staff@e2e-test.com", "staff")
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return client

@pytest.fixture
def mc_client(client, e2e_test_users):
    """Test client authenticated as MC."""
    cookie = get_session_cookie(client, "mc@e2e-test.com", "mc")
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return client
```

**Test Data Factories:**

Factories create complete test scenarios:

```python
@pytest.fixture
def create_e2e_tournament():
    """Factory to create tournament with categories and performers."""
    async def _create(
        name: str = None,
        phase: TournamentPhase = TournamentPhase.REGISTRATION,
        num_categories: int = 1,
        performers_per_category: int = 4,
    ):
        # Creates tournament, categories, dancers, performers
        return {
            "tournament": tournament,
            "categories": categories,
            "dancers": dancers,
            "performers": performers,
        }
    return _create
```

**HTMX Helpers:**

Utilities for testing HTMX interactions:

```python
from tests.e2e import is_partial_html, htmx_headers

def test_event_queue_returns_partial(mc_client, create_e2e_tournament):
    """HTMX endpoint returns partial HTML."""
    data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))

    response = mc_client.get(
        f"/event/{data['tournament'].id}/queue",
        headers=htmx_headers(),  # {"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert is_partial_html(response.text)  # No <html> tag
```

**E2E vs Service Integration Tests:**

| Aspect | Service Integration | E2E Tests |
|--------|---------------------|-----------|
| Layer | Service + Repository | Full HTTP stack |
| Database | Real | Real |
| Authentication | None | Session cookies |
| HTTP | None | TestClient |
| HTMX | None | HX-Request headers |
| Use For | Business logic | User workflows |

**Priority User Flows Tested:**

1. **Event Mode (Critical)** - MC tournament day workflow
   - Command center access
   - Battle start
   - Results encoding (preselection, pools, tiebreak, finals)

2. **Tournament Management (High)** - Admin setup workflow
   - Tournament creation
   - Category management
   - Phase advancement

3. **HTMX Interactions (High)** - Partial response verification
   - All HTMX endpoints return partials
   - Full pages without HX-Request header

### Async E2E Tests (Session Sharing Pattern)

For E2E tests that need to access pre-created database data, use the async pattern with session sharing.

**The Problem:**
Standard E2E tests use sync TestClient, which creates separate database sessions. Data created in async fixtures is invisible to routes because of SQLAlchemy session isolation - each `async with async_session_maker()` creates an isolated transaction context.

**The Solution:**
Use `httpx.AsyncClient` with dependency override to share a single session between fixture data creation and HTTP request handling.

**Location:** `tests/e2e/async_conftest.py`

**Pattern:**
```python
@pytest.mark.asyncio
async def test_with_fixture_data(
    async_e2e_session,
    async_client_factory,
    create_async_tournament,
):
    """Test that can see fixture-created data."""
    # Create data - uses shared session
    tournament = await create_async_tournament(name="Test")

    # Make HTTP request - same session via dependency override
    async with async_client_factory("staff") as client:
        response = await client.get(f"/tournaments/{tournament.id}")
        assert response.status_code == 200  # Works!
```

**Key Fixtures:**

| Fixture | Purpose |
|---------|---------|
| `async_e2e_session` | Shared SQLAlchemy session for entire test |
| `async_client_factory(role)` | Creates authenticated AsyncClient with session override |
| `create_async_tournament` | Factory for tournaments |
| `create_async_category` | Factory for categories |
| `create_async_performer` | Factory for performers with dancers |
| `create_async_battle` | Factory for battles |
| `create_async_tournament_scenario` | Complete scenario factory (tournament + categories + performers) |

**When to Use Async E2E Tests:**
- Testing with pre-created data (tournaments, battles, performers)
- Multi-step workflows where data must persist between requests
- Validating Gherkin scenarios with specific database state
- Testing Event Mode with real battle data

**When to Use Sync E2E Tests:**
- Simple route tests without pre-created data
- Tests that only need HTTP-created data (create via POST, then GET)
- Tests where session isolation doesn't matter

**E2E Test Docstring Standard (BLOCKING)**

All E2E tests MUST include a Gherkin reference in their docstring. This ensures tests validate correct functional behavior, not scope creep.

**Required docstring format:**
```python
@pytest.mark.asyncio
async def test_command_center_shows_real_tournament(
    async_client_factory,
    create_async_tournament_scenario,
):
    """Test command center displays fixture-created tournament.

    Validates: feature-spec.md Scenario "View tournament command center"
    Gherkin:
        Given a tournament "Summer Battle 2024" exists in PRESELECTION phase
        And the tournament has 1 category with 4 performers
        When I navigate to /event/{tournament_id}
        Then the page should load successfully (200)
        And I should see the tournament name
    """
    # Given - create tournament in PRESELECTION phase
    data = await create_async_tournament_scenario(
        name="Summer Battle 2024",
        phase=TournamentPhase.PRESELECTION,
        num_categories=1,
        performers_per_category=4,
    )

    # When - navigate to command center
    async with async_client_factory("mc") as client:
        response = await client.get(f"/event/{data['tournament'].id}")

    # Then - page loads with tournament data
    assert response.status_code == 200
    assert b"Summer Battle 2024" in response.content
```

**Why this is BLOCKING:**
- E2E tests validate user workflows (the "Then" in Gherkin)
- Without Gherkin reference, failing tests don't tell us: is code wrong, or is requirement wrong?
- This prevents "tests that validate wrong behavior" (scope creep)

**When E2E test fails, Claude MUST ask:**
1. "Does this test correctly reflect the Gherkin scenario?" (compare docstring to feature-spec)
2. "Is the requirement clear, or should I ask user for clarification?"
3. "Is this a bug in code OR a gap in requirements?"

**Technical Details:**
- Session is shared via `app.dependency_overrides[get_db]`
- Uses `session.flush()` instead of `commit()` to keep data in transaction
- Transaction rolls back at end for automatic cleanup
- AsyncClient uses `ASGITransport` for proper async handling

## Writing Tests

### Test File Naming

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test Structure

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_example():
    """Test description."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/endpoint")

    assert response.status_code == 200
    assert "expected content" in response.text
```

### Using Fixtures

Common fixtures are defined in `tests/__init__.py`:

```python
@pytest.fixture
def sample_user():
    """Fixture providing a sample user."""
    return {
        "email": "test@example.com",
        "role": "participant",
        "name": "Test User"
    }
```

### Testing Async Code

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Testing Authentication

Mock authenticated requests using test tokens:

```python
async def test_protected_route():
    token = create_test_token(user_id=1, role="admin")
    headers = {"Cookie": f"auth_token={token}"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/endpoint", headers=headers)

    assert response.status_code == 200
```

## Mocking and Fixtures

### Mocking External Services

#### Email Service Mocking (Adapter Pattern)

The email service uses dependency injection, making it easy to mock for testing:

```python
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service

class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send_magic_link(self, to_email: str, magic_link: str, first_name: str) -> bool:
        """Store email data instead of sending."""
        self.sent_emails.append({
            "to_email": to_email,
            "magic_link": magic_link,
            "first_name": first_name
        })
        return True

    def clear(self):
        """Clear sent emails."""
        self.sent_emails = []

@pytest.fixture
def mock_email_provider():
    """Create mock email provider."""
    return MockEmailProvider()

@pytest.fixture
def client(mock_email_provider):
    """Create test client with mocked email service."""
    def get_mock_email_service():
        return EmailService(mock_email_provider)

    # Override dependency
    app.dependency_overrides[get_email_service] = get_mock_email_service

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()
    mock_email_provider.clear()

# Use in tests
def test_send_magic_link(client, mock_email_provider):
    response = client.post("/auth/send-magic-link", data={"email": "test@example.com"})

    # Verify email was "sent"
    assert len(mock_email_provider.sent_emails) == 1
    assert mock_email_provider.sent_emails[0]["to_email"] == "test@example.com"
```

**Benefits of this approach:**
- ✅ No need for `unittest.mock.patch`
- ✅ Tests actual email service logic
- ✅ Can verify email content and recipients
- ✅ Follows SOLID principles (testable by design)

#### Testing Gmail Provider

The Gmail provider is tested exactly the same way - using the mock provider approach:

```python
def test_send_magic_link_gmail(client, mock_email_provider):
    """Test magic link with Gmail provider (mocked)."""
    # Works identically regardless of actual provider
    # The mock provider intercepts the send_magic_link call
    response = client.post("/auth/send-magic-link", data={"email": "test@example.com"})

    assert len(mock_email_provider.sent_emails) == 1
    assert mock_email_provider.sent_emails[0]["to_email"] == "test@example.com"
```

**No need to test actual SMTP connection in unit tests.**

For integration testing with real Gmail:
- Set `EMAIL_PROVIDER=gmail` in test environment
- Use real Gmail credentials
- Send to test email address
- Verify delivery manually

We don't include real SMTP tests in CI/CD to avoid:
- Slow test execution
- External service dependencies
- Credential management in CI

### Database Fixtures (Phase 1+)

For database tests, use fixtures to create clean test data:

```python
@pytest.fixture
async def db_session():
    """Provide a clean database session for testing."""
    # Setup: Create test database
    session = await create_test_db()

    yield session

    # Teardown: Clean up test database
    await cleanup_test_db(session)
```

## Continuous Integration

### Pre-commit Testing

Run tests before committing:

```bash
pytest --cov=app --cov-report=term-missing
```

### CI/CD Pipeline (Planned)

Future CI/CD will include:
- Automated test execution on pull requests
- Coverage reporting and enforcement
- Performance regression testing
- Security vulnerability scanning

## Test Data Management

### In-Memory Stores (Phase 0)

Phase 0 uses in-memory dictionaries for testing:
- `users_db` - User storage
- `magic_links` - Magic link tokens
- `sessions` - Active sessions

Tests automatically get clean state per test run.

### Database Testing (Phase 1+)

Future database tests will:
- Use test database separate from development
- Implement transaction rollback after each test
- Use factory patterns for test data generation

## Debugging Tests

### Running Tests in Debug Mode

```bash
pytest --pdb  # Drop into debugger on failure
```

### Verbose Output

```bash
pytest -vv  # Extra verbose
pytest -s   # Show print statements
```

### Running Failed Tests Only

```bash
pytest --lf  # Run last failed
pytest --ff  # Run failed first, then others
```

## Performance Testing

### Benchmark Tests (Planned)

The `.benchmarks/` directory is reserved for performance testing:

```python
import pytest

@pytest.mark.benchmark
def test_authentication_performance(benchmark):
    result = benchmark(authenticate_user, "test@example.com")
    assert result is not None
```

## Best Practices

1. **One assertion per test** (when possible) - Makes failures easier to diagnose
2. **Descriptive test names** - Should explain what is being tested
3. **AAA pattern** - Arrange, Act, Assert
4. **Independent tests** - Tests should not depend on each other
5. **Fast tests** - Keep unit tests under 100ms when possible
6. **Mock external services** - Don't make real API calls in unit tests
7. **Test edge cases** - Empty inputs, null values, boundary conditions
8. **Use fixtures** - Share common setup across tests
9. **Clean up after tests** - Reset state, close connections
10. **Document complex tests** - Add docstrings explaining the test scenario

## Common Issues

### Import Errors

If you get import errors, ensure you're running pytest from the project root:

```bash
cd /path/to/web-app
pytest
```

### Async Warnings

Ensure `pytest-asyncio` is installed and tests are marked:

```python
@pytest.mark.asyncio
async def test_async_function():
    pass
```

### Coverage Not Found

Ensure the `pytest-cov` package is installed:

```bash
pip install pytest-cov
```

## Testing Checklist

Before committing code:

- [ ] All tests pass (`pytest`)
- [ ] New code has test coverage
- [ ] No reduction in overall coverage
- [ ] Tests are independent and can run in any order
- [ ] External services are mocked
- [ ] Edge cases are covered
- [ ] Test names are descriptive
- [ ] No hardcoded values (use fixtures/constants)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)

## Future Enhancements

### Phase 1
- Database integration tests
- Transaction rollback patterns
- Test data factories

### Phase 2+
- Stripe webhook testing
- Email delivery verification
- Performance benchmarking

### Phase 4+
- End-to-end testing with Playwright
- Visual regression testing
- Load testing with Locust

---

## UX Consistency Tests (Phase 3.10)

E2E tests that validate template consistency and prevent UX regressions.

**Location:** `tests/e2e/test_ux_consistency.py`

**Purpose:** Automated tests to catch UX inconsistencies like orphaned templates, inline styles, and inconsistent patterns.

**What's Tested:**

| Test | Business Rule | Purpose |
|------|---------------|---------|
| `test_no_orphaned_templates` | BR-UX-003 | Detect unused template files |
| `test_overview_html_deleted` | BR-UX-003 | Verify legacy file removed |
| `test_inline_styles_below_threshold` | BR-UX-001 | Enforce style consistency |
| `test_no_inline_color_styles` | BR-UX-001 | Enforce badge pattern usage |
| `test_permission_uses_symbols` | BR-UX-004 | Enforce checkmark format |

**Running UX Tests:**
```bash
# Run all UX consistency tests
pytest tests/e2e/test_ux_consistency.py -v

# Run specific test class
pytest tests/e2e/test_ux_consistency.py::TestOrphanedTemplates -v
```

**Configuration:**

Tests use configuration constants at the top of the file:

```python
# Templates intentionally not wired to routes (future features)
ALLOWED_ORPHANED_TEMPLATES = {
    "pools/overview.html",  # Future: Pool standings view
}

# Maximum allowed inline styles (after filtering exceptions)
MAX_INLINE_STYLES = 5

# Inline styles that are acceptable exceptions
ALLOWED_INLINE_STYLE_PATTERNS = [
    # Add patterns here as needed
]
```

**Adding New Exceptions:**

If a template is intentionally orphaned or an inline style is necessary:

1. **Orphaned Template:** Add to `ALLOWED_ORPHANED_TEMPLATES`
2. **Inline Style:** Add regex pattern to `ALLOWED_INLINE_STYLE_PATTERNS`

**Why These Tests Exist:**

The Battle-D application accumulated UX inconsistencies after Phase 3.3 (UX Navigation Redesign) where:
- Legacy `overview.html` remained but was replaced by `dashboard/index.html`
- Inline styles were used instead of `.badge` CSS classes
- Permission display used `Yes/No` instead of checkmark symbols

These tests prevent similar regressions by automatically detecting:
- Templates with no references (orphaned code)
- Inline styles that should use CSS classes
- Inconsistent patterns across templates

**Related Documentation:**
- `FRONTEND.md` - Badge classes, permission display standard
- `ROADMAP.md` - Phase 3.10 UX Consistency Audit

---

**Current Status**: Phase 3.10 - UX Consistency Audit - Tests in progress

Last updated: 2025-12-17
