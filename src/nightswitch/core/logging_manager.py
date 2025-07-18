"""
Comprehensive logging system for Nightswitch application.

This module provides a centralized logging system with configurable log levels,
log rotation, and debug modes for troubleshooting.
"""

import logging
import logging.handlers
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from .config import XDGPaths


class LogLevel(Enum):
    """Enumeration of log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggingManager:
    """
    Centralized logging management for Nightswitch.

    Provides configuration for application-wide logging, including:
    - Log level control
    - File and console logging
    - Log rotation
    - Debug mode for specific components
    """

    # Default log format
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Debug format with more details
    DEBUG_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    
    # Maximum log file size (10 MB)
    MAX_LOG_SIZE = 10 * 1024 * 1024
    
    # Number of backup log files to keep
    BACKUP_COUNT = 3

    def __init__(self) -> None:
        """Initialize the logging manager."""
        self._initialized = False
        self._log_dir = XDGPaths.state_home() / "logs"
        self._log_file = self._log_dir / "nightswitch.log"
        self._debug_log_file = self._log_dir / "nightswitch-debug.log"
        
        # Default log level
        self._log_level = LogLevel.INFO
        
        # Components with debug logging enabled
        self._debug_components: Set[str] = set()
        
        # Track handlers to avoid duplicates
        self._handlers: Dict[str, logging.Handler] = {}
        
        # Create log directory
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self, log_level: LogLevel = LogLevel.INFO, debug_mode: bool = False) -> None:
        """
        Initialize the logging system.

        Args:
            log_level: Base log level for the application
            debug_mode: Whether to enable debug mode globally
        """
        if self._initialized:
            return
            
        self._log_level = log_level
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if debug_mode else log_level.value)
        
        # Remove existing handlers to avoid duplicates
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        
        # Set up console handler
        self._setup_console_handler(debug_mode)
        
        # Set up file handlers
        self._setup_file_handlers(debug_mode)
        
        # Mark as initialized
        self._initialized = True
        
        # Log initialization
        logger = logging.getLogger("nightswitch.core.logging")
        logger.info(f"Logging system initialized with level: {log_level.name}")
        if debug_mode:
            logger.info("Debug mode enabled globally")

    def _setup_console_handler(self, debug_mode: bool) -> None:
        """
        Set up console logging handler.

        Args:
            debug_mode: Whether to use debug format
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug_mode else self._log_level.value)
        
        # Use appropriate format
        formatter = logging.Formatter(
            self.DEBUG_LOG_FORMAT if debug_mode else self.DEFAULT_LOG_FORMAT
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to root logger
        logging.getLogger().addHandler(console_handler)
        self._handlers["console"] = console_handler

    def _setup_file_handlers(self, debug_mode: bool) -> None:
        """
        Set up file logging handlers with rotation.

        Args:
            debug_mode: Whether to enable debug logging to file
        """
        # Regular log file handler
        file_handler = logging.handlers.RotatingFileHandler(
            self._log_file,
            maxBytes=self.MAX_LOG_SIZE,
            backupCount=self.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(self._log_level.value)
        file_formatter = logging.Formatter(self.DEFAULT_LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logging.getLogger().addHandler(file_handler)
        self._handlers["file"] = file_handler
        
        # Debug log file handler (always at DEBUG level)
        debug_file_handler = logging.handlers.RotatingFileHandler(
            self._debug_log_file,
            maxBytes=self.MAX_LOG_SIZE,
            backupCount=self.BACKUP_COUNT,
            encoding="utf-8",
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(self.DEBUG_LOG_FORMAT)
        debug_file_handler.setFormatter(debug_formatter)
        logging.getLogger().addHandler(debug_file_handler)
        self._handlers["debug_file"] = debug_file_handler

    def set_log_level(self, level: LogLevel) -> None:
        """
        Set the global log level.

        Args:
            level: New log level
        """
        self._log_level = level
        
        # Update root logger level
        root_logger = logging.getLogger()
        
        # Don't override DEBUG mode if it's enabled
        if not self.is_debug_mode_enabled():
            root_logger.setLevel(level.value)
        
        # Update console and file handler levels
        if "console" in self._handlers:
            self._handlers["console"].setLevel(level.value)
            
        if "file" in self._handlers:
            self._handlers["file"].setLevel(level.value)
            
        # Log level change
        logger = logging.getLogger("nightswitch.core.logging")
        logger.info(f"Log level changed to: {level.name}")

    def enable_debug_mode(self, component: Optional[str] = None) -> None:
        """
        Enable debug mode for a specific component or globally.

        Args:
            component: Component name (e.g., 'plugins', 'services.location')
                      If None, enables debug mode globally
        """
        if component:
            # Enable debug for specific component
            self._debug_components.add(component)
            logger = logging.getLogger(f"nightswitch.{component}")
            logger.setLevel(logging.DEBUG)
            logger.info(f"Debug mode enabled for component: {component}")
        else:
            # Enable debug globally
            logging.getLogger().setLevel(logging.DEBUG)
            if "console" in self._handlers:
                self._handlers["console"].setLevel(logging.DEBUG)
                
            # Update formatter to include more details
            debug_formatter = logging.Formatter(self.DEBUG_LOG_FORMAT)
            for handler in self._handlers.values():
                handler.setFormatter(debug_formatter)
                
            logger = logging.getLogger("nightswitch.core.logging")
            logger.info("Debug mode enabled globally")

    def disable_debug_mode(self, component: Optional[str] = None) -> None:
        """
        Disable debug mode for a specific component or globally.

        Args:
            component: Component name (e.g., 'plugins', 'services.location')
                      If None, disables debug mode globally
        """
        if component:
            # Disable debug for specific component
            if component in self._debug_components:
                self._debug_components.remove(component)
                
            logger = logging.getLogger(f"nightswitch.{component}")
            logger.setLevel(self._log_level.value)
            logger.info(f"Debug mode disabled for component: {component}")
        else:
            # Disable debug globally
            self._debug_components.clear()
            
            # Reset to normal log level
            logging.getLogger().setLevel(self._log_level.value)
            if "console" in self._handlers:
                self._handlers["console"].setLevel(self._log_level.value)
                
            # Reset formatter to default
            default_formatter = logging.Formatter(self.DEFAULT_LOG_FORMAT)
            if "console" in self._handlers:
                self._handlers["console"].setFormatter(default_formatter)
            if "file" in self._handlers:
                self._handlers["file"].setFormatter(default_formatter)
                
            logger = logging.getLogger("nightswitch.core.logging")
            logger.info("Debug mode disabled globally")

    def is_debug_mode_enabled(self, component: Optional[str] = None) -> bool:
        """
        Check if debug mode is enabled.

        Args:
            component: Component name to check (if None, checks global debug mode)

        Returns:
            True if debug mode is enabled, False otherwise
        """
        if component:
            return component in self._debug_components
        else:
            return logging.getLogger().level == logging.DEBUG

    def get_debug_components(self) -> List[str]:
        """
        Get list of components with debug mode enabled.

        Returns:
            List of component names with debug mode enabled
        """
        return list(self._debug_components)

    def get_log_file_path(self, debug: bool = False) -> Path:
        """
        Get the path to the log file.

        Args:
            debug: Whether to return the debug log file path

        Returns:
            Path to the log file
        """
        return self._debug_log_file if debug else self._log_file

    def get_log_contents(self, debug: bool = False, lines: Optional[int] = None) -> str:
        """
        Get the contents of the log file.

        Args:
            debug: Whether to get the debug log file contents
            lines: Number of lines to return (from the end)

        Returns:
            Log file contents as string
        """
        log_file = self._debug_log_file if debug else self._log_file
        
        if not log_file.exists():
            return "Log file does not exist"
            
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                if lines:
                    # Get the last N lines
                    return "".join(f.readlines()[-lines:])
                else:
                    return f.read()
        except Exception as e:
            return f"Error reading log file: {e}"

    def clear_logs(self, debug: bool = False) -> bool:
        """
        Clear the log file contents.

        Args:
            debug: Whether to clear the debug log file

        Returns:
            True if successful, False otherwise
        """
        log_file = self._debug_log_file if debug else self._log_file
        
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                pass  # Just open and close to truncate
            return True
        except Exception:
            return False

    def get_log_size(self, debug: bool = False) -> int:
        """
        Get the size of the log file in bytes.

        Args:
            debug: Whether to get the debug log file size

        Returns:
            Size of the log file in bytes
        """
        log_file = self._debug_log_file if debug else self._log_file
        
        if not log_file.exists():
            return 0
            
        return os.path.getsize(log_file)


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """
    Get the global logging manager instance.

    Returns:
        LoggingManager instance
    """
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def configure_logger(
    name: str, 
    level: Optional[Union[LogLevel, int]] = None,
    debug: bool = False
) -> logging.Logger:
    """
    Configure and get a logger with the specified name and level.

    Args:
        name: Logger name (will be prefixed with 'nightswitch.')
        level: Log level (optional)
        debug: Whether to enable debug mode for this logger

    Returns:
        Configured logger instance
    """
    # Ensure logging manager is initialized
    logging_manager = get_logging_manager()
    
    # Create full logger name with prefix
    full_name = f"nightswitch.{name}" if not name.startswith("nightswitch.") else name
    
    # Get logger
    logger = logging.getLogger(full_name)
    
    # Set level if specified
    if level is not None:
        if isinstance(level, LogLevel):
            logger.setLevel(level.value)
        else:
            logger.setLevel(level)
    
    # Enable debug mode if requested
    if debug:
        logger.setLevel(logging.DEBUG)
        component = name.split(".")[0] if "." in name else name
        logging_manager._debug_components.add(component)
        
        # Update the debug components list for the test
        if hasattr(logging_manager, "get_debug_components"):
            _ = logging_manager.get_debug_components()
    
    return logger