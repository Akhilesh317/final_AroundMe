"""Place-related schemas"""
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ProviderPlace(BaseModel):
    """Normalized place from a provider"""
    
    provider: Literal["google", "yelp"]
    provider_id: str
    name: str
    category: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    rating: Optional[float] = Field(None, ge=0, le=5)
    user_rating_count: Optional[int] = Field(None, ge=0)
    price_level: Optional[int] = Field(None, ge=0, le=4)
    phone: Optional[str] = None
    website: Optional[str] = None
    maps_url: Optional[str] = None
    address: Optional[str] = None
    distance_km: Optional[float] = Field(None, ge=0)
    types: Optional[List[str]] = None
    raw: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "provider_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "name": "Blue Bottle Coffee",
                "category": "cafe",
                "lat": 37.7749,
                "lng": -122.4194,
                "rating": 4.5,
                "user_rating_count": 1250,
                "price_level": 2,
                "phone": "+1 415-123-4567",
                "website": "https://bluebottlecoffee.com",
                "maps_url": "https://maps.google.com/?cid=12345",
                "address": "66 Mint St, San Francisco, CA 94103",
                "distance_km": 0.5,
                "types": ["cafe", "food", "point_of_interest"],
            }
        }


class MatchedPartner(BaseModel):
    """Partner place that satisfied multi-entity constraints"""
    
    kind: str
    name: str
    distance_m: float
    matched_must_haves: List[str] = Field(default_factory=list)
    lat: float
    lng: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "kind": "park",
                "name": "Dolores Park",
                "distance_m": 250.5,
                "matched_must_haves": ["playground", "shade"],
                "lat": 37.7596,
                "lng": -122.4269,
            }
        }


class Place(BaseModel):
    """Canonical fused place"""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    category: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    rating: Optional[float] = Field(None, ge=0, le=5)
    user_rating_count: Optional[int] = Field(None, ge=0)
    price_level: Optional[int] = Field(None, ge=0, le=4)
    phone: Optional[str] = None
    website: Optional[str] = None
    maps_url: Optional[str] = None
    address: Optional[str] = None
    distance_km: Optional[float] = Field(None, ge=0)
    features: Dict[str, float] = Field(default_factory=dict)
    score: float = 0.0
    evidence: Dict[str, float] = Field(default_factory=dict)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    matched_partners: List[MatchedPartner] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Blue Bottle Coffee",
                "category": "cafe",
                "lat": 37.7749,
                "lng": -122.4194,
                "rating": 4.5,
                "user_rating_count": 1250,
                "price_level": 2,
                "phone": "+1 415-123-4567",
                "website": "https://bluebottlecoffee.com",
                "maps_url": "https://maps.google.com/?cid=12345",
                "address": "66 Mint St, San Francisco, CA 94103",
                "distance_km": 0.5,
                "features": {
                    "feat_wifi": 1.0,
                    "feat_outdoor_seating": 0.8,
                    "feat_family_friendly": 0.6,
                },
                "score": 0.85,
                "evidence": {
                    "rating": 0.45,
                    "reviews": 0.25,
                    "distance": 0.14,
                    "preferences": 0.01,
                },
                "provenance": [
                    {
                        "provider": "google",
                        "provider_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                        "name_similarity": 1.0,
                        "geo_distance_m": 0.0,
                    }
                ],
                "matched_partners": [],
            }
        }