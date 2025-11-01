"""Health check endpoints"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.cache.redis_client import get_redis_client
from app.deps import get_db
from app.schemas.profile import HealthResponse, MetricsResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis_client),
) -> HealthResponse:
    """
    Health check endpoint
    
    Verifies connectivity to:
    - Database
    - Redis
    """
    try:
        # Check database
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        # Check Redis
        await redis_client.ping()
        
        return HealthResponse(
            status="healthy",
            version=__version__,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            version=__version__,
            timestamp=datetime.utcnow(),
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    redis_client=Depends(get_redis_client),
) -> MetricsResponse:
    """
    Get application metrics
    
    Returns:
    - Provider call counts
    - Cache hit/miss stats
    - Constraint join stats
    """
    # In a production system, these would be tracked in Redis or a metrics service
    # For now, return placeholder values
    
    return MetricsResponse(
        provider_calls={
            "google": 0,
            "yelp": 0,
        },
        cache_hits=0,
        cache_misses=0,
        join_stats={
            "total": 0,
            "kept": 0,
            "dropped": 0,
        },
    )