# Feature Specification: Fix Broken Phases Navigation Links

**Date:** 2025-12-07
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

Admins cannot advance tournament phases because multiple navigation buttons and links return 404 errors. This blocks the entire tournament lifecycle - tournaments cannot progress from Registration to Preselection or any subsequent phases.

---

## 2. Executive Summary

### Scope
Fix all broken links related to tournament phase navigation so admins can advance tournaments through their lifecycle phases.

### What Works ✅
| Feature | Status |
|---------|--------|
| Phase router at `/tournaments/{id}/phase` | Production Ready |
| Phase advance route at `/tournaments/{id}/advance` | Production Ready |
| Dashboard displays tournament status | Production Ready |
| Phase overview template renders | Production Ready |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| Sidebar "Phases" link → 404 | BUG | base.html:183 |
| "Manage Phases" button → 404 | BUG | _registration_mode.html:11 |
| "Phase Management" button → 404 | BUG | _event_active.html:13 |
| "Manage Phases" links → 404 (3 locations) | BUG | overview.html:26,43,65 |
| "Advance to preselection" form → 404 | BUG | phases/overview.html:33 |
| "Go Back" form → 404 (route doesn't exist) | BUG | phases/overview.html:27 |
| Missing template variables | BUG | phases/overview.html uses undefined variables |

### Root Cause
**URL Prefix Mismatch:** The phases router is defined with `prefix="/tournaments"` but all templates use `/phases/` as the URL prefix.

```python
# app/routers/phases.py:22
router = APIRouter(prefix="/tournaments", tags=["phases"])
```

### Key Business Rules
- **BR-PHASE-001:** Phases are forward-only - no going back (per design)
- **BR-PHASE-002:** Only admins can advance tournament phases
- **BR-PHASE-003:** All navigation to phases must work without 404 errors

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 ADMIN WORKFLOW: Advance Tournament Phase
═══════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  CURRENT STATE (BROKEN):                                                │
  │                                                                         │
  │  Dashboard ─────► "Manage Phases" button ─────► 🚨 404 ERROR            │
  │      │                                                                  │
  │      ▼                                                                  │
  │  Sidebar ───────► "Phases" link ──────────────► 🚨 404 ERROR            │
  │      │                                                                  │
  │      ▼                                                                  │
  │  Phase Page ────► "Advance to..." button ─────► 🚨 404 ERROR            │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

                                    ▼

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  DESIRED STATE (FIXED):                                                 │
  │                                                                         │
  │  Dashboard ─────► "Manage Phases" button ─────► Phase Overview Page     │
  │      │                                                                  │
  │      ▼                                                                  │
  │  Sidebar ───────► "Phases" link ──────────────► Phase Overview Page     │
  │      │                                                                  │
  │      ▼                                                                  │
  │  Phase Page ────► "Advance to..." button ─────► Confirmation Dialog     │
  │                           │                                             │
  │                           ▼                                             │
  │                    Phase Advanced Successfully                          │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

### Expected Navigation Flow

```
┌──────────────┐     ┌─────────────────┐     ┌────────────────────┐
│   Dashboard  │────►│  Phase Overview │────►│ Advance Phase Form │
│              │     │                 │     │                    │
│ "Manage      │     │ Shows:          │     │ POST to:           │
│  Phases"     │     │ - Current phase │     │ /tournaments/{id}/ │
│              │     │ - Phase list    │     │   advance          │
│ Link to:     │     │ - Advance btn   │     │                    │
│ /tournaments/│     │                 │     │ Redirects to:      │
│   {id}/phase │     │ (No Go Back -   │     │ /tournaments/{id}  │
└──────────────┘     │  forward only)  │     └────────────────────┘
                     └─────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Phase Navigation Must Work

**Business Rule BR-NAV-001: All Phase Links Must Work**
> Every navigation button or link that leads to phase management must successfully load the phase overview page without 404 errors.

**Acceptance Criteria:**
```gherkin
Feature: Tournament Phase Navigation
  As an admin
  I want all phase navigation links to work
  So that I can manage tournament phases during events

Scenario: Sidebar phases link works
  Given I am logged in as admin
  And there is an active tournament "Battle-D Winter 2025"
  When I click "Phases" in the sidebar
  Then I see the Tournament Phases page
  And I see "Current Phase: REGISTRATION"
  And I do not see a 404 error

Scenario: Dashboard "Manage Phases" button works
  Given I am logged in as admin
  And I am on the dashboard in registration mode
  When I click "Manage Phases"
  Then I see the Tournament Phases page
  And I do not see a 404 error

Scenario: Advance phase button works
  Given I am logged in as admin
  And I am on the Tournament Phases page
  And the tournament has enough performers registered
  When I click "Advance to preselection"
  Then the phase transition form is submitted
  And I see the confirmation or validation result
  And I do not see a 404 error
```

### 4.2 Forward-Only Phase Progression

**Business Rule BR-PHASE-001: Phases Are Forward-Only**
> Tournament phases can only advance forward. There is no "Go Back" functionality. This is by design to maintain tournament integrity.

**Acceptance Criteria:**
- [ ] The "Go Back" button is removed from the phase overview page
- [ ] No route exists for going back to a previous phase
- [ ] Phase overview shows only the "Advance" action (when available)

---

## 5. Current State Analysis

### 5.1 Router Configuration (Correct)
**Location:** `app/routers/phases.py:22-69`

```python
router = APIRouter(prefix="/tournaments", tags=["phases"])

@router.get("/{tournament_id}/phase")     # → /tournaments/{id}/phase
@router.post("/{tournament_id}/advance")  # → /tournaments/{id}/advance
```
**Status:** ✅ Correctly implemented

### 5.2 Sidebar Link (Broken)
**Location:** `app/templates/base.html:183`

```html
<!-- Current (WRONG) -->
<li><a href="/phases/{{ active_tournament.id }}/phase">Phases</a></li>

<!-- Should be -->
<li><a href="/tournaments/{{ active_tournament.id }}/phase">Phases</a></li>
```
**Status:** ❌ Wrong URL prefix

### 5.3 Dashboard Registration Mode (Broken)
**Location:** `app/templates/dashboard/_registration_mode.html:11`

```html
<!-- Current (WRONG) -->
<a href="/phases/{{ dashboard.tournament.id }}/phase">Manage Phases</a>

<!-- Should be -->
<a href="/tournaments/{{ dashboard.tournament.id }}/phase">Manage Phases</a>
```
**Status:** ❌ Wrong URL prefix

### 5.4 Dashboard Event Active (Broken)
**Location:** `app/templates/dashboard/_event_active.html:13`

```html
<!-- Current (WRONG) -->
<a href="/phases/{{ dashboard.tournament.id }}/phase">Phase Management</a>

<!-- Should be -->
<a href="/tournaments/{{ dashboard.tournament.id }}/phase">Phase Management</a>
```
**Status:** ❌ Wrong URL prefix

### 5.5 Overview Page (Broken - 3 locations)
**Location:** `app/templates/overview.html:26,43,65`

All three links use `/phases/` instead of `/tournaments/`
**Status:** ❌ Wrong URL prefix (x3)

### 5.6 Phase Advance Form (Broken)
**Location:** `app/templates/phases/overview.html:33`

```html
<!-- Current (WRONG) -->
<form action="/phases/advance" method="post">

<!-- Should be -->
<form action="/tournaments/{{ tournament.id }}/advance" method="post">
```
**Status:** ❌ Wrong URL prefix AND missing tournament_id

### 5.7 Go Back Form (Broken - No Route Exists)
**Location:** `app/templates/phases/overview.html:27`

```html
<!-- Current (Route doesn't exist) -->
<form action="/phases/go-back" method="post">
```
**Decision:** Remove entirely (phases are forward-only per BR-PHASE-001)
**Status:** ❌ Route doesn't exist, button should be removed

### 5.8 Missing Template Variables
**Location:** `app/templates/phases/overview.html:28-29`

```html
<!-- Template uses these variables -->
{% if not can_go_back %}disabled{% endif %}
{{ prev_phase.value if prev_phase else "N/A" }}

<!-- But router only provides -->
"next_phase": next_phase,
"can_advance": next_phase is not None,
```
**Status:** ❌ Variables `prev_phase` and `can_go_back` not provided by router

---

## 6. Implementation Recommendations

### 6.1 Critical (Must Fix Now)

| # | File | Line | Change |
|---|------|------|--------|
| 1 | `app/templates/base.html` | 183 | Change `/phases/` → `/tournaments/` |
| 2 | `app/templates/dashboard/_registration_mode.html` | 11 | Change `/phases/` → `/tournaments/` |
| 3 | `app/templates/dashboard/_event_active.html` | 13 | Change `/phases/` → `/tournaments/` |
| 4 | `app/templates/overview.html` | 26, 43, 65 | Change `/phases/` → `/tournaments/` (3 locations) |
| 5 | `app/templates/phases/overview.html` | 33 | Change `/phases/advance` → `/tournaments/{{ tournament.id }}/advance` |
| 6 | `app/templates/phases/overview.html` | 27-31 | Remove entire "Go Back" form section |
| 7 | `app/templates/phases/overview.html` | N/A | Remove references to `prev_phase` and `can_go_back` |

### 6.2 Summary

**Total Changes:**
- 6 template files need modification
- 10 individual link/form corrections
- 1 form section removal (Go Back)

**Estimated Impact:**
- ~15-20 lines changed across templates
- No backend changes required
- No new routes needed

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should "Go Back" functionality exist?
  - **A:** No - user confirmed phases are forward-only. Remove the button.

- **Q:** Why do templates use `/phases/` when router uses `/tournaments/`?
  - **A:** Templates were created/modified without verifying actual router configuration. Testing was insufficient.

### 7.2 Files Changed Summary

```
app/templates/
├── base.html                           # Line 183
├── overview.html                       # Lines 26, 43, 65
├── dashboard/
│   ├── _registration_mode.html         # Line 11
│   └── _event_active.html              # Line 13
└── phases/
    └── overview.html                   # Lines 27-31, 33
```

### 7.3 User Confirmation

- [x] User confirmed problem statement (screenshots of 404 errors provided)
- [x] User validated that phases should be forward-only (Remove Go Back)
- [x] User approved scope (fix all broken links)
