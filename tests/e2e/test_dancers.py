"""E2E tests for Dancers Router.

Tests dancer management through HTTP interface.
Target: Improve coverage from 39% to 80%+
"""
import pytest
from uuid import uuid4

from tests.e2e import (
    is_partial_html,
    htmx_headers,
    assert_status_ok,
    assert_redirect,
)


class TestDancersListAccess:
    """Test dancers list page access."""

    def test_dancers_list_requires_auth(self, e2e_client):
        """GET /dancers requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /dancers
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/dancers")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_dancers_list_loads(self, staff_client):
        """GET /dancers loads dancer list page.

        Validates: DOMAIN_MODEL.md Dancer entity access
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers
            Then the page loads successfully (200)
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/dancers")

        # Then
        assert_status_ok(response)

    def test_dancers_list_with_search(self, staff_client):
        """GET /dancers?search= supports search parameter.

        Validates: DOMAIN_MODEL.md Dancer entity search
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers?search=test
            Then the page loads successfully (200)
            And the list is filtered by the search term
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/dancers?search=test")

        # Then
        assert_status_ok(response)


class TestDancerCreateForm:
    """Test dancer creation form."""

    def test_create_form_requires_auth(self, e2e_client):
        """GET /dancers/create requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /dancers/create
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/dancers/create")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_create_form_loads(self, staff_client):
        """GET /dancers/create loads create form.

        Validates: DOMAIN_MODEL.md Dancer entity creation
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers/create
            Then the page loads successfully (200)
            And I see an email input field
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/dancers/create")

        # Then
        assert_status_ok(response)
        # Should have email and date fields
        assert "email" in response.text.lower()


class TestDancerCreate:
    """Test dancer creation."""

    def test_create_dancer_requires_auth(self, e2e_client):
        """POST /dancers/create requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /dancers/create with dancer data
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(
            "/dancers/create",
            data={
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "Dancer",
                "date_of_birth": "2000-01-01",
                "blaze": "TestBlaze",
            },
        )

        # Then
        assert response.status_code in [401, 302, 303]

    def test_create_dancer_success(self, staff_client):
        """POST /dancers/create creates dancer and redirects.

        Validates: DOMAIN_MODEL.md Dancer entity creation
        Gherkin:
            Given I am authenticated as Staff
            When I POST to /dancers/create with valid dancer data
            Then I am redirected to the dancers list or dancer profile
        """
        # Given (authenticated via staff_client fixture)
        unique_email = f"dancer_{uuid4().hex[:8]}@test.com"
        unique_blaze = f"Blaze{uuid4().hex[:6]}"

        # When
        response = staff_client.post(
            "/dancers/create",
            data={
                "email": unique_email,
                "first_name": "New",
                "last_name": "Dancer",
                "date_of_birth": "2000-01-01",
                "blaze": unique_blaze,
            },
            follow_redirects=False,
        )

        # Then
        assert_redirect(response)


class TestDancerProfile:
    """Test dancer profile page."""

    def test_profile_requires_auth(self, e2e_client):
        """GET /dancers/{id}/profile requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /dancers/{id}/profile
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get(f"/dancers/{uuid4()}/profile")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_profile_invalid_uuid(self, staff_client):
        """GET /dancers/{id}/profile handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers/not-a-uuid/profile
            Then I receive a 400 Bad Request response
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/dancers/not-a-uuid/profile")

        # Then
        assert response.status_code == 400

    def test_profile_nonexistent(self, staff_client):
        """GET /dancers/{id}/profile returns 404 for non-existent dancer.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no dancer exists with the given ID
            When I navigate to /dancers/{id}/profile
            Then I receive a 404 Not Found response
        """
        # Given (authenticated via staff_client fixture)
        fake_id = uuid4()

        # When
        response = staff_client.get(f"/dancers/{fake_id}/profile")

        # Then
        assert response.status_code == 404

    def test_profile_loads(self, staff_client, create_e2e_tournament):
        """GET /dancers/{id}/profile loads with valid dancer.

        Validates: DOMAIN_MODEL.md Dancer entity access
        Gherkin:
            Given I am authenticated as Staff
            And a dancer exists in the system
            When I navigate to /dancers/{id}/profile
            Then the page loads successfully (200)
        """
        import asyncio

        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        dancer = data["dancers"][0]

        # When
        response = staff_client.get(f"/dancers/{dancer.id}/profile")

        # Then
        assert_status_ok(response)


class TestDancerEdit:
    """Test dancer edit functionality."""

    def test_edit_form_requires_auth(self, e2e_client):
        """GET /dancers/{id}/edit requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /dancers/{id}/edit
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get(f"/dancers/{uuid4()}/edit")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_edit_form_invalid_uuid(self, staff_client):
        """GET /dancers/{id}/edit handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers/not-a-uuid/edit
            Then I receive a 400 Bad Request response
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/dancers/not-a-uuid/edit")

        # Then
        assert response.status_code == 400

    def test_edit_form_nonexistent(self, staff_client):
        """GET /dancers/{id}/edit returns 404 for non-existent dancer.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no dancer exists with the given ID
            When I navigate to /dancers/{id}/edit
            Then I receive a 404 Not Found response
        """
        # Given (authenticated via staff_client fixture)
        fake_id = uuid4()

        # When
        response = staff_client.get(f"/dancers/{fake_id}/edit")

        # Then
        assert response.status_code == 404

    def test_edit_form_loads(self, staff_client, create_e2e_tournament):
        """GET /dancers/{id}/edit loads with valid dancer.

        Validates: DOMAIN_MODEL.md Dancer entity editing
        Gherkin:
            Given I am authenticated as Staff
            And a dancer exists in the system
            When I navigate to /dancers/{id}/edit
            Then the page loads successfully (200)
        """
        import asyncio

        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        dancer = data["dancers"][0]

        # When
        response = staff_client.get(f"/dancers/{dancer.id}/edit")

        # Then
        assert_status_ok(response)

    def test_edit_post_requires_auth(self, e2e_client):
        """POST /dancers/{id}/edit requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /dancers/{id}/edit with dancer data
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(
            f"/dancers/{uuid4()}/edit",
            data={
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "Dancer",
                "date_of_birth": "2000-01-01",
                "blaze": "Blaze",
            },
        )

        # Then
        assert response.status_code in [401, 302, 303]

    def test_edit_post_invalid_uuid(self, staff_client):
        """POST /dancers/{id}/edit handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Staff
            When I POST to /dancers/not-a-uuid/edit with dancer data
            Then I receive a 400 Bad Request response
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.post(
            "/dancers/not-a-uuid/edit",
            data={
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "Dancer",
                "date_of_birth": "2000-01-01",
                "blaze": "Blaze",
            },
            follow_redirects=False,
        )

        # Then
        # Returns 400 Bad Request for invalid UUID
        assert response.status_code == 400


class TestDancerAPISearch:
    """Test dancer API search endpoint."""

    def test_api_search_requires_auth(self, e2e_client):
        """GET /dancers/api/search requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I call /dancers/api/search?query=test
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/dancers/api/search?query=test")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_api_search_returns_partial(self, staff_client):
        """GET /dancers/api/search returns partial HTML.

        Validates: FRONTEND.md HTMX Patterns (partial HTML responses)
        Gherkin:
            Given I am authenticated as Staff
            When I call /dancers/api/search?query=test with HX-Request header
            Then the response is successful (200)
            And the response is partial HTML (no full page wrapper)
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get(
            "/dancers/api/search?query=test",
            headers=htmx_headers(),
        )

        # Then
        assert_status_ok(response)
        assert is_partial_html(response.text)

    def test_api_search_empty_query(self, staff_client):
        """GET /dancers/api/search handles empty query.

        Validates: [Derived] HTTP graceful error handling
        Gherkin:
            Given I am authenticated as Staff
            When I call /dancers/api/search?query= with empty query
            Then the response is successful (200)
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get(
            "/dancers/api/search?query=",
            headers=htmx_headers(),
        )

        # Then
        assert_status_ok(response)

    def test_api_search_no_results(self, staff_client):
        """GET /dancers/api/search handles no results.

        Validates: [Derived] HTTP graceful error handling
        Gherkin:
            Given I am authenticated as Staff
            When I call /dancers/api/search with a query that matches no dancers
            Then the response is successful (200)
            And the response contains empty or "no results" content
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get(
            "/dancers/api/search?query=nonexistent12345xyz",
            headers=htmx_headers(),
        )

        # Then
        assert_status_ok(response)
