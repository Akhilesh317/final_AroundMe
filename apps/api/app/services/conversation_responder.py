"""Generate conversational responses for follow-up queries"""
from typing import List, Dict, Optional
import openai
from app.config import settings
from app.schemas.places import Place
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def generate_conversational_response(
    query: str,
    places: List[Place],
    context: Optional[Dict] = None
) -> str:
    """
    Generate a natural language response for follow-up queries
    
    Args:
        query: User's follow-up question
        places: Filtered/sorted places to present
        context: Previous conversation context
        
    Returns:
        Natural language response string
    """
    
    # Build place summaries for top 5
    place_summaries = []
    for i, place in enumerate(places[:5], 1):
        summary = {
            "rank": i,
            "name": place.name,
            "rating": place.rating,
            "price_level": "$" * (place.price_level or 1),
            "distance_km": round(place.distance_km, 1) if place.distance_km else None,
            "category": place.category,
        }
        place_summaries.append(summary)
    
    prompt = f"""You are a helpful local discovery assistant. The user asked a follow-up question about their restaurant search.

Previous context: {context.get('original_query', 'restaurant search') if context else 'restaurant search'}
User's follow-up: "{query}"
Total places found: {len(places)}

Top results:
{format_places_for_prompt(place_summaries)}

Generate a friendly, concise response that:
1. Acknowledges the user's request
2. Lists the top 2-3 most relevant options as a bulleted list
3. Includes key details (name, price, distance, rating)
4. Ends with a helpful suggestion or question

Keep it natural and conversational, like talking to a friend."""

    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful local discovery assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        conversational_response = response.choices[0].message.content.strip()
        
        logger.info("conversational_response_generated", 
                   query=query, 
                   response_length=len(conversational_response))
        
        return conversational_response
        
    except Exception as e:
        logger.error("conversational_response_failed", error=str(e))
        # Fallback to simple response
        return format_fallback_response(query, places)


def format_places_for_prompt(summaries: List[Dict]) -> str:
    """Format place summaries for the AI prompt"""
    lines = []
    for summary in summaries:
        line = f"{summary['rank']}. {summary['name']} - {summary['price_level']}"
        if summary['rating']:
            line += f" ({summary['rating']}⭐)"
        if summary['distance_km']:
            line += f" - {summary['distance_km']}km away"
        lines.append(line)
    return "\n".join(lines)


def format_fallback_response(query: str, places: List[Place]) -> str:
    """Simple fallback response if AI fails"""
    
    if not places:
        return "I couldn't find any places matching your criteria. Try adjusting your filters!"
    
    response = f"Here are the top {min(3, len(places))} options:\n\n"
    
    for i, place in enumerate(places[:3], 1):
        response += f"{i}. **{place.name}**"
        if place.price_level:
            response += f" - {'$' * place.price_level}"
        if place.rating:
            response += f" ({place.rating}⭐)"
        if place.distance_km:
            response += f" - {round(place.distance_km, 1)}km away"
        response += "\n"
    
    return response