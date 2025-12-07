# Workbench: UX Navigation Redesign

**Date:** 2025-12-07
**Author:** Claude
**Status:** In Progress

---

## Purpose

Complete UX redesign with context-aware navigation, smart dashboard, event mode command center, and improved registration. Fixes broken 404 links and creates coherent user workflows.

---

## Documentation Changes

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- No entity changes needed (existing schema sufficient)

**VALIDATION_RULES.md:**
- No new validation rules needed

### Level 2: Derived

**ROADMAP.md:**
- [x] Add Phase 3.3: UX Navigation Redesign

### Level 3: Operational

**ARCHITECTURE.md:**
- [x] Add Dashboard/Event Service patterns

**FRONTEND.md:**
- [x] Add Event Mode Layout pattern
- [x] Add Two-Panel Registration pattern
- [x] Add Smart Dashboard component

---

## Verification

**Grep checks performed:**
```bash
grep -r "BR-NAV" *.md        # New business rules
grep -r "event mode" *.md    # New concept
grep -r "command center" *.md # New concept
```

**Results:**
- ✅ All references consistent
- ✅ No orphaned references
- ✅ Cross-references valid

---

## Files Modified

### Documentation (Phase 4)
- ROADMAP.md - Added Phase 3.3
- ARCHITECTURE.md - Added Dashboard/Event service patterns
- FRONTEND.md - Added Event Mode, Two-Panel Registration patterns

### Code (Phase 5)

**Batch 1: Fix Broken Links (COMPLETE)**
- `app/templates/base.html` - Context-aware sidebar navigation
  - Removed broken `/phases` link
  - Added active tournament section with proper links
  - Links now use `active_tournament.id` for context
- `app/templates/overview.html` - Fixed broken links
  - Fixed `/phases` → `/phases/{{ active_tournament.id }}/phase`
  - Removed broken `/registration` link (will be re-added in Batch 4)
  - Removed judge section with `/battles/current` (non-existent route)
  - All phase links now conditional on active_tournament

**Batch 2: Smart Dashboard (COMPLETE)**
- `app/services/dashboard_service.py` - NEW
  - DashboardContext dataclass with 3 states
  - CategoryStats dataclass for registration progress
  - get_dashboard_context() method
  - get_relevant_tournament() with priority logic
- `app/routers/dashboard.py` - NEW
  - Handles `/` and `/overview` routes
  - Uses DashboardService for context
  - Passes active_tournament for sidebar
- `app/dependencies.py` - Updated
  - Added get_dashboard_service() dependency
  - Added get_active_tournament() dependency
- `app/templates/dashboard/index.html` - NEW
  - Smart dashboard with state-based content
- `app/templates/dashboard/_no_tournament.html` - NEW
  - State 1: No active tournament CTA
- `app/templates/dashboard/_registration_mode.html` - NEW
  - State 2: Registration progress with category cards
- `app/templates/dashboard/_event_active.html` - NEW
  - State 3: Event mode CTA
- `app/main.py` - Updated
  - Replaced overview route with dashboard router
  - Cleaned up unused imports
- `tests/test_auth.py` - Updated
  - Changed assertion from "Overview" to "Dashboard"

**Batch 3: Event Mode (COMPLETE)**
- `app/services/event_service.py` - NEW
  - CommandCenterContext dataclass
  - BattleQueueItem, PhaseProgress, CategoryInfo dataclasses
  - get_command_center_context() method
  - get_phase_progress() method
  - get_battle_queue() with category filter
- `app/routers/event.py` - NEW
  - `/event/{tournament_id}` - Command center route
  - `/event/{tournament_id}/current-battle` - HTMX partial
  - `/event/{tournament_id}/queue` - HTMX partial with category filter
  - `/event/{tournament_id}/progress` - HTMX partial
- `app/dependencies.py` - Updated
  - Added get_event_service() dependency
- `app/templates/event_base.html` - NEW
  - Full-screen layout without sidebar
  - Compact header with LIVE indicator
- `app/templates/event/command_center.html` - NEW
  - Grid layout with current battle, queue, progress
  - HTMX auto-refresh every 5 seconds
- `app/templates/event/_current_battle.html` - NEW
  - Current battle card with performer names
- `app/templates/event/_battle_queue.html` - NEW
  - Battle queue list with positions
- `app/templates/event/_phase_progress.html` - NEW
  - Progress bar with percentage
- `app/static/css/event.css` - NEW
  - Full event mode styling
- `app/main.py` - Updated
  - Added event router

**Batch 4: Registration UX (COMPLETE)**
- `app/routers/registration.py` - Updated
  - Added `/available` HTMX partial endpoint
  - Added `/registered` HTMX partial endpoint
  - Added `/register/{dancer_id}` HTMX endpoint with OOB swap
  - Added `/unregister-htmx/{performer_id}` HTMX endpoint
- `app/templates/registration/register.html` - Rewritten
  - Two-panel layout for solo registration
  - Kept duo registration with existing search UI
  - HTMX-powered instant registration
- `app/templates/registration/_available_list.html` - NEW
  - Available dancers partial with add buttons
- `app/templates/registration/_registered_list.html` - NEW
  - Registered performers partial with remove buttons
- `app/templates/registration/_registration_update.html` - NEW
  - OOB swap template for updating both panels
- `app/static/css/registration.css` - NEW
  - Two-panel layout styling
  - Responsive design

---

## Notes

- Tests passing: 209 passed, 8 skipped
- All 4 batches complete
