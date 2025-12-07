# Battle-D Development Methodology
**For AI Assistant (Claude) - Comprehensive Workflow Guide**

**Last Updated:** 2025-12-03
**Version:** 1.0

---

## Purpose

This document provides a complete development methodology for the Battle-D project, designed specifically for AI-assisted development. It guides the entire lifecycle from business analysis through testing and deployment, ensuring consistency, quality, and adherence to established patterns.

**Target Reader:** Claude AI Assistant (me)
**Scope:** Business analysis → Requirements → Design → Documentation → Implementation → Testing → Deployment → Closure

---

## Table of Contents

### PART 1: QUICK REFERENCE
- [Decision Trees](#decision-trees)
- [Quality Gates Checklists](#quality-gates-checklists)
- [Common Mistakes Reference](#common-mistakes-reference)

### PART 2: DEVELOPMENT LIFECYCLE
1. [Business Analysis Phase](#1-business-analysis-phase)
2. [Requirements Definition Phase](#2-requirements-definition-phase)
3. [Technical Design Phase](#3-technical-design-phase)
4. [Documentation Phase](#4-documentation-phase)
5. [Implementation Phase](#5-implementation-phase)
6. [Testing Phase](#6-testing-phase)
7. [Deployment Phase](#7-deployment-phase)
8. [Closure Phase](#8-closure-phase)

### PART 3: PROJECT MANAGEMENT
- [Phase Planning](#phase-planning)
- [Stakeholder Communication](#stakeholder-communication)
- [Risk Management](#risk-management)

### PART 4: TEMPLATES & EXAMPLES
- [Workbench File Template](#workbench-file-template)
- [Test Structure Templates](#test-structure-templates)
- [Commit Message Template](#commit-message-template)
- [Good vs Bad Patterns](#good-vs-bad-patterns)

### PART 5: INTEGRATION WITH EXISTING DOCS
- [Documentation Map](#documentation-map)
- [When to Read Which Document](#when-to-read-which-document)
- [How Plan Mode Maps to Methodology](#how-plan-mode-maps-to-methodology)

---

# PART 1: QUICK REFERENCE

## Decision Trees

### Decision: New Entity vs Extend Existing Entity?

```
Does an existing entity closely match the need?
├─ YES: Can it be extended without breaking existing code?
│  ├─ YES: Extend existing entity
│  │  └─ Add fields/methods to model
│  │  └─ Update DOMAIN_MODEL.md
│  │  └─ Create Alembic migration
│  └─ NO: Create new entity
│     └─ New model file
│     └─ Add to DOMAIN_MODEL.md
│     └─ Create Alembic migration
└─ NO: Create new entity
   └─ (same as above)
```

**Examples:**
- Adding `tournament_date` to Tournament → **Extend** (simple field addition)
- Adding Judge entity for V2 → **Create new** (distinct concept)

---

### Decision: New Service vs Extend Existing Service?

```
Does an existing service handle related functionality?
├─ YES: Would adding new method violate SRP?
│  ├─ YES: Create new service
│  │  └─ New file: app/services/new_service.py
│  │  └─ Document in ARCHITECTURE.md
│  └─ NO: Extend existing service
│     └─ Add method to existing service
│     └─ Keep cohesive responsibility
└─ NO: Create new service
   └─ (same as above)
```

**Examples:**
- Adding `get_active_tournament()` to TournamentService → **Extend** (related to tournaments)
- Adding email functionality → **Create new** EmailService (distinct responsibility)

---

### Decision: New UI Component vs Reuse Existing?

```
Check FRONTEND.md Component Library
├─ Component exists?
│  ├─ YES: Can it be reused as-is?
│  │  ├─ YES: Reuse component
│  │  │  └─ Follow FRONTEND.md patterns
│  │  └─ NO: Can it be extended with minor changes?
│  │     ├─ YES: Extend component
│  │     │  └─ Update FRONTEND.md
│  │     └─ NO: Create new component
│  │        └─ Document in FRONTEND.md
│  └─ NO: Create new component
│     └─ Ask user if custom design needed
│     └─ Document in FRONTEND.md
└─ End
```

**Examples:**
- Need a delete confirmation modal → **Reuse** (exists in FRONTEND.md)
- Need a custom battle scoreboard → **Create new** (domain-specific, unique)

---

### Decision: Sub-Phase vs Major Phase?

```
Is the work described in current ROADMAP.md?
├─ YES: Use existing phase number
│  └─ No ROADMAP update needed
└─ NO: Is it a major milestone change?
   ├─ NO (minor addition/fix):
   │  └─ Use sub-phase (X.1, X.2, X.3)
   │  └─ Example: Phase 1.1 (fixes), Phase 1.2 (consolidation)
   └─ YES (major feature):
      └─ Consider creating new major phase
      └─ Discuss with user first
      └─ Update ROADMAP.md
```

**When to use sub-phases:**
- Bug fixes discovered post-phase
- Documentation consolidation
- Minor enhancements
- Refactoring

**When to create new phases:**
- New major features (Battle Management was Phase 2)
- Significant system changes
- Major milestones (V1 → V2)

---

## Quality Gates Checklists

### Before Moving to Implementation

**Business Analysis Complete:**
- [ ] Business goal clearly identified
- [ ] Affected entities documented (read DOMAIN_MODEL.md)
- [ ] Affected services documented (read ARCHITECTURE.md)
- [ ] Required UI components identified (read FRONTEND.md)
- [ ] Missing components flagged for user discussion
- [ ] User clarifications obtained via AskUserQuestion

**Requirements Defined:**
- [ ] Functional requirements clear
- [ ] Non-functional requirements (performance, security, accessibility)
- [ ] Validation rules defined
- [ ] UI specifications complete (components, HTMX patterns, accessibility)
- [ ] Acceptance criteria written

**Technical Design Approved:**
- [ ] All affected files identified
- [ ] Backend patterns chosen (service, validation, repository)
- [ ] Frontend patterns chosen (components, HTMX, accessibility)
- [ ] Database changes planned (migrations, data migrations)
- [ ] Documentation updates planned (Level 1 → 2 → 3)
- [ ] Risks identified with mitigation plans

---

### Before Committing Code

**Code Quality:**
- [ ] All new code has tests (unit + integration)
- [ ] All existing tests pass (no regressions)
- [ ] No console errors/warnings
- [ ] Code follows architectural patterns (ARCHITECTURE.md, FRONTEND.md)
- [ ] Service layer has validation (ValidationResult pattern)
- [ ] Routers are thin (delegate to services)

**Frontend Quality (if UI changes):**
- [ ] UI uses FRONTEND.md components (not reinvented)
- [ ] HTMX patterns applied correctly
- [ ] Semantic HTML (nav, article, section, aside)
- [ ] ARIA attributes present (aria-label, aria-describedby)
- [ ] PicoCSS classes used (minimal custom CSS)
- [ ] Flash messages for user feedback
- [ ] Empty states for lists

**Accessibility (if UI changes):**
- [ ] Keyboard navigation works (tab through all elements)
- [ ] Screen reader tested (VoiceOver or NVDA)
- [ ] Color contrast meets WCAG 2.1 AA (4.5:1 text, 3:1 UI)
- [ ] Focus indicators visible

**Responsive (if UI changes):**
- [ ] Mobile tested (320px-768px)
- [ ] Tablet tested (769px-1024px)
- [ ] Desktop tested (1025px+)

---

### Before Deployment

**Pre-Deployment:**
- [ ] Integration tests pass
- [ ] Database migration tested (up and down)
- [ ] Rollback plan documented
- [ ] Documentation reflects changes
- [ ] CHANGELOG.md updated

**Deployment Verification:**
- [ ] Railway logs checked
- [ ] Smoke test critical flows
- [ ] No errors in production logs
- [ ] Performance acceptable

---

### Before Closing

**Closure Checklist:**
- [ ] Workbench file archived to archive/
- [ ] ROADMAP.md updated (phase marked complete)
- [ ] Git commit created with proper message
- [ ] User acceptance confirmed

---

## Common Mistakes Reference

### Architecture Violations

**❌ Business Logic in Routers**
```python
# BAD
@router.post("/battles/{id}/encode")
async def encode_battle(id: UUID, scores: dict):
    battle = await battle_repo.get(id)
    # Validation logic here ❌
    if not scores or len(scores) == 0:
        raise ValueError("No scores")
    # Business logic here ❌
    battle.outcome = scores
    await battle_repo.update(battle)
```

**✅ Business Logic in Services**
```python
# GOOD
@router.post("/battles/{id}/encode")
async def encode_battle(id: UUID, scores: dict, service: BattleService):
    result = await service.encode_battle_results(id, scores)
    if not result.success:
        # Handle validation errors
        pass
    return result
```

---

**❌ Skipping Service Layer**
```python
# BAD - Router directly calls repository
@router.get("/tournaments/active")
async def get_active(repo: TournamentRepository):
    return await repo.get_active()  # ❌ No business logic, validation
```

**✅ Using Service Layer**
```python
# GOOD - Router delegates to service
@router.get("/tournaments/active")
async def get_active(service: TournamentService):
    return await service.get_active_tournament()  # ✅ Service handles logic
```

---

**❌ Hardcoding Business Logic**
```python
# BAD
if performer_count < 4:  # ❌ Magic number, formula not clear
    raise ValidationError("Not enough performers")
```

**✅ Using Calculation Functions**
```python
# GOOD
from app.utils.tournament_calculations import calculate_minimum_performers

minimum = calculate_minimum_performers(groups_ideal)
if performer_count < minimum:
    raise ValidationError(f"Need {minimum - performer_count} more performers")
```

---

### Documentation Mistakes

**❌ Updating Code Before Docs**
```
1. Write code ❌
2. Test code
3. Update documentation ❌
```

**✅ Documentation-First Approach**
```
1. Create workbench file ✅
2. Update Level 1 docs (DOMAIN_MODEL, VALIDATION_RULES) ✅
3. Update Level 2 docs (ROADMAP, README) ✅
4. Update Level 3 docs (ARCHITECTURE, FRONTEND, TESTING) ✅
5. Verify with grep ✅
6. THEN write code ✅
```

---

**❌ Not Using Workbench**
```
Direct edits to:
- DOMAIN_MODEL.md ❌
- VALIDATION_RULES.md ❌
- ARCHITECTURE.md ❌
(No tracking, hard to verify consistency)
```

**✅ Using Workbench System**
```
1. Create workbench/CHANGE_2025-12-03_ADD_FEATURE.md ✅
2. Track all doc changes in workbench ✅
3. Verify consistency with grep ✅
4. Archive workbench when done ✅
```

---

### Frontend Mistakes

**❌ Reinventing Components**
```html
<!-- BAD - Custom modal when one exists -->
<div class="my-custom-modal">  <!-- ❌ Reinventing -->
  <div class="overlay"></div>
  <div class="content">...</div>
</div>
```

**✅ Reusing FRONTEND.md Components**
```html
<!-- GOOD - Use existing modal component -->
{% include "components/delete_modal.html" with context %}  <!-- ✅ Reuse -->
```

---

**❌ Skipping Accessibility**
```html
<!-- BAD -->
<div onclick="submit()">Submit</div>  <!-- ❌ Not keyboard accessible -->
<input type="text">  <!-- ❌ No label -->
```

**✅ Following Accessibility Guidelines**
```html
<!-- GOOD -->
<button type="submit">Submit</button>  <!-- ✅ Keyboard accessible -->
<label for="email">Email</label>  <!-- ✅ Proper label -->
<input type="email" id="email" name="email" aria-describedby="email-error">
```

---

### Testing Mistakes

**❌ Not Testing Edge Cases**
```python
# BAD - Only tests happy path
def test_create_pools():
    result = pool_service.create_pools(10, 2)
    assert len(result) == 2  # ❌ What about 3 performers? 5? 11?
```

**✅ Testing Edge Cases**
```python
# GOOD - Tests edge cases
@pytest.mark.parametrize("count,groups,expected", [
    (5, 2, [3, 2]),  # Minimum
    (10, 2, [5, 5]),  # Even distribution
    (11, 2, [6, 5]),  # Uneven distribution
    (3, 3, None),    # Not enough for pools (should fail)
])
def test_create_pools_edge_cases(count, groups, expected):
    # Test implementation
```

---

**❌ Forgetting Async Tests**
```python
# BAD
def test_get_active_tournament():  # ❌ Missing @pytest.mark.asyncio
    result = await service.get_active()  # ❌ SyntaxError
```

**✅ Proper Async Tests**
```python
# GOOD
@pytest.mark.asyncio  # ✅ Marks as async test
async def test_get_active_tournament():
    result = await service.get_active()  # ✅ Works
    assert result is not None
```

---

# PART 2: DEVELOPMENT LIFECYCLE

## 1. Business Analysis Phase

**Purpose:** Understand the business need before touching code

---

### Step 1: Understand the Problem (Pure Business - No Technical Context)

**1.1 Extract User Request Intent**
- What did the user ask for? (exact words)
- What problem are they trying to solve? (infer, then confirm)
- What triggered this request? (bug report, user feedback, new requirement)

**1.2 Identify the "Five Whys"**
- **Who** is affected? (users, staff, admins, stakeholders)
- **What** is the current pain point? (what's broken or missing)
- **When** does this problem occur? (workflow, frequency)
- **Where** in the user journey does this happen? (specific screens, processes)
- **Why** does this matter to the business? (impact: efficiency, revenue, satisfaction)

**Example:**
```
User Request: "Improve the battle queue"

Five Whys Analysis:
- WHO: Staff members managing tournaments
- WHAT: Staff waste time scrolling through long unfiltered battle lists
- WHEN: During tournament execution (pools/finals phases)
- WHERE: Battles list page when encoding results
- WHY: Staff report spending 30+ minutes finding battles to encode in tournaments with 50+ battles, causing delays
```

**1.3 Define Success Criteria (Business Perspective)**
- How will we know this solved the problem?
- What would make users say "this is better"?
- What metrics would improve? (time saved, errors reduced, satisfaction score)

**Example:**
```
Success Criteria:
- Staff can find any battle within 5 seconds (vs. current 30+ seconds)
- Time to encode all battles in a tournament reduced by 50%
- Staff satisfaction rating for battle encoding improves from 3/5 to 4.5/5
- Zero reports of "couldn't find the right battle"
```

**1.4 Create User Story with BDD-Style Acceptance Criteria**

**Format:**
```gherkin
Feature: [Feature name]
  As a [type of user]
  I want [capability]
  So that [business value]

Scenario: [Scenario name]
  Given [initial context/state]
  When [action taken]
  Then [expected outcome]
  And [additional expected outcome]

Scenario: [Alternative scenario]
  Given [different context]
  When [different action]
  Then [different outcome]
```

**Example 1: Battle Queue Improvements**
```gherkin
Feature: Battle Queue Filtering and Status Indicators
  As a staff member managing a tournament
  I want to filter battles by status and phase
  So that I can quickly find battles that need encoding

Scenario: Filter battles by encoding status
  Given I am on the battles list page
  And there are 50 battles in various states
  When I click the "Pending Encoding" filter
  Then I see only battles with status COMPLETED that have no outcome encoded
  And the battle count shows "12 pending encoding"
  And the list is sorted by completion time (oldest first)

Scenario: See visual status indicators
  Given I am viewing the battle list
  When battles have different encoding states
  Then pending battles show an orange "Needs Encoding" badge
  And encoded battles show a green "Encoded" badge
  And active battles show a blue "In Progress" badge
  And each badge has accessible aria-label for screen readers

Scenario: Quick access to encoding form
  Given I see a battle with "Needs Encoding" status
  When I click the "Encode" button on the battle card
  Then I am taken directly to the encoding form for that battle
  And the form is pre-populated with battle information
  And after submitting, I return to the filtered list (not full list)
```

**Example 2: New Feature - Judge Scoring Interface**
```gherkin
Feature: Judge Battle Scoring
  As a judge at a tournament
  I want to score battles independently on my device
  So that I can provide unbiased scores without seeing other judges' scores

Scenario: Judge logs in with temporary code
  Given I am a judge assigned to a tournament
  When I navigate to the judge portal
  And I enter my 6-digit access code
  Then I see a welcome screen with my name
  And I see a list of battles assigned to me
  And I do not see any other judges' scores

Scenario: Score a preselection battle
  Given I am logged in as a judge
  And I have a preselection battle assigned
  When I click on the battle
  Then I see performer names (in randomized order to prevent bias)
  And I see a score input for each performer (0.0 to 10.0)
  And I can enter scores with one decimal precision
  When I enter all scores and click "Submit"
  Then my scores are saved
  And I see a success message "Scores submitted for Battle #12"
  And the battle is marked as "Scored" in my list
  And I cannot edit my scores after submission

Scenario: Cannot see other judges' scores (blind scoring)
  Given I am logged in as a judge
  When I view any battle
  Then I only see my own scores (if I've scored)
  And I do not see scores from other judges
  And I do not see the average or aggregate score
  And the UI does not hint at how others scored

Scenario: System prevents incomplete scoring
  Given I am scoring a preselection battle with 3 performers
  When I enter scores for only 2 performers
  And I click "Submit"
  Then I see an error message "Please score all performers"
  And the missing score field is highlighted in red
  And my partial scores are preserved (not lost)
```

**1.5 Validate Understanding with User**

Use **AskUserQuestion** to:
- Confirm problem statement: "My understanding is [problem]. Is this correct?"
- Clarify ambiguous terms: "By 'improve battle queue' do you mean [A] or [B]?"
- Confirm scope: "This would affect [X, Y, Z]. Is that the scope you intended?"
- Present scenarios: "I wrote these scenarios - do they match your vision?"

**MANDATORY CHECKPOINT:** Cannot proceed until user confirms understanding.

---

### Step 2: Analyze Current System (As-Is) - Business Lens Only

**Purpose:** Understand what the system does TODAY from a business perspective, not how it's coded.

**2.1 Identify Affected Business Entities**

Read **DOMAIN_MODEL.md** to understand:
- What business concepts exist? (Tournament, Battle, Dancer, Category, Pool, etc.)
- What are their business definitions? (not technical fields, but what they represent)
- What relationships exist? (Tournament has Categories, Category has Performers, etc.)
- What workflows involve these entities? (lifecycle, state transitions)

**Questions to answer:**
- Which entities are involved in this problem?
- What can users currently do with these entities?
- What can't they do (that they want to)?

**Example (Business lens, not technical):**
```
Affected Entities:
- Battle: Represents a competition between 2+ performers
  - Current capabilities: Can be created, started, completed, encoded
  - Current limitations: No filtering, no status indicators
  - Lifecycle: PENDING → ACTIVE → COMPLETED

- Performer: A dancer competing in a battle
  - Current capabilities: Assigned to battles, receives scores
  - Relationship to Battle: Many-to-many (performers can be in multiple battles)

- Tournament: The event containing all battles
  - Current capabilities: Manages phases, tracks progress
  - Relationship to Battle: One tournament → many battles
```

**❌ Avoid technical lens:**
```
Battle model has:
- id: UUID
- status: Mapped[BattleStatus]
- outcome: JSON field
- performers: relationship with lazy loading
```

**2.2 Identify Current Business Rules & Constraints**

Read **VALIDATION_RULES.md** to understand:
- What validation rules exist today?
- What constraints limit user actions?
- What formulas/calculations are in place?
- Why do these rules exist? (business reason, not technical reason)

**Example (Business lens):**
```
Current Business Rules:
1. Battle Status Transitions:
   - Rule: Battles must be ACTIVE before results can be encoded
   - Reason: Prevents encoding results for battles that haven't occurred
   - Constraint: Staff must manually start each battle

2. Preselection Scoring:
   - Rule: Scores must be 0.0 to 10.0 with one decimal precision
   - Reason: Standardized scoring system for fair comparison
   - Constraint: All performers must receive a score (no partial scoring)

3. Pool Battle Outcomes:
   - Rule: Must have winner OR draw (mutually exclusive)
   - Reason: Points allocation requires clear outcome (win=3pts, draw=1pt)
   - Constraint: Cannot leave outcome blank

Current Gaps in Rules:
- No rule preventing duplicate encoding (staff could encode twice)
- No rule for battle ordering/sequencing
```

**2.3 Analyze Current User Experience (UI/Workflow)**

**Read FRONTEND.md Component Library** to understand:
- What UI components exist today?
- What patterns are established? (forms, tables, modals, navigation)
- What accessibility/responsive standards are in place?

**Navigate the system mentally** by reading templates (`app/templates/**/*.html`):
- What screens are involved in this workflow?
- What actions can users take? (buttons, forms, links)
- What feedback do users get? (success messages, errors, loading states)
- What's the current user journey? (step-by-step flow)

**Focus on user experience, not implementation:**

**Example (UX lens):**
```
Current Battle Encoding Workflow:

Step 1: Navigate to Battles
- Staff clicks "Battles" in sidebar
- Sees list of ALL battles (no filters)
- List shows: Phase, Status, Performers, Action buttons

Step 2: Find the Right Battle
- Staff must visually scan entire list
- No search functionality
- No filter by status/phase
- No indication which battles need encoding
- With 50+ battles, this takes 30+ seconds

Step 3: Click "Encode Results"
- Staff clicks button on battle card
- Redirects to encoding form
- Form shows battle details and input fields

Step 4: Submit Scores/Outcome
- Staff enters data
- Clicks "Submit"
- If valid: Success message + redirect to battle list
- If invalid: Error message + form preserved

Step 5: Return to List (repeat)
- Back at full unfiltered list
- Must find next battle to encode
- No indication of progress

Pain Points:
- Finding battles is tedious (no filter/search)
- No visual distinction between encoded/pending
- Must return to full list each time (context lost)
- No sense of progress (how many left?)
- No bulk or sequential encoding
```

**❌ Avoid technical lens:**
```
The battles/list.html uses Jinja2 for loop.
Battle cards use PicoCSS grid.
Encode form uses hx-post for HTMX.
```

**2.4 Identify Current Backend Business Logic (If Relevant)**

**Only if the problem involves business logic** (not just UI):

Read backend code (`app/services/*.py`, `app/routers/*.py`) to understand **WHAT** happens, not **HOW**:

**Example (Business logic lens):**
```
Current Battle Encoding Logic:

What Happens Automatically:
- System validates battle is in COMPLETED status
- System validates all required data is provided
- System updates battle outcome in single transaction
- System updates performer statistics (scores/wins/losses)
- System marks battle as encoded

What Requires Manual Action:
- Staff must manually navigate to each battle
- Staff must manually determine which battles need encoding
- Staff must manually start battles before encoding

Business Rules Enforced:
- Cannot encode PENDING or ACTIVE battles
- Cannot encode without complete data
- Cannot encode same battle twice (prevented by UI, not backend)

Current Gaps:
- No batch operations
- No battle ordering/sequencing logic
- No "next pending battle" navigation
```

**❌ Avoid technical lens:**
```
The BattleResultsEncodingService uses:
- encode_preselection_results() with ValidationResult pattern
- Async session with transaction management
- Repository pattern for data access
```

**2.5 Create Gap Analysis (Current vs Desired)**

Compare what you learned in Step 1 (problem) with Step 2 (current system):

**Example:**
```
GAP ANALYSIS: Battle Queue Improvements

Current State (As-Is):
- Battle list shows all battles without filters
- No visual indicators of encoding status
- Staff must manually find each battle to encode
- No search or filter functionality
- Return to full list after each encoding
- No progress tracking

Desired State (To-Be):
- Battle list has status filters (pending/encoded/active)
- Visual badges show encoding status clearly
- Staff can see "next pending battle" quickly
- Search by battle number or performer name
- Option to stay in encoding flow (sequential encoding)
- Progress indicator shows "12 of 50 encoded"

Gap (What's Missing):
- Filter/search UI components
- Status badge component
- Backend filtering logic
- Progress calculation
- Sequential encoding workflow
- "Next battle" navigation logic

Business Impact of Gap:
- Current: 30+ minutes to encode 50 battles
- Desired: 15 minutes to encode 50 battles
- Time saved: 50% reduction
- Frustration: High → Low
- Errors: "Wrong battle encoded" → Zero errors
```

---

### Step 3: Define Functional Requirements (Bridge to Technical)

**3.1 List "Must Have" Requirements (BDD Scenarios)**

Use the scenarios from Step 1.4 to derive concrete requirements:

**Example:**
```
Must Have:
- [ ] Filter battles by encoding status (Pending/Encoded/All)
- [ ] Filter battles by phase (Preselection/Pool/Tiebreak/Finals)
- [ ] Display status badge on each battle card
- [ ] Show battle count for each filter ("12 pending encoding")
- [ ] Encode button opens form for that specific battle
- [ ] After encoding, return to filtered view (preserve context)
- [ ] Display progress indicator ("12 of 50 encoded")

Derived from Scenarios:
✓ "Filter battles by encoding status" → Filter UI + backend filtering
✓ "See visual status indicators" → Status badge component
✓ "Quick access to encoding form" → Direct link from battle card
```

**3.2 List "Should Have" Requirements (Nice-to-Have)**

**Example:**
```
Should Have (if time permits):
- [ ] Search battles by battle number
- [ ] Search battles by performer name
- [ ] "Next pending battle" button (sequential workflow)
- [ ] Keyboard shortcuts (N for next, E for encode)
- [ ] Remember last filter selection (session persistence)
```

**3.3 List "Won't Have" (Out of Scope)**

**Example:**
```
Won't Have (explicitly excluded):
- Bulk encoding (encode multiple battles at once)
- Battle reordering (drag-and-drop sequencing)
- Export battle list to CSV
- Email notifications when battles are encoded
- Mobile app (web only)
```

---

### Step 4: Identify UI/UX Requirements (If User-Facing)

**4.1 Check Existing Components**

Read **FRONTEND.md Component Library**:
- What components already exist that we can reuse?
- What's missing?

**Example:**
```
Components to Reuse:
✓ Badges (status indicators) - exists in FRONTEND.md
✓ Buttons (primary, secondary) - exists
✓ Forms (encoding form) - exists
✓ Flash messages (success/error) - exists

Components Missing:
✗ Filter chips (clickable status filters)
✗ Battle count indicator
✗ Progress bar or indicator
```

**4.2 Identify HTMX Patterns Needed**

**Example:**
```
HTMX Patterns Needed:
- Live filtering: hx-get with hx-trigger on filter click
- Partial update: hx-swap="outerHTML" for battle list
- Preserve state: hx-push-url for filter state in URL
```

**4.3 Flag Missing Components for Discussion**

Use **AskUserQuestion** to discuss design for missing components:

**Example:**
```
Question: "How should we display battle encoding progress?"

Options:
1. Progress bar - "24 of 50 encoded" with visual bar
2. Simple text count - "24 / 50 battles encoded"
3. Percentage badge - "48% encoded" badge
4. Both bar + percentage
```

---

### Step 5: Ask Clarifying Questions (Mandatory if Any Ambiguity)

**When to ask (mandatory):**
- Multiple valid interpretations of user request
- Business impact is unclear
- Success criteria are vague
- Scope is ambiguous (what's included vs excluded)
- Gap analysis reveals complexity
- Missing UI component needs design decision
- BDD scenarios have unclear outcomes

**How to ask:**
Use **AskUserQuestion** with:
- **Clear question**: Specific, actionable
- **Context**: Why you're asking (what you're trying to clarify)
- **Options**: 2-4 choices with tradeoffs explained
- **Recommendation**: What you'd suggest and why (based on As-Is analysis)

**Example:**
```
Question: "Should filtered view persist when returning from encoding form?"

Context: "Currently staff lose filter context and return to full list. Based on As-Is analysis, this is a major pain point."

Options:
1. Persist filter in URL params
   - Pros: Works with browser back button, shareable URLs
   - Cons: Slightly more complex implementation

2. Persist filter in session
   - Pros: Simpler implementation
   - Cons: Lost on browser refresh, not shareable

3. Don't persist (return to "All")
   - Pros: Simplest implementation
   - Cons: Doesn't solve the pain point

Recommendation: Option 1 (URL params) - solves the root problem and provides better UX
```

---

### Deliverable: Business Requirements Document

**Format:**
```markdown
# Business Analysis: [Feature Name]

## 1. Problem Statement
[1-2 sentences describing the problem from business perspective]

## 2. User Story & BDD Scenarios

Feature: [Feature name]
  As a [type of user]
  I want [capability]
  So that [business value]

Scenario: [Scenario name]
  Given [initial context]
  When [action taken]
  Then [expected outcome]
  And [additional outcome]

[Additional scenarios...]

## 3. Success Criteria (Business)
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [User satisfaction metric]

## 4. As-Is Analysis

### 4.1 Current Business Entities
- Entity 1: [what it represents, current capabilities, limitations]
- Entity 2: [relationships, lifecycle]

### 4.2 Current Business Rules
- Rule 1: [from VALIDATION_RULES.md - why it exists]
- Rule 2: [constraints, formulas]

### 4.3 Current User Experience
**Current Workflow:**
[Step-by-step current user journey with pain points]

**Current Components:**
[What exists in FRONTEND.md]

### 4.4 Current Business Logic
- [What system does automatically]
- [What requires manual intervention]
- [What constraints are enforced]

### 4.5 Gap Analysis
**Current State:** [what exists today]
**Desired State:** [what's needed per user story]
**Gap:** [what's missing/broken]
**Business Impact:** [time/cost/satisfaction impact]

## 5. Functional Requirements

### Must Have (from BDD scenarios):
- [ ] Requirement 1
- [ ] Requirement 2

### Should Have:
- [ ] Nice-to-have 1

### Won't Have (Out of Scope):
- Explicitly excluded item

## 6. UI/UX Requirements

### Components to Reuse:
- Existing: [list from FRONTEND.md]

### Components Missing:
- New: [flagged for design discussion]

### HTMX Patterns:
- Pattern 1: [which pattern from FRONTEND.md]

### Workflow Changes:
- [How the user journey will change]

## 7. Open Questions & Answers
- [ ] Question 1 asked via AskUserQuestion
  - Answer: [user's response]
- [ ] Question 2 asked via AskUserQuestion
  - Answer: [user's response]

## 8. User Confirmation
- [ ] User confirmed problem statement
- [ ] User validated BDD scenarios
- [ ] User confirmed gap analysis
- [ ] User confirmed scope (Must/Should/Won't)
- [ ] User approved approach
```

**Example Deliverable:**
```markdown
# Business Analysis: Battle Queue Status Filtering

## 1. Problem Statement
Staff waste 30+ minutes finding battles to encode in tournaments with 50+ battles due to lack of filtering and status indicators, causing tournament delays and frustration.

## 2. User Story & BDD Scenarios

Feature: Battle Queue Filtering and Status Indicators
  As a staff member managing a tournament
  I want to filter battles by encoding status
  So that I can quickly find battles that need my attention

Scenario: Filter battles by encoding status
  Given I am on the battles list page
  And there are 50 battles in various states
  When I click the "Pending Encoding" filter
  Then I see only battles with status COMPLETED that have no outcome encoded
  And the battle count shows "12 pending encoding"
  And the list is sorted by completion time (oldest first)

Scenario: See visual status indicators
  Given I am viewing the battle list
  When battles have different encoding states
  Then pending battles show an orange "Needs Encoding" badge
  And encoded battles show a green "Encoded" badge
  And each badge has accessible aria-label

## 3. Success Criteria
- [ ] Staff can find any battle within 5 seconds (vs current 30+ seconds)
- [ ] Time to encode all battles reduced by 50%
- [ ] Zero reports of "couldn't find the right battle"

## 4. As-Is Analysis

### 4.1 Current Business Entities
- Battle: Competition between performers
  - Capabilities: Create, start, complete, encode
  - Limitations: No status-based filtering
  - Lifecycle: PENDING → ACTIVE → COMPLETED

### 4.2 Current Business Rules
- Battles must be COMPLETED before encoding
- All performers must receive scores
- Winner OR draw required (mutually exclusive)

### 4.3 Current User Experience
**Current Workflow:**
1. Navigate to Battles page → see ALL battles
2. Manually scan list to find pending battles (30+ seconds)
3. Click "Encode Results" → redirected to form
4. Submit → return to FULL unfiltered list
5. Repeat process (context lost)

**Pain Points:**
- No filters/search
- No status indicators
- Context lost after encoding
- No progress tracking

### 4.4 Current Business Logic
- System validates battle status before encoding
- System updates battle + performer stats transactionally
- No batch operations
- No "next pending" logic

### 4.5 Gap Analysis
**Current State:** Unfiltered list, manual search, 30+ min for 50 battles
**Desired State:** Filtered by status, visual indicators, 15 min for 50 battles
**Gap:** Filter UI, status badges, progress tracking, context preservation
**Business Impact:** 50% time reduction, zero encoding errors

## 5. Functional Requirements

### Must Have:
- [ ] Filter by encoding status (Pending/Encoded/All)
- [ ] Status badges on battle cards
- [ ] Battle count per filter
- [ ] Preserve filter context after encoding
- [ ] Progress indicator

### Should Have:
- [ ] Search by battle number
- [ ] "Next pending battle" button

### Won't Have:
- Bulk encoding
- Battle reordering

## 6. UI/UX Requirements

### Components to Reuse:
- Badges (status indicators) - exists
- Buttons - exists
- Forms - exists

### Components Missing:
- Filter chips (clickable filters) - need design

### HTMX Patterns:
- Live filtering with partial update
- URL state preservation

## 7. Open Questions & Answers
- [x] Should filter persist on return from encoding?
  - Answer: Yes, use URL params

## 8. User Confirmation
- [x] User confirmed problem statement
- [x] User validated BDD scenarios
- [x] User confirmed must-have requirements
- [x] User approved approach
```

---

### Quality Gate (BLOCKING)

**Cannot proceed to Requirements Definition or Technical Design until:**

**Problem Understanding:**
- [ ] Problem statement written in business terms (not technical)
- [ ] User story created with "As a / I want / So that" format
- [ ] BDD scenarios written with Given/When/Then format
- [ ] Success criteria defined (measurable outcomes)
- [ ] User confirmed understanding of problem

**As-Is Analysis Complete:**
- [ ] Affected business entities identified (from DOMAIN_MODEL.md)
- [ ] Current business rules documented (from VALIDATION_RULES.md)
- [ ] Current user experience analyzed (workflow, pain points)
- [ ] Current business logic understood (what system does today)
- [ ] Gap analysis completed (current vs desired with business impact)

**Requirements Defined:**
- [ ] Functional requirements derived from BDD scenarios
- [ ] Must/Should/Won't clearly separated
- [ ] UI components identified or flagged (from FRONTEND.md)
- [ ] All ambiguities resolved via AskUserQuestion

**User Validation:**
- [ ] User validated BDD scenarios match their vision
- [ ] User confirmed scope (must/should/won't)
- [ ] User approved approach

**If any checkbox is empty, STOP and complete that step.**

---

### Common Mistakes to Avoid

**❌ Jumping to Technical Details:**
```
BAD: "We'll add a filter_by_status() method to BattleRepository"
GOOD: "Staff need to see only battles that haven't been encoded yet"
```

**❌ Vague Acceptance Criteria:**
```
BAD: "System should be faster"
GOOD: "Staff can find any battle within 5 seconds"
```

**❌ Skipping Gap Analysis:**
```
BAD: Reading code and proposing changes without understanding current workflow
GOOD: Document current workflow → identify pain points → propose improvements
```

**❌ Not Using BDD Format:**
```
BAD: "Add filter feature"
GOOD:
  Given I am on the battles list
  When I click "Pending Encoding" filter
  Then I see only unencoded battles
```

**❌ Mixing Business and Technical:**
```
BAD: "Add hx-get endpoint for filtering"
GOOD: "Staff can filter battles by status with one click"
```

---

## 2. Requirements Definition Phase

**Purpose:** Translate business need to concrete specifications

### Steps

**2.1 Define Functional Requirements**
- What must the system do?
- User flows/workflows
- Input/output specifications
- UI interactions (forms, tables, modals, navigation)

**2.2 Define Non-Functional Requirements**
- Performance constraints
- Scalability needs
- Security requirements
- **Accessibility requirements** (WCAG 2.1 AA per FRONTEND.md)
- **Responsive behavior** (mobile-first per FRONTEND.md)

**2.3 Define Validation Rules**
- Business constraints
- Data validation requirements (check VALIDATION_RULES.md for existing patterns)
- UI validation (field-level, form-level)
- Will these go in VALIDATION_RULES.md? (if domain rules, yes)

**2.4 Define UI Specifications** (if user-facing)
- Which components from FRONTEND.md Component Library?
- Custom components needed? (if so, document why standard components insufficient)
- HTMX patterns needed?
  - Live search with debounce
  - Form submission with partial update
  - Inline validation
  - Polling/auto-refresh
- Accessibility considerations (keyboard nav, screen readers, ARIA attributes)
- Responsive behavior (mobile, tablet, desktop breakpoints)

**2.5 Create Acceptance Criteria**
- How will we know it's done?
- What tests must pass?
- UI acceptance criteria:
  - Accessibility tested? (keyboard, screen reader)
  - Responsive tested? (mobile, tablet, desktop)
  - HTMX patterns working?

### Deliverable

Requirements specification document with:
- Functional requirements
- Non-functional requirements
- Validation rules
- UI specifications
- Acceptance criteria

### Quality Gate

- [ ] Functional requirements clear
- [ ] Validation rules defined
- [ ] UI components specified (or reused from FRONTEND.md)
- [ ] Accessibility requirements documented
- [ ] Acceptance criteria complete

---

## 3. Technical Design Phase

**Purpose:** Plan the implementation approach

### Steps

**3.1 Identify Affected Files/Components**
- Which models need changes? (`app/models/*.py`)
- Which services need changes? (`app/services/*.py`)
- Which repositories need changes? (`app/repositories/*.py`)
- Which routes need changes? (`app/routers/*.py`)
- Which templates need changes? (`app/templates/**/*.html`)
- Which frontend components? (from FRONTEND.md Component Library)

**3.2 Choose Architectural Patterns**

**Backend patterns:**
- Service Layer needed? (usually yes for business logic)
- Validation pattern? (use ValidationResult from ARCHITECTURE.md)
- New repository methods?
- Exception handling (ValidationError, IntegrityError)

**Frontend patterns** (check FRONTEND.md):
- Which HTMX patterns?
  - Live search: `hx-get` + `hx-trigger="keyup changed delay:500ms"`
  - Form submission: `hx-post` + `hx-swap="outerHTML"`
  - Inline validation: `hx-get` + `hx-target="#error-message"`
  - Polling/auto-refresh: `hx-get` + `hx-trigger="every 10s"`
- Components to reuse from FRONTEND.md or create new?
- Custom CSS needed? (minimize, prefer PicoCSS)
- Custom JavaScript needed? (minimize, prefer HTMX)

**3.3 Plan Database Changes**
- New tables/columns?
- Alembic migration needed?
- Data migration needed? (update existing records)
- Indexes needed for performance?

**3.4 Plan Frontend Implementation** (if UI changes)
- Which components to reuse? (check FRONTEND.md Component Library)
- Which HTMX patterns to apply? (check FRONTEND.md HTMX Patterns section)
- Custom CSS needed? (minimize, prefer PicoCSS utility classes)
- Custom JavaScript needed? (minimize, prefer HTMX declarative approach)
- Accessibility plan:
  - Keyboard navigation (tab order, focus management)
  - ARIA attributes (labels, descriptions, states)
  - Screen reader considerations
- Responsive strategy:
  - Mobile (320px-768px): Stack vertically, full-width buttons
  - Tablet (769px-1024px): 2-column layouts where appropriate
  - Desktop (1025px+): Multi-column, sidebar navigation

**3.5 Plan Documentation Updates**

**Level 1: Source of Truth**
- DOMAIN_MODEL.md (if entities change)
- VALIDATION_RULES.md (if validation rules change)

**Level 2: Derived**
- ROADMAP.md (if new phase/sub-phase)
- README.md (if major feature change)

**Level 3: Operational**
- ARCHITECTURE.md (if new backend pattern)
- FRONTEND.md (if new UI component or pattern)
- TESTING.md (if new test approach)

**3.6 Identify Risks**
- Breaking changes? (will existing code break?)
- Performance concerns? (N+1 queries, large datasets)
- Complexity concerns? (too complex for maintenance?)
- Accessibility risks? (new interaction patterns untested)
- Browser compatibility? (HTMX features, CSS Grid support)

### Deliverable

Technical design document with:
- List of affected files
- Backend patterns chosen
- Frontend patterns chosen
- Database changes planned
- Documentation updates planned
- Risks identified with mitigation strategies

### Quality Gate

- [ ] All affected files identified
- [ ] Backend patterns chosen (service, validation, repository)
- [ ] Frontend patterns chosen (components, HTMX, accessibility)
- [ ] Documentation updates planned
- [ ] Risks identified and mitigation planned

---

## 4. Documentation Phase

**Purpose:** Update documentation FIRST (before writing code)

### Steps

**4.1 Create Workbench File**

Follow **DOCUMENTATION_CHANGE_PROCEDURE.md**:

Format: `workbench/CHANGE_YYYY-MM-DD_TOPIC.md`

Example: `workbench/CHANGE_2025-12-03_ADD_JUDGE_INTERFACE.md`

**4.2 Update Level 1 Docs** (Source of Truth)

**DOMAIN_MODEL.md:**
- Add/update entity definitions
- Update business rules
- Update workflows

**VALIDATION_RULES.md:**
- Add/update validation rules
- Update formulas
- Update constraints

**4.3 Update Level 2 Docs** (Derived)

**ROADMAP.md** (if new phase):
- Add phase section
- Document objectives, deliverables, status

**README.md** (if major change):
- Update feature list
- Update quick start if needed

**4.4 Update Level 3 Docs** (Operational)

**ARCHITECTURE.md** (if new backend pattern):
- Document new service pattern
- Document new validation approach
- Add examples

**FRONTEND.md** (if new UI component or pattern):
- Add to Component Library section
- Document HTMX pattern if new
- Update accessibility guidelines if needed

**TESTING.md** (if new test approach):
- Document new test pattern
- Add examples

**4.5 Verify with Grep**

Check consistency across all docs:
```bash
# Search for entity name across all docs
grep -r "EntityName" *.md

# Search for validation rule references
grep -r "minimum_performers" *.md
```

Ensure:
- No orphaned references
- Consistent terminology
- Cross-references valid

### Deliverable

Updated documentation + workbench file tracking all changes

### Quality Gate

- [ ] Workbench file created
- [ ] Level 1 docs updated (DOMAIN_MODEL, VALIDATION_RULES)
- [ ] Level 2 docs updated if needed (ROADMAP, README)
- [ ] Level 3 docs updated if needed (ARCHITECTURE, FRONTEND, TESTING)
- [ ] Grep verification complete (no orphaned references)

---

## 5. Implementation Phase

**Purpose:** Write the code following established patterns

### Steps

**5.1 Create TodoWrite Task List**

Use **TodoWrite** tool to create task list:
- Break work into concrete steps
- One task per file/component
- Mark one task as `in_progress` at a time
- Mark tasks `completed` immediately when done

Example:
```
- Create Alembic migration for Judge table
- Add Judge model to app/models/judge.py
- Add JudgeRepository to app/repositories/judge.py
- Add JudgeService to app/services/judge_service.py
- Add judge routes to app/routers/judges.py
- Create judge templates
- Write unit tests for JudgeService
- Write integration tests for judge routes
```

**5.2 Database Changes First**

**Write Alembic migration:**
```bash
alembic revision --autogenerate -m "Add judge table"
```

**Review migration file:**
- Check column types
- Check constraints (unique, foreign keys, not null)
- Check indexes

**Test migration:**
```bash
alembic upgrade head  # Test up
alembic downgrade -1  # Test down
alembic upgrade head  # Back to current
```

**Update models:**
- Add model class to `app/models/`
- Follow SQLAlchemy 2.0 async patterns
- Add relationships if needed

**Update repositories:**
- Add CRUD methods to repository
- Use async/await
- Handle exceptions

**5.3 Service Layer Changes**

Follow **Service Layer Pattern** (ARCHITECTURE.md):

**Implement business logic:**
```python
class ExampleService:
    def __init__(self, repo: ExampleRepository):
        self.repo = repo

    async def create_example(self, data: ExampleCreate) -> ValidationResult[Example]:
        # Validation
        errors = []
        if not data.name:
            errors.append("Name is required")

        if errors:
            return ValidationResult(success=False, errors=errors)

        # Business logic
        example = Example(**data.dict())
        created = await self.repo.create(example)

        return ValidationResult(success=True, data=created)
```

**Add validation (ValidationResult pattern):**
- Return `ValidationResult[T]` from service methods
- Collect errors in list
- Return success=True with data, or success=False with errors

**Handle exceptions:**
- Catch `IntegrityError` → convert to `ValidationError`
- Provide user-friendly error messages
- Log technical errors, show business errors to user

**5.4 Router Changes**

Follow **Router Pattern** (ARCHITECTURE.md):

**Keep routers thin:**
```python
@router.post("/examples")
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends(get_example_service)
):
    result = await service.create_example(data)

    if not result.success:
        # Add flash message for errors
        flash(request, "error", "; ".join(result.errors))
        return templates.TemplateResponse("examples/create.html", {
            "request": request,
            "errors": result.errors
        })

    flash(request, "success", "Example created successfully")
    return RedirectResponse("/examples", status_code=303)
```

**Delegate to services:**
- Router handles HTTP concerns (request, response)
- Service handles business logic
- No validation or business logic in router

**5.5 Frontend Implementation** (if UI changes)

**Use FRONTEND.md Component Library (don't reinvent):**
- Check Component Library section
- Reuse existing components (forms, tables, modals, badges, etc.)
- Only create custom components when necessary

**Follow Design Principles (FRONTEND.md):**

**Minimalism:**
- Remove unnecessary elements
- Use whitespace instead of borders
- Clean visual hierarchy

**Accessibility (WCAG 2.1 AA):**
- Keyboard navigation (all interactive elements accessible via keyboard)
- Screen readers (semantic HTML, ARIA attributes)
- Color contrast (4.5:1 text, 3:1 UI components)
- Focus indicators (visible focus states)

**Mobile-first:**
- Design for 320px first
- Enhance for tablet (769px+)
- Enhance for desktop (1025px+)

**Progressive enhancement:**
- Works without JavaScript
- Enhanced with HTMX
- Custom JS only when necessary

**Apply HTMX Patterns (FRONTEND.md HTMX Patterns section):**

**Live search:**
```html
<input
  type="search"
  name="q"
  hx-get="/dancers/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#search-results"
>
<div id="search-results"></div>
```

**Form submission with partial update:**
```html
<form
  hx-post="/examples/create"
  hx-swap="outerHTML"
  hx-target="#form-container"
>
  <!-- form fields -->
</form>
```

**Inline validation:**
```html
<input
  type="email"
  name="email"
  hx-post="/validate/email"
  hx-trigger="blur"
  hx-target="#email-error"
>
<div id="email-error"></div>
```

**Use Semantic HTML:**
```html
<nav>...</nav>           <!-- Navigation -->
<article>...</article>   <!-- Independent content -->
<section>...</section>   <!-- Thematic grouping -->
<aside>...</aside>       <!-- Sidebar content -->
```

**Add ARIA attributes:**
```html
<label for="email">Email</label>
<input
  type="email"
  id="email"
  name="email"
  aria-describedby="email-error"
  aria-invalid="true"
>
<small id="email-error" role="alert">Invalid email format</small>
```

**Use PicoCSS classes (minimize custom CSS):**
- PicoCSS provides semantic styling automatically
- Use utility classes when needed
- Avoid custom CSS unless necessary

**Add flash messages:**
```python
from app.utils.flash import flash

flash(request, "success", "Operation successful")
flash(request, "error", "Operation failed")
flash(request, "warning", "Warning message")
flash(request, "info", "Information message")
```

**Add empty states:**
```html
{% if items %}
  <!-- Display items -->
{% else %}
  {% include "components/empty_state.html" with
    title="No items found",
    message="Get started by creating your first item."
  %}
{% endif %}
```

**5.6 Follow Architecture Patterns**

**Backend (ARCHITECTURE.md):**
- Service Layer Pattern (business logic in services)
- Validation Pattern (ValidationResult)
- Router Pattern (thin routers)
- Repository Pattern (data access)

**Frontend (FRONTEND.md):**
- Component Library (reuse components)
- HTMX Patterns (declarative AJAX)
- Accessibility Guidelines (WCAG 2.1 AA)
- Responsive Design (mobile-first)

**Avoid common pitfalls:**
- No business logic in routers
- No skipping service layer
- No hardcoded values (use calculation functions)
- No reinventing UI components
- No skipping accessibility

### Deliverable

Working code following established patterns

### Quality Gate

- [ ] Database migration tested (up and down)
- [ ] Service layer has validation (ValidationResult pattern)
- [ ] Routers are thin (delegate to services)
- [ ] UI uses FRONTEND.md components (not reinvented)
- [ ] HTMX patterns applied correctly
- [ ] Semantic HTML used
- [ ] ARIA attributes present
- [ ] PicoCSS used (minimal custom CSS)
- [ ] Flash messages implemented
- [ ] Empty states implemented
- [ ] Accessibility tested (keyboard nav, screen reader)
- [ ] Responsive tested (mobile, tablet, desktop)
- [ ] Code follows architectural patterns

---

## 6. Testing Phase

**Purpose:** Verify implementation works correctly

### Steps

**6.1 Write Unit Tests**

Follow **TESTING.md** patterns:

**Service layer tests:**
```python
@pytest.mark.asyncio
async def test_create_example_success(example_repository):
    service = ExampleService(example_repository)
    data = ExampleCreate(name="Test", value=10)

    result = await service.create_example(data)

    assert result.success
    assert result.data.name == "Test"
    assert result.data.value == 10
```

**Validation tests:**
```python
@pytest.mark.asyncio
async def test_create_example_validation_error(example_repository):
    service = ExampleService(example_repository)
    data = ExampleCreate(name="", value=10)  # Empty name

    result = await service.create_example(data)

    assert not result.success
    assert "Name is required" in result.errors
```

**Repository tests:**
```python
@pytest.mark.asyncio
async def test_repository_create(async_session):
    repo = ExampleRepository(async_session)
    example = Example(name="Test", value=10)

    created = await repo.create(example)

    assert created.id is not None
    assert created.name == "Test"
```

**6.2 Write Integration Tests**

**Route tests (with AsyncClient):**
```python
@pytest.mark.asyncio
async def test_create_example_route(async_client):
    response = await async_client.post("/examples", json={
        "name": "Test",
        "value": 10
    })

    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

**Full workflow tests:**
```python
@pytest.mark.asyncio
async def test_complete_workflow(async_client):
    # Create
    create_response = await async_client.post("/examples", json={...})
    example_id = create_response.json()["id"]

    # Read
    get_response = await async_client.get(f"/examples/{example_id}")
    assert get_response.status_code == 200

    # Update
    update_response = await async_client.put(f"/examples/{example_id}", json={...})
    assert update_response.status_code == 200

    # Delete
    delete_response = await async_client.delete(f"/examples/{example_id}")
    assert delete_response.status_code == 204
```

**HTMX interaction tests:**
```python
@pytest.mark.asyncio
async def test_htmx_live_search(async_client):
    response = await async_client.get(
        "/dancers/search?q=john",
        headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert "john" in response.text.lower()
```

**6.3 Accessibility Testing** (if UI changes)

Use **FRONTEND.md Accessibility Guidelines** as checklist:

**Keyboard navigation:**
- [ ] Tab through all interactive elements
- [ ] Enter/Space activates buttons/links
- [ ] Escape closes modals/dialogs
- [ ] Arrow keys work in select/radio groups
- [ ] Focus order is logical

**Screen reader testing:**
- [ ] Test with VoiceOver (macOS) or NVDA (Windows)
- [ ] All images have alt text
- [ ] Form fields have labels
- [ ] Error messages are announced
- [ ] Status updates are announced (aria-live)

**ARIA attributes:**
- [ ] aria-label on icons/buttons without text
- [ ] aria-describedby links fields to error messages
- [ ] aria-invalid on fields with validation errors
- [ ] role="alert" on error messages
- [ ] aria-current on current page nav link

**Color contrast:**
- [ ] Text contrast ≥ 4.5:1
- [ ] UI component contrast ≥ 3:1
- [ ] Test with browser DevTools contrast checker

**Focus indicators:**
- [ ] Focus visible on all interactive elements
- [ ] Focus ring not removed with CSS
- [ ] Focus order follows visual order

**6.4 Responsive Testing** (if UI changes)

Test on different viewport sizes:

**Mobile (320px-768px):**
- [ ] Content stacks vertically
- [ ] Buttons are full-width or properly sized
- [ ] Text is readable (min 16px)
- [ ] Touch targets ≥ 44x44px
- [ ] Sidebar collapses or becomes top nav
- [ ] Tables scroll horizontally or transform

**Tablet (769px-1024px):**
- [ ] 2-column layouts work
- [ ] Sidebar visible or easily accessible
- [ ] Forms use optimal width (max 600px)

**Desktop (1025px+):**
- [ ] Multi-column layouts work
- [ ] Sidebar navigation visible
- [ ] Content doesn't stretch too wide
- [ ] Proper use of whitespace

**Testing tools:**
- Chrome DevTools device emulation
- Responsive Design Mode (Firefox)
- Actual devices (phone, tablet) if available

**6.5 Run Existing Tests**

Ensure no regressions:
```bash
pytest
```

Expected: All 97+ tests pass

**Fix any broken tests:**
- Identify failures
- Update tests to match new behavior
- Don't just make tests pass—understand why they failed

**6.6 Manual Testing**

**Test UI flows:**
- Happy path (everything works correctly)
- Error paths (validation errors, missing data)
- Edge cases (empty lists, maximum values, etc.)

**Test edge cases:**
- Empty states (no data in lists)
- Loading states (slow network, large datasets)
- Error states (validation errors, server errors)

**Test error handling:**
- Validation errors display correctly
- Flash messages appear and dismiss
- Form fields show errors below them

**Test HTMX interactions:**
- Live search debounces correctly (no request on every keystroke)
- Partial updates work (only target element changes)
- Form submissions update correctly
- Polling/auto-refresh works

**6.7 Coverage Check**

Run coverage report:
```bash
pytest --cov=app --cov-report=html
```

**Coverage targets:**
- Overall: ≥ 90%
- Critical paths: 100% (authentication, validation, data integrity)

**Review uncovered lines:**
- Are they error handling that's hard to trigger?
- Are they truly unreachable code?
- Add tests to cover critical paths

### Deliverable

Passing test suite with accessibility and responsive verification

### Quality Gate

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Keyboard navigation works (if UI changes)
- [ ] Screen reader tested (if UI changes)
- [ ] ARIA attributes correct (if UI changes)
- [ ] Color contrast meets WCAG 2.1 AA (if UI changes)
- [ ] Focus indicators visible (if UI changes)
- [ ] Responsive on mobile/tablet/desktop (if UI changes)
- [ ] No regressions (existing tests pass)
- [ ] Coverage targets met (90%+ overall, 100% critical paths)
- [ ] Manual testing complete

---

## 7. Deployment Phase

**Purpose:** Release to production safely

### Steps

**7.1 Run Database Migration**

```bash
# On Railway (automatic via start.sh)
# Or manual:
alembic upgrade head
```

**Verify migration:**
- Check Railway logs for migration success
- Verify database schema matches expected
- Ensure no errors in logs

**7.2 Deploy Code**

**Railway auto-deploys on merge to main:**
- Merge PR to main branch
- Railway detects push
- Runs build
- Runs `start.sh` (migrations + seed + server)
- Deploys new version

**Or manual deployment:**
```bash
railway up
```

**7.3 Verify Deployment**

**Check Railway logs:**
```bash
railway logs
```

Look for:
- Migration success messages
- Server start messages
- No error stack traces

**Smoke test critical flows:**
- Login works
- Can create/edit entities
- Can navigate pages
- No console errors (browser DevTools)

**7.4 Monitor**

**Watch for errors:**
- Railway logs (first 24 hours)
- User reports
- Performance issues

**Check performance:**
- Page load times acceptable
- Database queries not slow (check Railway metrics)
- No memory leaks (check Railway resource usage)

### Deliverable

Live feature in production

### Quality Gate

- [ ] Database migration successful
- [ ] Deployment successful (no errors in logs)
- [ ] Smoke tests pass
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Monitoring in place

---

## 8. Closure Phase

**Purpose:** Complete the development cycle properly

### Steps

**8.1 Update CHANGELOG.md**

Document what changed:
```markdown
## [2025-12-03] - Feature: Judge Interface

### Added
- Judge user role and authentication
- Judge scoring interface for battles
- Blind scoring (judges can't see other scores)
- Admin aggregation view for all judge scores

### Changed
- Battle model now stores individual judge scores
- Preselection phase uses judge scores instead of staff encoding

### Fixed
- N/A

**Files Modified:**
- app/models/judge.py (new)
- app/services/judge_service.py (new)
- app/routers/judges.py (new)
- 15 other files...

**Tests Added:**
- tests/test_judge_service.py (18 tests)
- tests/test_judge_routes.py (12 tests)
```

**8.2 Archive Workbench File**

Move to archive/:
```bash
mv workbench/CHANGE_2025-12-03_ADD_JUDGE_INTERFACE.md archive/
```

**8.3 Update ROADMAP.md**

Mark phase/feature as complete:
```markdown
## Phase 6: Judge Interface (V2)

**Status:** ✅ COMPLETE

**Completed:** 2025-12-03

**Deliverables:**
- ✅ Judge model and authentication
- ✅ Judge scoring interface
- ✅ Blind scoring enforcement
- ✅ Admin aggregation view
```

**8.4 Create Git Commit**

Follow commit message guidelines:

```bash
git add .
git commit -m "$(cat <<'EOF'
feat: Add judge interface for V2

Implement complete judge workflow:
- Judges can score battles independently (blind scoring)
- Admin can view all scores and aggregate results
- Battle model stores individual judge scores
- Preselection uses judge scores instead of staff encoding

Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Commit message format:**
```
<type>: <subject>

<body>

<footer>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- test: Test additions/changes
- chore: Build/tooling changes

### Deliverable

Closed development cycle with all artifacts updated

### Quality Gate

- [ ] CHANGELOG.md updated
- [ ] Workbench file archived
- [ ] ROADMAP.md updated
- [ ] Git commit created with proper message
- [ ] User acceptance confirmed

---

# PART 3: PROJECT MANAGEMENT

## Phase Planning

### When to Create Sub-Phases vs Major Phases

**Use Sub-Phases (X.1, X.2, X.3) when:**
- Bug fixes discovered post-phase
- Documentation consolidation
- Minor enhancements to existing features
- Refactoring without new features
- Performance optimizations

**Examples:**
- Phase 1.1: Fixes and Enhancements
- Phase 1.2: Documentation Consolidation
- Phase 2.1: Battle Encoding Improvements

**Create New Major Phases when:**
- Significant new feature (Battle Management, Judge Interface)
- Major architectural changes
- Version milestones (V1, V2)
- Major workflow changes

**Examples:**
- Phase 2: Battle Management + Preselection Logic
- Phase 6: Judge Interface (V2)

### Roadmap Phase Management

**From DOCUMENTATION_CHANGE_PROCEDURE.md:**

```
Is the work in the current ROADMAP.md?
├─ YES: Use existing phase number
│  └─ No ROADMAP update needed (work already planned)
└─ NO: Is it a major milestone change?
   ├─ NO (minor addition/fix):
   │  └─ Use next sub-phase number (e.g., 1.3, 1.4, 2.1)
   │  └─ Add section to ROADMAP.md under current phase
   └─ YES (major feature):
      └─ Discuss with user before creating new major phase
      └─ Add new phase section to ROADMAP.md
```

### Phase Numbering Convention

**Major phases:** Integer numbers (1, 2, 3, 4, 5, 6...)
**Sub-phases:** Decimal numbers (1.1, 1.2, 2.1, 2.2...)

**Sequential numbering:**
- Major phases increment: 1 → 2 → 3
- Sub-phases increment within major phase: 1.1 → 1.2 → 1.3

**Don't skip numbers:**
- Always use next sequential number
- Don't create gaps (no Phase 1, 3, 5)

---

## Stakeholder Communication

### When to Use AskUserQuestion Tool

**Use AskUserQuestion when:**

1. **Requirements are ambiguous**
   - Multiple interpretations possible
   - Unclear scope or priority
   - Missing information needed to proceed

2. **Multiple valid approaches exist**
   - Different architectural patterns could work
   - Tradeoffs between options unclear
   - User preference needed for design decision

3. **Missing UI components identified**
   - Component doesn't exist in FRONTEND.md
   - Custom design needed
   - User input on design approach

4. **Risk identified that needs user awareness**
   - Breaking changes possible
   - Performance concerns
   - Complexity concerns

### How to Present Options

**Good pattern:**
```
Use AskUserQuestion with:
- Clear question (specific, actionable)
- 2-4 options (not too many)
- Each option has:
  - Label (short, descriptive)
  - Description (tradeoffs, implications)
- Allow "Other" for custom input (automatic)
```

**Example:**
```python
AskUserQuestion(
    question="Which authentication method should judges use?",
    options=[
        {
            "label": "Magic links (like staff)",
            "description": "Consistent with current system, no passwords to remember. Requires email access during event."
        },
        {
            "label": "Temporary passwords",
            "description": "Works offline, faster login. Requires secure password distribution."
        },
        {
            "label": "QR code scanning",
            "description": "Very fast, no typing. Requires QR code generation and display system."
        }
    ]
)
```

### Communication Anti-Patterns

**❌ Don't assume user intent:**
- Making major decisions without asking
- Guessing at requirements
- Implementing features not requested

**❌ Don't ask too many questions:**
- Overwhelming with choices
- Asking about trivial details
- Not doing due diligence first

**✅ Do balance autonomy and communication:**
- Handle straightforward decisions independently
- Ask when genuinely ambiguous
- Present researched options with tradeoffs

---

## Risk Management

### Identifying Risks

**Technical risks:**
- Breaking changes to existing code
- Performance degradation (N+1 queries, large datasets)
- Scalability concerns (will it work with 1000 users? 10000?)
- Browser compatibility (HTMX features, CSS Grid)
- Accessibility violations (new interaction patterns)

**Process risks:**
- Tight deadlines
- Complex interdependencies
- Insufficient testing
- Unclear requirements

**Business risks:**
- User workflow disruption
- Data migration challenges
- Deployment rollback needs

### Communicating Risks

**When to communicate:**
- During Technical Design Phase (before implementation)
- When risk is discovered during implementation
- Before deployment if deployment risk exists

**How to communicate:**
- Be specific (not "might have performance issues" but "N+1 query will run for each of 100 categories")
- Provide mitigation options
- Recommend approach but allow user decision

**Example:**
```
Risk identified: Breaking change

Current behavior: Tournament.status has 2 values (ACTIVE, COMPLETED)
Proposed change: Add CREATED status, make it initial status

Impact: Existing tournaments in database have status=ACTIVE
Will need data migration to set appropriate status

Mitigation options:
1. Migrate all existing ACTIVE tournaments to CREATED (safest)
2. Migrate only REGISTRATION phase tournaments to CREATED (targeted)
3. Leave existing data as-is, apply only to new tournaments (risky)

Recommendation: Option 2 (targeted migration)
```

### Risk Mitigation Strategies

**For breaking changes:**
- Database migration with data updates
- Backward compatibility layer (if needed)
- Feature flags (if rollback needed)
- Staged rollout

**For performance concerns:**
- Add database indexes
- Use eager loading (avoid N+1)
- Add caching layer
- Monitor and optimize

**For complex changes:**
- Break into smaller phases
- Implement behind feature flag
- Deploy to staging first
- Rollback plan documented

---

# PART 4: TEMPLATES & EXAMPLES

## Workbench File Template

**File:** `workbench/CHANGE_YYYY-MM-DD_TOPIC.md`

```markdown
# Workbench: [Brief Description]

**Date:** YYYY-MM-DD
**Author:** Claude
**Status:** In Progress | Complete | Archived

---

## Purpose

Brief description of what this change accomplishes and why it's needed.

---

## Documentation Changes

### Level 1: Source of Truth

**DOMAIN_MODEL.md:**
- [ ] Section X.X: Added/Updated EntityName
- [ ] Section Y.Y: Updated business rule

**VALIDATION_RULES.md:**
- [ ] Section X.X: Added validation rule for...
- [ ] Section Y.Y: Updated formula

### Level 2: Derived

**ROADMAP.md:**
- [ ] Phase X.X: Added new phase/sub-phase

**README.md:**
- [ ] Updated feature list

### Level 3: Operational

**ARCHITECTURE.md:**
- [ ] Section X: Added new service pattern

**FRONTEND.md:**
- [ ] Component Library: Added new component

**TESTING.md:**
- [ ] Section X: Added test pattern

---

## Verification

**Grep checks performed:**
```bash
grep -r "EntityName" *.md
grep -r "validation_rule_name" *.md
grep -r "new_component_name" *.md
```

**Results:**
- ✅ All references consistent
- ✅ No orphaned references
- ✅ Cross-references valid

---

## Files Modified

**Documentation:**
- DOMAIN_MODEL.md
- VALIDATION_RULES.md
- ARCHITECTURE.md
- FRONTEND.md

**Code:**
- app/models/example.py
- app/services/example_service.py
- app/routers/example.py
- app/templates/example/list.html

**Tests:**
- tests/test_example_service.py
- tests/test_example_routes.py

---

## Notes

Any additional notes, caveats, or follow-up items.
```

---

## Test Structure Templates

### Service Integration Test Template (PRIMARY - Required)

**IMPORTANT:** Service tests should use REAL repositories and database, NOT mocks.

Mocked tests hide bugs like:
- Invalid enum values (`BattleStatus.IN_PROGRESS` doesn't exist)
- Repository signature mismatches
- Lazy loading issues

```python
import pytest
from app.services.example_service import ExampleService
from app.repositories.example import ExampleRepository
from app.models.example import Example

@pytest.mark.asyncio
async def test_create_example_integration(async_session_maker):
    """Integration test: create example with real DB."""
    async with async_session_maker() as session:
        # 1. Create REAL repository (not mock)
        repo = ExampleRepository(session)
        service = ExampleService(repo)

        # 2. Execute against REAL database
        result = await service.create_example(name="Test", value=10)

        # 3. Verify actual behavior
        assert result.success
        assert result.data.id is not None
        assert result.data.name == "Test"

        # 4. Verify database state
        saved = await repo.get_by_id(result.data.id)
        assert saved is not None
        assert saved.name == "Test"


@pytest.mark.asyncio
async def test_create_example_validation_integration(async_session_maker):
    """Integration test: validation errors with real DB."""
    async with async_session_maker() as session:
        repo = ExampleRepository(session)
        service = ExampleService(repo)

        # Empty name should fail validation
        result = await service.create_example(name="", value=10)

        assert not result.success
        assert "Name is required" in result.errors


@pytest.mark.asyncio
async def test_create_example_duplicate_integration(async_session_maker):
    """Integration test: duplicate detection with real DB."""
    async with async_session_maker() as session:
        repo = ExampleRepository(session)
        service = ExampleService(repo)

        # Create first example
        await service.create_example(name="Unique", value=10)

        # Try duplicate - should fail
        result = await service.create_example(name="Unique", value=20)

        assert not result.success
        assert "already exists" in result.errors[0].lower()
```

### Unit Test Template (OPTIONAL - Isolated Logic Only)

**Use mocked unit tests ONLY for:**
- Pure calculation functions (no DB)
- Complex branching logic worth isolating
- External API mocking (not repository mocking)

```python
# GOOD: Unit test for pure calculation (no database interaction)
def test_calculate_minimum_performers():
    """Unit test for pure calculation function."""
    from app.utils.tournament_calculations import calculate_minimum_performers

    result = calculate_minimum_performers(groups_ideal=3)
    assert result == 7  # (3 * 2) + 1


# BAD: Don't mock repositories for service tests!
# This pattern hides bugs like invalid enum values.
# @pytest.mark.asyncio
# async def test_service_with_mocked_repo(mock_repo):  # DON'T DO THIS
#     mock_repo.get_by_id.return_value = mock_entity
#     ...
```

### Integration Test Template (Routes)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_example_route_success(async_client: AsyncClient):
    """Test successful example creation via route."""
    response = await async_client.post("/examples", json={
        "name": "Test Example",
        "value": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Example"
    assert data["value"] == 10


@pytest.mark.asyncio
async def test_create_example_route_validation_error(async_client: AsyncClient):
    """Test example creation with validation error."""
    response = await async_client.post("/examples", json={
        "name": "",
        "value": 10
    })

    assert response.status_code == 422
    assert "Name is required" in response.text


@pytest.mark.asyncio
async def test_get_example_route(async_client: AsyncClient):
    """Test getting an example."""
    # Create example first
    create_response = await async_client.post("/examples", json={
        "name": "Test",
        "value": 10
    })
    example_id = create_response.json()["id"]

    # Get example
    get_response = await async_client.get(f"/examples/{example_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == example_id


@pytest.mark.asyncio
async def test_complete_crud_workflow(async_client: AsyncClient):
    """Test complete CRUD workflow."""
    # Create
    create_response = await async_client.post("/examples", json={
        "name": "Test",
        "value": 10
    })
    assert create_response.status_code == 200
    example_id = create_response.json()["id"]

    # Read
    get_response = await async_client.get(f"/examples/{example_id}")
    assert get_response.status_code == 200

    # Update
    update_response = await async_client.put(f"/examples/{example_id}", json={
        "name": "Updated",
        "value": 20
    })
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated"

    # Delete
    delete_response = await async_client.delete(f"/examples/{example_id}")
    assert delete_response.status_code == 204

    # Verify deleted
    get_deleted = await async_client.get(f"/examples/{example_id}")
    assert get_deleted.status_code == 404
```

---

## Commit Message Template

```
<type>: <subject line>

<body - explain what and why, not how>

<footer - issue references, breaking changes>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semi-colons, etc (no code change)
- `refactor`: Code refactoring (no feature change)
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

**Examples:**

```
feat: Add judge scoring interface for battles

Implement complete judge workflow:
- Judges can score battles independently (blind scoring)
- Admin can view all scores and aggregate results
- Battle model stores individual judge scores
- Preselection uses judge scores instead of staff encoding

This enables V2 functionality where judges directly input scores
instead of staff manually encoding results.

Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
fix: Correct minimum performer formula from +2 to +1

The formula for minimum performers was too restrictive. Changed from
(groups_ideal × 2) + 2 to (groups_ideal × 2) + 1 to ensure exactly
one elimination instead of two.

Updated:
- tournament_calculations.py
- All 24 tournament calculation tests
- VALIDATION_RULES.md documentation

Fixes #145

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Good vs Bad Patterns

### Pattern: Service Layer

**❌ BAD - Business logic in router:**
```python
@router.post("/tournaments/{id}/advance")
async def advance_phase(id: UUID, repo: TournamentRepository):
    tournament = await repo.get(id)

    # Validation in router ❌
    if tournament.phase == TournamentPhase.REGISTRATION:
        categories = await category_repo.get_by_tournament(id)
        for category in categories:
            performers = await performer_repo.count_by_category(category.id)
            minimum = (category.groups_ideal * 2) + 1
            if performers < minimum:
                raise ValueError(f"Not enough performers in {category.name}")

    # Business logic in router ❌
    tournament.advance_phase()
    await repo.update(tournament)
    return tournament
```

**✅ GOOD - Business logic in service:**
```python
# Router (thin)
@router.post("/tournaments/{id}/advance")
async def advance_phase(id: UUID, service: TournamentService):
    result = await service.advance_tournament_phase(id)
    if not result.success:
        flash(request, "error", "; ".join(result.errors))
        return redirect("/tournaments")
    flash(request, "success", "Phase advanced successfully")
    return redirect(f"/tournaments/{id}")

# Service (business logic)
class TournamentService:
    async def advance_tournament_phase(self, id: UUID) -> ValidationResult:
        tournament = await self.repo.get(id)

        # Validation
        validation_result = await validate_phase_transition(tournament)
        if not validation_result.is_valid:
            return ValidationResult(success=False, errors=validation_result.errors)

        # Business logic
        tournament.advance_phase()
        await self.repo.update(tournament)

        return ValidationResult(success=True, data=tournament)
```

---

### Pattern: Frontend Components

**❌ BAD - Reinventing modal:**
```html
<!-- Custom modal when standard exists -->
<div id="my-modal" style="display:none; position:fixed; ...">
  <div class="overlay" onclick="closeModal()"></div>
  <div class="modal-content">
    <h2>Are you sure?</h2>
    <p>This will delete the item.</p>
    <button onclick="confirmDelete()">Yes</button>
    <button onclick="closeModal()">No</button>
  </div>
</div>

<script>
function closeModal() { /* ... */ }
function confirmDelete() { /* ... */ }
</script>
```

**✅ GOOD - Reusing FRONTEND.md component:**
```html
<!-- Use existing delete_modal component -->
{% include "components/delete_modal.html" with
  modal_id="delete-example-modal",
  title="Delete Example?",
  message="This will permanently delete the example. This action cannot be undone.",
  form_action="/examples/" ~ example.id ~ "/delete",
  form_method="post"
%}

<!-- Trigger button -->
<button
  type="button"
  onclick="document.getElementById('delete-example-modal').showModal()"
  class="secondary"
>
  Delete
</button>
```

---

### Pattern: HTMX Usage

**❌ BAD - Custom JavaScript for search:**
```html
<input type="search" id="search" oninput="debounceSearch()">
<div id="results"></div>

<script>
let timeout;
function debounceSearch() {
  clearTimeout(timeout);
  timeout = setTimeout(async () => {
    const q = document.getElementById('search').value;
    const response = await fetch(`/search?q=${q}`);
    const html = await response.text();
    document.getElementById('results').innerHTML = html;
  }, 500);
}
</script>
```

**✅ GOOD - HTMX declarative approach:**
```html
<input
  type="search"
  name="q"
  hx-get="/dancers/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#search-results"
  placeholder="Search dancers..."
>
<div id="search-results"></div>
```

---

# PART 5: INTEGRATION WITH EXISTING DOCS

## Documentation Map

### Level 0: Meta (Navigation & Reference)
- **DOCUMENTATION_INDEX.md** - Central navigation hub
- **GLOSSARY.md** - Key term definitions
- **CHANGELOG.md** - Track documentation changes
- **DOCUMENTATION_CHANGE_PROCEDURE.md** - How to modify docs

### Level 1: Source of Truth (Business Rules)
- **DOMAIN_MODEL.md** - Entity definitions, business rules, workflows
- **VALIDATION_RULES.md** - Constraints, formulas, validation logic

### Level 2: Derived (Planning & Overview)
- **ROADMAP.md** - Phased development plan
- **README.md** - Project overview, quick start

### Level 3: Operational (Technical Procedures)
- **ARCHITECTURE.md** - Backend patterns (services, validators, repositories)
- **FRONTEND.md** - Frontend patterns (components, HTMX, accessibility)
- **TESTING.md** - Test strategies and patterns
- **DEPLOYMENT.md** - Infrastructure setup (Railway, SQLite)

---

## When to Read Which Document

### "I need to understand..."

| Need to know... | Read |
|-----------------|------|
| What entities exist and their business rules | [DOMAIN_MODEL.md](../DOMAIN_MODEL.md) |
| Validation rules and formulas | [VALIDATION_RULES.md](../VALIDATION_RULES.md) |
| Backend architectural patterns | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| Frontend patterns and components | [FRONTEND.md](../FRONTEND.md) |
| Testing approaches | [TESTING.md](../TESTING.md) |
| Deployment procedures | [DEPLOYMENT.md](../DEPLOYMENT.md) |
| Current development phase | [ROADMAP.md](../ROADMAP.md) |
| Term definitions | [GLOSSARY.md](../GLOSSARY.md) |
| How to modify documentation | [DOCUMENTATION_CHANGE_PROCEDURE.md](../DOCUMENTATION_CHANGE_PROCEDURE.md) |
| All available documents | [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) |

### "I'm working on..."

| Task | Read These (in order) |
|------|----------------------|
| New feature with UI | 1. DOMAIN_MODEL.md (entities)<br>2. FRONTEND.md (components)<br>3. ARCHITECTURE.md (patterns)<br>4. TESTING.md (test strategy) |
| Bug fix | 1. DOMAIN_MODEL.md (business rules)<br>2. VALIDATION_RULES.md (constraints)<br>3. ARCHITECTURE.md (where logic lives) |
| Database change | 1. DOMAIN_MODEL.md (entities)<br>2. VALIDATION_RULES.md (constraints)<br>3. ARCHITECTURE.md (migration pattern) |
| UI change | 1. FRONTEND.md (components & patterns)<br>2. VALIDATION_RULES.md (validation display)<br>3. TESTING.md (accessibility testing) |
| Deployment | 1. DEPLOYMENT.md (procedures)<br>2. ROADMAP.md (current phase)<br>3. CHANGELOG.md (recent changes) |

---

## How Plan Mode Maps to Methodology

### Plan Mode Phases → Methodology Phases

**Plan Mode Phase 1: Initial Understanding**
- Maps to: Business Analysis Phase
- Maps to: Requirements Definition Phase
- Actions:
  - Read DOMAIN_MODEL.md for entities
  - Read ARCHITECTURE.md for services
  - Read FRONTEND.md for components
  - Use AskUserQuestion for clarifications

**Plan Mode Phase 2: Planning**
- Maps to: Technical Design Phase
- Maps to: Documentation Phase (planning updates)
- Actions:
  - Choose architectural patterns
  - Plan database changes
  - Plan frontend implementation
  - Plan documentation updates

**Plan Mode Phase 3: Synthesis**
- Maps to: Risk Management
- Maps to: Stakeholder Communication
- Actions:
  - Synthesize different approaches
  - Use AskUserQuestion for tradeoff decisions
  - Confirm scope and approach

**Plan Mode Phase 4: Final Plan**
- Deliverable: Plan file with approach, rationale, files to modify
- Ready to transition to Execution Mode

**Plan Mode Phase 5: Exit Plan Mode**
- Transition to Execution Mode
- Begin following Implementation Phase

---

### Execution Mode → Methodology Phases

**When user approves plan:**
1. Follow Documentation Phase (update docs first)
2. Follow Implementation Phase (write code)
3. Follow Testing Phase (verify code)
4. Follow Deployment Phase (if requested)
5. Follow Closure Phase (wrap up)

---

## Summary

This methodology provides:
- **8-phase development lifecycle** from business analysis to closure
- **Quality gates** at each phase to ensure nothing is missed
- **Decision trees** for common scenarios
- **Templates** for workbench files, tests, commits
- **Examples** of good vs bad patterns from Battle-D project
- **Integration** with existing documentation

**Key Principle:** Documentation first, code second, quality always.

**Remember:** This methodology is a guide, not a prison. Use judgment, adapt as needed, but always maintain quality and consistency.

---

**End of Methodology Document**
