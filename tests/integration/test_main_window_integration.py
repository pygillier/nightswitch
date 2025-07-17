"""
Integration tests for main window functionality.

Tests the main window UI components, interactions, and integration with
the mode controller and theme switching functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

from src.nightswitch.ui.main_window import MainWindow, create_main_window, cleanup_main_window
from src.nightswitch.core.mode_controller import ModeController, ThemeMode
from src.nightswitch.core.manual_mode import ThemeType
from src.nightswitch.core.schedule_mode import ScheduleModeHandler
from src.nightswitch.core.location_mode import LocationModeHandler
from src.nightswitch.services.location import LocationService


class TestMainWindowIntegration:
    """Integration tests for main window functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clean up any existing global instances
        cleanup_main_window()
        
        # Mock GTK application
        self.mock_app = Mock(spec=Gtk.Application)
        
        # Mock mode controller
        self.mock_mode_controller = Mock(spec=ModeController)
        self.mock_mode_controller.get_current_mode.return_value = ThemeMode.MANUAL
        self.mock_mode_controller.get_current_theme.return_value = ThemeType.LIGHT
        self.mock_mode_controller.add_mode_change_callback = Mock()
        self.mock_mode_controller.add_theme_change_callback = Mock()
        
        # Mock schedule handler
        self.mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        self.mock_schedule_handler.get_schedule_times.return_value = (None, None)
        self.mock_schedule_handler.get_next_trigger.return_value = None
        self.mock_schedule_handler.validate_schedule_times.return_value = (True, None)
        self.mock_schedule_handler.add_status_callback = Mock()
        
        # Mock location handler
        self.mock_location_handler = Mock(spec=LocationModeHandler)
        self.mock_location_handler.get_current_location.return_value = None
        self.mock_location_handler.is_auto_location.return_value = True
        self.mock_location_handler.get_next_sun_event.return_value = None
        self.mock_location_handler._validate_coordinates.return_value = True
        self.mock_location_handler.add_status_callback = Mock()
        self.mock_location_handler.add_error_callback = Mock()
        
        # Mock location service
        self.mock_location_service = Mock(spec=LocationService)

    def teardown_method(self):
        """Clean up after tests."""
        cleanup_main_window()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_main_window_creation(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test main window creation."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Verify window was created
        assert window is not None
        
        # Verify callbacks were registered
        self.mock_mode_controller.add_mode_change_callback.assert_called()
        self.mock_mode_controller.add_theme_change_callback.assert_called()
        self.mock_schedule_handler.add_status_callback.assert_called()
        self.mock_location_handler.add_status_callback.assert_called()
        self.mock_location_handler.add_error_callback.assert_called()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_manual_mode_buttons(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test manual mode button functionality."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Test dark theme button
        self.mock_mode_controller.manual_switch_to_dark.return_value = True
        window._on_dark_button_clicked(Mock())
        self.mock_mode_controller.manual_switch_to_dark.assert_called_once()
        
        # Test light theme button
        self.mock_mode_controller.manual_switch_to_light.return_value = True
        window._on_light_button_clicked(Mock())
        self.mock_mode_controller.manual_switch_to_light.assert_called_once()
        
        # Test toggle button
        self.mock_mode_controller.manual_toggle_theme.return_value = True
        window._on_toggle_button_clicked(Mock())
        self.mock_mode_controller.manual_toggle_theme.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_schedule_mode_switch(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test schedule mode switch functionality."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up schedule entries
        window._dark_time_entry = Mock()
        window._dark_time_entry.get_text.return_value = "20:00"
        window._light_time_entry = Mock()
        window._light_time_entry.get_text.return_value = "08:00"
        
        # Test enabling schedule mode
        self.mock_mode_controller.set_schedule_mode.return_value = True
        result = window._on_schedule_switch_toggled(Mock(), True)
        assert result is True
        self.mock_mode_controller.set_schedule_mode.assert_called_once_with("20:00", "08:00")
        
        # Test disabling schedule mode
        self.mock_mode_controller.set_manual_mode.return_value = True
        result = window._on_schedule_switch_toggled(Mock(), False)
        assert result is True
        self.mock_mode_controller.set_manual_mode.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_schedule_validation_failure(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test schedule validation failure handling."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up schedule entries with invalid times
        window._dark_time_entry = Mock()
        window._dark_time_entry.get_text.return_value = "invalid"
        window._light_time_entry = Mock()
        window._light_time_entry.get_text.return_value = "08:00"
        
        # Mock validation failure
        self.mock_schedule_handler.validate_schedule_times.return_value = (False, "Invalid time format")
        
        # Mock error dialog
        window._show_error_dialog = Mock()
        
        # Test enabling schedule mode with invalid times
        result = window._on_schedule_switch_toggled(Mock(), True)
        assert result is False  # Should prevent switch from turning on
        window._show_error_dialog.assert_called_once_with("Invalid time format")
        self.mock_mode_controller.set_schedule_mode.assert_not_called()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_location_mode_switch_auto(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test location mode switch with auto-detection."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up auto-location switch
        window._auto_location_switch = Mock()
        window._auto_location_switch.get_active.return_value = True
        
        # Test enabling location mode with auto-detection
        self.mock_mode_controller.set_location_mode.return_value = True
        result = window._on_location_switch_toggled(Mock(), True)
        assert result is True
        self.mock_mode_controller.set_location_mode.assert_called_once_with()
        
        # Test disabling location mode
        self.mock_mode_controller.set_manual_mode.return_value = True
        result = window._on_location_switch_toggled(Mock(), False)
        assert result is True
        self.mock_mode_controller.set_manual_mode.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_location_mode_switch_manual(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test location mode switch with manual coordinates."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up auto-location switch and coordinate entries
        window._auto_location_switch = Mock()
        window._auto_location_switch.get_active.return_value = False
        
        window._latitude_entry = Mock()
        window._latitude_entry.get_text.return_value = "51.5074"
        
        window._longitude_entry = Mock()
        window._longitude_entry.get_text.return_value = "-0.1278"
        
        # Test enabling location mode with manual coordinates
        self.mock_mode_controller.set_location_mode.return_value = True
        result = window._on_location_switch_toggled(Mock(), True)
        assert result is True
        self.mock_mode_controller.set_location_mode.assert_called_once_with(51.5074, -0.1278)

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_location_invalid_coordinates(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test location mode with invalid coordinates."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up auto-location switch and invalid coordinate entries
        window._auto_location_switch = Mock()
        window._auto_location_switch.get_active.return_value = False
        
        window._latitude_entry = Mock()
        window._latitude_entry.get_text.return_value = "invalid"
        
        window._longitude_entry = Mock()
        window._longitude_entry.get_text.return_value = "-0.1278"
        
        # Mock error dialog
        window._show_error_dialog = Mock()
        
        # Test enabling location mode with invalid coordinates
        result = window._on_location_switch_toggled(Mock(), True)
        assert result is False  # Should prevent switch from turning on
        window._show_error_dialog.assert_called_once()
        self.mock_mode_controller.set_location_mode.assert_not_called()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_auto_location_switch_toggle(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test auto-location switch toggle."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Set up coordinate entries
        window._latitude_entry = Mock()
        window._longitude_entry = Mock()
        
        # Test enabling auto-location
        result = window._on_auto_location_switch_toggled(Mock(), True)
        assert result is True
        window._latitude_entry.set_sensitive.assert_called_once_with(False)
        window._longitude_entry.set_sensitive.assert_called_once_with(False)
        
        # Reset mocks
        window._latitude_entry.reset_mock()
        window._longitude_entry.reset_mock()
        
        # Test disabling auto-location
        result = window._on_auto_location_switch_toggled(Mock(), False)
        assert result is True
        window._latitude_entry.set_sensitive.assert_called_once_with(True)
        window._longitude_entry.set_sensitive.assert_called_once_with(True)

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_mode_change_callback(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test mode change callback handling."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock update methods
        window._update_ui_state = Mock()
        
        # Test mode change callback
        window._on_mode_changed(ThemeMode.SCHEDULE, ThemeMode.MANUAL)
        window._update_ui_state.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_theme_change_callback(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test theme change callback handling."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock update methods
        window._update_ui_state = Mock()
        
        # Test theme change callback
        window._on_theme_changed(ThemeType.DARK)
        window._update_ui_state.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_location_error_callback(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test location error callback handling."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock error dialog
        window._show_error_dialog = Mock()
        window._status_label = Mock()
        
        # Test location error callback with important error
        window._on_location_error("location_detection_failed", "Could not detect location")
        window._show_error_dialog.assert_called_once()
        window._status_label.set_markup.assert_called_once()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_window_close_request(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test window close request handling."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Test close request
        result = window._on_close_request(window)
        assert result is False  # Should allow window to close
        
        # Verify callbacks were removed
        self.mock_mode_controller.remove_mode_change_callback.assert_called()
        self.mock_mode_controller.remove_theme_change_callback.assert_called()
        self.mock_schedule_handler.remove_status_callback.assert_called()
        self.mock_location_handler.remove_status_callback.assert_called()
        self.mock_location_handler.remove_error_callback.assert_called()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    @patch('src.nightswitch.ui.main_window.get_main_window')
    def test_global_main_window_management(self, mock_get_main_window, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test global main window instance management."""
        # Set up mocks
        mock_get_schedule_handler.return_value = self.mock_schedule_handler
        mock_get_location_handler.return_value = self.mock_location_handler
        mock_get_location_service.return_value = self.mock_location_service
        mock_get_main_window.return_value = None
        
        # Initially no global instance
        assert mock_get_main_window() is None
        
        # Create global instance
        with patch('src.nightswitch.ui.main_window.MainWindow') as mock_window_class:
            mock_window = Mock()
            mock_window_class.return_value = mock_window
            
            window = create_main_window(
                application=self.mock_app,
                mode_controller=self.mock_mode_controller
            )
            
            # Should create window
            mock_window_class.assert_called_once()
            mock_window.add_css_provider.assert_called_once()
            
            # Update mock for get_main_window
            mock_get_main_window.return_value = mock_window
            
            # Test show_main_window
            from src.nightswitch.ui.main_window import show_main_window
            show_main_window()
            mock_window.present.assert_called_once()
            
            # Test cleanup
            cleanup_main_window()
            mock_get_main_window.return_value = None


class TestMainWindowErrorHandling:
    """Test error handling in main window functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        cleanup_main_window()
        self.mock_app = Mock(spec=Gtk.Application)
        self.mock_mode_controller = Mock(spec=ModeController)
        self.mock_mode_controller.get_current_mode.return_value = ThemeMode.MANUAL
        self.mock_mode_controller.get_current_theme.return_value = ThemeType.LIGHT

    def teardown_method(self):
        """Clean up after tests."""
        cleanup_main_window()

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_manual_button_error_handling(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test error handling in manual button clicks."""
        # Set up mocks
        mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        mock_location_handler = Mock(spec=LocationModeHandler)
        mock_location_service = Mock(spec=LocationService)
        
        mock_get_schedule_handler.return_value = mock_schedule_handler
        mock_get_location_handler.return_value = mock_location_handler
        mock_get_location_service.return_value = mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock status label and error dialog
        window._status_label = Mock()
        window._show_error_dialog = Mock()
        
        # Test error handling when switching to dark theme fails
        self.mock_mode_controller.manual_switch_to_dark.return_value = False
        window._on_dark_button_clicked(Mock())
        window._show_error_dialog.assert_called_once_with("Failed to switch to dark theme")
        
        # Reset mocks
        window._status_label.reset_mock()
        window._show_error_dialog.reset_mock()
        
        # Test error handling when switching to light theme raises exception
        self.mock_mode_controller.manual_switch_to_light.side_effect = Exception("Test error")
        window._on_light_button_clicked(Mock())
        window._show_error_dialog.assert_called_once()
        assert "Test error" in window._show_error_dialog.call_args[0][0]

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_schedule_error_handling(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test error handling in schedule mode operations."""
        # Set up mocks
        mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        mock_location_handler = Mock(spec=LocationModeHandler)
        mock_location_service = Mock(spec=LocationService)
        
        mock_get_schedule_handler.return_value = mock_schedule_handler
        mock_get_location_handler.return_value = mock_location_handler
        mock_get_location_service.return_value = mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock status label, error dialog, and entries
        window._status_label = Mock()
        window._show_error_dialog = Mock()
        window._dark_time_entry = Mock()
        window._dark_time_entry.get_text.return_value = "20:00"
        window._light_time_entry = Mock()
        window._light_time_entry.get_text.return_value = "08:00"
        
        # Test error handling when setting schedule mode fails
        self.mock_mode_controller.set_schedule_mode.return_value = False
        result = window._on_schedule_switch_toggled(Mock(), True)
        assert result is False  # Should prevent switch from turning on
        window._show_error_dialog.assert_called_once_with("Failed to enable schedule mode")

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    def test_location_error_handling(self, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test error handling in location mode operations."""
        # Set up mocks
        mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        mock_location_handler = Mock(spec=LocationModeHandler)
        mock_location_service = Mock(spec=LocationService)
        
        mock_get_schedule_handler.return_value = mock_schedule_handler
        mock_get_location_handler.return_value = mock_location_handler
        mock_get_location_service.return_value = mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock status label, error dialog, and switches/entries
        window._status_label = Mock()
        window._show_error_dialog = Mock()
        window._auto_location_switch = Mock()
        window._auto_location_switch.get_active.return_value = True
        
        # Test error handling when setting location mode fails
        self.mock_mode_controller.set_location_mode.return_value = False
        result = window._on_location_switch_toggled(Mock(), True)
        assert result is False  # Should prevent switch from turning on
        window._show_error_dialog.assert_called_once_with("Failed to enable location mode")

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    @patch('src.nightswitch.ui.main_window.Gtk.AlertDialog.new')
    def test_error_dialog_creation(self, mock_alert_dialog_new, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test error dialog creation."""
        # Set up mocks
        mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        mock_location_handler = Mock(spec=LocationModeHandler)
        mock_location_service = Mock(spec=LocationService)
        
        mock_get_schedule_handler.return_value = mock_schedule_handler
        mock_get_location_handler.return_value = mock_location_handler
        mock_get_location_service.return_value = mock_location_service
        
        # Mock alert dialog
        mock_dialog = Mock()
        mock_alert_dialog_new.return_value = mock_dialog
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Test error dialog creation
        window._show_error_dialog("Test error message")
        mock_alert_dialog_new.assert_called_once_with("Test error message")
        mock_dialog.set_modal.assert_called_once_with(True)
        mock_dialog.set_buttons.assert_called_once_with(["OK"])
        mock_dialog.show.assert_called_once_with(window)

    @patch('src.nightswitch.ui.main_window.get_schedule_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_mode_handler')
    @patch('src.nightswitch.ui.main_window.get_location_service')
    @patch('src.nightswitch.ui.main_window.Gtk.AlertDialog.new', side_effect=Exception("Dialog error"))
    def test_error_dialog_fallback(self, mock_alert_dialog_new, mock_get_location_service, mock_get_location_handler, mock_get_schedule_handler):
        """Test error dialog fallback when dialog creation fails."""
        # Set up mocks
        mock_schedule_handler = Mock(spec=ScheduleModeHandler)
        mock_location_handler = Mock(spec=LocationModeHandler)
        mock_location_service = Mock(spec=LocationService)
        
        mock_get_schedule_handler.return_value = mock_schedule_handler
        mock_get_location_handler.return_value = mock_location_handler
        mock_get_location_service.return_value = mock_location_service
        
        # Create main window
        window = MainWindow(
            application=self.mock_app,
            mode_controller=self.mock_mode_controller
        )
        
        # Mock status label
        window._status_label = Mock()
        
        # Test error dialog fallback
        window._show_error_dialog("Test error message")
        window._status_label.set_markup.assert_called_once_with("<small>Error: Test error message</small>")