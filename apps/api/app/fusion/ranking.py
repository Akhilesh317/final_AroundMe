"""Ranking and scoring logic"""
import math
from typing import Dict, List, Optional

from app.config import settings
from app.schemas.places import Place, ProviderPlace
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


def calculate_base_score(
    place: ProviderPlace,
    preset: str = "balanced",
    max_distance_km: float = 10.0,
) -> tuple[float, Dict[str, float]]:
    """Calculate base score for a place
    
    Returns: (score, evidence_dict)
    """
    weights = RankingPreset.get(preset)
    evidence = {}
    
    # Rating component (0-5 scale)
    rating = place.rating or 0
    rating_score = (rating / 5.0) * weights["rating"]
    evidence["rating"] = round(rating_score, 4)
    
    # Reviews component (logarithmic scale)
    reviews = place.user_rating_count or 0
    if reviews > 0:
        reviews_score = min(1.0, math.log1p(reviews) / 8.0) * weights["reviews"]
    else:
        reviews_score = 0.0
    evidence["reviews"] = round(reviews_score, 4)
    
    # Distance component (inverse, closer is better)
    distance_km = place.distance_km or 0
    if distance_km <= max_distance_km:
        distance_score = (1.0 - min(distance_km, max_distance_km) / max_distance_km) * weights["distance"]
    else:
        distance_score = 0.0
    evidence["distance"] = round(distance_score, 4)
    
    # Total base score
    base_score = rating_score + reviews_score + distance_score
    
    return base_score, evidence


def apply_filter_bonuses(
    base_score: float,
    evidence: Dict[str, float],
    place: ProviderPlace,
    filters: Optional[Dict] = None,
) -> tuple[float, Dict[str, float]]:
    """Apply bonuses/penalties based on filters"""
    if not filters:
        return base_score, evidence
    
    score = base_score
    
    # Open now bonus
    if filters.get("open_now"):
        # We don't have real-time hours in the schema, but this is where it would go
        # For now, assume neutral (0.0)
        evidence["open_now"] = 0.0
    
    # Price fit bonus/penalty
    price_range = filters.get("price")
    if price_range and place.price_level is not None:
        min_price, max_price = price_range
        if min_price <= place.price_level <= max_price:
            price_bonus = 0.05
        elif abs(place.price_level - min_price) <= 1 or abs(place.price_level - max_price) <= 1:
            price_bonus = 0.02
        else:
            price_bonus = -0.03
        
        score += price_bonus
        evidence["price_fit"] = round(price_bonus, 4)
    
    return score, evidence


def apply_personalization(
    score: float,
    evidence: Dict[str, float],
    place: ProviderPlace,
    preferences: Optional[List[Dict]] = None,
) -> tuple[float, Dict[str, float]]:
    """Apply personalization boosts"""
    if not preferences:
        return score, evidence
    
    total_boost = 0.0
    
    for pref in preferences:
        key = pref.get("key", "")
        value = pref.get("value", "")
        weight = pref.get("weight", 0.5)
        
        # Category match
        if key == "category" and place.category == value:
            boost = 0.05 * weight
            total_boost += boost
        
        # Type match
        elif key == "type" and place.types and value in place.types:
            boost = 0.04 * weight
            total_boost += boost
        
        # Feature match (would check place.features if populated)
        elif key.startswith("feat_"):
            # This would check features extracted from reviews
            pass
    
    # Cap personalization boost
    total_boost = min(total_boost, settings.max_personalization_boost)
    
    if total_boost > 0:
        score += total_boost
        evidence["preferences"] = round(total_boost, 4)
    
    return score, evidence


def rank_places(
    places: List[ProviderPlace],
    preset: str = "balanced",
    filters: Optional[Dict] = None,
    preferences: Optional[List[Dict]] = None,
) -> List[tuple[ProviderPlace, float, Dict[str, float]]]:
    """Rank places and return sorted list with scores and evidence
    
    Returns: List of (place, score, evidence) tuples
    """
    scored_places = []
    
    for place in places:
        # Calculate base score
        score, evidence = calculate_base_score(place, preset)
        
        # Apply filter bonuses
        score, evidence = apply_filter_bonuses(score, evidence, place, filters)
        
        # Apply personalization
        score, evidence = apply_personalization(score, evidence, place, preferences)
        
        scored_places.append((place, score, evidence))
    
    # Sort by score descending
    scored_places.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(
        "ranking_complete",
        preset=preset,
        count=len(scored_places),
        top_score=scored_places[0][1] if scored_places else 0,
    )
    
    return scored_places