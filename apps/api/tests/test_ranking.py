"""Tests for ranking logic"""
import pytest

from app.fusion.ranking import (
    RankingPreset,
    calculate_base_score,
    apply_filter_bonuses,
    apply_personalization,
    rank_places,
)
from app.schemas.places import ProviderPlace


class TestRanking:
    """Tests for ranking"""
    
    def test_ranking_presets(self):
        """Test ranking preset weights"""
        balanced = RankingPreset.get("balanced")
        assert balanced["rating"] == 0.55
        assert balanced["reviews"] == 0.30
        assert balanced["distance"] == 0.15
        
        nearby = RankingPreset.get("nearby")
        assert nearby["distance"] == 0.45
        
        review_heavy = RankingPreset.get("review-heavy")
        assert review_heavy["reviews"] == 0.50
    
    def test_calculate_base_score(self):
        """Test base score calculation"""
        place = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Test Place",
            lat=37.7749,
            lng=-122.4194,
            rating=4.5,
            user_rating_count=100,
            distance_km=1.0,
        )
        
        score, evidence = calculate_base_score(place, preset="balanced")
        
        assert score > 0
        assert "rating" in evidence
        assert "reviews" in evidence
        assert "distance" in evidence
        assert evidence["rating"] > 0
        assert evidence["reviews"] > 0
        assert evidence["distance"] > 0
    
    def test_calculate_base_score_no_reviews(self):
        """Test base score with no reviews"""
        place = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Test Place",
            lat=37.7749,
            lng=-122.4194,
            rating=4.0,
            user_rating_count=0,
            distance_km=1.0,
        )
        
        score, evidence = calculate_base_score(place, preset="balanced")
        
        assert score > 0
        assert evidence["reviews"] == 0.0
    
    def test_apply_filter_bonuses_price_match(self):
        """Test price filter bonus"""
        place = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Test Place",
            lat=37.7749,
            lng=-122.4194,
            price_level=2,
        )
        
        score, evidence = apply_filter_bonuses(
            0.5,
            {},
            place,
            filters={"price": [1, 3]},
        )
        
        assert score > 0.5
        assert "price_fit" in evidence
        assert evidence["price_fit"] > 0
    
    def test_apply_filter_bonuses_price_mismatch(self):
        """Test price filter penalty"""
        place = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Test Place",
            lat=37.7749,
            lng=-122.4194,
            price_level=4,
        )
        
        score, evidence = apply_filter_bonuses(
            0.5,
            {},
            place,
            filters={"price": [1, 2]},
        )
        
        assert score < 0.5
        assert evidence["price_fit"] < 0
    
    def test_apply_personalization(self):
        """Test personalization boost"""
        place = ProviderPlace(
            provider="google",
            provider_id="1",
            name="Test Place",
            lat=37.7749,
            lng=-122.4194,
            category="cafe",
        )
        
        preferences = [
            {"key": "category", "value": "cafe", "weight": 0.8}
        ]
        
        score, evidence = apply_personalization(0.5, {}, place, preferences)
        
        assert score > 0.5
        assert "preferences" in evidence
        assert evidence["preferences"] > 0
    
    def test_rank_places(self):
        """Test full ranking pipeline"""
        places = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="High Rated Close",
                lat=37.7749,
                lng=-122.4194,
                rating=4.8,
                user_rating_count=500,
                distance_km=0.5,
            ),
            ProviderPlace(
                provider="google",
                provider_id="2",
                name="Medium Rated Far",
                lat=37.7749,
                lng=-122.4194,
                rating=4.0,
                user_rating_count=100,
                distance_km=5.0,
            ),
            ProviderPlace(
                provider="google",
                provider_id="3",
                name="Low Rated Close",
                lat=37.7749,
                lng=-122.4194,
                rating=3.5,
                user_rating_count=50,
                distance_km=0.8,
            ),
        ]
        
        ranked = rank_places(places, preset="balanced")
        
        assert len(ranked) == 3
        
        # First place should be highest rated and closest
        assert ranked[0][0].name == "High Rated Close"
        
        # Scores should be descending
        assert ranked[0][1] >= ranked[1][1] >= ranked[2][1]
    
    def test_rank_places_nearby_preset(self):
        """Test ranking with nearby preset"""
        places = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="Far High Rated",
                lat=37.7749,
                lng=-122.4194,
                rating=4.8,
                user_rating_count=500,
                distance_km=8.0,
            ),
            ProviderPlace(
                provider="google",
                provider_id="2",
                name="Close Low Rated",
                lat=37.7749,
                lng=-122.4194,
                rating=3.8,
                user_rating_count=100,
                distance_km=0.3,
            ),
        ]
        
        ranked = rank_places(places, preset="nearby")
        
        # With nearby preset, closer place should rank higher despite lower rating
        # (distance weight is 0.45 vs 0.15 in balanced)
        assert ranked[0][0].name == "Close Low Rated"