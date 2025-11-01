"""Google Places API v1 provider"""
import asyncio
from typing import Any, Dict, List, Optional

from app.config import settings
from app.providers.base import BaseProvider
from app.schemas.places import ProviderPlace
from app.utils.field_masks import GOOGLE_PLACES_FIELD_MASK
from app.utils.geo import calculate_distance_km
from app.utils.logging import get_logger

logger = get_logger(__name__)


class GooglePlacesProvider(BaseProvider):
    """Google Places API v1 provider"""
    
    BASE_URL = "https://places.googleapis.com/v1"
    
    @property
    def name(self) -> str:
        return "google"
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        return {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
            "Content-Type": "application/json",
        }
    
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
        if query:
            return await self._search_text(lat, lng, radius_m, query, max_results)
        else:
            return await self._search_nearby_circle(lat, lng, radius_m, category, max_results)
    
    async def _search_nearby_circle(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Search using searchNearby endpoint"""
        url = f"{self.BASE_URL}/places:searchNearby"
        
        payload = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": min(radius_m, 50000),  # Max 50km
                }
            },
            "maxResultCount": min(max_results, 20),  # API limit per request
        }
        
        if category:
            payload["includedTypes"] = [category]
        
        places = []
        page_token = None
        
        while len(places) < max_results:
            if page_token:
                payload["pageToken"] = page_token
                await asyncio.sleep(2)  # Respect rate limits
            
            response = await self._request_with_retry(
                "POST",
                url,
                headers=self._build_headers(),
                json=payload,
            )
            
            data = response.json()
            
            if "places" in data:
                for place_data in data["places"]:
                    place = self._normalize_place(place_data, lat, lng)
                    if place:
                        places.append(place)
            
            page_token = data.get("nextPageToken")
            if not page_token or len(places) >= max_results:
                break
        
        logger.info(
            "google_search_nearby",
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            category=category,
            count=len(places),
        )
        
        return places[:max_results]
    
    async def _search_text(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: str,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Search using searchText endpoint"""
        url = f"{self.BASE_URL}/places:searchText"
        
        payload = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": min(radius_m, 50000),
                }
            },
            "maxResultCount": min(max_results, 20),
        }
        
        places = []
        page_token = None
        
        while len(places) < max_results:
            if page_token:
                payload["pageToken"] = page_token
                await asyncio.sleep(2)
            
            response = await self._request_with_retry(
                "POST",
                url,
                headers=self._build_headers(),
                json=payload,
            )
            
            data = response.json()
            
            if "places" in data:
                for place_data in data["places"]:
                    place = self._normalize_place(place_data, lat, lng)
                    if place:
                        places.append(place)
            
            page_token = data.get("nextPageToken")
            if not page_token or len(places) >= max_results:
                break
        
        logger.info(
            "google_search_text",
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            query=query,
            count=len(places),
        )
        
        return places[:max_results]
    
    def _normalize_place(
        self,
        data: Dict[str, Any],
        origin_lat: float,
        origin_lng: float,
    ) -> Optional[ProviderPlace]:
        """Normalize Google place data to ProviderPlace"""
        try:
            location = data.get("location", {})
            lat = location.get("latitude")
            lng = location.get("longitude")
            
            if lat is None or lng is None:
                return None
            
            # Extract display name
            display_name = data.get("displayName", {})
            name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
            
            if not name:
                return None
            
            # Calculate distance
            distance_km = calculate_distance_km(origin_lat, origin_lng, lat, lng)
            
            # Extract types
            types = data.get("types", [])
            primary_type = data.get("primaryType")
            
            # Map price level (PRICE_LEVEL_UNSPECIFIED=0, FREE=1, INEXPENSIVE=2, MODERATE=3, EXPENSIVE=4, VERY_EXPENSIVE=5)
            price_level_str = data.get("priceLevel", "")
            price_map = {
                "PRICE_LEVEL_FREE": 0,
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4,
            }
            price_level = price_map.get(price_level_str)
            
            return ProviderPlace(
                provider="google",
                provider_id=data.get("id", ""),
                name=name,
                category=primary_type,
                lat=lat,
                lng=lng,
                rating=data.get("rating"),
                user_rating_count=data.get("userRatingCount"),
                price_level=price_level,
                phone=data.get("internationalPhoneNumber"),
                website=data.get("websiteUri"),
                maps_url=data.get("googleMapsUri"),
                address=data.get("formattedAddress"),
                distance_km=distance_km,
                types=types,
                raw=data,
            )
        except Exception as e:
            logger.error("google_normalize_error", error=str(e), data=data)
            return None