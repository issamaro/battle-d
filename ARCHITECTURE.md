# Battle-D Architecture Guide
**Level 3: Operational** | Last Updated: 2025-12-06

This document describes the architectural patterns, design principles, and best practices used in the Battle-D web application.

---

## Prerequisites

Before reading this document, familiarize yourself with:
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Entity definitions and business rules
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - Constraints and validation logic
- [FRONTEND.md](FRONTEND.md) - Frontend patterns, components, and HTMX usage

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Service Layer Pattern](#service-layer-pattern)
- [Validation Pattern](#validation-pattern)
- [Router Pattern with Services](#router-pattern-with-services)
- [Battle System Architecture](#battle-system-architecture)
- [Phase Transition Hooks](#phase-transition-hooks)
- [Tiebreak Auto-Detection Pattern](#tiebreak-auto-detection-pattern)
- [HTMX Patterns](#htmx-patterns)
- [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
- [Service Layer Reference](#service-layer-reference)

---

## Architecture Overview

Battle-D follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│   (Jinja2 Templates + HTMX)        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│          Router Layer               │
│      (FastAPI Routers)              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         Service Layer               │
│    (Business Logic + Validation)    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Repository Layer             │
│    (Database Access via SQLAlchemy) │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         Database Layer              │
│         (SQLite + Alembic)          │
└─────────────────────────────────────┘
```

**Key Principles:**

- **Dependency Injection**: Services and repositories injected via FastAPI dependencies
- **Single Responsibility**: Each layer has one clear responsibility
- **Separation of Concerns**: Business logic stays in services, not routers
- **Type Safety**: Pydantic schemas validate all input/output
- **SOLID Principles**: Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

---

## Service Layer Pattern

### Purpose

The service layer encapsulates business logic and orchestrates operations between repositories. It ensures:

- **Business rules** are enforced consistently
- **Validation** happens before database operations
- **Complex operations** (multi-repository coordination) are managed
- **Reusability** across different routers/endpoints

### Pattern Structure

```python
# In services/
class SomeService:
    """Service for managing some entity with business logic."""

    def __init__(self, repo1: SomeRepository, repo2: AnotherRepository):
        """Initialize service with required repositories."""
        self.repo1 = repo1
        self.repo2 = repo2

    async def do_something(self, ...) -> Model:
        """
        Perform a business operation with validation.

        Args:
            ...: Parameters needed

        Returns:
            Model: The resulting model

        Raises:
            ValidationError: If business rules are violated
        """
        # Step 1: Validation
        if await self.repo1.some_check():
            raise ValidationError(["Error message"])

        # Step 2: Business logic
        result = await self.repo1.create(...)

        # Step 3: Side effects (if needed)
        await self.repo2.update(...)

        return result
```

### Dependency Injection

```python
# In dependencies.py
def get_some_service(
    repo1: SomeRepository = Depends(get_some_repository),
    repo2: AnotherRepository = Depends(get_another_repository),
) -> SomeService:
    """Factory function for SomeService."""
    return SomeService(repo1, repo2)
```

### Example: DancerService

```python
# app/services/dancer_service.py
class DancerService:
    def __init__(self, dancer_repo: DancerRepository):
        self.dancer_repo = dancer_repo

    async def create_dancer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        blaze: str,
        country: str | None = None,
        city: str | None = None,
    ) -> Dancer:
        """Create a new dancer with validation."""
        # Validation: Check email uniqueness
        if await self.dancer_repo.email_exists(email):
            raise ValidationError([f"Email {email} is already registered"])

        # Validation: Check age (must be 10-100 years old)
        age = (date.today() - date_of_birth).days // 365
        if age < 10 or age > 100:
            raise ValidationError([f"Dancer age must be between 10 and 100 years (got {age})"])

        # Business logic: Create dancer
        return await self.dancer_repo.create_dancer(
            email=email,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            blaze=blaze,
            country=country,
            city=city,
        )
```

---

## Validation Pattern

### ValidationResult Dataclass

Type-safe error handling with support for both errors and warnings:

```python
# In validators/result.py
@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        success: True if validation passed
        errors: List of blocking errors
        warnings: List of non-blocking warnings
    """
    success: bool
    errors: list[str]
    warnings: list[str]

    @staticmethod
    def success_result(warnings: list[str] | None = None) -> "ValidationResult":
        """Create a successful validation result."""
        return ValidationResult(success=True, errors=[], warnings=warnings or [])

    @staticmethod
    def failure(errors: list[str], warnings: list[str] | None = None) -> "ValidationResult":
        """Create a failed validation result."""
        return ValidationResult(success=False, errors=errors, warnings=warnings or [])
```

### Validation Function Pattern

```python
# In validators/
async def validate_something(...) -> ValidationResult:
    """
    Validate some business rule.

    Returns:
        ValidationResult with success/failure and messages
    """
    errors = []
    warnings = []

    # Check conditions
    if condition_failed:
        errors.append("Error message explaining what failed")

    elif condition_edge_case:
        warnings.append("Warning message for edge case")

    # Return result
    if errors:
        return ValidationResult.failure(errors, warnings)

    return ValidationResult.success_result(warnings)
```

### Example: Phase Transition Validation

```python
# app/validators/phase_validators.py
async def validate_registration_to_preselection(
    tournament: Tournament,
    category_repo: CategoryRepository,
    performer_repo: PerformerRepository,
) -> ValidationResult:
    """
    Validate if tournament can advance from Registration to Preselection.

    Business Rule:
    - Each category must have at least (groups_ideal × 2 + 1) performers

    Returns:
        ValidationResult with errors if categories don't meet minimum
    """
    errors = []
    warnings = []

    categories = await category_repo.get_by_tournament(tournament.id)

    for category in categories:
        performers = await performer_repo.get_by_category(category.id)
        performer_count = len(performers)

        # Calculate minimum required
        minimum_required = (category.groups_ideal * 2) + 1

        if performer_count < minimum_required:
            needed = minimum_required - performer_count
            errors.append(
                f"Category '{category.name}': needs {needed} more performers "
                f"(has {performer_count}, needs {minimum_required})"
            )

        elif performer_count == minimum_required:
            warnings.append(
                f"Category '{category.name}': has exactly minimum performers ({minimum_required}) "
                "- consider getting more for better competition"
            )

    if errors:
        return ValidationResult.failure(errors, warnings)

    return ValidationResult.success_result(warnings)
```

---

## Router Pattern with Services

### Purpose

Routers handle HTTP requests/responses and delegate business logic to services.

### Pattern Structure

```python
# In routers/
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from app.dependencies import get_some_service, require_staff
from app.services.some_service import SomeService
from app.exceptions import ValidationError

router = APIRouter(prefix="/some-route", tags=["some-tag"])

@router.post("/something")
async def create_something(
    # Request data (form, JSON, path params, etc.)
    data: CreateSchema,
    # Authentication/authorization
    current_user = Depends(require_staff),
    # Service dependency
    service: SomeService = Depends(get_some_service),
):
    """
    Create something with validation.

    Permissions: Staff only
    """
    try:
        # Delegate to service layer
        result = await service.do_something(
            field1=data.field1,
            field2=data.field2,
        )

        # Success: redirect with 303 See Other
        return RedirectResponse(
            url=f"/success/{result.id}",
            status_code=303
        )

    except ValidationError as e:
        # Business rule violation: show error page
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "errors": e.errors,
                "warnings": e.warnings,
            },
            status_code=400
        )
```

### Key Principles

1. **Thin routers**: Routers should be thin, delegating logic to services
2. **Dependency injection**: Use FastAPI's `Depends()` for services
3. **Error handling**: Catch `ValidationError` and display user-friendly messages
4. **HTTP semantics**: Use proper status codes (303 for redirects, 400 for validation errors)
5. **No business logic**: Keep business rules in services, not routers

---

## Battle System Architecture

### Overview

The battle system (Phase 2) handles all battle generation, pool management, tiebreak resolution, and result encoding. It consists of three coordinated services that work together during tournament execution.

### Battle Services

#### BattleService

**Purpose**: Generate and manage battles across all tournament phases.

**File**: `app/services/battle_service.py` (317 lines)

**Key Methods**:

```python
class BattleService:
    """Service for battle generation and lifecycle management."""

    def __init__(
        self,
        battle_repo: BattleRepository,
        performer_repo: PerformerRepository,
    ):
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo

    async def generate_preselection_battles(
        self, category_id: UUID
    ) -> list[Battle]:
        """
        Generate preselection battles for category.

        Creates one battle per performer with SCORED outcome type.
        Each performer battles alone (1v1 or 2v2 based on category type).

        Business Rules:
        - One battle per registered performer
        - PENDING status initially
        - SCORED outcome type (0-10 scoring)

        Returns:
            List of created preselection battles
        """
        performers = await self.performer_repo.get_by_category(category_id)

        battles = []
        for performer in performers:
            battle = Battle(
                category_id=category_id,
                phase=BattlePhase.PRESELECTION,
                outcome_type=BattleOutcomeType.SCORED,
                status=BattleStatus.PENDING,
            )
            battle = await self.battle_repo.create(battle)

            # Link performer to battle
            await self.battle_repo.add_performer_to_battle(
                battle.id, performer.id
            )
            battles.append(battle)

        return battles

    async def generate_pool_battles(
        self, category_id: UUID, pool_id: UUID
    ) -> list[Battle]:
        """
        Generate round-robin pool battles.

        Creates all possible matchups between pool performers.
        Uses WIN_DRAW_LOSS outcome type for pool standings.

        Returns:
            List of created pool battles
        """
        # Get performers in pool
        pool = await self.pool_repo.get_pool_with_performers(pool_id)
        performers = pool.performers

        battles = []
        # Generate all possible matchups (round robin)
        for i, p1 in enumerate(performers):
            for p2 in performers[i+1:]:
                battle = Battle(
                    category_id=category_id,
                    phase=BattlePhase.POOLS,
                    pool_id=pool_id,
                    outcome_type=BattleOutcomeType.WIN_DRAW_LOSS,
                    status=BattleStatus.PENDING,
                )
                battle = await self.battle_repo.create(battle)

                # Link both performers
                await self.battle_repo.add_performer_to_battle(
                    battle.id, p1.id
                )
                await self.battle_repo.add_performer_to_battle(
                    battle.id, p2.id
                )
                battles.append(battle)

        return battles

    async def generate_finals_battles(
        self, category_id: UUID
    ) -> list[Battle]:
        """
        Generate finals bracket battles from pool winners.

        Creates single-elimination bracket (8→4→2→1).
        Uses WIN_LOSS outcome type for bracket progression.

        Business Rules:
        - Extract pool winners (one per pool)
        - Create bracket battles in rounds
        - Link to FINALS phase

        Returns:
            List of created finals battles
        """
        # Get pool winners for category
        winners = await self.pool_repo.get_pool_winners(category_id)

        # Generate bracket battles
        battles = self._create_bracket_battles(category_id, winners)
        return battles

    async def start_battle(self, battle_id: UUID) -> Battle:
        """
        Start a battle (PENDING → ACTIVE).

        Args:
            battle_id: Battle UUID

        Returns:
            Updated battle with ACTIVE status
        """
        battle = await self.battle_repo.get_by_id(battle_id)
        battle.status = BattleStatus.ACTIVE
        return await self.battle_repo.update(battle)

    async def complete_battle(self, battle_id: UUID) -> Battle:
        """
        Complete a battle (ACTIVE → COMPLETED).

        Args:
            battle_id: Battle UUID

        Returns:
            Updated battle with COMPLETED status
        """
        battle = await self.battle_repo.get_by_id(battle_id)
        battle.status = BattleStatus.COMPLETED
        return await self.battle_repo.update(battle)
```

**Test Coverage**: 25 tests in `tests/test_battle_service.py` (637 lines)

#### PoolService

**Purpose**: Create pools from preselection results and determine winners.

**File**: `app/services/pool_service.py` (236 lines)

**Key Methods**:

```python
class PoolService:
    """Service for pool creation and management."""

    def __init__(
        self,
        pool_repo: PoolRepository,
        performer_repo: PerformerRepository,
    ):
        self.pool_repo = pool_repo
        self.performer_repo = performer_repo

    async def create_pools_from_preselection(
        self, category_id: UUID, num_pools: int
    ) -> list[Pool]:
        """
        Create pools from preselection qualification results.

        Business Rules:
        - Extract qualified performers (preselection_qualified = True)
        - Distribute evenly across num_pools pools
        - Snake draft distribution for fairness

        Args:
            category_id: Category UUID
            num_pools: Number of pools to create (from category.groups_ideal)

        Returns:
            List of created pools with performers assigned
        """
        # Get qualified performers, sorted by preselection_score DESC
        qualified = await self.performer_repo.get_qualified_performers(
            category_id
        )

        # Create pools
        pools = []
        for i in range(num_pools):
            pool = Pool(
                category_id=category_id,
                name=f"Pool {chr(65 + i)}",  # Pool A, Pool B, etc.
                status=PoolStatus.PENDING,
            )
            pool = await self.pool_repo.create(pool)
            pools.append(pool)

        # Distribute performers (snake draft)
        self._distribute_performers_to_pools(pools, qualified)

        return pools

    async def determine_pool_winner(self, pool_id: UUID) -> UUID:
        """
        Determine pool winner based on points.

        Points Formula:
        - Win: 3 points
        - Draw: 1 point
        - Loss: 0 points

        Tiebreaker Rules:
        1. Most points
        2. If tied, tiebreak battle required

        Returns:
            UUID of winning performer
        """
        pool = await self.pool_repo.get_pool_with_performers(pool_id)

        # Calculate points for each performer
        standings = []
        for performer in pool.performers:
            points = (performer.pool_wins * 3) + (performer.pool_draws * 1)
            standings.append((performer, points))

        # Sort by points DESC
        standings.sort(key=lambda x: x[1], reverse=True)

        # Check for tie at top
        top_points = standings[0][1]
        tied_performers = [p for p, pts in standings if pts == top_points]

        if len(tied_performers) > 1:
            raise ValidationError([
                f"Pool {pool.name} has tie for first place - "
                "tiebreak battle required"
            ])

        winner = standings[0][0]

        # Update pool winner
        pool.winner_id = winner.id
        pool.status = PoolStatus.COMPLETED
        await self.pool_repo.update(pool)

        return winner.id
```

**Test Coverage**: 17 tests in `tests/test_pool_service.py` (445 lines)

#### TiebreakService

**Purpose**: Detect ties and resolve them through tiebreak battles.

**File**: `app/services/tiebreak_service.py` (274 lines)

**Key Methods**:

```python
class TiebreakService:
    """Service for detecting and resolving tiebreak situations."""

    def __init__(
        self,
        battle_repo: BattleRepository,
        pool_repo: PoolRepository,
        performer_repo: PerformerRepository,
    ):
        self.battle_repo = battle_repo
        self.pool_repo = pool_repo
        self.performer_repo = performer_repo

    async def detect_preselection_tie(
        self, category_id: UUID, qualification_cutoff: int
    ) -> list[UUID] | None:
        """
        Detect tie at preselection qualification cutoff.

        Args:
            category_id: Category UUID
            qualification_cutoff: Number of performers to qualify

        Returns:
            List of tied performer UUIDs if tie exists, None otherwise
        """
        performers = await self.performer_repo.get_by_category(category_id)

        # Sort by preselection_score DESC
        performers.sort(
            key=lambda p: p.preselection_score or 0, reverse=True
        )

        # Check if performers at cutoff have same score
        cutoff_score = performers[qualification_cutoff - 1].preselection_score
        tied = [
            p for p in performers
            if p.preselection_score == cutoff_score
        ]

        if len(tied) > 1:
            return [p.id for p in tied]

        return None

    async def detect_pool_tie(self, pool_id: UUID) -> list[UUID] | None:
        """
        Detect tie for first place in pool standings.

        Returns:
            List of tied performer UUIDs if tie exists, None otherwise
        """
        pool = await self.pool_repo.get_pool_with_performers(pool_id)

        # Calculate points
        standings = []
        for performer in pool.performers:
            points = (performer.pool_wins * 3) + (performer.pool_draws * 1)
            standings.append((performer, points))

        # Check for tie at top
        standings.sort(key=lambda x: x[1], reverse=True)
        top_points = standings[0][1]
        tied = [p for p, pts in standings if pts == top_points]

        if len(tied) > 1:
            return [p.id for p in tied]

        return None

    async def create_tiebreak_battle(
        self,
        category_id: UUID,
        tied_performer_ids: list[UUID],
        voting_mode: str,
    ) -> Battle:
        """
        Create a tiebreak battle for tied performers.

        Args:
            category_id: Category UUID
            tied_performer_ids: List of performer UUIDs in tiebreak
            voting_mode: 'KEEP' (N=2) or 'ELIMINATE' (N>2)

        Returns:
            Created tiebreak battle
        """
        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.TIEBREAK,
            outcome_type=BattleOutcomeType.TIEBREAK,
            status=BattleStatus.PENDING,
            voting_mode=voting_mode,
        )
        battle = await self.battle_repo.create(battle)

        # Link all tied performers
        for performer_id in tied_performer_ids:
            await self.battle_repo.add_performer_to_battle(
                battle.id, performer_id
            )

        return battle
```

**Test Coverage**: 22 tests in `tests/test_tiebreak_service.py` (533 lines)

### Battle Routing and Encoding

**File**: `app/routers/battles.py` (262 lines)

**Purpose**: Provide web interface for battle management and result encoding.

**Key Endpoints**:

```python
@router.get("", response_class=HTMLResponse)
async def list_battles(...):
    """
    List battles with filtering.

    Query Params:
    - category_id: Filter by category
    - status_filter: 'pending', 'active', 'completed'

    Template: battles/list.html
    """
    battles = await battle_repo.get_by_category(category_id)

    # Apply status filter if provided
    if status_filter:
        battles = [b for b in battles if b.status.value == status_filter]

    return templates.TemplateResponse(...)

@router.get("/{battle_id}", response_class=HTMLResponse)
async def battle_detail(battle_id: UUID, ...):
    """
    Show battle details.

    Template: battles/detail.html
    Features:
    - Performer cards with winner highlighting
    - Outcome display
    - Role-based action buttons (Start, Encode)
    """
    battle = await battle_repo.get_battle_with_performers(battle_id)
    return templates.TemplateResponse(...)

@router.post("/{battle_id}/start")
async def start_battle(battle_id: UUID, ...):
    """
    Start a battle (PENDING → ACTIVE).

    Permissions: Staff only
    """
    battle = await battle_repo.get_by_id(battle_id)
    battle.status = BattleStatus.ACTIVE
    await battle_repo.update(battle)

    return RedirectResponse(
        url=f"/battles/{battle_id}", status_code=303
    )

@router.get("/{battle_id}/encode", response_class=HTMLResponse)
async def encode_battle_form(battle_id: UUID, ...):
    """
    Show encoding form based on battle phase.

    Templates:
    - battles/encode_preselection.html (score input 0-10)
    - battles/encode_pool.html (winner selection or draw)
    - battles/encode_tiebreak.html (winner selection)
    - battles/encode_finals.html (winner selection)

    Permissions: Staff only
    """
    battle = await battle_repo.get_battle_with_performers(battle_id)

    template_map = {
        BattlePhase.PRESELECTION: "encode_preselection.html",
        BattlePhase.POOLS: "encode_pool.html",
        BattlePhase.TIEBREAK: "encode_tiebreak.html",
        BattlePhase.FINALS: "encode_finals.html",
    }

    return templates.TemplateResponse(
        f"battles/{template_map[battle.phase]}",
        {"battle": battle, ...}
    )

@router.post("/{battle_id}/encode")
async def encode_battle(request: Request, battle_id: UUID, ...):
    """
    Submit battle results (phase-dependent logic).

    PRESELECTION:
    - Parse scores from form (score_<performer_id>)
    - Update performer.preselection_score

    POOLS:
    - Parse winner_id or is_draw flag
    - Update pool_wins/draws/losses

    TIEBREAK:
    - Parse winner_id
    - Update tiebreak_winner

    FINALS:
    - Parse winner_id
    - Update finals_winner

    Permissions: Staff only
    """
    form_data = await request.form()
    battle = await battle_repo.get_battle_with_performers(battle_id)

    if battle.phase == BattlePhase.PRESELECTION:
        for performer in battle.performers:
            score_key = f"score_{performer.id}"
            score = float(form_data[score_key])
            performer.preselection_score = score
            await performer_repo.update(performer)

    elif battle.phase == BattlePhase.POOLS:
        is_draw = form_data.get("is_draw") == "true"

        if is_draw:
            # Mark draw for both performers
            for performer in battle.performers:
                performer.pool_draws = (performer.pool_draws or 0) + 1
                await performer_repo.update(performer)
        else:
            winner_id = UUID(form_data["winner_id"])
            for performer in battle.performers:
                if performer.id == winner_id:
                    performer.pool_wins = (performer.pool_wins or 0) + 1
                else:
                    performer.pool_losses = (performer.pool_losses or 0) + 1
                await performer_repo.update(performer)

    # Mark battle as completed
    battle.status = BattleStatus.COMPLETED
    await battle_repo.update(battle)

    return RedirectResponse(
        url=f"/battles/{battle_id}", status_code=303
    )
```

**Templates**:
- `battles/list.html`: Grid view with status filters
- `battles/detail.html`: Battle details with performer cards
- `battles/encode_preselection.html`: Score input (0-10)
- `battles/encode_pool.html`: Winner selection or draw
- `battles/encode_tiebreak.html`: Winner selection with stats
- `pools/overview.html`: Pool standings table

### Battle Outcome Types

The system uses different outcome types for different phases:

| Outcome Type | Used In | Description |
|--------------|---------|-------------|
| `SCORED` | Preselection | Performers scored 0-10 by judges |
| `WIN_DRAW_LOSS` | Pools | Winner/draw/loser for round-robin |
| `TIEBREAK` | Tiebreak | Special voting (KEEP/ELIMINATE) |
| `WIN_LOSS` | Finals | Simple winner/loser for bracket |

---

## Phase Transition Hooks

### Purpose

Phase transition hooks automatically generate battles and pools when advancing tournament phases. This ensures all required battles exist before entering a new phase.

### Implementation

**File**: `app/services/tournament_service.py:185-248`

```python
async def _execute_phase_transition_hooks(
    self, tournament: Tournament
) -> None:
    """
    Execute phase-specific hooks when transitioning to next phase.

    Generates battles and pools based on current phase before advancing.

    Raises:
        ValidationError: If battle/pool generation fails

    See: ROADMAP.md §2.4 Phase Transition Hooks
    """

    # REGISTRATION → PRESELECTION: Generate preselection battles
    if tournament.phase == TournamentPhase.REGISTRATION:
        if self._battle_service is None:
            return

        categories = await self.category_repo.get_by_tournament(
            tournament.id
        )

        for category in categories:
            # Generate one battle per performer
            await self._battle_service.generate_preselection_battles(
                category.id
            )

    # PRESELECTION → POOLS: Create pools + generate pool battles
    elif tournament.phase == TournamentPhase.PRESELECTION:
        if self._pool_service is None or self._battle_service is None:
            return

        categories = await self.category_repo.get_by_tournament(
            tournament.id
        )

        for category in categories:
            # Create pools from qualification results
            pools = await self._pool_service.create_pools_from_preselection(
                category.id, category.groups_ideal
            )

            # Generate round-robin battles for each pool
            for pool in pools:
                await self._battle_service.generate_pool_battles(
                    category.id, pool.id
                )

    # POOLS → FINALS: Generate finals bracket battles
    elif tournament.phase == TournamentPhase.POOLS:
        if self._battle_service is None:
            return

        categories = await self.category_repo.get_by_tournament(
            tournament.id
        )

        for category in categories:
            # Generate bracket battles from pool winners
            await self._battle_service.generate_finals_battles(
                category.id
            )

    # FINALS → COMPLETED: No hooks needed
    elif tournament.phase == TournamentPhase.FINALS:
        pass
```

### Hook Execution Order

1. **Validation**: Check if tournament can advance (via `_validate_phase_advance()`)
2. **Auto-Activation**: Activate tournament if advancing from REGISTRATION (if no other active tournament)
3. **Hook Execution**: Generate battles/pools BEFORE advancing phase
4. **Phase Advancement**: Update tournament.phase to next phase
5. **Database Commit**: Persist changes

This order ensures battles/pools exist when entering the new phase.

---

## Tiebreak Auto-Detection Pattern

### Purpose

Tiebreak auto-detection ensures that tie situations are automatically detected and tiebreak battles are created without manual intervention. This is triggered when the last battle of a phase is completed.

### Business Rules

- **BR-TIE-001**: Preselection tiebreak auto-created when last preselection battle scored
- **BR-TIE-002**: Pool winner tiebreak auto-created when last pool battle completed
- **BR-TIE-003**: All performers with the boundary score must compete in tiebreak

### Implementation Pattern

**Integration Point**: `BattleResultsEncodingService` triggers tiebreak detection after encoding.

```python
# app/services/battle_results_encoding_service.py

async def encode_preselection_battle(
    self, battle_id: UUID, scores: dict[UUID, Decimal]
) -> ValidationResult[Battle]:
    """Encode preselection battle and trigger tiebreak detection.

    After encoding, checks if this was the last preselection battle
    and triggers tiebreak detection if needed.
    """
    # 1. Validate and encode (existing logic)
    # ... validation code ...

    async with self.session.begin():
        # Update battle and performers
        # ... encoding code ...

        # 2. Check if this was the last preselection battle
        remaining_battles = await self.battle_repo.count_pending_by_category_and_phase(
            battle.category_id, BattlePhase.PRESELECTION
        )

        if remaining_battles == 0:
            # 3. Last battle completed - check for ties
            tiebreak = await self.tiebreak_service.detect_and_create_preselection_tiebreak(
                battle.category_id
            )
            if tiebreak:
                return ValidationResult.success(
                    battle,
                    warnings=[f"Tiebreak battle created for {len(tiebreak.performers)} tied performers"]
                )

    return ValidationResult.success(battle)
```

### TiebreakService Methods

```python
# app/services/tiebreak_service.py

async def detect_and_create_preselection_tiebreak(
    self, category_id: UUID
) -> Optional[Battle]:
    """Detect preselection ties and create tiebreak battle if needed.

    Called automatically when last preselection battle is completed.

    Business Rule BR-TIE-001: Tiebreak auto-created when last battle scored.
    Business Rule BR-TIE-003: ALL performers with boundary score compete.

    Returns:
        Created tiebreak battle or None if no tie
    """
    # 1. Get category config and performers
    category = await self.category_repo.get_by_id(category_id)
    performers = await self.performer_repo.get_by_category(category_id)

    # 2. Calculate pool capacity (how many qualify)
    pool_capacity, _, _ = calculate_pool_capacity(
        len(performers),
        category.groups_ideal,
        category.performers_ideal
    )

    # 3. Detect ties at boundary
    tied_performers = await self.detect_preselection_ties(
        category_id, pool_capacity
    )

    if not tied_performers:
        return None

    # 4. Calculate winners needed
    boundary_score = tied_performers[0].preselection_score
    performers_above = [
        p for p in performers
        if p.preselection_score > boundary_score
    ]
    winners_needed = pool_capacity - len(performers_above)

    # 5. Create tiebreak battle
    return await self.create_tiebreak_battle(
        category_id,
        tied_performers,
        winners_needed
    )


async def detect_and_create_pool_winner_tiebreak(
    self, pool_id: UUID
) -> Optional[Battle]:
    """Detect pool winner ties and create tiebreak battle if needed.

    Called when last pool battle is completed.

    Business Rule BR-TIE-002: Pool winner tiebreak auto-created.
    """
    pool = await self.pool_repo.get_by_id(pool_id)

    # Find performers with highest points
    max_points = max(p.pool_points for p in pool.performers)
    tied_performers = [
        p for p in pool.performers
        if p.pool_points == max_points
    ]

    if len(tied_performers) == 1:
        # Clear winner, no tiebreak needed
        return None

    # Create tiebreak for pool winner (exactly 1 winner needed)
    return await self.create_tiebreak_battle(
        pool.category_id,
        tied_performers,
        winners_needed=1
    )
```

### Sequence Diagram

```
┌────────────┐    ┌─────────────────────┐    ┌────────────────┐    ┌────────────┐
│   Router   │    │ EncodingService     │    │ TiebreakService│    │ BattleRepo │
└─────┬──────┘    └──────────┬──────────┘    └───────┬────────┘    └─────┬──────┘
      │                      │                       │                   │
      │ encode_preselection()│                       │                   │
      │─────────────────────>│                       │                   │
      │                      │                       │                   │
      │                      │ update battle/perfs   │                   │
      │                      │───────────────────────│───────────────────>
      │                      │                       │                   │
      │                      │ count_pending_battles │                   │
      │                      │───────────────────────│───────────────────>
      │                      │                       │                   │
      │                      │ (remaining = 0)       │                   │
      │                      │                       │                   │
      │                      │ detect_and_create_tiebreak()              │
      │                      │──────────────────────>│                   │
      │                      │                       │                   │
      │                      │                       │ calculate capacity│
      │                      │                       │ detect ties       │
      │                      │                       │ create battle     │
      │                      │                       │───────────────────>
      │                      │                       │                   │
      │                      │<──────────────────────│                   │
      │                      │    tiebreak_battle    │                   │
      │                      │                       │                   │
      │<─────────────────────│                       │                   │
      │  ValidationResult    │                       │                   │
      │  (with warning)      │                       │                   │
```

### Why Trigger on Last Battle Completion (Not Phase Advance)?

1. **Immediate feedback**: User sees tiebreak created immediately after scoring
2. **No race conditions**: Tiebreak detected before any phase advance attempt
3. **Atomic operation**: Tiebreak creation is part of encoding transaction
4. **Clear UX**: Flash message informs user of tiebreak creation

### Transaction Safety

Tiebreak detection and creation happens within the encoding transaction:

```python
async with self.session.begin():
    # 1. Update battle outcome
    # 2. Update performer stats
    # 3. Count remaining battles
    # 4. If last battle: detect and create tiebreak

    # All committed together or rolled back on error
```

This prevents orphaned tiebreak battles if encoding fails.

### Dependency Injection



**File**: `app/dependencies.py:295-327`

```python
def get_tournament_service(session: AsyncSession = Depends(get_db)):
    """Get TournamentService with battle/pool services injected."""
    from app.services.tournament_service import TournamentService
    from app.services.battle_service import BattleService
    from app.services.pool_service import PoolService

    # Create repositories
    tournament_repo = TournamentRepository(session)
    category_repo = CategoryRepository(session)
    performer_repo = PerformerRepository(session)
    battle_repo = BattleRepository(session)
    pool_repo = PoolRepository(session)

    # Create battle and pool services for phase transitions
    battle_service = BattleService(battle_repo, performer_repo)
    pool_service = PoolService(pool_repo, performer_repo)

    return TournamentService(
        tournament_repo=tournament_repo,
        category_repo=category_repo,
        performer_repo=performer_repo,
        battle_repo=battle_repo,
        pool_repo=pool_repo,
        battle_service=battle_service,  # Injected for hooks
        pool_service=pool_service,      # Injected for hooks
    )
```

### Why Optional Services?

The `battle_service` and `pool_service` parameters are optional (`None` default) to maintain backward compatibility and allow TournamentService to be instantiated without them (e.g., in tests that don't need phase transitions).

---

## HTMX Patterns

### Live Search with Debounce

```html
<!-- In templates/ -->
<input
    type="text"
    name="query"
    hx-get="/api/search"
    hx-trigger="keyup changed delay:500ms"
    hx-target="#results"
    hx-swap="innerHTML"
    placeholder="Search dancers..."
>
<div id="results"></div>
```

**Backend:**

```python
@router.get("/api/search")
async def search_api(
    query: str = "",
    service: SomeService = Depends(get_some_service),
):
    """HTMX endpoint for live search."""
    results = await service.search(query)

    return templates.TemplateResponse(
        "_table.html",  # Partial template
        {"results": results}
    )
```

### Inline Validation

```html
<input
    name="email"
    hx-post="/api/validate/email"
    hx-trigger="change"
    hx-target="next .error"
>
<div class="error"></div>
```

### Delete Confirmation

```html
<button
    hx-delete="/users/{id}"
    hx-confirm="Are you sure you want to delete this user?"
    hx-target="closest tr"
    hx-swap="outerHTML swap:1s"
>
    Delete
</button>
```

### Form Submission Without Page Reload

```html
<form hx-post="/dancers/create" hx-swap="outerHTML">
    <input type="text" name="first_name" required>
    <input type="email" name="email" required>
    <button type="submit">Create Dancer</button>
</form>
```

---

## Common Pitfalls to Avoid

### 1. ❌ Don't Hardcode Minimum Performers

```python
# ❌ BAD
if performer_count < 4:
    raise ValidationError(["Need at least 4 performers"])
```

```python
# ✅ GOOD
from app.utils.tournament_calculations import calculate_minimum_performers

minimum = calculate_minimum_performers(category.groups_ideal)
if performer_count < minimum:
    raise ValidationError([f"Need at least {minimum} performers"])
```

### 2. ❌ Don't Allow Phase Rollback

```python
# ❌ BAD
tournament.phase = new_phase  # Allows any phase transition
```

```python
# ✅ GOOD
# Only allow forward progression
allowed_transitions = {
    Phase.REGISTRATION: Phase.PRESELECTION,
    Phase.PRESELECTION: Phase.POOLS,
    Phase.POOLS: Phase.FINALS,
    Phase.FINALS: Phase.COMPLETED,
}

if new_phase != allowed_transitions.get(tournament.phase):
    raise ValidationError(["Cannot go backwards or skip phases"])
```

### 3. ❌ Don't Skip Validation in Routers

```python
# ❌ BAD - Router does validation
@router.post("/dancers/create")
async def create_dancer(...):
    if await dancer_repo.email_exists(email):
        raise HTTPException(400, "Email exists")
    # More validation...
```

```python
# ✅ GOOD - Service handles validation
@router.post("/dancers/create")
async def create_dancer(
    service: DancerService = Depends(get_dancer_service),
    ...
):
    try:
        dancer = await service.create_dancer(...)  # Validation inside
        return RedirectResponse(...)
    except ValidationError as e:
        return templates.TemplateResponse("error.html", {"errors": e.errors})
```

### 4. ❌ Don't Forget HTMX Debounce for Search

```html
<!-- ❌ BAD - Fires on every keystroke -->
<input hx-get="/api/search" hx-trigger="keyup">
```

```html
<!-- ✅ GOOD - Debounced search -->
<input hx-get="/api/search" hx-trigger="keyup changed delay:500ms">
```

### 5. ❌ Don't Forget to Activate Virtual Environment

```bash
# ❌ BAD
pytest tests/

# ✅ GOOD
source .venv/bin/activate
pytest tests/
```

---

## Service Layer Reference

### Available Services

#### DancerService

```python
# app/services/dancer_service.py
await dancer_service.create_dancer(email, first_name, last_name, dob, blaze, country, city)
await dancer_service.update_dancer(dancer_id, **fields)
await dancer_service.search_dancers(query)
```

**Validations:**
- Email uniqueness
- Age between 10-100 years

#### TournamentService

```python
# app/services/tournament_service.py
await tournament_service.advance_tournament_phase(tournament_id)
await tournament_service.get_phase_validation(tournament_id)
```

**Validations:**
- Minimum performers per category
- Phase transition rules
- All categories ready before advancing

#### PerformerService

```python
# app/services/performer_service.py
await performer_service.register_performer(tournament_id, category_id, dancer_id, duo_partner_id)
await performer_service.unregister_performer(performer_id)
await performer_service.get_performers_by_category(category_id)
```

**Validations:**
- One dancer per tournament rule
- Duo pairing validation (both dancers available)
- Category type validation (1v1 vs 2v2)

#### BattleService

```python
# app/services/battle_service.py
await battle_service.generate_preselection_battles(category_id)
await battle_service.generate_pool_battles(category_id, pool_id)
await battle_service.generate_finals_battles(category_id)
await battle_service.start_battle(battle_id)
await battle_service.complete_battle(battle_id)
await battle_service.get_battle_queue(category_id, phase, status)
```

**Business Rules:**
- Preselection: One battle per performer
- Pools: Round-robin matchups (all vs all)
- Finals: Single-elimination bracket
- Battle lifecycle: PENDING → ACTIVE → COMPLETED

#### BattleResultsEncodingService

```python
# app/services/battle_results_encoding_service.py
await encoding_service.encode_preselection_results(battle_id, scores)
await encoding_service.encode_pool_results(battle_id, winner_id, is_draw)
await encoding_service.encode_tiebreak_results(battle_id, winner_id)
await encoding_service.encode_finals_results(battle_id, winner_id)
```

**Business Rules:**
- **Preselection:** Scores 0.0-10.0, all performers must be scored, updates performer.preselection_score
- **Pool:** Winner OR draw (mutually exclusive), updates pool points (win=+3, draw=+1, loss=+0)
- **Tiebreak:** Winner required, no draws allowed
- **Finals:** Winner required, determines category champion
- All encoding operations use transactions (battle + performer updates are atomic)
- Validation before persistence (prevents invalid data)

**Transaction Pattern:**
```python
async def encode_preselection_battle(
    self, battle_id: UUID, scores: dict[UUID, Decimal]
) -> ValidationResult[Battle]:
    """Encode preselection battle with transaction management.

    Args:
        battle_id: Battle to encode
        scores: Mapping of performer_id → score (0.0-10.0)

    Returns:
        ValidationResult with battle or list of errors
    """
    # 1. Get battle and validate status
    battle = await self.battle_repo.get_by_id(battle_id)
    if battle.status != BattleStatus.ACTIVE:
        return ValidationResult.failure(["Battle must be ACTIVE to encode"])

    # 2. Validate scores
    errors = self._validate_preselection_scores(battle, scores)
    if errors:
        return ValidationResult.failure(errors)

    # 3. Begin transaction
    async with self.session.begin():
        # Update battle
        await self.battle_repo.update(
            battle.id,
            outcome=scores,
            status=BattleStatus.COMPLETED
        )

        # Update performers
        for performer in battle.performers:
            score = scores[performer.id]
            await self.performer_repo.update(
                performer.id,
                preselection_score=score
            )

        # Commit or rollback (automatic)

    return ValidationResult.success(battle)
```

**Key Features:**
- **Atomic updates:** All changes committed together or none at all
- **Validation first:** Check all rules before any database modifications
- **ValidationResult pattern:** Consistent error handling across all encoding methods
- **Phase-specific logic:** Each battle phase has its own encoding method with appropriate validations

**Error Handling:**
- Returns `ValidationResult.failure(errors)` with list of validation errors
- Transaction automatically rolls back on errors
- Router converts ValidationResult to flash messages for user feedback

#### PoolService

```python
# app/services/pool_service.py
await pool_service.create_pools_from_preselection(category_id, num_pools)
await pool_service.determine_pool_winner(pool_id)
await pool_service.get_pool_standings(pool_id)
```

**Business Rules:**
- Snake draft distribution for fairness
- Points: Win=3, Draw=1, Loss=0
- Tie detection for tiebreak battles

#### TiebreakService

```python
# app/services/tiebreak_service.py
await tiebreak_service.detect_preselection_tie(category_id, qualification_cutoff)
await tiebreak_service.detect_pool_tie(pool_id)
await tiebreak_service.create_tiebreak_battle(category_id, tied_performer_ids, voting_mode)
await tiebreak_service.process_tiebreak_votes(battle_id, votes)
```

**Business Rules:**
- KEEP mode: N=2 performers (vote for winner)
- ELIMINATE mode: N>2 performers (vote for who to eliminate)
- Multiple voting rounds until one winner remains

---

## Summary

Battle-D's architecture prioritizes:

1. **Separation of concerns** - Each layer has a clear responsibility
2. **Business logic in services** - Not in routers or repositories
3. **Type-safe validation** - ValidationResult pattern for consistent error handling
4. **Dependency injection** - Services and repositories injected via FastAPI
5. **HTMX for interactivity** - Live search, inline validation, dynamic forms
6. **SOLID principles** - Open/Closed, Liskov, Interface Segregation, Dependency Inversion

Following these patterns ensures maintainable, testable, and scalable code.

---

**Last Updated:** 2025-11-26
