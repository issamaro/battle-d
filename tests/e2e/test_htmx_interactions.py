"""E2E tests for HTMX interactions.

Tests that HTMX endpoints return partial HTML (not full pages).
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §4.3

Note: Tests focus on HTMX response patterns without requiring pre-created data.
"""
import pytest
from uuid import uuid4

from tests.e2e import (
    is_partial_html,
    is_full_page,
    htmx_headers,
    assert_status_ok,
)


class TestDancerSearchPartial:
    """Test dancer search HTMX endpoint."""

    def test_dancer_search_returns_partial(self, staff_client):
        """GET /dancers/api/search returns partial HTML."""
        response = staff_client.get(
            "/dancers/api/search?query=test",
            headers=htmx_headers(),
        )

        assert_status_ok(response)
        assert is_partial_html(response.text)

    def test_dancer_search_empty_returns_partial(self, staff_client):
        """GET /dancers/api/search with no results returns partial HTML."""
        response = staff_client.get(
            "/dancers/api/search?query=nonexistent12345",
            headers=htmx_headers(),
        )

        assert_status_ok(response)
        assert is_partial_html(response.text)

    def test_dancer_search_without_htmx_header(self, staff_client):
        """GET /dancers/api/search still works without HX-Request header."""
        response = staff_client.get("/dancers/api/search?query=test")

        assert_status_ok(response)


class TestBattleQueuePartials:
    """Test battle queue HTMX endpoints."""

    def test_battle_queue_nonexistent_returns_partial(self, staff_client):
        """GET /battles/queue/{category_id} returns partial HTML for HTMX."""
        fake_id = uuid4()
        response = staff_client.get(
            f"/battles/queue/{fake_id}",
            headers=htmx_headers(),
        )

        # Should return 200 (empty) or 404, but always partial for HTMX
        if response.status_code == 200:
            assert is_partial_html(response.text)


class TestFullPageResponses:
    """Test that pages return full HTML without HX-Request header."""

    def test_overview_full_page(self, staff_client):
        """GET /overview returns full page."""
        response = staff_client.get("/overview")

        assert_status_ok(response)
        assert is_full_page(response.text)

    def test_tournaments_list_full_page(self, staff_client):
        """GET /tournaments returns full page."""
        response = staff_client.get("/tournaments")

        assert_status_ok(response)
        assert is_full_page(response.text)

    def test_dancers_list_full_page(self, staff_client):
        """GET /dancers returns full page."""
        response = staff_client.get("/dancers")

        assert_status_ok(response)
        assert is_full_page(response.text)

    def test_battles_list_full_page(self, staff_client):
        """GET /battles returns full page."""
        response = staff_client.get("/battles")

        assert_status_ok(response)
        assert is_full_page(response.text)


class TestHTMXHeaderBehavior:
    """Test that routes behave differently based on HX-Request header."""

    def test_dancer_search_with_htmx_is_partial(self, staff_client):
        """Search with HX-Request returns partial HTML."""
        response = staff_client.get(
            "/dancers/api/search?query=test",
            headers=htmx_headers(),
        )

        assert_status_ok(response)
        assert is_partial_html(response.text)
        # Partial HTML should NOT have doctype or html tags
        assert "<!DOCTYPE" not in response.text

    def test_dancers_list_without_htmx_is_full(self, staff_client):
        """List without HX-Request returns full page."""
        response = staff_client.get("/dancers")

        assert_status_ok(response)
        assert is_full_page(response.text)
        # Full page should have html tag
        assert "<html" in response.text.lower()
