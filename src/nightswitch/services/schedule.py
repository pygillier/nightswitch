"""
Schedule service for time-based theme switching in Nightswitch.

This module provides the ScheduleService class that handles recurring timer
functionality for automatic theme changes based on user-defined schedules.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple


class ScheduleService:
    """
    Service for managing time-based theme switching schedules.
    
    Provides recurring timer functionality for automatic theme changes
    with precise timing and error handling.
    """

    def __init__(self):
        """Initialize the schedule service."""
        self.logger = logging.getLogger("nightswitch.services.schedule")
        
        # Schedule state
        self._dark_time: Optional[str] = None
        self._light_time: Optional[str] = None
        self._callback: Optional[Callable[[str], None]] = None
        
        # Timer management
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        
        # Lock for thread safety
        self._lock = threading.Lock()

    def set_schedule(
        self, 
        dark_time: str, 
        light_time: str, 
        callback: Callable[[str], None]
    ) -> bool:
        """
        Set up recurring theme switches at specified times.
        
        Args:
            dark_time: Time to switch to dark theme (HH:MM format)
            light_time: Time to switch to light theme (HH:MM format)
            callback: Function to call for theme changes (receives 'dark' or 'light')
            
        Returns:
            True if schedule was set successfully, False otherwise
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
            
            with self._lock:
                # Stop existing schedule
                self._stop_schedule_internal()
                
                # Set new schedule
                self._dark_time = dark_time
                self._light_time = light_time
                self._callback = callback
                
                # Start timer thread
                self._start_timer_thread()
                
            self.logger.info(f"Schedule set: dark={dark_time}, light={light_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set schedule: {e}")
            return False

    def stop_schedule(self) -> None:
        """Stop the current schedule and cancel all timers."""
        with self._lock:
            self._stop_schedule_internal()
        self.logger.info("Schedule stopped")

    def _stop_schedule_internal(self) -> None:
        """Internal method to stop schedule (assumes lock is held)."""
        if self._is_running:
            self._stop_event.set()
            self._is_running = False
            
            # Wait for timer thread to finish
            if self._timer_thread and self._timer_thread.is_alive():
                self._timer_thread.join(timeout=2.0)
                
            self._timer_thread = None
            self._stop_event.clear()

    def _start_timer_thread(self) -> None:
        """Start the timer thread for schedule monitoring."""
        self._stop_event.clear()
        self._is_running = True
        self._timer_thread = threading.Thread(
            target=self._timer_loop,
            name="ScheduleTimer",
            daemon=True
        )
        self._timer_thread.start()

    def _timer_loop(self) -> None:
        """Main timer loop that monitors for scheduled theme changes."""
        self.logger.debug("Schedule timer loop started")
        
        last_check_minute = -1
        
        while not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                current_minute = current_time.hour * 60 + current_time.minute
                
                # Only check once per minute to avoid duplicate triggers
                if current_minute != last_check_minute:
                    last_check_minute = current_minute
                    self._check_schedule_triggers(current_time)
                
                # Sleep for a short interval to avoid busy waiting
                # but still maintain reasonable accuracy
                self._stop_event.wait(timeout=10.0)
                
            except Exception as e:
                self.logger.error(f"Error in timer loop: {e}")
                # Continue running even if there's an error
                self._stop_event.wait(timeout=30.0)
        
        self.logger.debug("Schedule timer loop stopped")

    def _check_schedule_triggers(self, current_time: datetime) -> None:
        """
        Check if current time matches any scheduled theme changes.
        
        Args:
            current_time: Current datetime to check against schedule
        """
        try:
            current_time_str = current_time.strftime("%H:%M")
            
            # Check for dark theme trigger
            if self._dark_time and current_time_str == self._dark_time:
                self.logger.info(f"Triggering dark theme at {current_time_str}")
                if self._callback:
                    try:
                        self._callback("dark")
                    except Exception as e:
                        self.logger.error(f"Error in dark theme callback: {e}")
            
            # Check for light theme trigger
            elif self._light_time and current_time_str == self._light_time:
                self.logger.info(f"Triggering light theme at {current_time_str}")
                if self._callback:
                    try:
                        self._callback("light")
                    except Exception as e:
                        self.logger.error(f"Error in light theme callback: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error checking schedule triggers: {e}")

    def get_next_trigger_time(self) -> Optional[Tuple[str, str]]:
        """
        Get the next scheduled trigger time and theme.
        
        Returns:
            Tuple of (time_string, theme) for next trigger, or None if no schedule
        """
        try:
            if not self._dark_time or not self._light_time:
                return None
            
            current_time = datetime.now()
            current_minutes = current_time.hour * 60 + current_time.minute
            
            # Parse schedule times
            dark_minutes = self._time_to_minutes(self._dark_time)
            light_minutes = self._time_to_minutes(self._light_time)
            
            # Find next trigger
            triggers = [
                (dark_minutes, self._dark_time, "dark"),
                (light_minutes, self._light_time, "light")
            ]
            
            # Sort by time
            triggers.sort(key=lambda x: x[0])
            
            # Find next trigger after current time
            for minutes, time_str, theme in triggers:
                if minutes > current_minutes:
                    return (time_str, theme)
            
            # If no trigger today, return first trigger tomorrow
            return (triggers[0][1], triggers[0][2])
            
        except Exception as e:
            self.logger.error(f"Error getting next trigger time: {e}")
            return None

    def get_schedule_status(self) -> dict:
        """
        Get current schedule status information.
        
        Returns:
            Dictionary with schedule status details
        """
        with self._lock:
            status = {
                "is_running": self._is_running,
                "dark_time": self._dark_time,
                "light_time": self._light_time,
                "has_callback": self._callback is not None,
                "thread_alive": self._timer_thread.is_alive() if self._timer_thread else False
            }
            
            # Add next trigger info
            next_trigger = self.get_next_trigger_time()
            if next_trigger:
                status["next_trigger_time"] = next_trigger[0]
                status["next_trigger_theme"] = next_trigger[1]
            
            return status

    def _validate_time_format(self, time_str: str) -> bool:
        """
        Validate time format (HH:MM).
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        import re
        
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

    def _time_to_minutes(self, time_str: str) -> int:
        """
        Convert time string to minutes since midnight.
        
        Args:
            time_str: Time in HH:MM format
            
        Returns:
            Minutes since midnight
        """
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except ValueError:
            return 0

    def is_running(self) -> bool:
        """
        Check if schedule service is currently running.
        
        Returns:
            True if service is running, False otherwise
        """
        with self._lock:
            return self._is_running

    def cleanup(self) -> None:
        """Clean up resources and stop all timers."""
        self.logger.info("Cleaning up schedule service")
        self.stop_schedule()


# Global schedule service instance
_schedule_service: Optional[ScheduleService] = None


def get_schedule_service() -> ScheduleService:
    """
    Get the global schedule service instance.
    
    Returns:
        ScheduleService instance
    """
    global _schedule_service
    if _schedule_service is None:
        _schedule_service = ScheduleService()
    return _schedule_service