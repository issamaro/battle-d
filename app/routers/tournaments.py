"""Tournament management routes."""
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
    get_performer_repo,
)
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository

router = APIRouter(prefix="/tournaments", tags=["tournaments"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_tournaments(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """List all tournaments (staff only).

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        HTML page with tournament list
    """
    user = require_staff(current_user)

    # Get all tournaments
    tournaments = await tournament_repo.get_all()

    return templates.TemplateResponse(
        request=request,
        name="tournaments/list.html",
        context={
            "current_user": user,
            "tournaments": tournaments,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_tournament_form(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Display create tournament form (staff only).

    Args:
        request: FastAPI request
        current_user: Current authenticated user

    Returns:
        HTML form for creating tournament
    """
    user = require_staff(current_user)

    return templates.TemplateResponse(
        request=request,
        name="tournaments/create.html",
        context={
            "current_user": user,
        },
    )


@router.post("/create")
async def create_tournament(
    name: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Create a new tournament (staff only).

    Args:
        name: Tournament name
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        Redirect to tournament detail page
    """
    user = require_staff(current_user)

    # Create tournament
    tournament = await tournament_repo.create_tournament(name=name)

    return RedirectResponse(
        url=f"/tournaments/{tournament.id}", status_code=303
    )


@router.get("/{tournament_id}", response_class=HTMLResponse)
async def tournament_detail(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
):
    """View tournament details with categories (staff only).

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository

    Returns:
        HTML page with tournament details
    """
    user = require_staff(current_user)

    # Parse UUID
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

    # Get categories
    categories = await category_repo.get_by_tournament(tournament_uuid)

    # Get performer counts for each category
    category_data = []
    for category in categories:
        performers = await category_repo.get_with_performers(category.id)
        category_data.append({
            "category": category,
            "performer_count": len(performers.performers) if performers else 0,
        })

    return templates.TemplateResponse(
        request=request,
        name="tournaments/detail.html",
        context={
            "current_user": user,
            "tournament": tournament,
            "category_data": category_data,
        },
    )


@router.get("/{tournament_id}/add-category", response_class=HTMLResponse)
async def add_category_form(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Display add category form (staff only).

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        HTML form for adding category
    """
    user = require_staff(current_user)

    # Parse UUID
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

    return templates.TemplateResponse(
        request=request,
        name="tournaments/add_category.html",
        context={
            "current_user": user,
            "tournament": tournament,
        },
    )


@router.post("/{tournament_id}/add-category")
async def add_category(
    tournament_id: str,
    name: str = Form(...),
    is_duo: bool = Form(False),
    groups_ideal: int = Form(2),
    performers_ideal: int = Form(4),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repo),
):
    """Add a category to a tournament (staff only).

    Args:
        tournament_id: Tournament UUID
        name: Category name
        is_duo: Whether this is a 2v2 category
        groups_ideal: Target number of pools
        performers_ideal: Target performers per pool
        current_user: Current authenticated user
        category_repo: Category repository

    Returns:
        Redirect to tournament detail page
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament ID",
        )

    # Create category
    await category_repo.create_category(
        tournament_id=tournament_uuid,
        name=name,
        is_duo=is_duo,
        groups_ideal=groups_ideal,
        performers_ideal=performers_ideal,
    )

    return RedirectResponse(
        url=f"/tournaments/{tournament_id}", status_code=303
    )
