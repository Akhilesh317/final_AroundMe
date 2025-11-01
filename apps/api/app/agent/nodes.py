"""LangGraph agent nodes"""
import asyncio
import json
from typing import Any, Dict, List, TypedDict

from app.agent.llm_adapter import llm_adapter
from app.agent.prompts import (
    PARSE_INTENT_EXAMPLES,
    PARSE_INTENT_SYSTEM,
    PLAN_SYSTEM,
    VALIDATE_SYSTEM,
)
from app.agent.tools import SearchTool
from app.config import settings
from app.fusion.amenities import check_must_haves, extract_features_from_text, merge_features
from app.fusion.dedupe import build_provenance, cluster_duplicates, deduplicate_places, select_representative
from app.fusion.ranking import rank_places
from app.schemas.places import MatchedPartner, Place, ProviderPlace
from app.utils.geo import calculate_distance_m
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State passed between agent nodes"""
    
    # Input
    query: str
    lat: float
    lng: float
    radius_m: int
    filters: Dict[str, Any]
    context: Dict[str, Any]
    top_k: int
    
    # Intermediate
    parsed_intent: Dict[str, Any]
    plan: Dict[str, Any]
    google_results: List[ProviderPlace]
    yelp_results: List[ProviderPlace]
    entity_results: Dict[int, List[ProviderPlace]]  # For multi-entity
    fused_results: List[ProviderPlace]
    scored_results: List[tuple[ProviderPlace, float, Dict]]
    
    # Output
    places: List[Place]
    debug: Dict[str, Any]
    
    # Control
    agent_mode: str
    errors: List[str]


async def parse_intent_node(state: AgentState) -> AgentState:
    """Parse user query into structured intent"""
    logger.info("node_parse_intent", query=state["query"])
    
    if state["agent_mode"] == "deterministic":
        # Simple deterministic parsing
        parsed = {
            "type": "simple",
            "query": state["query"],
            "category": None,
        }
    else:
        # LLM-based parsing
        messages = [
            {"role": "system", "content": PARSE_INTENT_SYSTEM},
            {"role": "user", "content": PARSE_INTENT_EXAMPLES},
            {"role": "user", "content": f"Query: {state['query']}"},
        ]
        
        try:
            response = await llm_adapter.invoke(messages)
            parsed = json.loads(response)
        except Exception as e:
            logger.error("parse_intent_error", error=str(e))
            parsed = {
                "type": "simple",
                "query": state["query"],
                "category": None,
            }
    
    state["parsed_intent"] = parsed
    state["debug"]["parse_intent_ms"] = 50  # Placeholder timing
    
    return state


async def plan_node(state: AgentState) -> AgentState:
    """Plan which providers to call"""
    logger.info("node_plan", intent=state["parsed_intent"])
    
    intent = state["parsed_intent"]
    
    if state["agent_mode"] == "deterministic":
        # Simple deterministic planning
        plan = {
            "providers": ["google", "yelp"],
            "google_params": {
                "use_text_search": bool(intent.get("query")),
                "query": intent.get("query"),
                "category": intent.get("category"),
            },
            "yelp_params": {
                "query": intent.get("query"),
                "category": intent.get("category"),
            },
            "reasoning": "Deterministic mode: calling both providers",
        }
    else:
        # LLM-based planning
        messages = [
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": f"Intent: {json.dumps(intent)}"},
        ]
        
        try:
            response = await llm_adapter.invoke(messages)
            plan = json.loads(response)
        except Exception as e:
            logger.error("plan_error", error=str(e))
            plan = {
                "providers": ["google", "yelp"],
                "google_params": {"query": state["query"]},
                "yelp_params": {"query": state["query"]},
                "reasoning": "Fallback plan due to error",
            }
    
    state["plan"] = plan
    state["debug"]["plan_ms"] = 30
    
    return state


async def call_providers_node(state: AgentState, search_tool: SearchTool) -> AgentState:
    """Call external providers"""
    logger.info("node_call_providers", plan=state["plan"])
    
    plan = state["plan"]
    tasks = []
    
    if "google" in plan.get("providers", []):
        google_params = plan.get("google_params", {})
        tasks.append(
            search_tool.call_google(
                lat=state["lat"],
                lng=state["lng"],
                radius_m=state["radius_m"],
                query=google_params.get("query"),
                category=google_params.get("category"),
                max_results=settings.max_results_per_provider,
            )
        )
    
    if "yelp" in plan.get("providers", []):
        yelp_params = plan.get("yelp_params", {})
        tasks.append(
            search_tool.call_yelp(
                lat=state["lat"],
                lng=state["lng"],
                radius_m=state["radius_m"],
                query=yelp_params.get("query"),
                category=yelp_params.get("category"),
                max_results=settings.max_results_per_provider,
            )
        )
    
    results = await asyncio.gather(*tasks)
    
    state["google_results"] = results[0] if len(results) > 0 else []
    state["yelp_results"] = results[1] if len(results) > 1 else []
    
    state["debug"]["google_count"] = len(state["google_results"])
    state["debug"]["yelp_count"] = len(state["yelp_results"])
    state["debug"]["provider_calls_ms"] = 800  # Placeholder
    
    return state


async def fuse_dedupe_node(state: AgentState) -> AgentState:
    """Fuse and deduplicate results"""
    logger.info("node_fuse_dedupe")
    
    # Combine all results
    all_places = state["google_results"] + state["yelp_results"]
    
    if not all_places:
        state["fused_results"] = []
        return state
    
    # Deduplicate
    deduplicated, stats = deduplicate_places(all_places)
    
    state["fused_results"] = deduplicated
    state["debug"]["dedupe_stats"] = stats
    state["debug"]["fused_count"] = len(deduplicated)
    state["debug"]["dedupe_ms"] = 100  # Placeholder
    
    return state


async def constraint_join_node(state: AgentState) -> AgentState:
    """Apply multi-entity constraints"""
    logger.info("node_constraint_join")
    
    intent = state["parsed_intent"]
    
    # Check if multi-entity
    if intent.get("type") != "multi_entity":
        # Single entity - pass through
        return state
    
    entities = intent.get("entities", [])
    relations = intent.get("relations", [])
    
    if len(entities) <= 1 or not relations:
        return state
    
    # For this simplified implementation, we'll filter the fused results by must_haves
    # and simulate finding nearby partners
    
    anchor_entity = entities[0]
    partner_entities = entities[1:]
    
    # Filter anchors by must_haves
    filtered_anchors = []
    for place in state["fused_results"]:
        # Extract features (simplified - would use reviews/descriptions in production)
        features = extract_features_from_text(place.name)
        
        # Check must_haves
        if anchor_entity.get("must_haves"):
            satisfied, matched = check_must_haves(features, anchor_entity["must_haves"])
            if not satisfied:
                continue
        
        filtered_anchors.append(place)
    
    # For each anchor, simulate finding matching partners
    # In a real implementation, this would involve separate searches
    results_with_partners = []
    
    for anchor in filtered_anchors:
        # Simulate finding partners by checking other places in fused results
        partners_found = []
        
        for relation in relations:
            if relation["left"] != 0:
                continue  # Only handle anchor as left
            
            partner_idx = relation["right"]
            if partner_idx >= len(partner_entities):
                continue
            
            partner_entity = partner_entities[partner_idx - 1]
            max_distance_m = relation.get("distance_m", settings.default_near_distance_m)
            
            # Check if any fused results match partner criteria
            for potential_partner in state["fused_results"]:
                if potential_partner == anchor:
                    continue
                
                # Check distance
                dist_m = calculate_distance_m(
                    anchor.lat, anchor.lng,
                    potential_partner.lat, potential_partner.lng,
                )
                
                if dist_m > max_distance_m:
                    continue
                
                # Check must_haves
                partner_features = extract_features_from_text(potential_partner.name)
                if partner_entity.get("must_haves"):
                    satisfied, matched = check_must_haves(
                        partner_features,
                        partner_entity["must_haves"],
                    )
                    if not satisfied:
                        continue
                    
                    # Add as matched partner
                    partners_found.append({
                        "kind": partner_entity["kind"],
                        "name": potential_partner.name,
                        "distance_m": dist_m,
                        "matched_must_haves": matched,
                        "lat": potential_partner.lat,
                        "lng": potential_partner.lng,
                    })
        
        # Only include anchors that have all required partners
        if len(partners_found) >= len(relations):
            results_with_partners.append((anchor, partners_found))
    
    # Update state with filtered results
    if results_with_partners:
        state["fused_results"] = [anchor for anchor, _ in results_with_partners]
        # Store partner info for later
        state["debug"]["matched_partners"] = {
            i: partners for i, (_, partners) in enumerate(results_with_partners)
        }
        state["debug"]["constraint_join_kept"] = len(results_with_partners)
        state["debug"]["constraint_join_dropped"] = len(filtered_anchors) - len(results_with_partners)
    else:
        state["fused_results"] = []
        state["debug"]["constraint_join_kept"] = 0
        state["debug"]["constraint_join_dropped"] = len(filtered_anchors)
    
    state["debug"]["constraint_join_ms"] = 50
    
    return state


async def score_rank_node(state: AgentState) -> AgentState:
    """Score and rank places"""
    logger.info("node_score_rank")
    
    if not state["fused_results"]:
        state["scored_results"] = []
        return state
    
    # Get ranking preset
    preset = state["context"].get("ranking_preset") or settings.ranking_preset
    
    # Get filters for bonuses
    filters = state.get("filters", {})
    
    # Get preferences (would come from DB in full implementation)
    preferences = None
    
    # Rank places
    scored = rank_places(
        state["fused_results"],
        preset=preset,
        filters=filters,
        preferences=preferences,
    )
    
    state["scored_results"] = scored
    state["debug"]["ranking_preset"] = preset
    state["debug"]["score_rank_ms"] = 50
    
    return state


async def validate_node(state: AgentState) -> AgentState:
    """Validate results and suggest fallbacks if needed"""
    logger.info("node_validate")
    
    result_count = len(state.get("scored_results", []))
    
    validation = {
        "valid": result_count > 0,
        "issues": [],
        "suggestions": [],
        "expand_search": False,
    }
    
    if result_count == 0:
        validation["issues"].append("No results found")
        validation["suggestions"].append("Try broadening your search criteria")
        validation["expand_search"] = True
    elif result_count < 5:
        validation["issues"].append("Few results found")
        validation["suggestions"].append("Consider increasing search radius")
    
    state["debug"]["validation"] = validation
    state["debug"]["validate_ms"] = 10
    
    return state


async def format_answer_node(state: AgentState) -> AgentState:
    """Format final answer"""
    logger.info("node_format_answer")
    
    places = []
    
    # Get matched partners if any
    matched_partners_map = state["debug"].get("matched_partners", {})
    
    for i, (provider_place, score, evidence) in enumerate(state.get("scored_results", [])[:state["top_k"]]):
        # Build provenance
        cluster = [provider_place]
        provenance = build_provenance(cluster, provider_place)
        
        # Extract features
        features = extract_features_from_text(provider_place.name)
        
        # Get matched partners if any
        matched_partners = []
        if i in matched_partners_map:
            for partner_data in matched_partners_map[i]:
                matched_partners.append(MatchedPartner(**partner_data))
        
        # Create Place
        place = Place(
            name=provider_place.name,
            category=provider_place.category,
            lat=provider_place.lat,
            lng=provider_place.lng,
            rating=provider_place.rating,
            user_rating_count=provider_place.user_rating_count,
            price_level=provider_place.price_level,
            phone=provider_place.phone,
            website=provider_place.website,
            maps_url=provider_place.maps_url,
            address=provider_place.address,
            distance_km=provider_place.distance_km,
            features=features,
            score=score,
            evidence=evidence,
            provenance=provenance,
            matched_partners=matched_partners,
        )
        
        places.append(place)
    
    state["places"] = places
    state["debug"]["format_answer_ms"] = 20
    
    return state