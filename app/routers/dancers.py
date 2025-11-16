"""Dancer management routes."""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_staff,
    CurrentUser,
    get_dancer_repo,
)
from app.repositories.dancer import DancerRepository

router = APIRouter(prefix="/dancers", tags=["dancers"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_dancers(
    request: Request,
    search: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    dancer_repo: DancerRepository = Depends(get_dancer_repo),
):
    """List all dancers with optional search (staff only).

    Args:
        request: FastAPI request
        search: Optional search query
        current_user: Current authenticated user
        dancer_repo: Dancer repository

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
    """Create a new dancer (staff only).

    Args:
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

    # Check if email already exists
    if await dancer_repo.email_exists(email.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Parse date
    try:
        dob = date.fromisoformat(date_of_birth)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Create dancer
    await dancer_repo.create_dancer(
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        blaze=blaze,
        country=country if country else None,
        city=city if city else None,
    )

    return RedirectResponse(url="/dancers", status_code=303)


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
