# Implementation Plan: UI Mockup Alignment Fixes

**Date:** 2025-12-23
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-23_UI-MOCKUP-ALIGNMENT.md

---

## 1. Summary

**Feature:** Fix 4 UI bugs/gaps to align with Figma mockups
**Approach:** CSS fixes, Lucide Icons integration, component updates, HTMX modal

---

## 2. Affected Files

### Frontend

**SCSS:**
- `app/static/scss/components/_modals.scss`: Fix display bug (Critical)
- `app/static/scss/components/_empty-state.scss`: Update icon styles
- `app/static/scss/components/_cards.scss`: Add tournament card variant
- `app/static/css/main.css`: Recompile

**Templates:**
- `app/templates/components/empty_state.html`: Add Lucide icon mapping
- `app/templates/components/delete_modal.html`: Verify modal behavior
- `app/templates/components/tournament_create_modal.html`: NEW - Create modal form
- `app/templates/tournaments/list.html`: Replace table with cards + add modal trigger

**No Backend Changes Required** - All fixes are frontend-only.

### Tests

**Updated Test Files:**
- `tests/e2e/test_ux_consistency.py`: Add modal display tests
- `tests/e2e/test_delete_modal.py`: Verify modal hidden on load

**New Test File:**
- `tests/e2e/test_tournament_cards.py`: Test card layout and modal

### Documentation

**Level 3:**
- `FRONTEND.md`: Document Lucide Icons integration, tournament card component

---

## 3. Implementation Order

**Recommended sequence (dependencies noted):**

| # | Task | Priority | Dependencies | Est. Complexity |
|---|------|----------|--------------|-----------------|
| 1 | Fix modal CSS display bug | CRITICAL | None | Low |
| 2 | Add Lucide Icons to empty_state | HIGH | None | Medium |
| 3 | Create tournament card layout | HIGH | None | Medium |
| 4 | Create tournament modal | MEDIUM | #1, #3 | Medium |
| 5 | Update tests | LOW | #1-4 | Low |
| 6 | Recompile SCSS | FINAL | #1-4 | Trivial |

---

## 4. Detailed Implementation Plan

### 4.1 Fix Modal CSS Display Bug (CRITICAL)

**File:** `app/static/scss/components/_modals.scss`

**Problem:** Line 11 has `display: flex` which overrides native `<dialog>` hidden state.

**Solution:**
```scss
// BEFORE (broken)
.modal {
  position: fixed;
  inset: 0;
  z-index: $z-modal;
  display: flex;  // ← Always visible!
  ...
}

// AFTER (fixed)
.modal {
  // Native <dialog> is hidden by default
  // Only show when [open] attribute present
  display: none;

  &[open] {
    display: flex;
    position: fixed;
    inset: 0;
    z-index: $z-modal;
    align-items: center;
    justify-content: center;
    padding: $space-4;
    animation: modal-fade-in $transition-normal;
  }

  // Backdrop
  &::backdrop {
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
  }
}
```

**Validation:**
- Navigate to `/admin/users`
- Modal should NOT be visible on page load
- Click "Delete" button → Modal appears
- Click "Cancel" or X → Modal closes

---

### 4.2 Add Lucide Icons to Empty State

**File:** `app/templates/components/empty_state.html`

**Approach:** Create icon name → SVG mapping using Lucide Icons.

**Implementation:**
```html
{#
  Empty State Component with Lucide Icons

  Usage:
    {% set icon = "trophy" %}  {# or "user", "search", "calendar" #}
    {% include "components/empty_state.html" %}
#}

{# Lucide Icon SVG definitions #}
{% set icons = {
  'trophy': '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>',
  'user': '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  'search': '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
  'calendar': '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
  'map-pin': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>'
} %}

<div class="empty-state" role="status" aria-live="polite">
  <div class="empty-state-content">
    {% if icon and icon in icons %}
    <div class="empty-state-icon" aria-hidden="true">{{ icons[icon]|safe }}</div>
    {% endif %}

    <h3 class="empty-state-title">{{ title }}</h3>
    <p class="empty-state-message">{{ message }}</p>

    {% if action_url and action_text %}
    <a href="{{ action_url }}" class="btn btn-primary">
      {{ action_text }}
    </a>
    {% endif %}
  </div>
</div>
```

**SCSS Updates (`_empty-state.scss`):**
```scss
.empty-state-icon {
  width: 80px;
  height: 80px;
  margin-bottom: $space-4;
  color: $color-neutral;  // Gray icon color

  svg {
    width: 100%;
    height: 100%;
  }
}
```

**Validation:**
- Navigate to `/tournaments` with no tournaments
- Should see gray trophy SVG icon (not "trophy" text)

---

### 4.3 Tournament Card Layout

**File:** `app/templates/tournaments/list.html`

**Approach:** Replace table with card-grid using existing `.card-grid` class.

**Card Structure (per mockup):**
```html
{% if tournaments %}
<div class="card-grid">
  {% for tournament in tournaments %}
  <article class="card tournament-card">
    <div class="card-body">
      <div class="tournament-card-header">
        <h3 class="tournament-card-title">{{ tournament.name }}</h3>
        <button type="button" class="btn-icon" aria-label="More options">
          <!-- Vertical dots icon (future: dropdown menu) -->
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg>
        </button>
      </div>

      <div class="tournament-card-meta">
        <div class="card-meta">
          <!-- Calendar icon -->
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
          <span>{{ tournament.created_at.strftime('%d/%m/%Y') }}</span>
        </div>
        {# Location hidden for MVP - requires model change
        <div class="card-meta">
          <svg>...</svg>
          <span>{{ tournament.location }}</span>
        </div>
        #}
      </div>

      <div class="tournament-card-footer">
        {% set phase_class = {
          'registration': 'badge-registration',
          'preselection': 'badge-preselection',
          'pools': 'badge-pools',
          'finals': 'badge-finals',
          'completed': 'badge-completed'
        }.get(tournament.phase.value, 'badge-pending') %}
        <span class="badge {{ phase_class }}">
          {{ tournament.phase.value|capitalize }}
        </span>
        <a href="/tournaments/{{ tournament.id }}" class="btn btn-sm btn-secondary">View</a>
      </div>
    </div>
  </article>
  {% endfor %}
</div>

<p class="text-muted mt-4">
  <strong>Total:</strong> {{ tournaments|length }} tournament{% if tournaments|length != 1 %}s{% endif %}
</p>
{% else %}
  {# Empty state #}
{% endif %}
```

**New SCSS (`_cards.scss` additions):**
```scss
// Tournament card variant
.tournament-card {
  .card-body {
    display: flex;
    flex-direction: column;
    gap: $space-3;
  }
}

.tournament-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.tournament-card-title {
  font-size: $font-size-xl;
  font-weight: $font-weight-semibold;
  margin: 0;
  color: $color-text;
}

.tournament-card-meta {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.tournament-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: $space-3;
  border-top: 1px solid $color-border-light;
}

// Icon-only button (for menu dots)
.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: $radius-sm;
  color: $color-text-muted;
  cursor: pointer;

  &:hover {
    background: $color-neutral-light;
    color: $color-text;
  }
}
```

---

### 4.4 Tournament Creation Modal

**New File:** `app/templates/components/tournament_create_modal.html`

**Structure:**
```html
{#
  Tournament Create Modal Component

  Usage:
    {% include "components/tournament_create_modal.html" %}

  Trigger:
    <button onclick="document.getElementById('create-tournament-modal').showModal()">
      Create Tournament
    </button>
#}

<dialog id="create-tournament-modal" class="modal" aria-labelledby="create-tournament-title">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="create-tournament-title" class="modal-title">Create New Tournament</h3>
      <button
        type="button"
        class="modal-close"
        aria-label="Close"
        onclick="document.getElementById('create-tournament-modal').close()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <form
      method="POST"
      action="/tournaments/create"
      hx-post="/tournaments/create"
      hx-target="#tournament-list"
      hx-swap="innerHTML"
    >
      <div class="modal-body">
        <div class="form-group">
          <label for="tournament-name" class="form-label">Tournament Name <span class="required">*</span></label>
          <input
            type="text"
            id="tournament-name"
            name="name"
            class="form-input"
            placeholder="e.g., Battle-D Winter 2026"
            required
            autofocus
          >
          <small class="form-help">Give your tournament a unique, descriptive name</small>
        </div>
      </div>

      <div class="modal-footer">
        <button
          type="button"
          class="btn btn-secondary"
          onclick="document.getElementById('create-tournament-modal').close()"
        >
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Create Tournament
        </button>
      </div>
    </form>
  </div>
</dialog>

<script>
  // Close modal on successful creation (HTMX afterSwap)
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'tournament-list') {
      document.getElementById('create-tournament-modal').close();
    }
  });

  // ESC key handling
  document.getElementById('create-tournament-modal').addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  });
</script>
```

**Update `tournaments/list.html` button:**
```html
<button
  type="button"
  class="btn btn-create"
  onclick="document.getElementById('create-tournament-modal').showModal()"
>
  + Create Tournament
</button>

{# Include modal at end of content block #}
{% include "components/tournament_create_modal.html" %}
```

**Backend Route Update (optional - for HTMX partial response):**
```python
@router.post("/create")
async def create_tournament(
    request: Request,
    name: str = Form(...),
    ...
):
    # ... existing logic ...

    # Check if HTMX request
    if request.headers.get("HX-Request"):
        # Return just the tournament list partial
        tournaments = await tournament_repo.get_all()
        return templates.TemplateResponse(
            request=request,
            name="tournaments/_list.html",  # Partial template
            context={"tournaments": tournaments, ...}
        )

    # Regular redirect for non-HTMX
    return RedirectResponse(url="/tournaments", status_code=303)
```

---

## 5. Testing Plan

### 5.1 Manual Testing Checklist

**Modal Display Fix (BR-UI-002):**
- [ ] Navigate to `/admin/users` - modal NOT visible
- [ ] Click Delete button - modal appears with backdrop
- [ ] Click Cancel - modal closes
- [ ] Click X - modal closes
- [ ] Press ESC - modal closes
- [ ] Click backdrop - modal remains open (native dialog behavior)

**Empty State Icons (BR-UI-001):**
- [ ] `/tournaments` (empty) - trophy icon visible
- [ ] `/admin/users` (empty) - user icon visible
- [ ] `/admin/users?role_filter=...` (empty filter) - search icon visible

**Tournament Cards (BR-UI-004):**
- [ ] Cards display in 2-column grid on desktop
- [ ] Cards stack on mobile (< 768px)
- [ ] Each card shows: name, date, phase badge
- [ ] "View" button navigates to detail page

**Tournament Modal (BR-UI-003):**
- [ ] "+ Create Tournament" opens modal
- [ ] Form validates (name required)
- [ ] Submit creates tournament
- [ ] Modal closes on success
- [ ] New tournament appears in list

### 5.2 Automated Tests

**Update `tests/e2e/test_delete_modal.py`:**
```python
def test_modal_hidden_on_page_load(self, admin_client):
    """Modal should NOT be visible when page loads.

    Validates: BR-UI-002 Modal display on user action
    """
    response = admin_client.get("/admin/users")
    assert response.status_code == 200

    # Check that no modal is in [open] state
    assert 'class="modal"[open]' not in response.text
    # Or more robust: check dialog doesn't have open attribute
    assert '<dialog id="delete-user-' in response.text  # Modal exists
    assert 'open' not in response.text.split('<dialog')[1].split('>')[0]  # Not open
```

**New `tests/e2e/test_tournament_ui.py`:**
```python
class TestTournamentCards:
    """Tests for tournament card layout (BR-UI-004)."""

    def test_tournaments_display_as_cards(self, staff_client, tournament):
        """Tournaments should display as cards, not table rows."""
        response = staff_client.get("/tournaments")
        assert response.status_code == 200

        # Should have card-grid container
        assert 'class="card-grid"' in response.text

        # Should have tournament cards
        assert 'class="card tournament-card"' in response.text

        # Should NOT have table
        assert '<table' not in response.text

    def test_empty_state_shows_trophy_icon(self, staff_client):
        """Empty tournaments page shows trophy icon."""
        response = staff_client.get("/tournaments")
        assert response.status_code == 200

        # Should have SVG (not text "trophy")
        assert '<svg' in response.text
        assert '>trophy<' not in response.text  # Not raw text


class TestTournamentCreateModal:
    """Tests for tournament creation modal (BR-UI-003)."""

    def test_create_modal_included_in_page(self, staff_client):
        """Create modal should be included in tournaments page."""
        response = staff_client.get("/tournaments")
        assert 'id="create-tournament-modal"' in response.text

    def test_create_button_triggers_modal(self, staff_client):
        """Create button should have onclick to open modal."""
        response = staff_client.get("/tournaments")
        assert 'showModal()' in response.text
```

---

## 6. Risk Analysis

### Risk 1: HTMX Partial Response Complexity
**Concern:** HTMX form submission requires partial template response
**Likelihood:** Medium
**Impact:** Low (fallback: full page redirect works)
**Mitigation:**
- Check `HX-Request` header in route
- Return partial for HTMX, redirect for regular form
- Progressive enhancement - works without JS

### Risk 2: Modal Z-Index Conflicts
**Concern:** Modal might appear behind other elements
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Use existing `$z-modal: 400` from variables
- Test with flash messages, sidebar open

### Risk 3: Icon SVG Size Consistency
**Concern:** SVG icons might render at inconsistent sizes
**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- Set explicit width/height in SCSS
- Use viewBox for scalability

---

## 7. Technical POC

**Status:** Not required
**Reason:** All changes follow existing patterns:
- Modal SCSS follows existing `_modals.scss` structure
- Card grid uses existing `.card-grid` class
- HTMX follows existing patterns in codebase
- Lucide Icons are standard inline SVGs

---

## 8. Documentation Updates

### FRONTEND.md

**Add to Component Library section:**

```markdown
### 9. Lucide Icons

**Icon Library:** [Lucide Icons](https://lucide.dev/) (SVG, MIT License)

**Usage in Templates:**
Icons are embedded as inline SVGs in components for:
- Zero external requests
- CSS styling via `currentColor`
- Accessibility via `aria-hidden="true"`

**Available Icons (empty_state.html):**
- `trophy` - Tournaments empty state
- `user` - Users empty state
- `search` - Search no results
- `calendar` - Date display
- `map-pin` - Location display

**Adding New Icons:**
1. Get SVG from https://lucide.dev/icons/
2. Add to `icons` dict in `components/empty_state.html`
3. Set `stroke-width="1.5"` for consistency
```

**Add to Components section:**

```markdown
### 10. Tournament Card

**Use Case:** Display tournament in card grid format

**HTML Structure:**
```html
<article class="card tournament-card">
  <div class="card-body">
    <div class="tournament-card-header">
      <h3 class="tournament-card-title">{{ name }}</h3>
      <button class="btn-icon">...</button>
    </div>
    <div class="tournament-card-meta">
      <div class="card-meta">
        <svg>...</svg>
        <span>{{ date }}</span>
      </div>
    </div>
    <div class="tournament-card-footer">
      <span class="badge">{{ phase }}</span>
      <a href="..." class="btn btn-sm">View</a>
    </div>
  </div>
</article>
```
```

---

## 9. Implementation Checklist

**Pre-Implementation:**
- [ ] User approved this plan
- [ ] SCSS watch mode running

**Implementation:**
- [ ] Fix `_modals.scss` display bug
- [ ] Update `_empty-state.scss` for icon sizing
- [ ] Add `tournament-card` styles to `_cards.scss`
- [ ] Update `components/empty_state.html` with icon mapping
- [ ] Update `tournaments/list.html` with card layout
- [ ] Create `components/tournament_create_modal.html`
- [ ] Add modal include and button trigger to list.html
- [ ] Recompile SCSS (`sass app/static/scss:app/static/css`)

**Verification:**
- [ ] Manual testing checklist complete
- [ ] Automated tests passing
- [ ] No console errors
- [ ] Responsive layout works

**Documentation:**
- [ ] FRONTEND.md updated

---

## 10. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed implementation order acceptable
