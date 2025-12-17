"""Tiebreak service for tie detection and tiebreak battle management.

See: ROADMAP.md §2.3 Tiebreak Service
See: DOMAIN_MODEL.md §5 Tie-Breaking Logic (BR-TIE-001, BR-TIE-002, BR-TIE-003)
"""
import uuid
from typing import List, Dict, Optional
from decimal import Decimal
from collections import Counter

from app.exceptions import ValidationError
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.models.performer import Performer
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.repositories.category import CategoryRepository
from app.utils.tournament_calculations import calculate_pool_capacity


class TiebreakService:
    """Service for tiebreak detection and resolution.

    Handles:
    - Detecting ties in preselection qualification boundaries
    - Detecting ties in pool winner determination
    - Creating tiebreak battles
    - Processing tiebreak votes (KEEP for N=2, ELIMINATE for N>2)
    - Determining tiebreak winners

    See: DOMAIN_MODEL.md §5 Tie-Breaking Logic
    """

    def __init__(
        self,
        battle_repo: BattleRepository,
        performer_repo: PerformerRepository,
        category_repo: Optional[CategoryRepository] = None,
    ):
        """Initialize tiebreak service.

        Args:
            battle_repo: Battle repository
            performer_repo: Performer repository
            category_repo: Category repository (optional, needed for auto-detection)
        """
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo
        self.category_repo = category_repo

    async def detect_preselection_ties(
        self, category_id: uuid.UUID, pool_capacity: int
    ) -> List[Performer]:
        """Detect ties at preselection qualification boundary.

        Args:
            category_id: Category UUID
            pool_capacity: Number of spots available in pools

        Returns:
            List of tied performers at boundary (empty if no tie)

        Raises:
            ValidationError: If performers missing scores
        """
        # Get all performers with scores
        performers = await self.performer_repo.get_by_category(category_id)

        # Filter to those with scores
        scored_performers = [p for p in performers if p.preselection_score is not None]

        if len(scored_performers) < len(performers):
            raise ValidationError(
                [f"Cannot detect ties: {len(performers) - len(scored_performers)} performers missing scores"]
            )

        # Sort by score descending, then guest priority, then registration time
        # BR-GUEST-006: Guests win tiebreak at pool qualification boundary
        sorted_performers = sorted(
            scored_performers,
            key=lambda p: (
                -p.preselection_score,  # Highest score first
                -int(p.is_guest),       # Guests before regulars at same score
                p.created_at,           # Earlier registration wins ties
            ),
        )

        # Check if there's a tie at the qualification boundary
        if len(sorted_performers) <= pool_capacity:
            return []  # No tie, everyone qualifies

        # Get the cutoff score (last qualifying position)
        cutoff_score = sorted_performers[pool_capacity - 1].preselection_score

        # Find all performers with the cutoff score (both above and below cutoff)
        tied_performers = [
            p for p in sorted_performers if p.preselection_score == cutoff_score
        ]

        # Only return if there's actually a tie (more than 1 at cutoff)
        if len(tied_performers) <= 1:
            return []

        # Count how many with cutoff score are in the qualifying zone
        qualified_count = sum(
            1 for p in sorted_performers[:pool_capacity]
            if p.preselection_score == cutoff_score
        )

        # If we need to choose some but not all tied performers, it's a tie
        # Example: 3 tied at 7.5, but only 2 spots available → tiebreak needed
        if qualified_count < len(tied_performers):
            return tied_performers

        return []

    async def create_tiebreak_battle(
        self, category_id: uuid.UUID, tied_performers: List[Performer], winners_needed: int
    ) -> Battle:
        """Create a tiebreak battle.

        Args:
            category_id: Category UUID
            tied_performers: List of tied performers
            winners_needed: Number of winners needed from this battle

        Returns:
            Created tiebreak battle

        Raises:
            ValidationError: If invalid parameters
        """
        if len(tied_performers) < 2:
            raise ValidationError([f"Tiebreak requires at least 2 performers, got {len(tied_performers)}"])

        if winners_needed >= len(tied_performers):
            raise ValidationError(
                [f"Winners needed ({winners_needed}) must be less than tied performers ({len(tied_performers)})"]
            )

        if winners_needed < 1:
            raise ValidationError([f"Winners needed must be at least 1, got {winners_needed}"])

        # Create battle
        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.TIEBREAK,
            status=BattleStatus.PENDING,
            outcome_type=BattleOutcomeType.TIEBREAK,
        )
        battle.performers = tied_performers

        # Store metadata in outcome for tracking
        battle.outcome = {
            "winners_needed": winners_needed,
            "total_performers": len(tied_performers),
            "current_round": 0,
        }

        created_battle = await self.battle_repo.create(battle)
        return created_battle

    def process_tiebreak_votes(
        self,
        tied_performers: List[Performer],
        votes: Dict[str, uuid.UUID],
        winners_needed: int,
        current_round: int = 1,
    ) -> Dict:
        """Process tiebreak votes and determine outcome.

        Args:
            tied_performers: List of performers in tiebreak
            votes: Dictionary of judge_id -> performer_id votes
            winners_needed: Number of winners needed
            current_round: Current round number

        Returns:
            Dictionary with outcome:
            - eliminated: List of eliminated performer IDs (if any)
            - winners: List of winner performer IDs (if battle complete)
            - next_round_performers: List of remaining performer IDs (if more rounds needed)
            - complete: Boolean indicating if tiebreak is resolved

        Raises:
            ValidationError: If invalid vote data
        """
        if not votes:
            raise ValidationError(["No votes provided"])

        if len(tied_performers) < 2:
            raise ValidationError([f"Need at least 2 performers for tiebreak, got {len(tied_performers)}"])

        # Validate all votes are for valid performers
        performer_ids = {p.id for p in tied_performers}
        for judge_id, voted_id in votes.items():
            if voted_id not in performer_ids:
                raise ValidationError([f"Invalid vote from {judge_id}: performer not in tiebreak"])

        # Count votes
        vote_counts = Counter(votes.values())

        # Determine voting mode based on number of performers
        if len(tied_performers) == 2:
            # KEEP mode: performer with most votes wins
            winner_id = vote_counts.most_common(1)[0][0]
            winners = [winner_id]

            return {
                "eliminated": [p.id for p in tied_performers if p.id != winner_id],
                "winners": winners,
                "next_round_performers": [],
                "complete": True,
                "mode": "KEEP",
                "round": current_round,
            }
        else:
            # ELIMINATE mode: performer with most votes is eliminated
            eliminated_id = vote_counts.most_common(1)[0][0]
            remaining_performer_ids = [p.id for p in tied_performers if p.id != eliminated_id]

            # Check if we've reached winners_needed
            if len(remaining_performer_ids) == winners_needed:
                return {
                    "eliminated": [eliminated_id],
                    "winners": remaining_performer_ids,
                    "next_round_performers": [],
                    "complete": True,
                    "mode": "ELIMINATE",
                    "round": current_round,
                }
            else:
                return {
                    "eliminated": [eliminated_id],
                    "winners": [],
                    "next_round_performers": remaining_performer_ids,
                    "complete": False,
                    "mode": "ELIMINATE",
                    "round": current_round,
                }

    async def get_tiebreak_winners(
        self, battle_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Get winners from a completed tiebreak battle.

        Args:
            battle_id: Tiebreak battle UUID

        Returns:
            List of winner performer IDs

        Raises:
            ValidationError: If battle not found, not completed, or no winners
        """
        battle = await self.battle_repo.get_by_id(battle_id)
        if not battle:
            raise ValidationError([f"Battle {battle_id} not found"])

        if battle.phase != BattlePhase.TIEBREAK:
            raise ValidationError([f"Battle {battle_id} is not a tiebreak battle"])

        if battle.status != BattleStatus.COMPLETED:
            raise ValidationError([f"Tiebreak battle {battle_id} is not completed"])

        if not battle.outcome or "winners" not in battle.outcome:
            raise ValidationError([f"Tiebreak battle {battle_id} has no winners recorded"])

        winners = battle.outcome.get("winners", [])
        if not winners:
            raise ValidationError([f"Tiebreak battle {battle_id} has empty winners list"])

        # Convert string UUIDs to UUID objects if needed
        return [uuid.UUID(w) if isinstance(w, str) else w for w in winners]

    async def needs_tiebreak(
        self, category_id: uuid.UUID, pool_capacity: int
    ) -> bool:
        """Check if category needs a tiebreak for preselection.

        Args:
            category_id: Category UUID
            pool_capacity: Number of pool spots

        Returns:
            True if tiebreak needed, False otherwise
        """
        tied = await self.detect_preselection_ties(category_id, pool_capacity)
        return len(tied) > 0

    def calculate_next_round_performers(
        self, current_performers: List[Performer], eliminated_ids: List[uuid.UUID]
    ) -> List[Performer]:
        """Calculate remaining performers for next round.

        Args:
            current_performers: Current round performers
            eliminated_ids: IDs of eliminated performers

        Returns:
            List of remaining performers
        """
        return [p for p in current_performers if p.id not in eliminated_ids]

    async def detect_and_create_preselection_tiebreak(
        self, category_id: uuid.UUID
    ) -> Optional[Battle]:
        """Detect preselection ties and create tiebreak battle if needed.

        Called automatically when last preselection battle is completed.

        Business Rule BR-TIE-001: Tiebreak auto-created when last battle scored.
        Business Rule BR-TIE-003: ALL performers with boundary score compete.

        Args:
            category_id: Category UUID

        Returns:
            Created tiebreak battle or None if no tie

        Raises:
            ValidationError: If category_repo not configured
        """
        if not self.category_repo:
            raise ValidationError(["Category repository required for auto-detection"])

        # Check if tiebreak already exists to prevent duplicates
        if await self.battle_repo.has_pending_tiebreak(category_id):
            return None

        # Get category config
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise ValidationError([f"Category {category_id} not found"])

        # Get performers for this category
        performers = await self.performer_repo.get_by_category(category_id)

        # Calculate pool capacity using BR-POOL-001 rules
        pool_capacity, _, _ = calculate_pool_capacity(
            len(performers),
            category.groups_ideal,
            category.performers_ideal,
        )

        # Detect ties at boundary
        tied_performers = await self.detect_preselection_ties(category_id, pool_capacity)

        if not tied_performers:
            return None

        # Calculate winners needed
        # Count performers with scores ABOVE the boundary score
        boundary_score = tied_performers[0].preselection_score
        performers_above = [
            p for p in performers
            if p.preselection_score is not None and p.preselection_score > boundary_score
        ]
        spots_remaining = pool_capacity - len(performers_above)
        winners_needed = spots_remaining

        # Create tiebreak battle
        tiebreak = await self.create_tiebreak_battle(
            category_id,
            tied_performers,
            winners_needed,
        )

        return tiebreak

    async def detect_and_create_pool_winner_tiebreak(
        self, pool_id: uuid.UUID, category_id: uuid.UUID
    ) -> Optional[Battle]:
        """Detect pool winner ties and create tiebreak battle if needed.

        Called when last pool battle in a pool is completed.

        Business Rule BR-TIE-002: Pool winner tiebreak auto-created.

        Args:
            pool_id: Pool UUID
            category_id: Category UUID

        Returns:
            Created tiebreak battle or None if no tie
        """
        # Import here to avoid circular dependency
        from app.repositories.pool import PoolRepository

        # Check if tiebreak already exists for this category
        if await self.battle_repo.has_pending_tiebreak(category_id):
            return None

        # Get pool with performers
        pool_repo = PoolRepository(self.battle_repo.session)
        pool = await pool_repo.get_with_performers(pool_id)

        if not pool or not pool.performers:
            return None

        # Find performers with highest points
        max_points = max(
            p.pool_points or 0 for p in pool.performers
        )
        tied_performers = [
            p for p in pool.performers
            if (p.pool_points or 0) == max_points
        ]

        if len(tied_performers) == 1:
            # Clear winner, no tiebreak needed
            return None

        # Create tiebreak for pool winner (exactly 1 winner needed)
        tiebreak = await self.create_tiebreak_battle(
            category_id,
            tied_performers,
            winners_needed=1,
        )

        return tiebreak

    async def detect_and_create_pool_winner_tiebreaks(
        self, category_id: uuid.UUID
    ) -> List[Battle]:
        """Detect pool winner ties for ALL pools and create tiebreak battles.

        Called when ALL pool-phase battles in a category are complete.
        Checks each pool for tied winners and creates tiebreak battles.

        Business Rule BR-TIE-002: Pool winner tiebreak auto-created.

        Design Decision: Check all pools at once (not per-pool) to:
        - Add audience tension by grouping tiebreaks at end of pool phase
        - Avoid needing pool_id on Battle model

        Args:
            category_id: Category UUID

        Returns:
            List of created tiebreak battles (may be empty if no ties)
        """
        from app.repositories.pool import PoolRepository

        pool_repo = PoolRepository(self.battle_repo.session)
        pools = await pool_repo.get_by_category(category_id)

        if not pools:
            return []

        created_tiebreaks: List[Battle] = []

        for pool in pools:
            # Skip if pool already has a winner set
            if pool.winner_id:
                continue

            # Load performers for this pool
            pool_with_performers = await pool_repo.get_with_performers(pool.id)
            if not pool_with_performers or not pool_with_performers.performers:
                continue

            # Find performers with highest points
            max_points = max(
                p.pool_points or 0 for p in pool_with_performers.performers
            )
            tied_performers = [
                p for p in pool_with_performers.performers
                if (p.pool_points or 0) == max_points
            ]

            if len(tied_performers) == 1:
                # Clear winner - set on pool
                pool_with_performers.winner_id = tied_performers[0].id
                await pool_repo.update(pool_with_performers)
                continue

            # Multiple tied - create tiebreak battle
            tiebreak = await self.create_tiebreak_battle(
                category_id,
                tied_performers,
                winners_needed=1,
            )
            created_tiebreaks.append(tiebreak)

        return created_tiebreaks
