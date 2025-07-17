"""
Integration tests for system tray functionality.

Tests the system tray icon behavior, menu interactions, and integration
with the mode controller and theme switching functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gtk, Gio

from src.nightswitch.ui.system_tray import SystemTrayIcon, create_system_tray, cleanup_system_tray
from src.nightswitch.core.mode_controller import ModeController, ThemeMode
from src.nightswitch.core.manual_mode import ThemeType


class TestSystemTrayIntegration:
    """Integration tests for system tray functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clean up any existing global instances
        cleanup_system_tray()
        
        # Mock mode controller
        self.mock_mode_controller = Mock(spec=ModeController)
        self.mock_mode_controller.get_current_mode.return_value = ThemeMode.MANUAL
        self.mock_mode_controller.get_current_theme.return_value = ThemeType.LIGHT
        self.mock_mode_controller.add_mode_change_callback = Mock()
        self.mock_mode_change_callback = Mock()
        self.mock_theme_change_callback = Mock()
        
        # Mock callbacks
        self.mock_show_window = Mock()
        self.mock_quit = Mock()

    def teardown_method(self):
        """Clean up after tests."""
        cleanup_system_tray()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_system_tray_creation_with_appindicator(self, mock_appindicator):
        """Test system tray creation with AppIndicator3."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        mock_appindicator.IndicatorCategory.APPLICATION_STATUS = "APPLICATION_STATUS"
        mock_appindicator.IndicatorStatus.ACTIVE = "ACTIVE"

        # Create system tray with mocked menu creation
        with patch.object(SystemTrayIcon, '_create_gtk4_compatible_menu') as mock_create_menu:
            mock_menu = Mock()
            mock_create_menu.return_value = mock_menu
            
            tray = SystemTrayIcon(
                mode_controller=self.mock_mode_controller,
                show_window_callback=self.mock_show_window,
                quit_callback=self.mock_quit
            )

            # Verify AppIndicator3 was used
            mock_appindicator.Indicator.new.assert_called_once_with(
                "nightswitch",
                "applications-system",
                "APPLICATION_STATUS"
            )
            
            # Verify indicator setup
            mock_indicator.set_status.assert_called()
            mock_indicator.set_menu.assert_called_with(mock_menu)

            # Verify callbacks were registered
            self.mock_mode_controller.add_mode_change_callback.assert_called()
            self.mock_mode_controller.add_theme_change_callback.assert_called()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', False)
    def test_system_tray_creation_without_appindicator(self):
        """Test system tray creation without AppIndicator3."""
        # Create system tray (should work but with limited functionality)
        tray = SystemTrayIcon(
            mode_controller=self.mock_mode_controller,
            show_window_callback=self.mock_show_window,
            quit_callback=self.mock_quit
        )

        # Should still create the tray object
        assert tray is not None
        
        # Verify callbacks were still registered
        self.mock_mode_controller.add_mode_change_callback.assert_called()
        self.mock_mode_controller.add_theme_change_callback.assert_called()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_tray_icon_visibility(self, mock_appindicator):
        """Test tray icon show/hide functionality."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        mock_appindicator.IndicatorStatus.ACTIVE = "ACTIVE"
        mock_appindicator.IndicatorStatus.PASSIVE = "PASSIVE"

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Test show
        tray.show()
        mock_indicator.set_status.assert_called_with("ACTIVE")
        assert tray.is_visible() is True

        # Test hide
        tray.hide()
        mock_indicator.set_status.assert_called_with("PASSIVE")
        assert tray.is_visible() is False

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_menu_theme_switching(self, mock_appindicator):
        """Test theme switching through tray menu."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Test dark theme switching
        self.mock_mode_controller.manual_switch_to_dark.return_value = True
        tray._on_switch_to_dark(Mock())
        self.mock_mode_controller.manual_switch_to_dark.assert_called_once()

        # Test light theme switching
        self.mock_mode_controller.manual_switch_to_light.return_value = True
        tray._on_switch_to_light(Mock())
        self.mock_mode_controller.manual_switch_to_light.assert_called_once()

        # Test theme toggle
        self.mock_mode_controller.manual_toggle_theme.return_value = True
        tray._on_toggle_theme(Mock())
        self.mock_mode_controller.manual_toggle_theme.assert_called_once()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_menu_mode_switching(self, mock_appindicator):
        """Test mode switching through tray menu."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(
            mode_controller=self.mock_mode_controller,
            show_window_callback=self.mock_show_window
        )

        # Test manual mode
        self.mock_mode_controller.set_manual_mode.return_value = True
        tray._on_manual_mode(Mock())
        self.mock_mode_controller.set_manual_mode.assert_called_once()

        # Test schedule mode (should show window)
        tray._on_schedule_mode(Mock())
        self.mock_show_window.assert_called_once()

        # Test location mode (should show window)
        tray._on_location_mode(Mock())
        assert self.mock_show_window.call_count == 2

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_menu_window_and_quit_actions(self, mock_appindicator):
        """Test window show and quit actions from tray menu."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(
            mode_controller=self.mock_mode_controller,
            show_window_callback=self.mock_show_window,
            quit_callback=self.mock_quit
        )

        # Test show window
        tray._on_show_window(Mock())
        self.mock_show_window.assert_called_once()

        # Test quit
        tray._on_quit(Mock())
        self.mock_quit.assert_called_once()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_mode_change_callback(self, mock_appindicator):
        """Test handling of mode change events."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Mock notification sending
        with patch.object(tray, '_show_info_notification') as mock_notify:
            with patch.object(tray, '_update_menu_state') as mock_update_menu:
                with patch.object(tray, '_update_icon') as mock_update_icon:
                    # Simulate mode change
                    tray._on_mode_changed(ThemeMode.SCHEDULE, ThemeMode.MANUAL)

                    # Verify updates were called
                    mock_update_menu.assert_called_once()
                    mock_update_icon.assert_called_once()
                    mock_notify.assert_called_once_with("Switched to Schedule mode")

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_theme_change_callback(self, mock_appindicator):
        """Test handling of theme change events."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Mock notification sending
        with patch.object(tray, '_show_info_notification') as mock_notify:
            with patch.object(tray, '_update_menu_state') as mock_update_menu:
                with patch.object(tray, '_update_icon') as mock_update_icon:
                    # Simulate theme change
                    tray._on_theme_changed(ThemeType.DARK)

                    # Verify updates were called
                    mock_update_menu.assert_called_once()
                    mock_update_icon.assert_called_once()
                    mock_notify.assert_called_once_with("Switched to Dark theme")

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_icon_update_based_on_theme(self, mock_appindicator):
        """Test tray icon updates based on current theme."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Test with dark theme
        self.mock_mode_controller.get_current_theme.return_value = ThemeType.DARK
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)
        
        # Should set dark theme icon
        mock_indicator.set_icon.assert_called_with("weather-clear-night-symbolic")

        # Test with light theme
        mock_indicator.reset_mock()
        self.mock_mode_controller.get_current_theme.return_value = ThemeType.LIGHT
        tray._update_icon()
        
        # Should set light theme icon
        mock_indicator.set_icon.assert_called_with("weather-clear-symbolic")

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    @patch('src.nightswitch.ui.system_tray.Gtk.Application.get_default')
    def test_notification_sending(self, mock_get_app, mock_appindicator):
        """Test notification sending functionality."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Mock application
        mock_app = Mock()
        mock_get_app.return_value = mock_app

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Test info notification
        with patch('src.nightswitch.ui.system_tray.Gio.Notification.new') as mock_notification:
            mock_notif = Mock()
            mock_notification.return_value = mock_notif
            
            tray._show_info_notification("Test message")
            
            mock_notification.assert_called_once_with("Nightswitch")
            mock_notif.set_body.assert_called_once_with("Test message")
            mock_app.send_notification.assert_called_once()

        # Test error notification
        mock_app.reset_mock()
        with patch('src.nightswitch.ui.system_tray.Gio.Notification.new') as mock_notification:
            mock_notif = Mock()
            mock_notification.return_value = mock_notif
            
            tray._show_error_notification("Error message")
            
            mock_notification.assert_called_once_with("Nightswitch Error")
            mock_notif.set_body.assert_called_once_with("Error message")
            mock_app.send_notification.assert_called_once()

    def test_global_system_tray_management(self):
        """Test global system tray instance management."""
        # Initially no global instance
        from src.nightswitch.ui.system_tray import get_system_tray
        assert get_system_tray() is None

        # Create global instance
        tray = create_system_tray(
            mode_controller=self.mock_mode_controller,
            show_window_callback=self.mock_show_window,
            quit_callback=self.mock_quit
        )

        # Should return the same instance
        assert get_system_tray() is tray
        assert create_system_tray() is tray

        # Cleanup should clear global instance
        cleanup_system_tray()
        assert get_system_tray() is None

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_menu_state_updates(self, mock_appindicator):
        """Test menu state updates based on current mode and theme."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray with mocked GTK3 menu items
        with patch('src.nightswitch.ui.system_tray.gi.require_version'):
            with patch('src.nightswitch.ui.system_tray.Gtk3', create=True) as mock_gtk3:
                # Mock menu items
                mock_status_item = Mock()
                mock_dark_item = Mock()
                mock_light_item = Mock()
                mock_toggle_item = Mock()
                mock_manual_item = Mock()
                mock_schedule_item = Mock()
                mock_location_item = Mock()
                
                # Create system tray
                tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)
                
                # Set up mock menu items
                tray._status_item = mock_status_item
                tray._theme_items = {
                    "dark": mock_dark_item,
                    "light": mock_light_item,
                    "toggle": mock_toggle_item
                }
                tray._mode_items = {
                    "manual": mock_manual_item,
                    "schedule": mock_schedule_item,
                    "location": mock_location_item
                }
                
                # Test with manual mode
                self.mock_mode_controller.get_current_mode.return_value = ThemeMode.MANUAL
                self.mock_mode_controller.get_current_theme.return_value = ThemeType.DARK
                
                tray._update_menu_state()
                
                # Verify status item was updated
                mock_status_item.set_label.assert_called_with("Status: Mode: Manual | Theme: Dark")
                
                # Verify theme items are enabled in manual mode
                mock_dark_item.set_sensitive.assert_called_with(True)
                mock_light_item.set_sensitive.assert_called_with(True)
                mock_toggle_item.set_sensitive.assert_called_with(True)
                
                # Verify active mode is highlighted
                mock_manual_item.set_label.assert_called_with("✓ Manual Mode")
                mock_schedule_item.set_label.assert_called_with("Schedule Mode")
                mock_location_item.set_label.assert_called_with("Location Mode")
                
                # Test with schedule mode
                self.mock_mode_controller.get_current_mode.return_value = ThemeMode.SCHEDULE
                tray._update_menu_state()
                
                # Verify theme items are disabled in schedule mode
                mock_dark_item.set_sensitive.assert_called_with(False)
                mock_light_item.set_sensitive.assert_called_with(False)
                mock_toggle_item.set_sensitive.assert_called_with(False)
                
                # Verify active mode is highlighted
                mock_manual_item.set_label.assert_called_with("Manual Mode")
                mock_schedule_item.set_label.assert_called_with("✓ Schedule Mode")
                mock_location_item.set_label.assert_called_with("Location Mode")

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_error_handling_in_theme_switching(self, mock_appindicator):
        """Test error handling during theme switching operations."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Mock failed theme switching
        self.mock_mode_controller.manual_switch_to_dark.return_value = False

        with patch.object(tray, '_show_error_notification') as mock_error_notify:
            tray._on_switch_to_dark(Mock())
            mock_error_notify.assert_called_once_with("Failed to switch to dark theme")

        # Test exception handling
        self.mock_mode_controller.manual_switch_to_light.side_effect = Exception("Test error")

        with patch.object(tray, '_show_error_notification'):
            # Should not raise exception
            tray._on_switch_to_light(Mock())

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_cleanup_functionality(self, mock_appindicator):
        """Test cleanup functionality."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)

        # Verify callbacks were registered
        self.mock_mode_controller.add_mode_change_callback.assert_called()
        self.mock_mode_controller.add_theme_change_callback.assert_called()

        # Cleanup
        tray.cleanup()

        # Verify callbacks were removed
        self.mock_mode_controller.remove_mode_change_callback.assert_called()
        self.mock_mode_controller.remove_theme_change_callback.assert_called()

        # Verify tray was hidden
        assert not tray.is_visible()


class TestSystemTrayErrorHandling:
    """Test error handling in system tray functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        cleanup_system_tray()
        self.mock_mode_controller = Mock(spec=ModeController)

    def teardown_method(self):
        """Clean up after tests."""
        cleanup_system_tray()

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_appindicator_creation_failure(self, mock_appindicator):
        """Test handling of AppIndicator3 creation failure."""
        # Mock AppIndicator3 to raise exception
        mock_appindicator.Indicator.new.side_effect = Exception("AppIndicator3 error")

        # Should raise exception during creation
        with pytest.raises(Exception):
            SystemTrayIcon(mode_controller=self.mock_mode_controller)

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_menu_creation_failure(self, mock_appindicator):
        """Test handling of menu creation failure."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Mock _create_simple_menu to raise exception and _create_gtk4_compatible_menu to propagate it
        with patch.object(SystemTrayIcon, '_create_simple_menu', side_effect=Exception("Menu error")):
            with patch.object(SystemTrayIcon, '_setup_tray_icon', side_effect=Exception("Menu error")):
                with pytest.raises(Exception):
                    SystemTrayIcon(mode_controller=self.mock_mode_controller)

    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_callback_registration_failure(self, mock_appindicator):
        """Test handling of callback registration failure."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator

        # Mock mode controller to raise exception on callback registration
        self.mock_mode_controller.add_mode_change_callback.side_effect = Exception("Callback error")

        # Should still create tray but log error
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)
        assert tray is not None
        
    @patch('src.nightswitch.ui.system_tray.HAS_APPINDICATOR', True)
    @patch('src.nightswitch.ui.system_tray.AppIndicator3')
    def test_gtk4_compatible_menu_creation(self, mock_appindicator):
        """Test creation of GTK4 compatible menu for AppIndicator3."""
        # Mock AppIndicator3
        mock_indicator = Mock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        
        # Create system tray
        tray = SystemTrayIcon(mode_controller=self.mock_mode_controller)
        
        # Call the menu creation method directly
        with patch.object(tray, '_create_simple_menu') as mock_create_simple_menu:
            mock_menu = Mock()
            mock_create_simple_menu.return_value = mock_menu
            
            menu = tray._create_gtk4_compatible_menu()
            
            # Verify menu was created
            assert menu is not None
            assert menu == mock_menu
            
            # Verify simple menu was called
            mock_create_simple_menu.assert_called_once()