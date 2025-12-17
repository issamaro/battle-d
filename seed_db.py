"""Seed the database with initial data for development/testing."""
import asyncio
from datetime import date
from app.db.database import async_session_maker
from app.repositories.user import UserRepository
from app.repositories.dancer import DancerRepository
from app.models.user import UserRole


# Sample dancer data: 40 realistic dancers with diverse backgrounds
SAMPLE_DANCERS = [
    # International breaking legends (blazes)
    {"email": "bboy.storm@example.com", "first_name": "Niels", "last_name": "Robitzky", "blaze": "Storm", "dob": date(1985, 3, 15), "country": "Germany", "city": "Berlin"},
    {"email": "bboy.menno@example.com", "first_name": "Menno", "last_name": "van Gorp", "blaze": "Menno", "dob": date(1991, 6, 20), "country": "Netherlands", "city": "Tilburg"},
    {"email": "bgirl.ami@example.com", "first_name": "Ami", "last_name": "Yuasa", "blaze": "Ami", "dob": date(1998, 4, 10), "country": "Japan", "city": "Osaka"},
    {"email": "bboy.victor@example.com", "first_name": "Victor", "last_name": "Montalvo", "blaze": "Victor", "dob": date(1997, 8, 5), "country": "USA", "city": "Kissimmee"},
    {"email": "bgirl.kastet@example.com", "first_name": "Katerina", "last_name": "Dereli", "blaze": "Kastet", "dob": date(1997, 11, 22), "country": "Ukraine", "city": "Kyiv"},
    # More international dancers
    {"email": "bboy.lil.g@example.com", "first_name": "Gavriel", "last_name": "Garcia", "blaze": "Lil G", "dob": date(1993, 2, 28), "country": "Venezuela", "city": "Caracas"},
    {"email": "bgirl.logistx@example.com", "first_name": "Logan", "last_name": "Edra", "blaze": "Logistx", "dob": date(2004, 1, 14), "country": "USA", "city": "San Diego"},
    {"email": "bboy.phil@example.com", "first_name": "Phil", "last_name": "Kim", "blaze": "Phil Wizard", "dob": date(1998, 9, 3), "country": "Canada", "city": "Vancouver"},
    {"email": "bgirl.ayumi@example.com", "first_name": "Ayumi", "last_name": "Fukushima", "blaze": "Ayumi", "dob": date(1999, 7, 18), "country": "Japan", "city": "Tokyo"},
    {"email": "bboy.shigekix@example.com", "first_name": "Shigeyuki", "last_name": "Nakarai", "blaze": "Shigekix", "dob": date(2002, 3, 11), "country": "Japan", "city": "Yokohama"},
    # French scene
    {"email": "bboy.lilou@example.com", "first_name": "Ali", "last_name": "Ramdani", "blaze": "Lilou", "dob": date(1984, 12, 5), "country": "France", "city": "Lyon"},
    {"email": "bgirl.sarah@example.com", "first_name": "Sarah", "last_name": "Bee", "blaze": "Sarah Bee", "dob": date(1995, 5, 20), "country": "France", "city": "Paris"},
    {"email": "bboy.mounir@example.com", "first_name": "Mounir", "last_name": "Biba", "blaze": "Mounir", "dob": date(1985, 8, 12), "country": "France", "city": "Montpellier"},
    {"email": "bgirl.carlota@example.com", "first_name": "Carlota", "last_name": "Dudek", "blaze": "Carlota", "dob": date(2000, 4, 8), "country": "France", "city": "Nice"},
    {"email": "bboy.lagaet@example.com", "first_name": "Gaetan", "last_name": "Aissa", "blaze": "Lagaet", "dob": date(1994, 10, 30), "country": "France", "city": "Marseille"},
    # Korean scene
    {"email": "bboy.hong10@example.com", "first_name": "Hong", "last_name": "Sung Jin", "blaze": "Hong 10", "dob": date(1984, 1, 25), "country": "South Korea", "city": "Seoul"},
    {"email": "bgirl.yell@example.com", "first_name": "Kim", "last_name": "Ye Ri", "blaze": "Yell", "dob": date(1998, 6, 15), "country": "South Korea", "city": "Busan"},
    {"email": "bboy.wing@example.com", "first_name": "Park", "last_name": "Ji Sung", "blaze": "Wing", "dob": date(1987, 9, 8), "country": "South Korea", "city": "Seoul"},
    {"email": "bgirl.zooty@example.com", "first_name": "Lee", "last_name": "Su Min", "blaze": "Zooty", "dob": date(2001, 3, 22), "country": "South Korea", "city": "Incheon"},
    {"email": "bboy.vero@example.com", "first_name": "Choi", "last_name": "Jun Ho", "blaze": "Vero", "dob": date(1995, 11, 17), "country": "South Korea", "city": "Daegu"},
    # USA scene
    {"email": "bboy.darkness@example.com", "first_name": "Brandon", "last_name": "Mitchell", "blaze": "Darkness", "dob": date(1992, 7, 4), "country": "USA", "city": "New York"},
    {"email": "bgirl.sunny@example.com", "first_name": "Sunny", "last_name": "Choi", "blaze": "Sunny", "dob": date(1994, 2, 14), "country": "USA", "city": "Boston"},
    {"email": "bboy.neguin@example.com", "first_name": "Marcus", "last_name": "Pereira", "blaze": "Neguin", "dob": date(1988, 5, 30), "country": "Brazil", "city": "São Paulo"},
    {"email": "bgirl.terra@example.com", "first_name": "Terra", "last_name": "Kimura", "blaze": "Terra", "dob": date(1996, 8, 25), "country": "USA", "city": "Los Angeles"},
    {"email": "bboy.gravity@example.com", "first_name": "Derek", "last_name": "Martin", "blaze": "Gravity", "dob": date(1990, 12, 1), "country": "USA", "city": "Chicago"},
    # UK scene
    {"email": "bboy.sunni@example.com", "first_name": "Darius", "last_name": "Smith", "blaze": "Sunni", "dob": date(1997, 4, 19), "country": "UK", "city": "London"},
    {"email": "bgirl.roxy@example.com", "first_name": "Roxanne", "last_name": "Williams", "blaze": "Roxy", "dob": date(1999, 10, 7), "country": "UK", "city": "Manchester"},
    {"email": "bboy.killa.t@example.com", "first_name": "Thomas", "last_name": "Johnson", "blaze": "Killa T", "dob": date(1993, 6, 28), "country": "UK", "city": "Birmingham"},
    {"email": "bgirl.vanessa@example.com", "first_name": "Vanessa", "last_name": "Marina", "blaze": "Vanessa", "dob": date(1995, 1, 12), "country": "Portugal", "city": "Lisbon"},
    {"email": "bboy.lil.zoo@example.com", "first_name": "Zuhayr", "last_name": "Abbas", "blaze": "Lil Zoo", "dob": date(1996, 9, 16), "country": "UK", "city": "Leeds"},
    # Additional diverse dancers
    {"email": "bboy.cico@example.com", "first_name": "Federico", "last_name": "Rossi", "blaze": "Cico", "dob": date(1989, 3, 5), "country": "Italy", "city": "Milan"},
    {"email": "bgirl.india@example.com", "first_name": "Priya", "last_name": "Sharma", "blaze": "India", "dob": date(2000, 7, 22), "country": "India", "city": "Mumbai"},
    {"email": "bboy.issei@example.com", "first_name": "Issei", "last_name": "Hino", "blaze": "Issei", "dob": date(1997, 11, 3), "country": "Japan", "city": "Fukuoka"},
    {"email": "bgirl.emma@example.com", "first_name": "Emma", "last_name": "Anderson", "blaze": "B-Girl Emma", "dob": date(1998, 5, 9), "country": "Sweden", "city": "Stockholm"},
    {"email": "bboy.mad.max@example.com", "first_name": "Maxime", "last_name": "Dubois", "blaze": "Mad Max", "dob": date(1991, 8, 14), "country": "Belgium", "city": "Brussels"},
    {"email": "bgirl.nina@example.com", "first_name": "Nina", "last_name": "Volkov", "blaze": "Nina", "dob": date(1996, 2, 27), "country": "Russia", "city": "Moscow"},
    {"email": "bboy.spinmaster@example.com", "first_name": "Carlos", "last_name": "Rodriguez", "blaze": "Spinmaster", "dob": date(1994, 12, 18), "country": "Spain", "city": "Madrid"},
    {"email": "bgirl.maya@example.com", "first_name": "Maya", "last_name": "Chen", "blaze": "Maya", "dob": date(2001, 4, 3), "country": "Taiwan", "city": "Taipei"},
    {"email": "bboy.kid.freeze@example.com", "first_name": "Ahmad", "last_name": "Hassan", "blaze": "Kid Freeze", "dob": date(1999, 6, 11), "country": "Egypt", "city": "Cairo"},
    {"email": "bgirl.aurora@example.com", "first_name": "Aurora", "last_name": "Silva", "blaze": "Aurora", "dob": date(1997, 9, 29), "country": "Brazil", "city": "Rio de Janeiro"},
]


async def seed_database():
    """Seed database with default users and dancers."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        dancer_repo = DancerRepository(session)

        # === Seed Users ===
        print("👤 Seeding users...")

        # Check if admin already exists
        admin = await user_repo.get_by_email("admin@battle-d.com")
        if admin:
            print("  ✓ Admin user already exists")
        else:
            admin = await user_repo.create_user(
                email="admin@battle-d.com",
                first_name="Admin",
                role=UserRole.ADMIN,
            )
            print(f"  ✓ Created admin user: {admin.email}")

        # Check if staff already exists
        staff = await user_repo.get_by_email("staff@battle-d.com")
        if staff:
            print("  ✓ Staff user already exists")
        else:
            staff = await user_repo.create_user(
                email="staff@battle-d.com",
                first_name="Staff",
                role=UserRole.STAFF,
            )
            print(f"  ✓ Created staff user: {staff.email}")

        # Check if MC already exists
        mc = await user_repo.get_by_email("mc@battle-d.com")
        if mc:
            print("  ✓ MC user already exists")
        else:
            mc = await user_repo.create_user(
                email="mc@battle-d.com",
                first_name="MC",
                role=UserRole.MC,
            )
            print(f"  ✓ Created MC user: {mc.email}")

        # === Seed Dancers ===
        print("\n💃 Seeding dancers...")
        created_count = 0
        existing_count = 0

        for dancer_data in SAMPLE_DANCERS:
            existing = await dancer_repo.get_by_email(dancer_data["email"])
            if existing:
                existing_count += 1
            else:
                await dancer_repo.create_dancer(
                    email=dancer_data["email"],
                    first_name=dancer_data["first_name"],
                    last_name=dancer_data["last_name"],
                    date_of_birth=dancer_data["dob"],
                    blaze=dancer_data["blaze"],
                    country=dancer_data.get("country"),
                    city=dancer_data.get("city"),
                )
                created_count += 1

        if existing_count > 0:
            print(f"  ✓ {existing_count} dancers already exist")
        if created_count > 0:
            print(f"  ✓ Created {created_count} new dancers")

        await session.commit()
        print("\n✅ Database seeded successfully!")


if __name__ == "__main__":
    print("🌱 Seeding database...")
    asyncio.run(seed_database())
