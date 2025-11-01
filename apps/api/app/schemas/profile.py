"""Profile and personalization schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProfilePreference(BaseModel):
    """User preference"""
    
    key: str = Field(..., description="Preference key (category, cuisine, feat_*, etc.)")
    value: str = Field(..., description="Preference value")
    weight: float = Field(0.5, ge=0, le=1, description="Preference weight")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "cuisine",
                "value": "italian",
                "weight": 0.8,
            }
        }


class ProfilePreferenceInDB(ProfilePreference):
    """Preference with database fields"""
    
    id: int
    profile_id: int
    updated_at: datetime


class ProfileCreate(BaseModel):
    """Create profile"""
    
    user_id: str


class Profile(BaseModel):
    """User profile"""
    
    id: int
    user_id: str
    created_at: datetime


class PreferenceListResponse(BaseModel):
    """List of preferences"""
    
    preferences: list[ProfilePreferenceInDB]


class PreferenceUpdateRequest(BaseModel):
    """Update preference request"""
    
    preferences: list[ProfilePreference]


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str
    version: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Metrics response"""
    
    provider_calls: dict[str, int]
    cache_hits: int
    cache_misses: int
    join_stats: dict[str, int]