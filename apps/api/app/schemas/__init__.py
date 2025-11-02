"""Schema exports"""
from app.schemas.places import Place, ProviderPlace, MatchedPartner
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    MultiEntityIntent,
    EntitySpec,
    RelationSpec,
    SearchFilters,
    SearchContext,
    SearchDebug,
)
from app.schemas.profile import (
    ProfileCreate,
    Profile,
    ProfilePreference,
    ProfilePreferenceInDB,
    PreferenceListResponse,
    PreferenceUpdateRequest,
    HealthResponse,
    MetricsResponse,
)

__all__ = [
    # Place schemas
    "Place",
    "ProviderPlace",
    "MatchedPartner",
    # Search schemas
    "SearchRequest",
    "SearchResponse",
    "MultiEntityIntent",
    "EntitySpec",
    "RelationSpec",
    "SearchFilters",
    "SearchContext",
    "SearchDebug",
    # Profile schemas
    "ProfileCreate",
    "Profile",
    "ProfilePreference",
    "ProfilePreferenceInDB",
    "PreferenceListResponse",
    "PreferenceUpdateRequest",
    # Health & Metrics
    "HealthResponse",
    "MetricsResponse",
]