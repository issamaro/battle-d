"""Event mode routes for command center interface."""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_mc,
    require_admin,
    CurrentUser,
    get_flash_messages_dependency,
    get_event_service,
    get_tournament_repo,
    get_tournament_service,
)
from app.services.event_service import EventService
from app.services.tournament_service import TournamentService
from app.repositories.tournament import TournamentRepository
from app.models.tournament import TournamentPhase
from app.exceptions import ValidationError
from app.utils.flash import add_flash_message

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


@router.post("/{tournament_id}/advance", response_class=HTMLResponse)
async def advance_tournament_phase(
    tournament_id: str,
    request: Request,
    confirmed: bool = Form(False),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Advance tournament to next phase with validation.

    Two-step process:
    1. First request: Validate and show confirmation dialog
    2. Second request (confirmed=True): Actually advance phase

    Only admins can advance phases.
    Phases are forward-only (no rollback).

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        confirmed: Whether user confirmed the advancement
        current_user: Current authenticated user
        tournament_service: Tournament service for phase operations
        tournament_repo: Tournament repository

    Returns:
        HTML partial with confirmation dialog, validation errors, or redirect
    """
    user = require_admin(current_user)

    # Parse tournament UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament ID",
        )

    # Get tournament
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Check if HTMX request (for partial responses)
    is_htmx = request.headers.get("HX-Request") == "true"

    # First request: Show validation and confirmation
    if not confirmed:
        try:
            # Validate phase transition
            validation_result = await tournament_service.get_phase_validation(
                tournament_uuid
            )

            if not validation_result:
                # Validation failed - show errors
                template_name = "event/_validation_errors.html"
                return templates.TemplateResponse(
                    request=request,
                    name=template_name,
                    context={
                        "current_user": user,
                        "tournament": tournament,
                        "errors": validation_result.errors if validation_result else [],
                        "warnings": validation_result.warnings if validation_result else [],
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Validation passed - show confirmation
            next_phase = TournamentPhase.get_next_phase(tournament.phase)
            template_name = "event/_confirm_advance.html"
            return templates.TemplateResponse(
                request=request,
                name=template_name,
                context={
                    "current_user": user,
                    "tournament": tournament,
                    "from_phase": tournament.phase,
                    "to_phase": next_phase,
                    "warnings": validation_result.warnings,
                    "warning_message": _get_phase_warning_message(tournament.phase),
                },
            )

        except ValidationError as e:
            template_name = "event/_validation_errors.html"
            return templates.TemplateResponse(
                request=request,
                name=template_name,
                context={
                    "current_user": user,
                    "tournament": tournament,
                    "errors": e.errors,
                    "warnings": e.warnings if hasattr(e, 'warnings') else [],
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Second request: Confirmed - advance phase
    try:
        tournament = await tournament_service.advance_tournament_phase(tournament_uuid)
        next_phase = TournamentPhase.get_next_phase(tournament.phase)
        add_flash_message(
            request,
            f"Tournament advanced to {tournament.phase.value.upper()} phase successfully",
            "success"
        )

        # Redirect back to event mode
        if is_htmx:
            # For HTMX, set redirect header
            response = RedirectResponse(
                url=f"/event/{tournament_id}",
                status_code=status.HTTP_303_SEE_OTHER
            )
            response.headers["HX-Redirect"] = f"/event/{tournament_id}"
            return response
        else:
            return RedirectResponse(
                url=f"/event/{tournament_id}",
                status_code=status.HTTP_303_SEE_OTHER
            )

    except ValidationError as e:
        add_flash_message(
            request,
            f"Cannot advance phase: {', '.join(e.errors)}",
            "error"
        )
        template_name = "event/_validation_errors.html"
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context={
                "current_user": user,
                "tournament": tournament,
                "errors": e.errors,
                "warnings": e.warnings if hasattr(e, 'warnings') else [],
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def _get_phase_warning_message(current_phase: TournamentPhase) -> str:
    """Get appropriate warning message for phase advancement.

    Args:
        current_phase: Current tournament phase

    Returns:
        Warning message describing irreversibility
    """
    messages = {
        TournamentPhase.REGISTRATION: (
            "This will create preselection battles for all categories. "
            "This action is IRREVERSIBLE - you cannot go back to registration."
        ),
        TournamentPhase.PRESELECTION: (
            "This will finalize preselection results and create pools. "
            "This action is IRREVERSIBLE - you cannot modify preselection scores after this."
        ),
        TournamentPhase.POOLS: (
            "This will finalize pool results and create finals battles. "
            "This action is IRREVERSIBLE - you cannot modify pool results after this."
        ),
        TournamentPhase.FINALS: (
            "This will complete the tournament and archive all data. "
            "This action is IRREVERSIBLE - the tournament will be marked as completed."
        ),
    }
    return messages.get(
        current_phase,
        "This action is IRREVERSIBLE. Are you sure you want to proceed?",
    )
