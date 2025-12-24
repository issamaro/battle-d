# Feature Specification: Navigation Streamlining

**Date:** 2025-12-23
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)

---

## 1. Problem Statement

The current navigation structure includes a Dashboard page that provides little unique value - it mostly duplicates information available elsewhere (Tournament Details, Tournaments List) and serves primarily as a pass-through to other pages. This creates unnecessary clicks, confusing navigation, and a "Frankenstein" feel where related functionality is scattered across multiple pages.

**User's exact feedback:** "Dashboard page is not meaningful anymore. The only thing accessible from there (only if tournament is active) is the Event mode, which should either be stuck to the actual tournament (tournaments page) or a whole section (side bar additional button), or both."

---

## 2. Executive Summary

### Scope
Streamline navigation by removing redundant Dashboard page and improving Event Mode accessibility.

### What Works ✅
| Feature | Status |
|---------|--------|
| Tournaments List (`/tournaments`) | Production Ready - Good hub for tournament management |
| Tournament Detail (`/tournaments/{id}`) | Production Ready - Shows categories and status |
| Event Mode (`/event/{id}`) | Production Ready - Command center for live events |
| Dancers (`/dancers`) | Production Ready - No redundancy |
| Users (`/admin/users`) | Production Ready - No redundancy |

### What's Broken 🚨
| Issue | Type | Impact |
|-------|------|--------|
| Dashboard is redundant | UX Debt | Extra clicks, confusing navigation |
| Event Mode access unclear | UX Gap | Buried in Tournament Detail, not prominent |
| Login lands on Dashboard | UX Friction | Users must navigate away immediately |
| "Your Permissions" table | Clutter | Not useful, adds noise to Dashboard |

### Key Changes Proposed
1. **Remove Dashboard** - Delete `/overview` route and `dashboard/` templates
2. **Redirect login to Tournaments** - `/overview` → `/tournaments`
3. **Event Mode in Sidebar** - Prominent button when tournament is active
4. **Event Mode on Tournament Card** - Button on active tournament card in list
5. **Keep Event Mode on Detail** - Already exists, just ensure it's prominent

---

## 3. User Flow Diagram

### Current Flow (Problematic)
```
═══════════════════════════════════════════════════════════════
 USER LOGS IN
═══════════════════════════════════════════════════════════════

  [Login Success] ─────────────────────────────────────────────►

  ┌──────────────────────────────────────────────────────────┐
  │  DASHBOARD (/overview)                                   │
  │  ⚠️ PROBLEM: Just shows quick links to other pages      │
  │  • Tournament info (duplicate of Tournament Detail)      │
  │  • Quick Links (duplicate of Sidebar navigation)         │
  │  • "Your Permissions" (not useful)                       │
  └──────────────────────────────────────────────────────────┘

                      │
         ┌───────────┴───────────┐
         ▼                       ▼
  ┌──────────────┐       ┌──────────────┐
  │ Tournaments  │       │   Dancers    │
  │   List       │       │   List       │
  └──────────────┘       └──────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  TOURNAMENT DETAIL (/tournaments/{id})                   │
  │  ⚠️ Only place to access Event Mode button              │
  │  • Tournament Info                                       │
  │  • Categories Table                                      │
  │  • [Event Mode] button (easy to miss)                    │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  EVENT MODE (/event/{id})                                │
  │  ✅ Good - Command Center for live events                │
  └──────────────────────────────────────────────────────────┘
```

### Proposed Flow (Streamlined)
```
═══════════════════════════════════════════════════════════════
 USER LOGS IN → LANDS ON TOURNAMENTS LIST
═══════════════════════════════════════════════════════════════

  [Login Success] ─────────────────────────────────────────────►

  ┌──────────────────────────────────────────────────────────┐
  │  TOURNAMENTS LIST (/tournaments)                         │
  │  ✅ Primary hub after login                              │
  │                                                          │
  │  ┌─────────────────────────────────────────────────────┐ │
  │  │ Tournament Card (Active)                            │ │
  │  │ • Name, Date, Phase Badge                           │ │
  │  │ • [Event Mode] button (prominent, orange)  ← NEW    │ │
  │  │ • [View] button                                     │ │
  │  └─────────────────────────────────────────────────────┘ │
  │                                                          │
  │  ┌─────────────────────────────────────────────────────┐ │
  │  │ Tournament Card (Other)                             │ │
  │  │ • Name, Date, Phase Badge                           │ │
  │  │ • [View] button only                                │ │
  │  └─────────────────────────────────────────────────────┘ │
  └──────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │  SIDEBAR                                                 │
  │                                                          │
  │  [Tournaments]                                           │
  │  [Dancers]                                               │
  │  [Users]                                                 │
  │  ─────────────                                           │
  │  [⚡ Event Mode] ← Only shows when active tournament    │
  │                    Prominent button (orange)             │
  └──────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Login Redirect

**Business Rule BR-NAV-001: Login Lands on Tournaments**
> After successful login, users should land on the Tournaments list page, not a separate dashboard.

**Acceptance Criteria:**
```gherkin
Feature: Login redirect
  As a logged-in user
  I want to land on the Tournaments page
  So that I can immediately see and manage tournaments

  Scenario: Successful login redirects to Tournaments
    Given I am on the login page
    When I complete the login process
    Then I should be redirected to /tournaments
    And I should see the tournament list

  Scenario: Direct access to /overview redirects
    Given I am logged in
    When I navigate to /overview
    Then I should be redirected to /tournaments
```

### 4.2 Event Mode Accessibility

**Business Rule BR-NAV-002: Event Mode Prominent Access**
> Event Mode should be accessible from 3 places: sidebar, tournament card (active only), and tournament detail page.

**Acceptance Criteria:**
```gherkin
Feature: Event Mode access points
  As an MC or Admin
  I want Event Mode to be easily accessible
  So that I can quickly enter command center during an event

  Scenario: Event Mode button in sidebar
    Given an active tournament exists
    And I am logged in as MC or Admin
    When I view any page
    Then I should see "Event Mode" button in the sidebar (below Users, after divider)
    And the button should be visually prominent (orange/primary color)
    And there should be NO "Tournament Name" section or "Tournament Details" link

  Scenario: Event Mode button on active tournament card
    Given an active tournament exists
    And I am on the Tournaments list page
    When I look at the active tournament card
    Then I should see an "Event Mode" button on the card
    And the button should be orange/primary color

  Scenario: Event Mode button on tournament detail
    Given I am viewing a tournament detail page
    And the tournament is in an active phase (not registration/completed)
    When I look at the tournament info section
    Then I should see an "Event Mode" button
```

### 4.3 Dashboard Removal

**Business Rule BR-NAV-003: No Dashboard Page**
> The Dashboard page should be removed; all its functionality is available elsewhere.

**Acceptance Criteria:**
```gherkin
Feature: Dashboard removal
  As a user
  I want navigation to be streamlined
  So that I don't have to click through redundant pages

  Scenario: Dashboard route redirects
    Given I am logged in
    When I navigate to /overview
    Then I should be redirected to /tournaments
    And I should NOT see a Dashboard option in the sidebar

  Scenario: Sidebar shows Tournaments first
    Given I am logged in
    When I view the sidebar navigation
    Then the first item should be "Tournaments" (not "Dashboard")
```

### 4.4 Permissions Table Removal

**Business Rule BR-NAV-004: No Permissions Display**
> The "Your Permissions" table should be removed; user role is already visible in sidebar footer.

**Acceptance Criteria:**
- [ ] "Your Permissions" table removed from UI
- [ ] User role remains visible in sidebar footer (already exists)

---

## 5. Current State Analysis

### 5.1 Dashboard Templates Analysis

**Location:** `app/templates/dashboard/`

| Template | Purpose | Recommendation |
|----------|---------|----------------|
| `index.html` | Main dashboard page | DELETE |
| `_no_tournament.html` | Shows when no active tournament | DELETE (just go to /tournaments) |
| `_registration_mode.html` | Shows during registration | DELETE (duplicate of tournament detail) |
| `_event_active.html` | Shows when event running | DELETE (Event Mode link in sidebar) |

### 5.2 Routes Analysis

**Location:** `app/routers/dashboard.py` (or similar)

| Route | Current Behavior | New Behavior |
|-------|-----------------|--------------|
| `/overview` | Serves Dashboard | Redirect to `/tournaments` |
| Post-login | Redirect to `/overview` | Redirect to `/tournaments` |

### 5.3 Sidebar Navigation

**Location:** `app/templates/base.html`

**Current:**
```
Dashboard          ← REMOVE
Dancers
Tournaments
Users
─────────────
[Tournament Name]
  Tournament Details
  Event Mode
```

**Proposed:**
```
Tournaments        ← NOW FIRST
Dancers
Users
─────────────
⚡ Event Mode      ← Only shows when active tournament exists
                     Prominent orange button, no tournament section
```

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Redirect `/overview` to `/tournaments`**
   - Modify route to return 302 redirect
   - Update any hardcoded links to `/overview`

2. **Update login redirect**
   - Change post-login redirect from `/overview` to `/tournaments`

3. **Remove Dashboard from sidebar**
   - Update `base.html` to not show "Dashboard" nav item
   - Make "Tournaments" the first item

4. **Add Event Mode to tournament card**
   - Modify `tournaments/list.html` to show "Event Mode" button on active tournament
   - Only show for MC/Admin users
   - Use orange/primary color for prominence

5. **Simplify sidebar when active tournament**
   - Remove entire "Tournament Name" section and "Tournament Details" link
   - Show only "Event Mode" button (orange, prominent) below divider
   - Button only visible to MC/Admin users

### 6.2 Recommended

6. **Delete Dashboard templates**
   - Remove `app/templates/dashboard/` directory
   - Clean up any imports/includes

7. **Update tests**
   - Remove Dashboard-specific tests
   - Update navigation tests to expect redirect

### 6.3 Nice-to-Have (Future)

8. **Add "Event Mode" badge/indicator**
   - When tournament is in event mode (preselection/pools/finals)
   - Visual indicator on sidebar button

---

## 7. Open Questions & Answers

- **Q:** Should we keep the Dashboard route for backwards compatibility?
  - **A:** Yes - redirect to /tournaments (302) so bookmarks still work

- **Q:** What happens to non-staff users who can't see Tournaments?
  - **A:** They should still land on /tournaments but see appropriate content (empty state or limited view)

- **Q:** Should Event Mode button show for all tournament phases?
  - **A:** Only for phases after Registration (Preselection, Pools, Finals) when event is actually running

---

## 8. User Confirmation

- [x] User confirmed Dashboard is not meaningful
- [x] User chose: Land on Tournaments list after login
- [x] User chose: Event Mode in sidebar + tournament card + detail page
- [x] User chose: Remove "Your Permissions" table
