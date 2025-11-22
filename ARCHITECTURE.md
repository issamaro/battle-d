# Battle-D Architecture Guide

This document describes the architectural patterns, design principles, and best practices used in the Battle-D web application.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Service Layer Pattern](#service-layer-pattern)
- [Validation Pattern](#validation-pattern)
- [Router Pattern with Services](#router-pattern-with-services)
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

**Last Updated:** 2025-01-19
