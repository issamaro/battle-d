# Phase 4: Projection Interface - Documentation Plan
**Created:** 2025-11-30
**Status:** Planning Phase - Documentation Before Implementation

---

## Executive Summary

This plan details how to create **complete functional documentation** for Phase 4: Projection Interface before any implementation begins. The goal is to produce clear, unambiguous specifications that resolve user questions and prevent scope creep.

### User Decisions Confirmed
- **Battle Display:** Simplified V1 (no rounds, no judges display) - Option A
- **URL Structure:** `/projection` (auto-select active tournament)
- **Scope Exclusions:** Rounds data, judge status, avatars, sponsor slides
- **Keep:** Tournament progression visualization (rename "bracket")

### Questions to Resolve Through Documentation
1. Battle state lifecycle (is "PENDING" the "to come" state?)
2. Empty state UX (no battles, tournament not started, etc.)
3. Display mode logic (what is "intelligent display"?)
4. Terminology ("standing" vs "leaderboard", "bracket" rename)
5. Multi-category handling (cycling through categories)
6. Testing strategy for public endpoints

---

## Code Investigation Findings

### Battle Status Enum (CONFIRMED)
```python
class BattleStatus(str, enum.Enum):
    PENDING = "pending"      # User's "to come" state
    ACTIVE = "active"        # Currently happening
    COMPLETED = "completed"  # Finished
```

**Answer to Question 1:** YES, PENDING is the "to come" state. Projection should display as "Coming Up" or "Upcoming".

### Tournament Status (CONFIRMED)
```python
class TournamentStatus(str, enum.Enum):
    CREATED = "created"      # Setup only
    ACTIVE = "active"        # Tournament running
    COMPLETED = "completed"  # Tournament finished
```

**Projection Behavior:**
- CREATED: Not shown (tournament not started)
- ACTIVE: Auto-selected for `/projection`
- COMPLETED: Show final results

### Tournament Phase (CONFIRMED)
```python
class TournamentPhase(str, enum.Enum):
    REGISTRATION = "registration"
    PRESELECTION = "preselection"
    POOLS = "pools"
    FINALS = "finals"
```

**Note:** There is NO "completed" phase - that's a tournament STATUS, not a phase.

---

## PHASE 1: TERMINOLOGY CLARIFICATION (Day 1, Session 1)

### Objective
Create a glossary of projection-specific terms to eliminate ambiguity before writing specs.

### Deliverable: `docs/PHASE_4_TERMINOLOGY.md`

**Content Structure:**

#### Core Concepts

**Projection Display**
- Public-facing display screen
- No authentication required
- Optimized for large format (projectors, TVs)
- Auto-refreshing content
- Max 5 concurrent viewers

**Tournament Progression View** (Replace "bracket")
OPTIONS TO EXPLORE:
- "Tournament Tree"
- "Finals Matchup View"  
- "Championship Progression"
- "Finals Overview"
- RECOMMENDATION: [TBD based on user feedback]

**Standings vs Leaderboard**
CURRENT UNDERSTANDING:
- "Standings" = pool rankings (W-D-L records, points)
- "Leaderboard" = public display version of standings
- QUESTION: Are these the same thing or different views?

**Battle Queue**
- List of pending battles
- Currently active battle
- Recently completed battles

**Display Mode**
- Different views (battle, standings, queue, progression)
- How system switches between modes
- Manual vs automatic transitions

#### Battle State Terminology

**Battle Status for Projection:**
- PENDING → Display as "Coming Up" or "Upcoming"
- ACTIVE → Display as "Now Playing" or "Live"
- COMPLETED → Display as "Finished" or "Recent"

**Tournament Status for Projection:**
- CREATED: Not shown (setup only)
- ACTIVE: Auto-selected for display
- COMPLETED: Show final results

#### Data Concepts

**Pool Standings Data**
WHAT IS A "STANDING"?
- Technical: Row showing performer rank, W-D-L, points, status
- User-facing: "Pool Rankings" or "Pool Leaderboard"
- Data includes:
  - Rank within pool
  - Performer blaze (stage name)
  - Wins-Draws-Losses record
  - Pool points (wins × 3 + draws × 1)
  - Advancement status (advancing vs eliminated)

**Battle Result Summary**
- Winner blaze (stage name)
- Pool/phase context
- Battle number
- Timestamp

### Validation Tasks
- [ ] User reviews terminology document
- [ ] User confirms or corrects each definition
- [ ] User selects preferred term for "bracket" replacement
- [ ] User clarifies "standings" vs "leaderboard"
- [ ] Add approved terms to `GLOSSARY.md`

---

## PHASE 2: BATTLE STATE INVESTIGATION (Day 1, Session 1)

### Objective
Document complete battle lifecycle as it applies to projection display.

### Code Investigation Complete

**Files Examined:**
- ✅ `/app/models/battle.py` - Battle status enum (PENDING/ACTIVE/COMPLETED)
- ✅ `/app/models/tournament.py` - Tournament status/phase enums
- ⏳ `/app/services/battle_service.py` - Battle state transitions (need to examine)
- ⏳ `/app/repositories/battle.py` - Battle queries (need to examine)

**Investigation Questions:**
- [x] What are the exact enum values? (PENDING, ACTIVE, COMPLETED)
- [ ] When does PENDING → ACTIVE transition occur?
- [ ] When does ACTIVE → COMPLETED transition occur?
- [ ] How to query "next pending battle"?
- [ ] How to query "current active battle"?
- [ ] How to query "recently completed battles"?

### Deliverable: `docs/PHASE_4_BATTLE_LIFECYCLE.md`

**Content Structure:**

#### Battle Status Enum
```python
class BattleStatus(str, enum.Enum):
    PENDING = "pending"      # Not yet started
    ACTIVE = "active"        # Currently happening
    COMPLETED = "completed"  # Finished
```

#### State Transitions

**PENDING → ACTIVE**
- **Trigger:** [Document from code investigation]
- **Who:** Staff/Admin clicks "Start Battle"
- **Data Available:** Battle ID, performers, category, phase
- **Projection Impact:** Battle moves from queue to "Now Playing"

**ACTIVE → COMPLETED**
- **Trigger:** [Document from code investigation]
- **Who:** Staff/Admin encodes battle result
- **Data Available:** Winner, outcome, all battle details
- **Projection Impact:** Battle moves to "Recent Results", next battle activates

#### Data Available by State

**PENDING Battles:**
- Battle ID
- Performers (IDs, blazes)
- Category name
- Phase (preselection/pools/tiebreak/finals)
- Pool name (if applicable)
- Battle number/order
- NOT available: Winner, score, timing

**ACTIVE Battles:**
- All PENDING data plus status = "active"
- NOT available in V1: Real-time judge scores, round-by-round data

**COMPLETED Battles:**
- All ACTIVE data plus winner ID, outcome, timestamp

#### Query Patterns for Projection

```python
# Get Active Tournament
active_tournament = await tournament_repo.get_active()

# Get Current Battle
active_battle = await battle_repo.get_active_battle()

# Get Next Pending Battles
pending_battles = await battle_repo.filter_battles(
    status=BattleStatus.PENDING,
    limit=5
)

# Get Recent Completed Battles
recent_battles = await battle_repo.filter_battles(
    status=BattleStatus.COMPLETED,
    order_by="completed_at DESC",
    limit=3
)
```

#### Edge Cases

1. **No Active Battle:** Tournament in REGISTRATION phase
2. **No Pending Battles:** Tournament completed
3. **Battle Stuck in ACTIVE:** Manual intervention needed
4. **Multiple Categories:** How to show battles from different categories?

### Validation Tasks
- [ ] Verify state transitions from code
- [ ] Confirm data availability in each state
- [ ] Test edge cases in current system
- [ ] Document any gaps or assumptions

---

## PHASE 3: DISPLAY COMPONENTS SPECIFICATION (Day 1, Session 2)

### Objective
Revise UI_MOCKUPS Section 13 to match V1 scope and clarify each display component.

### 3.1 Revise Section 13.1: Battle View

**Changes from Original UI_MOCKUPS:**
- ❌ Remove: Judge scoring indicators ("Judge #1 ✓")
- ❌ Remove: Round-by-round display ("Round 4 of 5")
- ❌ Remove: Avatars/photos (no placeholders)
- ✅ Keep: Performer names (blazes)
- ✅ Keep: Current battle context (category, pool)
- ✅ Keep: Auto-refresh via HTMX

**New V1 Battle View Spec:**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│       HIP HOP 1V1 • POOL A • BATTLE #12     │
├─────────────────────────────────────────────┤
│                                             │
│   ┌─────────────┐       ┌─────────────┐    │
│   │  B-BOY      │       │   CRAZY     │    │
│   │  STORM      │  VS   │   LEGS      │    │
│   └─────────────┘       └─────────────┘    │
│                                             │
│            NOW PLAYING                      │
│                                             │
│   Next Up: Battle #13 • Phoenix vs Thunder │
│                                             │
└─────────────────────────────────────────────┘
```

**States to Document:**
1. **Battle Active:** Shows current battle
2. **Between Battles:** Shows "Next up" preview
3. **No Active Battle:** [Define message]
4. **Tournament Not Started:** [Define message]
5. **Tournament Complete:** [Define message]

### 3.2 Revise Section 13.2: Standings View

**Clarification Needed:**
- What is "standings"? → Pool rankings table
- What data to show? → Rank, Blaze, W-D-L, Points, Status
- Multi-pool handling? → Cycle through pools? Show all?

**Questions for User:**
- Should standings show advancement indicators?
- How to handle multiple categories?
- Auto-cycle interval if multiple pools?

**New V1 Standings Spec:**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│        HIP HOP 1V1 • POOL A STANDINGS       │
├─────────────────────────────────────────────┤
│                                             │
│ RANK │ PERFORMER   │ W-D-L │ PTS │ STATUS  │
│══════════════════════════════════════════════│
│  1   │ B-Boy Storm │ 4-0-0 │ 12  │ ✓ ADV   │
│  2   │ Phoenix     │ 3-0-1 │  9  │ ✓ ADV   │
│──────────────────────────────────────────────│
│  3   │ Thunder     │ 2-0-2 │  6  │         │
│  4   │ Crazy Legs  │ 1-0-3 │  3  │         │
│  5   │ Lightning   │ 0-0-4 │  0  │         │
│                                             │
│     Last Updated: 14:45                     │
│                                             │
└─────────────────────────────────────────────┘
```

**States to Document:**
1. **Pools Active:** Show current standings
2. **No Pool Data:** [Define when this happens]
3. **Multiple Pools:** [Define cycling behavior]
4. **Pools Complete:** Show final standings

### 3.3 Revise Section 13.3: Queue View

**Clarification Needed:**
- What defines "queue"? → List of pending battles
- How many to show? → Current + next + 5 pending?
- Real-time updates? → Yes, HTMX every 10s

**New V1 Queue Spec:**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│          UPCOMING BATTLES QUEUE             │
├─────────────────────────────────────────────┤
│                                             │
│ 🔴 NOW PLAYING                              │
│ Battle #12 • Hip Hop 1v1 • Pool A          │
│ B-Boy Storm vs Crazy Legs                  │
│                                             │
│ ⏳ UP NEXT                                  │
│ Battle #13 • Hip Hop 1v1 • Pool A          │
│ Phoenix vs Thunder                          │
│                                             │
│ UPCOMING:                                   │
│ #14 │ Storm vs Phoenix    │ HH 1v1 │ Pool A│
│ #15 │ Thunder vs Legs     │ HH 1v1 │ Pool A│
│ #16 │ Lightning vs Storm  │ HH 1v1 │ Pool A│
│                                             │
│          Last Updated: 14:47                │
│                                             │
└─────────────────────────────────────────────┘
```

**States to Document:**
1. **Battles Queued:** Show list
2. **No Active Battle:** Show next up
3. **No Pending Battles:** "All battles complete"
4. **Multiple Categories:** [How to handle?]

### 3.4 Revise Section 13.4: Progression View

**Rename "bracket" to:** [User selects from terminology doc]

**Clarification Needed:**
- Finals only or all phases?
- 2-pool scenario: 2 winners → 1 finals battle
- Show completed path or just structure?

**New V1 Progression Spec (2-pool scenario):**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│       HIP HOP 1V1 • FINALS PROGRESSION      │
├─────────────────────────────────────────────┤
│                                             │
│   POOL WINNERS        FINALS      CHAMPION  │
│                                             │
│   ┌──────────┐                              │
│   │ Pool A   │                              │
│   │ B-Boy    │────┐                         │
│   │ Storm    │    │   ┌──────────┐          │
│   └──────────┘    ├───│  TBD     │          │
│                   │   └──────────┘          │
│   ┌──────────┐    │                         │
│   │ Pool B   │    │                         │
│   │ Phoenix  │────┘                         │
│   └──────────┘                              │
│                                             │
│     Finals Battle: Pending                  │
│                                             │
└─────────────────────────────────────────────┘
```

**States to Document:**
1. **Pools Not Complete:** Show "TBD" for winners
2. **Winners Determined:** Show names
3. **Finals Active:** Highlight current battle
4. **Champion Crowned:** Show winner prominently

### Deliverable
Updated `UI_MOCKUPS.md` Section 13 with:
- [ ] 13.1 Battle View (V1 simplified)
- [ ] 13.2 Standings (clarified terminology)
- [ ] 13.3 Queue (defined structure)
- [ ] 13.4 Progression (renamed, simplified)
- [ ] V1 badges on all sections
- [ ] "Future V2 Enhancements" subsection

---

## PHASE 4: UX FLOW DOCUMENTATION (Day 2, Session 1)

### Objective
Define user experience flows for projection display, including intelligent display logic and empty states.

### Deliverable: `docs/PHASE_4_UX_FLOWS.md`

#### 4.1 Intelligent Display Logic

**User Question:** "What determines which view shows when?"

**Proposed Algorithm:**

```
When user navigates to /projection:

1. Check active tournament exists
   → If NO: Show "No active tournament" message
   → If YES: Continue to step 2

2. Check current tournament phase
   → REGISTRATION: Show "Tournament not started" + stats
   → PRESELECTION/POOLS/FINALS: Continue to step 3

3. Check for active battle
   → If YES: Show Battle View
   → If NO: Continue to step 4

4. Check for pending battles
   → If YES: Show Queue View
   → If NO: Continue to step 5

5. Check tournament status
   → ACTIVE + FINALS complete: Show Progression View with champion
   → ACTIVE: Show Standings View
   → COMPLETED: Show final results
```

**Auto-Transition Rules:**

**While displaying Battle View:**
- Battle completes → Switch to Standings View for 15s → Return to Queue View
- No state change → Stay on Battle View

**While displaying Queue View:**
- Battle starts → Switch to Battle View immediately
- No battles pending → Switch to Standings View

**While displaying Standings View:**
- New battle starts → Switch to Battle View
- After 30s idle → Switch to Queue View (if pending battles exist)
- After 30s idle → Stay on Standings (if no pending battles)

**While displaying Progression View:**
- During FINALS phase only
- Auto-refresh as battles complete
- Champion crowned → Persistent display

#### 4.2 Empty State Handling

**User Question:** "What UX for empty scenarios?"

**Scenario 1: No Active Tournament**
```
┌─────────────────────────────────────────────┐
│          🏆 BATTLE-D PROJECTION             │
│                                             │
│       No active tournament                  │
│                                             │
│   Check back when tournament begins!        │
└─────────────────────────────────────────────┘
```

**Scenario 2: Tournament in REGISTRATION Phase**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│                                             │
│       Registration Open                     │
│                                             │
│   Hip Hop 1v1: 12 registered                │
│   Breaking 2v2: 8 teams registered          │
│                                             │
│   Battles begin soon!                       │
└─────────────────────────────────────────────┘
```

**Scenario 3: No Active Battle (Mid-Tournament)**
- Show Queue View with "Next Up" battle
- No empty state needed

**Scenario 4: No Pending Battles**
- Show Standings View for current phase

**Scenario 5: Tournament Complete**
```
┌─────────────────────────────────────────────┐
│          SUMMER BATTLE 2024                 │
│                                             │
│         🏆 CHAMPIONS 🏆                     │
│                                             │
│   Hip Hop 1v1: B-Boy Storm                 │
│   Breaking 2v2: Phoenix & Thunder          │
│                                             │
│   Thank you for watching!                   │
└─────────────────────────────────────────────┘
```

**Scenario 6: Connection Lost**
```
┌─────────────────────────────────────────────┐
│          ⚠️  RECONNECTING...                │
│                                             │
│   Attempting to restore connection          │
└─────────────────────────────────────────────┘
```

#### 4.3 Multi-Category Handling

**User Question:** "How to show tournaments with multiple categories?"

**Option A: Single Category Focus**
- Projection shows one category at a time
- Admin selects which category to display
- URL: `/projection?category_id=<uuid>`
- Default: First category alphabetically

**Option B: Automatic Cycling**
- Projection cycles through all categories
- 30-second interval per category
- Shows category name prominently
- Pauses on active battle (doesn't switch mid-battle)

**Recommendation for V1:** [User chooses Option A or B]

### Validation Tasks
- [ ] User reviews intelligent display algorithm
- [ ] User selects multi-category strategy (A or B)
- [ ] User confirms empty state messages
- [ ] User approves auto-transition timing

---

## PHASE 5: URL AND ROUTE SPECIFICATION (Day 2, Session 2)

### Objective
Define precise API endpoints and routing behavior for projection interface.

### Deliverable: `docs/PHASE_4_API_SPECIFICATION.md`

#### Primary Route: GET `/projection`

**Purpose:** Main projection display page
**Authentication:** None (public route)
**Query Parameters:**
- `category_id` (optional): UUID of category to display
- `mode` (optional): Force display mode (battle/queue/standings/progression)

**Behavior:**
1. Fetch active tournament (status=ACTIVE)
2. If no active tournament → Show empty state
3. Apply intelligent display logic
4. Render full-page projection template
5. Template includes HTMX for auto-refresh

**Examples:**
```
GET /projection
→ Auto-selected view for active tournament

GET /projection?category_id=abc-123
→ Projection for specific category

GET /projection?mode=standings
→ Forces standings view
```

#### HTMX Refresh Endpoints

**GET `/projection/battle/current`**
- Purpose: Get current active battle data
- Authentication: None
- Returns: HTML fragment (battle card)
- Refresh Interval: 3 seconds

**GET `/projection/queue`**
- Purpose: Get battle queue data
- Authentication: None
- Returns: HTML fragment (queue list)
- Refresh Interval: 10 seconds

**GET `/projection/standings`**
- Purpose: Get pool standings data
- Authentication: None
- Query Parameters: `category_id`, `pool_id` (optional)
- Returns: HTML fragment (standings table)
- Refresh Interval: 30 seconds

**GET `/projection/progression`**
- Purpose: Get finals progression tree
- Authentication: None
- Returns: HTML fragment (progression diagram)
- Refresh Interval: 15 seconds (FINALS phase only)

#### Data Models for Responses

**BattleDisplayData:**
```python
{
  "tournament_name": str,
  "category_name": str,
  "pool_name": str | None,
  "battle_number": int,
  "performer_1_blaze": str,
  "performer_2_blaze": str,
  "status": "active" | "pending" | "completed",
  "winner_blaze": str | None,
  "next_battle": {...} | None
}
```

**StandingsDisplayData:**
```python
{
  "tournament_name": str,
  "category_name": str,
  "pool_name": str,
  "standings": [
    {
      "rank": int,
      "blaze": str,
      "wins": int,
      "draws": int,
      "losses": int,
      "points": int,
      "advancing": bool
    }
  ],
  "last_updated": datetime
}
```

**QueueDisplayData:**
```python
{
  "tournament_name": str,
  "current_battle": BattleDisplayData | None,
  "next_battle": BattleDisplayData | None,
  "pending_battles": [BattleDisplayData],
  "last_updated": datetime
}
```

**ProgressionDisplayData:**
```python
{
  "tournament_name": str,
  "category_name": str,
  "pool_winners": [
    {
      "pool_name": str,
      "winner_blaze": str | None
    }
  ],
  "finals_battle": {
    "status": "pending" | "active" | "completed",
    "performer_1_blaze": str | None,
    "performer_2_blaze": str | None,
    "winner_blaze": str | None
  },
  "champion_blaze": str | None
}
```

#### Security Considerations

**Rate Limiting:**
- 100 requests/minute per IP
- Max concurrent connections: 5 (projection screen context)
- No sensitive data exposed (public tournament info only)

**Data Privacy:**
- Exposed: Tournament name, category names, performer blazes
- NOT exposed: Email addresses, real names, DOB, user accounts, internal IDs

**Performance:**
- Cache active tournament query (5 second TTL)
- Cache category list (tournament lifetime)
- Cache pool standings (recalculate on battle complete)
- Don't cache active battle (real-time)

### Validation Tasks
- [ ] Confirm refresh intervals (3s/10s/30s)
- [ ] Approve data models
- [ ] Confirm security requirements
- [ ] Validate fallback behaviors

---

## PHASE 6: TESTING STRATEGY (Day 3)

### Objective
Define how to test projection endpoints before and during implementation.

### Deliverable: `docs/PHASE_4_TESTING_STRATEGY.md`

#### 1. Unit Tests (Service Layer)

**File:** `tests/test_projection_service.py`

**Test Coverage:**
- Intelligent display logic (which view to show)
- Empty state detection
- Multi-category selection
- Data transformation (DB models → display models)

**Example Tests:**
```python
async def test_select_display_mode_active_battle():
    """Test that active battle triggers battle view."""
    
async def test_select_display_mode_no_active_tournament():
    """Test empty state when no tournament active."""
    
async def test_multi_category_cycling():
    """Test category cycling logic."""
```

#### 2. Route Tests (Integration)

**File:** `tests/test_projection_routes.py`

**Test Coverage:**
- Public route accessibility (no auth required)
- HTMX endpoint responses
- Query parameter handling
- Error handling (404, 500)

**Example Tests:**
```python
async def test_projection_route_accessible_without_auth():
    """Test that /projection is publicly accessible."""
    response = client.get("/projection")
    assert response.status_code == 200
    
async def test_projection_battle_current_returns_html():
    """Test battle endpoint returns valid HTML fragment."""
    
async def test_projection_handles_no_active_tournament():
    """Test empty state rendering."""
```

#### 3. Manual Testing Procedures

**Setup Test Data:**
- Create `tests/fixtures/create_projection_test_data.py`
- Generate sample tournament with:
  - 2 categories (Hip Hop 1v1, Breaking 2v2)
  - 2 pools per category
  - 10 battles (mix of pending/active/completed)
  - Pool standings data

**Manual Test Checklist:**

**Battle View:**
- [ ] Displays active battle correctly
- [ ] Updates when battle completes
- [ ] Shows "Next Up" when no active battle
- [ ] Auto-refreshes every 3 seconds
- [ ] Handles connection loss gracefully

**Queue View:**
- [ ] Shows current battle at top
- [ ] Lists pending battles in order
- [ ] Updates when battles start/complete
- [ ] Auto-refreshes every 10 seconds
- [ ] Empty state when no battles

**Standings View:**
- [ ] Displays pool rankings correctly
- [ ] Calculates points correctly (W×3 + D×1)
- [ ] Shows advancement indicators
- [ ] Updates after battle completes
- [ ] Cycles through pools (if multi-pool)

**Progression View:**
- [ ] Shows pool winners correctly
- [ ] Displays finals bracket structure
- [ ] Updates as finals battles complete
- [ ] Highlights champion when crowned
- [ ] Only shows during FINALS phase

**Empty States:**
- [ ] No active tournament message
- [ ] Registration phase message
- [ ] Tournament complete message
- [ ] Connection lost message
- [ ] No data available message

#### 4. Load Testing

**Tool:** Locust (Python load testing)

**Scenario:**
- 5 concurrent viewers (max expected)
- Each viewer polling every 3s (battle view)
- Sustained for 2 hours (typical tournament duration)

**Metrics:**
- Response time (target: <500ms)
- Error rate (target: <0.1%)
- Database connection pool usage
- Memory usage over time

**Script:** `tests/load/projection_load_test.py`

```python
from locust import HttpUser, task, between

class ProjectionViewer(HttpUser):
    wait_time = between(3, 5)
    
    @task
    def view_projection(self):
        self.client.get("/projection")
    
    @task(3)
    def poll_battle_current(self):
        self.client.get("/projection/battle/current")
    
    @task(1)
    def poll_queue(self):
        self.client.get("/projection/queue")
```

**Run:**
```bash
locust -f tests/load/projection_load_test.py --users 5 --spawn-rate 1
```

#### Success Criteria

**Phase 4 Testing Complete When:**
- [ ] All unit tests passing (>90% coverage)
- [ ] All route tests passing
- [ ] All template tests passing
- [ ] Manual test checklist 100% complete
- [ ] Load test successful (5 concurrent users, 2 hours)
- [ ] Zero critical accessibility violations
- [ ] Documentation updated with testing results

### Validation Tasks
- [ ] Confirm testing approach
- [ ] Approve test data requirements
- [ ] Validate load testing parameters
- [ ] Confirm success criteria

---

## DOCUMENTATION STRUCTURE SUMMARY

### New Documents to Create

1. **`docs/PHASE_4_TERMINOLOGY.md`** (Level 0: Meta)
   - Projection-specific terms
   - Battle state labels
   - Display component names
   - User-facing terminology

2. **`docs/PHASE_4_BATTLE_LIFECYCLE.md`** (Level 3: Operational)
   - Battle status enum
   - State transitions
   - Data availability by state
   - Query patterns

3. **`docs/PHASE_4_UX_FLOWS.md`** (Level 3: Operational)
   - Intelligent display algorithm
   - Empty state handling
   - Multi-category strategy
   - Auto-transition rules

4. **`docs/PHASE_4_API_SPECIFICATION.md`** (Level 3: Operational)
   - Route definitions
   - HTMX endpoints
   - Data models
   - Security/performance

5. **`docs/PHASE_4_TESTING_STRATEGY.md`** (Level 3: Operational)
   - Unit test plan
   - Integration test plan
   - Manual test procedures
   - Load testing approach

### Documents to Update

6. **`UI_MOCKUPS.md`** - Section 13 (Level 2: Derived)
   - Revise all 4 projection displays
   - Remove scope creep features
   - Add V1 badges
   - Clarify terminology

7. **`GLOSSARY.md`** (Level 0: Meta)
   - Add projection-specific terms
   - Add display mode definitions
   - Add battle state labels

8. **`ROADMAP.md`** (Level 2: Derived)
   - Update Phase 4 section with documentation deliverables
   - Mark documentation phase complete when done

---

## TASK BREAKDOWN AND TIMELINE

### Day 1: Core Investigation and Terminology

**Session 1 (3-4 hours):**
- [x] Read existing documentation
- [x] Investigate battle status enum
- [x] Investigate tournament status/phase enums
- [ ] Draft PHASE_4_TERMINOLOGY.md
- [ ] Draft PHASE_4_BATTLE_LIFECYCLE.md
- [ ] Submit to user for review

**Session 2 (3-4 hours):**
- [ ] Incorporate user feedback on terminology
- [ ] Draft Section 13.1 revision (Battle View)
- [ ] Draft Section 13.2 revision (Standings)
- [ ] Submit to user for review

### Day 2: UX Flows and API Specification

**Session 1 (3-4 hours):**
- [ ] Incorporate user feedback on display components
- [ ] Draft PHASE_4_UX_FLOWS.md
- [ ] Define intelligent display algorithm
- [ ] Define all empty states
- [ ] Submit to user for review

**Session 2 (3-4 hours):**
- [ ] Incorporate user feedback on UX flows
- [ ] Draft PHASE_4_API_SPECIFICATION.md
- [ ] Define all routes and endpoints
- [ ] Define data models
- [ ] Submit to user for review

### Day 3: Testing and Finalization

**Session 1 (3-4 hours):**
- [ ] Incorporate user feedback on API spec
- [ ] Draft PHASE_4_TESTING_STRATEGY.md
- [ ] Complete Section 13.3 revision (Queue)
- [ ] Complete Section 13.4 revision (Progression)
- [ ] Submit to user for review

**Session 2 (2-3 hours):**
- [ ] Incorporate all final feedback
- [ ] Update GLOSSARY.md with approved terms
- [ ] Update ROADMAP.md Phase 4 section
- [ ] Create final documentation package
- [ ] Submit for final approval

### Day 4: Optional Buffer
- [ ] Address any remaining questions
- [ ] Refine documentation based on final feedback
- [ ] Create implementation checklist from docs
- [ ] Documentation COMPLETE ✅

---

## VALIDATION AND SUCCESS CRITERIA

### Documentation Complete When:

**Terminology Clarity:**
- [ ] All projection-specific terms defined
- [ ] User confirms "standings" vs "leaderboard" distinction
- [ ] "Bracket" replacement term selected
- [ ] Battle state labels approved (PENDING → "Coming Up", etc.)

**Battle Lifecycle:**
- [ ] All state transitions documented
- [ ] Data availability confirmed for each state
- [ ] Query patterns validated from code
- [ ] Edge cases identified and documented

**Display Components:**
- [ ] All 4 displays revised in UI_MOCKUPS
- [ ] Scope creep features removed (judges, rounds, avatars)
- [ ] Empty states defined for each display
- [ ] Multi-category handling strategy chosen

**UX Flows:**
- [ ] Intelligent display algorithm approved
- [ ] Auto-transition rules defined
- [ ] Empty state UX confirmed
- [ ] Multi-category strategy selected (A or B)

**API Specification:**
- [ ] All routes defined
- [ ] HTMX endpoints specified
- [ ] Data models approved
- [ ] Security requirements confirmed

**Testing Strategy:**
- [ ] Test approach approved
- [ ] Manual test procedures defined
- [ ] Load testing parameters confirmed
- [ ] Success criteria agreed

**Integration:**
- [ ] GLOSSARY.md updated
- [ ] ROADMAP.md updated
- [ ] No contradictions with DOMAIN_MODEL.md or VALIDATION_RULES.md
- [ ] Cross-references added to DOCUMENTATION_INDEX.md

**User Approval:**
- [ ] User reviews all 5 new documents
- [ ] User approves UI_MOCKUPS revisions
- [ ] User confirms no missing requirements
- [ ] User agrees documentation is implementation-ready

---

## DELIVERABLES SUMMARY

### Artifacts Produced

**New Documentation (5 files):**
1. `docs/PHASE_4_TERMINOLOGY.md` - ~500 lines
2. `docs/PHASE_4_BATTLE_LIFECYCLE.md` - ~300 lines
3. `docs/PHASE_4_UX_FLOWS.md` - ~600 lines
4. `docs/PHASE_4_API_SPECIFICATION.md` - ~700 lines
5. `docs/PHASE_4_TESTING_STRATEGY.md` - ~500 lines

**Updated Documentation (3 files):**
6. `UI_MOCKUPS.md` - Section 13 complete rewrite (~800 lines)
7. `GLOSSARY.md` - +15 new terms (~50 lines added)
8. `ROADMAP.md` - Phase 4 documentation section (~100 lines)

**Total:** ~3550 lines of comprehensive documentation

### Knowledge Captured

**Questions Answered:**
1. ✅ Battle state lifecycle (PENDING = "to come")
2. ✅ Empty state UX (8 scenarios defined)
3. ✅ Display mode logic (intelligent algorithm)
4. ✅ Terminology clarity (standings, progression, battle states)
5. ✅ Multi-category handling (Option A vs B)
6. ✅ Testing strategy (unit, integration, manual, load)

**Scope Defined:**
- ✅ V1 features included
- ✅ V1 features excluded (judges, rounds, avatars, sponsors)
- ✅ V2 future enhancements identified
- ✅ Edge cases documented
- ✅ Performance requirements specified

**Implementation Ready:**
- ✅ Clear API contracts
- ✅ Defined data models
- ✅ Template structure specified
- ✅ Test coverage planned
- ✅ No ambiguity remaining

---

## NEXT STEPS AFTER DOCUMENTATION

### Phase 4 Implementation Sequence

**Step 1: Route Structure** (Day 1)
- Create `app/routers/projection.py`
- Register routes in `app/main.py`
- Basic template structure

**Step 2: Service Layer** (Day 2)
- Create `app/services/projection_service.py`
- Implement intelligent display logic
- Data transformation methods

**Step 3: Templates** (Day 3)
- `templates/projection/base.html`
- `templates/projection/battle_view.html`
- `templates/projection/queue_view.html`
- `templates/projection/standings_view.html`
- `templates/projection/progression_view.html`

**Step 4: HTMX Endpoints** (Day 4)
- Battle current endpoint
- Queue endpoint
- Standings endpoint
- Progression endpoint

**Step 5: Testing** (Day 5)
- Unit tests
- Integration tests
- Manual testing
- Load testing

**Step 6: Refinement** (Day 6)
- Performance optimization
- CSS styling
- Edge case handling
- Documentation updates

**Estimated:** 6-8 days implementation (conservative estimate)

---

## CRITICAL FILES FOR IMPLEMENTATION

Based on this documentation plan, these files will be critical:

1. **`app/routers/projection.py`** - Main projection routes and HTMX endpoints (NEW)
2. **`app/services/projection_service.py`** - Business logic for display selection (NEW)
3. **`app/templates/projection/base.html`** - Base template with HTMX polling (NEW)
4. **`app/templates/projection/battle_view.html`** - Battle display component (NEW)
5. **`app/repositories/battle.py`** - Query methods for battles (EXTEND EXISTING)

---

## CONCLUSION

This documentation plan provides a comprehensive approach to creating complete functional specifications for Phase 4: Projection Interface before implementation begins.

**Key Benefits:**
1. **Eliminates Ambiguity:** All terminology clarified before coding
2. **Prevents Scope Creep:** Clear V1/V2 boundaries established
3. **Testable Specifications:** Testing strategy defined upfront
4. **Implementation-Ready:** No guesswork needed during coding
5. **User Validation:** Multiple review checkpoints throughout process

**Estimated Timeline:** 3-4 days for complete documentation
**Implementation Confidence:** High (clear specs, validated by user)
**Risk Mitigation:** Questions answered before code written

The plan is actionable, measurable, and delivers clear success criteria.

---

### Critical Files for Implementation

Once documentation is complete, these will be the most critical files for implementing Phase 4:

1. **`/Users/aissacasa/Library/CloudStorage/GoogleDrive-aissacasapro@gmail.com/My Drive/My clients/Battle-D/dev/web-app/app/routers/projection.py`** - Main projection routes (NEW - will be created)
2. **`/Users/aissacasa/Library/CloudStorage/GoogleDrive-aissacasapro@gmail.com/My Drive/My clients/Battle-D/dev/web-app/app/services/projection_service.py`** - Business logic (NEW - will be created)
3. **`/Users/aissacasa/Library/CloudStorage/GoogleDrive-aissacasapro@gmail.com/My Drive/My clients/Battle-D/dev/web-app/app/templates/projection/base.html`** - HTMX base template (NEW - will be created)
4. **`/Users/aissacasa/Library/CloudStorage/GoogleDrive-aissacasapro@gmail.com/My Drive/My clients/Battle-D/dev/web-app/app/repositories/battle.py`** - Battle query methods (EXTEND EXISTING)
5. **`/Users/aissacasa/Library/CloudStorage/GoogleDrive-aissacasapro@gmail.com/My Drive/My clients/Battle-D/dev/web-app/app/templates/projection/battle_view.html`** - Battle view component (NEW - will be created)
