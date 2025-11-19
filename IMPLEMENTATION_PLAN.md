# Battle-D Implementation Plan

Phased development roadmap from POC to V2.

---

## Phase 0: POC + Production Railway (COMPLETED ✅)

**Duration:** 3-5 days

**Objective:** Proof of concept deployed on Railway with full production setup.

**Deliverables:**
- ✅ FastAPI application architecture
- ✅ Magic link authentication (passwordless)
- ✅ Role-based access control (Admin, Staff, MC)
- ✅ Hardcoded phase navigation (Registration → Preselection → Pools → Finals → Completed)
- ✅ Minimal HTML templates (zero CSS, structural only)
- ✅ 49 tests passing (auth, permissions, phases)
- ✅ Railway deployment with SQLite persistent volume
- ✅ Brevo API configured (production emails - no domain required)
- ✅ Live URL accessible
- ✅ Cost: ~$0-5/month

**Tech Stack:**
- FastAPI + Uvicorn
- Jinja2 templates
- itsdangerous (magic links)
- Brevo Python SDK (emails - adapter pattern, SDK-verified)
- SQLite (persistent volume on Railway)

**Status:** COMPLETE - Application live on Railway

**Post-Phase 0 Refactoring:**
- ✅ **Email Service Refactored** - Migrated to SOLID architecture with Adapter Pattern
  - Created `EmailProvider` interface for provider abstraction
  - Implemented `BrevoEmailProvider` (RECOMMENDED for Railway - no domain, 300/day free)
  - Implemented `ResendEmailProvider` using official Resend SDK (requires domain)
  - Implemented `GmailEmailProvider` using Gmail SMTP (BLOCKED on Railway)
  - Implemented `ConsoleEmailProvider` for development mode
  - Added provider factory with dependency injection
  - SDK-verified implementation using Context7 documentation
  - **Benefits:** Easy to swap email providers, testable by design, follows DIP principle
  - **Files:** `app/services/email/` (new structure)
  - **Configuration:** `EMAIL_PROVIDER` environment variable (brevo/resend/gmail/console)
  - **Brevo (Recommended):** No domain needed, 300 emails/day, works on Railway, SDK best practices
  - **Tests:** 79 passing (11 Brevo tests with name validation, tags, response validation)

---

## Phase 1: Database + CRUD (COMPLETED ✅)

**Duration:** 7-10 days

**Objective:** Add persistence layer and full CRUD operations.

**Database Models (SQLAlchemy):**
- `User` (email, first_name, role)
- `Dancer` (email, first_name, last_name, date_of_birth, blaze, country, city)
- `Tournament` (name, status, phase)
- `Category` (name, is_duo, groups_ideal, performers_ideal)
- `Performer` (dancer_id, tournament_id, category_id, duo_partner_id)
- `Pool` (category_id, performers, winner_id)
- `Battle` (category_id, phase, status, performers, outcome)

**CRUD Interfaces:**

1. **Admin Manage Users** ✅
   - Create User accounts (Staff/MC)
   - Send magic links
   - List users by role
   - Edit and delete users
   - Resend magic links

2. **Staff Manage Dancers** ✅
   - Create Dancer (full form: 8 fields)
   - Edit Dancer information
   - Search Dancers (by blaze, name, email) with HTMX live search
   - View Dancer profile and history (tournaments participated)

3. **Staff Manage Tournaments** ✅
   - Create Tournament
   - Add/configure Categories (1v1 and 2v2)
   - Set groups_ideal, performers_ideal per category
   - Dynamic minimum performer calculation display
   - Database-driven phase navigation with validation

4. **Staff Register Dancers** ✅
   - Select Tournament + Category
   - Search and select Dancer with HTMX live search
   - Create Performer record
   - Handle duo pairing (if 2v2 category) with partner linking
   - JavaScript-based duo selection UI

**Service Layer Architecture:** ✅
- `DancerService` - Business logic for dancer operations with age/email validation
- `TournamentService` - Tournament phase advancement with validation
- `PerformerService` - Registration with duo pairing support
- `ValidationResult` - Type-safe error handling
- `ValidationError` - Custom exception for business rules

**Validators & Utils:** ✅
- `phase_validators.py` - Phase transition validation functions
- `tournament_calculations.py` - Formulas for min performers, pool distribution
- Pydantic schemas for all entities with field validation

**Migrations:** ✅
- Alembic setup
- Initial schema migration
- Migration from CLI data (optional)

**Validations:** ✅
- Unique email constraints
- Unique dancer per tournament
- Minimum performer requirements: `(groups_ideal × 2) + 2`
- Phase transition validation (cannot skip phases)

**Tests:** ✅
- Model tests
- CRUD operation tests
- Validation tests
- Tournament calculation tests (24 tests)
- CRUD workflow integration tests
- Target: 90%+ coverage - **ACHIEVED**

**Deployment:** ✅
- Same Railway setup
- SQLite database on `/data` volume
- Alembic migrations run on deploy

**Status:** COMPLETE - All UI components implemented and tested

---

## Phase 2: Battle Management + Preselection Logic

**Duration:** 7-10 days (reduced from 10-14, infrastructure already complete)

**Status:** 🟡 IN PROGRESS (~35% complete - Infrastructure done, Execution logic needed)

**Objective:** Implement battle execution, scoring interfaces, and queue management.

### **2.0 Infrastructure Layer (COMPLETED ✅ in Phase 1)**

**Database Models:** ✅ COMPLETE
- Battle model with all phases (PRESELECTION, POOLS, TIEBREAK, FINALS)
- Battle outcome types (SCORED, WIN_DRAW_LOSS, TIEBREAK, WIN_LOSS)
- Pool model with performer relationships and winner tracking
- Performer stats (preselection_score, pool_wins/draws/losses, pool_points computed property)
- Database migrations applied and tested

**Repository Layer:** ✅ COMPLETE
- `BattleRepository` - CRUD, filter by category/phase/status, get active battle
- `PoolRepository` - CRUD, get by category, create pools
- All repository methods tested

**Calculation Utilities:** ✅ COMPLETE
- `calculate_pool_capacity(registered_performers, groups_ideal)` - Determines pool size with ~20-25% elimination
- `distribute_performers_to_pools(performer_count, groups_ideal)` - Even distribution (sizes differ by max 1)
- `calculate_minimum_performers(groups_ideal)` - Formula: (groups_ideal × 2) + 2
- `calculate_minimum_for_category(groups_ideal, performers_ideal)` - All tournament metrics
- **24 comprehensive tests** covering all formulas and edge cases

**Phase Validators:** ✅ COMPLETE
- `validate_registration_to_preselection()` - Checks minimum performers per category
- `validate_preselection_to_pools()` - Validates battle completion and scores
- `validate_pools_to_finals()` - Validates pool battles and winners
- `validate_finals_to_completed()` - Validates finals completion
- **Note:** Validators assume battles exist (battle creation logic in sections 2.1-2.4 below)

**What This Means:**
- All data structures ready for battle management
- All formulas implemented and tested
- Validation logic ready
- **Remaining work:** Battle generation services, scoring UI, queue management

---

### **2.1 Battle Generation Services** ❌ NOT STARTED (~20% of Phase 2)

**Create BattleService:**
- [ ] Preselection battle generation
  - [ ] 1v1 pairing algorithm with random shuffle
  - [ ] 3-way battle creation if odd number of performers
  - [ ] Assign outcome_type = SCORED
- [ ] Pool battle generation
  - [ ] Round-robin generation (all vs all within pool)
  - [ ] Assign outcome_type = WIN_DRAW_LOSS
- [ ] Finals battle generation
  - [ ] Create battle with pool winners
  - [ ] Assign outcome_type = WIN_LOSS (no draws)
- [ ] Battle status transitions
  - [ ] pending → active (start battle)
  - [ ] active → completed (encode results)
- [ ] Queue management
  - [ ] Enforce one active battle at a time
  - [ ] Get next pending battle

**Create PoolService:**
- [ ] Pool creation based on qualification results
  - [ ] Use `calculate_pool_capacity()` to determine pool size
  - [ ] Sort performers by preselection_score (descending)
  - [ ] Select top pp performers
- [ ] Performer distribution to pools
  - [ ] Use `distribute_performers_to_pools()` for even distribution
  - [ ] Assign performers to created pools
- [ ] Winner determination
  - [ ] Calculate pool_points for all performers
  - [ ] Determine highest points per pool
  - [ ] Detect ties and trigger tiebreak

**Create TiebreakService:**
- [ ] Detect ties at preselection qualification cutoff
  - [ ] Find performers with same score at boundary
  - [ ] Calculate how many spots available (P) vs tied (N)
- [ ] Detect ties for pool winners
  - [ ] Find performers with same pool_points at top
  - [ ] Require exactly 1 winner per pool
- [ ] Generate tiebreak battles
  - [ ] Create battle with N tied performers
  - [ ] Assign outcome_type = TIEBREAK
  - [ ] Set P (winners_needed) in battle
- [ ] Implement voting logic
  - [ ] N=2: Judges vote who to KEEP
  - [ ] N>2: Judges vote who to ELIMINATE (iterative rounds)
  - [ ] Store all votes in battle.outcome

**Files to Create:**
- `app/services/battle_service.py`
- `app/services/pool_service.py`
- `app/services/tiebreak_service.py`

### **2.2 Battle Routes & UI** ❌ NOT STARTED (~25% of Phase 2)

**Battle Routes** (`app/routers/battles.py`):
- [ ] `GET /battles` - Battle queue/list view
  - [ ] Show all battles by status (pending, active, completed)
  - [ ] Highlight current active battle
  - [ ] "Next Battle" button (starts next pending)
- [ ] `GET /battles/{id}` - Battle details view
  - [ ] Display performers, phase, status
  - [ ] Show current outcome if completed
- [ ] `POST /battles/{id}/start` - Start battle (pending → active)
  - [ ] Validate no other battle is active
  - [ ] Update status to ACTIVE
  - [ ] Redirect to encoding interface
- [ ] `POST /battles/{id}/encode` - Encode battle results
  - [ ] Route to appropriate encoding handler based on outcome_type
  - [ ] Validate all required data present
  - [ ] Store results in battle.outcome
  - [ ] Update performer stats if needed
- [ ] `POST /battles/{id}/complete` - Complete battle (active → completed)
  - [ ] Validate outcome data is present
  - [ ] Update status to COMPLETED
  - [ ] Redirect to battle queue

**Templates to Create:**
- [ ] `battles/list.html` - Queue display with status indicators
- [ ] `battles/detail.html` - Battle information
- [ ] `battles/encode_preselection.html` - Scoring grid (judges × performers)
- [ ] `battles/encode_pool.html` - Winner/draw selection
- [ ] `battles/encode_tiebreak.html` - Judge voting interface
- [ ] `pools/overview.html` - Pool standings and points

**HTMX Features:**
- [ ] Auto-refresh battle queue every 10 seconds
- [ ] Inline status updates without page reload
- [ ] Dynamic encoding form based on outcome_type

### **2.3 Scoring & Encoding Logic** ❌ NOT STARTED (~20% of Phase 2)

**Preselection Encoding:**
- [ ] Input validation
  - [ ] 0-10 range per performer per judge
  - [ ] Decimal allowed (e.g., 7.5)
  - [ ] All judges must submit scores for all performers
- [ ] Calculate average scores
  - [ ] Average across all judges per performer
  - [ ] Round to 2 decimal places
  - [ ] Store in `performer.preselection_score`
- [ ] Determine qualification
  - [ ] Sort performers by score (descending)
  - [ ] Mark top pp as qualified
  - [ ] Detect ties at cutoff

**Pool Battle Encoding:**
- [ ] Winner selection interface
  - [ ] Radio buttons: Performer 1, Performer 2, Draw
  - [ ] Validate exactly one option selected
- [ ] Update performer stats
  - [ ] Winner: `performer.add_pool_win()`
  - [ ] Loser: `performer.add_pool_loss()`
  - [ ] Draw: `performer.add_pool_draw()` for both
  - [ ] Auto-calculate `pool_points` property
- [ ] Store outcome
  - [ ] `battle.set_win_draw_loss_outcome(winner_id, is_draw)`

**Tiebreak Battle Encoding:**
- [ ] Judge voting interface
  - [ ] If N=2: Radio buttons "Keep Performer 1" / "Keep Performer 2"
  - [ ] If N>2: Checkboxes "Eliminate Performer X" (one per judge)
- [ ] Round management
  - [ ] Collect votes from all judges
  - [ ] Determine majority vote
  - [ ] If N>2: Eliminate one, repeat with N-1
  - [ ] If N=2: Select winner based on majority
- [ ] Store all votes
  - [ ] Format: `{"judge_1_round_1": "performer_id", ...}`
  - [ ] `battle.set_tiebreak_outcome(n_participants, p_winners_needed, judge_votes, winner_ids)`

**Pydantic Schemas to Create:**
- [ ] `app/schemas/battle.py` - CreateBattleSchema, EncodeBattleSchema
- [ ] `app/schemas/pool.py` - CreatePoolSchema, PoolStandingsSchema
- [ ] `app/schemas/scoring.py` - PreselectionScoreSchema, TiebreakVoteSchema

### **2.4 Phase Transition Hooks** ❌ CRITICAL (~10% of Phase 2)

**Integration Points:**

**REGISTRATION → PRESELECTION:**
- [ ] Call `BattleService.generate_preselection_battles(category_id)`
  - [ ] For each category with sufficient performers
  - [ ] Create 1v1 or 3-way battles
  - [ ] Set all battles to status = PENDING

**PRESELECTION → POOLS:**
- [ ] Call `PoolService.create_pools_from_qualification(category_id)`
  - [ ] Use preselection_score to determine top pp performers
  - [ ] Create pools with even distribution
  - [ ] Call `BattleService.generate_pool_battles(pool_id)` for each pool
  - [ ] Set all battles to status = PENDING

**POOLS → FINALS:**
- [ ] Call `BattleService.generate_finals_battles(category_id)`
  - [ ] Extract one winner per pool
  - [ ] Create finals bracket
  - [ ] Set all battles to status = PENDING

**Current Gap:**
`app/routers/phases.py` validates phase transitions but **does NOT create battles**.

**Files to Modify:**
- [ ] `app/routers/phases.py` - Add battle/pool generation calls after validation
- [ ] `app/services/tournament_service.py` - Coordinate battle/pool/tiebreak services

**Example Implementation:**
```python
# In app/routers/phases.py - advance_tournament_phase()
if tournament.phase == Phase.REGISTRATION and validation.success:
    # Auto-generate preselection battles
    for category in tournament.categories:
        await battle_service.generate_preselection_battles(category.id)

    tournament.phase = Phase.PRESELECTION
    await tournament_repo.update(tournament)
```

### **2.5 Testing & Documentation**

**Tests to Create:**
- [ ] `tests/test_battle_service.py` - Battle generation, status transitions
- [ ] `tests/test_pool_service.py` - Pool creation, distribution, winner determination
- [ ] `tests/test_tiebreak_service.py` - Tie detection, tiebreak battles, voting logic
- [ ] `tests/test_battle_routes.py` - HTTP endpoints, encoding, queue management
- [ ] `tests/test_phase_2_integration.py` - Complete tournament flow (registration → completed)

**Documentation:**
- [ ] Update ARCHITECTURE.md with battle service patterns
- [ ] Document battle encoding workflows
- [ ] Add tiebreak algorithm explanation

---

## Phase 3: Projection Interface

**Duration:** 3-5 days

**Objective:** Public display screen for audience.

**Route:** `/projection/{tournament_id}` (no authentication)

**Display Elements:**
- Current battle (performers, category)
- Last battle result (winner/draw)
- Pool standings (points table)
- Current champions per category

**Auto-Refresh:**
- HTMX polling every 5 seconds
- Or Server-Sent Events (SSE)
- Real-time updates without page reload

**HTML:**
- Large text for visibility
- Structural layout only (no CSS styling)
- Optimized for projector display

**Tests:**
- Public route accessible
- Data correctness
- Refresh mechanism

---

## Phase 4: V1 Completion

**Duration:** 3-5 days

**Objective:** Production-ready V1 release.

### **4.1 End-to-End Tests**

**Test Scenarios:**
- Complete tournament flow (registration → champion)
- Multiple categories simultaneously
- Edge cases (minimum performers, ties, odd numbers)
- Browser testing (Chrome, Firefox, Safari)

**Tools:**
- Playwright or Selenium
- pytest integration

### **4.2 CI/CD Setup**

**GitHub Actions:**
- Run tests on every PR
- Auto-deploy to Railway on merge to `main`
- Environment-specific configs

**Deployment Pipeline:**
```yaml
Pull Request → Tests → Review → Merge → Auto-deploy → Railway Production
```

### **4.3 Backup Strategy**

**SQLite Backups:**
- Manual: `railway run cat /data/battle_d.db > backup.db`
- Automated: Cron job (Railway cron) daily backups to S3/Cloudflare R2
- Retention: 30 days

### **4.4 Monitoring**

- Railway dashboard (CPU, RAM, requests)
- Error logging (Sentry optional)
- Health check endpoint monitoring

### **4.5 Documentation**

- User guide for Admin/Staff
- How to create tournament
- How to manage battles
- Troubleshooting common issues

**Release:** V1 STABLE ✅

---

## Phase 5: Judge Interface (V2)

**Duration:** 5-7 days

**Objective:** Direct judge scoring, no manual encoding.

### **5.1 Judge Model**

- `Judge` table (user_id, tournament_id, deleted_at)
- Judges are temporary Users (role='judge')
- Soft-deleted after tournament ends

### **5.2 Judge Interface**

**Authentication:**
- Admin creates judge accounts
- Judges receive magic link
- Access restricted to assigned tournament only

**Scoring Interface:**
- List of active battles for tournament
- **Preselection:** Input 0-10 per performer
- **Pools/Tiebreak:** Select winner or mark draw
- **Blind scoring:** Judge sees only their own scores

**Real-time Submission:**
- Scores saved immediately
- No page refresh required
- Judge cannot change after submission (optional lock)

### **5.3 Admin Aggregation**

**Admin View:**
- See all judge scores
- Identify missing scores
- Calculate averages automatically
- Validate battle completion

**Battle Completion:**
- Admin clicks "Complete Battle"
- System aggregates all judge scores
- Determines winner/qualifiers
- Updates performer stats

**Workflow:**
```
Battle starts
  → Judges score independently (blind)
  → Admin monitors submissions
  → All judges submitted?
  → Admin validates and completes battle
  → Results calculated
  → Next battle
```

### **5.4 Judge Management**

- Admin creates/deletes judge accounts
- Assign judges to tournaments
- Soft-delete judges after tournament
- Judge activity logs

**Tests:**
- Judge authentication
- Blind scoring isolation
- Score aggregation accuracy
- Permission boundaries

**Release:** V2 COMPLETE ✅

---

## Estimated Timeline Summary

| Phase | Duration | Cumulative | Status |
|-------|----------|------------|--------|
| Phase 0 (POC + Railway) | 3-5 days | 3-5 days | ✅ COMPLETE |
| Phase 1 (Database + CRUD) | 7-10 days | 10-15 days | ✅ COMPLETE |
| Phase 2 (Battle Logic) | 7-10 days | 17-25 days | 🟡 IN PROGRESS (35% infrastructure done) |
| Phase 3 (Projection) | 3-5 days | 20-30 days | ⏳ Planned |
| Phase 4 (V1 Complete) | 3-5 days | 23-35 days | ⏳ Planned |
| **V1 RELEASE** | - | **~23-35 days** | 🎯 Target |
| Phase 5 (Judge Interface V2) | 5-7 days | 28-42 days | ⏳ Future |
| **V2 RELEASE** | - | **~28-42 days** | 🎯 Extended |

**Notes:**
- Solo developer timeline
- Assumes ~6-8 hours/day focused work
- Includes testing and deployment time
- Buffer for unexpected issues

---

## Technology Stack Evolution

### **Phase 0-4 (V1):**
- FastAPI + Uvicorn
- Jinja2 templates
- HTMX (auto-refresh)
- SQLAlchemy 2.0 (async)
- Alembic (migrations)
- SQLite (Railway volume)
- Brevo (emails - recommended for Railway)
- pytest + pytest-asyncio

### **Phase 5 (V2):**
- Add: Real-time judge scoring
- Consider: WebSockets for live updates (optional)
- Same stack otherwise

### **Future Considerations:**
- If scale exceeds SQLite: Migrate to PostgreSQL (Railway makes this easy)
- If concurrent users increase: Add Redis caching
- If international: Add i18n support (English base)

---

## Success Criteria

### **V1 Launch Ready When:**
- ✅ All CRUD operations functional
- ✅ Complete tournament can be run start-to-finish
- ✅ Preselection mandatory and adaptive
- ✅ Tiebreak logic fully automatic
- ✅ Projection screen displays correctly
- ✅ 90%+ test coverage
- ✅ Deployed and stable on Railway
- ✅ User documentation complete

### **V2 Launch Ready When:**
- ✅ Judges can score independently
- ✅ Blind scoring enforced
- ✅ Admin aggregation working
- ✅ All V1 features stable
- ✅ Judge workflow documented

---

## Maintenance Plan

**Post-V1:**
- Bug fixes as reported
- Performance optimization if needed
- Backup verification monthly
- Railway costs monitoring

**Post-V2:**
- Feature requests evaluation
- Potential enhancements:
  - Mobile app (if needed)
  - Video integration
  - Analytics dashboard
  - Multi-language support

---

## Current Status

**Latest:** Phase 1 COMPLETE ✅, Phase 2 IN PROGRESS 🟡
**Next:** Phase 2 Battle Execution Logic (infrastructure 35% done)
**Target:** V1 in ~13-20 days remaining

**Live URL:** [To be added after Railway deployment]
**Cost:** ~$0-5/month (SQLite on Railway free tier)

**Phase 1 Highlights:**
- Complete CRUD UIs for users, dancers, tournaments, and registration
- Service layer architecture with validators and utils
- HTMX integration for live search and dynamic forms
- Database-driven phase navigation
- 90%+ test coverage achieved

**Phase 2 Infrastructure Complete (35%):**
- Database models (Battle, Pool, Performer stats) ✅
- Repositories (BattleRepository, PoolRepository) ✅
- Calculation utilities (pool structure, distribution) with 24 tests ✅
- Phase validators (validation logic ready) ✅
- **Remaining:** Battle generation services, scoring UI, queue management, phase hooks
