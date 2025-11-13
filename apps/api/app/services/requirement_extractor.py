"""AI-powered requirement extraction from user queries"""
import json
from typing import Dict
import openai
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

REQUIREMENT_EXTRACTION_PROMPT = """You are a search query analyzer for restaurant and venue searches. Extract user requirements.

Identify:
1. **Features** - Physical amenities (wifi, parking, outdoor seating, etc.)
2. **Qualities** - Subjective attributes (authentic, cozy, romantic, etc.)

Return JSON with normalized requirements:
{
  "normalized_requirements": [
    {
      "requirement": "WiFi",
      "category": "feature",
      "keywords": ["wifi", "internet", "wireless"],
      "importance": "high"
    }
  ]
}

Examples:

Query: "coffee shop with wifi"
{
  "normalized_requirements": [
    {"requirement": "WiFi", "category": "feature", "keywords": ["wifi", "wi-fi", "internet", "wireless"], "importance": "high"}
  ]
}

Query: "romantic italian restaurant with outdoor seating"
{
  "normalized_requirements": [
    {"requirement": "Romantic Atmosphere", "category": "quality", "keywords": ["romantic", "intimate", "date"], "importance": "high"},
    {"requirement": "Outdoor Seating", "category": "feature", "keywords": ["outdoor", "patio", "terrace", "outside"], "importance": "high"}
  ]
}

Query: "family friendly restaurant with playground"
{
  "normalized_requirements": [
    {"requirement": "Family Friendly", "category": "feature", "keywords": ["family", "kids", "children", "family friendly"], "importance": "high"},
    {"requirement": "Playground", "category": "feature", "keywords": ["playground", "play area"], "importance": "medium"}
  ]
}

Query: "spicy authentic indian food"
{
  "normalized_requirements": [
    {"requirement": "Spicy Food", "category": "quality", "keywords": ["spicy", "hot", "heat"], "importance": "high"},
    {"requirement": "Authentic Cuisine", "category": "quality", "keywords": ["authentic", "traditional", "genuine"], "importance": "high"}
  ]
}

Query: "place where I can work on my laptop"
{
  "normalized_requirements": [
    {"requirement": "WiFi", "category": "feature", "keywords": ["laptop", "work", "wifi", "internet", "workspace"], "importance": "high"},
    {"requirement": "Quiet Atmosphere", "category": "quality", "keywords": ["work", "quiet", "focus", "study"], "importance": "medium"}
  ]
}

Query: "vegan restaurant with good parking"
{
  "normalized_requirements": [
    {"requirement": "Vegan Options", "category": "feature", "keywords": ["vegan", "plant based", "vegetarian"], "importance": "high"},
    {"requirement": "Parking", "category": "feature", "keywords": ["parking", "valet", "garage"], "importance": "medium"}
  ]
}

Now analyze:"""


async def extract_requirements(query: str) -> Dict:
    """Extract user requirements from search query using AI"""
    
    if not query or len(query.strip()) < 3:
        return {"normalized_requirements": []}
    
    # Skip if query is too generic
    generic_terms = ["restaurant", "food", "cafe", "bar", "place"]
    if query.lower().strip() in generic_terms:
        return {"normalized_requirements": []}
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REQUIREMENT_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Query: {query}"}
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure normalized_requirements exists
        if "normalized_requirements" not in result:
            result["normalized_requirements"] = []
        
        logger.info("requirements_extracted", 
                   query=query,
                   count=len(result["normalized_requirements"]),
                   requirements=[r["requirement"] for r in result["normalized_requirements"]])
        
        return result
        
    except Exception as e:
        logger.error("requirement_extraction_failed", error=str(e), query=query)
        return {"normalized_requirements": []}