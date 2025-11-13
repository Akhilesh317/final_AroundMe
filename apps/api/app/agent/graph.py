"""LangGraph agent graph definition"""
from typing import Dict, List

from app.agent.nodes import (
    AgentState,
    call_providers_node,
    constraint_join_node,
    format_answer_node,
    fuse_dedupe_node,
    parse_intent_node,
    plan_node,
    score_rank_node,
    validate_node,
)
from app.agent.tools import SearchTool
from app.config import settings
from app.schemas.places import Place
from app.schemas.search import SearchDebug
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DiscoveryAgent:
    """Agent for local discovery"""
    
    def __init__(self):
        # ✅ SearchTool no longer needs provider instances
        self.search_tool = SearchTool()
    
    async def run(
        self,
        query: str,
        lat: float,
        lng: float,
        radius_m: int,
        filters: Dict,
        context: Dict,
        top_k: int,
    ) -> tuple[List[Place], SearchDebug]:
        """Run the agent graph"""
        
        # Initialize state
        state: AgentState = {
            "query": query or "",
            "lat": lat,
            "lng": lng,
            "radius_m": radius_m,
            "filters": filters,
            "context": context,
            "top_k": top_k,
            "parsed_intent": {},
            "plan": {},
            "google_results": [],
            "yelp_results": [],
            "entity_results": {},
            "fused_results": [],
            "scored_results": [],
            "places": [],
            "debug": {},
            "agent_mode": context.get("agent_mode") or settings.agent_mode,
            "errors": [],
        }
        
        logger.info("agent_start", query=query, lat=lat, lng=lng, radius_m=radius_m)
        
        # Execute graph nodes in sequence
        try:
            # Parse intent
            state = await parse_intent_node(state)
            
            # Plan
            state = await plan_node(state)
            
            # Call providers
            state = await call_providers_node(state, self.search_tool)
            
            # Fuse and dedupe
            state = await fuse_dedupe_node(state)
            
            # Apply constraints (multi-entity)
            state = await constraint_join_node(state)
            
            # Score and rank
            state = await score_rank_node(state)
            
            # Validate
            state = await validate_node(state)
            
            # Format answer
            state = await format_answer_node(state)
            
        except Exception as e:
            logger.error("agent_error", error=str(e))
            state["errors"].append(str(e))
        
        # Build debug info
        debug = SearchDebug(
            timings=self._extract_timings(state["debug"]),
            cache_hit=False,
            agent_trace_id=state["debug"].get("trace_id", ""),
            counts_before_after=self._extract_counts(state["debug"]),
            ranking_preset=state["debug"].get("ranking_preset", settings.ranking_preset),
            constraints_satisfied=self._extract_constraints(state["debug"]),
            agent_mode=state["agent_mode"],
        )
        
        logger.info("agent_complete", places_count=len(state["places"]))
        
        return state["places"], debug
    
    def _extract_timings(self, debug: Dict) -> Dict[str, float]:
        """Extract timing information"""
        timings = {}
        for key, value in debug.items():
            if key.endswith("_ms"):
                timings[key.replace("_ms", "")] = value
        
        # Calculate total
        timings["total"] = sum(timings.values())
        
        return timings
    
    def _extract_counts(self, debug: Dict) -> Dict[str, int]:
        """Extract count information"""
        return {
            "google": debug.get("google_count", 0),
            "yelp": debug.get("yelp_count", 0),
            "fused": debug.get("fused_count", 0),
            "final": len(debug.get("places", [])),
        }
    
    def _extract_constraints(self, debug: Dict) -> Dict:
        """Extract constraint satisfaction info"""
        return {
            "kept": debug.get("constraint_join_kept", 0),
            "dropped": debug.get("constraint_join_dropped", 0),
        }
    
    async def close(self):
        """Close provider connections"""
        # ✅ No longer needed since we're using httpx.AsyncClient context managers
        pass