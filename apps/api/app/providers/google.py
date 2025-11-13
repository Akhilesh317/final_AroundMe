"""Google Places API v1 provider"""
import asyncio
from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.schemas.places import ProviderPlace
from app.utils.geo import calculate_distance_m
from app.utils.logging import get_logger

logger = get_logger(__name__)

GOOGLE_PLACES_BASE = "https://places.googleapis.com/v1"


async def search_google_places(
    lat: float,
    lng: float,
    radius_m: int = 3000,
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_results: int = 20,
) -> List[ProviderPlace]:
    """Search Google Places API v1"""
    
    if not settings.google_places_api_key:
        logger.error("google_api_key_missing")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            # Determine search type
            if query:
                # Text search
                response = await _text_search(client, lat, lng, query, radius_m, max_results)
            else:
                # Nearby search
                response = await _nearby_search(client, lat, lng, category, radius_m, max_results)
            
            places = []
            for place_data in response.get("places", []):
                try:
                    converted = _convert_place(place_data, lat, lng)
                    places.append(converted)
                except Exception as e:
                    logger.warning("place_conversion_failed", error=str(e))
                    continue
            
            logger.info("google_search_complete", count=len(places), query=query)
            return places
            
    except Exception as e:
        logger.error("google_search_failed", error=str(e))
        return []


async def _text_search(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    query: str,
    radius_m: int,
    max_results: int,
) -> Dict:
    """Text search endpoint"""
    
    url = f"{GOOGLE_PLACES_BASE}/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.google_places_api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.userRatingCount,"
            "places.priceLevel,places.primaryType,places.types,"
            "places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,"
            "places.editorialSummary,"
            "places.goodForChildren,places.goodForGroups,"
            "places.outdoorSeating,places.reservable,"
            "places.allowsDogs,places.servesBeer,places.servesBreakfast,"
            "places.servesBrunch,places.servesDinner,places.servesLunch,"
            "places.servesVegetarianFood,places.servesWine,"
            "places.takeout,places.delivery,places.dineIn,"
            "places.accessibilityOptions,places.parkingOptions,"
            "places.paymentOptions,places.currentOpeningHours"
        ),
    }
    
    body = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
        "maxResultCount": max_results,
    }
    
    response = await client.post(url, json=body, headers=headers, timeout=10.0)
    response.raise_for_status()
    
    return response.json()


async def _nearby_search(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    category: Optional[str],
    radius_m: int,
    max_results: int,
) -> Dict:
    """Nearby search endpoint"""
    
    url = f"{GOOGLE_PLACES_BASE}/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.google_places_api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.userRatingCount,"
            "places.priceLevel,places.primaryType,places.types,"
            "places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,"
            "places.editorialSummary,"
            "places.goodForChildren,places.goodForGroups,"
            "places.outdoorSeating,places.reservable,"
            "places.allowsDogs,places.servesBeer,places.servesBreakfast,"
            "places.servesBrunch,places.servesDinner,places.servesLunch,"
            "places.servesVegetarianFood,places.servesWine,"
            "places.takeout,places.delivery,places.dineIn,"
            "places.accessibilityOptions,places.parkingOptions,"
            "places.paymentOptions,places.currentOpeningHours"
        ),
    }
    
    body = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
        "maxResultCount": max_results,
    }
    
    if category:
        body["includedTypes"] = [category]
    
    response = await client.post(url, json=body, headers=headers, timeout=10.0)
    response.raise_for_status()
    
    return response.json()


def _convert_place(place_data: Dict, user_lat: float, user_lng: float) -> ProviderPlace:
    """Convert Google Place to ProviderPlace with enhanced amenity data"""
    
    # Basic fields
    place_id = place_data.get("id", "")
    name = place_data.get("displayName", {}).get("text", "Unknown")
    
    # Location
    location = place_data.get("location", {})
    lat = location.get("latitude", 0.0)
    lng = location.get("longitude", 0.0)
    
    # Calculate distance
    distance_m = calculate_distance_m(user_lat, user_lng, lat, lng)
    distance_km = distance_m / 1000.0
    
    # Rating
    rating = place_data.get("rating")
    user_rating_count = place_data.get("userRatingCount")
    
    # Price level (convert string to int)
    price_level_str = place_data.get("priceLevel", "")
    price_level = None
    if price_level_str:
        price_map = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }
        price_level = price_map.get(price_level_str)
    
    # Category
    primary_type = place_data.get("primaryType", "")
    category = primary_type.replace("_", " ").title() if primary_type else None
    
    # Contact info
    phone = place_data.get("nationalPhoneNumber")
    website = place_data.get("websiteUri")
    maps_url = place_data.get("googleMapsUri")
    formatted_address = place_data.get("formattedAddress", "")
    
    # ✅ ENHANCED: Extract all amenity data
    enhanced_raw = {
        **place_data,
        
        # Editorial summary (descriptions)
        "editorial_summary": place_data.get("editorialSummary", {}).get("text", ""),
        
        # Types (categories)
        "types": place_data.get("types", []),
        
        # ✅ CRITICAL: Boolean amenities from Google
        "outdoor_seating": place_data.get("outdoorSeating", False),
        "good_for_children": place_data.get("goodForChildren", False),
        "good_for_groups": place_data.get("goodForGroups", False),
        "allows_dogs": place_data.get("allowsDogs", False),
        "reservable": place_data.get("reservable", False),
        
        # Food/drink service
        "serves_beer": place_data.get("servesBeer", False),
        "serves_breakfast": place_data.get("servesBreakfast", False),
        "serves_brunch": place_data.get("servesBrunch", False),
        "serves_dinner": place_data.get("servesDinner", False),
        "serves_lunch": place_data.get("servesLunch", False),
        "serves_vegetarian_food": place_data.get("servesVegetarianFood", False),
        "serves_wine": place_data.get("servesWine", False),
        
        # Service options
        "takeout": place_data.get("takeout", False),
        "delivery": place_data.get("delivery", False),
        "dine_in": place_data.get("dineIn", False),
        
        # Accessibility
        "wheelchair_accessible": place_data.get("accessibilityOptions", {}).get("wheelchairAccessibleEntrance", False),
        
        # Parking
        "parking_options": place_data.get("parkingOptions", {}),
        
        # Payment
        "payment_options": place_data.get("paymentOptions", {}),
        
        # Hours
        "opening_hours": place_data.get("currentOpeningHours", {}),
    }
    
    return ProviderPlace(
        provider="google",
        provider_id=place_id,
        name=name,
        category=category,
        lat=lat,
        lng=lng,
        rating=rating,
        user_rating_count=user_rating_count,
        price_level=price_level,
        phone=phone,
        website=website,
        maps_url=maps_url,
        address=formatted_address,
        distance_km=distance_km,
        types=place_data.get("types", []),
        raw=enhanced_raw,
    )