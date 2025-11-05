"""AI-powered feature analysis for places"""
import json
from typing import List, Dict
from openai import AsyncOpenAI
from app.config import settings
from app.schemas.places import Place

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def analyze_features(
    places: List[Place],
    original_query: str,
    user_requirements: List[str] = None
) -> Dict[str, any]:
    """
    Use AI to intelligently determine likely features for places
    
    Args:
        places: List of places from search results
        original_query: User's original search query
        user_requirements: Extracted requirements (e.g., "with wifi", "family friendly")
    
    Returns:
        Dictionary with feature availability data
    """
    
    # Extract place categories
    categories = list(set([p.category for p in places if p.category]))
    
    # Build context about the places
    place_context = []
    for place in places[:10]:  # Sample first 10 for context
        place_context.append({
            "name": place.name,
            "category": place.category,
            "rating": place.rating,
            "price_level": place.price_level,
        })
    
    prompt = f"""You are analyzing search results for places to determine likely feature availability.

**User's Search Query:** "{original_query}"
**User Requirements:** {user_requirements or "None specified"}
**Place Categories Found:** {', '.join(categories)}
**Sample Places:** {json.dumps(place_context, indent=2)}
**Total Places:** {len(places)}

Based on the search context, intelligently determine which features are MOST RELEVANT and LIKELY to be available at these types of places.

For example:
- If searching for "restaurant", relevant features include: WiFi, Outdoor Seating, Parking, Reservations, Delivery, Wheelchair Accessible, Good for Groups, Credit Cards
- If searching for "coffee shop", relevant features include: WiFi, Outdoor Seating, Laptop Friendly, Power Outlets, Quiet Atmosphere, Pastries Available
- If searching for "park", relevant features include: Playground, Picnic Areas, Walking Trails, Restrooms, Parking, Dog Friendly, Sports Facilities
- If searching for "gym", relevant features include: Personal Training, Group Classes, Locker Rooms, Showers, Parking, 24/7 Access, Equipment Variety
- If searching for "hotel", relevant features include: WiFi, Parking, Pool, Gym, Restaurant, Room Service, Pet Friendly, Business Center

**Important Guidelines:**
1. ONLY suggest features that make sense for these place types
2. If user specified requirements (e.g., "with wifi"), make sure to include those features
3. Provide realistic percentage estimates (0-100) for how many places likely have each feature
4. Consider the price level and ratings when estimating percentages
5. Higher-rated and higher-priced places more likely have premium features
6. Return 6-10 most relevant features

Return ONLY valid JSON in this exact format:
{{
  "features": [
    {{
      "name": "Feature Name",
      "icon": "emoji icon",
      "estimated_percentage": 75,
      "relevance": "high|medium|low",
      "reasoning": "Brief explanation why this feature is relevant"
    }}
  ],
  "insights": "1-2 sentence summary about feature availability for these places"
}}

Example output:
{{
  "features": [
    {{
      "name": "WiFi Available",
      "icon": "📶",
      "estimated_percentage": 85,
      "relevance": "high",
      "reasoning": "Most modern restaurants offer free WiFi to attract customers"
    }},
    {{
      "name": "Outdoor Seating",
      "icon": "🌳",
      "estimated_percentage": 60,
      "relevance": "high",
      "reasoning": "Many restaurants have patio or outdoor dining options"
    }}
  ],
  "insights": "Most restaurants in this area offer essential amenities like WiFi and accept credit cards. Outdoor seating and parking availability vary by location."
}}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a local search expert analyzing place features. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        result_json = response.choices[0].message.content
        analysis = json.loads(result_json)
        
        # Calculate actual counts based on percentages
        for feature in analysis.get("features", []):
            percentage = feature["estimated_percentage"]
            feature["count"] = round((percentage / 100) * len(places))
        
        return analysis
        
    except Exception as e:
        # Fallback to generic features
        return {
            "features": [
                {
                    "name": "Credit Cards Accepted",
                    "icon": "💳",
                    "estimated_percentage": 95,
                    "count": round(0.95 * len(places)),
                    "relevance": "high",
                    "reasoning": "Most businesses accept credit cards"
                },
                {
                    "name": "Parking Available",
                    "icon": "🅿️",
                    "estimated_percentage": 70,
                    "count": round(0.70 * len(places)),
                    "relevance": "medium",
                    "reasoning": "Many locations provide parking"
                }
            ],
            "insights": "Feature analysis based on place types and ratings."
        }