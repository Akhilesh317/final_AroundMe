"""Amenities normalization and feature extraction"""
from typing import Dict, List, Set

# Amenity mapping: aliases to normalized feature keys
AMENITY_MAP = {
    # Family features
    "changing_station": ["changing_station", "changing_table", "baby_changing", "diaper_changing"],
    "stroller_parking": ["stroller_parking", "stroller_friendly", "pram_parking"],
    "playground": ["playground", "play_area", "kids_play", "children_playground"],
    "family_friendly": ["family_friendly", "kid_friendly", "kids_welcome", "children_welcome"],
    
    # Cinema features
    "recliners": ["recliners", "recliner_seats", "luxury_seating"],
    "dolby": ["dolby", "dolby_atmos", "dolby_cinema", "dolby_sound"],
    
    # Outdoor features
    "shade": ["shade", "shaded_area", "covered_seating", "umbrella"],
    "outdoor_seating": ["outdoor_seating", "patio", "terrace", "outdoor_dining", "garden_seating"],
    
    # Connectivity
    "wifi": ["wifi", "wireless", "internet", "free_wifi"],
    
    # Accessibility
    "wheelchair_accessible": ["wheelchair_accessible", "accessible", "ada_compliant"],
    
    # Parking
    "parking": ["parking", "parking_lot", "valet_parking", "free_parking"],
    
    # Pet features
    "pet_friendly": ["pet_friendly", "dog_friendly", "pets_allowed"],
    
    # Food features
    "vegetarian": ["vegetarian", "veggie_options", "vegetarian_friendly"],
    "vegan": ["vegan", "vegan_options", "plant_based"],
    "gluten_free": ["gluten_free", "gf_options"],
    
    # Service features
    "takeout": ["takeout", "take_out", "to_go"],
    "delivery": ["delivery", "food_delivery"],
    "reservations": ["reservations", "booking", "table_booking"],
    
    # Atmosphere
    "quiet": ["quiet", "peaceful", "calm", "relaxing"],
    "live_music": ["live_music", "music", "entertainment"],
}

# Build reverse map for quick lookup
ALIAS_TO_FEATURE: Dict[str, str] = {}
for feature, aliases in AMENITY_MAP.items():
    for alias in aliases:
        ALIAS_TO_FEATURE[alias.lower()] = f"feat_{feature}"


def normalize_amenity(text: str) -> str:
    """Normalize amenity text to feature key"""
    text_lower = text.lower().strip()
    return ALIAS_TO_FEATURE.get(text_lower, f"feat_{text_lower.replace(' ', '_')}")


def extract_features_from_text(text: str) -> Dict[str, float]:
    """Extract features from text (reviews, descriptions)"""
    features = {}
    text_lower = text.lower()
    
    for feature, aliases in AMENITY_MAP.items():
        feat_key = f"feat_{feature}"
        score = 0.0
        
        for alias in aliases:
            if alias in text_lower:
                # Simple presence scoring
                count = text_lower.count(alias)
                score = min(1.0, 0.3 + (count * 0.2))
                break
        
        if score > 0:
            features[feat_key] = score
    
    return features


def merge_features(features_list: List[Dict[str, float]]) -> Dict[str, float]:
    """Merge multiple feature dictionaries, taking max values"""
    merged = {}
    
    for features in features_list:
        for key, value in features.items():
            merged[key] = max(merged.get(key, 0.0), value)
    
    return merged


def check_must_haves(features: Dict[str, float], must_haves: List[str]) -> tuple[bool, List[str]]:
    """Check if features satisfy must-have requirements
    
    Returns: (all_satisfied, matched_list)
    """
    matched = []
    
    for must_have in must_haves:
        feat_key = normalize_amenity(must_have)
        if features.get(feat_key, 0.0) >= 0.5:  # Threshold for "has" feature
            matched.append(must_have)
    
    all_satisfied = len(matched) == len(must_haves)
    return all_satisfied, matched


def get_feature_display_name(feat_key: str) -> str:
    """Get human-readable feature name"""
    if feat_key.startswith("feat_"):
        return feat_key[5:].replace("_", " ").title()
    return feat_key