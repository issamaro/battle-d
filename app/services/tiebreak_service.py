"""Tiebreak service for tie detection and tiebreak battle management.

See: ROADMAP.md §2.3 Tiebreak Service
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
        self, battle_repo: BattleRepository, performer_repo: PerformerRepository
    ):
        """Initialize tiebreak service.

        Args:
            battle_repo: Battle repository
            performer_repo: Performer repository
        """
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo

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

        # Sort by score descending
        sorted_performers = sorted(
            scored_performers,
            key=lambda p: p.preselection_score,  # type: ignore
            reverse=True,
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
