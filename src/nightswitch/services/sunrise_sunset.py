"""
Sunrise/sunset service for astronomical calculations in Nightswitch.

This module provides the SunriseSunsetService class that integrates with
the sunrisesunset.io API to get accurate sunrise and sunset times for
location-based theme switching.
"""

import logging
import requests
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Dict, Any, Callable
import threading
import time


class SunriseSunsetService:
    """
    Service for getting sunrise and sunset times using sunrisesunset.io API.
    
    Provides sunrise/sunset time calculation with scheduling capabilities
    for automatic theme switching based on natural lighting conditions.
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the sunrise/sunset service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.logger = logging.getLogger("nightswitch.services.sunrise_sunset")
        self.timeout = timeout
        self.api_base_url = "https://api.sunrisesunset.io"
        
        # Cache for sun times
        self._cached_sun_times: Dict[str, Any] = {}
        
        # Scheduling state
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_scheduling = False
        self._current_callback: Optional[Callable[[str], None]] = None
        self._current_location: Optional[Tuple[float, float]] = None
        
        # Lock for thread safety
        self._lock = threading.Lock()

    def get_sun_times(
        self, 
        latitude: float, 
        longitude: float, 
        target_date: Optional[date] = None
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Get sunrise and sunset times for given coordinates and date.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            target_date: Date to get times for (defaults to today)
            
        Returns:
            Tuple of (sunrise_datetime, sunset_datetime) or None if failed
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Check cache first
            cache_key = f"{latitude},{longitude},{target_date}"
            if cache_key in self._cached_sun_times:
                cached = self._cached_sun_times[cache_key]
                # Check if cache is still valid (same day)
                if cached["date"] == target_date:
                    self.logger.debug(f"Using cached sun times for {target_date}")
                    return (cached["sunrise"], cached["sunset"])
            
            # Query API
            url = f"{self.api_base_url}/json"
            params = {
                "lat": latitude,
                "lng": longitude,
                "date": target_date.strftime("%Y-%m-%d"),
                "formatted": 0  # Get UTC timestamps
            }
            
            self.logger.debug(f"Querying sunrise/sunset API for {latitude}, {longitude} on {target_date}")
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK":
                self.logger.error(f"API returned error status: {data}")
                return None
            
            results = data.get("results", {})
            sunrise_utc = results.get("sunrise")
            sunset_utc = results.get("sunset")
            
            if not sunrise_utc or not sunset_utc:
                self.logger.error(f"Missing sunrise/sunset data in API response: {results}")
                return None
            
            # Parse UTC timestamps and convert to local time
            sunrise_dt = datetime.fromisoformat(sunrise_utc.replace("Z", "+00:00"))
            sunset_dt = datetime.fromisoformat(sunset_utc.replace("Z", "+00:00"))
            
            # Convert to local timezone
            sunrise_local = sunrise_dt.astimezone()
            sunset_local = sunset_dt.astimezone()
            
            # Cache the result
            self._cached_sun_times[cache_key] = {
                "date": target_date,
                "sunrise": sunrise_local,
                "sunset": sunset_local,
                "cached_at": datetime.now()
            }
            
            self.logger.info(
                f"Sun times for {target_date}: sunrise={sunrise_local.strftime('%H:%M')}, "
                f"sunset={sunset_local.strftime('%H:%M')}"
            )
            
            return (sunrise_local, sunset_local)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error getting sun times: {e}")
            return None
        except (ValueError, KeyError) as e:
            self.logger.error(f"Invalid API response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting sun times: {e}")
            return None

    def schedule_sun_events(
        self, 
        latitude: float, 
        longitude: float, 
        callback: Callable[[str], None]
    ) -> bool:
        """
        Set up sunrise/sunset event scheduling using API data.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            callback: Function to call for theme changes (receives 'sunrise' or 'sunset')
            
        Returns:
            True if scheduling was set up successfully, False otherwise
        """
        try:
            with self._lock:
                # Stop existing scheduling
                self._stop_scheduling_internal()
                
                # Validate coordinates
                if not self._validate_coordinates(latitude, longitude):
                    self.logger.error(f"Invalid coordinates: {latitude}, {longitude}")
                    return False
                
                # Set up new scheduling
                self._current_location = (latitude, longitude)
                self._current_callback = callback
                
                # Start scheduler thread
                self._start_scheduler_thread()
                
            self.logger.info(f"Sun event scheduling enabled for {latitude}, {longitude}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule sun events: {e}")
            return False

    def stop_sun_events(self) -> None:
        """Stop sunrise/sunset event scheduling."""
        with self._lock:
            self._stop_scheduling_internal()
        self.logger.info("Sun event scheduling stopped")

    def _stop_scheduling_internal(self) -> None:
        """Internal method to stop scheduling (assumes lock is held)."""
        if self._is_scheduling:
            self._stop_event.set()
            self._is_scheduling = False
            
            # Wait for scheduler thread to finish
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=2.0)
                
            self._scheduler_thread = None
            self._stop_event.clear()

    def _start_scheduler_thread(self) -> None:
        """Start the scheduler thread for monitoring sun events."""
        self._stop_event.clear()
        self._is_scheduling = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="SunEventScheduler",
            daemon=True
        )
        self._scheduler_thread.start()

    def _scheduler_loop(self) -> None:
        """Main scheduler loop that monitors for sunrise/sunset events."""
        self.logger.debug("Sun event scheduler loop started")
        
        last_check_minute = -1
        last_date = None
        current_sun_times = None
        
        while not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                current_date = current_time.date()
                current_minute = current_time.hour * 60 + current_time.minute
                
                # Get sun times for today if needed
                if current_date != last_date or current_sun_times is None:
                    if self._current_location:
                        lat, lon = self._current_location
                        current_sun_times = self.get_sun_times(lat, lon, current_date)
                        last_date = current_date
                        
                        if current_sun_times:
                            sunrise, sunset = current_sun_times
                            self.logger.debug(
                                f"Updated sun times for {current_date}: "
                                f"sunrise={sunrise.strftime('%H:%M')}, sunset={sunset.strftime('%H:%M')}"
                            )
                
                # Only check once per minute to avoid duplicate triggers
                if current_minute != last_check_minute and current_sun_times:
                    last_check_minute = current_minute
                    self._check_sun_events(current_time, current_sun_times)
                
                # Sleep for a short interval
                self._stop_event.wait(timeout=30.0)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                self._stop_event.wait(timeout=60.0)
        
        self.logger.debug("Sun event scheduler loop stopped")

    def _check_sun_events(self, current_time: datetime, sun_times: Tuple[datetime, datetime]) -> None:
        """
        Check if current time matches any sun events.
        
        Args:
            current_time: Current datetime to check
            sun_times: Tuple of (sunrise, sunset) datetimes
        """
        try:
            sunrise, sunset = sun_times
            
            # Check for sunrise event (within 1 minute)
            if self._is_time_match(current_time, sunrise):
                self.logger.info(f"Triggering sunrise event at {current_time.strftime('%H:%M')}")
                if self._current_callback:
                    try:
                        self._current_callback("sunrise")
                    except Exception as e:
                        self.logger.error(f"Error in sunrise callback: {e}")
            
            # Check for sunset event (within 1 minute)
            elif self._is_time_match(current_time, sunset):
                self.logger.info(f"Triggering sunset event at {current_time.strftime('%H:%M')}")
                if self._current_callback:
                    try:
                        self._current_callback("sunset")
                    except Exception as e:
                        self.logger.error(f"Error in sunset callback: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error checking sun events: {e}")

    def _is_time_match(self, current_time: datetime, target_time: datetime) -> bool:
        """
        Check if current time matches target time within a 1-minute window.
        
        Args:
            current_time: Current datetime
            target_time: Target datetime to match
            
        Returns:
            True if times match within 1 minute, False otherwise
        """
        try:
            # Calculate difference in minutes
            diff = abs((current_time - target_time).total_seconds() / 60)
            return diff < 1.0
            
        except Exception:
            return False

    def get_next_sun_event(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Tuple[datetime, str]]:
        """
        Get the next sunrise or sunset event.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Tuple of (event_datetime, event_type) or None if failed
        """
        try:
            current_time = datetime.now()
            current_date = current_time.date()
            
            # Get today's sun times
            sun_times = self.get_sun_times(latitude, longitude, current_date)
            if not sun_times:
                return None
            
            sunrise, sunset = sun_times
            
            # Check if sunrise is in the future today
            if sunrise > current_time:
                return (sunrise, "sunrise")
            
            # Check if sunset is in the future today
            if sunset > current_time:
                return (sunset, "sunset")
            
            # Both events have passed today, get tomorrow's sunrise
            tomorrow = current_date + timedelta(days=1)
            tomorrow_sun_times = self.get_sun_times(latitude, longitude, tomorrow)
            if tomorrow_sun_times:
                tomorrow_sunrise, _ = tomorrow_sun_times
                return (tomorrow_sunrise, "sunrise")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting next sun event: {e}")
            return None

    def get_current_sun_period(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[str]:
        """
        Determine if it's currently day or night based on sun times.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            'day' if between sunrise and sunset, 'night' otherwise, or None if failed
        """
        try:
            current_time = datetime.now()
            sun_times = self.get_sun_times(latitude, longitude)
            
            if not sun_times:
                return None
            
            sunrise, sunset = sun_times
            
            # Check if current time is between sunrise and sunset
            if sunrise <= current_time <= sunset:
                return "day"
            else:
                return "night"
                
        except Exception as e:
            self.logger.error(f"Error determining sun period: {e}")
            return None

    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        try:
            return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
        except (TypeError, ValueError):
            return False

    def clear_cache(self) -> None:
        """Clear cached sun times data."""
        self._cached_sun_times.clear()
        self.logger.debug("Sun times cache cleared")

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get detailed service status information.
        
        Returns:
            Dictionary with service status details
        """
        with self._lock:
            status = {
                "is_scheduling": self._is_scheduling,
                "api_url": self.api_base_url,
                "timeout": self.timeout,
                "has_callback": self._current_callback is not None,
                "current_location": self._current_location,
                "thread_alive": self._scheduler_thread.is_alive() if self._scheduler_thread else False,
                "cached_entries": len(self._cached_sun_times)
            }
            
            # Add next event info if scheduling
            if self._is_scheduling and self._current_location:
                lat, lon = self._current_location
                next_event = self.get_next_sun_event(lat, lon)
                if next_event:
                    event_time, event_type = next_event
                    status["next_event_time"] = event_time.strftime("%H:%M")
                    status["next_event_type"] = event_type
                    status["next_event_date"] = event_time.date().isoformat()
                
                # Add current sun period
                current_period = self.get_current_sun_period(lat, lon)
                if current_period:
                    status["current_period"] = current_period
            
            return status

    def test_api_connectivity(self) -> bool:
        """
        Test connectivity to the sunrisesunset.io API.
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            # Test with a known location (London)
            test_url = f"{self.api_base_url}/json"
            test_params = {"lat": 51.5074, "lng": -0.1278, "formatted": 0}
            
            response = requests.get(test_url, params=test_params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            success = data.get("status") == "OK"
            
            if success:
                self.logger.debug("API connectivity test passed")
            else:
                self.logger.warning(f"API connectivity test failed: {data}")
            
            return success
            
        except Exception as e:
            self.logger.warning(f"API connectivity test failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources and stop scheduling."""
        try:
            self.logger.info("Cleaning up sunrise/sunset service")
            self.stop_sun_events()
            self.clear_cache()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global sunrise/sunset service instance
_sunrise_sunset_service: Optional[SunriseSunsetService] = None


def get_sunrise_sunset_service() -> SunriseSunsetService:
    """
    Get the global sunrise/sunset service instance.
    
    Returns:
        SunriseSunsetService instance
    """
    global _sunrise_sunset_service
    if _sunrise_sunset_service is None:
        _sunrise_sunset_service = SunriseSunsetService()
    return _sunrise_sunset_service