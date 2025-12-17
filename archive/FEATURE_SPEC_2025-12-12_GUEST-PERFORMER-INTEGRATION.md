# Feature Specification: Guest Performer Integration

**Date:** 2025-12-12
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

Tournament organizers need to invite pre-qualified performers (e.g., champions from other events, judges' picks, sponsors' invites) who should skip preselection and go directly to pools, while still participating in pool battles like regular competitors. Currently, all performers must go through the full preselection process, leaving no way to accommodate invited guests.

---

## 2. Executive Summary

### Scope
Integration of "Guest" performer concept into the registration workflow, with impacts on:
- Performer registration (new `is_guest` flag)
- Minimum performer calculation (guests reduce required regular performers)
- Preselection phase (guests get automatic top score of 10.0)
- Pool capacity (guests count toward capacity, taking spots from regulars)
- UI display (guests marked with badge in registration list)

### What Works Today
| Feature | Status |
|---------|--------|
| Dancer creation and management | Production Ready |
| Performer registration (1v1 and 2v2) | Production Ready |
| One dancer per tournament constraint | Production Ready |
| Preselection scoring (0-10 range) | Production Ready |
| Pool capacity calculation (equal sizes) | Production Ready |
| Phase transitions with validation | Production Ready |

### What's Missing
| Gap | Type | Impact |
|-----|------|--------|
| No guest performer concept | FEATURE GAP | Cannot invite pre-qualified performers |
| No way to skip preselection | FEATURE GAP | All performers must battle |
| Minimum calculation doesn't account for guaranteed qualifiers | LOGIC GAP | Guests should reduce minimum requirements |
| Registration UI doesn't distinguish performer types | UI GAP | No visual differentiation |

### Key Business Rules Defined
- **BR-GUEST-001:** Guest designation only allowed during Registration phase
- **BR-GUEST-002:** Guests automatically receive 10.0 preselection score (no battle required)
- **BR-GUEST-003:** Guests count toward pool capacity (take spots from regulars)
- **BR-GUEST-004:** Each guest reduces minimum performer requirement by 1
- **BR-GUEST-005:** Guests distributed randomly across pools (same as regulars)

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 PHASE: REGISTRATION                                          [Status: CREATED]
═══════════════════════════════════════════════════════════════════════════════

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  CURRENT REGISTRATION WORKFLOW:                                           │
  │                                                                           │
  │  1. Staff searches for dancer in database                                 │
  │  2. Staff clicks "Register" → creates Performer record                    │
  │  3. Performer appears in "Registered" list                                │
  │  4. Repeat until enough performers registered                             │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  NEW: GUEST REGISTRATION WORKFLOW                                         │
  │                                                                           │
  │  1. Staff searches for dancer in database                                 │
  │  2. Staff selects "Register as Guest" OR "Register (Regular)"             │
  │     └─ If Guest: is_guest = true, preselection_score = 10.0              │
  │     └─ If Regular: is_guest = false, preselection_score = null           │
  │  3. Performer appears in list with appropriate badge:                     │
  │     └─ [GUEST] B-Boy Champion - Pre-qualified                            │
  │     └─        B-Boy John - Regular registration                          │
  │  4. Minimum count adjusts: min_required = (groups * 2) + 1 - guest_count │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  VALIDATION CHECK (Registration → Preselection):                          │
  │                                                                           │
  │  NEW FORMULA:                                                             │
  │  ✅ adjusted_minimum = (groups_ideal × 2) + 1 - guest_count              │
  │  ✅ regular_count + guest_count >= adjusted_minimum + guest_count        │
  │                                                                           │
  │  EXAMPLE (groups_ideal = 2):                                              │
  │  • Standard minimum = (2 × 2) + 1 = 5                                    │
  │  • With 2 guests: need only 3 regulars (5 - 2 = 3)                       │
  │  • Total: 3 regulars + 2 guests = 5 performers (valid)                   │
  │                                                                           │
  │  ⚠️ Edge case: All guests (0 regulars)                                   │
  │     → Should we allow? Decision needed                                    │
  └───────────────────────────────────────────────────────────────────────────┘

  [ADMIN: ADVANCE PHASE] ──────────────────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE: PRESELECTION                                           [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  PRESELECTION BATTLES:                                                    │
  │                                                                           │
  │  CURRENT: Generate 1 battle per performer (all performers battle)         │
  │                                                                           │
  │  NEW: Generate 1 battle per REGULAR performer only                        │
  │     └─ Guests have preselection_score = 10.0 (already set at registration)│
  │     └─ Guests do NOT appear in preselection battle queue                  │
  │     └─ Guests shown in "Pre-Qualified" section of preselection view       │
  │                                                                           │
  │  EXAMPLE:                                                                 │
  │  • 5 total performers: 2 guests + 3 regulars                             │
  │  • System generates 3 preselection battles (regulars only)               │
  │  • Guests wait with score=10.0 (guaranteed top scorers)                  │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  POOL CAPACITY CALCULATION (unchanged algorithm, but guest impact):       │
  │                                                                           │
  │  pool_capacity = groups_ideal × performers_per_pool                       │
  │                                                                           │
  │  ⚠️ KEY INSIGHT: Guests count toward pool_capacity                       │
  │                                                                           │
  │  EXAMPLE (groups_ideal=2, performers_ideal=4, 9 total, 2 guests):        │
  │  • pool_capacity = 8 (2 pools × 4 performers)                            │
  │  • 2 guests guaranteed in pools (score=10.0)                             │
  │  • 6 spots remain for 7 regulars → 1 regular eliminated                  │
  │  • Top 6 regulars advance (by preselection_score)                        │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  VALIDATION CHECK (Preselection → Pools):                                 │
  │                                                                           │
  │  ✅ All preselection battles complete (REGULAR performers only)          │
  │  ✅ All performers have preselection_score set                           │
  │     └─ Guests: score = 10.0 (set at registration)                        │
  │     └─ Regulars: score = 0.0-10.0 (from battles)                         │
  │                                                                           │
  │  ⚠️ Edge case: Guest has same score as regular (both 10.0)              │
  │     → Guest wins tiebreak? Or random? Decision needed                     │
  └───────────────────────────────────────────────────────────────────────────┘

  [ADMIN: ADVANCE PHASE] ──────────────────────────────────────────────────────►

═══════════════════════════════════════════════════════════════════════════════
 PHASE: POOLS                                                  [Status: ACTIVE]
═══════════════════════════════════════════════════════════════════════════════

  ┌───────────────────────────────────────────────────────────────────────────┐
  │  POOL DISTRIBUTION (guests distributed same as regulars):                 │
  │                                                                           │
  │  1. Sort all qualified performers by preselection_score DESC             │
  │  2. Guests will be at top (score=10.0)                                   │
  │  3. Snake draft distribution applies to ALL (no special treatment)        │
  │                                                                           │
  │  EXAMPLE (8 qualifiers: 2 guests + 6 regulars, 2 pools):                 │
  │  Sorted: [Guest1-10.0, Guest2-10.0, Reg1-9.5, Reg2-9.0, ...]            │
  │  Pool A: Guest1, Reg2, Reg3, Reg6                                        │
  │  Pool B: Guest2, Reg1, Reg4, Reg5                                        │
  │                                                                           │
  │  ✅ Guests compete in pool battles like everyone else                    │
  │  ✅ No special treatment in pools or finals                              │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Guest Registration

**Business Rule BR-GUEST-001: Guest Designation Timing**
> Performers can only be designated as guests during the Registration phase. Once the tournament advances to Preselection, the guest flag cannot be changed.

**Acceptance Criteria:**
```gherkin
Feature: Guest Performer Registration
  As a tournament organizer
  I want to register invited performers as guests
  So that they can skip preselection and go directly to pools

  Scenario: Register dancer as guest during registration phase
    Given a tournament in REGISTRATION phase
    And a category "Hip Hop Boys 1v1" exists
    And a dancer "B-Boy Champion" exists in the database
    When I register "B-Boy Champion" as a guest
    Then a performer record is created with is_guest = true
    And the performer's preselection_score is set to 10.0
    And the performer appears in the registration list with a "Guest" badge

  Scenario: Cannot add guest after registration phase ends
    Given a tournament in PRESELECTION phase
    And a category with existing performers
    When I attempt to register a dancer as guest
    Then the system rejects with error "Guests can only be added during Registration phase"

  Scenario: Convert regular performer to guest
    Given a tournament in REGISTRATION phase
    And a performer "B-Boy John" is registered as regular
    When I mark "B-Boy John" as a guest
    Then the performer's is_guest becomes true
    And the performer's preselection_score is set to 10.0
```

---

### 4.2 Minimum Performer Calculation

**Business Rule BR-GUEST-004: Guests Reduce Minimum Requirements**
> Each guest reduces the minimum performer requirement by 1. The adjusted minimum ensures at least 1 regular performer must be eliminated in preselection.

**Formula:**
```
adjusted_minimum = max(2, (groups_ideal × 2) + 1 - guest_count)
```

**Acceptance Criteria:**
```gherkin
Feature: Adjusted Minimum Performer Calculation
  As a tournament organizer
  I want guests to reduce the minimum performer requirement
  So that I can run smaller events with invited guests

  Scenario: Minimum reduced by guest count
    Given a category with groups_ideal = 2
    And the standard minimum is 5 performers
    When I register 2 guests
    Then the adjusted minimum becomes 3 (5 - 2)
    And I need only 3 regular performers to advance phase

  Scenario: Minimum cannot go below 2
    Given a category with groups_ideal = 2
    And the standard minimum is 5 performers
    When I register 4 guests
    Then the adjusted minimum is 2 (not 1)
    And I need at least 2 regular performers

  Scenario: Phase validation uses adjusted minimum
    Given a category with groups_ideal = 2
    And 2 guests are registered
    And 3 regular performers are registered
    When I attempt to advance to PRESELECTION
    Then the validation passes (5 total >= 3 adjusted minimum + 2 guests)
```

---

### 4.3 Preselection Battle Generation

**Business Rule BR-GUEST-002: Guests Receive Automatic Top Score**
> Guests do not participate in preselection battles. They are automatically assigned the maximum score (10.0) at registration time, guaranteeing their advancement to pools.

**Acceptance Criteria:**
```gherkin
Feature: Preselection Battle Generation
  As a tournament organizer
  I want guests to skip preselection battles
  So that pre-qualified performers don't need to prove themselves again

  Scenario: Battles generated only for regular performers
    Given a category with 5 performers (2 guests + 3 regulars)
    When the tournament advances to PRESELECTION
    Then 3 preselection battles are created (one per regular)
    And guests have no battles assigned

  Scenario: Guests shown in pre-qualified section
    Given a tournament in PRESELECTION phase
    And a category with 2 guests and 3 regulars
    When I view the preselection dashboard
    Then guests appear in "Pre-Qualified (Guests)" section
    And guests show score "10.0" with "Guest" badge
    And regular performers appear in battle queue

  Scenario: Guest score is immutable
    Given a guest performer with preselection_score = 10.0
    When I attempt to modify the guest's preselection_score
    Then the system rejects with error "Guest scores cannot be modified"
```

---

### 4.4 Pool Capacity Impact

**Business Rule BR-GUEST-003: Guests Count Toward Pool Capacity**
> Guests occupy pool slots like regular performers. Their presence reduces the number of regular performers who can qualify from preselection.

**Acceptance Criteria:**
```gherkin
Feature: Pool Capacity with Guests
  As a tournament organizer
  I want guests to count toward pool capacity
  So that pool sizes remain balanced and predictable

  Scenario: Guests reduce spots for regular qualifiers
    Given a category with pool_capacity = 8 (2 pools × 4 performers)
    And 2 guests are registered
    And 8 regular performers are registered
    When pools are created after preselection
    Then 2 guests advance (guaranteed)
    And only top 6 regulars advance (by score)
    And 2 regulars are eliminated

  Scenario: Pool distribution includes guests
    Given 8 qualified performers (2 guests + 6 regulars)
    And 2 pools to create
    When performers are distributed to pools
    Then guests are distributed via snake draft like regulars
    And each pool has approximately equal guest count
    And pool sizes are equal (4 each)
```

---

### 4.5 Tiebreak at Pool Boundary

**Business Rule BR-GUEST-006: Guest Wins Boundary Tiebreak**
> When a guest and regular performer have the same score at the pool qualification boundary, the guest wins the tiebreak (guaranteed qualification).

**Acceptance Criteria:**
```gherkin
Feature: Tiebreak Resolution with Guests
  As a tournament organizer
  I want guests to win tiebreaks at the qualification boundary
  So that invited guests are guaranteed pool placement

  Scenario: Guest wins tiebreak against regular with same score
    Given pool_capacity = 4
    And 5 performers with scores:
      | Performer | Score | Is Guest |
      | A         | 10.0  | Yes      |
      | B         | 10.0  | No       |
      | C         | 9.0   | No       |
      | D         | 8.0   | No       |
      | E         | 7.0   | No       |
    When determining who advances
    Then Guest A advances (rank 1, guest priority)
    And Regular B advances (rank 2, highest regular)
    And Regular C advances (rank 3)
    And Regular D advances (rank 4)
    And Regular E is eliminated (rank 5)

  Scenario: Multiple guests with same score
    Given 2 guests both with score 10.0
    And they need to be ranked
    Then both advance (both guaranteed)
    And internal ranking is by registration order (first registered = higher rank)
```

---

## 5. Current State Analysis

### 5.1 Performer Model

**Business Rule:** Performers link dancers to tournament categories with stats.

**Implementation Status:** Production Ready

**Evidence:** `app/models/performer.py:21-119`

**Current Fields:**
- `tournament_id`, `category_id`, `dancer_id` - linking
- `duo_partner_id` - for 2v2 categories
- `preselection_score` - nullable, set during preselection
- `pool_wins`, `pool_draws`, `pool_losses` - pool stats

**Gap:** No `is_guest` field exists.

---

### 5.2 Minimum Performer Calculation

**Business Rule:** `minimum = (groups_ideal × 2) + 1`

**Implementation Status:** Production Ready

**Evidence:** `app/utils/tournament_calculations.py:9-41`

**Gap:** Does not account for guests reducing the minimum.

---

### 5.3 Preselection Battle Generation

**Business Rule:** Generate one battle per performer.

**Implementation Status:** Production Ready

**Evidence:** `ARCHITECTURE.md` Battle System Architecture section

**Gap:** Generates battles for all performers, should exclude guests.

---

### 5.4 Registration UI

**Business Rule:** Staff can register dancers to categories.

**Implementation Status:** Production Ready

**Evidence:** `app/templates/registration/register.html`

**Gap:** No option to register as guest, no guest badge display.

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Add `is_guest` field to Performer model**
   - Boolean field, default False
   - Set preselection_score = 10.0 when is_guest = True

2. **Update minimum performer calculation**
   - Modify `calculate_minimum_performers()` to accept guest_count parameter
   - Formula: `max(2, (groups_ideal × 2) + 1 - guest_count)`

3. **Update preselection battle generation**
   - Filter out guests when creating preselection battles
   - Only generate battles for performers where `is_guest = False`

4. **Add phase validation for guest timing**
   - Prevent is_guest changes after Registration phase
   - Validate in PerformerService

5. **Update registration UI**
   - Add "Register as Guest" button option
   - Display "Guest" badge on guest performers
   - Show adjusted minimum in category stats

### 6.2 Recommended

1. **Add guest count display in category overview**
   - Show "X guests, Y regulars" in registration summary

2. **Update preselection dashboard**
   - Add "Pre-Qualified (Guests)" section
   - Visually separate guests from battle queue

3. **Add guest conversion ability**
   - Allow marking existing regular performer as guest
   - Only during Registration phase

### 6.3 Nice-to-Have (Future)

1. **Guest invitation workflow**
   - Send email invitations to potential guests
   - Track invitation status (pending, accepted, declined)

2. **Guest quota per category**
   - Set maximum guest percentage (e.g., max 25% of pool capacity)
   - Prevent over-reliance on guests

3. **Guest reason/note field**
   - Optional text field explaining why dancer is a guest
   - "Previous champion", "Sponsor invite", etc.

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** What does 'guest' mean in Battle-D context?
  - **A:** Pre-qualified invited performer who skips preselection and goes directly to pools.

- **Q:** Should guests affect pool capacity calculation?
  - **A:** Yes - guests count toward capacity, taking spots from regular performers.

- **Q:** When can a guest be added to a category?
  - **A:** Only during Registration phase.

- **Q:** How should guests be distributed across pools?
  - **A:** Randomized distribution (same as regular performers via snake draft).

- **Q:** Should guests appear with special marking?
  - **A:** Yes - marked with "Guest" badge in registration list.

- **Q:** How do guests affect minimum performer requirement?
  - **A:** Each guest reduces the minimum by 1 (reduced minimum approach).

- **Q:** Do guests go through preselection battles?
  - **A:** No - they receive automatic top score (10.0) without battling.

- **Q:** Can all performers be guests (0 regulars)?
  - **A:** Open question - needs business decision. Recommendation: require minimum 2 regulars.

- **Q:** What happens if guest ties with regular at boundary?
  - **A:** Guest wins tiebreak (guaranteed qualification).

### 7.2 Formulas/Calculations

**Standard Minimum:**
```
minimum_performers = (groups_ideal × 2) + 1
```

**Adjusted Minimum (with guests):**
```
adjusted_minimum = max(2, (groups_ideal × 2) + 1 - guest_count)
```

**Pool Capacity (unchanged):**
```
pool_capacity = groups_ideal × performers_per_pool
```

**Spots Available for Regulars:**
```
regular_spots = pool_capacity - guest_count
```

### 7.3 User Confirmation

- [x] User confirmed problem statement (pre-qualified invited performers)
- [x] User validated guest type (skips preselection)
- [x] User confirmed pool impact (guests count toward capacity)
- [x] User confirmed timing (Registration phase only)
- [x] User confirmed distribution (randomized like regulars)
- [x] User confirmed visibility (Guest badge marking)
- [x] User confirmed minimum impact (reduced by guest count)
- [x] User confirmed preselection handling (automatic 10.0 score)
