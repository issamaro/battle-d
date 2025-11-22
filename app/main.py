"""Main FastAPI application - Battle-D Web App."""
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.routers import auth, phases, admin, dancers, tournaments, registration
from app.dependencies import (
    get_current_user,
    require_auth,
    CurrentUser,
    set_email_service,
    get_tournament_repo,
)
from app.repositories.tournament import TournamentRepository
from app.services.email.factory import create_email_provider
from app.services.email.service import EmailService
from app.logging_config import setup_logging

# Initialize logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (startup and shutdown)."""
    # Startup
    logger.info("Starting Battle-D application")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Base URL: {settings.BASE_URL}")

    provider = create_email_provider()
    email_service = EmailService(provider)
    set_email_service(email_service)
    logger.info(f"Email service initialized with {type(provider).__name__}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Battle-D application")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Templates
templates = Jinja2Templates(directory="app/templates")


# Include routers
app.include_router(auth.router)
app.include_router(phases.router)
app.include_router(admin.router)
app.include_router(dancers.router)
app.include_router(tournaments.router)
app.include_router(registration.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to login page."""
    return RedirectResponse(url="/auth/login")


@app.get("/overview", response_class=HTMLResponse)
async def overview(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Overview page - role-specific view with active tournament context."""
    user = require_auth(current_user)

    # Get active tournament for context
    active_tournament = await tournament_repo.get_active()

    return templates.TemplateResponse(
        request=request,
        name="overview.html",
        context={
            "current_user": user,
            "active_tournament": active_tournament,
        },
    )


# Legacy redirect: /dashboard -> /overview
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """Redirect old /dashboard route to /overview."""
    return RedirectResponse(url="/overview", status_code=301)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
