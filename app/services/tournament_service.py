"""Tournament service for business operations."""

from uuid import UUID
from typing import TYPE_CHECKING

from app.exceptions import ValidationError
from app.models.tournament import Tournament, TournamentPhase, TournamentStatus
from app.repositories.battle import BattleRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.pool import PoolRepository
from app.repositories.tournament import TournamentRepository
from app.validators import phase_validators
from app.validators.result import ValidationResult

if TYPE_CHECKING:
    from app.services.battle_service import BattleService
    from app.services.pool_service import PoolService


class TournamentService:
    """Service for tournament business operations.

    Handles tournament lifecycle including phase transitions with validation.
    Coordinates between repositories and applies business rules.
    """

    def __init__(
        self,
        tournament_repo: TournamentRepository,
        category_repo: CategoryRepository,
        performer_repo: PerformerRepository,
        battle_repo: BattleRepository,
        pool_repo: PoolRepository,
        battle_service: "BattleService | None" = None,
        pool_service: "PoolService | None" = None,
    ):
        """Initialize tournament service.

        Args:
            tournament_repo: Tournament repository
            category_repo: Category repository
            performer_repo: Performer repository
            battle_repo: Battle repository
            pool_repo: Pool repository
            battle_service: Optional BattleService for phase transitions
            pool_service: Optional PoolService for phase transitions
        """
        self.tournament_repo = tournament_repo
        self.category_repo = category_repo
        self.performer_repo = performer_repo
        self.battle_repo = battle_repo
        self.pool_repo = pool_repo
        self._battle_service = battle_service
        self._pool_service = pool_service

    async def advance_tournament_phase(self, tournament_id: UUID) -> Tournament:
        """Advance tournament to next phase after validation.

        Validates phase transition rules before advancing. Phases are
        one-way only (no rollback permitted).

        Auto-activates tournament (CREATED → ACTIVE) when advancing from
        REGISTRATION phase if validation passes and no other tournament is active.

        Args:
            tournament_id: Tournament UUID

        Returns:
            Updated tournament with new phase

        Raises:
            ValidationError: If validation fails or another tournament is active
            ValueError: If already in final phase

        Examples:
            >>> tournament = await service.advance_tournament_phase(tournament_id)
            >>> print(tournament.phase)  # PRESELECTION (advanced from REGISTRATION)
            >>> print(tournament.status)  # ACTIVE (auto-activated)
        """
        tournament = await self.tournament_repo.get_by_id(tournament_id)
        if not tournament:
            raise ValidationError(["Tournament not found"])

        # Validate phase transition
        result = await self._validate_phase_advance(tournament)
        if not result:
            raise ValidationError(result.errors, result.warnings)

        # Auto-activate tournament when advancing from REGISTRATION
        if (
            tournament.status == TournamentStatus.CREATED
            and tournament.phase == TournamentPhase.REGISTRATION
        ):
            # Check: No other active tournament exists
            active_tournament = await self.tournament_repo.get_active()
            if active_tournament and active_tournament.id != tournament.id:
                raise ValidationError([
                    f"Cannot activate tournament: '{active_tournament.name}' is already active. "
                    "Complete or deactivate it first."
                ])

            # Activate tournament
            tournament.activate()

        # Execute phase transition hooks BEFORE advancing
        await self._execute_phase_transition_hooks(tournament)

        # Advance phase (uses model method)
        tournament.advance_phase()
        await self.tournament_repo.update(
            tournament.id, phase=tournament.phase, status=tournament.status
        )

        # Refresh to get updated instance
        tournament = await self.tournament_repo.get_by_id(tournament.id)
        return tournament

    async def get_phase_validation(self, tournament_id: UUID) -> ValidationResult:
        """Get phase validation result without advancing.

        Useful for checking if tournament is ready to advance and
        showing validation errors/warnings to user before confirming.

        Args:
            tournament_id: Tournament UUID

        Returns:
            ValidationResult with errors/warnings

        Raises:
            ValidationError: If tournament not found
        """
        tournament = await self.tournament_repo.get_by_id(tournament_id)
        if not tournament:
            raise ValidationError(["Tournament not found"])

        return await self._validate_phase_advance(tournament)

    async def _validate_phase_advance(
        self, tournament: Tournament
    ) -> ValidationResult:
        """Validate tournament can advance to next phase.

        Routes to appropriate validator based on current phase.

        Args:
            tournament: Tournament instance

        Returns:
            ValidationResult with pass/fail and messages
        """
        if tournament.phase == TournamentPhase.REGISTRATION:
            return await phase_validators.validate_registration_to_preselection(
                tournament.id,
                self.tournament_repo,
                self.category_repo,
                self.performer_repo,
            )

        elif tournament.phase == TournamentPhase.PRESELECTION:
            return await phase_validators.validate_preselection_to_pools(
                tournament.id,
                self.battle_repo,
                self.category_repo,
                self.performer_repo,
            )

        elif tournament.phase == TournamentPhase.POOLS:
            return await phase_validators.validate_pools_to_finals(
                tournament.id,
                self.battle_repo,
                self.pool_repo,
                self.category_repo,
            )

        elif tournament.phase == TournamentPhase.FINALS:
            return await phase_validators.validate_finals_to_completed(
                tournament.id, self.battle_repo, self.category_repo
            )

        else:
            return ValidationResult.failure(["Tournament already completed"])

    async def _execute_phase_transition_hooks(self, tournament: Tournament) -> None:
        """Execute phase-specific hooks when transitioning to next phase.

        Generates battles and pools based on current phase before advancing.

        Args:
            tournament: Tournament instance (current phase)

        Raises:
            ValidationError: If battle/pool generation fails

        See: ROADMAP.md §2.4 Phase Transition Hooks
        """
        # REGISTRATION → PRESELECTION: Generate preselection battles
        if tournament.phase == TournamentPhase.REGISTRATION:
            if self._battle_service is None:
                # No battle service provided - skip battle generation
                return

            # Get all categories in tournament
            categories = await self.category_repo.get_by_tournament(tournament.id)

            for category in categories:
                # Generate preselection battles for each category
                await self._battle_service.generate_preselection_battles(category.id)

        # PRESELECTION → POOLS: Create pools from preselection results
        elif tournament.phase == TournamentPhase.PRESELECTION:
            if self._pool_service is None or self._battle_service is None:
                # No services provided - skip pool/battle generation
                return

            # Get all categories in tournament
            categories = await self.category_repo.get_by_tournament(tournament.id)

            for category in categories:
                # Create pools from preselection qualification
                pools = await self._pool_service.create_pools_from_preselection(
                    category.id, category.groups_ideal
                )

                # Generate pool battles for each pool
                for pool in pools:
                    await self._battle_service.generate_pool_battles(
                        category.id, pool.id
                    )

        # POOLS → FINALS: Generate finals battles from pool winners
        elif tournament.phase == TournamentPhase.POOLS:
            if self._battle_service is None:
                # No battle service provided - skip battle generation
                return

            # Get all categories in tournament
            categories = await self.category_repo.get_by_tournament(tournament.id)

            for category in categories:
                # Generate finals battles (bracket style)
                await self._battle_service.generate_finals_battles(category.id)

        # FINALS → COMPLETED: No hooks needed
        elif tournament.phase == TournamentPhase.FINALS:
            pass  # Tournament completion has no generation hooks
