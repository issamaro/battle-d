"""Battle service for battle generation and management.

See: ROADMAP.md §2.1 Battle Generation Services
"""
import random
import uuid
from typing import List, Optional
from itertools import combinations

from app.exceptions import ValidationError
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.models.performer import Performer
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository


class BattleService:
    """Service for battle generation and lifecycle management.

    Handles:
    - Battle generation for all phases (preselection, pools, finals)
    - Battle queue management (one active at a time)
    - Battle status transitions (pending → active → completed)

    See: DOMAIN_MODEL.md for battle rules and phases
    """

    def __init__(
        self, battle_repo: BattleRepository, performer_repo: PerformerRepository
    ):
        """Initialize battle service.

        Args:
            battle_repo: Battle repository
            performer_repo: Performer repository
        """
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo

    async def generate_preselection_battles(
        self, category_id: uuid.UUID
    ) -> List[Battle]:
        """Generate preselection battles for a category.

        Creates 1v1 battles with random pairing. If odd number of performers,
        creates one 3-way battle with the remaining performers.

        Args:
            category_id: Category UUID

        Returns:
            List of created battles

        Raises:
            ValidationError: If category has no performers
        """
        # Get all performers in category
        performers = await self.performer_repo.get_by_category(category_id)

        if not performers:
            raise ValidationError(["Cannot generate battles: no performers in category"])

        # Shuffle for random pairing
        performer_list = list(performers)
        random.shuffle(performer_list)

        battles = []
        num_performers = len(performer_list)

        # If exactly 3 performers, create one 3-way battle
        if num_performers == 3:
            battle = Battle(
                category_id=category_id,
                phase=BattlePhase.PRESELECTION,
                status=BattleStatus.PENDING,
                outcome_type=BattleOutcomeType.SCORED,
            )
            battle.performers = performer_list
            created_battle = await self.battle_repo.create(battle)
            battles.append(created_battle)
        else:
            # Create 1v1 battles, leaving last 3 if odd number > 1
            i = 0
            # Stop 3 performers early if odd number (to make a 3-way battle)
            limit = num_performers - 3 if num_performers % 2 == 1 and num_performers > 3 else num_performers

            while i + 1 < limit:
                battle = Battle(
                    category_id=category_id,
                    phase=BattlePhase.PRESELECTION,
                    status=BattleStatus.PENDING,
                    outcome_type=BattleOutcomeType.SCORED,
                )
                battle.performers = [performer_list[i], performer_list[i + 1]]
                created_battle = await self.battle_repo.create(battle)
                battles.append(created_battle)
                i += 2

            # If we have remaining performers (should be 3 for odd numbers > 3, or 2 for even)
            if i < num_performers:
                battle = Battle(
                    category_id=category_id,
                    phase=BattlePhase.PRESELECTION,
                    status=BattleStatus.PENDING,
                    outcome_type=BattleOutcomeType.SCORED,
                )
                battle.performers = performer_list[i:]
                created_battle = await self.battle_repo.create(battle)
                battles.append(created_battle)

        return battles

    async def generate_pool_battles(self, pool_id: uuid.UUID) -> List[Battle]:
        """Generate round-robin pool battles.

        Creates all vs all battles within the pool.

        Args:
            pool_id: Pool UUID

        Returns:
            List of created battles

        Raises:
            ValidationError: If pool not found or has no performers
        """
        # Get pool with performers
        pool = await self.performer_repo.get_pool_with_performers(pool_id)

        if not pool:
            raise ValidationError([f"Pool {pool_id} not found"])

        if not pool.performers:
            raise ValidationError([f"Pool {pool_id} has no performers"])

        battles = []

        # Generate all possible pairings (round-robin)
        performer_list = list(pool.performers)
        pairings = list(combinations(performer_list, 2))

        for p1, p2 in pairings:
            battle = Battle(
                category_id=pool.category_id,
                phase=BattlePhase.POOLS,
                status=BattleStatus.PENDING,
                outcome_type=BattleOutcomeType.WIN_DRAW_LOSS,
            )
            battle.performers = [p1, p2]
            created_battle = await self.battle_repo.create(battle)
            battles.append(created_battle)

        return battles

    async def generate_finals_battles(self, category_id: uuid.UUID) -> List[Battle]:
        """Generate finals battles for a category.

        Creates a battle with all pool winners.

        Args:
            category_id: Category UUID

        Returns:
            List containing the finals battle

        Raises:
            ValidationError: If no pool winners found
        """
        # Get all pool winners for this category
        winners = await self.performer_repo.get_pool_winners(category_id)

        if not winners:
            raise ValidationError(
                [f"Cannot generate finals: no pool winners for category {category_id}"]
            )

        if len(winners) < 2:
            raise ValidationError(
                [f"Cannot generate finals: need at least 2 pool winners, got {len(winners)}"]
            )

        # Create finals battle with all winners
        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.FINALS,
            status=BattleStatus.PENDING,
            outcome_type=BattleOutcomeType.WIN_LOSS,
        )
        battle.performers = winners
        created_battle = await self.battle_repo.create(battle)

        return [created_battle]

    async def start_battle(self, battle_id: uuid.UUID) -> Battle:
        """Start a battle (transition pending → active).

        Args:
            battle_id: Battle UUID

        Returns:
            Updated battle

        Raises:
            ValidationError: If battle not found, not pending, or another battle is active
        """
        # Get battle
        battle = await self.battle_repo.get_by_id(battle_id)
        if not battle:
            raise ValidationError([f"Battle {battle_id} not found"])

        # Verify status is pending
        if battle.status != BattleStatus.PENDING:
            raise ValidationError(
                [f"Cannot start battle: status is {battle.status}, must be PENDING"]
            )

        # Check if any other battle is active
        active_battle = await self.battle_repo.get_active_battle()
        if active_battle:
            raise ValidationError(
                [f"Cannot start battle: another battle ({active_battle.id}) is already active"]
            )

        # Update status to active
        battle.status = BattleStatus.ACTIVE
        updated_battle = await self.battle_repo.update(battle)

        return updated_battle

    async def complete_battle(self, battle_id: uuid.UUID) -> Battle:
        """Complete a battle (transition active → completed).

        Args:
            battle_id: Battle UUID

        Returns:
            Updated battle

        Raises:
            ValidationError: If battle not found, not active, or has no outcome
        """
        # Get battle
        battle = await self.battle_repo.get_by_id(battle_id)
        if not battle:
            raise ValidationError([f"Battle {battle_id} not found"])

        # Verify status is active
        if battle.status != BattleStatus.ACTIVE:
            raise ValidationError(
                [f"Cannot complete battle: status is {battle.status}, must be ACTIVE"]
            )

        # Verify outcome data exists
        if not battle.outcome:
            raise ValidationError(
                ["Cannot complete battle: outcome data is missing. Encode results first."]
            )

        # Update status to completed
        battle.status = BattleStatus.COMPLETED
        updated_battle = await self.battle_repo.update(battle)

        return updated_battle

    async def get_next_pending_battle(
        self, tournament_id: uuid.UUID
    ) -> Optional[Battle]:
        """Get the next pending battle for a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            Next pending battle or None if no pending battles
        """
        # Get all pending battles for tournament
        pending_battles = await self.battle_repo.get_by_tournament_and_status(
            tournament_id, BattleStatus.PENDING
        )

        if not pending_battles:
            return None

        # Return first pending battle (FIFO queue)
        return pending_battles[0]

    async def get_active_battle(
        self, tournament_id: Optional[uuid.UUID] = None
    ) -> Optional[Battle]:
        """Get the currently active battle.

        Args:
            tournament_id: Optional tournament UUID to filter by

        Returns:
            Active battle or None
        """
        if tournament_id:
            active_battles = await self.battle_repo.get_by_tournament_and_status(
                tournament_id, BattleStatus.ACTIVE
            )
            return active_battles[0] if active_battles else None

        return await self.battle_repo.get_active_battle()

    async def get_battle_queue(
        self, tournament_id: uuid.UUID
    ) -> dict[BattleStatus, List[Battle]]:
        """Get battle queue organized by status.

        Args:
            tournament_id: Tournament UUID

        Returns:
            Dictionary mapping status to list of battles
        """
        battles = await self.battle_repo.get_by_tournament(tournament_id)

        # Organize by status
        queue = {
            BattleStatus.PENDING: [],
            BattleStatus.ACTIVE: [],
            BattleStatus.COMPLETED: [],
        }

        for battle in battles:
            queue[battle.status].append(battle)

        return queue
