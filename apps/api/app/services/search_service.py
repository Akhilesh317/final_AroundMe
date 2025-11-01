"""Search service orchestration"""
import time
from typing import Optional
from uuid import uuid4

from app.agent.graph import DiscoveryAgent
from app.cache.redis_client import RedisCache
from app.cache.result_store import ResultStore, generate_cache_key
from app.schemas.search import SearchRequest, SearchResponse
from app.utils.logging import get_logger, set_trace_id

logger = get_logger(__name__)


class SearchService:
    """Search service"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.result_store = ResultStore(cache)
        self.agent = DiscoveryAgent()
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute search request"""
        
        # Generate trace ID
        trace_id = str(uuid4())
        set_trace_id(trace_id)
        
        start_time = time.time()
        
        logger.info(
            "search_start",
            query=request.query,
            lat=request.lat,
            lng=request.lng,
            radius_m=request.radius_m,
        )
        
        # Check for follow-up
        if request.context and request.context.follow_up:
            return await self._handle_followup(request, trace_id)
        
        # Check cache
        cache_key = generate_cache_key(
            query=request.query,
            lat=request.lat,
            lng=request.lng,
            radius_m=request.radius_m,
            filters=request.filters.model_dump() if request.filters else None,
            ranking_preset=request.context.ranking_preset if request.context else None,
            multi_entity=request.multi_entity.model_dump() if request.multi_entity else None,
        )
        
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.info("cache_hit", cache_key=cache_key)
            cached_response["debug"]["cache_hit"] = True
            cached_response["debug"]["agent_trace_id"] = trace_id
            return SearchResponse(**cached_response)
        
        # Run agent
        places, debug = await self.agent.run(
            query=request.query,
            lat=request.lat,
            lng=request.lng,
            radius_m=request.radius_m,
            filters=request.filters.model_dump() if request.filters else {},
            context=request.context.model_dump() if request.context else {},
            top_k=request.top_k,
        )
        
        # Store result set
        conversation_id = request.context.conversation_id if request.context else None
        result_set_id = await self.result_store.store_result_set(
            places=[p.model_dump() for p in places],
            conversation_id=conversation_id,
        )
        
        # Build response
        debug.agent_trace_id = trace_id
        debug.timings["total"] = time.time() - start_time
        
        response = SearchResponse(
            places=places,
            debug=debug,
            result_set_id=result_set_id,
        )
        
        # Cache response
        await self.cache.set(cache_key, response.model_dump())
        
        logger.info(
            "search_complete",
            places_count=len(places),
            duration_s=debug.timings["total"],
        )
        
        return response
    
    async def _handle_followup(
        self,
        request: SearchRequest,
        trace_id: str,
    ) -> SearchResponse:
        """Handle follow-up query that refines previous results"""
        
        logger.info("followup_start", conversation_id=request.context.conversation_id)
        
        # Get previous result set
        previous_places = None
        if request.context.result_set_id:
            previous_places = await self.result_store.get_result_set(
                request.context.result_set_id
            )
        elif request.context.conversation_id:
            previous_places = await self.result_store.get_latest_result_set(
                request.context.conversation_id
            )
        
        if not previous_places:
            logger.warning("followup_no_previous_results")
            # Fall back to regular search
            request.context.follow_up = False
            return await self.search(request)
        
        # Filter previous results based on new criteria
        from app.schemas.places import Place
        
        filtered_places = []
        for place_dict in previous_places:
            place = Place(**place_dict)
            
            # Apply filters
            if request.filters:
                # Price filter
                if request.filters.price and place.price_level is not None:
                    min_price, max_price = request.filters.price
                    if not (min_price <= place.price_level <= max_price):
                        continue
                
                # Category filter
                if request.filters.category:
                    categories = (
                        [request.filters.category]
                        if isinstance(request.filters.category, str)
                        else request.filters.category
                    )
                    if place.category not in categories:
                        continue
            
            # Check for must-haves in query
            if request.query:
                from app.fusion.amenities import check_must_haves
                
                # Extract must-haves from query (simplified)
                must_haves = []
                query_lower = request.query.lower()
                if "changing station" in query_lower or "changing_station" in query_lower:
                    must_haves.append("changing_station")
                if "wifi" in query_lower:
                    must_haves.append("wifi")
                if "outdoor seating" in query_lower:
                    must_haves.append("outdoor_seating")
                
                if must_haves:
                    satisfied, matched = check_must_haves(place.features, must_haves)
                    if not satisfied:
                        continue
            
            filtered_places.append(place)
        
        # Store filtered result set
        result_set_id = await self.result_store.store_result_set(
            places=[p.model_dump() for p in filtered_places],
            conversation_id=request.context.conversation_id,
        )
        
        # Build debug info
        from app.schemas.search import SearchDebug
        
        debug = SearchDebug(
            timings={"followup_filter": 0.1, "total": 0.1},
            cache_hit=False,
            agent_trace_id=trace_id,
            counts_before_after={
                "before": len(previous_places),
                "after": len(filtered_places),
            },
            ranking_preset="balanced",
            constraints_satisfied={},
            agent_mode="followup",
        )
        
        logger.info(
            "followup_complete",
            before_count=len(previous_places),
            after_count=len(filtered_places),
        )
        
        return SearchResponse(
            places=filtered_places[:request.top_k],
            debug=debug,
            result_set_id=result_set_id,
        )
    
    async def close(self):
        """Close connections"""
        await self.agent.close()