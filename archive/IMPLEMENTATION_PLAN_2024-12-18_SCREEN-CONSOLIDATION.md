# Implementation Plan: Screen Consolidation - Phases & Battles

**Date:** 2024-12-18
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2024-12-18_SCREEN-CONSOLIDATION.md

---

## 1. Summary

**Feature:** Remove redundant Battles List and Phases Overview screens, consolidate into Event Mode
**Approach:**
- Delete `/battles` list route (keep detail/encode/start routes used by Event Mode)
- Delete `/tournaments/{id}/phase` overview route
- Move phase advancement to Event Mode command center
- Update all navigation links to use Event Mode instead

---

## 2. Affected Files

### Backend - DELETE

| File | Action | Reason |
|------|--------|--------|
| `app/routers/phases.py` | **DELETE ENTIRE FILE** | Both routes removed - advance moves to event.py |
| `app/templates/phases/overview.html` | **DELETE** | Overview screen removed |
| `app/templates/phases/confirm_advance.html` | **MOVE** to `app/templates/event/` | Needed for advance in Event Mode |
| `app/templates/phases/validation_errors.html` | **MOVE** to `app/templates/event/` | Needed for advance in Event Mode |
| `app/templates/battles/list.html` | **DELETE** | List screen removed |

### Backend - EDIT

| File | Action | Details |
|------|--------|---------|
| `app/routers/battles.py` | **EDIT** | Remove `list_battles` route (lines 33-87), keep all other routes |
| `app/routers/event.py` | **EDIT** | Add phase advance route + button |
| `app/main.py` | **EDIT** | Remove `phases` router include |

### Frontend - EDIT

| File | Action | Details |
|------|--------|---------|
| `app/templates/base.html:183-186` | **EDIT** | Remove "Phases" and "Battle Queue" sidebar links |
| `app/templates/dashboard/_event_active.html:12-13` | **EDIT** | Remove "Battle Queue" and "Phase Management" links |
| `app/templates/dashboard/_event_active.html:23` | **EDIT** | Remove second "Battle Queue" link |
| `app/templates/dashboard/_registration_mode.html:11` | **EDIT** | Remove "Manage Phases" link |
| `app/templates/tournaments/detail.html:43` | **EDIT** | Remove "Manage Phase" button |
| `app/templates/pools/overview.html:86` | **EDIT** | Change `/battles?category_id=` to Event Mode link |
| `app/templates/event/command_center.html` | **EDIT** | Add phase advance section |
| `app/templates/event/_phase_progress.html` | **EDIT** | Add "Advance Phase" button for admins |

### Tests - DELETE/UPDATE

| File | Action | Details |
|------|--------|---------|
| `tests/test_phases_routes.py` | **DELETE** | Routes being tested no longer exist |
| `tests/e2e/test_ux_consistency.py` | **UPDATE** | May reference deleted routes |
| `tests/e2e/test_event_mode.py` | **UPDATE** | Add tests for phase advance in Event Mode |
| `tests/e2e/test_tournament_management.py` | **UPDATE** | May reference deleted routes |
| `tests/test_permissions.py` | **UPDATE** | May test phase/battle routes |

---

## 3. Backend Implementation Plan

### 3.1 Remove Phases Router

**File:** `app/main.py`

```python
# REMOVE this line:
app.include_router(phases.router)

# REMOVE this import:
from app.routers import phases
```

**File:** `app/routers/phases.py`
- **DELETE ENTIRE FILE**

### 3.2 Remove Battles List Route

**File:** `app/routers/battles.py`

Remove lines 33-87 (the `list_battles` function). Keep all other routes:
- `GET /battles/{battle_id}` - detail
- `POST /battles/{battle_id}/start` - start
- `GET /battles/{battle_id}/encode` - encode form
- `POST /battles/{battle_id}/encode` - encode submit
- `GET /battles/queue/{category_id}` - queue partial
- `POST /battles/{battle_id}/reorder` - reorder

### 3.3 Add Phase Advance to Event Router

**File:** `app/routers/event.py`

Add new route (import from phases.py before deleting):

```python
from app.models.tournament import TournamentPhase
from app.utils.flash import add_flash_message
from app.exceptions import ValidationError
from fastapi import Form

@router.post("/{tournament_id}/advance")
async def advance_tournament_phase(
    tournament_id: str,
    request: Request,
    confirmed: bool = Form(False),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    tournament_repo: TournamentRepository = Depends(get_tournament_repo),
):
    """Advance tournament to next phase.

    Two-step process:
    1. First request: Validate and show confirmation dialog
    2. Second request (confirmed=True): Actually advance phase

    Only admins can advance phases.
    """
    from app.dependencies import require_admin, get_tournament_service
    require_admin(current_user)

    try:
        tournament_uuid = uuid.UUID(tournament_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tournament ID",
        )

    tournament = await tournament_repo.get_by_id(tournament_uuid)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Get tournament service for validation and advancement
    tournament_service = await get_tournament_service(...)  # Dependency injection

    if not confirmed:
        # Show confirmation dialog
        validation_result = await tournament_service.get_phase_validation(tournament_uuid)

        if not validation_result:
            return templates.TemplateResponse(
                request=request,
                name="event/_validation_errors.html",
                context={
                    "current_user": current_user,
                    "tournament": tournament,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        next_phase = TournamentPhase.get_next_phase(tournament.phase)
        return templates.TemplateResponse(
            request=request,
            name="event/_confirm_advance.html",
            context={
                "current_user": current_user,
                "tournament": tournament,
                "from_phase": tournament.phase,
                "to_phase": next_phase,
                "warnings": validation_result.warnings,
            },
        )

    # Confirmed - advance phase
    try:
        tournament = await tournament_service.advance_tournament_phase(tournament_uuid)
        add_flash_message(request, "Phase advanced successfully", "success")
        return RedirectResponse(
            url=f"/event/{tournament_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except ValidationError as e:
        add_flash_message(request, f"Cannot advance: {', '.join(e.errors)}", "error")
        return RedirectResponse(
            url=f"/event/{tournament_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
```

---

## 4. Frontend Implementation Plan

### 4.1 Update Sidebar Navigation

**File:** `app/templates/base.html`

Remove lines 183-186:
```html
<!-- DELETE THESE LINES -->
<li><a href="/tournaments/{{ active_tournament.id }}/phase">Phases</a></li>
{% if current_user.is_mc or current_user.is_admin %}
<li><a href="/battles">Battle Queue</a></li>
{% endif %}
```

### 4.2 Update Dashboard Links

**File:** `app/templates/dashboard/_event_active.html`

Replace "Battle Queue" and "Phase Management" links with Event Mode:
```html
<!-- Line 12-13: REPLACE -->
<a href="/event/{{ dashboard.tournament.id }}" role="button">Event Mode</a>
<!-- Remove Phase Management link entirely -->

<!-- Line 23: REPLACE -->
<a href="/event/{{ dashboard.tournament.id }}" role="button">Event Mode</a>
```

**File:** `app/templates/dashboard/_registration_mode.html`

Line 11 - Remove "Manage Phases" link or replace with:
```html
<!-- REMOVE or keep only if admin needs phase advance during registration -->
```

### 4.3 Update Tournament Detail

**File:** `app/templates/tournaments/detail.html`

Line 43 - Remove "Manage Phase" button:
```html
<!-- DELETE -->
<a href="/tournaments/{{ tournament.id }}/phase" role="button" class="secondary">
    Manage Phase
</a>
```

### 4.4 Add Phase Advance to Event Mode

**File:** `app/templates/event/_phase_progress.html`

Add advance button for admins:
```html
<!-- Phase Progress -->
<div class="progress-container">
    <div class="progress-header">
        <h3>Phase Progress</h3>
        <span class="progress-text">{{ progress.completed }}/{{ progress.total }} battles completed</span>
    </div>
    <progress value="{{ progress.completed }}" max="{{ progress.total }}"></progress>
    <div class="progress-percentage">{{ progress.percentage }}%</div>

    <!-- NEW: Phase Advance Button (Admin Only) -->
    {% if current_user.is_admin and progress.can_advance %}
    <div class="phase-advance-section" style="margin-top: 1rem;">
        <form action="/event/{{ tournament_id }}/advance" method="post"
              hx-post="/event/{{ tournament_id }}/advance"
              hx-target="#advance-modal"
              hx-swap="innerHTML">
            <button type="submit" class="secondary">
                Advance to {{ progress.next_phase }}
            </button>
        </form>
    </div>
    {% endif %}
</div>

<!-- Modal for confirmation -->
<div id="advance-modal"></div>
```

**New File:** `app/templates/event/_confirm_advance.html`
(Move from phases/confirm_advance.html, update form action)

**New File:** `app/templates/event/_validation_errors.html`
(Move from phases/validation_errors.html, update for HTMX partial)

### 4.5 Update Pools Overview Link

**File:** `app/templates/pools/overview.html`

Line 86 - Change battle link to Event Mode:
```html
<!-- REPLACE -->
<a href="/battles?category_id={{ pool.category_id }}" ...>
<!-- WITH -->
<a href="/event/{{ tournament.id }}?category_id={{ pool.category_id }}" ...>
```

---

## 5. Testing Plan - 95%+ Coverage Requirement

### 5.0 Coverage Policy

**MANDATORY:** All changes must achieve 95%+ test coverage before merge.

**Pre-implementation baseline:**
- Current tests: 527
- Battle routes coverage: 22% (must preserve existing behavior)
- Phase routes coverage: ~50% (moving to event.py)

**Post-implementation targets:**
- New `event.py` advance route: 100% coverage
- Preserved `battles.py` routes: 95%+ coverage
- Removed routes: 100% verified returning 404
- All templates: functional regression tests

### 5.1 Functional Behaviors to PRESERVE (Regression Tests)

These behaviors MUST continue working after changes. Each requires explicit test:

#### Battle Routes (KEEP - Used by Event Mode)

| Route | Behavior | Test Required |
|-------|----------|---------------|
| `GET /battles/{id}` | Returns battle detail page | `test_battle_detail_returns_200` |
| `GET /battles/{id}` | 404 if battle not found | `test_battle_detail_404_not_found` |
| `GET /battles/{id}` | 401 if not authenticated | `test_battle_detail_requires_auth` |
| `GET /battles/{id}` | Staff-only access | `test_battle_detail_requires_staff` |
| `POST /battles/{id}/start` | Changes status PENDING→ACTIVE | `test_start_battle_changes_status` |
| `POST /battles/{id}/start` | Error if not PENDING | `test_start_battle_rejects_non_pending` |
| `POST /battles/{id}/start` | 404 if battle not found | `test_start_battle_404_not_found` |
| `POST /battles/{id}/start` | Redirects to detail | `test_start_battle_redirects` |
| `GET /battles/{id}/encode` | Returns preselection form | `test_encode_form_preselection` |
| `GET /battles/{id}/encode` | Returns pool form | `test_encode_form_pool` |
| `GET /battles/{id}/encode` | Returns tiebreak form | `test_encode_form_tiebreak` |
| `GET /battles/{id}/encode` | Returns finals form | `test_encode_form_finals` |
| `POST /battles/{id}/encode` | Encodes preselection scores | `test_encode_preselection_scores` |
| `POST /battles/{id}/encode` | Encodes pool win/draw/loss | `test_encode_pool_result` |
| `POST /battles/{id}/encode` | Encodes tiebreak winner | `test_encode_tiebreak_winner` |
| `POST /battles/{id}/encode` | Validation errors shown | `test_encode_validation_errors` |
| `GET /battles/queue/{cat_id}` | Returns ordered queue | `test_battle_queue_ordered` |
| `GET /battles/queue/{cat_id}` | Shows active battle | `test_battle_queue_shows_active` |
| `POST /battles/{id}/reorder` | Reorders queue position | `test_reorder_battle_success` |
| `POST /battles/{id}/reorder` | HTMX returns partial | `test_reorder_htmx_partial` |
| `POST /battles/{id}/reorder` | Validation errors | `test_reorder_validation_error` |

#### Phase Advancement (MOVE to Event Mode)

| Original Route | New Route | Behavior | Test Required |
|----------------|-----------|----------|---------------|
| `POST /tournaments/{id}/advance` | `POST /event/{id}/advance` | Shows confirmation first | `test_advance_shows_confirmation` |
| `POST /tournaments/{id}/advance` | `POST /event/{id}/advance` | Validates before advance | `test_advance_validates_requirements` |
| `POST /tournaments/{id}/advance` | `POST /event/{id}/advance` | Actually advances phase | `test_advance_changes_phase` |
| `POST /tournaments/{id}/advance` | `POST /event/{id}/advance` | Admin-only | `test_advance_requires_admin` |
| `POST /tournaments/{id}/advance` | `POST /event/{id}/advance` | Shows validation errors | `test_advance_shows_errors` |

### 5.2 Tests to DELETE

**File:** `tests/test_phases_routes.py`
- DELETE ENTIRE FILE after implementing replacement tests in event mode

### 5.3 Tests to CREATE

#### File: `tests/e2e/test_screen_consolidation.py`

```python
"""Tests for screen consolidation - 95%+ coverage required.

Verifies:
1. Removed routes return 404
2. Preserved routes still work
3. Phase advance moved to Event Mode
4. Navigation links updated
"""
import pytest
import uuid
from fastapi.testclient import TestClient


class TestRemovedRoutes:
    """Verify deprecated routes are properly removed."""

    def test_battles_list_returns_404(self, unauthenticated_client):
        """GET /battles should return 404 (not 401)."""
        response = unauthenticated_client.get("/battles")
        assert response.status_code == 404, "Route should be removed, not just protected"

    def test_phase_overview_returns_404(self, unauthenticated_client):
        """GET /tournaments/{id}/phase should return 404."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/tournaments/{fake_id}/phase")
        assert response.status_code == 404

    def test_old_advance_route_returns_404(self, unauthenticated_client):
        """POST /tournaments/{id}/advance should return 404."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/tournaments/{fake_id}/advance")
        assert response.status_code == 404


class TestPreservedBattleRoutes:
    """Verify battle detail/encode/start routes still work."""

    def test_battle_detail_requires_auth(self, unauthenticated_client):
        """GET /battles/{id} requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/battles/{fake_id}")
        assert response.status_code == 401

    def test_battle_start_requires_auth(self, unauthenticated_client):
        """POST /battles/{id}/start requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/battles/{fake_id}/start")
        assert response.status_code == 401

    def test_battle_encode_form_requires_auth(self, unauthenticated_client):
        """GET /battles/{id}/encode requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/battles/{fake_id}/encode")
        assert response.status_code == 401

    def test_battle_encode_submit_requires_auth(self, unauthenticated_client):
        """POST /battles/{id}/encode requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/battles/{fake_id}/encode")
        assert response.status_code == 401

    def test_battle_queue_requires_auth(self, unauthenticated_client):
        """GET /battles/queue/{category_id} requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/battles/queue/{fake_id}")
        assert response.status_code == 401

    def test_battle_reorder_requires_auth(self, unauthenticated_client):
        """POST /battles/{id}/reorder requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/battles/{fake_id}/reorder")
        assert response.status_code == 401


class TestEventModePhaseAdvance:
    """Test phase advancement from Event Mode."""

    def test_advance_route_exists(self, unauthenticated_client):
        """POST /event/{id}/advance should exist (return 401, not 404)."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/event/{fake_id}/advance")
        # Should require auth (401), not be missing (404)
        assert response.status_code == 401

    def test_advance_requires_admin(self, mc_client, tournament_in_preselection):
        """MC cannot advance phases - admin only."""
        response = mc_client.post(
            f"/event/{tournament_in_preselection.id}/advance"
        )
        assert response.status_code == 403  # Forbidden for MC

    def test_advance_shows_confirmation(self, admin_client, tournament_ready_to_advance):
        """First POST shows confirmation dialog, not immediate advance."""
        response = admin_client.post(
            f"/event/{tournament_ready_to_advance.id}/advance"
        )
        assert response.status_code == 200
        assert "confirm" in response.text.lower() or "warning" in response.text.lower()

    def test_advance_with_confirmation(self, admin_client, tournament_ready_to_advance):
        """POST with confirmed=true advances the phase."""
        response = admin_client.post(
            f"/event/{tournament_ready_to_advance.id}/advance",
            data={"confirmed": "true"}
        )
        assert response.status_code == 303  # Redirect
        # Verify phase changed
        # ...

    def test_advance_validation_errors(self, admin_client, tournament_not_ready):
        """Advance blocked when validation fails."""
        response = admin_client.post(
            f"/event/{tournament_not_ready.id}/advance"
        )
        assert response.status_code == 400
        assert "error" in response.text.lower()


class TestNavigationLinksRemoved:
    """Verify old navigation links no longer appear."""

    def test_sidebar_no_phases_link(self, staff_client, active_tournament):
        """Sidebar should NOT have link to /phase."""
        response = staff_client.get("/overview")
        assert f"/tournaments/{active_tournament.id}/phase" not in response.text

    def test_sidebar_no_battles_link(self, staff_client, active_tournament):
        """Sidebar should NOT have link to /battles."""
        response = staff_client.get("/overview")
        # Check for the exact broken link pattern
        assert 'href="/battles"' not in response.text

    def test_dashboard_no_phase_management_button(self, admin_client, active_tournament):
        """Dashboard should NOT have 'Phase Management' button."""
        response = admin_client.get("/overview")
        assert "Phase Management" not in response.text

    def test_tournament_detail_no_manage_phase(self, admin_client, tournament):
        """Tournament detail should NOT have 'Manage Phase' button."""
        response = admin_client.get(f"/tournaments/{tournament.id}")
        # Check exact pattern that was removed
        assert f"/tournaments/{tournament.id}/phase" not in response.text
```

#### File: `tests/e2e/test_battle_routes_regression.py`

```python
"""Regression tests for battle routes - ensures nothing breaks.

These tests verify the EXACT behavior of routes we're keeping.
Any change to these behaviors is a regression.
"""
import pytest
import uuid
from decimal import Decimal


class TestBattleDetailRoute:
    """GET /battles/{id} - Battle detail page."""

    async def test_returns_battle_info(self, staff_client, battle_in_db):
        """Detail page shows battle information."""
        response = staff_client.get(f"/battles/{battle_in_db.id}")
        assert response.status_code == 200
        assert str(battle_in_db.id) in response.text

    async def test_returns_404_for_missing_battle(self, staff_client):
        """Returns 404 for non-existent battle."""
        fake_id = uuid.uuid4()
        response = staff_client.get(f"/battles/{fake_id}")
        assert response.status_code == 404

    async def test_shows_performers(self, staff_client, battle_with_performers):
        """Detail page shows performers in battle."""
        response = staff_client.get(f"/battles/{battle_with_performers.id}")
        assert response.status_code == 200
        for performer in battle_with_performers.performers:
            assert performer.dancer.blaze in response.text


class TestBattleStartRoute:
    """POST /battles/{id}/start - Start a battle."""

    async def test_starts_pending_battle(self, staff_client, pending_battle):
        """Starting a pending battle changes status to ACTIVE."""
        response = staff_client.post(f"/battles/{pending_battle.id}/start")
        assert response.status_code == 303  # Redirect

        # Verify status changed
        detail = staff_client.get(f"/battles/{pending_battle.id}")
        assert "ACTIVE" in detail.text

    async def test_rejects_active_battle(self, staff_client, active_battle):
        """Cannot start an already active battle."""
        response = staff_client.post(f"/battles/{active_battle.id}/start")
        assert response.status_code == 303  # Still redirects
        # But with error flash message
        detail = staff_client.get(f"/battles/{active_battle.id}")
        assert "Cannot start battle" in detail.text or "error" in detail.text.lower()

    async def test_rejects_completed_battle(self, staff_client, completed_battle):
        """Cannot start a completed battle."""
        response = staff_client.post(f"/battles/{completed_battle.id}/start")
        assert response.status_code == 303
        detail = staff_client.get(f"/battles/{completed_battle.id}")
        assert "Cannot start battle" in detail.text or "error" in detail.text.lower()


class TestBattleEncodeFormRoute:
    """GET /battles/{id}/encode - Encode form display."""

    async def test_preselection_battle_shows_score_form(
        self, staff_client, preselection_battle
    ):
        """Preselection battles show score input form."""
        response = staff_client.get(f"/battles/{preselection_battle.id}/encode")
        assert response.status_code == 200
        assert "score" in response.text.lower()

    async def test_pool_battle_shows_winner_form(self, staff_client, pool_battle):
        """Pool battles show winner selection form."""
        response = staff_client.get(f"/battles/{pool_battle.id}/encode")
        assert response.status_code == 200
        assert "winner" in response.text.lower() or "draw" in response.text.lower()

    async def test_tiebreak_battle_shows_winner_form(
        self, staff_client, tiebreak_battle
    ):
        """Tiebreak battles show winner selection (no draw)."""
        response = staff_client.get(f"/battles/{tiebreak_battle.id}/encode")
        assert response.status_code == 200
        assert "winner" in response.text.lower()


class TestBattleEncodeSubmitRoute:
    """POST /battles/{id}/encode - Submit battle results."""

    async def test_encode_preselection_scores(
        self, staff_client, preselection_battle_with_performers
    ):
        """Can encode preselection scores."""
        battle = preselection_battle_with_performers
        scores = {
            f"score_{p.id}": "7.5" for p in battle.performers
        }
        response = staff_client.post(
            f"/battles/{battle.id}/encode",
            data=scores
        )
        assert response.status_code == 303  # Redirect on success

    async def test_encode_pool_winner(self, staff_client, pool_battle_with_performers):
        """Can encode pool battle winner."""
        battle = pool_battle_with_performers
        winner = battle.performers[0]
        response = staff_client.post(
            f"/battles/{battle.id}/encode",
            data={"winner_id": str(winner.id)}
        )
        assert response.status_code == 303

    async def test_encode_pool_draw(self, staff_client, pool_battle_with_performers):
        """Can encode pool battle as draw."""
        battle = pool_battle_with_performers
        response = staff_client.post(
            f"/battles/{battle.id}/encode",
            data={"is_draw": "true"}
        )
        assert response.status_code == 303

    async def test_invalid_form_shows_error(self, staff_client, pool_battle):
        """Invalid form data shows error message."""
        response = staff_client.post(
            f"/battles/{pool_battle.id}/encode",
            data={}  # Missing required fields
        )
        # Should redirect back to form with error
        assert response.status_code == 303


class TestBattleQueueRoute:
    """GET /battles/queue/{category_id} - Battle queue partial."""

    async def test_returns_ordered_battles(
        self, staff_client, category_with_pending_battles
    ):
        """Queue returns battles in sequence order."""
        response = staff_client.get(
            f"/battles/queue/{category_with_pending_battles.id}"
        )
        assert response.status_code == 200

    async def test_returns_404_for_missing_category(self, staff_client):
        """Returns 404 for non-existent category."""
        fake_id = uuid.uuid4()
        response = staff_client.get(f"/battles/queue/{fake_id}")
        assert response.status_code == 404


class TestBattleReorderRoute:
    """POST /battles/{id}/reorder - Reorder battle in queue."""

    async def test_reorders_battle(self, staff_client, reorderable_battle):
        """Can reorder a battle to new position."""
        response = staff_client.post(
            f"/battles/{reorderable_battle.id}/reorder",
            data={"new_position": 2}
        )
        assert response.status_code == 303  # Redirect

    async def test_htmx_returns_partial(self, staff_client, reorderable_battle):
        """HTMX request returns partial HTML."""
        response = staff_client.post(
            f"/battles/{reorderable_battle.id}/reorder",
            data={"new_position": 2},
            headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert "_battle_queue" in response.text or "queue" in response.text.lower()
```

### 5.4 Test Fixtures Required

```python
# Add to tests/conftest.py or tests/e2e/conftest.py

@pytest.fixture
def tournament_in_preselection(db_session):
    """Tournament in PRESELECTION phase."""
    ...

@pytest.fixture
def tournament_ready_to_advance(db_session):
    """Tournament with all battles completed, ready for phase advance."""
    ...

@pytest.fixture
def tournament_not_ready(db_session):
    """Tournament with incomplete battles, cannot advance."""
    ...

@pytest.fixture
def pending_battle(db_session):
    """Battle with status PENDING."""
    ...

@pytest.fixture
def active_battle(db_session):
    """Battle with status ACTIVE."""
    ...

@pytest.fixture
def completed_battle(db_session):
    """Battle with status COMPLETED."""
    ...

@pytest.fixture
def preselection_battle(db_session):
    """Battle in PRESELECTION phase."""
    ...

@pytest.fixture
def pool_battle(db_session):
    """Battle in POOLS phase."""
    ...

@pytest.fixture
def tiebreak_battle(db_session):
    """Battle in TIEBREAK phase."""
    ...

@pytest.fixture
def reorderable_battle(db_session):
    """Battle that can be reordered (2+ positions after active)."""
    ...
```

### 5.5 Coverage Verification

**Before implementation:**
```bash
pytest --cov=app/routers/battles --cov=app/routers/phases --cov=app/routers/event \
       --cov-report=term-missing --cov-fail-under=0
```

**After implementation:**
```bash
pytest --cov=app/routers/battles --cov=app/routers/event \
       --cov-report=term-missing --cov-fail-under=95
```

**Coverage gate:** Build MUST fail if coverage < 95%

### 5.6 Tests to UPDATE

**File:** `tests/e2e/test_ux_consistency.py`
- Remove checks for `/battles` and `/phase` links
- Add checks that these links are ABSENT

**File:** `tests/e2e/test_event_mode.py`
- Add phase advance tests
- Update any references to old phase routes

**File:** `tests/test_permissions.py`
- Update route references from `/tournaments/{id}/advance` to `/event/{id}/advance`

---

## 6. Documentation Update Plan

### Level 1: Source of Truth

No changes needed - these are UI/routing changes, not domain model changes.

### Level 2: Derived

**ROADMAP.md:**
- Add Phase 3.11 - Screen Consolidation
- Mark as completed when done

### Level 3: Operational

**FRONTEND.md:**
- Update "Navigation Structure" section
- Remove references to Phases and Battles List screens
- Document Event Mode as single entry point for battle management

---

## 7. Risk Analysis

### Risk 1: Functionality Loss - Phase Advancement
**Concern:** Moving advance to Event Mode might break workflow
**Likelihood:** Low (we're moving, not removing)
**Impact:** High (can't advance tournament)
**Mitigation:**
- Copy code carefully from phases.py
- Test advance flow thoroughly
- Keep validation logic intact

### Risk 2: Broken Battle Links
**Concern:** Templates using `/battles/{id}` might break
**Likelihood:** Low (we're keeping detail routes)
**Impact:** Medium
**Mitigation:**
- Only remove list route (`GET /battles`)
- Keep all `/battles/{id}/*` routes
- Search and verify all template links

### Risk 3: Missing Tests
**Concern:** Some tests might fail after route removal
**Likelihood:** Medium
**Impact:** Low (tests fail, not production)
**Mitigation:**
- Run test suite before merge
- Update failing tests
- Add new tests for removed routes returning 404

### Risk 4: User Confusion During Transition
**Concern:** Users with bookmarks to old URLs
**Likelihood:** Low (internal app)
**Impact:** Low
**Mitigation:**
- Could add redirects from old URLs to Event Mode
- Document changes

---

## 8. Implementation Order - TEST-FIRST APPROACH

**Philosophy:** Write tests BEFORE making changes. Tests act as a safety net.

**Coverage Gate:** 95%+ coverage on affected routes. Build MUST fail otherwise.

---

### PHASE A: Baseline & Safety Net (Before ANY Changes)

#### Step A1: Capture Current Coverage
```bash
# Record current state
pytest --cov=app/routers/battles --cov=app/routers/phases --cov=app/routers/event \
       --cov-report=html --cov-report=term-missing > coverage_baseline.txt
```

#### Step A2: Write Regression Tests for Routes We're KEEPING
**Files to create:**
- `tests/e2e/test_battle_routes_regression.py`

**Tests to write (20+ tests):**
1. `test_battle_detail_returns_200`
2. `test_battle_detail_404_not_found`
3. `test_battle_detail_requires_auth`
4. `test_start_battle_changes_status`
5. `test_start_battle_rejects_non_pending`
6. `test_start_battle_404_not_found`
7. `test_encode_form_preselection`
8. `test_encode_form_pool`
9. `test_encode_form_tiebreak`
10. `test_encode_preselection_scores`
11. `test_encode_pool_winner`
12. `test_encode_pool_draw`
13. `test_encode_validation_errors`
14. `test_battle_queue_ordered`
15. `test_battle_queue_shows_active`
16. `test_battle_queue_404_missing_category`
17. `test_reorder_battle_success`
18. `test_reorder_htmx_partial`
19. `test_reorder_validation_error`
20. `test_reorder_requires_auth`

**Run tests - ALL MUST PASS before proceeding:**
```bash
pytest tests/e2e/test_battle_routes_regression.py -v
```

#### Step A3: Create Required Test Fixtures
Add to `tests/conftest.py`:
- `pending_battle`
- `active_battle`
- `completed_battle`
- `preselection_battle`
- `pool_battle`
- `tiebreak_battle`
- `battle_with_performers`
- `reorderable_battle`
- `category_with_pending_battles`

---

### PHASE B: Build New Before Removing Old

#### Step B1: Move Templates (Zero Risk)
1. Copy `phases/confirm_advance.html` → `event/_confirm_advance.html`
2. Copy `phases/validation_errors.html` → `event/_validation_errors.html`
3. Update form actions to `/event/{id}/advance`
4. **DO NOT DELETE originals yet**

#### Step B2: Write Tests for New Advance Route
**File:** `tests/e2e/test_screen_consolidation.py` - EventModePhaseAdvance class

**Tests to write (5+ tests):**
1. `test_advance_route_exists` (returns 401, not 404)
2. `test_advance_requires_admin`
3. `test_advance_shows_confirmation`
4. `test_advance_with_confirmation`
5. `test_advance_validation_errors`

**Run tests - THEY WILL FAIL (route doesn't exist yet):**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestEventModePhaseAdvance -v
# Expected: 5 FAILED
```

#### Step B3: Implement New Advance Route
1. Add `/event/{id}/advance` route to `event.py`
2. Update `EventService.get_phase_progress()` for `can_advance`, `next_phase`
3. Update `event/_phase_progress.html` with advance button

**Run tests - NOW THEY SHOULD PASS:**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestEventModePhaseAdvance -v
# Expected: 5 PASSED
```

#### Step B4: Verify Both Routes Work
At this point, BOTH old and new advance routes work:
- `POST /tournaments/{id}/advance` (old - still exists)
- `POST /event/{id}/advance` (new - just added)

**Run full test suite:**
```bash
pytest -v
# All 527+ tests should pass
```

---

### PHASE C: Remove Old (Tests Protect Us)

#### Step C1: Write Tests for Removed Routes
**File:** `tests/e2e/test_screen_consolidation.py` - TestRemovedRoutes class

**Tests to write (3+ tests):**
1. `test_battles_list_returns_404`
2. `test_phase_overview_returns_404`
3. `test_old_advance_route_returns_404`

**Run tests - THEY WILL FAIL (routes still exist):**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestRemovedRoutes -v
# Expected: 3 FAILED
```

#### Step C2: Write Tests for Removed Navigation Links
**File:** `tests/e2e/test_screen_consolidation.py` - TestNavigationLinksRemoved class

**Tests to write (4+ tests):**
1. `test_sidebar_no_phases_link`
2. `test_sidebar_no_battles_link`
3. `test_dashboard_no_phase_management_button`
4. `test_tournament_detail_no_manage_phase`

**Run tests - THEY WILL FAIL (links still exist):**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestNavigationLinksRemoved -v
# Expected: 4 FAILED
```

#### Step C3: Remove Old Routes
1. Remove `list_battles` from `battles.py` (lines 33-87)
2. Delete `app/routers/phases.py`
3. Remove phases router from `main.py`

**Run removed route tests - NOW PASS:**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestRemovedRoutes -v
# Expected: 3 PASSED
```

#### Step C4: Update Navigation Links
1. Edit `base.html` - remove sidebar links
2. Edit `dashboard/_event_active.html` - point to Event Mode
3. Edit `dashboard/_registration_mode.html` - remove phase link
4. Edit `tournaments/detail.html` - remove phase button
5. Edit `pools/overview.html` - point to Event Mode

**Run navigation tests - NOW PASS:**
```bash
pytest tests/e2e/test_screen_consolidation.py::TestNavigationLinksRemoved -v
# Expected: 4 PASSED
```

#### Step C5: Delete Old Templates
1. Delete `templates/battles/list.html`
2. Delete `templates/phases/` directory (now empty)

---

### PHASE D: Verify & Clean Up

#### Step D1: Run Full Regression Suite
```bash
pytest tests/e2e/test_battle_routes_regression.py -v
# Expected: 20+ PASSED - nothing broke
```

#### Step D2: Run All Consolidation Tests
```bash
pytest tests/e2e/test_screen_consolidation.py -v
# Expected: 12+ PASSED
```

#### Step D3: Verify 95%+ Coverage
```bash
pytest --cov=app/routers/battles --cov=app/routers/event \
       --cov-report=term-missing --cov-fail-under=95
# Expected: PASSED with 95%+ coverage
```

#### Step D4: Run Full Test Suite
```bash
pytest -v
# Expected: All tests PASS
```

#### Step D5: Clean Up Old Test Files
1. Delete `tests/test_phases_routes.py` (routes gone)
2. Update `tests/e2e/test_ux_consistency.py` if needed
3. Update `tests/test_permissions.py` if references old routes

---

### PHASE E: Documentation

#### Step E1: Update ROADMAP.md
Add Phase 3.11 - Screen Consolidation

#### Step E2: Update FRONTEND.md
- Update Navigation Structure section
- Document Event Mode as single entry point

---

## Implementation Checkpoints

| Checkpoint | Tests Required | Expected Result |
|------------|----------------|-----------------|
| After A2 | Regression tests written | All PASS (current behavior documented) |
| After B2 | New advance tests written | All FAIL (route not yet created) |
| After B3 | New advance route added | All PASS (new route works) |
| After C1 | Removed route tests written | All FAIL (routes still exist) |
| After C3 | Old routes removed | Removed tests PASS, regression PASS |
| After C4 | Navigation updated | Navigation tests PASS |
| After D3 | Coverage check | 95%+ coverage achieved |
| After D4 | Full suite | ALL 540+ tests PASS |

---

## 9. Open Questions

- [x] Where should phase advancement live? → **Event Mode** (user confirmed)
- [x] Should we keep battle detail routes? → **Yes** (used by Event Mode)
- [x] Should we add redirects from old URLs? → **No** (internal app, not needed)

---

## 10. User Approval

- [x] User approved removal of both screens
- [x] User approved adding phase advancement to Event Mode
- [ ] User reviewed implementation plan
- [ ] User confirmed risks acceptable
- [ ] User approved implementation order
