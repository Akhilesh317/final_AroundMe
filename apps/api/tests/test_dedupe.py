"""Tests for deduplication logic"""
import pytest

from app.fusion.dedupe import (
    are_duplicates,
    cluster_duplicates,
    deduplicate_places,
    normalize_name,
    select_representative,
)
from app.schemas.places import ProviderPlace


class TestDeduplication:
    """Tests for deduplication"""
    
    def test_normalize_name(self):
        """Test name normalization"""
        assert normalize_name("Blue Bottle Coffee, Inc.") == "blue bottle coffee"
        assert normalize_name("Starbucks Coffee") == "starbucks coffee"
        assert normalize_name("Joe's Café!!!") == "joes café"
        assert normalize_name("  Multiple   Spaces  ") == "multiple spaces"
    
    def test_are_duplicates_same_place(self):
        """Test duplicate detection for same place"""
        place1 = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Blue Bottle Coffee",
            lat=37.7749,
            lng=-122.4194,
        )
        
        place2 = ProviderPlace(
            provider="yelp",
            provider_id="2",
            name="Blue Bottle Coffee",
            lat=37.7750,
            lng=-122.4195,
        )
        
        assert are_duplicates(place1, place2) is True
    
    def test_are_duplicates_different_places(self):
        """Test duplicate detection for different places"""
        place1 = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Blue Bottle Coffee",
            lat=37.7749,
            lng=-122.4194,
        )
        
        place2 = ProviderPlace(
            provider="yelp",
            provider_id="2",
            name="Philz Coffee",
            lat=37.7749,
            lng=-122.4194,
        )
        
        assert are_duplicates(place1, place2) is False
    
    def test_are_duplicates_same_name_far_apart(self):
        """Test duplicate detection for same name but far apart"""
        place1 = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Starbucks",
            lat=37.7749,
            lng=-122.4194,
        )
        
        place2 = ProviderPlace(
            provider="yelp",
            provider_id="2",
            name="Starbucks",
            lat=37.8749,
            lng=-122.4194,
        )
        
        assert are_duplicates(place1, place2) is False
    
    def test_cluster_duplicates(self):
        """Test clustering of duplicates"""
        places = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="Blue Bottle Coffee",
                lat=37.7749,
                lng=-122.4194,
            ),
            ProviderPlace(
                provider="yelp",
                provider_id="2",
                name="Blue Bottle Coffee",
                lat=37.7750,
                lng=-122.4195,
            ),
            ProviderPlace(
                provider="google",
                provider_id="3",
                name="Philz Coffee",
                lat=37.7800,
                lng=-122.4200,
            ),
        ]
        
        clusters = cluster_duplicates(places)
        
        assert len(clusters) == 2
        # One cluster should have 2 places (Blue Bottle duplicates)
        cluster_sizes = sorted([len(c) for c in clusters])
        assert cluster_sizes == [1, 2]
    
    def test_select_representative(self):
        """Test representative selection"""
        places = [
            ProviderPlace(
                provider="yelp",
                provider_id="1",
                name="Coffee Shop",
                lat=37.7749,
                lng=-122.4194,
                rating=4.3,
                user_rating_count=50,
            ),
            ProviderPlace(
                provider="google",
                provider_id="2",
                name="Coffee Shop",
                lat=37.7749,
                lng=-122.4194,
                rating=4.5,
                user_rating_count=100,
            ),
        ]
        
        representative = select_representative(places)
        
        # Should select Google place (higher rating count)
        assert representative.provider == "google"
        assert representative.user_rating_count == 100
    
    def test_deduplicate_places(self):
        """Test full deduplication pipeline"""
        places = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="Blue Bottle Coffee",
                lat=37.7749,
                lng=-122.4194,
                rating=4.5,
                user_rating_count=100,
            ),
            ProviderPlace(
                provider="yelp",
                provider_id="2",
                name="Blue Bottle Coffee",
                lat=37.7750,
                lng=-122.4195,
                rating=4.3,
                user_rating_count=80,
            ),
            ProviderPlace(
                provider="google",
                provider_id="3",
                name="Philz Coffee",
                lat=37.7800,
                lng=-122.4200,
                rating=4.6,
                user_rating_count=200,
            ),
        ]
        
        deduplicated, stats = deduplicate_places(places)
        
        assert len(deduplicated) == 2
        assert stats["input_count"] == 3
        assert stats["output_count"] == 2
        assert stats["duplicates_removed"] == 1
        
        # Check that Google Blue Bottle was kept (higher rating count)
        blue_bottle = [p for p in deduplicated if "Blue Bottle" in p.name][0]
        assert blue_bottle.provider == "google"