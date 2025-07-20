"""
Schedule mode tab for the Nightswitch application.

This module provides the ScheduleTab class that implements the schedule mode
tab in the main window, allowing users to set up time-based theme switching.
"""

import logging
from typing import Optional, Callable, Tuple

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ...core.mode_controller import ModeController, ThemeMode
from ...core.schedule_mode import ScheduleModeHandler


class ScheduleTab:
    """
    Schedule mode tab for the Nightswitch application.
    
    Provides controls for setting up time-based theme switching.
    """
    
    def __init__(
        self,
        parent_notebook: Gtk.Notebook,
        mode_controller: ModeController,
        schedule_handler: ScheduleModeHandler,
        location_switch: Optional[Gtk.Switch] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the schedule mode tab.
        
        Args:
            parent_notebook: The notebook to add this tab to
            mode_controller: Mode controller for theme switching
            schedule_handler: Handler for schedule mode operations
            location_switch: Location mode switch for exclusivity
            status_callback: Callback for updating status messages
            error_callback: Callback for showing error messages
        """
        self.logger = logging.getLogger("nightswitch.ui.tabs.schedule_tab")
        self._mode_controller = mode_controller
        self._schedule_handler = schedule_handler
        self._location_switch = location_switch
        self._status_callback = status_callback
        self._error_callback = error_callback
        
        # UI components
        self._tab_container = None
        self._frame = None
        self._schedule_switch = None
        self._dark_time_entry = None
        self._light_time_entry = None
        self._next_schedule_label = None
        
        # Create and add the tab
        self._create_tab(parent_notebook)
        
    def _create_tab(self, parent_notebook: Gtk.Notebook) -> None:
        """
        Create the schedule mode tab and add it to the notebook.
        
        Args:
            parent_notebook: The notebook to add this tab to
        """
        try:
            # Container for schedule controls
            self._tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self._tab_container.set_margin_start(12)
            self._tab_container.set_margin_end(12)
            self._tab_container.set_margin_top(12)
            self._tab_container.set_margin_bottom(12)
            
            # Create tab label with icon
            tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            icon = Gtk.Image.new_from_icon_name("appointment-soon-symbolic", Gtk.IconSize.MENU)
            label = Gtk.Label(label="Schedule Mode")
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
            inner_box.pack_start(description, False, False, 0)
            
            # Time settings grid
            grid = Gtk.Grid()
            grid.set_column_spacing(12)
            grid.set_row_spacing(8)
            inner_box.pack_start(grid, False, False, 0)
            
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
            inner_box.pack_start(apply_button, False, False, 0)
            
            # Next trigger info label
            self._next_schedule_label = Gtk.Label()
            self._next_schedule_label.set_markup("<small>No schedule active</small>")
            self._next_schedule_label.set_halign(Gtk.Align.START)
            self._next_schedule_label.set_margin_top(4)
            inner_box.pack_start(self._next_schedule_label, False, False, 0)
            
            self.logger.debug("Schedule mode tab created")
            
        except Exception as e:
            self.logger.error(f"Failed to create schedule mode tab: {e}")
            raise
    
    def update_ui_state(self, current_mode: ThemeMode) -> None:
        """
        Update UI components based on current mode.
        
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
                context = self._frame.get_style_context()
                context.add_class("active-mode-frame")
            else:
                context = self._frame.get_style_context()
                context.remove_class("active-mode-frame")
                
        except Exception as e:
            self.logger.error(f"Failed to update schedule UI: {e}")
            self._next_schedule_label.set_markup("<small>Error updating schedule information</small>")
    
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
                    if self._status_callback:
                        self._status_callback(error_msg)
                    if self._error_callback:
                        self._error_callback(error_msg)
                    return False  # Prevent switch from turning on
                
                # Ensure location mode is turned off (exclusivity)
                if self._location_switch:
                    self._location_switch.set_active(False)
                
                # Enable schedule mode
                if self._status_callback:
                    self._status_callback("Enabling schedule mode...")
                    
                success = self._mode_controller.set_schedule_mode(dark_time, light_time)
                
                if not success:
                    if self._status_callback:
                        self._status_callback("Failed to enable schedule mode")
                    if self._error_callback:
                        self._error_callback("Failed to enable schedule mode")
                    return False  # Prevent switch from turning on
            else:
                # Disable schedule mode (switch to manual)
                if self._status_callback:
                    self._status_callback("Disabling schedule mode...")
                    
                success = self._mode_controller.set_manual_mode()
                
                if not success:
                    if self._status_callback:
                        self._status_callback("Failed to disable schedule mode")
                    if self._error_callback:
                        self._error_callback("Failed to disable schedule mode")
                    return False  # Prevent switch from turning off
            
            return True  # Allow state change
            
        except Exception as e:
            self.logger.error(f"Error toggling schedule mode: {e}")
            if self._status_callback:
                self._status_callback("Error toggling schedule mode")
            if self._error_callback:
                self._error_callback(f"Error toggling schedule mode: {e}")
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
                if self._status_callback:
                    self._status_callback(error_msg)
                if self._error_callback:
                    self._error_callback(error_msg)
                return
            
            # Ensure location mode is turned off (exclusivity)
            if self._location_switch:
                self._location_switch.set_active(False)
            
            # Enable schedule mode
            if self._status_callback:
                self._status_callback("Applying schedule...")
                
            success = self._mode_controller.set_schedule_mode(dark_time, light_time)
            
            # Update schedule switch to reflect the new state
            self._schedule_switch.set_active(True)
            
            if not success:
                if self._status_callback:
                    self._status_callback("Failed to apply schedule")
                if self._error_callback:
                    self._error_callback("Failed to apply schedule")
                
        except Exception as e:
            self.logger.error(f"Error applying schedule: {e}")
            if self._status_callback:
                self._status_callback("Error applying schedule")
            if self._error_callback:
                self._error_callback(f"Error applying schedule: {e}")