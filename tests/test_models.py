"""Tests for database models."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from app.models import (
    User,
    UserRole,
    Dancer,
    Tournament,
    TournamentStatus,
    TournamentPhase,
    Category,
    Performer,
    Pool,
    Battle,
    BattlePhase,
    BattleStatus,
    BattleOutcomeType,
)
from app.db.database import async_session_maker


@pytest.mark.asyncio
async def test_user_model():
    """Test User model creation and properties."""
    async with async_session_maker() as session:
        # Create user
        user = User(
            email="test@example.com",
            first_name="Test",
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Verify attributes
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.role == UserRole.ADMIN
        assert user.id is not None
        assert user.created_at is not None

        # Verify properties
        assert user.is_admin is True
        assert user.is_staff is True
        assert user.is_mc is True
        assert user.is_judge is False


@pytest.mark.asyncio
async def test_dancer_model():
    """Test Dancer model creation and properties."""
    async with async_session_maker() as session:
        # Create dancer
        dancer = Dancer(
            email="dancer@example.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 1),
            blaze="JDoe",
            country="USA",
            city="New York",
        )
        session.add(dancer)
        await session.commit()
        await session.refresh(dancer)

        # Verify attributes
        assert dancer.email == "dancer@example.com"
        assert dancer.blaze == "JDoe"
        assert dancer.full_name == "John Doe"
        assert dancer.age > 0  # Will be calculated from date_of_birth


@pytest.mark.asyncio
async def test_tournament_phase_progression():
    """Test tournament phase progression."""
    async with async_session_maker() as session:
        # Create tournament
        tournament = Tournament(
            name="Test Tournament",
            status=TournamentStatus.ACTIVE,
            phase=TournamentPhase.REGISTRATION,
        )
        session.add(tournament)
        await session.commit()

        # Advance phases
        tournament.advance_phase()
        assert tournament.phase == TournamentPhase.PRESELECTION

        tournament.advance_phase()
        assert tournament.phase == TournamentPhase.POOLS

        tournament.advance_phase()
        assert tournament.phase == TournamentPhase.FINALS

        tournament.advance_phase()
        assert tournament.phase == TournamentPhase.COMPLETED
        assert tournament.status == TournamentStatus.COMPLETED


@pytest.mark.asyncio
async def test_category_model():
    """Test Category model and computed properties."""
    async with async_session_maker() as session:
        # Create tournament
        tournament = Tournament(name="Test Tournament")
        session.add(tournament)
        await session.flush()

        # Create category
        category = Category(
            tournament_id=tournament.id,
            name="Hip Hop 1v1",
            is_duo=False,
            groups_ideal=2,
            performers_ideal=4,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)

        # Verify computed properties
        assert category.category_type == "1v1"
        assert category.ideal_pool_capacity == 8  # 2 * 4


@pytest.mark.asyncio
async def test_performer_pool_points():
    """Test Performer pool_points calculation."""
    async with async_session_maker() as session:
        # Create necessary objects
        tournament = Tournament(name="Test")
        dancer = Dancer(
            email="test@example.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="TestBlaze",
        )
        session.add_all([tournament, dancer])
        await session.flush()

        category = Category(
            tournament_id=tournament.id,
            name="Test Category",
        )
        session.add(category)
        await session.flush()

        performer = Performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
            pool_wins=3,
            pool_draws=2,
            pool_losses=1,
        )
        session.add(performer)
        await session.commit()
        await session.refresh(performer)

        # Verify pool points calculation: (3 * 3) + (2 * 1) = 11
        assert performer.pool_points == 11


@pytest.mark.asyncio
async def test_battle_outcome_types():
    """Test Battle model with different outcome types."""
    async with async_session_maker() as session:
        # Create necessary objects
        tournament = Tournament(name="Test")
        session.add(tournament)
        await session.flush()

        category = Category(
            tournament_id=tournament.id,
            name="Test Category",
        )
        session.add(category)
        await session.flush()

        # Create battle with scored outcome
        battle = Battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            status=BattleStatus.PENDING,
            outcome_type=BattleOutcomeType.SCORED,
        )
        session.add(battle)
        await session.commit()

        # Set scored outcome
        battle.set_scored_outcome({
            "performer_1": 7.5,
            "performer_2": 8.3,
        })
        await session.commit()

        assert battle.outcome["performer_1"] == 7.5
        assert battle.outcome["performer_2"] == 8.3


@pytest.mark.asyncio
async def test_unique_dancer_per_tournament():
    """Test that a dancer can only register once per tournament."""
    async with async_session_maker() as session:
        # Create tournament and dancer
        tournament = Tournament(name="Test")
        dancer = Dancer(
            email="test@example.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="TestBlaze",
        )
        session.add_all([tournament, dancer])
        await session.flush()

        # Create two categories
        category1 = Category(tournament_id=tournament.id, name="Cat 1")
        category2 = Category(tournament_id=tournament.id, name="Cat 2")
        session.add_all([category1, category2])
        await session.flush()

        # Register in first category
        performer1 = Performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer.id,
        )
        session.add(performer1)
        await session.commit()

        # Try to register in second category (should fail)
        performer2 = Performer(
            tournament_id=tournament.id,
            category_id=category2.id,
            dancer_id=dancer.id,
        )
        session.add(performer2)

        with pytest.raises(Exception):  # Unique constraint violation
            await session.commit()
