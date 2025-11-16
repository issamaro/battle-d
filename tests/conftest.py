"""Shared test configuration and fixtures."""
import pytest
import pytest_asyncio
from app.db.database import init_db, drop_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """Setup and teardown test database for each test.

    This fixture automatically runs before and after each test function.
    It ensures a clean database state for every test.
    """
    # Ensure clean state by dropping any existing tables
    await drop_db()

    # Create all tables fresh
    await init_db()

    yield

    # Clean up after test
    await drop_db()
