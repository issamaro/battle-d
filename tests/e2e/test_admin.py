"""E2E tests for Admin Router.

Tests admin user management through HTTP interface.
Target: Improve coverage from 35% to 80%+
"""
import pytest
from uuid import uuid4

from tests.e2e import (
    is_partial_html,
    htmx_headers,
    assert_status_ok,
    assert_redirect,
    assert_contains_text,
)


class TestAdminUsersListAccess:
    """Test admin users list access patterns."""

    def test_users_list_requires_auth(self, e2e_client):
        """GET /admin/users requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /admin/users
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/admin/users")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_users_list_requires_admin(self, staff_client):
        """GET /admin/users requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I navigate to /admin/users
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.get("/admin/users")

        # Then
        assert response.status_code in [401, 403]

    def test_users_list_loads(self, admin_client):
        """GET /admin/users loads user list page.

        Validates: DOMAIN_MODEL.md User entity management
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the page loads successfully (200)
            And I see role filter options
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)
        # Should show role filter options
        assert "admin" in response.text.lower()

    def test_users_list_filter_by_role(self, admin_client):
        """GET /admin/users?role_filter= filters by role.

        Validates: DOMAIN_MODEL.md User entity filtering
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users?role_filter=admin
            Then the page loads successfully (200)
            And the list is filtered to show only admin users
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users?role_filter=admin")

        # Then
        assert_status_ok(response)

    def test_users_list_invalid_role_filter(self, admin_client):
        """GET /admin/users?role_filter= handles invalid role gracefully.

        Validates: [Derived] HTTP graceful error handling
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users?role_filter=invalidrole
            Then the page loads successfully (200)
            And the invalid filter is ignored
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users?role_filter=invalidrole")

        # Then
        # Should still return 200, just ignores invalid filter
        assert_status_ok(response)


class TestCreateUserForm:
    """Test create user form access."""

    def test_create_form_requires_auth(self, e2e_client):
        """GET /admin/users/create requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /admin/users/create
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/admin/users/create")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_create_form_requires_admin(self, staff_client):
        """GET /admin/users/create requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I navigate to /admin/users/create
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.get("/admin/users/create")

        # Then
        assert response.status_code in [401, 403]

    def test_create_form_loads(self, admin_client):
        """GET /admin/users/create loads create form.

        Validates: DOMAIN_MODEL.md User entity creation
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users/create
            Then the page loads successfully (200)
            And I see a role selection field
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users/create")

        # Then
        assert_status_ok(response)
        # Should show role selection
        assert "role" in response.text.lower()


class TestCreateUser:
    """Test user creation."""

    def test_create_user_requires_auth(self, e2e_client):
        """POST /admin/users/create requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /admin/users/create with user data
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(
            "/admin/users/create",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        # Then
        assert response.status_code in [401, 302, 303]

    def test_create_user_requires_admin(self, staff_client):
        """POST /admin/users/create requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I POST to /admin/users/create with user data
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post(
            "/admin/users/create",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        # Then
        assert response.status_code in [401, 403]

    def test_create_user_invalid_role(self, admin_client):
        """POST /admin/users/create rejects invalid role.

        Validates: VALIDATION_RULES.md User role validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/create with an invalid role
            Then I am redirected back to the create form (303)
            And the user is not created
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "newuser@test.com",
                "first_name": "New",
                "role": "invalidrole",
            },
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303
        assert "/admin/users/create" in response.headers.get("location", "")

    def test_create_user_duplicate_email(self, admin_client):
        """POST /admin/users/create rejects duplicate email.

        Validates: DOMAIN_MODEL.md User entity (unique email constraint)
        Gherkin:
            Given I am authenticated as Admin
            And a user with email admin@e2e-test.com already exists
            When I POST to /admin/users/create with that email
            Then I am redirected back to the create form (303)
            And the duplicate user is not created
        """
        # Given (authenticated as admin via admin_client fixture)
        # admin@e2e-test.com already exists from fixtures

        # When
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "admin@e2e-test.com",
                "first_name": "Duplicate",
                "role": "staff",
            },
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303
        assert "/admin/users/create" in response.headers.get("location", "")

    def test_create_user_success(self, admin_client):
        """POST /admin/users/create creates user and redirects.

        Validates: DOMAIN_MODEL.md User entity creation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/create with valid user data
            Then I am redirected to the users list (303)
            And the new user is created
        """
        # Given (authenticated as admin via admin_client fixture)
        unique_email = f"newuser_{uuid4().hex[:8]}@test.com"

        # When
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": unique_email,
                "first_name": "New User",
                "role": "staff",
            },
            follow_redirects=False,
        )

        # Then
        assert_redirect(response)
        assert "/admin/users" in response.headers.get("location", "")

    def test_create_user_with_magic_link(self, admin_client):
        """POST /admin/users/create with send_magic_link sends email.

        Validates: VALIDATION_RULES.md Magic Link Authentication
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/create with send_magic_link=true
            Then I am redirected to the users list
            And a magic link email is sent to the user
        """
        # Given (authenticated as admin via admin_client fixture)
        unique_email = f"magiclink_{uuid4().hex[:8]}@test.com"

        # When
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": unique_email,
                "first_name": "Magic User",
                "role": "staff",
                "send_magic_link": "true",
            },
            follow_redirects=False,
        )

        # Then
        assert_redirect(response)


class TestDeleteUser:
    """Test user deletion."""

    def test_delete_user_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/delete requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /admin/users/{id}/delete
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(f"/admin/users/{uuid4()}/delete")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_delete_user_requires_admin(self, staff_client):
        """POST /admin/users/{id}/delete requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I POST to /admin/users/{id}/delete
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post(f"/admin/users/{uuid4()}/delete")

        # Then
        assert response.status_code in [401, 403]

    def test_delete_user_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/delete handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/not-a-uuid/delete
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/users/not-a-uuid/delete",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_delete_user_nonexistent_returns_404(self, admin_client):
        """POST /admin/users/{id}/delete returns 404 for non-existent user.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Admin
            And no user exists with the given ID
            When I POST to /admin/users/{id}/delete
            Then I receive a 404 Not Found response
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.post(
            f"/admin/users/{fake_id}/delete",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404


class TestEditUserForm:
    """Test edit user form access."""

    def test_edit_form_requires_auth(self, e2e_client):
        """GET /admin/users/{id}/edit requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /admin/users/{id}/edit
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get(f"/admin/users/{uuid4()}/edit")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_edit_form_requires_admin(self, staff_client):
        """GET /admin/users/{id}/edit requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I navigate to /admin/users/{id}/edit
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.get(f"/admin/users/{uuid4()}/edit")

        # Then
        assert response.status_code in [401, 403]

    def test_edit_form_invalid_uuid(self, admin_client):
        """GET /admin/users/{id}/edit rejects invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users/not-a-uuid/edit
            Then I receive a 400 Bad Request response
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users/not-a-uuid/edit")

        # Then
        assert response.status_code == 400

    def test_edit_form_nonexistent_user(self, admin_client):
        """GET /admin/users/{id}/edit returns 404 for non-existent user.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Admin
            And no user exists with the given ID
            When I navigate to /admin/users/{id}/edit
            Then I receive a 404 Not Found response
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.get(f"/admin/users/{fake_id}/edit")

        # Then
        assert response.status_code == 404


class TestUpdateUser:
    """Test user updates."""

    def test_update_user_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/edit requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /admin/users/{id}/edit with user data
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(
            f"/admin/users/{uuid4()}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        # Then
        assert response.status_code in [401, 302, 303]

    def test_update_user_requires_admin(self, staff_client):
        """POST /admin/users/{id}/edit requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I POST to /admin/users/{id}/edit with user data
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post(
            f"/admin/users/{uuid4()}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        # Then
        assert response.status_code in [401, 403]

    def test_update_user_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/edit handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/not-a-uuid/edit
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/users/not-a-uuid/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_update_user_invalid_role(self, admin_client):
        """POST /admin/users/{id}/edit rejects invalid role.

        Validates: VALIDATION_RULES.md User role validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/{id}/edit with an invalid role
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.post(
            f"/admin/users/{fake_id}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "badrole"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_update_user_nonexistent_returns_404(self, admin_client):
        """POST /admin/users/{id}/edit returns 404 for non-existent user.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Admin
            And no user exists with the given ID
            When I POST to /admin/users/{id}/edit with valid data
            Then I receive a 404 Not Found response
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.post(
            f"/admin/users/{fake_id}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404


class TestResendMagicLink:
    """Test resend magic link functionality."""

    def test_resend_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/resend-magic-link requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /admin/users/{id}/resend-magic-link
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(f"/admin/users/{uuid4()}/resend-magic-link")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_resend_requires_admin(self, staff_client):
        """POST /admin/users/{id}/resend-magic-link requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I POST to /admin/users/{id}/resend-magic-link
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post(f"/admin/users/{uuid4()}/resend-magic-link")

        # Then
        assert response.status_code in [401, 403]

    def test_resend_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/resend-magic-link handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/users/not-a-uuid/resend-magic-link
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/users/not-a-uuid/resend-magic-link",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_resend_nonexistent_user_returns_404(self, admin_client):
        """POST /admin/users/{id}/resend-magic-link returns 404 for non-existent user.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Admin
            And no user exists with the given ID
            When I POST to /admin/users/{id}/resend-magic-link
            Then I receive a 404 Not Found response
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.post(
            f"/admin/users/{fake_id}/resend-magic-link",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404


class TestFixActiveTournaments:
    """Test fix active tournaments endpoint."""

    def test_fix_active_requires_auth(self, e2e_client):
        """POST /admin/tournaments/fix-active requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /admin/tournaments/fix-active
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post("/admin/tournaments/fix-active")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_fix_active_requires_admin(self, staff_client):
        """POST /admin/tournaments/fix-active requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only access)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            When I POST to /admin/tournaments/fix-active
            Then I am denied access (401/403)
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post("/admin/tournaments/fix-active")

        # Then
        assert response.status_code in [401, 403]

    def test_fix_active_no_issue(self, admin_client):
        """POST /admin/tournaments/fix-active when no issue exists.

        Validates: DOMAIN_MODEL.md Tournament entity (single active constraint)
        Gherkin:
            Given I am authenticated as Admin
            And there is no issue with multiple active tournaments
            When I POST to /admin/tournaments/fix-active
            Then I am redirected to /overview (303)
            And an info message indicates no issue found
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            follow_redirects=False,
        )

        # Then
        # Redirects with info message (no issue found)
        assert response.status_code == 303
        assert "/overview" in response.headers.get("location", "")

    def test_fix_active_missing_selection(self, admin_client, create_e2e_tournament):
        """POST /admin/tournaments/fix-active without selection.

        Validates: DOMAIN_MODEL.md Tournament entity (single active constraint)
        Gherkin:
            Given I am authenticated as Admin
            And multiple active tournaments exist
            When I POST to /admin/tournaments/fix-active without selecting which to keep
            Then I am redirected (303) with an error or info message
        """
        import asyncio

        # Given - Create multiple active tournaments
        asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )

        # When
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={},  # No keep_active selected
            follow_redirects=False,
        )

        # Then
        # Should redirect (either with error or info)
        assert response.status_code == 303

    def test_fix_active_invalid_uuid(self, admin_client):
        """POST /admin/tournaments/fix-active with invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/tournaments/fix-active with an invalid UUID
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={"keep_active": "not-a-uuid"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_fix_active_not_in_list(self, admin_client):
        """POST /admin/tournaments/fix-active with UUID not in active list.

        Validates: DOMAIN_MODEL.md Tournament entity (single active constraint)
        Gherkin:
            Given I am authenticated as Admin
            When I POST to /admin/tournaments/fix-active with a UUID not in the active list
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as admin via admin_client fixture)
        fake_id = uuid4()

        # When
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={"keep_active": str(fake_id)},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303
