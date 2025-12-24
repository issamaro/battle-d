# Implementation Plan: UX Issues Batch Fix

**Date:** 2024-12-24
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2024-12-24_UX-ISSUES-BATCH.md
**Last Updated:** 2024-12-24 (Comprehensive revision with actual codebase analysis)

---

## 1. Summary

**Feature:** Fix 6 UX inconsistencies + 1 harmonization task in the admin interface
**Approach:** Prioritized implementation starting with critical issues (modal positioning, phase advancement), then medium-priority (category removal, creation modals, modal harmonization), then low-priority polish (three dots menu, empty state alignment)

**Build System:** Dart Sass (already configured)
```bash
# Development (watch mode)
sass --watch app/static/scss:app/static/css

# Production (single compile)
sass app/static/scss:app/static/css --style=compressed
```

---

## 2. Affected Files

### 2.1 Backend

**Routes:**

| File | Changes | Issue |
|------|---------|-------|
| `app/routers/tournaments.py` | Add `DELETE /{id}/categories/{cat_id}`, Add `POST /{id}/rename`, Add `POST /{id}/advance` | #3, #1, #6 |
| `app/routers/admin.py` | Add `POST /users/create` HTMX support (HX-Redirect) | #4, #7 |
| `app/routers/dancers.py` | Add `POST /create` HTMX support (HX-Redirect) | #4, #7 |

**Repositories:**
- `app/repositories/category.py`: Use existing `delete(category_id)` from BaseRepository
- No new repository methods needed - existing patterns sufficient

**Services:**
- No new services needed - existing patterns sufficient

### 2.2 Frontend - Templates

**Templates - Existing (Updates):**

| File | Changes | Issue |
|------|---------|-------|
| `app/templates/tournaments/list.html:46-52` | Replace dead button with dropdown menu | #1 |
| `app/templates/tournaments/detail.html:93-95` | Add category remove button + phase advance button | #3, #6 |
| `app/templates/admin/users.html:13` | Change `<a>` to `<button>` + include modal | #4 |
| `app/templates/dancers/list.html:13` | Change `<a>` to `<button>` + include modal | #4 |
| `app/templates/components/tournament_create_modal.html:30` | Convert from `method="POST"` to `hx-post` | #7 |

**Templates - New Components:**

| File | Purpose | Issue |
|------|---------|-------|
| `app/templates/components/tournament_actions_dropdown.html` | Three dots menu for tournament cards | #1 |
| `app/templates/components/rename_modal.html` | Simple rename modal | #1 |
| `app/templates/components/user_create_modal.html` | User creation form modal | #4 |
| `app/templates/components/dancer_create_modal.html` | Dancer creation form modal | #4 |
| `app/templates/components/phase_advance_modal.html` | Phase advancement preview modal | #6 |
| `app/templates/components/category_remove_modal.html` | Category removal confirmation | #3 |

### 2.3 Frontend - SCSS (Source Files)

**IMPORTANT:** All CSS changes must be made to SCSS source files, not `main.css`.

**SCSS Files to Modify:**

| File | Issue | Change |
|------|-------|--------|
| `app/static/scss/components/_modals.scss:9-14` | #5 | Add `margin: auto;` to `.modal` class |
| `app/static/scss/components/_empty-state.scss:23-26` | #2 | Add `display: block;` to `.empty-state-icon svg` |

**SCSS Files to Reuse (No Changes):**

| File | Purpose |
|------|---------|
| `app/static/scss/components/_dropdown.scss` | Complete dropdown menu styles (`.dropdown`, `.dropdown-menu`, `.dropdown-item`, `.btn-actions`) |
| `app/static/scss/components/_buttons.scss` | Button variants (`.btn-*`, `.btn-sm`, `.btn-icon`) |
| `app/static/scss/components/_badges.scss` | Status badges (`.badge-*`) |
| `app/static/scss/abstracts/_variables.scss` | Design tokens |

**After SCSS changes, run:**
```bash
sass app/static/scss:app/static/css
```

### 2.4 Database
- No schema changes needed
- No migrations required

### 2.5 Tests

**New Test Files:**
- `tests/e2e/test_ux_issues_batch.py`: End-to-end tests for all 7 issues

**Updated Test Files:**
- `tests/test_tournaments.py`: Add category removal tests
- `tests/test_admin.py`: Add HTMX user create tests

### 2.6 Documentation

**Level 1 - Source of Truth:**
- `workbench/DOMAIN_MODEL.md`: Update category deletion rule (CASCADE behavior)

**Level 3 - Operational:**
- `FRONTEND.md`: Document HTMX modal pattern, dropdown usage

---

## 3. Backend Implementation Plan

### 3.1 No Database Changes Needed
All functionality uses existing models and relationships.
- Category deletion uses existing `BaseRepository.delete()` method
- CASCADE deletion of Performers is handled by SQLAlchemy relationship configuration

### 3.2 Route Changes

#### Router: `app/routers/tournaments.py`

**Existing Code Analysis:**
- Lines 89-115: `POST /create` - Currently returns `RedirectResponse`
- Lines 230-277: `POST /{id}/add-category` - Pattern for category management

**New Endpoint: Category Removal (Issue #3)**

Location: Add after line 277

```python
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

    # Delete category (CASCADE deletes performers via SQLAlchemy)
    deleted = await category_repo.delete(category_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    add_flash_message(request, "Category removed successfully", "success")

    # Return empty response for HTMX swap="delete"
    return HTMLResponse(content="", status_code=200)
```

**New Endpoint: Tournament Rename (Issue #1)**

Location: Add after category delete endpoint

```python
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
```

**New Endpoint: Phase Advancement (Issue #6)**

Location: Add after rename endpoint

```python
@router.post("/{tournament_id}/advance")
async def advance_phase_from_tournaments(
    tournament_id: str,
    request: Request,
    confirmed: bool = Form(False),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Advance tournament to next phase (admin only).

    Business Rules (BR-UX-006):
    - NEW endpoint at /tournaments/{id}/advance (replaces deprecated /event/{id}/advance)
    - Admin-only access
    - Shows detailed preview before confirmation
    - Redirects to Event Mode on success

    Args:
        tournament_id: Tournament UUID
        request: FastAPI request
        confirmed: Whether user confirmed advancement
        current_user: Current authenticated user
        tournament_service: Tournament service for phase operations
        tournament_repo: Tournament repository

    Returns:
        Preview modal partial, validation errors, or redirect to event mode
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

    # Get tournament
    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    is_htmx = request.headers.get("HX-Request") == "true"

    # If confirmed, advance phase
    if confirmed:
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
            add_flash_message(request, e.errors[0] if e.errors else "Cannot advance phase", "error")
            return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=303)

    # Not confirmed - this endpoint is called from the modal form
    # The modal handles the preview UI; just submit the form
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Confirmation required",
    )
```

**Update Existing Endpoint: Tournament Create (Issue #7)**

Location: Modify lines 89-115

```python
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

    # Validate name
    if not name or not name.strip():
        # Return form partial with error for HTMX swap
        return templates.TemplateResponse(
            request=request,
            name="components/tournament_create_form_partial.html",
            context={
                "error": "Tournament name is required",
                "name": name,
            },
            status_code=400,
        )

    # Create tournament
    tournament = await tournament_repo.create_tournament(name=name.strip())
    add_flash_message(request, f"Tournament '{name}' created successfully", "success")

    # Check if HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Redirect"] = f"/tournaments/{tournament.id}"
        return response

    return RedirectResponse(url=f"/tournaments/{tournament.id}", status_code=303)
```

#### Router: `app/routers/admin.py`

**Update Existing Endpoint: User Create (Issue #4, #7)**

Location: Modify lines 99-154

```python
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
```

#### Router: `app/routers/dancers.py`

**Update Existing Endpoint: Dancer Create (Issue #4, #7)**

Location: Modify lines 125-181

```python
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
```

### 3.3 Repository Changes

**No new repository methods needed** - existing patterns are sufficient:
- `BaseRepository.delete()` handles category deletion
- `BaseRepository.update()` handles tournament rename
- CASCADE deletion of Performers is configured in SQLAlchemy model relationships

---

## 4. Frontend Implementation Plan

### 4.1 Issue #5: Modal Centering (CRITICAL - Fix First)

**Root Cause:** `<dialog>` element has browser-default positioning that overrides flexbox centering. The existing `.modal[open]` styles use flexbox, but browser defaults override them.

**Evidence:** Current CSS at `_modals.scss:9-26` has correct flexbox but missing `margin: auto` reset.

**Fix Location:** `app/static/scss/components/_modals.scss`

**Current Code (lines 9-15):**
```scss
.modal {
  // Hidden by default - native dialog behavior
  display: none;
  border: none;
  padding: 0;
  background: transparent;
```

**Updated Code:**
```scss
.modal {
  // Hidden by default - native dialog behavior
  display: none;
  border: none;
  padding: 0;
  background: transparent;
  margin: auto;  // ADD: Override browser default dialog positioning
```

**Why this works:** The `<dialog>` element has browser defaults that position it. By adding `margin: auto` to the base `.modal` class, we ensure the dialog centers properly when combined with the flexbox container.

**Testing:**
- Chrome: Verify create tournament modal opens centered
- Firefox: Verify delete modals open centered
- Safari: Verify all modals open centered

---

### 4.2 Issue #2: Empty State Icon Alignment

**Root Cause:** The SVG inside `.empty-state-icon` renders as inline by default, which can cause centering issues when the parent uses flexbox.

**Evidence:** Current CSS at `_empty-state.scss:23-26` sets width/height but not display.

**Fix Location:** `app/static/scss/components/_empty-state.scss`

**Current Code (lines 23-26):**
```scss
  svg {
    width: 100%;
    height: 100%;
  }
```

**Updated Code:**
```scss
  svg {
    display: block;  // ADD: Ensure SVG is block-level for proper centering
    width: 100%;
    height: 100%;
  }
```

---

### 4.3 Issue #6: Phase Advancement UI (CRITICAL)

**Current State:**
- Backend exists at `POST /event/{tournament_id}/advance` (will be DEPRECATED)
- No UI on tournament detail page
- **New endpoint:** `POST /tournaments/{tournament_id}/advance`

**File: `app/templates/tournaments/detail.html`**

Add phase advancement section after categories (after line 114):

```html
{# Phase Advancement Section - Admin Only #}
{% if current_user.is_admin and tournament.phase.value == 'registration' %}
<section class="mt-6">
    <h3>Phase Advancement</h3>

    {% set all_ready = true %}
    {% for item in category_data %}
        {% if item.performer_count < item.category.minimum_performers_required %}
            {% set all_ready = false %}
        {% endif %}
    {% endfor %}

    {% if all_ready and category_data|length > 0 %}
    <div class="card">
        <div class="card-body">
            <p>All categories meet minimum requirements. You can advance to the next phase.</p>
            <button type="button"
                    class="btn btn-primary"
                    onclick="document.getElementById('phase-advance-modal').showModal()">
                Advance to Preselection →
            </button>
        </div>
    </div>
    {% else %}
    <div class="card">
        <div class="card-body">
            <div class="alert alert-warning">
                <strong>Cannot advance phase:</strong>
                {% if category_data|length == 0 %}
                    No categories have been added yet.
                {% else %}
                    Not all categories meet minimum performer requirements.
                {% endif %}
            </div>
        </div>
    </div>
    {% endif %}
</section>

{# Include Phase Advance Modal #}
{% set modal_tournament = tournament %}
{% set modal_category_data = category_data %}
{% include "components/phase_advance_modal.html" %}
{% endif %}
```

**File: `app/templates/components/phase_advance_modal.html` (NEW)**

```html
{#
  Phase Advancement Preview Modal

  Usage:
    {% set modal_tournament = tournament %}
    {% set modal_category_data = category_data %}
    {% include "components/phase_advance_modal.html" %}

  Required context:
    - modal_tournament: Tournament object
    - modal_category_data: List of {category, performer_count} dicts
#}

<dialog id="phase-advance-modal" class="modal modal-lg" aria-labelledby="phase-advance-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="phase-advance-title" class="modal-title">Advance Tournament Phase</h3>
      <button type="button"
              class="modal-close"
              aria-label="Close"
              onclick="document.getElementById('phase-advance-modal').close()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="modal-body">
      <div class="modal-warning" role="alert">
        <strong>Warning:</strong> This action is IRREVERSIBLE. You cannot go back to the Registration phase.
      </div>

      <h4>Phase Transition</h4>
      <table class="table mb-4">
        <tr>
          <td><strong>Current Phase:</strong></td>
          <td><span class="badge badge-pending">{{ modal_tournament.phase.value|upper }}</span></td>
        </tr>
        <tr>
          <td><strong>Next Phase:</strong></td>
          <td><span class="badge badge-active">PRESELECTION</span></td>
        </tr>
        <tr>
          <td><strong>Status Change:</strong></td>
          <td>CREATED → ACTIVE</td>
        </tr>
      </table>

      <h4>Category Readiness</h4>
      <table class="table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Registered</th>
            <th>Required</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for item in modal_category_data %}
          {% set min_req = item.category.minimum_performers_required %}
          {% set is_ready = item.performer_count >= min_req %}
          <tr>
            <td>{{ item.category.name }}</td>
            <td>{{ item.performer_count }}</td>
            <td>{{ min_req }}</td>
            <td>
              {% if is_ready %}
              <span class="badge badge-completed">Ready</span>
              {% else %}
              <span class="badge badge-pending">Needs {{ min_req - item.performer_count }} more</span>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>

      <div class="alert alert-info mt-4">
        <p><strong>What happens next:</strong></p>
        <ul>
          <li>Preselection battles will be generated for all categories</li>
          <li>Tournament status changes to ACTIVE</li>
          <li>You will be redirected to Event Mode</li>
        </ul>
      </div>
    </div>

    <div class="modal-footer">
      <button type="button"
              class="btn btn-secondary"
              onclick="document.getElementById('phase-advance-modal').close()">
        Cancel
      </button>
      <form method="POST" action="/tournaments/{{ modal_tournament.id }}/advance" class="inline-form">
        <input type="hidden" name="confirmed" value="true">
        <button type="submit" class="btn btn-primary">
          Confirm Advancement
        </button>
      </form>
    </div>
  </div>
</dialog>

<script>
  // ESC key handling
  document.getElementById('phase-advance-modal').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  });

  // Close on backdrop click
  document.getElementById('phase-advance-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      this.close();
    }
  });
</script>
```

---

### 4.4 Issue #3: Category Removal

**File: `app/templates/tournaments/detail.html`**

Update Actions column in category table (around line 94):

```html
<td>
    <div class="btn-group">
        <a href="/registration/{{ tournament.id }}/{{ item.category.id }}" class="btn btn-sm btn-secondary">
            Register
        </a>
        {% if tournament.phase.value == 'registration' %}
        <button type="button"
                class="btn btn-sm btn-danger"
                hx-delete="/tournaments/{{ tournament.id }}/categories/{{ item.category.id }}"
                hx-confirm="Remove category '{{ item.category.name }}'? {% if item.performer_count > 0 %}This will also remove {{ item.performer_count }} registered performer(s).{% endif %}"
                hx-target="closest tr"
                hx-swap="delete">
            Remove
        </button>
        {% endif %}
    </div>
</td>
```

**Note:** We use `hx-confirm` for simple confirmation instead of a separate modal (per BR-UX-003: "Simple confirmation modal"). The HTMX `hx-delete` with `hx-swap="delete"` removes the row in-place.

---

### 4.5 Issue #4: Creation Forms as Modals

#### User Create Modal

**File: `app/templates/admin/users.html`**

Update line 13 (change `<a>` to `<button>`):

```html
<button type="button"
        class="btn btn-create"
        onclick="document.getElementById('create-user-modal').showModal()">
    + Create User
</button>
```

Add at end of file (before `{% endblock %}`):

```html
{# User Create Modal #}
{% include "components/user_create_modal.html" %}
```

**File: `app/templates/components/user_create_modal.html` (NEW)**

```html
{#
  User Create Modal Component

  Usage:
    {% include "components/user_create_modal.html" %}

  Required context:
    - roles: List of role values (passed from parent template)

  CSS: Uses classes from components/_modals.scss
#}

<dialog id="create-user-modal" class="modal" aria-labelledby="create-user-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="create-user-title" class="modal-title">Create New User</h3>
      <button type="button"
              class="modal-close"
              aria-label="Close"
              onclick="document.getElementById('create-user-modal').close()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <form hx-post="/admin/users/create"
          hx-target="#create-user-modal .modal-body"
          hx-swap="innerHTML">
      <div class="modal-body" id="create-user-form-container">
        {% include "components/user_create_form_partial.html" %}
      </div>

      <div class="modal-footer">
        <button type="button"
                class="btn btn-secondary"
                onclick="document.getElementById('create-user-modal').close()">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Create User
        </button>
      </div>
    </form>
  </div>
</dialog>

<script>
  document.getElementById('create-user-modal').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  });

  document.getElementById('create-user-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      this.close();
    }
  });
</script>
```

**File: `app/templates/components/user_create_form_partial.html` (NEW)**

```html
{#
  User Create Form Partial (for HTMX swap)

  Used inside user_create_modal.html
  Swapped on validation errors
#}

{% if errors %}
<div class="alert alert-danger mb-4">
  {% for field, message in errors.items() %}
  <p>{{ message }}</p>
  {% endfor %}
</div>
{% endif %}

<div class="form-group">
  <label for="email" class="form-label">Email <span class="required">*</span></label>
  <input type="email"
         id="email"
         name="email"
         required
         class="form-input {% if errors and errors.email %}is-invalid{% endif %}"
         value="{{ email|default('', true) }}"
         autofocus>
</div>

<div class="form-group">
  <label for="first_name" class="form-label">First Name <span class="required">*</span></label>
  <input type="text"
         id="first_name"
         name="first_name"
         required
         class="form-input"
         value="{{ first_name|default('', true) }}">
</div>

<div class="form-group">
  <label for="role" class="form-label">Role <span class="required">*</span></label>
  <select id="role" name="role" required class="form-select">
    {% for r in roles %}
    <option value="{{ r }}" {% if role == r %}selected{% endif %}>{{ r }}</option>
    {% endfor %}
  </select>
</div>

<div class="form-check mb-4">
  <input type="checkbox" name="send_magic_link" value="true" checked class="form-check-input" id="send_magic_link">
  <label for="send_magic_link" class="form-check-label">Send magic link email to user</label>
</div>
```

#### Dancer Create Modal

**File: `app/templates/dancers/list.html`**

Update line 13 (change `<a>` to `<button>`):

```html
<button type="button"
        class="btn btn-create"
        onclick="document.getElementById('create-dancer-modal').showModal()">
    + Create Dancer
</button>
```

Add at end of file (before `{% endblock %}`):

```html
{# Dancer Create Modal #}
{% include "components/dancer_create_modal.html" %}
```

**File: `app/templates/components/dancer_create_modal.html` (NEW)**

```html
{#
  Dancer Create Modal Component

  Usage:
    {% include "components/dancer_create_modal.html" %}

  CSS: Uses classes from components/_modals.scss
#}

<dialog id="create-dancer-modal" class="modal modal-lg" aria-labelledby="create-dancer-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="create-dancer-title" class="modal-title">Create New Dancer</h3>
      <button type="button"
              class="modal-close"
              aria-label="Close"
              onclick="document.getElementById('create-dancer-modal').close()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <form hx-post="/dancers/create"
          hx-target="#create-dancer-modal .modal-body"
          hx-swap="innerHTML">
      <div class="modal-body" id="create-dancer-form-container">
        {% include "components/dancer_create_form_partial.html" %}
      </div>

      <div class="modal-footer">
        <button type="button"
                class="btn btn-secondary"
                onclick="document.getElementById('create-dancer-modal').close()">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Create Dancer
        </button>
      </div>
    </form>
  </div>
</dialog>

<script>
  document.getElementById('create-dancer-modal').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  });

  document.getElementById('create-dancer-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      this.close();
    }
  });
</script>
```

**File: `app/templates/components/dancer_create_form_partial.html` (NEW)**

```html
{#
  Dancer Create Form Partial (for HTMX swap)

  Used inside dancer_create_modal.html
  Swapped on validation errors
#}

{% if errors %}
<div class="alert alert-danger mb-4">
  {% for field, message in errors.items() %}
  <p>{{ message }}</p>
  {% endfor %}
</div>
{% endif %}

<div class="form-row">
  <div class="form-group">
    <label for="first_name" class="form-label">First Name <span class="required">*</span></label>
    <input type="text"
           id="first_name"
           name="first_name"
           required
           class="form-input"
           value="{{ first_name|default('', true) }}"
           autofocus>
  </div>
  <div class="form-group">
    <label for="last_name" class="form-label">Last Name <span class="required">*</span></label>
    <input type="text"
           id="last_name"
           name="last_name"
           required
           class="form-input"
           value="{{ last_name|default('', true) }}">
  </div>
</div>

<div class="form-group">
  <label for="blaze" class="form-label">Blaze (Stage Name) <span class="required">*</span></label>
  <input type="text"
         id="blaze"
         name="blaze"
         required
         class="form-input"
         value="{{ blaze|default('', true) }}">
  <small class="form-help">The dancer's stage name or nickname</small>
</div>

<div class="form-group">
  <label for="email" class="form-label">Email <span class="required">*</span></label>
  <input type="email"
         id="email"
         name="email"
         required
         class="form-input {% if errors and errors.email %}is-invalid{% endif %}"
         value="{{ email|default('', true) }}">
</div>

<div class="form-group">
  <label for="date_of_birth" class="form-label">Date of Birth <span class="required">*</span></label>
  <input type="date"
         id="date_of_birth"
         name="date_of_birth"
         required
         class="form-input {% if errors and errors.date_of_birth %}is-invalid{% endif %}"
         value="{{ date_of_birth|default('', true) }}">
  <small class="form-help">Must be between 10 and 100 years old</small>
</div>

<div class="form-row">
  <div class="form-group">
    <label for="country" class="form-label">Country</label>
    <input type="text"
           id="country"
           name="country"
           class="form-input"
           value="{{ country|default('', true) }}">
    <small class="form-help">Optional</small>
  </div>
  <div class="form-group">
    <label for="city" class="form-label">City</label>
    <input type="text"
           id="city"
           name="city"
           class="form-input"
           value="{{ city|default('', true) }}">
    <small class="form-help">Optional</small>
  </div>
</div>
```

---

### 4.6 Issue #7: Modal Harmonization (Tournament Create)

**File: `app/templates/components/tournament_create_modal.html`**

Update the form (around line 30):

**Current Code:**
```html
<form method="POST" action="/tournaments/create">
```

**Updated Code:**
```html
<form hx-post="/tournaments/create"
      hx-target="#create-tournament-modal .modal-body"
      hx-swap="innerHTML">
```

Also create form partial for error handling:

**File: `app/templates/components/tournament_create_form_partial.html` (NEW)**

```html
{#
  Tournament Create Form Partial (for HTMX swap)

  Used inside tournament_create_modal.html
  Swapped on validation errors
#}

{% if error %}
<div class="alert alert-danger mb-4">
  <p>{{ error }}</p>
</div>
{% endif %}

<div class="form-group">
  <label for="tournament-name" class="form-label">Tournament Name <span class="required">*</span></label>
  <input type="text"
         id="tournament-name"
         name="name"
         required
         placeholder="e.g., Battle-D Winter 2024"
         class="form-input {% if error %}is-invalid{% endif %}"
         value="{{ name|default('', true) }}"
         autofocus>
  <small class="form-help">Give your tournament a unique, descriptive name</small>
</div>

<div class="alert alert-info">
  <p>
    <strong>Note:</strong> After creating the tournament, you can add categories and register dancers.
    The tournament will start in the <strong>REGISTRATION</strong> phase.
  </p>
</div>
```

Update the modal body to use the partial:

**File: `app/templates/components/tournament_create_modal.html`**

Replace the modal-body content with:

```html
<div class="modal-body">
  {% include "components/tournament_create_form_partial.html" %}
</div>
```

---

### 4.7 Issue #1: Three Dots Menu

**File: `app/templates/tournaments/list.html`**

Replace the static button (lines 46-52) with dropdown:

```html
<div class="dropdown">
    <button type="button"
            class="btn-actions dropdown-trigger"
            aria-label="More options"
            aria-expanded="false"
            onclick="toggleDropdown(this)">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="1"/>
            <circle cx="12" cy="5" r="1"/>
            <circle cx="12" cy="19" r="1"/>
        </svg>
    </button>
    <div class="dropdown-menu">
        <a href="/tournaments/{{ tournament.id }}" class="dropdown-item">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
            </svg>
            View
        </a>
        <button type="button"
                class="dropdown-item"
                onclick="openRenameModal('{{ tournament.id }}', '{{ tournament.name|e }}')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            </svg>
            Rename
        </button>
        {% if tournament.status.value == 'created' %}
        <div class="dropdown-divider"></div>
        <button type="button"
                class="dropdown-item dropdown-item-danger"
                onclick="openDeleteModal('delete-tournament-{{ tournament.id }}')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/>
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
            Delete
        </button>
        {% endif %}
    </div>
</div>
```

Add JavaScript at end of file (before `{% endblock %}`):

```html
{# Include rename modal #}
{% include "components/rename_modal.html" %}

{# Delete modals for each tournament #}
{% for tournament in tournaments %}
    {% if tournament.status.value == 'created' %}
        {% set modal_id = "delete-tournament-" ~ tournament.id %}
        {% set item_name = tournament.name %}
        {% set delete_url = "/tournaments/" ~ tournament.id ~ "/delete" %}
        {% set warning_message = "This will permanently delete the tournament and all its data." %}
        {% include "components/delete_modal.html" %}
    {% endif %}
{% endfor %}

<script>
function toggleDropdown(trigger) {
    const dropdown = trigger.closest('.dropdown');
    const wasOpen = dropdown.classList.contains('is-open');

    // Close all other dropdowns first
    document.querySelectorAll('.dropdown.is-open').forEach(d => {
        d.classList.remove('is-open');
        d.querySelector('.dropdown-trigger').setAttribute('aria-expanded', 'false');
    });

    // Toggle this one
    if (!wasOpen) {
        dropdown.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');

        // Close when clicking outside
        const closeHandler = (e) => {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('is-open');
                trigger.setAttribute('aria-expanded', 'false');
                document.removeEventListener('click', closeHandler);
            }
        };
        setTimeout(() => document.addEventListener('click', closeHandler), 0);
    }
}

function openRenameModal(tournamentId, currentName) {
    const modal = document.getElementById('rename-modal');
    const form = modal.querySelector('form');
    const input = modal.querySelector('#new-name');

    // Update form action and input value
    form.setAttribute('hx-post', '/tournaments/' + tournamentId + '/rename');
    htmx.process(form);  // Re-process HTMX attributes
    input.value = currentName;

    modal.showModal();
}
</script>
```

**File: `app/templates/components/rename_modal.html` (NEW)**

```html
{#
  Rename Modal Component

  Usage:
    {% include "components/rename_modal.html" %}

  Opens via JavaScript:
    openRenameModal(tournamentId, currentName)

  CSS: Uses classes from components/_modals.scss
#}

<dialog id="rename-modal" class="modal" aria-labelledby="rename-modal-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="rename-modal-title" class="modal-title">Rename Tournament</h3>
      <button type="button"
              class="modal-close"
              aria-label="Close"
              onclick="document.getElementById('rename-modal').close()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <form hx-post="/tournaments/placeholder/rename"
          hx-swap="none">
      <div class="modal-body">
        <div class="form-group">
          <label for="new-name" class="form-label">New Name <span class="required">*</span></label>
          <input type="text"
                 id="new-name"
                 name="name"
                 required
                 class="form-input"
                 autofocus>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button"
                class="btn btn-secondary"
                onclick="document.getElementById('rename-modal').close()">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Rename
        </button>
      </div>
    </form>
  </div>
</dialog>

<script>
  document.getElementById('rename-modal').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  });

  document.getElementById('rename-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      this.close();
    }
  });
</script>
```

---

### 4.8 Components to Reuse

**From FRONTEND.md Component Library:**
- `delete_modal.html`: Pattern for tournament deletion (already exists)
- `tournament_create_modal.html`: Base pattern for other modals (update to HTMX)
- `empty_state.html`: Already centered (minor SVG fix)
- `loading.html`: For HTMX indicators

**From SCSS Component Library:**
- `_dropdown.scss`: Complete dropdown styles (`.dropdown`, `.dropdown-menu`, `.dropdown-item`, `.btn-actions`)
- `_modals.scss`: Modal structure and variants
- `_buttons.scss`: Button variants
- `_badges.scss`: Status badges

### 4.9 HTMX Patterns Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| Form with HX-Redirect | Modal create forms | `hx-post` + server returns `HX-Redirect` header |
| Target swap for errors | Validation | `hx-target="#modal .modal-body"` + `hx-swap="innerHTML"` |
| Delete with confirm | Category removal | `hx-delete` + `hx-confirm` + `hx-swap="delete"` |

**Backend Pattern (Standard):**
```python
if is_htmx:
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/redirect-url"
    return response
```

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- Section: Category Entity
- Change: Update deletion rule
- OLD: "Can Delete When = No performers registered"
- NEW: "Can Delete When = Tournament in REGISTRATION phase. CASCADE deletes Performers, preserves Dancers."

### Level 3: Operational

**FRONTEND.md - Component Library Section:**
Add:
- Dropdown Menu component documentation
- Rename Modal component documentation
- HTMX Modal Pattern (with HX-Redirect)

---

## 6. Testing Plan

### Unit Tests

**tests/test_tournaments.py:**
```python
async def test_delete_category_success():
    """Can delete empty category in REGISTRATION phase."""

async def test_delete_category_with_performers_cascades():
    """Deleting category with performers CASCADE deletes performers."""

async def test_delete_category_wrong_phase_fails():
    """Cannot delete category after REGISTRATION phase."""

async def test_rename_tournament_success():
    """Can rename tournament at any status."""

async def test_rename_tournament_active():
    """Can rename ACTIVE tournament."""

async def test_advance_phase_success():
    """Admin can advance from REGISTRATION to PRESELECTION."""

async def test_advance_phase_non_admin_fails():
    """Non-admin cannot advance phase."""
```

### Integration/E2E Tests

**tests/e2e/test_ux_issues_batch.py:**
```python
class TestUXIssuesBatch:
    """Test all 7 UX issues from the batch."""

    def test_modal_centering_css(self, client):
        """Issue #5: Verify CSS includes margin: auto for modals."""
        # Read compiled CSS and verify .modal has margin: auto

    def test_empty_state_svg_centered(self, client):
        """Issue #2: Verify SVG has display: block."""
        # Read compiled CSS and verify svg has display: block

    def test_phase_advancement_button_admin_only(self, client, admin_user):
        """Issue #6: Admin sees advance button on tournament detail."""
        # Login as admin, view tournament detail, assert button visible

    def test_phase_advancement_button_hidden_staff(self, client, staff_user):
        """Issue #6: Staff does not see advance button."""
        # Login as staff, view tournament detail, assert button not visible

    def test_category_removal_htmx(self, client, admin_user):
        """Issue #3: Can remove category via HTMX."""
        # Create tournament with category, delete via HTMX, verify removed

    def test_category_removal_cascades_performers(self, client, admin_user):
        """Issue #3: Performer records are CASCADE deleted."""
        # Create tournament, category, register performer, delete category
        # Verify performer record deleted but dancer profile exists

    def test_user_create_modal_htmx(self, client, admin_user):
        """Issue #4: User creation via modal with HTMX."""
        # Open modal, submit form, verify HX-Redirect

    def test_dancer_create_modal_htmx(self, client, staff_user):
        """Issue #4: Dancer creation via modal with HTMX."""
        # Open modal, submit form, verify HX-Redirect

    def test_tournament_dropdown_menu(self, client, staff_user):
        """Issue #1: Tournament cards have working dropdown."""
        # Verify dropdown structure exists in template

    def test_rename_modal_any_status(self, client, admin_user):
        """Issue #1: Can rename tournament at any status."""
        # Create ACTIVE tournament, rename it, verify success
```

### Manual Testing Checklist

**Browser Testing:**
- [ ] Modal centering in Chrome
- [ ] Modal centering in Firefox
- [ ] Modal centering in Safari
- [ ] Dropdown opens and closes correctly
- [ ] Dropdown closes on outside click
- [ ] Empty state icon centered in search results

**Functionality Testing:**
- [ ] Phase advance button shows for admin only
- [ ] Phase advance shows correct preview data
- [ ] Phase advance redirects to event mode
- [ ] Category remove works (HTMX in-place)
- [ ] Category remove cascades performers
- [ ] User create modal opens and submits
- [ ] User create shows validation errors in modal
- [ ] Dancer create modal opens and submits
- [ ] Three dots View action navigates correctly
- [ ] Three dots Rename opens modal
- [ ] Three dots Delete shows confirmation (CREATED only)

---

## 7. Risk Analysis

### Risk 1: Modal Centering Browser Compatibility
**Concern:** `<dialog>` element behavior varies between browsers
**Likelihood:** Low (well-supported in modern browsers)
**Impact:** High (affects all modals)
**Mitigation:**
- Test in Chrome, Firefox, Safari
- The `margin: auto` fix is standard CSS

### Risk 2: HTMX Form Submission Errors
**Concern:** Form errors in modals need proper display
**Likelihood:** Medium
**Impact:** Medium (poor UX on error)
**Mitigation:**
- Return full form partial with errors (not just error message)
- Use `hx-swap="innerHTML"` on modal body
- Test error scenarios thoroughly

### Risk 3: Dropdown Click Outside Detection
**Concern:** JavaScript click-outside handler could conflict with HTMX
**Likelihood:** Low
**Impact:** Low (dropdown stays open)
**Mitigation:**
- Use simple vanilla JS pattern
- Clean up event listener on close
- Test with HTMX interactions

### Risk 4: Category CASCADE Deletion
**Concern:** User might not realize performers will be deleted
**Likelihood:** Medium (user confirmed simple confirmation is OK)
**Impact:** Medium (data loss)
**Mitigation:**
- Use `hx-confirm` with performer count in message
- Per BR-UX-003: User wants simple confirmation, not detailed warning

### Risk 5: Deprecating /event/advance Endpoint
**Concern:** Old endpoint might be called from somewhere
**Likelihood:** Low (only UI calls it)
**Impact:** Medium (broken functionality)
**Mitigation:**
- Keep old endpoint working (mark deprecated in code comment)
- New endpoint at `/tournaments/` handles advancement
- Remove old endpoint in future cleanup PR

---

## 8. Implementation Order

**Recommended sequence (dependency-based):**

### Phase 1: CSS Fixes (No Dependencies) - ~30 min
1. **Issue #5: Modal Centering**
   - Edit `app/static/scss/components/_modals.scss`
   - Add `margin: auto;` to `.modal` class
   - Compile: `sass app/static/scss:app/static/css`
   - Test in browser

2. **Issue #2: Empty State Alignment**
   - Edit `app/static/scss/components/_empty-state.scss`
   - Add `display: block;` to `.empty-state-icon svg`
   - Compile CSS
   - Test with search no results

### Phase 2: Critical Functionality - ~2 hours
3. **Issue #6: Phase Advancement UI**
   - Add button to `tournaments/detail.html`
   - Create `components/phase_advance_modal.html`
   - Add `POST /tournaments/{id}/advance` endpoint
   - Test phase advancement flow

### Phase 3: Medium Priority - ~3 hours
4. **Issue #3: Category Removal**
   - Add `DELETE /tournaments/{id}/categories/{cat_id}` endpoint
   - Update `tournaments/detail.html` Actions column with HTMX delete
   - Test CASCADE deletion behavior

5. **Issue #7: Modal Harmonization**
   - Update `tournament_create_modal.html` to use HTMX
   - Create `tournament_create_form_partial.html`
   - Update `POST /tournaments/create` to return HX-Redirect
   - Test create flow

6. **Issue #4: Creation Form Modals**
   - Create `user_create_modal.html` + form partial
   - Create `dancer_create_modal.html` + form partial
   - Update `admin/users.html` to use modal
   - Update `dancers/list.html` to use modal
   - Update backend endpoints for HX-Redirect
   - Test both creation flows

### Phase 4: Polish - ~1.5 hours
7. **Issue #1: Three Dots Menu**
   - Add dropdown structure to `tournaments/list.html`
   - Create `components/rename_modal.html`
   - Add `POST /tournaments/{id}/rename` endpoint
   - Add JavaScript for dropdown toggle
   - Test View, Rename, Delete actions

### Phase 5: Testing & Documentation - ~1 hour
8. Write `tests/e2e/test_ux_issues_batch.py`
9. Update documentation (DOMAIN_MODEL.md, FRONTEND.md)
10. Manual testing across browsers

---

## 9. Technical POC

**Status:** Not required
**Reason:** All implementations use existing, proven patterns:
- Modal pattern already exists (`tournament_create_modal.html`, `delete_modal.html`)
- Dropdown CSS already complete (`_dropdown.scss`)
- HTMX form submission pattern already used in codebase
- Backend route patterns follow existing conventions
- No new technologies or integrations

---

## 10. Open Questions

All questions have been resolved via feature spec:

- [x] Three dots menu options → View, Rename, Delete (not full Edit)
- [x] Rename availability → ALWAYS allowed (any status)
- [x] Phase advancement confirmation → Detailed preview
- [x] Phase advancement endpoint → NEW at `/tournaments/{id}/advance`
- [x] Category deletion behavior → CASCADE delete Performers, preserve Dancers
- [x] Category deletion confirmation → Simple (hx-confirm with performer count)
- [x] Modal submission pattern → HTMX + HX-Redirect for ALL modals
- [x] Harmonize existing modals → Yes, update tournament create too
- [x] Keep full-page forms as fallback → Yes, modals are enhancement

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order

---

## 12. Estimated Files to Create/Modify

### New Files (9):
1. `app/templates/components/phase_advance_modal.html`
2. `app/templates/components/user_create_modal.html`
3. `app/templates/components/user_create_form_partial.html`
4. `app/templates/components/dancer_create_modal.html`
5. `app/templates/components/dancer_create_form_partial.html`
6. `app/templates/components/tournament_create_form_partial.html`
7. `app/templates/components/rename_modal.html`
8. `tests/e2e/test_ux_issues_batch.py`

### Modified Files - SCSS (2):
1. `app/static/scss/components/_modals.scss` - Add `margin: auto;`
2. `app/static/scss/components/_empty-state.scss` - Add `display: block;` to SVG

### Modified Files - Templates (5):
3. `app/templates/tournaments/list.html` - Add dropdown menu
4. `app/templates/tournaments/detail.html` - Add phase advance + category remove
5. `app/templates/admin/users.html` - Change create to modal trigger
6. `app/templates/dancers/list.html` - Change create to modal trigger
7. `app/templates/components/tournament_create_modal.html` - Convert to HTMX

### Modified Files - Backend (3):
8. `app/routers/tournaments.py` - Add category delete, rename, advance endpoints; update create
9. `app/routers/admin.py` - Update user create for HTMX
10. `app/routers/dancers.py` - Update dancer create for HTMX

### Build Step Required
After modifying SCSS files:
```bash
sass app/static/scss:app/static/css
```

---

## 13. Quality Gate Checklist

Before marking implementation complete:

**Technical Design:**
- [x] All affected files identified (backend, frontend, SCSS, tests, docs)
- [x] Backend patterns chosen (existing route/repo patterns, HTMX redirect)
- [x] Frontend patterns chosen (existing modal/dropdown/HTMX patterns)
- [x] Database changes planned (none needed - CASCADE already configured)
- [x] Documentation updates planned (DOMAIN_MODEL.md, FRONTEND.md)

**Technical Risk Validation:**
- [x] Technical risks identified (5 risks documented with mitigations)
- [x] POC status documented (not required - standard patterns)

**Risk Analysis:**
- [x] Breaking changes identified (none - additive + HTMX enhancement)
- [x] Performance concerns documented (none - no new queries)
- [x] Each risk has mitigation plan

**User Validation:**
- [x] Open questions resolved via feature spec
- [ ] User approved technical approach
- [ ] User confirmed implementation order

---

**End of Implementation Plan**
