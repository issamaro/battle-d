"""Tests for TiebreakService.

Tests tiebreak detection, battle creation, and vote processing.
See: ROADMAP.md §2.3 Tiebreak Service
"""
import pytest
import uuid
from typing import List
from unittest.mock import AsyncMock
from decimal import Decimal

from app.exceptions import ValidationError
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.models.performer import Performer
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.services.tiebreak_service import TiebreakService


@pytest.fixture
def battle_repo():
    """Mock battle repository."""
    return AsyncMock(spec=BattleRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def tiebreak_service(battle_repo, performer_repo):
    """Tiebreak service with mocked repositories."""
    return TiebreakService(battle_repo, performer_repo)


@pytest.fixture
def tournament_id():
    """Sample tournament UUID."""
    return uuid.uuid4()


@pytest.fixture
def category_id():
    """Sample category UUID."""
    return uuid.uuid4()


def create_performer_with_score(
    tournament_id: uuid.UUID,
    category_id: uuid.UUID,
    score: Decimal,
    name: str = "Performer",
) -> Performer:
    """Helper to create a performer with preselection score."""
    performer = Performer(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=uuid.uuid4(),
        preselection_score=score,
    )
    performer.id = uuid.uuid4()
    return performer


class TestDetectPreselectionTies:
    """Tests for detecting preselection qualification ties."""

    async def test_no_tie_all_qualify(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test when all performers qualify (no tie)."""
        # 5 performers, 8 spots → everyone qualifies
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal(f"{10 - i}.0"))
            for i in range(5)
        ]
        performer_repo.get_by_category.return_value = performers

        tied = await tiebreak_service.detect_preselection_ties(category_id, 8)

        assert tied == []

    async def test_no_tie_clear_cutoff(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test when cutoff is clear (no tie at boundary)."""
        # 10 performers with unique scores, 8 qualify
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal(f"{10 - i}.0"))
            for i in range(10)
        ]
        performer_repo.get_by_category.return_value = performers

        tied = await tiebreak_service.detect_preselection_ties(category_id, 8)

        assert tied == []

    async def test_tie_at_boundary(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test tie at qualification boundary."""
        # Performers: 10.0, 9.0, 8.0, 7.8, 7.5, 7.5, 7.5, 6.0, 5.0
        # Pool capacity: 6
        # Top 6 would be: 10.0, 9.0, 8.0, 7.8, 7.5, 7.5
        # But 3 performers have 7.5, only 2 spots available → tiebreak
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("10.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("9.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("8.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.8")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),  # Tied
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),  # Tied
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),  # Tied
            create_performer_with_score(tournament_id, category_id, Decimal("6.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("5.0")),
        ]
        performer_repo.get_by_category.return_value = performers

        tied = await tiebreak_service.detect_preselection_ties(category_id, 6)

        # Should return 3 tied performers at 7.5
        assert len(tied) == 3
        assert all(p.preselection_score == Decimal("7.5") for p in tied)

    async def test_tie_all_fit(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test when all tied performers fit (no tiebreak needed)."""
        # 5 performers: 10.0, 9.0, 8.0, 7.5, 7.5
        # Pool capacity: 5 → all fit
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("10.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("9.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("8.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),
        ]
        performer_repo.get_by_category.return_value = performers

        tied = await tiebreak_service.detect_preselection_ties(category_id, 5)

        assert tied == []

    async def test_missing_scores(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test that missing scores raises error."""
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("10.0")),
            create_performer_with_score(tournament_id, category_id, None),  # type: ignore
        ]
        performer_repo.get_by_category.return_value = performers

        with pytest.raises(ValidationError, match="missing scores"):
            await tiebreak_service.detect_preselection_ties(category_id, 2)


class TestCreateTiebreakBattle:
    """Tests for creating tiebreak battles."""

    async def test_create_tiebreak_success(
        self,
        tiebreak_service,
        battle_repo,
        tournament_id,
        category_id,
    ):
        """Test successful tiebreak battle creation."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
            for _ in range(3)
        ]

        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        battle = await tiebreak_service.create_tiebreak_battle(
            category_id, tied_performers, winners_needed=2
        )

        assert battle.phase == BattlePhase.TIEBREAK
        assert battle.status == BattleStatus.PENDING
        assert battle.outcome_type == BattleOutcomeType.TIEBREAK
        assert len(battle.performers) == 3
        assert battle.outcome["winners_needed"] == 2
        assert battle.outcome["total_performers"] == 3

    async def test_create_tiebreak_insufficient_performers(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test that < 2 performers raises error."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        ]

        with pytest.raises(ValidationError, match="at least 2 performers"):
            await tiebreak_service.create_tiebreak_battle(
                category_id, tied_performers, winners_needed=1
            )

    async def test_create_tiebreak_invalid_winners_needed(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test that winners_needed >= tied_performers raises error."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
            for _ in range(3)
        ]

        with pytest.raises(ValidationError, match="must be less than"):
            await tiebreak_service.create_tiebreak_battle(
                category_id, tied_performers, winners_needed=3
            )

    async def test_create_tiebreak_zero_winners(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test that winners_needed < 1 raises error."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
            for _ in range(3)
        ]

        with pytest.raises(ValidationError, match="must be at least 1"):
            await tiebreak_service.create_tiebreak_battle(
                category_id, tied_performers, winners_needed=0
            )


class TestProcessTiebreakVotes:
    """Tests for processing tiebreak votes."""

    def test_process_votes_keep_mode(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test KEEP mode (N=2 performers)."""
        p1 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p2 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        tied_performers = [p1, p2]

        # 3 judges: 2 vote for p1, 1 votes for p2
        votes = {
            "judge_1": p1.id,
            "judge_2": p1.id,
            "judge_3": p2.id,
        }

        result = tiebreak_service.process_tiebreak_votes(
            tied_performers, votes, winners_needed=1, current_round=1
        )

        assert result["complete"] is True
        assert result["mode"] == "KEEP"
        assert result["winners"] == [p1.id]
        assert p2.id in result["eliminated"]
        assert result["next_round_performers"] == []

    def test_process_votes_eliminate_mode_complete(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test ELIMINATE mode reaching winners_needed."""
        p1 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p2 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p3 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        tied_performers = [p1, p2, p3]

        # 3 judges vote to eliminate p3
        votes = {
            "judge_1": p3.id,
            "judge_2": p3.id,
            "judge_3": p1.id,
        }

        result = tiebreak_service.process_tiebreak_votes(
            tied_performers, votes, winners_needed=2, current_round=1
        )

        assert result["complete"] is True
        assert result["mode"] == "ELIMINATE"
        assert p3.id in result["eliminated"]
        assert set(result["winners"]) == {p1.id, p2.id}
        assert result["next_round_performers"] == []

    def test_process_votes_eliminate_mode_continue(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test ELIMINATE mode needing more rounds."""
        p1 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p2 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p3 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p4 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        tied_performers = [p1, p2, p3, p4]

        # Need 2 winners, eliminate p4
        votes = {
            "judge_1": p4.id,
            "judge_2": p4.id,
            "judge_3": p1.id,
        }

        result = tiebreak_service.process_tiebreak_votes(
            tied_performers, votes, winners_needed=2, current_round=1
        )

        assert result["complete"] is False
        assert result["mode"] == "ELIMINATE"
        assert p4.id in result["eliminated"]
        assert result["winners"] == []
        assert set(result["next_round_performers"]) == {p1.id, p2.id, p3.id}

    def test_process_votes_no_votes(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test that no votes raises error."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
            for _ in range(2)
        ]

        with pytest.raises(ValidationError, match="No votes provided"):
            tiebreak_service.process_tiebreak_votes(
                tied_performers, {}, winners_needed=1
            )

    def test_process_votes_invalid_vote(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test that invalid performer ID raises error."""
        tied_performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
            for _ in range(2)
        ]

        invalid_id = uuid.uuid4()
        votes = {"judge_1": invalid_id}

        with pytest.raises(ValidationError, match="Invalid vote"):
            tiebreak_service.process_tiebreak_votes(
                tied_performers, votes, winners_needed=1
            )


class TestGetTiebreakWinners:
    """Tests for getting tiebreak winners."""

    async def test_get_winners_success(
        self,
        tiebreak_service,
        battle_repo,
        category_id,
    ):
        """Test getting winners from completed tiebreak."""
        battle_id = uuid.uuid4()
        winner_id = uuid.uuid4()

        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.TIEBREAK,
            status=BattleStatus.COMPLETED,
            outcome_type=BattleOutcomeType.TIEBREAK,
        )
        battle.id = battle_id
        battle.outcome = {"winners": [str(winner_id)]}

        battle_repo.get_by_id.return_value = battle

        winners = await tiebreak_service.get_tiebreak_winners(battle_id)

        assert winners == [winner_id]

    async def test_get_winners_battle_not_found(
        self,
        tiebreak_service,
        battle_repo,
    ):
        """Test that missing battle raises error."""
        battle_id = uuid.uuid4()
        battle_repo.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="not found"):
            await tiebreak_service.get_tiebreak_winners(battle_id)

    async def test_get_winners_not_tiebreak(
        self,
        tiebreak_service,
        battle_repo,
        category_id,
    ):
        """Test that non-tiebreak battle raises error."""
        battle_id = uuid.uuid4()

        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.PRESELECTION,  # Not tiebreak
            status=BattleStatus.COMPLETED,
            outcome_type=BattleOutcomeType.SCORED,
        )
        battle.id = battle_id

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="not a tiebreak battle"):
            await tiebreak_service.get_tiebreak_winners(battle_id)

    async def test_get_winners_not_completed(
        self,
        tiebreak_service,
        battle_repo,
        category_id,
    ):
        """Test that incomplete battle raises error."""
        battle_id = uuid.uuid4()

        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.TIEBREAK,
            status=BattleStatus.ACTIVE,  # Not completed
            outcome_type=BattleOutcomeType.TIEBREAK,
        )
        battle.id = battle_id

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="not completed"):
            await tiebreak_service.get_tiebreak_winners(battle_id)

    async def test_get_winners_no_outcome(
        self,
        tiebreak_service,
        battle_repo,
        category_id,
    ):
        """Test that missing outcome raises error."""
        battle_id = uuid.uuid4()

        battle = Battle(
            category_id=category_id,
            phase=BattlePhase.TIEBREAK,
            status=BattleStatus.COMPLETED,
            outcome_type=BattleOutcomeType.TIEBREAK,
        )
        battle.id = battle_id
        battle.outcome = None

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="no winners recorded"):
            await tiebreak_service.get_tiebreak_winners(battle_id)


class TestNeedsTiebreak:
    """Tests for needs_tiebreak helper."""

    async def test_needs_tiebreak_true(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test when tiebreak is needed."""
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("10.0")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),
            create_performer_with_score(tournament_id, category_id, Decimal("7.5")),
        ]
        performer_repo.get_by_category.return_value = performers

        needs = await tiebreak_service.needs_tiebreak(category_id, 2)

        assert needs is True

    async def test_needs_tiebreak_false(
        self,
        tiebreak_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test when no tiebreak needed."""
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal(f"{10 - i}.0"))
            for i in range(5)
        ]
        performer_repo.get_by_category.return_value = performers

        needs = await tiebreak_service.needs_tiebreak(category_id, 3)

        assert needs is False


class TestCalculateNextRoundPerformers:
    """Tests for calculating next round performers."""

    def test_calculate_next_round(
        self,
        tiebreak_service,
        tournament_id,
        category_id,
    ):
        """Test removing eliminated performers."""
        p1 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p2 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        p3 = create_performer_with_score(tournament_id, category_id, Decimal("7.5"))
        current = [p1, p2, p3]

        remaining = tiebreak_service.calculate_next_round_performers(
            current, [p3.id]
        )

        assert len(remaining) == 2
        assert p1 in remaining
        assert p2 in remaining
        assert p3 not in remaining
