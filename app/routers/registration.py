"""Dancer registration routes for tournaments."""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_staff,
    CurrentUser,
    get_tournament_repo,
    get_category_repo,
    get_dancer_repo,
    get_performer_repo,
)
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository

router = APIRouter(prefix="/registration", tags=["registration"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/{tournament_id}/{category_id}", response_class=HTMLResponse)
async def registration_page(
    tournament_id: str,
    category_id: str,
    search: Optional[str] = None,
    request: Request = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Dancer registration page for a tournament category (staff only).

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        search: Optional search query for dancers
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        dancer_repo: Dancer repository
        performer_repo: Performer repository

    Returns:
        HTML page with registration interface
    """
    user = require_staff(current_user)

    # Parse UUIDs
    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament or category ID",
        )

    # Get tournament
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Get category
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Get registered performers
    performers = await performer_repo.get_by_category(category_uuid)

    # Get dancer search results
    dancers = []
    if search:
        dancers = await dancer_repo.search(search, limit=50)

    return templates.TemplateResponse(
        request=request,
        name="registration/register.html",
        context={
            "current_user": user,
            "tournament": tournament,
            "category": category,
            "performers": performers,
            "dancers": dancers,
            "search": search or "",
        },
    )


@router.post("/{tournament_id}/{category_id}/register")
async def register_dancer(
    tournament_id: str,
    category_id: str,
    dancer_id: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Register a dancer in a tournament category (staff only).

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        dancer_id: Dancer UUID to register
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        dancer_repo: Dancer repository
        performer_repo: Performer repository

    Returns:
        Redirect back to registration page
    """
    user = require_staff(current_user)

    # Parse UUIDs
    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
        dancer_uuid = uuid.UUID(dancer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    # Verify tournament exists
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Verify category exists
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Verify dancer exists
    dancer = await dancer_repo.get_by_id(dancer_uuid)
    if not dancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dancer not found",
        )

    # Check if dancer is already registered in this tournament
    if await performer_repo.dancer_registered_in_tournament(
        dancer_uuid, tournament_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dancer {dancer.blaze} is already registered in this tournament (one category per tournament)",
        )

    # Register dancer as performer
    await performer_repo.create_performer(
        tournament_id=tournament_uuid,
        category_id=category_uuid,
        dancer_id=dancer_uuid,
    )

    return RedirectResponse(
        url=f"/registration/{tournament_id}/{category_id}",
        status_code=303,
    )


@router.post("/{tournament_id}/{category_id}/unregister/{performer_id}")
async def unregister_dancer(
    tournament_id: str,
    category_id: str,
    performer_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Unregister a dancer from a tournament category (staff only).

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        performer_id: Performer UUID to unregister
        current_user: Current authenticated user
        performer_repo: Performer repository

    Returns:
        Redirect back to registration page
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        performer_uuid = uuid.UUID(performer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid performer ID",
        )

    # Delete performer
    deleted = await performer_repo.delete(performer_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performer not found",
        )

    return RedirectResponse(
        url=f"/registration/{tournament_id}/{category_id}",
        status_code=303,
    )
