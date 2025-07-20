"""
Dialog components for the Nightswitch application.

This package contains dialog components:
- About dialog
- Help dialog
- Error dialog
"""

from .about_dialog import show_about_dialog
from .help_dialog import show_help_dialog
from .error_dialog import show_error_dialog

__all__ = [
    "show_about_dialog",
    "show_help_dialog",
    "show_error_dialog",
]