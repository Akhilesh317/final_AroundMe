"""Base provider class"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.utils.errors import ProviderError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BaseProvider(ABC):
    """Base class for place providers"""
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self.client
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry"""
        client = await self._get_client()
        
        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "provider_retry",
                        provider=self.name,
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        status=e.response.status_code,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ProviderError(
                    provider=self.name,
                    message=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                    status_code=502,
                )
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "provider_retry",
                        provider=self.name,
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ProviderError(
                    provider=self.name,
                    message=f"Request failed: {str(e)}",
                    status_code=502,
                )
        
        raise ProviderError(
            provider=self.name,
            message="Max retries exceeded",
            status_code=502,
        )
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @abstractmethod
    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 60,
    ) -> List[Any]:
        """Search places nearby"""
        pass