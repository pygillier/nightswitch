"""
Plugin manager for Nightswitch theme plugins.

This module provides the PluginManager class that handles plugin discovery,
loading, registration, and lifecycle management.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base import (
    PluginCompatibilityError,
    PluginError,
    PluginInfo,
    PluginInitializationError,
    ThemePlugin,
)


class PluginManager:
    """
    Plugin manager for discovering, loading, and managing theme plugins.

    Handles the complete plugin lifecycle including discovery, compatibility
    checking, loading, initialization, and cleanup.
    """

    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self.logger = logging.getLogger("nightswitch.plugins.manager")
        self._registered_plugins: Dict[str, Type[ThemePlugin]] = {}
        self._loaded_plugins: Dict[str, ThemePlugin] = {}
        self._active_plugin: Optional[ThemePlugin] = None
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}

    def discover_plugins(self, plugin_paths: Optional[List[Path]] = None) -> List[str]:
        """
        Discover available plugins in the specified paths.

        Args:
            plugin_paths: List of paths to search for plugins. If None, searches
                         the default plugins directory.

        Returns:
            List of discovered plugin names
        """
        if plugin_paths is None:
            # Default to the plugins directory in the package
            plugin_paths = [Path(__file__).parent]

        discovered = []

        for plugin_path in plugin_paths:
            if not plugin_path.exists():
                self.logger.warning(f"Plugin path does not exist: {plugin_path}")
                continue

            # Search for Python modules in the plugin directory
            for module_info in pkgutil.iter_modules([str(plugin_path)]):
                module_name = module_info.name

                # Skip base module and manager
                if module_name in ["base", "manager", "__init__"]:
                    continue

                try:
                    # Import the module
                    module_path = f"src.nightswitch.plugins.{module_name}"
                    module = importlib.import_module(module_path)

                    # Look for ThemePlugin subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, ThemePlugin)
                            and obj is not ThemePlugin
                            and not inspect.isabstract(obj)
                        ):

                            plugin_name = obj.__name__
                            self._registered_plugins[plugin_name] = obj
                            discovered.append(plugin_name)
                            self.logger.info(f"Discovered plugin: {plugin_name}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to load plugin module {module_name}: {e}"
                    )

        return discovered

    def register_plugin(self, plugin_class: Type[ThemePlugin]) -> None:
        """
        Manually register a plugin class.

        Args:
            plugin_class: ThemePlugin subclass to register

        Raises:
            ValueError: If plugin_class is not a valid ThemePlugin subclass
        """
        if not (
            inspect.isclass(plugin_class)
            and issubclass(plugin_class, ThemePlugin)
            and plugin_class is not ThemePlugin
        ):
            raise ValueError("plugin_class must be a ThemePlugin subclass")

        plugin_name = plugin_class.__name__
        self._registered_plugins[plugin_name] = plugin_class
        self.logger.info(f"Registered plugin: {plugin_name}")

    def get_registered_plugins(self) -> Dict[str, Type[ThemePlugin]]:
        """
        Get all registered plugin classes.

        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        return self._registered_plugins.copy()

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Get information about a registered plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginInfo instance or None if plugin not found
        """
        if plugin_name not in self._registered_plugins:
            return None

        try:
            # Create a temporary instance to get info
            plugin_class = self._registered_plugins[plugin_name]
            temp_instance = plugin_class()
            return temp_instance.get_info()
        except Exception as e:
            self.logger.error(f"Failed to get info for plugin {plugin_name}: {e}")
            return None

    def check_plugin_compatibility(self, plugin_name: str) -> bool:
        """
        Check if a plugin is compatible with the current environment.

        Args:
            plugin_name: Name of the plugin to check

        Returns:
            True if plugin is compatible, False otherwise
        """
        if plugin_name not in self._registered_plugins:
            return False

        try:
            plugin_class = self._registered_plugins[plugin_name]
            temp_instance = plugin_class()
            return temp_instance.detect_compatibility()
        except Exception as e:
            self.logger.error(
                f"Failed to check compatibility for plugin {plugin_name}: {e}"
            )
            return False

    def get_compatible_plugins(self) -> List[str]:
        """
        Get list of plugins compatible with the current environment.

        Returns:
            List of compatible plugin names, sorted by priority (highest first)
        """
        compatible = []

        for plugin_name in self._registered_plugins:
            if self.check_plugin_compatibility(plugin_name):
                compatible.append(plugin_name)

        # Sort by priority (highest first)
        def get_priority(plugin_name: str) -> int:
            info = self.get_plugin_info(plugin_name)
            return info.priority if info else 0

        compatible.sort(key=get_priority, reverse=True)
        return compatible

    def load_plugin(
        self, plugin_name: str, config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Load and initialize a plugin.

        Args:
            plugin_name: Name of the plugin to load
            config: Plugin-specific configuration

        Returns:
            True if plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If plugin loading fails
        """
        if plugin_name not in self._registered_plugins:
            raise PluginError(f"Plugin not registered: {plugin_name}")

        # Check if already loaded
        if plugin_name in self._loaded_plugins:
            self.logger.info(f"Plugin {plugin_name} already loaded")
            return True

        try:
            # Check compatibility first
            if not self.check_plugin_compatibility(plugin_name):
                raise PluginCompatibilityError(
                    f"Plugin {plugin_name} is not compatible"
                )

            # Create plugin instance
            plugin_class = self._registered_plugins[plugin_name]
            plugin_config = config or self._plugin_configs.get(plugin_name, {})
            plugin_instance = plugin_class(plugin_config)

            # Initialize the plugin
            if not plugin_instance.initialize():
                raise PluginInitializationError(
                    f"Plugin {plugin_name} initialization failed"
                )

            plugin_instance.set_initialized(True)
            self._loaded_plugins[plugin_name] = plugin_instance
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True

        except (PluginCompatibilityError, PluginInitializationError) as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise  # Re-raise the specific exception
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise PluginError(f"Failed to load plugin {plugin_name}: {e}")

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin and clean up its resources.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self._loaded_plugins:
            self.logger.warning(f"Plugin {plugin_name} is not loaded")
            return False

        try:
            plugin = self._loaded_plugins[plugin_name]

            # Deactivate if this is the active plugin
            if self._active_plugin is plugin:
                self._active_plugin = None

            # Clean up plugin resources
            plugin.cleanup()
            plugin.set_initialized(False)

            # Remove from loaded plugins
            del self._loaded_plugins[plugin_name]

            self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def set_active_plugin(self, plugin_name: str) -> bool:
        """
        Set the active plugin for theme switching.

        Args:
            plugin_name: Name of the plugin to activate

        Returns:
            True if plugin was activated successfully, False otherwise
        """
        if plugin_name not in self._loaded_plugins:
            # Try to load the plugin first
            if not self.load_plugin(plugin_name):
                return False

        self._active_plugin = self._loaded_plugins[plugin_name]
        self.logger.info(f"Set active plugin: {plugin_name}")
        return True

    def get_active_plugin(self) -> Optional[ThemePlugin]:
        """
        Get the currently active plugin.

        Returns:
            Active ThemePlugin instance or None if no plugin is active
        """
        return self._active_plugin

    def get_active_plugin_name(self) -> Optional[str]:
        """
        Get the name of the currently active plugin.

        Returns:
            Name of active plugin or None if no plugin is active
        """
        if self._active_plugin is None:
            return None

        for name, plugin in self._loaded_plugins.items():
            if plugin is self._active_plugin:
                return name

        return None

    def auto_select_plugin(self) -> Optional[str]:
        """
        Automatically select the best compatible plugin.

        Returns:
            Name of selected plugin or None if no compatible plugins found
        """
        compatible_plugins = self.get_compatible_plugins()

        if not compatible_plugins:
            self.logger.warning("No compatible plugins found")
            return None

        # Select the highest priority compatible plugin
        selected_plugin = compatible_plugins[0]

        if self.set_active_plugin(selected_plugin):
            self.logger.info(f"Auto-selected plugin: {selected_plugin}")
            return selected_plugin

        return None

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        Set configuration for a plugin.

        Args:
            plugin_name: Name of the plugin
            config: Configuration dictionary
        """
        self._plugin_configs[plugin_name] = config

        # If plugin is loaded, update its config
        if plugin_name in self._loaded_plugins:
            self._loaded_plugins[plugin_name].config = config

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Configuration dictionary
        """
        return self._plugin_configs.get(plugin_name, {})

    def cleanup_all(self) -> None:
        """Clean up all loaded plugins."""
        plugin_names = list(self._loaded_plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)

        self._active_plugin = None
        self.logger.info("Cleaned up all plugins")

    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of currently loaded plugin names.

        Returns:
            List of loaded plugin names
        """
        return list(self._loaded_plugins.keys())


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.

    Returns:
        PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
