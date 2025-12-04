"""Battle encoding and lifecycle validation functions.

These validators ensure battles can only be encoded and transitioned
when all business rules are satisfied.

See: VALIDATION_RULES.md for complete validation rules
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.models.battle import Battle, BattlePhase, BattleStatus
from app.validators.result import ValidationResult


def validate_preselection_scores(
    battle: Battle,
    scores: dict[UUID, Decimal]
) -> ValidationResult:
    """Validate preselection battle scores.

    Business Rules:
    - All performers must be scored
    - Scores must be in range 0.0-10.0
    - Score precision: maximum 2 decimal places

    Args:
        battle: Battle being encoded
        scores: Dictionary mapping performer_id to score

    Returns:
        ValidationResult with pass/fail and messages

    Examples:
        >>> result = validate_preselection_scores(battle, {
        ...     uuid1: Decimal("8.5"),
        ...     uuid2: Decimal("9.0")
        ... })
        >>> if not result:
        ...     print(result.errors)
    """
    errors = []
    warnings = []

    if not battle.performers:
        return ValidationResult.failure(["Battle has no performers"])

    # Check all performers are scored
    performer_ids = {p.id for p in battle.performers}
    scored_ids = set(scores.keys())

    missing_scores = performer_ids - scored_ids
    if missing_scores:
        errors.append(
            f"Missing scores for {len(missing_scores)} performer(s): "
            f"{', '.join(str(pid) for pid in missing_scores)}"
        )

    extra_scores = scored_ids - performer_ids
    if extra_scores:
        warnings.append(
            f"Scores provided for {len(extra_scores)} performer(s) not in battle "
            "(will be ignored)"
        )

    # Validate each score
    for performer_id, score in scores.items():
        # Skip validation for performers not in battle (already warned)
        if performer_id not in performer_ids:
            continue

        # Check range
        if not (Decimal("0.0") <= score <= Decimal("10.0")):
            errors.append(
                f"Performer {performer_id}: score {score} out of range (0.0-10.0)"
            )

        # Check precision (max 2 decimal places)
        # Convert to string and check decimal places
        score_str = str(score)
        if "." in score_str:
            decimal_places = len(score_str.split(".")[1])
            if decimal_places > 2:
                errors.append(
                    f"Performer {performer_id}: score {score} has too many decimal places "
                    f"(max 2 allowed)"
                )

    if errors:
        return ValidationResult.failure(errors, warnings)
    return ValidationResult.success(warnings)


def validate_pool_outcome(
    battle: Battle,
    winner_id: Optional[UUID],
    is_draw: bool
) -> ValidationResult:
    """Validate pool battle outcome.

    Business Rules:
    - Must specify winner OR draw (mutually exclusive)
    - If winner specified, must be one of battle performers
    - Pool battles can have draws

    Args:
        battle: Battle being encoded
        winner_id: Winner performer UUID (None if draw)
        is_draw: Whether battle is a draw

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    if not battle.performers:
        return ValidationResult.failure(["Battle has no performers"])

    # Check mutually exclusive: winner XOR draw
    if is_draw and winner_id:
        errors.append("Cannot specify both winner and draw - must be one or the other")

    if not is_draw and not winner_id:
        errors.append("Must specify either a winner or mark as draw")

    # If winner specified, validate it's a battle performer
    if winner_id:
        performer_ids = {p.id for p in battle.performers}
        if winner_id not in performer_ids:
            errors.append(
                f"Winner {winner_id} is not a performer in this battle. "
                f"Valid performers: {', '.join(str(pid) for pid in performer_ids)}"
            )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_tiebreak_outcome(
    battle: Battle,
    winner_id: UUID
) -> ValidationResult:
    """Validate tiebreak battle outcome.

    Business Rules:
    - Must have exactly one winner
    - Winner must be one of battle performers
    - No draws allowed in tiebreaks

    Args:
        battle: Battle being encoded
        winner_id: Winner performer UUID

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    if not battle.performers:
        return ValidationResult.failure(["Battle has no performers"])

    if not winner_id:
        errors.append("Tiebreak battles must have a winner - draws not allowed")

    # Validate winner is a battle performer
    performer_ids = {p.id for p in battle.performers}
    if winner_id not in performer_ids:
        errors.append(
            f"Winner {winner_id} is not a performer in this battle. "
            f"Valid performers: {', '.join(str(pid) for pid in performer_ids)}"
        )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_finals_outcome(
    battle: Battle,
    winner_id: UUID
) -> ValidationResult:
    """Validate finals battle outcome.

    Business Rules:
    - Must have exactly one winner
    - Winner must be one of battle performers
    - No draws allowed in finals

    Args:
        battle: Battle being encoded
        winner_id: Winner performer UUID

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    if not battle.performers:
        return ValidationResult.failure(["Battle has no performers"])

    if not winner_id:
        errors.append("Finals battles must have a winner - draws not allowed")

    # Validate winner is a battle performer
    performer_ids = {p.id for p in battle.performers}
    if winner_id not in performer_ids:
        errors.append(
            f"Winner {winner_id} is not a performer in this battle. "
            f"Valid performers: {', '.join(str(pid) for pid in performer_ids)}"
        )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_battle_can_start(
    battle: Battle,
    active_battle: Optional[Battle] = None
) -> ValidationResult:
    """Validate a battle can be started.

    Business Rules:
    - Battle must be in PENDING status
    - No other battle can be ACTIVE

    Args:
        battle: Battle to start
        active_battle: Currently active battle (if any)

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    if battle.status != BattleStatus.PENDING:
        errors.append(
            f"Cannot start battle: status is {battle.status.value}, must be PENDING"
        )

    if active_battle:
        errors.append(
            f"Cannot start battle: another battle ({active_battle.id}) is already ACTIVE. "
            "Complete or cancel the active battle first."
        )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_battle_can_complete(battle: Battle) -> ValidationResult:
    """Validate a battle can be completed.

    Business Rules:
    - Battle must be in ACTIVE status
    - Battle must have outcome data

    Args:
        battle: Battle to complete

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    if battle.status != BattleStatus.ACTIVE:
        errors.append(
            f"Cannot complete battle: status is {battle.status.value}, must be ACTIVE"
        )

    if not battle.outcome:
        errors.append(
            "Cannot complete battle: outcome data is missing. Encode results first."
        )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


def validate_battle_encoding(
    battle: Battle,
    **encoding_data
) -> ValidationResult:
    """Validate battle encoding based on phase.

    Routes to appropriate phase-specific validator.

    Args:
        battle: Battle being encoded
        **encoding_data: Phase-specific encoding data
            - Preselection: scores: dict[UUID, Decimal]
            - Pools: winner_id: Optional[UUID], is_draw: bool
            - Tiebreak: winner_id: UUID
            - Finals: winner_id: UUID

    Returns:
        ValidationResult with pass/fail and messages

    Raises:
        ValueError: If unknown battle phase
    """
    if battle.phase == BattlePhase.PRESELECTION:
        scores = encoding_data.get("scores", {})
        return validate_preselection_scores(battle, scores)

    elif battle.phase == BattlePhase.POOLS:
        winner_id = encoding_data.get("winner_id")
        is_draw = encoding_data.get("is_draw", False)
        return validate_pool_outcome(battle, winner_id, is_draw)

    elif battle.phase == BattlePhase.TIEBREAK:
        winner_id = encoding_data.get("winner_id")
        if not winner_id:
            return ValidationResult.failure(["Winner ID required for tiebreak battles"])
        return validate_tiebreak_outcome(battle, winner_id)

    elif battle.phase == BattlePhase.FINALS:
        winner_id = encoding_data.get("winner_id")
        if not winner_id:
            return ValidationResult.failure(["Winner ID required for finals battles"])
        return validate_finals_outcome(battle, winner_id)

    else:
        raise ValueError(f"Unknown battle phase: {battle.phase}")
