"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from fastapi import Cookie, HTTPException, status
from app.auth import magic_link_auth
from app.config import settings


class CurrentUser:
    """Represents the currently authenticated user."""

    def __init__(self, email: str, role: str):
        self.email = email
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("admin", "staff")

    @property
    def is_mc(self) -> bool:
        return self.role in ("admin", "staff", "mc")

    @property
    def is_judge(self) -> bool:
        return self.role == "judge"


def get_current_user(
    battle_d_session: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME)
) -> Optional[CurrentUser]:
    """Extract current user from session cookie.

    Args:
        battle_d_session: Session cookie value

    Returns:
        CurrentUser if authenticated, None otherwise
    """
    if not battle_d_session:
        return None

    # Verify session token (it's the same as magic link token, just long-lived)
    payload = magic_link_auth.verify_token(
        battle_d_session, max_age=settings.SESSION_MAX_AGE_SECONDS
    )

    if not payload:
        return None

    return CurrentUser(email=payload["email"], role=payload["role"])


def require_auth(
    current_user: Optional[CurrentUser] = None,
) -> CurrentUser:
    """Require authentication (any role).

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        CurrentUser if authenticated

    Raises:
        HTTPException 401 if not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


def require_admin(
    current_user: Optional[CurrentUser] = None,
) -> CurrentUser:
    """Require admin role.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        CurrentUser if admin

    Raises:
        HTTPException 401 if not authenticated, 403 if not admin
    """
    user = require_auth(current_user)
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_staff(
    current_user: Optional[CurrentUser] = None,
) -> CurrentUser:
    """Require staff role (admin or staff).

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        CurrentUser if staff or admin

    Raises:
        HTTPException 401 if not authenticated, 403 if not staff/admin
    """
    user = require_auth(current_user)
    if not user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return user


def require_mc(
    current_user: Optional[CurrentUser] = None,
) -> CurrentUser:
    """Require MC role (admin, staff, or mc).

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        CurrentUser if mc, staff, or admin

    Raises:
        HTTPException 401 if not authenticated, 403 if not authorized
    """
    user = require_auth(current_user)
    if not user.is_mc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MC access required",
        )
    return user


def require_judge(
    current_user: Optional[CurrentUser] = None,
) -> CurrentUser:
    """Require judge role.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        CurrentUser if judge

    Raises:
        HTTPException 401 if not authenticated, 403 if not judge
    """
    user = require_auth(current_user)
    if not user.is_judge:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Judge access required",
        )
    return user
