"""Authentication routes for magic link login."""
from fastapi import APIRouter, Form, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import magic_link_auth
from app.email_service import email_service
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# In-memory user store for POC (Phase 1 will use database)
# Format: {email: {"first_name": str, "role": str}}
USERS_STORE = {
    "admin@battle-d.com": {"first_name": "Admin", "role": "admin"},
    "staff@battle-d.com": {"first_name": "Staff", "role": "staff"},
    "mc@battle-d.com": {"first_name": "MC", "role": "mc"},
}


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    return templates.TemplateResponse(request=request, name="auth/login.html")


@router.post("/send-magic-link")
async def send_magic_link(email: str = Form(...)):
    """Send magic link to user's email.

    Args:
        email: User email address

    Returns:
        Success message
    """
    # Check if user exists
    user = USERS_STORE.get(email.lower())
    if not user:
        # Don't reveal if user exists or not (security best practice)
        return {
            "message": "If an account exists with this email, you will receive a login link."
        }

    # Generate magic link
    magic_link = magic_link_auth.generate_magic_link(email.lower(), user["role"])

    # Send email
    await email_service.send_magic_link(email.lower(), magic_link, user["first_name"])

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
