"""
Help dialog for the Nightswitch application.

This module provides a function to show the help dialog.
"""

import logging
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def show_help_dialog(parent: Optional[Gtk.Window] = None) -> None:
    """
    Show the help dialog.
    
    Args:
        parent: Parent window for the dialog
    """
    logger = logging.getLogger("nightswitch.ui.dialogs.help_dialog")
    
    try:
        # Create dialog
        dialog = Gtk.Dialog(
            title="Help",
            parent=parent,
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
        
        logger.debug("Help dialog shown")
        
    except Exception as e:
        logger.error(f"Error showing help dialog: {e}")