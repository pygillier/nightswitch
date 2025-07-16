"""
Unit tests for plugin base classes and interfaces.
"""

from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest

from src.nightswitch.plugins.base import (
    PluginCompatibilityError,
    PluginError,
    PluginInfo,
    PluginInitializationError,
    PluginOperationError,
    ThemePlugin,
)


class MockThemePlugin(ThemePlugin):
    """Mock implementation of ThemePlugin for testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.compatibility = True
        self.initialization_success = True
        self.current_theme = "light"
        self.theme_apply_success = True

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="mock_plugin",
            version="1.0.0",
            description="Mock plugin for testing",
            author="Test Author",
            desktop_environments=["test_de"],
            priority=75,
            requires_packages=["test-package"],
            config_schema={"test_option": {"type": "string", "default": "test_value"}},
        )

    def detect_compatibility(self) -> bool:
        return self.compatibility

    def initialize(self) -> bool:
        return self.initialization_success

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        if self.theme_apply_success:
            self.current_theme = "dark"
        return self.theme_apply_success

    def apply_light_theme(self) -> bool:
        if self.theme_apply_success:
            self.current_theme = "light"
        return self.theme_apply_success

    def get_current_theme(self) -> Optional[str]:
        return self.current_theme


class TestPluginInfo:
    """Test cases for PluginInfo dataclass."""

    def test_plugin_info_creation(self):
        """Test creating PluginInfo with all fields."""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            desktop_environments=["gnome", "kde"],
            priority=80,
            requires_packages=["package1", "package2"],
            config_schema={"option1": {"type": "string"}},
        )

        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.description == "Test plugin"
        assert info.author == "Test Author"
        assert info.desktop_environments == ["gnome", "kde"]
        assert info.priority == 80
        assert info.requires_packages == ["package1", "package2"]
        assert info.config_schema == {"option1": {"type": "string"}}

    def test_plugin_info_defaults(self):
        """Test PluginInfo with default values."""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            desktop_environments=["gnome"],
        )

        assert info.priority == 50
        assert info.requires_packages == []
        assert info.config_schema == {}


class TestThemePlugin:
    """Test cases for ThemePlugin abstract base class."""

    def test_plugin_initialization(self):
        """Test plugin initialization with config."""
        config = {"test_key": "test_value"}
        plugin = MockThemePlugin(config)

        assert plugin.config == config
        assert not plugin.is_initialized()
        assert plugin.logger.name == "nightswitch.plugins.mock_plugin"

    def test_plugin_initialization_no_config(self):
        """Test plugin initialization without config."""
        plugin = MockThemePlugin()

        assert plugin.config == {}
        assert not plugin.is_initialized()

    def test_get_info(self):
        """Test getting plugin information."""
        plugin = MockThemePlugin()
        info = plugin.get_info()

        assert isinstance(info, PluginInfo)
        assert info.name == "mock_plugin"
        assert info.version == "1.0.0"
        assert info.priority == 75

    def test_detect_compatibility_success(self):
        """Test successful compatibility detection."""
        plugin = MockThemePlugin()
        assert plugin.detect_compatibility() is True

    def test_detect_compatibility_failure(self):
        """Test failed compatibility detection."""
        plugin = MockThemePlugin()
        plugin.compatibility = False
        assert plugin.detect_compatibility() is False

    def test_initialize_success(self):
        """Test successful plugin initialization."""
        plugin = MockThemePlugin()
        assert plugin.initialize() is True

    def test_initialize_failure(self):
        """Test failed plugin initialization."""
        plugin = MockThemePlugin()
        plugin.initialization_success = False
        assert plugin.initialize() is False

    def test_apply_dark_theme_success(self):
        """Test successful dark theme application."""
        plugin = MockThemePlugin()
        assert plugin.apply_dark_theme() is True
        assert plugin.get_current_theme() == "dark"

    def test_apply_dark_theme_failure(self):
        """Test failed dark theme application."""
        plugin = MockThemePlugin()
        plugin.theme_apply_success = False
        assert plugin.apply_dark_theme() is False
        assert plugin.get_current_theme() == "light"  # Should remain unchanged

    def test_apply_light_theme_success(self):
        """Test successful light theme application."""
        plugin = MockThemePlugin()
        plugin.current_theme = "dark"
        assert plugin.apply_light_theme() is True
        assert plugin.get_current_theme() == "light"

    def test_apply_light_theme_failure(self):
        """Test failed light theme application."""
        plugin = MockThemePlugin()
        plugin.current_theme = "dark"
        plugin.theme_apply_success = False
        assert plugin.apply_light_theme() is False
        assert plugin.get_current_theme() == "dark"  # Should remain unchanged

    def test_get_current_theme(self):
        """Test getting current theme."""
        plugin = MockThemePlugin()
        assert plugin.get_current_theme() == "light"

        plugin.current_theme = "dark"
        assert plugin.get_current_theme() == "dark"

        plugin.current_theme = None
        assert plugin.get_current_theme() is None

    def test_validate_config_default(self):
        """Test default config validation."""
        plugin = MockThemePlugin()
        assert plugin.validate_config({"any": "config"}) is True

    def test_get_config_schema(self):
        """Test getting config schema."""
        plugin = MockThemePlugin()
        schema = plugin.get_config_schema()

        assert isinstance(schema, dict)
        assert "test_option" in schema
        assert schema["test_option"]["type"] == "string"

    def test_initialization_state_management(self):
        """Test plugin initialization state management."""
        plugin = MockThemePlugin()

        assert not plugin.is_initialized()

        plugin.set_initialized(True)
        assert plugin.is_initialized()

        plugin.set_initialized(False)
        assert not plugin.is_initialized()

    @patch("logging.getLogger")
    def test_logging_methods(self, mock_get_logger):
        """Test plugin logging methods."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = MockThemePlugin()

        plugin.log_info("info message")
        mock_logger.info.assert_called_with("info message")

        plugin.log_warning("warning message")
        mock_logger.warning.assert_called_with("warning message")

        plugin.log_error("error message")
        mock_logger.error.assert_called_with("error message")

        plugin.log_debug("debug message")
        mock_logger.debug.assert_called_with("debug message")


class TestPluginExceptions:
    """Test cases for plugin exception classes."""

    def test_plugin_error(self):
        """Test PluginError exception."""
        error = PluginError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_plugin_compatibility_error(self):
        """Test PluginCompatibilityError exception."""
        error = PluginCompatibilityError("Compatibility error")
        assert str(error) == "Compatibility error"
        assert isinstance(error, PluginError)
        assert isinstance(error, Exception)

    def test_plugin_initialization_error(self):
        """Test PluginInitializationError exception."""
        error = PluginInitializationError("Initialization error")
        assert str(error) == "Initialization error"
        assert isinstance(error, PluginError)
        assert isinstance(error, Exception)

    def test_plugin_operation_error(self):
        """Test PluginOperationError exception."""
        error = PluginOperationError("Operation error")
        assert str(error) == "Operation error"
        assert isinstance(error, PluginError)
        assert isinstance(error, Exception)
