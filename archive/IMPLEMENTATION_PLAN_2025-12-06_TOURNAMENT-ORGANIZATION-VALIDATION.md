# Implementation Plan: Tournament Organization Validation

**Date:** 2025-12-06
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-04_TOURNAMENT-ORGANIZATION-VALIDATION.md

---

## 1. Summary

**Feature:** Fix tournament organization bugs (pool sizing, tiebreak auto-creation, battle interleaving) and ensure production-ready validation for tournament flow.

**Approach:**
1. Fix the 25% elimination rule bug with correct equal-pool-sizing algorithm
2. Integrate tiebreak auto-detection into battle completion flow (trigger on last battle scored)
3. Add battle queue interleaving and reordering with proper constraints
4. Update tests to cover all edge cases

---

## 2. Affected Files

### Backend

**Utils:**
- `app/utils/tournament_calculations.py`: **FIX** `calculate_pool_capacity()` - replace 25% rule with equal pool sizing algorithm

**Services:**
- `app/services/battle_service.py`:
  - **NEW** `generate_battles_interleaved()` - interleave battles across categories
  - **NEW** `reorder_battle()` - reorder pending battles with constraints
  - **MODIFY** `complete_battle()` - trigger tiebreak detection after completion
- `app/services/battle_results_encoding_service.py`:
  - **MODIFY** encoding methods - trigger tiebreak detection on last battle completion
- `app/services/tiebreak_service.py`:
  - **MODIFY** `detect_preselection_ties()` - ensure correct integration
  - **NEW** `detect_and_create_tiebreak()` - combined detection + battle creation
- `app/services/pool_service.py`:
  - **MODIFY** `create_pools_from_preselection()` - use fixed pool capacity calculation
  - **MODIFY** `check_for_ties()` - trigger auto-creation of tiebreak battles
- `app/services/tournament_service.py`:
  - **MODIFY** `_execute_phase_transition_hooks()` - use interleaved battle generation

**Repositories:**
- `app/repositories/battle.py`:
  - **NEW** `get_pending_battles_ordered()` - get battles with sequence_order
  - **NEW** `update_sequence_order()` - update battle order
  - **NEW** `count_pending_by_category_and_phase()` - count for tiebreak detection

**Routes:**
- `app/routers/battles.py`:
  - **NEW** `POST /battles/reorder` - battle reorder endpoint
  - **MODIFY** battle list - add category filter for interleaved view

**Models:**
- `app/models/battle.py`:
  - **NEW** `sequence_order: int` - battle queue position (nullable, for ordering)

### Frontend

**Templates:**
- `app/templates/battles/list.html`:
  - **MODIFY** Add drag-and-drop reordering UI (HTMX)
  - **MODIFY** Show locked vs movable battles
  - **MODIFY** Add category filter chips
- `app/templates/battles/_battle_card.html`: **NEW** Partial for battle card (HTMX updates)
- `app/templates/battles/_battle_queue.html`: **NEW** Partial for queue section (HTMX updates)

**Components:**
- Reuse: Status badges, filter chips from FRONTEND.md
- Reuse: Flash messages for reorder feedback

**CSS:**
- `app/static/css/battles.css`:
  - **MODIFY** Add drag handle styles
  - **MODIFY** Add locked/movable visual indicators

**JavaScript:**
- `app/static/js/battle-reorder.js`: **NEW** Sortable.js integration for drag-and-drop

### Database

**Migrations:**
- **NEW** `alembic/versions/YYYY_add_battle_sequence_order.py`:
  - Add `sequence_order` column to battles table (nullable integer)
  - Add index on `(category_id, sequence_order)` for ordering queries

### Tests

**New Test Files:**
- `tests/test_pool_sizing.py`: Test equal pool sizing algorithm
- `tests/test_tiebreak_integration.py`: End-to-end tiebreak auto-creation
- `tests/test_battle_reordering.py`: Battle queue reorder tests

**Updated Test Files:**
- `tests/test_tournament_calculations.py`: Update `calculate_pool_capacity()` tests
- `tests/test_battle_service.py`: Add interleaving tests
- `tests/test_pool_service.py`: Add tiebreak integration tests
- `tests/test_tiebreak_service.py`: Add auto-detection tests

### Documentation

**Level 1 (Source of Truth):**
- `DOMAIN_MODEL.md`:
  - Section: Pool Structure
  - Change: Document equal pool sizing rule (BR-POOL-001)
  - Change: Document tiebreak auto-creation triggers (BR-TIE-001, BR-TIE-002)

- `VALIDATION_RULES.md`:
  - Section: Tournament Calculations
  - Change: Replace 25% elimination rule with equal pool sizing formula
  - Change: Add battle queue ordering constraints

**Level 2 (Derived):**
- `ROADMAP.md`:
  - Phase: 3.2 - Tournament Organization Validation
  - Status: In Progress
  - Objectives: Fix pool sizing, auto-tiebreaks, battle interleaving
  - Deliverables: Bug fixes, integration, UI improvements

**Level 3 (Operational):**
- `ARCHITECTURE.md`:
  - Section: Service Layer Patterns
  - Add: Tiebreak integration pattern (trigger on battle completion)

- `FRONTEND.md`:
  - Section: HTMX Patterns
  - Add: Drag-and-drop reordering pattern with constraints

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:**
```sql
-- Migration: YYYY-MM-DD_add_battle_sequence_order
-- Add sequence_order column to battles table for queue ordering
ALTER TABLE battles ADD COLUMN sequence_order INTEGER;

-- Add index for efficient ordering queries
CREATE INDEX idx_battles_category_sequence ON battles(category_id, sequence_order);
```

**Data Migration:**
```python
# Set initial sequence_order based on created_at for existing battles
# This preserves existing order
UPDATE battles
SET sequence_order = (
    SELECT COUNT(*)
    FROM battles b2
    WHERE b2.category_id = battles.category_id
    AND b2.created_at <= battles.created_at
);
```

### 3.2 Fix Pool Sizing (BUG #1 and #2)

**Current (WRONG) Logic in `tournament_calculations.py:88`:**
```python
elimination_target = max(1, int(registered_performers * 0.25))
pool_performers = registered_performers - elimination_target
```

**New (CORRECT) Logic:**
```python
def calculate_pool_capacity(
    registered_performers: int,
    groups_ideal: int,
    performers_ideal: int,
) -> tuple[int, int, int]:
    """Calculate pool structure ensuring EQUAL pool sizes.

    Business Rule BR-POOL-001: All pools must have equal sizes.

    Args:
        registered_performers: Number of registered performers
        groups_ideal: Target number of pools (FIXED)
        performers_ideal: Target performers per pool (ADAPTIVE DOWN)

    Returns:
        Tuple of (pool_capacity, performers_per_pool, eliminated_count)
        - pool_capacity: Total performers qualifying for pools
        - performers_per_pool: Size of each pool (EQUAL)
        - eliminated_count: Performers eliminated in preselection

    Examples:
        >>> calculate_pool_capacity(9, 2, 4)
        (8, 4, 1)  # 9 registered, 8 capacity (2×4), 1 eliminated

        >>> calculate_pool_capacity(8, 2, 4)
        (6, 3, 2)  # 8 registered, must reduce to 2×3=6 to ensure elimination

        >>> calculate_pool_capacity(7, 2, 4)
        (6, 3, 1)  # 7 registered, 6 capacity (2×3), 1 eliminated
    """
    min_required = calculate_minimum_performers(groups_ideal)
    if registered_performers < min_required:
        raise ValueError(
            f"Need at least {min_required} performers for {groups_ideal} pools, "
            f"got {registered_performers}"
        )

    ideal_capacity = groups_ideal * performers_ideal

    # Case 1: More performers than ideal + 1 → use ideal capacity
    if registered_performers >= ideal_capacity + 1:
        eliminated = registered_performers - ideal_capacity
        return ideal_capacity, performers_ideal, eliminated

    # Case 2: Need to reduce pool size to ensure elimination
    # Find largest performers_per_pool where (groups × pool_size) < registered
    for pool_size in range(performers_ideal, 1, -1):  # Start from ideal, go down to 2
        capacity = groups_ideal * pool_size
        if capacity < registered_performers:
            eliminated = registered_performers - capacity
            return capacity, pool_size, eliminated

    # Fallback: minimum 2 per pool
    capacity = groups_ideal * 2
    eliminated = registered_performers - capacity
    return capacity, 2, eliminated
```

**Update `distribute_performers_to_pools()`:**
```python
def distribute_performers_to_pools(
    performer_count: int,
    groups_ideal: int,
) -> list[int]:
    """Calculate EQUAL distribution of performers across pools.

    Business Rule BR-POOL-001: All pools must have equal sizes.

    Args:
        performer_count: Number of performers to distribute
        groups_ideal: Number of pools

    Returns:
        List of pool sizes (all equal)

    Raises:
        ValueError: If performer_count not evenly divisible by groups_ideal

    Examples:
        >>> distribute_performers_to_pools(8, 2)
        [4, 4]  # Equal distribution ONLY

        >>> distribute_performers_to_pools(9, 2)
        # Should NOT be called with 9 - pool_capacity calculation
        # ensures this never happens
        ValueError: Cannot evenly distribute 9 performers into 2 pools
    """
    if performer_count % groups_ideal != 0:
        raise ValueError(
            f"Cannot evenly distribute {performer_count} performers "
            f"into {groups_ideal} pools (must be divisible)"
        )

    pool_size = performer_count // groups_ideal
    if pool_size < 2:
        raise ValueError(
            f"Need at least {groups_ideal * 2} performers for {groups_ideal} pools "
            f"(minimum 2 per pool), got {performer_count}"
        )

    return [pool_size] * groups_ideal
```

### 3.3 Tiebreak Auto-Detection Integration (GAP #1 and #2)

**New Method in `TiebreakService`:**
```python
async def detect_and_create_preselection_tiebreak(
    self, category_id: uuid.UUID
) -> Optional[Battle]:
    """Detect preselection ties and create tiebreak battle if needed.

    Called automatically when last preselection battle is completed.

    Business Rule BR-TIE-001: Tiebreak auto-created when last battle scored.
    Business Rule BR-TIE-003: ALL performers with boundary score compete.

    Args:
        category_id: Category UUID

    Returns:
        Created tiebreak battle or None if no tie
    """
    # Get pool capacity for this category
    category = await self.category_repo.get_by_id(category_id)
    performers = await self.performer_repo.get_by_category(category_id)

    pool_capacity, _, _ = calculate_pool_capacity(
        len(performers),
        category.groups_ideal,
        category.performers_ideal
    )

    # Detect ties at boundary
    tied_performers = await self.detect_preselection_ties(category_id, pool_capacity)

    if not tied_performers:
        return None

    # Calculate winners needed
    # Count performers with scores ABOVE the boundary score
    boundary_score = tied_performers[0].preselection_score
    performers_above = [
        p for p in performers
        if p.preselection_score > boundary_score
    ]
    spots_remaining = pool_capacity - len(performers_above)
    winners_needed = spots_remaining

    # Create tiebreak battle
    tiebreak = await self.create_tiebreak_battle(
        category_id,
        tied_performers,
        winners_needed
    )

    return tiebreak
```

**Integration in `BattleResultsEncodingService`:**
```python
async def encode_preselection_battle(
    self, battle_id: uuid.UUID, scores: Dict[uuid.UUID, Decimal]
) -> ValidationResult[Battle]:
    """Encode preselection battle and trigger tiebreak detection.

    After encoding, checks if this was the last preselection battle
    and triggers tiebreak detection if needed.
    """
    # ... existing encoding logic ...

    # After successful encoding, check if this was the last battle
    remaining_battles = await self.battle_repo.count_pending_by_category_and_phase(
        battle.category_id, BattlePhase.PRESELECTION
    )

    if remaining_battles == 0:
        # Last preselection battle completed - check for ties
        tiebreak = await self.tiebreak_service.detect_and_create_preselection_tiebreak(
            battle.category_id
        )
        if tiebreak:
            # Add info to result about tiebreak creation
            return ValidationResult.success(
                battle,
                warnings=[f"Tiebreak battle created for {len(tiebreak.performers)} tied performers"]
            )

    return ValidationResult.success(battle)
```

**Pool Winner Tiebreak Detection:**
```python
async def detect_and_create_pool_winner_tiebreak(
    self, pool_id: uuid.UUID
) -> Optional[Battle]:
    """Detect pool winner ties and create tiebreak battle if needed.

    Called when last pool battle is completed.

    Business Rule BR-TIE-002: Pool winner tiebreak auto-created.
    """
    pool = await self.pool_repo.get_by_id(pool_id)

    # Find performers with highest points
    max_points = max(p.pool_points for p in pool.performers)
    tied_performers = [p for p in pool.performers if p.pool_points == max_points]

    if len(tied_performers) == 1:
        # Clear winner, no tiebreak needed
        return None

    # Create tiebreak for pool winner
    tiebreak = await self.create_tiebreak_battle(
        pool.category_id,
        tied_performers,
        winners_needed=1  # Pool winner is exactly 1
    )

    return tiebreak
```

### 3.4 Battle Interleaving (GAP #3)

**New Method in `BattleService`:**
```python
async def generate_interleaved_preselection_battles(
    self, tournament_id: uuid.UUID
) -> List[Battle]:
    """Generate preselection battles interleaved across all categories.

    Business Rule BR-SCHED-001: Battle queue interleaved across categories.

    Args:
        tournament_id: Tournament UUID

    Returns:
        List of created battles in interleaved order
    """
    categories = await self.category_repo.get_by_tournament(tournament_id)

    # Generate battles for each category (not saved yet)
    category_battles: Dict[uuid.UUID, List[Battle]] = {}
    for category in categories:
        performers = await self.performer_repo.get_by_category(category.id)
        battles = self._create_preselection_battle_objects(category.id, performers)
        category_battles[category.id] = battles

    # Interleave across categories (round-robin)
    interleaved = []
    max_battles = max(len(b) for b in category_battles.values())

    for i in range(max_battles):
        for cat_id in category_battles:
            if i < len(category_battles[cat_id]):
                battle = category_battles[cat_id][i]
                battle.sequence_order = len(interleaved) + 1
                created = await self.battle_repo.create(battle)
                interleaved.append(created)

    return interleaved
```

### 3.5 Battle Queue Reordering

**New Method in `BattleService`:**
```python
async def reorder_battle(
    self, battle_id: uuid.UUID, new_position: int
) -> ValidationResult[Battle]:
    """Reorder a battle in the queue.

    Business Rule BR-SCHED-002: Only battles 2+ positions after ACTIVE can be moved.

    Args:
        battle_id: Battle to move
        new_position: Target position (1-indexed)

    Returns:
        ValidationResult with success/failure
    """
    battle = await self.battle_repo.get_by_id(battle_id)
    if not battle:
        return ValidationResult.failure(["Battle not found"])

    # Validate: Cannot move completed battles
    if battle.status == BattleStatus.COMPLETED:
        return ValidationResult.failure(["Completed battles cannot be moved"])

    # Validate: Cannot move active battle
    if battle.status == BattleStatus.ACTIVE:
        return ValidationResult.failure(["Active battle cannot be moved"])

    # Get all pending battles ordered
    pending_battles = await self.battle_repo.get_pending_battles_ordered(
        battle.category_id
    )

    # Find "on deck" battle (first pending)
    if pending_battles and pending_battles[0].id == battle_id:
        return ValidationResult.failure(["Next battle is locked and cannot be moved"])

    # Validate: Cannot move to locked positions (before "on deck")
    if new_position <= 1:
        return ValidationResult.failure(["Cannot move battle to a locked position"])

    # Perform reorder
    await self.battle_repo.update_sequence_order(battle_id, new_position)

    # Reindex other battles
    await self._reindex_battle_order(battle.category_id)

    return ValidationResult.success(battle)
```

**New Route:**
```python
@router.post("/{battle_id}/reorder")
async def reorder_battle(
    request: Request,
    battle_id: uuid.UUID,
    new_position: int = Form(...),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    battle_service: BattleService = Depends(get_battle_service),
):
    """Reorder a battle in the queue via drag-and-drop."""
    user = require_staff(current_user)

    result = await battle_service.reorder_battle(battle_id, new_position)

    if not result:
        for error in result.errors:
            add_flash_message(request, error, "error")
        return RedirectResponse(
            url=f"/battles?category_id={battle.category_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    add_flash_message(request, "Battle reordered successfully", "success")
    # Return partial HTML for HTMX
    return templates.TemplateResponse(
        request=request,
        name="battles/_battle_queue.html",
        context={"battles": await battle_service.get_battle_queue(battle.category_id)}
    )
```

---

## 4. Frontend Implementation Plan

### 4.1 Components to Reuse

**From FRONTEND.md Component Library:**
- Status badges (PENDING/ACTIVE/COMPLETED with correct colors)
- Filter chips for category/status filtering
- Flash messages for feedback
- Loading indicator for HTMX requests

### 4.2 New Components Needed

**Battle Queue with Reordering:**
```html
<!-- battles/_battle_queue.html -->
<div id="battle-queue"
     class="battle-queue"
     hx-get="/battles/queue?category_id={{ category_id }}"
     hx-trigger="every 5s"
     hx-swap="outerHTML">

    {% for battle in battles %}
    <article
        class="battle-card {% if battle.is_locked %}battle-locked{% endif %}"
        id="battle-{{ battle.id }}"
        data-battle-id="{{ battle.id }}"
        data-position="{{ loop.index }}"
        {% if not battle.is_locked %}
        draggable="true"
        {% endif %}
    >
        <!-- Drag handle (only for movable) -->
        {% if not battle.is_locked %}
        <div class="drag-handle" aria-label="Drag to reorder">
            <span aria-hidden="true">⋮⋮</span>
        </div>
        {% else %}
        <div class="lock-indicator" aria-label="Battle locked">
            <span aria-hidden="true">🔒</span>
        </div>
        {% endif %}

        <!-- Battle content -->
        <div class="battle-card-content">
            <!-- ... existing battle card content ... -->
        </div>
    </article>
    {% endfor %}
</div>
```

### 4.3 HTMX Patterns

**Battle Queue Auto-Refresh:**
```html
<div id="battle-queue"
     hx-get="/battles/queue?category_id={{ category_id }}"
     hx-trigger="every 5s"
     hx-swap="outerHTML"
     aria-live="polite">
```

**Reorder via Drag-and-Drop:**
```html
<form hx-post="/battles/{{ battle.id }}/reorder"
      hx-target="#battle-queue"
      hx-swap="outerHTML"
      hx-indicator=".loading">
    <input type="hidden" name="new_position" value="{{ new_position }}">
</form>
```

### 4.4 Accessibility Implementation

**Keyboard Navigation for Reordering:**
```html
<article
    class="battle-card"
    tabindex="0"
    role="listitem"
    aria-label="Battle {{ loop.index }}: {{ performers | join(' vs ') }}"
    aria-describedby="battle-{{ battle.id }}-status"
>
```

**Screen Reader Announcements:**
```html
<div id="reorder-status"
     role="status"
     aria-live="polite"
     class="sr-only">
    <!-- Populated by JavaScript on reorder -->
</div>
```

**Lock Indicator:**
```html
{% if battle.is_locked %}
<span class="lock-indicator"
      role="img"
      aria-label="Battle is locked (cannot be reordered)">
    🔒
</span>
{% endif %}
```

### 4.5 Responsive Strategy

**Mobile (320px-768px):**
- Stack battle cards vertically
- Swipe gestures for reordering (future enhancement)
- Larger touch targets for drag handles

**Tablet (769px-1024px):**
- 2-column grid for battle cards
- Drag handles visible on hover

**Desktop (1025px+):**
- 3-column grid for battle cards
- Full drag-and-drop functionality

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- Section: Pool Structure
- Add: Business Rule BR-POOL-001 (Equal Pool Sizes)
  ```
  All pools within a category MUST have the same number of performers.
  Pool capacity is calculated as `groups_ideal × performers_per_pool` where
  `performers_per_pool` is adaptive but EQUAL across all pools.
  ```

- Section: Tie-Breaking Logic
- Add: Business Rule BR-TIE-001 (Preselection Tiebreak Auto-Detection)
  ```
  When the last preselection battle is completed, the system automatically
  checks for ties at the qualification boundary and creates a tiebreak battle.
  ```

- Add: Business Rule BR-TIE-002 (Pool Winner Tiebreak Auto-Detection)
  ```
  When the last pool battle is completed, the system automatically checks
  for pool winner ties and creates a tiebreak battle.
  ```

**VALIDATION_RULES.md:**
- Section: Tournament Calculations
- Replace: 25% elimination rule with equal pool sizing formula
- Add: Pool sizing examples table (from feature spec)

### Level 2: Derived

**ROADMAP.md:**
- Phase: 3.2 - Tournament Organization Validation
- Status: In Progress → Complete
- Objectives:
  - Fix pool sizing bug (25% rule → equal pools)
  - Implement auto-tiebreak detection
  - Add battle queue interleaving
- Deliverables:
  - Fixed pool capacity calculation
  - Tiebreak integration into battle completion
  - Battle reordering UI

### Level 3: Operational

**ARCHITECTURE.md:**
- Section: Service Layer Patterns
- Add: Tiebreak Integration Pattern
  ```
  Tiebreak detection is triggered automatically by BattleResultsEncodingService
  when the last battle of a phase is completed. This ensures seamless integration
  without requiring manual intervention.
  ```

**FRONTEND.md:**
- Section: HTMX Patterns
- Add: Drag-and-Drop Reordering
  ```html
  <!-- Pattern: Sortable list with constraints -->
  <div class="sortable-list"
       data-sortable-handle=".drag-handle"
       data-sortable-filter=".battle-locked">
  ```

---

## 6. Testing Plan

### Unit Tests

**test_tournament_calculations.py:**
```python
# New tests for equal pool sizing
def test_calculate_pool_capacity_9_registered_2_pools_4_ideal():
    """9 registered, 2×4=8 ideal → 8 capacity, 1 eliminated."""
    capacity, per_pool, eliminated = calculate_pool_capacity(9, 2, 4)
    assert capacity == 8
    assert per_pool == 4
    assert eliminated == 1

def test_calculate_pool_capacity_8_registered_must_reduce():
    """8 registered = ideal, must reduce to ensure elimination."""
    capacity, per_pool, eliminated = calculate_pool_capacity(8, 2, 4)
    assert capacity == 6  # 2×3
    assert per_pool == 3
    assert eliminated == 2

def test_calculate_pool_capacity_7_registered():
    """7 registered, reduce to 2×3=6."""
    capacity, per_pool, eliminated = calculate_pool_capacity(7, 2, 4)
    assert capacity == 6
    assert per_pool == 3
    assert eliminated == 1

def test_distribute_performers_must_be_equal():
    """Pool sizes must be equal - uneven raises error."""
    with pytest.raises(ValueError, match="evenly distribute"):
        distribute_performers_to_pools(9, 2)  # 9/2 not even
```

**test_tiebreak_service.py:**
```python
# New integration tests
async def test_detect_and_create_preselection_tiebreak():
    """Auto-creates tiebreak when ties detected at boundary."""
    # Setup: 9 performers, 5 with same boundary score
    # ... create performers with scores ...

    tiebreak = await tiebreak_service.detect_and_create_preselection_tiebreak(
        category_id
    )

    assert tiebreak is not None
    assert len(tiebreak.performers) == 5  # All tied
    assert tiebreak.outcome["winners_needed"] == 4  # Fill spots 5-8

async def test_no_tiebreak_when_clear_cutoff():
    """No tiebreak created when clear score separation."""
    # Setup: Clear score separation at boundary

    tiebreak = await tiebreak_service.detect_and_create_preselection_tiebreak(
        category_id
    )

    assert tiebreak is None
```

**test_battle_service.py:**
```python
# New tests for interleaving
async def test_generate_interleaved_battles_two_categories():
    """Battles interleaved: H1, K1, H2, K2, H3, K3, H4, K4."""
    battles = await battle_service.generate_interleaved_preselection_battles(
        tournament_id
    )

    # Verify interleaving
    categories = [b.category_id for b in battles]
    assert categories[0] != categories[1]  # First two different
    assert categories[0] == categories[2]  # Every other same

async def test_reorder_battle_locked_positions():
    """Cannot reorder completed, active, or on-deck battles."""
    # Setup: COMPLETED, ACTIVE, PENDING (on deck), PENDING (movable)

    # Try to reorder completed
    result = await battle_service.reorder_battle(completed_id, 5)
    assert not result
    assert "Completed battles cannot be moved" in result.errors

    # Try to reorder active
    result = await battle_service.reorder_battle(active_id, 5)
    assert not result
    assert "Active battle cannot be moved" in result.errors

    # Try to reorder on-deck
    result = await battle_service.reorder_battle(on_deck_id, 5)
    assert not result
    assert "Next battle is locked" in result.errors
```

### Integration Tests

**test_tiebreak_integration.py:**
```python
async def test_full_preselection_flow_with_tiebreak():
    """End-to-end: preselection → tiebreak auto-created → resolved."""
    # 1. Create tournament with 9 performers
    # 2. Advance to PRESELECTION
    # 3. Complete all preselection battles with tie at boundary
    # 4. Verify tiebreak battle auto-created
    # 5. Complete tiebreak battle
    # 6. Verify phase can advance to POOLS
```

### Accessibility Tests

**Manual Testing Checklist:**
- [ ] Keyboard navigation through battle queue
- [ ] Tab to drag handles, Enter/Space to activate
- [ ] Escape to cancel drag operation
- [ ] Screen reader announces battle position
- [ ] Screen reader announces locked status
- [ ] ARIA live region announces reorder results
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 UI)
- [ ] Focus indicators visible during drag

### Responsive Tests

**Manual Testing Checklist:**
- [ ] Mobile (320px): Cards stack, touch targets 44px+
- [ ] Tablet (769px): 2-column grid, drag handles visible
- [ ] Desktop (1025px): 3-column grid, full drag-and-drop

---

## 7. Risk Analysis

### Risk 1: Pool Sizing Change Breaks Existing Data
**Concern:** Existing tournaments may have pools created with old 25% rule
**Likelihood:** Low (Phase 3.1 not yet in production with data)
**Impact:** High (data inconsistency)
**Mitigation:**
- Add migration to recalculate existing pool data
- Add validation to prevent phase advancement with uneven pools
- Document breaking change in release notes

### Risk 2: Tiebreak Auto-Creation Race Conditions
**Concern:** Two concurrent battle completions might both trigger tiebreak detection
**Likelihood:** Medium (battle completion is user-triggered)
**Impact:** Medium (duplicate tiebreak battles)
**Mitigation:**
- Use database transaction with row-level locking
- Check if tiebreak already exists before creating
- Add unique constraint on (category_id, phase=TIEBREAK, status!=COMPLETED)

### Risk 3: Battle Reordering During Active Tournament
**Concern:** Reordering battles might confuse judges/staff
**Likelihood:** Medium (feature purpose is reordering)
**Impact:** Low (visual confusion only)
**Mitigation:**
- Only allow reordering PENDING battles (not active/completed)
- Lock "on deck" battle from reordering
- Add flash message confirming reorder
- Add visual indicator for locked battles

### Risk 4: HTMX Polling Performance
**Concern:** 5-second polling on battle queue might overwhelm server
**Likelihood:** Low (small user base, ~50 dancers)
**Impact:** Low (Railway can handle)
**Mitigation:**
- Use `hx-trigger="every 5s"` with conditional stop
- Stop polling when no active tournament
- Add ETag/If-None-Match for unchanged responses

### Risk 5: Drag-and-Drop Accessibility
**Concern:** Keyboard-only users cannot reorder battles
**Likelihood:** High (drag-and-drop is mouse-centric)
**Impact:** Medium (accessibility violation)
**Mitigation:**
- Add keyboard shortcuts (Arrow keys + Enter)
- Add "Move Up/Down" buttons as alternative
- Announce changes via ARIA live region

---

## 8. Implementation Order

**Recommended sequence to minimize risk:**

1. **Database Migration** (Foundation)
   - Create migration for `sequence_order` column
   - Test upgrade/downgrade
   - Deploy to dev

2. **Pool Sizing Fix** (Critical Bug #1 and #2)
   - Update `calculate_pool_capacity()`
   - Update `distribute_performers_to_pools()`
   - Write comprehensive tests
   - Verify no existing data affected

3. **Tiebreak Integration** (Critical Gap #1 and #2)
   - Add `detect_and_create_preselection_tiebreak()`
   - Add `detect_and_create_pool_winner_tiebreak()`
   - Integrate into `BattleResultsEncodingService`
   - Write integration tests

4. **Battle Interleaving** (Gap #3)
   - Add `generate_interleaved_preselection_battles()`
   - Update `_execute_phase_transition_hooks()`
   - Write interleaving tests

5. **Documentation** (Before Frontend)
   - Update DOMAIN_MODEL.md
   - Update VALIDATION_RULES.md
   - Update ROADMAP.md

6. **Battle Reordering Backend** (New Feature)
   - Add `reorder_battle()` service method
   - Add `/battles/{id}/reorder` route
   - Write reordering tests

7. **Frontend UI** (Polish)
   - Update battle list template
   - Add drag-and-drop JavaScript
   - Add HTMX patterns
   - Test in browser

8. **Accessibility** (Quality Gate)
   - Add ARIA attributes
   - Test keyboard navigation
   - Test screen reader
   - Verify color contrast

9. **Responsive Testing** (Final Polish)
   - Test mobile layout
   - Test tablet layout
   - Test desktop layout

---

## 9. Open Questions

- [x] Should pool capacity be based on `performers_ideal` from category config? → **Yes, use category's `performers_ideal` as target**
- [x] Should filter state persist in URL? → **Yes, use URL params for shareability**
- [x] What happens if a tiebreak is created but tournament phase is advanced before completion? → **Phase validation blocks advancement if pending tiebreak exists**
- [ ] Should staff be able to manually create tiebreak battles? → **Defer to user feedback**
- [ ] Should we add drag-and-drop fallback for mobile? → **Future enhancement, not in initial implementation**

---

## 10. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
- [ ] User confirmed open questions resolved

---

## Appendix: Pool Sizing Examples

| Registered | Ideal (2×4) | Pool Capacity | Eliminated | Pool Sizes |
|------------|-------------|---------------|------------|------------|
| 12         | 8           | 8             | 4          | [4, 4]     |
| 10         | 8           | 8             | 2          | [4, 4]     |
| 9          | 8           | 8             | 1          | [4, 4]     |
| 8          | 8           | 6             | 2          | [3, 3]     |
| 7          | 8           | 6             | 1          | [3, 3]     |
| 6          | 8           | 4             | 2          | [2, 2]     |
| 5          | 8           | 4             | 1          | [2, 2]     |

**Note:** When registered equals ideal capacity, we MUST reduce pool size to ensure at least 1 elimination (preselection is mandatory).

---

**End of Implementation Plan**
