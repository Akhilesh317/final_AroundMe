"""Yelp Fusion API provider"""
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.schemas.places import ProviderPlace
from app.utils.geo import calculate_distance_m
from app.utils.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://api.yelp.com/v3"


async def search_yelp_places(
    lat: float,
    lng: float,
    radius_m: int = 3000,
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_results: int = 20,
) -> List[ProviderPlace]:
    """Search Yelp Fusion API"""
    
    if not settings.yelp_api_key:
        logger.error("yelp_api_key_missing")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            places = []
            offset = 0
            limit = 50  # Yelp max per request
            
            while len(places) < max_results:
                params = {
                    "latitude": lat,
                    "longitude": lng,
                    "radius": min(radius_m, 40000),  # Yelp max 40km
                    "limit": min(limit, max_results - len(places)),
                    "offset": offset,
                    "sort_by": "best_match",
                }
                
                if query:
                    params["term"] = query
                
                if category:
                    params["categories"] = category
                
                headers = {
                    "Authorization": f"Bearer {settings.yelp_api_key}",
                    "Accept": "application/json",
                }
                
                response = await client.get(
                    f"{BASE_URL}/businesses/search",
                    headers=headers,
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()
                
                data = response.json()
                businesses = data.get("businesses", [])
                
                if not businesses:
                    break
                
                for business in businesses:
                    place = _normalize_place(business, lat, lng)
                    if place:
                        places.append(place)
                
                offset += len(businesses)
                
                # Check if we've reached the end
                if len(businesses) < limit:
                    break
            
            logger.info("yelp_search_complete", count=len(places), query=query)
            return places[:max_results]
            
    except Exception as e:
        logger.error("yelp_search_failed", error=str(e))
        return []


def _map_price_level(price_str: Optional[str]) -> Optional[int]:
    """Map Yelp price string to numeric level"""
    if not price_str:
        return None
    
    price_map = {
        "$": 1,
        "$$": 2,
        "$$$": 3,
        "$$$$": 4,
    }
    return price_map.get(price_str)


def _normalize_place(
    data: Dict[str, Any],
    origin_lat: float,
    origin_lng: float,
) -> Optional[ProviderPlace]:
    """Normalize Yelp business data to ProviderPlace"""
    try:
        coordinates = data.get("coordinates", {})
        lat = coordinates.get("latitude")
        lng = coordinates.get("longitude")
        
        if lat is None or lng is None:
            return None
        
        name = data.get("name", "")
        if not name:
            return None
        
        # Calculate distance
        distance_m = calculate_distance_m(origin_lat, origin_lng, lat, lng)
        distance_km = distance_m / 1000.0
        
        # Extract category
        categories = data.get("categories", [])
        category = categories[0].get("alias") if categories else None
        
        # Build address
        location = data.get("location", {})
        address_parts = [
            location.get("address1", ""),
            location.get("city", ""),
            location.get("state", ""),
            location.get("zip_code", ""),
        ]
        address = ", ".join(filter(None, address_parts))
        
        # Map price level
        price_level = _map_price_level(data.get("price"))
        
        # Use Yelp URL as both website and maps_url
        url = data.get("url")
        
        return ProviderPlace(
            provider="yelp",
            provider_id=data.get("id", ""),
            name=name,
            category=category,
            lat=lat,
            lng=lng,
            rating=data.get("rating"),
            user_rating_count=data.get("review_count"),
            price_level=price_level,
            phone=data.get("phone"),
            website=url,
            maps_url=url,
            address=address if address else None,
            distance_km=distance_km,
            types=[cat.get("alias") for cat in categories],
            raw=data,
        )
    except Exception as e:
        logger.error("yelp_normalize_error", error=str(e), data=data)
        return None


# ✅ Keep the class for backward compatibility
class YelpProvider:
    """Yelp Fusion API provider - Legacy class wrapper"""
    
    BASE_URL = BASE_URL
    
    def __init__(self):
        self.api_key = settings.yelp_api_key
    
    @property
    def name(self) -> str:
        return "yelp"
    
    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Search places nearby - wrapper for function"""
        return await search_yelp_places(
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            query=query,
            category=category,
            max_results=max_results,
        )