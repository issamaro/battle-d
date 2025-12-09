# Implementation Plan: E2E Testing Session Isolation Fix

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_E2E-TESTING-SESSION-ISOLATION-FIX.md

---

## 1. Summary

**Feature:** Fix E2E testing session isolation so tests can access fixture-created database data
**Approach:** Replace sync TestClient with httpx.AsyncClient and override `get_db()` to share a single session between fixture data creation and HTTP requests

---

## 2. Affected Files

### Backend
**Models:**
- No changes needed

**Services:**
- No changes needed

**Repositories:**
- No changes needed

**Routes:**
- No changes needed

**Validators:**
- No changes needed

**Utils:**
- No changes needed

### Frontend
**Templates:**
- No changes needed

**Components:**
- No changes needed

**CSS:**
- No changes needed

### Database
**Migrations:**
- No changes needed

### Tests
**New Test Files:**
- `tests/e2e/async_conftest.py`: New async E2E fixture infrastructure

**Updated Test Files:**
- `tests/e2e/conftest.py`: Keep existing sync fixtures for backward compatibility
- `tests/e2e/test_event_mode.py`: Migrate to async pattern, restore previously removed tests
- `tests/e2e/test_session_isolation_fix.py`: Keep as reference/validation tests (already created during POC)

### Documentation
**Level 1:**
- No changes (not domain rules)

**Level 2:**
- No changes

**Level 3:**
- `TESTING.md`: Add section on async E2E testing pattern

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**No database changes required.**

### 3.2 Service Layer Changes

**No service changes required.**

### 3.3 Route Changes

**No route changes required.**

---

## 4. Test Infrastructure Implementation Plan

### 4.1 New Async E2E Conftest (`tests/e2e/async_conftest.py`)

Create new fixture file with async-aware E2E testing infrastructure:

```python
"""Async E2E test fixtures using httpx.AsyncClient with session override.

This module solves the session isolation problem:
- Fixtures create data in a shared session
- Routes use the same session via dependency override
- All data is visible throughout the test

Usage:
    @pytest.mark.asyncio
    async def test_with_fixture_data(async_e2e_session, async_client_factory):
        # Create test data
        tournament = await create_tournament(async_e2e_session)
        await async_e2e_session.flush()

        # Get authenticated client
        async with async_client_factory("staff") as client:
            response = await client.get(f"/tournaments/{tournament.id}")
            assert response.status_code == 200
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.database import async_session_maker, get_db
from app.repositories.user import UserRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository
from app.repositories.battle import BattleRepository
from app.models.user import UserRole
from app.auth import magic_link_auth
from app.config import settings
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service


# =============================================================================
# MOCK EMAIL PROVIDER
# =============================================================================

class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for async E2E tests."""

    def __init__(self):
        self.sent_emails = []

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        self.sent_emails.append({
            "to_email": to_email,
            "magic_link": magic_link,
            "first_name": first_name
        })
        return True

    def clear(self):
        self.sent_emails = []


# =============================================================================
# CORE SESSION FIXTURE
# =============================================================================

@pytest_asyncio.fixture
async def async_e2e_session() -> AsyncGenerator[AsyncSession, None]:
    """Shared async session for E2E tests.

    This session is shared between:
    - Test fixture data creation
    - HTTP routes (via dependency override)

    Data created here IS visible to routes because they share the session.

    Uses flush() instead of commit() to keep data in transaction.
    Transaction rolls back at end for automatic cleanup.
    """
    async with async_session_maker() as session:
        yield session
        # Rollback at end - no need to clean up manually
        await session.rollback()


# =============================================================================
# ASYNC CLIENT FACTORY
# =============================================================================

@pytest.fixture
def async_client_factory(async_e2e_session: AsyncSession):
    """Factory to create authenticated AsyncClient instances.

    Usage:
        async with async_client_factory("staff") as client:
            response = await client.get("/tournaments")

    Available roles: "admin", "staff", "mc", "judge"
    """
    mock_email = MockEmailProvider()

    @asynccontextmanager
    async def _create_client(role: str = "staff"):
        """Create an authenticated async client.

        Args:
            role: User role (admin, staff, mc, judge)

        Yields:
            AsyncClient with authentication cookies
        """
        # Override get_db to return shared session
        async def override_get_db():
            yield async_e2e_session

        def get_mock_email_service():
            return EmailService(mock_email)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_email_service] = get_mock_email_service

        try:
            # Generate auth token
            email = f"{role}@async-e2e-test.com"
            token = magic_link_auth.generate_token(email, role)

            # Create client
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test"
            ) as client:
                # Verify token to get session cookie
                verify_response = await client.get(
                    f"/auth/verify?token={token}",
                    follow_redirects=False
                )

                # Client now has auth cookie
                yield client

        finally:
            app.dependency_overrides.clear()
            mock_email.clear()

    return _create_client


# =============================================================================
# DATA FACTORY FIXTURES
# =============================================================================

@pytest.fixture
def create_async_tournament(async_e2e_session: AsyncSession):
    """Factory to create tournaments in async E2E tests.

    Usage:
        tournament = await create_async_tournament(name="Summer Battle")
        tournament = await create_async_tournament(phase=TournamentPhase.PRESELECTION)
    """
    async def _create(
        name: str = None,
        phase = None,
        status = None,
    ):
        from uuid import uuid4
        from app.models.tournament import TournamentPhase, TournamentStatus

        tournament_repo = TournamentRepository(async_e2e_session)

        name = name or f"Async E2E Tournament {uuid4().hex[:8]}"
        tournament = await tournament_repo.create_tournament(name=name)

        # Update phase/status if specified
        updates = {}
        if phase is not None:
            updates["phase"] = phase
        if status is not None:
            updates["status"] = status

        if updates:
            tournament = await tournament_repo.update(tournament.id, **updates)

        await async_e2e_session.flush()
        return tournament

    return _create


@pytest.fixture
def create_async_category(async_e2e_session: AsyncSession):
    """Factory to create categories in async E2E tests."""
    async def _create(
        tournament_id,
        name: str = None,
        is_duo: bool = False,
        groups_ideal: int = 2,
        performers_ideal: int = 4,
    ):
        from uuid import uuid4

        category_repo = CategoryRepository(async_e2e_session)

        name = name or f"Category {uuid4().hex[:8]}"
        category = await category_repo.create_category(
            tournament_id=tournament_id,
            name=name,
            is_duo=is_duo,
            groups_ideal=groups_ideal,
            performers_ideal=performers_ideal,
        )

        await async_e2e_session.flush()
        return category

    return _create


@pytest.fixture
def create_async_performer(async_e2e_session: AsyncSession):
    """Factory to create performers (with dancers) in async E2E tests."""
    async def _create(
        tournament_id,
        category_id,
        blaze: str = None,
    ):
        from uuid import uuid4
        from datetime import date

        dancer_repo = DancerRepository(async_e2e_session)
        performer_repo = PerformerRepository(async_e2e_session)

        # Create dancer
        unique_id = uuid4().hex[:8]
        dancer = await dancer_repo.create_dancer(
            email=f"dancer_{unique_id}@test.com",
            first_name="Dancer",
            last_name=unique_id,
            date_of_birth=date(2000, 1, 1),
            blaze=blaze or f"B-Boy {unique_id}",
        )

        # Create performer
        performer = await performer_repo.create_performer(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer.id,
        )

        await async_e2e_session.flush()
        return performer, dancer

    return _create


@pytest.fixture
def create_async_battle(async_e2e_session: AsyncSession):
    """Factory to create battles in async E2E tests."""
    async def _create(
        category_id,
        phase,
        performer_ids: list,
        status = None,
    ):
        from app.models.battle import BattleStatus, BattleOutcomeType, BattlePhase

        battle_repo = BattleRepository(async_e2e_session)

        # Determine outcome type based on phase
        outcome_type_map = {
            BattlePhase.PRESELECTION: BattleOutcomeType.SCORED,
            BattlePhase.POOLS: BattleOutcomeType.WIN_DRAW_LOSS,
            BattlePhase.TIEBREAK: BattleOutcomeType.TIEBREAK,
            BattlePhase.FINALS: BattleOutcomeType.WIN_LOSS,
        }
        outcome_type = outcome_type_map.get(phase, BattleOutcomeType.WIN_LOSS)

        battle = await battle_repo.create_battle(
            category_id=category_id,
            phase=phase,
            outcome_type=outcome_type,
            performer_ids=performer_ids,
        )

        if status is not None and status != BattleStatus.PENDING:
            await battle_repo.update(battle.id, status=status)

        await async_e2e_session.flush()

        # Re-fetch with performers
        battle = await battle_repo.get_with_performers(battle.id)
        return battle

    return _create


# =============================================================================
# COMPLETE SCENARIO FACTORY
# =============================================================================

@pytest.fixture
def create_async_tournament_scenario(
    async_e2e_session: AsyncSession,
    create_async_tournament,
    create_async_category,
    create_async_performer,
):
    """Factory to create complete tournament scenarios for E2E tests.

    Usage:
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=2,
            performers_per_category=8
        )

        # Access data
        data["tournament"]
        data["categories"][0]
        data["performers"][0]
    """
    async def _create(
        name: str = None,
        phase = None,
        num_categories: int = 1,
        performers_per_category: int = 4,
    ):
        from app.models.tournament import TournamentPhase

        # Create tournament
        tournament = await create_async_tournament(
            name=name,
            phase=phase or TournamentPhase.REGISTRATION,
        )

        # Create categories and performers
        categories = []
        performers = []
        dancers = []

        for i in range(num_categories):
            category = await create_async_category(
                tournament_id=tournament.id,
                name=f"Category {i + 1}",
            )
            categories.append(category)

            for j in range(performers_per_category):
                performer, dancer = await create_async_performer(
                    tournament_id=tournament.id,
                    category_id=category.id,
                )
                performers.append(performer)
                dancers.append(dancer)

        return {
            "tournament": tournament,
            "categories": categories,
            "performers": performers,
            "dancers": dancers,
        }

    return _create
```

### 4.2 Example Test Migration (`tests/e2e/test_event_mode_async.py`)

Create new async version of event mode tests:

```python
"""Async E2E tests for Event Mode using shared session pattern.

These tests can access fixture-created data because they use
the async_e2e_session fixture with dependency override.
"""
import pytest
from app.models.tournament import TournamentPhase
from app.models.battle import BattlePhase, BattleStatus


class TestEventModeWithRealData:
    """Event Mode tests with pre-created tournament and battle data.

    These tests were previously impossible due to session isolation.
    Now work because fixture data and routes share the same session.
    """

    @pytest.mark.asyncio
    async def test_command_center_shows_real_tournament(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Test that command center displays fixture-created tournament.

        Gherkin:
        Given a tournament "Summer Battle 2024" exists in PRESELECTION phase
        And the tournament has 1 category with 4 performers
        When I navigate to /event/{tournament_id}
        Then the page should load successfully (200)
        And I should see the tournament name
        """
        # Given
        data = await create_async_tournament_scenario(
            name="Summer Battle 2024",
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]

        # When
        async with async_client_factory("mc") as client:
            response = await client.get(f"/event/{tournament.id}")

        # Then
        assert response.status_code == 200
        assert b"Summer Battle 2024" in response.content

    @pytest.mark.asyncio
    async def test_battle_queue_shows_real_battles(
        self,
        async_client_factory,
        create_async_tournament_scenario,
        create_async_battle,
    ):
        """Test that battle queue shows fixture-created battles.

        Gherkin:
        Given a tournament in PRESELECTION phase
        And 2 pending battles exist in the queue
        When I navigate to /event/{tournament_id}/queue
        Then the response should show the battles
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]
        category = data["categories"][0]
        performers = data["performers"]

        # Create 2 battles
        battle1 = await create_async_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            performer_ids=[performers[0].id, performers[1].id],
        )
        battle2 = await create_async_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            performer_ids=[performers[2].id, performers[3].id],
        )

        # When
        async with async_client_factory("mc") as client:
            response = await client.get(
                f"/event/{tournament.id}/queue",
                headers={"HX-Request": "true"}
            )

        # Then
        assert response.status_code == 200
        # Should be partial HTML (HTMX response)
        assert b"<html>" not in response.content

    @pytest.mark.asyncio
    async def test_can_start_fixture_created_battle(
        self,
        async_e2e_session,
        async_client_factory,
        create_async_tournament_scenario,
        create_async_battle,
    ):
        """Test starting a battle that was created in fixtures.

        Gherkin:
        Given a battle exists with status PENDING
        And I am authenticated as MC
        When I POST to /battles/{battle_id}/start
        Then the battle status should change to ACTIVE
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=2,
        )
        tournament = data["tournament"]
        category = data["categories"][0]
        performers = data["performers"]

        battle = await create_async_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            performer_ids=[performers[0].id, performers[1].id],
            status=BattleStatus.PENDING,
        )

        # When
        async with async_client_factory("mc") as client:
            response = await client.post(
                f"/battles/{battle.id}/start",
                follow_redirects=False
            )

        # Then
        assert response.status_code == 303  # Redirect on success

        # Verify battle status changed
        from app.repositories.battle import BattleRepository
        battle_repo = BattleRepository(async_e2e_session)
        updated_battle = await battle_repo.get_by_id(battle.id)
        assert updated_battle.status == BattleStatus.ACTIVE
```

---

## 5. Documentation Update Plan

### TESTING.md

Add new section after "End-to-End Tests (Phase 3.6)":

```markdown
### Async E2E Tests (Session Sharing Pattern)

For E2E tests that need to access pre-created database data, use the async pattern with session sharing.

**The Problem:**
Standard E2E tests use sync TestClient, which creates separate database sessions. Data created in async fixtures is invisible to routes because of session isolation.

**The Solution:**
Use `httpx.AsyncClient` with dependency override to share a single session between fixture data creation and HTTP request handling.

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

    # Make HTTP request - same session via override
    async with async_client_factory("staff") as client:
        response = await client.get(f"/tournaments/{tournament.id}")
        assert response.status_code == 200  # Works!
```

**Key Fixtures (from `tests/e2e/async_conftest.py`):**

| Fixture | Purpose |
|---------|---------|
| `async_e2e_session` | Shared SQLAlchemy session for test |
| `async_client_factory` | Creates authenticated AsyncClient |
| `create_async_tournament` | Factory for tournaments |
| `create_async_category` | Factory for categories |
| `create_async_performer` | Factory for performers with dancers |
| `create_async_battle` | Factory for battles |
| `create_async_tournament_scenario` | Complete scenario factory |

**When to Use:**
- Testing with pre-created data (tournaments, battles, performers)
- Multi-step workflows where data must persist between requests
- Validating Gherkin scenarios with specific database state

**When NOT to Use:**
- Simple route tests (use sync TestClient)
- Tests that only need HTTP-created data
- Performance testing (async overhead)
```

---

## 6. Testing Plan

### Validation Tests

The prototype tests in `tests/e2e/test_session_isolation_fix.py` already validate the approach:

| Test | Status | Purpose |
|------|--------|---------|
| `test_fixture_data_visible_via_session_override` | PASSED | Proves tournament visible |
| `test_async_approach_can_create_complex_scenario` | PASSED | Proves Event Mode works |

### New Tests to Add

**test_event_mode_async.py:**
- `test_command_center_shows_real_tournament`
- `test_battle_queue_shows_real_battles`
- `test_can_start_fixture_created_battle`

### Regression Tests

Run full test suite to ensure no regressions:
```bash
pytest tests/ -v
```

---

## 7. Risk Analysis

### Risk 1: Session State Leakage
**Concern:** Shared session might cause test pollution
**Likelihood:** Low
**Impact:** Medium (flaky tests)
**Mitigation:**
- Use `session.rollback()` at end of each test
- Each test gets fresh session via fixture scope

### Risk 2: Async Test Complexity
**Concern:** Async tests harder to debug
**Likelihood:** Medium
**Impact:** Low (learning curve)
**Mitigation:**
- Clear documentation in TESTING.md
- Example tests as reference
- Keep sync tests for simple cases

### Risk 3: Performance Overhead
**Concern:** Async tests might be slower
**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- Only use async pattern when needed
- Keep sync tests for simple cases
- Profile if needed

---

## 8. Technical POC

**Status:** Completed during analysis phase
**Location:** `tests/e2e/test_session_isolation_fix.py`

**Results:**
```
TestAsyncClientApproach::test_fixture_data_visible_via_session_override PASSED
TestCompareApproaches::test_async_approach_can_create_complex_scenario PASSED
```

**Findings:**
- AsyncClient + session override works correctly
- Fixture-created tournaments visible to HTTP routes
- Event Mode command center accessible with pre-created tournament
- Pattern is production-ready

**Decision:** Proceed with implementation as planned

---

## 9. Implementation Order

**Recommended sequence:**

1. **Create async_conftest.py** (~30 min)
   - Core session fixture
   - Client factory
   - Data factories
   - Scenario factory

2. **Add example async tests** (~20 min)
   - Create `test_event_mode_async.py`
   - Add 3 tests validating Gherkin scenarios
   - Verify all pass

3. **Update TESTING.md** (~15 min)
   - Add async E2E testing section
   - Document fixtures and patterns
   - Add usage examples

4. **Run full test suite** (~5 min)
   - Verify no regressions
   - All 460+ tests should pass

5. **Clean up prototype file** (~5 min)
   - Keep `test_session_isolation_fix.py` as validation tests
   - Remove redundant tests if any

---

## 10. Open Questions

- [x] Which approach to use? → AsyncClient + Session Override (user confirmed)
- [x] Does the pattern work? → Yes, POC passed
- [x] Keep sync fixtures? → Yes, for backward compatibility

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
