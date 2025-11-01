"""Deduplication and fusion logic"""
from typing import Dict, List, Tuple

from rapidfuzz import fuzz

from app.config import settings
from app.schemas.places import ProviderPlace
from app.utils.geo import calculate_distance_m
from app.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_name(name: str) -> str:
    """Normalize place name for comparison"""
    name = name.lower()
    
    # Remove common suffixes
    suffixes = [", inc", ", llc", " inc.", " llc.", " ltd.", " corporation", " corp."]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    # Remove punctuation
    for char in ".,!?;:\"'()":
        name = name.replace(char, "")
    
    # Normalize whitespace
    name = " ".join(name.split())
    
    return name.strip()


def are_duplicates(
    place1: ProviderPlace,
    place2: ProviderPlace,
    name_threshold: float = None,
    geo_threshold_m: float = None,
) -> bool:
    """Check if two places are duplicates"""
    name_threshold = name_threshold or settings.name_similarity_threshold * 100
    geo_threshold_m = geo_threshold_m or settings.geo_distance_threshold_m
    
    # Normalize names
    name1 = normalize_name(place1.name)
    name2 = normalize_name(place2.name)
    
    # Calculate name similarity
    name_sim = fuzz.partial_ratio(name1, name2)
    
    # Calculate geographic distance
    geo_dist_m = calculate_distance_m(
        place1.lat, place1.lng,
        place2.lat, place2.lng,
    )
    
    # Both conditions must be met
    is_duplicate = (name_sim >= name_threshold and geo_dist_m <= geo_threshold_m)
    
    if is_duplicate:
        logger.debug(
            "duplicate_found",
            name1=place1.name,
            name2=place2.name,
            name_sim=name_sim,
            geo_dist_m=geo_dist_m,
        )
    
    return is_duplicate


def cluster_duplicates(places: List[ProviderPlace]) -> List[List[ProviderPlace]]:
    """Cluster duplicate places using union-find"""
    n = len(places)
    parent = list(range(n))
    
    def find(i):
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_j] = root_i
    
    # Find all duplicate pairs
    for i in range(n):
        for j in range(i + 1, n):
            if are_duplicates(places[i], places[j]):
                union(i, j)
    
    # Group by cluster
    clusters: Dict[int, List[ProviderPlace]] = {}
    for i in range(n):
        root = find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(places[i])
    
    return list(clusters.values())


def select_representative(cluster: List[ProviderPlace]) -> ProviderPlace:
    """Select the best representative from a cluster"""
    if len(cluster) == 1:
        return cluster[0]
    
    # Sort by:
    # 1. Higher user rating count
    # 2. Higher rating
    # 3. Provider preference (Google > Yelp)
    def sort_key(place: ProviderPlace) -> Tuple:
        return (
            -(place.user_rating_count or 0),
            -(place.rating or 0),
            0 if place.provider == "google" else 1,
        )
    
    sorted_cluster = sorted(cluster, key=sort_key)
    return sorted_cluster[0]


def build_provenance(cluster: List[ProviderPlace], representative: ProviderPlace) -> List[Dict]:
    """Build provenance information for a cluster"""
    provenance = []
    
    for place in cluster:
        name_sim = fuzz.partial_ratio(
            normalize_name(place.name),
            normalize_name(representative.name),
        )
        
        geo_dist_m = calculate_distance_m(
            place.lat, place.lng,
            representative.lat, representative.lng,
        )
        
        provenance.append({
            "provider": place.provider,
            "provider_id": place.provider_id,
            "name": place.name,
            "name_similarity": name_sim / 100.0,
            "geo_distance_m": round(geo_dist_m, 2),
            "rating": place.rating,
            "user_rating_count": place.user_rating_count,
            "price_level": place.price_level,
        })
    
    return provenance


def deduplicate_places(places: List[ProviderPlace]) -> Tuple[List[ProviderPlace], Dict]:
    """Deduplicate a list of places
    
    Returns: (deduplicated_places, stats)
    """
    if not places:
        return [], {"input_count": 0, "output_count": 0, "clusters_found": 0}
    
    clusters = cluster_duplicates(places)
    
    deduplicated = []
    for cluster in clusters:
        representative = select_representative(cluster)
        deduplicated.append(representative)
    
    stats = {
        "input_count": len(places),
        "output_count": len(deduplicated),
        "clusters_found": len(clusters),
        "duplicates_removed": len(places) - len(deduplicated),
    }
    
    logger.info("deduplication_complete", **stats)
    
    return deduplicated, stats