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
        """GET /dancers requires authentication."""
        response = e2e_client.get("/dancers")

        assert response.status_code in [401, 302, 303]

    def test_dancers_list_loads(self, staff_client):
        """GET /dancers loads dancer list page."""
        response = staff_client.get("/dancers")

        assert_status_ok(response)

    def test_dancers_list_with_search(self, staff_client):
        """GET /dancers?search= supports search parameter."""
        response = staff_client.get("/dancers?search=test")

        assert_status_ok(response)


class TestDancerCreateForm:
    """Test dancer creation form."""

    def test_create_form_requires_auth(self, e2e_client):
        """GET /dancers/create requires authentication."""
        response = e2e_client.get("/dancers/create")

        assert response.status_code in [401, 302, 303]

    def test_create_form_loads(self, staff_client):
        """GET /dancers/create loads create form."""
        response = staff_client.get("/dancers/create")

        assert_status_ok(response)
        # Should have email and date fields
        assert "email" in response.text.lower()


class TestDancerCreate:
    """Test dancer creation."""

    def test_create_dancer_requires_auth(self, e2e_client):
        """POST /dancers/create requires authentication."""
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

        assert response.status_code in [401, 302, 303]

    def test_create_dancer_success(self, staff_client):
        """POST /dancers/create creates dancer and redirects."""
        unique_email = f"dancer_{uuid4().hex[:8]}@test.com"
        unique_blaze = f"Blaze{uuid4().hex[:6]}"
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

        assert_redirect(response)


class TestDancerProfile:
    """Test dancer profile page."""

    def test_profile_requires_auth(self, e2e_client):
        """GET /dancers/{id}/profile requires authentication."""
        response = e2e_client.get(f"/dancers/{uuid4()}/profile")

        assert response.status_code in [401, 302, 303]

    def test_profile_invalid_uuid(self, staff_client):
        """GET /dancers/{id}/profile handles invalid UUID."""
        response = staff_client.get("/dancers/not-a-uuid/profile")

        assert response.status_code == 400

    def test_profile_nonexistent(self, staff_client):
        """GET /dancers/{id}/profile returns 404 for non-existent dancer."""
        fake_id = uuid4()
        response = staff_client.get(f"/dancers/{fake_id}/profile")

        assert response.status_code == 404

    def test_profile_loads(self, staff_client, create_e2e_tournament):
        """GET /dancers/{id}/profile loads with valid dancer."""
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        dancer = data["dancers"][0]

        response = staff_client.get(f"/dancers/{dancer.id}/profile")

        assert_status_ok(response)


class TestDancerEdit:
    """Test dancer edit functionality."""

    def test_edit_form_requires_auth(self, e2e_client):
        """GET /dancers/{id}/edit requires authentication."""
        response = e2e_client.get(f"/dancers/{uuid4()}/edit")

        assert response.status_code in [401, 302, 303]

    def test_edit_form_invalid_uuid(self, staff_client):
        """GET /dancers/{id}/edit handles invalid UUID."""
        response = staff_client.get("/dancers/not-a-uuid/edit")

        assert response.status_code == 400

    def test_edit_form_nonexistent(self, staff_client):
        """GET /dancers/{id}/edit returns 404 for non-existent dancer."""
        fake_id = uuid4()
        response = staff_client.get(f"/dancers/{fake_id}/edit")

        assert response.status_code == 404

    def test_edit_form_loads(self, staff_client, create_e2e_tournament):
        """GET /dancers/{id}/edit loads with valid dancer."""
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        dancer = data["dancers"][0]

        response = staff_client.get(f"/dancers/{dancer.id}/edit")

        assert_status_ok(response)

    def test_edit_post_requires_auth(self, e2e_client):
        """POST /dancers/{id}/edit requires authentication."""
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

        assert response.status_code in [401, 302, 303]

    def test_edit_post_invalid_uuid(self, staff_client):
        """POST /dancers/{id}/edit handles invalid UUID."""
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

        # Returns 400 Bad Request for invalid UUID
        assert response.status_code == 400


class TestDancerAPISearch:
    """Test dancer API search endpoint."""

    def test_api_search_requires_auth(self, e2e_client):
        """GET /dancers/api/search requires authentication."""
        response = e2e_client.get("/dancers/api/search?query=test")

        assert response.status_code in [401, 302, 303]

    def test_api_search_returns_partial(self, staff_client):
        """GET /dancers/api/search returns partial HTML."""
        response = staff_client.get(
            "/dancers/api/search?query=test",
            headers=htmx_headers(),
        )

        assert_status_ok(response)
        assert is_partial_html(response.text)

    def test_api_search_empty_query(self, staff_client):
        """GET /dancers/api/search handles empty query."""
        response = staff_client.get(
            "/dancers/api/search?query=",
            headers=htmx_headers(),
        )

        assert_status_ok(response)

    def test_api_search_no_results(self, staff_client):
        """GET /dancers/api/search handles no results."""
        response = staff_client.get(
            "/dancers/api/search?query=nonexistent12345xyz",
            headers=htmx_headers(),
        )

        assert_status_ok(response)
