# Feature Specification: Fix Command Center Missing Progress Variable

**Date:** 2025-12-08
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

The Event Command Center page (`/event/{tournament_id}`) crashes with a 500 Server Error when accessed because the template expects a `progress` variable that the router doesn't provide. This prevents MC/Staff from accessing the event mode during live tournaments.

---

## 2. Executive Summary

### Scope
Fix the missing template context variables in the Event Command Center route.

### What Works ✅
| Feature | Status |
|---------|--------|
| HTMX partial: `/event/{id}/progress` | Production Ready - passes `progress` correctly |
| HTMX partial: `/event/{id}/queue` | Production Ready - passes `queue` correctly |
| HTMX partial: `/event/{id}/current-battle` | Production Ready - passes `context` correctly |
| Service: `get_phase_progress()` | Production Ready |
| Service: `get_command_center_context()` | Production Ready |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| `progress` not passed to template | BUG | `app/routers/event.py:98-108` |
| `queue` not passed to template | BUG | `app/routers/event.py:98-108` |

### Key Business Rules Defined
- **BR-UI-001:** All template partials must receive their required context variables from parent templates

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 USER ACTION: Navigate to /event/{tournament_id}
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Route: command_center() in app/routers/event.py                         │
  │                                                                          │
  │  Current context passed to template:                                     │
  │  ✅ current_user                                                         │
  │  ✅ context (CommandCenterContext)                                       │
  │  ✅ tournament                                                           │
  │  ✅ active_tournament                                                    │
  │  ✅ category_filter                                                      │
  │  ✅ flash_messages                                                       │
  │  ❌ progress (MISSING!)                                                  │
  │  ❌ queue (MISSING - but fails gracefully)                               │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Template: command_center.html                                           │
  │                                                                          │
  │  Line 12: {% include "event/_current_battle.html" %}                     │
  │           → Uses `context` ✅                                            │
  │                                                                          │
  │  Line 41: {% include "event/_battle_queue.html" %}                       │
  │           → Uses `queue` but handles None gracefully                     │
  │                                                                          │
  │  Line 50: {% include "event/_phase_progress.html" %}                     │
  │           → Uses `progress.completed`, `progress.total`, etc.            │
  │           🚨 CRASHES: 'progress' is undefined                            │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  🚨 500 Server Error                                                     │
  │  UndefinedError: 'progress' is undefined                                 │
  │                                                                          │
  │  Traceback points to:                                                    │
  │  - app/templates/event/_phase_progress.html, line 5                      │
  │  - {{ progress.completed }}/{{ progress.total }}                         │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Event Command Center Must Load Successfully

**Business Rule BR-UI-001: Template Context Completeness**
> When rendering a template that includes partials, the route must provide all variables required by those partials.

**Acceptance Criteria:**
```gherkin
Feature: Event Command Center page loads successfully
  As an MC or Staff member
  I want to view the Event Command Center
  So that I can manage live tournament battles

Scenario: Command center loads for active tournament
  Given a tournament exists in PRESELECTION phase
  And I am logged in as MC role
  When I navigate to /event/{tournament_id}
  Then the page should load without errors
  And I should see the phase progress bar
  And I should see the battle queue
  And I should see the current battle section

Scenario: Command center shows progress correctly
  Given a tournament has 10 total battles
  And 3 battles are completed
  When I view the Event Command Center
  Then I should see "3/10 battles completed"
  And the progress bar should show 30%
```

---

## 5. Current State Analysis

### 5.1 Main Route Missing Context Variables

**Business Rule:** Template partials receive required variables
**Implementation Status:** ❌ Broken

**Evidence:**
```python
# app/routers/event.py:98-108
return templates.TemplateResponse(
    request=request,
    name="event/command_center.html",
    context={
        "current_user": user,
        "context": context,
        "tournament": tournament,
        "active_tournament": active_tournament,
        "category_filter": category_uuid,
        "flash_messages": flash_messages,
        # MISSING: "progress": progress,
        # MISSING: "queue": queue,
    },
)
```

**Test Coverage:** ❌ No E2E test loads command center with real tournament

### 5.2 HTMX Partial Routes Work Correctly

**Implementation Status:** ✅ Working

**Evidence:**
- `progress_partial()` at line 222-230 correctly passes `progress`
- `queue_partial()` at line 184-194 correctly passes `queue`
- `current_battle_partial()` at line 137-147 correctly passes `context`

---

## 6. Implementation Recommendations

### 6.1 Critical (Must Fix)

1. **Add `progress` and `queue` to main route context**
   - Call `event_service.get_phase_progress()` in `command_center()` route
   - Call `event_service.get_battle_queue()` in `command_center()` route
   - Add both to template context
   - File: `app/routers/event.py:90-108`

### 6.2 Recommended

1. **Add E2E test for command center with real tournament**
   - Create tournament in event phase via HTTP
   - Verify page loads successfully (status 200)
   - This would have caught the bug

### 6.3 Nice-to-Have (Future)

1. **Consider adding template variable validation**
   - Jinja2 `undefined` behavior could be configured to fail loudly in dev
   - Would catch missing variables earlier

---

## 7. Appendix: Reference Material

### 7.1 Why Tests Didn't Catch This Bug

**Root Cause:** No E2E test loads the command center with a REAL tournament in an event phase.

**Evidence from `tests/e2e/test_event_mode.py:182-187`:**
```python
# NOTE: Tests with real battle data (TestBattleWorkflowWithRealData,
# TestEventModeWithRealTournament) removed due to database session isolation.
# Data created in async fixtures is not visible to TestClient.
# These code paths are covered by service integration tests instead
```

**The gap:**
- Service integration tests verify the SERVICE returns correct data
- But no test verifies the ROUTER passes all required variables to the TEMPLATE
- The existing E2E test only uses a non-existent tournament ID (returns 404 before template renders)

### 7.2 Pattern Scan Results

**Pattern searched:** Templates including partials without required context

**Search command:**
```bash
grep -rn "include.*event/_" app/templates/
```

**Results:**
| File | Line | Partial | Required Variable | Status |
|------|------|---------|-------------------|--------|
| `command_center.html` | 12 | `_current_battle.html` | `context` | ✅ Provided |
| `command_center.html` | 41 | `_battle_queue.html` | `queue` | ❌ Missing (graceful) |
| `command_center.html` | 50 | `_phase_progress.html` | `progress` | ❌ **Missing (CRASH)** |

**Decision:**
- [x] Fix all in this feature (add both `progress` and `queue`)

### 7.3 User Confirmation

- [x] User confirmed problem statement (screenshot of 500 error)
- [x] User asked why tests didn't catch it (answered)
- [ ] User approved requirements (pending review)
