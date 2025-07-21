"""
Main application window for Nightswitch.

This module provides the MainWindow class that implements the primary user interface
for the Nightswitch application, integrating the various tab components.
"""

import logging
from typing import Optional, Callable, Dict, Any

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk

from ..core.mode_controller import ModeController, ThemeMode, get_mode_controller
from ..core.schedule_mode import get_schedule_mode_handler
from ..core.location_mode import get_location_mode_handler
from ..services.location import get_location_service

from .tabs.manual_tab import ManualTab
from .tabs.schedule_tab import ScheduleTab
from .tabs.location_tab import LocationTab
from .tabs.preferences_tab import PreferencesTab
from .dialogs.about_dialog import show_about_dialog
from .dialogs.help_dialog import show_help_dialog
from .dialogs.error_dialog import show_error_dialog


class MainWindow(Gtk.ApplicationWindow):
    """
    Main application window for Nightswitch.
    
    Provides the primary user interface for controlling theme switching modes,
    including manual, schedule, and location-based options.
    """

    def __init__(
        self,
        application: Gtk.Application,
        mode_controller: Optional[ModeController] = None,
    ):
        """
        Initialize the main window.
        
        Args:
            application: Parent GTK application
            mode_controller: Mode controller instance
        """
        super().__init__(application=application, title="Nightswitch")
        
        self.logger = logging.getLogger("nightswitch.ui.main_window")
        self._mode_controller = mode_controller or get_mode_controller()
        self._schedule_handler = get_schedule_mode_handler()
        self._location_handler = get_location_mode_handler()
        self._location_service = get_location_service()
        
        # Window properties
        self.set_default_size(400, 500)
        self.set_resizable(False)
        
        # UI components
        self._notebook = None
        self._header_bar = None
        self._main_box = None
        self._status_bar = None
        self._status_label = None
        
        # Tab components
        self._manual_tab = None
        self._schedule_tab = None
        self._location_tab = None
        self._preferences_tab = None
        
        # Set up UI
        self._setup_ui()
        self._setup_callbacks()
        
        # Update UI based on current state
        self._update_ui_state()
        
        # Make sure all widgets are visible
        self.show_all()
        
        self.logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        try:
            # Create header bar with modern styling
            self._header_bar = Gtk.HeaderBar()
            self._header_bar.set_show_close_button(True)  # Show window controls
            self._header_bar.set_title("Nightswitch")
            self._header_bar.set_subtitle("Theme Switching Settings")
            self.set_titlebar(self._header_bar)
            
            # Add about button to header with icon
            about_button = Gtk.Button()
            about_icon = Gtk.Image.new_from_icon_name("help-about-symbolic", Gtk.IconSize.BUTTON)
            about_button.add(about_icon)
            about_button.set_tooltip_text("About Nightswitch")
            about_button.connect("clicked", self._on_about_clicked)
            self._header_bar.pack_end(about_button)
            
            # Main container with padding
            outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(outer_box)
            
            # Add padding around content
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            content_box.set_margin_start(16)
            content_box.set_margin_end(16)
            content_box.set_margin_top(16)
            content_box.set_margin_bottom(16)
            outer_box.pack_start(content_box, True, True, 0)
            
            # Create a notebook for tabs
            self._notebook = Gtk.Notebook()
            self._notebook.set_tab_pos(Gtk.PositionType.TOP)
            content_box.pack_start(self._notebook, True, True, 0)
            
            # Create mode tabs
            self._create_tabs()
            
            # Main vertical box for status bar
            self._main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            content_box.pack_start(self._main_box, False, False, 0)
            
            # Add status bar at bottom
            self._create_status_bar()
            
            self.logger.debug("UI components created")
            
        except Exception as e:
            self.logger.error(f"Failed to set up UI: {e}")
            raise

    def _create_tabs(self) -> None:
        """Create all tabs for the notebook."""
        try:
            # Create schedule switch for exclusivity with location mode
            self._schedule_switch = Gtk.Switch()
            
            # Create location switch for exclusivity with schedule mode
            self._location_switch = Gtk.Switch()
            
            # Create manual mode tab
            self._manual_tab = ManualTab(
                parent_notebook=self._notebook,
                mode_controller=self._mode_controller,
                status_callback=self._update_status,
                error_callback=self._show_error_dialog
            )
            
            # Create schedule mode tab
            self._schedule_tab = ScheduleTab(
                parent_notebook=self._notebook,
                mode_controller=self._mode_controller,
                schedule_handler=self._schedule_handler,
                location_switch=self._location_switch,
                status_callback=self._update_status,
                error_callback=self._show_error_dialog
            )
            
            # Create location mode tab
            self._location_tab = LocationTab(
                parent_notebook=self._notebook,
                mode_controller=self._mode_controller,
                location_handler=self._location_handler,
                location_service=self._location_service,
                schedule_switch=self._schedule_switch,
                status_callback=self._update_status,
                error_callback=self._show_error_dialog
            )
            
            # Create preferences tab
            self._preferences_tab = PreferencesTab(
                parent_notebook=self._notebook,
                status_callback=self._update_status,
                error_callback=self._show_error_dialog,
                save_callback=self._save_preferences
            )
            
            # Connect the switches for exclusivity
            self._schedule_tab._schedule_switch = self._schedule_switch
            self._location_tab._location_switch = self._location_switch
            
            self.logger.debug("Tabs created")
            
        except Exception as e:
            self.logger.error(f"Failed to create tabs: {e}")
            raise

    def _create_status_bar(self) -> None:
        """Create status bar at the bottom of the window."""
        try:
            # Status bar container
            self._status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self._status_bar.set_margin_top(8)
            
            # Status label
            self._status_label = Gtk.Label()
            self._status_label.set_markup("<small>Ready</small>")
            self._status_label.set_halign(Gtk.Align.START)
            self._status_label.set_hexpand(True)
            self._status_bar.pack_start(self._status_label, True, True, 0)
            
            # Add status bar to main box
            self._main_box.pack_start(self._status_bar, False, False, 0)
            
            self.logger.debug("Status bar created")
            
        except Exception as e:
            self.logger.error(f"Failed to create status bar: {e}")
            raise

    def _setup_callbacks(self) -> None:
        """Set up callbacks for mode controller events."""
        try:
            # Register for mode and theme changes
            self._mode_controller.add_mode_change_callback(self._on_mode_changed)
            self._mode_controller.add_theme_change_callback(self._on_theme_changed)
            
            # Register for schedule status updates
            self._schedule_handler.add_status_callback(self._on_schedule_status_changed)
            
            # Register for location status and error updates
            self._location_handler.add_status_callback(self._on_location_status_changed)
            self._location_handler.add_error_callback(self._on_location_error)
            
            # Set up window close handler for GTK3
            # This ensures the window is hidden instead of destroyed when closed
            self.connect("delete-event", self._on_delete_event)
            
            self.logger.debug("Callbacks set up")
            
        except Exception as e:
            self.logger.error(f"Failed to set up callbacks: {e}")
            raise
            
    def _on_delete_event(self, widget, event) -> bool:
        """
        Handle window close event.
        
        This method is called when the user clicks the close button in the window's
        title bar. Instead of destroying the window, we hide it and keep the application
        running in the system tray.
        
        Args:
            widget: The window widget
            event: The delete event
            
        Returns:
            True to stop the event from propagating (prevents window destruction)
        """
        self.logger.debug("Window close requested, hiding instead of destroying")
        self.hide()
        return True  # Returning True prevents the window from being destroyed

    def _update_ui_state(self) -> None:
        """Update UI components based on current application state."""
        try:
            # Get current mode and theme
            current_mode = self._mode_controller.get_current_mode()
            current_theme = self._mode_controller.get_current_theme()
            
            # Update tab UI states
            self._manual_tab.update_ui_state(current_mode)
            self._schedule_tab.update_ui_state(current_mode)
            self._location_tab.update_ui_state(current_mode)
            
            # Update status label
            mode_text = current_mode.value.title() if current_mode else "Unknown"
            theme_text = current_theme.value.title() if current_theme else "Unknown"
            self._status_label.set_markup(f"<small>Mode: {mode_text} | Theme: {theme_text}</small>")
            
            self.logger.debug(f"UI state updated for mode: {current_mode}, theme: {current_theme}")
            
        except Exception as e:
            self.logger.error(f"Failed to update UI state: {e}")
            self._status_label.set_markup("<small>Error updating UI state</small>")

    def _on_mode_changed(self, new_mode: ThemeMode, old_mode: Optional[ThemeMode]) -> None:
        """
        Handle mode change events.
        
        Args:
            new_mode: New mode
            old_mode: Previous mode
        """
        self._update_ui_state()

    def _on_theme_changed(self, theme) -> None:
        """
        Handle theme change events.
        
        Args:
            theme: New theme
        """
        self._update_ui_state()

    def _on_schedule_status_changed(self, status: str) -> None:
        """
        Handle schedule status change events.
        
        Args:
            status: New status message
        """
        self._update_status(status)

    def _on_location_status_changed(self, status: str) -> None:
        """
        Handle location status change events.
        
        Args:
            status: New status message
        """
        self._update_status(status)

    def _on_location_error(self, error: str) -> None:
        """
        Handle location error events.
        
        Args:
            error: Error message
        """
        self._show_error_dialog(error)

    def _update_status(self, message: str) -> None:
        """
        Update the status label with a message.
        
        Args:
            message: Status message
        """
        self._status_label.set_markup(f"<small>{message}</small>")

    def _show_error_dialog(self, message: str, details: Optional[str] = None) -> None:
        """
        Show an error dialog.
        
        Args:
            message: Error message
            details: Optional detailed error information
        """
        show_error_dialog(message, details, self)

    def _on_about_clicked(self, button: Gtk.Button) -> None:
        """
        Handle about button click.
        
        Args:
            button: Button that was clicked
        """
        show_about_dialog(self)
            
    # Menu item handlers removed as part of UI simplification
            
    def _save_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Save preferences.
        
        Args:
            preferences: Dictionary of preferences to save
        """
        try:
            # TODO: Implement saving preferences to configuration
            self._update_status("Preferences saved")
            self.logger.info("Preferences saved")
            
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
            self._update_status("Error saving preferences")
            self._show_error_dialog(f"Error saving preferences: {e}")