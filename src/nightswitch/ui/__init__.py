"""
User interface components for Nightswitch application.

This package contains GTK 3 UI components including:
- System tray icon and menu
- Main application window
- Tab components
- Dialog components
"""

from .system_tray import SystemTrayIcon, create_system_tray, cleanup_system_tray, get_system_tray
from .main_window import MainWindow

__all__ = [
    "SystemTrayIcon",
    "create_system_tray", 
    "cleanup_system_tray",
    "get_system_tray",
    "MainWindow",
]