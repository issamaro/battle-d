# Feature Specification: Screen Consolidation - Phases & Battles

**Date:** 2024-12-18
**Status:** Approved - Ready for Implementation

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

Two screens in the application create confusion and workflow issues:
1. **Tournament Phases screen** (`/tournaments/{id}/phase`) - Partially redundant, displays information already shown elsewhere
2. **Battles screen** (`/battles`) - Non-functional due to missing category selection UI

These screens contribute to a "Frankenstein app" effect where users encounter incomplete or duplicated functionality, disrupting their workflow and causing confusion about where to perform key tasks.

---

## 2. Executive Summary

### Scope
Analysis of two screens flagged by user as problematic, with assessment of their necessity and recommendations for consolidation.

### What Works (Partially)

| Screen | Status | Assessment |
|--------|--------|------------|
| Tournament Phases | Functional | Redundant - same info on Dashboard + Tournament Detail |
| Battles List | **Non-functional** | Missing category selection UI - users cannot use it |

### What's Broken

| Issue | Type | Location |
|-------|------|----------|
| No category selector on Battles screen | BUG | `app/templates/battles/list.html` |
| Sidebar "Battle Queue" link goes to broken URL | BUG | `app/templates/base.html:185` |
| 3 different screens show phase info | REDUNDANCY | Dashboard, Tournament Detail, Phases screen |
| 2 different ways to manage battles | REDUNDANCY | Battles screen vs Event Mode |

### Key Business Rules Affected
- **BR-NAV-001:** Users should have ONE clear path to each major function
- **BR-UX-001:** All screens must be fully functional (no dead ends)
- **BR-WF-001:** Event mode is the primary workflow for tournament execution

---

## 3. User Flow Diagram

```
===================================================================
 CURRENT STATE: FRAGMENTED NAVIGATION
===================================================================

                     ┌─────────────────┐
                     │    Dashboard    │
                     │   (/overview)   │
                     └────────┬────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Tournament      │ │ "Manage Phases" │ │ "Event Mode"    │
│ Detail          │ │ Link            │ │ Button          │
│ (/tournaments/) │ │                 │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   │                   ▼
┌─────────────────┐          │          ┌─────────────────┐
│ "Manage Phase"  │          │          │ Event Command   │
│ Button          │──────────┤          │ Center          │
└────────┬────────┘          │          │ (/event/{id})   │
         │                   │          │                 │
         └───────────────────┤          │ ✅ Has:         │
                             │          │ - Category tabs │
                             ▼          │ - Battle queue  │
                   ┌─────────────────┐  │ - Phase display │
                   │ Phase Screen    │  │ - All actions   │
                   │ (/tournaments/  │  └─────────────────┘
                   │  {id}/phase)    │
                   │                 │
                   │ ⚠️ REDUNDANT:   │
                   │ Same info as    │
                   │ Dashboard       │
                   └─────────────────┘


===================================================================
 SIDEBAR: "BATTLE QUEUE" LINK
===================================================================

┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR NAVIGATION                                             │
│  ─────────────────                                              │
│  • Dashboard                                                    │
│  • Dancers (staff)                                              │
│  • Tournaments (staff)                                          │
│  • Users (admin)                                                │
│  ─────────────────                                              │
│  [Active Tournament Name]                                       │
│  • Tournament Details                                           │
│  • Phases (admin only)                                          │
│  • Battle Queue ────────► /battles (NO CATEGORY!)               │
└─────────────────────────────────────────────────────────────────┘

                             │
                             ▼
              ┌─────────────────────────────┐
              │ Battles Screen (/battles)   │
              │                             │
              │ 🚨 BROKEN:                  │
              │ "No Category Selected"      │
              │ "Please select a category"  │
              │                             │
              │ ❌ NO WAY TO SELECT ONE!    │
              │                             │
              │ User is stuck here.         │
              └─────────────────────────────┘


===================================================================
 RECOMMENDED STATE: CONSOLIDATED NAVIGATION
===================================================================

                     ┌─────────────────┐
                     │    Dashboard    │
                     │   (/overview)   │
                     └────────┬────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│ Tournament      │                     │ "Event Mode"    │
│ Detail          │                     │ Button          │
│ (/tournaments/) │                     │ (primary CTA)   │
└────────┬────────┘                     └────────┬────────┘
         │                                       │
         │ (View tournament                      ▼
         │  info only)               ┌─────────────────┐
         │                           │ Event Command   │
         │                           │ Center          │
         │                           │ (/event/{id})   │
         │                           │                 │
         │                           │ ✅ Has:         │
         │                           │ - Category tabs │
         │                           │ - Battle queue  │
         │                           │ - Phase display │
         │                           │ - Advance phase │
         │                           │   (moved here)  │
         │                           └─────────────────┘
         │
         │ Only if needed:
         ▼
┌─────────────────┐
│ Phases Screen   │
│ (Archived View) │
│ OR DELETED      │
└─────────────────┘

SIDEBAR CHANGES:
• Remove "Battle Queue" link OR redirect to Event Mode
• Remove "Phases" link (if consolidating to Event Mode)
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Screen Necessity Assessment

**Business Rule BR-NAV-001: Single Path to Functions**
> Users should have ONE clear, functional path to each major application function. Duplicate paths create confusion.

**Acceptance Criteria:**
```gherkin
Feature: Consolidated Navigation
  As a tournament staff member
  I want clear, non-duplicated navigation
  So that I always know where to find functionality

Scenario: Accessing battle management
  Given I am logged in as MC or Admin
  When I want to manage tournament battles
  Then there should be exactly ONE obvious path (Event Mode)
  And that path should always work (no dead ends)

Scenario: Accessing phase management
  Given I am logged in as Admin
  When I want to advance tournament phase
  Then I should find this option in Event Mode
  And NOT need to visit a separate "Phases" screen
```

### 4.2 Battles Screen Issue

**Business Rule BR-UX-001: No Dead-End Screens**
> Every navigable screen must be fully functional. Users should never encounter a screen that requires parameters they cannot provide.

**Acceptance Criteria:**
```gherkin
Feature: Battles Screen Fix
  As a staff member
  I want the Battles screen to be functional
  So that I can view battles without editing URLs

Scenario: Navigating to Battles via sidebar
  Given I click "Battle Queue" in the sidebar
  When the Battles screen loads
  Then I should either:
    | Option A | See a category selector to choose battles |
    | Option B | Be redirected to Event Mode with battles   |
  And I should NOT see "No Category Selected" with no way to fix it
```

### 4.3 Phase Screen Redundancy

**Business Rule BR-WF-001: Event Mode as Primary Workflow**
> Event Mode is the designed workflow for running tournaments. Other screens should support it, not duplicate it.

**Acceptance Criteria:**
```gherkin
Feature: Phase Management Location
  As an admin
  I want phase management in one logical place
  So that I don't have to navigate between multiple screens

Scenario: Phase advancement during event
  Given I am running a tournament in Event Mode
  When I need to advance to the next phase
  Then I should be able to do so from Event Mode
  And NOT need to leave to a separate Phases screen
```

---

## 5. Current State Analysis

### 5.1 Tournament Phases Screen

**What it does:**
- Shows current phase (PRESELECTION in screenshot)
- Lists all 5 phases with descriptions
- Shows "Advance to pools" button for admins
- Displays validation errors before advancing

**Implementation Status:** ✅ Functional but redundant

**Evidence:**
- Route: `app/routers/phases.py:26-66`
- Template: `app/templates/phases/overview.html`
- Same phase info shown at: Dashboard, Tournament Detail, Event Mode

**Problems:**
1. Provides NO additional functionality over Event Mode
2. Creates confusion about where to manage phases
3. Two navigation paths lead here (Dashboard + Tournament Detail)
4. No battle context - admin can't see readiness before advancing

### 5.2 Battles Screen

**What it should do:**
- List battles for a tournament category
- Allow filtering by status (All, Pending, Active, Completed)
- Allow starting battles, encoding results
- Allow reordering battle queue

**Implementation Status:** ❌ Non-functional

**Evidence:**
- Route: `app/routers/battles.py:33-87` (requires `category_id`)
- Template: `app/templates/battles/list.html:149-152` (empty state)
- Sidebar link: `app/templates/base.html:185` (missing `category_id`)

**Critical Bug:**
```python
# battles.py line 33-35
@router.get("")
async def list_battles(..., category_id: Optional[UUID] = Query(None)):
    if not category_id:
        # Shows "No Category Selected" with NO way to select one
```

**Test Coverage:** No test for missing category selector scenario

### 5.3 Event Mode Command Center

**What it does:**
- Shows current battle with full context
- Lists battle queue with reordering
- Has category tabs for filtering
- Shows phase progress
- Has all battle actions (start, encode, complete)

**Implementation Status:** ✅ Complete and functional

**Assessment:** This is the superior implementation. The Battles screen duplicates its functionality but without the category selection.

---

## 6. Implementation Recommendations

### 6.1 Critical - APPROVED FOR IMPLEMENTATION

**User Decision:** Remove both screens and consolidate into Event Mode

1. **Remove Battles Screen**
   - Delete `/battles` route from `app/routers/battles.py`
   - Delete `app/templates/battles/list.html` and related templates
   - Remove "Battle Queue" link from sidebar (`app/templates/base.html`)
   - Keep battle detail routes if still needed by Event Mode

2. **Remove Phases Screen**
   - Delete `/tournaments/{id}/phase` route from `app/routers/phases.py`
   - Delete `app/templates/phases/overview.html` and related templates
   - Remove "Phases" link from sidebar
   - Move phase advancement functionality to Event Mode (if not already there)

3. **Update Navigation**
   - Remove broken sidebar links
   - Ensure Event Mode is the single entry point for battle/phase management
   - Update any dashboard links that pointed to removed screens

### 6.2 Recommended (Part of this work)

1. **Verify Event Mode has all functionality**
   - Confirm phase advancement is available in Event Mode
   - Confirm battle queue is accessible via Event Mode
   - No functionality loss from removing screens

2. **Update tests**
   - Remove tests for deleted routes
   - Add tests to verify removed routes return 404 or redirect

### 6.3 Nice-to-Have (Future)

1. **Add Quick Navigation from Event Mode**
   - "View Tournament Details" link
   - "Back to Dashboard" link

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Why does the Battles screen exist if Event Mode is complete?
  - **A:** Likely created before Event Mode was built, now orphaned

- **Q:** Should Battles screen be fixed or removed?
  - **A:** **DECIDED: REMOVE** - User approved removal

- **Q:** Is Phase screen ever needed?
  - **A:** **DECIDED: REMOVE** - User approved removal, consolidate to Event Mode

### 7.2 Affected Files

| File | Action |
|------|--------|
| `app/routers/battles.py` | **DELETE** route for `/battles` list (keep detail routes if needed) |
| `app/templates/battles/list.html` | **DELETE** |
| `app/templates/base.html` | **EDIT** - Remove "Battle Queue" and "Phases" sidebar links |
| `app/routers/phases.py` | **DELETE** |
| `app/templates/phases/overview.html` | **DELETE** |
| `app/templates/phases/confirm_advance.html` | **DELETE** (or move to Event Mode) |
| `app/templates/phases/validation_errors.html` | **DELETE** (or move to Event Mode) |
| `app/routers/event.py` | **VERIFY** - Ensure phase advance functionality exists |

### 7.3 User Confirmation

- [x] User confirmed problem statement (screens are confusing/broken)
- [x] User validated scenarios match their vision (consolidate to Event Mode)
- [x] User approved removal vs. fix decision (**REMOVE both screens**)
- [x] User approved navigation consolidation approach (Event Mode as single entry)
