"""Event mode routes for command center interface."""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_mc,
    CurrentUser,
    get_flash_messages_dependency,
    get_event_service,
    get_tournament_repo,
)
from app.services.event_service import EventService
from app.repositories.tournament import TournamentRepository
from app.models.tournament import TournamentPhase

router = APIRouter(prefix="/event", tags=["event"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/{tournament_id}", response_class=HTMLResponse)
async def command_center(
    tournament_id: str,
    request: Request,
    category_id: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """Command center for event mode.

    Full-screen interface with:
    - Current battle card
    - Battle queue
    - Phase progress
    - Category filtering

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        category_id: Optional category filter
        current_user: Current authenticated user
        event_service: Event service for data aggregation
        tournament_repo: Tournament repository
        flash_messages: Flash messages from session

    Returns:
        HTML command center page
    """
    user = require_mc(current_user)

    # Parse tournament UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament ID",
        )

    # Parse category UUID if provided
    category_uuid = None
    if category_id:
        try:
            category_uuid = uuid.UUID(category_id)
        except ValueError:
            pass  # Ignore invalid category, show all

    # Get tournament
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Check if tournament is in event phase
    event_phases = [
        TournamentPhase.PRESELECTION,
        TournamentPhase.POOLS,
        TournamentPhase.FINALS,
    ]
    if tournament.phase not in event_phases:
        # Redirect to dashboard with message
        return RedirectResponse(url="/overview", status_code=303)

    # Get command center context
    context = await event_service.get_command_center_context(
        tournament_uuid, category_uuid
    )

    # Get phase progress for progress bar
    progress = await event_service.get_phase_progress(tournament_uuid)

    # Get battle queue
    queue = await event_service.get_battle_queue(tournament_uuid, category_uuid)

    # Get active tournament for template (same as current)
    active_tournament = tournament

    return templates.TemplateResponse(
        request=request,
        name="event/command_center.html",
        context={
            "current_user": user,
            "context": context,
            "tournament": tournament,
            "active_tournament": active_tournament,
            "category_filter": category_uuid,
            "flash_messages": flash_messages,
            "progress": progress,
            "queue": queue,
        },
    )


@router.get("/{tournament_id}/current-battle", response_class=HTMLResponse)
async def current_battle_partial(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    """HTMX partial: Current battle card.

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        event_service: Event service

    Returns:
        HTML partial with current battle info
    """
    user = require_mc(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        return HTMLResponse("<p>Invalid tournament ID</p>")

    context = await event_service.get_command_center_context(tournament_uuid)

    return templates.TemplateResponse(
        request=request,
        name="event/_current_battle.html",
        context={
            "current_user": user,
            "context": context,
            "tournament": context.tournament,
        },
    )


@router.get("/{tournament_id}/queue", response_class=HTMLResponse)
async def queue_partial(
    tournament_id: str,
    request: Request,
    category_id: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    """HTMX partial: Battle queue with optional category filter.

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        category_id: Optional category filter
        current_user: Current authenticated user
        event_service: Event service

    Returns:
        HTML partial with battle queue
    """
    user = require_mc(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        return HTMLResponse("<p>Invalid tournament ID</p>")

    category_uuid = None
    if category_id:
        try:
            category_uuid = uuid.UUID(category_id)
        except ValueError:
            pass

    queue = await event_service.get_battle_queue(tournament_uuid, category_uuid)

    return templates.TemplateResponse(
        request=request,
        name="event/_battle_queue.html",
        context={
            "current_user": user,
            "queue": queue,
            "tournament_id": tournament_id,
        },
    )


@router.get("/{tournament_id}/progress", response_class=HTMLResponse)
async def progress_partial(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    """HTMX partial: Phase progress.

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        event_service: Event service

    Returns:
        HTML partial with progress bar
    """
    user = require_mc(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        return HTMLResponse("<p>Invalid tournament ID</p>")

    progress = await event_service.get_phase_progress(tournament_uuid)

    return templates.TemplateResponse(
        request=request,
        name="event/_phase_progress.html",
        context={
            "current_user": user,
            "progress": progress,
        },
    )
