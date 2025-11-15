"""AI-powered requirement extraction from user queries"""
import json
from typing import Dict
import openai
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

REQUIREMENT_EXTRACTION_PROMPT = """You are a search query analyzer for restaurant and venue searches. Extract ONLY explicit user requirements for amenities, features, or qualities.

IMPORTANT RULES:
1. DO NOT extract distance/location terms as requirements (nearby, close, walking distance, etc.)
2. ONLY extract explicit amenities or qualities the user is asking for
3. Distance/proximity should NOT be treated as a requirement - it's handled separately

Extract:
- **Features**: Physical amenities (wifi, parking, outdoor seating, playground, etc.)
- **Qualities**: Subjective attributes (authentic, cozy, romantic, spicy, etc.)

DO NOT EXTRACT:
- Distance/location terms: "nearby", "close", "walking distance", "close by"
- Basic search terms: "restaurant", "cafe", "place"
- Time-based terms: "open now", "24 hours"

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

Query: "family friendly restaurant nearby"
{
  "normalized_requirements": [
    {"requirement": "Family Friendly", "category": "feature", "keywords": ["family", "kids", "children", "family friendly"], "importance": "high"}
  ]
}
NOTE: "nearby" is NOT extracted - it's a distance preference, not a requirement.

Query: "restaurant close by"
{
  "normalized_requirements": []
}
NOTE: "close by" is distance, not a requirement.

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

Query: "restaurant open now"
{
  "normalized_requirements": []
}
NOTE: "open now" is a filter, not a requirement for scoring.

Query: "best pizza nearby with delivery"
{
  "normalized_requirements": [
    {"requirement": "Delivery", "category": "feature", "keywords": ["delivery", "delivers"], "importance": "high"}
  ]
}
NOTE: "nearby" ignored, "best" ignored (handled by ranking), only "delivery" extracted.

Now analyze:"""


async def extract_requirements(query: str) -> Dict:
    """Extract user requirements from search query using AI"""
    
    if not query or len(query.strip()) < 3:
        return {"normalized_requirements": []}
    
    # Skip if query is too generic
    generic_terms = ["restaurant", "food", "cafe", "bar", "place", "nearby", "close by"]
    if query.lower().strip() in generic_terms:
        return {"normalized_requirements": []}
    
    # Skip if query only contains distance/location terms
    distance_only_patterns = [
        "restaurant nearby",
        "restaurant close by",
        "restaurant near me",
        "places nearby",
        "food near me",
        "restaurants around here",
    ]
    query_normalized = query.lower().strip()
    if query_normalized in distance_only_patterns:
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
        
        # ✅ Filter out any distance-related requirements that slipped through
        distance_keywords = ["nearby", "close", "walking", "distance", "proximity", "near"]
        filtered_requirements = []
        
        for req in result["normalized_requirements"]:
            req_name_lower = req.get("requirement", "").lower()
            
            # Skip if requirement name contains distance keywords
            if any(keyword in req_name_lower for keyword in distance_keywords):
                logger.info("filtered_distance_requirement", requirement=req.get("requirement"))
                continue
            
            filtered_requirements.append(req)
        
        result["normalized_requirements"] = filtered_requirements
        
        logger.info("requirements_extracted", 
                   query=query,
                   count=len(result["normalized_requirements"]),
                   requirements=[r["requirement"] for r in result["normalized_requirements"]])
        
        return result
        
    except Exception as e:
        logger.error("requirement_extraction_failed", error=str(e), query=query)
        return {"normalized_requirements": []}