"""
Unit tests for plugin manager functionality.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.nightswitch.plugins.base import (
    PluginCompatibilityError,
    PluginError,
    PluginInfo,
    PluginInitializationError,
    ThemePlugin,
)
from src.nightswitch.plugins.manager import PluginManager, get_plugin_manager


class TestPlugin1(ThemePlugin):
    """Test plugin with high priority."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="test_plugin_1",
            version="1.0.0",
            description="Test plugin 1",
            author="Test Author",
            desktop_environments=["test_de1"],
            priority=80,
        )

    def detect_compatibility(self) -> bool:
        return True

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        return True

    def apply_light_theme(self) -> bool:
        return True

    def get_current_theme(self) -> Optional[str]:
        return "light"


class TestPlugin2(ThemePlugin):
    """Test plugin with low priority."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="test_plugin_2",
            version="1.0.0",
            description="Test plugin 2",
            author="Test Author",
            desktop_environments=["test_de2"],
            priority=30,
        )

    def detect_compatibility(self) -> bool:
        return True

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        return True

    def apply_light_theme(self) -> bool:
        return True

    def get_current_theme(self) -> Optional[str]:
        return "dark"


class IncompatiblePlugin(ThemePlugin):
    """Test plugin that is incompatible."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="incompatible_plugin",
            version="1.0.0",
            description="Incompatible plugin",
            author="Test Author",
            desktop_environments=["nonexistent_de"],
            priority=50,
        )

    def detect_compatibility(self) -> bool:
        return False

    def initialize(self) -> bool:
        return False

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        return False

    def apply_light_theme(self) -> bool:
        return False

    def get_current_theme(self) -> Optional[str]:
        return None


class FailingPlugin(ThemePlugin):
    """Test plugin that fails to initialize."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="failing_plugin",
            version="1.0.0",
            description="Failing plugin",
            author="Test Author",
            desktop_environments=["test_de"],
            priority=50,
        )

    def detect_compatibility(self) -> bool:
        return True

    def initialize(self) -> bool:
        return False

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        return False

    def apply_light_theme(self) -> bool:
        return False

    def get_current_theme(self) -> Optional[str]:
        return None


class TestPluginManager:
    """Test cases for PluginManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = PluginManager()

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        assert isinstance(self.manager._registered_plugins, dict)
        assert isinstance(self.manager._loaded_plugins, dict)
        assert self.manager._active_plugin is None
        assert isinstance(self.manager._plugin_configs, dict)

    def test_register_plugin(self):
        """Test manual plugin registration."""
        self.manager.register_plugin(TestPlugin1)

        registered = self.manager.get_registered_plugins()
        assert "TestPlugin1" in registered
        assert registered["TestPlugin1"] is TestPlugin1

    def test_register_invalid_plugin(self):
        """Test registering invalid plugin class."""
        with pytest.raises(ValueError):
            self.manager.register_plugin(str)  # Not a ThemePlugin subclass

        with pytest.raises(ValueError):
            self.manager.register_plugin(ThemePlugin)  # Abstract base class

    def test_get_plugin_info(self):
        """Test getting plugin information."""
        self.manager.register_plugin(TestPlugin1)

        info = self.manager.get_plugin_info("TestPlugin1")
        assert info is not None
        assert info.name == "test_plugin_1"
        assert info.priority == 80

        # Test non-existent plugin
        info = self.manager.get_plugin_info("NonExistentPlugin")
        assert info is None

    def test_check_plugin_compatibility(self):
        """Test plugin compatibility checking."""
        self.manager.register_plugin(TestPlugin1)
        self.manager.register_plugin(IncompatiblePlugin)

        assert self.manager.check_plugin_compatibility("TestPlugin1") is True
        assert self.manager.check_plugin_compatibility("IncompatiblePlugin") is False
        assert self.manager.check_plugin_compatibility("NonExistentPlugin") is False

    def test_get_compatible_plugins(self):
        """Test getting compatible plugins sorted by priority."""
        self.manager.register_plugin(TestPlugin1)  # Priority 80
        self.manager.register_plugin(TestPlugin2)  # Priority 30
        self.manager.register_plugin(IncompatiblePlugin)  # Incompatible

        compatible = self.manager.get_compatible_plugins()

        assert len(compatible) == 2
        assert compatible[0] == "TestPlugin1"  # Higher priority first
        assert compatible[1] == "TestPlugin2"
        assert "IncompatiblePlugin" not in compatible

    def test_load_plugin_success(self):
        """Test successful plugin loading."""
        self.manager.register_plugin(TestPlugin1)

        result = self.manager.load_plugin("TestPlugin1")
        assert result is True

        loaded = self.manager.get_loaded_plugins()
        assert "TestPlugin1" in loaded

        plugin = self.manager._loaded_plugins["TestPlugin1"]
        assert plugin.is_initialized() is True

    def test_load_plugin_with_config(self):
        """Test loading plugin with configuration."""
        self.manager.register_plugin(TestPlugin1)
        config = {"test_option": "test_value"}

        result = self.manager.load_plugin("TestPlugin1", config)
        assert result is True

        plugin = self.manager._loaded_plugins["TestPlugin1"]
        assert plugin.config == config

    def test_load_plugin_incompatible(self):
        """Test loading incompatible plugin."""
        self.manager.register_plugin(IncompatiblePlugin)

        with pytest.raises(PluginCompatibilityError):
            self.manager.load_plugin("IncompatiblePlugin")

    def test_load_plugin_initialization_failure(self):
        """Test loading plugin that fails to initialize."""
        self.manager.register_plugin(FailingPlugin)

        with pytest.raises(PluginInitializationError):
            self.manager.load_plugin("FailingPlugin")

    def test_load_plugin_not_registered(self):
        """Test loading non-registered plugin."""
        with pytest.raises(PluginError):
            self.manager.load_plugin("NonExistentPlugin")

    def test_load_plugin_already_loaded(self):
        """Test loading already loaded plugin."""
        self.manager.register_plugin(TestPlugin1)

        # Load first time
        result1 = self.manager.load_plugin("TestPlugin1")
        assert result1 is True

        # Load second time
        result2 = self.manager.load_plugin("TestPlugin1")
        assert result2 is True

    def test_unload_plugin(self):
        """Test plugin unloading."""
        self.manager.register_plugin(TestPlugin1)
        self.manager.load_plugin("TestPlugin1")

        result = self.manager.unload_plugin("TestPlugin1")
        assert result is True

        loaded = self.manager.get_loaded_plugins()
        assert "TestPlugin1" not in loaded

    def test_unload_plugin_not_loaded(self):
        """Test unloading plugin that is not loaded."""
        result = self.manager.unload_plugin("NonExistentPlugin")
        assert result is False

    def test_set_active_plugin(self):
        """Test setting active plugin."""
        self.manager.register_plugin(TestPlugin1)
        self.manager.load_plugin("TestPlugin1")

        result = self.manager.set_active_plugin("TestPlugin1")
        assert result is True

        active = self.manager.get_active_plugin()
        assert active is not None
        assert isinstance(active, TestPlugin1)

        active_name = self.manager.get_active_plugin_name()
        assert active_name == "TestPlugin1"

    def test_set_active_plugin_auto_load(self):
        """Test setting active plugin with automatic loading."""
        self.manager.register_plugin(TestPlugin1)

        result = self.manager.set_active_plugin("TestPlugin1")
        assert result is True

        # Should be loaded and active
        loaded = self.manager.get_loaded_plugins()
        assert "TestPlugin1" in loaded

        active_name = self.manager.get_active_plugin_name()
        assert active_name == "TestPlugin1"

    def test_auto_select_plugin(self):
        """Test automatic plugin selection."""
        self.manager.register_plugin(TestPlugin1)  # Priority 80
        self.manager.register_plugin(TestPlugin2)  # Priority 30

        selected = self.manager.auto_select_plugin()
        assert selected == "TestPlugin1"  # Should select highest priority

        active_name = self.manager.get_active_plugin_name()
        assert active_name == "TestPlugin1"

    def test_auto_select_plugin_no_compatible(self):
        """Test automatic plugin selection with no compatible plugins."""
        self.manager.register_plugin(IncompatiblePlugin)

        selected = self.manager.auto_select_plugin()
        assert selected is None

        active = self.manager.get_active_plugin()
        assert active is None

    def test_plugin_config_management(self):
        """Test plugin configuration management."""
        config = {"test_option": "test_value"}

        self.manager.set_plugin_config("TestPlugin1", config)
        retrieved_config = self.manager.get_plugin_config("TestPlugin1")

        assert retrieved_config == config

        # Test getting config for non-existent plugin
        empty_config = self.manager.get_plugin_config("NonExistentPlugin")
        assert empty_config == {}

    def test_cleanup_all(self):
        """Test cleaning up all plugins."""
        self.manager.register_plugin(TestPlugin1)
        self.manager.register_plugin(TestPlugin2)
        self.manager.load_plugin("TestPlugin1")
        self.manager.load_plugin("TestPlugin2")
        self.manager.set_active_plugin("TestPlugin1")

        self.manager.cleanup_all()

        loaded = self.manager.get_loaded_plugins()
        assert len(loaded) == 0

        active = self.manager.get_active_plugin()
        assert active is None

    def test_unload_active_plugin(self):
        """Test unloading the currently active plugin."""
        self.manager.register_plugin(TestPlugin1)
        self.manager.load_plugin("TestPlugin1")
        self.manager.set_active_plugin("TestPlugin1")

        result = self.manager.unload_plugin("TestPlugin1")
        assert result is True

        active = self.manager.get_active_plugin()
        assert active is None


class TestPluginManagerSingleton:
    """Test cases for plugin manager singleton."""

    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns the same instance."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
