"""Search endpoints"""
from typing import List, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.schemas import SearchRequest, SearchResponse, Place
from app.schemas.search import SearchDebug
from app.cache.redis_client import RedisCache, get_redis_client
from app.services.search_service import SearchService
from app.services.followup_parser import parse_followup
from app.services.feature_analyzer import analyze_features
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

# ✅ STEP 1: In-memory storage (at the TOP, after router definition)
_place_cache: dict[str, dict[str, Any]] = {}


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    redis_client=Depends(get_redis_client),
) -> SearchResponse:
    """Search for places around a location"""

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
            # Handle follow-up logic...
            try:
                cached_results = await cache.get(f"results:{request.context.result_set_id}")
                
                if cached_results:
                    original_query = request.context.original_query or request.query
                    intent = await parse_followup(
                        followup_text=request.query,
                        original_query=original_query,
                        current_radius=request.radius_m
                    )
                    
                    logger.info("followup_parsed", intent=intent.model_dump())
                    
                    if intent.is_new_search and intent.new_query:
                        request.query = intent.new_query
                        response = await service.search(request)
                    else:
                        response = await apply_followup_filters(
                            places=cached_results.get("places", []),
                            intent=intent,
                            request=request
                        )
                    
                    # Store follow-up results too
                    for place in response.places:
                        _place_cache[place.id] = place.model_dump()
                    
                    return response
            except Exception as e:
                logger.warning("followup_cache_failed", error=str(e))
        
        # Normal search
        response = await service.search(request)
        
        # AI-powered feature analysis
        if response.places and len(response.places) > 0:
            try:
                feature_analysis = await analyze_features(
                    places=response.places,
                    original_query=request.query or "",
                    user_requirements=[]
                )
                
                if not response.debug:
                    response.debug = SearchDebug(
                        timings={"total": 0},
                        cache_hit=False,
                        agent_trace_id="",
                        counts_before_after={},
                        ranking_preset="balanced",
                        agent_mode="full"
                    )
                
                response.debug.feature_analysis = feature_analysis
            except Exception as e:
                logger.warning("feature_analysis_failed", error=str(e))
        
        # ✅ STEP 2: Store places in cache (RIGHT BEFORE return statement)
        # ✅ STEP 2: Store places in cache (RIGHT BEFORE return statement)
            print(f"\n{'='*60}")
            print(f"DEBUG: About to cache {len(response.places)} places")
            print(f"{'='*60}")

            for place in response.places:
                place_dict = place.model_dump()
                place_id = str(place.id)  # ✅ Convert UUID to string
                _place_cache[place_id] = place_dict
                print(f"✅ Cached: {place_id[:8]}... | {place.name}")

            print(f"\n📦 Total cache size: {len(_place_cache)} places")
            print(f"{'='*60}\n")
        
        
        # Try Redis cache (optional, can fail)
        result_set_id = str(uuid4())
        try:
            await cache.set(
                f"results:{result_set_id}",
                {"places": [p.model_dump() for p in response.places]},
                ttl=900
            )
        except Exception as e:
            logger.warning("redis_cache_failed", error=str(e))
        
        response.result_set_id = result_set_id
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("search_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ✅ STEP 3: Place details endpoint with debug
@router.get("/places/{place_id}")
async def get_place_details(place_id: str):
    """Get detailed information about a specific place"""
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG: Looking for place_id: {place_id}")
    print(f"📦 Cache size: {len(_place_cache)} places")
    print(f"🔑 First 5 IDs in cache: {list(_place_cache.keys())[:5]}")
    print(f"❓ Is requested ID in cache? {place_id in _place_cache}")
    print(f"{'='*60}\n")
    
    if place_id not in _place_cache:
        print(f"❌ ERROR: Place {place_id} NOT FOUND in cache!")
        print(f"Available IDs: {list(_place_cache.keys())}")
        raise HTTPException(
            status_code=404,
            detail=f"Place not found. Cache has {len(_place_cache)} places. Please search again."
        )
    
    print(f"✅ SUCCESS: Found place {place_id}")
    return _place_cache[place_id]


# ✅ STEP 4: Debug endpoint to check cache
@router.get("/debug/cache")
async def debug_cache():
    """Debug endpoint to check what's in the cache"""
    return {
        "cache_size": len(_place_cache),
        "place_ids": list(_place_cache.keys()),
        "place_names": [p.get("name") for p in _place_cache.values()],
        "sample_place": list(_place_cache.values())[0] if _place_cache else None
    }


# Helper function for follow-up filtering
async def apply_followup_filters(
    places: List[dict],
    intent,
    request: SearchRequest
):
    """Apply AI-parsed filters to existing results"""
    
    from app.schemas.places import Place
    place_objects = [Place(**p) for p in places]
    
    filtered_places = place_objects
    
    if intent.adjust_radius:
        filtered_places = [
            p for p in filtered_places
            if not p.distance_km or (p.distance_km * 1000) <= intent.adjust_radius
        ]
    
    if intent.price_min is not None and intent.price_max is not None:
        filtered_places = [
            p for p in filtered_places
            if p.price_level and intent.price_min <= p.price_level <= intent.price_max
        ]
    
    if intent.min_rating:
        filtered_places = [
            p for p in filtered_places
            if p.rating and p.rating >= intent.min_rating
        ]
    
    if intent.sort_by == "distance":
        filtered_places.sort(key=lambda p: p.distance_km or 999)
    elif intent.sort_by == "rating":
        filtered_places.sort(key=lambda p: p.rating or 0, reverse=True)
    else:
        filtered_places.sort(key=lambda p: p.score, reverse=True)
    
    filtered_places = filtered_places[:request.top_k]
    
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
