"""Geospatial utility functions"""
import math
from typing import Tuple

from haversine import haversine, Unit


def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate haversine distance in kilometers"""
    return haversine((lat1, lng1), (lat2, lng2), unit=Unit.KILOMETERS)


def calculate_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate haversine distance in meters"""
    return haversine((lat1, lng1), (lat2, lng2), unit=Unit.METERS)


def is_within_radius(
    lat1: float, lng1: float, lat2: float, lng2: float, radius_m: float
) -> bool:
    """Check if two points are within a radius"""
    return calculate_distance_m(lat1, lng1, lat2, lng2) <= radius_m


def normalize_coordinates(lat: float, lng: float) -> Tuple[float, float]:
    """Normalize coordinates to valid ranges"""
    # Clamp latitude to [-90, 90]
    lat = max(-90.0, min(90.0, lat))
    # Normalize longitude to [-180, 180]
    lng = ((lng + 180) % 360) - 180
    return lat, lng


def calculate_bounding_box(
    lat: float, lng: float, radius_m: float
) -> Tuple[float, float, float, float]:
    """Calculate bounding box for a circle
    
    Returns: (min_lat, min_lng, max_lat, max_lng)
    """
    # Earth radius in meters
    earth_radius = 6371000.0
    
    # Angular distance in radians
    angular_distance = radius_m / earth_radius
    
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    
    min_lat = lat_rad - angular_distance
    max_lat = lat_rad + angular_distance
    
    # Handle poles
    if min_lat > -math.pi / 2 and max_lat < math.pi / 2:
        delta_lng = math.asin(math.sin(angular_distance) / math.cos(lat_rad))
        min_lng = lng_rad - delta_lng
        max_lng = lng_rad + delta_lng
    else:
        # Pole is within distance
        min_lat = max(min_lat, -math.pi / 2)
        max_lat = min(max_lat, math.pi / 2)
        min_lng = -math.pi
        max_lng = math.pi
    
    return (
        math.degrees(min_lat),
        math.degrees(min_lng),
        math.degrees(max_lat),
        math.degrees(max_lng),
    )