# Implementation Plan: Navigation Streamlining

**Date:** 2025-12-23
**Feature Spec:** FEATURE_SPEC_2025-12-23_NAVIGATION-STREAMLINING.md
**Status:** Ready for Implementation

---

## 1. Summary

**Feature:** Remove redundant Dashboard page and streamline navigation to reduce clicks to Event Mode.

**Approach:**
- Redirect `/overview` and post-login to `/tournaments` (no DB changes needed)
- Simplify sidebar navigation: remove Dashboard, reorder items, add prominent Event Mode button
- Add Event Mode button directly to active tournament cards for faster access
- Delete orphaned Dashboard templates after verification

---

## 2. Affected Files

### Backend

**Routes:**
- `app/routers/dashboard.py`: Simplify to redirect only (remove template rendering)
- `app/routers/auth.py`: Update post-login redirect from `/overview` to `/tournaments` (lines 112, 171)

**Services:**
- None required (no business logic changes)

**Models:**
- None required (no schema changes)

### Frontend

**Templates:**
- `app/templates/base.html`: Update sidebar navigation (lines 24-69)
- `app/templates/tournaments/list.html`: Add Event Mode button to tournament cards (line 67-79)

**Components:**
- No new components needed - reusing existing `.btn`, `.badge` classes

**SCSS:**
- `app/static/scss/layout/_sidebar.scss`: Add `.nav-item-event-mode` style
- `app/static/scss/components/_cards.scss`: Add `.tournament-card-actions` style

### Database

**Migrations:**
- None required (no schema changes)

### Tests

**Files to Update:**
- `tests/test_permissions.py`: Update `/overview` tests (lines 93-112) - expect 302 redirect
- `tests/test_auth.py`: Update login redirect test (line 190) - expect `/tournaments`
- `tests/test_dashboard_service.py`: Keep tests (service still exists for future use)
- `tests/e2e/test_ux_consistency.py`: Update Dashboard tests (lines 148-167, 286-302)
- `tests/e2e/test_htmx_interactions.py`: Update `/overview` test (lines 115-128)
- `tests/e2e/test_admin.py`: Update redirect assertion (line 730)

### Documentation

**Level 1:** No changes needed (no domain model changes)

**Level 2:** No changes needed (not a new roadmap phase)

**Level 3:**
- `FRONTEND.md`: Could document Event Mode button pattern (optional)

### Files to Delete

- `app/templates/dashboard/index.html`
- `app/templates/dashboard/_no_tournament.html`
- `app/templates/dashboard/_registration_mode.html`
- `app/templates/dashboard/_event_active.html`
- `app/templates/dashboard/` directory

---

## 3. Technical POC

**Status:** Not required

**Reason:** Standard redirect and template changes following existing patterns. No new integrations, no risky technical assumptions.

---

## 4. Implementation Steps

### Step 1: Update Sidebar Navigation

**File:** `app/templates/base.html`

**Changes:**
1. Remove "Dashboard" nav item
2. Make "Tournaments" the first item
3. Remove the entire "Tournament Name" section with "Tournament Details" link
4. Replace with simple "Event Mode" button (only when active tournament exists)

**Current Code (lines 24-68):**
```html
<nav class="sidebar-nav">
    <ul class="nav-list">
        <li>
            <a href="/overview" class="nav-item {% if request.url.path == '/overview' %}is-active{% endif %}">
                Dashboard
            </a>
        </li>

        {% if current_user.is_staff %}
        <li>
            <a href="/dancers" class="nav-item ...">Dancers</a>
        </li>
        <li>
            <a href="/tournaments" class="nav-item ...">Tournaments</a>
        </li>
        {% endif %}

        {% if current_user.is_admin %}
        <li>
            <a href="/admin/users" class="nav-item ...">Users</a>
        </li>
        {% endif %}

        {% if active_tournament %}
        <li><hr class="nav-divider"></li>
        <li class="nav-section-label">{{ active_tournament.name }}</li>
        <li>
            <a href="/tournaments/{{ active_tournament.id }}" class="nav-item">
                Tournament Details
            </a>
        </li>
        {% if current_user.is_mc or current_user.is_admin %}
        <li>
            <a href="/event/{{ active_tournament.id }}" class="nav-item">
                Event Mode
            </a>
        </li>
        {% endif %}
        {% endif %}
    </ul>
</nav>
```

**New Code:**
```html
<nav class="sidebar-nav">
    <ul class="nav-list">
        {% if current_user.is_staff %}
        <li>
            <a href="/tournaments" class="nav-item {% if '/tournaments' in request.url.path %}is-active{% endif %}">
                Tournaments
            </a>
        </li>
        <li>
            <a href="/dancers" class="nav-item {% if '/dancers' in request.url.path %}is-active{% endif %}">
                Dancers
            </a>
        </li>
        {% endif %}

        {% if current_user.is_admin %}
        <li>
            <a href="/admin/users" class="nav-item {% if '/admin' in request.url.path %}is-active{% endif %}">
                Users
            </a>
        </li>
        {% endif %}

        {% if active_tournament and (current_user.is_mc or current_user.is_admin) %}
        <li><hr class="nav-divider"></li>
        <li>
            <a href="/event/{{ active_tournament.id }}" class="nav-item nav-item-event-mode {% if '/event' in request.url.path %}is-active{% endif %}">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                Event Mode
            </a>
        </li>
        {% endif %}
    </ul>
</nav>
```

---

### Step 2: Add Event Mode Button Styling

**File:** `app/static/scss/layout/_sidebar.scss`

**Add new style for Event Mode button:**
```scss
// Event Mode prominent button
.nav-item-event-mode {
  background-color: $color-primary;
  color: white !important;
  border-radius: $radius-md;
  margin: $space-2;
  padding: $space-3 !important;
  display: flex;
  align-items: center;
  gap: $space-2;
  font-weight: $font-weight-semibold;

  &:hover {
    background-color: $color-primary-dark;
    color: white !important;
  }

  &.is-active {
    background-color: $color-primary-dark;
  }

  svg {
    width: 16px;
    height: 16px;
  }
}
```

---

### Step 3: Update Dashboard Route to Redirect

**File:** `app/routers/dashboard.py`

**Current:** Serves dashboard templates

**New:** Redirect to `/tournaments`

```python
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/overview")
async def overview(request: Request):
    """Redirect to tournaments list (dashboard removed)."""
    return RedirectResponse(url="/tournaments", status_code=302)
```

---

### Step 4: Update Login Redirect

**File:** `app/routers/auth.py` (or wherever login redirect is handled)

**Find:** Post-login redirect to `/overview`

**Change to:** Redirect to `/tournaments`

```python
# Find the line like:
return RedirectResponse(url="/overview", status_code=302)

# Change to:
return RedirectResponse(url="/tournaments", status_code=302)
```

---

### Step 5: Add Event Mode Button to Tournament Card

**File:** `app/templates/tournaments/list.html`

**Current tournament card footer (line 67-79):**
```html
<div class="tournament-card-footer">
    {% set phase_class = {...}.get(tournament.phase.value, 'badge-pending') %}
    <span class="badge {{ phase_class }}">
        {{ tournament.phase.value|capitalize }}
    </span>
    <a href="/tournaments/{{ tournament.id }}" class="btn btn-sm btn-secondary">View</a>
</div>
```

**New tournament card footer:**
```html
<div class="tournament-card-footer">
    {% set phase_class = {...}.get(tournament.phase.value, 'badge-pending') %}
    <span class="badge {{ phase_class }}">
        {{ tournament.phase.value|capitalize }}
    </span>
    <div class="tournament-card-actions">
        {% if tournament.status.value == 'active' and (current_user.is_mc or current_user.is_admin) %}
        <a href="/event/{{ tournament.id }}" class="btn btn-sm btn-primary">
            Event Mode
        </a>
        {% endif %}
        <a href="/tournaments/{{ tournament.id }}" class="btn btn-sm btn-secondary">View</a>
    </div>
</div>
```

**Add CSS for actions container:**
```scss
.tournament-card-actions {
  display: flex;
  gap: $space-2;
}
```

---

### Step 6: Delete Dashboard Templates (Cleanup)

**Files to delete:**
- `app/templates/dashboard/index.html`
- `app/templates/dashboard/_no_tournament.html`
- `app/templates/dashboard/_registration_mode.html`
- `app/templates/dashboard/_event_active.html`
- `app/templates/dashboard/` (directory)

**Note:** Only delete after confirming redirect works correctly.

---

### Step 7: Update Tests

**Files to update:**
- Any tests that expect `/overview` to return 200 → expect 302 redirect
- Any tests checking sidebar contains "Dashboard" → remove those checks
- Navigation tests expecting "Dashboard" as first item → expect "Tournaments"

**Tests to potentially update:**
```bash
grep -rn "overview" tests/
grep -rn "Dashboard" tests/
```

---

## 5. Risk Analysis

### Risk 1: Tests Failing After Redirect Change
**Concern:** Many tests expect `/overview` to return 200, will fail with 302
**Likelihood:** High (9 test files reference `/overview` or Dashboard)
**Impact:** Medium (CI/CD blocked but no user impact)
**Mitigation:**
- Update tests in same commit as route changes
- Use `follow_redirects=True` where appropriate
- Update expected status codes from 200 to 302

### Risk 2: Users Bookmarked /overview
**Concern:** Users with `/overview` bookmarks get redirected
**Likelihood:** Low (internal tool, few users)
**Impact:** Low (redirect works, not broken)
**Mitigation:**
- 302 redirect preserves user flow
- No action needed - redirect is seamless

### Risk 3: Breaking Active Tournament Detection for Event Mode Button
**Concern:** Tournament status check may not match sidebar's `active_tournament` context
**Likelihood:** Low (both use same `status == 'active'` check)
**Impact:** Medium (Event Mode button missing when expected)
**Mitigation:**
- Test with active and inactive tournaments
- Verify condition: `tournament.status.value == 'active'`

### Risk 4: SCSS Variable Not Defined
**Concern:** `$color-primary-dark` may not exist in abstracts
**Likelihood:** Medium (need to verify)
**Impact:** Low (SCSS compilation fails, caught immediately)
**Mitigation:**
- Check `_variables.scss` for `$color-primary-dark`
- Use `$color-primary-hover` as fallback if not defined

---

## 6. Implementation Order

**Recommended sequence (minimizes risk):**

1. **Backend Routes First** (Foundation)
   - Update `dashboard.py` to redirect
   - Update `auth.py` post-login redirects
   - Test manually: login → should go to `/tournaments`

2. **Frontend Templates** (Core UI)
   - Update `base.html` sidebar navigation
   - Update `tournaments/list.html` card footer
   - Test manually: verify new navigation works

3. **SCSS Styles** (Polish)
   - Add `.nav-item-event-mode` to `_sidebar.scss`
   - Add `.tournament-card-actions` to `_cards.scss`
   - Compile SCSS: `sass app/static/scss:app/static/css --no-source-map`
   - Test manually: verify Event Mode button is orange

4. **Update Tests** (Quality)
   - Update all tests expecting `/overview` → 200
   - Remove Dashboard-specific assertions
   - Run test suite: `pytest tests/`

5. **Delete Dashboard Templates** (Cleanup - LAST)
   - Only after all tests pass
   - Delete entire `app/templates/dashboard/` directory
   - Verify no broken template references

---

## 7. Rollback Plan

If issues arise:
1. Revert `base.html` to restore Dashboard nav item
2. Revert `dashboard.py` to serve templates again
3. Revert `auth.py` to redirect to `/overview`
4. Keep dashboard templates (don't delete until stable)

---

## 8. Testing Plan

### Unit Tests to Update

**`tests/test_permissions.py`:**
```python
# Change from:
response = client.get("/overview", cookies=...)
assert response.status_code == 200

# To:
response = client.get("/overview", cookies=..., follow_redirects=False)
assert response.status_code == 302
assert response.headers["location"] == "/tournaments"
```

**`tests/test_auth.py`:**
```python
# Line 190 - verify redirect goes to /tournaments
assert response.headers["location"] == "/tournaments"
```

### E2E Tests to Update

**`tests/e2e/test_ux_consistency.py`:**
- Remove or update `test_dashboard_permission_symbols` (lines 148-167)
- Update `test_dashboard_page_loads` (lines 286-302) to test redirect

**`tests/e2e/test_htmx_interactions.py`:**
- Update `test_overview_full_page` to expect redirect

### New Test Cases

**Navigation Tests:**
```python
def test_sidebar_shows_tournaments_first(staff_client):
    """Tournaments should be first nav item after login."""
    response = staff_client.get("/tournaments")
    assert "Tournaments" in response.text
    # Verify order: Tournaments appears before Dancers
    tournaments_pos = response.text.find('href="/tournaments"')
    dancers_pos = response.text.find('href="/dancers"')
    assert tournaments_pos < dancers_pos

def test_event_mode_button_in_sidebar_for_mc(mc_client, active_tournament):
    """MC should see Event Mode button in sidebar."""
    response = mc_client.get("/tournaments")
    assert "Event Mode" in response.text
    assert f"/event/{active_tournament.id}" in response.text

def test_event_mode_button_not_in_sidebar_for_staff(staff_client, active_tournament):
    """Staff (non-MC) should NOT see Event Mode button."""
    response = staff_client.get("/tournaments")
    assert "Event Mode" not in response.text

def test_event_mode_button_on_active_tournament_card(admin_client, active_tournament):
    """Active tournament card should have Event Mode button."""
    response = admin_client.get("/tournaments")
    # Find the card for active tournament
    assert "Event Mode" in response.text
```

### Manual Testing Checklist

**Login Flow:**
- [ ] Login redirects to `/tournaments` (not `/overview`)
- [ ] `/overview` redirects to `/tournaments`
- [ ] Root `/` redirects appropriately

**Sidebar Navigation:**
- [ ] Tournaments is first nav item
- [ ] Dancers is second nav item
- [ ] No "Dashboard" nav item
- [ ] Users appears for admin only
- [ ] No "Tournament Name" section
- [ ] No "Tournament Details" link

**Event Mode Button (Sidebar):**
- [ ] Appears when active tournament exists
- [ ] Only visible to MC and Admin
- [ ] NOT visible to Staff
- [ ] Has orange/primary background
- [ ] Has lightning bolt icon
- [ ] Links to correct `/event/{id}` URL

**Event Mode Button (Tournament Card):**
- [ ] Appears on ACTIVE tournament cards only
- [ ] Only visible to MC and Admin
- [ ] NOT visible to Staff
- [ ] Positioned next to "View" button

### Accessibility Checks

- [ ] Event Mode button keyboard accessible
- [ ] Button has visible focus indicator
- [ ] Icon is decorative (no aria-label on icon)
- [ ] Button text is readable ("Event Mode")

---

## 9. Detailed Code Changes

### Step 4.3 (Addition): Update Root Redirect

**File:** `app/routers/dashboard.py`

The root route `/` also redirects to `/overview`. Update to redirect to `/tournaments`:

```python
@router.get("/", response_class=HTMLResponse)
async def root():
    """Root route redirects to tournaments."""
    return RedirectResponse(url="/tournaments", status_code=302)
```

### Step 4.4 (Addition): Fix Link in Tournament List Warning

**File:** `app/templates/tournaments/list.html` (line 33)

The data integrity warning links to `/overview`. Update to link to `/tournaments`:

**Current:**
```html
<a href="/overview">Visit Overview to fix this issue</a>.
```

**New:**
```html
<a href="/tournaments">Refresh this page to see current status</a>.
```

### Step 4.5 (Correction): Auth.py Has Two Redirect Points

**File:** `app/routers/auth.py`

Two places need updating:
1. Line 112: `verify_magic_link` - redirect after successful token verification
2. Line 171: `backdoor_login` - redirect after backdoor access

Both currently redirect to `/overview`, change to `/tournaments`.

---

## 10. Files Changed Summary

| File | Change Type | Lines Affected |
|------|-------------|----------------|
| `app/routers/dashboard.py` | Simplify (redirect only) | ~50 lines removed |
| `app/routers/auth.py` | Modify redirect URLs | Lines 112, 171 |
| `app/templates/base.html` | Modify sidebar nav | Lines 24-69 |
| `app/templates/tournaments/list.html` | Add Event Mode button + fix link | Lines 33, 67-79 |
| `app/static/scss/layout/_sidebar.scss` | Add new style | +25 lines |
| `app/static/scss/components/_cards.scss` | Add actions container | +5 lines |
| `tests/test_permissions.py` | Update expectations | Lines 93-112 |
| `tests/test_auth.py` | Update redirect assertion | Line 190 |
| `tests/e2e/test_ux_consistency.py` | Update/remove tests | Lines 148-167, 286-302 |
| `tests/e2e/test_htmx_interactions.py` | Update test | Lines 115-128 |
| `tests/e2e/test_admin.py` | Update assertion | Line 730 |
| `app/templates/dashboard/*` | DELETE | 4 files |

---

## 11. Open Questions

- [x] Should `/overview` return 301 (permanent) or 302 (temporary)? → **302** (allows easy rollback)
- [x] Keep DashboardService for future use? → **Yes** (no harm, may need later)
- [x] What about tournaments/list.html line 33 link to `/overview`? → **Update to `/tournaments`**

---

## 12. Quality Gate Checklist

**Technical Design:**
- [x] All affected files identified (backend, frontend, tests)
- [x] Backend patterns chosen (simple redirect, no service changes)
- [x] Frontend patterns chosen (existing components, new SCSS class)
- [x] Database changes planned (none needed)
- [x] Documentation updates planned (minimal)

**Technical Risk Validation:**
- [x] Technical risks identified (test failures, SCSS variable)
- [x] POC not required (standard patterns)

**Risk Analysis:**
- [x] Breaking changes identified (test expectations)
- [x] Performance concerns documented (none)
- [x] Complexity concerns addressed (simplification, not added complexity)
- [x] Each risk has mitigation plan

**User Validation:**
- [ ] User approved technical approach
- [ ] User confirmed risks acceptable

**Deliverable:**
- [x] Implementation plan complete
- [x] All sections filled out
- [x] Implementation order defined
