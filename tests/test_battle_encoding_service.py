"""Tests for Battle Results Encoding Service.

Focused tests for validation logic and service orchestration.
Integration with database is tested through existing repository tests.

Test Categories:
- Preselection validation
- Pool validation
- Tiebreak validation
- Finals validation
- Phase mismatch detection
- Battle not found handling
"""

import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.models.performer import Performer
from app.models.dancer import Dancer
from app.services.battle_results_encoding_service import BattleResultsEncodingService
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository


# ==================== Fixtures ====================

@pytest.fixture
def mock_session():
    """Mock database session."""
    from contextlib import asynccontextmanager

    session = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield

    session.begin = mock_begin
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def battle_repo():
    """Mock battle repository."""
    return AsyncMock(spec=BattleRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def encoding_service(mock_session, battle_repo, performer_repo):
    """Battle results encoding service with mocked dependencies."""
    return BattleResultsEncodingService(mock_session, battle_repo, performer_repo)


# ==================== Helper Functions ====================

def create_test_battle(phase: BattlePhase, status: BattleStatus, num_performers: int = 2):
    """Create a mock battle with performers."""
    from unittest.mock import MagicMock

    battle = MagicMock()
    battle.id = uuid.uuid4()
    battle.category_id = uuid.uuid4()
    battle.phase = phase
    battle.status = status
    battle.outcome_type = BattleOutcomeType.SCORED if phase == BattlePhase.PRESELECTION else BattleOutcomeType.WIN_DRAW_LOSS
    battle.outcome = None
    battle.winner_id = None

    # Create mock performers
    battle.performers = []
    for i in range(num_performers):
        dancer = MagicMock()
        dancer.id = uuid.uuid4()
        dancer.dancer_name = f"Dancer{i}"
        dancer.email = f"dancer{i}@test.com"

        performer = MagicMock()
        performer.id = uuid.uuid4()
        performer.dancer_id = dancer.id
        performer.category_id = battle.category_id
        performer.dancer = dancer
        performer.pool_wins = 0
        performer.pool_losses = 0
        performer.pool_draws = 0
        performer.preselection_score = None

        battle.performers.append(performer)

    return battle


# ==================== Preselection Tests ====================

@pytest.mark.asyncio
async def test_encode_preselection_battle_success(encoding_service, battle_repo, performer_repo):
    """Test successful preselection results recording."""
    # Setup
    battle = create_test_battle(BattlePhase.PRESELECTION, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()
    performer_repo.update = AsyncMock()

    # Encode
    scores = {
        battle.performers[0].id: Decimal("8.5"),
        battle.performers[1].id: Decimal("9.0"),
    }
    result = await encoding_service.encode_preselection_results(battle.id, scores)

    # Assert
    assert result.valid
    assert len(result.errors) == 0
    battle_repo.update.assert_called_once()
    assert performer_repo.update.call_count == 2


@pytest.mark.asyncio
async def test_encode_preselection_missing_scores(encoding_service, battle_repo):
    """Test preselection fails when scores missing."""
    battle = create_test_battle(BattlePhase.PRESELECTION, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle

    # Missing one performer's score
    scores = {battle.performers[0].id: Decimal("8.5")}
    result = await encoding_service.encode_preselection_results(battle.id, scores)

    assert not result.valid
    assert "Missing scores" in result.errors[0]


@pytest.mark.asyncio
async def test_encode_preselection_invalid_score_range(encoding_service, battle_repo):
    """Test preselection fails for invalid score range."""
    battle = create_test_battle(BattlePhase.PRESELECTION, BattleStatus.ACTIVE, 1)
    battle_repo.get_with_performers.return_value = battle

    # Score out of range
    scores = {battle.performers[0].id: Decimal("15.0")}
    result = await encoding_service.encode_preselection_results(battle.id, scores)

    assert not result.valid
    assert "out of range" in result.errors[0].lower()


# ==================== Pool Tests ====================

@pytest.mark.asyncio
async def test_encode_pool_with_winner(encoding_service, battle_repo, performer_repo):
    """Test pool encoding with winner."""
    battle = create_test_battle(BattlePhase.POOLS, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()
    performer_repo.update = AsyncMock()

    winner_id = battle.performers[0].id
    result = await encoding_service.encode_pool_results(battle.id, winner_id, is_draw=False)

    assert result.valid
    battle_repo.update.assert_called_once()
    assert performer_repo.update.call_count == 2  # Update both performers


@pytest.mark.asyncio
async def test_encode_pool_with_draw(encoding_service, battle_repo, performer_repo):
    """Test pool encoding with draw."""
    battle = create_test_battle(BattlePhase.POOLS, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()
    performer_repo.update = AsyncMock()

    result = await encoding_service.encode_pool_results(battle.id, winner_id=None, is_draw=True)

    assert result.valid
    battle_repo.update.assert_called_once()
    assert performer_repo.update.call_count == 2  # Both get draw


@pytest.mark.asyncio
async def test_encode_pool_winner_and_draw_mutually_exclusive(encoding_service, battle_repo):
    """Test pool fails when both winner and draw specified."""
    battle = create_test_battle(BattlePhase.POOLS, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle

    # Try to specify both
    result = await encoding_service.encode_pool_results(
        battle.id,
        winner_id=battle.performers[0].id,
        is_draw=True
    )

    assert not result.valid
    assert "both winner and draw" in result.errors[0].lower()


# ==================== Tiebreak Tests ====================

@pytest.mark.asyncio
async def test_encode_tiebreak_success(encoding_service, battle_repo):
    """Test tiebreak encoding."""
    battle = create_test_battle(BattlePhase.TIEBREAK, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()

    winner_id = battle.performers[0].id
    result = await encoding_service.encode_tiebreak_results(battle.id, winner_id)

    assert result.valid
    battle_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_encode_tiebreak_no_draws_allowed(encoding_service, battle_repo):
    """Test tiebreak requires winner (no draws)."""
    battle = create_test_battle(BattlePhase.TIEBREAK, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle

    # Winner ID is required
    fake_winner = uuid.uuid4()  # Not in battle
    result = await encoding_service.encode_tiebreak_results(battle.id, fake_winner)

    assert not result.valid


# ==================== Finals Tests ====================

@pytest.mark.asyncio
async def test_encode_finals_success(encoding_service, battle_repo):
    """Test finals encoding."""
    battle = create_test_battle(BattlePhase.FINALS, BattleStatus.ACTIVE, 3)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()

    winner_id = battle.performers[0].id
    result = await encoding_service.encode_finals_results(battle.id, winner_id)

    assert result.valid
    battle_repo.update.assert_called_once()


# ==================== Error Handling Tests ====================

@pytest.mark.asyncio
async def test_encode_battle_not_found(encoding_service, battle_repo):
    """Test encoding fails for non-existent battle."""
    battle_repo.get_with_performers.return_value = None

    fake_id = uuid.uuid4()
    result = await encoding_service.encode_preselection_results(fake_id, {})

    assert not result.valid
    assert "not found" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_encode_wrong_phase_fails(encoding_service, battle_repo):
    """Test encoding fails for wrong phase."""
    # Try to encode FINALS battle as preselection
    battle = create_test_battle(BattlePhase.FINALS, BattleStatus.ACTIVE, 2)
    battle_repo.get_with_performers.return_value = battle

    scores = {battle.performers[0].id: Decimal("8.5")}
    result = await encoding_service.encode_preselection_results(battle.id, scores)

    assert not result.valid
    assert "PRESELECTION" in result.errors[0]


# ==================== Single Performer Tests ====================

@pytest.mark.asyncio
async def test_encode_single_performer_preselection(encoding_service, battle_repo, performer_repo):
    """Test encoding preselection with single performer."""
    battle = create_test_battle(BattlePhase.PRESELECTION, BattleStatus.ACTIVE, 1)
    battle_repo.get_with_performers.return_value = battle
    battle_repo.update = AsyncMock()
    performer_repo.update = AsyncMock()

    scores = {battle.performers[0].id: Decimal("7.5")}
    result = await encoding_service.encode_preselection_results(battle.id, scores)

    assert result.valid
    battle_repo.update.assert_called_once()
