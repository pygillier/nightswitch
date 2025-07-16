"""
Services for Nightswitch application.

This package contains service classes that handle external integrations:
- Schedule service for time-based switching
- Location service for IP-based location detection
- Sunrise/sunset service for astronomical calculations
"""

from .schedule import ScheduleService, get_schedule_service
from .location import LocationService, get_location_service
from .sunrise_sunset import SunriseSunsetService, get_sunrise_sunset_service

__all__ = [
    "ScheduleService",
    "get_schedule_service",
    "LocationService", 
    "get_location_service",
    "SunriseSunsetService",
    "get_sunrise_sunset_service",
]
