"""Dashboard routes for smart context-aware dashboard."""
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_auth,
    CurrentUser,
    get_flash_messages_dependency,
    get_dashboard_service,
    get_tournament_repo,
)
from app.services.dashboard_service import DashboardService
from app.repositories.tournament import TournamentRepository

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root():
    """Root route redirects to dashboard."""
    return RedirectResponse(url="/overview")


@router.get("/overview", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """Smart dashboard with 3 states.

    States:
    1. No tournament: Show create CTA
    2. Registration phase: Show category registration status
    3. Event phases: Show "Go to Event Mode" CTA

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        dashboard_service: Dashboard service for context aggregation
        tournament_repo: Tournament repository for active tournament check
        flash_messages: Flash messages from session

    Returns:
        HTML dashboard page with context-appropriate content
    """
    user = require_auth(current_user)

    # Check for data integrity: multiple ACTIVE tournaments
    active_tournaments = await tournament_repo.get_active_tournaments()
    if len(active_tournaments) > 1:
        # Multiple ACTIVE tournaments - show fix UI for admins
        if user.is_admin:
            return templates.TemplateResponse(
                request=request,
                name="admin/fix_active_tournaments.html",
                context={
                    "current_user": user,
                    "active_tournaments": active_tournaments,
                },
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="errors/tournament_config_error.html",
                context={"current_user": user},
                status_code=500,
            )

    # Get dashboard context (handles 3 states)
    dashboard_context = await dashboard_service.get_dashboard_context()

    # Get active tournament for sidebar
    active_tournament = active_tournaments[0] if active_tournaments else None

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "current_user": user,
            "dashboard": dashboard_context,
            "active_tournament": active_tournament,
            "flash_messages": flash_messages,
        },
    )
