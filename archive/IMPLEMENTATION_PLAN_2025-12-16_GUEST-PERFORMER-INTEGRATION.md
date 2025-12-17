# Implementation Plan: Guest Performer Integration

**Date:** 2025-12-16
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-12_GUEST-PERFORMER-INTEGRATION.md

---

## 1. Summary

**Feature:** Guest performer registration system allowing pre-qualified performers to skip preselection and go directly to pools.

**Approach:** Add `is_guest` boolean field to Performer model with automatic preselection_score of 10.0. Update registration UI with guest option, modify minimum calculations to account for guests, and exclude guests from preselection battle generation.

---

## 2. Affected Files

### Backend

**Models:**
- `app/models/performer.py`: Add `is_guest: bool` field (default False)

**Services:**
- `app/services/performer_service.py`: Add guest registration logic with phase validation
- `app/services/battle_service.py`: Exclude guests from preselection battle generation
- `app/services/pool_service.py`: Update qualification logic to respect guest priority in tiebreaks

**Repositories:**
- `app/repositories/performer.py`: Add methods for guest count, filter by guest status

**Routes:**
- `app/routers/registration.py`: Add guest registration endpoints, update list endpoints to show guest status

**Validators:**
- `app/validators/phase_validators.py`: Update minimum performer validation to account for guests

**Utils:**
- `app/utils/tournament_calculations.py`: Add `calculate_adjusted_minimum()` function

### Frontend

**Templates:**
- `app/templates/registration/register.html`: Add "Register as Guest" button option
- `app/templates/registration/_available_list.html`: Add guest registration button variant
- `app/templates/registration/_registered_list.html`: Display guest badge, show guest/regular counts
- `app/templates/registration/_registration_update.html`: Include guest badge in OOB swap

**Components:**
- New: Guest badge component (inline in templates)
- Reuse: Existing button styles, flash messages

**CSS:**
- `app/static/css/registration.css`: Add `.guest-badge` styling (minimal, use existing patterns)

### Database

**Migrations:**
- New migration: `YYYYMMDD_add_is_guest_to_performers.py`
  - Add `is_guest` boolean column (default False)
  - Add index on `(category_id, is_guest)` for efficient guest count queries

### Tests

**New Test Files:**
- `tests/test_guest_performer.py`: Comprehensive guest registration tests

**Updated Test Files:**
- `tests/test_performer_service_integration.py`: Add guest registration tests
- `tests/test_battle_service.py` (if exists): Test guest exclusion from preselection
- `tests/test_tournament_calculations.py`: Test adjusted minimum calculation

### Documentation

**Level 1:**
- `DOMAIN_MODEL.md`: Add `is_guest` field to Performer entity, add BR-GUEST-* business rules
- `VALIDATION_RULES.md`: Add Guest Registration Validation section

**Level 2:**
- `ROADMAP.md`: Add Phase 3.X for Guest Performer Integration

---

## 3. Backend Implementation Plan

### 3.1 Database Changes

**Schema Changes:**
```sql
-- Migration: YYYYMMDD_add_is_guest_to_performers
-- Add is_guest column to performers table
ALTER TABLE performers ADD COLUMN is_guest BOOLEAN NOT NULL DEFAULT FALSE;

-- Add index for efficient guest count queries
CREATE INDEX idx_performers_category_is_guest ON performers(category_id, is_guest);
```

**No data migration needed:** All existing performers will have `is_guest = false` by default, which is the correct behavior.

### 3.2 Model Changes

**File:** `app/models/performer.py`

Add new field after `pool_losses`:
```python
is_guest: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False,
)
```

### 3.3 Utils Changes

**File:** `app/utils/tournament_calculations.py`

Add new function:
```python
def calculate_adjusted_minimum(groups_ideal: int, guest_count: int = 0) -> int:
    """Calculate adjusted minimum performers with guests.

    Formula: max(2, (groups_ideal * 2) + 1 - guest_count)

    Guests reduce the minimum required performers because they are
    guaranteed to qualify for pools. The minimum is capped at 2 to
    ensure at least some competition.

    Args:
        groups_ideal: Target number of pools (must be >= 1)
        guest_count: Number of guest performers (default 0)

    Returns:
        Adjusted minimum number of performers required

    Raises:
        ValueError: If groups_ideal < 1 or guest_count < 0

    Examples:
        >>> calculate_adjusted_minimum(2, guest_count=0)
        5  # Standard: (2 * 2) + 1 = 5

        >>> calculate_adjusted_minimum(2, guest_count=2)
        3  # Adjusted: max(2, 5 - 2) = 3

        >>> calculate_adjusted_minimum(2, guest_count=4)
        2  # Floor: max(2, 5 - 4) = 2 (not 1)
    """
    if groups_ideal < 1:
        raise ValueError("groups_ideal must be at least 1")
    if guest_count < 0:
        raise ValueError("guest_count cannot be negative")

    standard_minimum = calculate_minimum_performers(groups_ideal)
    adjusted = standard_minimum - guest_count
    return max(2, adjusted)
```

### 3.4 Repository Changes

**File:** `app/repositories/performer.py`

Add new methods:
```python
async def get_guest_count(self, category_id: uuid.UUID) -> int:
    """Get count of guest performers in a category.

    Args:
        category_id: Category UUID

    Returns:
        Number of guest performers
    """
    result = await self.session.execute(
        select(func.count(Performer.id)).where(
            Performer.category_id == category_id,
            Performer.is_guest == True,
        )
    )
    return result.scalar_one()

async def get_regular_performers(self, category_id: uuid.UUID) -> List[Performer]:
    """Get non-guest performers in a category.

    Args:
        category_id: Category UUID

    Returns:
        List of regular (non-guest) performers
    """
    result = await self.session.execute(
        select(Performer)
        .options(selectinload(Performer.dancer))
        .where(
            Performer.category_id == category_id,
            Performer.is_guest == False,
        )
    )
    return list(result.scalars().all())

async def get_guests(self, category_id: uuid.UUID) -> List[Performer]:
    """Get guest performers in a category.

    Args:
        category_id: Category UUID

    Returns:
        List of guest performers
    """
    result = await self.session.execute(
        select(Performer)
        .options(selectinload(Performer.dancer))
        .where(
            Performer.category_id == category_id,
            Performer.is_guest == True,
        )
    )
    return list(result.scalars().all())

async def create_guest_performer(
    self,
    tournament_id: uuid.UUID,
    category_id: uuid.UUID,
    dancer_id: uuid.UUID,
) -> Performer:
    """Create a guest performer with automatic top score.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        dancer_id: Dancer UUID

    Returns:
        Created guest performer with preselection_score=10.0
    """
    return await self.create(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=dancer_id,
        is_guest=True,
        preselection_score=Decimal("10.00"),
    )

async def convert_to_guest(self, performer_id: uuid.UUID) -> Performer:
    """Convert a regular performer to guest.

    Args:
        performer_id: Performer UUID

    Returns:
        Updated performer with guest status

    Raises:
        ValueError: If performer not found
    """
    performer = await self.get_by_id(performer_id)
    if not performer:
        raise ValueError(f"Performer {performer_id} not found")

    performer.is_guest = True
    performer.preselection_score = Decimal("10.00")
    await self.session.commit()
    return performer
```

### 3.5 Service Layer Changes

**File:** `app/services/performer_service.py`

Add new methods:
```python
async def register_guest_performer(
    self,
    tournament_id: UUID,
    category_id: UUID,
    dancer_id: UUID,
) -> Performer:
    """Register performer as guest with automatic top score.

    BR-GUEST-001: Guest designation only allowed during Registration phase.
    BR-GUEST-002: Guests automatically receive 10.0 preselection score.

    Args:
        tournament_id: Tournament UUID
        category_id: Category UUID
        dancer_id: Dancer UUID

    Returns:
        Created guest performer

    Raises:
        ValidationError: If validation fails or not in Registration phase
    """
    # Validate phase - guests only allowed during REGISTRATION
    category = await self.category_repo.get_by_id(category_id)
    if not category:
        raise ValidationError(["Category not found"])

    tournament = category.tournament
    if tournament.phase != TournamentPhase.REGISTRATION:
        raise ValidationError([
            "Guests can only be added during Registration phase"
        ])

    # Use existing validation from register_performer
    # (category exists, belongs to tournament, dancer exists, not already registered)
    await self._validate_registration(tournament_id, category_id, dancer_id)

    # Create guest performer
    try:
        performer = await self.performer_repo.create_guest_performer(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer_id,
        )
    except IntegrityError as e:
        # Handle race conditions
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            raise ValidationError([
                "Dancer is already registered in this tournament."
            ])
        raise ValidationError(["Database integrity error during registration"])

    return performer

async def convert_performer_to_guest(
    self,
    performer_id: UUID,
    tournament_id: UUID,
) -> Performer:
    """Convert regular performer to guest.

    BR-GUEST-001: Only allowed during Registration phase.

    Args:
        performer_id: Performer UUID
        tournament_id: Tournament UUID

    Returns:
        Updated performer

    Raises:
        ValidationError: If not in Registration phase or performer not found
    """
    # Validate phase
    tournament = await self.tournament_repo.get_by_id(tournament_id)
    if not tournament:
        raise ValidationError(["Tournament not found"])

    if tournament.phase != TournamentPhase.REGISTRATION:
        raise ValidationError([
            "Performer guest status can only be changed during Registration phase"
        ])

    # Get performer
    performer = await self.performer_repo.get_by_id(performer_id)
    if not performer:
        raise ValidationError(["Performer not found"])

    if performer.tournament_id != tournament_id:
        raise ValidationError(["Performer does not belong to this tournament"])

    if performer.is_guest:
        raise ValidationError(["Performer is already a guest"])

    # Convert to guest
    performer = await self.performer_repo.convert_to_guest(performer_id)
    return performer

async def _validate_registration(
    self,
    tournament_id: UUID,
    category_id: UUID,
    dancer_id: UUID,
) -> None:
    """Validate common registration requirements.

    Extracted from register_performer for reuse.
    """
    # Validate category exists and belongs to tournament
    category = await self.category_repo.get_by_id(category_id)
    if not category:
        raise ValidationError(["Category not found"])

    if category.tournament_id != tournament_id:
        raise ValidationError(["Category does not belong to this tournament"])

    # Validate dancer exists
    dancer = await self.dancer_repo.get_by_id(dancer_id)
    if not dancer:
        raise ValidationError(["Dancer not found"])

    # Check dancer not already registered
    if await self.performer_repo.dancer_registered_in_tournament(
        dancer_id, tournament_id
    ):
        raise ValidationError([
            f"Dancer '{dancer.full_name}' is already registered in this tournament"
        ])
```

**File:** `app/services/battle_service.py`

Update `generate_preselection_battles` and `_create_preselection_battles_for_category`:
```python
async def generate_preselection_battles(
    self, category_id: uuid.UUID
) -> List[Battle]:
    """Generate preselection battles for a category.

    BR-GUEST-002: Guests do not participate in preselection battles.
    Creates 1v1 battles with random pairing for REGULAR performers only.

    Args:
        category_id: Category UUID

    Returns:
        List of created battles

    Raises:
        ValidationError: If category has no regular performers
    """
    # Get only REGULAR performers (exclude guests)
    performers = await self.performer_repo.get_regular_performers(category_id)

    if not performers:
        # Check if there are guests - if so, no battles needed
        guest_count = await self.performer_repo.get_guest_count(category_id)
        if guest_count > 0:
            # All performers are guests, no preselection battles needed
            return []
        raise ValidationError(["Cannot generate battles: no performers in category"])

    # Existing battle generation logic with regular performers only...
    # (rest of the method remains the same, just using filtered performers)
```

Similarly update `_create_preselection_battles_for_category`.

### 3.6 Validator Changes

**File:** `app/validators/phase_validators.py`

Update `validate_registration_to_preselection`:
```python
async def validate_registration_to_preselection(
    tournament_id: UUID,
    tournament_repo: TournamentRepository,
    category_repo: CategoryRepository,
    performer_repo: PerformerRepository,
) -> ValidationResult:
    """Validate tournament can advance from REGISTRATION to PRESELECTION.

    Business Rules:
    - Tournament must exist
    - Tournament must have at least one category
    - Each category must have minimum performers: (groups_ideal * 2 + 1) - guest_count
    - Minimum cannot go below 2 total performers

    BR-GUEST-004: Each guest reduces minimum performer requirement by 1.
    """
    errors = []
    warnings = []

    # Check tournament exists
    tournament = await tournament_repo.get_with_categories(tournament_id)
    if not tournament:
        return ValidationResult.failure(["Tournament not found"])

    # Check has categories
    if not tournament.categories:
        return ValidationResult.failure(
            ["Tournament has no categories. Add at least one category."]
        )

    # Check each category meets minimum performers (adjusted for guests)
    for category in tournament.categories:
        performers = await performer_repo.get_by_category(category.id)
        performer_count = len(performers)
        guest_count = sum(1 for p in performers if p.is_guest)
        regular_count = performer_count - guest_count

        # Calculate adjusted minimum
        adjusted_min = calculate_adjusted_minimum(category.groups_ideal, guest_count)

        if performer_count < adjusted_min:
            errors.append(
                f"Category '{category.name}': has {performer_count} performers "
                f"({guest_count} guests, {regular_count} regulars), "
                f"minimum required: {adjusted_min}"
            )
        elif performer_count == adjusted_min:
            warnings.append(
                f"Category '{category.name}': has exactly minimum performers "
                f"({performer_count}). Only 1 will be eliminated in preselection."
            )

        # Warn if no regular performers
        if regular_count == 0 and guest_count > 0:
            warnings.append(
                f"Category '{category.name}': has only guest performers. "
                f"No preselection battles will occur."
            )

    if errors:
        return ValidationResult.failure(errors, warnings)
    return ValidationResult.success(warnings)
```

### 3.7 Route Changes

**File:** `app/routers/registration.py`

Add new endpoints:
```python
@router.post("/{tournament_id}/{category_id}/register-guest/{dancer_id}", response_class=HTMLResponse)
async def register_guest_htmx(
    tournament_id: str,
    category_id: str,
    dancer_id: str,
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    performer_service: PerformerService = Depends(get_performer_service),
    # ... other dependencies
):
    """HTMX: Register dancer as guest.

    Returns both panels updated via OOB swap.
    """
    user = require_staff(current_user)

    # Parse UUIDs and validate
    # ...

    # Register as guest
    try:
        await performer_service.register_guest_performer(
            tournament_uuid, category_uuid, dancer_uuid
        )
    except ValidationError as e:
        add_flash_message(request, e.errors[0], "error")
        # Return error response

    # Return updated panels (same pattern as register_dancer_htmx)


@router.post("/{tournament_id}/{category_id}/convert-to-guest/{performer_id}", response_class=HTMLResponse)
async def convert_to_guest_htmx(
    tournament_id: str,
    category_id: str,
    performer_id: str,
    request: Request,
    # ... dependencies
):
    """HTMX: Convert registered performer to guest.

    BR-GUEST-001: Only allowed during Registration phase.
    """
    # Implementation similar to above
```

Update existing endpoints to include guest count in context:
```python
# In registered_dancers_partial and similar endpoints, add:
guest_count = sum(1 for p in performers if p.is_guest)
regular_count = len(performers) - guest_count

context = {
    # ... existing context
    "guest_count": guest_count,
    "regular_count": regular_count,
}
```

---

## 4. Frontend Implementation Plan

### 4.1 Components to Reuse

**From existing patterns:**
- Button styles (`.btn-add`, `.btn-remove`)
- Flash messages for feedback
- HTMX swap patterns (OOB updates)
- Card layouts (`.performer-card`, `.dancer-card`)

### 4.2 New Components Needed

**Component: Guest Badge**
- Location: Inline in templates (simple enough, no separate file needed)
- Purpose: Visual indicator for guest performers
- HTML: `<mark class="guest-badge">Guest</mark>`
- CSS: Minimal styling in registration.css

### 4.3 Template Changes

**File:** `app/templates/registration/_available_list.html`

Add guest registration button option:
```html
{% if available_dancers %}
<div class="dancer-list">
    {% for dancer in available_dancers %}
    <article class="dancer-card">
        <div class="dancer-info">
            <strong class="dancer-blaze">{{ dancer.blaze }}</strong>
            <span class="dancer-name">{{ dancer.full_name }}</span>
            <small class="dancer-meta">{{ dancer.country or "-" }} | Age {{ dancer.age }}</small>
        </div>
        <div class="dancer-actions" role="group">
            <!-- Regular registration -->
            <button class="btn-add"
                    hx-post="/registration/{{ tournament_id }}/{{ category_id }}/register/{{ dancer.id }}"
                    hx-target="#available-list"
                    hx-swap="innerHTML"
                    hx-indicator="#reg-loading"
                    title="Register as regular performer">
                + Add
            </button>
            <!-- Guest registration -->
            <button class="btn-add-guest"
                    hx-post="/registration/{{ tournament_id }}/{{ category_id }}/register-guest/{{ dancer.id }}"
                    hx-target="#available-list"
                    hx-swap="innerHTML"
                    hx-indicator="#reg-loading"
                    title="Register as guest (pre-qualified, skips preselection)">
                + Guest
            </button>
        </div>
    </article>
    {% endfor %}
</div>
{% else %}
<div class="empty-message">
    <p>No available dancers found.</p>
</div>
{% endif %}
```

**File:** `app/templates/registration/_registered_list.html`

Display guest badge and counts:
```html
<!-- Registered Dancers List (HTMX Partial) -->
<div class="registered-header">
    <strong>{{ registered_count }}</strong> / {{ ideal_count }} registered
    {% if guest_count > 0 %}
    <small class="guest-count">({{ guest_count }} guest{{ 's' if guest_count != 1 else '' }}, {{ regular_count }} regular{{ 's' if regular_count != 1 else '' }})</small>
    {% endif %}
    {% if registered_count >= minimum_required %}
    <mark class="status-ready">Ready</mark>
    {% else %}
    <small class="status-need-more">(Need {{ minimum_required - registered_count }} more)</small>
    {% endif %}
</div>

{% if performers %}
<div class="performer-list">
    {% for performer in performers %}
    <article class="performer-card{% if performer.is_guest %} performer-guest{% endif %}">
        <div class="performer-info">
            <strong class="performer-blaze">
                {{ performer.dancer.blaze }}
                {% if performer.is_guest %}
                <mark class="guest-badge">Guest</mark>
                {% endif %}
            </strong>
            <span class="performer-name">{{ performer.dancer.full_name }}</span>
            {% if performer.is_guest %}
            <small class="guest-note">Pre-qualified (Score: 10.0)</small>
            {% endif %}
        </div>
        <div class="performer-actions">
            {% if not performer.is_guest %}
            <!-- Option to convert to guest -->
            <button class="btn-convert-guest"
                    hx-post="/registration/{{ tournament_id }}/{{ category_id }}/convert-to-guest/{{ performer.id }}"
                    hx-target="#registered-list"
                    hx-swap="innerHTML"
                    hx-confirm="Mark {{ performer.dancer.blaze }} as guest?"
                    hx-indicator="#reg-loading"
                    title="Convert to guest (pre-qualified)">
                Make Guest
            </button>
            {% endif %}
            <button class="btn-remove"
                    hx-post="/registration/{{ tournament_id }}/{{ category_id }}/unregister-htmx/{{ performer.id }}"
                    hx-target="#available-list"
                    hx-swap="innerHTML"
                    hx-confirm="Unregister {{ performer.dancer.blaze }}?"
                    hx-indicator="#reg-loading">
                Remove
            </button>
        </div>
    </article>
    {% endfor %}
</div>
{% else %}
<div class="empty-message">
    <p>No dancers registered yet.</p>
</div>
{% endif %}
```

### 4.4 CSS Changes

**File:** `app/static/css/registration.css`

Add minimal guest styling:
```css
/* Guest badge styling */
.guest-badge {
    background-color: var(--pico-primary);
    color: var(--pico-primary-inverse);
    padding: 0.1em 0.4em;
    border-radius: 0.25em;
    font-size: 0.75em;
    font-weight: 600;
    margin-left: 0.5em;
}

/* Guest performer card highlight */
.performer-guest {
    border-left: 3px solid var(--pico-primary);
}

/* Guest note styling */
.guest-note {
    color: var(--pico-muted-color);
    font-style: italic;
}

/* Guest action buttons */
.btn-add-guest {
    background-color: var(--pico-secondary);
}

.btn-convert-guest {
    font-size: 0.75em;
    padding: 0.25em 0.5em;
}

/* Guest count in header */
.guest-count {
    color: var(--pico-muted-color);
    margin-left: 0.5em;
}
```

### 4.5 Accessibility Implementation

**Keyboard Navigation:**
- All buttons tabbable in logical order
- Button groups have `role="group"` for screen readers

**ARIA Attributes:**
```html
<!-- Guest badge -->
<mark class="guest-badge" aria-label="Guest performer">Guest</mark>

<!-- Button titles for clarity -->
<button title="Register as guest (pre-qualified, skips preselection)">+ Guest</button>

<!-- Status indicators -->
<div id="registered-list" aria-live="polite" aria-label="Registered performers list">
```

**Screen Reader:**
- Guest status clearly announced via badge
- Action buttons have descriptive titles
- Live region for list updates

### 4.6 Responsive Strategy

The registration UI is already responsive. Guest additions follow existing patterns:
- Button groups stack on mobile if needed
- Guest badge remains visible at all sizes
- No special responsive handling required

---

## 5. Documentation Update Plan

### Level 1: Source of Truth

**DOMAIN_MODEL.md**
- Section: Performer Entity
- Add `is_guest` field description
- Add text:
  ```markdown
  - `is_guest`: bool (default False) - If true, performer skips preselection
  ```
- Add Business Rules section:
  ```markdown
  ### Guest Performer Rules

  **BR-GUEST-001:** Guest designation only during Registration phase
  **BR-GUEST-002:** Guests receive automatic 10.0 preselection score
  **BR-GUEST-003:** Guests count toward pool capacity
  **BR-GUEST-004:** Each guest reduces minimum requirement by 1
  **BR-GUEST-005:** Guests distributed via snake draft like regulars
  **BR-GUEST-006:** Guest wins tiebreak at boundary
  ```

**VALIDATION_RULES.md**
- Section: New section "Guest Registration Validation"
- Add:
  ```markdown
  ## Guest Registration Validation

  ### Guest Designation Rules

  **Timing:**
  - Guests can only be designated during REGISTRATION phase
  - Cannot change guest status after phase advances

  **Automatic Score:**
  - Guest performers receive preselection_score = 10.0 at registration
  - Score is immutable

  **Minimum Adjustment:**
  - adjusted_minimum = max(2, (groups_ideal × 2) + 1 - guest_count)
  ```

### Level 2: Derived

**ROADMAP.md**
- Add Phase 3.X:
  ```markdown
  ## Phase 3.X: Guest Performer Integration

  **Objective:** Support pre-qualified invited performers who skip preselection.

  **Deliverables:**
  - is_guest field on Performer model
  - Guest registration in UI with badge display
  - Adjusted minimum calculations
  - Preselection battle exclusion for guests
  - Documentation updates (DOMAIN_MODEL, VALIDATION_RULES)
  ```

### Level 3: Operational

No updates needed - this feature follows existing patterns documented in ARCHITECTURE.md and FRONTEND.md.

---

## 6. Testing Plan

### Unit Tests

**tests/test_guest_performer.py:**
```python
# Registration tests
- test_register_guest_sets_is_guest_true()
- test_register_guest_sets_preselection_score_10()
- test_register_guest_fails_if_not_registration_phase()
- test_convert_regular_to_guest()
- test_convert_guest_fails_if_already_guest()
- test_convert_guest_fails_if_not_registration_phase()

# Calculation tests
- test_adjusted_minimum_no_guests()
- test_adjusted_minimum_with_guests()
- test_adjusted_minimum_floor_at_2()

# Repository tests
- test_get_guest_count()
- test_get_regular_performers()
- test_get_guests()
- test_create_guest_performer()
```

**tests/test_tournament_calculations.py:**
```python
- test_calculate_adjusted_minimum_standard()
- test_calculate_adjusted_minimum_reduced_by_guests()
- test_calculate_adjusted_minimum_min_floor()
- test_calculate_adjusted_minimum_invalid_inputs()
```

### Integration Tests

**tests/test_guest_performer.py (continued):**
```python
# Phase transition tests
- test_phase_validation_counts_guests_in_minimum()
- test_phase_validation_passes_with_guests_reducing_minimum()
- test_phase_validation_warning_for_all_guests()

# Battle generation tests
- test_preselection_battles_exclude_guests()
- test_no_battles_when_all_guests()
- test_guest_already_has_score_in_pools()
```

### Route Tests

**tests/test_registration_routes.py (new or update):**
```python
- test_register_guest_htmx_success()
- test_register_guest_htmx_phase_error()
- test_convert_to_guest_htmx_success()
- test_registered_list_shows_guest_badge()
- test_registered_list_shows_guest_count()
```

### Accessibility Tests

**Manual Testing Checklist:**
- [ ] Guest badge visible and readable
- [ ] Buttons have clear labels/titles
- [ ] Keyboard navigation works for all actions
- [ ] Screen reader announces guest status
- [ ] Color contrast meets WCAG AA

---

## 7. Risk Analysis

### Risk 1: Phase Enforcement
**Concern:** User might try to add guests after Registration phase
**Likelihood:** Medium
**Impact:** High (data integrity)
**Mitigation:**
- Validate phase in PerformerService.register_guest_performer()
- Hide "Guest" button in UI after Registration phase (use tournament.phase check)
- Test phase validation thoroughly

### Risk 2: Score Immutability
**Concern:** Guest score might be accidentally modified during preselection encoding
**Likelihood:** Low
**Impact:** Medium (unfair advantage/disadvantage)
**Mitigation:**
- Exclude guests from preselection battle generation
- Guests won't appear in encoding forms
- Add check in encoding service if needed

### Risk 3: Pool Qualification Tiebreak
**Concern:** Guest with 10.0 ties with regular who scored 10.0
**Likelihood:** Low (10.0 is rare for regulars)
**Impact:** Medium (fairness question)
**Mitigation:**
- BR-GUEST-006 specifies guest wins tiebreak
- Sort by (score DESC, is_guest DESC, registration_time ASC) in pool creation
- Document this clearly in UI/help text

### Risk 4: Empty Preselection Phase
**Concern:** If all performers are guests, no preselection battles occur
**Likelihood:** Low (unusual configuration)
**Impact:** Low (valid scenario)
**Mitigation:**
- Handle gracefully in battle generation (return empty list)
- Add warning in phase validation
- Phase can still advance (guests already scored)

### Risk 5: Migration on Production Data
**Concern:** Adding column might affect existing performers
**Likelihood:** Low
**Impact:** Low (default false is correct)
**Mitigation:**
- Use `default=False` in migration
- Test migration with sample data
- Verify existing performers unaffected

---

## 8. Implementation Order

**Recommended sequence to minimize risk:**

1. **Database Migration** (Foundation)
   - Create migration for `is_guest` column
   - Test upgrade/downgrade
   - Apply to dev database

2. **Model & Repository** (Core Data)
   - Add `is_guest` to Performer model
   - Add repository methods (get_guests, get_regular_performers, etc.)
   - Write unit tests

3. **Utils & Validators** (Business Logic)
   - Add `calculate_adjusted_minimum()` function
   - Update phase validators
   - Write calculation tests

4. **Service Layer** (Business Operations)
   - Add guest registration methods to PerformerService
   - Update BattleService to exclude guests
   - Write integration tests

5. **Documentation** (Before UI)
   - Update DOMAIN_MODEL.md
   - Update VALIDATION_RULES.md
   - Update ROADMAP.md

6. **Routes** (API)
   - Add guest registration endpoints
   - Add convert-to-guest endpoint
   - Update context with guest counts
   - Write route tests

7. **Frontend** (UI)
   - Add guest button to available list
   - Add guest badge to registered list
   - Add CSS styling
   - Test in browser

8. **Accessibility & Polish** (Quality)
   - Add ARIA attributes
   - Test keyboard navigation
   - Verify screen reader behavior

---

## 9. Technical POC

**Status:** Not required

**Reason:** This feature uses standard patterns already established in the codebase:
- Boolean field addition follows existing model patterns
- Service layer follows existing PerformerService patterns
- HTMX endpoints follow existing registration patterns
- No new technologies or unfamiliar integrations

---

## 10. Open Questions

- [x] Should filter state persist? → Not applicable (registration list, not filtered)
- [x] What happens if all performers are guests? → Valid, no preselection battles, phase can advance
- [x] Tiebreak at 10.0 boundary? → Guest wins per BR-GUEST-006
- [x] Can all performers be guests (0 regulars)? → Yes, but add warning in validation

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved technical approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
