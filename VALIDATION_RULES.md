# Battle-D Validation Rules

This document specifies all validation rules for the Battle-D tournament management system, particularly focusing on phase transitions and tournament constraints.

## Table of Contents
- [Performer Registration Validation](#performer-registration-validation)
- [Phase Transition Validation](#phase-transition-validation)
- [Tournament Calculations](#tournament-calculations)
- [Duo Registration Validation](#duo-registration-validation)

---

## Performer Registration Validation

### Minimum Performer Requirements

**Formula:** `minimum_performers = (groups_ideal × 2) + 2`

**Rationale:**
- Ensures minimum 2 performers per pool group
- Guarantees at least 2 performers are eliminated in preselection
- Prevents tournaments with insufficient competition

**Examples:**
| groups_ideal | Calculation | Minimum Required |
|--------------|-------------|------------------|
| 1            | (1 × 2) + 2 | 4                |
| 2            | (2 × 2) + 2 | 6                |
| 3            | (3 × 2) + 2 | 8                |
| 4            | (4 × 2) + 2 | 10               |

**Implementation:**
```python
from app.utils.tournament_calculations import calculate_minimum_performers

minimum = calculate_minimum_performers(groups_ideal=2)
# Returns: 6
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
REGISTRATION → PRESELECTION → POOLS → FINALS → ARCHIVED
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
       minimum_required = (category.groups_ideal * 2) + 2

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

### Phase 4: FINALS → ARCHIVED

**Validation Rules:**

1. **All Finals Battles Complete:**
   - Championship match complete
   - Winner determined

2. **Final Rankings Calculated:**
   - Champion, runner-up, and other placements determined

**Automatic Actions:**
- Mark tournament as archived
- Lock all data from further modification
- Generate final results report

---

## Tournament Calculations

### Pool Size Distribution

**Algorithm:** `distribute_performers_to_pools(num_performers, groups_ideal)`

**Rules:**
1. Minimum 2 performers per pool
2. Pool sizes must differ by at most 1
3. Total performers must equal input

**Examples:**

| Performers | Pools | Distribution | Algorithm |
|------------|-------|--------------|-----------|
| 8          | 2     | [4, 4]       | Even      |
| 9          | 2     | [5, 4]       | +1 to first |
| 10         | 3     | [4, 3, 3]    | +1 to first |
| 11         | 3     | [4, 4, 3]    | +1 to first two |

**Implementation:**
```python
from app.utils.tournament_calculations import distribute_performers_to_pools

distribution = distribute_performers_to_pools(num_performers=9, groups_ideal=2)
# Returns: [5, 4]
```

### Preselection Elimination Count

**Formula:**
```python
elimination_count = registered_performers - ideal_pool_capacity
```

**Constraint:** Must eliminate at least 2 performers

**Validation:**
```python
if registered_performers <= ideal_pool_capacity:
    raise ValueError("Need more performers than pool capacity for elimination")

elimination_count = registered_performers - ideal_pool_capacity
if elimination_count < 2:
    raise ValueError("Must eliminate at least 2 performers in preselection")
```

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
• Category "Hip Hop Boys 1v1": needs 2 more performers (has 4, needs 6)
• Category "Breaking Girls 1v1": needs 1 more performer (has 5, needs 6)

Warnings:
• Category "Krump Open": has exactly minimum performers (6) - consider getting more
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
- **Calculations:** `app/utils/tournament_calculations.py`
- **Database Constraints:** `app/models/performer.py`
- **Phase Router:** `app/routers/phases.py`

### Test Coverage

All validation rules are tested in:
- `tests/test_tournament_calculations.py` - Formula correctness
- `tests/test_models.py` - Database constraints
- `tests/test_crud_workflows.py` - Integration workflows

---

## Version History

- **2025-01-19:** Initial documentation of validation rules
- **2025-01-19:** Corrected minimum performer formula (was 4, now formula-based)
