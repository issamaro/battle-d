# Implementation Plan: UX Navigation Redesign

**Date:** 2025-12-07
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-07_UX-NAVIGATION-REDESIGN.md

---

## 1. Summary

**Feature:** Complete UX redesign with context-aware navigation, smart dashboard, event mode command center, and improved registration.

**Approach:**
- Phase 1: Fix broken navigation (remove/redirect 404 links)
- Phase 2: Smart Dashboard (3-state context-aware home)
- Phase 3: Event Mode (full-screen command center)
- Phase 4: Registration UX (two-panel HTMX)

---

## 2. Affected Files

### Backend

**Models:**
- No model changes needed (existing schema sufficient)

**Services:**
- `app/services/dashboard_service.py`: NEW - aggregate dashboard data
- `app/services/event_service.py`: NEW - event mode data aggregation

**Repositories:**
- No changes needed (use existing repositories)

**Routes:**
- `app/routers/dashboard.py`: NEW - smart dashboard route
- `app/routers/event.py`: NEW - event mode command center routes
- `app/routers/registration.py`: UPDATE - add HTMX partial endpoints

**Validators:**
- No changes needed

### Frontend

**Templates - Base/Layout:**
- `app/templates/base.html`: UPDATE - context-aware sidebar links
- `app/templates/event_base.html`: NEW - event mode layout (no sidebar)

**Templates - Dashboard:**
- `app/templates/dashboard/index.html`: NEW - smart dashboard with conditionals
- `app/templates/dashboard/_no_tournament.html`: NEW - state 1 partial
- `app/templates/dashboard/_registration_mode.html`: NEW - state 2 partial
- `app/templates/dashboard/_event_active.html`: NEW - state 3 partial

**Templates - Event Mode:**
- `app/templates/event/command_center.html`: NEW - main event interface
- `app/templates/event/_current_battle.html`: NEW - current battle card
- `app/templates/event/_battle_queue.html`: NEW - queue with filters
- `app/templates/event/_phase_progress.html`: NEW - progress indicator
- `app/templates/event/_standings.html`: NEW - standings table
- `app/templates/event/_encode_modal.html`: NEW - inline encoding form

**Templates - Registration:**
- `app/templates/registration/register_v2.html`: NEW - two-panel layout
- `app/templates/registration/_available_list.html`: NEW - HTMX partial
- `app/templates/registration/_registered_list.html`: NEW - HTMX partial
- `app/templates/registration/_dancer_card.html`: NEW - reusable card

**Templates - Deprecated:**
- `app/templates/overview.html`: DEPRECATE - replace with dashboard

**Components:**
- Reuse: Status badges, flash messages, loading indicators, empty states
- New: Progress bar, category tabs

**CSS:**
- `app/static/css/dashboard.css`: NEW - dashboard styles
- `app/static/css/event.css`: NEW - event mode styles
- `app/static/css/registration.css`: NEW - two-panel registration

### Database

**Migrations:**
- No migrations needed (existing schema sufficient)

### Tests

**New Test Files:**
- `tests/test_dashboard_routes.py`: Dashboard route tests
- `tests/test_event_routes.py`: Event mode route tests

**Updated Test Files:**
- `tests/test_registration_routes.py`: Add HTMX partial tests

### Documentation

**Level 1:**
- No changes (no new business rules)

**Level 2:**
- `ROADMAP.md`: Add Phase 3.3 - UX Navigation Redesign

**Level 3:**
- `FRONTEND.md`: Add Event Mode Layout, Two-Panel Registration patterns
- `ARCHITECTURE.md`: Document dashboard/event service patterns

---

## 3. Backend Implementation Plan

### 3.1 Dashboard Service (NEW)

**File:** `app/services/dashboard_service.py`

```python
class DashboardService:
    """Aggregate dashboard data based on tournament state."""

    async def get_dashboard_context(self) -> DashboardContext:
        """Get context for smart dashboard.

        Returns:
            DashboardContext with:
            - state: 'no_tournament' | 'registration' | 'event_active'
            - tournament: Optional[Tournament]
            - categories: List with registration counts
            - battle_progress: Optional progress info
        """

    async def get_active_or_created_tournament(self) -> Optional[Tournament]:
        """Get the most relevant tournament for dashboard.

        Priority:
        1. ACTIVE tournament (event in progress)
        2. CREATED tournament in REGISTRATION phase
        3. None (no active work)
        """
```

### 3.2 Event Service (NEW)

**File:** `app/services/event_service.py`

```python
class EventService:
    """Aggregate event mode data for command center."""

    async def get_command_center_context(
        self, tournament_id: UUID
    ) -> CommandCenterContext:
        """Get all data for command center view.

        Returns:
            CommandCenterContext with:
            - tournament: Tournament
            - current_battle: Optional[Battle]
            - queue: List[Battle] (next 10 pending)
            - progress: PhaseProgress (completed/total, percentage)
            - standings: Dict[category_id, List[standings]]
        """

    async def get_phase_progress(
        self, tournament_id: UUID
    ) -> PhaseProgress:
        """Get battle completion progress for current phase."""

    async def get_standings_for_category(
        self, category_id: UUID
    ) -> List[StandingEntry]:
        """Get current standings for a category."""
```

### 3.3 Dashboard Route (NEW)

**File:** `app/routers/dashboard.py`

```python
router = APIRouter(prefix="", tags=["dashboard"])

@router.get("/", response_class=HTMLResponse)
@router.get("/overview", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user = Depends(get_current_user),
    dashboard_service = Depends(get_dashboard_service),
):
    """Smart dashboard with 3 states.

    States:
    1. No tournament: Show create CTA
    2. Registration phase: Show category registration status
    3. Event phases: Show "Go to Event Mode" CTA

    Auto-redirect:
    If tournament in PRESELECTION/POOLS/FINALS and user clicks dashboard,
    show option to go to event mode (don't force redirect).
    """
```

### 3.4 Event Route (NEW)

**File:** `app/routers/event.py`

```python
router = APIRouter(prefix="/event", tags=["event"])

@router.get("/{tournament_id}", response_class=HTMLResponse)
async def command_center(
    tournament_id: UUID,
    request: Request,
    current_user = Depends(get_current_user),
    event_service = Depends(get_event_service),
):
    """Command center for event mode.

    Full-screen interface with:
    - Current battle card
    - Battle queue
    - Phase progress
    - Standings (by category)
    """

@router.get("/{tournament_id}/current-battle", response_class=HTMLResponse)
async def current_battle_partial(tournament_id: UUID, ...):
    """HTMX partial: Current battle card."""

@router.get("/{tournament_id}/queue", response_class=HTMLResponse)
async def queue_partial(tournament_id: UUID, category_id: Optional[UUID] = None, ...):
    """HTMX partial: Battle queue with optional category filter."""

@router.get("/{tournament_id}/progress", response_class=HTMLResponse)
async def progress_partial(tournament_id: UUID, ...):
    """HTMX partial: Phase progress."""

@router.get("/{tournament_id}/standings/{category_id}", response_class=HTMLResponse)
async def standings_partial(tournament_id: UUID, category_id: UUID, ...):
    """HTMX partial: Category standings."""
```

### 3.5 Registration Route Updates

**File:** `app/routers/registration.py`

**New Endpoints:**
```python
@router.get("/{tournament_id}/{category_id}/available", response_class=HTMLResponse)
async def available_dancers_partial(...):
    """HTMX partial: Available dancers list."""

@router.get("/{tournament_id}/{category_id}/registered", response_class=HTMLResponse)
async def registered_dancers_partial(...):
    """HTMX partial: Registered dancers list."""

@router.post("/{tournament_id}/{category_id}/register/{dancer_id}", response_class=HTMLResponse)
async def register_dancer_htmx(...):
    """HTMX: Register single dancer, return both panels."""
```

---

## 4. Frontend Implementation Plan

### 4.1 Base Template Updates

**File:** `app/templates/base.html`

**Changes:**
```html
<!-- BEFORE: Broken links -->
<li><a href="/phases">Phases</a></li>

<!-- AFTER: Context-aware links -->
{% if active_tournament %}
    {% if active_tournament.phase.value in ['preselection', 'pools', 'finals'] %}
    <li><a href="/event/{{ active_tournament.id }}">🔴 Event Mode</a></li>
    {% else %}
    <li><a href="/tournaments/{{ active_tournament.id }}/phase">Phases</a></li>
    {% endif %}
{% endif %}
```

**Pattern:** Inject `active_tournament` into base template context via middleware or dependency.

### 4.2 Event Mode Base Template (NEW)

**File:** `app/templates/event_base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Event Mode - Battle-D{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <link rel="stylesheet" href="/static/css/event.css">
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body class="event-mode">
    <!-- Compact Header (no sidebar) -->
    <header class="event-header">
        <div class="event-header-left">
            <span class="event-live-indicator">🔴 LIVE</span>
            <h1>{{ tournament.name }}</h1>
            <span class="event-phase-badge">{{ tournament.phase.value|upper }}</span>
        </div>
        <div class="event-header-right">
            <span class="event-progress">{{ progress.completed }}/{{ progress.total }}</span>
            <a href="/overview" class="event-exit-btn">Exit to Prep</a>
            <span class="event-user">{{ current_user.email }}</span>
        </div>
    </header>

    {% include "components/flash_messages.html" %}

    <main class="event-main">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### 4.3 Command Center Layout

**File:** `app/templates/event/command_center.html`

```html
{% extends "event_base.html" %}

{% block content %}
<div class="command-center-grid">
    <!-- Left Column: Current Battle -->
    <section class="cc-current-battle"
             hx-get="/event/{{ tournament.id }}/current-battle"
             hx-trigger="every 5s"
             hx-swap="innerHTML">
        {% include "event/_current_battle.html" %}
    </section>

    <!-- Right Column: Queue -->
    <section class="cc-queue">
        <div class="cc-queue-header">
            <h2>Battle Queue</h2>
            <!-- Category filter tabs -->
            <div class="category-tabs" role="tablist">
                <button class="tab-btn {% if not category_filter %}active{% endif %}"
                        hx-get="/event/{{ tournament.id }}/queue"
                        hx-target=".cc-queue-list"
                        hx-swap="innerHTML">
                    All
                </button>
                {% for cat in categories %}
                <button class="tab-btn {% if category_filter == cat.id %}active{% endif %}"
                        hx-get="/event/{{ tournament.id }}/queue?category_id={{ cat.id }}"
                        hx-target=".cc-queue-list"
                        hx-swap="innerHTML">
                    {{ cat.name }}
                </button>
                {% endfor %}
            </div>
        </div>
        <div class="cc-queue-list"
             hx-get="/event/{{ tournament.id }}/queue"
             hx-trigger="every 5s"
             hx-swap="innerHTML">
            {% include "event/_battle_queue.html" %}
        </div>
    </section>

    <!-- Bottom Left: Progress -->
    <section class="cc-progress"
             hx-get="/event/{{ tournament.id }}/progress"
             hx-trigger="every 5s"
             hx-swap="innerHTML">
        {% include "event/_phase_progress.html" %}
    </section>

    <!-- Bottom Right: Standings -->
    <section class="cc-standings">
        <div class="standings-header">
            <h2>Standings</h2>
            <select id="standings-category"
                    hx-get="/event/{{ tournament.id }}/standings"
                    hx-trigger="change"
                    hx-target=".standings-table"
                    hx-include="this">
                {% for cat in categories %}
                <option value="{{ cat.id }}">{{ cat.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="standings-table">
            {% include "event/_standings.html" %}
        </div>
    </section>
</div>
{% endblock %}
```

### 4.4 Two-Panel Registration

**File:** `app/templates/registration/register_v2.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="registration-header">
    <a href="/tournaments/{{ tournament.id }}">← Back to Tournament</a>
    <h2>Register: {{ category.name }}</h2>
    <p class="registration-count">
        <strong>{{ registered_count }}/{{ ideal_capacity }}</strong> registered
        {% if registered_count >= minimum_required %}
        <span class="status-ready">✓ Ready</span>
        {% else %}
        <span class="status-need-more">Need {{ minimum_required - registered_count }} more</span>
        {% endif %}
    </p>
</div>

<div class="registration-panels">
    <!-- Left: Available Dancers -->
    <section class="panel panel-available">
        <div class="panel-header">
            <h3>Available Dancers</h3>
            <input type="search"
                   name="q"
                   placeholder="Search by blaze, name, email..."
                   hx-get="/registration/{{ tournament.id }}/{{ category.id }}/available"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#available-list"
                   hx-indicator="#search-loading">
            <span id="search-loading" class="htmx-indicator">Searching...</span>
        </div>
        <div id="available-list" class="panel-list">
            {% include "registration/_available_list.html" %}
        </div>
    </section>

    <!-- Right: Registered Dancers -->
    <section class="panel panel-registered">
        <div class="panel-header">
            <h3>Registered ({{ registered_count }})</h3>
        </div>
        <div id="registered-list" class="panel-list">
            {% include "registration/_registered_list.html" %}
        </div>
    </section>
</div>
{% endblock %}
```

**File:** `app/templates/registration/_available_list.html`

```html
{% for dancer in available_dancers %}
<article class="dancer-card">
    <div class="dancer-info">
        <strong>{{ dancer.blaze }}</strong>
        <span class="dancer-name">{{ dancer.full_name }}</span>
        <span class="dancer-meta">{{ dancer.country }} • Age {{ dancer.age }}</span>
    </div>
    <button class="btn-add"
            hx-post="/registration/{{ tournament_id }}/{{ category_id }}/register/{{ dancer.id }}"
            hx-target="#available-list"
            hx-swap="innerHTML"
            hx-swap-oob="innerHTML:#registered-list">
        + Add
    </button>
</article>
{% else %}
<p class="empty-message">No available dancers found.</p>
{% endfor %}
```

### 4.5 CSS Layout

**File:** `app/static/css/event.css`

```css
/* Event Mode Base */
body.event-mode {
    margin: 0;
    padding: 0;
    background: var(--pico-background-color);
}

.event-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: var(--pico-primary-background);
    color: white;
}

.event-live-indicator {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Command Center Grid */
.command-center-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr auto;
    gap: 1rem;
    padding: 1rem;
    height: calc(100vh - 60px);
}

.cc-current-battle { grid-column: 1; grid-row: 1; }
.cc-queue { grid-column: 2; grid-row: 1 / 3; }
.cc-progress { grid-column: 1; grid-row: 2; }

/* Responsive */
@media (max-width: 1024px) {
    .command-center-grid {
        grid-template-columns: 1fr;
        grid-template-rows: auto;
    }
}
```

---

## 5. Implementation Order

**Recommended sequence to minimize risk:**

### Batch 1: Foundation (Critical Path)
1. **Fix broken links in base.html** - Remove `/phases`, `/registration` from sidebar
2. **Fix broken links in overview.html** - Remove judge section, fix staff links
3. **Test navigation** - All links should work

### Batch 2: Dashboard Service & Route
4. **Create DashboardService** - Aggregate tournament state
5. **Create dashboard route** - Replace overview with smart dashboard
6. **Create dashboard templates** - 3-state conditional display
7. **Test dashboard** - All 3 states work correctly

### Batch 3: Event Mode
8. **Create event_base.html** - No-sidebar layout
9. **Create EventService** - Command center data aggregation
10. **Create event router** - Command center + partials
11. **Create command center template** - Grid layout with HTMX
12. **Create event CSS** - Styling
13. **Test event mode** - Full workflow

### Batch 4: Registration UX
14. **Create registration_v2.html** - Two-panel layout
15. **Add HTMX endpoints** - Available/registered partials
16. **Update register endpoint** - Return both panels with hx-swap-oob
17. **Test registration** - No page refresh

### Batch 5: Documentation & Polish
18. **Update ROADMAP.md** - Add Phase 3.3
19. **Update FRONTEND.md** - Document new patterns
20. **Run full test suite** - Verify no regressions

---

## 6. Risk Analysis

### Risk 1: Breaking Existing Functionality
**Concern:** Changes to base.html or overview.html might break other pages
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Make base.html changes backward compatible
- Create new dashboard route instead of modifying overview
- Keep overview.html working as redirect

### Risk 2: HTMX Partial Update Complexity
**Concern:** Updating two panels simultaneously (available + registered) might be complex
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Use `hx-swap-oob` to update second panel
- Test thoroughly with different response patterns
- Have fallback to page refresh if HTMX fails

### Risk 3: Event Mode Session State
**Concern:** User might lose context when navigating between event mode and prep
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Event mode is a separate URL (`/event/{id}`)
- "Exit to Prep" button clearly labeled
- No session state needed (all URL-based)

### Risk 4: Mobile Responsiveness
**Concern:** Command center grid might not work on mobile
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Design mobile-first CSS
- Stack columns on small screens
- Test on actual devices

---

## 7. Testing Plan

### Unit Tests

**test_dashboard_service.py:**
```python
- test_get_dashboard_context_no_tournament()
- test_get_dashboard_context_registration_phase()
- test_get_dashboard_context_event_phase()
- test_get_active_or_created_tournament_priority()
```

**test_event_service.py:**
```python
- test_get_command_center_context()
- test_get_phase_progress()
- test_get_standings_for_category()
```

### Integration Tests

**test_dashboard_routes.py:**
```python
- test_dashboard_renders_no_tournament_state()
- test_dashboard_renders_registration_state()
- test_dashboard_renders_event_active_state()
- test_overview_redirects_to_dashboard()
```

**test_event_routes.py:**
```python
- test_command_center_requires_auth()
- test_command_center_renders_correctly()
- test_queue_partial_returns_html()
- test_queue_filters_by_category()
```

### Manual Testing Checklist

**Navigation:**
- [ ] All sidebar links work (no 404s)
- [ ] Dashboard shows correct state
- [ ] "Go to Event Mode" button works

**Event Mode:**
- [ ] Command center displays all sections
- [ ] HTMX polling updates data
- [ ] Start/Encode buttons work
- [ ] "Exit to Prep" returns to dashboard

**Registration:**
- [ ] Two panels display correctly
- [ ] Search filters available dancers
- [ ] Add button registers without refresh
- [ ] Remove button unregisters without refresh
- [ ] Count updates in real-time

**Accessibility:**
- [ ] Keyboard navigation works
- [ ] Screen reader announces updates
- [ ] Color contrast meets WCAG AA

**Responsive:**
- [ ] Mobile (320px): Single column layout
- [ ] Tablet (768px): Adjusted grid
- [ ] Desktop (1024px+): Full grid layout

---

## 8. Open Questions

- [x] Should dashboard auto-redirect to event mode? → No, show CTA button
- [x] Should registration use drag-and-drop? → Not in v1, use buttons (simpler)
- [ ] Should event mode have keyboard shortcuts? → Defer to Phase 2

---

## 9. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed batch order acceptable
- [ ] User approved risk mitigations

---

**Next Step:** After user approval, run `/implement-feature` to begin Batch 1.
