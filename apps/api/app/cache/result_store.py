"""Result set storage for conversational follow-ups"""
import hashlib
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.cache.redis_client import RedisCache
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ResultStore:
    """Store and retrieve result sets for follow-up queries"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    def _make_result_set_key(self, result_set_id: str) -> str:
        """Generate Redis key for result set"""
        return f"result_set:{result_set_id}"
    
    def _make_conversation_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation"""
        return f"conversation:{conversation_id}"
    
    async def store_result_set(
        self,
        places: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
    ) -> str:
        """Store a result set and return its ID"""
        result_set_id = str(uuid4())
        
        data = {
            "result_set_id": result_set_id,
            "places": places,
            "conversation_id": conversation_id,
        }
        
        # Store result set
        key = self._make_result_set_key(result_set_id)
        await self.cache.set(key, data, ttl=settings.conversation_ttl_seconds)
        
        # Link to conversation if provided
        if conversation_id:
            conv_key = self._make_conversation_key(conversation_id)
            await self.cache.set(
                conv_key,
                {"latest_result_set_id": result_set_id},
                ttl=settings.conversation_ttl_seconds,
            )
        
        logger.info(
            "result_set_stored",
            result_set_id=result_set_id,
            conversation_id=conversation_id,
            count=len(places),
        )
        
        return result_set_id
    
    async def get_result_set(self, result_set_id: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve a result set by ID"""
        key = self._make_result_set_key(result_set_id)
        data = await self.cache.get(key)
        
        if data:
            logger.info("result_set_retrieved", result_set_id=result_set_id)
            return data.get("places", [])
        
        logger.warning("result_set_not_found", result_set_id=result_set_id)
        return None
    
    async def get_latest_result_set(
        self, conversation_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get the latest result set for a conversation"""
        conv_key = self._make_conversation_key(conversation_id)
        conv_data = await self.cache.get(conv_key)
        
        if not conv_data:
            return None
        
        result_set_id = conv_data.get("latest_result_set_id")
        if not result_set_id:
            return None
        
        return await self.get_result_set(result_set_id)


def generate_cache_key(
    query: Optional[str],
    lat: float,
    lng: float,
    radius_m: int,
    filters: Optional[Dict[str, Any]] = None,
    ranking_preset: str = "balanced",
    multi_entity: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate cache key for search request"""
    parts = [
        query or "",
        f"{lat:.6f}",
        f"{lng:.6f}",
        str(radius_m),
        ranking_preset,
    ]
    
    if filters:
        parts.append(json.dumps(filters, sort_keys=True))
    
    if multi_entity:
        parts.append(json.dumps(multi_entity, sort_keys=True))
    
    key_string = "|".join(str(p) if p is not None else "" for p in parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    return f"search:{key_hash}"