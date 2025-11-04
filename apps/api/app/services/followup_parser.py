"""Follow-up query parser using OpenAI"""
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


class FollowUpIntent(BaseModel):
    """Parsed follow-up intent"""
    
    is_new_search: bool = Field(default=False, description="True if completely new search")
    new_query: Optional[str] = Field(default=None, description="If new search, what to search for")
    
    # Refinement filters (if refining existing results)
    adjust_radius: Optional[int] = Field(default=None, description="New radius in meters, None = keep same")
    price_min: Optional[int] = Field(default=None, description="1-4, None = no filter")
    price_max: Optional[int] = Field(default=None, description="1-4, None = no filter")
    open_now: Optional[bool] = Field(default=None, description="True/False, None = no filter")
    required_features: List[str] = Field(default_factory=list, description="e.g., ['wifi', 'outdoor_seating']")
    min_rating: Optional[float] = Field(default=None, description="Minimum rating, None = no filter")
    sort_by: Optional[str] = Field(default=None, description="'distance', 'rating', 'price', None = keep current")


async def parse_followup(
    followup_text: str,
    original_query: str,
    current_radius: int
) -> FollowUpIntent:
    """
    Use OpenAI to parse a follow-up query into structured filters
    
    Args:
        followup_text: The user's follow-up message
        original_query: The original search query
        current_radius: Current search radius in meters
    
    Returns:
        FollowUpIntent with parsed filters
    """
    
    reduced_radius = int(current_radius * 0.5)
    
    prompt = f"""You are analyzing a follow-up search refinement.

Original search: "{original_query}"
Current radius: {current_radius} meters
Follow-up: "{followup_text}"

Determine if this is:
1. A COMPLETELY NEW SEARCH (user wants to search for something different)
2. A REFINEMENT of existing results (filter, sort, or adjust search)

If it's a NEW SEARCH, set is_new_search=true and provide the new_query.
If it's a REFINEMENT, set is_new_search=false and provide the filters.

Parse the follow-up into structured filters:

**Distance conversions:**
- "within X miles" → radius in meters (1 mile = 1609 meters)
- "within X km" → radius in meters (1 km = 1000 meters)
- "closer" → {reduced_radius} meters (50% of current)
- "nearby" → 1000 meters
- "walking distance" → 800 meters

**Price filters:**
- "cheap", "affordable", "budget", "inexpensive" → price_min=1, price_max=2
- "moderate", "mid-range" → price_min=2, price_max=3
- "expensive", "fancy", "upscale" → price_min=3, price_max=4

**Features:**
- "wifi", "internet" → ["wifi"]
- "outdoor seating", "patio", "outside" → ["outdoor_seating"]
- "parking" → ["parking"]
- "family friendly", "kids" → ["family_friendly"]

**Other filters:**
- "open now" → open_now=true
- "highly rated", "top rated", "best rated" → min_rating=4.0
- "highest rated first" → sort_by="rating"
- "closest first", "nearest" → sort_by="distance"

Return ONLY valid JSON matching this structure:
{{
    "is_new_search": boolean,
    "new_query": string or null,
    "adjust_radius": number or null,
    "price_min": number or null,
    "price_max": number or null,
    "open_now": boolean or null,
    "required_features": array of strings,
    "min_rating": number or null,
    "sort_by": string or null
}}

Examples:

Follow-up: "cheaper options"
{{
    "is_new_search": false,
    "new_query": null,
    "adjust_radius": null,
    "price_min": 1,
    "price_max": 2,
    "open_now": null,
    "required_features": [],
    "min_rating": null,
    "sort_by": null
}}

Follow-up: "within 2 miles"
{{
    "is_new_search": false,
    "new_query": null,
    "adjust_radius": 3218,
    "price_min": null,
    "price_max": null,
    "open_now": null,
    "required_features": [],
    "min_rating": null,
    "sort_by": null
}}

Follow-up: "pizza places"
{{
    "is_new_search": true,
    "new_query": "pizza",
    "adjust_radius": null,
    "price_min": null,
    "price_max": null,
    "open_now": null,
    "required_features": [],
    "min_rating": null,
    "sort_by": null
}}

Follow-up: "with wifi and outdoor seating, closer"
{{
    "is_new_search": false,
    "new_query": null,
    "adjust_radius": {reduced_radius},
    "price_min": null,
    "price_max": null,
    "open_now": null,
    "required_features": ["wifi", "outdoor_seating"],
    "min_rating": null,
    "sort_by": null
}}

Now parse: "{followup_text}"
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a search refinement parser. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result_json = response.choices[0].message.content
        intent_data = json.loads(result_json)
        
        return FollowUpIntent(**intent_data)
        
    except Exception as e:
        # Fallback: treat as refinement with combined query
        return FollowUpIntent(
            is_new_search=False,
            new_query=None
        )