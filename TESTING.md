# Testing Guide

This document describes the testing strategy, setup, and practices for the Battle-D web application.

## Overview

The project uses pytest as the primary testing framework with support for async tests and code coverage reporting. As of Phase 1, we maintain 100% test pass rate (97+ tests passing, 8 skipped).

## Test Structure

```
tests/
├── __init__.py                      # Test configuration and fixtures
├── test_auth.py                     # Authentication and magic link tests
├── test_permissions.py              # Role-based access control tests
├── test_phases.py                   # Tournament phase routing tests
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

# Test phases only
pytest tests/test_phases.py
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
- **Routing**: Phase-specific access and redirects
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

### Unit Tests (Current - Phase 0)

Unit tests focus on individual components and functions in isolation.

**Current test files:**
- `test_auth.py` - Authentication flows and token management
- `test_permissions.py` - Decorator-based access control
- `test_phases.py` - Route protection and phase access

### Integration Tests (Planned - Phase 1+)

Integration tests will verify interactions between components:
- Database operations
- Email service integration
- External API calls (Stripe, etc.)

### End-to-End Tests (Planned - Phase 4+)

E2E tests will verify complete user workflows:
- Registration → Verification → Dashboard
- Tournament creation → Judging → Results
- Payment flow → Confirmation

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

**Current Status**: Phase 1 COMPLETE - 97+ tests passing, 8 skipped ✅

Last updated: 2025-01-19
