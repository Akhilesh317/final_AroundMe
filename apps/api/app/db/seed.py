"""Database seeding script"""
import asyncio
from datetime import datetime

from sqlalchemy import select

from app.db.models import Profile, ProfilePreference, SearchLog
from app.db.session import async_session_maker


async def seed_database():
    """Seed the database with sample data"""
    async with async_session_maker() as session:
        print("Seeding database...")
        
        # Check if already seeded
        result = await session.execute(select(Profile))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return
        
        # Create demo profile
        demo_profile = Profile(user_id="demo_user")
        session.add(demo_profile)
        await session.flush()
        
        # Add demo preferences
        preferences = [
            ProfilePreference(
                profile_id=demo_profile.id,
                key="category",
                value="cafe",
                weight=0.8,
            ),
            ProfilePreference(
                profile_id=demo_profile.id,
                key="cuisine",
                value="italian",
                weight=0.7,
            ),
            ProfilePreference(
                profile_id=demo_profile.id,
                key="feat_wifi",
                value="true",
                weight=0.6,
            ),
        ]
        
        for pref in preferences:
            session.add(pref)
        
        # Add sample search log
        search_log = SearchLog(
            conversation_id="demo-conv-1",
            request_json={
                "query": "coffee",
                "lat": 32.814,
                "lng": -96.948,
                "radius_m": 3000,
            },
            response_meta={
                "places_count": 25,
                "cache_hit": False,
            },
        )
        session.add(search_log)
        
        await session.commit()
        print("Database seeded successfully!")
        print(f"- Created profile: {demo_profile.user_id}")
        print(f"- Added {len(preferences)} preferences")
        print("- Added 1 search log entry")


if __name__ == "__main__":
    asyncio.run(seed_database())