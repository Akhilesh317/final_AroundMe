"""Tests for API endpoints"""
import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


class TestSearchEndpoint:
    """Tests for search endpoint"""
    
    @pytest.mark.asyncio
    async def test_search_simple_query(self, client: AsyncClient, sample_search_request):
        """Test simple search query"""
        with patch("app.routes.search.SearchService") as mock_service:
            # Mock service response
            mock_instance = AsyncMock()
            mock_instance.search.return_value = {
                "places": [],
                "debug": {
                    "timings": {"total": 1.0},
                    "cache_hit": False,
                    "agent_trace_id": "test-123",
                    "counts_before_after": {},
                    "ranking_preset": "balanced",
                    "constraints_satisfied": {},
                    "agent_mode": "full",
                },
                "result_set_id": "result-123",
            }
            mock_service.return_value = mock_instance
            
            response = await client.post("/api/search", json=sample_search_request)
            
            assert response.status_code == 200
            data = response.json()
            assert "places" in data
            assert "debug" in data
            assert "result_set_id" in data
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, client: AsyncClient):
        """Test search with filters"""
        request = {
            "query": "coffee",
            "lat": 32.814,
            "lng": -96.948,
            "radius_m": 3000,
            "filters": {
                "price": [1, 3],
                "open_now": True,
            },
            "top_k": 10,
        }
        
        with patch("app.routes.search.SearchService") as mock_service:
            mock_instance = AsyncMock()
            mock_instance.search.return_value = {
                "places": [],
                "debug": {
                    "timings": {"total": 1.0},
                    "cache_hit": False,
                    "agent_trace_id": "test-123",
                    "counts_before_after": {},
                    "ranking_preset": "balanced",
                    "constraints_satisfied": {},
                    "agent_mode": "full",
                },
                "result_set_id": "result-123",
            }
            mock_service.return_value = mock_instance
            
            response = await client.post("/api/search", json=request)
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_search_invalid_coordinates(self, client: AsyncClient):
        """Test search with invalid coordinates"""
        request = {
            "query": "coffee",
            "lat": 91.0,  # Invalid latitude
            "lng": -96.948,
            "radius_m": 3000,
        }
        
        response = await client.post("/api/search", json=request)
        
        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Tests for health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data


class TestProfileEndpoints:
    """Tests for profile endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_preferences_empty(self, client: AsyncClient):
        """Test getting preferences for new user"""
        response = await client.get("/api/profile/preferences?user_id=test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        assert len(data["preferences"]) == 0
    
    @pytest.mark.asyncio
    async def test_update_preferences(self, client: AsyncClient):
        """Test updating preferences"""
        request = {
            "preferences": [
                {
                    "key": "category",
                    "value": "italian",
                    "weight": 0.8,
                }
            ]
        }
        
        response = await client.put(
            "/api/profile/preferences?user_id=test_user",
            json=request,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        assert len(data["preferences"]) == 1
        assert data["preferences"][0]["key"] == "category"
    
    @pytest.mark.asyncio
    async def test_delete_preferences(self, client: AsyncClient):
        """Test deleting preferences"""
        # First create some preferences
        request = {
            "preferences": [
                {"key": "category", "value": "italian", "weight": 0.8}
            ]
        }
        await client.put("/api/profile/preferences?user_id=test_user", json=request)
        
        # Then delete them
        response = await client.delete("/api/profile/preferences?user_id=test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert data["deleted"] >= 0