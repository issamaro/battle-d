"""Tournament phases routes - database-driven phase navigation."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import (
    get_current_user,
    require_auth,
    require_admin,
    CurrentUser,
    get_tournament_service,
    get_flash_messages_dependency,
)
from app.exceptions import ValidationError
from app.models.tournament import TournamentPhase
from app.services.tournament_service import TournamentService
from app.utils.flash import add_flash_message

router = APIRouter(prefix="/tournaments", tags=["phases"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/{tournament_id}/phase", response_class=HTMLResponse)
async def tournament_phase_overview(
    tournament_id: UUID,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """Display tournament phase overview.

    Shows current phase and navigation to advance.
    Note: No going back - phases are forward-only.
    """
    user = require_auth(current_user)

    # Get tournament
    tournament = await tournament_service.tournament_repo.get_by_id(tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
        )

    # Get validation status
    validation_result = await tournament_service.get_phase_validation(tournament_id)

    next_phase = TournamentPhase.get_next_phase(tournament.phase)

    return templates.TemplateResponse(
        request=request,
        name="phases/overview.html",
        context={
            "current_user": user,
            "tournament": tournament,
            "current_phase": tournament.phase,
            "next_phase": next_phase,
            "can_advance": next_phase is not None,
            "validation_errors": validation_result.errors if not validation_result else [],
            "validation_warnings": validation_result.warnings if validation_result else [],
            "flash_messages": flash_messages,
        },
    )


@router.post("/{tournament_id}/advance")
async def advance_tournament_phase(
    tournament_id: UUID,
    confirmed: bool = Form(False),
    request: Request = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
):
    """Advance tournament to next phase with validation.

    Two-step process:
    1. First request: Validate and show confirmation dialog
    2. Second request (confirmed=True): Actually advance phase

    Only admins can advance phases.
    Phases are forward-only (no rollback).
    """
    require_admin(current_user)

    # Get tournament
    tournament = await tournament_service.tournament_repo.get_by_id(tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
        )

    # First request: Show validation and confirmation
    if not confirmed:
        try:
            # Validate phase transition
            validation_result = await tournament_service.get_phase_validation(
                tournament_id
            )

            if not validation_result:
                # Validation failed - show errors
                return templates.TemplateResponse(
                    request=request,
                    name="phases/validation_errors.html",
                    context={
                        "current_user": current_user,
                        "tournament": tournament,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Validation passed - show confirmation
            next_phase = TournamentPhase.get_next_phase(tournament.phase)
            return templates.TemplateResponse(
                request=request,
                name="phases/confirm_advance.html",
                context={
                    "current_user": current_user,
                    "tournament": tournament,
                    "from_phase": tournament.phase,
                    "to_phase": next_phase,
                    "warnings": validation_result.warnings,
                    "warning_message": _get_phase_warning_message(tournament.phase),
                },
            )

        except ValidationError as e:
            return templates.TemplateResponse(
                request=request,
                name="phases/validation_errors.html",
                context={
                    "current_user": current_user,
                    "tournament": tournament,
                    "errors": e.errors,
                    "warnings": e.warnings,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Second request: Confirmed - advance phase
    try:
        tournament = await tournament_service.advance_tournament_phase(tournament_id)
        next_phase = TournamentPhase.get_next_phase(tournament.phase)
        add_flash_message(
            request,
            f"Tournament advanced to {next_phase.value if next_phase else 'COMPLETED'} phase successfully",
            "success"
        )
        return RedirectResponse(
            url=f"/tournaments/{tournament_id}", status_code=status.HTTP_303_SEE_OTHER
        )
    except ValidationError as e:
        add_flash_message(
            request,
            f"Cannot advance phase: {', '.join(e.errors)}",
            "error"
        )
        return templates.TemplateResponse(
            request=request,
            name="phases/validation_errors.html",
            context={
                "current_user": current_user,
                "tournament": tournament,
                "errors": e.errors,
                "warnings": e.warnings,
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
