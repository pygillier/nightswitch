"""
Unit tests for the main application module.
"""

import unittest
from unittest.mock import patch, MagicMock

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from nightswitch.core.error_handler import ErrorContext, ErrorCategory, ErrorSeverity
from nightswitch.core.notification import NotificationType
from nightswitch.main import TrayApplication


class TestTrayApplication(unittest.TestCase):
    """Test cases for the TrayApplication class."""

    @patch("nightswitch.main.get_config")
    @patch("nightswitch.main.get_plugin_manager")
    @patch("nightswitch.main.get_mode_controller")
    @patch("nightswitch.main.create_system_tray")
    def test_application_initialization(self, mock_create_tray, mock_get_mode_controller, 
                                       mock_get_plugin_manager, mock_get_config):
        """Test that the application initializes correctly."""
        # Set up mocks
        mock_config = MagicMock()
        mock_config.get_app_config.return_value = MagicMock(start_minimized=False)
        mock_get_config.return_value = mock_config
        
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.discover_plugins.return_value = None
        mock_plugin_manager.auto_select_plugin.return_value = MagicMock()
        mock_get_plugin_manager.return_value = mock_plugin_manager
        
        mock_mode_controller = MagicMock()
        mock_get_mode_controller.return_value = mock_mode_controller
        
        mock_system_tray = MagicMock()
        mock_create_tray.return_value = mock_system_tray
        
        # Create application
        app = TrayApplication()
        
        # Verify initialization
        self.assertIsNotNone(app)
        self.assertEqual(app.get_application_id(), "org.nightswitch.Nightswitch")
    
    @patch("nightswitch.main.get_config")
    @patch("nightswitch.main.get_plugin_manager")
    @patch("nightswitch.main.get_mode_controller")
    @patch("nightswitch.main.create_system_tray")
    @patch("nightswitch.main.MainWindow")
    def test_startup_and_activate(self, mock_main_window, mock_create_tray, 
                                 mock_get_mode_controller, mock_get_plugin_manager, 
                                 mock_get_config):
        """Test application startup and activation."""
        # Set up mocks
        mock_config = MagicMock()
        mock_config.get_app_config.return_value = MagicMock(start_minimized=False)
        mock_get_config.return_value = mock_config
        
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.discover_plugins.return_value = None
        mock_plugin_manager.auto_select_plugin.return_value = MagicMock()
        mock_get_plugin_manager.return_value = mock_plugin_manager
        
        mock_mode_controller = MagicMock()
        mock_get_mode_controller.return_value = mock_mode_controller
        
        mock_system_tray = MagicMock()
        mock_create_tray.return_value = mock_system_tray
        
        mock_window = MagicMock()
        mock_main_window.return_value = mock_window
        
        # Create application
        app = TrayApplication()
        
        # Simulate startup
        with patch.object(Gtk.Application, 'do_startup'):
            app.do_startup()
            
            # Verify core components initialized
            mock_get_config.assert_called_once()
            mock_get_plugin_manager.assert_called_once()
            mock_plugin_manager.discover_plugins.assert_called_once()
            mock_plugin_manager.auto_select_plugin.assert_called_once()
            mock_get_mode_controller.assert_called_once()
        
        # Simulate activation
        with patch.object(Gtk.Application, 'do_activate'):
            app.do_activate()
            
            # Verify UI components created
            mock_main_window.assert_called_once()
            mock_create_tray.assert_called_once()
            mock_system_tray.show.assert_called_once()
    
    @patch("nightswitch.main.get_config")
    @patch("nightswitch.main.get_plugin_manager")
    @patch("nightswitch.main.get_mode_controller")
    @patch("nightswitch.main.create_system_tray")
    @patch("nightswitch.main.cleanup_system_tray")
    def test_quit_application(self, mock_cleanup_tray, mock_create_tray, 
                             mock_get_mode_controller, mock_get_plugin_manager, 
                             mock_get_config):
        """Test application quit with proper cleanup."""
        # Set up mocks
        mock_config = MagicMock()
        mock_config.get_app_config.return_value = MagicMock(start_minimized=False)
        mock_get_config.return_value = mock_config
        
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.discover_plugins.return_value = None
        mock_plugin_manager.auto_select_plugin.return_value = MagicMock()
        mock_get_plugin_manager.return_value = mock_plugin_manager
        
        mock_mode_controller = MagicMock()
        mock_get_mode_controller.return_value = mock_mode_controller
        
        mock_system_tray = MagicMock()
        mock_create_tray.return_value = mock_system_tray
        
        # Create application
        app = TrayApplication()
        app._config_manager = mock_config
        app._plugin_manager = mock_plugin_manager
        app._mode_controller = mock_mode_controller
        
        # Mock error handler and notification manager
        app._error_handler = MagicMock()
        app._notification_manager = MagicMock()
        
        # Mock quit method
        with patch.object(app, 'quit') as mock_quit:
            # Call quit_application
            app.quit_application()
            
            # Verify cleanup
            mock_config._save_config.assert_called_once()
            mock_cleanup_tray.assert_called_once()
            mock_mode_controller.cleanup.assert_called_once()
            mock_plugin_manager.cleanup_all.assert_called_once()
            app._error_handler.clear_error_history.assert_called_once()
            app._notification_manager.clear_notification_history.assert_called_once()
            mock_quit.assert_called_once()
    
    @patch("nightswitch.main.get_config")
    @patch("nightswitch.main.get_plugin_manager")
    @patch("nightswitch.main.get_mode_controller")
    def test_show_hide_main_window(self, mock_get_mode_controller, 
                                  mock_get_plugin_manager, mock_get_config):
        """Test showing and hiding the main window."""
        # Set up mocks
        mock_config = MagicMock()
        mock_config.get_app_config.return_value = MagicMock(start_minimized=False)
        mock_get_config.return_value = mock_config
        
        mock_plugin_manager = MagicMock()
        mock_plugin_manager.discover_plugins.return_value = None
        mock_plugin_manager.auto_select_plugin.return_value = MagicMock()
        mock_get_plugin_manager.return_value = mock_plugin_manager
        
        mock_mode_controller = MagicMock()
        mock_get_mode_controller.return_value = mock_mode_controller
        
        # Create application
        app = TrayApplication()
        
        # Create mock window
        mock_window = MagicMock()
        app._main_window = mock_window
        
        # Test show_main_window
        app.show_main_window()
        mock_window.present.assert_called_once()
        
        # Test hide_main_window
        app.hide_main_window()
        mock_window.hide.assert_called_once()

    @patch("nightswitch.main.get_error_handler")
    @patch("nightswitch.main.get_notification_manager")
    def test_error_handling_fallbacks(self, mock_get_notification_manager, mock_get_error_handler):
        """Test error handling fallback mechanisms."""
        # Create application
        app = TrayApplication()
        
        # Set up mocks
        mock_error_handler = MagicMock()
        mock_get_error_handler.return_value = mock_error_handler
        
        mock_notification_manager = MagicMock()
        mock_get_notification_manager.return_value = mock_notification_manager
        
        mock_plugin_manager = MagicMock()
        mock_mode_controller = MagicMock()
        
        # Set up application with mocks
        app._error_handler = mock_error_handler
        app._notification_manager = mock_notification_manager
        app._plugin_manager = mock_plugin_manager
        app._mode_controller = mock_mode_controller
        
        # Test plugin fallback handler
        error_context = ErrorContext(
            message="No compatible plugins found for your desktop environment.",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PLUGIN,
        )
        
        # Set up plugin manager for fallback test
        mock_plugin_manager.get_registered_plugins.return_value = {"TestPlugin": MagicMock()}
        mock_plugin_manager.get_active_plugin.return_value = None
        mock_plugin_manager.load_plugin.return_value = True
        
        # Call the fallback handler directly
        result = app._plugin_error_fallback(error_context)
        
        # Verify plugin manager was used to find alternative plugins
        mock_plugin_manager.get_registered_plugins.assert_called_once()
        
        # Test service fallback handler
        location_error_context = ErrorContext(
            message="Location detection failed",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SERVICE,
            source="LocationService",
        )
        
        # Call the service fallback handler
        result = app._service_error_fallback(location_error_context)
        
        # Verify notification was shown
        mock_notification_manager.notify.assert_called()
        
        # Test network fallback handler
        network_error_context = ErrorContext(
            message="Network connection failed",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
        )
        
        # Set up mode controller for network fallback test
        mock_mode_controller.get_current_mode = MagicMock(return_value=MagicMock(value="location"))
        
        # Call the network fallback handler
        result = app._network_error_fallback(network_error_context)
        
        # Verify notification was shown again
        self.assertEqual(mock_notification_manager.notify.call_count, 2)


if __name__ == "__main__":
    unittest.main()