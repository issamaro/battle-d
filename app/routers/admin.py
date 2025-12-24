"""Admin routes for user management."""
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from starlette.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import (
    get_current_user,
    require_admin,
    CurrentUser,
    get_user_repo,
    get_email_service,
    get_flash_messages_dependency,
    get_tournament_repo,
)
from app.repositories.user import UserRepository
from app.repositories.tournament import TournamentRepository
from app.models.user import UserRole
from app.models.tournament import TournamentStatus, TournamentPhase
from app.auth import magic_link_auth
from app.services.email.service import EmailService
from app.utils.flash import add_flash_message

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    role_filter: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    flash_messages: list = Depends(get_flash_messages_dependency),
):
    """List all users (admin only).

    Args:
        request: FastAPI request
        role_filter: Optional role filter
        current_user: Current authenticated user
        user_repo: User repository
        flash_messages: Flash messages from session

    Returns:
        HTML page with user list
    """
    user = require_admin(current_user)

    # Get users (filtered by role if specified)
    if role_filter:
        try:
            role_enum = UserRole(role_filter)
            users = await user_repo.get_by_role(role_enum)
        except ValueError:
            users = await user_repo.get_all()
    else:
        users = await user_repo.get_all()

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "current_user": user,
            "users": users,
            "roles": [role.value for role in UserRole],
            "selected_role": role_filter,
            "flash_messages": flash_messages,
        },
    )


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_form(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Display create user form (admin only).

    Args:
        request: FastAPI request
        current_user: Current authenticated user

    Returns:
        HTML form for creating user
    """
    user = require_admin(current_user)

    return templates.TemplateResponse(
        request=request,
        name="admin/create_user.html",
        context={
            "current_user": user,
            "roles": [role.value for role in UserRole],
        },
    )


@router.post("/users/create")
async def create_user(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    role: str = Form(...),
    send_magic_link: bool = Form(False),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    email_service: EmailService = Depends(get_email_service),
):
    """Create a new user (admin only).

    Business Rules (BR-UX-004, BR-UX-007):
    - Uses HTMX + HX-Redirect pattern for modal submission
    - Returns form partial with errors on validation failure
    - Returns HX-Redirect to user list on success

    Args:
        request: FastAPI request
        email: User email
        first_name: User first name
        role: User role
        send_magic_link: Whether to send magic link email
        current_user: Current authenticated user
        user_repo: User repository
        email_service: Email service

    Returns:
        HX-Redirect to user list on success
    """
    user = require_admin(current_user)
    is_htmx = request.headers.get("HX-Request") == "true"
    errors = {}

    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        errors["role"] = f"Invalid role: {role}"

    # Check if email already exists
    if await user_repo.email_exists(email.lower()):
        errors["email"] = f"Email '{email}' is already registered"

    # If validation errors, return form partial
    if errors:
        if is_htmx:
            return templates.TemplateResponse(
                request=request,
                name="components/user_create_form_partial.html",
                context={
                    "errors": errors,
                    "email": email,
                    "first_name": first_name,
                    "role": role,
                    "roles": [r.value for r in UserRole],
                },
                status_code=400,
            )
        add_flash_message(request, list(errors.values())[0], "error")
        return RedirectResponse(url="/admin/users/create", status_code=303)

    # Create user
    new_user = await user_repo.create_user(
        email=email.lower(),
        first_name=first_name,
        role=user_role,
    )

    # Send magic link if requested
    if send_magic_link:
        magic_link = magic_link_auth.generate_magic_link(new_user.email, new_user.role.value)
        await email_service.send_magic_link(new_user.email, magic_link, new_user.first_name)
        add_flash_message(request, f"User '{first_name}' created and magic link sent", "success")
    else:
        add_flash_message(request, f"User '{first_name}' created successfully", "success")

    # Return HX-Redirect for HTMX
    if is_htmx:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = "/admin/users"
        return response

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/delete")
async def delete_user(
    request: Request,
    user_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Delete a user (admin only).

    Args:
        request: FastAPI request
        user_id: User UUID
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        Redirect to user list
    """
    user = require_admin(current_user)

    # Parse UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        add_flash_message(request, "Invalid user ID", "error")
        return RedirectResponse(url="/admin/users", status_code=303)

    # Delete user
    deleted = await user_repo.delete(user_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    add_flash_message(request, "User deleted successfully", "success")
    return RedirectResponse(url="/admin/users", status_code=303)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    user_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Display edit user form (admin only).

    Args:
        user_id: User UUID
        request: FastAPI request
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        HTML form for editing user
    """
    require_admin(current_user)

    # Parse UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    # Get user
    user_to_edit = await user_repo.get_by_id(user_uuid)
    if not user_to_edit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/edit_user.html",
        context={
            "current_user": current_user,
            "user_to_edit": user_to_edit,
            "roles": [role.value for role in UserRole],
        },
    )


@router.post("/users/{user_id}/edit")
async def update_user(
    request: Request,
    user_id: str,
    email: str = Form(...),
    first_name: str = Form(...),
    role: str = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Update a user (admin only).

    Args:
        request: FastAPI request
        user_id: User UUID
        email: User email
        first_name: User first name
        role: User role
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        Redirect to user list
    """
    require_admin(current_user)

    # Parse UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        add_flash_message(request, "Invalid user ID", "error")
        return RedirectResponse(url="/admin/users", status_code=303)

    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        add_flash_message(request, f"Invalid role: {role}", "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=303)

    # Check if user exists
    existing_user = await user_repo.get_by_id(user_uuid)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if email is being changed and if new email already exists
    email_lower = email.lower()
    if email_lower != existing_user.email:
        if await user_repo.email_exists(email_lower):
            add_flash_message(request, f"Email '{email}' is already registered", "error")
            return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=303)

    # Update user
    await user_repo.update(
        user_uuid,
        email=email_lower,
        first_name=first_name,
        role=user_role,
    )
    add_flash_message(request, f"User '{first_name}' updated successfully", "success")

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/resend-magic-link")
async def resend_magic_link(
    request: Request,
    user_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    email_service: EmailService = Depends(get_email_service),
):
    """Resend magic link to a user (admin only).

    Args:
        request: FastAPI request
        user_id: User UUID
        current_user: Current authenticated user
        user_repo: User repository
        email_service: Email service

    Returns:
        Redirect to user list
    """
    require_admin(current_user)

    # Parse UUID
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        add_flash_message(request, "Invalid user ID", "error")
        return RedirectResponse(url="/admin/users", status_code=303)

    # Get user
    user_to_send = await user_repo.get_by_id(user_uuid)
    if not user_to_send:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate and send magic link
    magic_link = magic_link_auth.generate_magic_link(
        user_to_send.email, user_to_send.role.value
    )
    await email_service.send_magic_link(
        user_to_send.email, magic_link, user_to_send.first_name
    )
    add_flash_message(request, f"Magic link sent to {user_to_send.email}", "success")

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/tournaments/fix-active")
async def fix_active_tournaments(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Fix multiple active tournaments with intelligent status selection.

    Admin only selects which tournament to keep active. The endpoint
    automatically determines the correct status for deactivated tournaments
    based on their current phase.

    Phase-Status Mapping:
    - REGISTRATION → CREATED (hasn't started yet)
    - PRESELECTION/POOLS/FINALS → CANCELLED (in-progress, stopped)
    - COMPLETED → COMPLETED (already finished)

    Args:
        request: FastAPI request with form data
        current_user: Current authenticated user
        tournament_repo: Tournament repository

    Returns:
        Redirect to tournaments with success/error message
    """
    require_admin(current_user)

    # Get all active tournaments
    active_tournaments = await tournament_repo.get_active_tournaments()

    if len(active_tournaments) <= 1:
        add_flash_message(
            request,
            "No data integrity issue found. Only one or zero tournaments are active.",
            "info"
        )
        return RedirectResponse(url="/tournaments", status_code=303)

    # Parse form: Only tournament_id field with value "keep"
    form_data = await request.form()
    keep_active_id = form_data.get("keep_active")

    if not keep_active_id:
        add_flash_message(
            request,
            "You must select one tournament to keep active.",
            "error"
        )
        return RedirectResponse(url="/tournaments", status_code=303)

    try:
        keep_active_uuid = uuid.UUID(keep_active_id)
    except ValueError:
        add_flash_message(request, "Invalid tournament ID.", "error")
        return RedirectResponse(url="/tournaments", status_code=303)

    # Validate the selected tournament is in the active list
    if not any(t.id == keep_active_uuid for t in active_tournaments):
        add_flash_message(
            request,
            "Selected tournament is not in the active list.",
            "error"
        )
        return RedirectResponse(url="/tournaments", status_code=303)

    # Deactivate all others with intelligent status selection
    deactivated_count = 0
    for tournament in active_tournaments:
        if tournament.id != keep_active_uuid:
            # Determine correct status based on phase
            if tournament.phase == TournamentPhase.REGISTRATION:
                new_status = TournamentStatus.CREATED
            elif tournament.phase == TournamentPhase.COMPLETED:
                new_status = TournamentStatus.COMPLETED
            else:
                # PRESELECTION, POOLS, or FINALS
                new_status = TournamentStatus.CANCELLED

            await tournament_repo.update(tournament.id, status=new_status)
            deactivated_count += 1

    add_flash_message(
        request,
        f"Tournament configuration fixed. {deactivated_count} tournament(s) deactivated.",
        "success"
    )
    return RedirectResponse(url="/tournaments", status_code=303)
