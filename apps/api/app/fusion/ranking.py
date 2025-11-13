"""Ranking and scoring logic with 4-method feature matching"""
import math
import asyncio
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.schemas.places import ProviderPlace
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RankingPreset:
    """Ranking weight presets"""
    
    BALANCED = {
        "rating": 0.55,
        "reviews": 0.30,
        "distance": 0.15,
    }
    
    NEARBY = {
        "rating": 0.35,
        "reviews": 0.20,
        "distance": 0.45,
    }
    
    REVIEW_HEAVY = {
        "rating": 0.45,
        "reviews": 0.50,
        "distance": 0.05,
    }
    
    @classmethod
    def get(cls, preset: str) -> Dict[str, float]:
        """Get preset weights"""
        presets = {
            "balanced": cls.BALANCED,
            "nearby": cls.NEARBY,
            "review-heavy": cls.REVIEW_HEAVY,
        }
        return presets.get(preset, cls.BALANCED)


def check_structured_amenities(
    place: ProviderPlace,
    requirement: str,
    keywords: List[str]
) -> Optional[str]:
    """
    METHOD 1: Check Google's structured amenity fields
    
    Returns: Matched field name if found, None otherwise
    """
    
    raw_data = place.raw if hasattr(place, 'raw') else {}
    
    # Map requirements to Google fields
    amenity_mapping = {
        "wifi": ["wifi", "internet", "wireless"],
        "outdoor seating": ["outdoor_seating"],
        "outdoor": ["outdoor_seating"],
        "patio": ["outdoor_seating"],
        "parking": ["parking_options"],
        "family friendly": ["good_for_children"],
        "family": ["good_for_children"],
        "kids": ["good_for_children"],
        "pet friendly": ["allows_dogs"],
        "dog": ["allows_dogs"],
        "pet": ["allows_dogs"],
        "wheelchair": ["wheelchair_accessible"],
        "accessible": ["wheelchair_accessible"],
        "delivery": ["delivery"],
        "takeout": ["takeout"],
        "pickup": ["takeout"],
        "reservations": ["reservable"],
        "reservation": ["reservable"],
        "booking": ["reservable"],
        "vegetarian": ["serves_vegetarian_food"],
        "breakfast": ["serves_breakfast"],
        "brunch": ["serves_brunch"],
        "lunch": ["serves_lunch"],
        "dinner": ["serves_dinner"],
        "beer": ["serves_beer"],
        "wine": ["serves_wine"],
        "groups": ["good_for_groups"],
    }
    
    # Check if requirement matches any field
    req_lower = requirement.lower()
    
    # First try exact matches
    for keyword in keywords:
        kw_lower = keyword.lower()
        if kw_lower in amenity_mapping:
            for field_name in amenity_mapping[kw_lower]:
                # Check if field exists and is True
                if raw_data.get(field_name) is True:
                    logger.debug("structured_match", requirement=requirement, field=field_name)
                    return field_name
                
                # Check nested objects (e.g., parking_options)
                if isinstance(raw_data.get(field_name), dict):
                    nested = raw_data[field_name]
                    if any(v is True for v in nested.values()):
                        logger.debug("structured_match_nested", requirement=requirement, field=field_name)
                        return field_name
    
    # Try partial matches
    for key_term, field_names in amenity_mapping.items():
        if key_term in req_lower:
            for field_name in field_names:
                if raw_data.get(field_name) is True:
                    return field_name
                if isinstance(raw_data.get(field_name), dict):
                    nested = raw_data[field_name]
                    if any(v is True for v in nested.values()):
                        return field_name
    
    return None


def build_comprehensive_place_text(place: ProviderPlace) -> str:
    """
    METHOD 2: Build comprehensive searchable text from all place data
    """
    
    text_parts = [place.name]
    
    if place.category:
        text_parts.append(place.category)
    
    if place.address:
        text_parts.append(place.address)
    
    # Add types
    if hasattr(place, 'types') and place.types:
        text_parts.extend(place.types)
    
    # Add raw data fields
    if hasattr(place, 'raw') and isinstance(place.raw, dict):
        raw = place.raw
        
        # Editorial summary
        if raw.get("editorial_summary"):
            text_parts.append(str(raw["editorial_summary"]))
        
        # All boolean amenities that are True
        amenity_fields = [
            "outdoor_seating", "good_for_children", "good_for_groups",
            "allows_dogs", "reservable", "serves_beer", "serves_breakfast",
            "serves_brunch", "serves_dinner", "serves_lunch",
            "serves_vegetarian_food", "serves_wine", "takeout",
            "delivery", "dine_in", "wheelchair_accessible"
        ]
        
        for field in amenity_fields:
            if raw.get(field) is True:
                # Convert field name to readable text
                readable = field.replace("_", " ").replace("serves ", "").replace("allows ", "")
                text_parts.append(readable)
    
    return " ".join(text_parts).lower()


def check_keyword_match(
    place: ProviderPlace,
    keywords: List[str]
) -> Optional[str]:
    """
    METHOD 2: Check keyword matching in comprehensive place text
    
    Returns: Matched keyword if found, None otherwise
    """
    
    place_text = build_comprehensive_place_text(place)
    
    for keyword in keywords:
        if keyword.lower() in place_text:
            logger.debug("keyword_match", keyword=keyword, place=place.name)
            return keyword
    
    return None


async def check_semantic_match(
    requirement: str,
    place: ProviderPlace,
    threshold: float = 0.75
) -> Optional[Tuple[float, str]]:
    """
    METHOD 3: Check semantic match using AI embeddings
    
    Returns: (confidence_score, matched_text) if matched, None otherwise
    """
    
    try:
        from app.services.semantic_matcher import semantic_match
        
        # Build place texts for semantic matching
        place_texts = []
        
        if place.name:
            place_texts.append(place.name)
        
        if place.category:
            place_texts.append(place.category)
        
        if hasattr(place, 'raw') and place.raw.get("editorial_summary"):
            place_texts.append(place.raw["editorial_summary"])
        
        if hasattr(place, 'address') and place.address:
            place_texts.append(place.address)
        
        # Check semantic similarity
        matches = await semantic_match(requirement, place_texts, threshold)
        
        if matches:
            # Return highest similarity score and matched text
            idx, score, text = matches[0]
            logger.debug("semantic_match", requirement=requirement, score=score, text=text[:50])
            return (score, text[:100])
        
        return None
        
    except Exception as e:
        logger.warning("semantic_match_failed", error=str(e))
        return None


async def check_review_mentions(
    requirement: str,
    place: ProviderPlace,
    keywords: List[str]
) -> Optional[str]:
    """
    METHOD 4: Check if requirement is mentioned in reviews/descriptions
    
    Returns: Evidence string if found, None otherwise
    """
    
    # For now, check editorial summary which often includes review highlights
    if not hasattr(place, 'raw'):
        return None
    
    raw = place.raw
    editorial = raw.get("editorial_summary", "").lower()
    
    if not editorial:
        return None
    
    # Check if any keyword appears in editorial summary
    for keyword in keywords:
        if keyword.lower() in editorial:
            # Extract context around the keyword
            idx = editorial.find(keyword.lower())
            start = max(0, idx - 30)
            end = min(len(editorial), idx + len(keyword) + 30)
            context = editorial[start:end].strip()
            
            logger.debug("review_mention", requirement=requirement, keyword=keyword, context=context)
            return f"Review mentions: '{context}'"
    
    return None


async def rank_places_async(
    places: List[ProviderPlace],
    preset: str = "balanced",
    filters: Optional[Dict] = None,
    preferences: Optional[List[Dict]] = None,
    requirements: Optional[Dict] = None,
    use_semantic_matching: bool = True,
) -> List[Tuple[ProviderPlace, float, Dict[str, float], Dict]]:
    """
    Rank places with 4-method feature matching:
    1. Structured data (Google amenity fields) - 100% confidence
    2. Keyword matching (in text) - 80% confidence
    3. Semantic matching (AI embeddings) - 75%+ confidence
    4. Review mentions (in descriptions) - 70% confidence
    """
    
    if not places:
        return []
    
    # Get normalized requirements
    normalized_requirements = []
    if requirements and "normalized_requirements" in requirements:
        normalized_requirements = requirements["normalized_requirements"]
    
    has_requirements = len(normalized_requirements) > 0
    
    # Base weights
    base_weights = RankingPreset.get(preset)
    
    # Calculate max possible score
    base_score_max = 100.0
    
    if has_requirements:
        # Each requirement worth 10 points
        bonus_points_max = len(normalized_requirements) * 10
        max_possible_score = base_score_max + bonus_points_max
    else:
        max_possible_score = base_score_max
    
    # Convert weights to points (out of 100 base)
    if preset == "balanced":
        points = {"rating": 55.0, "reviews": 30.0, "distance": 15.0}
    elif preset == "nearby":
        points = {"rating": 35.0, "reviews": 20.0, "distance": 45.0}
    elif preset == "review-heavy":
        points = {"rating": 45.0, "reviews": 50.0, "distance": 5.0}
    else:
        points = {"rating": 55.0, "reviews": 30.0, "distance": 15.0}
    
    scored = []
    
    for place in places:
        score = 0.0
        evidence = {}
        requirement_matches = []
        
        # 1. Rating component
        if place.rating:
            rating_score = (place.rating / 5.0) * points["rating"]
            score += rating_score
            evidence["rating"] = round(rating_score, 2)
        
        # 2. Review count component (logarithmic)
        if place.user_rating_count:
            review_score = min(1.0, math.log1p(place.user_rating_count) / 8.0) * points["reviews"]
            score += review_score
            evidence["reviews"] = round(review_score, 2)
        
        # 3. Distance component
        if place.distance_km is not None:
            max_distance_km = 10.0
            if place.distance_km <= max_distance_km:
                distance_score = (1.0 - min(place.distance_km, max_distance_km) / max_distance_km) * points["distance"]
            else:
                distance_score = 0.0
            score += distance_score
            evidence["distance"] = round(distance_score, 2)
        
        # 4. Price fit bonus
        if filters and "price" in filters:
            price_range = filters["price"]
            if place.price_level is not None:
                min_price, max_price = price_range
                if min_price <= place.price_level <= max_price:
                    price_bonus = 5.0
                else:
                    price_bonus = 0.0
                score += price_bonus
                evidence["price_fit"] = round(price_bonus, 2)
        
        # ✅ 5. ENHANCED: 4-Method Requirement Matching
        for req in normalized_requirements:
            requirement_name = req.get("requirement", "Unknown")
            keywords = req.get("keywords", [])
            category = req.get("category", "feature")
            
            matched = False
            matched_keyword = None
            match_method = None
            confidence = 0.0
            evidence_text = None
            
            # METHOD 1: Check structured data (Google amenity fields) - BEST
            structured_field = check_structured_amenities(place, requirement_name, keywords)
            if structured_field:
                matched = True
                match_method = "structured_data"
                matched_keyword = structured_field
                confidence = 1.0
                evidence_text = f"✓ Verified by Google: {structured_field.replace('_', ' ')}"
            
            # METHOD 2: Keyword matching in text - GOOD
            if not matched:
                matched_kw = check_keyword_match(place, keywords)
                if matched_kw:
                    matched = True
                    match_method = "keyword"
                    matched_keyword = matched_kw
                    confidence = 0.8
                    evidence_text = f"Found keyword: '{matched_kw}'"
            
            # METHOD 3: Semantic matching (AI embeddings) - SMART
            if not matched and use_semantic_matching:
                semantic_result = await check_semantic_match(
                    requirement_name,
                    place,
                    threshold=0.75
                )
                if semantic_result:
                    semantic_score, semantic_text = semantic_result
                    matched = True
                    match_method = "semantic"
                    confidence = semantic_score
                    evidence_text = f"AI match ({int(semantic_score * 100)}%): {semantic_text[:50]}..."
            
            # METHOD 4: Review mentions - CONTEXTUAL
            if not matched:
                review_mention = await check_review_mentions(requirement_name, place, keywords)
                if review_mention:
                    matched = True
                    match_method = "review"
                    confidence = 0.7
                    evidence_text = review_mention
            
            # Award points based on confidence
            bonus = 10.0 * confidence if matched else 0.0
            
            requirement_matches.append({
                "requirement": requirement_name,
                "matched": matched,
                "score_bonus": round(bonus, 2),
                "evidence": evidence_text,
                "type": category,
                "confidence": round(confidence, 2),
                "method": match_method
            })
            
            if matched:
                score += bonus
                evidence[f"req_{requirement_name.lower().replace(' ', '_')}"] = round(bonus, 2)
        
        # Calculate match percentage
        if len(normalized_requirements) > 0:
            matched_count = sum(1 for m in requirement_matches if m["matched"])
            match_percentage = (matched_count / len(normalized_requirements)) * 100
        else:
            match_percentage = 100.0
        
        # Store requirements info
        all_requirement_names = [req.get("requirement", "") for req in normalized_requirements]
        
        requirements_info = {
            "user_requirements": all_requirement_names,
            "requirements_matched": requirement_matches,
            "match_percentage": round(match_percentage, 1),
            "max_possible_score": max_possible_score,
        }
        
        scored.append((place, score, evidence, requirements_info))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(
        "ranking_complete",
        preset=preset,
        count=len(scored),
        top_score=round(scored[0][1], 2) if scored else 0,
        requirements_count=len(normalized_requirements)
    )
    
    return scored


# Synchronous wrapper for backward compatibility
def rank_places(
    places: List[ProviderPlace],
    preset: str = "balanced",
    filters: Optional[Dict] = None,
    preferences: Optional[List[Dict]] = None,
    requirements: Optional[Dict] = None,
) -> List[Tuple[ProviderPlace, float, Dict[str, float], Dict]]:
    """
    Synchronous wrapper for rank_places_async
    Uses only Methods 1 and 2 (no semantic/async methods)
    """
    
    if not places:
        return []
    
    # Get normalized requirements
    normalized_requirements = []
    if requirements and "normalized_requirements" in requirements:
        normalized_requirements = requirements["normalized_requirements"]
    
    has_requirements = len(normalized_requirements) > 0
    
    # Base weights
    base_weights = RankingPreset.get(preset)
    
    # Calculate max possible score
    base_score_max = 100.0
    
    if has_requirements:
        bonus_points_max = len(normalized_requirements) * 10
        max_possible_score = base_score_max + bonus_points_max
    else:
        max_possible_score = base_score_max
    
    # Convert weights to points
    if preset == "balanced":
        points = {"rating": 55.0, "reviews": 30.0, "distance": 15.0}
    elif preset == "nearby":
        points = {"rating": 35.0, "reviews": 20.0, "distance": 45.0}
    elif preset == "review-heavy":
        points = {"rating": 45.0, "reviews": 50.0, "distance": 5.0}
    else:
        points = {"rating": 55.0, "reviews": 30.0, "distance": 15.0}
    
    scored = []
    
    for place in places:
        score = 0.0
        evidence = {}
        requirement_matches = []
        
        # Base scoring (rating, reviews, distance)
        if place.rating:
            rating_score = (place.rating / 5.0) * points["rating"]
            score += rating_score
            evidence["rating"] = round(rating_score, 2)
        
        if place.user_rating_count:
            review_score = min(1.0, math.log1p(place.user_rating_count) / 8.0) * points["reviews"]
            score += review_score
            evidence["reviews"] = round(review_score, 2)
        
        if place.distance_km is not None:
            max_distance_km = 10.0
            if place.distance_km <= max_distance_km:
                distance_score = (1.0 - min(place.distance_km, max_distance_km) / max_distance_km) * points["distance"]
            else:
                distance_score = 0.0
            score += distance_score
            evidence["distance"] = round(distance_score, 2)
        
        # Price fit
        if filters and "price" in filters:
            price_range = filters["price"]
            if place.price_level is not None:
                min_price, max_price = price_range
                if min_price <= place.price_level <= max_price:
                    price_bonus = 5.0
                else:
                    price_bonus = 0.0
                score += price_bonus
                evidence["price_fit"] = round(price_bonus, 2)
        
        # Requirement matching (Methods 1 & 2 only - sync)
        for req in normalized_requirements:
            requirement_name = req.get("requirement", "Unknown")
            keywords = req.get("keywords", [])
            category = req.get("category", "feature")
            
            matched = False
            match_method = None
            confidence = 0.0
            evidence_text = None
            
            # METHOD 1: Structured data
            structured_field = check_structured_amenities(place, requirement_name, keywords)
            if structured_field:
                matched = True
                match_method = "structured_data"
                confidence = 1.0
                evidence_text = f"✓ Verified: {structured_field.replace('_', ' ')}"
            
            # METHOD 2: Keyword matching
            if not matched:
                matched_kw = check_keyword_match(place, keywords)
                if matched_kw:
                    matched = True
                    match_method = "keyword"
                    confidence = 0.8
                    evidence_text = f"Found: '{matched_kw}'"
            
            # Award points
            bonus = 10.0 * confidence if matched else 0.0
            
            requirement_matches.append({
                "requirement": requirement_name,
                "matched": matched,
                "score_bonus": round(bonus, 2),
                "evidence": evidence_text,
                "type": category,
                "confidence": round(confidence, 2),
                "method": match_method
            })
            
            if matched:
                score += bonus
                evidence[f"req_{requirement_name.lower().replace(' ', '_')}"] = round(bonus, 2)
        
        # Calculate match percentage
        if len(normalized_requirements) > 0:
            matched_count = sum(1 for m in requirement_matches if m["matched"])
            match_percentage = (matched_count / len(normalized_requirements)) * 100
        else:
            match_percentage = 100.0
        
        requirements_info = {
            "user_requirements": [req.get("requirement", "") for req in normalized_requirements],
            "requirements_matched": requirement_matches,
            "match_percentage": round(match_percentage, 1),
            "max_possible_score": max_possible_score,
        }
        
        scored.append((place, score, evidence, requirements_info))
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored