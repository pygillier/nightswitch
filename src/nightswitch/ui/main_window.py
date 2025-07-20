"""
Main application window for Nightswitch.

This module provides the MainWindow class that implements the primary user interface
for the Nightswitch application, including controls for manual, schedule, and
location-based theme switching.
"""

import logging
from typing import Optional, Callable, Dict, Any, Tuple

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk

from ..core.mode_controller import ModeController, ThemeMode, get_mode_controller
from ..core.manual_mode import ThemeType
from ..core.schedule_mode import get_schedule_mode_handler
from ..core.location_mode import get_location_mode_handler
from ..services.location import get_location_service


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
        self._main_box = None
        self._header_bar = None
        self._manual_group = None
        self._schedule_group = None
        self._location_group = None
        
        # Schedule mode widgets
        self._dark_time_entry = None
        self._light_time_entry = None
        self._schedule_switch = None
        
        # Location mode widgets
        self._location_switch = None
        self._auto_location_switch = None
        self._latitude_entry = None
        self._longitude_entry = None
        self._location_info_label = None
        self._next_event_label = None
        
        # Status widgets
        self._status_bar = None
        self._status_label = None
        
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
            
            # Add a menu button to header
            menu_button = Gtk.MenuButton()
            menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
            menu_button.add(menu_icon)
            menu_button.set_tooltip_text("Menu")
            
            # Create menu for the menu button
            menu = Gtk.Menu()
            
            # Add menu items
            preferences_item = Gtk.MenuItem.new_with_label("Preferences")
            preferences_item.connect("activate", self._on_preferences_clicked)
            menu.append(preferences_item)
            
            help_item = Gtk.MenuItem.new_with_label("Help")
            help_item.connect("activate", self._on_help_clicked)
            menu.append(help_item)
            
            menu.show_all()
            menu_button.set_popup(menu)
            
            self._header_bar.pack_end(menu_button)
            
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
            
            # Main vertical box for content
            self._main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
            content_box.pack_start(self._main_box, True, True, 0)
            
            # Create mode groups
            self._create_manual_group()
            self._create_schedule_group()
            self._create_location_group()
            
            # Add status bar at bottom
            self._create_status_bar()
            
            self.logger.debug("UI components created")
            
        except Exception as e:
            self.logger.error(f"Failed to set up UI: {e}")
            raise

    def _create_manual_group(self) -> None:
        """Create manual mode button group with Dark/Light options."""
        try:
            # Create frame with label
            frame = Gtk.Frame()
            frame.set_label("Manual Mode")
            self._main_box.pack_start(frame, False, True, 0)
            
            # Container for manual controls
            manual_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            manual_box.set_margin_start(12)
            manual_box.set_margin_end(12)
            manual_box.set_margin_top(12)
            manual_box.set_margin_bottom(12)
            frame.add(manual_box)
            
            # Description label
            description = Gtk.Label()
            description.set_markup("<small>Directly control the theme with these buttons</small>")
            description.set_halign(Gtk.Align.START)
            # description.set_wrap(True)
            manual_box.pack_start(description, False, False, 0)
            
            # Button box for theme controls
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            button_box.set_halign(Gtk.Align.CENTER)
            manual_box.pack_start(button_box, False, False, 0)
            
            # Dark theme button
            dark_button = Gtk.Button(label="Dark Theme")
            dark_button.connect("clicked", self._on_dark_button_clicked)
            dark_button.set_hexpand(True)
            button_box.pack_start(dark_button, True, True, 0)
            
            # Light theme button
            light_button = Gtk.Button(label="Light Theme")
            light_button.connect("clicked", self._on_light_button_clicked)
            light_button.set_hexpand(True)
            button_box.pack_start(light_button, True, True, 0)
            
            # Toggle button
            toggle_button = Gtk.Button(label="Toggle Theme")
            toggle_button.connect("clicked", self._on_toggle_button_clicked)
            toggle_button.set_margin_top(8)
            toggle_button.set_hexpand(True)
            manual_box.pack_start(toggle_button, False, False, 0)
            
            # Store reference to group
            self._manual_group = frame
            
            self.logger.debug("Manual mode group created")
            
        except Exception as e:
            self.logger.error(f"Failed to create manual group: {e}")
            raise

    def _create_schedule_group(self) -> None:
        """Create schedule mode toggle group with time input fields."""
        try:
            # Create frame with label
            frame = Gtk.Frame()
            frame.set_label("Schedule Mode")
            self._main_box.pack_start(frame, False, True, 0)
            
            # Container for schedule controls
            schedule_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            schedule_box.set_margin_start(12)
            schedule_box.set_margin_end(12)
            schedule_box.set_margin_top(12)
            schedule_box.set_margin_bottom(12)
            frame.add(schedule_box)
            
            # Enable switch row
            switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            switch_box.set_margin_bottom(8)
            schedule_box.pack_start(switch_box, False, True, 0)
            
            switch_label = Gtk.Label(label="Enable Schedule Mode")
            switch_label.set_hexpand(True)
            switch_label.set_halign(Gtk.Align.START)
            switch_box.pack_start(switch_label, True, True, 0)
            
            self._schedule_switch = Gtk.Switch()
            self._schedule_switch.set_halign(Gtk.Align.END)
            self._schedule_switch.connect("state-set", self._on_schedule_switch_toggled)
            switch_box.pack_start(self._schedule_switch, False, False, 0)
            
            # Description label
            description = Gtk.Label()
            description.set_markup("<small>Automatically switch themes at specific times</small>")
            description.set_halign(Gtk.Align.START)
            # description.set_wrap(True)
            schedule_box.pack_start(description, False, False, 0)
            
            # Time settings grid
            grid = Gtk.Grid()
            grid.set_column_spacing(12)
            grid.set_row_spacing(8)
            schedule_box.pack_start(grid, False, False, 0)
            
            # Dark time row
            dark_label = Gtk.Label(label="Switch to Dark:")
            dark_label.set_halign(Gtk.Align.START)
            grid.attach(dark_label, 0, 0, 1, 1)
            
            self._dark_time_entry = Gtk.Entry()
            self._dark_time_entry.set_placeholder_text("HH:MM")
            self._dark_time_entry.set_max_length(5)
            self._dark_time_entry.set_width_chars(5)
            self._dark_time_entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
            grid.attach(self._dark_time_entry, 1, 0, 1, 1)
            
            # Light time row
            light_label = Gtk.Label(label="Switch to Light:")
            light_label.set_halign(Gtk.Align.START)
            grid.attach(light_label, 0, 1, 1, 1)
            
            self._light_time_entry = Gtk.Entry()
            self._light_time_entry.set_placeholder_text("HH:MM")
            self._light_time_entry.set_max_length(5)
            self._light_time_entry.set_width_chars(5)
            self._light_time_entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
            grid.attach(self._light_time_entry, 1, 1, 1, 1)
            
            # Apply button
            apply_button = Gtk.Button(label="Apply Schedule")
            apply_button.connect("clicked", self._on_apply_schedule_clicked)
            apply_button.set_margin_top(8)
            schedule_box.pack_start(apply_button, False, False, 0)
            
            # Next trigger info label
            self._next_schedule_label = Gtk.Label()
            self._next_schedule_label.set_markup("<small>No schedule active</small>")
            self._next_schedule_label.set_halign(Gtk.Align.START)
            self._next_schedule_label.set_margin_top(4)
            schedule_box.pack_start(self._next_schedule_label, False, False, 0)
            
            # Store reference to group
            self._schedule_group = frame
            
            self.logger.debug("Schedule mode group created")
            
        except Exception as e:
            self.logger.error(f"Failed to create schedule group: {e}")
            raise

    def _create_location_group(self) -> None:
        """Create location mode toggle group with settings interface."""
        try:
            # Create frame with label
            frame = Gtk.Frame()
            frame.set_label("Location Mode")
            self._main_box.pack_start(frame, False, True, 0)
            
            # Container for location controls
            location_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            location_box.set_margin_start(12)
            location_box.set_margin_end(12)
            location_box.set_margin_top(12)
            location_box.set_margin_bottom(12)
            frame.add(location_box)
            
            # Enable switch row
            switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            switch_box.set_margin_bottom(8)
            location_box.pack_start(switch_box, False, True, 0)
            
            switch_label = Gtk.Label(label="Enable Location Mode")
            switch_label.set_hexpand(True)
            switch_label.set_halign(Gtk.Align.START)
            switch_box.pack_start(switch_label, True, True, 0)
            
            self._location_switch = Gtk.Switch()
            self._location_switch.set_halign(Gtk.Align.END)
            self._location_switch.connect("state-set", self._on_location_switch_toggled)
            switch_box.pack_start(self._location_switch, False, False, 0)
            
            # Description label
            description = Gtk.Label()
            description.set_markup("<small>Automatically switch themes based on sunrise and sunset times</small>")
            description.set_halign(Gtk.Align.START)
            # description.set_wrap(True)
            location_box.pack_start(description, False, False, 0)
            
            # Auto-location switch
            auto_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            location_box.pack_start(auto_box, False, True, 0)
            
            auto_label = Gtk.Label(label="Auto-detect Location")
            auto_label.set_hexpand(True)
            auto_label.set_halign(Gtk.Align.START)
            auto_box.pack_start(auto_label, True, True, 0)
            
            self._auto_location_switch = Gtk.Switch()
            self._auto_location_switch.set_active(True)
            self._auto_location_switch.set_halign(Gtk.Align.END)
            self._auto_location_switch.connect("state-set", self._on_auto_location_switch_toggled)
            auto_box.pack_start(self._auto_location_switch, False, False, 0)
            
            # Manual coordinates grid
            coords_grid = Gtk.Grid()
            coords_grid.set_column_spacing(12)
            coords_grid.set_row_spacing(8)
            coords_grid.set_margin_top(8)
            location_box.pack_start(coords_grid, False, False, 0)
            
            # Latitude row
            lat_label = Gtk.Label(label="Latitude:")
            lat_label.set_halign(Gtk.Align.START)
            coords_grid.attach(lat_label, 0, 0, 1, 1)
            
            self._latitude_entry = Gtk.Entry()
            self._latitude_entry.set_placeholder_text("e.g. 51.5074")
            self._latitude_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
            coords_grid.attach(self._latitude_entry, 1, 0, 1, 1)
            
            # Longitude row
            lon_label = Gtk.Label(label="Longitude:")
            lon_label.set_halign(Gtk.Align.START)
            coords_grid.attach(lon_label, 0, 1, 1, 1)
            
            self._longitude_entry = Gtk.Entry()
            self._longitude_entry.set_placeholder_text("e.g. -0.1278")
            self._longitude_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
            coords_grid.attach(self._longitude_entry, 1, 1, 1, 1)
            
            # Apply button
            apply_button = Gtk.Button(label="Apply Location")
            apply_button.connect("clicked", self._on_apply_location_clicked)
            apply_button.set_margin_top(8)
            location_box.pack_start(apply_button, False, False, 0)
            
            # Location info label
            self._location_info_label = Gtk.Label()
            self._location_info_label.set_markup("<small>No location detected</small>")
            self._location_info_label.set_halign(Gtk.Align.START)
            self._location_info_label.set_margin_top(4)
            location_box.pack_start(self._location_info_label, False, False, 0)
            
            # Next event info label
            self._next_event_label = Gtk.Label()
            self._next_event_label.set_markup("<small>No sunrise/sunset data available</small>")
            self._next_event_label.set_halign(Gtk.Align.START)
            self._next_event_label.set_margin_top(4)
            location_box.pack_start(self._next_event_label, False, False, 0)
            
            # Store reference to group
            self._location_group = frame
            
            self.logger.debug("Location mode group created")
            
        except Exception as e:
            self.logger.error(f"Failed to create location group: {e}")
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
            
            # Update mode-specific UI elements
            self._update_manual_ui(current_mode)
            self._update_schedule_ui(current_mode)
            self._update_location_ui(current_mode)
            
            # Update status label
            mode_text = current_mode.value.title() if current_mode else "Unknown"
            theme_text = current_theme.value.title() if current_theme else "Unknown"
            self._status_label.set_markup(f"<small>Mode: {mode_text} | Theme: {theme_text}</small>")
            
            self.logger.debug(f"UI state updated for mode: {current_mode}, theme: {current_theme}")
            
        except Exception as e:
            self.logger.error(f"Failed to update UI state: {e}")
            self._status_label.set_markup("<small>Error updating UI state</small>")

    def _update_manual_ui(self, current_mode: ThemeMode) -> None:
        """
        Update manual mode UI components.
        
        Args:
            current_mode: Current active mode
        """
        # Manual mode is always available but may be disabled if another mode is active
        is_manual_active = (current_mode == ThemeMode.MANUAL)
        
        # In GTK4, we need to use CSS for visual indication of active mode
        if is_manual_active:
            # Add visual indication that manual mode is active
            context = self._manual_group.get_style_context()
            context.add_class("active-mode-frame")
        else:
            # Remove visual indication
            context = self._manual_group.get_style_context()
            context.remove_class("active-mode-frame")

    def _update_schedule_ui(self, current_mode: ThemeMode) -> None:
        """
        Update schedule mode UI components.
        
        Args:
            current_mode: Current active mode
        """
        try:
            # Check if schedule mode is active
            is_schedule_active = (current_mode == ThemeMode.SCHEDULE)
            
            # Update switch state without triggering callback
            self._schedule_switch.set_active(is_schedule_active)
            
            # Get schedule times if available
            dark_time, light_time = self._schedule_handler.get_schedule_times()
            
            # Update time entries
            if dark_time:
                self._dark_time_entry.set_text(dark_time)
            
            if light_time:
                self._light_time_entry.set_text(light_time)
            
            # Update next trigger info
            next_trigger = self._schedule_handler.get_next_trigger()
            if next_trigger and is_schedule_active:
                time_str, theme_str = next_trigger
                self._next_schedule_label.set_markup(
                    f"<small>Next: Switch to {theme_str} at {time_str}</small>"
                )
            else:
                self._next_schedule_label.set_markup("<small>No schedule active</small>")
            
            # Visual indication of active mode
            if is_schedule_active:
                context = self._schedule_group.get_style_context()
                context.add_class("active-mode-frame")
            else:
                context = self._schedule_group.get_style_context()
                context.remove_class("active-mode-frame")
                
        except Exception as e:
            self.logger.error(f"Failed to update schedule UI: {e}")
            self._next_schedule_label.set_markup("<small>Error updating schedule information</small>")

    def _update_location_ui(self, current_mode: ThemeMode) -> None:
        """
        Update location mode UI components.
        
        Args:
            current_mode: Current active mode
        """
        try:
            # Check if location mode is active
            is_location_active = (current_mode == ThemeMode.LOCATION)
            
            # Update switch state without triggering callback
            self._location_switch.set_active(is_location_active)
            
            # Update auto-location switch
            is_auto_location = self._location_handler.is_auto_location()
            self._auto_location_switch.set_active(is_auto_location)
            
            # Enable/disable coordinate entries based on auto-location
            self._latitude_entry.set_sensitive(not is_auto_location)
            self._longitude_entry.set_sensitive(not is_auto_location)
            
            # Get current location if available
            location = self._location_handler.get_current_location()
            if location and is_location_active:
                lat, lon, description = location
                
                # Update coordinate entries if using manual location
                if not is_auto_location:
                    self._latitude_entry.set_text(str(lat))
                    self._longitude_entry.set_text(str(lon))
                
                # Update location info label
                self._location_info_label.set_markup(f"<small>Location: {description}</small>")
                
                # Update next event info
                next_event = self._location_handler.get_next_sun_event()
                if next_event:
                    event_time, event_type, event_date = next_event
                    self._next_event_label.set_markup(
                        f"<small>Next: {event_type.title()} at {event_time}</small>"
                    )
                else:
                    self._next_event_label.set_markup("<small>No sunrise/sunset data available</small>")
            else:
                self._location_info_label.set_markup("<small>No location detected</small>")
                self._next_event_label.set_markup("<small>No sunrise/sunset data available</small>")
            
            # Visual indication of active mode
            if is_location_active:
                context = self._location_group.get_style_context()
                context.add_class("active-mode-frame")
            else:
                context = self._location_group.get_style_context()
                context.remove_class("active-mode-frame")
                
        except Exception as e:
            self.logger.error(f"Failed to update location UI: {e}")
            self._location_info_label.set_markup("<small>Error updating location information</small>")

    def _on_dark_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle dark theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            self._status_label.set_markup("<small>Switching to dark theme...</small>")
            success = self._mode_controller.manual_switch_to_dark()
            
            if not success:
                self._status_label.set_markup("<small>Failed to switch to dark theme</small>")
                self._show_error_dialog("Failed to switch to dark theme")
                
        except Exception as e:
            self.logger.error(f"Error switching to dark theme: {e}")
            self._status_label.set_markup("<small>Error switching to dark theme</small>")
            self._show_error_dialog(f"Error switching to dark theme: {e}")

    def _on_light_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle light theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            self._status_label.set_markup("<small>Switching to light theme...</small>")
            success = self._mode_controller.manual_switch_to_light()
            
            if not success:
                self._status_label.set_markup("<small>Failed to switch to light theme</small>")
                self._show_error_dialog("Failed to switch to light theme")
                
        except Exception as e:
            self.logger.error(f"Error switching to light theme: {e}")
            self._status_label.set_markup("<small>Error switching to light theme</small>")
            self._show_error_dialog(f"Error switching to light theme: {e}")

    def _on_toggle_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle toggle theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            self._status_label.set_markup("<small>Toggling theme...</small>")
            success = self._mode_controller.manual_toggle_theme()
            
            if not success:
                self._status_label.set_markup("<small>Failed to toggle theme</small>")
                self._show_error_dialog("Failed to toggle theme")
                
        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")
            self._status_label.set_markup("<small>Error toggling theme</small>")
            self._show_error_dialog(f"Error toggling theme: {e}")

    def _on_schedule_switch_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        """
        Handle schedule mode switch toggle.
        
        Args:
            switch: Switch that was toggled
            state: New switch state
            
        Returns:
            True to allow state change, False to prevent it
        """
        try:
            if state:
                # Get time values from entries
                dark_time = self._dark_time_entry.get_text()
                light_time = self._light_time_entry.get_text()
                
                # Validate times
                valid, error_msg = self._schedule_handler.validate_schedule_times(dark_time, light_time)
                if not valid:
                    self._status_label.set_markup(f"<small>{error_msg}</small>")
                    self._show_error_dialog(error_msg)
                    return False  # Prevent switch from turning on
                
                # Enable schedule mode
                self._status_label.set_markup("<small>Enabling schedule mode...</small>")
                success = self._mode_controller.set_schedule_mode(dark_time, light_time)
                
                if not success:
                    self._status_label.set_markup("<small>Failed to enable schedule mode</small>")
                    self._show_error_dialog("Failed to enable schedule mode")
                    return False  # Prevent switch from turning on
            else:
                # Disable schedule mode (switch to manual)
                self._status_label.set_markup("<small>Disabling schedule mode...</small>")
                success = self._mode_controller.set_manual_mode()
                
                if not success:
                    self._status_label.set_markup("<small>Failed to disable schedule mode</small>")
                    self._show_error_dialog("Failed to disable schedule mode")
                    return False  # Prevent switch from turning off
            
            return True  # Allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling schedule mode: {e}")
            self._status_label.set_markup("<small>Error toggling schedule mode</small>")
            self._show_error_dialog(f"Error toggling schedule mode: {e}")
            return False  # Prevent switch state change on error

    def _on_apply_schedule_clicked(self, button: Gtk.Button) -> None:
        """
        Handle apply schedule button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            # Get time values from entries
            dark_time = self._dark_time_entry.get_text()
            light_time = self._light_time_entry.get_text()
            
            # Validate times
            valid, error_msg = self._schedule_handler.validate_schedule_times(dark_time, light_time)
            if not valid:
                self._status_label.set_markup(f"<small>{error_msg}</small>")
                self._show_error_dialog(error_msg)
                return
            
            # Enable schedule mode
            self._status_label.set_markup("<small>Applying schedule...</small>")
            success = self._mode_controller.set_schedule_mode(dark_time, light_time)
            
            if not success:
                self._status_label.set_markup("<small>Failed to apply schedule</small>")
                self._show_error_dialog("Failed to apply schedule")
                
        except Exception as e:
            self.logger.error(f"Error applying schedule: {e}")
            self._status_label.set_markup("<small>Error applying schedule</small>")
            self._show_error_dialog(f"Error applying schedule: {e}")

    def _on_location_switch_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        """
        Handle location mode switch toggle.
        
        Args:
            switch: Switch that was toggled
            state: New switch state
            
        Returns:
            True to allow state change, False to prevent it
        """
        try:
            if state:
                # Check if we're using auto or manual location
                is_auto = self._auto_location_switch.get_active()
                
                if is_auto:
                    # Enable location mode with auto-detection
                    self._status_label.set_markup("<small>Enabling location mode with auto-detection...</small>")
                    success = self._mode_controller.set_location_mode()
                else:
                    # Get coordinates from entries
                    try:
                        latitude = float(self._latitude_entry.get_text())
                        longitude = float(self._longitude_entry.get_text())
                    except ValueError:
                        self._status_label.set_markup("<small>Invalid coordinates format</small>")
                        self._show_error_dialog("Please enter valid latitude and longitude values")
                        return False  # Prevent switch from turning on
                    
                    # Enable location mode with manual coordinates
                    self._status_label.set_markup("<small>Enabling location mode with manual coordinates...</small>")
                    success = self._mode_controller.set_location_mode(latitude, longitude)
                
                if not success:
                    self._status_label.set_markup("<small>Failed to enable location mode</small>")
                    self._show_error_dialog("Failed to enable location mode")
                    return False  # Prevent switch from turning on
            else:
                # Disable location mode (switch to manual)
                self._status_label.set_markup("<small>Disabling location mode...</small>")
                success = self._mode_controller.set_manual_mode()
                
                if not success:
                    self._status_label.set_markup("<small>Failed to disable location mode</small>")
                    self._show_error_dialog("Failed to disable location mode")
                    return False  # Prevent switch from turning off
            
            return True  # Allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling location mode: {e}")
            self._status_label.set_markup("<small>Error toggling location mode</small>")
            self._show_error_dialog(f"Error toggling location mode: {e}")
            return False  # Prevent switch state change on error

    def _on_auto_location_switch_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        """
        Handle auto-location switch toggle.
        
        Args:
            switch: Switch that was toggled
            state: New switch state
            
        Returns:
            True to allow state change, False to prevent it
        """
        try:
            # Update sensitivity of coordinate entries
            self._latitude_entry.set_sensitive(not state)
            self._longitude_entry.set_sensitive(not state)
            
            # If location mode is active, we need to update it
            current_mode = self._mode_controller.get_current_mode()
            if current_mode == ThemeMode.LOCATION:
                if state:
                    # Switch to auto-location
                    self._status_label.set_markup("<small>Switching to auto-location...</small>")
                    success = self._mode_controller.set_location_mode()
                else:
                    # Try to get coordinates from entries
                    try:
                        latitude = float(self._latitude_entry.get_text())
                        longitude = float(self._longitude_entry.get_text())
                    except ValueError:
                        # If no valid coordinates, just allow the switch to toggle
                        # but don't update the location mode
                        return True
                    
                    # Switch to manual coordinates
                    self._status_label.set_markup("<small>Switching to manual coordinates...</small>")
                    success = self._mode_controller.set_location_mode(latitude, longitude)
                
                if not success:
                    self._status_label.set_markup("<small>Failed to update location mode</small>")
                    # Allow the switch to toggle anyway
            
            return True  # Always allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling auto-location: {e}")
            self._status_label.set_markup("<small>Error toggling auto-location</small>")
            return True  # Allow state change even on error

    def _on_apply_location_clicked(self, button: Gtk.Button) -> None:
        """
        Handle apply location button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            # Check if we're using auto or manual location
            is_auto = self._auto_location_switch.get_active()
            
            if is_auto:
                # Enable location mode with auto-detection
                self._status_label.set_markup("<small>Applying auto-location...</small>")
                success = self._mode_controller.set_location_mode()
            else:
                # Get coordinates from entries
                try:
                    latitude = float(self._latitude_entry.get_text())
                    longitude = float(self._longitude_entry.get_text())
                except ValueError:
                    self._status_label.set_markup("<small>Invalid coordinates format</small>")
                    self._show_error_dialog("Please enter valid latitude and longitude values")
                    return
                
                # Validate coordinates
                if not self._location_handler._validate_coordinates(latitude, longitude):
                    self._status_label.set_markup("<small>Invalid coordinates range</small>")
                    self._show_error_dialog("Latitude must be between -90 and 90, longitude between -180 and 180")
                    return
                
                # Enable location mode with manual coordinates
                self._status_label.set_markup("<small>Applying manual coordinates...</small>")
                success = self._mode_controller.set_location_mode(latitude, longitude)
            
            if not success:
                self._status_label.set_markup("<small>Failed to apply location settings</small>")
                self._show_error_dialog("Failed to apply location settings")
                
        except Exception as e:
            self.logger.error(f"Error applying location: {e}")
            self._status_label.set_markup("<small>Error applying location</small>")
            self._show_error_dialog(f"Error applying location: {e}")

    def _on_about_clicked(self, button: Gtk.Button) -> None:
        """
        Handle about button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            # Create about dialog
            dialog = Gtk.AboutDialog()
            dialog.set_transient_for(self)
            dialog.set_modal(True)
            
            # Set dialog properties
            dialog.set_program_name("Nightswitch")
            dialog.set_version("1.0.0")
            dialog.set_copyright("© 2025 Nightswitch Contributors")
            dialog.set_comments("Automatic theme switching for Linux desktop environments")
            dialog.set_website("https://github.com/example/nightswitch")
            dialog.set_website_label("GitHub Repository")
            dialog.set_license_type(Gtk.License.GPL_3_0)
            
            # Set authors
            dialog.set_authors(["Nightswitch Contributors"])
            
            # Show dialog
            dialog.show()
            
        except Exception as e:
            self.logger.error(f"Error showing about dialog: {e}")
            
    def _on_preferences_clicked(self, menu_item: Gtk.MenuItem) -> None:
        """
        Handle preferences menu item click.
        
        Args:
            menu_item: Menu item that was clicked
        """
        try:
            self._show_preferences_dialog()
            self.logger.debug("Preferences dialog requested")
        except Exception as e:
            self.logger.error(f"Error showing preferences dialog: {e}")
            
    def _on_help_clicked(self, menu_item: Gtk.MenuItem) -> None:
        """
        Handle help menu item click.
        
        Args:
            menu_item: Menu item that was clicked
        """
        try:
            self._show_help_dialog()
            self.logger.debug("Help dialog requested")
        except Exception as e:
            self.logger.error(f"Error showing help dialog: {e}")
            
    def _show_preferences_dialog(self) -> None:
        """Show the preferences dialog."""
        dialog = Gtk.Dialog(
            title="Preferences",
            parent=self,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons=(
                "Cancel", Gtk.ResponseType.CANCEL,
                "Save", Gtk.ResponseType.APPLY
            )
        )
        dialog.set_default_size(350, 300)
        
        # Create content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_start(12)
        content_area.set_margin_end(12)
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        
        # Create notebook for tabs
        notebook = Gtk.Notebook()
        content_area.pack_start(notebook, True, True, 0)
        
        # General settings tab
        general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        general_box.set_margin_start(12)
        general_box.set_margin_end(12)
        general_box.set_margin_top(12)
        general_box.set_margin_bottom(12)
        notebook.append_page(general_box, Gtk.Label(label="General"))
        
        # Start minimized option
        start_min_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        start_min_label = Gtk.Label(label="Start minimized to tray")
        start_min_label.set_halign(Gtk.Align.START)
        start_min_label.set_hexpand(True)
        start_min_switch = Gtk.Switch()
        start_min_switch.set_active(True)  # Default to true
        
        start_min_box.pack_start(start_min_label, True, True, 0)
        start_min_box.pack_start(start_min_switch, False, False, 0)
        general_box.pack_start(start_min_box, False, False, 0)
        
        # Show notifications option
        notif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        notif_label = Gtk.Label(label="Show notifications")
        notif_label.set_halign(Gtk.Align.START)
        notif_label.set_hexpand(True)
        notif_switch = Gtk.Switch()
        notif_switch.set_active(True)  # Default to true
        
        notif_box.pack_start(notif_label, True, True, 0)
        notif_box.pack_start(notif_switch, False, False, 0)
        general_box.pack_start(notif_box, False, False, 0)
        
        # Autostart option
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        autostart_label = Gtk.Label(label="Start on system boot")
        autostart_label.set_halign(Gtk.Align.START)
        autostart_label.set_hexpand(True)
        autostart_switch = Gtk.Switch()
        autostart_switch.set_active(False)  # Default to false
        
        autostart_box.pack_start(autostart_label, True, True, 0)
        autostart_box.pack_start(autostart_switch, False, False, 0)
        general_box.pack_start(autostart_box, False, False, 0)
        
        # Advanced settings tab
        advanced_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        advanced_box.set_margin_start(12)
        advanced_box.set_margin_end(12)
        advanced_box.set_margin_top(12)
        advanced_box.set_margin_bottom(12)
        notebook.append_page(advanced_box, Gtk.Label(label="Advanced"))
        
        # Log level option
        log_level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        log_level_label = Gtk.Label(label="Log Level")
        log_level_label.set_halign(Gtk.Align.START)
        log_level_combo = Gtk.ComboBoxText()
        for level in ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]:
            log_level_combo.append_text(level)
        log_level_combo.set_active(0)  # Default to INFO
        
        log_level_box.pack_start(log_level_label, False, False, 0)
        log_level_box.pack_start(log_level_combo, True, True, 0)
        advanced_box.pack_start(log_level_box, False, False, 0)
        
        # Debug mode option
        debug_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        debug_label = Gtk.Label(label="Debug Mode")
        debug_label.set_halign(Gtk.Align.START)
        debug_label.set_hexpand(True)
        debug_switch = Gtk.Switch()
        debug_switch.set_active(False)  # Default to false
        
        debug_box.pack_start(debug_label, True, True, 0)
        debug_box.pack_start(debug_switch, False, False, 0)
        advanced_box.pack_start(debug_box, False, False, 0)
        
        # Show the dialog
        dialog.show_all()
        
        # Handle response
        response = dialog.run()
        if response == Gtk.ResponseType.APPLY:
            # Save preferences
            self.logger.info("Saving preferences")
            # TODO: Implement saving preferences
        
        dialog.destroy()
            
    def _show_help_dialog(self) -> None:
        try:
            """Show the help dialog."""
            dialog = Gtk.Dialog(
                title="Help",
                parent=self,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                buttons=("Close", Gtk.ResponseType.CLOSE)
            )
            dialog.set_default_size(400, 300)
            
            # Create content area
            content_area = dialog.get_content_area()
            content_area.set_spacing(10)
            content_area.set_margin_start(12)
            content_area.set_margin_end(12)
            content_area.set_margin_top(12)
            content_area.set_margin_bottom(12)
            
            # Add help content
            help_label = Gtk.Label()
            help_label.set_markup(
                "<b>Nightswitch Help</b>\n\n"
                "<b>Manual Mode:</b>\n"
                "Directly control the theme with the Dark/Light buttons.\n\n"
                "<b>Schedule Mode:</b>\n"
                "Set specific times to automatically switch between dark and light themes.\n\n"
                "<b>Location Mode:</b>\n"
                "Automatically switch themes based on sunrise and sunset times for your location.\n\n"
                "<b>System Tray:</b>\n"
                "Use the system tray icon to quickly toggle themes or access settings."
            )
            help_label.set_line_wrap(True)
            help_label.set_halign(Gtk.Align.START)
            help_label.set_valign(Gtk.Align.START)
            
            content_area.pack_start(help_label, True, True, 0)
            
            # Show the dialog
            dialog.show_all()
            dialog.run()
            dialog.destroy()
        except Exception as e:
            self.logger.error(f"Error showing about dialog: {e}")
            self._show_error_dialog(f"Error showing about dialog: {e}")

    def _on_mode_changed(self, new_mode: ThemeMode, old_mode: Optional[ThemeMode]) -> None:
        """
        Handle mode change events.
        
        Args:
            new_mode: New mode that was activated
            old_mode: Previous mode that was active
        """
        try:
            # Update UI state
            self._update_ui_state()
            
            # Update status label
            self._status_label.set_markup(f"<small>Switched to {new_mode.value} mode</small>")
            
            self.logger.info(f"Mode changed: {old_mode} -> {new_mode}")
            
        except Exception as e:
            self.logger.error(f"Error handling mode change: {e}")
            self._status_label.set_markup("<small>Error handling mode change</small>")

    def _on_theme_changed(self, theme: ThemeType) -> None:
        """
        Handle theme change events.
        
        Args:
            theme: New theme that was applied
        """
        try:
            # Update UI state
            self._update_ui_state()
            
            # Update status label
            self._status_label.set_markup(f"<small>Switched to {theme.value} theme</small>")
            
            self.logger.info(f"Theme changed to: {theme}")
            
        except Exception as e:
            self.logger.error(f"Error handling theme change: {e}")
            self._status_label.set_markup("<small>Error handling theme change</small>")

    def _on_schedule_status_changed(self, status: Dict[str, Any]) -> None:
        """
        Handle schedule status change events.
        
        Args:
            status: Schedule status information
        """
        try:
            # Only update if schedule mode is active
            current_mode = self._mode_controller.get_current_mode()
            if current_mode == ThemeMode.SCHEDULE:
                self._update_schedule_ui(current_mode)
                
        except Exception as e:
            self.logger.error(f"Error handling schedule status change: {e}")

    def _on_location_status_changed(self, status: Dict[str, Any]) -> None:
        """
        Handle location status change events.
        
        Args:
            status: Location status information
        """
        try:
            # Only update if location mode is active
            current_mode = self._mode_controller.get_current_mode()
            if current_mode == ThemeMode.LOCATION:
                self._update_location_ui(current_mode)
                
        except Exception as e:
            self.logger.error(f"Error handling location status change: {e}")

    def _on_location_error(self, error_type: str, error_message: str) -> None:
        """
        Handle location error events.
        
        Args:
            error_type: Type of error that occurred
            error_message: Human-readable error message
        """
        try:
            # Show error in status bar
            self._status_label.set_markup(f"<small>Location error: {error_message}</small>")
            
            # Show error dialog for important errors
            if error_type in ["location_detection_failed", "invalid_coordinates", "api_error"]:
                self._show_error_dialog(f"Location error: {error_message}")
                
            self.logger.error(f"Location error ({error_type}): {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling location error: {e}")

    def _on_close_request(self, window: Gtk.Window) -> bool:
        """
        Handle window close request.
        
        Args:
            window: Window being closed
            
        Returns:
            False to allow default close behavior
        """
        try:
            # Clean up callbacks
            self._mode_controller.remove_mode_change_callback(self._on_mode_changed)
            self._mode_controller.remove_theme_change_callback(self._on_theme_changed)
            
            self._schedule_handler.remove_status_callback(self._on_schedule_status_changed)
            
            self._location_handler.remove_status_callback(self._on_location_status_changed)
            self._location_handler.remove_error_callback(self._on_location_error)
            
            self.logger.info("Main window closing, callbacks removed")
            
        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            
        return False  # Allow window to close

    def _show_error_dialog(self, message: str) -> None:
        """
        Show an error dialog with the given message.
        
        Args:
            message: Error message to display
        """
        try:
            # Create dialog
            dialog = Gtk.AlertDialog.new(message)
            dialog.set_modal(True)
            dialog.set_buttons(["OK"])
            dialog.set_detail("Please check the application logs for more information.")
            
            # Show dialog
            dialog.show(self)
            
        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")
            # Fall back to status label
            self._status_label.set_markup(f"<small>Error: {message}</small>")

    def add_css_provider(self) -> None:
        """Add custom CSS styling for the application."""
        try:
            # Create CSS provider
            provider = Gtk.CssProvider()
            
            # Define CSS
            css = """
            frame.active-mode-frame {
                border: 2px solid @accent_color;
            }
            """
            
            # Load CSS
            provider.load_from_data(css.encode())
            
            # Add provider to default display
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                
            self.logger.debug("CSS provider added")
            
        except Exception as e:
            self.logger.error(f"Failed to add CSS provider: {e}")


# Global main window instance
_main_window: Optional[MainWindow] = None


def get_main_window() -> Optional[MainWindow]:
    """
    Get the global main window instance.
    
    Returns:
        MainWindow instance or None if not initialized
    """
    return _main_window


def create_main_window(
    application: Gtk.Application,
    mode_controller: Optional[ModeController] = None,
) -> MainWindow:
    """
    Create and initialize the global main window instance.
    
    Args:
        application: Parent GTK application
        mode_controller: Mode controller instance
        
    Returns:
        MainWindow instance
    """
    global _main_window
    if _main_window is None:
        _main_window = MainWindow(application, mode_controller)
        _main_window.add_css_provider()
    return _main_window


def show_main_window() -> None:
    """Show the global main window instance."""
    if _main_window:
        _main_window.present()


def cleanup_main_window() -> None:
    """Clean up the global main window instance."""
    global _main_window
    _main_window = None