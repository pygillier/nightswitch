"""
Unit tests for the ManualModeHandler class.

Tests manual theme switching, visual feedback, callback functionality,
and integration with the plugin manager.
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.nightswitch.core.manual_mode import ManualModeHandler, get_manual_mode_handler
from src.nightswitch.core.mode_controller import ThemeType
from src.nightswitch.plugins.base import ThemePlugin
from src.nightswitch.plugins.manager import PluginManager


class MockThemePlugin(ThemePlugin):
    """Mock theme plugin for testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.dark_theme_applied = False
        self.light_theme_applied = False
        self.apply_dark_success = True
        self.apply_light_success = True

    def get_info(self):
        from src.nightswitch.plugins.base import PluginInfo

        return PluginInfo(
            name="MockPlugin",
            version="1.0.0",
            description="Mock plugin for testing",
            author="Test",
            desktop_environments=["test"],
        )

    def detect_compatibility(self) -> bool:
        return True

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass

    def apply_dark_theme(self) -> bool:
        if self.apply_dark_success:
            self.dark_theme_applied = True
            self.light_theme_applied = False
        return self.apply_dark_success

    def apply_light_theme(self) -> bool:
        if self.apply_light_success:
            self.light_theme_applied = True
            self.dark_theme_applied = False
        return self.apply_light_success

    def get_current_theme(self) -> Optional[str]:
        if self.dark_theme_applied:
            return "dark"
        elif self.light_theme_applied:
            return "light"
        return None


@pytest.fixture
def mock_plugin_manager():
    """Create a mock plugin manager."""
    plugin_manager = Mock(spec=PluginManager)
    mock_plugin = MockThemePlugin()
    plugin_manager.get_active_plugin.return_value = mock_plugin
    plugin_manager.get_active_plugin_name.return_value = "MockPlugin"
    return plugin_manager


@pytest.fixture
def manual_mode_handler(mock_plugin_manager):
    """Create a manual mode handler with mocked dependencies."""
    return ManualModeHandler(mock_plugin_manager)


class TestManualModeHandlerInitialization:
    """Test manual mode handler initialization."""

    def test_init_with_plugin_manager(self, mock_plugin_manager):
        """Test initialization with provided plugin manager."""
        handler = ManualModeHandler(mock_plugin_manager)

        assert handler._plugin_manager is mock_plugin_manager
        assert handler._current_theme is None
        assert handler._is_enabled is True
        assert len(handler._theme_change_callbacks) == 0
        assert len(handler._feedback_callbacks) == 0

    @patch('src.nightswitch.core.manual_mode.get_plugin_manager')
    def test_init_without_plugin_manager(self, mock_get_plugin_manager):
        """Test initialization without provided plugin manager."""
        mock_plugin_manager = Mock(spec=PluginManager)
        mock_get_plugin_manager.return_value = mock_plugin_manager

        handler = ManualModeHandler()

        assert handler._plugin_manager is mock_plugin_manager
        mock_get_plugin_manager.assert_called_once()

    def test_is_enabled(self, manual_mode_handler):
        """Test that manual mode is always enabled."""
        assert manual_mode_handler.is_enabled() is True


class TestThemeSwitching:
    """Test theme switching functionality."""

    def test_switch_to_dark_success(self, manual_mode_handler):
        """Test successfully switching to dark theme."""
        result = manual_mode_handler.switch_to_dark()

        assert result is True
        assert manual_mode_handler._current_theme == ThemeType.DARK

        # Check that plugin was called
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        assert plugin.dark_theme_applied is True

    def test_switch_to_light_success(self, manual_mode_handler):
        """Test successfully switching to light theme."""
        result = manual_mode_handler.switch_to_light()

        assert result is True
        assert manual_mode_handler._current_theme == ThemeType.LIGHT

        # Check that plugin was called
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        assert plugin.light_theme_applied is True

    def test_switch_to_dark_no_plugin(self, manual_mode_handler):
        """Test switching to dark theme when no plugin is available."""
        manual_mode_handler._plugin_manager.get_active_plugin.return_value = None

        result = manual_mode_handler.switch_to_dark()

        assert result is False
        assert manual_mode_handler._current_theme is None

    def test_switch_to_light_no_plugin(self, manual_mode_handler):
        """Test switching to light theme when no plugin is available."""
        manual_mode_handler._plugin_manager.get_active_plugin.return_value = None

        result = manual_mode_handler.switch_to_light()

        assert result is False
        assert manual_mode_handler._current_theme is None

    def test_switch_to_dark_plugin_failure(self, manual_mode_handler):
        """Test switching to dark theme when plugin fails."""
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        plugin.apply_dark_success = False

        result = manual_mode_handler.switch_to_dark()

        assert result is False
        assert manual_mode_handler._current_theme is None

    def test_switch_to_light_plugin_failure(self, manual_mode_handler):
        """Test switching to light theme when plugin fails."""
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        plugin.apply_light_success = False

        result = manual_mode_handler.switch_to_light()

        assert result is False
        assert manual_mode_handler._current_theme is None

    def test_switch_to_dark_plugin_exception(self, manual_mode_handler):
        """Test switching to dark theme when plugin raises exception."""
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        plugin.apply_dark_theme = Mock(side_effect=Exception("Plugin error"))

        result = manual_mode_handler.switch_to_dark()

        assert result is False
        assert manual_mode_handler._current_theme is None

    def test_toggle_theme_from_none_to_dark(self, manual_mode_handler):
        """Test toggling theme when current theme is None (defaults to dark)."""
        result = manual_mode_handler.toggle_theme()

        assert result is True
        assert manual_mode_handler._current_theme == ThemeType.DARK

    def test_toggle_theme_from_dark_to_light(self, manual_mode_handler):
        """Test toggling theme from dark to light."""
        manual_mode_handler._current_theme = ThemeType.DARK

        result = manual_mode_handler.toggle_theme()

        assert result is True
        assert manual_mode_handler._current_theme == ThemeType.LIGHT

    def test_toggle_theme_from_light_to_dark(self, manual_mode_handler):
        """Test toggling theme from light to dark."""
        manual_mode_handler._current_theme = ThemeType.LIGHT

        result = manual_mode_handler.toggle_theme()

        assert result is True
        assert manual_mode_handler._current_theme == ThemeType.DARK


class TestThemeAvailability:
    """Test theme availability functionality."""

    def test_get_available_themes(self, manual_mode_handler):
        """Test getting available themes."""
        themes = manual_mode_handler.get_available_themes()

        assert ThemeType.LIGHT in themes
        assert ThemeType.DARK in themes
        assert len(themes) == 2

    def test_is_theme_available_with_plugin(self, manual_mode_handler):
        """Test checking theme availability with active plugin."""
        assert manual_mode_handler.is_theme_available(ThemeType.DARK) is True
        assert manual_mode_handler.is_theme_available(ThemeType.LIGHT) is True

    def test_is_theme_available_no_plugin(self, manual_mode_handler):
        """Test checking theme availability without active plugin."""
        manual_mode_handler._plugin_manager.get_active_plugin.return_value = None

        assert manual_mode_handler.is_theme_available(ThemeType.DARK) is False
        assert manual_mode_handler.is_theme_available(ThemeType.LIGHT) is False


class TestCallbacks:
    """Test callback functionality."""

    def test_theme_change_callback(self, manual_mode_handler):
        """Test theme change callback."""
        callback = Mock()
        manual_mode_handler.add_theme_change_callback(callback)

        manual_mode_handler.switch_to_dark()

        callback.assert_called_once_with(ThemeType.DARK)

    def test_theme_change_callback_no_change(self, manual_mode_handler):
        """Test theme change callback when theme doesn't change."""
        callback = Mock()
        manual_mode_handler.add_theme_change_callback(callback)
        manual_mode_handler._current_theme = ThemeType.DARK

        manual_mode_handler.switch_to_dark()

        # Callback should not be called if theme doesn't change
        callback.assert_not_called()

    def test_feedback_callback_success(self, manual_mode_handler):
        """Test feedback callback on successful theme switch."""
        callback = Mock()
        manual_mode_handler.add_feedback_callback(callback)

        manual_mode_handler.switch_to_dark()

        # Should be called twice: starting and success
        assert callback.call_count == 2
        
        # Check the calls
        calls = callback.call_args_list
        assert calls[0][0][0] == "Switching to dark theme..."
        assert calls[0][0][1] is True
        assert calls[1][0][0] == "Successfully switched to dark theme"
        assert calls[1][0][1] is True

    def test_feedback_callback_failure(self, manual_mode_handler):
        """Test feedback callback on failed theme switch."""
        callback = Mock()
        manual_mode_handler.add_feedback_callback(callback)
        
        # Make plugin fail
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        plugin.apply_dark_success = False

        manual_mode_handler.switch_to_dark()

        # Should be called twice: starting and failure
        assert callback.call_count == 2
        
        # Check the calls
        calls = callback.call_args_list
        assert calls[0][0][0] == "Switching to dark theme..."
        assert calls[0][0][1] is True
        assert calls[1][0][0] == "Failed to apply dark theme"
        assert calls[1][0][1] is False

    def test_feedback_callback_no_plugin(self, manual_mode_handler):
        """Test feedback callback when no plugin is available."""
        callback = Mock()
        manual_mode_handler.add_feedback_callback(callback)
        manual_mode_handler._plugin_manager.get_active_plugin.return_value = None

        manual_mode_handler.switch_to_dark()

        # Should be called once with error message
        callback.assert_called_once_with(
            "No active plugin available for theme switching", False
        )

    def test_remove_theme_change_callback(self, manual_mode_handler):
        """Test removing theme change callback."""
        callback = Mock()
        manual_mode_handler.add_theme_change_callback(callback)
        manual_mode_handler.remove_theme_change_callback(callback)

        manual_mode_handler.switch_to_dark()

        callback.assert_not_called()

    def test_remove_feedback_callback(self, manual_mode_handler):
        """Test removing feedback callback."""
        callback = Mock()
        manual_mode_handler.add_feedback_callback(callback)
        manual_mode_handler.remove_feedback_callback(callback)

        manual_mode_handler.switch_to_dark()

        callback.assert_not_called()

    def test_callback_error_handling(self, manual_mode_handler):
        """Test that callback errors don't break functionality."""
        def failing_callback(*args):
            raise Exception("Callback error")

        manual_mode_handler.add_theme_change_callback(failing_callback)
        manual_mode_handler.add_feedback_callback(failing_callback)

        # Should not raise exception
        result = manual_mode_handler.switch_to_dark()
        assert result is True

    def test_duplicate_callback_prevention(self, manual_mode_handler):
        """Test that duplicate callbacks are not added."""
        callback = Mock()
        
        manual_mode_handler.add_theme_change_callback(callback)
        manual_mode_handler.add_theme_change_callback(callback)  # Add again
        
        assert len(manual_mode_handler._theme_change_callbacks) == 1

        manual_mode_handler.add_feedback_callback(callback)
        manual_mode_handler.add_feedback_callback(callback)  # Add again
        
        assert len(manual_mode_handler._feedback_callbacks) == 1


class TestStatusAndInfo:
    """Test status and information functionality."""

    def test_get_current_theme(self, manual_mode_handler):
        """Test getting current theme."""
        assert manual_mode_handler.get_current_theme() is None

        manual_mode_handler.switch_to_dark()
        assert manual_mode_handler.get_current_theme() == ThemeType.DARK

        manual_mode_handler.switch_to_light()
        assert manual_mode_handler.get_current_theme() == ThemeType.LIGHT

    def test_get_plugin_status_with_plugin(self, manual_mode_handler):
        """Test getting plugin status with active plugin."""
        status = manual_mode_handler.get_plugin_status()

        assert status["has_active_plugin"] is True
        assert status["plugin_name"] == "MockPlugin"
        assert status["plugin_initialized"] is False  # Mock plugin not initialized
        assert "available_themes" in status
        assert status["current_theme"] is None

    def test_get_plugin_status_no_plugin(self, manual_mode_handler):
        """Test getting plugin status without active plugin."""
        manual_mode_handler._plugin_manager.get_active_plugin.return_value = None
        manual_mode_handler._plugin_manager.get_active_plugin_name.return_value = None

        status = manual_mode_handler.get_plugin_status()

        assert status["has_active_plugin"] is False
        assert status["plugin_name"] is None
        assert status["plugin_initialized"] is False

    def test_get_status(self, manual_mode_handler):
        """Test getting comprehensive status."""
        # Add some callbacks
        callback1 = Mock()
        callback2 = Mock()
        manual_mode_handler.add_theme_change_callback(callback1)
        manual_mode_handler.add_feedback_callback(callback2)

        # Set a theme
        manual_mode_handler.switch_to_dark()

        status = manual_mode_handler.get_status()

        assert status["enabled"] is True
        assert status["current_theme"] == "dark"
        assert "available_themes" in status
        assert "plugin_status" in status
        assert status["callback_counts"]["theme_change"] == 1
        assert status["callback_counts"]["feedback"] == 1


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup(self, manual_mode_handler):
        """Test cleanup functionality."""
        # Add some callbacks
        callback1 = Mock()
        callback2 = Mock()
        manual_mode_handler.add_theme_change_callback(callback1)
        manual_mode_handler.add_feedback_callback(callback2)

        manual_mode_handler.cleanup()

        assert len(manual_mode_handler._theme_change_callbacks) == 0
        assert len(manual_mode_handler._feedback_callbacks) == 0

    def test_cleanup_error_handling(self, manual_mode_handler):
        """Test cleanup error handling."""
        # This should not raise an exception
        manual_mode_handler.cleanup()


class TestGlobalInstance:
    """Test global instance functionality."""

    def test_get_manual_mode_handler_singleton(self):
        """Test that get_manual_mode_handler returns singleton instance."""
        with patch('src.nightswitch.core.manual_mode.get_plugin_manager'):
            handler1 = get_manual_mode_handler()
            handler2 = get_manual_mode_handler()

            assert handler1 is handler2

    @patch('src.nightswitch.core.manual_mode._manual_mode_handler', None)
    def test_get_manual_mode_handler_creates_new_instance(self):
        """Test that get_manual_mode_handler creates new instance when needed."""
        with patch('src.nightswitch.core.manual_mode.get_plugin_manager'):
            handler = get_manual_mode_handler()

            assert handler is not None
            assert isinstance(handler, ManualModeHandler)


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_rapid_theme_switching(self, manual_mode_handler):
        """Test rapid theme switching."""
        # Switch themes rapidly
        assert manual_mode_handler.switch_to_dark() is True
        assert manual_mode_handler.switch_to_light() is True
        assert manual_mode_handler.switch_to_dark() is True
        assert manual_mode_handler.switch_to_light() is True

        # Should end up with light theme
        assert manual_mode_handler._current_theme == ThemeType.LIGHT

    def test_theme_switching_with_callbacks(self, manual_mode_handler):
        """Test theme switching with multiple callbacks."""
        theme_callback = Mock()
        feedback_callback = Mock()
        
        manual_mode_handler.add_theme_change_callback(theme_callback)
        manual_mode_handler.add_feedback_callback(feedback_callback)

        # Switch themes
        manual_mode_handler.switch_to_dark()
        manual_mode_handler.switch_to_light()

        # Check theme callbacks
        assert theme_callback.call_count == 2
        theme_callback.assert_any_call(ThemeType.DARK)
        theme_callback.assert_any_call(ThemeType.LIGHT)

        # Check feedback callbacks (2 calls per theme switch)
        assert feedback_callback.call_count == 4

    def test_plugin_manager_integration(self, manual_mode_handler):
        """Test integration with plugin manager."""
        # Test that plugin manager methods are called correctly
        manual_mode_handler.switch_to_dark()

        manual_mode_handler._plugin_manager.get_active_plugin.assert_called()

    def test_error_recovery(self, manual_mode_handler):
        """Test error recovery scenarios."""
        plugin = manual_mode_handler._plugin_manager.get_active_plugin()
        
        # First call fails, second succeeds
        plugin.apply_dark_success = False
        assert manual_mode_handler.switch_to_dark() is False
        
        plugin.apply_dark_success = True
        assert manual_mode_handler.switch_to_dark() is True
        assert manual_mode_handler._current_theme == ThemeType.DARK