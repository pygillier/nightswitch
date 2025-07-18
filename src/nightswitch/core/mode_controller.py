"""
Mode controller for coordinating theme switching modes in Nightswitch.

This module provides the ModeController class that manages different theme
switching modes (manual, schedule, location) and handles mode conflicts.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional

from ..plugins.manager import PluginManager, get_plugin_manager
from .config import AppConfig, ConfigManager, get_config
from .manual_mode import ManualModeHandler, get_manual_mode_handler, ThemeType
from .schedule_mode import ScheduleModeHandler, get_schedule_mode_handler
from .location_mode import LocationModeHandler, get_location_mode_handler


class ThemeMode(Enum):
    """Enumeration of available theme switching modes."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    LOCATION = "location"


class ModeController:
    """
    Controller for managing theme switching modes and coordinating theme changes.

    Handles mode switching, conflict resolution, and state management for the
    different theme switching modes available in Nightswitch.
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        plugin_manager: Optional[PluginManager] = None,
        manual_mode_handler: Optional[ManualModeHandler] = None,
        schedule_mode_handler: Optional[ScheduleModeHandler] = None,
        location_mode_handler: Optional[LocationModeHandler] = None,
    ):
        """
        Initialize the mode controller.

        Args:
            config_manager: Configuration manager instance
            plugin_manager: Plugin manager instance
            manual_mode_handler: Manual mode handler instance
            schedule_mode_handler: Schedule mode handler instance
        """
        self.logger = logging.getLogger("nightswitch.core.mode_controller")
        self._config_manager = config_manager or get_config()
        self._plugin_manager = plugin_manager or get_plugin_manager()
        self._manual_mode_handler = manual_mode_handler or get_manual_mode_handler()
        self._schedule_mode_handler = schedule_mode_handler or get_schedule_mode_handler()
        self._location_mode_handler = location_mode_handler or get_location_mode_handler()

        # Current state
        self._current_mode: Optional[ThemeMode] = None
        self._current_theme: Optional[ThemeType] = None
        self._mode_handlers: Dict[ThemeMode, Any] = {}
        self._active_handler: Optional[Any] = None

        # Callbacks for mode changes
        self._mode_change_callbacks: list[
            Callable[[ThemeMode, Optional[ThemeMode]], None]
        ] = []
        self._theme_change_callbacks: list[Callable[[ThemeType], None]] = []

        # Initialize from configuration
        self._load_state_from_config()
        
        # Set up mode handlers
        self._setup_mode_handlers()
        
        # Set up manual mode handler callbacks
        self._setup_manual_mode_callbacks()

    def _load_state_from_config(self) -> None:
        """Load current state from configuration."""
        try:
            config = self._config_manager.get_app_config()

            # Set current mode
            if config.current_mode in [mode.value for mode in ThemeMode]:
                self._current_mode = ThemeMode(config.current_mode)
            else:
                self._current_mode = ThemeMode.MANUAL
                self.logger.warning(
                    f"Invalid mode in config: {config.current_mode}, defaulting to manual"
                )

            # Set current theme
            if config.manual_theme in [theme.value for theme in ThemeType]:
                self._current_theme = ThemeType(config.manual_theme)
            else:
                self._current_theme = ThemeType.LIGHT
                self.logger.warning(
                    f"Invalid theme in config: {config.manual_theme}, defaulting to light"
                )

            # Update state tracking
            self._config_manager.update_last_mode(self._current_mode.value)
            self._config_manager.update_last_theme(self._current_theme.value)

            self.logger.info(
                f"Loaded state: mode={self._current_mode.value}, theme={self._current_theme.value}"
            )

        except Exception as e:
            self.logger.error(f"Failed to load state from config: {e}")
            self._current_mode = ThemeMode.MANUAL
            self._current_theme = ThemeType.LIGHT

    def _save_state_to_config(self) -> None:
        """Save current state to configuration."""
        try:
            config = self._config_manager.get_app_config()

            if self._current_mode:
                config.current_mode = self._current_mode.value

            if self._current_theme:
                config.manual_theme = self._current_theme.value

            self._config_manager.set_app_config(config)
            self.logger.debug("Saved state to configuration")

        except Exception as e:
            self.logger.error(f"Failed to save state to config: {e}")

    def _setup_mode_handlers(self) -> None:
        """Set up mode handlers and their callbacks."""
        try:
            # Register schedule mode handler
            self.register_mode_handler(ThemeMode.SCHEDULE, self._schedule_mode_handler)
            
            # Set up theme callback for schedule mode handler
            self._schedule_mode_handler.set_theme_callback(self.apply_theme)
            
            # Register location mode handler
            self.register_mode_handler(ThemeMode.LOCATION, self._location_mode_handler)
            
            # Set up theme callback for location mode handler
            self._location_mode_handler.set_theme_callback(self.apply_theme)
            
            self.logger.debug("Set up mode handlers")
            
        except Exception as e:
            self.logger.error(f"Failed to set up mode handlers: {e}")

    def _setup_manual_mode_callbacks(self) -> None:
        """Set up callbacks for manual mode handler integration."""
        try:
            # Add theme change callback to sync with manual mode handler
            def sync_theme_with_manual_handler(theme: ThemeType) -> None:
                """Sync theme changes with manual mode handler."""
                if self._current_mode == ThemeMode.MANUAL:
                    self._manual_mode_handler._current_theme = theme

            self._manual_mode_handler.add_theme_change_callback(sync_theme_with_manual_handler)
            
            self.logger.debug("Set up manual mode handler callbacks")
            
        except Exception as e:
            self.logger.error(f"Failed to set up manual mode callbacks: {e}")

    def register_mode_handler(self, mode: ThemeMode, handler: Any) -> None:
        """
        Register a handler for a specific mode.

        Args:
            mode: The theme mode
            handler: Handler instance for the mode
        """
        self._mode_handlers[mode] = handler
        self.logger.info(f"Registered handler for mode: {mode.value}")

    def unregister_mode_handler(self, mode: ThemeMode) -> None:
        """
        Unregister a handler for a specific mode.

        Args:
            mode: The theme mode to unregister
        """
        if mode in self._mode_handlers:
            # Disable the mode if it's currently active
            if self._current_mode == mode:
                self.set_manual_mode()

            del self._mode_handlers[mode]
            self.logger.info(f"Unregistered handler for mode: {mode.value}")

    def get_current_mode(self) -> Optional[ThemeMode]:
        """
        Get the current active mode.

        Returns:
            Current ThemeMode or None if not set
        """
        return self._current_mode

    def get_current_theme(self) -> Optional[ThemeType]:
        """
        Get the current theme type.

        Returns:
            Current ThemeType or None if not set
        """
        return self._current_theme

    def set_manual_mode(self, theme: Optional[ThemeType] = None) -> bool:
        """
        Switch to manual mode and optionally apply a theme.

        Args:
            theme: Theme to apply (optional)

        Returns:
            True if mode was set successfully, False otherwise
        """
        try:
            # Disable current mode handler if active
            if self._active_handler and hasattr(self._active_handler, "disable"):
                self._active_handler.disable()
                self._active_handler = None

            # Set manual mode
            old_mode = self._current_mode
            self._current_mode = ThemeMode.MANUAL

            # Apply theme if specified
            if theme:
                if not self.apply_theme(theme):
                    self.logger.error("Failed to apply theme in manual mode")
                    return False

            # Save state
            self._save_state_to_config()

            # Notify callbacks
            self._notify_mode_change(old_mode, self._current_mode)

            self.logger.info(
                f"Switched to manual mode with theme: {self._current_theme.value if self._current_theme else 'unchanged'}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set manual mode: {e}")
            return False

    def manual_switch_to_dark(self) -> bool:
        """
        Immediately switch to dark theme using manual mode.
        
        This method ensures manual mode is active and applies dark theme
        with visual feedback through the manual mode handler.

        Returns:
            True if theme was applied successfully, False otherwise
        """
        try:
            # Ensure we're in manual mode
            if self._current_mode != ThemeMode.MANUAL:
                if not self.set_manual_mode():
                    return False

            # Use manual mode handler for immediate switching with feedback
            return self._manual_mode_handler.switch_to_dark()

        except Exception as e:
            self.logger.error(f"Failed to manually switch to dark theme: {e}")
            return False

    def manual_switch_to_light(self) -> bool:
        """
        Immediately switch to light theme using manual mode.
        
        This method ensures manual mode is active and applies light theme
        with visual feedback through the manual mode handler.

        Returns:
            True if theme was applied successfully, False otherwise
        """
        try:
            # Ensure we're in manual mode
            if self._current_mode != ThemeMode.MANUAL:
                if not self.set_manual_mode():
                    return False

            # Use manual mode handler for immediate switching with feedback
            return self._manual_mode_handler.switch_to_light()

        except Exception as e:
            self.logger.error(f"Failed to manually switch to light theme: {e}")
            return False

    def manual_toggle_theme(self) -> bool:
        """
        Toggle between dark and light themes using manual mode.
        
        This method ensures manual mode is active and toggles the theme
        with visual feedback through the manual mode handler.

        Returns:
            True if theme was toggled successfully, False otherwise
        """
        try:
            # Ensure we're in manual mode
            if self._current_mode != ThemeMode.MANUAL:
                if not self.set_manual_mode():
                    return False

            # Use manual mode handler for immediate toggling with feedback
            return self._manual_mode_handler.toggle_theme()

        except Exception as e:
            self.logger.error(f"Failed to manually toggle theme: {e}")
            return False

    def get_manual_mode_handler(self) -> ManualModeHandler:
        """
        Get the manual mode handler instance.
        
        Returns:
            ManualModeHandler instance
        """
        return self._manual_mode_handler

    def set_schedule_mode(self, dark_time: str, light_time: str) -> bool:
        """
        Switch to schedule mode with specified times.

        Args:
            dark_time: Time to switch to dark theme (HH:MM format)
            light_time: Time to switch to light theme (HH:MM format)

        Returns:
            True if mode was set successfully, False otherwise
        """
        try:
            # Validate time format
            if not self._validate_time_format(
                dark_time
            ) or not self._validate_time_format(light_time):
                self.logger.error("Invalid time format for schedule mode")
                return False

            # Check if schedule handler is available
            if ThemeMode.SCHEDULE not in self._mode_handlers:
                self.logger.error("Schedule mode handler not available")
                return False

            # Disable current mode handler if active
            if self._active_handler and hasattr(self._active_handler, "disable"):
                self._active_handler.disable()

            # Set schedule mode
            old_mode = self._current_mode
            self._current_mode = ThemeMode.SCHEDULE

            # Enable schedule handler
            schedule_handler = self._mode_handlers[ThemeMode.SCHEDULE]
            if hasattr(schedule_handler, "enable"):
                if not schedule_handler.enable(dark_time, light_time):
                    self.logger.error("Failed to enable schedule handler")
                    return False

            self._active_handler = schedule_handler

            # Update configuration
            config = self._config_manager.get_app_config()
            config.schedule_enabled = True
            config.dark_time = dark_time
            config.light_time = light_time
            self._config_manager.set_app_config(config)

            # Save state
            self._save_state_to_config()

            # Notify callbacks
            self._notify_mode_change(old_mode, self._current_mode)

            self.logger.info(
                f"Switched to schedule mode: dark={dark_time}, light={light_time}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set schedule mode: {e}")
            return False

    def set_location_mode(
        self, latitude: Optional[float] = None, longitude: Optional[float] = None
    ) -> bool:
        """
        Switch to location mode with optional coordinates.

        Args:
            latitude: Latitude coordinate (optional, will auto-detect if not provided)
            longitude: Longitude coordinate (optional, will auto-detect if not provided)

        Returns:
            True if mode was set successfully, False otherwise
        """
        try:
            # Check if location handler is available
            if ThemeMode.LOCATION not in self._mode_handlers:
                self.logger.error("Location mode handler not available")
                return False

            # Validate coordinates if provided
            if latitude is not None and longitude is not None:
                if not self._validate_coordinates(latitude, longitude):
                    self.logger.error("Invalid coordinates for location mode")
                    return False

            # Disable current mode handler if active
            if self._active_handler and hasattr(self._active_handler, "disable"):
                self._active_handler.disable()

            # Set location mode
            old_mode = self._current_mode
            self._current_mode = ThemeMode.LOCATION

            # Enable location handler
            location_handler = self._mode_handlers[ThemeMode.LOCATION]
            if hasattr(location_handler, "enable"):
                if not location_handler.enable(latitude, longitude):
                    self.logger.error("Failed to enable location handler")
                    return False

            self._active_handler = location_handler

            # Update configuration
            config = self._config_manager.get_app_config()
            config.location_enabled = True
            if latitude is not None and longitude is not None:
                config.latitude = latitude
                config.longitude = longitude
                config.auto_location = False
            else:
                config.auto_location = True
            self._config_manager.set_app_config(config)

            # Save state
            self._save_state_to_config()

            # Notify callbacks
            self._notify_mode_change(old_mode, self._current_mode)

            self.logger.info(
                f"Switched to location mode: lat={latitude}, lon={longitude}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set location mode: {e}")
            return False

    def apply_theme(self, theme: ThemeType) -> bool:
        """
        Apply a theme using the active plugin.

        Args:
            theme: Theme type to apply

        Returns:
            True if theme was applied successfully, False otherwise
        """
        try:
            # Get active plugin
            active_plugin = self._plugin_manager.get_active_plugin()
            if not active_plugin:
                self.logger.error("No active plugin available for theme switching")
                return False

            # Apply theme
            success = False
            if theme == ThemeType.DARK:
                success = active_plugin.apply_dark_theme()
            elif theme == ThemeType.LIGHT:
                success = active_plugin.apply_light_theme()

            if success:
                old_theme = self._current_theme
                self._current_theme = theme
                self._save_state_to_config()

                # Notify callbacks
                if old_theme != theme:
                    self._notify_theme_change(theme)

                self.logger.info(f"Applied {theme.value} theme successfully")
                return True
            else:
                self.logger.error(f"Failed to apply {theme.value} theme")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply theme {theme.value}: {e}")
            return False

    def get_available_modes(self) -> list[ThemeMode]:
        """
        Get list of available modes based on registered handlers.

        Returns:
            List of available ThemeMode values
        """
        available = [ThemeMode.MANUAL]  # Manual mode is always available
        available.extend(self._mode_handlers.keys())
        return list(set(available))  # Remove duplicates

    def is_mode_active(self, mode: ThemeMode) -> bool:
        """
        Check if a specific mode is currently active.

        Args:
            mode: Mode to check

        Returns:
            True if mode is active, False otherwise
        """
        return self._current_mode == mode

    def disable_current_mode(self) -> bool:
        """
        Disable the current mode and switch to manual mode.

        Returns:
            True if mode was disabled successfully, False otherwise
        """
        if self._current_mode == ThemeMode.MANUAL:
            self.logger.info("Already in manual mode")
            return True

        return self.set_manual_mode()

    def add_mode_change_callback(
        self, callback: Callable[[ThemeMode, Optional[ThemeMode]], None]
    ) -> None:
        """
        Add a callback for mode change events.

        Args:
            callback: Function to call when mode changes (old_mode, new_mode)
        """
        self._mode_change_callbacks.append(callback)

    def remove_mode_change_callback(
        self, callback: Callable[[ThemeMode, Optional[ThemeMode]], None]
    ) -> None:
        """
        Remove a mode change callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._mode_change_callbacks:
            self._mode_change_callbacks.remove(callback)

    def add_theme_change_callback(self, callback: Callable[[ThemeType], None]) -> None:
        """
        Add a callback for theme change events.

        Args:
            callback: Function to call when theme changes
        """
        self._theme_change_callbacks.append(callback)

    def remove_theme_change_callback(
        self, callback: Callable[[ThemeType], None]
    ) -> None:
        """
        Remove a theme change callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)

    def _notify_mode_change(
        self, old_mode: Optional[ThemeMode], new_mode: ThemeMode
    ) -> None:
        """
        Notify all registered callbacks about mode change.

        Args:
            old_mode: Previous mode
            new_mode: New mode
        """
        for callback in self._mode_change_callbacks:
            try:
                callback(new_mode, old_mode)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")

    def _notify_theme_change(self, theme: ThemeType) -> None:
        """
        Notify all registered callbacks about theme change.

        Args:
            theme: New theme
        """
        for callback in self._theme_change_callbacks:
            try:
                callback(theme)
            except Exception as e:
                self.logger.error(f"Error in theme change callback: {e}")

    def _validate_time_format(self, time_str: str) -> bool:
        """
        Validate time format (HH:MM).

        Args:
            time_str: Time string to validate

        Returns:
            True if format is valid, False otherwise
        """
        import re

        pattern = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
        return bool(pattern.match(time_str))

    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates.

        Args:
            latitude: Latitude value
            longitude: Longitude value

        Returns:
            True if coordinates are valid, False otherwise
        """
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)

    def get_mode_status(self) -> Dict[str, Any]:
        """
        Get detailed status information about current mode and settings.

        Returns:
            Dictionary with mode status information
        """
        status = {
            "current_mode": self._current_mode.value if self._current_mode else None,
            "current_theme": self._current_theme.value if self._current_theme else None,
            "available_modes": [mode.value for mode in self.get_available_modes()],
            "active_handler": (
                self._active_handler.__class__.__name__
                if self._active_handler
                else None
            ),
            "plugin_active": self._plugin_manager.get_active_plugin_name(),
        }

        # Add mode-specific status
        try:
            config = self._config_manager.get_app_config()

            if self._current_mode == ThemeMode.SCHEDULE:
                status["schedule"] = {
                    "enabled": config.schedule_enabled,
                    "dark_time": config.dark_time,
                    "light_time": config.light_time,
                }

            elif self._current_mode == ThemeMode.LOCATION:
                status["location"] = {
                    "enabled": config.location_enabled,
                    "latitude": config.latitude,
                    "longitude": config.longitude,
                    "auto_location": config.auto_location,
                }

        except Exception as e:
            self.logger.error(f"Failed to get mode-specific status: {e}")

        return status

    def cleanup(self) -> None:
        """Clean up resources and disable active handlers."""
        try:
            # Disable active handler
            if self._active_handler and hasattr(self._active_handler, "disable"):
                self._active_handler.disable()
                self._active_handler = None

            # Clear callbacks
            self._mode_change_callbacks.clear()
            self._theme_change_callbacks.clear()

            self.logger.info("Mode controller cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global mode controller instance
_mode_controller: Optional[ModeController] = None


def get_mode_controller() -> ModeController:
    """
    Get the global mode controller instance.

    Returns:
        ModeController instance
    """
    global _mode_controller
    if _mode_controller is None:
        _mode_controller = ModeController()
    return _mode_controller
