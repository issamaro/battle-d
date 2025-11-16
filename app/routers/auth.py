"""Authentication routes for magic link login."""
import logging
from fastapi import APIRouter, Form, Request, Response, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import magic_link_auth
from app.config import settings
from app.services.email.service import EmailService
from app.dependencies import get_email_service, get_user_repo
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    return templates.TemplateResponse(request=request, name="auth/login.html")


@router.post("/send-magic-link")
async def send_magic_link(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    email_service: EmailService = Depends(get_email_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Send magic link to user's email.

    Args:
        background_tasks: FastAPI background tasks for async email sending
        email: User email address
        email_service: Injected email service dependency
        user_repo: Injected user repository dependency

    Returns:
        Success message (returns immediately, email sends in background)
    """
    logger.info(f"Magic link request for email: {email}")

    # Check if user exists in database
    user = await user_repo.get_by_email(email.lower())
    if not user:
        logger.warning(f"Magic link requested for non-existent user: {email}")
        # Don't reveal if user exists or not (security best practice)
        return {
            "message": "If an account exists with this email, you will receive a login link."
        }

    # Generate magic link
    magic_link = magic_link_auth.generate_magic_link(email.lower(), user.role.value)
    logger.info(f"Generated magic link for user: {email}")

    # Send email in background (non-blocking)
    background_tasks.add_task(
        email_service.send_magic_link,
        email.lower(),
        magic_link,
        user.first_name
    )
    logger.info(f"Queued background task to send magic link to {email}")

    return {
        "message": "If an account exists with this email, you will receive a login link."
    }


@router.get("/verify")
async def verify_magic_link(token: str, response: Response):
    """Verify magic link token and create session.

    Args:
        token: Magic link token from URL
        response: FastAPI response object

    Returns:
        Redirect to dashboard
    """
    # Verify token
    payload = magic_link_auth.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link",
        )

    # Create session token (same as magic link but with longer expiry)
    session_token = magic_link_auth.serializer.dumps(
        {"email": payload["email"], "role": payload["role"]}, salt="magic-link"
    )

    # Set session cookie
    redirect_response = RedirectResponse(url="/dashboard", status_code=303)
    redirect_response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )

    return redirect_response


@router.get("/logout")
async def logout():
    """Logout user by clearing session cookie."""
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return response
