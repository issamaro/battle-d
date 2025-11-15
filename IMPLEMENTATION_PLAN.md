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
- ✅ Resend API configured (production emails)
- ✅ Live URL accessible
- ✅ Cost: ~$0-5/month

**Tech Stack:**
- FastAPI + Uvicorn
- Jinja2 templates
- itsdangerous (magic links)
- Resend Python SDK (emails - adapter pattern)
- SQLite (persistent volume on Railway)

**Status:** COMPLETE - Application live on Railway

**Post-Phase 0 Refactoring:**
- ✅ **Email Service Refactored** - Migrated to SOLID architecture with Adapter Pattern
  - Created `EmailProvider` interface for provider abstraction
  - Implemented `ResendEmailProvider` using official Resend SDK (replaced direct HTTP calls)
  - Implemented `ConsoleEmailProvider` for development mode
  - Added provider factory with dependency injection
  - Updated tests to use mock providers (no more `unittest.mock.patch`)
  - **Benefits:** Easy to swap email providers, testable by design, follows DIP principle
  - **Files:** `app/services/email/` (new structure)
  - **Configuration:** `EMAIL_PROVIDER` environment variable (resend/console)

---

## Phase 1: Database + CRUD

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

1. **Admin Manage Users**
   - Create User accounts (Staff/MC)
   - Send magic links
   - List users by role

2. **Staff Manage Dancers**
   - Create Dancer (full form: 8 fields)
   - Edit Dancer information
   - Search Dancers (by blaze, name, email)
   - View Dancer history (tournaments participated)

3. **Staff Manage Tournaments**
   - Create Tournament
   - Add/configure Categories
   - Set groups_ideal, performers_ideal per category

4. **Staff Register Dancers**
   - Select Tournament + Category
   - Search and select Dancer
   - Create Performer record
   - Handle duo pairing (if 2v2 category)

**Migrations:**
- Alembic setup
- Initial schema migration
- Migration from CLI data (optional)

**Validations:**
- Unique email constraints
- Unique dancer per tournament
- Minimum performer requirements

**Tests:**
- Model tests
- CRUD operation tests
- Validation tests
- Target: 90%+ coverage

**Deployment:**
- Same Railway setup
- SQLite database on `/data` volume
- Alembic migrations run on deploy

---

## Phase 2: Battle Management + Preselection Logic

**Duration:** 10-14 days

**Objective:** Complete battle system with mandatory preselection.

### **2.1 Preselection (MANDATORY)**

**Pool Structure Calculation:**
- Input: registered_performers (rp), groups_ideal
- Output: pool_performers (pp) where pp < rp
- Constraint: Always eliminate at least 2 performers
- Adaptive pool sizes (e.g., rp=8 → pp=6, pools of 3)

**Battle Generation:**
- Mostly 1v1 pairings (random shuffle)
- 3-way battle if odd number
- Judges score 0-10 per performer
- Calculate average score (2 decimals)

**Qualification:**
- Sort by descending score
- Top pp performers qualify
- Detect ties at boundary
- **Auto-create tiebreak battles** if tied at cutoff

### **2.2 Pool Phase**

**Pool Creation:**
- Create groups_ideal pools
- Distribute performers evenly
- Round-robin battle generation (all vs all)

**Battle Execution:**
- Sequential battles (one active at a time)
- Interface: Start Battle / End Battle buttons
- Staff/Admin manually encodes results (Win/Draw/Loss)

**Points Calculation:**
- Win = 3 points
- Draw = 1 point
- Loss = 0 points
- Computed pool_points property

**Winner Determination:**
- Highest pool_points wins
- Detect ties at top
- **Auto-create tiebreak battles** if tied

### **2.3 Tiebreak Logic (Complete Implementation)**

**Tiebreak Battle Creation:**
- Triggered automatically when ties detected
- Input: N tied performers, P winners needed
- Constraint: P < N

**Judging Algorithm:**
- If N=2: Judges vote who to KEEP
- If N>2: Judges vote who to ELIMINATE (iterative)
- Rounds continue until exactly P winners
- Majority vote per round
- Store all judge votes for audit

**Integration Points:**
- Preselection qualification ties
- Pool winner ties
- Multi-round handling

### **2.4 Queue Management**

- Global battle queue
- One battle active at a time
- Status transitions: pending → active → completed
- Admin/Staff controls progression

### **2.5 Manual Encoding Interface**

**Preselection:**
- Form with 3 judges × N performers
- Input: scores 0-10
- Calculate averages automatically

**Pools/Finals:**
- Select winner or mark draw
- Update performer stats (wins, draws, losses)
- Compute pool_points

**Tests:**
- Battle generation tests
- Scoring calculation tests
- Tiebreak algorithm tests
- Pool structure tests
- Phase transition tests

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
| Phase 1 (Database + CRUD) | 7-10 days | 10-15 days | 📋 Next |
| Phase 2 (Battle Logic) | 10-14 days | 20-29 days | ⏳ Planned |
| Phase 3 (Projection) | 3-5 days | 23-34 days | ⏳ Planned |
| Phase 4 (V1 Complete) | 3-5 days | 26-39 days | ⏳ Planned |
| **V1 RELEASE** | - | **~26-39 days** | 🎯 Target |
| Phase 5 (Judge Interface V2) | 5-7 days | 31-46 days | ⏳ Future |
| **V2 RELEASE** | - | **~31-46 days** | 🎯 Extended |

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
- Resend (emails)
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

**Latest:** Phase 0 COMPLETE ✅
**Next:** Phase 1 (Database + CRUD)
**Target:** V1 in ~26-39 days

**Live URL:** [To be added after Railway deployment]
**Cost:** ~$0-5/month (SQLite on Railway free tier)
