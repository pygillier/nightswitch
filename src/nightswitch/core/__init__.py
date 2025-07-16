"""
Core modules for Nightswitch application.

This package contains the fundamental components of the application including:
- Application lifecycle management
- Mode controllers and handlers
- Configuration management
- Error handling
"""

from .config import AppConfig, ConfigManager, get_config
from .mode_controller import ModeController, ThemeMode, get_mode_controller
from .manual_mode import ManualModeHandler, ThemeType, get_manual_mode_handler
from .schedule_mode import ScheduleModeHandler, get_schedule_mode_handler
from .location_mode import LocationModeHandler, get_location_mode_handler

__all__ = [
    "AppConfig",
    "ConfigManager", 
    "get_config",
    "ModeController",
    "ThemeMode",
    "get_mode_controller",
    "ManualModeHandler",
    "ThemeType",
    "get_manual_mode_handler",
    "ScheduleModeHandler",
    "get_schedule_mode_handler",
    "LocationModeHandler",
    "get_location_mode_handler",
]
