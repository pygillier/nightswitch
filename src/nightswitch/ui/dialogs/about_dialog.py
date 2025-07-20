"""
About dialog for the Nightswitch application.

This module provides a function to show the about dialog.
"""

import logging
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def show_about_dialog(parent: Optional[Gtk.Window] = None) -> None:
    """
    Show the about dialog.
    
    Args:
        parent: Parent window for the dialog
    """
    logger = logging.getLogger("nightswitch.ui.dialogs.about_dialog")
    
    try:
        # Create about dialog
        dialog = Gtk.AboutDialog()
        if parent:
            dialog.set_transient_for(parent)
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
        
        logger.debug("About dialog shown")
        
    except Exception as e:
        logger.error(f"Error showing about dialog: {e}")