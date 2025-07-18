"""
Integration tests for complete workflows in Nightswitch.

Tests end-to-end workflows for location mode and system tray mode switching.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta

from src.nightswitch.core.mode_controller import ModeController, ThemeMode
from src.nightswitch.core.manual_mode import ManualModeHandler, ThemeType
from src.nightswitch.core.schedule_mode import ScheduleModeHandler
from src.nightswitch.core.location_mode import LocationModeHandler
from src.nightswitch.plugins.manager import PluginManager
from src.nightswitch.plugins.base import ThemePlugin
from src.nightswitch.services.location import LocationService
from src.nightswitch.services.sunrise_sunset import SunriseSunsetService
from src.nightswitch.services.schedule import ScheduleService


class MockThemePlugin(ThemePlugin):
    """Mock theme plugin for testing."""
    
    def __init__(self):
        """Initialize the mock plugin."""
        self._initialized = False
        self._current_theme = "light"
        self.theme_change_count = 0
    
    def detect_compatibility(self) -> bool:
        """Check if plugin is compatible with current environment."""
        return True
    
    def initialize(self) -> bool:
        """Initialize the plugin."""
        self._initialized = True
        return True
    
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def apply_dark_theme(self) -> bool:
        """Apply dark theme to desktop environment."""
        self._current_theme = "dark"
        self.theme_change_count += 1
        return True
    
    def apply_light_theme(self) -> bool:
        """Apply light theme to desktop environment."""
        self._current_theme = "light"
        self.theme_change_count += 1
        return True
    
    def get_current_theme(self) -> str:
        """Return current theme state."""
        return self._current_theme
    
    def get_info(self) -> dict:
        """Return plugin information."""
        return {
            "name": "mock_plugin",
            "version": "1.0.0",
            "description": "Mock plugin for testing",
            "author": "Test Author",
            "desktop_environments": ["test"],
            "priority": 100
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False


class TestLocationModeWorkflow:
    """Test location mode workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock plugin
        self.mock_plugin = MockThemePlugin()
        
        # Create plugin manager with mock plugin
        self.plugin_manager = PluginManager()
        self.plugin_manager._plugins = {"MockPlugin": self.mock_plugin}
        self.plugin_manager._active_plugin = self.mock_plugin
        self.plugin_manager._active_plugin_name = "MockPlugin"
        
        # Create mock services
        self.mock_location_service = MagicMock(spec=LocationService)
        self.mock_location_service.get_current_location.return_value = (51.5074, -0.1278, "London, UK")
        
        self.mock_sunrise_sunset_service = MagicMock(spec=SunriseSunsetService)
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = True
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "day"
        
        # Create location mode handler
        self.location_mode_handler = LocationModeHandler(
            location_service=self.mock_location_service,
            sunrise_sunset_service=self.mock_sunrise_sunset_service
        )
        
        # Create mode controller
        self.mode_controller = ModeController(
            plugin_manager=self.plugin_manager,
            location_mode_handler=self.location_mode_handler
        )
        
        # Set up mode handlers in controller
        self.mode_controller.register_mode_handler(ThemeMode.LOCATION, self.location_mode_handler)
        
        # Set up callbacks
        self.location_mode_handler.set_theme_callback(self.mode_controller.apply_theme)
        
        # Track callbacks
        self.mode_change_events = []
        self.theme_change_events = []
        
        self.mode_controller.add_mode_change_callback(
            lambda new_mode, old_mode: self.mode_change_events.append((new_mode, old_mode))
        )
        
        self.mode_controller.add_theme_change_callback(
            lambda theme: self.theme_change_events.append(theme)
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        self.mode_controller.cleanup()
        self.location_mode_handler.cleanup()
        self.plugin_manager.cleanup_all()
    
    def test_location_mode_sunrise_sunset_switching(self):
        """Test location mode with sunrise/sunset theme switching."""
        # Start in manual mode with light theme
        self.mode_controller.manual_switch_to_light()
        assert self.mode_controller.get_current_mode() == ThemeMode.MANUAL
        assert self.mode_controller.get_current_theme() == ThemeType.LIGHT
        
        # 1. Switch to location mode with auto-detection
        result = self.mode_controller.set_location_mode()
        assert result is True
        assert self.mode_controller.get_current_mode() == ThemeMode.LOCATION
        assert len(self.mode_change_events) == 1
        assert self.mode_change_events[0][0] == ThemeMode.LOCATION
        
        # 2. Verify location service was called
        self.mock_location_service.get_current_location.assert_called_once()
        
        # 3. Verify sunrise/sunset service was called with correct parameters
        self.mock_sunrise_sunset_service.schedule_sun_events.assert_called_once()
        args = self.mock_sunrise_sunset_service.schedule_sun_events.call_args[0]
        assert args[0] == 51.5074  # Latitude
        assert args[1] == -0.1278  # Longitude
        assert callable(args[2])  # Callback function
        
        # 4. Verify initial theme was applied based on current sun period
        self.mock_sunrise_sunset_service.get_current_sun_period.assert_called_once()
        
        # 5. Simulate sunset event
        callback_func = args[2]
        callback_func("sunset")
        assert self.mode_controller.get_current_theme() == ThemeType.DARK
        assert self.mock_plugin.get_current_theme() == "dark"
        
        # 6. Simulate sunrise event
        callback_func("sunrise")
        assert self.mode_controller.get_current_theme() == ThemeType.LIGHT
        assert self.mock_plugin.get_current_theme() == "light"
        
        # 7. Switch to manual coordinates
        result = self.mode_controller.set_location_mode(40.7128, -74.0060)
        assert result is True
        assert self.mode_controller.get_current_mode() == ThemeMode.LOCATION
        
        # 8. Verify sunrise/sunset service was called with new coordinates
        assert self.mock_sunrise_sunset_service.schedule_sun_events.call_count == 2
        args = self.mock_sunrise_sunset_service.schedule_sun_events.call_args[0]
        assert args[0] == 40.7128  # New latitude
        assert args[1] == -74.0060  # New longitude
        
        # 9. Disable location mode
        result = self.mode_controller.set_manual_mode()
        assert result is True
        assert self.mode_controller.get_current_mode() == ThemeMode.MANUAL
        assert len(self.mode_change_events) == 3
        assert self.mode_change_events[2][0] == ThemeMode.MANUAL
        
        # 10. Verify sunrise/sunset service was stopped
        self.mock_sunrise_sunset_service.stop_sun_events.assert_called()


class TestSystemTrayModeSwitch:
    """Test mode switching through system tray."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock plugin
        self.mock_plugin = MockThemePlugin()
        
        # Create plugin manager with mock plugin
        self.plugin_manager = PluginManager()
        self.plugin_manager._plugins = {"MockPlugin": self.mock_plugin}
        self.plugin_manager._active_plugin = self.mock_plugin
        self.plugin_manager._active_plugin_name = "MockPlugin"
        
        # Create mock services
        self.mock_location_service = MagicMock(spec=LocationService)
        self.mock_location_service.get_current_location.return_value = (51.5074, -0.1278, "London, UK")
        
        self.mock_sunrise_sunset_service = MagicMock(spec=SunriseSunsetService)
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = True
        
        self.mock_schedule_service = MagicMock(spec=ScheduleService)
        self.mock_schedule_service.set_schedule.return_value = True
        
        # Create mode handlers
        self.manual_mode_handler = ManualModeHandler(plugin_manager=self.plugin_manager)
        
        self.schedule_mode_handler = ScheduleModeHandler(
            schedule_service=self.mock_schedule_service
        )
        
        self.location_mode_handler = LocationModeHandler(
            location_service=self.mock_location_service,
            sunrise_sunset_service=self.mock_sunrise_sunset_service
        )
        
        # Create mode controller
        self.mode_controller = ModeController(
            plugin_manager=self.plugin_manager,
            manual_mode_handler=self.manual_mode_handler,
            schedule_mode_handler=self.schedule_mode_handler,
            location_mode_handler=self.location_mode_handler
        )
        
        # Set up mode handlers in controller
        self.mode_controller.register_mode_handler(ThemeMode.SCHEDULE, self.schedule_mode_handler)
        self.mode_controller.register_mode_handler(ThemeMode.LOCATION, self.location_mode_handler)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.mode_controller.cleanup()
        self.manual_mode_handler.cleanup()
        self.schedule_mode_handler.cleanup()
        self.location_mode_handler.cleanup()
        self.plugin_manager.cleanup_all()
    
    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_system_tray_mode_switching(self, mock_appindicator):
        """Test mode switching through system tray."""
        from src.nightswitch.ui.system_tray import SystemTrayIcon
        
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        
        # Create system tray with show window callback
        show_window_mock = Mock()
        tray = SystemTrayIcon(
            mode_controller=self.mode_controller,
            show_window_callback=show_window_mock
        )
        
        # Test manual mode
        self.mode_controller.set_schedule_mode("20:00", "08:00")
        assert self.mode_controller.get_current_mode() == ThemeMode.SCHEDULE
        
        tray._on_manual_mode(Mock())
        assert self.mode_controller.get_current_mode() == ThemeMode.MANUAL
        
        # Test schedule mode (should show window)
        tray._on_schedule_mode(Mock())
        show_window_mock.assert_called_once()
        
        # Test location mode (should show window)
        tray._on_location_mode(Mock())
        assert show_window_mock.call_count == 2