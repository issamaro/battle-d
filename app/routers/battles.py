"""Battle management routes.

See: ROADMAP.md §2 Phase 2 - Battle Management
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from decimal import Decimal

from app.dependencies import (
    get_current_user,
    require_staff,
    CurrentUser,
    get_battle_repo,
    get_category_repo,
    get_performer_repo,
    get_flash_messages_dependency,
    get_battle_results_encoding_service,
)
from app.utils.flash import add_flash_message
from app.repositories.battle import BattleRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.models.battle import BattleStatus, BattlePhase, BattleOutcomeType
from app.exceptions import ValidationError

router = APIRouter(prefix="/battles", tags=["battles"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_battles(
    request: Request,
    category_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """List battles for a category.

    Args:
        request: FastAPI request
        category_id: Category UUID to filter battles
        status_filter: Optional status filter (PENDING, ACTIVE, COMPLETED)
        current_user: Current authenticated user
        battle_repo: Battle repository
        category_repo: Category repository

    Returns:
        HTML page with battle list
    """
    user = require_staff(current_user)

    category = None
    if category_id:
        category = await category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Get battles
    if category_id:
        battles = await battle_repo.get_by_category(category_id)
    else:
        battles = []

    # Apply status filter
    if status_filter and status_filter.upper() in [s.value.upper() for s in BattleStatus]:
        battles = [b for b in battles if b.status.value.upper() == status_filter.upper()]

    return templates.TemplateResponse(
        request=request,
        name="battles/list.html",
        context={
            "current_user": user,
            "battles": battles,
            "category": category,
            "status_filter": status_filter,
            "flash_messages": flash_messages,
        },
    )


@router.get("/{battle_id}", response_class=HTMLResponse)
async def battle_detail(
    request: Request,
    battle_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """View battle details.

    Args:
        request: FastAPI request
        battle_id: Battle UUID
        current_user: Current authenticated user
        battle_repo: Battle repository

    Returns:
        HTML page with battle details
    """
    user = require_staff(current_user)

    battle = await battle_repo.get_by_id(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="battles/detail.html",
        context={
            "current_user": user,
            "battle": battle,
            "flash_messages": flash_messages,
        },
    )


@router.post("/{battle_id}/start")
async def start_battle(
    request: Request,
    battle_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
):
    """Start a battle (change status to ACTIVE).

    Args:
        battle_id: Battle UUID
        current_user: Current authenticated user
        battle_repo: Battle repository

    Returns:
        Redirect to battle detail
    """
    user = require_staff(current_user)

    battle = await battle_repo.get_by_id(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    if battle.status != BattleStatus.PENDING:
        add_flash_message(
            request,
            f"Cannot start battle with status {battle.status.value}",
            "error"
        )
        return RedirectResponse(
            url=f"/battles/{battle_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    await battle_repo.update(battle.id, status=BattleStatus.ACTIVE)

    add_flash_message(request, "Battle started successfully", "success")
    return RedirectResponse(
        url=f"/battles/{battle_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/{battle_id}/encode", response_class=HTMLResponse)
async def encode_battle_form(
    request: Request,
    battle_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """Display battle encoding form.

    Args:
        request: FastAPI request
        battle_id: Battle UUID
        current_user: Current authenticated user
        battle_repo: Battle repository

    Returns:
        HTML form for encoding battle results
    """
    user = require_staff(current_user)

    battle = await battle_repo.get_by_id(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    # Select appropriate template based on phase
    if battle.phase == BattlePhase.PRESELECTION:
        template_name = "battles/encode_preselection.html"
    elif battle.phase == BattlePhase.POOLS:
        template_name = "battles/encode_pool.html"
    elif battle.phase == BattlePhase.TIEBREAK:
        template_name = "battles/encode_tiebreak.html"
    else:
        template_name = "battles/encode_pool.html"  # Default for finals

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "current_user": user,
            "battle": battle,
            "flash_messages": flash_messages,
        },
    )


@router.post("/{battle_id}/encode")
async def encode_battle(
    request: Request,
    battle_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    encoding_service=Depends(get_battle_results_encoding_service),
    battle_repo: BattleRepository = Depends(get_battle_repo),
):
    """Encode battle results.

    Delegates to BattleResultsEncodingService for validation and atomic updates.

    Args:
        request: FastAPI request
        battle_id: Battle UUID
        current_user: Current authenticated user
        encoding_service: Battle encoding service
        battle_repo: Battle repository

    Returns:
        Redirect to battle detail or encode form on validation failure
    """
    user = require_staff(current_user)

    # Get battle to determine phase
    battle = await battle_repo.get_with_performers(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    # Parse form data based on phase
    form_data = await request.form()
    result = None

    try:
        if battle.phase == BattlePhase.PRESELECTION:
            # Parse scores from form
            scores = {
                performer.id: Decimal(str(form_data[f"score_{performer.id}"]))
                for performer in battle.performers
                if f"score_{performer.id}" in form_data
            }
            result = await encoding_service.encode_preselection_battle(battle_id, scores)

        elif battle.phase == BattlePhase.POOLS:
            # Parse winner or draw
            winner_id = uuid.UUID(form_data["winner_id"]) if form_data.get("winner_id") else None
            is_draw = form_data.get("is_draw") == "true"
            result = await encoding_service.encode_pool_battle(battle_id, winner_id, is_draw)

        elif battle.phase == BattlePhase.TIEBREAK:
            # Parse winner
            winner_id_str = form_data.get("winner_id")
            if not winner_id_str:
                add_flash_message(request, "Must specify tiebreak winner", "error")
                return RedirectResponse(
                    url=f"/battles/{battle_id}/encode",
                    status_code=status.HTTP_303_SEE_OTHER
                )
            winner_id = uuid.UUID(winner_id_str)
            result = await encoding_service.encode_tiebreak_battle(battle_id, winner_id)

        else:  # FINALS
            # Parse winner
            winner_id_str = form_data.get("winner_id")
            if not winner_id_str:
                add_flash_message(request, "Must specify winner", "error")
                return RedirectResponse(
                    url=f"/battles/{battle_id}/encode",
                    status_code=status.HTTP_303_SEE_OTHER
                )
            winner_id = uuid.UUID(winner_id_str)
            result = await encoding_service.encode_finals_battle(battle_id, winner_id)

    except (ValueError, KeyError) as e:
        # Handle form data parsing errors
        add_flash_message(request, f"Invalid form data: {str(e)}", "error")
        return RedirectResponse(
            url=f"/battles/{battle_id}/encode",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Handle validation result
    if not result:
        # Validation failed - show errors
        for error in result.errors:
            add_flash_message(request, error, "error")
        return RedirectResponse(
            url=f"/battles/{battle_id}/encode",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Success
    add_flash_message(request, "Battle results encoded successfully", "success")
    return RedirectResponse(
        url=f"/battles/{battle_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/queue/{category_id}", response_class=HTMLResponse)
async def get_battle_queue(
    request: Request,
    category_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """Get battle queue for a category (partial for HTMX).

    Business Rule BR-SCHED-001: Returns battles ordered by sequence_order.

    Args:
        request: FastAPI request
        category_id: Category UUID
        current_user: Current authenticated user
        battle_repo: Battle repository
        category_repo: Category repository

    Returns:
        HTML partial with battle queue
    """
    user = require_staff(current_user)

    category = await category_repo.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Get pending battles ordered
    pending_battles = await battle_repo.get_pending_battles_ordered(category_id)

    # Get active battle if any
    active_battles = await battle_repo.get_by_category_and_status(
        category_id, BattleStatus.ACTIVE
    )
    active_battle = active_battles[0] if active_battles else None

    return templates.TemplateResponse(
        request=request,
        name="battles/_battle_queue.html",
        context={
            "current_user": user,
            "category": category,
            "pending_battles": pending_battles,
            "active_battle": active_battle,
            "flash_messages": flash_messages,
        },
    )


@router.post("/{battle_id}/reorder")
async def reorder_battle(
    request: Request,
    battle_id: uuid.UUID,
    new_position: int = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_repo: BattleRepository = Depends(get_battle_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
):
    """Reorder a battle in the queue.

    Business Rule BR-SCHED-002: Only battles 2+ positions after ACTIVE can be moved.

    Args:
        request: FastAPI request
        battle_id: Battle UUID to move
        new_position: Target position (1-indexed)
        current_user: Current authenticated user
        battle_repo: Battle repository
        performer_repo: Performer repository
        category_repo: Category repository

    Returns:
        Redirect to battle queue or HTML partial for HTMX
    """
    user = require_staff(current_user)

    # Import battle service here to avoid circular imports
    from app.services.battle_service import BattleService

    battle = await battle_repo.get_by_id(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    battle_service = BattleService(battle_repo, performer_repo)

    try:
        await battle_service.reorder_battle(battle_id, new_position)
        add_flash_message(request, "Battle reordered successfully", "success")
    except ValidationError as e:
        for error in e.errors:
            add_flash_message(request, error, "error")

    # Check if HTMX request
    if request.headers.get("HX-Request"):
        # Return partial HTML for HTMX
        category = await category_repo.get_by_id(battle.category_id)
        pending_battles = await battle_repo.get_pending_battles_ordered(battle.category_id)
        active_battles = await battle_repo.get_by_category_and_status(
            battle.category_id, BattleStatus.ACTIVE
        )
        active_battle = active_battles[0] if active_battles else None

        return templates.TemplateResponse(
            request=request,
            name="battles/_battle_queue.html",
            context={
                "current_user": user,
                "category": category,
                "pending_battles": pending_battles,
                "active_battle": active_battle,
                "flash_messages": [],
            },
        )

    return RedirectResponse(
        url=f"/battles?category_id={battle.category_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )
