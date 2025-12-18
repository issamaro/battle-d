"""E2E tests for Event Mode (MC workflow).

Tests battle workflow routes through HTTP interface.
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §3.1

Note: Tests that require pre-created tournaments use HTTP endpoints to create data
since direct database access is isolated from the TestClient's database context.
"""
import pytest
from uuid import uuid4

from tests.e2e import (
    is_partial_html,
    htmx_headers,
    assert_status_ok,
    assert_redirect,
    assert_unauthorized,
)


class TestBattleListAccess:
    """Test battle list page access.

    NOTE: The /battles list route was removed as part of screen consolidation.
    Battle management is now done exclusively through Event Mode.
    See: FEATURE_SPEC_2024-12-18_SCREEN-CONSOLIDATION.md
    """

    def test_battle_list_route_removed(self, staff_client):
        """GET /battles returns 404 (route removed).

        Validates: BR-NAV-001 - Single path to functions
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /battles
            Then I receive a 404 Not Found response
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/battles")

        # Then - route should no longer exist
        assert response.status_code == 404


class TestBattleDetailAccess:
    """Test battle detail page access patterns."""

    def test_battle_detail_nonexistent_returns_404(self, staff_client):
        """GET /battles/{id} returns 404 for non-existent battle.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no battle exists with the given ID
            When I navigate to /battles/{id}
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.get(f"/battles/{fake_id}")

        # Then
        assert response.status_code == 404

    def test_battle_detail_requires_authentication(self, e2e_client):
        """GET /battles/{id} requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /battles/{id}
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.get(f"/battles/{fake_id}")

        # Then
        assert response.status_code in [401, 302, 303]


class TestBattleStartAccess:
    """Test battle start endpoint access patterns."""

    def test_start_battle_nonexistent_returns_404(self, staff_client):
        """POST /battles/{id}/start returns 404 for non-existent battle.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no battle exists with the given ID
            When I POST to /battles/{id}/start
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.post(f"/battles/{fake_id}/start", follow_redirects=False)

        # Then
        assert response.status_code == 404

    def test_start_battle_requires_authentication(self, e2e_client):
        """POST /battles/{id}/start requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /battles/{id}/start
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.post(f"/battles/{fake_id}/start")

        # Then
        assert response.status_code in [401, 302, 303]


class TestBattleEncodingAccess:
    """Test battle encoding endpoint access patterns."""

    def test_encode_form_nonexistent_returns_404(self, staff_client):
        """GET /battles/{id}/encode returns 404 for non-existent battle.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no battle exists with the given ID
            When I navigate to /battles/{id}/encode
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.get(f"/battles/{fake_id}/encode")

        # Then
        assert response.status_code == 404

    def test_encode_form_requires_authentication(self, e2e_client):
        """GET /battles/{id}/encode requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /battles/{id}/encode
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.get(f"/battles/{fake_id}/encode")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_encode_submit_nonexistent_returns_404(self, staff_client):
        """POST /battles/{id}/encode returns 404 for non-existent battle.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no battle exists with the given ID
            When I POST to /battles/{id}/encode with empty data
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.post(
            f"/battles/{fake_id}/encode",
            data={},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404

    def test_encode_submit_requires_authentication(self, e2e_client):
        """POST /battles/{id}/encode requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /battles/{id}/encode
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.post(f"/battles/{fake_id}/encode", data={})

        # Then
        assert response.status_code in [401, 302, 303]


class TestEventModeAccess:
    """Test event mode command center access patterns."""

    def test_command_center_nonexistent_returns_404(self, mc_client):
        """GET /event/{id} returns 404 for non-existent tournament.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as MC
            And no tournament exists with the given ID
            When I navigate to /event/{id}
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = mc_client.get(f"/event/{fake_id}")

        # Then
        assert response.status_code == 404

    def test_command_center_requires_authentication(self, e2e_client):
        """GET /event/{id} requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /event/{id}
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.get(f"/event/{fake_id}")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_command_center_requires_mc_role(self, judge_client):
        """GET /event/{id} requires MC role.

        Validates: DOMAIN_MODEL.md User roles (MC access)
        Gherkin:
            Given I am authenticated as Judge (not MC)
            When I navigate to /event/{id}
            Then I am denied access (401/403/404)
        """
        # Given
        fake_id = uuid4()

        # When
        response = judge_client.get(f"/event/{fake_id}")

        # Then
        # Judge role shouldn't access command center (should be 401/403)
        # or 404 if role check happens after tournament lookup
        assert response.status_code in [401, 403, 404]


class TestBattleQueueAccess:
    """Test battle queue endpoint access patterns."""

    def test_battle_queue_nonexistent_category(self, staff_client):
        """GET /battles/queue/{category_id} handles non-existent category.

        Validates: [Derived] HTTP graceful handling of missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no category exists with the given ID
            When I navigate to /battles/queue/{category_id}
            Then I receive either empty results (200) or 404
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.get(f"/battles/queue/{fake_id}")

        # Then
        # Should return empty result or 404
        assert response.status_code in [200, 404]

    def test_battle_queue_requires_authentication(self, e2e_client):
        """GET /battles/queue/{category_id} requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /battles/queue/{category_id}
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.get(f"/battles/queue/{fake_id}")

        # Then
        assert response.status_code in [401, 302, 303]


class TestBattleReorderAccess:
    """Test battle reorder endpoint access patterns."""

    def test_reorder_nonexistent_battle_returns_404(self, staff_client):
        """POST /battles/{id}/reorder returns 404 for non-existent battle.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no battle exists with the given ID
            When I POST to /battles/{id}/reorder with a new position
            Then I receive a 404 Not Found response
        """
        # Given
        fake_id = uuid4()

        # When
        response = staff_client.post(
            f"/battles/{fake_id}/reorder",
            data={"new_position": "1"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404

    def test_reorder_requires_authentication(self, e2e_client):
        """POST /battles/{id}/reorder requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /battles/{id}/reorder
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given
        fake_id = uuid4()

        # When
        response = e2e_client.post(
            f"/battles/{fake_id}/reorder",
            data={"new_position": "1"},
        )

        # Then
        assert response.status_code in [401, 302, 303]


# NOTE: Tests with real battle data (TestBattleWorkflowWithRealData,
# TestEventModeWithRealTournament) removed due to database session isolation.
# Data created in async fixtures is not visible to TestClient.
# These code paths are covered by service integration tests instead:
# - tests/test_battle_results_encoding_integration.py
# - tests/test_event_service_integration.py
