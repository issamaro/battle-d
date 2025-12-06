# Battle-D Validation Rules
**Level 1: Source of Truth** | Last Updated: 2025-12-06

This document specifies all validation rules for the Battle-D tournament management system, particularly focusing on phase transitions and tournament constraints.

## Table of Contents
- [Tournament Status Lifecycle](#tournament-status-lifecycle)
- [Performer Registration Validation](#performer-registration-validation)
- [Phase Transition Validation](#phase-transition-validation)
- [Tournament Calculations](#tournament-calculations)
- [Duo Registration Validation](#duo-registration-validation)
- [Battle Encoding Validation](#battle-encoding-validation)

---

## Tournament Status Lifecycle

**Status Enum:** `TournamentStatus(created | active | cancelled | completed)`

**Lifecycle Flow:**
```
CREATED → ACTIVE → COMPLETED (normal flow)
       ↘       ↓
         CANCELLED (admin intervention)
```

### Status Definitions

**CREATED:**
- Initial status when tournament is created
- Tournament setup in progress (adding categories, configuring settings)
- Not yet open for competition
- Multiple tournaments can be in CREATED status simultaneously
- Valid phase: REGISTRATION only

**ACTIVE:**
- Tournament is running and open for competition
- **Only one tournament can be ACTIVE at a time** (enforced constraint)
- Automatic activation occurs when advancing from REGISTRATION phase if validation passes
- Cannot manually activate if another tournament is already ACTIVE
- Valid phases: PRESELECTION, POOLS, FINALS

**CANCELLED:**
- Tournament was active but stopped before natural completion
- Set when admin deactivates in-progress tournaments (phases: PRESELECTION, POOLS, FINALS)
- Cannot advance phases from this status (terminal state for abandoned tournaments)
- Used for data integrity fixes when multiple ACTIVE tournaments detected
- Valid phases: PRESELECTION, POOLS, FINALS (any in-progress phase)

**COMPLETED:**
- Tournament has finished all phases normally
- Final results are locked
- Automatic completion when advancing from FINALS phase
- Valid phase: COMPLETED only

### Activation Rules

**Auto-Activation on Phase Advancement:**
When advancing from REGISTRATION → PRESELECTION:
1. Tournament must be in CREATED status
2. Validation must pass (minimum performers, categories configured)
3. No other tournament can be ACTIVE
4. If all checks pass: tournament automatically transitions CREATED → ACTIVE

**Implementation:**
```python
# In TournamentService.advance_tournament_phase()
if tournament.status == TournamentStatus.CREATED and tournament.phase == TournamentPhase.REGISTRATION:
    active_tournament = await tournament_repo.get_active()
    if active_tournament and active_tournament.id != tournament.id:
        raise ValidationError(["Cannot activate: another tournament is already active"])

    tournament.activate()  # CREATED → ACTIVE
```

**Constraint Enforcement:**
- Attempting to activate when another tournament is ACTIVE raises `ValidationError`
- Complete or deactivate the active tournament before activating a new one

---

## Performer Registration Validation

### Minimum Performer Requirements

**Formula:** `minimum_performers = (groups_ideal × 2) + 1`

**Rationale:**
- Ensures minimum 2 performers per pool group
- Guarantees at least 1 performer is eliminated in preselection
- Prevents tournaments with insufficient competition

**Examples:**
| groups_ideal | Calculation | Minimum Required |
|--------------|-------------|------------------|
| 1            | (1 × 2) + 1 | 3                |
| 2            | (2 × 2) + 1 | 5                |
| 3            | (3 × 2) + 1 | 7                |
| 4            | (4 × 2) + 1 | 9                |

**Implementation:**
```python
from app.utils.tournament_calculations import calculate_minimum_performers

minimum = calculate_minimum_performers(groups_ideal=2)
# Returns: 5
```

### One Dancer Per Tournament Rule

**Rule:** Each dancer can only register in ONE category per tournament.

**Validation:**
- Check `performers` table for existing `(dancer_id, tournament_id)` combination
- Enforced by database unique constraint: `uq_dancer_tournament`

**Error Message:**
```
"Dancer {blaze} is already registered in this tournament (one category per tournament)"
```

### Ideal Pool Capacity

**Formula:** `ideal_pool_capacity = groups_ideal × performers_ideal`

**Purpose:**
- Target number of performers after preselection
- Determines how many performers advance from preselection to pools

**Example:**
- groups_ideal = 2
- performers_ideal = 4
- ideal_pool_capacity = 2 × 4 = 8 performers

---

## Phase Transition Validation

### Phase Sequence

Tournaments must progress through phases in strict order:

```
REGISTRATION → PRESELECTION → POOLS → FINALS → COMPLETED
```

**Rules:**
1. Cannot skip phases
2. Cannot go backwards (except admin override)
3. Must satisfy validation for each transition

### Phase 1: REGISTRATION → PRESELECTION

**Validation Rules:**

1. **Minimum Performers Met:**
   ```python
   for category in tournament.categories:
       performer_count = count_performers(category_id)
       minimum_required = (category.groups_ideal * 2) + 1

       if performer_count < minimum_required:
           errors.append(f"Category {category.name}: needs {minimum_required - performer_count} more performers")
   ```

2. **All Categories Have Performers:**
   - At least one performer in each category
   - Empty categories should be deleted before advancing

**Error Example:**
```
Cannot advance to PRESELECTION phase:
- Category "Hip Hop Boys 1v1": needs 2 more performers (has 4, needs 6)
- Category "Breaking Girls 2v2": needs 3 more performers (has 5, needs 8)
```

### Phase 2: PRESELECTION → POOLS

**Validation Rules:**

1. **All Preselection Battles Complete:**
   ```python
   pending_battles = count_battles(
       category_id=category.id,
       battle_type="preselection",
       status="pending"
   )

   if pending_battles > 0:
       errors.append(f"Category {category.name}: {pending_battles} preselection battles incomplete")
   ```

2. **Preselection Scores Assigned:**
   - All performers must have `preselection_score` set
   - Scores used to determine top performers advancing to pools

3. **Pool Structure Calculated:**
   - Top `ideal_pool_capacity` performers selected
   - Pool assignments created based on distribution algorithm

**Automatic Actions:**
- System creates pool assignments
- Calculates which performers advance

### Phase 3: POOLS → FINALS

**Validation Rules:**

1. **All Pool Battles Complete:**
   ```python
   pending_battles = count_battles(
       category_id=category.id,
       battle_type="pool",
       status="pending"
   )
   ```

2. **Pool Points Calculated:**
   - Each performer has wins/draws/losses recorded
   - Pool points formula: `(wins × 3) + (draws × 1) + (losses × 0)`

3. **Pool Winners Determined:**
   - Winner from each pool identified
   - Ties resolved (tiebreaker rules apply)

**Automatic Actions:**
- Create finals bracket with pool winners
- Seed bracket based on pool performance

### Phase 4: FINALS → COMPLETED

**Validation Rules:**

1. **All Finals Battles Complete:**
   - Championship match complete
   - Winner determined

2. **Final Rankings Calculated:**
   - Champion, runner-up, and other placements determined

**Automatic Actions:**
- Mark tournament as completed
- Lock all data from further modification
- Generate final results report

---

## Tournament Calculations

### Pool Capacity Calculation (BR-POOL-001)

**Business Rule:** All pools within a category MUST have EQUAL sizes. Pool sizes never differ.

**Algorithm:** `calculate_pool_capacity(registered_performers, groups_ideal, performers_ideal)`

**Logic:**
1. Calculate `ideal_capacity = groups_ideal × performers_ideal`
2. If `registered_performers >= ideal_capacity + 1`: use ideal capacity
3. Otherwise: reduce `performers_per_pool` until `capacity < registered_performers`
4. This ensures at least 1 performer is eliminated (preselection is mandatory)

**Implementation:**
```python
def calculate_pool_capacity(
    registered_performers: int,
    groups_ideal: int,
    performers_ideal: int,
) -> tuple[int, int, int]:
    """Calculate pool structure ensuring EQUAL pool sizes.

    Returns:
        Tuple of (pool_capacity, performers_per_pool, eliminated_count)
    """
    ideal_capacity = groups_ideal * performers_ideal

    # Case 1: More performers than ideal + 1 → use ideal capacity
    if registered_performers >= ideal_capacity + 1:
        eliminated = registered_performers - ideal_capacity
        return ideal_capacity, performers_ideal, eliminated

    # Case 2: Need to reduce pool size to ensure elimination
    for pool_size in range(performers_ideal, 1, -1):
        capacity = groups_ideal * pool_size
        if capacity < registered_performers:
            eliminated = registered_performers - capacity
            return capacity, pool_size, eliminated

    # Fallback: minimum 2 per pool
    capacity = groups_ideal * 2
    eliminated = registered_performers - capacity
    return capacity, 2, eliminated
```

**Examples (groups_ideal=2, performers_ideal=4):**

| Registered | Ideal (2×4) | Pool Capacity | Eliminated | Pool Sizes |
|------------|-------------|---------------|------------|------------|
| 12         | 8           | 8             | 4          | [4, 4]     |
| 10         | 8           | 8             | 2          | [4, 4]     |
| 9          | 8           | 8             | 1          | [4, 4]     |
| 8          | 8           | 6             | 2          | [3, 3]     |
| 7          | 8           | 6             | 1          | [3, 3]     |
| 6          | 8           | 4             | 2          | [2, 2]     |
| 5          | 8           | 4             | 1          | [2, 2]     |

**Key Change from Previous Version:**
- OLD (INCORRECT): 25% elimination rule that allowed unequal pool sizes like [5, 4]
- NEW (CORRECT): Equal pool sizes always, pool size reduces to ensure elimination

### Pool Size Distribution

**Algorithm:** `distribute_performers_to_pools(pool_capacity, groups_ideal)`

**Rules:**
1. Pool capacity MUST be evenly divisible by groups_ideal
2. All pools have exactly the same size
3. Minimum 2 performers per pool

**Implementation:**
```python
def distribute_performers_to_pools(pool_capacity: int, groups_ideal: int) -> list[int]:
    """Distribute performers EQUALLY across pools.

    Raises ValueError if not evenly divisible.
    """
    if pool_capacity % groups_ideal != 0:
        raise ValueError(
            f"Cannot evenly distribute {pool_capacity} performers into {groups_ideal} pools"
        )

    pool_size = pool_capacity // groups_ideal
    return [pool_size] * groups_ideal
```

**Examples:**

| Pool Capacity | Pools | Distribution | Notes |
|---------------|-------|--------------|-------|
| 8             | 2     | [4, 4]       | Equal |
| 6             | 2     | [3, 3]       | Equal |
| 4             | 2     | [2, 2]       | Equal |
| 9             | 2     | ERROR        | Not evenly divisible |

**Note:** The `calculate_pool_capacity()` function ensures pool capacity is always evenly divisible by groups_ideal.

### Preselection Elimination Count

**Formula:**
```python
pool_capacity, _, eliminated_count = calculate_pool_capacity(
    registered_performers, groups_ideal, performers_ideal
)
```

**Constraint:** Must eliminate at least 1 performer (preselection is mandatory)

**Validation:**
```python
if eliminated_count < 1:
    raise ValueError("Preselection must eliminate at least 1 performer")
```

---

## Battle Queue Ordering

### Battle Interleaving (BR-SCHED-001)

**Rule:** When generating preselection battles for a tournament with multiple categories, battles are interleaved across categories in round-robin fashion.

**Example with 2 categories (Hip Hop with 4 battles, Krump with 3 battles):**
| Sequence | Category | Battle |
|----------|----------|--------|
| 1        | Hip Hop  | #1     |
| 2        | Krump    | #1     |
| 3        | Hip Hop  | #2     |
| 4        | Krump    | #2     |
| 5        | Hip Hop  | #3     |
| 6        | Krump    | #3     |
| 7        | Hip Hop  | #4     |

**Rationale:** Keeps audience engaged with variety; gives performers rest between battles.

### Battle Reordering Constraints (BR-SCHED-002)

**Rule:** Staff can reorder pending battles with the following restrictions:

| Battle Status | Can Move? | Reason |
|---------------|-----------|--------|
| COMPLETED     | No        | Already finished, historical record |
| ACTIVE        | No        | Currently in progress |
| First PENDING | No        | "On deck" - locked for preparation |
| Other PENDING | Yes       | Can be reordered freely |

**Validation:**
```python
async def reorder_battle(battle_id: UUID, new_position: int) -> ValidationResult:
    battle = await battle_repo.get_by_id(battle_id)

    if battle.status == BattleStatus.COMPLETED:
        return ValidationResult.failure(["Completed battles cannot be moved"])

    if battle.status == BattleStatus.ACTIVE:
        return ValidationResult.failure(["Active battle cannot be moved"])

    pending_battles = await battle_repo.get_pending_ordered(battle.category_id)
    if pending_battles and pending_battles[0].id == battle_id:
        return ValidationResult.failure(["Next battle is locked and cannot be moved"])

    if new_position < 2:
        return ValidationResult.failure(["Cannot move battle to a locked position"])

    return ValidationResult.success(battle)
```

**UI Indicators:**
- Locked battles show lock icon
- Movable battles show drag handle
- Completed battles greyed out

---

## UI Field Validation

### Field Length Requirements

| Field | Min Length | Max Length | Notes |
|-------|------------|------------|-------|
| Tournament Name | 1 char | 100 chars | Required, unique |
| Tournament Description | 0 char | 500 chars | Optional |
| Blaze Name | 1 char | 50 chars | Required, unique |
| Real Name | 1 char | 100 chars | Required |
| Email | Valid format | 255 chars | Required, RFC 5322 format |
| Category Name | 1 char | 50 chars | Required, unique per tournament |

### Pool Configuration Limits

| Setting | Min | Max | Notes |
|---------|-----|-----|-------|
| Pools per Category | 2 | 10 | Minimum 2 required for finals |
| Performers per Pool | 2 | - | Auto-distributed evenly |

**Pool Distribution:** Pool sizes must differ by at most 1 (automatically balanced by system).

### Magic Link Authentication

| Setting | Value | Notes |
|---------|-------|-------|
| Link Expiration | 5 minutes | From time of generation |
| Cooldown | 30 seconds | Between requests for same email |
| Rate Limit | 5 per 15 minutes | Per email address |

### Deletion Rules

| Entity | Can Delete When | Cannot Delete When |
|--------|-----------------|-------------------|
| Dancer | No active tournament registrations | Has registrations in active tournaments |
| User | Anytime | - |
| Tournament | Status = CREATED | Status = ACTIVE or COMPLETED |
| Category | No performers registered | Has performers registered |

---

## Duo Registration Validation

### 2v2 Category Rules

**Validation for Duo Registration:**

1. **Two Different Dancers:**
   ```python
   if dancer1_id == dancer2_id:
       raise ValueError("Cannot register the same dancer twice in a duo")
   ```

2. **Both Dancers Available:**
   - Neither dancer registered in this tournament yet
   - Check `uq_dancer_tournament` constraint for each

3. **Category is Duo Type:**
   ```python
   if not category.is_duo:
       raise ValueError("This category is not a duo category")
   ```

4. **Partner Linking:**
   - Both performers registered with `duo_partner_id` set
   - Mutual linking: performer1.duo_partner_id = performer2.id

**Database Constraint:**
```sql
-- Both performers reference each other
performer1.duo_partner_id = performer2.id
performer2.duo_partner_id = performer1.id
```

### Unregistering from Duo

**Current Implementation:**
- Unregistering one partner does NOT automatically unregister the other
- System allows orphaned duo partners
- **Future Enhancement:** Cascade unregister both partners

---

## Battle Encoding Validation

### Overview

Battle encoding is the process of recording battle results (outcomes) into the system. Different battle phases have different encoding requirements and validation rules. All validation must occur before persisting outcome data to prevent invalid states.

### Battle Status Requirements

**Encoding Preconditions:**
- Battle must exist and be loaded with performers
- Battle status must be `ACTIVE` (cannot encode pending or completed battles)
- User must have staff role

**Status Transitions:**
```
PENDING → (start battle) → ACTIVE → (encode result) → COMPLETED
```

**Validation Error Example:**
```python
if battle.status != BattleStatus.ACTIVE:
    raise ValidationError(["Cannot encode battle: status must be ACTIVE"])
```

---

### Preselection Battle Encoding

**Phase:** `PRESELECTION`

**Outcome Format:** JSON scores mapping performer IDs to decimal scores
```json
{
  "uuid-performer-1": 8.5,
  "uuid-performer-2": 7.0,
  "uuid-performer-3": 9.0
}
```

**Validation Rules:**

1. **All Performers Must Be Scored**
   ```python
   for performer in battle.performers:
       if str(performer.id) not in scores:
           errors.append(f"Missing score for {performer.dancer.blaze}")
   ```

2. **Score Range: 0.0 - 10.0**
   ```python
   for performer_id, score in scores.items():
       if not (0.0 <= score <= 10.0):
           errors.append(f"Score {score} out of range (must be 0.0-10.0)")
   ```

3. **Score Precision: 2 decimal places**
   ```python
   score = Decimal(str(score)).quantize(Decimal('0.01'))
   ```

4. **Performer Stats Update**
   - Set `performer.preselection_score = score` for each performer
   - Used for ranking performers to advance to pools

**Implementation Location:** `app/services/battle_results_encoding_service.py::encode_preselection_results()`

---

### Pool Battle Encoding

**Phase:** `POOL`

**Outcome Types:**
- **Win:** One performer wins (winner_id set, is_draw = false)
- **Draw:** No winner (winner_id = null, is_draw = true)

**Outcome Format:** JSON with winner or draw flag
```json
{
  "winner_id": "uuid-performer-1",
  "is_draw": false
}
```

**Validation Rules:**

1. **Winner OR Draw (Mutually Exclusive)**
   ```python
   if is_draw and winner_id:
       raise ValidationError(["Cannot specify winner and draw simultaneously"])
   if not is_draw and not winner_id:
       raise ValidationError(["Must specify winner or mark as draw"])
   ```

2. **Winner Must Be Battle Participant**
   ```python
   if winner_id:
       performer_ids = {p.id for p in battle.performers}
       if winner_id not in performer_ids:
           raise ValidationError(["Winner must be a battle participant"])
   ```

3. **Pool Points Update**
   - **Winner:** +3 points, increment wins
   - **Loser:** +0 points, increment losses
   - **Draw:** +1 point each, increment draws

**Implementation Location:** `app/services/battle_results_encoding_service.py::encode_pool_results()`

---

### Tiebreak Battle Encoding

**Phase:** `TIEBREAK`

**Outcome Type:** Winner required (no draws allowed in tiebreaks)

**Outcome Format:** JSON with winner ID
```json
{
  "winner_id": "uuid-performer-1"
}
```

**Validation Rules:**

1. **Winner Required**
   ```python
   if not winner_id:
       raise ValidationError(["Tiebreak battles must have a winner"])
   ```

2. **No Draw Allowed**
   ```python
   if is_draw:
       raise ValidationError(["Draws are not allowed in tiebreak battles"])
   ```

3. **Winner Must Be Battle Participant**
   - Same validation as pool battles

**Implementation Location:** `app/services/battle_results_encoding_service.py::encode_tiebreak_results()`

---

### Finals Battle Encoding

**Phase:** `FINALS`

**Outcome Type:** Winner required (tournament champion)

**Outcome Format:** JSON with winner ID
```json
{
  "winner_id": "uuid-performer-1"
}
```

**Validation Rules:**

1. **Winner Required**
   ```python
   if not winner_id:
       raise ValidationError(["Finals battle must have a winner"])
   ```

2. **Winner Must Be Battle Participant**
   - Same validation as pool/tiebreak battles

3. **Championship Status**
   - Winner becomes category champion
   - Marks end of category competition

**Implementation Location:** `app/services/battle_results_encoding_service.py::encode_finals_results()`

---

### Transaction Requirements

**All encoding operations must be atomic:**

```python
async def encode_battle(battle_id: UUID, outcome: dict) -> ValidationResult[Battle]:
    async with session.begin():  # Start transaction
        # 1. Validate outcome data
        validation_errors = validate_outcome(battle, outcome)
        if validation_errors:
            return ValidationResult.failure(validation_errors)

        # 2. Update battle.outcome
        battle.outcome = outcome
        battle.status = BattleStatus.COMPLETED

        # 3. Update performer stats (preselection_score, pool_points, etc.)
        update_performer_stats(battle, outcome)

        # 4. Commit or rollback (automatic)
        return ValidationResult.success(battle)
```

**Rationale:**
- Prevents partial updates if encoding fails mid-operation
- Ensures battle and performer stats remain consistent
- Allows rollback on validation errors

---

### Error Handling

**Validation Error Format:**
```python
ValidationResult.failure([
    "Missing score for B-Boy John",
    "Score 11.5 out of range (must be 0.0-10.0)",
    "Winner must be a battle participant"
])
```

**User Feedback:**
- Flash message with all validation errors
- Form data preserved (HTMX partial update)
- Field-level error indicators (aria-invalid)

**Example Error Messages:**
```
✗ Missing score for B-Boy Sarah
✗ Score 11.0 out of range (must be 0.0-10.0)
✗ Must specify winner or mark as draw
✗ Tiebreak battles must have a winner (no draws allowed)
```

---

## Error Messages

### Standard Error Format

**Registration Errors:**
```
✗ Category "Hip Hop Boys 1v1": Dancer B-Boy John is already registered in this tournament
✗ Category "Breaking Duo 2v2": Cannot register the same dancer twice in a duo
```

**Phase Transition Errors:**
```
Cannot advance to PRESELECTION phase:

Errors:
• Category "Hip Hop Boys 1v1": needs 1 more performer (has 4, needs 5)
• Category "Breaking Girls 1v1": has minimum performers (5)

Warnings:
• Category "Krump Open": has exactly minimum performers (5) - consider getting more
```

**Battle Status Errors:**
```
Cannot advance to POOLS phase:

• Category "Hip Hop Boys 1v1": 3 preselection battles incomplete
• Category "Breaking Duo 2v2": 1 preselection battle incomplete
```

---

## Implementation Reference

### Key Files

- **Validation Logic:** `app/services/phase_service.py`
- **Battle Encoding:** `app/services/battle_results_encoding_service.py`
- **Battle Validators:** `app/validators/battle_validators.py`
- **Calculations:** `app/utils/tournament_calculations.py`
- **Database Constraints:** `app/models/performer.py`
- **Phase Router:** `app/routers/phases.py`
- **Battle Router:** `app/routers/battles.py`

### Test Coverage

All validation rules are tested in:
- `tests/test_tournament_calculations.py` - Formula correctness
- `tests/test_models.py` - Database constraints
- `tests/test_crud_workflows.py` - Integration workflows
- `tests/test_battle_results_encoding_service.py` - Battle encoding validation (preselection, pool, tiebreak, finals)
- `tests/test_battle_routes.py` - Battle routing and encoding integration

---

## Version History

- **2025-01-19:** Initial documentation of validation rules
- **2025-01-19:** Corrected minimum performer formula (was 4, now formula-based)
- **2025-11-19:** Updated minimum formula from `(groups_ideal × 2) + 2` to `(groups_ideal × 2) + 1` (minimum 1 elimination instead of 2)
- **2025-11-19:** Added tournament status lifecycle documentation (CREATED → ACTIVE → COMPLETED)
- **2025-11-19:** Removed percentage references from documentation
- **2025-12-04:** Added Battle Encoding Validation section (preselection, pool, tiebreak, finals)
- **2025-12-04:** Added transaction requirements and error handling documentation
- **2025-12-04:** Updated implementation reference with battle encoding files
- **2025-12-06:** Replaced pool sizing algorithm (25% rule → equal pool sizes BR-POOL-001)
- **2025-12-06:** Added battle queue ordering rules (BR-SCHED-001, BR-SCHED-002)
