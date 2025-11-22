"""Tournament service for business operations."""

from uuid import UUID

from app.exceptions import ValidationError
from app.models.tournament import Tournament, TournamentPhase, TournamentStatus
from app.repositories.battle import BattleRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.pool import PoolRepository
from app.repositories.tournament import TournamentRepository
from app.validators import phase_validators
from app.validators.result import ValidationResult


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
    ):
        """Initialize tournament service.

        Args:
            tournament_repo: Tournament repository
            category_repo: Category repository
            performer_repo: Performer repository
            battle_repo: Battle repository
            pool_repo: Pool repository
        """
        self.tournament_repo = tournament_repo
        self.category_repo = category_repo
        self.performer_repo = performer_repo
        self.battle_repo = battle_repo
        self.pool_repo = pool_repo

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
