# Feature Specification: Fix MissingGreenlet Error in Event Service

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

When accessing the Event Command Center page (`/event/{tournament_id}`), users encounter a **500 Server Error** with the message:

> **MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?**

This error prevents staff and MC users from accessing the event-day command center during active tournaments, which is critical functionality for tournament operations.

---

## 2. Executive Summary

### Scope
This analysis covers the SQLAlchemy async relationship loading bug that causes a 500 error when the EventService attempts to access lazy-loaded relationships outside of an async context.

### What Works ✅
| Feature | Status |
|---------|--------|
| Battle Repository fetches battles with performers | Production Ready |
| PerformerRepository loads dancer relationships | Production Ready |
| All other tournament routes | Production Ready |

### What's Broken 🚨
| Issue | Type | Location |
|-------|------|----------|
| EventService accesses `performer.dancer.blaze` without eager loading | BUG | `app/services/event_service.py:285` |
| BattleRepository doesn't chain-load `Performer.dancer` relationship | BUG | `app/repositories/battle.py:50` (and 8 other locations) |

### Key Business Rules Defined
- **BR-ASYNC-001:** All SQLAlchemy relationship access in async code must use eager loading (`selectinload`, `joinedload`)
- **BR-ASYNC-002:** Nested relationships (A→B→C) must be explicitly chained in eager loading options

---

## 3. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 USER ACTION: Access Event Command Center
═══════════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  User navigates to: /event/{tournament_id}                               │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Router: event.py:command_center()                                       │
  │  • Validates tournament exists                                           │
  │  • Checks user has MC role                                               │
  │  • Calls EventService.get_command_center_context()                       │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  EventService.get_command_center_context()                               │
  │  • Fetches tournament                                                    │
  │  • Fetches categories                                                    │
  │  • Calls _get_all_tournament_battles()                                   │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  EventService._get_all_tournament_battles()                              │
  │  • Calls battle_repo.get_by_category() for each category                 │
  │  • Returns List[Battle] with performers loaded                           │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  EventService._get_performer_display_name(performer)                     │
  │  • Accesses performer.dancer  ←── PROBLEM: Not eagerly loaded!           │
  │  • Accesses performer.dancer.blaze                                       │
  └──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  🚨 ERROR: MissingGreenlet                                               │
  │                                                                          │
  │  SQLAlchemy attempts to lazy-load dancer relationship                    │
  │  but there is no active async context (greenlet not spawned)             │
  │                                                                          │
  │  Result: 500 Server Error                                                │
  └──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
 ROOT CAUSE ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

  BattleRepository.get_by_category() uses:
    .options(selectinload(Battle.performers))

  This loads: Battle → List[Performer]

  But does NOT load: Performer → Dancer

  When EventService accesses performer.dancer.blaze:
  - SQLAlchemy tries to lazy-load the dancer relationship
  - Async SQLAlchemy requires explicit await for DB access
  - Lazy loading doesn't know how to await → MissingGreenlet error

═══════════════════════════════════════════════════════════════════════════════
 EXPECTED FLOW (After Fix)
═══════════════════════════════════════════════════════════════════════════════

  BattleRepository.get_by_category() should use:
    .options(
        selectinload(Battle.performers).selectinload(Performer.dancer)
    )

  This loads: Battle → List[Performer] → Dancer (per performer)

  Result: performer.dancer.blaze is already loaded, no lazy loading needed

═══════════════════════════════════════════════════════════════════════════════
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Event Command Center Must Load Successfully

**Business Rule BR-ASYNC-001: Eager Loading for Async Relationships**
> All SQLAlchemy relationship access in async services must use eager loading (`selectinload` or `joinedload`) to prevent lazy loading errors.

**Acceptance Criteria:**
```gherkin
Feature: Event Command Center Access
  As a staff or MC user
  I want to access the event command center during tournaments
  So that I can manage battles and track progress

Scenario: Access command center with active battles
  Given a tournament in PRESELECTION phase
  And at least one battle exists with performers
  When I navigate to /event/{tournament_id}
  Then I should see the command center page
  And I should see performer names (blazes) displayed correctly
  And I should NOT see a 500 error

Scenario: Access command center with pending queue
  Given a tournament with pending battles
  When I navigate to /event/{tournament_id}
  Then I should see the battle queue with performer names
  And each queue item should display performer1_name and performer2_name

Scenario: View current battle with performer names
  Given a tournament with an ACTIVE battle
  When I view the command center
  Then I should see the current battle card
  And performer names should be displayed (not "Unknown")
```

### 4.2 Nested Relationship Loading

**Business Rule BR-ASYNC-002: Chained Eager Loading for Nested Relationships**
> When a service method needs to access nested relationships (e.g., Battle → Performer → Dancer), all intermediate relationships must be explicitly loaded in the repository query.

**Acceptance Criteria:**
```gherkin
Scenario: Battle performers have dancer information loaded
  Given a battle with 2 performers
  When the battle is fetched from BattleRepository
  Then each performer should have its dancer relationship loaded
  And accessing performer.dancer.blaze should not trigger lazy loading
```

---

## 5. Current State Analysis

### 5.1 BattleRepository Query Pattern

**Business Rule:** Battle queries that return performers should also load dancer relationships.

**Implementation Status:** ⚠️ Partial

**Evidence:**
```python
# app/repositories/battle.py:48-52
async def get_by_category(self, category_id: uuid.UUID) -> List[Battle]:
    result = await self.session.execute(
        select(Battle)
        .options(selectinload(Battle.performers))  # ← Missing: .selectinload(Performer.dancer)
        .where(Battle.category_id == category_id)
    )
    return list(result.scalars().all())
```

**Affected Methods (9 locations in battle.py):**
| Line | Method | Current State |
|------|--------|---------------|
| 50 | `get_by_category` | Missing dancer loading |
| 71 | `get_by_category_and_status` | Missing dancer loading |
| 93 | `get_by_phase` | Missing dancer loading |
| 112 | `get_by_status` | Missing dancer loading |
| 125 | `get_active_battle` | Missing dancer loading |
| 141 | `get_with_performers` | Missing dancer loading |
| 202 | `get_by_tournament` | Missing dancer loading |
| 225 | `get_by_tournament_and_status` | Missing dancer loading |
| 274 | `get_pending_battles_ordered` | Missing dancer loading |

**Test Coverage:** ❓ Unknown - tests may mock repository methods

### 5.2 EventService Relationship Access

**Business Rule:** Service methods should not trigger lazy loading.

**Implementation Status:** ❌ Broken

**Evidence:**
```python
# app/services/event_service.py:278-295
def _get_performer_display_name(self, performer) -> str:
    """Get display name for a performer."""
    if not performer:
        return "TBD"

    # For solo: use blaze from dancer
    if hasattr(performer, 'dancer') and performer.dancer:  # ← Triggers lazy load!
        return performer.dancer.blaze                       # ← Triggers lazy load!

    # ... rest of method
```

**Called From:**
- `get_command_center_context()` line 139, 140
- `_get_battle_queue()` line 242, 244

### 5.3 PerformerRepository (Working Example)

**Evidence of correct pattern:**
```python
# app/repositories/performer.py:46-48
async def get_by_id_with_dancer(self, performer_id: uuid.UUID) -> Optional[Performer]:
    result = await self.session.execute(
        select(Performer)
        .options(selectinload(Performer.dancer))  # ← Correctly loads dancer
        .where(Performer.id == performer_id)
    )
```

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Fix BattleRepository to chain-load Performer.dancer**
   - Update all 9 methods that use `selectinload(Battle.performers)`
   - Change to: `selectinload(Battle.performers).selectinload(Performer.dancer)`
   - Files: `app/repositories/battle.py`

2. **Add integration test for EventService**
   - Test `get_command_center_context()` with real database
   - Verify no lazy loading errors occur
   - Files: `tests/integration/test_event_service.py` (new)

### 6.2 Recommended

1. **Create reusable eager loading options**
   - Define common loading patterns as constants
   - Example: `BATTLE_WITH_FULL_PERFORMERS = selectinload(Battle.performers).selectinload(Performer.dancer)`
   - Reduces duplication across methods

2. **Add type hints for relationship checks**
   - Consider using a helper method that explicitly expects loaded relationships
   - Fail fast if relationships are not loaded

### 6.3 Nice-to-Have (Future)

1. **Audit all services for similar patterns**
   - Search for `.relationship.attribute` access patterns
   - Verify corresponding repository uses eager loading

2. **Add linting rule or test**
   - Detect lazy loading attempts in async code
   - Could use custom SQLAlchemy event hooks

---

## 7. Appendix: Reference Material

### 7.1 Pattern Scan Results

**Pattern searched:** Accessing nested relationships (e.g., `performer.dancer.blaze`) without eager loading

**Search commands:**
```bash
grep -rn "\.dancer\." app/services/
grep -rn "selectinload(Battle.performers)" app/repositories/
```

**Results:**
| File | Line | Description |
|------|------|-------------|
| event_service.py | 285 | Accesses `performer.dancer.blaze` - triggers lazy load |
| battle.py | 50, 71, 93, 112, 125, 141, 202, 225, 274 | Uses `selectinload(Battle.performers)` without chaining to dancer |

**Decision:**
- [x] Fix all in this feature (update all 9 BattleRepository methods)

### 7.2 SQLAlchemy Async Best Practices

**From SQLAlchemy documentation:**

> When using async I/O with SQLAlchemy, all relationship loading must be eager (not lazy). Use `selectinload()` or `joinedload()` to pre-load relationships in the query.

**Correct Pattern:**
```python
# Load Battle → Performers → Dancer
select(Battle).options(
    selectinload(Battle.performers).selectinload(Performer.dancer)
)
```

**Incorrect Pattern (causes MissingGreenlet):**
```python
# Only loads Battle → Performers (dancer is lazy)
select(Battle).options(
    selectinload(Battle.performers)
)
# Then accessing performer.dancer triggers lazy load → Error
```

### 7.3 Error Details from Screenshot

**Error Message:**
```
MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
Was IO attempted in an unexpected place? (Background on this error at: https://sqlalche.me/e/20/xd2s)
```

**Stack Trace Location:**
- `/app/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py:121`
- `raise exc.MissingGreenlet(...)`

**URL:** `battle-d-production.up.railway.app/event/85dd9ae5-691c-4fd3-89bc-cdcfa343f4a2`

### 7.4 User Confirmation

- [x] User confirmed problem statement (500 error on event page)
- [x] User validated full feature spec approach
- [ ] User approved requirements (pending review)

---

## Next Steps

After this specification is approved:
1. Run `/plan-implementation FEATURE_SPEC_2025-12-08_FIX-MISSING-GREENLET-ERROR.md`
2. Implement the fix in BattleRepository
3. Add integration tests
4. Deploy and verify on production
