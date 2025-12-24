"""Tournament management routes."""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_staff,
    require_admin,
    CurrentUser,
    get_tournament_repo,
    get_category_repo,
    get_performer_repo,
    get_flash_messages_dependency,
    get_tournament_service,
)
from app.exceptions import ValidationError
from app.models.tournament import TournamentStatus
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.services.tournament_service import TournamentService
from app.utils.flash import add_flash_message

router = APIRouter(prefix="/tournaments", tags=["tournaments"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_tournaments(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """List all tournaments (staff only).

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        flash_messages: Flash messages from session

    Returns:
        HTML page with tournament list
    """
    user = require_staff(current_user)

    # Get all tournaments
    tournaments = await tournament_repo.get_all()

    # Check for data integrity issue: multiple ACTIVE tournaments
    active_tournaments = await tournament_repo.get_active_tournaments()
    has_integrity_issue = len(active_tournaments) > 1

    return templates.TemplateResponse(
        request=request,
        name="tournaments/list.html",
        context={
            "current_user": user,
            "tournaments": tournaments,
            "flash_messages": flash_messages,
            "has_integrity_issue": has_integrity_issue,
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
    request: Request,
    name: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Create a new tournament (staff only).

    Business Rules (BR-UX-007):
    - Uses HTMX + HX-Redirect pattern for modal submission
    - Returns HX-Redirect to tournament detail on success
    - Returns form partial with errors on validation failure

    Args:
        request: FastAPI request
        name: Tournament name
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        HX-Redirect to tournament detail on success
    """
    user = require_staff(current_user)
    is_htmx = request.headers.get("HX-Request") == "true"

    # Validate name
    if not name or not name.strip():
        # Return form partial with error for HTMX swap
        if is_htmx:
            return templates.TemplateResponse(
                request=request,
                name="components/tournament_create_form_partial.html",
                context={
                    "error": "Tournament name is required",
                    "name": name,
                },
                status_code=400,
            )
        add_flash_message(request, "Tournament name is required", "error")
        return RedirectResponse(url="/tournaments/create", status_code=303)

    # Create tournament
    tournament = await tournament_repo.create_tournament(name=name.strip())
    add_flash_message(request, f"Tournament '{name}' created successfully", "success")

    # Check if HTMX request
    if is_htmx:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = f"/tournaments/{tournament.id}"
        return response

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
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """View tournament details with categories (staff only).

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        flash_messages: Flash messages from session

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
            "flash_messages": flash_messages,
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
    request: Request,
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
        request: FastAPI request
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
        add_flash_message(request, "Invalid tournament ID", "error")
        return RedirectResponse(url="/tournaments", status_code=303)

    # Create category
    await category_repo.create_category(
        tournament_id=tournament_uuid,
        name=name,
        is_duo=is_duo,
        groups_ideal=groups_ideal,
        performers_ideal=performers_ideal,
    )
    add_flash_message(request, f"Category '{name}' added successfully", "success")

    return RedirectResponse(
        url=f"/tournaments/{tournament_id}", status_code=303
    )


@router.delete("/{tournament_id}/categories/{category_id}")
async def delete_category(
    tournament_id: str,
    category_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
):
    """Remove a category from tournament (staff only).

    Business Rules (BR-UX-003):
    - Only allowed during REGISTRATION phase
    - CASCADE deletes Performers (keeps Dancer profiles)
    - Uses HTMX in-place row removal

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository

    Returns:
        Empty response with 200 (HTMX will remove row)
    """
    user = require_staff(current_user)

    # Parse UUIDs
    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    # Get tournament and verify phase
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    if tournament.phase.value != "registration":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categories can only be removed during REGISTRATION phase",
        )

    # Delete category using ORM cascade (BR-FIX-002)
    # Uses session.delete() to trigger ORM cascade, properly deleting performers
    deleted = await category_repo.delete_with_cascade(category_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    add_flash_message(request, "Category removed successfully", "success")

    # Return empty response for HTMX swap="delete"
    return HTMLResponse(content="", status_code=200)


@router.post("/{tournament_id}/rename")
async def rename_tournament(
    tournament_id: str,
    request: Request,
    name: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Rename a tournament (staff only).

    Business Rules (BR-UX-001):
    - Rename is ALWAYS allowed (any status: CREATED, ACTIVE, COMPLETED)
    - Uses HTMX + HX-Redirect pattern

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        name: New tournament name
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        HX-Redirect to tournaments list on success
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

    # Update tournament name
    updated = await tournament_repo.update(tournament_uuid, name=name)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    add_flash_message(request, f"Tournament renamed to '{name}'", "success")

    # Check if HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = "/tournaments"
        return response

    return RedirectResponse(url="/tournaments", status_code=303)


@router.post("/{tournament_id}/advance")
async def advance_phase(
    tournament_id: str,
    request: Request,
    confirmed: bool = Form(False),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Advance tournament to next phase (admin only).

    Business Rules (BR-UX-006):
    - Admin-only access
    - Requires confirmation
    - Redirects to Event Mode on success

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        confirmed: Whether user confirmed advancement
        current_user: Current authenticated user
        tournament_service: Tournament service for phase operations
        tournament_repo: Tournament repository

    Returns:
        Redirect to event mode on success, or back to tournament on error
    """
    user = require_admin(current_user)

    # Parse UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament ID",
        )

    is_htmx = request.headers.get("HX-Request") == "true"

    # If not confirmed, return error
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required",
        )

    # Advance phase
    try:
        tournament = await tournament_service.advance_tournament_phase(tournament_uuid)
        add_flash_message(
            request,
            f"Tournament advanced to {tournament.phase.value.upper()} phase",
            "success"
        )

        # Redirect to event mode
        if is_htmx:
            response = HTMLResponse(content="", status_code=200)
            response.headers["HX-Redirect"] = f"/event/{tournament_id}"
            return response

        return RedirectResponse(url=f"/event/{tournament_id}", status_code=303)

    except ValidationError as e:
        error_msg = e.errors[0] if e.errors else "Cannot advance phase"
        add_flash_message(request, error_msg, "error")
        return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=303)


@router.post("/{tournament_id}/delete")
async def delete_tournament(
    tournament_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Delete a tournament (staff only, CREATED status only).

    Business Rules (BR-DEL-001):
    - Only CREATED status tournaments can be deleted
    - CASCADE deletes Categories and Performers
    - Dancer profiles are preserved

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        Redirect to /tournaments with success message
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        add_flash_message(request, "Invalid tournament ID", "error")
        return RedirectResponse(url="/tournaments", status_code=303)

    # Get tournament and validate status
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )

    # Validate CREATED status (BR-DEL-001)
    if tournament.status != TournamentStatus.CREATED:
        add_flash_message(
            request,
            f"Cannot delete tournament in {tournament.status.value.upper()} status. "
            "Only CREATED tournaments can be deleted.",
            "error"
        )
        return RedirectResponse(url="/tournaments", status_code=303)

    # Delete with cascade
    tournament_name = tournament.name  # Save for flash message
    deleted = await tournament_repo.delete_with_cascade(tournament_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )

    add_flash_message(request, f"Tournament '{tournament_name}' deleted successfully", "success")

    # Check if HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = "/tournaments"
        return response

    return RedirectResponse(url="/tournaments", status_code=303)
