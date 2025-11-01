"""Tests for agent nodes"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.nodes import (
    AgentState,
    parse_intent_node,
    plan_node,
    fuse_dedupe_node,
    score_rank_node,
)
from app.schemas.places import ProviderPlace


class TestAgentNodes:
    """Tests for agent nodes"""
    
    @pytest.fixture
    def base_state(self) -> AgentState:
        """Create base agent state"""
        return AgentState(
            query="coffee",
            lat=32.814,
            lng=-96.948,
            radius_m=3000,
            filters={},
            context={},
            top_k=10,
            parsed_intent={},
            plan={},
            google_results=[],
            yelp_results=[],
            entity_results={},
            fused_results=[],
            scored_results=[],
            places=[],
            debug={},
            agent_mode="deterministic",
            errors=[],
        )
    
    @pytest.mark.asyncio
    async def test_parse_intent_deterministic(self, base_state):
        """Test intent parsing in deterministic mode"""
        result = await parse_intent_node(base_state)
        
        assert "parsed_intent" in result
        assert result["parsed_intent"]["type"] == "simple"
        assert result["parsed_intent"]["query"] == "coffee"
    
    @pytest.mark.asyncio
    async def test_plan_node_deterministic(self, base_state):
        """Test planning in deterministic mode"""
        base_state["parsed_intent"] = {
            "type": "simple",
            "query": "coffee",
            "category": "cafe",
        }
        
        result = await plan_node(base_state)
        
        assert "plan" in result
        assert "google" in result["plan"]["providers"]
        assert "yelp" in result["plan"]["providers"]
        assert result["plan"]["google_params"]["query"] == "coffee"
    
    @pytest.mark.asyncio
    async def test_fuse_dedupe_node(self, base_state):
        """Test fusion and deduplication"""
        base_state["google_results"] = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="Blue Bottle Coffee",
                lat=32.814,
                lng=-96.948,
                rating=4.5,
                user_rating_count=100,
            ),
        ]
        
        base_state["yelp_results"] = [
            ProviderPlace(
                provider="yelp",
                provider_id="2",
                name="Blue Bottle Coffee",
                lat=32.8141,
                lng=-96.9481,
                rating=4.3,
                user_rating_count=80,
            ),
            ProviderPlace(
                provider="yelp",
                provider_id="3",
                name="Starbucks",
                lat=32.815,
                lng=-96.949,
                rating=4.0,
                user_rating_count=200,
            ),
        ]
        
        result = await fuse_dedupe_node(base_state)
        
        assert "fused_results" in result
        # Should dedupe Blue Bottle (1 + 1 deduped = 1) and keep Starbucks (1) = 2 total
        assert len(result["fused_results"]) == 2
        assert "dedupe_stats" in result["debug"]
    
    @pytest.mark.asyncio
    async def test_score_rank_node(self, base_state):
        """Test scoring and ranking"""
        base_state["fused_results"] = [
            ProviderPlace(
                provider="google",
                provider_id="1",
                name="High Rated",
                lat=32.814,
                lng=-96.948,
                rating=4.8,
                user_rating_count=500,
                distance_km=0.5,
            ),
            ProviderPlace(
                provider="google",
                provider_id="2",
                name="Low Rated",
                lat=32.815,
                lng=-96.949,
                rating=3.5,
                user_rating_count=50,
                distance_km=1.0,
            ),
        ]
        
        result = await score_rank_node(base_state)
        
        assert "scored_results" in result
        assert len(result["scored_results"]) == 2
        
        # First result should be higher rated
        assert result["scored_results"][0][0].name == "High Rated"
        
        # Scores should be descending
        assert result["scored_results"][0][1] > result["scored_results"][1][1]