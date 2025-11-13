"""Semantic matching using OpenAI embeddings"""
import asyncio
from typing import List, Dict, Tuple, Optional
import openai
import numpy as np
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Cache for embeddings (in production, use Redis)
_embedding_cache: Dict[str, List[float]] = {}


async def get_embedding(text: str) -> List[float]:
    """Get embedding for text, with caching"""
    
    if not text or len(text.strip()) == 0:
        return []
    
    # Check cache
    cache_key = text.lower().strip()
    if cache_key in _embedding_cache:
        logger.debug("embedding_cache_hit", text=text[:50])
        return _embedding_cache[cache_key]
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",  # Cheaper and faster
            input=text
        )
        
        embedding = response.data[0].embedding
        
        # Cache it
        _embedding_cache[cache_key] = embedding
        
        logger.debug("embedding_created", text=text[:50], dim=len(embedding))
        
        return embedding
        
    except Exception as e:
        logger.error("embedding_failed", error=str(e), text=text[:50])
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2:
        return 0.0
    
    try:
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        logger.error("cosine_similarity_error", error=str(e))
        return 0.0


async def semantic_match(
    requirement: str,
    place_texts: List[str],
    threshold: float = 0.75
) -> List[Tuple[int, float, str]]:
    """
    Check if requirement semantically matches any place text
    
    Args:
        requirement: The requirement to match (e.g., "WiFi")
        place_texts: List of text snippets from the place
        threshold: Similarity threshold (0-1)
        
    Returns:
        List of (index, similarity_score, matched_text) for matches above threshold
    """
    
    if not requirement or not place_texts:
        return []
    
    # Get embedding for requirement
    req_embedding = await get_embedding(requirement)
    
    if not req_embedding:
        return []
    
    # Get embeddings for all place texts (in parallel)
    place_embedding_tasks = [get_embedding(text) for text in place_texts if text]
    place_embeddings = await asyncio.gather(*place_embedding_tasks)
    
    # Calculate similarities
    matches = []
    text_idx = 0
    for idx, place_emb in enumerate(place_embeddings):
        if not place_emb:
            continue
        
        # Find corresponding text (skip empty ones)
        while text_idx < len(place_texts) and not place_texts[text_idx]:
            text_idx += 1
        
        if text_idx >= len(place_texts):
            break
            
        similarity = cosine_similarity(req_embedding, place_emb)
        
        if similarity >= threshold:
            matches.append((idx, similarity, place_texts[text_idx]))
        
        text_idx += 1
    
    # Sort by similarity descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    logger.info("semantic_match_complete",
                requirement=requirement,
                texts_checked=len(place_texts),
                matches_found=len(matches))
    
    return matches


async def batch_semantic_match(
    requirements: List[str],
    place_texts: List[str],
    threshold: float = 0.75
) -> Dict[str, Tuple[bool, float]]:
    """
    Batch check multiple requirements against place texts
    
    Returns:
        Dict mapping requirement -> (matched, confidence_score)
    """
    
    results = {}
    
    for req in requirements:
        matches = await semantic_match(req, place_texts, threshold)
        if matches:
            # Return highest similarity
            results[req] = (True, matches[0][1])
        else:
            results[req] = (False, 0.0)
    
    return results