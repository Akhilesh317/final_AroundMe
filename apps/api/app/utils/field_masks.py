"""Google Places API field mask utilities"""

# Google Places API v1 field mask
# Includes all relevant fields while respecting API pricing
GOOGLE_PLACES_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.internationalPhoneNumber",
    "places.googleMapsUri",
    "places.websiteUri",
    "places.currentOpeningHours",
    "places.types",
    "places.primaryType",
    "places.businessStatus",
    "nextPageToken",
])


def build_field_mask(fields: list[str]) -> str:
    """Build a field mask string from a list of fields"""
    return ",".join(f"places.{field}" for field in fields)


def get_minimal_field_mask() -> str:
    """Get minimal field mask for basic place data"""
    return build_field_mask([
        "id",
        "displayName",
        "location",
        "types",
    ])


def get_standard_field_mask() -> str:
    """Get standard field mask (default)"""
    return GOOGLE_PLACES_FIELD_MASK