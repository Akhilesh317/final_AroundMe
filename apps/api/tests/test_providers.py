"""Tests for provider integrations"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.google import GooglePlacesProvider
from app.providers.yelp import YelpProvider
from app.schemas.places import ProviderPlace


class TestGooglePlacesProvider:
    """Tests for Google Places provider"""
    
    @pytest.fixture
    def google_provider(self):
        """Create Google provider instance"""
        return GooglePlacesProvider(api_key="test_key", timeout=5)
    
    @pytest.mark.asyncio
    async def test_normalize_place(self, google_provider):
        """Test place normalization"""
        raw_data = {
            "id": "ChIJtest123",
            "displayName": {"text": "Blue Bottle Coffee"},
            "location": {"latitude": 37.7749, "longitude": -122.4194},
            "rating": 4.5,
            "userRatingCount": 1250,
            "priceLevel": "PRICE_LEVEL_MODERATE",
            "formattedAddress": "66 Mint St, San Francisco, CA",
            "googleMapsUri": "https://maps.google.com/?cid=123",
            "types": ["cafe", "food"],
        }
        
        place = google_provider._normalize_place(raw_data, 37.7749, -122.4194)
        
        assert place is not None
        assert place.provider == "google"
        assert place.name == "Blue Bottle Coffee"
        assert place.lat == 37.7749
        assert place.lng == -122.4194
        assert place.rating == 4.5
        assert place.price_level == 2
    
    @pytest.mark.asyncio
    async def test_normalize_place_invalid(self, google_provider):
        """Test normalization with invalid data"""
        raw_data = {"id": "test", "displayName": {"text": "Test"}}
        
        place = google_provider._normalize_place(raw_data, 0, 0)
        
        assert place is None


class TestYelpProvider:
    """Tests for Yelp provider"""
    
    @pytest.fixture
    def yelp_provider(self):
        """Create Yelp provider instance"""
        return YelpProvider(api_key="test_key", timeout=5)
    
    def test_map_price_level(self, yelp_provider):
        """Test price level mapping"""
        assert yelp_provider._map_price_level("$") == 1
        assert yelp_provider._map_price_level("$$") == 2
        assert yelp_provider._map_price_level("$$$") == 3
        assert yelp_provider._map_price_level("$$$$") == 4
        assert yelp_provider._map_price_level(None) is None
    
    @pytest.mark.asyncio
    async def test_normalize_place(self, yelp_provider):
        """Test place normalization"""
        raw_data = {
            "id": "yelp_test_123",
            "name": "Philz Coffee",
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
            "rating": 4.5,
            "review_count": 800,
            "price": "$$",
            "location": {
                "address1": "201 Berry St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94158",
            },
            "url": "https://www.yelp.com/biz/philz-coffee",
            "categories": [{"alias": "coffee", "title": "Coffee"}],
        }
        
        place = yelp_provider._normalize_place(raw_data, 37.7749, -122.4194)
        
        assert place is not None
        assert place.provider == "yelp"
        assert place.name == "Philz Coffee"
        assert place.rating == 4.5
        assert place.price_level == 2
        assert place.category == "coffee"