"""
Schedule mode handler for time-based theme switching in Nightswitch.

This module provides the ScheduleModeHandler class that integrates with the
ScheduleService to provide automatic theme switching based on user-defined schedules.
"""

import logging
from typing import Callable, Optional

from ..services.schedule import ScheduleService, get_schedule_service
from .manual_mode import ThemeType


class ScheduleModeHandler:
    """
    Handler for schedule-based automatic theme switching.
    
    Integrates with ScheduleService to provide time validation, scheduling,
    and theme switching coordination for schedule mode.
    """

    def __init__(
        self,
        schedule_service: Optional[ScheduleService] = None,
        theme_callback: Optional[Callable[[ThemeType], bool]] = None
    ):
        """
        Initialize the schedule mode handler.
        
        Args:
            schedule_service: Schedule service instance
            theme_callback: Callback function for applying themes
        """
        self.logger = logging.getLogger("nightswitch.core.schedule_mode")
        self._schedule_service = schedule_service or get_schedule_service()
        self._theme_callback = theme_callback
        
        # State tracking
        self._is_enabled = False
        self._dark_time: Optional[str] = None
        self._light_time: Optional[str] = None
        
        # Callbacks for status updates
        self._status_callbacks: list[Callable[[dict], None]] = []

    def enable(self, dark_time: str, light_time: str) -> bool:
        """
        Enable schedule mode with specified times.
        
        Args:
            dark_time: Time to switch to dark theme (HH:MM format)
            light_time: Time to switch to light theme (HH:MM format)
            
        Returns:
            True if schedule mode was enabled successfully, False otherwise
        """
        try:
            # Validate time formats
            if not self._validate_time_format(dark_time) or not self._validate_time_format(light_time):
                self.logger.error(f"Invalid time format: dark={dark_time}, light={light_time}")
                return False
            
            # Validate that times are different
            if dark_time == light_time:
                self.logger.error("Dark and light times cannot be the same")
                return False
            
            # Set up schedule with callback
            if not self._schedule_service.set_schedule(
                dark_time, light_time, self._handle_scheduled_theme_change
            ):
                self.logger.error("Failed to set schedule in service")
                return False
            
            # Update state
            self._is_enabled = True
            self._dark_time = dark_time
            self._light_time = light_time
            
            # Notify status callbacks
            self._notify_status_change()
            
            self.logger.info(f"Schedule mode enabled: dark={dark_time}, light={light_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable schedule mode: {e}")
            return False

    def disable(self) -> bool:
        """
        Disable schedule mode and stop automatic switching.
        
        Returns:
            True if schedule mode was disabled successfully, False otherwise
        """
        try:
            # Stop schedule service
            self._schedule_service.stop_schedule()
            
            # Update state
            self._is_enabled = False
            self._dark_time = None
            self._light_time = None
            
            # Notify status callbacks
            self._notify_status_change()
            
            self.logger.info("Schedule mode disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable schedule mode: {e}")
            return False

    def set_theme_callback(self, callback: Callable[[ThemeType], bool]) -> None:
        """
        Set the callback function for applying themes.
        
        Args:
            callback: Function that applies themes and returns success status
        """
        self._theme_callback = callback
        self.logger.debug("Theme callback set for schedule mode")

    def _handle_scheduled_theme_change(self, theme_str: str) -> None:
        """
        Handle scheduled theme changes from the schedule service.
        
        Args:
            theme_str: Theme string ('dark' or 'light')
        """
        try:
            # Convert string to ThemeType
            if theme_str == "dark":
                theme = ThemeType.DARK
            elif theme_str == "light":
                theme = ThemeType.LIGHT
            else:
                self.logger.error(f"Invalid theme string from schedule: {theme_str}")
                return
            
            self.logger.info(f"Applying scheduled theme change: {theme.value}")
            
            # Apply theme if callback is available
            if self._theme_callback:
                success = self._theme_callback(theme)
                if success:
                    self.logger.info(f"Successfully applied scheduled {theme.value} theme")
                else:
                    self.logger.error(f"Failed to apply scheduled {theme.value} theme")
            else:
                self.logger.warning("No theme callback available for scheduled change")
                
        except Exception as e:
            self.logger.error(f"Error handling scheduled theme change: {e}")

    def get_schedule_times(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get the current schedule times.
        
        Returns:
            Tuple of (dark_time, light_time) or (None, None) if not set
        """
        return (self._dark_time, self._light_time)

    def is_enabled(self) -> bool:
        """
        Check if schedule mode is currently enabled.
        
        Returns:
            True if schedule mode is enabled, False otherwise
        """
        return self._is_enabled

    def get_next_trigger(self) -> Optional[tuple[str, str]]:
        """
        Get information about the next scheduled trigger.
        
        Returns:
            Tuple of (time, theme) for next trigger, or None if no schedule
        """
        try:
            return self._schedule_service.get_next_trigger_time()
        except Exception as e:
            self.logger.error(f"Error getting next trigger: {e}")
            return None

    def get_status(self) -> dict:
        """
        Get detailed status information about schedule mode.
        
        Returns:
            Dictionary with schedule mode status
        """
        status = {
            "enabled": self._is_enabled,
            "dark_time": self._dark_time,
            "light_time": self._light_time,
            "has_theme_callback": self._theme_callback is not None,
        }
        
        # Add schedule service status
        try:
            service_status = self._schedule_service.get_schedule_status()
            status["service"] = service_status
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            status["service"] = {"error": str(e)}
        
        # Add next trigger info
        next_trigger = self.get_next_trigger()
        if next_trigger:
            status["next_trigger_time"] = next_trigger[0]
            status["next_trigger_theme"] = next_trigger[1]
        
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

    def _notify_status_change(self) -> None:
        """Notify all registered callbacks about status changes."""
        status = self.get_status()
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")

    def _validate_time_format(self, time_str: str) -> bool:
        """
        Validate time format (HH:MM).
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        import re
        from datetime import datetime
        
        # Check format with regex
        pattern = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
        if not pattern.match(time_str):
            return False
        
        # Additional validation by parsing
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def validate_schedule_times(self, dark_time: str, light_time: str) -> tuple[bool, Optional[str]]:
        """
        Validate schedule times and return detailed error information.
        
        Args:
            dark_time: Dark theme time string
            light_time: Light theme time string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check time formats
            if not self._validate_time_format(dark_time):
                return (False, f"Invalid dark time format: {dark_time}")
            
            if not self._validate_time_format(light_time):
                return (False, f"Invalid light time format: {light_time}")
            
            # Check that times are different
            if dark_time == light_time:
                return (False, "Dark and light times cannot be the same")
            
            return (True, None)
            
        except Exception as e:
            return (False, f"Validation error: {e}")

    def cleanup(self) -> None:
        """Clean up resources and disable schedule mode."""
        try:
            self.logger.info("Cleaning up schedule mode handler")
            
            # Disable schedule mode
            if self._is_enabled:
                self.disable()
            
            # Clear callbacks
            self._status_callbacks.clear()
            
            # Clean up schedule service
            if self._schedule_service:
                self._schedule_service.cleanup()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global schedule mode handler instance
_schedule_mode_handler: Optional[ScheduleModeHandler] = None


def get_schedule_mode_handler() -> ScheduleModeHandler:
    """
    Get the global schedule mode handler instance.
    
    Returns:
        ScheduleModeHandler instance
    """
    global _schedule_mode_handler
    if _schedule_mode_handler is None:
        _schedule_mode_handler = ScheduleModeHandler()
    return _schedule_mode_handler