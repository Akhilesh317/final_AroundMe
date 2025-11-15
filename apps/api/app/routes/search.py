"""Search endpoints"""
from typing import List, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response
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

# In-memory storage for places (since Redis is failing)
_place_cache: dict[str, dict[str, Any]] = {}
_result_sets: dict[str, List[str]] = {}  # ✅ NEW: Track which places belong to which result set


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    response: Response,
    redis_client=Depends(get_redis_client),
) -> SearchResponse:
    """Search for places around a location"""
    print(f"\n🚀 ROUTE ENTERED: query={request.query}, is_followup={request.context and request.context.follow_up}")
    logger.info("🚀 route_entered", query=request.query)


    # Validate API keys
    if not settings.google_places_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_PLACES_API_KEY not configured")
    if not settings.yelp_api_key:
        raise HTTPException(status_code=500, detail="YELP_API_KEY not configured")
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    print("✅ API keys validated")

    try:
        cache = RedisCache(redis_client)
        service = SearchService(cache)
        print(f"✅ Service created")

        
        # ✅ CHECK IF THIS IS A FOLLOW-UP QUERY
        is_followup = request.context and request.context.follow_up
        print(f"✅ is_followup={is_followup}")

        
        if is_followup and request.context.result_set_id:
            logger.info("followup_detected", result_set_id=request.context.result_set_id)
            print(f"✅ FOLLOWUP PATH: result_set_id={request.context.result_set_id}")
            # ✅ Get places from in-memory cache
            result_set_id = request.context.result_set_id
            place_ids = _result_sets.get(result_set_id, [])
            
            print(f"🔍 Looking for result_set_id: {result_set_id}")
            print(f"📦 Available result_sets: {list(_result_sets.keys())}")
            print(f"🎯 Found place_ids: {len(place_ids)}")
            
            if place_ids:
                print(f"✅ FOUND {len(place_ids)} places in result set!")
                # ... rest of code
            else:
                print(f"❌ NO PLACES FOUND for result_set_id={result_set_id}")
                print(f"❌ This means frontend sent wrong ID or backend didn't store it")

                    
            if place_ids:
                logger.info("using_inmemory_cache", 
                           result_set_id=result_set_id,
                           place_count=len(place_ids))
                
                # Reconstruct places from cache
                from app.schemas.places import Place
                cached_places = []
                for place_id in place_ids:
                    if place_id in _place_cache:
                        cached_places.append(Place(**_place_cache[place_id]))
                
                if cached_places:
                    original_query = request.context.original_query or request.query
                    
                    # Parse follow-up intent
                    intent = await parse_followup(
                        followup_text=request.query,
                        original_query=original_query,
                        current_radius=request.radius_m
                    )
                    
                    logger.info("followup_parsed", 
                               intent=intent.model_dump(),
                               cached_count=len(cached_places))
                    
                    if intent.is_new_search and intent.new_query:
                        # New search needed
                        logger.info("followup_new_search", new_query=intent.new_query)
                        request.query = intent.new_query
                        response = await service.search(request)
                    else:
                        # ✅ Filter existing results
                        logger.info("followup_filtering", filter_count=len(cached_places))
                        response = await apply_followup_filters(
                            places=[p.model_dump() for p in cached_places],
                            intent=intent,
                            request=request
                        )
                        
                        # ✅ Generate conversational response
                        try:
                            from app.services.conversation_responder import generate_conversational_response
                            
                            conversational_text = await generate_conversational_response(
                                query=request.query,
                                places=response.places,
                                context={
                                    "original_query": original_query,
                                    "follow_up": True
                                }
                            )
                            response.conversational_response = conversational_text
                            logger.info("conversational_response_added", 
                                       length=len(conversational_text))
                            
                        except Exception as e:
                            logger.error("conversational_response_failed", error=str(e))
                            import traceback
                            traceback.print_exc()
                    
                    # Store filtered results
                    new_result_set_id = str(uuid4())
                    new_place_ids = []
                    
                    for place in response.places:
                        place_id = str(place.id)
                        _place_cache[place_id] = place.model_dump()
                        new_place_ids.append(place_id)
                    
                    _result_sets[new_result_set_id] = new_place_ids
                    response.result_set_id = new_result_set_id
                    
                    logger.info("followup_complete", 
                               filtered_count=len(response.places))
                    print(f"✅ FOLLOWUP COMPLETE: {len(response.places)} places after filtering")
                    # ✅ Add no-cache headers
                    return Response(
                        content=response.model_dump_json(),
                        media_type="application/json",
                        headers={
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0"
                        }
                    )

                                
            logger.warning("followup_no_cache", 
                          result_set_id=result_set_id,
                          cache_size=len(_place_cache))
        
        # ✅ NORMAL SEARCH (NOT A FOLLOW-UP)
        logger.info("normal_search", query=request.query)
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
        
        # ✅ Store places in cache with result set tracking
        result_set_id = str(uuid4())
        place_ids = []
        
        for place in response.places:
            place_id = str(place.id)
            _place_cache[place_id] = place.model_dump()
            place_ids.append(place_id)
        
        _result_sets[result_set_id] = place_ids
        response.result_set_id = result_set_id
        
        logger.info("search_complete", 
                   place_count=len(response.places),
                   result_set_id=result_set_id,
                   cache_size=len(_place_cache))
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("search_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/places/{place_id}")
async def get_place_details(place_id: str):
    """Get detailed information about a specific place"""
    
    if place_id not in _place_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Place not found. Please search again."
        )
    
    return _place_cache[place_id]


@router.get("/debug/cache")
async def debug_cache():
    """Debug endpoint to check what's in the cache"""
    return {
        "cache_size": len(_place_cache),
        "result_sets": len(_result_sets),
        "place_ids": list(_place_cache.keys())[:10],
        "result_set_ids": list(_result_sets.keys())[:5],
    }


async def apply_followup_filters(
    places: List[dict],
    intent,
    request: SearchRequest
):
    """Apply AI-parsed filters to existing results"""
    
    from app.schemas.places import Place
    place_objects = [Place(**p) for p in places]
    
    filtered_places = place_objects
    
    # Apply filters based on intent
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
    
    # Sort results
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
