"""
Location mode tab for the Nightswitch application.

This module provides the LocationTab class that implements the location mode
tab in the main window, allowing users to set up location-based theme switching.
"""

import logging
from typing import Optional, Callable, Tuple

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ...core.mode_controller import ModeController, ThemeMode
from ...core.location_mode import LocationModeHandler
from ...services.location import LocationService


class LocationTab:
    """
    Location mode tab for the Nightswitch application.
    
    Provides controls for setting up location-based theme switching.
    """
    
    def __init__(
        self,
        parent_notebook: Gtk.Notebook,
        mode_controller: ModeController,
        location_handler: LocationModeHandler,
        location_service: LocationService,
        schedule_switch: Optional[Gtk.Switch] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the location mode tab.
        
        Args:
            parent_notebook: The notebook to add this tab to
            mode_controller: Mode controller for theme switching
            location_handler: Handler for location mode operations
            location_service: Service for location detection
            schedule_switch: Schedule mode switch for exclusivity
            status_callback: Callback for updating status messages
            error_callback: Callback for showing error messages
        """
        self.logger = logging.getLogger("nightswitch.ui.tabs.location_tab")
        self._mode_controller = mode_controller
        self._location_handler = location_handler
        self._location_service = location_service
        self._schedule_switch = schedule_switch
        self._status_callback = status_callback
        self._error_callback = error_callback
        
        # UI components
        self._tab_container = None
        self._frame = None
        self._location_switch = None
        self._auto_location_switch = None
        self._latitude_entry = None
        self._longitude_entry = None
        self._location_info_label = None
        self._next_event_label = None
        
        # Create and add the tab
        self._create_tab(parent_notebook)
        
    def _create_tab(self, parent_notebook: Gtk.Notebook) -> None:
        """
        Create the location mode tab and add it to the notebook.
        
        Args:
            parent_notebook: The notebook to add this tab to
        """
        try:
            # Container for location controls
            self._tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self._tab_container.set_margin_start(12)
            self._tab_container.set_margin_end(12)
            self._tab_container.set_margin_top(12)
            self._tab_container.set_margin_bottom(12)
            
            # Create tab label with icon
            tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            icon = Gtk.Image.new_from_icon_name("mark-location-symbolic", Gtk.IconSize.MENU)
            label = Gtk.Label(label="Location Mode")
            tab_label.pack_start(icon, False, False, 0)
            tab_label.pack_start(label, False, False, 0)
            tab_label.show_all()
            
            # Add the tab to the notebook
            parent_notebook.append_page(self._tab_container, tab_label)
            
            # Create frame for visual grouping
            self._frame = Gtk.Frame()
            self._frame.set_shadow_type(Gtk.ShadowType.NONE)
            self._tab_container.pack_start(self._frame, True, True, 0)
            
            # Container inside frame
            inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            inner_box.set_margin_start(12)
            inner_box.set_margin_end(12)
            inner_box.set_margin_top(12)
            inner_box.set_margin_bottom(12)
            self._frame.add(inner_box)
            
            # Enable switch row
            switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            switch_box.set_margin_bottom(8)
            inner_box.pack_start(switch_box, False, True, 0)
            
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
            inner_box.pack_start(description, False, False, 0)
            
            # Auto-location switch
            auto_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            inner_box.pack_start(auto_box, False, True, 0)
            
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
            inner_box.pack_start(coords_grid, False, False, 0)
            
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
            inner_box.pack_start(apply_button, False, False, 0)
            
            # Location info label
            self._location_info_label = Gtk.Label()
            self._location_info_label.set_markup("<small>No location detected</small>")
            self._location_info_label.set_halign(Gtk.Align.START)
            self._location_info_label.set_margin_top(4)
            inner_box.pack_start(self._location_info_label, False, False, 0)
            
            # Next event info label
            self._next_event_label = Gtk.Label()
            self._next_event_label.set_markup("<small>No sunrise/sunset data available</small>")
            self._next_event_label.set_halign(Gtk.Align.START)
            self._next_event_label.set_margin_top(4)
            inner_box.pack_start(self._next_event_label, False, False, 0)
            
            self.logger.debug("Location mode tab created")
            
        except Exception as e:
            self.logger.error(f"Failed to create location mode tab: {e}")
            raise
    
    def update_ui_state(self, current_mode: ThemeMode) -> None:
        """
        Update UI components based on current mode.
        
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
                context = self._frame.get_style_context()
                context.add_class("active-mode-frame")
            else:
                context = self._frame.get_style_context()
                context.remove_class("active-mode-frame")
                
        except Exception as e:
            self.logger.error(f"Failed to update location UI: {e}")
            self._location_info_label.set_markup("<small>Error updating location information</small>")
    
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
                
                # Ensure schedule mode is turned off (exclusivity)
                if self._schedule_switch:
                    self._schedule_switch.set_active(False)
                
                if is_auto:
                    # Enable location mode with auto-detection
                    if self._status_callback:
                        self._status_callback("Enabling location mode with auto-detection...")
                        
                    success = self._mode_controller.set_location_mode()
                else:
                    # Get coordinates from entries
                    try:
                        latitude = float(self._latitude_entry.get_text())
                        longitude = float(self._longitude_entry.get_text())
                    except ValueError:
                        if self._status_callback:
                            self._status_callback("Invalid coordinates format")
                        if self._error_callback:
                            self._error_callback("Please enter valid latitude and longitude values")
                        return False  # Prevent switch from turning on
                    
                    # Enable location mode with manual coordinates
                    if self._status_callback:
                        self._status_callback("Enabling location mode with manual coordinates...")
                        
                    success = self._mode_controller.set_location_mode(latitude, longitude)
                
                if not success:
                    if self._status_callback:
                        self._status_callback("Failed to enable location mode")
                    if self._error_callback:
                        self._error_callback("Failed to enable location mode")
                    return False  # Prevent switch from turning on
            else:
                # Disable location mode (switch to manual)
                if self._status_callback:
                    self._status_callback("Disabling location mode...")
                    
                success = self._mode_controller.set_manual_mode()
                
                if not success:
                    if self._status_callback:
                        self._status_callback("Failed to disable location mode")
                    if self._error_callback:
                        self._error_callback("Failed to disable location mode")
                    return False  # Prevent switch from turning off
            
            return True  # Allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling location mode: {e}")
            if self._status_callback:
                self._status_callback("Error toggling location mode")
            if self._error_callback:
                self._error_callback(f"Error toggling location mode: {e}")
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
                    if self._status_callback:
                        self._status_callback("Switching to auto-location...")
                        
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
                    if self._status_callback:
                        self._status_callback("Switching to manual coordinates...")
                        
                    success = self._mode_controller.set_location_mode(latitude, longitude)
                
                if not success:
                    if self._status_callback:
                        self._status_callback("Failed to update location mode")
                    # Allow the switch to toggle anyway
            
            return True  # Always allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling auto-location: {e}")
            if self._status_callback:
                self._status_callback("Error toggling auto-location")
            return True  # Allow state change even on error
    
    def _on_apply_location_clicked(self, button: Gtk.Button) -> None:
        """
        Handle apply location button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            # Ensure schedule mode is turned off (exclusivity)
            if self._schedule_switch:
                self._schedule_switch.set_active(False)
            
            # Check if we're using auto or manual location
            is_auto = self._auto_location_switch.get_active()
            
            if is_auto:
                # Enable location mode with auto-detection
                if self._status_callback:
                    self._status_callback("Applying auto-location...")
                    
                success = self._mode_controller.set_location_mode()
                
                # Update location switch to reflect the new state
                self._location_switch.set_active(True)
            else:
                # Get coordinates from entries
                try:
                    latitude = float(self._latitude_entry.get_text())
                    longitude = float(self._longitude_entry.get_text())
                except ValueError:
                    if self._status_callback:
                        self._status_callback("Invalid coordinates format")
                    if self._error_callback:
                        self._error_callback("Please enter valid latitude and longitude values")
                    return
                
                # Validate coordinates
                if not self._location_handler._validate_coordinates(latitude, longitude):
                    if self._status_callback:
                        self._status_callback("Invalid coordinates range")
                    if self._error_callback:
                        self._error_callback("Latitude must be between -90 and 90, longitude between -180 and 180")
                    return
                
                # Enable location mode with manual coordinates
                if self._status_callback:
                    self._status_callback("Applying manual coordinates...")
                    
                success = self._mode_controller.set_location_mode(latitude, longitude)
                
                # Update location switch to reflect the new state
                self._location_switch.set_active(True)
            
            if not success:
                if self._status_callback:
                    self._status_callback("Failed to apply location settings")
                if self._error_callback:
                    self._error_callback("Failed to apply location settings")
                
        except Exception as e:
            self.logger.error(f"Error applying location: {e}")
            if self._status_callback:
                self._status_callback("Error applying location")
            if self._error_callback:
                self._error_callback(f"Error applying location: {e}")