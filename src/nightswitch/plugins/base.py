"""
Base plugin interface for Nightswitch theme plugins.

This module defines the abstract base class that all theme plugins must implement
to provide desktop environment-specific theme switching functionality.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginInfo:
    """
    Plugin metadata and information.

    Contains essential information about a plugin including its name,
    version, compatibility requirements, and configuration.
    """

    name: str
    version: str
    description: str
    author: str
    desktop_environments: List[str]  # List of supported desktop environments
    priority: int = 50  # Higher priority plugins are preferred (0-100)
    requires_packages: List[str] = field(
        default_factory=list
    )  # System packages required
    config_schema: Dict[str, Any] = field(default_factory=dict)  # Configuration schema


class ThemePlugin(ABC):
    """
    Abstract base class for theme switching plugins.

    All theme plugins must inherit from this class and implement the required
    methods to provide desktop environment-specific theme switching functionality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin.

        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"nightswitch.plugins.{self.get_info().name}")
        self._is_initialized = False

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """
        Get plugin information and metadata.

        Returns:
            PluginInfo instance with plugin details
        """
        pass

    @abstractmethod
    def detect_compatibility(self) -> bool:
        """
        Check if this plugin is compatible with the current environment.

        This method should check for the presence of required desktop environment
        components, system packages, or other dependencies.

        Returns:
            True if plugin is compatible with current environment, False otherwise
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin for use.

        This method is called once when the plugin is selected for use.
        It should perform any necessary setup, validation, or resource allocation.

        Returns:
            True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up plugin resources.

        This method is called when the plugin is being unloaded or the
        application is shutting down. It should release any resources,
        cancel timers, or perform other cleanup tasks.
        """
        pass

    @abstractmethod
    def apply_dark_theme(self) -> bool:
        """
        Apply dark theme to the desktop environment.

        Returns:
            True if dark theme was applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def apply_light_theme(self) -> bool:
        """
        Apply light theme to the desktop environment.

        Returns:
            True if light theme was applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_current_theme(self) -> Optional[str]:
        """
        Get the current theme state from the desktop environment.

        Returns:
            'dark', 'light', or None if theme state cannot be determined
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        # Default implementation - plugins can override for custom validation
        return True

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this plugin.

        Returns:
            Dictionary describing the expected configuration structure
        """
        return self.get_info().config_schema

    def is_initialized(self) -> bool:
        """
        Check if the plugin has been initialized.

        Returns:
            True if plugin is initialized, False otherwise
        """
        return self._is_initialized

    def set_initialized(self, initialized: bool) -> None:
        """
        Set the plugin initialization state.

        Args:
            initialized: True if plugin is initialized, False otherwise
        """
        self._is_initialized = initialized

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def log_debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class PluginCompatibilityError(PluginError):
    """Raised when a plugin is not compatible with the current environment."""

    pass


class PluginInitializationError(PluginError):
    """Raised when plugin initialization fails."""

    pass


class PluginOperationError(PluginError):
    """Raised when a plugin operation fails."""

    pass
