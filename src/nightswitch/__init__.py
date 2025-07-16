"""
Nightswitch - A PyGTK 4 application for managing night mode in Linux desktop environments.

This package provides comprehensive theme switching functionality through multiple modes:
- Manual mode for direct user control
- Schedule mode for time-based automatic switching  
- Location mode for sunrise/sunset-based switching

The application uses a plugin system to support different desktop environments.
"""

__version__ = "0.1.0"
__author__ = "Nightswitch Team"
__email__ = "team@nightswitch.org"

from .main import main

__all__ = ["main"]