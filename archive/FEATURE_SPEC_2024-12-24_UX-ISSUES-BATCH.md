# Feature Specification: UX Issues Batch Fix

**Date:** 2024-12-24
**Status:** Ready for Implementation
**Last Updated:** 2024-12-24 (Business rules validated with user)

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Five Whys Analysis](#3-five-whys-analysis)
4. [Success Criteria](#4-success-criteria)
5. [User Flow Diagram](#5-user-flow-diagram)
6. [Business Rules & Acceptance Criteria](#6-business-rules--acceptance-criteria)
7. [Gap Analysis](#7-gap-analysis)
8. [Current State Analysis](#8-current-state-analysis)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [UI Specifications](#10-ui-specifications)
11. [Implementation Recommendations](#11-implementation-recommendations)
12. [Appendix: Reference Material](#12-appendix-reference-material)

---

## 1. Problem Statement

Multiple UX inconsistencies and missing functionalities are degrading the user experience in the admin interface. These issues range from non-functional UI elements (dead buttons) to missing critical workflow actions (no way to advance phases), creating confusion and **blocking staff from completing essential tournament management tasks**.

---

## 2. Executive Summary

### Scope
This analysis covers 6 UX issues reported via screenshots, plus 1 harmonization task identified during analysis:

| # | Issue | Type | Severity |
|---|-------|------|----------|
| 1 | Three dots menu does nothing | BUG | Low |
| 2 | Empty state loupe icon misaligned | BUG | Low |
| 3 | Cannot remove categories | GAP | Medium |
| 4 | User/Dancer forms are full pages, not modals | GAP | Medium |
| 5 | Modals positioned upper-left instead of centered | BUG | High |
| 6 | No way to advance tournament phase from detail page | GAP | **Critical** |
| 7 | Modal submission patterns inconsistent | TECH DEBT | Medium |

### What Works ✅
| Feature | Status |
|---------|--------|
| Tournament creation modal | Functional (but needs HTMX harmonization) |
| Dancer/User list pages | Production Ready |
| Search functionality | Functional |
| Delete modals | Functional (but positioning issue) |
| Phase advancement backend | Exists at `/event/{id}/advance` (**DEPRECATED**) |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| Three dots menu does nothing | BUG | `tournaments/list.html:46-52` |
| Empty state icon misaligned | BUG | CSS - `empty_state.html` styling |
| Cannot remove category | GAP | `tournaments/detail.html` - no action |
| Creation forms not modals | GAP | `admin/create_user.html`, `dancers/create.html` |
| Modal positioning wrong | BUG | `main.css:984` - dialog centering |
| No phase advancement UI | GAP | `tournaments/detail.html` - no button |
| Modal patterns inconsistent | TECH DEBT | `tournament_create_modal.html` uses plain POST |

### Key Business Rules Defined
- **BR-UX-001:** Tournament card actions menu (View, Rename, Delete) - **Rename ALWAYS allowed**
- **BR-UX-002:** Consistent empty state display (centered alignment)
- **BR-UX-003:** Category removal - **CASCADE deletes Performers** (not Dancers), REGISTRATION phase only
- **BR-UX-004:** Consistent creation patterns (modals with HTMX + HX-Redirect)
- **BR-UX-005:** Modal positioning (centered viewport)
- **BR-UX-006:** Phase advancement UI - **NEW endpoint** at `/tournaments/{id}/advance` (deprecates `/event/`)
- **BR-UX-007:** Modal pattern harmonization - **ALL modals use HTMX + HX-Redirect** (including existing tournament create)

---

## 3. Five Whys Analysis

### Who is affected?
- **Admin users:** Cannot advance tournament phases from detail page (must know hidden route)
- **Staff users:** Confused by non-functional buttons, inconsistent form patterns
- **All users:** Poor UX from misaligned elements and off-center modals

### What is the current pain point?
1. **Dead UI elements:** Three dots button exists but does nothing - suggests incomplete implementation
2. **Missing critical functionality:** No visible way to advance tournament phases from prep mode
3. **Inconsistent patterns:** Tournament creates via modal, but User/Dancer create via full page
4. **Visual bugs:** Modals render in wrong position, empty states misaligned

### When does this problem occur?
- **Issue #1 (dots):** Every time user views tournament list
- **Issue #2 (alignment):** When search returns no results
- **Issue #3 (category):** When trying to correct category mistakes during setup
- **Issue #4 (forms):** Every time creating a user or dancer
- **Issue #5 (modals):** Every time a modal opens (tournament create, delete confirms)
- **Issue #6 (phase):** When tournament is ready to advance from Registration

### Where in the user journey does this happen?
```
Tournament Setup Flow:
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. Create Tournament (modal) ────────────────────────> ✅   │
  │ 2. View in list (three dots broken) ──────────────────> 🚨 │
  │ 3. Add categories ────────────────────────────────────> ✅  │
  │ 4. Remove wrong category ─────────────────────────────> 🚨 │
  │ 5. Register dancers ──────────────────────────────────> ✅  │
  │ 6. Create new dancer (full page, not modal) ──────────> ⚠️  │
  │ 7. Advance to Preselection ───────────────────────────> 🚨 │
  └─────────────────────────────────────────────────────────────┘
```

### Why does this matter to the business?
- **Blocked workflows:** Staff cannot advance tournaments without knowing hidden URL
- **Lost trust:** Non-functional buttons suggest unfinished product
- **Inefficiency:** Full page navigation for simple forms wastes time
- **Unprofessional appearance:** Misaligned elements and off-center modals

---

## 4. Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| All interactive elements functional | Dead button count | 0 |
| Consistent modal positioning | Off-center modals | 0 |
| Complete tournament workflow | Steps blocked by missing UI | 0 |
| Consistent creation patterns | Full-page forms for simple entities | 0 |
| Visual alignment | Misaligned empty states | 0 |

**User would say "this is better" when:**
- "I can manage tournaments entirely from the detail page without needing hidden URLs"
- "All buttons actually do something when I click them"
- "Creating users/dancers is as smooth as creating tournaments"
- "Modals appear in the center of my screen like they should"

---

## 5. User Flow Diagram

### Tournament Setup Flow (Current vs Desired)

```
═══════════════════════════════════════════════════════════════════════════════
 PHASE: REGISTRATION (Setup)                                [Status: CREATED]
═══════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  TOURNAMENTS LIST PAGE                                                  │
  │                                                                         │
  │  ┌─────────────────────────────┐                                       │
  │  │ Tournament Card             │                                       │
  │  │ "Winter 2026"               │                                       │
  │  │                    [⋮]  ◄───┼─── 🚨 BUG: Does nothing               │
  │  │ 23/12/2025                  │        DESIRED: Dropdown menu         │
  │  │ [REGISTRATION]      [View]  │        (View, Rename, Delete)         │
  │  └─────────────────────────────┘                                       │
  │                                                                         │
  │  [+ Create Tournament] ◄───────────── Opens modal (but off-center) 🚨  │
  └─────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼ Click "View"

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  TOURNAMENT DETAIL PAGE                                                 │
  │                                                                         │
  │  Tournament: Winter 2026                                                │
  │  Status: CREATED    Phase: REGISTRATION                                 │
  │                                                                         │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │  Categories                                                      │   │
  │  │  ┌────────────┬──────┬────────┬─────────┬─────────┬───────────┐ │   │
  │  │  │ Name       │ Type │ Reg'd  │ Min Req │ Actions │           │ │   │
  │  │  ├────────────┼──────┼────────┼─────────┼─────────┼───────────┤ │   │
  │  │  │ Hip Hop    │ 1v1  │ 5      │ 5       │ [Reg]   │   🚨      │ │   │
  │  │  │ Boys       │      │        │         │         │ No Remove │ │   │
  │  │  └────────────┴──────┴────────┴─────────┴─────────┴───────────┘ │   │
  │  │                                                                  │   │
  │  │  [+ Add Category]                                                │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │                                                                         │
  │  🚨 GAP: NO "ADVANCE TO PRESELECTION" BUTTON                           │
  │                                                                         │
  │  DESIRED:                                                               │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │  [Advance to Preselection →]     (Admin only, when ready)       │   │
  │  │  Shows detailed preview modal before confirming                  │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 VALIDATION CHECK (REGISTRATION → PRESELECTION):
═══════════════════════════════════════════════════════════════════════════════

  ✅ Each category has minimum (groups_ideal × 2) + 1 performers
  ✅ No other tournament is ACTIVE
  ⚠️  Cannot validate from UI - no button exists!

  [ADVANCE PHASE] ─────────────────────────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE: PRESELECTION                                         [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════
```

### Modal Positioning Issue

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  CURRENT (BUG):                         DESIRED:                        │
  │                                                                         │
  │  ┌──────────────┐                       ┌─────────────────────────────┐│
  │  │ Modal        │                       │                             ││
  │  │ (upper-left) │                       │    ┌──────────────┐         ││
  │  └──────────────┘                       │    │   Modal      │         ││
  │                                         │    │  (centered)  │         ││
  │                                         │    └──────────────┘         ││
  │                                         │                             ││
  │        [Page content dimmed]            │    [Page content dimmed]    ││
  │                                         └─────────────────────────────┘│
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Business Rules & Acceptance Criteria

### 6.1 Three Dots Menu on Tournament Card (BR-UX-001)

**Business Rule BR-UX-001: Tournament Card Actions Menu**
> Tournament cards should provide quick access to common actions via a dropdown menu triggered by the three dots button.

**User Decisions:**
- Include View, Rename, Delete options (not full Edit)
- **Rename is ALWAYS allowed** (any status: CREATED, ACTIVE, COMPLETED)
- Delete is only allowed when status = CREATED

**Acceptance Criteria:**
```gherkin
Feature: Tournament Card Actions Menu
  As a staff member
  I want to quickly access tournament actions from the card
  So that I can manage tournaments efficiently

  Scenario: Open actions menu
    Given I am on the tournaments list page
    When I click the three dots button on a tournament card
    Then a dropdown menu appears with options:
      | Option  | Availability                    |
      | View    | Always                          |
      | Rename  | Always (any status)             |
      | Delete  | Only if status = CREATED        |

  Scenario: Rename tournament at any status
    Given an ACTIVE tournament "Summer Battle 2024"
    And the actions menu is open
    When I click "Rename"
    Then a modal opens with a text input pre-filled with "Summer Battle 2024"
    And I can submit the new name or cancel
    And the rename succeeds regardless of tournament status

  Scenario: Rename uses HTMX with HX-Redirect
    Given the rename modal is open
    When I submit a new name "Winter Battle 2024"
    Then the form submits via HTMX
    And on success, HX-Redirect returns to the tournaments list
    And a flash message confirms "Tournament renamed successfully"

  Scenario: Delete tournament from menu
    Given the actions menu is open on a CREATED tournament
    When I click "Delete"
    Then a confirmation modal appears
    And I can confirm or cancel the deletion

  Scenario: Cannot delete active tournament
    Given the actions menu is open on an ACTIVE tournament
    Then the "Delete" option is disabled or hidden
```

---

### 6.2 Empty State Icon Alignment (BR-UX-002)

**Business Rule BR-UX-002: Consistent Empty State Display**
> Empty state components must display with centered alignment for icon, title, and message.

**Acceptance Criteria:**
```gherkin
Feature: Empty State Alignment
  As a user
  I want empty states to be visually consistent
  So that the interface feels polished

  Scenario: Search with no results
    Given I am on the dancers list page
    When I search for a non-existent dancer "tyga"
    Then the empty state displays with:
      | Element | Alignment | Margin  |
      | Icon    | Center    | 0 auto  |
      | Title   | Center    | auto    |
      | Message | Center    | auto    |
    And the icon appears directly above the title (not offset)
```

---

### 6.3 Category Removal (BR-UX-003)

**Business Rule BR-UX-003: Category Removal with CASCADE Deletion**
> Staff can remove a category from a tournament during REGISTRATION phase. Removing a category CASCADE DELETES all associated Performer records (tournament participation), but does NOT delete the underlying Dancer profiles.

**⚠️ IMPORTANT - Updated from DOMAIN_MODEL.md:**
> Original rule stated "only when empty". **User clarified:** Categories CAN be deleted even with performers registered. The Performers (tournament participation) are cascade-deleted, but Dancer profiles remain intact.

**User Decisions:**
- **CASCADE deletion**: Deleting category removes all Performer records
- **Dancers preserved**: Underlying Dancer profiles are NOT deleted
- **REGISTRATION phase only**: Cannot delete categories after phase advances
- **Simple confirmation**: No detailed warning about performers being removed
- **HTMX in-place update**: Row removed without page reload

**Acceptance Criteria:**
```gherkin
Feature: Category Removal with Cascade
  As a staff member
  I want to remove categories from a tournament
  So that I can correct mistakes during setup

  Scenario: Remove empty category
    Given a tournament in REGISTRATION phase
    And a category "Hip Hop Boys" with 0 registered performers
    When I click "Remove" on the category row
    Then a confirmation modal appears asking "Remove category 'Hip Hop Boys'?"
    And upon confirmation, the category is deleted
    And the category row is removed via HTMX (no page reload)

  Scenario: Remove category with performers (CASCADE)
    Given a tournament in REGISTRATION phase
    And a category "Krump" with 3 registered performers
    When I click "Remove" on the category row
    Then a confirmation modal appears asking "Remove category 'Krump'?"
    And upon confirmation:
      - The category is deleted
      - All 3 Performer records are CASCADE deleted
      - The underlying Dancer profiles remain intact
      - The category row is removed via HTMX

  Scenario: Dancer profiles preserved after cascade
    Given a dancer "B-Boy Storm" registered in category "Breaking"
    When the category "Breaking" is deleted
    Then the Performer record linking Storm to the tournament is deleted
    But the Dancer profile for "B-Boy Storm" still exists in the system
    And Storm can be registered in other categories or tournaments

  Scenario: Cannot remove category after registration phase
    Given a tournament in PRESELECTION phase
    Then no "Remove" action appears in the Actions column
    And the category table shows no remove buttons

  Scenario: HTMX removes row in-place
    Given a category row is displayed in the table
    When deletion is confirmed
    Then the row is removed via hx-target="closest tr" hx-swap="delete"
    And no page reload occurs
```

**Technical Note - HTTP Method:**
- Use `DELETE /tournaments/{id}/categories/{cat_id}` (REST-style)
- Requires JavaScript/HTMX (not plain form submission)

---

### 6.4 User/Dancer Creation Forms as Modals (BR-UX-004)

**Business Rule BR-UX-004: Consistent Creation Patterns with HTMX**
> Creation forms for simple entities should use modals with HTMX + HX-Redirect pattern for consistent UX.

**Current State:**
- Tournament creation: Modal ✅ (but uses plain form POST - needs HTMX update)
- User creation: Full page ❌ (`/admin/users/create`)
- Dancer creation: Full page ❌ (`/dancers/create`)

**User Decisions:**
- **HTMX + HX-Redirect pattern**: All modals use `hx-post` and return `HX-Redirect` header on success
- **Harmonize ALL modals**: Including existing tournament create modal (breaking change accepted)
- **Validation in modal**: Errors display inline, modal stays open
- **Success = redirect**: On success, HX-Redirect refreshes the list page with flash message

**Acceptance Criteria:**
```gherkin
Feature: Modal-Based Creation Forms with HTMX
  As a staff member
  I want creation forms to open in modals
  So that I stay in context and can quickly return to the list

  Scenario: Create user from users list
    Given I am on the users list page
    When I click "+ Create User"
    Then a modal opens with the user creation form
    And the form has hx-post="/admin/users/create"
    When I submit valid data
    Then the server returns HX-Redirect header to /admin/users
    And the page redirects with flash message "User created successfully"

  Scenario: Create dancer from dancers list
    Given I am on the dancers list page
    When I click "+ Create Dancer"
    Then a modal opens with the dancer creation form
    And the form has hx-post="/dancers/create"
    When I submit valid data
    Then the server returns HX-Redirect header to /dancers
    And the page redirects with flash message "Dancer created successfully"

  Scenario: Form validation in modal
    Given the dancer creation modal is open
    When I submit with invalid data (missing required fields)
    Then the server returns the form partial with validation errors
    And the modal body is swapped with the error-containing form
    And the modal remains open for correction

  Scenario: HTMX submission pattern
    Given any creation modal is open
    Then the form element has:
      | Attribute   | Value                           |
      | hx-post     | /entity/create                  |
      | hx-target   | #modal-id .modal-body           |
      | hx-swap     | innerHTML                       |
    And on success, server returns:
      | Header      | Value                           |
      | HX-Redirect | /entity-list-url                |
```

**See also:** BR-UX-007 for harmonization of existing tournament create modal.

---

### 6.5 Modal Centering (BR-UX-005)

**Business Rule BR-UX-005: Modal Positioning**
> All modals must be vertically and horizontally centered on the viewport with a semi-transparent backdrop.

**Current State:** Modals appear in upper-left corner (Image #5).

**Evidence from CSS (`main.css:984-993`):**
```css
.modal[open] {
  display: flex;
  position: fixed;
  inset: 0;
  z-index: 400;
  align-items: center;
  justify-content: center;
  /* ... */
}
```
CSS appears correct, but `<dialog>` element may have browser-specific behavior overriding these styles.

**Acceptance Criteria:**
```gherkin
Feature: Centered Modals
  As a user
  I want modals to be centered on the screen
  So that they draw my attention and feel professional

  Scenario: Tournament creation modal positioning
    Given I am on the tournaments list page
    When I click "+ Create Tournament"
    Then the modal appears centered:
      | Axis       | Position           |
      | Horizontal | 50% viewport width |
      | Vertical   | 50% viewport height|
    And a backdrop dims the background content

  Scenario: Delete confirmation modal positioning
    Given I click a delete button
    Then the confirmation modal appears centered
    And the backdrop prevents interaction with content behind
```

---

### 6.6 Tournament Phase Advancement (BR-UX-006)

**Business Rule BR-UX-006: Phase Advancement UI with NEW Endpoint**
> Admins must be able to advance a tournament to the next phase from the tournament detail page when all readiness criteria are met.

**Current State:**
- Backend exists: `POST /event/{tournament_id}/advance` - **⚠️ DEPRECATED**
- UI gap: No button on tournament detail page
- Result: **Staff cannot advance from REGISTRATION to PRESELECTION**

**User Decision - NEW ENDPOINT:**
> Create **NEW endpoint** at `POST /tournaments/{tournament_id}/advance`
> The existing `/event/{id}/advance` endpoint is **DEPRECATED** and should be removed from the codebase in a future cleanup.

**Rationale:** The `/event/` prefix is for event mode operations. Phase advancement is a tournament management operation and belongs under `/tournaments/`.

**Phase Sequence (from DOMAIN_MODEL.md):**
```
Registration → Preselection → Pools → Finals → Completed
```

**User Decision:** Show detailed preview of what will happen (battles to be created, status changes).

**Acceptance Criteria:**
```gherkin
Feature: Tournament Phase Advancement
  As an admin
  I want to advance the tournament to the next phase
  So that the competition can progress through its stages

  Scenario: Advance from Registration to Preselection
    Given I am an admin viewing a tournament in REGISTRATION phase
    And all categories have at least minimum required performers
    When I click "Advance to Preselection →"
    Then a detailed preview modal appears showing:
      | Information                              |
      | Current phase: REGISTRATION              |
      | Next phase: PRESELECTION                 |
      | Status will change: CREATED → ACTIVE    |
      | Battles to be generated: X battles      |
      | Categories ready: 1/1                    |
    And upon confirmation:
      - Form POSTs to /tournaments/{id}/advance (NEW endpoint)
      - Tournament phase changes to PRESELECTION
      - Tournament status changes to ACTIVE
      - Preselection battles are generated
      - Page redirects to Event Mode

  Scenario: Cannot advance when not ready
    Given I am viewing a tournament in REGISTRATION phase
    And "Hip Hop Boys" category has 3 performers (min required: 5)
    Then the "Advance Phase" button is disabled
    And a message shows: "Category 'Hip Hop Boys' needs 2 more performers"

  Scenario: Only admin can advance
    Given I am logged in as staff (not admin)
    When I view the tournament detail page
    Then I should not see the "Advance Phase" button

  Scenario: No advance on completed tournament
    Given a tournament in COMPLETED phase
    Then no "Advance Phase" button should appear
```

**Technical Note - Endpoint Migration:**
```
OLD (DEPRECATED): POST /event/{tournament_id}/advance
NEW:              POST /tournaments/{tournament_id}/advance
```
The new endpoint should replicate the logic from the deprecated endpoint. The old endpoint should be marked for removal in a future PR.

---

### 6.7 Modal Pattern Harmonization (BR-UX-007)

**Business Rule BR-UX-007: Unified Modal Submission Pattern**
> ALL modals in the application must use the HTMX + HX-Redirect pattern for form submission. This includes updating the existing tournament create modal.

**Current State:**
- `tournament_create_modal.html`: Uses plain `<form method="POST">` (inconsistent)
- New modals (user, dancer, rename): Will use HTMX pattern

**User Decision:**
> **Harmonize ALL modals** - Update existing tournament create modal to use HTMX pattern. This is a breaking change but ensures consistency.

**Acceptance Criteria:**
```gherkin
Feature: Unified Modal Pattern
  As a developer
  I want all modals to use the same submission pattern
  So that the codebase is consistent and maintainable

  Scenario: Tournament create modal uses HTMX
    Given I am on the tournaments list page
    When I open the "Create Tournament" modal
    Then the form element has:
      | Attribute   | Value                           |
      | hx-post     | /tournaments/create             |
      | hx-target   | #create-tournament-modal .modal-body |
      | hx-swap     | innerHTML                       |

  Scenario: All modals follow same pattern
    Given any creation/action modal in the application
    Then it uses hx-post for submission
    And on success, server returns HX-Redirect header
    And validation errors swap the modal body content

  Scenario: Consistent success feedback
    Given I successfully submit any modal form
    Then the page redirects via HX-Redirect
    And a flash message confirms the action
```

**Files to Update:**
1. `app/templates/components/tournament_create_modal.html` - Convert from plain POST to HTMX
2. `app/routers/tournaments.py` - Update `/create` endpoint to return HX-Redirect on success

**HTMX Modal Pattern (Standard):**
```html
<form hx-post="/entity/create"
      hx-target="#modal-id .modal-body"
      hx-swap="innerHTML">
    <!-- form fields -->
</form>
```

**Backend Pattern (Standard):**
```python
@router.post("/create")
async def create_entity(request: Request, ...):
    # Validate
    if errors:
        return templates.TemplateResponse(
            "components/entity_form_partial.html",
            {"errors": errors, ...}
        )

    # Create entity
    entity = await repo.create(...)

    # Success - HTMX redirect
    add_flash_message(request, "Entity created successfully", "success")
    response = HTMLResponse(status_code=200)
    response.headers["HX-Redirect"] = "/entities"
    return response
```

---

## 7. Gap Analysis

### Issue #1: Three Dots Menu
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| Button | Exists, no handler | Dropdown with actions | Missing JS + dropdown HTML | Confuses users, suggests broken UI |
| Rename | N/A | Always allowed (any status) | New endpoint + modal | - |

### Issue #2: Empty State Alignment
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| Icon | Misaligned (left?) | Centered | CSS adjustment | Unprofessional appearance |

### Issue #3: Category Removal
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| Remove action | None | Button with modal confirm | Backend route + UI | Cannot correct setup mistakes |
| Cascade behavior | N/A | DELETE Performers, keep Dancers | New business logic | - |
| HTMX | N/A | Row removed in-place | hx-delete + swap | Smooth UX |

### Issue #4: Creation Forms
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| User create | Full page | Modal with HTMX | New component + HX-Redirect | Workflow interruption |
| Dancer create | Full page | Modal with HTMX | New component + HX-Redirect | Workflow interruption |

### Issue #5: Modal Positioning
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| Position | Upper-left | Centered | CSS fix for `<dialog>` | Unprofessional, poor UX |

### Issue #6: Phase Advancement
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| UI | None on detail page | Button + preview modal | New UI component | **CRITICAL: Blocks entire workflow** |
| Backend | Exists at `/event/` | NEW at `/tournaments/` | New endpoint (old deprecated) | Route consistency |

### Issue #7: Modal Harmonization (NEW)
| Aspect | Current State | Desired State | Gap | Business Impact |
|--------|---------------|---------------|-----|-----------------|
| Tournament modal | Plain form POST | HTMX + HX-Redirect | Refactor existing component | Consistency |
| All modals | Inconsistent patterns | Unified HTMX pattern | Standardize all | Maintainability |

---

## 8. Current State Analysis

### 8.1 Three Dots Menu (Issue #1)
**File:** `app/templates/tournaments/list.html:46-52`
**Implementation Status:** ❌ Partial - Button exists, no functionality
**Evidence:**
```html
<button type="button" class="btn-icon" aria-label="More options">
    <svg><!-- vertical dots icon --></svg>
</button>
```
No `onclick`, no dropdown menu component. No dropdown components exist anywhere in templates.

**Pattern Scan:**
```bash
grep -rn "dropdown" app/templates/
# Result: No matches found
```

---

### 8.2 Empty State Alignment (Issue #2)
**File:** `app/templates/components/empty_state.html`
**CSS:** `main.css:1460-1511`
**Implementation Status:** ⚠️ CSS exists but not working correctly
**Evidence:**
```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  /* ... */
}
```
CSS looks correct - may be SVG-specific issue with width/centering.

**Pattern Scan:**
```bash
grep -rn "empty-state" app/templates/
# Found in: components/empty_state.html, event/_current_battle.html
```

---

### 8.3 Category Removal (Issue #3)
**File:** `app/templates/tournaments/detail.html:94`
**Implementation Status:** ❌ Not implemented
**Evidence:**
```html
<td>
    <a href="/registration/{{ tournament.id }}/{{ item.category.id }}">Register Dancers</a>
</td>
```
Actions column only has "Register Dancers" link.

**Backend Status:** No route exists for category deletion.

---

### 8.4 Creation Forms (Issue #4)
**Files:**
- `app/templates/admin/create_user.html` (full page)
- `app/templates/dancers/create.html` (full page)
**Implementation Status:** ❌ Inconsistent with tournament pattern

**Pattern Scan:**
```bash
grep -rn 'href=.*create' app/templates/
# Results:
# dancers/list.html:13: <a href="/dancers/create"...
# admin/users.html:13: <a href="/admin/users/create"...
# registration/_available_list.html:37: <a href="/dancers/create"...
# registration/register.html:191: <a href="/dancers/create"...
```

All 4 references navigate away instead of opening modals.

---

### 8.5 Modal Positioning (Issue #5)
**File:** `app/static/css/main.css:978-1024`
**Implementation Status:** ⚠️ CSS appears correct but not working

**Evidence:** `<dialog>` element has browser default positioning that may override CSS. Need to add explicit styling:
```css
dialog {
  margin: auto;  /* Centers dialog in viewport */
}
```

---

### 8.6 Phase Advancement (Issue #6)
**File:** `app/templates/tournaments/detail.html`
**Implementation Status:** ❌ UI not implemented

**Backend Status:** ✅ Route exists at `app/routers/event.py:248`:
```python
@router.post("/{tournament_id}/advance", response_class=HTMLResponse)
async def advance_tournament_phase(...)
```

**Gap:** Route is under `/event/` prefix, but tournament detail page is at `/tournaments/{id}`. Users have no way to trigger advancement from prep mode.

---

## 9. Non-Functional Requirements

### 9.1 Performance
- Modal opening: < 100ms
- Dropdown menu: < 50ms (no server round-trip)
- Form submission feedback: < 500ms

### 9.2 Accessibility (WCAG 2.1 AA)
- All dropdowns must be keyboard navigable (Arrow keys, Enter, Escape)
- Modals must trap focus and return focus on close
- Disabled buttons must have `aria-disabled="true"` and tooltip explanation
- Phase advancement preview must be screen-reader friendly

### 9.3 Browser Support
- Chrome 90+
- Firefox 90+
- Safari 14+
- Edge 90+

### 9.4 Responsive Behavior
- Modals: Max-width 500px, full-width on mobile
- Dropdowns: Full-width on mobile (< 768px)
- Phase advancement button: Full-width on mobile

---

## 10. UI Specifications

### 10.1 Components to Reuse (from FRONTEND.md)

| Component | Location | Status |
|-----------|----------|--------|
| Delete modal | `components/delete_modal.html` | Exists ✅ |
| Empty state | `components/empty_state.html` | Exists ✅ |
| Flash messages | `components/flash_messages.html` | Exists ✅ |
| Loading indicator | `components/loading.html` | Exists ✅ |
| Modal base styles | `main.css:978-1107` | Exists ✅ |
| Button styles | `main.css:554-668` | Exists ✅ |
| Dropdown styles | `main.css:1600-1708` | Exists ✅ |

### 10.2 Components to Create

| Component | Purpose |
|-----------|---------|
| `tournament_actions_dropdown.html` | Three dots menu for tournament cards |
| `rename_modal.html` | Simple rename modal with single text input |
| `user_create_modal.html` | User creation form in modal |
| `dancer_create_modal.html` | Dancer creation form in modal |
| `phase_advance_modal.html` | Detailed preview for phase advancement |

### 10.3 HTMX Patterns Needed

| Pattern | Use Case |
|---------|----------|
| Form submission with swap | Modal forms (create user/dancer) |
| Click outside to close | Dropdown menus |
| Confirm before action | Delete, phase advance |

### 10.4 Color Usage

| Element | Color | CSS Variable |
|---------|-------|--------------|
| Primary button | Orange #F97316 | `$color-primary` |
| Danger button | Red #EF4444 | `$color-danger` |
| Disabled state | Gray #6B7280 | `$color-neutral` |
| Success feedback | Green #22C55E | `$color-success` |

---

## 11. Implementation Recommendations

### 11.1 Critical (Must Fix)

1. **Fix Modal Positioning (Issue #5)**
   - Add `dialog { margin: auto; }` to reset browser defaults
   - Test in Chrome, Firefox, Safari
   - Affects all modals globally

2. **Add Phase Advancement UI (Issue #6)**
   - Add button to `tournaments/detail.html`
   - Create `phase_advance_modal.html` with detailed preview
   - **Create NEW endpoint** `POST /tournaments/{id}/advance`
   - Mark `/event/{id}/advance` as DEPRECATED
   - Admin-only visibility

3. **Modal Harmonization (Issue #7 - NEW)**
   - Update `tournament_create_modal.html` to use HTMX pattern
   - Update `POST /tournaments/create` to return HX-Redirect
   - All new modals must follow same pattern

### 11.2 Recommended

4. **Add Category Removal (Issue #3)**
   - Add "Remove" button in category table (always enabled during REGISTRATION)
   - Create backend route `DELETE /tournaments/{id}/categories/{cat_id}`
   - **CASCADE delete** Performers (keep Dancers)
   - HTMX removes row in-place (no page reload)
   - Simple confirmation modal

5. **Convert Creation Forms to Modals (Issue #4)**
   - Create `user_create_modal.html` with HTMX
   - Create `dancer_create_modal.html` with HTMX
   - Update list pages to trigger modals
   - Backend returns HX-Redirect on success

### 11.3 Nice-to-Have

6. **Implement Three Dots Menu (Issue #1)**
   - Create dropdown component
   - Add Rename modal (HTMX pattern)
   - **Rename allowed at ANY status** (CREATED, ACTIVE, COMPLETED)
   - Wire View, Rename, Delete actions

7. **Fix Empty State Alignment (Issue #2)**
   - Debug SVG centering
   - May need `display: block; margin: 0 auto;` on icon

---

## 12. Appendix: Reference Material

### 12.1 User Decisions (Resolved)

| Question | Answer | Date |
|----------|--------|------|
| Three dots menu options | View, Rename, Delete (not full Edit) | 2024-12-24 |
| Rename availability | **Always allowed** (any status: CREATED, ACTIVE, COMPLETED) | 2024-12-24 |
| Phase advancement confirmation | Detailed preview (battles to create, status changes) | 2024-12-24 |
| Phase advancement endpoint | **NEW endpoint** at `/tournaments/{id}/advance` (deprecate `/event/`) | 2024-12-24 |
| Category deletion behavior | **CASCADE delete** Performers, preserve Dancer profiles | 2024-12-24 |
| Category deletion phase | REGISTRATION phase only | 2024-12-24 |
| Category deletion confirmation | Simple confirmation (no detailed warning) | 2024-12-24 |
| After category deletion UX | HTMX removes row in-place (no page reload) | 2024-12-24 |
| Modal submission pattern | **HTMX + HX-Redirect** for ALL modals | 2024-12-24 |
| Harmonize existing modals | **Yes** - update tournament create modal too | 2024-12-24 |
| Implementation priority | All issues in one PR | 2024-12-24 |

### 12.2 Pattern Scan Results

**Full-page forms for entity creation:**

| File | Pattern | Action |
|------|---------|--------|
| `admin/create_user.html` | Full page form | Convert to modal |
| `dancers/create.html` | Full page form | Convert to modal |
| `tournaments/create.html` | Exists but unused | Remove (already using modal) |

**Dropdown menus:**
```bash
grep -rn "dropdown" app/templates/
# No matches - need to create dropdown component
```

**Phase advancement routes:**
- Backend: `POST /event/{tournament_id}/advance` (exists - **DEPRECATED**)
- NEW: `POST /tournaments/{tournament_id}/advance` (to be created)
- UI: None in `tournaments/detail.html` (gap)

### 12.3 Referenced Business Rules

From **DOMAIN_MODEL.md**:
- Phase sequence: Registration → Preselection → Pools → Finals → Completed
- Minimum performers: `(groups_ideal × 2) + 1`
- ~~Category deletion: Only when no performers registered~~ **UPDATED: CASCADE delete allowed**
- Phase transitions: Sequential only, no skipping

From **FRONTEND.md**:
- Section 8: Delete Confirmation Modal component
- Section 5.1: Dropdown component CSS exists
- HTMX Pattern 5: Delete with confirmation

**⚠️ DOMAIN_MODEL.md Update Required:**
> The category deletion rule needs to be updated to reflect CASCADE behavior:
> - OLD: "Category: Can Delete When = No performers registered"
> - NEW: "Category: Can Delete When = Tournament in REGISTRATION phase. CASCADE deletes Performers, preserves Dancers."

### 12.4 User Confirmation

- [x] User confirmed problem statement
- [x] User validated scenarios (via screenshots)
- [x] User approved requirements
- [x] User answered open questions (menu options, confirmation detail, priority)
- [x] **User validated business rule assumptions (2024-12-24)**
  - [x] Rename always allowed
  - [x] Category CASCADE deletion
  - [x] NEW phase advance endpoint
  - [x] HTMX modal harmonization

---

**Next Steps:**
1. Review this complete specification
2. Run `/plan-implementation workbench/FEATURE_SPEC_2024-12-24_UX-ISSUES-BATCH.md`
3. Implement all 6 issues in single PR

---

**End of Document**
