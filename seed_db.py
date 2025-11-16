"""Seed the database with initial data for development/testing."""
import asyncio
from app.db.database import async_session_maker
from app.repositories.user import UserRepository
from app.models.user import UserRole


async def seed_database():
    """Seed database with default users."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)

        # Check if admin already exists
        admin = await user_repo.get_by_email("admin@battle-d.com")
        if admin:
            print("✓ Admin user already exists")
        else:
            # Create default admin user
            admin = await user_repo.create_user(
                email="admin@battle-d.com",
                first_name="Admin",
                role=UserRole.ADMIN,
            )
            print(f"✓ Created admin user: {admin.email}")

        # Check if staff already exists
        staff = await user_repo.get_by_email("staff@battle-d.com")
        if staff:
            print("✓ Staff user already exists")
        else:
            # Create default staff user
            staff = await user_repo.create_user(
                email="staff@battle-d.com",
                first_name="Staff",
                role=UserRole.STAFF,
            )
            print(f"✓ Created staff user: {staff.email}")

        # Check if MC already exists
        mc = await user_repo.get_by_email("mc@battle-d.com")
        if mc:
            print("✓ MC user already exists")
        else:
            # Create default MC user
            mc = await user_repo.create_user(
                email="mc@battle-d.com",
                first_name="MC",
                role=UserRole.MC,
            )
            print(f"✓ Created MC user: {mc.email}")

        await session.commit()
        print("\n✅ Database seeded successfully!")


if __name__ == "__main__":
    print("🌱 Seeding database...")
    asyncio.run(seed_database())
