"""
System tray icon implementation for Nightswitch application.

This module provides system tray integration using AppIndicator3
for displaying the application icon and context menu in the system notification area.
"""

import logging
from typing import Optional, Callable, Any
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")

# Try to import AppIndicator3, but allow for graceful failure in test environments
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_APPINDICATOR = True
except (ValueError, ImportError):
    AppIndicator3 = None
    HAS_APPINDICATOR = False
    import sys
    # Only show warning in non-test environments
    if 'pytest' not in sys.modules:
        print("WARNING: AppIndicator3 not available. System tray functionality will be limited.")

from gi.repository import Gtk, Gio, GLib

from ..core.mode_controller import ModeController, ThemeMode, get_mode_controller
from ..core.manual_mode import ThemeType


class SystemTrayIcon:
    """
    System tray icon for Nightswitch application.
    
    Provides system tray integration with context menu functionality
    and click handling to show/hide the main window.
    """

    def __init__(
        self,
        mode_controller: Optional[ModeController] = None,
        show_window_callback: Optional[Callable[[], None]] = None,
        quit_callback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the system tray icon.

        Args:
            mode_controller: Mode controller instance for theme switching
            show_window_callback: Callback to show main window
            quit_callback: Callback to quit application
        """
        self.logger = logging.getLogger("nightswitch.ui.system_tray")
        self._mode_controller = mode_controller or get_mode_controller()
        self._show_window_callback = show_window_callback
        self._quit_callback = quit_callback

        # Tray icon components
        self._indicator: Optional[Any] = None
        self._menu: Optional[Gtk.Menu] = None
        self._is_visible = False

        # Menu items for dynamic updates
        self._menu_model: Optional[Gio.Menu] = None
        self._current_status = "Manual | Light"
        self._theme_items = {}
        self._mode_items = {}
        self._status_item = None

        # Initialize tray icon
        self._setup_tray_icon()
        self._setup_menu()
        self._setup_callbacks()

        self.logger.info("System tray icon initialized")

    def _setup_tray_icon(self) -> None:
        """Set up the system tray icon using AppIndicator."""
        try:
            self._setup_appindicator()
        except Exception as e:
            self.logger.error(f"Failed to set up tray icon: {e}")
            raise

    def _setup_appindicator(self) -> None:
        """Set up tray icon using AppIndicator3."""
        try:
            self._indicator = AppIndicator3.Indicator.new(
                "nightswitch",
                "applications-system",  # Default icon name
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self.logger.debug("Indicator instance created")
            
            # Set icon based on current theme
            self._update_icon()
            
            # Set status to active
            self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            
            self.logger.info("AppIndicator3 tray icon created")
            
        except Exception as e:
            self.logger.error(f"Failed to create AppIndicator3 icon: {e}")
            raise

    # AppIndicator is now required, so we no longer need a fallback method

    def _setup_menu(self) -> None:
        """Set up the context menu for the tray icon."""
        try:
            # In GTK3, we can directly create a Gtk.Menu for AppIndicator3
            try:
                # Create a GTK3 menu for AppIndicator3
                self._menu = self._create_gtk3_menu()
            except Exception as e:
                self.logger.warning(f"Failed to create GTK3 menu: {e}")
                self._menu = None

            # Set menu for indicator
            if self._indicator and self._menu:
                self._indicator.set_menu(self._menu)

            # Update menu state
            self._update_menu_state()

            self.logger.info("Tray menu created")

        except Exception as e:
            self.logger.error(f"Failed to create tray menu: {e}")
            raise

    def _create_gtk3_menu(self) -> Any:
        """
        Create a menu compatible with GTK 3 and AppIndicator3.
        
        GTK 3 has native support for Gtk.Menu which works well with AppIndicator3.
        
        Returns:
            Menu object compatible with AppIndicator3
        """
        try:
            # Initialize empty collections for menu items
            self._theme_items = {}
            self._mode_items = {}
            self._status_item = None
            
            # Create a menu structure for AppIndicator3
            menu = self._create_appindicator_menu_structure()
            
            self.logger.debug("Created menu for AppIndicator3")
            return menu
            
        except Exception as e:
            self.logger.error(f"Failed to create AppIndicator3 menu: {e}")
            return None
            
    def _create_appindicator_menu_structure(self) -> Any:
        """
        Create a menu structure for AppIndicator3.
        
        This method creates a menu structure that works with AppIndicator3
        in a GTK 3 environment.
        
        Returns:
            A menu object compatible with AppIndicator3
        """
        try:
            # Create a GTK3 menu for AppIndicator3
            menu = Gtk.Menu()
            
            # Status section
            self._status_item = Gtk.MenuItem(label=f"Status: {self._current_status}")
            self._status_item.set_sensitive(False)  # Not clickable
            menu.append(self._status_item)
            
            # Separator
            menu.append(Gtk.SeparatorMenuItem())
            
            # Theme switching section (only active in manual mode)
            dark_item = Gtk.MenuItem(label="Switch to Dark")
            dark_item.connect("activate", self._on_switch_to_dark)
            menu.append(dark_item)
            self._theme_items["dark"] = dark_item
            
            light_item = Gtk.MenuItem(label="Switch to Light")
            light_item.connect("activate", self._on_switch_to_light)
            menu.append(light_item)
            self._theme_items["light"] = light_item
            
            toggle_item = Gtk.MenuItem(label="Toggle Theme")
            toggle_item.connect("activate", self._on_toggle_theme)
            menu.append(toggle_item)
            self._theme_items["toggle"] = toggle_item
            
            # Separator
            menu.append(Gtk.SeparatorMenuItem())
            
            # Mode switching section
            manual_item = Gtk.MenuItem(label="Manual Mode")
            manual_item.connect("activate", self._on_manual_mode)
            menu.append(manual_item)
            self._mode_items["manual"] = manual_item
            
            schedule_item = Gtk.MenuItem(label="Schedule Mode")
            schedule_item.connect("activate", self._on_schedule_mode)
            menu.append(schedule_item)
            self._mode_items["schedule"] = schedule_item
            
            location_item = Gtk.MenuItem(label="Location Mode")
            location_item.connect("activate", self._on_location_mode)
            menu.append(location_item)
            self._mode_items["location"] = location_item
            
            # Separator
            menu.append(Gtk.SeparatorMenuItem())
            
            # Application section
            show_window_item = Gtk.MenuItem(label="Show Window")
            show_window_item.connect("activate", self._on_show_window)
            menu.append(show_window_item)
            
            quit_item = Gtk.MenuItem(label="Quit")
            quit_item.connect("activate", self._on_quit)
            menu.append(quit_item)
            
            # Show all menu items
            menu.show_all()
            
            self.logger.debug("Created AppIndicator3 menu structure")
            return menu
            
        except Exception as e:
            self.logger.error(f"Failed to create AppIndicator3 menu structure: {e}")
            
            # Fallback to a simple menu if menu creation fails
            return self._create_simple_menu()
            
    def _create_simple_menu(self) -> Any:
        """
        Create a simple menu structure for AppIndicator3.
        
        This is a fallback method when proper GTK 3 menu creation is not possible.
        
        Returns:
            A simple menu object or None
        """
        try:
            self.logger.warning("Using fallback simple menu implementation")
            
            # Create a simple object with the required methods
            class SimpleMenu:
                def __init__(self):
                    pass
                
                def show_all(self):
                    pass
                    
                def append(self, item):
                    pass
            
            menu = SimpleMenu()
            
            # Create a simple status item
            self._status_item = type('obj', (object,), {
                'set_label': lambda self, label: None,
                'set_sensitive': lambda self, sensitive: None
            })()
            
            # Create theme items
            for theme in ["dark", "light", "toggle"]:
                self._theme_items[theme] = type('obj', (object,), {
                    'set_label': lambda self, label: None,
                    'set_sensitive': lambda self, sensitive: None
                })()
            
            # Create mode items
            for mode in ["manual", "schedule", "location"]:
                self._mode_items[mode] = type('obj', (object,), {
                    'set_label': lambda self, label: None,
                    'set_sensitive': lambda self, sensitive: None
                })()
                
            return menu
            
        except Exception as e:
            self.logger.error(f"Failed to create simple menu: {e}")
            return None
            
    def _create_appindicator_menu(self) -> None:
        """Create menu items for AppIndicator3 compatibility."""
        try:
            # For AppIndicator3, we need to use the older Gtk.Menu approach
            # but we'll create a simplified version that works with available GTK components
            
            # Create menu items using available GTK 4 components
            # Note: We'll use a simplified approach since full MenuItem isn't available
            
            # Status display (using a simple action)
            self._setup_menu_actions()
            
            self.logger.debug("AppIndicator menu items created")
            
        except Exception as e:
            self.logger.error(f"Failed to create AppIndicator menu items: {e}")
            
    def _setup_menu_actions(self) -> None:
        """Set up menu actions for the application."""
        try:
            # Get the default application to add actions
            app = Gtk.Application.get_default()
            if not app:
                self.logger.warning("No default application found for menu actions")
                return
                
            # Create actions for menu items
            actions = [
                ("status", None, self._on_status_action),
                ("switch-dark", None, self._on_switch_to_dark_action),
                ("switch-light", None, self._on_switch_to_light_action),
                ("toggle-theme", None, self._on_toggle_theme_action),
                ("manual-mode", None, self._on_manual_mode_action),
                ("schedule-mode", None, self._on_schedule_mode_action),
                ("location-mode", None, self._on_location_mode_action),
                ("show-window", None, self._on_show_window_action),
                ("quit", None, self._on_quit_action),
            ]
            
            for action_name, parameter_type, callback in actions:
                action = Gio.SimpleAction.new(action_name, parameter_type)
                action.connect("activate", callback)
                app.add_action(action)
                
            self.logger.debug("Menu actions set up")
            
        except Exception as e:
            self.logger.error(f"Failed to set up menu actions: {e}")

    def _setup_callbacks(self) -> None:
        """Set up callbacks for mode controller events."""
        try:
            # Listen for mode and theme changes
            self._mode_controller.add_mode_change_callback(self._on_mode_changed)
            self._mode_controller.add_theme_change_callback(self._on_theme_changed)

            self.logger.debug("Tray callbacks set up")

        except Exception as e:
            self.logger.error(f"Failed to set up callbacks: {e}")

    def show(self) -> None:
        """Show the tray icon."""
        try:
            if self._indicator:
                self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                self._is_visible = True
                self.logger.info("Tray icon shown")
            else:
                self.logger.warning("Cannot show tray icon - no indicator available")

        except Exception as e:
            self.logger.error(f"Failed to show tray icon: {e}")

    def hide(self) -> None:
        """Hide the tray icon."""
        try:
            if self._indicator:
                self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
                self._is_visible = False
                self.logger.info("Tray icon hidden")

        except Exception as e:
            self.logger.error(f"Failed to hide tray icon: {e}")

    def is_visible(self) -> bool:
        """
        Check if tray icon is visible.

        Returns:
            True if visible, False otherwise
        """
        return self._is_visible

    def _update_icon(self) -> None:
        """Update tray icon based on current theme."""
        try:
            if not self._indicator:
                return

            current_theme = self._mode_controller.get_current_theme()
            
            # Set icon based on theme
            if current_theme == ThemeType.DARK:
                icon_name = "weather-clear-night-symbolic"  # Moon icon for dark theme
            else:
                icon_name = "weather-clear-symbolic"  # Sun icon for light theme

            self._indicator.set_icon(icon_name)
            self.logger.debug(f"Updated tray icon to: {icon_name}")

        except Exception as e:
            self.logger.error(f"Failed to update tray icon: {e}")

    def _update_menu_state(self) -> None:
        """Update menu items based on current mode and theme."""
        try:
            current_mode = self._mode_controller.get_current_mode()
            current_theme = self._mode_controller.get_current_theme()

            # Update current status for display
            mode_text = current_mode.value.title() if current_mode else "Unknown"
            theme_text = current_theme.value.title() if current_theme else "Unknown"
            self._current_status = f"Mode: {mode_text} | Theme: {theme_text}"
            
            # Update status item if available
            if self._status_item:
                self._status_item.set_label(f"Status: {self._current_status}")
            
            # Update theme items sensitivity based on mode
            # Theme switching is only available in manual mode
            if self._theme_items:
                for item in self._theme_items.values():
                    item.set_sensitive(current_mode == ThemeMode.MANUAL)
            
            # Update mode items to show which is active
            if self._mode_items and current_mode:
                for mode_key, item in self._mode_items.items():
                    # Highlight the active mode
                    if mode_key == current_mode.value:
                        # In GTK3, we can use a different label to indicate active state
                        item.set_label(f"✓ {mode_key.title()} Mode")
                    else:
                        item.set_label(f"{mode_key.title()} Mode")

            self.logger.debug("Updated menu state")

        except Exception as e:
            self.logger.error(f"Failed to update menu state: {e}")

    # Action handlers for Gio.SimpleAction callbacks
    def _on_status_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle status action (no-op, just for display)."""
        pass

    def _on_switch_to_dark_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle switch to dark theme action."""
        try:
            success = self._mode_controller.manual_switch_to_dark()
            if not success:
                self._show_error_notification("Failed to switch to dark theme")
            self.logger.info("Manual switch to dark theme requested")

        except Exception as e:
            self.logger.error(f"Error switching to dark theme: {e}")

    def _on_switch_to_light_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle switch to light theme action."""
        try:
            success = self._mode_controller.manual_switch_to_light()
            if not success:
                self._show_error_notification("Failed to switch to light theme")
            self.logger.info("Manual switch to light theme requested")

        except Exception as e:
            self.logger.error(f"Error switching to light theme: {e}")

    def _on_toggle_theme_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle toggle theme action."""
        try:
            success = self._mode_controller.manual_toggle_theme()
            if not success:
                self._show_error_notification("Failed to toggle theme")
            self.logger.info("Manual theme toggle requested")

        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")

    def _on_manual_mode_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle manual mode action."""
        try:
            success = self._mode_controller.set_manual_mode()
            if success:
                self._show_info_notification("Switched to manual mode")
            else:
                self._show_error_notification("Failed to switch to manual mode")
            self.logger.info("Manual mode requested")

        except Exception as e:
            self.logger.error(f"Error setting manual mode: {e}")

    def _on_schedule_mode_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle schedule mode action."""
        try:
            # For now, just show window to configure schedule
            # In a full implementation, this might show a quick setup dialog
            if self._show_window_callback:
                self._show_window_callback()
            self.logger.info("Schedule mode configuration requested")

        except Exception as e:
            self.logger.error(f"Error handling schedule mode: {e}")

    def _on_location_mode_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle location mode action."""
        try:
            # For now, just show window to configure location
            # In a full implementation, this might show a quick setup dialog
            if self._show_window_callback:
                self._show_window_callback()
            self.logger.info("Location mode configuration requested")

        except Exception as e:
            self.logger.error(f"Error handling location mode: {e}")

    def _on_show_window_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle show window action."""
        try:
            if self._show_window_callback:
                self._show_window_callback()
            self.logger.info("Show window requested")

        except Exception as e:
            self.logger.error(f"Error showing window: {e}")

    def _on_quit_action(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle quit action."""
        try:
            if self._quit_callback:
                self._quit_callback()
            self.logger.info("Quit requested")

        except Exception as e:
            self.logger.error(f"Error quitting application: {e}")

    # Compatibility methods for tests (without _action suffix)
    def _on_switch_to_dark(self, widget) -> None:
        """Handle switch to dark theme (compatibility method)."""
        self._on_switch_to_dark_action(None, None)

    def _on_switch_to_light(self, widget) -> None:
        """Handle switch to light theme (compatibility method)."""
        self._on_switch_to_light_action(None, None)

    def _on_toggle_theme(self, widget) -> None:
        """Handle toggle theme (compatibility method)."""
        self._on_toggle_theme_action(None, None)

    def _on_manual_mode(self, widget) -> None:
        """Handle manual mode (compatibility method)."""
        self._on_manual_mode_action(None, None)

    def _on_schedule_mode(self, widget) -> None:
        """Handle schedule mode (compatibility method)."""
        self._on_schedule_mode_action(None, None)

    def _on_location_mode(self, widget) -> None:
        """Handle location mode (compatibility method)."""
        self._on_location_mode_action(None, None)

    def _on_show_window(self, widget) -> None:
        """Handle show window (compatibility method)."""
        self._on_show_window_action(None, None)

    def _on_quit(self, widget) -> None:
        """Handle quit (compatibility method)."""
        self._on_quit_action(None, None)

    def _on_mode_changed(self, new_mode: ThemeMode, old_mode: Optional[ThemeMode]) -> None:
        """Handle mode change events."""
        try:
            self._update_menu_state()
            self._update_icon()
            
            # Show notification
            mode_name = new_mode.value.title()
            self._show_info_notification(f"Switched to {mode_name} mode")
            
            self.logger.info(f"Mode changed: {old_mode} -> {new_mode}")

        except Exception as e:
            self.logger.error(f"Error handling mode change: {e}")

    def _on_theme_changed(self, theme: ThemeType) -> None:
        """Handle theme change events."""
        try:
            self._update_menu_state()
            self._update_icon()
            
            # Show notification
            theme_name = theme.value.title()
            self._show_info_notification(f"Switched to {theme_name} theme")
            
            self.logger.info(f"Theme changed to: {theme}")

        except Exception as e:
            self.logger.error(f"Error handling theme change: {e}")

    def _show_info_notification(self, message: str) -> None:
        """Show an info notification."""
        try:
            notification = Gio.Notification.new("Nightswitch")
            notification.set_body(message)
            notification.set_icon(Gio.ThemedIcon.new("applications-system"))
            
            # Send notification through application
            app = Gtk.Application.get_default()
            if app:
                app.send_notification("nightswitch-info", notification)
            
            self.logger.debug(f"Sent info notification: {message}")

        except Exception as e:
            self.logger.error(f"Failed to send info notification: {e}")

    def _show_error_notification(self, message: str) -> None:
        """Show an error notification."""
        try:
            notification = Gio.Notification.new("Nightswitch Error")
            notification.set_body(message)
            notification.set_icon(Gio.ThemedIcon.new("dialog-error"))
            notification.set_priority(Gio.NotificationPriority.HIGH)
            
            # Send notification through application
            app = Gtk.Application.get_default()
            if app:
                app.send_notification("nightswitch-error", notification)
            
            self.logger.debug(f"Sent error notification: {message}")

        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")

    def cleanup(self) -> None:
        """Clean up tray icon resources."""
        try:
            # Remove callbacks
            self._mode_controller.remove_mode_change_callback(self._on_mode_changed)
            self._mode_controller.remove_theme_change_callback(self._on_theme_changed)

            # Hide tray icon
            self.hide()

            # Clear references
            self._indicator = None
            self._menu = None
            self._theme_items.clear()
            self._mode_items.clear()
            self._status_item = None

            self.logger.info("System tray cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during tray cleanup: {e}")


# Global system tray instance
_system_tray: Optional[SystemTrayIcon] = None


def get_system_tray() -> Optional[SystemTrayIcon]:
    """
    Get the global system tray instance.

    Returns:
        SystemTrayIcon instance or None if not initialized
    """
    return _system_tray


def create_system_tray(
    mode_controller: Optional[ModeController] = None,
    show_window_callback: Optional[Callable[[], None]] = None,
    quit_callback: Optional[Callable[[], None]] = None,
) -> SystemTrayIcon:
    """
    Create and initialize the global system tray instance.

    Args:
        mode_controller: Mode controller instance
        show_window_callback: Callback to show main window
        quit_callback: Callback to quit application

    Returns:
        SystemTrayIcon instance
    """
    global _system_tray
    if _system_tray is None:
        _system_tray = SystemTrayIcon(mode_controller, show_window_callback, quit_callback)
    return _system_tray


def cleanup_system_tray() -> None:
    """Clean up the global system tray instance."""
    global _system_tray
    if _system_tray:
        _system_tray.cleanup()
        _system_tray = None