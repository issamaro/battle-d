"""Event service for aggregating command center data."""

from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from app.models.battle import Battle, BattleStatus
from app.models.tournament import Tournament, TournamentPhase
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository


@dataclass
class PhaseProgress:
    """Progress through the current phase."""
    completed: int
    total: int
    percentage: int  # 0-100


@dataclass
class BattleQueueItem:
    """A battle in the queue for display."""
    id: UUID
    position: int
    performer1_name: str
    performer2_name: str
    category_name: str
    phase: str  # preselection, pools, finals
    status: str


@dataclass
class CategoryInfo:
    """Category info for event mode."""
    id: UUID
    name: str
    is_duo: bool


@dataclass
class CommandCenterContext:
    """Context data for event mode command center.

    Attributes:
        tournament: The active tournament
        current_battle: Currently in-progress battle (if any)
        queue: Next battles waiting
        progress: Phase completion progress
        categories: List of categories for filtering
        phase_display: Human-readable phase name
    """
    tournament: Tournament
    current_battle: Optional[Battle] = None
    current_battle_performer1: str = ""
    current_battle_performer2: str = ""
    queue: List[BattleQueueItem] = None
    progress: PhaseProgress = None
    categories: List[CategoryInfo] = None
    phase_display: str = ""

    def __post_init__(self):
        if self.queue is None:
            self.queue = []
        if self.categories is None:
            self.categories = []
        if self.progress is None:
            self.progress = PhaseProgress(0, 0, 0)


class EventService:
    """Service for aggregating event mode command center data.

    The command center provides a focused interface for event-day operations:
    - Current battle display
    - Battle queue with filtering
    - Phase progress tracking
    - Category-based views
    """

    def __init__(
        self,
        tournament_repo: TournamentRepository,
        category_repo: CategoryRepository,
        battle_repo: BattleRepository,
        performer_repo: PerformerRepository,
    ):
        """Initialize event service.

        Args:
            tournament_repo: Tournament repository
            category_repo: Category repository
            battle_repo: Battle repository
            performer_repo: Performer repository
        """
        self.tournament_repo = tournament_repo
        self.category_repo = category_repo
        self.battle_repo = battle_repo
        self.performer_repo = performer_repo

    async def get_command_center_context(
        self,
        tournament_id: UUID,
        category_id: Optional[UUID] = None,
    ) -> CommandCenterContext:
        """Get all data for command center view.

        Args:
            tournament_id: Tournament UUID
            category_id: Optional category filter

        Returns:
            CommandCenterContext with tournament data
        """
        tournament = await self.tournament_repo.get_by_id(tournament_id)
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        # Get categories for this tournament
        categories = await self.category_repo.get_by_tournament(tournament_id)
        category_info = [
            CategoryInfo(id=c.id, name=c.name, is_duo=c.is_duo)
            for c in categories
        ]

        # Get current battle (IN_PROGRESS)
        current_battle = None
        current_performer1 = ""
        current_performer2 = ""
        all_battles = await self._get_all_tournament_battles(tournament_id)
        in_progress = [b for b in all_battles if b.status == BattleStatus.IN_PROGRESS]
        if in_progress:
            current_battle = in_progress[0]
            # Get performer names
            if current_battle.performer1_id:
                p1 = await self.performer_repo.get_by_id(current_battle.performer1_id)
                current_performer1 = self._get_performer_display_name(p1)
            if current_battle.performer2_id:
                p2 = await self.performer_repo.get_by_id(current_battle.performer2_id)
                current_performer2 = self._get_performer_display_name(p2)

        # Get battle queue (PENDING battles)
        queue = await self._get_battle_queue(tournament_id, category_id, limit=10)

        # Get phase progress
        progress = await self.get_phase_progress(tournament_id)

        phase_display = tournament.phase.value.replace("_", " ").title()

        return CommandCenterContext(
            tournament=tournament,
            current_battle=current_battle,
            current_battle_performer1=current_performer1,
            current_battle_performer2=current_performer2,
            queue=queue,
            progress=progress,
            categories=category_info,
            phase_display=phase_display,
        )

    async def get_phase_progress(self, tournament_id: UUID) -> PhaseProgress:
        """Get battle completion progress for current phase.

        Args:
            tournament_id: Tournament UUID

        Returns:
            PhaseProgress with completed/total counts
        """
        tournament = await self.tournament_repo.get_by_id(tournament_id)
        if not tournament:
            return PhaseProgress(0, 0, 0)

        # Get all battles for this tournament's current phase
        all_battles = await self._get_all_tournament_battles(tournament_id)

        # Filter by current phase
        phase_battles = [
            b for b in all_battles
            if b.phase.value == tournament.phase.value
        ]

        total = len(phase_battles)
        completed = len([b for b in phase_battles if b.status == BattleStatus.COMPLETED])

        percentage = int((completed / total) * 100) if total > 0 else 0

        return PhaseProgress(completed=completed, total=total, percentage=percentage)

    async def get_battle_queue(
        self,
        tournament_id: UUID,
        category_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[BattleQueueItem]:
        """Get battle queue for display.

        Args:
            tournament_id: Tournament UUID
            category_id: Optional category filter
            limit: Maximum battles to return

        Returns:
            List of BattleQueueItem
        """
        return await self._get_battle_queue(tournament_id, category_id, limit)

    async def _get_battle_queue(
        self,
        tournament_id: UUID,
        category_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[BattleQueueItem]:
        """Internal method to get battle queue."""
        all_battles = await self._get_all_tournament_battles(tournament_id)

        # Filter by category if specified
        if category_id:
            all_battles = [
                b for b in all_battles
                if hasattr(b, 'category_id') and str(b.category_id) == str(category_id)
            ]

        # Get PENDING battles only
        pending = [b for b in all_battles if b.status == BattleStatus.PENDING]

        # Sort by battle_order
        pending.sort(key=lambda b: b.battle_order or 999)

        # Limit results
        pending = pending[:limit]

        # Build queue items
        queue = []
        for i, battle in enumerate(pending):
            # Get performer names
            p1_name = ""
            p2_name = ""
            if battle.performer1_id:
                p1 = await self.performer_repo.get_by_id(battle.performer1_id)
                p1_name = self._get_performer_display_name(p1)
            if battle.performer2_id:
                p2 = await self.performer_repo.get_by_id(battle.performer2_id)
                p2_name = self._get_performer_display_name(p2)

            # Get category name
            cat_name = ""
            if hasattr(battle, 'category_id') and battle.category_id:
                cat = await self.category_repo.get_by_id(battle.category_id)
                cat_name = cat.name if cat else ""

            queue.append(BattleQueueItem(
                id=battle.id,
                position=i + 1,
                performer1_name=p1_name,
                performer2_name=p2_name,
                category_name=cat_name,
                phase=battle.phase.value,
                status=battle.status.value,
            ))

        return queue

    async def _get_all_tournament_battles(self, tournament_id: UUID) -> List[Battle]:
        """Get all battles for a tournament across all categories."""
        categories = await self.category_repo.get_by_tournament(tournament_id)
        all_battles = []

        for category in categories:
            battles = await self.battle_repo.get_by_category(category.id)
            # Add category_id to each battle for filtering
            for battle in battles:
                battle.category_id = category.id
            all_battles.extend(battles)

        return all_battles

    def _get_performer_display_name(self, performer) -> str:
        """Get display name for a performer."""
        if not performer:
            return "TBD"

        # For solo: use blaze from dancer
        if hasattr(performer, 'dancer') and performer.dancer:
            return performer.dancer.blaze

        # For duo: use duo_name or combine names
        if hasattr(performer, 'duo_name') and performer.duo_name:
            return performer.duo_name

        if hasattr(performer, 'dancer1') and performer.dancer1:
            name1 = performer.dancer1.blaze
            name2 = performer.dancer2.blaze if performer.dancer2 else "?"
            return f"{name1} & {name2}"

        return "Unknown"
