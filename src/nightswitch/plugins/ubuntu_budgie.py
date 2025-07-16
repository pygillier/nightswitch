"""
Ubuntu Budgie theme plugin for Nightswitch.

This plugin provides theme switching functionality for Ubuntu Budgie desktop
environment using gsettings to control the color scheme preference.
"""

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from .base import PluginError, PluginInfo, PluginOperationError, ThemePlugin


class UbuntuBudgiePlugin(ThemePlugin):
    """
    Theme plugin for Ubuntu Budgie desktop environment.

    Uses gsettings to control the 'org.gnome.desktop.interface color-scheme'
    setting to switch between light and dark themes.
    """

    GSETTINGS_SCHEMA = "org.gnome.desktop.interface"
    GSETTINGS_KEY = "color-scheme"
    DARK_VALUE = "prefer-dark"
    LIGHT_VALUE = "default"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Ubuntu Budgie plugin."""
        super().__init__(config)
        self._gsettings_available = False
        self._schema_available = False

    def get_info(self) -> PluginInfo:
        """Get plugin information and metadata."""
        return PluginInfo(
            name="ubuntu_budgie",
            version="1.0.0",
            description="Theme switching plugin for Ubuntu Budgie desktop environment",
            author="Nightswitch Team",
            desktop_environments=["budgie", "ubuntu:budgie", "budgie-desktop"],
            priority=90,  # High priority for Ubuntu Budgie
            requires_packages=["gsettings", "budgie-desktop"],
            config_schema={
                "gsettings_schema": {
                    "type": "string",
                    "default": self.GSETTINGS_SCHEMA,
                    "description": "GSettings schema for color scheme",
                },
                "gsettings_key": {
                    "type": "string",
                    "default": self.GSETTINGS_KEY,
                    "description": "GSettings key for color scheme",
                },
            },
        )

    def detect_compatibility(self) -> bool:
        """
        Check if this plugin is compatible with the current environment.

        Checks for:
        1. Ubuntu Budgie desktop environment
        2. gsettings command availability
        3. Required GSettings schema availability

        Returns:
            True if compatible, False otherwise
        """
        try:
            # Check if gsettings command is available
            if not shutil.which("gsettings"):
                self.log_debug("gsettings command not found")
                return False

            # Check desktop environment
            if not self._is_budgie_desktop():
                self.log_debug("Not running Ubuntu Budgie desktop environment")
                return False

            # Check if the required GSettings schema is available
            if not self._check_gsettings_schema():
                self.log_debug(
                    f"GSettings schema '{self.GSETTINGS_SCHEMA}' not available"
                )
                return False

            self.log_info("Ubuntu Budgie plugin is compatible with current environment")
            return True

        except Exception as e:
            self.log_error(f"Error during compatibility check: {e}")
            return False

    def initialize(self) -> bool:
        """
        Initialize the plugin for use.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self._is_initialized:
                return True

            # Verify gsettings is available
            if not shutil.which("gsettings"):
                raise PluginOperationError("gsettings command not available")

            # Verify schema is available
            if not self._check_gsettings_schema():
                raise PluginOperationError(
                    f"GSettings schema '{self.GSETTINGS_SCHEMA}' not available"
                )

            self._gsettings_available = True
            self._schema_available = True
            self.set_initialized(True)

            self.log_info("Ubuntu Budgie plugin initialized successfully")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize Ubuntu Budgie plugin: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        self._gsettings_available = False
        self._schema_available = False
        self.set_initialized(False)
        self.log_info("Ubuntu Budgie plugin cleaned up")

    def apply_dark_theme(self) -> bool:
        """
        Apply dark theme to Ubuntu Budgie desktop.

        Returns:
            True if dark theme applied successfully, False otherwise
        """
        try:
            if not self._is_initialized:
                raise PluginOperationError("Plugin not initialized")

            result = self._set_gsettings_value(self.DARK_VALUE)
            if result:
                self.log_info("Dark theme applied successfully")
            else:
                self.log_error("Failed to apply dark theme")

            return result

        except Exception as e:
            self.log_error(f"Error applying dark theme: {e}")
            return False

    def apply_light_theme(self) -> bool:
        """
        Apply light theme to Ubuntu Budgie desktop.

        Returns:
            True if light theme applied successfully, False otherwise
        """
        try:
            if not self._is_initialized:
                raise PluginOperationError("Plugin not initialized")

            result = self._set_gsettings_value(self.LIGHT_VALUE)
            if result:
                self.log_info("Light theme applied successfully")
            else:
                self.log_error("Failed to apply light theme")

            return result

        except Exception as e:
            self.log_error(f"Error applying light theme: {e}")
            return False

    def get_current_theme(self) -> Optional[str]:
        """
        Get the current theme state from Ubuntu Budgie desktop.

        Returns:
            'dark', 'light', or None if theme state cannot be determined
        """
        try:
            if not self._is_initialized:
                self.log_warning("Plugin not initialized, cannot get current theme")
                return None

            current_value = self._get_gsettings_value()
            if current_value is None:
                return None

            if current_value == self.DARK_VALUE:
                return "dark"
            elif current_value == self.LIGHT_VALUE:
                return "light"
            else:
                self.log_warning(f"Unknown color scheme value: {current_value}")
                return None

        except Exception as e:
            self.log_error(f"Error getting current theme: {e}")
            return None

    def _is_budgie_desktop(self) -> bool:
        """
        Check if the current desktop environment is Ubuntu Budgie.

        Returns:
            True if running Ubuntu Budgie, False otherwise
        """
        # Check common environment variables
        desktop_env_vars = [
            "XDG_CURRENT_DESKTOP",
            "DESKTOP_SESSION",
            "XDG_SESSION_DESKTOP",
        ]

        budgie_identifiers = ["budgie", "ubuntu:budgie", "budgie-desktop", "Budgie"]

        for var in desktop_env_vars:
            value = os.environ.get(var, "").lower()
            if any(identifier.lower() in value for identifier in budgie_identifiers):
                self.log_debug(f"Detected Budgie desktop via {var}={value}")
                return True

        # Check if budgie-panel process is running
        try:
            result = subprocess.run(
                ["pgrep", "-f", "budgie-panel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.log_debug("Detected Budgie desktop via budgie-panel process")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False

    def _check_gsettings_schema(self) -> bool:
        """
        Check if the required GSettings schema is available.

        Returns:
            True if schema is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["gsettings", "list-schemas"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                schemas = result.stdout.strip().split("\n")
                return self.GSETTINGS_SCHEMA in schemas

            return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log_error(f"Error checking GSettings schema: {e}")
            return False

    def _set_gsettings_value(self, value: str) -> bool:
        """
        Set the color scheme value using gsettings.

        Args:
            value: The color scheme value to set

        Returns:
            True if value was set successfully, False otherwise
        """
        try:
            result = subprocess.run(
                ["gsettings", "set", self.GSETTINGS_SCHEMA, self.GSETTINGS_KEY, value],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.log_debug(f"Set {self.GSETTINGS_KEY} to {value}")
                return True
            else:
                self.log_error(f"gsettings set failed: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log_error(f"Error setting gsettings value: {e}")
            return False

    def _get_gsettings_value(self) -> Optional[str]:
        """
        Get the current color scheme value using gsettings.

        Returns:
            Current color scheme value or None if unable to retrieve
        """
        try:
            result = subprocess.run(
                ["gsettings", "get", self.GSETTINGS_SCHEMA, self.GSETTINGS_KEY],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                value = result.stdout.strip().strip("'\"")
                self.log_debug(f"Current {self.GSETTINGS_KEY} value: {value}")
                return value
            else:
                self.log_error(f"gsettings get failed: {result.stderr}")
                return None

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log_error(f"Error getting gsettings value: {e}")
            return None
