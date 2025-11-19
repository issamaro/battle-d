# Battle-D Domain Model

## Overview

Battle-D is a dance battle tournament management system designed for a single organization hosting multiple tournaments per year. The system manages the complete lifecycle of tournaments from registration through preselection, pools, finals, and champion declaration.

**Key Characteristics:**
- **Single Organization**: Not multi-tenant, internal tool for one dance organization
- **~50 Dancers**: Small, manageable pool of performers
- **Multiple Tournaments/Year**: Reusable dancer pool across tournaments
- **Sequential Battles**: One battle active at a time
- **Hardcoded Phases**: Always 5 phases in fixed order
- **No Dancer Logins**: Dancers are managed by staff, no user accounts for performers

---

## Fundamental Principle

### **Separation of Users and Dancers**

According to the functional specifications: *"Dancers and spectators do not have user accounts in the application"*

**Two Distinct Concepts:**

1. **System Users** (with login): Admin, Staff, MC, Judge
   - Have email + password (magic links)
   - Access the application
   - Perform management tasks

2. **Dancers** (without login): Performers
   - Managed by staff
   - Registered in tournaments
   - No application access
   - Just participants

---

## Entities

### **User** (System Accounts Only)

Represents people who access the application.

**Attributes:**
- `id`: UUID
- `email`: string (unique, required)
- `first_name`: string (required)
- `role`: Enum (admin | staff | mc | judge)

**Roles:**
- **admin**: Full access, can advance tournament phases, create users
- **staff**: Can manage dancers, tournaments, encode battle results
- **mc**: Read-only access for ceremony hosting
- **judge**: Scoring access (V2 only, with restricted permissions)

**No `blaze` field** - Users are not performers.

---

### **Dancer** (Performers, No Login)

Represents dancers/performers managed by staff.

**Attributes:**
- `id`: UUID
- `email`: string (unique, required) - Contact email
- `first_name`: string (required)
- `last_name`: string (required)
- `date_of_birth`: Date (required)
- `blaze`: string (required) - Stage name
- `country`: string (optional)
- `city`: string (optional)

**Characteristics:**
- **Reusable across tournaments**: Same dancer can participate in multiple tournaments
- **No login credentials**: Dancers don't access the application
- **Unique email**: One email = one dancer
- **Stage name (blaze)**: Primary identifier in battles

---

### **Performer** (Dancer in Tournament Context)

Links a Dancer to a specific Tournament + Category. Represents tournament-specific participation.

**Attributes:**
- `id`: UUID
- `tournament_id`: FK → Tournament
- `category_id`: FK → Category
- `dancer_id`: FK → Dancer
- `duo_partner_id`: FK → Performer (nullable, for 2v2 categories)
- `preselection_score`: Decimal (nullable, set during preselection)
- `pool_wins`: int (default 0)
- `pool_draws`: int (default 0)
- `pool_losses`: int (default 0)

**Computed Property:**
- `pool_points`: int = `(pool_wins × 3) + (pool_draws × 1)`

**Constraints:**
- `UNIQUE(dancer_id, tournament_id)`: One dancer = one category per tournament

---

### **Tournament**

Represents a competition event.

**Attributes:**
- `id`: UUID
- `name`: string
- `status`: Enum (active | completed)
- `phase`: Enum (registration | preselection | pools | finals | completed)
- `created_at`: DateTime
- `categories`: List[Category]

**Phase Management:**
- **Global phase**: All categories progress together
- **Hardcoded sequence**: Always 5 phases in fixed order
- **Cannot skip phases**: Must progress sequentially

---

### **Category** (1v1 or 2v2)

Represents a competition category within a tournament (e.g., "Hip Hop Boys 1v1", "Krump Duo 2v2").

**Attributes:**
- `id`: UUID
- `tournament_id`: FK → Tournament
- `name`: string
- `is_duo`: boolean (false = 1v1, true = 2v2)
- `groups_ideal`: int (default 2, number of pools)
- `performers_ideal`: int (default 4, target performers per pool)
- `performers`: List[Performer]

**Configuration:**
- `groups_ideal`: How many pools (typically 2)
- `performers_ideal`: Target size per pool (used for capacity calculations)

---

### **Battle**

Represents a single competition bout between performers.

**Attributes:**
- `id`: UUID
- `category_id`: FK → Category
- `phase`: Enum (preselection | pools | tiebreak | finals)
- `status`: Enum (pending | active | completed)
- `performers`: ManyToMany[Performer]
- `outcome_type`: Enum (scored | win_draw_loss | tiebreak | win_loss)
- `winner_id`: FK → Performer (nullable)
- `outcome`: JSON (structure depends on outcome_type)

**Outcome Types:**

1. **ScoredOutcome** (Preselection):
   ```json
   {
     "performer_id_1": 7.83,
     "performer_id_2": 8.45,
     "performer_id_3": 6.92
   }
   ```

2. **WinDrawLossOutcome** (Pools):
   ```json
   {
     "winner_id": "performer_uuid",
     "is_draw": false
   }
   ```

3. **TiebreakOutcome** (Tiebreaks):
   ```json
   {
     "n_participants": 3,
     "p_winners_needed": 1,
     "judge_votes": {
       "judge_1_round_1": "performer_id_to_eliminate",
       "judge_2_round_1": "performer_id_to_eliminate",
       ...
     },
     "winner_ids": ["performer_uuid"]
   }
   ```

4. **WinLossOutcome** (Finals):
   ```json
   {
     "winner_id": "performer_uuid"
   }
   ```

**Constraints:**
- Only one battle with `status='active'` globally at any time

---

### **Pool**

Represents a group in the pool phase where performers compete round-robin.

**Attributes:**
- `id`: UUID
- `category_id`: FK → Category
- `name`: string (e.g., "Pool A", "Pool B")
- `performers`: ManyToMany[Performer]
- `battles`: List[Battle]
- `winner_id`: FK → Performer (nullable, determined after all pool battles)

**Pool Structure:**
- All performers in pool compete against each other (round-robin)
- Winner has highest `pool_points`
- Ties resolved via tiebreak battles

---

### **Judge** (V2 Only)

Represents a judge account for direct scoring (not in Phase 0/V1).

**Attributes:**
- `id`: UUID
- `user_id`: FK → User (Judge is a temporary User)
- `tournament_id`: FK → Tournament (Judge specific to tournament)
- `deleted_at`: DateTime (nullable, soft delete after tournament)

**V2 Workflow:**
- Admin creates User with `role='judge'`
- Judge gets magic link, accesses scoring interface
- After tournament, judge account soft-deleted

---

## Business Rules

### **1. Hardcoded Tournament Phases**

**Sequence (Always the Same):**
```
Registration → Preselection → Pools → Finals → Completed
```

**Characteristics:**
- **5 phases always present**: Cannot be skipped or reordered
- **Global phase**: Applies to entire tournament, not per category
- **All categories progress together**: When tournament advances to Pools, ALL categories go to Pools
- **Sequential**: Must complete current phase before advancing

**Phase Purposes:**
- **Registration**: Staff registers dancers in categories
- **Preselection**: Elimination battles to narrow down to pool capacity
- **Pools**: Round-robin battles in groups
- **Finals**: Championship battles between pool winners
- **Completed**: Tournament finished, champions declared

---

### **2. Preselection MANDATORY** ⚠️ Key Change

**New Rule (vs CLI):** Preselection **ALWAYS** happens, regardless of registration count.

**Principle:**
```
registered_performers (rp) > pool_performers (pp)
```
- Preselection **must eliminate** at least some performers
- Pool size adapts to ensure preselection occurs

**Examples:**

| Registered (rp) | Groups | Pool Performers (pp) | Pool Structure | Eliminated |
|-----------------|--------|---------------------|----------------|------------|
| 8 | 2 | 6 | 2 pools of 3 | 2 |
| 10 | 2 | 8 | 2 pools of 4 | 2 |
| 12 | 2 | 10 | 2 pools of 5 | 2 |
| 16 | 2 | 12-14 | 2 pools of 6-7 | 2-4 |
| 20 | 2 | 16 | 2 pools of 8 | 4 |

**Rationale:**
- Ensures preselection phase always has purpose
- Creates competitive elimination phase
- Keeps tournament interesting even with exact capacity registrations

**Constraint:**
- **Minimum (groups_ideal × 2) + 2 registered performers** required to start tournament
  - Example: groups_ideal=2 → minimum 6 performers (NOT 4!)
  - Formula: `(groups_ideal * 2) + 2` ensures minimum 2 per pool + 2 for elimination
- Pool sizes adapt dynamically based on registrations

**Adaptation Logic:**
- System calculates optimal `pp` where `pp < rp`
- Typically eliminates ~20-25% of registered performers
- Ensures balanced pool sizes (equal or differ by max 1)
- Minimum 2 performers per pool

---

### **3. Preselection Scoring**

**Battle Format:**
- **Mostly 1v1**: Dancers paired randomly
- **3-way if odd**: Last battle has 3 performers if odd number registered

**Judging:**
- **3 judges** (configurable, default 3)
- Each judge scores **0-10** per performer
- **Independent scoring**: Judges don't see each other's scores

**Score Calculation:**
- **Average** of all judge scores per performer
- Rounded to **2 decimal places**
- Example: Judge 1=7.5, Judge 2=8.0, Judge 3=7.0 → Average = 7.50

**Qualification:**
- Performers sorted by **descending** preselection score
- **Top `pp`** performers advance to pools
- If tied at boundary → **Tiebreak battle** (see section 5)

---

### **4. Pool Phase**

**Structure:**
- Number of pools = `groups_ideal` (typically 2)
- Performers per pool = calculated dynamically (see Preselection rule)
- **Round-robin**: Every performer battles every other performer in their pool

**Scoring:**
- **Win** = 3 points
- **Draw** = 1 point
- **Loss** = 0 points
- `pool_points = (wins × 3) + (draws × 1)`

**Winner Determination:**
- Performer with **highest pool_points** wins the pool
- If tied at top → **Tiebreak battle** (see section 5)

**Pool Winners:**
- Exactly 1 winner per pool
- Pool winners advance to Finals

---

### **5. Tie-Breaking Logic** ⚠️ Critical

Tie-breaking occurs in two scenarios:

#### **Scenario A: Tie in Preselection Qualification**

**Situation:**
- N performers have the same preselection score at the qualification boundary
- P spots available in pools
- **Constraint:** P < N

**Example:**
```
Pool capacity = 8 performers
Performers at ranks 7, 8, 9 all have score = 7.50
Need to select 2 out of 3 → Tiebreak battle
```

**Resolution:**
- Create **Tiebreak Battle** with N tied performers
- Battle outcome determines which P performers advance

---

#### **Scenario B: Tie for Pool Winner**

**Situation:**
- Multiple performers have the same (highest) pool_points
- Need exactly 1 winner per pool

**Example:**
```
Pool A:
- Performer 1: 9 points (3 wins)
- Performer 2: 9 points (3 wins)
- Performer 3: 6 points
→ Tiebreak battle between Performers 1 and 2
```

**Resolution:**
- Create **Tiebreak Battle** with N tied performers
- P = 1 (need 1 winner)

---

#### **Tiebreak Battle Algorithm**

**Input:**
- N participants (tied performers)
- P winners needed
- Constraint: **P < N**

**Judging Process:**

**If N = 2** (2 tied performers):
- Judges vote for who to **KEEP**
- Each judge selects one performer to advance
- **Majority vote** determines winner
- Example: 3 judges, 2 vote for Performer A → A advances

**If N > 2** (more than 2 tied):
- **Iterative elimination**
- Each round, judges vote for who to **ELIMINATE**
- Each judge selects one performer to eliminate
- **Majority vote** → that performer is eliminated
- **Repeat** until exactly P performers remain

**Example (N=3, P=1):**
```
Round 1:
- 3 performers: A, B, C
- Judges vote to eliminate:
  - Judge 1: eliminate C
  - Judge 2: eliminate C
  - Judge 3: eliminate B
- Majority: C eliminated
- Remaining: A, B

Round 2:
- 2 performers: A, B
- Switch to KEEP voting (N=2 rule)
- Judges vote:
  - Judge 1: keep A
  - Judge 2: keep A
  - Judge 3: keep B
- Majority: A wins
```

**Termination:**
- Process continues until exactly P winners remain
- Winners advance (either to pools or to finals)

**Vote Storage:**
- All judge votes stored in battle outcome
- Format: `{"judge_{id}_round_{round}": "performer_id"}`
- Ensures transparency and audit trail

---

### **6. Finals Phase**

**Structure:**
- **Pool winners only**: 1 winner per pool advances
- **Direct battles**: Pool A winner vs Pool B winner (if 2 pools)
- If more than 2 pools: bracket system (not yet defined)

**Battle Format:**
- **1v1 battle**
- **No draws allowed in finals**
- Outcome: **Win/Loss** only

**Champion:**
- Finals winner = Tournament Category Champion
- Declared when tournament phase = Completed

---

### **7. Constraints and Validations**

**Database Constraints:**

```sql
-- Email uniqueness
CONSTRAINT unique_user_email UNIQUE(User.email)
CONSTRAINT unique_dancer_email UNIQUE(Dancer.email)

-- One dancer per category per tournament
CONSTRAINT unique_dancer_tournament UNIQUE(Performer.dancer_id, Performer.tournament_id)

-- One active battle globally
CHECK (
  SELECT COUNT(*) FROM Battle WHERE status = 'active'
) <= 1
```

**Business Validations:**

1. **Minimum Performers:**
   - Minimum `(groups_ideal × 2) + 2` registered performers required to start tournament
   - Example: groups_ideal=2 → minimum 6 performers
   - Minimum 2 performers per pool after distribution

2. **Phase Transitions:**
   - Can only advance to next phase in sequence
   - Cannot skip phases
   - All categories must be ready before advancing

3. **Battle Creation:**
   - Only one battle can have `status='active'` at a time
   - Battles must be completed before starting next battle

4. **Duo Pairing:**
   - If `category.is_duo = true`, performers must have `duo_partner_id` set
   - Partners must be in same category

5. **Judge Count:**
   - Minimum 1 judge (default 3)
   - Odd number preferred for majority voting

---

## Workflows

### **Workflow 1: Admin Creates System User**

```
Admin → Interface → Create User
  ├─ Email (required)
  ├─ First Name (required)
  └─ Role (admin|staff|mc|judge)

→ System sends magic link to email
→ User clicks link → Logged in
```

---

### **Workflow 2: Staff Creates Dancer**

```
Staff → Interface → Create Dancer
  ├─ Email (required, unique)
  ├─ First Name (required)
  ├─ Last Name (required)
  ├─ Date of Birth (required)
  ├─ Blaze / Stage Name (required)
  ├─ Country (optional)
  └─ City (optional)

→ Dancer saved in database
→ Dancer reusable across tournaments
→ No login credentials (dancer doesn't access app)
```

---

### **Workflow 3: Staff Registers Dancer in Tournament**

```
Staff → Select Tournament + Category
     → Search Dancer (by blaze, name, or email)
     → Select Dancer
     → Create Performer record
       ├─ dancer_id → Selected dancer
       ├─ tournament_id → Current tournament
       ├─ category_id → Selected category
       └─ duo_partner_id (if 2v2 category)

→ Performer created (dancer now registered)
→ Validation: Check if dancer already in another category this tournament
```

---

### **Workflow 4: Tournament Phase Progression**

```
1. Registration Phase:
   - Staff registers dancers in categories
   - Admin checks if minimum (groups_ideal × 2 + 2) performers per category
   - When ready → Admin clicks "Advance Phase"

2. Preselection Phase (ALWAYS triggered):
   - System calculates pool structure (pp < rp)
   - System creates preselection battles (1v1, 3-way if odd)
   - Admin/Staff starts each battle sequentially
   - Judges score 0-10 per performer (or staff manually encodes)
   - System calculates average scores
   - If tie at boundary → Tiebreak battle created automatically
   - Top pp performers qualify for pools
   - When all battles complete → Admin advances phase

3. Pools Phase:
   - System creates pools (groups_ideal pools)
   - System distributes qualified performers
   - System creates round-robin battles per pool
   - Admin/Staff runs battles sequentially
   - System calculates pool_points per performer
   - If tie at top of pool → Tiebreak battle created automatically
   - System determines 1 winner per pool
   - When all pools complete → Admin advances phase

4. Finals Phase:
   - System creates finals battle (pool winners)
   - Admin/Staff runs finals battle
   - No draws allowed (Win/Loss only)
   - Winner = Category Champion
   - Admin advances phase

5. Completed Phase:
   - Tournament finished
   - Champions declared
   - Results visible on projection screen
```

---

### **Workflow 5: Tiebreak Battle Resolution**

```
Detected Tie (preselection or pool winner):
  ├─ N performers with same score/points
  └─ P spots/winners needed (P < N)

→ System creates Tiebreak Battle
  ├─ phase = 'tiebreak'
  ├─ performers = tied performers
  └─ outcome_type = 'tiebreak'

→ Admin starts tiebreak battle

→ Judging process:
  If N=2:
    - Each judge votes for who to KEEP
    - Majority determines winner

  If N>2:
    - Round 1: Each judge votes who to ELIMINATE
    - Majority eliminated
    - Remaining N-1 performers
    - If N-1 > P: Repeat round
    - If N-1 = 2: Switch to KEEP voting
    - Continue until exactly P winners

→ System records all judge votes

→ Battle completed with P winners

→ Winners advance to next phase
```

---

## CLI to Web Migration

Mapping from existing CLI (`classes.py`) to Web App:

| CLI Entity | Web Entity | Changes |
|------------|------------|---------|
| `User(name, blaze)` | `Dancer(first_name, last_name, blaze, email, dob, country, city)` | Renamed, enriched fields |
| N/A | `User(email, first_name, role)` | New: system accounts |
| `Performer(user)` | `Performer(dancer_id)` | References Dancer, not User |
| `Tournament` | `Tournament` | Added `phase` enum |
| `Category` | `Category` | Same structure |
| `Battle` | `Battle` | Added `status` field |
| `Pool` | `Pool` | Same structure |
| N/A | `Judge` | New (V2 only) |

**Key Differences:**

1. **Dancer ≠ User**: Dancers don't log in, managed by staff
2. **Preselection Always Mandatory**: CLI was conditional, web is always triggered
3. **Adaptive Pool Sizes**: Web calculates dynamic pool structure
4. **Automatic Tiebreak Creation**: CLI had TODOs, web implements fully
5. **Enriched Dancer Profile**: Added email, DOB, country, city

---

## Summary

Battle-D manages dance tournaments with a clear separation between:
- **System Users** (staff who manage the system)
- **Dancers** (performers who participate in tournaments)

Key innovations in the web version:
- **Mandatory preselection** with adaptive pool sizing
- **Complete tie-breaking** logic automatically triggered
- **Rich dancer profiles** for better management
- **Sequential battle execution** (one at a time)
- **Global tournament phases** (all categories together)

The system ensures fair, transparent, and well-documented tournaments from registration through champion declaration.
