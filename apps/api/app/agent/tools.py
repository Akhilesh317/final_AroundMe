"""Agent tools for calling external providers"""
from typing import List, Optional

from app.config import settings
from app.providers.google import search_google_places
from app.providers.yelp import search_yelp_places
from app.schemas.places import ProviderPlace
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SearchTool:
    """Tool for searching places using external providers"""
    
    def __init__(self):
        """Initialize search tool"""
        logger.info("search_tool_initialized")
    
    async def call_google(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Call Google Places API"""
        try:
            logger.info("calling_google", query=query, category=category, radius_m=radius_m)
            
            results = await search_google_places(
                lat=lat,
                lng=lng,
                radius_m=radius_m,
                query=query,
                category=category,
                max_results=max_results,
            )
            
            logger.info("google_results", count=len(results))
            return results
            
        except Exception as e:
            logger.error("google_search_error", error=str(e))
            return []
    
    async def call_yelp(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[ProviderPlace]:
        """Call Yelp Fusion API"""
        try:
            logger.info("calling_yelp", query=query, category=category, radius_m=radius_m)
            
            results = await search_yelp_places(
                lat=lat,
                lng=lng,
                radius_m=radius_m,
                query=query,
                category=category,
                max_results=max_results,
            )
            
            logger.info("yelp_results", count=len(results))
            return results
            
        except Exception as e:
            logger.error("yelp_search_error", error=str(e))
            return []
