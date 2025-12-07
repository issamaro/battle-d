# Feature Specification: UX Navigation Redesign

**Date:** 2025-12-07
**Status:** Awaiting User Approval

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
   - 5.1-5.3 Current State
   - 5.4 Functional Requirements
   - 5.5 Non-Functional Requirements
   - 5.6 UI Specifications
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

The Battle-D application lacks a coherent user experience. While individual pages exist and work in isolation, the overall experience fails to guide users through the actual tournament workflow.

**Three interconnected problems:**

1. **Broken Navigation (Technical):** Links like `/phases` and `/registration` return 404 because they're missing required tournament context (IDs).

2. **No Workflow Guidance (UX):** Users don't know what to do next. Pages were built brick-by-brick but don't connect into a meaningful journey from "create tournament" to "declare champion."

3. **Wrong Interface for Context (Design):** The same sidebar navigation is shown whether staff is preparing (days before) or running battles (event day). Event day needs a focused, speed-optimized interface - not a website with menus.

**User's Vision:** A complete UX redesign that supports the real tournament workflow, with clear separation between preparation mode (exploratory, multi-page) and event mode (focused, single-screen).

---

## 2. Executive Summary

### Scope

This analysis covers the complete navigation and information architecture of Battle-D, focusing on how users move through the application to complete tournament management tasks.

### What Works ✅

| Feature | Status | Notes |
|---------|--------|-------|
| Tournament CRUD | Production Ready | List, create, view detail |
| Category CRUD | Production Ready | Add categories to tournaments |
| Dancer CRUD | Production Ready | List, create, profile, edit |
| User Management | Production Ready | Admin only |
| Registration | Partial | Works but requires direct URL with IDs |
| Battle Management | Partial | Works but no clear entry point |
| Phase Advancement | Partial | Works but requires tournament ID in URL |

### What's Broken 🚨

| Issue | Type | Evidence |
|-------|------|----------|
| `/phases` link returns 404 | BUG | Sidebar nav line 169 of base.html |
| `/registration` link returns 404 | BUG | overview.html line 53 |
| `/battles/current` link returns 404 | GAP | overview.html line 72 (V2 feature) |
| No clear workflow from overview to action | GAP | User doesn't know what to do next |
| Registration requires knowing URL pattern | GAP | Must manually construct `/registration/{t_id}/{c_id}` |

### Key Insight

The application has **two distinct operating modes**:

1. **Preparation Mode** (REGISTRATION phase)
   - Relaxed pace, days/weeks before event
   - Multi-screen exploration (tournaments, dancers, categories)
   - Standard website navigation appropriate

2. **Event Mode** (PRESELECTION → POOLS → FINALS)
   - Fast pace, time pressure
   - Single task: run battles sequentially
   - Staff repeats Start → Encode cycle 20-30+ times
   - Needs focused, single-screen interface

Current navigation doesn't acknowledge these different contexts.

---

## 3. User Flow Diagram

### 3.1 Complete Tournament Lifecycle

```
═══════════════════════════════════════════════════════════════════════════════
 PHASE 1: REGISTRATION                                    [Status: CREATED]
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ACTIONS:                                                                │
  │  👤 Admin/Staff: Create tournament                                       │
  │  👤 Admin/Staff: Add categories (Hip Hop 1v1, Krump 2v2, etc.)          │
  │  👤 Staff: Create dancers (if new to system)                            │
  │  👤 Staff: Register dancers to categories                               │
  │  ⚡ System: Creates Performer records                                   │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  VALIDATION CHECK (REGISTRATION → PRESELECTION):                         │
  │  ✅ Each category has minimum (groups_ideal × 2) + 1 performers          │
  │  ✅ No other tournament is ACTIVE                                        │
  │  ⚠️ GAP: No clear "Start Event" button on overview                      │
  │  ⚠️ GAP: Registration requires manual URL construction                  │
  └──────────────────────────────────────────────────────────────────────────┘

  [Admin clicks "Start Event"] ───────────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE 2: PRESELECTION                                    [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  SYSTEM AUTO-ACTIONS (on phase entry):                                   │
  │  ⚡ Tournament status: CREATED → ACTIVE                                  │
  │  ⚡ Generates all preselection battles                                   │
  │  ⚡ Interleaves battles across categories (BR-SCHED-001)                 │
  │  ⚡ Assigns sequence_order for queue ordering                            │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  THE BATTLE LOOP (repeats 20-30+ times):                                 │
  │                                                                          │
  │  ┌────────────────────────────────────────────────────────────────────┐  │
  │  │  1. ANNOUNCE                                                       │  │
  │  │     👤 MC reads from screen: "Next up: Maro vs Bboy, Hip Hop!"    │  │
  │  │     ⚠️ GAP: No MC-optimized view exists                           │  │
  │  └────────────────────────────────────────────────────────────────────┘  │
  │                            ▼                                             │
  │  ┌────────────────────────────────────────────────────────────────────┐  │
  │  │  2. START BATTLE                                                   │  │
  │  │     👤 Staff clicks [START]                                        │  │
  │  │     ⚡ System: battle.status = ACTIVE                              │  │
  │  │     ✅ Works: /battles/{id}/start exists                           │  │
  │  └────────────────────────────────────────────────────────────────────┘  │
  │                            ▼                                             │
  │  ┌────────────────────────────────────────────────────────────────────┐  │
  │  │  3. BATTLE HAPPENS (2-5 minutes, real world)                       │  │
  │  └────────────────────────────────────────────────────────────────────┘  │
  │                            ▼                                             │
  │  ┌────────────────────────────────────────────────────────────────────┐  │
  │  │  4. ENCODE RESULTS                                                 │  │
  │  │     👤 Staff enters scores (0-10 per performer)                    │  │
  │  │     ⚡ System: battle.status = COMPLETED                           │  │
  │  │     ⚡ System: Updates performer.preselection_score                │  │
  │  │     ⚡ System: May create tiebreak battle (BR-TIE-001)             │  │
  │  │     ✅ Works: /battles/{id}/encode exists                          │  │
  │  └────────────────────────────────────────────────────────────────────┘  │
  │                            ▼                                             │
  │  [More battles?] ─── YES ──► Loop back to ANNOUNCE                       │
  │        │                                                                 │
  │        NO                                                                │
  │        ▼                                                                 │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  VALIDATION CHECK (PRESELECTION → POOLS):                                │
  │  ✅ All preselection battles completed                                   │
  │  ✅ All tiebreaks resolved                                               │
  │  ⚠️ GAP: No clear progress indicator showing remaining battles          │
  │  ⚠️ GAP: Advance button requires knowing tournament ID                  │
  └──────────────────────────────────────────────────────────────────────────┘

  [Admin clicks "Advance to Pools"] ──────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE 3: POOLS                                           [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  SYSTEM AUTO-ACTIONS (on phase entry):                                   │
  │  ⚡ Creates pools (groups_ideal per category)                            │
  │  ⚡ Distributes qualified performers to pools (BR-POOL-001: equal sizes) │
  │  ⚡ Generates round-robin pool battles                                   │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  THE BATTLE LOOP (same as preselection, different encoding):             │
  │                                                                          │
  │  ENCODE: Staff selects Winner / Draw (not scores)                        │
  │  ⚡ System: Updates pool_wins/draws/losses                               │
  │  ⚡ System: Calculates pool_points                                       │
  │  ⚡ System: May create pool winner tiebreak (BR-TIE-002)                 │
  └──────────────────────────────────────────────────────────────────────────┘

  [Admin clicks "Advance to Finals"] ─────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE 4: FINALS                                          [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  SYSTEM AUTO-ACTIONS (on phase entry):                                   │
  │  ⚡ Creates finals battles (pool winners vs pool winners)                │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  THE BATTLE LOOP (1-2 battles per category):                             │
  │                                                                          │
  │  ENCODE: Staff selects Winner (no draws in finals)                       │
  │  ⚡ System: Declares category champion                                   │
  └──────────────────────────────────────────────────────────────────────────┘

  [Admin clicks "Complete Tournament"] ───────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE 5: COMPLETED                                       [Status: COMPLETED]
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  FINAL STATE:                                                            │
  │  ✅ All results locked                                                   │
  │  ✅ Champions declared per category                                      │
  │  ⚠️ GAP: No results/standings display page                              │
  └──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Navigation Gap Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CURRENT NAVIGATION vs. REQUIRED CONTEXT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SIDEBAR LINKS:                                                             │
│  ───────────────                                                            │
│  /overview        → ✅ Works (no context needed)                            │
│  /phases          → 🚨 404! Needs: /phases/{tournament_id}/phase            │
│  /dancers         → ✅ Works (no context needed)                            │
│  /tournaments     → ✅ Works (no context needed)                            │
│  /admin/users     → ✅ Works (no context needed)                            │
│                                                                             │
│  OVERVIEW QUICK ACTIONS:                                                    │
│  ───────────────────────                                                    │
│  /phases          → 🚨 404! Same issue                                      │
│  /registration    → 🚨 404! Needs: /registration/{t_id}/{c_id}              │
│  /battles/current → 🚨 404! Route doesn't exist (V2 judge feature)          │
│  /battles         → ✅ Works (shows all battles)                            │
│                                                                             │
│  THE PROBLEM:                                                               │
│  ─────────────                                                              │
│  Navigation links are CONTEXT-FREE but routes require TOURNAMENT CONTEXT.   │
│  User must know the tournament ID to construct working URLs.                │
│                                                                             │
│  SOLUTION PRINCIPLE:                                                        │
│  ───────────────────                                                        │
│  If there's an ACTIVE tournament, use its ID automatically.                 │
│  If in REGISTRATION, show tournament-scoped dashboard.                      │
│  If in EVENT PHASES, show focused event interface.                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Navigation Must Reflect Tournament Context

**Business Rule BR-NAV-001: Context-Aware Navigation**
> When a tournament is active (status=ACTIVE), navigation should automatically use that tournament's ID for tournament-scoped routes.

**Acceptance Criteria:**
```gherkin
Feature: Context-aware navigation
  As a staff member
  I want navigation links to work without me knowing tournament IDs
  So that I can complete my tasks without URL manipulation

Scenario: Staff accesses phases from sidebar
  Given there is an active tournament "Winter 2025"
  And the tournament is in PRESELECTION phase
  When I click "Phases" in the sidebar
  Then I am taken to the phase view for "Winter 2025"
  And I see the current phase status and progress

Scenario: Staff accesses registration from overview
  Given there is a tournament in REGISTRATION phase
  When I click "Register Performers" on the overview
  Then I see a list of categories for that tournament
  And I can select a category to register dancers

Scenario: No active tournament
  Given there is no active tournament
  When I click "Phases" in the sidebar
  Then I see a message "No active tournament"
  And I am prompted to create or start a tournament
```

### 4.2 Overview Should Be a Smart Dashboard

**Business Rule BR-NAV-002: Context-Aware Dashboard**
> The overview/dashboard should display different content based on the current tournament state.

**Acceptance Criteria:**
```gherkin
Feature: Smart dashboard
  As a staff member
  I want the dashboard to show me what I need right now
  So that I know what action to take next

Scenario: No active tournament - show create prompt
  Given there are no tournaments in CREATED or ACTIVE status
  When I view the dashboard
  Then I see "No Active Tournament"
  And I see a prominent "Create Tournament" button
  And I see a list of past completed tournaments

Scenario: Tournament in REGISTRATION - show registration status
  Given there is a tournament "Winter 2025" in REGISTRATION phase
  When I view the dashboard
  Then I see "Winter 2025 - Registration"
  And I see each category with registration count (e.g., "Hip Hop: 5/8 registered")
  And I see which categories need more performers (highlighted)
  And I see a "Start Event" button (disabled if not ready)

Scenario: Tournament in event phase - show go to event mode
  Given there is a tournament "Winter 2025" in PRESELECTION phase
  When I view the dashboard
  Then I see "Winter 2025 - LIVE"
  And I see a prominent "Go to Event Mode" button
  And I see current battle progress (12/28 battles)
```

### 4.3 Event Mode Should Be Focused

**Business Rule BR-NAV-003: Event Mode Interface**
> During event phases (PRESELECTION, POOLS, FINALS), staff should have a focused interface optimized for the repetitive battle loop.

**Acceptance Criteria:**
```gherkin
Feature: Event mode interface
  As a staff member running battles on event day
  I want all battle information on one screen
  So that I can work quickly without page navigation

Scenario: View current battle and queue
  Given I am in event mode for "Winter 2025"
  And the tournament is in PRESELECTION phase
  When I view the command center
  Then I see the current/next battle prominently displayed
  And I see the battle queue with remaining battles
  And I see phase progress (12/28 battles, 43%)
  And I see category standings

Scenario: Start and encode battle quickly
  Given I am viewing the command center
  And the next battle is "Maro vs Bboy"
  When I click "Start Battle"
  Then the battle is marked ACTIVE
  And the "Encode" button becomes available
  When I click "Encode" and enter scores
  Then the battle is completed
  And the next battle automatically becomes current
  And the queue updates

Scenario: Exit to preparation mode
  Given I am in event mode
  And I need to add a late-registration dancer
  When I click "Exit Event Mode"
  Then I return to the standard dashboard
  And I can access dancers, registration, etc.
```

### 4.4 Registration Should Be Efficient

**Business Rule BR-NAV-004: Batch Registration**
> Staff should be able to register multiple dancers quickly without page refreshes.

**Acceptance Criteria:**
```gherkin
Feature: Efficient batch registration
  As a staff member registering dancers
  I want to register multiple dancers quickly
  So that I can complete registration before the event

Scenario: Register dancer with one click
  Given I am on the registration page for "Hip Hop 1v1"
  And I search for "Maro"
  When I click the "Add" button next to Maro
  Then Maro is immediately registered
  And Maro moves from "Available" to "Registered" list
  And the page does not refresh
  And registration count updates (e.g., "6/8 registered")

Scenario: Unregister dancer with one click
  Given I am on the registration page for "Hip Hop 1v1"
  And Maro is in the "Registered" list
  When I click the "Remove" button next to Maro
  Then Maro is immediately unregistered
  And Maro moves back to "Available" list
  And the page does not refresh
```

---

## 5. Current State Analysis

### 5.1 Broken Navigation Links

**Business Rule:** Navigation should lead to functional pages
**Implementation Status:** 🚨 BROKEN

**Evidence:**
- `base.html:169` - `/phases` link in sidebar
- `overview.html:27,42,63` - `/phases` links in overview
- `overview.html:53` - `/registration` link
- `overview.html:72` - `/battles/current` link (V2)

**Actual Routes (from routers/):**
- Phases: `/phases/{tournament_id}/phase` (requires tournament_id)
- Registration: `/registration/{tournament_id}/{category_id}` (requires both IDs)
- Battles: `/battles` works, but `/battles/current` doesn't exist

### 5.2 Route-Navigation Mismatch

| Navigation Link | Expected by User | Actual Route | Status |
|-----------------|------------------|--------------|--------|
| `/phases` | See phases for active tournament | `/phases/{t_id}/phase` | 🚨 Mismatch |
| `/registration` | Register dancers | `/registration/{t_id}/{c_id}` | 🚨 Mismatch |
| `/battles/current` | Score current battle | Does not exist | 🚨 Missing |

### 5.3 Missing User Journeys

**Journey 1: "I want to register dancers"**
- Current: Click "Register Performers" → 404
- Expected: Click → See categories → Select category → Register dancers

**Journey 2: "I want to advance the phase"**
- Current: Click "Manage Phases" → 404
- Expected: Click → See current phase → Click "Advance" → Confirmation → Phase advances

**Journey 3: "I want to run battles on event day"**
- Current: Find /battles, click around, figure out workflow
- Expected: Dashboard shows "Go to Event Mode" → Focused battle interface

---

## 5.4 Functional Requirements

### Must Have (Critical for Production)

**Navigation & Routing:**
- [ ] FR-NAV-01: Remove or fix `/phases` link in sidebar (currently 404)
- [ ] FR-NAV-02: Remove or fix `/registration` link in overview (currently 404)
- [ ] FR-NAV-03: Remove `/battles/current` link (V2 feature)
- [ ] FR-NAV-04: When active tournament exists, navigation links auto-use its ID

**Smart Dashboard:**
- [ ] FR-DASH-01: Dashboard shows different content based on tournament state
- [ ] FR-DASH-02: No active tournament → "Create Tournament" CTA
- [ ] FR-DASH-03: Registration phase → Category list with registration status
- [ ] FR-DASH-04: Event phases → "Go to Event Mode" prominent CTA
- [ ] FR-DASH-05: Dashboard shows current phase and progress

**Event Mode (Command Center):**
- [ ] FR-EVENT-01: Full-screen interface without sidebar navigation
- [ ] FR-EVENT-02: Current battle displayed prominently with performer names
- [ ] FR-EVENT-03: Battle queue visible with upcoming battles
- [ ] FR-EVENT-04: "Start Battle" button sets status to ACTIVE
- [ ] FR-EVENT-05: "Encode" button opens encoding form
- [ ] FR-EVENT-06: Phase progress indicator (X/Y battles, percentage)
- [ ] FR-EVENT-07: "Exit to Prep" button returns to dashboard
- [ ] FR-EVENT-08: Auto-detect: show event mode when tournament in PRESELECTION/POOLS/FINALS

**Registration:**
- [ ] FR-REG-01: Two-panel layout: Available dancers | Registered dancers
- [ ] FR-REG-02: Single-click register (no page refresh)
- [ ] FR-REG-03: Single-click unregister (no page refresh)
- [ ] FR-REG-04: Search available dancers by blaze, name, or email
- [ ] FR-REG-05: Real-time count update (e.g., "5/8 registered")

### Should Have (Important but not blocking)

- [ ] FR-EVENT-09: Category filter for battle queue
- [ ] FR-EVENT-10: Standings display during event mode
- [ ] FR-REG-06: Batch register multiple dancers at once
- [ ] FR-DASH-06: "Start Event" button on dashboard (advances to PRESELECTION)

### Won't Have (Explicitly out of scope for this feature)

- Judge scoring interface (V2)
- Multi-tournament view (only one active at a time)
- Real-time sync across devices (SSE/WebSocket)
- Drag-and-drop battle reordering in this scope (already exists via BR-SCHED-002)

---

## 5.5 Non-Functional Requirements

**Performance:**
- NFR-01: Page load under 2 seconds on broadband
- NFR-02: HTMX partial updates under 500ms

**Accessibility (WCAG 2.1 AA):**
- NFR-03: All interactive elements keyboard accessible
- NFR-04: Color contrast minimum 4.5:1 for text
- NFR-05: Screen reader compatible (ARIA labels, semantic HTML)
- NFR-06: Focus indicators visible on all interactive elements

**Responsive Design:**
- NFR-07: Mobile-first (320px minimum)
- NFR-08: Touch targets minimum 44x44px
- NFR-09: Event mode usable on tablets (768px+)

**Browser Support:**
- NFR-10: Chrome, Firefox, Safari, Edge (latest 2 versions)

---

## 5.6 UI Specifications

### Components to Reuse (from FRONTEND.md)

| Component | Location | Use Case |
|-----------|----------|----------|
| Flash Messages | `components/flash_messages.html` | Success/error feedback |
| Status Badges | FRONTEND.md §5 | Tournament/battle status |
| Forms | FRONTEND.md §2 | Encoding forms |
| Tables | FRONTEND.md §3 | Standings display |
| Loading Indicators | `components/loading.html` | HTMX requests |

### New Components Needed

| Component | Description | Notes |
|-----------|-------------|-------|
| Smart Dashboard | 3-state context-aware home | Conditions based on tournament state |
| Event Mode Header | Compact header with tournament/phase info | No sidebar, exit button |
| Current Battle Card | Large display of current battle | Performer names, category, status |
| Battle Queue List | Scrollable queue with filters | Category tabs, status badges |
| Progress Bar | Phase progress indicator | X/Y battles, percentage |
| Two-Panel Registration | Available/Registered side-by-side | HTMX-powered transfers |

### HTMX Patterns Needed

| Pattern | Reference | Use Case |
|---------|-----------|----------|
| Live Search | FRONTEND.md Pattern 1 | Dancer search in registration |
| Partial Update | FRONTEND.md Pattern 2 | Register/unregister without refresh |
| Polling | FRONTEND.md Pattern 3 | Auto-refresh battle queue |

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Fix broken sidebar links**
   - Remove `/phases` link or redirect to active tournament's phase page
   - Remove `/registration` link (access via tournament detail)

2. **Fix broken overview links**
   - Replace `/phases` buttons with context-aware links
   - Replace `/registration` with link to tournament categories
   - Remove `/battles/current` (V2 feature) or hide judge section

### 6.2 Recommended

1. **Create smart dashboard**
   - State 1: No active tournament → Create tournament CTA
   - State 2: Registration phase → Category registration status
   - State 3: Event phases → "Go to Event Mode" CTA

2. **Create event mode interface**
   - Single screen with: current battle, queue, progress, standings
   - Optimized for the Start → Encode loop

3. **Improve registration UX**
   - Two-panel layout (available | registered)
   - HTMX-powered single-click register/unregister
   - No page refresh

### 6.3 Nice-to-Have (Future)

1. **MC view** - Read-only simplified view for announcing battles
2. **Keyboard shortcuts** - S=Start, E=Encode for power users
3. **Auto-advance** - Automatically show next battle after encoding

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should we auto-detect event mode based on tournament phase, or require explicit "Enter Event Mode"?
  - **A:** ✅ BOTH - Auto-detect when tournament enters event phases, but allow manual override in either direction. Show "Exit to Prep" in event mode and "Enter Event Mode" in prep mode.

- **Q:** Should registration show all categories on one page, or one category at a time?
  - **A:** ✅ One category at a time - User selects category first, then sees two-panel available/registered view for that category.

- **Q:** How should the standings be displayed during event mode?
  - **A:** TBD - To be determined during UI design phase

### 7.2 Role Responsibilities

| Role | Preparation Mode | Event Mode |
|------|------------------|------------|
| **ADMIN** | Create tournament, categories, users | Advance phases, handle exceptions |
| **STAFF** | Create dancers, register to categories | Start battles, encode results |
| **MC** | None | View queue, announce battles (read-only) |
| **JUDGE** | None | V2: Score battles directly |

### 7.3 User Confirmation

- [x] User confirmed problem statement (broader than just broken links - whole UX)
- [x] User chose mode switching approach (auto-detect + manual override)
- [x] User chose registration approach (one category at a time, two-panel view)
- [ ] User to validate acceptance criteria
- [ ] User to approve final requirements

---

**Status:** Business Analysis complete. Proceeding to Requirements Definition.
