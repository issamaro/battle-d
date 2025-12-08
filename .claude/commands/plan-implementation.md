# Plan Implementation - Technical Design

**Phase:** 3 (Technical Design)

**Purpose:** Plan HOW to build the feature based on the approved feature specification.

**Input Required:** feature-spec.md from `/analyze-feature` command

---

## Instructions for Claude

You are planning the technical implementation. Read the feature-spec.md file first, then follow these steps:

### Step 1: Review Feature Specification

**Read the feature-spec.md file completely:**
- Understand the problem statement
- Review BDD scenarios
- Note must-have vs should-have requirements
- Understand gap analysis
- Review UI/UX requirements

**MANDATORY:** If feature-spec.md is not provided or incomplete, STOP and ask user to run `/analyze-feature` first.

---

### Step 2: Identify Affected Files/Components (Methodology §3.1)

**2.1 Backend Files:**

**Models (app/models/*.py):**
- [ ] Which models need changes?
- [ ] New fields needed?
- [ ] New relationships?
- [ ] Enum changes?

**Services (app/services/*.py):**
- [ ] Which services need changes?
- [ ] New service methods needed?
- [ ] Which existing methods need updates?
- [ ] New service class needed?

**Repositories (app/repositories/*.py):**
- [ ] New repository methods needed?
- [ ] Query optimizations needed?
- [ ] New filtering/search methods?

**Routes (app/routers/*.py):**
- [ ] Which routers need changes?
- [ ] New endpoints needed?
- [ ] Which existing endpoints need updates?

**Validators (app/validators/*.py):**
- [ ] New validation functions needed?
- [ ] Which existing validators need updates?

**Utils/Calculations (app/utils/*.py):**
- [ ] New calculation functions needed?
- [ ] Which existing functions need updates?

**2.2 Frontend Files:**

**Templates (app/templates/**/*.html):**
- [ ] Which templates need changes?
- [ ] New templates needed?
- [ ] Which pages are affected?

**Components:**
- [ ] Which components from FRONTEND.md to reuse?
- [ ] New components needed?

**CSS (app/static/css/*.css):**
- [ ] New CSS file needed?
- [ ] Updates to existing CSS?
- [ ] Prefer PicoCSS classes (minimize custom CSS)

**JavaScript (if absolutely necessary):**
- [ ] Is custom JavaScript truly needed?
- [ ] Can HTMX handle this instead?
- [ ] Document why HTMX insufficient

**2.3 Database Files:**

**Migrations (alembic/versions/*.py):**
- [ ] Schema changes needed?
- [ ] New tables?
- [ ] New columns?
- [ ] Index changes?
- [ ] Data migration needed?

**2.4 Test Files:**

**Unit Tests (tests/test_*.py):**
- [ ] New test files needed?
- [ ] Which existing test files need updates?

**2.5 Documentation Files:**

From feature-spec.md requirements, identify which docs need updates:

**Level 1 (Source of Truth):**
- [ ] DOMAIN_MODEL.md: Entity changes?
- [ ] VALIDATION_RULES.md: New validation rules?

**Level 2 (Derived):**
- [ ] ROADMAP.md: New phase/sub-phase?
- [ ] README.md: Major feature change?

**Level 3 (Operational):**
- [ ] ARCHITECTURE.md: New backend pattern?
- [ ] FRONTEND.md: New UI component/pattern?
- [ ] TESTING.md: New test approach?

---

### Step 3: Choose Architectural Patterns (Methodology §3.2)

**3.1 Backend Patterns:**

**Service Layer:**
- [ ] New service needed or extend existing?
- [ ] Service methods needed (list with signatures)
- [ ] ValidationResult pattern for service methods?
- [ ] Transaction management needed?

**Validation:**
- [ ] Validator functions needed?
- [ ] Where to place validation? (app/validators/*.py)
- [ ] Use ValidationResult pattern

**Repository:**
- [ ] New repository methods needed?
- [ ] Query patterns (filtering, sorting, pagination)?
- [ ] Eager loading needed? (avoid N+1)

**Exception Handling:**
- [ ] ValidationError usage
- [ ] IntegrityError handling
- [ ] Custom exceptions needed?

**3.2 Frontend Patterns (from FRONTEND.md):**

**HTMX Patterns:**
- [ ] Live search: `hx-get` + `hx-trigger="keyup changed delay:500ms"`
- [ ] Form submission: `hx-post` + `hx-swap="outerHTML"`
- [ ] Inline validation: `hx-get` + `hx-target="#error-message"`
- [ ] Polling/auto-refresh: `hx-get` + `hx-trigger="every Xs"`
- [ ] Partial updates: `hx-swap` strategy
- [ ] URL state: `hx-push-url` for filter/navigation state

**Components (from FRONTEND.md Component Library):**
- [ ] Which components to reuse?
- [ ] How to integrate into feature?

**Accessibility (WCAG 2.1 AA):**
- [ ] Keyboard navigation strategy
- [ ] ARIA attributes plan (labels, descriptions, states)
- [ ] Screen reader considerations
- [ ] Focus management

**Responsive Strategy:**
- [ ] Mobile (320px-768px): How should this work?
- [ ] Tablet (769px-1024px): Layout changes?
- [ ] Desktop (1025px+): Full layout?

---

### Step 3.5: Technical Risk POC (If Applicable)

**When required:**
- New integration pattern (new test framework, external API, unfamiliar library)
- Significant architecture change (new service layer, caching, async patterns)
- Technology you haven't used in this codebase before

**When to skip:**
- Standard CRUD operations following existing patterns
- Simple template changes
- Documentation-only changes
- Bug fixes with clear solutions

**POC Process (1-2 hours maximum):**
1. Identify the riskiest technical assumption
2. Create minimal proof-of-concept (separate file or test)
3. Test whether the assumption holds
4. Document findings
5. Decide: proceed as planned / adjust approach / abandon

**Document in implementation-plan.md:**
```markdown
## Technical POC

**Risk identified:** [e.g., "Sync TestClient with async fixtures"]
**Hypothesis:** [e.g., "TestClient can see data created by async fixtures"]

**POC code:**
```python
# Minimal test to validate assumption
...
```

**Result:** ✅ PASSED / ❌ FAILED
**Findings:** [what you learned]
**Decision:** [proceed / adjust target from X to Y / abandon approach]
```

**If no POC needed, document:**
```markdown
## Technical POC

**Status:** Not required
**Reason:** Standard CRUD following existing patterns
```

---

### Step 4: Plan Database Changes (Methodology §3.3)

**4.1 Schema Changes:**

**New tables:**
```sql
-- Table: table_name
-- Purpose: [why this table is needed]
CREATE TABLE table_name (
    -- list fields with types and constraints
);
```

**New columns:**
```sql
-- Table: existing_table
-- New column: column_name
-- Purpose: [why this column is needed]
ALTER TABLE existing_table ADD COLUMN column_name TYPE;
```

**Indexes:**
- [ ] Which columns need indexes for performance?
- [ ] Composite indexes needed?

**4.2 Data Migration:**
- [ ] Do existing records need updates?
- [ ] Default values for new fields?
- [ ] Data transformation needed?

**4.3 Migration Testing Plan:**
- [ ] Test upgrade (alembic upgrade head)
- [ ] Test downgrade (alembic downgrade -1)
- [ ] Test with existing data

---

### Step 5: Plan Documentation Updates (Methodology §3.5)

**Based on identified changes, plan updates to:**

**Level 1 Updates:**

**DOMAIN_MODEL.md:**
- Section: [which section]
- Change: [what to add/update]
- Reason: [why this change]

**VALIDATION_RULES.md:**
- Section: [which section]
- Change: [what to add/update]
- Reason: [why this change]

**Level 2 Updates:**

**ROADMAP.md:**
- [ ] Is this a new phase/sub-phase?
- [ ] Phase number: [X.Y]
- [ ] Objectives: [list]
- [ ] Deliverables: [list]

**Level 3 Updates:**

**ARCHITECTURE.md:**
- [ ] New service pattern to document?
- [ ] New validation approach?

**FRONTEND.md:**
- [ ] New component to add?
- [ ] New HTMX pattern?
- [ ] Accessibility guideline updates?

**TESTING.md:**
- [ ] New test pattern?

---

### Step 6: Identify Risks (Methodology §3.6)

**6.1 Breaking Changes:**
- [ ] Will existing code break?
- [ ] API changes affecting other parts?
- [ ] Database schema changes require migration?
- Mitigation: [how to minimize impact]

**6.2 Performance Concerns:**
- [ ] N+1 query issues?
- [ ] Large dataset handling?
- [ ] Database query optimization needed?
- Mitigation: [indexes, eager loading, caching]

**6.3 Complexity Concerns:**
- [ ] Too complex for maintenance?
- [ ] Can it be simplified?
- [ ] Does it follow existing patterns?
- Mitigation: [simplification approach]

**6.4 Accessibility Risks:**
- [ ] New interaction patterns untested?
- [ ] Custom components need accessibility review?
- Mitigation: [testing plan]

**6.5 Browser Compatibility:**
- [ ] HTMX features supported?
- [ ] CSS Grid/Flexbox support?
- Mitigation: [fallbacks, progressive enhancement]

---

### Step 7: Present Options to User (If Multiple Approaches)

If there are multiple valid technical approaches, use **AskUserQuestion** to present options:

**Example:**
```
Question: "How should we implement battle filtering?"

Context: "There are two approaches with different tradeoffs."

Options:
1. Client-side filtering (JavaScript)
   - Pros: Instant response, no server round-trip
   - Cons: Won't work without JS, harder to test

2. Server-side filtering (HTMX + backend)
   - Pros: Progressive enhancement, easier to test
   - Cons: Requires server round-trip

3. Hybrid (HTMX with URL state)
   - Pros: Best of both, shareable URLs, back button works
   - Cons: Slightly more complex

Recommendation: Option 3 - aligns with FRONTEND.md progressive enhancement principle
```

**When to ask:**
- Multiple architectural patterns possible
- Performance vs complexity tradeoffs
- Custom component vs existing component tradeoff
- Significant technical decision needed

---

## Deliverable: Create implementation-plan.md

Create a file named: `workbench/IMPLEMENTATION_PLAN_YYYY-MM-DD_[FEATURE-NAME].md`

Use this format:

```markdown
# Implementation Plan: [Feature Name]

**Date:** YYYY-MM-DD
**Status:** Ready for Implementation
**Based on:** feature-spec.md

---

## 1. Summary

**Feature:** [One sentence summary]
**Approach:** [High-level technical approach]

---

## 2. Affected Files

### Backend
**Models:**
- app/models/example.py: [what changes]

**Services:**
- app/services/example_service.py: [new methods or updates]

**Repositories:**
- app/repositories/example.py: [new methods]

**Routes:**
- app/routers/example.py: [new endpoints or updates]

**Validators:**
- app/validators/example_validators.py: [new validators]

**Utils:**
- app/utils/example_calculations.py: [new functions]

### Frontend
**Templates:**
- app/templates/example/list.html: [what changes]
- app/templates/example/detail.html: [what changes]

**Components:**
- Reuse: [list from FRONTEND.md]
- New: [list new components needed]

**CSS:**
- app/static/css/example.css: [new styles needed]

### Database
**Migrations:**
- New migration: add_example_field.py: [schema changes]

### Tests
**New Test Files:**
- tests/test_example_service.py: [test coverage]

**Updated Test Files:**
- tests/test_example_routes.py: [additional tests]

### Documentation
**Level 1:**
- DOMAIN_MODEL.md: Section X.X: [changes]
- VALIDATION_RULES.md: Section Y.Y: [changes]

**Level 2:**
- ROADMAP.md: Phase X.Y: [new phase or update]

**Level 3:**
- ARCHITECTURE.md: Section Z: [new pattern]
- FRONTEND.md: Component Library: [new component]

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:**
```sql
-- Migration: YYYY-MM-DD_description
-- Add new column to battles table
ALTER TABLE battles ADD COLUMN encoding_status VARCHAR(20);

-- Add index for filtering
CREATE INDEX idx_battles_encoding_status ON battles(encoding_status);
```

**Data Migration:**
```python
# Set default encoding_status for existing battles
UPDATE battles
SET encoding_status = 'encoded'
WHERE outcome IS NOT NULL;

UPDATE battles
SET encoding_status = 'pending'
WHERE outcome IS NULL AND status = 'COMPLETED';
```

### 3.2 Service Layer Changes

**Service:** BattleService
**New Methods:**

```python
async def filter_battles_by_status(
    self,
    status: Optional[BattleStatus] = None,
    encoding_status: Optional[str] = None
) -> List[Battle]:
    """Filter battles by status and encoding status.

    Args:
        status: Battle status (PENDING/ACTIVE/COMPLETED)
        encoding_status: Encoding status (pending/encoded)

    Returns:
        Filtered list of battles

    Business Logic:
    - encoding_status='pending' means COMPLETED battles without outcome
    - encoding_status='encoded' means battles with outcome
    - Sorted by completion time for pending encoding
    """
```

**Validation Pattern:**
```python
async def encode_battle_results(...) -> ValidationResult[Battle]:
    """Encode battle results with validation.

    Returns ValidationResult with:
    - success: True if encoded
    - data: Updated battle
    - errors: List of validation errors if failed
    """
```

### 3.3 Repository Changes

**Repository:** BattleRepository
**New Methods:**

```python
async def get_by_status_and_encoding(
    self,
    status: Optional[BattleStatus] = None,
    encoding_status: Optional[str] = None
) -> List[Battle]:
    """Get battles filtered by status and encoding status.

    Query optimization:
    - Use single query with filters (not N+1)
    - Eager load performers if needed
    - Add index on encoding_status column
    """
```

### 3.4 Route Changes

**Router:** app/routers/battles.py
**New Endpoints:**

```python
@router.get("/battles/filter")
async def filter_battles(
    status: Optional[str] = None,
    encoding_status: Optional[str] = None,
    battle_service: BattleService = Depends(get_battle_service)
):
    """Filter battles with HTMX partial update.

    Query params:
    - status: PENDING/ACTIVE/COMPLETED
    - encoding_status: pending/encoded/all

    Response:
    - Partial HTML (battle list only)
    - Use hx-swap="outerHTML" on #battle-list
    """
```

---

## 4. Frontend Implementation Plan

### 4.1 Components to Reuse

**From FRONTEND.md Component Library:**
- Badges: Use for status indicators (orange/green/blue)
- Buttons: Primary/secondary for actions
- Forms: Standard form pattern for encoding
- Flash messages: Success/error feedback

### 4.2 New Components Needed

**Component: Filter Chips**
- Location: app/templates/components/filter_chips.html
- Purpose: Clickable filter buttons (All/Pending/Encoded)
- Accessibility: aria-current for active filter, keyboard navigation
- Responsive: Stack vertically on mobile

### 4.3 HTMX Patterns

**Live Filtering:**
```html
<button
  hx-get="/battles/filter?encoding_status=pending"
  hx-target="#battle-list"
  hx-swap="outerHTML"
  hx-push-url="true"
>
  Pending Encoding
</button>
```

**Preserve State:**
- Use hx-push-url to keep filter in URL
- Allows browser back button
- Shareable URLs

### 4.4 Accessibility Implementation

**Keyboard Navigation:**
- Tab through all filters
- Enter/Space to activate
- Escape to clear filter

**ARIA Attributes:**
```html
<div role="group" aria-label="Battle filters">
  <button aria-current="page">Pending</button>
  <button>Encoded</button>
</div>

<div
  id="battle-list"
  role="list"
  aria-live="polite"
  aria-label="Filtered battle list"
>
  <!-- battles -->
</div>
```

**Screen Reader:**
- Announce filter changes
- Announce battle count
- Announce status badges

### 4.5 Responsive Strategy

**Mobile (320px-768px):**
- Filter chips stack vertically
- Battle cards full-width
- Status badges inline

**Tablet (769px-1024px):**
- Filter chips horizontal
- Battle cards 2-column grid

**Desktop (1025px+):**
- Filter chips horizontal with counts
- Battle cards 3-column grid

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**DOMAIN_MODEL.md**
- Section: Battle Entity
- Add: encoding_status field explanation
- Add: Business rule for encoding status lifecycle

**VALIDATION_RULES.md**
- Section: Battle Encoding
- Add: Validation rule for encoding_status transitions
- Add: Constraint that pending battles must be COMPLETED

### Level 2: Derived

**ROADMAP.md**
- Phase: 3.2 - Battle Queue Improvements
- Status: In Progress
- Objectives: [list from feature-spec.md]
- Deliverables: [list]

### Level 3: Operational

**ARCHITECTURE.md**
- Section: Service Layer Patterns
- Add: Example of filtering pattern with ValidationResult

**FRONTEND.md**
- Section: Component Library
- Add: Filter Chips component
- Add: Usage example with HTMX

---

## 6. Testing Plan

### Unit Tests

**test_battle_service.py:**
```python
- test_filter_battles_by_status_pending()
- test_filter_battles_by_status_encoded()
- test_filter_battles_empty_result()
- test_encode_battle_validation_error()
```

**test_battle_repository.py:**
```python
- test_get_by_encoding_status_pending()
- test_get_by_encoding_status_encoded()
- test_query_performance_no_n_plus_1()
```

### Integration Tests

**test_battle_routes.py:**
```python
- test_filter_endpoint_returns_partial_html()
- test_filter_preserves_url_state()
- test_htmx_headers_present()
```

### Accessibility Tests

**Manual Testing Checklist:**
- [ ] Keyboard navigation through filters
- [ ] Screen reader announces changes
- [ ] ARIA attributes correct
- [ ] Color contrast meets WCAG AA (4.5:1 text, 3:1 UI)
- [ ] Focus indicators visible

### Responsive Tests

**Manual Testing Checklist:**
- [ ] Mobile (320px): Filters stack, cards full-width
- [ ] Tablet (769px): 2-column grid works
- [ ] Desktop (1025px): 3-column grid works

---

## 7. Risk Analysis

### Risk 1: Performance with Large Battle Lists
**Concern:** Filtering 100+ battles might be slow
**Likelihood:** Medium
**Impact:** High (user frustration)
**Mitigation:**
- Add database index on encoding_status
- Use pagination if > 50 battles
- Measure query performance in tests

### Risk 2: Filter State Lost on Navigation
**Concern:** Users lose filter when viewing battle detail
**Likelihood:** High if not implemented correctly
**Impact:** Medium (workflow disruption)
**Mitigation:**
- Use hx-push-url to preserve filter in URL
- Add "back to filtered list" link
- Test navigation flow

### Risk 3: Accessibility on Mobile
**Concern:** Filter chips might be hard to tap on mobile
**Likelihood:** Medium
**Impact:** Medium (accessibility violation)
**Mitigation:**
- Ensure 44x44px minimum touch target
- Add spacing between chips
- Test on actual device

---

## 8. Implementation Order

**Recommended sequence to minimize risk:**

1. **Database** (Foundation)
   - Create migration
   - Test upgrade/downgrade
   - Run on dev database

2. **Backend** (Core Logic)
   - Add repository methods
   - Add service methods with validation
   - Write unit tests

3. **Routes** (API)
   - Add filter endpoint
   - Test with curl/Postman
   - Write integration tests

4. **Documentation** (Before Frontend)
   - Update DOMAIN_MODEL.md
   - Update VALIDATION_RULES.md
   - Update ARCHITECTURE.md

5. **Frontend** (UI)
   - Create filter component
   - Update battle list template
   - Add HTMX attributes
   - Test in browser

6. **Accessibility** (Quality)
   - Add ARIA attributes
   - Test keyboard navigation
   - Test screen reader
   - Verify color contrast

7. **Responsive** (Polish)
   - Test mobile layout
   - Test tablet layout
   - Test desktop layout

---

## 9. Open Questions

- [x] Should filter state persist? → Yes, use URL params
- [ ] [Any other questions resolved during planning]

---

## 10. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
```

---

## Quality Gate (BLOCKING)

**Before marking this command complete, verify:**

**Technical Design:**
- [ ] All affected files identified (backend, frontend, database, tests, docs)
- [ ] Backend patterns chosen (service, validation, repository)
- [ ] Frontend patterns chosen (components, HTMX, accessibility)
- [ ] Database changes planned with migrations
- [ ] Documentation updates planned (which docs, which sections)

**Technical Risk Validation:**
- [ ] Technical risks identified (or "none - standard patterns" documented)
- [ ] POC performed for high-risk items (if applicable)
- [ ] POC results documented with decision
- [ ] (Skip POC if: standard CRUD, simple changes, bug fixes)

**Risk Analysis:**
- [ ] Breaking changes identified
- [ ] Performance concerns documented
- [ ] Complexity concerns addressed
- [ ] Accessibility risks mitigated
- [ ] Each risk has mitigation plan

**User Validation:**
- [ ] If multiple approaches exist, user chose via AskUserQuestion
- [ ] User approved technical approach
- [ ] User confirmed risks acceptable

**Deliverable:**
- [ ] implementation-plan.md created in workbench/
- [ ] All sections completed
- [ ] Implementation order defined

**If any checkbox is empty, STOP and complete that step.**

---

## Next Steps

After this command completes and user approves the implementation-plan.md:
1. User reviews implementation-plan.md
2. User provides feedback/approval
3. Run `/implement-feature implementation-plan.md` to start implementation

---

**Remember:** This phase is about planning HOW to build. Be specific about files, methods, patterns. Identify risks. Get user approval before proceeding to implementation.
