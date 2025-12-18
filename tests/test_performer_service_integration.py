"""Integration tests for PerformerService.

These tests use REAL repositories and database to catch bugs like:
- Invalid enum references
- Method signature mismatches
- Relationship issues
- Duo pairing validation

See: TESTING.md §Service Integration Tests
"""
import pytest
from datetime import date
from uuid import uuid4

# Use isolated test database - NEVER import from app.db.database!
from tests.conftest import test_session_maker
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.services.performer_service import PerformerService
from app.models import TournamentPhase, TournamentStatus
from app.exceptions import ValidationError


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


async def create_dancer(session, email: str, blaze: str) -> "Dancer":
    """Helper to create a dancer for tests."""
    dancer_repo = DancerRepository(session)
    return await dancer_repo.create_dancer(
        email=email,
        first_name="Test",
        last_name="Dancer",
        date_of_birth=date(2000, 1, 1),
        blaze=blaze,
    )


async def create_tournament(session) -> "Tournament":
    """Helper to create a tournament for tests."""
    tournament_repo = TournamentRepository(session)
    return await tournament_repo.create_tournament(
        name=f"Test Tournament {uuid4().hex[:8]}",
    )


async def create_category(session, tournament_id, is_duo: bool = False) -> "Category":
    """Helper to create a category for tests."""
    category_repo = CategoryRepository(session)
    return await category_repo.create_category(
        tournament_id=tournament_id,
        name=f"Test Category {uuid4().hex[:8]}",
        is_duo=is_duo,
        groups_ideal=2,
        performers_ideal=4,
    )


def create_performer_service(session) -> PerformerService:
    """Helper to create a PerformerService with real repositories."""
    return PerformerService(
        performer_repo=PerformerRepository(session),
        category_repo=CategoryRepository(session),
        dancer_repo=DancerRepository(session),
    )


# =============================================================================
# REGISTER PERFORMER - SOLO CATEGORY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_register_solo_performer_success():
    """Test successful solo performer registration."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        # Create test data
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "solo@test.com", "B-Boy Solo")

        # Register performer
        performer = await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        assert performer.id is not None
        assert performer.dancer_id == dancer.id
        assert performer.category_id == category.id
        assert performer.tournament_id == tournament.id
        assert performer.duo_partner_id is None


@pytest.mark.asyncio
async def test_register_solo_with_partner_fails():
    """Test that registering solo with duo partner raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        solo_category = await create_category(session, tournament.id, is_duo=False)
        dancer1 = await create_dancer(session, "dancer1@test.com", "Dancer 1")
        dancer2 = await create_dancer(session, "dancer2@test.com", "Dancer 2")

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=solo_category.id,
                dancer_id=dancer1.id,
                duo_partner_id=dancer2.id,  # Should fail - solo category
            )

        assert "solo category" in str(exc_info.value).lower()


# =============================================================================
# REGISTER PERFORMER - DUO CATEGORY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_register_duo_performer_success():
    """Test successful duo performer registration."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer1 = await create_dancer(session, "duo1@test.com", "B-Boy Duo1")
        dancer2 = await create_dancer(session, "duo2@test.com", "B-Boy Duo2")

        performer = await service.register_performer(
            tournament_id=tournament.id,
            category_id=duo_category.id,
            dancer_id=dancer1.id,
            duo_partner_id=dancer2.id,
        )

        assert performer.id is not None
        assert performer.dancer_id == dancer1.id
        assert performer.duo_partner_id == dancer2.id


@pytest.mark.asyncio
async def test_register_duo_without_partner_fails():
    """Test that registering duo without partner raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer = await create_dancer(session, "solo@test.com", "Solo Dancer")

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=duo_category.id,
                dancer_id=dancer.id,
                # No duo_partner_id - should fail
            )

        assert "must provide duo partner" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_duo_self_partner_fails():
    """Test that registering with self as partner raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=duo_category.id,
                dancer_id=dancer.id,
                duo_partner_id=dancer.id,  # Same as dancer_id
            )

        assert "own duo partner" in str(exc_info.value).lower()


# =============================================================================
# VALIDATION ERROR TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_register_category_not_found():
    """Test that non-existent category raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")
        fake_category_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=fake_category_id,
                dancer_id=dancer.id,
            )

        assert "category not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_wrong_tournament():
    """Test that category from wrong tournament raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament1 = await create_tournament(session)
        tournament2 = await create_tournament(session)
        category = await create_category(session, tournament1.id, is_duo=False)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament2.id,  # Different tournament
                category_id=category.id,
                dancer_id=dancer.id,
            )

        assert "does not belong to this tournament" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_dancer_not_found():
    """Test that non-existent dancer raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        fake_dancer_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=category.id,
                dancer_id=fake_dancer_id,
            )

        assert "dancer not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_dancer_already_registered():
    """Test that already registered dancer raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category1 = await create_category(session, tournament.id, is_duo=False)
        category2 = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")

        # Register first time
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer.id,
        )

        # Try to register again in different category
        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=category2.id,
                dancer_id=dancer.id,
            )

        assert "already registered" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_partner_not_found():
    """Test that non-existent duo partner raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")
        fake_partner_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=duo_category.id,
                dancer_id=dancer.id,
                duo_partner_id=fake_partner_id,
            )

        assert "duo partner not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_partner_already_registered():
    """Test that already registered partner raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        solo_category = await create_category(session, tournament.id, is_duo=False)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer1 = await create_dancer(session, "dancer1@test.com", "Dancer 1")
        dancer2 = await create_dancer(session, "dancer2@test.com", "Dancer 2")

        # Register dancer2 first in solo category
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=solo_category.id,
            dancer_id=dancer2.id,
        )

        # Try to use dancer2 as duo partner
        with pytest.raises(ValidationError) as exc_info:
            await service.register_performer(
                tournament_id=tournament.id,
                category_id=duo_category.id,
                dancer_id=dancer1.id,
                duo_partner_id=dancer2.id,  # Already registered
            )

        assert "duo partner" in str(exc_info.value).lower()
        assert "already registered" in str(exc_info.value).lower()


# =============================================================================
# UNREGISTER PERFORMER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_unregister_performer_success():
    """Test successful performer unregistration."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "dancer@test.com", "Dancer")

        performer = await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        result = await service.unregister_performer(performer.id)

        assert result is True

        # Verify performer was deleted
        performers = await service.get_performers_by_category(category.id)
        assert len(performers) == 0


@pytest.mark.asyncio
async def test_unregister_performer_not_found():
    """Test unregistering non-existent performer raises error."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        fake_performer_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.unregister_performer(fake_performer_id)

        assert "performer not found" in str(exc_info.value).lower()


# =============================================================================
# GET PERFORMERS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_performers_by_category():
    """Test getting all performers in a category."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category1 = await create_category(session, tournament.id, is_duo=False)
        category2 = await create_category(session, tournament.id, is_duo=False)
        dancer1 = await create_dancer(session, "dancer1@test.com", "Dancer 1")
        dancer2 = await create_dancer(session, "dancer2@test.com", "Dancer 2")
        dancer3 = await create_dancer(session, "dancer3@test.com", "Dancer 3")

        # Register dancers in category1
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer1.id,
        )
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer2.id,
        )

        # Register dancer in category2
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category2.id,
            dancer_id=dancer3.id,
        )

        performers = await service.get_performers_by_category(category1.id)

        assert len(performers) == 2


@pytest.mark.asyncio
async def test_get_performers_by_category_empty():
    """Test getting performers from empty category."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)

        performers = await service.get_performers_by_category(category.id)

        assert len(performers) == 0


@pytest.mark.asyncio
async def test_get_performers_by_tournament():
    """Test getting all performers in a tournament."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)
        category1 = await create_category(session, tournament.id, is_duo=False)
        category2 = await create_category(session, tournament.id, is_duo=False)
        dancer1 = await create_dancer(session, "dancer1@test.com", "Dancer 1")
        dancer2 = await create_dancer(session, "dancer2@test.com", "Dancer 2")

        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category1.id,
            dancer_id=dancer1.id,
        )
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category2.id,
            dancer_id=dancer2.id,
        )

        performers = await service.get_performers_by_tournament(tournament.id)

        assert len(performers) == 2


@pytest.mark.asyncio
async def test_get_performers_by_tournament_empty():
    """Test getting performers from empty tournament."""
    async with test_session_maker() as session:
        service = create_performer_service(session)

        tournament = await create_tournament(session)

        performers = await service.get_performers_by_tournament(tournament.id)

        assert len(performers) == 0


# =============================================================================
# GUEST PERFORMER TESTS (BR-GUEST-*)
# =============================================================================


def create_performer_service_with_tournament(session) -> PerformerService:
    """Helper to create a PerformerService with tournament repo for guest operations."""
    return PerformerService(
        performer_repo=PerformerRepository(session),
        category_repo=CategoryRepository(session),
        dancer_repo=DancerRepository(session),
        tournament_repo=TournamentRepository(session),
    )


@pytest.mark.asyncio
async def test_register_guest_performer_success():
    """Test successful guest performer registration.

    Validates: BR-GUEST-001, BR-GUEST-002
    Gherkin:
        Scenario: Register dancer as guest during registration phase
        Given a tournament in REGISTRATION phase
        And a category "Hip Hop Boys 1v1" exists
        And a dancer "B-Boy Champion" exists in the database
        When I register "B-Boy Champion" as a guest
        Then a performer record is created with is_guest = true
        And the performer's preselection_score is set to 10.0
        And the performer appears in the registration list with a "Guest" badge
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "guest@test.com", "Guest Performer")

        # When
        performer = await service.register_guest_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        # Then
        assert performer.id is not None
        assert performer.is_guest is True
        assert performer.preselection_score == 10.0
        assert performer.dancer_id == dancer.id


@pytest.mark.asyncio
async def test_register_guest_wrong_phase_fails():
    """Test that guest registration fails outside REGISTRATION phase.

    Validates: BR-GUEST-001
    Gherkin:
        Scenario: Cannot add guest after registration phase ends
        Given a tournament in PRESELECTION phase
        And a category with existing performers
        When I attempt to register a dancer as guest
        Then the system rejects with error "Guests can only be added during Registration phase"
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)
        tournament_repo = TournamentRepository(session)

        # Given - tournament in PRESELECTION phase
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "guest@test.com", "Guest")

        # Advance tournament to PRESELECTION
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            await service.register_guest_performer(
                tournament_id=tournament.id,
                category_id=category.id,
                dancer_id=dancer.id,
            )

        assert "registration phase" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_register_guest_in_duo_category_fails():
    """Test that guests cannot be registered in duo categories.

    Validates: Guest validation rules (guests not allowed in duo categories)
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        duo_category = await create_category(session, tournament.id, is_duo=True)
        dancer = await create_dancer(session, "guest@test.com", "Guest")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            await service.register_guest_performer(
                tournament_id=tournament.id,
                category_id=duo_category.id,
                dancer_id=dancer.id,
            )

        assert "duo" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_convert_regular_to_guest_success():
    """Test converting a regular performer to guest.

    Validates: BR-GUEST-001, BR-GUEST-002
    Gherkin:
        Scenario: Convert regular performer to guest
        Given a tournament in REGISTRATION phase
        And a performer "B-Boy John" is registered as regular
        When I mark "B-Boy John" as a guest
        Then the performer's is_guest becomes true
        And the performer's preselection_score is set to 10.0
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given - regular performer already registered
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "regular@test.com", "Regular")

        regular_performer = await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        assert regular_performer.is_guest is False
        assert regular_performer.preselection_score is None

        # When
        guest_performer = await service.convert_to_guest(regular_performer.id)

        # Then
        assert guest_performer.is_guest is True
        assert guest_performer.preselection_score == 10.0


@pytest.mark.asyncio
async def test_convert_to_guest_already_guest_fails():
    """Test that converting an already-guest performer fails.

    Validates: Guest validation rules (idempotency check)
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)
        dancer = await create_dancer(session, "guest@test.com", "Guest")

        guest_performer = await service.register_guest_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer.id,
        )

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            await service.convert_to_guest(guest_performer.id)

        assert "already a guest" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_guest_count():
    """Test getting guest count for a category.

    Validates: BR-GUEST-003, BR-GUEST-004 (guest count for capacity/minimum calculations)
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)

        # Register 2 regulars and 1 guest
        dancer1 = await create_dancer(session, "regular1@test.com", "Regular 1")
        dancer2 = await create_dancer(session, "regular2@test.com", "Regular 2")
        dancer3 = await create_dancer(session, "guest@test.com", "Guest")

        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer1.id,
        )
        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer2.id,
        )
        await service.register_guest_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer3.id,
        )

        # When
        guest_count = await service.get_guest_count(category.id)

        # Then
        assert guest_count == 1


@pytest.mark.asyncio
async def test_get_regular_performers():
    """Test getting only regular (non-guest) performers.

    Validates: BR-GUEST-002 Scenario "Battles generated only for regular performers"
    Gherkin:
        Given a category with 5 performers (2 guests + 3 regulars)
        When the tournament advances to PRESELECTION
        Then 3 preselection battles are created (one per regular)
        And guests have no battles assigned
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)

        dancer1 = await create_dancer(session, "regular@test.com", "Regular")
        dancer2 = await create_dancer(session, "guest@test.com", "Guest")

        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer1.id,
        )
        await service.register_guest_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer2.id,
        )

        # When
        regular_performers = await service.get_regular_performers(category.id)

        # Then
        assert len(regular_performers) == 1
        assert regular_performers[0].is_guest is False


@pytest.mark.asyncio
async def test_get_guests():
    """Test getting only guest performers.

    Validates: BR-GUEST-002, BR-GUEST-003 (guest filtering for pool distribution)
    """
    async with test_session_maker() as session:
        service = create_performer_service_with_tournament(session)

        # Given
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id, is_duo=False)

        dancer1 = await create_dancer(session, "regular@test.com", "Regular")
        dancer2 = await create_dancer(session, "guest@test.com", "Guest")

        await service.register_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer1.id,
        )
        await service.register_guest_performer(
            tournament_id=tournament.id,
            category_id=category.id,
            dancer_id=dancer2.id,
        )

        # When
        guests = await service.get_guests(category.id)

        # Then
        assert len(guests) == 1
        assert guests[0].is_guest is True
        assert guests[0].preselection_score == 10.0
