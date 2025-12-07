"""Tests for EventService.

Tests event mode command center data aggregation.
See: ARCHITECTURE.md Event Service Pattern
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.tournament import Tournament, TournamentPhase, TournamentStatus
from app.models.category import Category
from app.models.battle import Battle, BattleStatus, BattlePhase
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.services.event_service import (
    EventService,
    CommandCenterContext,
    PhaseProgress,
    BattleQueueItem,
    CategoryInfo,
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
def battle_repo():
    """Mock battle repository."""
    return AsyncMock(spec=BattleRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def event_service(tournament_repo, category_repo, battle_repo, performer_repo):
    """Event service with mocked repositories."""
    return EventService(tournament_repo, category_repo, battle_repo, performer_repo)


def create_tournament(
    status: TournamentStatus = TournamentStatus.ACTIVE,
    phase: TournamentPhase = TournamentPhase.PRESELECTION,
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
) -> Category:
    """Helper to create a category."""
    category = Category(
        tournament_id=tournament_id,
        name=name,
        is_duo=is_duo,
    )
    category.id = uuid.uuid4()
    return category


class TestGetCommandCenterContext:
    """Tests for get_command_center_context()."""

    @pytest.mark.asyncio
    async def test_returns_complete_context(
        self, event_service, tournament_repo, category_repo, battle_repo
    ):
        """Returns complete command center context."""
        tournament = create_tournament()
        category = create_category(tournament.id)

        tournament_repo.get_by_id.return_value = tournament
        category_repo.get_by_tournament.return_value = [category]
        battle_repo.get_by_category.return_value = []

        result = await event_service.get_command_center_context(tournament.id)

        assert isinstance(result, CommandCenterContext)
        assert result.tournament.id == tournament.id
        assert result.phase_display == "Preselection"
        assert len(result.categories) == 1

    @pytest.mark.asyncio
    async def test_tournament_not_found_raises(
        self, event_service, tournament_repo
    ):
        """Raises ValueError for non-existent tournament."""
        tournament_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await event_service.get_command_center_context(uuid.uuid4())


class TestGetPhaseProgress:
    """Tests for get_phase_progress()."""

    @pytest.mark.asyncio
    async def test_progress_tournament_not_found(
        self, event_service, tournament_repo
    ):
        """Returns 0/0/0 for non-existent tournament."""
        tournament_repo.get_by_id.return_value = None

        result = await event_service.get_phase_progress(uuid.uuid4())

        assert result.completed == 0
        assert result.total == 0
        assert result.percentage == 0


class TestGetPerformerDisplayName:
    """Tests for _get_performer_display_name()."""

    def test_none_performer_returns_tbd(self, event_service):
        """Returns 'TBD' for None performer."""
        result = event_service._get_performer_display_name(None)

        assert result == "TBD"

    def test_solo_performer_name(self, event_service):
        """Returns dancer blaze for solo performer."""
        performer = MagicMock()
        performer.dancer = MagicMock()
        performer.dancer.blaze = "B-Boy Thunder"

        result = event_service._get_performer_display_name(performer)

        assert result == "B-Boy Thunder"

    def test_duo_performer_name(self, event_service):
        """Returns duo_name for duo performer."""
        performer = MagicMock()
        performer.dancer = None
        performer.duo_name = "Thunder & Lightning"
        performer.dancer1 = None

        result = event_service._get_performer_display_name(performer)

        assert result == "Thunder & Lightning"


class TestCommandCenterContextDataclass:
    """Tests for CommandCenterContext dataclass behavior."""

    def test_default_queue_list(self):
        """queue defaults to empty list."""
        tournament = MagicMock()
        context = CommandCenterContext(tournament=tournament)
        assert context.queue == []

    def test_default_categories_list(self):
        """categories defaults to empty list."""
        tournament = MagicMock()
        context = CommandCenterContext(tournament=tournament)
        assert context.categories == []

    def test_default_progress(self):
        """progress defaults to PhaseProgress(0, 0, 0)."""
        tournament = MagicMock()
        context = CommandCenterContext(tournament=tournament)
        assert context.progress.completed == 0
        assert context.progress.total == 0
        assert context.progress.percentage == 0


class TestPhaseProgressDataclass:
    """Tests for PhaseProgress dataclass."""

    def test_phase_progress_creation(self):
        """PhaseProgress can be created with values."""
        progress = PhaseProgress(completed=5, total=10, percentage=50)
        assert progress.completed == 5
        assert progress.total == 10
        assert progress.percentage == 50
