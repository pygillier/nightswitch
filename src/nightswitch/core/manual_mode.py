"""
Manual mode handler for direct theme switching in Nightswitch.

This module provides the ManualModeHandler class that handles immediate
theme switching with visual feedback for manual user control.
"""

import logging
from typing import Callable, Optional

from enum import Enum
from ..plugins.manager import PluginManager, get_plugin_manager


class ThemeType(Enum):
    """Enumeration of theme types."""

    LIGHT = "light"
    DARK = "dark"


class ManualModeHandler:
    """
    Handler for manual theme switching mode.
    
    Provides immediate theme switching functionality with visual feedback
    and integrates with the plugin manager for theme application.
    """

    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        """
        Initialize the manual mode handler.
        
        Args:
            plugin_manager: Plugin manager instance for theme application
        """
        self.logger = logging.getLogger("nightswitch.core.manual_mode")
        self._plugin_manager = plugin_manager or get_plugin_manager()
        
        # Current state
        self._current_theme: Optional[ThemeType] = None
        self._is_enabled = True  # Manual mode is always available
        
        # Callbacks for theme changes and feedback
        self._theme_change_callbacks: list[Callable[[ThemeType], None]] = []
        self._feedback_callbacks: list[Callable[[str, bool], None]] = []

    def is_enabled(self) -> bool:
        """
        Check if manual mode is enabled.
        
        Returns:
            True (manual mode is always available)
        """
        return self._is_enabled

    def get_current_theme(self) -> Optional[ThemeType]:
        """
        Get the current theme type.
        
        Returns:
            Current ThemeType or None if not set
        """
        return self._current_theme

    def switch_to_dark(self) -> bool:
        """
        Switch to dark theme immediately.
        
        Returns:
            True if theme was applied successfully, False otherwise
        """
        return self._apply_theme(ThemeType.DARK)

    def switch_to_light(self) -> bool:
        """
        Switch to light theme immediately.
        
        Returns:
            True if theme was applied successfully, False otherwise
        """
        return self._apply_theme(ThemeType.LIGHT)

    def toggle_theme(self) -> bool:
        """
        Toggle between dark and light themes.
        
        Returns:
            True if theme was toggled successfully, False otherwise
        """
        if self._current_theme == ThemeType.DARK:
            return self.switch_to_light()
        else:
            return self.switch_to_dark()

    def _apply_theme(self, theme: ThemeType) -> bool:
        """
        Apply a theme using the active plugin with visual feedback.
        
        Args:
            theme: Theme type to apply
            
        Returns:
            True if theme was applied successfully, False otherwise
        """
        try:
            # Get active plugin
            active_plugin = self._plugin_manager.get_active_plugin()
            if not active_plugin:
                error_msg = "No active plugin available for theme switching"
                self.logger.error(error_msg)
                self._notify_feedback(error_msg, False)
                return False

            # Provide feedback that switching is starting
            self._notify_feedback(f"Switching to {theme.value} theme...", True)

            # Apply theme
            success = False
            if theme == ThemeType.DARK:
                success = active_plugin.apply_dark_theme()
            elif theme == ThemeType.LIGHT:
                success = active_plugin.apply_light_theme()

            if success:
                old_theme = self._current_theme
                self._current_theme = theme
                
                # Provide success feedback
                self._notify_feedback(f"Successfully switched to {theme.value} theme", True)
                
                # Notify theme change callbacks
                if old_theme != theme:
                    self._notify_theme_change(theme)
                
                self.logger.info(f"Applied {theme.value} theme successfully")
                return True
            else:
                error_msg = f"Failed to apply {theme.value} theme"
                self.logger.error(error_msg)
                self._notify_feedback(error_msg, False)
                return False

        except Exception as e:
            error_msg = f"Error applying {theme.value} theme: {e}"
            self.logger.error(error_msg)
            self._notify_feedback(error_msg, False)
            return False

    def get_available_themes(self) -> list[ThemeType]:
        """
        Get list of available themes.
        
        Returns:
            List of available ThemeType values
        """
        return [ThemeType.LIGHT, ThemeType.DARK]

    def is_theme_available(self, theme: ThemeType) -> bool:
        """
        Check if a specific theme is available.
        
        Args:
            theme: Theme to check
            
        Returns:
            True if theme is available, False otherwise
        """
        # Check if we have an active plugin
        active_plugin = self._plugin_manager.get_active_plugin()
        if not active_plugin:
            return False
            
        # All themes are available if we have a plugin
        return theme in self.get_available_themes()

    def get_plugin_status(self) -> dict:
        """
        Get status information about the active plugin.
        
        Returns:
            Dictionary with plugin status information
        """
        active_plugin = self._plugin_manager.get_active_plugin()
        plugin_name = self._plugin_manager.get_active_plugin_name()
        
        return {
            "has_active_plugin": active_plugin is not None,
            "plugin_name": plugin_name,
            "plugin_initialized": active_plugin.is_initialized() if active_plugin else False,
            "available_themes": [theme.value for theme in self.get_available_themes()],
            "current_theme": self._current_theme.value if self._current_theme else None,
        }

    def add_theme_change_callback(self, callback: Callable[[ThemeType], None]) -> None:
        """
        Add a callback for theme change events.
        
        Args:
            callback: Function to call when theme changes
        """
        if callback not in self._theme_change_callbacks:
            self._theme_change_callbacks.append(callback)

    def remove_theme_change_callback(self, callback: Callable[[ThemeType], None]) -> None:
        """
        Remove a theme change callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)

    def add_feedback_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Add a callback for visual feedback events.
        
        Args:
            callback: Function to call for feedback (message, success)
        """
        if callback not in self._feedback_callbacks:
            self._feedback_callbacks.append(callback)

    def remove_feedback_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Remove a feedback callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._feedback_callbacks:
            self._feedback_callbacks.remove(callback)

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

    def _notify_feedback(self, message: str, success: bool) -> None:
        """
        Notify all registered callbacks about feedback events.
        
        Args:
            message: Feedback message
            success: Whether the operation was successful
        """
        for callback in self._feedback_callbacks:
            try:
                callback(message, success)
            except Exception as e:
                self.logger.error(f"Error in feedback callback: {e}")

    def cleanup(self) -> None:
        """Clean up resources and clear callbacks."""
        try:
            # Clear callbacks
            self._theme_change_callbacks.clear()
            self._feedback_callbacks.clear()
            
            self.logger.info("Manual mode handler cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def get_status(self) -> dict:
        """
        Get detailed status information about manual mode.
        
        Returns:
            Dictionary with manual mode status information
        """
        plugin_status = self.get_plugin_status()
        
        return {
            "enabled": self._is_enabled,
            "current_theme": self._current_theme.value if self._current_theme else None,
            "available_themes": [theme.value for theme in self.get_available_themes()],
            "plugin_status": plugin_status,
            "callback_counts": {
                "theme_change": len(self._theme_change_callbacks),
                "feedback": len(self._feedback_callbacks),
            }
        }


# Global manual mode handler instance
_manual_mode_handler: Optional[ManualModeHandler] = None


def get_manual_mode_handler() -> ManualModeHandler:
    """
    Get the global manual mode handler instance.
    
    Returns:
        ManualModeHandler instance
    """
    global _manual_mode_handler
    if _manual_mode_handler is None:
        _manual_mode_handler = ManualModeHandler()
    return _manual_mode_handler