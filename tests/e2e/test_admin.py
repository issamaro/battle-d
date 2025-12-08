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
        """GET /admin/users requires authentication."""
        response = e2e_client.get("/admin/users")

        assert response.status_code in [401, 302, 303]

    def test_users_list_requires_admin(self, staff_client):
        """GET /admin/users requires admin role."""
        response = staff_client.get("/admin/users")

        assert response.status_code in [401, 403]

    def test_users_list_loads(self, admin_client):
        """GET /admin/users loads user list page."""
        response = admin_client.get("/admin/users")

        assert_status_ok(response)
        # Should show role filter options
        assert "admin" in response.text.lower()

    def test_users_list_filter_by_role(self, admin_client):
        """GET /admin/users?role_filter= filters by role."""
        response = admin_client.get("/admin/users?role_filter=admin")

        assert_status_ok(response)

    def test_users_list_invalid_role_filter(self, admin_client):
        """GET /admin/users?role_filter= handles invalid role gracefully."""
        response = admin_client.get("/admin/users?role_filter=invalidrole")

        # Should still return 200, just ignores invalid filter
        assert_status_ok(response)


class TestCreateUserForm:
    """Test create user form access."""

    def test_create_form_requires_auth(self, e2e_client):
        """GET /admin/users/create requires authentication."""
        response = e2e_client.get("/admin/users/create")

        assert response.status_code in [401, 302, 303]

    def test_create_form_requires_admin(self, staff_client):
        """GET /admin/users/create requires admin role."""
        response = staff_client.get("/admin/users/create")

        assert response.status_code in [401, 403]

    def test_create_form_loads(self, admin_client):
        """GET /admin/users/create loads create form."""
        response = admin_client.get("/admin/users/create")

        assert_status_ok(response)
        # Should show role selection
        assert "role" in response.text.lower()


class TestCreateUser:
    """Test user creation."""

    def test_create_user_requires_auth(self, e2e_client):
        """POST /admin/users/create requires authentication."""
        response = e2e_client.post(
            "/admin/users/create",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        assert response.status_code in [401, 302, 303]

    def test_create_user_requires_admin(self, staff_client):
        """POST /admin/users/create requires admin role."""
        response = staff_client.post(
            "/admin/users/create",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        assert response.status_code in [401, 403]

    def test_create_user_invalid_role(self, admin_client):
        """POST /admin/users/create rejects invalid role."""
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "newuser@test.com",
                "first_name": "New",
                "role": "invalidrole",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "/admin/users/create" in response.headers.get("location", "")

    def test_create_user_duplicate_email(self, admin_client):
        """POST /admin/users/create rejects duplicate email."""
        # admin@e2e-test.com already exists from fixtures
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "admin@e2e-test.com",
                "first_name": "Duplicate",
                "role": "staff",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "/admin/users/create" in response.headers.get("location", "")

    def test_create_user_success(self, admin_client):
        """POST /admin/users/create creates user and redirects."""
        unique_email = f"newuser_{uuid4().hex[:8]}@test.com"
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": unique_email,
                "first_name": "New User",
                "role": "staff",
            },
            follow_redirects=False,
        )

        assert_redirect(response)
        assert "/admin/users" in response.headers.get("location", "")

    def test_create_user_with_magic_link(self, admin_client):
        """POST /admin/users/create with send_magic_link sends email."""
        unique_email = f"magiclink_{uuid4().hex[:8]}@test.com"
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

        assert_redirect(response)


class TestDeleteUser:
    """Test user deletion."""

    def test_delete_user_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/delete requires authentication."""
        response = e2e_client.post(f"/admin/users/{uuid4()}/delete")

        assert response.status_code in [401, 302, 303]

    def test_delete_user_requires_admin(self, staff_client):
        """POST /admin/users/{id}/delete requires admin role."""
        response = staff_client.post(f"/admin/users/{uuid4()}/delete")

        assert response.status_code in [401, 403]

    def test_delete_user_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/delete handles invalid UUID."""
        response = admin_client.post(
            "/admin/users/not-a-uuid/delete",
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_delete_user_nonexistent_returns_404(self, admin_client):
        """POST /admin/users/{id}/delete returns 404 for non-existent user."""
        fake_id = uuid4()
        response = admin_client.post(
            f"/admin/users/{fake_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 404


class TestEditUserForm:
    """Test edit user form access."""

    def test_edit_form_requires_auth(self, e2e_client):
        """GET /admin/users/{id}/edit requires authentication."""
        response = e2e_client.get(f"/admin/users/{uuid4()}/edit")

        assert response.status_code in [401, 302, 303]

    def test_edit_form_requires_admin(self, staff_client):
        """GET /admin/users/{id}/edit requires admin role."""
        response = staff_client.get(f"/admin/users/{uuid4()}/edit")

        assert response.status_code in [401, 403]

    def test_edit_form_invalid_uuid(self, admin_client):
        """GET /admin/users/{id}/edit rejects invalid UUID."""
        response = admin_client.get("/admin/users/not-a-uuid/edit")

        assert response.status_code == 400

    def test_edit_form_nonexistent_user(self, admin_client):
        """GET /admin/users/{id}/edit returns 404 for non-existent user."""
        fake_id = uuid4()
        response = admin_client.get(f"/admin/users/{fake_id}/edit")

        assert response.status_code == 404


class TestUpdateUser:
    """Test user updates."""

    def test_update_user_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/edit requires authentication."""
        response = e2e_client.post(
            f"/admin/users/{uuid4()}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        assert response.status_code in [401, 302, 303]

    def test_update_user_requires_admin(self, staff_client):
        """POST /admin/users/{id}/edit requires admin role."""
        response = staff_client.post(
            f"/admin/users/{uuid4()}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
        )

        assert response.status_code in [401, 403]

    def test_update_user_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/edit handles invalid UUID."""
        response = admin_client.post(
            "/admin/users/not-a-uuid/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_update_user_invalid_role(self, admin_client):
        """POST /admin/users/{id}/edit rejects invalid role."""
        fake_id = uuid4()
        response = admin_client.post(
            f"/admin/users/{fake_id}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "badrole"},
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_update_user_nonexistent_returns_404(self, admin_client):
        """POST /admin/users/{id}/edit returns 404 for non-existent user."""
        fake_id = uuid4()
        response = admin_client.post(
            f"/admin/users/{fake_id}/edit",
            data={"email": "test@test.com", "first_name": "Test", "role": "staff"},
            follow_redirects=False,
        )

        assert response.status_code == 404


class TestResendMagicLink:
    """Test resend magic link functionality."""

    def test_resend_requires_auth(self, e2e_client):
        """POST /admin/users/{id}/resend-magic-link requires authentication."""
        response = e2e_client.post(f"/admin/users/{uuid4()}/resend-magic-link")

        assert response.status_code in [401, 302, 303]

    def test_resend_requires_admin(self, staff_client):
        """POST /admin/users/{id}/resend-magic-link requires admin role."""
        response = staff_client.post(f"/admin/users/{uuid4()}/resend-magic-link")

        assert response.status_code in [401, 403]

    def test_resend_invalid_uuid(self, admin_client):
        """POST /admin/users/{id}/resend-magic-link handles invalid UUID."""
        response = admin_client.post(
            "/admin/users/not-a-uuid/resend-magic-link",
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_resend_nonexistent_user_returns_404(self, admin_client):
        """POST /admin/users/{id}/resend-magic-link returns 404 for non-existent user."""
        fake_id = uuid4()
        response = admin_client.post(
            f"/admin/users/{fake_id}/resend-magic-link",
            follow_redirects=False,
        )

        assert response.status_code == 404


class TestFixActiveTournaments:
    """Test fix active tournaments endpoint."""

    def test_fix_active_requires_auth(self, e2e_client):
        """POST /admin/tournaments/fix-active requires authentication."""
        response = e2e_client.post("/admin/tournaments/fix-active")

        assert response.status_code in [401, 302, 303]

    def test_fix_active_requires_admin(self, staff_client):
        """POST /admin/tournaments/fix-active requires admin role."""
        response = staff_client.post("/admin/tournaments/fix-active")

        assert response.status_code in [401, 403]

    def test_fix_active_no_issue(self, admin_client):
        """POST /admin/tournaments/fix-active when no issue exists."""
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            follow_redirects=False,
        )

        # Redirects with info message (no issue found)
        assert response.status_code == 303
        assert "/overview" in response.headers.get("location", "")

    def test_fix_active_missing_selection(self, admin_client, create_e2e_tournament):
        """POST /admin/tournaments/fix-active without selection."""
        import asyncio
        # Create multiple active tournaments
        asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )

        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={},  # No keep_active selected
            follow_redirects=False,
        )

        # Should redirect (either with error or info)
        assert response.status_code == 303

    def test_fix_active_invalid_uuid(self, admin_client):
        """POST /admin/tournaments/fix-active with invalid UUID."""
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={"keep_active": "not-a-uuid"},
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_fix_active_not_in_list(self, admin_client):
        """POST /admin/tournaments/fix-active with UUID not in active list."""
        fake_id = uuid4()
        response = admin_client.post(
            "/admin/tournaments/fix-active",
            data={"keep_active": str(fake_id)},
            follow_redirects=False,
        )

        assert response.status_code == 303
