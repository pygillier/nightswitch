"""
Preferences tab for the Nightswitch application.

This module provides the PreferencesTab class that implements the preferences
tab in the main window, allowing users to configure application settings.
"""

import logging
from typing import Optional, Callable, Dict, Any

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class PreferencesTab:
    """
    Preferences tab for the Nightswitch application.
    
    Provides controls for configuring application settings.
    """
    
    def __init__(
        self,
        parent_notebook: Gtk.Notebook,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        save_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the preferences tab.
        
        Args:
            parent_notebook: The notebook to add this tab to
            status_callback: Callback for updating status messages
            error_callback: Callback for showing error messages
            save_callback: Callback for saving preferences
        """
        self.logger = logging.getLogger("nightswitch.ui.tabs.preferences_tab")
        self._status_callback = status_callback
        self._error_callback = error_callback
        self._save_callback = save_callback
        
        # UI components
        self._tab_container = None
        self._start_min_switch = None
        self._notif_switch = None
        self._autostart_switch = None
        self._log_level_combo = None
        self._debug_switch = None
        
        # Create and add the tab
        self._create_tab(parent_notebook)
        
    def _create_tab(self, parent_notebook: Gtk.Notebook) -> None:
        """
        Create the preferences tab and add it to the notebook.
        
        Args:
            parent_notebook: The notebook to add this tab to
        """
        try:
            # Container for preferences
            self._tab_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            self._tab_container.set_margin_start(12)
            self._tab_container.set_margin_end(12)
            self._tab_container.set_margin_top(12)
            self._tab_container.set_margin_bottom(12)
            
            # Create tab label with icon
            tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU)
            label = Gtk.Label(label="Preferences")
            tab_label.pack_start(icon, False, False, 0)
            tab_label.pack_start(label, False, False, 0)
            tab_label.show_all()
            
            # Add the tab to the notebook
            parent_notebook.append_page(self._tab_container, tab_label)
            
            # Create inner notebook for preferences tabs
            inner_notebook = Gtk.Notebook()
            inner_notebook.set_tab_pos(Gtk.PositionType.LEFT)
            self._tab_container.pack_start(inner_notebook, True, True, 0)
            
            # General settings tab
            general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            general_box.set_margin_start(12)
            general_box.set_margin_end(12)
            general_box.set_margin_top(12)
            general_box.set_margin_bottom(12)
            inner_notebook.append_page(general_box, Gtk.Label(label="General"))
            
            # Start minimized option
            start_min_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            start_min_label = Gtk.Label(label="Start minimized to tray")
            start_min_label.set_halign(Gtk.Align.START)
            start_min_label.set_hexpand(True)
            self._start_min_switch = Gtk.Switch()
            self._start_min_switch.set_active(True)  # Default to true
            
            start_min_box.pack_start(start_min_label, True, True, 0)
            start_min_box.pack_start(self._start_min_switch, False, False, 0)
            general_box.pack_start(start_min_box, False, False, 0)
            
            # Show notifications option
            notif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            notif_label = Gtk.Label(label="Show notifications")
            notif_label.set_halign(Gtk.Align.START)
            notif_label.set_hexpand(True)
            self._notif_switch = Gtk.Switch()
            self._notif_switch.set_active(True)  # Default to true
            
            notif_box.pack_start(notif_label, True, True, 0)
            notif_box.pack_start(self._notif_switch, False, False, 0)
            general_box.pack_start(notif_box, False, False, 0)
            
            # Autostart option
            autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            autostart_label = Gtk.Label(label="Start on system boot")
            autostart_label.set_halign(Gtk.Align.START)
            autostart_label.set_hexpand(True)
            self._autostart_switch = Gtk.Switch()
            self._autostart_switch.set_active(False)  # Default to false
            
            autostart_box.pack_start(autostart_label, True, True, 0)
            autostart_box.pack_start(self._autostart_switch, False, False, 0)
            general_box.pack_start(autostart_box, False, False, 0)
            
            # Advanced settings tab
            advanced_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            advanced_box.set_margin_start(12)
            advanced_box.set_margin_end(12)
            advanced_box.set_margin_top(12)
            advanced_box.set_margin_bottom(12)
            inner_notebook.append_page(advanced_box, Gtk.Label(label="Advanced"))
            
            # Log level option
            log_level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            log_level_label = Gtk.Label(label="Log Level")
            log_level_label.set_halign(Gtk.Align.START)
            self._log_level_combo = Gtk.ComboBoxText()
            for level in ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]:
                self._log_level_combo.append_text(level)
            self._log_level_combo.set_active(0)  # Default to INFO
            
            log_level_box.pack_start(log_level_label, False, False, 0)
            log_level_box.pack_start(self._log_level_combo, True, True, 0)
            advanced_box.pack_start(log_level_box, False, False, 0)
            
            # Debug mode option
            debug_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            debug_label = Gtk.Label(label="Debug Mode")
            debug_label.set_halign(Gtk.Align.START)
            debug_label.set_hexpand(True)
            self._debug_switch = Gtk.Switch()
            self._debug_switch.set_active(False)  # Default to false
            
            debug_box.pack_start(debug_label, True, True, 0)
            debug_box.pack_start(self._debug_switch, False, False, 0)
            advanced_box.pack_start(debug_box, False, False, 0)
            
            # Add save button at the bottom
            save_button = Gtk.Button(label="Save Preferences")
            save_button.connect("clicked", self._on_save_preferences_clicked)
            save_button.set_margin_top(10)
            self._tab_container.pack_start(save_button, False, False, 0)
            
            self.logger.debug("Preferences tab created")
            
        except Exception as e:
            self.logger.error(f"Failed to create preferences tab: {e}")
            raise
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Update UI components based on current preferences.
        
        Args:
            preferences: Dictionary of current preferences
        """
        try:
            # Update UI components with current preferences
            self._start_min_switch.set_active(preferences.get("start_minimized", True))
            self._notif_switch.set_active(preferences.get("show_notifications", True))
            self._autostart_switch.set_active(preferences.get("autostart", False))
            
            # Set log level
            log_level = preferences.get("log_level", "INFO")
            log_levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
            if log_level in log_levels:
                self._log_level_combo.set_active(log_levels.index(log_level))
            else:
                self._log_level_combo.set_active(0)  # Default to INFO
                
            # Set debug mode
            self._debug_switch.set_active(preferences.get("debug_mode", False))
            
        except Exception as e:
            self.logger.error(f"Failed to update preferences UI: {e}")
    
    def _on_save_preferences_clicked(self, button: Gtk.Button) -> None:
        """
        Handle save preferences button click.
        
        Args:
            button: Button that was clicked
        """
        try:
            # Get preferences values
            preferences = {
                "start_minimized": self._start_min_switch.get_active(),
                "show_notifications": self._notif_switch.get_active(),
                "autostart": self._autostart_switch.get_active(),
                "log_level": self._log_level_combo.get_active_text(),
                "debug_mode": self._debug_switch.get_active(),
            }
            
            # Call save callback if provided
            if self._save_callback:
                self._save_callback(preferences)
            
            # Update status
            if self._status_callback:
                self._status_callback("Preferences saved")
                
            self.logger.info("Preferences saved")
            
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
            if self._status_callback:
                self._status_callback("Error saving preferences")
            if self._error_callback:
                self._error_callback(f"Error saving preferences: {e}")