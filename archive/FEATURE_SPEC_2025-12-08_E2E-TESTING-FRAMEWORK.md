# Feature Specification: End-to-End Testing Framework

**Date:** 2025-12-08
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagrams](#3-user-flow-diagrams)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

Current test coverage focuses on service and repository layers (83% service coverage), but lacks HTTP-level tests that validate complete user workflows. This means individual components may work correctly in isolation, but integration issues between routes, templates, and services can go undetected until manual testing or production.

---

## 2. Executive Summary

### Scope
Add comprehensive end-to-end testing for critical user flows using two complementary approaches:
1. **HTTP + Real DB Tests** - Fast, reliable tests using httpx/TestClient with real database
2. **Browser Automation (Future)** - Playwright-based tests for true browser E2E testing

### Priority Flows
1. **Event Mode** - MC workflow for tournament day (critical)
2. **Tournament Management** - Admin workflow for setup

### Current Test Coverage

| Test Type | Count | Status |
|-----------|-------|--------|
| Unit Tests | ~50 | ✅ Good |
| Repository Tests | ~35 | ✅ Good |
| Service Integration | ~100 | ✅ Good (83% coverage) |
| HTTP/Route Tests | ~30 | ⚠️ Partial |
| E2E User Flows | 0 | ❌ Missing |

### What's Missing

| Gap | Impact | Priority |
|-----|--------|----------|
| Event Mode HTTP tests | Can't validate tournament day workflow | Critical |
| Tournament management HTTP tests | Admin workflow untested at HTTP level | High |
| HTMX partial response tests | Interactive features untested | High |
| Authentication flow tests | Login/logout cycle not fully tested | Medium |

---

## 3. User Flow Diagrams

### 3.1 Event Mode Flow (Critical)

```
═══════════════════════════════════════════════════════════════
 EVENT MODE: MC TOURNAMENT DAY WORKFLOW
═══════════════════════════════════════════════════════════════

  [MC Authentication]
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  GET /event                                              │
  │  ────────────────────────────────────────────────────────│
  │  • Loads Command Center                                  │
  │  • Shows active tournament                               │
  │  • Lists categories and battles                          │
  │                                                          │
  │  TEST: Response 200, contains tournament name            │
  │  TEST: Contains battle cards for current phase           │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  POST /event/battles/{id}/start                          │
  │  ────────────────────────────────────────────────────────│
  │  • Changes battle status PENDING → ACTIVE                │
  │  • Returns updated battle card (HTMX partial)            │
  │                                                          │
  │  TEST: Battle status updated in DB                       │
  │  TEST: Response is partial HTML (no <html> tag)          │
  │  TEST: Response contains "ACTIVE" badge                  │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  POST /event/battles/{id}/encode                         │
  │  ────────────────────────────────────────────────────────│
  │  • Validates scores/outcome                              │
  │  • Updates battle and performers                         │
  │  • Returns success or validation error                   │
  │                                                          │
  │  TEST: Valid scores → battle COMPLETED                   │
  │  TEST: Invalid scores → validation error message         │
  │  TEST: Performer scores updated in DB                    │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  GET /event/battles/{id}/next                            │
  │  ────────────────────────────────────────────────────────│
  │  • Returns next pending battle                           │
  │  • Or indicates phase complete                           │
  │                                                          │
  │  TEST: Returns next battle in sequence                   │
  │  TEST: When no battles left, indicates phase complete    │
  └──────────────────────────────────────────────────────────┘
```

### 3.2 Tournament Management Flow

```
═══════════════════════════════════════════════════════════════
 TOURNAMENT MANAGEMENT: ADMIN SETUP WORKFLOW
═══════════════════════════════════════════════════════════════

  [Admin Authentication]
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  GET /tournaments                                        │
  │  ────────────────────────────────────────────────────────│
  │  • Lists all tournaments                                 │
  │  • Shows status badges                                   │
  │                                                          │
  │  TEST: Response 200, tournament list rendered            │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  POST /tournaments/create                                │
  │  ────────────────────────────────────────────────────────│
  │  • Creates new tournament                                │
  │  • Redirects to tournament detail                        │
  │                                                          │
  │  TEST: Tournament created in DB                          │
  │  TEST: Redirects to /tournaments/{id}                    │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  POST /tournaments/{id}/categories/create                │
  │  ────────────────────────────────────────────────────────│
  │  • Adds category to tournament                           │
  │  • Returns updated category list (HTMX)                  │
  │                                                          │
  │  TEST: Category created in DB                            │
  │  TEST: Response contains new category                    │
  └──────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │  POST /tournaments/{id}/advance                          │
  │  ────────────────────────────────────────────────────────│
  │  • Validates phase requirements                          │
  │  • Advances to next phase                                │
  │  • Generates battles/pools as needed                     │
  │                                                          │
  │  TEST: Valid → phase advances, success message           │
  │  TEST: Invalid → error message, phase unchanged          │
  └──────────────────────────────────────────────────────────┘
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Event Mode E2E Tests

**Business Rule BR-E2E-001: Event Mode Critical Path**
> An authenticated MC should be able to complete a full battle encoding workflow through the HTTP interface.

**Acceptance Criteria:**
```gherkin
Feature: Event Mode Battle Workflow
  As an MC
  I want to start and encode battles through the event interface
  So that I can run a tournament efficiently

  Background:
    Given an active tournament with battles in PENDING status
    And I am authenticated as an MC

  Scenario: Start a battle
    Given I am viewing the event command center
    When I click "Start Battle" for a pending battle
    Then the battle status changes to ACTIVE
    And I see the updated battle card with ACTIVE badge

  Scenario: Encode preselection scores
    Given a battle is in ACTIVE status with PRESELECTION phase
    When I submit valid scores for all performers
    Then the battle status changes to COMPLETED
    And the performer preselection scores are updated

  Scenario: Encode pool results with winner
    Given a battle is in ACTIVE status with POOLS phase
    When I select a winner and submit
    Then the battle status changes to COMPLETED
    And the winner has pool_wins incremented
    And the loser has pool_losses incremented

  Scenario: Validation error preserves form
    Given a battle is in ACTIVE status
    When I submit incomplete scores
    Then I see a validation error message
    And the form retains my entered values
    And the battle status remains ACTIVE
```

### 4.2 Tournament Management E2E Tests

**Business Rule BR-E2E-002: Tournament Setup Path**
> An authenticated admin should be able to create and configure a tournament through the HTTP interface.

**Acceptance Criteria:**
```gherkin
Feature: Tournament Management Workflow
  As an Admin
  I want to create and configure tournaments
  So that I can prepare for events

  Background:
    Given I am authenticated as an Admin

  Scenario: Create new tournament
    Given I am on the tournaments list page
    When I submit the create tournament form with valid data
    Then a new tournament is created
    And I am redirected to the tournament detail page

  Scenario: Add category to tournament
    Given I am viewing a tournament in REGISTRATION phase
    When I add a new category with valid settings
    Then the category is created
    And I see the category in the list

  Scenario: Advance tournament phase
    Given a tournament has minimum required performers
    When I click "Advance Phase"
    Then the tournament phase advances
    And appropriate battles/pools are generated

  Scenario: Phase advance blocked when requirements not met
    Given a tournament has insufficient performers
    When I click "Advance Phase"
    Then I see an error message explaining what's missing
    And the phase remains unchanged
```

### 4.3 HTMX Interaction Tests

**Business Rule BR-E2E-003: HTMX Partial Responses**
> All HTMX endpoints must return partial HTML (not full pages) when HX-Request header is present.

**Acceptance Criteria:**
```gherkin
Feature: HTMX Partial Responses
  As a user
  I want smooth partial page updates
  So that I have a responsive experience

  Scenario: HTMX request returns partial HTML
    Given an HTMX-enabled endpoint
    When I send a request with HX-Request header
    Then the response contains only the target content
    And the response does not contain <html> or <body> tags

  Scenario: Regular request returns full page
    Given an HTMX-enabled endpoint
    When I send a request without HX-Request header
    Then the response contains the full page
    And the response includes <html> and <body> tags
```

---

## 5. Current State Analysis

### 5.1 Existing HTTP Test Infrastructure

**Location:** `tests/test_crud_workflows.py`

**What exists:**
- MockEmailProvider for testing email flows
- Session cookie extraction helper
- Basic CRUD workflow tests for users

**What's reusable:**
- Authentication pattern (get_session_cookie)
- Test client setup with dependency overrides
- Database session management

### 5.2 Route Coverage Analysis

| Router | File | HTTP Tests | Status |
|--------|------|------------|--------|
| Auth | `auth.py` | `test_auth.py` | ⚠️ Unit tests only |
| Admin | `admin.py` | `test_crud_workflows.py` | ⚠️ Partial |
| Battles | `battles.py` | None | ❌ Missing |
| Dashboard | `dashboard.py` | None | ❌ Missing |
| Event | `event.py` | None | ❌ Missing |
| Phases | `phases.py` | `test_phases_routes.py` | ✅ Exists |
| Registration | `registration.py` | None | ❌ Missing |
| Tournaments | `tournaments.py` | None | ❌ Missing |
| Dancers | `dancers.py` | `test_crud_workflows.py` | ⚠️ Partial |

### 5.3 Test Fixtures Needed

Current fixtures in `conftest.py`:
- `async_session_maker` - Database session factory
- Factory functions for dancers, tournaments, categories, performers

**Additional fixtures needed:**
- Authenticated test client (admin, staff, mc, judge)
- Pre-populated tournament with battles
- HTMX request helpers

---

## 6. Implementation Recommendations

### 6.1 Critical (Phase 1 - Immediate)

1. **Create test infrastructure module** (`tests/e2e/__init__.py`)
   - Authenticated client fixtures for each role
   - Database factory functions for test data
   - HTMX test helpers

2. **Event Mode E2E tests** (`tests/e2e/test_event_mode.py`)
   - Test complete battle workflow: view → start → encode
   - Test HTMX partial responses
   - Test validation error handling

3. **Tournament Management E2E tests** (`tests/e2e/test_tournament_management.py`)
   - Test create tournament flow
   - Test add category flow
   - Test phase advancement with validation

### 6.2 Recommended (Phase 2)

4. **HTMX-specific tests** (`tests/e2e/test_htmx_interactions.py`)
   - Verify all HTMX endpoints return partials
   - Test form error preservation
   - Test flash messages

5. **Authentication E2E tests** (`tests/e2e/test_authentication.py`)
   - Full magic link flow
   - Session management
   - Role-based access control

6. **Dashboard tests** (`tests/e2e/test_dashboard.py`)
   - Role-specific dashboard rendering
   - Quick action navigation

### 6.3 Nice-to-Have (Phase 3 - Future)

7. **Playwright browser tests** (`tests/browser/`)
   - True E2E with real browser
   - Visual regression testing
   - Cross-browser testing

8. **Performance tests**
   - Response time assertions
   - Load testing setup

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should we use sync TestClient or async AsyncClient?
  - **A:** Use sync TestClient for simplicity (like existing test_crud_workflows.py). AsyncClient can be used where needed.

- **Q:** How to handle database state between tests?
  - **A:** Use pytest fixtures with function scope, letting each test have clean state.

### 7.2 Test File Structure

```
tests/
├── e2e/
│   ├── __init__.py           # E2E test infrastructure
│   ├── conftest.py           # E2E-specific fixtures
│   ├── test_event_mode.py    # Event mode workflow tests
│   ├── test_tournament_management.py
│   ├── test_htmx_interactions.py
│   └── test_authentication.py
├── browser/                   # Future: Playwright tests
│   └── ...
└── (existing test files)
```

### 7.3 User Confirmation

- [x] User confirmed priority flows: Event Mode, Tournament Management
- [x] User confirmed testing approach: HTTP + Real DB, with Playwright for future
- [x] User approved scope of E2E testing framework

---

## Next Steps

1. User reviews this specification
2. User provides feedback/approval
3. Run `/plan-implementation` to create technical design
