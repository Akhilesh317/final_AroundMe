"""Yelp Fusion API provider"""
from typing import Any, Dict, List, Optional

from app.providers.base import BaseProvider
from app.schemas.places import ProviderPlace
from app.utils.geo import calculate_distance_km
from app.utils.logging import get_logger

logger = get_logger(__name__)


class YelpProvider(BaseProvider):
    """Yelp Fusion API provider"""
    
    BASE_URL = "https://api.yelp.com/v3"
    
    @property
    def name(self) -> str:
        return "yelp"
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
    
    def _map_price_level(self, price_str: Optional[str]) -> Optional[int]:
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
    
    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Search places nearby"""
        url = f"{self.BASE_URL}/businesses/search"
        
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
            
            response = await self._request_with_retry(
                "GET",
                url,
                headers=self._build_headers(),
                params=params,
            )
            
            data = response.json()
            businesses = data.get("businesses", [])
            
            if not businesses:
                break
            
            for business in businesses:
                place = self._normalize_place(business, lat, lng)
                if place:
                    places.append(place)
            
            offset += len(businesses)
            
            # Check if we've reached the end
            if len(businesses) < limit:
                break
        
        logger.info(
            "yelp_search_nearby",
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            query=query,
            category=category,
            count=len(places),
        )
        
        return places[:max_results]
    
    def _normalize_place(
        self,
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
            distance_km = calculate_distance_km(origin_lat, origin_lng, lat, lng)
            
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
            price_level = self._map_price_level(data.get("price"))
            
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