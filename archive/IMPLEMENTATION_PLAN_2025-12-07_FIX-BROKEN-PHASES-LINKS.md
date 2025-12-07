# Implementation Plan: Fix Broken Phases Navigation Links

**Date:** 2025-12-07
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-07_FIX-BROKEN-PHASES-LINKS.md

---

## 1. Summary

**Feature:** Fix all broken navigation links related to tournament phases (7 broken links causing 404 errors)

**Approach:** Template-only changes - replace `/phases/` with `/tournaments/` in 6 template files, remove Go Back button, and add comprehensive test coverage for the new services that were never tested.

---

## 2. Affected Files

### Backend
**Models:** No changes needed

**Services:** No changes needed (services work correctly)

**Repositories:** No changes needed

**Routes:** No changes needed (routes work correctly at `/tournaments/`)

**Validators:** No changes needed

**Utils:** No changes needed

### Frontend
**Templates to Modify:**

| File | Change |
|------|--------|
| `app/templates/base.html:183` | `/phases/` → `/tournaments/` |
| `app/templates/dashboard/_registration_mode.html:11` | `/phases/` → `/tournaments/` |
| `app/templates/dashboard/_event_active.html:13` | `/phases/` → `/tournaments/` |
| `app/templates/overview.html:26,43,65` | `/phases/` → `/tournaments/` (3 locations) |
| `app/templates/phases/overview.html:27-31` | Remove "Go Back" form section |
| `app/templates/phases/overview.html:33` | `/phases/advance` → `/tournaments/{{ tournament.id }}/advance` |

**CSS:** No changes needed

### Database
**Migrations:** No changes needed

### Tests (NEW)
**New Test Files:**
- `tests/test_dashboard_service.py` - Unit tests for DashboardService (currently 0 tests)
- `tests/test_event_service.py` - Unit tests for EventService (currently 0 tests)
- `tests/test_phases_routes.py` - Integration tests for phase navigation routes

**Updated Test Files:**
- `tests/test_auth.py` - Add dashboard navigation tests

### Documentation
**Level 3:**
- CHANGELOG.md: Document bug fix

---

## 3. Template Changes (Detailed)

### 3.1 base.html - Sidebar Link

**Location:** Line 183

**Current:**
```html
<li><a href="/phases/{{ active_tournament.id }}/phase">Phases</a></li>
```

**Fixed:**
```html
<li><a href="/tournaments/{{ active_tournament.id }}/phase">Phases</a></li>
```

### 3.2 _registration_mode.html - Manage Phases Button

**Location:** Line 11

**Current:**
```html
<a href="/phases/{{ dashboard.tournament.id }}/phase" role="button" class="secondary">Manage Phases</a>
```

**Fixed:**
```html
<a href="/tournaments/{{ dashboard.tournament.id }}/phase" role="button" class="secondary">Manage Phases</a>
```

### 3.3 _event_active.html - Phase Management Button

**Location:** Line 13

**Current:**
```html
<a href="/phases/{{ dashboard.tournament.id }}/phase" role="button" class="secondary">Phase Management</a>
```

**Fixed:**
```html
<a href="/tournaments/{{ dashboard.tournament.id }}/phase" role="button" class="secondary">Phase Management</a>
```

### 3.4 overview.html - Multiple Links (3 locations)

**Location:** Lines 26, 43, 65

**Current (all 3 locations):**
```html
<a href="/phases/{{ active_tournament.id }}/phase" role="button">Manage Phases</a>
```

**Fixed:**
```html
<a href="/tournaments/{{ active_tournament.id }}/phase" role="button">Manage Phases</a>
```

### 3.5 phases/overview.html - Remove Go Back + Fix Advance

**Location:** Lines 27-37

**Current:**
```html
<form action="/phases/go-back" method="post">
    <button type="submit" {% if not can_go_back %}disabled{% endif %}>
        ← Go Back to {{ prev_phase.value if prev_phase else "N/A" }}
    </button>
</form>

<form action="/phases/advance" method="post">
    <button type="submit" {% if not can_advance %}disabled{% endif %}>
        Advance to {{ next_phase.value if next_phase else "N/A" }} →
    </button>
</form>
```

**Fixed:**
```html
<form action="/tournaments/{{ tournament.id }}/advance" method="post">
    <button type="submit" {% if not can_advance %}disabled{% endif %}>
        Advance to {{ next_phase.value if next_phase else "N/A" }} →
    </button>
</form>
```

---

## 4. Testing Plan

### 4.1 New Test File: test_dashboard_service.py

Tests for DashboardService that currently has 0% coverage:

```python
# Test coverage plan:
class TestDashboardService:
    """Unit tests for DashboardService."""

    async def test_get_dashboard_context_no_tournament()
        """Returns no_tournament state when no tournaments exist."""

    async def test_get_dashboard_context_registration_phase()
        """Returns registration state for CREATED tournament in REGISTRATION phase."""

    async def test_get_dashboard_context_event_active()
        """Returns event_active state for ACTIVE tournament in PRESELECTION/POOLS/FINALS."""

    async def test_get_relevant_tournament_active_priority()
        """Active tournament takes priority over CREATED."""

    async def test_get_relevant_tournament_created_fallback()
        """CREATED tournament returned when no ACTIVE."""

    async def test_get_category_stats()
        """Returns correct registration counts per category."""

    async def test_get_category_stats_is_ready()
        """is_ready flag correctly calculated based on minimum."""
```

### 4.2 New Test File: test_event_service.py

Tests for EventService that currently has 0% coverage:

```python
# Test coverage plan:
class TestEventService:
    """Unit tests for EventService."""

    async def test_get_command_center_context()
        """Returns complete command center context."""

    async def test_get_command_center_tournament_not_found()
        """Raises ValueError for non-existent tournament."""

    async def test_get_phase_progress()
        """Calculates correct phase progress percentages."""

    async def test_get_phase_progress_empty()
        """Returns 0/0/0 for tournament with no battles."""

    async def test_get_battle_queue()
        """Returns pending battles in correct order."""

    async def test_get_battle_queue_with_category_filter()
        """Filters queue by category when specified."""

    async def test_get_performer_display_name_solo()
        """Returns dancer blaze for solo performer."""

    async def test_get_performer_display_name_duo()
        """Returns combined names for duo performer."""
```

### 4.3 New Test File: test_phases_routes.py

Integration tests for phase navigation routes:

```python
# Test coverage plan:
class TestPhasesRoutes:
    """Integration tests for phase navigation."""

    def test_phases_overview_authenticated()
        """GET /tournaments/{id}/phase returns 200 for authenticated user."""

    def test_phases_overview_unauthenticated()
        """GET /tournaments/{id}/phase returns 401 without auth."""

    def test_phases_advance_admin_only()
        """POST /tournaments/{id}/advance requires admin role."""

    def test_phases_advance_staff_forbidden()
        """POST /tournaments/{id}/advance returns 403 for staff."""

    def test_phases_overview_shows_correct_phase()
        """Phase overview displays current tournament phase."""

    def test_phases_advance_form_action_correct()
        """Advance form posts to correct URL with tournament ID."""
```

### 4.4 Updated: test_auth.py

Add dashboard navigation tests:

```python
class TestDashboardNavigation:
    """Tests for dashboard navigation links."""

    def test_sidebar_phases_link_correct()
        """Sidebar phases link uses /tournaments/ prefix."""

    def test_dashboard_manage_phases_link_correct()
        """Dashboard 'Manage Phases' button uses correct URL."""
```

---

## 5. Implementation Order

Recommended sequence to minimize risk:

### Batch 1: Template Fixes (Quick Win)
1. **Fix base.html** - Sidebar link
2. **Fix overview.html** - 3 link locations
3. **Fix _registration_mode.html** - Manage Phases button
4. **Fix _event_active.html** - Phase Management button
5. **Fix phases/overview.html** - Remove Go Back, fix Advance form
6. **Manual test in browser** - Verify all links work

### Batch 2: Test Coverage (Quality)
1. **Create test_dashboard_service.py** - Unit tests for DashboardService
2. **Create test_event_service.py** - Unit tests for EventService
3. **Create test_phases_routes.py** - Integration tests for routes
4. **Run full test suite** - Ensure no regressions

### Batch 3: Documentation & Commit
1. **Update CHANGELOG.md** - Document bug fix
2. **Run full test suite** - Final verification
3. **Create commit** - Single commit with all changes
4. **Push to main** - Deploy fix

---

## 6. Risk Analysis

### Risk 1: Template Syntax Error
**Concern:** Typo in Jinja2 template causes server error
**Likelihood:** Low (simple string replacements)
**Impact:** High (500 errors)
**Mitigation:**
- Test each template change individually
- Browser verification after each edit

### Risk 2: Missing Tournament Context
**Concern:** Template variable `tournament.id` not available in some contexts
**Likelihood:** Low (already used elsewhere)
**Impact:** Medium (broken advance button)
**Mitigation:**
- Check router provides `tournament` in context
- Verify with existing phases/overview.html usage

### Risk 3: Test Failures Reveal More Bugs
**Concern:** New tests might find additional issues
**Likelihood:** Medium
**Impact:** Positive (better quality)
**Mitigation:**
- Fix discovered issues as part of this work
- Expand scope if needed

---

## 7. Acceptance Criteria

### Template Changes
- [ ] Sidebar "Phases" link navigates to `/tournaments/{id}/phase` (no 404)
- [ ] Dashboard "Manage Phases" button navigates correctly (no 404)
- [ ] Event dashboard "Phase Management" button navigates correctly (no 404)
- [ ] Overview page "Manage Phases" links navigate correctly (no 404)
- [ ] Phase advance form posts to `/tournaments/{id}/advance` (no 404)
- [ ] "Go Back" button removed from phases overview

### Test Coverage
- [ ] DashboardService has unit tests (7+ tests)
- [ ] EventService has unit tests (8+ tests)
- [ ] Phase routes have integration tests (6+ tests)
- [ ] All tests pass (0 failures)

### Documentation
- [ ] CHANGELOG.md updated with bug fix entry

---

## 8. Estimated Effort

| Task | Estimate |
|------|----------|
| Template fixes (Batch 1) | 10 minutes |
| Browser verification | 5 minutes |
| test_dashboard_service.py | 20 minutes |
| test_event_service.py | 25 minutes |
| test_phases_routes.py | 15 minutes |
| CHANGELOG update | 2 minutes |
| Final testing & commit | 5 minutes |
| **Total** | ~82 minutes |

---

## 9. Open Questions

- [x] Should "Go Back" button be removed or implemented? → **REMOVED** (user confirmed)
- [x] Are there any other broken links? → **NO** (all 7 identified)

---

## 10. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed test coverage scope acceptable
- [ ] User approved implementation order
