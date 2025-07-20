"""
Tab components for the Nightswitch application.

This package contains the tab components used in the main window:
- Manual mode tab
- Schedule mode tab
- Location mode tab
- Preferences tab
"""

from .manual_tab import ManualTab
from .schedule_tab import ScheduleTab
from .location_tab import LocationTab
from .preferences_tab import PreferencesTab

__all__ = [
    "ManualTab",
    "ScheduleTab",
    "LocationTab",
    "PreferencesTab",
]