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
    get_flash_messages_dependency,
)
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository
from app.utils.flash import add_flash_message

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
    flash_messages: list = Depends(get_flash_messages_dependency),
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
        flash_messages: Flash messages from session

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

    # Get registered performers with duo partner relationships loaded
    performers = await performer_repo.get_by_category_with_partners(category_uuid)

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
            "flash_messages": flash_messages,
        },
    )


@router.post("/{tournament_id}/{category_id}/register")
async def register_dancer(
    request: Request,
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
        request: FastAPI request
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
        add_flash_message(request, "Invalid ID format", "error")
        return RedirectResponse(
            url=f"/registration/{tournament_id}/{category_id}",
            status_code=303,
        )

    # Verify tournament exists
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        add_flash_message(request, "Tournament not found", "error")
        return RedirectResponse(url="/tournaments", status_code=303)

    # Verify category exists
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        add_flash_message(request, "Category not found", "error")
        return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=303)

    # Verify dancer exists
    dancer = await dancer_repo.get_by_id(dancer_uuid)
    if not dancer:
        add_flash_message(request, "Dancer not found", "error")
        return RedirectResponse(
            url=f"/registration/{tournament_id}/{category_id}",
            status_code=303,
        )

    # Check if dancer is already registered in this tournament
    if await performer_repo.dancer_registered_in_tournament(
        dancer_uuid, tournament_uuid
    ):
        add_flash_message(
            request,
            f"Dancer '{dancer.blaze}' is already registered in this tournament",
            "error"
        )
        return RedirectResponse(
            url=f"/registration/{tournament_id}/{category_id}",
            status_code=303,
        )

    # Register dancer as performer
    await performer_repo.create_performer(
        tournament_id=tournament_uuid,
        category_id=category_uuid,
        dancer_id=dancer_uuid,
    )
    add_flash_message(request, f"Dancer '{dancer.blaze}' registered successfully", "success")

    return RedirectResponse(
        url=f"/registration/{tournament_id}/{category_id}",
        status_code=303,
    )


@router.get("/{tournament_id}/{category_id}/search-dancer", response_class=HTMLResponse)
async def search_dancer_api(
    tournament_id: str,
    category_id: str,
    request: Request,
    query: str = "",
    dancer_number: int = 1,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """HTMX endpoint for dancer search.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        request: FastAPI request
        query: Search query string
        dancer_number: Which dancer slot (1 or 2) for duo registration
        current_user: Current authenticated user
        category_repo: Category repository
        dancer_repo: Dancer repository

    Returns:
        HTML partial with search results
    """
    user = require_staff(current_user)

    # Parse UUIDs
    try:
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID",
        )

    # Get category to check if duo
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Search dancers
    dancers = []
    if query:
        dancers = await dancer_repo.search(query, limit=20)

    return templates.TemplateResponse(
        request=request,
        name="registration/_dancer_search.html",
        context={
            "dancers": dancers,
            "is_duo": category.is_duo,
            "dancer_number": dancer_number,
            "tournament_id": tournament_id,
            "category_id": category_id,
        },
    )


@router.post("/{tournament_id}/{category_id}/register-duo")
async def register_duo(
    tournament_id: str,
    category_id: str,
    dancer1_id: str = Form(...),
    dancer2_id: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Register a duo (two dancers) in a 2v2 tournament category (staff only).

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        dancer1_id: First dancer UUID
        dancer2_id: Second dancer UUID
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
        dancer1_uuid = uuid.UUID(dancer1_id)
        dancer2_uuid = uuid.UUID(dancer2_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    # Verify same dancer not selected twice
    if dancer1_uuid == dancer2_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register the same dancer twice in a duo",
        )

    # Verify tournament exists
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Verify category exists and is duo
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if not category.is_duo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This category is not a duo category",
        )

    # Verify both dancers exist
    dancer1 = await dancer_repo.get_by_id(dancer1_uuid)
    dancer2 = await dancer_repo.get_by_id(dancer2_uuid)
    if not dancer1 or not dancer2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both dancers not found",
        )

    # Check if either dancer is already registered in this tournament
    if await performer_repo.dancer_registered_in_tournament(
        dancer1_uuid, tournament_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dancer {dancer1.blaze} is already registered in this tournament",
        )
    if await performer_repo.dancer_registered_in_tournament(
        dancer2_uuid, tournament_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dancer {dancer2.blaze} is already registered in this tournament",
        )

    # Register first dancer (without partner link initially)
    performer1 = await performer_repo.create_performer(
        tournament_id=tournament_uuid,
        category_id=category_uuid,
        dancer_id=dancer1_uuid,
    )

    # Register second dancer (without partner link initially)
    performer2 = await performer_repo.create_performer(
        tournament_id=tournament_uuid,
        category_id=category_uuid,
        dancer_id=dancer2_uuid,
    )

    # Link them as duo partners
    await performer_repo.link_duo_partners(performer1.id, performer2.id)

    return RedirectResponse(
        url=f"/registration/{tournament_id}/{category_id}",
        status_code=303,
    )


@router.post("/{tournament_id}/{category_id}/unregister/{performer_id}")
async def unregister_dancer(
    request: Request,
    tournament_id: str,
    category_id: str,
    performer_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """Unregister a dancer from a tournament category (staff only).

    Args:
        request: FastAPI request
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
        add_flash_message(request, "Invalid performer ID", "error")
        return RedirectResponse(
            url=f"/registration/{tournament_id}/{category_id}",
            status_code=303,
        )

    # Delete performer
    deleted = await performer_repo.delete(performer_uuid)
    if not deleted:
        add_flash_message(request, "Performer not found", "error")
    else:
        add_flash_message(request, "Dancer unregistered successfully", "success")

    return RedirectResponse(
        url=f"/registration/{tournament_id}/{category_id}",
        status_code=303,
    )


# =============================================================================
# HTMX Two-Panel Registration Endpoints
# =============================================================================


@router.get("/{tournament_id}/{category_id}/available", response_class=HTMLResponse)
async def available_dancers_partial(
    tournament_id: str,
    category_id: str,
    request: Request,
    q: str = "",
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """HTMX partial: Available dancers list.

    Returns dancers that can be registered (not already in tournament).

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        request: FastAPI request
        q: Search query
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        dancer_repo: Dancer repository
        performer_repo: Performer repository

    Returns:
        HTML partial with available dancers
    """
    user = require_staff(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        return HTMLResponse("<p>Invalid ID</p>")

    # Get category
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        return HTMLResponse("<p>Category not found</p>")

    # Search dancers
    if q:
        all_dancers = await dancer_repo.search(q, limit=50)
    else:
        all_dancers = await dancer_repo.get_all()

    # Filter out dancers already registered in this tournament
    available = []
    for dancer in all_dancers:
        if not await performer_repo.dancer_registered_in_tournament(
            dancer.id, tournament_uuid
        ):
            available.append(dancer)

    # Limit to 20 for performance
    available = available[:20]

    return templates.TemplateResponse(
        request=request,
        name="registration/_available_list.html",
        context={
            "available_dancers": available,
            "tournament_id": tournament_id,
            "category_id": category_id,
            "is_duo": category.is_duo,
        },
    )


@router.get("/{tournament_id}/{category_id}/registered", response_class=HTMLResponse)
async def registered_dancers_partial(
    tournament_id: str,
    category_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """HTMX partial: Registered dancers list.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        request: FastAPI request
        current_user: Current authenticated user
        category_repo: Category repository
        performer_repo: Performer repository

    Returns:
        HTML partial with registered performers
    """
    user = require_staff(current_user)

    try:
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        return HTMLResponse("<p>Invalid ID</p>")

    # Get category for ideal count
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        return HTMLResponse("<p>Category not found</p>")

    # Get registered performers
    performers = await performer_repo.get_by_category_with_partners(category_uuid)

    return templates.TemplateResponse(
        request=request,
        name="registration/_registered_list.html",
        context={
            "performers": performers,
            "tournament_id": tournament_id,
            "category_id": category_id,
            "is_duo": category.is_duo,
            "registered_count": len(performers),
            "ideal_count": category.performers_ideal * category.groups_ideal,
            "minimum_required": category.performers_ideal,
        },
    )


@router.post("/{tournament_id}/{category_id}/register/{dancer_id}", response_class=HTMLResponse)
async def register_dancer_htmx(
    tournament_id: str,
    category_id: str,
    dancer_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """HTMX: Register single dancer and return both panels.

    Uses hx-swap-oob to update both available and registered lists.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        dancer_id: Dancer UUID to register
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        dancer_repo: Dancer repository
        performer_repo: Performer repository

    Returns:
        HTML with both panels updated via OOB swap
    """
    user = require_staff(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
        dancer_uuid = uuid.UUID(dancer_id)
    except ValueError:
        return HTMLResponse("<p>Invalid ID</p>")

    # Verify tournament and category exist
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    category = await category_repo.get_by_id(category_uuid)
    dancer = await dancer_repo.get_by_id(dancer_uuid)

    if not tournament or not category or not dancer:
        return HTMLResponse("<p>Not found</p>")

    # Check if already registered
    if await performer_repo.dancer_registered_in_tournament(dancer_uuid, tournament_uuid):
        return HTMLResponse(f"<p class='error'>Already registered</p>")

    # Register dancer
    await performer_repo.create_performer(
        tournament_id=tournament_uuid,
        category_id=category_uuid,
        dancer_id=dancer_uuid,
    )

    # Return both updated lists using OOB swap
    # Get updated available dancers (current search)
    all_dancers = await dancer_repo.get_all()
    available = []
    for d in all_dancers[:20]:
        if not await performer_repo.dancer_registered_in_tournament(d.id, tournament_uuid):
            available.append(d)

    # Get updated registered performers
    performers = await performer_repo.get_by_category_with_partners(category_uuid)

    return templates.TemplateResponse(
        request=request,
        name="registration/_registration_update.html",
        context={
            "available_dancers": available,
            "performers": performers,
            "tournament_id": tournament_id,
            "category_id": category_id,
            "is_duo": category.is_duo,
            "registered_count": len(performers),
            "ideal_count": category.performers_ideal * category.groups_ideal,
            "minimum_required": category.performers_ideal,
        },
    )


@router.post("/{tournament_id}/{category_id}/unregister-htmx/{performer_id}", response_class=HTMLResponse)
async def unregister_dancer_htmx(
    tournament_id: str,
    category_id: str,
    performer_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    performer_repo: PerformerRepository = Depends(get_performer_repo),
):
    """HTMX: Unregister dancer and return both panels.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        performer_id: Performer UUID
        request: FastAPI request
        current_user: Current authenticated user
        tournament_repo: Tournament repository
        category_repo: Category repository
        dancer_repo: Dancer repository
        performer_repo: Performer repository

    Returns:
        HTML with both panels updated via OOB swap
    """
    user = require_staff(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
        category_uuid = uuid.UUID(category_id)
        performer_uuid = uuid.UUID(performer_id)
    except ValueError:
        return HTMLResponse("<p>Invalid ID</p>")

    # Get category
    category = await category_repo.get_by_id(category_uuid)
    if not category:
        return HTMLResponse("<p>Category not found</p>")

    # Delete performer
    await performer_repo.delete(performer_uuid)

    # Return both updated lists
    all_dancers = await dancer_repo.get_all()
    available = []
    for d in all_dancers[:20]:
        if not await performer_repo.dancer_registered_in_tournament(d.id, tournament_uuid):
            available.append(d)

    performers = await performer_repo.get_by_category_with_partners(category_uuid)

    return templates.TemplateResponse(
        request=request,
        name="registration/_registration_update.html",
        context={
            "available_dancers": available,
            "performers": performers,
            "tournament_id": tournament_id,
            "category_id": category_id,
            "is_duo": category.is_duo,
            "registered_count": len(performers),
            "ideal_count": category.performers_ideal * category.groups_ideal,
            "minimum_required": category.performers_ideal,
        },
    )
