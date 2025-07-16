"""
Location mode handler for sunrise/sunset-based theme switching in Nightswitch.

This module provides the LocationModeHandler class that integrates location
and sunrise/sunset services to provide automatic theme switching based on
natural lighting conditions.
"""

import logging
from typing import Callable, Optional, Tuple, Dict, Any

from ..services.location import LocationService, get_location_service
from ..services.sunrise_sunset import SunriseSunsetService, get_sunrise_sunset_service
from .manual_mode import ThemeType


class LocationModeHandler:
    """
    Handler for location-based automatic theme switching.
    
    Integrates LocationService and SunriseSunsetService to provide automatic
    theme switching based on sunrise and sunset times for the user's location.
    """

    def __init__(
        self,
        location_service: Optional[LocationService] = None,
        sunrise_sunset_service: Optional[SunriseSunsetService] = None,
        theme_callback: Optional[Callable[[ThemeType], bool]] = None
    ):
        """
        Initialize the location mode handler.
        
        Args:
            location_service: Location service instance
            sunrise_sunset_service: Sunrise/sunset service instance
            theme_callback: Callback function for applying themes
        """
        self.logger = logging.getLogger("nightswitch.core.location_mode")
        self._location_service = location_service or get_location_service()
        self._sunrise_sunset_service = sunrise_sunset_service or get_sunrise_sunset_service()
        self._theme_callback = theme_callback
        
        # State tracking
        self._is_enabled = False
        self._current_location: Optional[Tuple[float, float, str]] = None
        self._auto_location = True
        
        # Callbacks for status updates
        self._status_callbacks: list[Callable[[dict], None]] = []
        self._error_callbacks: list[Callable[[str, str], None]] = []

    def enable(
        self, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None
    ) -> bool:
        """
        Enable location mode with optional manual coordinates.
        
        Args:
            latitude: Manual latitude (optional, will auto-detect if not provided)
            longitude: Manual longitude (optional, will auto-detect if not provided)
            
        Returns:
            True if location mode was enabled successfully, False otherwise
        """
        try:
            # Determine location
            if latitude is not None and longitude is not None:
                # Use manual coordinates
                if not self._validate_coordinates(latitude, longitude):
                    self.logger.error(f"Invalid manual coordinates: {latitude}, {longitude}")
                    self._notify_error("invalid_coordinates", "Invalid latitude or longitude coordinates")
                    return False
                
                self._current_location = (latitude, longitude, f"Manual location ({latitude}, {longitude})")
                self._auto_location = False
                self.logger.info(f"Using manual location: {latitude}, {longitude}")
                
            else:
                # Auto-detect location
                location_result = self._location_service.get_current_location()
                if not location_result:
                    self.logger.error("Failed to detect location automatically")
                    self._notify_error("location_detection_failed", 
                                     "Could not detect your location automatically. Please provide manual coordinates.")
                    return False
                
                self._current_location = location_result
                self._auto_location = True
                lat, lon, description = location_result
                self.logger.info(f"Auto-detected location: {description} ({lat}, {lon})")
            
            # Set up sunrise/sunset scheduling
            lat, lon, description = self._current_location
            if not self._sunrise_sunset_service.schedule_sun_events(lat, lon, self._handle_sun_event):
                self.logger.error("Failed to set up sunrise/sunset scheduling")
                self._notify_error("scheduling_failed", "Failed to set up sunrise/sunset event scheduling")
                return False
            
            # Apply initial theme based on current sun period
            self._apply_initial_theme()
            
            # Update state
            self._is_enabled = True
            
            # Notify status callbacks
            self._notify_status_change()
            
            self.logger.info(f"Location mode enabled for {description}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable location mode: {e}")
            self._notify_error("enable_failed", f"Failed to enable location mode: {str(e)}")
            return False

    def disable(self) -> bool:
        """
        Disable location mode and stop automatic switching.
        
        Returns:
            True if location mode was disabled successfully, False otherwise
        """
        try:
            # Stop sunrise/sunset scheduling
            self._sunrise_sunset_service.stop_sun_events()
            
            # Update state
            self._is_enabled = False
            self._current_location = None
            self._auto_location = True
            
            # Notify status callbacks
            self._notify_status_change()
            
            self.logger.info("Location mode disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable location mode: {e}")
            return False

    def set_theme_callback(self, callback: Callable[[ThemeType], bool]) -> None:
        """
        Set the callback function for applying themes.
        
        Args:
            callback: Function that applies themes and returns success status
        """
        self._theme_callback = callback
        self.logger.debug("Theme callback set for location mode")

    def _handle_sun_event(self, event_type: str) -> None:
        """
        Handle sunrise/sunset events from the sunrise/sunset service.
        
        Args:
            event_type: Event type ('sunrise' or 'sunset')
        """
        try:
            # Convert event to theme
            if event_type == "sunrise":
                theme = ThemeType.LIGHT
                self.logger.info("Sunrise detected - switching to light theme")
            elif event_type == "sunset":
                theme = ThemeType.DARK
                self.logger.info("Sunset detected - switching to dark theme")
            else:
                self.logger.error(f"Invalid sun event type: {event_type}")
                return
            
            # Apply theme if callback is available
            if self._theme_callback:
                success = self._theme_callback(theme)
                if success:
                    self.logger.info(f"Successfully applied {theme.value} theme for {event_type}")
                else:
                    self.logger.error(f"Failed to apply {theme.value} theme for {event_type}")
                    self._notify_error("theme_application_failed", 
                                     f"Failed to apply {theme.value} theme during {event_type}")
            else:
                self.logger.warning("No theme callback available for sun event")
                
        except Exception as e:
            self.logger.error(f"Error handling sun event {event_type}: {e}")
            self._notify_error("sun_event_error", f"Error processing {event_type} event: {str(e)}")

    def _apply_initial_theme(self) -> None:
        """Apply initial theme based on current sun period."""
        try:
            if not self._current_location:
                return
            
            lat, lon, _ = self._current_location
            current_period = self._sunrise_sunset_service.get_current_sun_period(lat, lon)
            
            if current_period == "day":
                initial_theme = ThemeType.LIGHT
                self.logger.info("Currently daytime - applying light theme")
            elif current_period == "night":
                initial_theme = ThemeType.DARK
                self.logger.info("Currently nighttime - applying dark theme")
            else:
                self.logger.warning("Could not determine current sun period, skipping initial theme")
                return
            
            # Apply initial theme
            if self._theme_callback:
                success = self._theme_callback(initial_theme)
                if success:
                    self.logger.info(f"Applied initial {initial_theme.value} theme")
                else:
                    self.logger.warning(f"Failed to apply initial {initial_theme.value} theme")
            
        except Exception as e:
            self.logger.error(f"Error applying initial theme: {e}")

    def refresh_location(self) -> bool:
        """
        Refresh the current location (only works in auto-location mode).
        
        Returns:
            True if location was refreshed successfully, False otherwise
        """
        try:
            if not self._auto_location:
                self.logger.info("Cannot refresh location in manual mode")
                return False
            
            if not self._is_enabled:
                self.logger.info("Location mode not enabled")
                return False
            
            # Clear location cache and re-detect
            self._location_service.clear_cache()
            location_result = self._location_service.get_current_location()
            
            if not location_result:
                self.logger.error("Failed to refresh location")
                self._notify_error("location_refresh_failed", "Failed to refresh location")
                return False
            
            old_location = self._current_location
            self._current_location = location_result
            
            lat, lon, description = location_result
            self.logger.info(f"Location refreshed: {description} ({lat}, {lon})")
            
            # Update sunrise/sunset scheduling with new location
            self._sunrise_sunset_service.stop_sun_events()
            if not self._sunrise_sunset_service.schedule_sun_events(lat, lon, self._handle_sun_event):
                self.logger.error("Failed to update scheduling with new location")
                # Restore old location if possible
                if old_location:
                    self._current_location = old_location
                return False
            
            # Apply theme for new location
            self._apply_initial_theme()
            
            # Notify status callbacks
            self._notify_status_change()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing location: {e}")
            self._notify_error("location_refresh_error", f"Error refreshing location: {str(e)}")
            return False

    def get_current_location(self) -> Optional[Tuple[float, float, str]]:
        """
        Get the current location being used.
        
        Returns:
            Tuple of (latitude, longitude, description) or None if not set
        """
        return self._current_location

    def is_enabled(self) -> bool:
        """
        Check if location mode is currently enabled.
        
        Returns:
            True if location mode is enabled, False otherwise
        """
        return self._is_enabled

    def is_auto_location(self) -> bool:
        """
        Check if auto-location detection is being used.
        
        Returns:
            True if using auto-location, False if using manual coordinates
        """
        return self._auto_location

    def get_next_sun_event(self) -> Optional[Tuple[str, str, str]]:
        """
        Get information about the next sunrise/sunset event.
        
        Returns:
            Tuple of (event_time, event_type, event_date) or None if not available
        """
        try:
            if not self._current_location:
                return None
            
            lat, lon, _ = self._current_location
            next_event = self._sunrise_sunset_service.get_next_sun_event(lat, lon)
            
            if next_event:
                event_datetime, event_type = next_event
                return (
                    event_datetime.strftime("%H:%M"),
                    event_type,
                    event_datetime.date().isoformat()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting next sun event: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed status information about location mode.
        
        Returns:
            Dictionary with location mode status
        """
        status = {
            "enabled": self._is_enabled,
            "auto_location": self._auto_location,
            "has_theme_callback": self._theme_callback is not None,
        }
        
        # Add location info
        if self._current_location:
            lat, lon, description = self._current_location
            status["location"] = {
                "latitude": lat,
                "longitude": lon,
                "description": description
            }
        
        # Add service status
        try:
            status["location_service"] = self._location_service.get_location_info()
            status["sunrise_sunset_service"] = self._sunrise_sunset_service.get_service_status()
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            status["service_error"] = str(e)
        
        # Add next event info
        next_event = self.get_next_sun_event()
        if next_event:
            event_time, event_type, event_date = next_event
            status["next_event"] = {
                "time": event_time,
                "type": event_type,
                "date": event_date
            }
        
        return status

    def add_status_callback(self, callback: Callable[[dict], None]) -> None:
        """
        Add a callback for status change notifications.
        
        Args:
            callback: Function to call when status changes
        """
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable[[dict], None]) -> None:
        """
        Remove a status change callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def add_error_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Add a callback for error notifications.
        
        Args:
            callback: Function to call when errors occur (error_type, error_message)
        """
        self._error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Remove an error callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    def _notify_status_change(self) -> None:
        """Notify all registered callbacks about status changes."""
        status = self.get_status()
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")

    def _notify_error(self, error_type: str, error_message: str) -> None:
        """
        Notify all registered callbacks about errors.
        
        Args:
            error_type: Type of error that occurred
            error_message: Human-readable error message
        """
        for callback in self._error_callbacks:
            try:
                callback(error_type, error_message)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")

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

    def test_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to location and sunrise/sunset services.
        
        Returns:
            Dictionary with connectivity test results
        """
        try:
            results = {
                "location_service": self._location_service.test_connectivity(),
                "sunrise_sunset_service": self._sunrise_sunset_service.test_api_connectivity()
            }
            
            self.logger.info(f"Connectivity test results: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing connectivity: {e}")
            return {"location_service": False, "sunrise_sunset_service": False}

    def cleanup(self) -> None:
        """Clean up resources and disable location mode."""
        try:
            self.logger.info("Cleaning up location mode handler")
            
            # Disable location mode
            if self._is_enabled:
                self.disable()
            
            # Clear callbacks
            self._status_callbacks.clear()
            self._error_callbacks.clear()
            
            # Clean up services
            if self._sunrise_sunset_service:
                self._sunrise_sunset_service.cleanup()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global location mode handler instance
_location_mode_handler: Optional[LocationModeHandler] = None


def get_location_mode_handler() -> LocationModeHandler:
    """
    Get the global location mode handler instance.
    
    Returns:
        LocationModeHandler instance
    """
    global _location_mode_handler
    if _location_mode_handler is None:
        _location_mode_handler = LocationModeHandler()
    return _location_mode_handler