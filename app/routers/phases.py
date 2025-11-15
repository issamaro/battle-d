"""Tournament phases routes - hardcoded navigation for POC."""
from enum import Enum
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, require_auth, CurrentUser

router = APIRouter(prefix="/phases", tags=["phases"])
templates = Jinja2Templates(directory="app/templates")


class TournamentPhase(str, Enum):
    """Tournament phases - hardcoded and sequential."""
    REGISTRATION = "registration"
    PRESELECTION = "preselection"
    POOLS = "pools"
    FINALS = "finals"
    COMPLETED = "completed"


# POC: In-memory phase state (Phase 1 will use database)
CURRENT_PHASE = TournamentPhase.REGISTRATION


def get_next_phase(current: TournamentPhase) -> Optional[TournamentPhase]:
    """Get the next phase in sequence.

    Args:
        current: Current phase

    Returns:
        Next phase or None if already completed
    """
    phases = list(TournamentPhase)
    try:
        current_index = phases.index(current)
        if current_index < len(phases) - 1:
            return phases[current_index + 1]
    except ValueError:
        pass
    return None


def get_previous_phase(current: TournamentPhase) -> Optional[TournamentPhase]:
    """Get the previous phase in sequence.

    Args:
        current: Current phase

    Returns:
        Previous phase or None if at registration
    """
    phases = list(TournamentPhase)
    try:
        current_index = phases.index(current)
        if current_index > 0:
            return phases[current_index - 1]
    except ValueError:
        pass
    return None


@router.get("/", response_class=HTMLResponse)
async def phases_overview(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Display tournament phases overview.

    Shows current phase and navigation to advance/go back.
    """
    user = require_auth(current_user)

    next_phase = get_next_phase(CURRENT_PHASE)
    prev_phase = get_previous_phase(CURRENT_PHASE)

    return templates.TemplateResponse(
        request=request,
        name="phases/overview.html",
        context={
            "current_user": user,
            "current_phase": CURRENT_PHASE,
            "next_phase": next_phase,
            "prev_phase": prev_phase,
            "can_advance": next_phase is not None,
            "can_go_back": prev_phase is not None,
        },
    )


@router.post("/advance")
async def advance_phase(current_user: Optional[CurrentUser] = Depends(get_current_user)):
    """Advance to next tournament phase.

    Only admins can advance phases.
    """
    global CURRENT_PHASE
    from app.dependencies import require_admin

    require_admin(current_user)

    next_phase = get_next_phase(CURRENT_PHASE)
    if next_phase:
        CURRENT_PHASE = next_phase
        return {"message": f"Advanced to {CURRENT_PHASE.value}", "phase": CURRENT_PHASE.value}

    return {"message": "Tournament is already completed", "phase": CURRENT_PHASE.value}


@router.post("/go-back")
async def go_back_phase(current_user: Optional[CurrentUser] = Depends(get_current_user)):
    """Go back to previous tournament phase.

    Only admins can change phases.
    """
    global CURRENT_PHASE
    from app.dependencies import require_admin

    require_admin(current_user)

    prev_phase = get_previous_phase(CURRENT_PHASE)
    if prev_phase:
        CURRENT_PHASE = prev_phase
        return {"message": f"Went back to {CURRENT_PHASE.value}", "phase": CURRENT_PHASE.value}

    return {"message": "Already at registration phase", "phase": CURRENT_PHASE.value}


@router.get("/current")
async def get_current_phase(
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Get current tournament phase.

    Available to all authenticated users.
    """
    require_auth(current_user)
    return {"phase": CURRENT_PHASE.value}
