"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from fastapi import Cookie, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import magic_link_auth
from app.config import settings
from app.db.database import get_db
from app.utils.flash import get_flash_messages
from app.repositories import (
    UserRepository,
    DancerRepository,
    TournamentRepository,
    CategoryRepository,
    PerformerRepository,
    PoolRepository,
    BattleRepository,
)

# Email service instance (initialized at startup)
_email_service = None


def set_email_service(service):
    """Set the email service instance (called at app startup).

    Args:
        service: EmailService instance to use
    """
    global _email_service
    _email_service = service


def get_email_service():
    """Get the email service instance for dependency injection.

    Returns:
        EmailService: The configured email service

    Raises:
        RuntimeError: If email service not initialized
    """
    if _email_service is None:
        raise RuntimeError("Email service not initialized")
    return _email_service


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


def get_flash_messages_dependency(request: Request) -> list[dict[str, str]]:
    """Get flash messages from session for template injection.

    Args:
        request: FastAPI request object

    Returns:
        List of flash message dictionaries with 'message' and 'category' keys
    """
    return get_flash_messages(request)


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


# Repository dependencies
def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get UserRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(session)


def get_dancer_repo(session: AsyncSession = Depends(get_db)) -> DancerRepository:
    """Get DancerRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        DancerRepository instance
    """
    return DancerRepository(session)


def get_tournament_repo(session: AsyncSession = Depends(get_db)) -> TournamentRepository:
    """Get TournamentRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        TournamentRepository instance
    """
    return TournamentRepository(session)


def get_category_repo(session: AsyncSession = Depends(get_db)) -> CategoryRepository:
    """Get CategoryRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        CategoryRepository instance
    """
    return CategoryRepository(session)


def get_performer_repo(session: AsyncSession = Depends(get_db)) -> PerformerRepository:
    """Get PerformerRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        PerformerRepository instance
    """
    return PerformerRepository(session)


def get_pool_repo(session: AsyncSession = Depends(get_db)) -> PoolRepository:
    """Get PoolRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        PoolRepository instance
    """
    return PoolRepository(session)


def get_battle_repo(session: AsyncSession = Depends(get_db)) -> BattleRepository:
    """Get BattleRepository instance for dependency injection.

    Args:
        session: Database session

    Returns:
        BattleRepository instance
    """
    return BattleRepository(session)


# Service dependencies
def get_tournament_service(session: AsyncSession = Depends(get_db)):
    """Get TournamentService instance for dependency injection.

    Args:
        session: Database session

    Returns:
        TournamentService instance with all required repositories
    """
    from app.services.tournament_service import TournamentService
    from app.services.battle_service import BattleService
    from app.services.pool_service import PoolService

    # Create repositories
    tournament_repo = TournamentRepository(session)
    category_repo = CategoryRepository(session)
    performer_repo = PerformerRepository(session)
    battle_repo = BattleRepository(session)
    pool_repo = PoolRepository(session)

    # Create battle and pool services for phase transitions
    battle_service = BattleService(battle_repo, performer_repo)
    pool_service = PoolService(pool_repo, performer_repo)

    return TournamentService(
        tournament_repo=tournament_repo,
        category_repo=category_repo,
        performer_repo=performer_repo,
        battle_repo=battle_repo,
        pool_repo=pool_repo,
        battle_service=battle_service,
        pool_service=pool_service,
    )


def get_dancer_service(session: AsyncSession = Depends(get_db)):
    """Get DancerService instance for dependency injection.

    Args:
        session: Database session

    Returns:
        DancerService instance
    """
    from app.services.dancer_service import DancerService

    return DancerService(dancer_repo=DancerRepository(session))


def get_performer_service(session: AsyncSession = Depends(get_db)):
    """Get PerformerService instance for dependency injection.

    Args:
        session: Database session

    Returns:
        PerformerService instance with all required repositories
    """
    from app.services.performer_service import PerformerService

    return PerformerService(
        performer_repo=PerformerRepository(session),
        category_repo=CategoryRepository(session),
        dancer_repo=DancerRepository(session),
    )


def get_battle_encoding_service(session: AsyncSession = Depends(get_db)):
    """Get BattleEncodingService instance for dependency injection.

    Args:
        session: Database session

    Returns:
        BattleEncodingService instance with all required repositories
    """
    from app.services.battle_encoding_service import BattleEncodingService

    return BattleEncodingService(
        session=session,
        battle_repo=BattleRepository(session),
        performer_repo=PerformerRepository(session),
    )
