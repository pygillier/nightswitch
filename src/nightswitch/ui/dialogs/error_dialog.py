"""
Error dialog for the Nightswitch application.

This module provides a function to show error dialogs.
"""

import logging
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def show_error_dialog(message: str, details: Optional[str] = None, parent: Optional[Gtk.Window] = None) -> None:
    """
    Show an error dialog.
    
    Args:
        message: Error message to display
        details: Optional detailed error information
        parent: Parent window for the dialog
    """
    logger = logging.getLogger("nightswitch.ui.dialogs.error_dialog")
    
    try:
        # Create dialog
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Nightswitch Error"
        )
        dialog.format_secondary_text(message)
        
        # Add details if provided
        if details:
            # Create expander for details
            expander = Gtk.Expander(label="Details")
            dialog.get_content_area().pack_start(expander, False, False, 0)
            
            # Create scrolled window for details
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_min_content_height(100)
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            # Create details label
            details_label = Gtk.Label(label=details)
            details_label.set_margin_start(12)
            details_label.set_margin_end(12)
            details_label.set_margin_top(6)
            details_label.set_margin_bottom(6)
            details_label.set_line_wrap(True)
            details_label.set_selectable(True)
            details_label.set_halign(Gtk.Align.START)
            details_label.set_valign(Gtk.Align.START)
            
            # Add label to scrolled window
            scrolled.add(details_label)
            expander.add(scrolled)
        
        # Show dialog
        dialog.show_all()
        dialog.run()
        dialog.destroy()
        
        logger.debug(f"Error dialog shown: {message}")
        
    except Exception as e:
        logger.error(f"Error showing error dialog: {e}")