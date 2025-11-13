"""Application configuration"""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # API Keys
    google_places_api_key: str = ""
    yelp_api_key: str = ""
    openai_api_key: str = ""
    
    # Database
    database_url: str = "postgresql+psycopg://aroundme:aroundme@localhost:5432/aroundme"
    redis_url: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Cache
    cache_ttl_seconds: int = 1200
    
    # Agent Configuration
    agent_mode: Literal["full", "deterministic"] = "full"
    personalization_default: Literal["on", "off"] = "off"
    snapshot_demo: bool = False
    ranking_preset: Literal["balanced", "nearby", "review-heavy"] = "balanced"
    
    # Application
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    web_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    
    # Logging
    log_level: str = "INFO"
    
    # Provider Settings
    google_timeout: int = 10
    yelp_timeout: int = 10
    max_results_per_provider: int = 60
    
    # Search Defaults
    default_radius_m: int = 3000
    default_top_k: int = 30
    max_radius_m: int = 50000
    
    # Fusion
    name_similarity_threshold: float = 0.82
    geo_distance_threshold_m: float = 120.0
    
    # Ranking
    max_personalization_boost: float = 0.15
    
    # Multi-entity
    default_near_distance_m: float = 500.0
    constraint_join_timeout: int = 5
    
    # Follow-ups
    conversation_ttl_seconds: int = 900  # 15 minutes
    max_followup_expansion_radius_m: int = 5000
    
    # ✅ NEW: Feature Matching Settings
    enable_semantic_matching: bool = True
    semantic_match_threshold: float = 0.75
    embedding_cache_ttl: int = 3600  # 1 hour
    max_semantic_searches_per_request: int = 50  # Limit to control OpenAI costs


settings = Settings()