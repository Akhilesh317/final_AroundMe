"""LLM adapter for swappable models"""
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class LLMAdapter:
    """Adapter for LLM interactions"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        self._client: Optional[BaseChatModel] = None
    
    def get_client(self) -> BaseChatModel:
        """Get or create LLM client"""
        if self._client is None:
            if settings.openai_api_key:
                self._client = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    api_key=settings.openai_api_key,
                )
                logger.info("llm_client_created", model=self.model_name)
            else:
                raise ValueError("OpenAI API key not configured")
        
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM with messages"""
        try:
            client = self.get_client()
            response = await client.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error("llm_invoke_error", error=str(e))
            raise
    
    async def invoke_with_schema(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Invoke LLM with structured output schema"""
        try:
            client = self.get_client()
            
            # Add schema to system message
            schema_prompt = f"\nRespond with valid JSON matching this schema:\n{schema}"
            messages[0]["content"] += schema_prompt
            
            response = await client.ainvoke(messages)
            
            # Parse JSON response
            import json
            content = response.content
            
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except Exception as e:
            logger.error("llm_structured_invoke_error", error=str(e))
            raise


# Global adapter instance
llm_adapter = LLMAdapter()