"""Prototype tests for session isolation fix.

This file explores two approaches to fix the session isolation problem:
1. AsyncClient with shared session override
2. HTTP-only factories (create data via HTTP requests)

Run with: pytest tests/e2e/test_session_isolation_fix.py -v
"""
import pytest
import pytest_asyncio
from datetime import date
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import async_session_maker, get_db
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository
from app.repositories.user import UserRepository
from app.models.user import UserRole
from app.models.tournament import TournamentPhase
from app.auth import magic_link_auth
from app.config import settings
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service


# =============================================================================
# MOCK EMAIL PROVIDER (needed for both approaches)
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


# =============================================================================
# APPROACH 1: AsyncClient with Shared Session Override
# =============================================================================


class TestAsyncClientApproach:
    """Test approach using httpx.AsyncClient with session override.

    This approach:
    1. Creates a shared session for the entire test
    2. Overrides get_db to return that shared session
    3. Uses AsyncClient for HTTP requests (async)
    4. All operations share the same session = data is visible!

    Pros:
    - Full flexibility - can test any scenario
    - Proper async throughout
    - Can create complex test data in fixtures

    Cons:
    - Requires async test functions
    - Need to manage session lifecycle
    - Slightly more complex setup
    """

    @pytest.mark.asyncio
    async def test_fixture_data_visible_via_session_override(self):
        """Verify fixture-created tournament is visible to HTTP request.

        Validates: TESTING.md Async E2E Tests (Session Sharing Pattern)
        Gherkin:
            Given a tournament is created directly in the shared database session
            And a staff user is created for authentication
            When I make an HTTP request to view the tournament
            Then the tournament should be visible (200 response)
            And the tournament name should appear in the response
        """
        # Given
        async with async_session_maker() as session:
            # Create test data in shared session
            tournament_repo = TournamentRepository(session)
            tournament = await tournament_repo.create_tournament(
                name=f"AsyncClient Test {uuid4().hex[:8]}"
            )
            # Use flush to make data visible within transaction (no commit yet)
            await session.flush()

            # Also create a user for authentication
            user_repo = UserRepository(session)
            await user_repo.create_user(
                "async_test@test.com", "Async Test User", UserRole.STAFF
            )
            await session.flush()

            # Override get_db to yield our shared session
            async def override_get_db():
                yield session

            # Override email service too
            mock_email = MockEmailProvider()

            def get_mock_email_service():
                return EmailService(mock_email)

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[get_email_service] = get_mock_email_service

            try:
                # Generate auth token for staff user
                token = magic_link_auth.generate_token("async_test@test.com", "staff")

                # When - Make HTTP request using AsyncClient
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://test"
                ) as client:
                    # First, verify the token to get session cookie
                    verify_response = await client.get(
                        f"/auth/verify?token={token}", follow_redirects=False
                    )
                    # Extract session cookie
                    cookies = verify_response.cookies

                    # Now request the tournament page
                    response = await client.get(
                        f"/tournaments/{tournament.id}",
                        cookies=cookies,
                    )

                    # Then - Verify tournament is visible!
                    assert response.status_code == 200
                    assert tournament.name.encode() in response.content

            finally:
                app.dependency_overrides.clear()
                # No commit - let transaction rollback (cleanup)

    @pytest.mark.asyncio
    async def test_can_query_fixture_created_performers(self):
        """Verify we can query performers created in fixture.

        Validates: TESTING.md Async E2E Tests (Session Sharing Pattern)
        Gherkin:
            Given a tournament with a category and 4 performers is created in fixture
            And a staff user is created for authentication
            When I make an HTTP request to view the tournament
            Then the tournament should be visible (200 response)
            And the category should appear in the response
        """
        # Given
        async with async_session_maker() as session:
            # Create full test scenario
            tournament_repo = TournamentRepository(session)
            category_repo = CategoryRepository(session)
            dancer_repo = DancerRepository(session)
            performer_repo = PerformerRepository(session)
            user_repo = UserRepository(session)

            # Create user
            await user_repo.create_user(
                "perf_test@test.com", "Perf Test User", UserRole.STAFF
            )

            # Create tournament
            tournament = await tournament_repo.create_tournament(
                name=f"Performer Test {uuid4().hex[:8]}"
            )

            # Create category
            category = await category_repo.create_category(
                tournament_id=tournament.id,
                name="Test Category",
                is_duo=False,
                groups_ideal=2,
                performers_ideal=4,
            )

            # Create dancers and performers
            for i in range(4):
                dancer = await dancer_repo.create_dancer(
                    email=f"dancer_{uuid4().hex[:8]}@test.com",
                    first_name="Dancer",
                    last_name=f"{i + 1}",
                    date_of_birth=date(2000, 1, 1),
                    blaze=f"B-Boy {uuid4().hex[:6]}",
                )
                await performer_repo.create_performer(
                    tournament_id=tournament.id,
                    category_id=category.id,
                    dancer_id=dancer.id,
                )

            await session.flush()

            # Override dependencies
            async def override_get_db():
                yield session

            mock_email = MockEmailProvider()

            def get_mock_email_service():
                return EmailService(mock_email)

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[get_email_service] = get_mock_email_service

            try:
                token = magic_link_auth.generate_token("perf_test@test.com", "staff")

                # When
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://test"
                ) as client:
                    verify_response = await client.get(
                        f"/auth/verify?token={token}", follow_redirects=False
                    )
                    cookies = verify_response.cookies

                    # Request tournament page (shows category with performers)
                    response = await client.get(
                        f"/tournaments/{tournament.id}",
                        cookies=cookies,
                    )

                    # Then - Tournament should be visible with category
                    assert response.status_code == 200
                    assert b"Test Category" in response.content

            finally:
                app.dependency_overrides.clear()


# =============================================================================
# APPROACH 2: HTTP-only Factories
# =============================================================================


class TestHTTPOnlyApproach:
    """Test approach using HTTP requests for all data creation.

    This approach:
    1. Creates data via HTTP POST requests (uses route's session)
    2. Queries data via HTTP GET requests (same route session context)
    3. All operations go through the same session lifecycle

    Pros:
    - Simpler - no session management needed
    - Tests the full stack including form handling
    - Works with existing sync TestClient

    Cons:
    - Limited to what HTTP endpoints expose
    - Can't easily create complex scenarios
    - More verbose test setup
    """

    @pytest.fixture
    def sync_client(self):
        """Sync TestClient with mocked email."""
        mock_email = MockEmailProvider()

        def get_mock_email_service():
            return EmailService(mock_email)

        app.dependency_overrides[get_email_service] = get_mock_email_service

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.fixture
    def auth_cookies(self, sync_client):
        """Get auth cookies for staff user via HTTP."""
        # Create user and get session cookie via HTTP flow
        token = magic_link_auth.generate_token("http_test@test.com", "staff")
        response = sync_client.get(f"/auth/verify?token={token}", follow_redirects=False)

        # Extract cookie
        cookie_name = settings.SESSION_COOKIE_NAME
        set_cookie = response.headers.get("set-cookie", "")
        start = set_cookie.find(f"{cookie_name}=") + len(f"{cookie_name}=")
        end = set_cookie.find(";", start)
        cookie_value = set_cookie[start:end]

        return {cookie_name: cookie_value}

    def test_create_and_view_tournament_via_http(self, sync_client, auth_cookies):
        """Create tournament via HTTP, then view it via HTTP.

        Validates: TESTING.md HTTP-only Factory Pattern
        Gherkin:
            Given I am authenticated as Staff
            When I create a tournament via HTTP POST to /tournaments/create
            Then the response should redirect to the tournament page (303)
            And when I view the tournament page
            Then the tournament should be visible (200 response)
        """
        # Given (authenticated via auth_cookies fixture)

        # When - Create tournament via HTTP POST
        create_response = sync_client.post(
            "/tournaments/create",
            data={"name": f"HTTP Test {uuid4().hex[:8]}"},
            cookies=auth_cookies,
            follow_redirects=False,
        )

        # Then - Should redirect to tournament page
        assert create_response.status_code == 303
        redirect_url = create_response.headers.get("location", "")
        assert "/tournaments/" in redirect_url

        # Extract tournament ID from redirect URL
        tournament_id = redirect_url.split("/tournaments/")[-1]

        # And when - View tournament via HTTP GET
        view_response = sync_client.get(
            f"/tournaments/{tournament_id}",
            cookies=auth_cookies,
        )

        # Then - Should see the tournament
        assert view_response.status_code == 200
        assert b"HTTP Test" in view_response.content

    def test_create_tournament_with_category_via_http(self, sync_client, auth_cookies):
        """Create tournament and category, then verify both visible.

        Validates: TESTING.md HTTP-only Factory Pattern
        Gherkin:
            Given I am authenticated as Staff
            When I create a tournament via HTTP POST
            And I add a category to the tournament via HTTP POST
            Then both should redirect successfully (303)
            And when I view the tournament page
            Then I should see the category name in the response
        """
        # Given (authenticated via auth_cookies fixture)

        # When - Create tournament
        create_response = sync_client.post(
            "/tournaments/create",
            data={"name": f"Cat Test {uuid4().hex[:8]}"},
            cookies=auth_cookies,
            follow_redirects=False,
        )
        tournament_id = create_response.headers.get("location", "").split("/tournaments/")[-1]

        # And - Create category via HTTP (correct route is add-category)
        cat_response = sync_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Test Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            cookies=auth_cookies,
            follow_redirects=False,
        )

        # Then - Should redirect back to tournament
        assert cat_response.status_code == 303

        # And when - View tournament - should show category
        view_response = sync_client.get(
            f"/tournaments/{tournament_id}",
            cookies=auth_cookies,
        )

        # Then
        assert view_response.status_code == 200
        assert b"Test Category" in view_response.content


# =============================================================================
# COMPARISON TEST
# =============================================================================


class TestCompareApproaches:
    """Test to compare what each approach can and cannot do."""

    @pytest.mark.asyncio
    async def test_async_approach_can_create_complex_scenario(self):
        """AsyncClient approach can create any scenario directly in DB.

        Validates: TESTING.md Async E2E Tests (Session Sharing Pattern)
        Gherkin:
            Given a tournament is created in PRESELECTION phase directly in fixture
            And an MC user is created for authentication
            When I access the event mode command center
            Then the page should load successfully (200)
            Because the tournament is already in the required phase
        """
        # Given
        async with async_session_maker() as session:
            tournament_repo = TournamentRepository(session)
            user_repo = UserRepository(session)

            # Create tournament in specific phase (not possible via HTTP without advancing)
            tournament = await tournament_repo.create_tournament(
                name=f"Complex Scenario {uuid4().hex[:8]}"
            )
            await tournament_repo.update(
                tournament.id, phase=TournamentPhase.PRESELECTION
            )
            await user_repo.create_user(
                "complex@test.com", "Complex User", UserRole.MC
            )
            await session.flush()

            async def override_get_db():
                yield session

            mock_email = MockEmailProvider()

            def get_mock_email_service():
                return EmailService(mock_email)

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[get_email_service] = get_mock_email_service

            try:
                token = magic_link_auth.generate_token("complex@test.com", "mc")

                # When
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://test"
                ) as client:
                    verify_response = await client.get(
                        f"/auth/verify?token={token}", follow_redirects=False
                    )
                    cookies = verify_response.cookies

                    # Access event mode command center (requires PRESELECTION phase)
                    response = await client.get(
                        f"/event/{tournament.id}",
                        cookies=cookies,
                    )

                    # Then - Should work because tournament is in PRESELECTION
                    assert response.status_code == 200

            finally:
                app.dependency_overrides.clear()
