"""
Unit tests for the main application module.
"""

import unittest
from unittest.mock import patch, MagicMock

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

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
        
        # Mock quit method
        with patch.object(app, 'quit') as mock_quit:
            # Call quit_application
            app.quit_application()
            
            # Verify cleanup
            mock_config._save_config.assert_called_once()
            mock_cleanup_tray.assert_called_once()
            mock_mode_controller.cleanup.assert_called_once()
            mock_plugin_manager.cleanup_all.assert_called_once()
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


if __name__ == "__main__":
    unittest.main()