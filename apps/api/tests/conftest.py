"""Pytest configuration and fixtures"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.models import Base
from app.deps import get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+psycopg://aroundme:aroundme@localhost:5432/aroundme_test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with test_session_maker() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_search_request():
    """Sample search request"""
    return {
        "query": "coffee",
        "lat": 32.814,
        "lng": -96.948,
        "radius_m": 3000,
        "top_k": 10,
    }


@pytest.fixture
def sample_provider_places():
    """Sample provider places for testing"""
    from app.schemas.places import ProviderPlace
    
    return [
        ProviderPlace(
            provider="google",
            provider_id="place_1",
            name="Coffee Shop A",
            lat=32.814,
            lng=-96.948,
            rating=4.5,
            user_rating_count=100,
            price_level=2,
            distance_km=0.5,
        ),
        ProviderPlace(
            provider="yelp",
            provider_id="place_2",
            name="Coffee Shop B",
            lat=32.815,
            lng=-96.949,
            rating=4.3,
            user_rating_count=80,
            price_level=2,
            distance_km=0.8,
        ),
    ]