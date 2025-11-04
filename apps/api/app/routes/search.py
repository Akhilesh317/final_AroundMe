"""Search endpoints"""
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.schemas import SearchRequest, SearchResponse, Place
from app.schemas.search import SearchDebug
from app.cache.redis_client import RedisCache, get_redis_client
from app.services.search_service import SearchService
from app.services.followup_parser import parse_followup
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

    # Validate API keys
    if not settings.google_places_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_PLACES_API_KEY not configured")
    if not settings.yelp_api_key:
        raise HTTPException(status_code=500, detail="YELP_API_KEY not configured")
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        cache = RedisCache(redis_client)
        service = SearchService(cache)
        
        # Check if this is a follow-up query
        is_followup = request.context and request.context.follow_up
        
        if is_followup and request.context.result_set_id:
            # Try to get original results from cache
            cached_results = await cache.get(f"results:{request.context.result_set_id}")
            
            if cached_results:
                # Parse follow-up intent using OpenAI
                original_query = request.context.original_query or request.query
                intent = await parse_followup(
                    followup_text=request.query,
                    original_query=original_query,
                    current_radius=request.radius_m
                )
                
                logger.info("followup_parsed", intent=intent.model_dump())
                
                # If it's a new search, do normal search
                if intent.is_new_search and intent.new_query:
                    request.query = intent.new_query
                    response = await service.search(request)
                else:
                    # Apply filters to cached results
                    response = await apply_followup_filters(
                        places=cached_results.get("places", []),
                        intent=intent,
                        request=request
                    )
                
                return response
        
        # Normal search
        response = await service.search(request)
        
        # Cache results for potential follow-ups
        result_set_id = str(uuid4())
        await cache.set(
            f"results:{result_set_id}",
            {"places": [p.model_dump() for p in response.places]},
            ttl=900  # 15 minutes
        )
        response.result_set_id = result_set_id
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("search_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def apply_followup_filters(
    places: List[dict],
    intent,
    request: SearchRequest
) -> SearchResponse:
    """Apply AI-parsed filters to existing results"""
    
    # Convert dict to Place objects
    from app.schemas.places import Place
    place_objects = [Place(**p) for p in places]
    
    filtered_places = place_objects
    
    # 1. Distance filter
    if intent.adjust_radius:
        filtered_places = [
            p for p in filtered_places
            if not p.distance_km or (p.distance_km * 1000) <= intent.adjust_radius
        ]
    
    # 2. Price filter
    if intent.price_min is not None and intent.price_max is not None:
        filtered_places = [
            p for p in filtered_places
            if p.price_level and intent.price_min <= p.price_level <= intent.price_max
        ]
    
    # 3. Rating filter
    if intent.min_rating:
        filtered_places = [
            p for p in filtered_places
            if p.rating and p.rating >= intent.min_rating
        ]
    
    # 4. Feature filter
    if intent.required_features:
        for feature in intent.required_features:
            feature_key = f"feat_{feature}"
            filtered_places = [
                p for p in filtered_places
                if p.features.get(feature_key, 0) > 0.5
            ]
    
    # 5. Sort
    if intent.sort_by == "distance":
        filtered_places.sort(key=lambda p: p.distance_km or 999)
    elif intent.sort_by == "rating":
        filtered_places.sort(key=lambda p: p.rating or 0, reverse=True)
    elif intent.sort_by == "price":
        filtered_places.sort(key=lambda p: p.price_level or 999)
    else:
        # Keep score-based sorting
        filtered_places.sort(key=lambda p: p.score, reverse=True)
    
    # Limit to top_k
    filtered_places = filtered_places[:request.top_k]
    
    # Return filtered results
    return SearchResponse(
        places=filtered_places,
        debug=SearchDebug(
            timings={"total": 0.05, "followup_filter": 0.05},
            cache_hit=True,
            agent_trace_id="followup",
            counts_before_after={
                "original": len(places),
                "filtered": len(filtered_places)
            },
            ranking_preset="followup",
            agent_mode="followup"
        ),
        result_set_id=str(uuid4())
    )