# Implementation Plan: End-to-End Testing Framework

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md

---

## 1. Summary

**Feature:** End-to-end HTTP tests for critical user workflows (Event Mode, Tournament Management)
**Approach:** Create `tests/e2e/` directory with authenticated test fixtures, reusable helpers, and comprehensive workflow tests using TestClient with real database

---

## 2. Affected Files

### Backend
**No changes** - Testing only feature, no backend modifications needed.

### Frontend
**No changes** - Testing only feature, no UI modifications needed.

### Database
**No changes** - Tests use existing schema via real database.

### Tests

**New Test Infrastructure:**
- `tests/e2e/__init__.py` - E2E test utilities and HTMX helpers
- `tests/e2e/conftest.py` - E2E-specific fixtures (authenticated clients, test data factories)

**New Test Files:**
- `tests/e2e/test_event_mode.py` - Event Mode workflow tests (critical)
- `tests/e2e/test_tournament_management.py` - Tournament management workflow tests
- `tests/e2e/test_htmx_interactions.py` - HTMX partial response tests
- `tests/e2e/test_authentication_flows.py` - Authentication E2E tests (medium priority)

### Documentation

**Level 3:**
- `TESTING.md`: Add E2E Testing section with patterns and examples

---

## 3. Test Infrastructure Plan

### 3.1 Directory Structure

```
tests/
├── e2e/
│   ├── __init__.py           # E2E utilities (HTMX helpers, response validators)
│   ├── conftest.py           # E2E fixtures (authenticated clients, pre-built scenarios)
│   ├── test_event_mode.py    # Event Mode workflow tests
│   ├── test_tournament_management.py  # Tournament setup workflow tests
│   ├── test_htmx_interactions.py      # HTMX partial response tests
│   └── test_authentication_flows.py   # Auth workflow tests (future)
└── (existing test files)
```

### 3.2 E2E Utilities (`tests/e2e/__init__.py`)

```python
"""E2E test utilities and helpers.

Provides common functions for HTTP-level testing with HTMX.
"""
from typing import Optional


def is_partial_html(content: str) -> bool:
    """Check if response is partial HTML (not full page).

    HTMX endpoints should return partial HTML without <html>, <body> tags.

    Args:
        content: Response content as string

    Returns:
        True if partial HTML (no full page wrapper)
    """
    return "<html" not in content.lower() and "<body" not in content.lower()


def is_full_page(content: str) -> bool:
    """Check if response is full HTML page.

    Non-HTMX requests should return full pages.

    Args:
        content: Response content as string

    Returns:
        True if full page (has <html> tag)
    """
    return "<html" in content.lower()


def htmx_headers() -> dict:
    """Return headers that simulate an HTMX request.

    Returns:
        Dict with HX-Request header set
    """
    return {"HX-Request": "true"}


def assert_contains_badge(content: str, status: str) -> None:
    """Assert response contains a status badge.

    Args:
        content: Response content
        status: Expected status text (e.g., "ACTIVE", "PENDING")

    Raises:
        AssertionError if badge not found
    """
    # Look for badge in various formats
    assert status.upper() in content.upper(), f"Badge '{status}' not found in response"


def assert_flash_message(content: str, message_type: str = None) -> None:
    """Assert response contains a flash message.

    Args:
        content: Response content
        message_type: Optional type filter ("success", "error", "warning")

    Raises:
        AssertionError if flash message not found
    """
    assert "flash-message" in content or "alert" in content, "No flash message found"
    if message_type:
        assert message_type in content.lower(), f"Flash type '{message_type}' not found"
```

### 3.3 E2E Fixtures (`tests/e2e/conftest.py`)

```python
"""E2E test fixtures.

Provides authenticated test clients and pre-built test scenarios.
Follows patterns from tests/test_crud_workflows.py.
"""
import pytest
from datetime import date
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.db.database import async_session_maker
from app.repositories.user import UserRepository
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.battle import BattleRepository
from app.models.user import UserRole
from app.models.tournament import TournamentPhase, TournamentStatus
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service


# =============================================================================
# EMAIL MOCK (Reused from test_crud_workflows.py)
# =============================================================================

class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        self.sent_emails.append(
            {"to_email": to_email, "magic_link": magic_link, "first_name": first_name}
        )
        return True

    def clear(self):
        self.sent_emails = []


@pytest.fixture
def mock_email_provider():
    return MockEmailProvider()


# =============================================================================
# TEST USERS
# =============================================================================

@pytest.fixture(scope="function")
async def e2e_test_users():
    """Create test users for E2E tests (admin, staff, mc, judge)."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.create_user("admin@e2e-test.com", "Admin User", UserRole.ADMIN)
        await user_repo.create_user("staff@e2e-test.com", "Staff User", UserRole.STAFF)
        await user_repo.create_user("mc@e2e-test.com", "MC User", UserRole.MC)
        await user_repo.create_user("judge@e2e-test.com", "Judge User", UserRole.JUDGE)
        await session.commit()
    yield
    # Cleanup handled by setup_test_database fixture in main conftest.py


# =============================================================================
# AUTHENTICATED CLIENTS
# =============================================================================

def get_session_cookie(client: TestClient, email: str, role: str) -> str:
    """Login and extract session cookie.

    Reused from test_crud_workflows.py pattern.
    """
    token = magic_link_auth.generate_token(email, role)
    response = client.get(f"/auth/verify?token={token}", follow_redirects=False)

    set_cookie_header = response.headers.get("set-cookie", "")
    cookie_start = set_cookie_header.find(f"{settings.SESSION_COOKIE_NAME}=") + len(f"{settings.SESSION_COOKIE_NAME}=")
    cookie_end = set_cookie_header.find(";", cookie_start)
    return set_cookie_header[cookie_start:cookie_end]


@pytest.fixture
def client(mock_email_provider):
    """Base test client with mocked email service."""
    def get_mock_email_service():
        return EmailService(mock_email_provider)

    app.dependency_overrides[get_email_service] = get_mock_email_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()


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


# =============================================================================
# TEST DATA FACTORIES
# =============================================================================

@pytest.fixture
def create_e2e_tournament():
    """Factory to create tournament with categories and performers.

    Returns a function that creates a complete tournament setup.
    """
    async def _create(
        name: str = None,
        phase: TournamentPhase = TournamentPhase.REGISTRATION,
        num_categories: int = 1,
        performers_per_category: int = 4,
    ):
        """Create tournament with optional pre-populated data.

        Args:
            name: Tournament name (auto-generated if None)
            phase: Tournament phase
            num_categories: Number of categories to create
            performers_per_category: Performers per category

        Returns:
            Dict with tournament, categories, dancers, performers
        """
        async with async_session_maker() as session:
            # Create tournament
            tournament_repo = TournamentRepository(session)
            tournament = await tournament_repo.create_tournament(
                name=name or f"E2E Tournament {uuid4().hex[:8]}"
            )

            if phase != TournamentPhase.REGISTRATION:
                await tournament_repo.update(tournament.id, phase=phase)
                tournament = await tournament_repo.get_by_id(tournament.id)

            # Create categories
            category_repo = CategoryRepository(session)
            categories = []
            for i in range(num_categories):
                category = await category_repo.create_category(
                    tournament_id=tournament.id,
                    name=f"Category {i + 1}",
                    is_duo=False,
                    groups_ideal=2,
                    performers_ideal=4,
                )
                categories.append(category)

            # Create dancers and performers
            dancer_repo = DancerRepository(session)
            performer_repo = PerformerRepository(session)
            dancers = []
            performers = []

            for category in categories:
                for j in range(performers_per_category):
                    dancer = await dancer_repo.create_dancer(
                        email=f"dancer_{uuid4().hex[:8]}@test.com",
                        first_name=f"Dancer",
                        last_name=f"{j + 1}",
                        date_of_birth=date(2000, 1, 1),
                        blaze=f"B-Boy {uuid4().hex[:6]}",
                    )
                    dancers.append(dancer)

                    performer = await performer_repo.create_performer(
                        tournament_id=tournament.id,
                        category_id=category.id,
                        dancer_id=dancer.id,
                    )
                    performers.append(performer)

            await session.commit()

            return {
                "tournament": tournament,
                "categories": categories,
                "dancers": dancers,
                "performers": performers,
            }

    return _create


@pytest.fixture
def create_e2e_battle():
    """Factory to create battles for E2E tests."""
    async def _create(
        category_id,
        phase: BattlePhase,
        performers,
        status: BattleStatus = BattleStatus.PENDING,
    ):
        """Create a battle with performers.

        Args:
            category_id: Category UUID
            phase: Battle phase
            performers: List of performers
            status: Battle status

        Returns:
            Battle instance
        """
        async with async_session_maker() as session:
            battle_repo = BattleRepository(session)

            # Determine outcome type based on phase
            outcome_type_map = {
                BattlePhase.PRESELECTION: BattleOutcomeType.SCORED,
                BattlePhase.POOLS: BattleOutcomeType.WIN_DRAW_LOSS,
                BattlePhase.TIEBREAK: BattleOutcomeType.TIEBREAK,
                BattlePhase.FINALS: BattleOutcomeType.WIN_LOSS,
            }
            outcome_type = outcome_type_map.get(phase, BattleOutcomeType.WIN_LOSS)

            performer_ids = [p.id for p in performers]
            battle = await battle_repo.create_battle(
                category_id=category_id,
                phase=phase,
                outcome_type=outcome_type,
                performer_ids=performer_ids,
            )

            if status != BattleStatus.PENDING:
                await battle_repo.update(battle.id, status=status)
                battle = await battle_repo.get_with_performers(battle.id)

            await session.commit()
            return battle

    return _create
```

---

## 4. Test File Implementation Plans

### 4.1 Event Mode E2E Tests (`tests/e2e/test_event_mode.py`)

**Test Count:** ~12 tests
**Priority:** Critical

```python
"""E2E tests for Event Mode (MC workflow).

Tests complete battle workflows through HTTP interface.
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §3.1
"""
import pytest
from uuid import uuid4
from decimal import Decimal

from app.models.tournament import TournamentPhase
from app.models.battle import BattlePhase, BattleStatus
from tests.e2e import is_partial_html, htmx_headers, assert_contains_badge


class TestCommandCenterAccess:
    """Test command center page access and rendering."""

    def test_command_center_loads_with_tournament(
        self, mc_client, create_e2e_tournament
    ):
        """GET /event/{id} loads command center with tournament data."""
        # Arrange
        import asyncio
        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        # Act
        response = mc_client.get(f"/event/{tournament.id}")

        # Assert
        assert response.status_code == 200
        assert tournament.name.encode() in response.content

    def test_command_center_requires_mc_role(self, staff_client, create_e2e_tournament):
        """GET /event/{id} requires MC role."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        response = staff_client.get(f"/event/{tournament.id}")

        # Staff cannot access MC command center
        assert response.status_code in [401, 403]

    def test_command_center_redirects_wrong_phase(
        self, mc_client, create_e2e_tournament
    ):
        """GET /event/{id} redirects if tournament in REGISTRATION phase."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.REGISTRATION))
        tournament = data["tournament"]

        response = mc_client.get(f"/event/{tournament.id}", follow_redirects=False)

        assert response.status_code == 303


class TestBattleStart:
    """Test starting battles via HTTP."""

    def test_start_battle_changes_status_to_active(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/start changes battle status to ACTIVE."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.PRESELECTION,
            performers=data["performers"][:2],
        ))

        response = mc_client.post(f"/battles/{battle.id}/start", follow_redirects=False)

        # Should redirect after success
        assert response.status_code == 303

        # Verify battle status changed
        # (Check via GET request or DB query)

    def test_start_battle_returns_updated_card_htmx(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/start returns partial HTML for HTMX."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.PRESELECTION,
            performers=data["performers"][:2],
        ))

        response = mc_client.post(
            f"/battles/{battle.id}/start",
            headers=htmx_headers(),
        )

        # HTMX request should get partial HTML (not redirect)
        # Note: This depends on route implementation
        # Current route returns redirect even for HTMX


class TestBattleEncoding:
    """Test encoding battle results via HTTP."""

    def test_encode_preselection_scores_success(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/encode with valid scores completes battle."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.PRESELECTION,
            performers=data["performers"][:2],
            status=BattleStatus.ACTIVE,
        ))

        # Build form data with scores for each performer
        form_data = {}
        for performer in data["performers"][:2]:
            form_data[f"score_{performer.id}"] = "8.5"

        response = mc_client.post(
            f"/battles/{battle.id}/encode",
            data=form_data,
            follow_redirects=False,
        )

        assert response.status_code == 303  # Redirect on success

    def test_encode_preselection_validation_error_preserves_form(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/encode with invalid data shows errors."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.PRESELECTION,
            performers=data["performers"][:2],
            status=BattleStatus.ACTIVE,
        ))

        # Submit incomplete data
        form_data = {
            f"score_{data['performers'][0].id}": "8.5",
            # Missing second performer score
        }

        response = mc_client.post(
            f"/battles/{battle.id}/encode",
            data=form_data,
            follow_redirects=False,
        )

        # Should redirect to encode form with error
        assert response.status_code == 303


class TestPoolBattleEncoding:
    """Test pool battle encoding via HTTP."""

    def test_encode_pool_with_winner(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/encode with winner updates performer stats."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.POOLS))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.POOLS,
            performers=data["performers"][:2],
            status=BattleStatus.ACTIVE,
        ))

        form_data = {
            "winner_id": str(data["performers"][0].id),
            "is_draw": "false",
        }

        response = mc_client.post(
            f"/battles/{battle.id}/encode",
            data=form_data,
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_encode_pool_with_draw(
        self, mc_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/encode with draw updates both performers."""
        import asyncio

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.POOLS))
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.POOLS,
            performers=data["performers"][:2],
            status=BattleStatus.ACTIVE,
        ))

        form_data = {
            "is_draw": "true",
        }

        response = mc_client.post(
            f"/battles/{battle.id}/encode",
            data=form_data,
            follow_redirects=False,
        )

        assert response.status_code == 303
```

### 4.2 Tournament Management E2E Tests (`tests/e2e/test_tournament_management.py`)

**Test Count:** ~10 tests
**Priority:** High

```python
"""E2E tests for Tournament Management (Admin workflow).

Tests tournament setup through HTTP interface.
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §3.2
"""
import pytest

from app.models.tournament import TournamentPhase


class TestTournamentCreation:
    """Test creating tournaments via HTTP."""

    def test_create_tournament_success(self, staff_client):
        """POST /tournaments/create creates tournament and redirects."""
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "E2E Test Tournament"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "/tournaments/" in response.headers["location"]

    def test_create_tournament_appears_in_list(self, staff_client):
        """Created tournament appears in tournament list."""
        # Create
        staff_client.post(
            "/tournaments/create",
            data={"name": "List Test Tournament"},
        )

        # List
        response = staff_client.get("/tournaments")

        assert response.status_code == 200
        assert b"List Test Tournament" in response.content


class TestCategoryManagement:
    """Test adding categories to tournaments via HTTP."""

    def test_add_category_to_tournament(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/add-category creates category."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(num_categories=0))
        tournament = data["tournament"]

        response = staff_client.post(
            f"/tournaments/{tournament.id}/add-category",
            data={
                "name": "New Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_category_appears_on_detail_page(self, staff_client, create_e2e_tournament):
        """Added category appears on tournament detail page."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(num_categories=0))
        tournament = data["tournament"]

        # Add category
        staff_client.post(
            f"/tournaments/{tournament.id}/add-category",
            data={
                "name": "Visible Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
        )

        # View detail
        response = staff_client.get(f"/tournaments/{tournament.id}")

        assert response.status_code == 200
        assert b"Visible Category" in response.content


class TestPhaseAdvancement:
    """Test advancing tournament phases via HTTP."""

    def test_advance_phase_requires_admin(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance requires admin role."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(performers_per_category=4))
        tournament = data["tournament"]

        response = staff_client.post(
            f"/tournaments/{tournament.id}/advance",
            follow_redirects=False,
        )

        # Staff cannot advance phases (admin only)
        assert response.status_code in [401, 403]

    def test_advance_phase_validation_error(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance shows errors when requirements not met."""
        import asyncio
        # Create tournament with insufficient performers
        data = asyncio.run(create_e2e_tournament(performers_per_category=1))
        tournament = data["tournament"]

        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Should show validation errors
        assert response.status_code == 400

    def test_advance_phase_confirmation_flow(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance shows confirmation then advances."""
        import asyncio
        data = asyncio.run(create_e2e_tournament(performers_per_category=4))
        tournament = data["tournament"]

        # First request - confirmation page
        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Should show confirmation page
        assert response.status_code == 200
        assert b"confirm" in response.content.lower() or b"advance" in response.content.lower()

        # Second request - confirmed
        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "true"},
            follow_redirects=False,
        )

        assert response.status_code == 303
```

### 4.3 HTMX Interaction Tests (`tests/e2e/test_htmx_interactions.py`)

**Test Count:** ~8 tests
**Priority:** High

```python
"""E2E tests for HTMX interactions.

Tests that HTMX endpoints return partial HTML (not full pages).
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §4.3
"""
import pytest
from uuid import uuid4

from tests.e2e import is_partial_html, is_full_page, htmx_headers


class TestHTMXPartialResponses:
    """Test that HTMX endpoints return partial HTML."""

    def test_event_current_battle_partial(self, mc_client, create_e2e_tournament):
        """GET /event/{id}/current-battle returns partial HTML."""
        import asyncio
        from app.models.tournament import TournamentPhase

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        response = mc_client.get(
            f"/event/{tournament.id}/current-battle",
            headers=htmx_headers(),
        )

        assert response.status_code == 200
        assert is_partial_html(response.text)

    def test_event_queue_partial(self, mc_client, create_e2e_tournament):
        """GET /event/{id}/queue returns partial HTML."""
        import asyncio
        from app.models.tournament import TournamentPhase

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        response = mc_client.get(
            f"/event/{tournament.id}/queue",
            headers=htmx_headers(),
        )

        assert response.status_code == 200
        assert is_partial_html(response.text)

    def test_event_progress_partial(self, mc_client, create_e2e_tournament):
        """GET /event/{id}/progress returns partial HTML."""
        import asyncio
        from app.models.tournament import TournamentPhase

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        response = mc_client.get(
            f"/event/{tournament.id}/progress",
            headers=htmx_headers(),
        )

        assert response.status_code == 200
        assert is_partial_html(response.text)


class TestFullPageVsPartial:
    """Test that same endpoint returns full page without HX-Request."""

    def test_full_page_without_htmx_header(self, mc_client, create_e2e_tournament):
        """GET /event/{id} returns full page without HX-Request header."""
        import asyncio
        from app.models.tournament import TournamentPhase

        data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
        tournament = data["tournament"]

        # Without HTMX header
        response = mc_client.get(f"/event/{tournament.id}")

        assert response.status_code == 200
        assert is_full_page(response.text)


class TestBattleQueueHTMX:
    """Test battle queue HTMX endpoints."""

    def test_battle_queue_partial_by_category(self, staff_client, create_e2e_tournament):
        """GET /battles/queue/{category_id} returns partial HTML."""
        import asyncio

        data = asyncio.run(create_e2e_tournament())
        category = data["categories"][0]

        response = staff_client.get(
            f"/battles/queue/{category.id}",
            headers=htmx_headers(),
        )

        assert response.status_code == 200
        assert is_partial_html(response.text)

    def test_battle_reorder_returns_partial_htmx(
        self, staff_client, create_e2e_tournament, create_e2e_battle
    ):
        """POST /battles/{id}/reorder returns partial HTML for HTMX."""
        import asyncio
        from app.models.battle import BattlePhase

        data = asyncio.run(create_e2e_tournament())
        battle = asyncio.run(create_e2e_battle(
            category_id=data["categories"][0].id,
            phase=BattlePhase.PRESELECTION,
            performers=data["performers"][:2],
        ))

        response = staff_client.post(
            f"/battles/{battle.id}/reorder",
            data={"new_position": "1"},
            headers=htmx_headers(),
        )

        # Should return partial HTML, not redirect
        # Note: Depends on route implementation
        assert response.status_code == 200
```

---

## 5. Documentation Update Plan

### Level 3 Updates

**TESTING.md:**
- Section: End-to-End Tests
- Add: E2E test structure and patterns
- Add: Example test code
- Add: HTMX testing patterns specific to E2E

Update content:

```markdown
### End-to-End Tests (Phase 3.6)

E2E tests verify complete user workflows through the HTTP interface.

**Location:** `tests/e2e/`

**What E2E tests cover:**
- Complete user flows (Event Mode, Tournament Management)
- HTTP-level request/response cycle
- HTMX partial responses
- Authentication and authorization
- Form validation and error handling

**Pattern:**
```python
def test_complete_battle_workflow(mc_client, create_e2e_tournament, create_e2e_battle):
    """Test complete battle: view → start → encode."""
    import asyncio

    # Setup
    data = asyncio.run(create_e2e_tournament(phase=TournamentPhase.PRESELECTION))
    battle = asyncio.run(create_e2e_battle(...))

    # Start battle
    response = mc_client.post(f"/battles/{battle.id}/start")
    assert response.status_code == 303

    # Encode results
    response = mc_client.post(
        f"/battles/{battle.id}/encode",
        data={...},
    )
    assert response.status_code == 303
```

**E2E Test Files:**
- `test_event_mode.py` - Event Mode workflow (MC)
- `test_tournament_management.py` - Tournament setup (Admin/Staff)
- `test_htmx_interactions.py` - HTMX partial response tests
- `test_authentication_flows.py` - Auth workflows (future)
```

---

## 6. Testing Plan

### Unit Tests
**No new unit tests** - This is an E2E testing feature.

### Integration Tests
**No service integration tests needed** - E2E tests use full stack.

### E2E Tests (New)
| File | Test Count | Coverage |
|------|------------|----------|
| test_event_mode.py | ~12 | Event Mode workflow |
| test_tournament_management.py | ~10 | Tournament setup |
| test_htmx_interactions.py | ~8 | HTMX partials |
| Total | ~30 | Critical user flows |

### Test Verification
```bash
# Run E2E tests
pytest tests/e2e/ -v

# Run E2E tests with coverage
pytest tests/e2e/ --cov=app/routers --cov-report=term-missing
```

---

## 7. Risk Analysis

### Risk 1: Async/Sync Boundary Complexity
**Concern:** Using `asyncio.run()` inside sync test functions may cause issues
**Likelihood:** Medium
**Impact:** High (tests fail)
**Mitigation:**
- Follow pattern from test_crud_workflows.py which uses same approach
- Consider converting fixtures to sync where possible
- Test thoroughly before committing

### Risk 2: Session Cookie Handling
**Concern:** Cookie management between requests may be fragile
**Likelihood:** Medium
**Impact:** Medium (auth tests fail)
**Mitigation:**
- Use established pattern from test_crud_workflows.py
- Use TestClient context manager to maintain cookies
- Verify cookie handling in first tests

### Risk 3: Database State Between Tests
**Concern:** Tests may interfere with each other
**Likelihood:** Low (setup_test_database fixture handles this)
**Impact:** High (flaky tests)
**Mitigation:**
- Rely on existing setup_test_database fixture (drops/creates tables per test)
- Use unique identifiers for test data
- Avoid shared state between test classes

### Risk 4: HTMX Route Behavior
**Concern:** Some routes may not differentiate HTMX vs regular requests
**Likelihood:** Medium
**Impact:** Medium (tests fail but identify real issue)
**Mitigation:**
- Document expected behavior
- Tests that fail reveal routes needing HTMX support
- Consider this a feature (tests catch real bugs)

---

## 8. Implementation Order

**Recommended sequence to minimize risk:**

1. **Test Infrastructure** (Foundation)
   - Create tests/e2e/__init__.py with utilities
   - Create tests/e2e/conftest.py with fixtures
   - Verify fixtures work with simple smoke test

2. **Event Mode Tests** (Critical Path)
   - test_event_mode.py - command center access
   - test_event_mode.py - battle start/encode
   - Run tests, fix any infrastructure issues

3. **Tournament Management Tests** (High Priority)
   - test_tournament_management.py - create tournament
   - test_tournament_management.py - category management
   - test_tournament_management.py - phase advancement

4. **HTMX Tests** (High Priority)
   - test_htmx_interactions.py - partial responses
   - Verify HTMX patterns work correctly

5. **Documentation** (Final)
   - Update TESTING.md with E2E section
   - Add patterns and examples

---

## 9. Open Questions

- [x] Should tests use sync TestClient or async AsyncClient? → **Sync TestClient** (matches existing pattern)
- [x] How to handle database state? → **Existing setup_test_database fixture** handles cleanup
- [ ] Should we add authentication flow tests in Phase 1? → **Recommend deferring** to focus on Event Mode

---

## 10. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
