"""
Unit tests for the ModeController class.

Tests mode switching, conflict resolution, state management, and callback functionality.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from src.nightswitch.core.config import AppConfig, ConfigManager
from src.nightswitch.core.mode_controller import (
    ModeController,
    ThemeMode,
    ThemeType,
    get_mode_controller,
)
from src.nightswitch.core.manual_mode import ManualModeHandler
from src.nightswitch.plugins.base import ThemePlugin
from src.nightswitch.plugins.manager import PluginManager


class MockThemePlugin(ThemePlugin):
    """Mock theme plugin for testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.dark_theme_applied = False
        self.light_theme_applied = False

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
        self.dark_theme_applied = True
        self.light_theme_applied = False
        return True

    def apply_light_theme(self) -> bool:
        self.light_theme_applied = True
        self.dark_theme_applied = False
        return True

    def get_current_theme(self) -> Optional[str]:
        if self.dark_theme_applied:
            return "dark"
        elif self.light_theme_applied:
            return "light"
        return None


class MockModeHandler:
    """Mock mode handler for testing."""

    def __init__(self):
        self.enabled = False
        self.disabled = False
        self.enable_params = None

    def enable(self, *args, **kwargs):
        self.enabled = True
        self.disabled = False
        self.enable_params = (args, kwargs)
        return True

    def disable(self):
        self.disabled = True
        self.enabled = False
        return True


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    config_manager = Mock(spec=ConfigManager)

    # Default app config
    app_config = AppConfig(
        current_mode="manual",
        manual_theme="light",
        schedule_enabled=False,
        dark_time="19:00",
        light_time="07:00",
        location_enabled=False,
        latitude=None,
        longitude=None,
        auto_location=True,
    )

    config_manager.get_app_config.return_value = app_config
    config_manager.set_app_config = Mock()

    return config_manager


@pytest.fixture
def mock_plugin_manager():
    """Create a mock plugin manager."""
    plugin_manager = Mock(spec=PluginManager)
    mock_plugin = MockThemePlugin()
    plugin_manager.get_active_plugin.return_value = mock_plugin
    plugin_manager.get_active_plugin_name.return_value = "MockPlugin"
    return plugin_manager


@pytest.fixture
def mock_manual_mode_handler():
    """Create a mock manual mode handler."""
    handler = Mock(spec=ManualModeHandler)
    handler._current_theme = None
    handler.switch_to_dark.return_value = True
    handler.switch_to_light.return_value = True
    handler.toggle_theme.return_value = True
    handler.add_theme_change_callback = Mock()
    return handler


@pytest.fixture
def mode_controller(mock_config_manager, mock_plugin_manager, mock_manual_mode_handler):
    """Create a mode controller with mocked dependencies."""
    with (
        patch(
            "src.nightswitch.core.mode_controller.get_config",
            return_value=mock_config_manager,
        ),
        patch(
            "src.nightswitch.core.mode_controller.get_plugin_manager",
            return_value=mock_plugin_manager,
        ),
        patch(
            "src.nightswitch.core.mode_controller.get_manual_mode_handler",
            return_value=mock_manual_mode_handler,
        ),
    ):
        controller = ModeController(mock_config_manager, mock_plugin_manager, mock_manual_mode_handler)
        return controller


class TestModeControllerInitialization:
    """Test mode controller initialization."""

    def test_init_with_dependencies(self, mock_config_manager, mock_plugin_manager):
        """Test initialization with provided dependencies."""
        controller = ModeController(mock_config_manager, mock_plugin_manager)

        assert controller._config_manager is mock_config_manager
        assert controller._plugin_manager is mock_plugin_manager
        assert controller._current_mode == ThemeMode.MANUAL
        assert controller._current_theme == ThemeType.LIGHT

    def test_init_loads_state_from_config(
        self, mock_config_manager, mock_plugin_manager
    ):
        """Test that initialization loads state from configuration."""
        # Set up config with schedule mode
        app_config = AppConfig(
            current_mode="schedule",
            manual_theme="dark",
        )
        mock_config_manager.get_app_config.return_value = app_config

        controller = ModeController(mock_config_manager, mock_plugin_manager)

        assert controller._current_mode == ThemeMode.SCHEDULE
        assert controller._current_theme == ThemeType.DARK

    def test_init_handles_invalid_config_values(
        self, mock_config_manager, mock_plugin_manager
    ):
        """Test that initialization handles invalid configuration values."""
        # Set up config with invalid values
        app_config = AppConfig(
            current_mode="invalid_mode",
            manual_theme="invalid_theme",
        )
        mock_config_manager.get_app_config.return_value = app_config

        controller = ModeController(mock_config_manager, mock_plugin_manager)

        # Should default to valid values
        assert controller._current_mode == ThemeMode.MANUAL
        assert controller._current_theme == ThemeType.LIGHT

    def test_init_handles_config_error(self, mock_config_manager, mock_plugin_manager):
        """Test that initialization handles configuration errors gracefully."""
        mock_config_manager.get_app_config.side_effect = Exception("Config error")

        controller = ModeController(mock_config_manager, mock_plugin_manager)

        # Should default to safe values
        assert controller._current_mode == ThemeMode.MANUAL
        assert controller._current_theme == ThemeType.LIGHT


class TestModeHandlerManagement:
    """Test mode handler registration and management."""

    def test_register_mode_handler(self, mode_controller):
        """Test registering a mode handler."""
        handler = MockModeHandler()

        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        assert ThemeMode.SCHEDULE in mode_controller._mode_handlers
        assert mode_controller._mode_handlers[ThemeMode.SCHEDULE] is handler

    def test_unregister_mode_handler(self, mode_controller):
        """Test unregistering a mode handler."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        mode_controller.unregister_mode_handler(ThemeMode.SCHEDULE)

        assert ThemeMode.SCHEDULE not in mode_controller._mode_handlers

    def test_unregister_active_mode_handler(self, mode_controller):
        """Test unregistering the currently active mode handler."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        mode_controller.unregister_mode_handler(ThemeMode.SCHEDULE)

        # Should switch back to manual mode
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert mode_controller._active_handler is None


class TestManualMode:
    """Test manual mode functionality."""

    def test_set_manual_mode_without_theme(self, mode_controller):
        """Test setting manual mode without specifying theme."""
        # Set up initial state
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        result = mode_controller.set_manual_mode()

        assert result is True
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert mode_controller._active_handler is None
        assert handler.disabled is True

    def test_set_manual_mode_with_theme(self, mode_controller):
        """Test setting manual mode with specific theme."""
        result = mode_controller.set_manual_mode(ThemeType.DARK)

        assert result is True
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert mode_controller._current_theme == ThemeType.DARK

        # Check that theme was applied via plugin
        plugin = mode_controller._plugin_manager.get_active_plugin()
        assert plugin.dark_theme_applied is True

    def test_set_manual_mode_theme_application_failure(self, mode_controller):
        """Test manual mode when theme application fails."""
        # Make plugin fail theme application
        plugin = mode_controller._plugin_manager.get_active_plugin()
        plugin.apply_dark_theme = Mock(return_value=False)

        result = mode_controller.set_manual_mode(ThemeType.DARK)

        assert result is False

    def test_set_manual_mode_saves_config(self, mode_controller):
        """Test that manual mode saves configuration."""
        mode_controller.set_manual_mode(ThemeType.DARK)

        # Should save state to config
        mode_controller._config_manager.set_app_config.assert_called()


class TestScheduleMode:
    """Test schedule mode functionality."""

    def test_set_schedule_mode_success(self, mode_controller):
        """Test successfully setting schedule mode."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        result = mode_controller.set_schedule_mode("19:00", "07:00")

        assert result is True
        assert mode_controller._current_mode == ThemeMode.SCHEDULE
        assert mode_controller._active_handler is handler
        assert handler.enabled is True
        assert handler.enable_params == (("19:00", "07:00"), {})

    def test_set_schedule_mode_invalid_time_format(self, mode_controller):
        """Test schedule mode with invalid time format."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        result = mode_controller.set_schedule_mode("25:00", "07:00")  # Invalid hour

        assert result is False
        assert mode_controller._current_mode != ThemeMode.SCHEDULE

    def test_set_schedule_mode_no_handler(self, mode_controller):
        """Test schedule mode when no handler is registered."""
        # Unregister the schedule handler to test the no-handler scenario
        mode_controller.unregister_mode_handler(ThemeMode.SCHEDULE)
        
        result = mode_controller.set_schedule_mode("19:00", "07:00")

        assert result is False
        assert mode_controller._current_mode != ThemeMode.SCHEDULE

    def test_set_schedule_mode_handler_enable_failure(self, mode_controller):
        """Test schedule mode when handler enable fails."""
        handler = MockModeHandler()
        handler.enable = Mock(return_value=False)
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        result = mode_controller.set_schedule_mode("19:00", "07:00")

        assert result is False

    def test_set_schedule_mode_updates_config(self, mode_controller):
        """Test that schedule mode updates configuration."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)

        mode_controller.set_schedule_mode("19:00", "07:00")

        # Should update config
        mode_controller._config_manager.set_app_config.assert_called()

        # Get the config that was set
        call_args = mode_controller._config_manager.set_app_config.call_args[0][0]
        assert call_args.schedule_enabled is True
        assert call_args.dark_time == "19:00"
        assert call_args.light_time == "07:00"


class TestLocationMode:
    """Test location mode functionality."""

    def test_set_location_mode_with_coordinates(self, mode_controller):
        """Test setting location mode with specific coordinates."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)

        result = mode_controller.set_location_mode(40.7128, -74.0060)  # NYC coordinates

        assert result is True
        assert mode_controller._current_mode == ThemeMode.LOCATION
        assert mode_controller._active_handler is handler
        assert handler.enabled is True
        assert handler.enable_params == ((40.7128, -74.0060), {})

    def test_set_location_mode_auto_detect(self, mode_controller):
        """Test setting location mode with auto-detection."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)

        result = mode_controller.set_location_mode()

        assert result is True
        assert mode_controller._current_mode == ThemeMode.LOCATION
        assert handler.enabled is True
        assert handler.enable_params == ((None, None), {})

    def test_set_location_mode_invalid_coordinates(self, mode_controller):
        """Test location mode with invalid coordinates."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)

        result = mode_controller.set_location_mode(91.0, -74.0060)  # Invalid latitude

        assert result is False
        assert mode_controller._current_mode != ThemeMode.LOCATION

    def test_set_location_mode_no_handler(self, mode_controller):
        """Test location mode when no handler is registered."""
        result = mode_controller.set_location_mode(40.7128, -74.0060)

        assert result is False
        assert mode_controller._current_mode != ThemeMode.LOCATION

    def test_set_location_mode_updates_config(self, mode_controller):
        """Test that location mode updates configuration."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)

        mode_controller.set_location_mode(40.7128, -74.0060)

        # Should update config
        mode_controller._config_manager.set_app_config.assert_called()

        # Get the config that was set
        call_args = mode_controller._config_manager.set_app_config.call_args[0][0]
        assert call_args.location_enabled is True
        assert call_args.latitude == 40.7128
        assert call_args.longitude == -74.0060
        assert call_args.auto_location is False


class TestThemeApplication:
    """Test theme application functionality."""

    def test_apply_dark_theme(self, mode_controller):
        """Test applying dark theme."""
        result = mode_controller.apply_theme(ThemeType.DARK)

        assert result is True
        assert mode_controller._current_theme == ThemeType.DARK

        plugin = mode_controller._plugin_manager.get_active_plugin()
        assert plugin.dark_theme_applied is True

    def test_apply_light_theme(self, mode_controller):
        """Test applying light theme."""
        result = mode_controller.apply_theme(ThemeType.LIGHT)

        assert result is True
        assert mode_controller._current_theme == ThemeType.LIGHT

        plugin = mode_controller._plugin_manager.get_active_plugin()
        assert plugin.light_theme_applied is True

    def test_apply_theme_no_plugin(self, mode_controller):
        """Test applying theme when no plugin is active."""
        mode_controller._plugin_manager.get_active_plugin.return_value = None

        result = mode_controller.apply_theme(ThemeType.DARK)

        assert result is False

    def test_apply_theme_plugin_failure(self, mode_controller):
        """Test applying theme when plugin fails."""
        plugin = mode_controller._plugin_manager.get_active_plugin()
        plugin.apply_dark_theme = Mock(return_value=False)

        result = mode_controller.apply_theme(ThemeType.DARK)

        assert result is False

    def test_apply_theme_saves_config(self, mode_controller):
        """Test that theme application saves configuration."""
        mode_controller.apply_theme(ThemeType.DARK)

        # Should save state to config
        mode_controller._config_manager.set_app_config.assert_called()


class TestStateManagement:
    """Test state management functionality."""

    def test_get_current_mode(self, mode_controller):
        """Test getting current mode."""
        mode_controller._current_mode = ThemeMode.SCHEDULE

        assert mode_controller.get_current_mode() == ThemeMode.SCHEDULE

    def test_get_current_theme(self, mode_controller):
        """Test getting current theme."""
        mode_controller._current_theme = ThemeType.DARK

        assert mode_controller.get_current_theme() == ThemeType.DARK

    def test_get_available_modes(self, mode_controller):
        """Test getting available modes."""
        handler1 = MockModeHandler()
        handler2 = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler1)
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler2)

        available = mode_controller.get_available_modes()

        assert ThemeMode.MANUAL in available
        assert ThemeMode.SCHEDULE in available
        assert ThemeMode.LOCATION in available

    def test_is_mode_active(self, mode_controller):
        """Test checking if mode is active."""
        mode_controller._current_mode = ThemeMode.SCHEDULE

        assert mode_controller.is_mode_active(ThemeMode.SCHEDULE) is True
        assert mode_controller.is_mode_active(ThemeMode.MANUAL) is False

    def test_disable_current_mode(self, mode_controller):
        """Test disabling current mode."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        result = mode_controller.disable_current_mode()

        assert result is True
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert handler.disabled is True

    def test_disable_current_mode_already_manual(self, mode_controller):
        """Test disabling current mode when already in manual mode."""
        result = mode_controller.disable_current_mode()

        assert result is True
        assert mode_controller._current_mode == ThemeMode.MANUAL


class TestCallbacks:
    """Test callback functionality."""

    def test_mode_change_callback(self, mode_controller):
        """Test mode change callback."""
        callback = Mock()
        mode_controller.add_mode_change_callback(callback)

        mode_controller.set_manual_mode()

        callback.assert_called_once()

    def test_theme_change_callback(self, mode_controller):
        """Test theme change callback."""
        callback = Mock()
        mode_controller.add_theme_change_callback(callback)

        mode_controller.apply_theme(ThemeType.DARK)

        callback.assert_called_once_with(ThemeType.DARK)

    def test_remove_mode_change_callback(self, mode_controller):
        """Test removing mode change callback."""
        callback = Mock()
        mode_controller.add_mode_change_callback(callback)
        mode_controller.remove_mode_change_callback(callback)

        mode_controller.set_manual_mode()

        callback.assert_not_called()

    def test_remove_theme_change_callback(self, mode_controller):
        """Test removing theme change callback."""
        callback = Mock()
        mode_controller.add_theme_change_callback(callback)
        mode_controller.remove_theme_change_callback(callback)

        mode_controller.apply_theme(ThemeType.DARK)

        callback.assert_not_called()

    def test_callback_error_handling(self, mode_controller):
        """Test that callback errors don't break functionality."""

        def failing_callback(*args):
            raise Exception("Callback error")

        mode_controller.add_mode_change_callback(failing_callback)

        # Should not raise exception
        result = mode_controller.set_manual_mode()
        assert result is True


class TestModeStatus:
    """Test mode status functionality."""

    def test_get_mode_status_basic(self, mode_controller):
        """Test getting basic mode status."""
        status = mode_controller.get_mode_status()

        assert status["current_mode"] == "manual"
        assert status["current_theme"] == "light"
        assert "available_modes" in status
        assert "plugin_active" in status

    def test_get_mode_status_with_schedule(self, mode_controller):
        """Test getting mode status with schedule mode active."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller.set_schedule_mode("19:00", "07:00")

        status = mode_controller.get_mode_status()

        assert status["current_mode"] == "schedule"
        assert "schedule" in status
        assert status["schedule"]["enabled"] is True
        assert status["schedule"]["dark_time"] == "19:00"
        assert status["schedule"]["light_time"] == "07:00"

    def test_get_mode_status_with_location(self, mode_controller):
        """Test getting mode status with location mode active."""
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)
        mode_controller.set_location_mode(40.7128, -74.0060)

        status = mode_controller.get_mode_status()

        assert status["current_mode"] == "location"
        assert "location" in status
        assert status["location"]["enabled"] is True
        assert status["location"]["latitude"] == 40.7128
        assert status["location"]["longitude"] == -74.0060


class TestValidation:
    """Test validation functionality."""

    def test_validate_time_format_valid(self, mode_controller):
        """Test time format validation with valid times."""
        assert mode_controller._validate_time_format("00:00") is True
        assert mode_controller._validate_time_format("12:30") is True
        assert mode_controller._validate_time_format("23:59") is True

    def test_validate_time_format_invalid(self, mode_controller):
        """Test time format validation with invalid times."""
        assert mode_controller._validate_time_format("24:00") is False
        assert mode_controller._validate_time_format("12:60") is False
        assert mode_controller._validate_time_format("12:3") is False
        assert mode_controller._validate_time_format("invalid") is False

    def test_validate_coordinates_valid(self, mode_controller):
        """Test coordinate validation with valid coordinates."""
        assert mode_controller._validate_coordinates(0, 0) is True
        assert mode_controller._validate_coordinates(40.7128, -74.0060) is True
        assert mode_controller._validate_coordinates(-90, -180) is True
        assert mode_controller._validate_coordinates(90, 180) is True

    def test_validate_coordinates_invalid(self, mode_controller):
        """Test coordinate validation with invalid coordinates."""
        assert mode_controller._validate_coordinates(91, 0) is False
        assert mode_controller._validate_coordinates(-91, 0) is False
        assert mode_controller._validate_coordinates(0, 181) is False
        assert mode_controller._validate_coordinates(0, -181) is False


class TestManualModeIntegration:
    """Test manual mode handler integration."""

    def test_manual_switch_to_dark_in_manual_mode(self, mode_controller):
        """Test manual switch to dark when already in manual mode."""
        mode_controller._current_mode = ThemeMode.MANUAL

        result = mode_controller.manual_switch_to_dark()

        assert result is True
        mode_controller._manual_mode_handler.switch_to_dark.assert_called_once()

    def test_manual_switch_to_dark_from_other_mode(self, mode_controller):
        """Test manual switch to dark when in another mode."""
        # Set up schedule mode
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        result = mode_controller.manual_switch_to_dark()

        assert result is True
        # Should switch to manual mode first
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert handler.disabled is True
        mode_controller._manual_mode_handler.switch_to_dark.assert_called_once()

    def test_manual_switch_to_light_in_manual_mode(self, mode_controller):
        """Test manual switch to light when already in manual mode."""
        mode_controller._current_mode = ThemeMode.MANUAL

        result = mode_controller.manual_switch_to_light()

        assert result is True
        mode_controller._manual_mode_handler.switch_to_light.assert_called_once()

    def test_manual_switch_to_light_from_other_mode(self, mode_controller):
        """Test manual switch to light when in another mode."""
        # Set up schedule mode
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        result = mode_controller.manual_switch_to_light()

        assert result is True
        # Should switch to manual mode first
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert handler.disabled is True
        mode_controller._manual_mode_handler.switch_to_light.assert_called_once()

    def test_manual_toggle_theme_in_manual_mode(self, mode_controller):
        """Test manual toggle theme when already in manual mode."""
        mode_controller._current_mode = ThemeMode.MANUAL

        result = mode_controller.manual_toggle_theme()

        assert result is True
        mode_controller._manual_mode_handler.toggle_theme.assert_called_once()

    def test_manual_toggle_theme_from_other_mode(self, mode_controller):
        """Test manual toggle theme when in another mode."""
        # Set up location mode
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.LOCATION, handler)
        mode_controller._current_mode = ThemeMode.LOCATION
        mode_controller._active_handler = handler

        result = mode_controller.manual_toggle_theme()

        assert result is True
        # Should switch to manual mode first
        assert mode_controller._current_mode == ThemeMode.MANUAL
        assert handler.disabled is True
        mode_controller._manual_mode_handler.toggle_theme.assert_called_once()

    def test_manual_switch_mode_change_failure(self, mode_controller):
        """Test manual switch when mode change fails."""
        # Set up schedule mode
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._current_mode = ThemeMode.SCHEDULE
        mode_controller._active_handler = handler

        # Make set_manual_mode fail by making apply_theme fail
        plugin = mode_controller._plugin_manager.get_active_plugin()
        plugin.apply_dark_theme = Mock(return_value=False)

        # This should fail because set_manual_mode will fail
        with patch.object(mode_controller, 'set_manual_mode', return_value=False):
            result = mode_controller.manual_switch_to_dark()

        assert result is False
        mode_controller._manual_mode_handler.switch_to_dark.assert_not_called()

    def test_manual_switch_handler_failure(self, mode_controller):
        """Test manual switch when handler fails."""
        mode_controller._current_mode = ThemeMode.MANUAL
        mode_controller._manual_mode_handler.switch_to_dark.return_value = False

        result = mode_controller.manual_switch_to_dark()

        assert result is False

    def test_manual_switch_exception_handling(self, mode_controller):
        """Test manual switch exception handling."""
        mode_controller._current_mode = ThemeMode.MANUAL
        mode_controller._manual_mode_handler.switch_to_dark.side_effect = Exception("Handler error")

        result = mode_controller.manual_switch_to_dark()

        assert result is False

    def test_get_manual_mode_handler(self, mode_controller):
        """Test getting manual mode handler."""
        handler = mode_controller.get_manual_mode_handler()

        assert handler is mode_controller._manual_mode_handler

    def test_manual_mode_callback_setup(self, mode_controller):
        """Test that manual mode callbacks are set up correctly."""
        # Verify that callback was added to manual mode handler
        mode_controller._manual_mode_handler.add_theme_change_callback.assert_called_once()


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup(self, mode_controller):
        """Test cleanup functionality."""
        # Set up some state
        handler = MockModeHandler()
        mode_controller.register_mode_handler(ThemeMode.SCHEDULE, handler)
        mode_controller._active_handler = handler

        callback1 = Mock()
        callback2 = Mock()
        mode_controller.add_mode_change_callback(callback1)
        mode_controller.add_theme_change_callback(callback2)

        mode_controller.cleanup()

        assert handler.disabled is True
        assert mode_controller._active_handler is None
        assert len(mode_controller._mode_change_callbacks) == 0
        assert len(mode_controller._theme_change_callbacks) == 0


class TestGlobalInstance:
    """Test global instance functionality."""

    def test_get_mode_controller_singleton(self):
        """Test that get_mode_controller returns singleton instance."""
        with (
            patch("src.nightswitch.core.mode_controller.get_config"),
            patch("src.nightswitch.core.mode_controller.get_plugin_manager"),
        ):

            controller1 = get_mode_controller()
            controller2 = get_mode_controller()

            assert controller1 is controller2

    @patch("src.nightswitch.core.mode_controller._mode_controller", None)
    def test_get_mode_controller_creates_new_instance(self):
        """Test that get_mode_controller creates new instance when needed."""
        with (
            patch("src.nightswitch.core.mode_controller.get_config"),
            patch("src.nightswitch.core.mode_controller.get_plugin_manager"),
        ):

            controller = get_mode_controller()

            assert controller is not None
            assert isinstance(controller, ModeController)
