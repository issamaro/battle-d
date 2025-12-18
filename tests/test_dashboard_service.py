"""Tests for DashboardService.

Tests dashboard context aggregation and state detection.
See: ARCHITECTURE.md Dashboard Service Pattern
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.tournament import Tournament, TournamentPhase, TournamentStatus
from app.models.category import Category
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.services.dashboard_service import (
    DashboardService,
    DashboardContext,
    CategoryStats,
)


@pytest.fixture
def tournament_repo():
    """Mock tournament repository."""
    return AsyncMock(spec=TournamentRepository)


@pytest.fixture
def category_repo():
    """Mock category repository."""
    return AsyncMock(spec=CategoryRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def dashboard_service(tournament_repo, category_repo, performer_repo):
    """Dashboard service with mocked repositories."""
    return DashboardService(tournament_repo, category_repo, performer_repo)


def create_tournament(
    status: TournamentStatus = TournamentStatus.CREATED,
    phase: TournamentPhase = TournamentPhase.REGISTRATION,
    name: str = "Test Tournament",
) -> Tournament:
    """Helper to create a tournament."""
    tournament = Tournament(
        name=name,
        status=status,
        phase=phase,
    )
    tournament.id = uuid.uuid4()
    tournament.created_at = datetime.now()
    return tournament


def create_category(
    tournament_id: uuid.UUID,
    name: str = "Hip Hop 1v1",
    is_duo: bool = False,
    performers_ideal: int = 4,
    groups_ideal: int = 2,
) -> Category:
    """Helper to create a category."""
    category = Category(
        tournament_id=tournament_id,
        name=name,
        is_duo=is_duo,
        performers_ideal=performers_ideal,
        groups_ideal=groups_ideal,
    )
    category.id = uuid.uuid4()
    category.performers = []
    return category


class TestGetDashboardContext:
    """Tests for get_dashboard_context()."""

    @pytest.mark.asyncio
    async def test_no_tournament_state(self, dashboard_service, tournament_repo):
        """Returns no_tournament state when no tournaments exist."""
        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = []

        result = await dashboard_service.get_dashboard_context()

        assert result.state == "no_tournament"
        assert result.tournament is None
        assert result.categories == []

    @pytest.mark.asyncio
    async def test_registration_state(
        self, dashboard_service, tournament_repo, category_repo
    ):
        """Returns registration state for CREATED tournament in REGISTRATION phase."""
        tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )
        category = create_category(tournament.id)

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [tournament]
        category_repo.get_by_tournament.return_value = [category]
        category_repo.get_with_performers.return_value = category

        result = await dashboard_service.get_dashboard_context()

        assert result.state == "registration"
        assert result.tournament.id == tournament.id
        assert len(result.categories) == 1

    @pytest.mark.asyncio
    async def test_event_active_state_preselection(
        self, dashboard_service, tournament_repo
    ):
        """Returns event_active state for ACTIVE tournament in PRESELECTION."""
        tournament = create_tournament(
            status=TournamentStatus.ACTIVE,
            phase=TournamentPhase.PRESELECTION,
        )
        tournament_repo.get_active_tournaments.return_value = [tournament]

        result = await dashboard_service.get_dashboard_context()

        assert result.state == "event_active"
        assert result.tournament.id == tournament.id
        assert result.phase_display == "Preselection"

    @pytest.mark.asyncio
    async def test_event_active_state_pools(self, dashboard_service, tournament_repo):
        """Returns event_active state for ACTIVE tournament in POOLS."""
        tournament = create_tournament(
            status=TournamentStatus.ACTIVE,
            phase=TournamentPhase.POOLS,
        )
        tournament_repo.get_active_tournaments.return_value = [tournament]

        result = await dashboard_service.get_dashboard_context()

        assert result.state == "event_active"
        assert result.phase_display == "Pools"

    @pytest.mark.asyncio
    async def test_event_active_state_finals(self, dashboard_service, tournament_repo):
        """Returns event_active state for ACTIVE tournament in FINALS."""
        tournament = create_tournament(
            status=TournamentStatus.ACTIVE,
            phase=TournamentPhase.FINALS,
        )
        tournament_repo.get_active_tournaments.return_value = [tournament]

        result = await dashboard_service.get_dashboard_context()

        assert result.state == "event_active"
        assert result.phase_display == "Finals"


class TestGetRelevantTournament:
    """Tests for get_relevant_tournament()."""

    @pytest.mark.asyncio
    async def test_active_tournament_priority(self, dashboard_service, tournament_repo):
        """Active tournament takes priority over CREATED."""
        active_tournament = create_tournament(
            status=TournamentStatus.ACTIVE,
            phase=TournamentPhase.PRESELECTION,
            name="Active Tournament",
        )
        created_tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
            name="Created Tournament",
        )

        tournament_repo.get_active_tournaments.return_value = [active_tournament]
        tournament_repo.get_all.return_value = [active_tournament, created_tournament]

        result = await dashboard_service.get_relevant_tournament()

        assert result.name == "Active Tournament"

    @pytest.mark.asyncio
    async def test_created_tournament_fallback(self, dashboard_service, tournament_repo):
        """CREATED tournament returned when no ACTIVE."""
        created_tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [created_tournament]

        result = await dashboard_service.get_relevant_tournament()

        assert result.id == created_tournament.id

    @pytest.mark.asyncio
    async def test_no_tournaments_returns_none(self, dashboard_service, tournament_repo):
        """Returns None when no tournaments exist."""
        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = []

        result = await dashboard_service.get_relevant_tournament()

        assert result is None

    @pytest.mark.asyncio
    async def test_most_recent_created_selected(self, dashboard_service, tournament_repo):
        """Returns most recently created tournament when multiple CREATED exist."""
        older_tournament = create_tournament(name="Older Tournament")
        older_tournament.created_at = datetime(2025, 1, 1)

        newer_tournament = create_tournament(name="Newer Tournament")
        newer_tournament.created_at = datetime(2025, 12, 1)

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [older_tournament, newer_tournament]

        result = await dashboard_service.get_relevant_tournament()

        assert result.name == "Newer Tournament"


class TestGetCategoryStats:
    """Tests for category stats calculation."""

    @pytest.mark.asyncio
    async def test_category_stats_calculation(
        self, dashboard_service, tournament_repo, category_repo
    ):
        """Returns correct registration counts per category."""
        tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )
        category = create_category(
            tournament.id,
            performers_ideal=4,
            groups_ideal=2,
        )
        # Simulate 6 performers registered
        category.performers = [MagicMock() for _ in range(6)]

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [tournament]
        category_repo.get_by_tournament.return_value = [category]
        category_repo.get_with_performers.return_value = category

        result = await dashboard_service.get_dashboard_context()

        assert len(result.categories) == 1
        cat_stats = result.categories[0]
        assert cat_stats.registered_count == 6
        assert cat_stats.ideal_count == 8  # 4 * 2
        assert cat_stats.minimum_required == 5  # (groups_ideal * 2) + 1 = (2 * 2) + 1

    @pytest.mark.asyncio
    async def test_category_is_ready_flag(
        self, dashboard_service, tournament_repo, category_repo
    ):
        """is_ready flag correctly calculated based on minimum."""
        tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )
        # Category with 4 performers_ideal, 3 registered (not ready)
        category_not_ready = create_category(
            tournament.id,
            name="Not Ready Category",
            performers_ideal=4,
            groups_ideal=2,
        )
        category_not_ready.performers = [MagicMock() for _ in range(3)]

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [tournament]
        category_repo.get_by_tournament.return_value = [category_not_ready]
        category_repo.get_with_performers.return_value = category_not_ready

        result = await dashboard_service.get_dashboard_context()

        cat_stats = result.categories[0]
        assert cat_stats.is_ready is False  # 3 < 5 minimum (formula: (2*2)+1=5)

    @pytest.mark.asyncio
    async def test_category_is_ready_when_meets_minimum(
        self, dashboard_service, tournament_repo, category_repo
    ):
        """is_ready is True when registered meets minimum."""
        tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )
        category = create_category(
            tournament.id,
            performers_ideal=4,
            groups_ideal=2,
        )
        # 6 performers registered (meets minimum of 5)
        category.performers = [MagicMock() for _ in range(6)]

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [tournament]
        category_repo.get_by_tournament.return_value = [category]
        category_repo.get_with_performers.return_value = category

        result = await dashboard_service.get_dashboard_context()

        cat_stats = result.categories[0]
        assert cat_stats.is_ready is True  # 6 >= 5 minimum (formula: (2*2)+1=5)

    @pytest.mark.asyncio
    async def test_empty_category(
        self, dashboard_service, tournament_repo, category_repo
    ):
        """Handles category with no performers."""
        tournament = create_tournament(
            status=TournamentStatus.CREATED,
            phase=TournamentPhase.REGISTRATION,
        )
        category = create_category(tournament.id)
        category.performers = []

        tournament_repo.get_active_tournaments.return_value = []
        tournament_repo.get_all.return_value = [tournament]
        category_repo.get_by_tournament.return_value = [category]
        category_repo.get_with_performers.return_value = category

        result = await dashboard_service.get_dashboard_context()

        cat_stats = result.categories[0]
        assert cat_stats.registered_count == 0
        assert cat_stats.is_ready is False


class TestDashboardContextDataclass:
    """Tests for DashboardContext dataclass behavior."""

    def test_default_categories_list(self):
        """categories defaults to empty list."""
        context = DashboardContext(state="no_tournament")
        assert context.categories == []

    def test_categories_not_shared(self):
        """Each instance has its own categories list."""
        context1 = DashboardContext(state="no_tournament")
        context2 = DashboardContext(state="no_tournament")
        context1.categories.append("test")
        assert context2.categories == []
