"""Tests for repository layer."""
import pytest
from datetime import date
from app.repositories import (
    UserRepository,
    DancerRepository,
    TournamentRepository,
    CategoryRepository,
    PerformerRepository,
)
from app.models import UserRole, TournamentPhase
from app.db.database import async_session_maker, init_db, drop_db


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup and teardown test database for each test."""
    await init_db()
    yield
    await drop_db()


@pytest.mark.asyncio
async def test_user_repository_create_and_get():
    """Test UserRepository create and get operations."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)

        # Create user
        user = await user_repo.create_user(
            email="admin@test.com",
            first_name="Admin",
            role=UserRole.ADMIN,
        )

        assert user.id is not None
        assert user.email == "admin@test.com"

        # Get by email
        found_user = await user_repo.get_by_email("admin@test.com")
        assert found_user.id == user.id

        # Check email exists
        exists = await user_repo.email_exists("admin@test.com")
        assert exists is True

        not_exists = await user_repo.email_exists("notfound@test.com")
        assert not_exists is False


@pytest.mark.asyncio
async def test_user_repository_get_by_role():
    """Test UserRepository get_by_role."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)

        # Create multiple users
        await user_repo.create_user("admin@test.com", "Admin", UserRole.ADMIN)
        await user_repo.create_user("staff1@test.com", "Staff1", UserRole.STAFF)
        await user_repo.create_user("staff2@test.com", "Staff2", UserRole.STAFF)
        await user_repo.create_user("mc@test.com", "MC", UserRole.MC)

        # Get by role
        admins = await user_repo.get_by_role(UserRole.ADMIN)
        assert len(admins) == 1

        staff = await user_repo.get_by_role(UserRole.STAFF)
        assert len(staff) == 2


@pytest.mark.asyncio
async def test_dancer_repository_search():
    """Test DancerRepository search functionality."""
    async with async_session_maker() as session:
        dancer_repo = DancerRepository(session)

        # Create dancers
        await dancer_repo.create_dancer(
            email="bboy1@test.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 1),
            blaze="Crazy Legs",
        )
        await dancer_repo.create_dancer(
            email="bboy2@test.com",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1999, 5, 15),
            blaze="Storm",
        )

        # Search by blaze
        results = await dancer_repo.search("Crazy")
        assert len(results) == 1
        assert results[0].blaze == "Crazy Legs"

        # Search by name
        results = await dancer_repo.search("Jane")
        assert len(results) == 1
        assert results[0].first_name == "Jane"


@pytest.mark.asyncio
async def test_tournament_repository():
    """Test TournamentRepository operations."""
    async with async_session_maker() as session:
        tournament_repo = TournamentRepository(session)

        # Create tournament
        tournament = await tournament_repo.create_tournament(
            name="Summer Battle 2024"
        )

        assert tournament.id is not None
        assert tournament.name == "Summer Battle 2024"
        assert tournament.phase == TournamentPhase.REGISTRATION

        # Get active tournaments
        active = await tournament_repo.get_active_tournaments()
        assert len(active) == 1

        # Get by phase
        registration_tournaments = await tournament_repo.get_by_phase(
            TournamentPhase.REGISTRATION
        )
        assert len(registration_tournaments) == 1


@pytest.mark.asyncio
async def test_category_repository():
    """Test CategoryRepository operations."""
    async with async_session_maker() as session:
        tournament_repo = TournamentRepository(session)
        category_repo = CategoryRepository(session)

        # Create tournament
        tournament = await tournament_repo.create_tournament("Test Tournament")

        # Create categories
        category1 = await category_repo.create_category(
            tournament_id=tournament.id,
            name="Hip Hop 1v1",
            is_duo=False,
        )
        category2 = await category_repo.create_category(
            tournament_id=tournament.id,
            name="Krump Duo",
            is_duo=True,
        )

        # Get by tournament
        categories = await category_repo.get_by_tournament(tournament.id)
        assert len(categories) == 2

        # Get with performers
        category = await category_repo.get_with_performers(category1.id)
        assert category is not None
        assert len(category.performers) == 0  # No performers yet


@pytest.mark.asyncio
async def test_performer_repository():
    """Test PerformerRepository operations."""
    async with async_session_maker() as session:
        tournament_repo = TournamentRepository(session)
        category_repo = CategoryRepository(session)
        dancer_repo = DancerRepository(session)
        performer_repo = PerformerRepository(session)

        # Create tournament and category
        tournament = await tournament_repo.create_tournament("Test")
        category = await category_repo.create_category(
            tournament_id=tournament.id,
            name="Test Category",
        )

        # Create dancer
        dancer = await dancer_repo.create_dancer(
            email="dancer@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="TestBlaze",
        )

        # Register dancer
        performer = await performer_repo.create_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        assert performer.id is not None

        # Check if dancer is registered
        is_registered = await performer_repo.dancer_registered_in_tournament(
            dancer.id, tournament.id
        )
        assert is_registered is True

        # Get by category
        performers = await performer_repo.get_by_category(category.id)
        assert len(performers) == 1


@pytest.mark.asyncio
async def test_performer_repository_unique_constraint():
    """Test that dancer can only register once per tournament."""
    async with async_session_maker() as session:
        tournament_repo = TournamentRepository(session)
        category_repo = CategoryRepository(session)
        dancer_repo = DancerRepository(session)
        performer_repo = PerformerRepository(session)

        # Create tournament with two categories
        tournament = await tournament_repo.create_tournament("Test")
        category1 = await category_repo.create_category(
            tournament_id=tournament.id,
            name="Category 1",
        )
        category2 = await category_repo.create_category(
            tournament_id=tournament.id,
            name="Category 2",
        )

        # Create dancer
        dancer = await dancer_repo.create_dancer(
            email="dancer@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="TestBlaze",
        )

        # Register in first category
        await performer_repo.create_performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer.id,
        )

        # Verify dancer is registered
        is_registered = await performer_repo.dancer_registered_in_tournament(
            dancer.id, tournament.id
        )
        assert is_registered is True

        # Try to register in second category (should be prevented by business logic)
        # The unique constraint should catch this at the database level
        with pytest.raises(Exception):
            await performer_repo.create_performer(
                tournament_id=tournament.id,
                category_id=category2.id,
                dancer_id=dancer.id,
            )
            await session.commit()
