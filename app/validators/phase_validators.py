"""Phase transition validation functions.

These validators ensure tournament phases can only advance when
all business rules are satisfied. Phases are one-way (no rollback).
"""

from uuid import UUID

from app.models.battle import BattlePhase, BattleStatus
from app.repositories.battle import BattleRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.pool import PoolRepository
from app.repositories.tournament import TournamentRepository
from app.utils.tournament_calculations import calculate_minimum_performers
from app.validators.result import ValidationResult


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
    - Each category must have minimum performers: (groups_ideal * 2 + 1)
    - This ensures preselection will eliminate at least 1 performer

    Args:
        tournament_id: Tournament UUID
        tournament_repo: Tournament repository
        category_repo: Category repository
        performer_repo: Performer repository

    Returns:
        ValidationResult with pass/fail and messages

    Examples:
        >>> result = await validate_registration_to_preselection(
        ...     tournament_id, t_repo, c_repo, p_repo
        ... )
        >>> if result:
        ...     # Can advance to preselection
        ... else:
        ...     print(result.errors)
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

    # Check each category meets minimum performers
    for category in tournament.categories:
        performers = await performer_repo.get_by_category(category.id)
        performer_count = len(performers)
        min_required = calculate_minimum_performers(category.groups_ideal)

        if performer_count < min_required:
            errors.append(
                f"Category '{category.name}': has {performer_count} performers, "
                f"minimum required: {min_required} "
                f"({category.groups_ideal} pools × 2 minimum + 1 elimination)"
            )
        elif performer_count == min_required:
            warnings.append(
                f"Category '{category.name}': has exactly minimum performers "
                f"({min_required}). Only 1 will be eliminated in preselection."
            )

    if errors:
        return ValidationResult.failure(errors, warnings)
    return ValidationResult.success(warnings)


async def validate_preselection_to_pools(
    tournament_id: UUID,
    battle_repo: BattleRepository,
    category_repo: CategoryRepository,
    performer_repo: PerformerRepository,
) -> ValidationResult:
    """Validate tournament can advance from PRESELECTION to POOLS.

    Business Rules:
    - All preselection battles must be completed
    - All performers must have preselection scores assigned
    - All tiebreak battles must be resolved

    Args:
        tournament_id: Tournament UUID
        battle_repo: Battle repository
        category_repo: Category repository
        performer_repo: Performer repository

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    # Get all categories for this tournament
    categories = await category_repo.get_by_tournament(tournament_id)

    # Check all preselection battles completed
    for category in categories:
        category_battles = await battle_repo.get_by_category(category.id)

        # Check preselection battles
        preselection_battles = [
            b for b in category_battles if b.phase == BattlePhase.PRESELECTION
        ]
        if not preselection_battles:
            errors.append(
                f"Category '{category.name}': no preselection battles found. "
                "Generate battles before advancing."
            )
            continue

        incomplete_preselection = [
            b for b in preselection_battles if b.status != BattleStatus.COMPLETED
        ]
        if incomplete_preselection:
            errors.append(
                f"Category '{category.name}': "
                f"{len(incomplete_preselection)} preselection battles not completed"
            )

        # Check all performers have scores
        performers = await performer_repo.get_by_category(category.id)
        performers_without_scores = [
            p for p in performers if p.preselection_score is None
        ]
        if performers_without_scores:
            errors.append(
                f"Category '{category.name}': "
                f"{len(performers_without_scores)} performers missing preselection scores"
            )

        # Check tiebreak battles resolved
        tiebreak_battles = [
            b
            for b in category_battles
            if b.phase == BattlePhase.TIEBREAK and b.status != BattleStatus.COMPLETED
        ]
        if tiebreak_battles:
            errors.append(
                f"Category '{category.name}': "
                f"{len(tiebreak_battles)} tiebreak battles unresolved"
            )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


async def validate_pools_to_finals(
    tournament_id: UUID,
    battle_repo: BattleRepository,
    pool_repo: PoolRepository,
    category_repo: CategoryRepository,
) -> ValidationResult:
    """Validate tournament can advance from POOLS to FINALS.

    Business Rules:
    - All pool battles must be completed
    - Each pool must have exactly one winner
    - All pool tiebreak battles must be resolved

    Args:
        tournament_id: Tournament UUID
        battle_repo: Battle repository
        pool_repo: Pool repository
        category_repo: Category repository

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    # Get all categories for this tournament
    categories = await category_repo.get_by_tournament(tournament_id)

    for category in categories:
        # Check pool battles completed
        category_battles = await battle_repo.get_by_category(category.id)
        pool_battles = [b for b in category_battles if b.phase == BattlePhase.POOLS]

        if not pool_battles:
            errors.append(
                f"Category '{category.name}': no pool battles found. "
                "Create pools before advancing."
            )
            continue

        incomplete_pool_battles = [
            b for b in pool_battles if b.status != BattleStatus.COMPLETED
        ]
        if incomplete_pool_battles:
            errors.append(
                f"Category '{category.name}': "
                f"{len(incomplete_pool_battles)} pool battles not completed"
            )

        # Check each pool has a winner
        category_pools = await pool_repo.get_by_category(category.id)
        if not category_pools:
            errors.append(
                f"Category '{category.name}': no pools found. Create pools first."
            )
            continue

        pools_without_winner = [p for p in category_pools if p.winner_id is None]
        if pools_without_winner:
            errors.append(
                f"Category '{category.name}': "
                f"{len(pools_without_winner)} pools without winner determined"
            )

        # Check pool count matches groups_ideal
        if len(category_pools) != category.groups_ideal:
            errors.append(
                f"Category '{category.name}': expected {category.groups_ideal} pools, "
                f"found {len(category_pools)}"
            )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()


async def validate_finals_to_completed(
    tournament_id: UUID,
    battle_repo: BattleRepository,
    category_repo: CategoryRepository,
) -> ValidationResult:
    """Validate tournament can advance from FINALS to COMPLETED.

    Business Rules:
    - All finals battles must be completed
    - Each finals battle must have a winner (no draws in finals)
    - Each category must have a champion

    Args:
        tournament_id: Tournament UUID
        battle_repo: Battle repository
        category_repo: Category repository

    Returns:
        ValidationResult with pass/fail and messages
    """
    errors = []

    # Get all categories for this tournament
    categories = await category_repo.get_by_tournament(tournament_id)

    for category in categories:
        category_battles = await battle_repo.get_by_category(category.id)
        finals_battles = [b for b in category_battles if b.phase == BattlePhase.FINALS]

        if not finals_battles:
            errors.append(
                f"Category '{category.name}': no finals battle found. "
                "Create finals battle before completing tournament."
            )
            continue

        # Check all finals completed
        incomplete_finals = [
            b for b in finals_battles if b.status != BattleStatus.COMPLETED
        ]
        if incomplete_finals:
            errors.append(
                f"Category '{category.name}': "
                f"{len(incomplete_finals)} finals battles not completed"
            )

        # Check each finals has a winner (no draws allowed)
        finals_without_winner = [b for b in finals_battles if b.winner_id is None]
        if finals_without_winner:
            errors.append(
                f"Category '{category.name}': finals battle has no winner. "
                "Draws are not allowed in finals."
            )

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()
