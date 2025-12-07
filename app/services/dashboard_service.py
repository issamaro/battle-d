"""Dashboard service for aggregating dashboard context."""

from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from app.models.tournament import Tournament, TournamentPhase, TournamentStatus
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository


@dataclass
class CategoryStats:
    """Statistics for a category's registration status."""
    id: UUID
    name: str
    is_duo: bool
    registered_count: int
    ideal_count: int  # performers_ideal * groups_ideal
    minimum_required: int  # performers_ideal (one full group minimum)
    is_ready: bool  # Has minimum required


@dataclass
class DashboardContext:
    """Context data for smart dashboard.

    Attributes:
        state: Current dashboard state
            - 'no_tournament': No active or registration-phase tournament
            - 'registration': Tournament in REGISTRATION phase
            - 'event_active': Tournament in PRESELECTION/POOLS/FINALS
        tournament: The active tournament (if any)
        categories: Category stats with registration counts (registration state)
        phase_display: Human-readable current phase (event state)
    """
    state: str  # 'no_tournament' | 'registration' | 'event_active'
    tournament: Optional[Tournament] = None
    categories: List[CategoryStats] = None
    phase_display: str = ""

    def __post_init__(self):
        if self.categories is None:
            self.categories = []


class DashboardService:
    """Service for aggregating dashboard data based on tournament state.

    The dashboard has three distinct states:
    1. No tournament: Show "Create Tournament" CTA
    2. Registration: Show category registration progress
    3. Event Active: Show "Go to Event Mode" CTA
    """

    def __init__(
        self,
        tournament_repo: TournamentRepository,
        category_repo: CategoryRepository,
        performer_repo: PerformerRepository,
    ):
        """Initialize dashboard service.

        Args:
            tournament_repo: Tournament repository
            category_repo: Category repository
            performer_repo: Performer repository
        """
        self.tournament_repo = tournament_repo
        self.category_repo = category_repo
        self.performer_repo = performer_repo

    async def get_dashboard_context(self) -> DashboardContext:
        """Get context for smart dashboard.

        Determines the dashboard state based on tournament existence and phase,
        then aggregates the appropriate data for that state.

        Returns:
            DashboardContext with state-appropriate data
        """
        tournament = await self.get_relevant_tournament()

        if tournament is None:
            return DashboardContext(state="no_tournament")

        # Determine state based on tournament phase
        if tournament.phase == TournamentPhase.REGISTRATION:
            categories = await self._get_category_stats(tournament.id)
            return DashboardContext(
                state="registration",
                tournament=tournament,
                categories=categories,
            )
        else:
            # PRESELECTION, POOLS, FINALS, or COMPLETED
            phase_display = tournament.phase.value.replace("_", " ").title()
            return DashboardContext(
                state="event_active",
                tournament=tournament,
                phase_display=phase_display,
            )

    async def get_relevant_tournament(self) -> Optional[Tournament]:
        """Get the most relevant tournament for dashboard.

        Priority:
        1. ACTIVE tournament (event in progress)
        2. CREATED tournament in any phase (work in progress)
        3. None (no active work)

        Returns:
            Tournament or None
        """
        # First, check for active tournament
        active_tournaments = await self.tournament_repo.get_active_tournaments()
        if active_tournaments:
            return active_tournaments[0]

        # Second, check for any CREATED tournament
        tournaments = await self.tournament_repo.get_all()
        created_tournaments = [
            t for t in tournaments
            if t.status == TournamentStatus.CREATED
        ]
        if created_tournaments:
            # Return most recently created
            return max(created_tournaments, key=lambda t: t.created_at)

        return None

    async def _get_category_stats(self, tournament_id: UUID) -> List[CategoryStats]:
        """Get registration statistics for all categories in a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            List of CategoryStats with registration counts
        """
        categories = await self.category_repo.get_by_tournament(tournament_id)
        stats = []

        for category in categories:
            # Get performers for this category
            category_with_performers = await self.category_repo.get_with_performers(
                category.id
            )
            performer_count = (
                len(category_with_performers.performers)
                if category_with_performers and category_with_performers.performers
                else 0
            )

            ideal_count = category.performers_ideal * category.groups_ideal
            minimum_required = category.performers_ideal  # One full group

            stats.append(CategoryStats(
                id=category.id,
                name=category.name,
                is_duo=category.is_duo,
                registered_count=performer_count,
                ideal_count=ideal_count,
                minimum_required=minimum_required,
                is_ready=performer_count >= minimum_required,
            ))

        return stats
