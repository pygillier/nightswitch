"""
Manual mode tab for the Nightswitch application.

This module provides the ManualTab class that implements the manual mode
tab in the main window, allowing users to directly control the theme.
"""

import logging
from typing import Optional, Callable

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ...core.mode_controller import ModeController, ThemeMode
from ...core.manual_mode import ThemeType


class ManualTab:
    """
    Manual mode tab for the Nightswitch application.
    
    Provides controls for manually switching between light and dark themes.
    """
    
    def __init__(
        self,
        parent_notebook: Gtk.Notebook,
        mode_controller: ModeController,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the manual mode tab.
        
        Args:
            parent_notebook: The notebook to add this tab to
            mode_controller: Mode controller for theme switching
            status_callback: Callback for updating status messages
            error_callback: Callback for showing error messages
        """
        self.logger = logging.getLogger("nightswitch.ui.tabs.manual_tab")
        self._mode_controller = mode_controller
        self._status_callback = status_callback
        self._error_callback = error_callback
        
        # UI components
        self._tab_container = None
        self._frame = None
        
        # Create and add the tab
        self._create_tab(parent_notebook)
        
    def _create_tab(self, parent_notebook: Gtk.Notebook) -> None:
        """
        Create the manual mode tab and add it to the notebook.
        
        Args:
            parent_notebook: The notebook to add this tab to
        """
        try:
            # Container for manual controls
            self._tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self._tab_container.set_margin_start(12)
            self._tab_container.set_margin_end(12)
            self._tab_container.set_margin_top(12)
            self._tab_container.set_margin_bottom(12)
            
            # Create tab label with icon
            tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            icon = Gtk.Image.new_from_icon_name("preferences-desktop-theme-symbolic", Gtk.IconSize.MENU)
            label = Gtk.Label(label="Manual Mode")
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
            
            # Description label
            description = Gtk.Label()
            description.set_markup("<small>Directly control the theme with these buttons</small>")
            description.set_halign(Gtk.Align.START)
            inner_box.pack_start(description, False, False, 0)
            
            # Button box for theme controls
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            button_box.set_halign(Gtk.Align.CENTER)
            inner_box.pack_start(button_box, False, False, 0)
            
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
            inner_box.pack_start(toggle_button, False, False, 0)
            
            self.logger.debug("Manual mode tab created")
            
        except Exception as e:
            self.logger.error(f"Failed to create manual mode tab: {e}")
            raise
    
    def update_ui_state(self, current_mode: ThemeMode) -> None:
        """
        Update UI components based on current mode.
        
        Args:
            current_mode: Current active mode
        """
        # Check if manual mode is active
        is_manual_active = (current_mode == ThemeMode.MANUAL)
        
        # Visual indication of active mode
        if is_manual_active:
            context = self._frame.get_style_context()
            context.add_class("active-mode-frame")
        else:
            context = self._frame.get_style_context()
            context.remove_class("active-mode-frame")
    
    def _on_dark_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle dark theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            if self._status_callback:
                self._status_callback("Switching to dark theme...")
                
            success = self._mode_controller.manual_switch_to_dark()
            
            if not success and self._error_callback:
                self._error_callback("Failed to switch to dark theme")
                
        except Exception as e:
            self.logger.error(f"Error switching to dark theme: {e}")
            if self._error_callback:
                self._error_callback(f"Error switching to dark theme: {e}")
    
    def _on_light_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle light theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            if self._status_callback:
                self._status_callback("Switching to light theme...")
                
            success = self._mode_controller.manual_switch_to_light()
            
            if not success and self._error_callback:
                self._error_callback("Failed to switch to light theme")
                
        except Exception as e:
            self.logger.error(f"Error switching to light theme: {e}")
            if self._error_callback:
                self._error_callback(f"Error switching to light theme: {e}")
    
    def _on_toggle_button_clicked(self, button: Gtk.Button) -> None:
        """
        Handle toggle theme button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            if self._status_callback:
                self._status_callback("Toggling theme...")
                
            success = self._mode_controller.manual_toggle_theme()
            
            if not success and self._error_callback:
                self._error_callback("Failed to toggle theme")
                
        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")
            if self._error_callback:
                self._error_callback(f"Error toggling theme: {e}")