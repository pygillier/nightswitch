"""
Location service for IP-based location detection in Nightswitch.

This module provides the LocationService class that handles automatic location
detection using IP geolocation APIs with fallback mechanisms.
"""

import logging
import requests
from typing import Optional, Tuple, Dict, Any
import json


class LocationService:
    """
    Service for detecting user location via IP geolocation.
    
    Provides automatic location detection with validation and manual
    location input fallback for location-based theme switching.
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the location service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.logger = logging.getLogger("nightswitch.services.location")
        self.timeout = timeout
        
        # Primary and fallback geolocation APIs
        self._apis = [
            {
                "name": "ipapi.co",
                "url": "https://ipapi.co/json/",
                "lat_key": "latitude",
                "lon_key": "longitude",
                "city_key": "city",
                "country_key": "country_name"
            },
            {
                "name": "ip-api.com", 
                "url": "http://ip-api.com/json/",
                "lat_key": "lat",
                "lon_key": "lon", 
                "city_key": "city",
                "country_key": "country"
            },
            {
                "name": "ipinfo.io",
                "url": "https://ipinfo.io/json",
                "lat_key": "loc",  # Special handling needed - format "lat,lon"
                "lon_key": "loc",
                "city_key": "city",
                "country_key": "country"
            }
        ]
        
        # Cache for location data
        self._cached_location: Optional[Dict[str, Any]] = None

    def get_current_location(self) -> Optional[Tuple[float, float, str]]:
        """
        Get current location via IP geolocation APIs.
        
        Tries multiple APIs for reliability and returns the first successful result.
        
        Returns:
            Tuple of (latitude, longitude, location_description) or None if failed
        """
        try:
            # Try each API in order
            for api in self._apis:
                try:
                    self.logger.debug(f"Trying location API: {api['name']}")
                    location_data = self._query_api(api)
                    
                    if location_data:
                        # Cache successful result
                        self._cached_location = location_data
                        
                        lat = location_data["latitude"]
                        lon = location_data["longitude"]
                        description = location_data.get("description", "Unknown location")
                        
                        self.logger.info(f"Location detected: {description} ({lat}, {lon})")
                        return (lat, lon, description)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get location from {api['name']}: {e}")
                    continue
            
            self.logger.error("All location APIs failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current location: {e}")
            return None

    def _query_api(self, api: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Query a specific geolocation API.
        
        Args:
            api: API configuration dictionary
            
        Returns:
            Normalized location data or None if failed
        """
        try:
            response = requests.get(api["url"], timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different API response formats
            if api["name"] == "ipinfo.io":
                # Special handling for ipinfo.io loc format "lat,lon"
                loc_str = data.get(api["lat_key"])
                if not loc_str or "," not in loc_str:
                    return None
                    
                lat_str, lon_str = loc_str.split(",", 1)
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
            else:
                # Standard format
                latitude = float(data.get(api["lat_key"], 0))
                longitude = float(data.get(api["lon_key"], 0))
            
            # Validate coordinates
            if not self.validate_coordinates(latitude, longitude):
                self.logger.warning(f"Invalid coordinates from {api['name']}: {latitude}, {longitude}")
                return None
            
            # Build location description
            city = data.get(api["city_key"], "")
            country = data.get(api["country_key"], "")
            description = f"{city}, {country}".strip(", ") if city or country else "Unknown location"
            
            return {
                "latitude": latitude,
                "longitude": longitude,
                "description": description,
                "source": api["name"],
                "raw_data": data
            }
            
        except requests.RequestException as e:
            self.logger.warning(f"Network error querying {api['name']}: {e}")
            return None
        except (ValueError, KeyError) as e:
            self.logger.warning(f"Invalid response from {api['name']}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error querying {api['name']}: {e}")
            return None

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates.
        
        Args:
            latitude: Latitude value to validate
            longitude: Longitude value to validate
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        try:
            # Check latitude range
            if not (-90 <= latitude <= 90):
                return False
            
            # Check longitude range  
            if not (-180 <= longitude <= 180):
                return False
            
            # Check for obviously invalid values (0,0 is often a default)
            if latitude == 0 and longitude == 0:
                return False
                
            return True
            
        except (TypeError, ValueError):
            return False

    def get_cached_location(self) -> Optional[Tuple[float, float, str]]:
        """
        Get cached location data if available.
        
        Returns:
            Tuple of (latitude, longitude, location_description) or None if no cache
        """
        if self._cached_location:
            return (
                self._cached_location["latitude"],
                self._cached_location["longitude"], 
                self._cached_location.get("description", "Cached location")
            )
        return None

    def clear_cache(self) -> None:
        """Clear cached location data."""
        self._cached_location = None
        self.logger.debug("Location cache cleared")

    def test_connectivity(self) -> bool:
        """
        Test connectivity to location services.
        
        Returns:
            True if at least one API is reachable, False otherwise
        """
        try:
            for api in self._apis:
                try:
                    response = requests.get(api["url"], timeout=5)
                    if response.status_code == 200:
                        self.logger.debug(f"Connectivity test passed for {api['name']}")
                        return True
                except:
                    continue
            
            self.logger.warning("No location APIs are reachable")
            return False
            
        except Exception as e:
            self.logger.error(f"Error testing connectivity: {e}")
            return False

    def get_location_info(self) -> Dict[str, Any]:
        """
        Get detailed location service information.
        
        Returns:
            Dictionary with service status and configuration
        """
        info = {
            "available_apis": [api["name"] for api in self._apis],
            "timeout": self.timeout,
            "has_cached_location": self._cached_location is not None,
            "connectivity": self.test_connectivity()
        }
        
        if self._cached_location:
            info["cached_location"] = {
                "latitude": self._cached_location["latitude"],
                "longitude": self._cached_location["longitude"],
                "description": self._cached_location.get("description"),
                "source": self._cached_location.get("source")
            }
        
        return info


# Global location service instance
_location_service: Optional[LocationService] = None


def get_location_service() -> LocationService:
    """
    Get the global location service instance.
    
    Returns:
        LocationService instance
    """
    global _location_service
    if _location_service is None:
        _location_service = LocationService()
    return _location_service