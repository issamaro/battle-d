# Implement Feature - Documentation + Code

**Phases:** 4 (Documentation) + 5 (Implementation)

**Purpose:** Update documentation FIRST, then write code following the implementation plan.

**Input Required:** implementation-plan.md from `/plan-implementation` command

---

## Instructions for Claude

You are implementing the feature. Read the implementation-plan.md file first, then follow these steps IN ORDER:

### CRITICAL: Documentation Before Code

**The methodology requires documentation updates BEFORE writing any code.**

This prevents:
- ❌ Documentation drift (code doesn't match docs)
- ❌ Forgetting to document (too busy coding)
- ❌ Inconsistent terminology
- ❌ Orphaned references

---

## Phase 4: Documentation Phase (MUST DO FIRST)

### Step 1: Create Workbench File (Methodology §4.1)

Create: `workbench/CHANGE_YYYY-MM-DD_[FEATURE-NAME].md`

Use DOCUMENTATION_CHANGE_PROCEDURE.md format:

```markdown
# Workbench: [Feature Name]

**Date:** YYYY-MM-DD
**Author:** Claude
**Status:** In Progress

---

## Purpose
[Brief description from feature-spec.md]

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- [ ] Section X.X: [what will be added/updated]

**VALIDATION_RULES.md:**
- [ ] Section Y.Y: [what will be added/updated]

### Level 2: Derived
**ROADMAP.md:**
- [ ] Phase X.Y: [what will be added/updated]

### Level 3: Operational
**ARCHITECTURE.md:**
- [ ] Section Z: [what will be added/updated]

**FRONTEND.md:**
- [ ] Component Library: [what will be added/updated]

---

## Verification
[Will be completed after updates]

---

## Files Modified
[Will be completed during implementation]
```

---

### Step 2: Update Level 1 Docs (Methodology §4.2)

**These are Source of Truth - must be updated first**

**2.1 Update DOMAIN_MODEL.md (if entities changed)**

From implementation-plan.md, identify entity changes:
- New entities
- New fields
- Updated relationships
- Updated business rules
- Updated workflows

**Read DOMAIN_MODEL.md first** to understand structure, then update.

**Example update:**
```markdown
#### Battle Entity

**New Field:**
- `encoding_status` (string): Tracks whether battle results have been encoded
  - Values: 'pending' | 'encoded'
  - Business rule: Set to 'pending' when battle status = COMPLETED with no outcome
  - Business rule: Set to 'encoded' when outcome is recorded
```

**2.2 Update VALIDATION_RULES.md (if validation rules changed)**

From implementation-plan.md, identify validation changes:
- New validation rules
- Updated formulas
- Updated constraints

**Read VALIDATION_RULES.md first** to understand structure, then update.

**Example update:**
```markdown
### Battle Encoding Status Validation

**Rule:** Battles can only be encoded when status is COMPLETED

**Implementation Location:** `app/services/battle_results_encoding_service.py::encode_*_results()`

**Validation Logic:**
```python
if battle.status != BattleStatus.COMPLETED:
    return ValidationResult(
        success=False,
        errors=["Battle must be COMPLETED before encoding"]
    )
```

**Business Reason:** Prevents encoding results for battles that haven't occurred yet.
```

---

### Step 3: Update Level 2 Docs (Methodology §4.3)

**These are derived from Level 1**

**3.1 Update ROADMAP.md (if new phase/sub-phase)**

From implementation-plan.md phase number:

```markdown
## Phase X.Y: [Feature Name]

**Status:** 🔄 In Progress

**Objectives:**
- [Objective 1 from feature-spec.md]
- [Objective 2]

**Deliverables:**
- [ ] Backend: [deliverable]
- [ ] Frontend: [deliverable]
- [ ] Tests: [deliverable]
- [ ] Documentation: [deliverable]

**Technical Approach:**
[High-level summary from implementation-plan.md]
```

**3.2 Update README.md (only if major feature change)**

Most features don't require README updates. Only update if:
- Major new capability
- Changes to quick start
- New setup requirements

---

### Step 4: Update Level 3 Docs (Methodology §4.4)

**These are operational references**

**4.1 Update ARCHITECTURE.md (if new backend pattern)**

From implementation-plan.md backend changes:

**Example: New service pattern**
```markdown
#### Filtering Pattern with URL State

**Service Layer:**
```python
class BattleService:
    async def filter_battles(
        self,
        status: Optional[BattleStatus] = None,
        encoding_status: Optional[str] = None
    ) -> List[Battle]:
        """Filter battles by multiple criteria.

        Returns filtered list, not ValidationResult (query operation).
        """
        return await self.battle_repo.get_by_filters(status, encoding_status)
```

**Router Layer:**
```python
@router.get("/battles/filter")
async def filter_battles(
    status: Optional[str] = None,
    encoding_status: Optional[str] = None,
    service: BattleService = Depends(get_battle_service)
):
    """HTMX endpoint returns partial HTML."""
    battles = await service.filter_battles(status, encoding_status)
    return templates.TemplateResponse("battles/partials/list.html", {
        "battles": battles
    })
```
```

**4.2 Update FRONTEND.md (if new UI component/pattern)**

From implementation-plan.md frontend changes:

**Example: New component**
```markdown
#### Filter Chips

**Purpose:** Clickable filter buttons for list views

**Location:** `app/templates/components/filter_chips.html`

**Usage:**
```html
{% include "components/filter_chips.html" with
  filters=[
    {"label": "All", "value": "all", "active": true},
    {"label": "Pending", "value": "pending", "count": 12},
    {"label": "Encoded", "value": "encoded", "count": 38}
  ],
  hx_get="/battles/filter",
  hx_target="#battle-list"
%}
```

**Accessibility:**
- aria-current="page" on active filter
- aria-label includes count ("Pending: 12 battles")
- Keyboard navigation support (Tab, Enter/Space)

**Responsive:**
- Mobile: Stack vertically
- Tablet/Desktop: Horizontal row
```

**4.3 Update TESTING.md (if new test approach)**

Only if introducing new testing patterns not covered in existing TESTING.md.

---

### Step 5: Verify with Grep (Methodology §4.5)

**Check consistency across all docs:**

```bash
# Search for entity name across all docs
grep -r "EntityName" *.md

# Search for new terms/concepts
grep -r "encoding_status" *.md

# Check for orphaned references
grep -r "old_term_that_should_be_gone" *.md
```

**Ensure:**
- [ ] No orphaned references to old names
- [ ] Consistent terminology
- [ ] Cross-references valid
- [ ] New concepts documented in all relevant places

---

### Step 6: Update Workbench Verification Section

In the workbench file, update:

```markdown
## Verification

**Grep checks performed:**
```bash
grep -r "encoding_status" *.md
grep -r "BattleEncodingStatus" *.md
```

**Results:**
- ✅ All references consistent
- ✅ No orphaned references
- ✅ Cross-references valid

**Files Updated:**
- DOMAIN_MODEL.md: Added encoding_status field to Battle entity
- VALIDATION_RULES.md: Added encoding status validation rule
- ARCHITECTURE.md: Added filtering pattern example
- FRONTEND.md: Added filter chips component
- ROADMAP.md: Added Phase 3.2 entry
```

---

## Phase 5: Implementation Phase (ONLY AFTER DOCS UPDATED)

**CHECKPOINT:** All documentation must be updated before proceeding to code.

---

### Step 7: Create TodoWrite Task List (Methodology §5.1)

Based on implementation-plan.md, create task list:

```javascript
TodoWrite({
  todos: [
    { content: "Create Alembic migration for schema changes", status: "pending", activeForm: "Creating Alembic migration" },
    { content: "Update Battle model with new fields", status: "pending", activeForm: "Updating Battle model" },
    { content: "Add filtering method to BattleRepository", status: "pending", activeForm: "Adding filtering to BattleRepository" },
    { content: "Add filter_battles method to BattleService", status: "pending", activeForm: "Adding filter_battles to BattleService" },
    { content: "Add /battles/filter endpoint to router", status: "pending", activeForm: "Adding filter endpoint" },
    { content: "Create filter chips component", status: "pending", activeForm: "Creating filter chips component" },
    { content: "Update battle list template with HTMX", status: "pending", activeForm: "Updating battle list template" },
    { content: "Write unit tests for service layer", status: "pending", activeForm: "Writing service tests" },
    { content: "Write integration tests for routes", status: "pending", activeForm: "Writing route tests" },
  ]
})
```

**IMPORTANT:**
- Mark ONE task as "in_progress" at a time
- Mark as "completed" IMMEDIATELY when done
- Don't batch completions

---

### Step 8: Database Changes First (Methodology §5.2)

**8.1 Create Alembic Migration**

```bash
alembic revision --autogenerate -m "Add encoding_status to battles"
```

**8.2 Review Generated Migration**

Read the generated file in `alembic/versions/` and verify:
- [ ] Column types correct
- [ ] Constraints correct (unique, foreign keys, not null)
- [ ] Indexes added if planned
- [ ] Default values set if needed

**Edit migration if needed** to add:
- Data migration (update existing records)
- Indexes for performance
- Proper upgrade/downgrade logic

**8.3 Test Migration**

```bash
alembic upgrade head    # Test upgrade
alembic downgrade -1    # Test downgrade
alembic upgrade head    # Back to current
```

**Verify:**
- [ ] Upgrade works without errors
- [ ] Downgrade works without errors
- [ ] Data preserved correctly

**8.4 Update Models**

Update `app/models/*.py` following implementation-plan.md:
- Add new fields with proper types
- Add relationships if needed
- Follow SQLAlchemy 2.0 async patterns
- Add docstrings for new fields

---

### Step 9: Service Layer Changes (Methodology §5.3)

**Follow Service Layer Pattern from ARCHITECTURE.md**

**9.1 Implement Business Logic**

In `app/services/*.py`:

**If adding validation:**
```python
async def method_name(...) -> ValidationResult[ModelType]:
    """Method description.

    Args:
        param: Description

    Returns:
        ValidationResult with success/errors/data
    """
    # Validation
    errors = []
    if not condition:
        errors.append("Error message")

    if errors:
        return ValidationResult(success=False, errors=errors)

    # Business logic
    result = await self.repo.method(...)

    return ValidationResult(success=True, data=result)
```

**If query/filtering (no validation needed):**
```python
async def filter_battles(...) -> List[Battle]:
    """Filter battles by criteria.

    Returns filtered list directly (not ValidationResult for queries).
    """
    return await self.battle_repo.get_by_filters(...)
```

**9.2 Add Validation**

For methods that change state:
- Return `ValidationResult[T]`
- Collect errors in list
- Return success=True with data, or success=False with errors

**9.3 Handle Exceptions**

```python
try:
    result = await self.repo.create(entity)
except IntegrityError:
    return ValidationResult(
        success=False,
        errors=["Entity already exists"]
    )
```

---

### Step 10: Repository Changes (Methodology §5.2)

In `app/repositories/*.py`:

**10.1 Add New Methods**

```python
async def get_by_filters(
    self,
    status: Optional[BattleStatus] = None,
    encoding_status: Optional[str] = None
) -> List[Battle]:
    """Get battles with filters.

    Query optimization:
    - Single query (not N+1)
    - Eager load relationships if needed
    """
    query = select(Battle)

    if status:
        query = query.where(Battle.status == status)

    if encoding_status == 'pending':
        query = query.where(
            Battle.status == BattleStatus.COMPLETED,
            Battle.outcome == None
        )
    elif encoding_status == 'encoded':
        query = query.where(Battle.outcome != None)

    # Eager load if needed
    # query = query.options(selectinload(Battle.performers))

    result = await self.session.execute(query)
    return result.scalars().all()
```

---

### Step 11: Router Changes (Methodology §5.4)

**Follow Router Pattern from ARCHITECTURE.md - keep routers THIN**

In `app/routers/*.py`:

```python
@router.get("/battles/filter")
async def filter_battles(
    request: Request,
    status: Optional[str] = None,
    encoding_status: Optional[str] = None,
    service: BattleService = Depends(get_battle_service),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """Filter battles endpoint for HTMX.

    Query params:
    - status: PENDING/ACTIVE/COMPLETED
    - encoding_status: pending/encoded/all

    Returns partial HTML for hx-swap.
    """
    # Delegate to service
    battles = await service.filter_battles(status, encoding_status)

    # Return partial template (not full page)
    return templates.TemplateResponse(
        "battles/partials/battle_list.html",
        {
            "request": request,
            "battles": battles,
            "current_filter": encoding_status
        }
    )
```

**Router responsibilities:**
- HTTP concerns (request, response)
- Dependency injection
- Template rendering
- Flash messages

**NOT in router:**
- Business logic (in service)
- Validation (in service/validators)
- Database queries (in repository)

---

### Step 12: Frontend Implementation (Methodology §5.5)

**12.1 Use FRONTEND.md Component Library**

**DON'T reinvent components. Check FRONTEND.md first.**

**12.2 Follow Design Principles (FRONTEND.md)**

**Minimalism:**
- Remove unnecessary elements
- Use whitespace instead of borders
- Clean visual hierarchy

**Accessibility (WCAG 2.1 AA):**
- Keyboard navigation (all interactive elements)
- Screen readers (semantic HTML, ARIA)
- Color contrast (4.5:1 text, 3:1 UI)
- Focus indicators (visible focus states)

**Mobile-first:**
- Design for 320px first
- Enhance for tablet (769px+)
- Enhance for desktop (1025px+)

**Progressive enhancement:**
- Works without JavaScript
- Enhanced with HTMX
- Custom JS only when necessary

**12.3 Apply HTMX Patterns (from implementation-plan.md)**

**Example: Live filtering**
```html
<div class="filter-chips" role="group" aria-label="Battle filters">
  <button
    hx-get="/battles/filter?encoding_status=all"
    hx-target="#battle-list"
    hx-swap="outerHTML"
    hx-push-url="true"
    aria-current="page"
  >
    All
  </button>

  <button
    hx-get="/battles/filter?encoding_status=pending"
    hx-target="#battle-list"
    hx-swap="outerHTML"
    hx-push-url="true"
  >
    Pending Encoding <span class="badge">12</span>
  </button>

  <button
    hx-get="/battles/filter?encoding_status=encoded"
    hx-target="#battle-list"
    hx-swap="outerHTML"
    hx-push-url="true"
  >
    Encoded <span class="badge">38</span>
  </button>
</div>

<div
  id="battle-list"
  role="list"
  aria-live="polite"
  aria-label="Battle list"
>
  <!-- Battle cards rendered here -->
  {% for battle in battles %}
    <article role="listitem">
      <!-- Battle card content -->
    </article>
  {% endfor %}
</div>
```

**12.4 Use Semantic HTML**

```html
<nav>...</nav>           <!-- Navigation -->
<article>...</article>   <!-- Independent content -->
<section>...</section>   <!-- Thematic grouping -->
<aside>...</aside>       <!-- Sidebar content -->
```

**12.5 Add ARIA Attributes**

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

**12.6 Use PicoCSS Classes**

**Minimize custom CSS.** PicoCSS provides semantic styling automatically.

**Only create custom CSS if:**
- PicoCSS doesn't provide the style
- Component needs specific layout
- Following FRONTEND.md patterns

**12.7 Add Flash Messages**

```python
from app.utils.flash import flash

flash(request, "success", "Battle encoded successfully")
flash(request, "error", "Failed to encode battle")
```

**12.8 Add Empty States**

```html
{% if battles %}
  <!-- Display battles -->
{% else %}
  <div class="empty-state">
    <p>No battles found</p>
    <a href="/battles" class="button">View all battles</a>
  </div>
{% endif %}
```

---

### Step 13: Write Tests (Methodology §5.1)

**Write tests AS YOU IMPLEMENT, not after.**

**13.1 Unit Tests (Service Layer)**

In `tests/test_*_service.py`:

```python
@pytest.mark.asyncio
async def test_filter_battles_by_encoding_status_pending(battle_service, battle_repo):
    """Test filtering battles by pending encoding status."""
    # Setup
    battle_repo.get_by_filters.return_value = [mock_battle_1, mock_battle_2]

    # Execute
    result = await battle_service.filter_battles(encoding_status='pending')

    # Verify
    assert len(result) == 2
    battle_repo.get_by_filters.assert_called_once_with(
        status=None,
        encoding_status='pending'
    )
```

**13.2 Integration Tests (Routes)**

In `tests/test_*_routes.py`:

```python
@pytest.mark.asyncio
async def test_filter_endpoint_returns_partial_html(async_client):
    """Test filter endpoint returns partial HTML for HTMX."""
    response = await async_client.get(
        "/battles/filter?encoding_status=pending",
        headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    # Should not contain full page wrapper
    assert "<html>" not in response.text
    assert "<head>" not in response.text
    # Should contain battle list
    assert 'id="battle-list"' in response.text
```

---

### Step 14: Follow Architecture Patterns (Methodology §5.6)

**Backend (ARCHITECTURE.md):**
- ✅ Service Layer Pattern (business logic in services)
- ✅ Validation Pattern (ValidationResult)
- ✅ Router Pattern (thin routers)
- ✅ Repository Pattern (data access)

**Frontend (FRONTEND.md):**
- ✅ Component Library (reuse components)
- ✅ HTMX Patterns (declarative AJAX)
- ✅ Accessibility Guidelines (WCAG 2.1 AA)
- ✅ Responsive Design (mobile-first)

**Avoid common pitfalls:**
- ❌ No business logic in routers
- ❌ No skipping service layer
- ❌ No hardcoded values (use calculation functions)
- ❌ No reinventing UI components
- ❌ No skipping accessibility

---

### Step 15: Update Workbench File with Implementation Details

In `workbench/CHANGE_*.md`, add:

```markdown
## Files Modified

**Code:**
- app/models/battle.py: Added encoding_status field
- app/repositories/battle.py: Added get_by_filters method
- app/services/battle_service.py: Added filter_battles method
- app/routers/battles.py: Added /battles/filter endpoint
- app/templates/battles/list.html: Added filter chips, HTMX
- app/static/css/battles.css: Added filter chip styles
- alembic/versions/xxx_add_encoding_status.py: Migration

**Tests:**
- tests/test_battle_service.py: Added 4 filter tests
- tests/test_battle_routes.py: Added 3 integration tests

**Documentation:**
- DOMAIN_MODEL.md: Updated Battle entity
- VALIDATION_RULES.md: Added encoding status rule
- ARCHITECTURE.md: Added filtering pattern example
- FRONTEND.md: Added filter chips component
- ROADMAP.md: Added Phase 3.2

## Notes

- Used URL state preservation (hx-push-url) for shareable filters
- Added database index on encoding_status for performance
- All tests passing (171 + 7 new = 178 total)
```

---

## Quality Gate (BLOCKING)

**Before marking this command complete, verify:**

**Documentation Phase Complete:**
- [ ] Workbench file created
- [ ] Level 1 docs updated (DOMAIN_MODEL, VALIDATION_RULES)
- [ ] Level 2 docs updated if needed (ROADMAP, README)
- [ ] Level 3 docs updated if needed (ARCHITECTURE, FRONTEND, TESTING)
- [ ] Grep verification performed (no orphaned references)
- [ ] Workbench file updated with verification results

**Implementation Phase Complete:**
- [ ] TodoWrite task list created
- [ ] Database migration created and tested (up and down)
- [ ] Models updated with new fields/relationships
- [ ] Repository methods added/updated
- [ ] Service layer implemented with validation
- [ ] Routes added/updated (thin routers, delegate to services)
- [ ] Frontend templates updated
- [ ] HTMX patterns applied correctly
- [ ] Semantic HTML used
- [ ] ARIA attributes present
- [ ] PicoCSS used (minimal custom CSS)
- [ ] Flash messages implemented
- [ ] Empty states implemented
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Code follows architectural patterns
- [ ] All TodoWrite tasks marked completed

**Quality Checks:**
- [ ] No business logic in routers
- [ ] Service layer has proper validation
- [ ] No N+1 query issues
- [ ] UI components reused from FRONTEND.md (not reinvented)
- [ ] Accessibility attributes present
- [ ] No console errors in browser
- [ ] Workbench file updated with implementation details

**If any checkbox is empty, STOP and complete that step.**

---

## Next Steps

After this command completes:
1. User reviews implemented code
2. User tests functionality manually
3. Run `/verify-feature` to perform comprehensive testing

---

**Remember:** Documentation FIRST, then code. Follow established patterns. Keep routers thin. Reuse components. Write tests as you go. Update workbench file throughout.
