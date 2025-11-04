"""Search-related schemas"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.places import Place


class SearchFilters(BaseModel):
    """Search filters"""
    
    price: Optional[List[int]] = Field(None, min_length=2, max_length=2)
    open_now: Optional[bool] = None
    category: Optional[str | List[str]] = None
    
    @field_validator("price")
    @classmethod
    def validate_price_range(cls, v):
        if v and (v[0] < 0 or v[1] > 4 or v[0] > v[1]):
            raise ValueError("Invalid price range")
        return v


class EntitySpec(BaseModel):
    """Entity specification for multi-entity queries"""
    
    kind: str = Field(..., description="Place type (e.g., restaurant, park)")
    must_haves: List[str] = Field(default_factory=list, description="Required amenities")
    filters: Optional[SearchFilters] = None


class RelationSpec(BaseModel):
    """Relation between entities"""
    
    left: int = Field(..., ge=0, description="Index of left entity")
    right: int = Field(..., ge=0, description="Index of right entity")
    relation: Literal["NEAR", "WITHIN_DISTANCE"]
    distance_m: Optional[float] = Field(None, ge=0, description="Distance in meters")
    
    @field_validator("distance_m")
    @classmethod
    def validate_distance(cls, v, info):
        if info.data.get("relation") == "WITHIN_DISTANCE" and v is None:
            raise ValueError("distance_m required for WITHIN_DISTANCE relation")
        return v


class MultiEntityIntent(BaseModel):
    """Multi-entity search intent"""
    
    entities: List[EntitySpec] = Field(..., min_length=1)
    relations: List[RelationSpec] = Field(default_factory=list)
    radius_m: int = Field(3000, ge=100, le=50000)
    top_k: int = Field(30, ge=1, le=100)


class SearchContext(BaseModel):
    """Search context for follow-ups"""
    
    conversation_id: Optional[str] = None
    result_set_id: Optional[str] = None
    follow_up: bool = False
    original_query: Optional[str] = None  # Add this line
    agent_mode: Optional[Literal["full", "deterministic"]] = None
    ranking_preset: Optional[Literal["balanced", "nearby", "review-heavy"]] = None

class SearchRequest(BaseModel):
    """Search request"""
    
    query: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius_m: int = Field(3000, ge=100, le=50000)
    filters: Optional[SearchFilters] = None
    multi_entity: Optional[MultiEntityIntent] = None
    context: Optional[SearchContext] = None
    top_k: int = Field(30, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "coffee",
                "lat": 32.814,
                "lng": -96.948,
                "radius_m": 3000,
                "filters": {"open_now": True, "price": [1, 3]},
                "top_k": 30,
            }
        }


class SearchDebug(BaseModel):
    """Debug information"""
    
    timings: Dict[str, float] = Field(default_factory=dict)
    cache_hit: bool = False
    agent_trace_id: str = ""
    counts_before_after: Dict[str, int] = Field(default_factory=dict)
    ranking_preset: str = "balanced"
    constraints_satisfied: Dict[str, Any] = Field(default_factory=dict)
    agent_mode: str = "full"


class SearchResponse(BaseModel):
    """Search response"""
    
    places: List[Place]
    debug: SearchDebug
    result_set_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "places": [],
                "debug": {
                    "timings": {"total": 1.234, "google": 0.567, "yelp": 0.456},
                    "cache_hit": False,
                    "agent_trace_id": "trace-123",
                    "counts_before_after": {"google": 20, "yelp": 15, "fused": 30},
                    "ranking_preset": "balanced",
                    "constraints_satisfied": {},
                    "agent_mode": "full",
                },
                "result_set_id": "result-123",
            }
        }