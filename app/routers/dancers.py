"""Dancer management routes."""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from starlette.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_staff,
    CurrentUser,
    get_dancer_repo,
    get_dancer_service,
    get_flash_messages_dependency,
)
from app.exceptions import ValidationError
from app.repositories.dancer import DancerRepository
from app.utils.flash import add_flash_message

router = APIRouter(prefix="/dancers", tags=["dancers"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_dancers(
    request: Request,
    search: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """List all dancers with optional search (staff only).

    Args:
        request: FastAPI request
        search: Optional search query
        current_user: Current authenticated user
        dancer_repo: Dancer repository
        flash_messages: Flash messages from session

    Returns:
        HTML page with dancer list
    """
    user = require_staff(current_user)

    # Get dancers (with search if provided)
    if search:
        dancers = await dancer_repo.search(search)
    else:
        dancers = await dancer_repo.get_all(limit=100)

    return templates.TemplateResponse(
        request=request,
        name="dancers/list.html",
        context={
            "current_user": user,
            "dancers": dancers,
            "search": search or "",
            "flash_messages": flash_messages,
        },
    )


@router.get("/api/search", response_class=HTMLResponse)
async def search_dancers_api(
    request: Request,
    query: str = "",
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """HTMX endpoint for live dancer search.

    Args:
        request: FastAPI request
        query: Search query
        current_user: Current authenticated user
        dancer_repo: Dancer repository

    Returns:
        HTML partial with dancer table
    """
    user = require_staff(current_user)

    # Search dancers
    if query:
        dancers = await dancer_repo.search(query)
    else:
        dancers = await dancer_repo.get_all(limit=100)

    return templates.TemplateResponse(
        request=request,
        name="dancers/_table.html",
        context={
            "dancers": dancers,
            "search": query,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_dancer_form(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Display create dancer form (staff only).

    Args:
        request: FastAPI request
        current_user: Current authenticated user

    Returns:
        HTML form for creating dancer
    """
    user = require_staff(current_user)

    return templates.TemplateResponse(
        request=request,
        name="dancers/create.html",
        context={
            "current_user": user,
        },
    )


@router.post("/create")
async def create_dancer(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    blaze: str = Form(...),
    country: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_service = Depends(get_dancer_service),
):
    """Create a new dancer (staff only).

    Business Rules (BR-UX-004, BR-UX-007):
    - Uses HTMX + HX-Redirect pattern for modal submission
    - Returns form partial with errors on validation failure
    - Returns HX-Redirect to dancer list on success

    Args:
        request: FastAPI request
        email: Dancer email
        first_name: First name
        last_name: Last name
        date_of_birth: Birth date (YYYY-MM-DD)
        blaze: Stage name
        country: Country (optional)
        city: City (optional)
        current_user: Current authenticated user
        dancer_service: Dancer service

    Returns:
        HX-Redirect to dancer list on success
    """
    user = require_staff(current_user)
    is_htmx = request.headers.get("HX-Request") == "true"
    errors = {}

    # Parse date
    dob = None
    try:
        dob = date.fromisoformat(date_of_birth)
    except ValueError:
        errors["date_of_birth"] = "Invalid date format. Use YYYY-MM-DD"

    # Create dancer via service (handles validation)
    if not errors:
        try:
            await dancer_service.create_dancer(
                email=email,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                blaze=blaze,
                country=country if country else None,
                city=city if city else None,
            )
            add_flash_message(request, f"Dancer '{blaze}' created successfully", "success")

            # Return HX-Redirect for HTMX
            if is_htmx:
                response = HTMLResponse(content="", status_code=200)
                response.headers["HX-Redirect"] = "/dancers"
                return response

            return RedirectResponse(url="/dancers", status_code=303)

        except ValidationError as e:
            errors["general"] = e.errors[0] if e.errors else "Validation error"

    # If errors, return form partial or redirect
    if is_htmx:
        return templates.TemplateResponse(
            request=request,
            name="components/dancer_create_form_partial.html",
            context={
                "errors": errors,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth,
                "blaze": blaze,
                "country": country,
                "city": city,
            },
            status_code=400,
        )

    add_flash_message(request, list(errors.values())[0], "error")
    return RedirectResponse(url="/dancers/create", status_code=303)


@router.get("/{dancer_id}/profile", response_class=HTMLResponse)
async def view_dancer_profile(
    dancer_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """Display dancer profile with tournament history (staff only).

    Args:
        dancer_id: Dancer UUID
        request: FastAPI request
        current_user: Current authenticated user
        dancer_repo: Dancer repository

    Returns:
        HTML page with dancer profile
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        dancer_uuid = uuid.UUID(dancer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dancer ID",
        )

    # Get dancer
    dancer = await dancer_repo.get_by_id(dancer_uuid)
    if not dancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dancer not found",
        )

    # TODO: In Phase 2, fetch tournament history via performer relationships
    # For now, just show dancer details
    return templates.TemplateResponse(
        request=request,
        name="dancers/profile.html",
        context={
            "current_user": user,
            "dancer": dancer,
        },
    )


@router.get("/{dancer_id}/edit", response_class=HTMLResponse)
async def edit_dancer_form(
    dancer_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """Display edit dancer form (staff only).

    Args:
        dancer_id: Dancer UUID
        request: FastAPI request
        current_user: Current authenticated user
        dancer_repo: Dancer repository

    Returns:
        HTML form for editing dancer
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        dancer_uuid = uuid.UUID(dancer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dancer ID",
        )

    # Get dancer
    dancer = await dancer_repo.get_by_id(dancer_uuid)
    if not dancer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dancer not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="dancers/edit.html",
        context={
            "current_user": user,
            "dancer": dancer,
        },
    )


@router.post("/{dancer_id}/edit")
async def edit_dancer(
    dancer_id: str,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    blaze: str = Form(...),
    country: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """Update a dancer (staff only).

    Args:
        dancer_id: Dancer UUID
        email: Dancer email
        first_name: First name
        last_name: Last name
        date_of_birth: Birth date (YYYY-MM-DD)
        blaze: Stage name
        country: Country (optional)
        city: City (optional)
        current_user: Current authenticated user
        dancer_repo: Dancer repository

    Returns:
        Redirect to dancer list
    """
    user = require_staff(current_user)

    # Parse UUID
    try:
        dancer_uuid = uuid.UUID(dancer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dancer ID",
        )

    # Parse date
    try:
        dob = date.fromisoformat(date_of_birth)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Update dancer
    updated = await dancer_repo.update(
        dancer_uuid,
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        blaze=blaze,
        country=country if country else None,
        city=city if city else None,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dancer not found",
        )

    return RedirectResponse(url="/dancers", status_code=303)
