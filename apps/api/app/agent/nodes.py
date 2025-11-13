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
from app.fusion.ranking import rank_places_async, rank_places
from app.schemas.places import MatchedPartner, Place, ProviderPlace, RequirementMatch
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
    entity_results: Dict[int, List[ProviderPlace]]
    fused_results: List[ProviderPlace]
    scored_results: List[tuple[ProviderPlace, float, Dict, Dict]]
    
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
        parsed = {
            "type": "simple",
            "query": state["query"],
            "category": None,
        }
    else:
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
    state["debug"]["parse_intent_ms"] = 50
    
    return state


async def plan_node(state: AgentState) -> AgentState:
    """Plan which providers to call"""
    logger.info("node_plan", intent=state["parsed_intent"])
    
    intent = state["parsed_intent"]
    
    if state["agent_mode"] == "deterministic":
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
    state["debug"]["provider_calls_ms"] = 800
    
    return state


async def fuse_dedupe_node(state: AgentState) -> AgentState:
    """Fuse and deduplicate results"""
    logger.info("node_fuse_dedupe")
    
    all_places = state["google_results"] + state["yelp_results"]
    
    if not all_places:
        state["fused_results"] = []
        return state
    
    deduplicated, stats = deduplicate_places(all_places)
    
    state["fused_results"] = deduplicated
    state["debug"]["dedupe_stats"] = stats
    state["debug"]["fused_count"] = len(deduplicated)
    state["debug"]["dedupe_ms"] = 100
    
    return state


async def constraint_join_node(state: AgentState) -> AgentState:
    """Apply multi-entity constraints"""
    logger.info("node_constraint_join")
    
    intent = state["parsed_intent"]
    
    if intent.get("type") != "multi_entity":
        return state
    
    entities = intent.get("entities", [])
    relations = intent.get("relations", [])
    
    if len(entities) <= 1 or not relations:
        return state
    
    anchor_entity = entities[0]
    partner_entities = entities[1:]
    
    filtered_anchors = []
    for place in state["fused_results"]:
        features = extract_features_from_text(place.name)
        
        if anchor_entity.get("must_haves"):
            satisfied, matched = check_must_haves(features, anchor_entity["must_haves"])
            if not satisfied:
                continue
        
        filtered_anchors.append(place)
    
    results_with_partners = []
    
    for anchor in filtered_anchors:
        partners_found = []
        
        for relation in relations:
            if relation["left"] != 0:
                continue
            
            partner_idx = relation["right"]
            if partner_idx >= len(partner_entities):
                continue
            
            partner_entity = partner_entities[partner_idx - 1]
            max_distance_m = relation.get("distance_m", settings.default_near_distance_m)
            
            for potential_partner in state["fused_results"]:
                if potential_partner == anchor:
                    continue
                
                dist_m = calculate_distance_m(
                    anchor.lat, anchor.lng,
                    potential_partner.lat, potential_partner.lng,
                )
                
                if dist_m > max_distance_m:
                    continue
                
                partner_features = extract_features_from_text(potential_partner.name)
                if partner_entity.get("must_haves"):
                    satisfied, matched = check_must_haves(
                        partner_features,
                        partner_entity["must_haves"],
                    )
                    if not satisfied:
                        continue
                    
                    partners_found.append({
                        "kind": partner_entity["kind"],
                        "name": potential_partner.name,
                        "distance_m": dist_m,
                        "matched_must_haves": matched,
                        "lat": potential_partner.lat,
                        "lng": potential_partner.lng,
                    })
        
        if len(partners_found) >= len(relations):
            results_with_partners.append((anchor, partners_found))
    
    if results_with_partners:
        state["fused_results"] = [anchor for anchor, _ in results_with_partners]
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
    """Score and rank places with 4-method feature matching"""
    logger.info("node_score_rank")
    
    if not state["fused_results"]:
        logger.warning("no_fused_results")
        state["scored_results"] = []
        return state
    
    # Get ranking preset
    preset = state["context"].get("ranking_preset") or settings.ranking_preset
    
    # Get filters
    filters = state.get("filters", {})
    
    # ✅ Extract requirements using AI
    query = state.get("query", "")
    requirements = None
    
    if query and len(query.strip()) > 0:
        try:
            from app.services.requirement_extractor import extract_requirements
            requirements = await extract_requirements(query)
            
            req_count = len(requirements.get("normalized_requirements", []))
            if req_count > 0:
                logger.info("ai_requirements_extracted",
                           query=query,
                           count=req_count,
                           requirements=[r["requirement"] for r in requirements.get("normalized_requirements", [])])
        except Exception as e:
            logger.error("requirement_extraction_failed", error=str(e))
            requirements = None
    
    # ✅ Use async ranking with all 4 methods
    try:
        scored = await rank_places_async(
            state["fused_results"],
            preset=preset,
            filters=filters,
            preferences=None,
            requirements=requirements,
            use_semantic_matching=True,  # ✅ Enable semantic matching
        )
        logger.info("async_ranking_success", methods="1,2,3,4")
    except Exception as e:
        logger.error("async_ranking_failed", error=str(e))
        # Fallback to sync ranking (Methods 1 & 2 only)
        scored = rank_places(
            state["fused_results"],
            preset=preset,
            filters=filters,
            requirements=requirements,
        )
        logger.info("sync_ranking_fallback", methods="1,2")
    
    state["scored_results"] = scored
    state["debug"]["ranking_preset"] = preset
    state["debug"]["requirements"] = requirements
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
    """Format final answer with enhanced requirement matching"""
    logger.info("node_format_answer")
    
    places = []
    matched_partners_map = state["debug"].get("matched_partners", {})
    
    for i, result_tuple in enumerate(state.get("scored_results", [])[:state["top_k"]]):
        # Unpack tuple (4 elements)
        provider_place = result_tuple[0]
        score = result_tuple[1]
        evidence = result_tuple[2]
        requirements_info = result_tuple[3] if len(result_tuple) > 3 else {}
        
        # Build provenance
        cluster = [provider_place]
        provenance = build_provenance(cluster, provider_place)
        
        # Extract features
        features = extract_features_from_text(provider_place.name)
        
        # Get matched partners
        matched_partners = []
        if i in matched_partners_map:
            for partner_data in matched_partners_map[i]:
                matched_partners.append(MatchedPartner(**partner_data))
        
        # ✅ Convert requirement matches to RequirementMatch objects
        requirement_matches = []
        if requirements_info.get("requirements_matched"):
            for match_data in requirements_info["requirements_matched"]:
                requirement_matches.append(RequirementMatch(
                    requirement=match_data["requirement"],
                    matched=match_data["matched"],
                    score_bonus=match_data["score_bonus"],
                    evidence=match_data.get("evidence")
                ))
        
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
            max_possible_score=requirements_info.get("max_possible_score", 100.0),
            evidence=evidence,
            user_requirements=requirements_info.get("user_requirements", []),
            requirements_matched=requirement_matches,
            match_percentage=requirements_info.get("match_percentage", 100.0),
            provenance=provenance,
            matched_partners=matched_partners,
        )
        
        places.append(place)
    
    state["places"] = places
    state["debug"]["format_answer_ms"] = 20
    
    return state