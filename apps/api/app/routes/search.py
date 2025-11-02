"""Search endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings  # Add this line
from app.schemas import SearchRequest, SearchResponse
# ... other imports

from app.cache.redis_client import RedisCache, get_redis_client
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    redis_client=Depends(get_redis_client),
) -> SearchResponse:
    """
    Search for places around a location
    
    Supports:
    - Simple queries: "coffee", "italian restaurant"
    - Multi-entity: "restaurant near park with playground"
    - Filters: price, open_now, category
    - Follow-ups: refine previous results
    """

    if not settings.google_places_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_PLACES_API_KEY not configured")
    if not settings.yelp_api_key:
        raise HTTPException(status_code=500, detail="YELP_API_KEY not configured")
    if not settings.openai_api_key:
        raise HTTPException
    
    try:
        cache = RedisCache(redis_client)
        service = SearchService(cache)
        
        response = await service.search(request)
        
        return response
        
    except Exception as e:
        logger.error("search_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))