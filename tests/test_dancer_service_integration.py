"""Integration tests for DancerService.

These tests use REAL repositories and database to catch bugs like:
- Invalid enum references
- Method signature mismatches
- Relationship issues
- Race conditions

See: TESTING.md §Service Integration Tests
"""
import pytest
from datetime import date
from uuid import uuid4

# Use isolated test database - NEVER import from app.db.database!
from tests.conftest import test_session_maker
from app.repositories.dancer import DancerRepository
from app.services.dancer_service import DancerService
from app.exceptions import ValidationError


# =============================================================================
# CREATE DANCER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_create_dancer_success():
    """Test successful dancer creation with all fields."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="bboy@test.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 15),
            blaze="B-Boy Storm",
            country="France",
            city="Paris",
        )

        assert dancer.id is not None
        assert dancer.email == "bboy@test.com"
        assert dancer.first_name == "John"
        assert dancer.last_name == "Doe"
        assert dancer.blaze == "B-Boy Storm"
        assert dancer.country == "France"
        assert dancer.city == "Paris"


@pytest.mark.asyncio
async def test_create_dancer_email_lowercase():
    """Test that email is converted to lowercase."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="BBOY@TEST.COM",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 15),
            blaze="B-Boy Storm",
        )

        assert dancer.email == "bboy@test.com"


@pytest.mark.asyncio
async def test_create_dancer_duplicate_email():
    """Test that duplicate email raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        # Create first dancer
        await service.create_dancer(
            email="unique@test.com",
            first_name="First",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Original",
        )

        # Try to create second dancer with same email
        with pytest.raises(ValidationError) as exc_info:
            await service.create_dancer(
                email="unique@test.com",
                first_name="Second",
                last_name="Dancer",
                date_of_birth=date(1999, 5, 5),
                blaze="Duplicate",
            )

        assert "already registered" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_dancer_age_too_young():
    """Test that dancer under 10 years raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        # Calculate date for 5 year old
        young_date = date(date.today().year - 5, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_dancer(
                email="young@test.com",
                first_name="Young",
                last_name="Kid",
                date_of_birth=young_date,
                blaze="Too Young",
            )

        assert "at least 10 years old" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_dancer_age_too_old():
    """Test that dancer over 100 years raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        # Calculate date for 101 year old
        old_date = date(date.today().year - 101, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_dancer(
                email="old@test.com",
                first_name="Very",
                last_name="Old",
                date_of_birth=old_date,
                blaze="Too Old",
            )

        assert "exceeds 100 years" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_dancer_optional_fields():
    """Test dancer creation with minimal required fields (no country/city)."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="minimal@test.com",
            first_name="Minimal",
            last_name="Dancer",
            date_of_birth=date(1995, 6, 15),
            blaze="B-Boy Minimal",
        )

        assert dancer.id is not None
        assert dancer.country is None
        assert dancer.city is None


# =============================================================================
# UPDATE DANCER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_update_dancer_success():
    """Test successful dancer update."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        # Create dancer
        dancer = await service.create_dancer(
            email="original@test.com",
            first_name="Original",
            last_name="Name",
            date_of_birth=date(2000, 1, 1),
            blaze="Original Blaze",
        )

        # Update dancer
        updated = await service.update_dancer(
            dancer_id=dancer.id,
            first_name="Updated",
            blaze="New Blaze",
        )

        assert updated.first_name == "Updated"
        assert updated.blaze == "New Blaze"
        assert updated.email == "original@test.com"  # Unchanged


@pytest.mark.asyncio
async def test_update_dancer_email_change():
    """Test updating dancer email to a new unique email."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="old@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Test Blaze",
        )

        updated = await service.update_dancer(
            dancer_id=dancer.id,
            email="new@test.com",
        )

        assert updated.email == "new@test.com"


@pytest.mark.asyncio
async def test_update_dancer_email_duplicate():
    """Test that updating email to existing email raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        # Create two dancers
        dancer1 = await service.create_dancer(
            email="dancer1@test.com",
            first_name="Dancer",
            last_name="One",
            date_of_birth=date(2000, 1, 1),
            blaze="Dancer One",
        )

        await service.create_dancer(
            email="dancer2@test.com",
            first_name="Dancer",
            last_name="Two",
            date_of_birth=date(1999, 1, 1),
            blaze="Dancer Two",
        )

        # Try to update dancer1's email to dancer2's email
        with pytest.raises(ValidationError) as exc_info:
            await service.update_dancer(
                dancer_id=dancer1.id,
                email="dancer2@test.com",
            )

        assert "already registered" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_dancer_not_found():
    """Test updating non-existent dancer raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        fake_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.update_dancer(
                dancer_id=fake_id,
                first_name="Ghost",
            )

        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_dancer_age_validation():
    """Test that updating birth date validates age."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="test@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Test",
        )

        # Try to update to too young age
        young_date = date(date.today().year - 5, 1, 1)
        with pytest.raises(ValidationError) as exc_info:
            await service.update_dancer(
                dancer_id=dancer.id,
                date_of_birth=young_date,
            )

        assert "at least 10 years old" in str(exc_info.value)


# =============================================================================
# SEARCH DANCERS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_search_dancers_by_blaze():
    """Test searching dancers by blaze."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        await service.create_dancer(
            email="storm@test.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 1),
            blaze="B-Boy Storm",
        )

        await service.create_dancer(
            email="thunder@test.com",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1999, 1, 1),
            blaze="B-Girl Thunder",
        )

        results = await service.search_dancers("Storm")

        assert len(results) == 1
        assert results[0].blaze == "B-Boy Storm"


@pytest.mark.asyncio
async def test_search_dancers_by_name():
    """Test searching dancers by first/last name."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        await service.create_dancer(
            email="john@test.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2000, 1, 1),
            blaze="Johnny",
        )

        await service.create_dancer(
            email="jane@test.com",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1999, 1, 1),
            blaze="Janey",
        )

        results = await service.search_dancers("Jane")

        assert len(results) == 1
        assert results[0].first_name == "Jane"


@pytest.mark.asyncio
async def test_search_dancers_empty_query():
    """Test that empty query returns all dancers."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        await service.create_dancer(
            email="one@test.com",
            first_name="One",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="First",
        )

        await service.create_dancer(
            email="two@test.com",
            first_name="Two",
            last_name="Dancer",
            date_of_birth=date(1999, 1, 1),
            blaze="Second",
        )

        results = await service.search_dancers("")

        assert len(results) == 2


@pytest.mark.asyncio
async def test_search_dancers_no_results():
    """Test search with no matching results."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        await service.create_dancer(
            email="test@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Tester",
        )

        results = await service.search_dancers("NonExistent")

        assert len(results) == 0


# =============================================================================
# GET DANCER BY ID TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_dancer_by_id_success():
    """Test getting dancer by ID."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        created = await service.create_dancer(
            email="test@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Tester",
        )

        found = await service.get_dancer_by_id(created.id)

        assert found.id == created.id
        assert found.email == created.email


@pytest.mark.asyncio
async def test_get_dancer_by_id_not_found():
    """Test getting non-existent dancer raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        fake_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.get_dancer_by_id(fake_id)

        assert "not found" in str(exc_info.value)


# =============================================================================
# UPDATE DANCER - ADDITIONAL COVERAGE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_update_dancer_age_over_100():
    """Test that updating birth date to age > 100 raises ValidationError."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="age100test@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Test",
        )

        # Try to update to age > 100
        old_date = date(date.today().year - 101, 1, 1)
        with pytest.raises(ValidationError) as exc_info:
            await service.update_dancer(
                dancer_id=dancer.id,
                date_of_birth=old_date,
            )

        assert "exceeds 100 years" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_dancer_all_optional_fields():
    """Test updating all optional fields at once covers all update paths."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="allfields@test.com",
            first_name="Original",
            last_name="Name",
            date_of_birth=date(2000, 1, 1),
            blaze="Original Blaze",
        )

        # Update all fields including optional country/city
        new_dob = date(1995, 6, 15)
        updated = await service.update_dancer(
            dancer_id=dancer.id,
            email="newallfields@test.com",
            first_name="New",
            last_name="Person",
            date_of_birth=new_dob,
            blaze="New Blaze",
            country="Canada",
            city="Toronto",
        )

        assert updated.email == "newallfields@test.com"
        assert updated.first_name == "New"
        assert updated.last_name == "Person"
        assert updated.date_of_birth == new_dob
        assert updated.blaze == "New Blaze"
        assert updated.country == "Canada"
        assert updated.city == "Toronto"


@pytest.mark.asyncio
async def test_update_dancer_same_email_no_error():
    """Test updating dancer with same email doesn't raise duplicate error."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        dancer = await service.create_dancer(
            email="sameemail@test.com",
            first_name="Test",
            last_name="Dancer",
            date_of_birth=date(2000, 1, 1),
            blaze="Test",
        )

        # Update with same email - should not raise
        updated = await service.update_dancer(
            dancer_id=dancer.id,
            email="sameemail@test.com",  # Same email
            first_name="Updated",
        )

        assert updated.email == "sameemail@test.com"
        assert updated.first_name == "Updated"


@pytest.mark.asyncio
async def test_search_dancers_whitespace_query():
    """Test that whitespace-only query returns all dancers."""
    async with test_session_maker() as session:
        dancer_repo = DancerRepository(session)
        service = DancerService(dancer_repo)

        await service.create_dancer(
            email="whitespace@test.com",
            first_name="Whitespace",
            last_name="Test",
            date_of_birth=date(2000, 1, 1),
            blaze="WS Dancer",
        )

        # Whitespace-only query should return all (calls get_all)
        results = await service.search_dancers("   ")

        assert len(results) >= 1
