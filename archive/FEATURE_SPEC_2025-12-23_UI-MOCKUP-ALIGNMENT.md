# Feature Specification: UI Mockup Alignment Fixes

**Date:** 2025-12-23
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Business Rules & Acceptance Criteria](#3-business-rules--acceptance-criteria)
4. [Current State Analysis](#4-current-state-analysis)
5. [Implementation Recommendations](#5-implementation-recommendations)

---

## 1. Problem Statement

The current UI implementation deviates from the approved Figma mockups in four key areas:
1. Empty state shows "trophy" text instead of an actual trophy icon
2. Delete modal displays automatically when visiting the Users page
3. Tournament creation form is a separate page instead of a modal
4. Tournament list uses a table layout instead of card-based design

These inconsistencies create a "Frankenstein" UX where the app doesn't match the user's expectations from the approved designs.

---

## 2. Executive Summary

### Scope
Fix 4 UI bugs/gaps to align implementation with Figma mockups.

### What's Broken

| Issue | Type | Severity | Location |
|-------|------|----------|----------|
| Trophy text instead of icon | BUG | Medium | `components/empty_state.html:21` |
| Delete modal auto-displays | BUG | High | `components/delete_modal.html` + `_modals.scss` |
| Tournament form not a modal | GAP | Medium | `tournaments/create.html` |
| Tournaments not cards | GAP | Medium | `tournaments/list.html` |

### Reference Mockups
- **Image 5:** Create Tournament Modal (French: "Créer un nouveau tournoi")
- **Image 6:** Empty State with Trophy Icon
- **Image 7:** Tournament Cards with tabs (Upcoming/Completed)

---

## 3. Business Rules & Acceptance Criteria

### 3.1 Empty State Icon Display

**Business Rule BR-UI-001: Empty State Icons**
> Empty states must display visual icons (SVG), not text placeholders.

**Acceptance Criteria:**
```gherkin
Feature: Empty state icon display
  Scenario: Tournament list empty state shows trophy icon
    Given I am on the tournaments page
    And there are no tournaments
    When the page loads
    Then I should see a trophy SVG icon
    And I should NOT see the text "trophy"

  Scenario: Users list empty state shows user icon
    Given I am on the admin users page
    And there are no users
    When the page loads
    Then I should see a user SVG icon
```

### 3.2 Delete Modal Display Behavior

**Business Rule BR-UI-002: Modal Display on User Action**
> Modals must only display when explicitly triggered by user action (button click), never on page load.

**Acceptance Criteria:**
```gherkin
Feature: Delete modal trigger behavior
  Scenario: Modal hidden on page load
    Given I navigate to /admin/users
    When the page loads
    Then the delete modal should NOT be visible
    And the page content should be fully accessible

  Scenario: Modal opens on delete button click
    Given I am on the admin users page
    And users exist in the system
    When I click the "Delete" button for a user
    Then the delete modal should appear
    And the modal should have a backdrop overlay
```

### 3.3 Tournament Creation Modal

**Business Rule BR-UI-003: Tournament Creation via Modal**
> Tournament creation should use a modal dialog (per mockup) to keep users in context.

**Acceptance Criteria:**
```gherkin
Feature: Tournament creation modal
  Scenario: Create tournament button opens modal
    Given I am on the tournaments page
    When I click "+ Create Tournament"
    Then a modal dialog should appear
    And the modal should contain the tournament form
    And the tournaments list should remain visible behind

  Scenario: Modal form submission creates tournament
    Given the create tournament modal is open
    And I fill in "Tournament Name" with "Winter 2026"
    When I click "Create Tournament"
    Then the tournament should be created
    And the modal should close
    And the new tournament should appear in the list
```

### 3.4 Tournament Card Layout

**Business Rule BR-UI-004: Tournament Card Display**
> Tournaments should display as cards with date, location, and phase badge (per mockup).

**Acceptance Criteria:**
```gherkin
Feature: Tournament card layout
  Scenario: Tournaments display as cards
    Given I am on the tournaments page
    And tournaments exist
    When the page loads
    Then tournaments should display as cards (not table rows)
    And each card should show tournament name
    And each card should show date with calendar icon
    And each card should show location with pin icon
    And each card should show phase badge

  Scenario: Card grid layout
    Given there are multiple tournaments
    When I view the tournaments page
    Then cards should display in a responsive grid
    And cards should be side-by-side on desktop
    And cards should stack on mobile
```

---

## 4. Current State Analysis

### 4.1 Empty State Icon Bug

**Location:** `app/templates/components/empty_state.html:21`

**Current Implementation:**
```html
{% if icon %}
<div class="empty-state-icon" aria-hidden="true">{{ icon }}</div>
{% endif %}
```

**Problem:** The `icon` variable is passed as a text string ("trophy", "user", "search") but rendered directly, displaying the word instead of an actual icon.

**Evidence from templates:**
- `tournaments/list.html:84`: `{% set icon = "trophy" %}`
- `admin/users.html:92`: `{% set icon = "user" %}`

**Expected (per mockup):** SVG trophy icon displayed visually.

### 4.2 Modal Auto-Display Bug

**Location:** `app/static/scss/components/_modals.scss:7-14`

**Current Implementation:**
```scss
.modal {
  position: fixed;
  inset: 0;
  z-index: $z-modal;
  display: flex;  // ← PROBLEM: Always visible
  align-items: center;
  justify-content: center;
```

**Problem:** The modal has `display: flex` by default, making it visible on page load. The `<dialog>` element's native behavior is overridden by this CSS.

**Native `<dialog>` behavior:** Should be hidden until `.showModal()` is called.

**Evidence:** Screenshot shows modal overlay visible immediately on page load at `/admin/users`.

### 4.3 Tournament Form Not Modal

**Location:** `app/templates/tournaments/create.html`

**Current Implementation:** Full-page form at route `/tournaments/create`

**Mockup shows:** Modal dialog overlaying the tournament list page

**Gap:** Form should be a modal triggered from the list page, not a separate route.

### 4.4 Tournament Table vs Cards

**Location:** `app/templates/tournaments/list.html:34-74`

**Current Implementation:**
```html
<div class="table-wrapper">
    <table class="table">
        <thead>...</thead>
        <tbody>...</tbody>
    </table>
</div>
```

**Mockup shows:**
- Card grid layout (2 columns on desktop)
- Each card with: Name, Date (calendar icon), Location (pin icon), Phase badge
- Tabs: "Tournois à venir" (Upcoming) / "Tournois terminés" (Completed)

**Gap:** Complete redesign from table to card layout needed.

---

## 5. Implementation Recommendations

### 5.1 Critical (Before Production)

1. **Fix modal CSS display bug** (BR-UI-002)
   - Change `.modal { display: flex }` to `display: none`
   - Add `.modal[open] { display: flex }` for when dialog is shown
   - This is a blocking bug making the users page unusable

2. **Fix empty state icon rendering** (BR-UI-001)
   - Create SVG icon mapping in empty_state.html
   - Or create SCSS-based icon component
   - Icons needed: trophy, user, search

### 5.2 Recommended

3. **Convert tournament form to modal** (BR-UI-003)
   - Create `components/tournament_create_modal.html`
   - Add HTMX for inline form submission
   - Keep `/tournaments/create` route for progressive enhancement

4. **Convert tournament list to cards** (BR-UI-004)
   - Replace table with card grid
   - Add new SCSS in `_cards.scss`
   - Implement Upcoming/Completed tabs (optional for MVP)

### 5.3 Nice-to-Have (Future)

5. **Tournament tabs** (Upcoming vs Completed)
   - Per mockup Image 7
   - HTMX filtering

6. **Location field on tournament**
   - Mockup shows "Paris, France" - not in current model
   - Would require domain model change

---

## 6. Pattern Scan Results

**Pattern searched:** Similar icon text rendering issues

**Search command:**
```bash
grep -rn '{% set icon' app/templates/
```

**Results:**
| File | Line | Icon Value |
|------|------|------------|
| tournaments/list.html | 84 | "trophy" |
| admin/users.html | 87 | "search" |
| admin/users.html | 92 | "user" |
| dancers/list.html | (if exists) | TBD |

**Decision:**
- [x] Fix all in this feature - all use same empty_state.html component

---

## 7. Open Questions & Answers

- **Q1:** Should the tournament modal include date and location fields (per mockup)?
  - **A:** No - keep simple with Name only for now. Additional fields can be added later.

- **Q2:** Should we implement the Upcoming/Completed tabs now?
  - **A:** No - skip for MVP. Show all tournaments in one list.

- **Q3:** What icons should be used?
  - **A:** Lucide Icons - lightweight SVGs, good match for mockup style.

---

## 8. User Confirmation

- [x] Confirm the 4 issues are accurately described
- [x] Tournament form: Keep simple (Name only), convert to modal
- [x] Tabs: Skip for MVP
- [x] Icons: Use Lucide Icons

---

## 9. Scope Summary (MVP)

**In Scope:**
1. Fix modal CSS bug (display on user action only)
2. Fix empty state icons (Lucide SVGs instead of text)
3. Convert tournament form to modal
4. Convert tournament list from table to cards

**Out of Scope (Future):**
- Tournament date, country, city fields
- Upcoming/Completed tabs
- Location display on cards
