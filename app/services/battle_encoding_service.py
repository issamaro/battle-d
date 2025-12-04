"""Battle encoding service with transaction management.

Handles encoding battle results with atomic multi-model updates.
All encoding operations use transactions to ensure data consistency.

See: ARCHITECTURE.md for service layer patterns
See: VALIDATION_RULES.md for encoding validation rules
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.battle import Battle, BattlePhase, BattleStatus
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.validators.battle_validators import (
    validate_preselection_scores,
    validate_pool_outcome,
    validate_tiebreak_outcome,
    validate_finals_outcome,
)
from app.validators.result import ValidationResult


class BattleEncodingService:
    """Service for encoding battle results with transaction management.

    All encoding methods use database transactions to ensure atomicity.
    If any part of the encoding fails, all changes are rolled back.

    Example:
        >>> service = BattleEncodingService(session, battle_repo, performer_repo)
        >>> result = await service.encode_preselection_battle(
        ...     battle_id, {performer1_id: Decimal("8.5"), performer2_id: Decimal("9.0")}
        ... )
        >>> if result:
        ...     print(f"Battle encoded: {result.data.id}")
        >>> else:
        ...     print(f"Validation failed: {result.errors}")
    """

    def __init__(
        self,
        session: AsyncSession,
        battle_repo: BattleRepository,
        performer_repo: PerformerRepository,
    ):
        """Initialize battle encoding service.

        Args:
            session: Database session for transactions
            battle_repo: Battle repository
            performer_repo: Performer repository
        """
        self.session = session
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo

    async def encode_preselection_battle(
        self, battle_id: UUID, scores: dict[UUID, Decimal]
    ) -> ValidationResult:
        """Encode preselection battle with scores.

        Updates battle outcome and performer preselection scores atomically.

        Args:
            battle_id: Battle UUID
            scores: Dictionary mapping performer_id to score (0.0-10.0)

        Returns:
            ValidationResult with success/failure and battle data

        Example:
            >>> result = await service.encode_preselection_battle(
            ...     battle_id,
            ...     {uuid1: Decimal("8.5"), uuid2: Decimal("9.0")}
            ... )
        """
        # Get battle with performers
        battle = await self.battle_repo.get_with_performers(battle_id)
        if not battle:
            return ValidationResult.failure([f"Battle {battle_id} not found"])

        # Validate phase
        if battle.phase != BattlePhase.PRESELECTION:
            return ValidationResult.failure(
                [f"Battle phase is {battle.phase.value}, expected PRESELECTION"]
            )

        # Validate scores using validator
        validation = validate_preselection_scores(battle, scores)
        if not validation:
            return validation

        # Convert scores dict to JSON-serializable format (str keys)
        outcome = {str(performer_id): float(score) for performer_id, score in scores.items()}

        # Begin transaction for atomic multi-model update
        async with self.session.begin():
            # Update battle
            await self.battle_repo.update(
                battle.id,
                outcome=outcome,
                status=BattleStatus.COMPLETED,
            )

            # Update each performer's preselection score
            for performer_id, score in scores.items():
                await self.performer_repo.update(
                    performer_id,
                    preselection_score=score,
                )

        # Refresh battle to get updated state
        await self.session.refresh(battle)

        return ValidationResult.success(validation.warnings)

    async def encode_pool_battle(
        self,
        battle_id: UUID,
        winner_id: Optional[UUID],
        is_draw: bool,
    ) -> ValidationResult:
        """Encode pool battle with winner or draw.

        Updates battle outcome and performer pool stats atomically.

        Pool Points:
        - Win: +3 points, pool_wins +1
        - Draw: +1 point each, pool_draws +1
        - Loss: +0 points, pool_losses +1

        Args:
            battle_id: Battle UUID
            winner_id: Winner performer UUID (None if draw)
            is_draw: Whether battle is a draw

        Returns:
            ValidationResult with success/failure and battle data

        Example:
            >>> # Record a win
            >>> result = await service.encode_pool_battle(
            ...     battle_id, winner_id=uuid1, is_draw=False
            ... )
            >>> # Record a draw
            >>> result = await service.encode_pool_battle(
            ...     battle_id, winner_id=None, is_draw=True
            ... )
        """
        # Get battle with performers
        battle = await self.battle_repo.get_with_performers(battle_id)
        if not battle:
            return ValidationResult.failure([f"Battle {battle_id} not found"])

        # Validate phase
        if battle.phase != BattlePhase.POOLS:
            return ValidationResult.failure(
                [f"Battle phase is {battle.phase.value}, expected POOLS"]
            )

        # Validate outcome using validator
        validation = validate_pool_outcome(battle, winner_id, is_draw)
        if not validation:
            return validation

        # Build outcome data
        outcome = {
            "winner_id": str(winner_id) if winner_id else None,
            "is_draw": is_draw,
        }

        # Begin transaction for atomic multi-model update
        async with self.session.begin():
            # Update battle
            update_fields = {
                "outcome": outcome,
                "status": BattleStatus.COMPLETED,
            }
            if winner_id:
                update_fields["winner_id"] = winner_id

            await self.battle_repo.update(battle.id, **update_fields)

            # Update performer pool stats
            if is_draw:
                # Both performers get +1 draw
                for performer in battle.performers:
                    await self.performer_repo.update(
                        performer.id,
                        pool_draws=(performer.pool_draws or 0) + 1,
                    )
            else:
                # Winner gets +1 win, loser gets +1 loss
                for performer in battle.performers:
                    if performer.id == winner_id:
                        await self.performer_repo.update(
                            performer.id,
                            pool_wins=(performer.pool_wins or 0) + 1,
                        )
                    else:
                        await self.performer_repo.update(
                            performer.id,
                            pool_losses=(performer.pool_losses or 0) + 1,
                        )

        # Refresh battle to get updated state
        await self.session.refresh(battle)

        return ValidationResult.success(validation.warnings)

    async def encode_tiebreak_battle(
        self,
        battle_id: UUID,
        winner_id: UUID,
    ) -> ValidationResult:
        """Encode tiebreak battle with winner.

        Tiebreak battles cannot be draws - a winner must be declared.

        Args:
            battle_id: Battle UUID
            winner_id: Winner performer UUID

        Returns:
            ValidationResult with success/failure and battle data

        Example:
            >>> result = await service.encode_tiebreak_battle(
            ...     battle_id, winner_id=uuid1
            ... )
        """
        # Get battle with performers
        battle = await self.battle_repo.get_with_performers(battle_id)
        if not battle:
            return ValidationResult.failure([f"Battle {battle_id} not found"])

        # Validate phase
        if battle.phase != BattlePhase.TIEBREAK:
            return ValidationResult.failure(
                [f"Battle phase is {battle.phase.value}, expected TIEBREAK"]
            )

        # Validate outcome using validator
        validation = validate_tiebreak_outcome(battle, winner_id)
        if not validation:
            return validation

        # Build outcome data (using "winners" list for tiebreak format)
        outcome = {"winners": [str(winner_id)]}

        # Begin transaction for atomic update
        async with self.session.begin():
            await self.battle_repo.update(
                battle.id,
                outcome=outcome,
                winner_id=winner_id,
                status=BattleStatus.COMPLETED,
            )

        # Refresh battle to get updated state
        await self.session.refresh(battle)

        return ValidationResult.success(validation.warnings)

    async def encode_finals_battle(
        self,
        battle_id: UUID,
        winner_id: UUID,
    ) -> ValidationResult:
        """Encode finals battle with winner.

        Finals battles cannot be draws - a winner must be declared.

        Args:
            battle_id: Battle UUID
            winner_id: Winner performer UUID (category champion)

        Returns:
            ValidationResult with success/failure and battle data

        Example:
            >>> result = await service.encode_finals_battle(
            ...     battle_id, winner_id=uuid1
            ... )
        """
        # Get battle with performers
        battle = await self.battle_repo.get_with_performers(battle_id)
        if not battle:
            return ValidationResult.failure([f"Battle {battle_id} not found"])

        # Validate phase
        if battle.phase != BattlePhase.FINALS:
            return ValidationResult.failure(
                [f"Battle phase is {battle.phase.value}, expected FINALS"]
            )

        # Validate outcome using validator
        validation = validate_finals_outcome(battle, winner_id)
        if not validation:
            return validation

        # Build outcome data
        outcome = {"winner_id": str(winner_id)}

        # Begin transaction for atomic update
        async with self.session.begin():
            await self.battle_repo.update(
                battle.id,
                outcome=outcome,
                winner_id=winner_id,
                status=BattleStatus.COMPLETED,
            )

        # Refresh battle to get updated state
        await self.session.refresh(battle)

        return ValidationResult.success(validation.warnings)

    async def encode_battle(
        self,
        battle_id: UUID,
        **encoding_data,
    ) -> ValidationResult:
        """Encode a battle based on its phase.

        Routes to the appropriate phase-specific encoding method.

        Args:
            battle_id: Battle UUID
            **encoding_data: Phase-specific encoding data
                - Preselection: scores: dict[UUID, Decimal]
                - Pools: winner_id: Optional[UUID], is_draw: bool
                - Tiebreak: winner_id: UUID
                - Finals: winner_id: UUID

        Returns:
            ValidationResult with success/failure and battle data

        Raises:
            ValueError: If unknown battle phase

        Example:
            >>> # Automatically routes to correct encoder
            >>> result = await service.encode_battle(
            ...     battle_id,
            ...     scores={uuid1: Decimal("8.5"), uuid2: Decimal("9.0")}
            ... )
        """
        # Get battle to determine phase
        battle = await self.battle_repo.get_by_id(battle_id)
        if not battle:
            return ValidationResult.failure([f"Battle {battle_id} not found"])

        # Route to phase-specific encoder
        if battle.phase == BattlePhase.PRESELECTION:
            scores = encoding_data.get("scores", {})
            return await self.encode_preselection_battle(battle_id, scores)

        elif battle.phase == BattlePhase.POOLS:
            winner_id = encoding_data.get("winner_id")
            is_draw = encoding_data.get("is_draw", False)
            return await self.encode_pool_battle(battle_id, winner_id, is_draw)

        elif battle.phase == BattlePhase.TIEBREAK:
            winner_id = encoding_data.get("winner_id")
            if not winner_id:
                return ValidationResult.failure(["Winner ID required for tiebreak battles"])
            return await self.encode_tiebreak_battle(battle_id, winner_id)

        elif battle.phase == BattlePhase.FINALS:
            winner_id = encoding_data.get("winner_id")
            if not winner_id:
                return ValidationResult.failure(["Winner ID required for finals battles"])
            return await self.encode_finals_battle(battle_id, winner_id)

        else:
            raise ValueError(f"Unknown battle phase: {battle.phase}")
