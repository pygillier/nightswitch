"""
User interface components for Nightswitch application.

This package contains GTK 4 UI components including:
- System tray icon and menu
- Main application window
- Settings dialogs
- Notification handlers
"""

from .system_tray import SystemTrayIcon, create_system_tray, cleanup_system_tray, get_system_tray

__all__ = [
    "SystemTrayIcon",
    "create_system_tray", 
    "cleanup_system_tray",
    "get_system_tray",
]
