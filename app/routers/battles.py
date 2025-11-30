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
        add_flash_message(request, "Battle not found", "error")
        return RedirectResponse(
            url="/battles",
            status_code=status.HTTP_303_SEE_OTHER
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

    battle.status = BattleStatus.ACTIVE
    await battle_repo.update(battle)

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
    battle_repo: BattleRepository = Depends(get_battle_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Encode battle results.

    Args:
        request: FastAPI request
        battle_id: Battle UUID
        current_user: Current authenticated user
        battle_repo: Battle repository
        performer_repo: Performer repository

    Returns:
        Redirect to battle detail
    """
    user = require_staff(current_user)

    battle = await battle_repo.get_by_id(battle_id)
    if not battle:
        add_flash_message(request, "Battle not found", "error")
        return RedirectResponse(
            url="/battles",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Parse form data
    form_data = await request.form()

    # Handle different outcome types
    if battle.phase == BattlePhase.PRESELECTION:
        # Scored outcome: {performer_id: score}
        scores = {}
        for performer in battle.performers:
            score_key = f"score_{performer.id}"
            if score_key in form_data:
                score = float(form_data[score_key])
                scores[str(performer.id)] = score
                # Update performer's preselection score
                performer.preselection_score = Decimal(str(score))
                await performer_repo.update(performer)

        battle.outcome = scores
        battle.status = BattleStatus.COMPLETED

    elif battle.phase == BattlePhase.POOLS:
        # Win/draw/loss outcome
        winner_id = form_data.get("winner_id")
        is_draw = form_data.get("is_draw") == "true"

        if is_draw:
            battle.outcome = {"winner_id": None, "is_draw": True}
            # Update performer pool draws
            for performer in battle.performers:
                performer.pool_draws = (performer.pool_draws or 0) + 1
                await performer_repo.update(performer)
        elif winner_id:
            winner_uuid = uuid.UUID(winner_id)
            battle.outcome = {"winner_id": str(winner_uuid), "is_draw": False}
            battle.winner_id = winner_uuid

            # Update performer pool stats
            for performer in battle.performers:
                if performer.id == winner_uuid:
                    performer.pool_wins = (performer.pool_wins or 0) + 1
                else:
                    performer.pool_losses = (performer.pool_losses or 0) + 1
                await performer_repo.update(performer)
        else:
            add_flash_message(request, "Must specify winner or mark as draw", "error")
            return RedirectResponse(
                url=f"/battles/{battle_id}/encode",
                status_code=status.HTTP_303_SEE_OTHER
            )

        battle.status = BattleStatus.COMPLETED

    elif battle.phase == BattlePhase.TIEBREAK:
        # Tiebreak outcome
        winner_id = form_data.get("winner_id")
        if not winner_id:
            add_flash_message(request, "Must specify tiebreak winner", "error")
            return RedirectResponse(
                url=f"/battles/{battle_id}/encode",
                status_code=status.HTTP_303_SEE_OTHER
            )

        winner_uuid = uuid.UUID(winner_id)
        battle.outcome = {"winners": [str(winner_uuid)]}
        battle.winner_id = winner_uuid
        battle.status = BattleStatus.COMPLETED

    else:  # FINALS
        winner_id = form_data.get("winner_id")
        if not winner_id:
            add_flash_message(request, "Must specify winner", "error")
            return RedirectResponse(
                url=f"/battles/{battle_id}/encode",
                status_code=status.HTTP_303_SEE_OTHER
            )

        winner_uuid = uuid.UUID(winner_id)
        battle.outcome = {"winner_id": str(winner_uuid)}
        battle.winner_id = winner_uuid
        battle.status = BattleStatus.COMPLETED

    await battle_repo.update(battle)

    add_flash_message(request, "Battle results encoded successfully", "success")
    return RedirectResponse(
        url=f"/battles/{battle_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )
