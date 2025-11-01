"""Agent tools"""
from typing import Any, Dict, List

from app.providers.google import GooglePlacesProvider
from app.providers.yelp import YelpProvider
from app.schemas.places import ProviderPlace
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SearchTool:
    """Tool for searching places"""
    
    def __init__(self, google_provider: GooglePlacesProvider, yelp_provider: YelpProvider):
        self.google = google_provider
        self.yelp = yelp_provider
    
    async def call_google(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: str = None,
        category: str = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Call Google Places API"""
        try:
            return await self.google.search_nearby(
                lat=lat,
                lng=lng,
                radius_m=radius_m,
                query=query,
                category=category,
                max_results=max_results,
            )
        except Exception as e:
            logger.error("google_search_error", error=str(e))
            return []
    
    async def call_yelp(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: str = None,
        category: str = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Call Yelp API"""
        try:
            return await self.yelp.search_nearby(
                lat=lat,
                lng=lng,
                radius_m=radius_m,
                query=query,
                category=category,
                max_results=max_results,
            )
        except Exception as e:
            logger.error("yelp_search_error", error=str(e))
            return []