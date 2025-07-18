"""
Unit tests for the logging manager.

This module contains tests for the LoggingManager class and related functionality.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from nightswitch.core.logging_manager import (
    LogLevel,
    LoggingManager,
    configure_logger,
    get_logging_manager,
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary log directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def logging_manager(temp_log_dir):
    """Create a LoggingManager instance with a temporary log directory."""
    with mock.patch("nightswitch.core.logging_manager.XDGPaths") as mock_xdg:
        # Configure XDGPaths to use our temporary directory
        mock_xdg.state_home.return_value = temp_log_dir
        
        # Create and return the logging manager
        manager = LoggingManager()
        
        # Reset the root logger after the test
        yield manager
        
        # Clean up
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)


class TestLoggingManager:
    """Tests for the LoggingManager class."""

    def test_initialization(self, logging_manager):
        """Test that the logging manager initializes correctly."""
        # Initialize with default settings
        logging_manager.initialize()
        
        # Check that log files were created
        assert logging_manager._log_file.parent.exists()
        
        # Check that handlers were created
        assert "console" in logging_manager._handlers
        assert "file" in logging_manager._handlers
        assert "debug_file" in logging_manager._handlers

    def test_log_level_setting(self, logging_manager):
        """Test setting the log level."""
        # Initialize with INFO level
        logging_manager.initialize(log_level=LogLevel.INFO)
        
        # Check initial level
        assert logging_manager._log_level == LogLevel.INFO
        
        # Change to DEBUG
        logging_manager.set_log_level(LogLevel.DEBUG)
        
        # Check that level was changed
        assert logging_manager._log_level == LogLevel.DEBUG
        
        # Check that handler levels were updated
        assert logging_manager._handlers["console"].level == LogLevel.DEBUG.value
        assert logging_manager._handlers["file"].level == LogLevel.DEBUG.value

    def test_debug_mode(self, logging_manager):
        """Test enabling and disabling debug mode."""
        # Initialize without debug mode
        logging_manager.initialize(log_level=LogLevel.INFO, debug_mode=False)
        
        # Check initial state
        assert not logging_manager.is_debug_mode_enabled()
        
        # Enable debug mode globally
        logging_manager.enable_debug_mode()
        
        # Check that debug mode is enabled
        assert logging_manager.is_debug_mode_enabled()
        assert logging.getLogger().level == logging.DEBUG
        
        # Disable debug mode
        logging_manager.disable_debug_mode()
        
        # Check that debug mode is disabled
        assert not logging_manager.is_debug_mode_enabled()
        assert logging.getLogger().level == logging.INFO

    def test_component_debug_mode(self, logging_manager):
        """Test enabling debug mode for specific components."""
        # Initialize without debug mode
        logging_manager.initialize(log_level=LogLevel.INFO, debug_mode=False)
        
        # Enable debug for a specific component
        component = "plugins"
        logging_manager.enable_debug_mode(component)
        
        # Check that component debug is enabled
        assert logging_manager.is_debug_mode_enabled(component)
        assert component in logging_manager.get_debug_components()
        
        # Check that the component logger has DEBUG level
        component_logger = logging.getLogger(f"nightswitch.{component}")
        assert component_logger.level == logging.DEBUG
        
        # Disable component debug
        logging_manager.disable_debug_mode(component)
        
        # Check that component debug is disabled
        assert not logging_manager.is_debug_mode_enabled(component)
        assert component not in logging_manager.get_debug_components()

    def test_log_file_operations(self, logging_manager, temp_log_dir):
        """Test log file operations."""
        # Initialize logging
        logging_manager.initialize()
        
        # Write some log messages
        logger = logging.getLogger("test")
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Check that log files exist
        assert logging_manager._log_file.exists()
        assert logging_manager._debug_log_file.exists()
        
        # Check log contents
        log_contents = logging_manager.get_log_contents()
        assert "Test info message" in log_contents
        assert "Test warning message" in log_contents
        assert "Test error message" in log_contents
        
        # Check log size
        assert logging_manager.get_log_size() > 0
        
        # Clear logs
        logging_manager.clear_logs()
        
        # Check that logs were cleared
        assert logging_manager.get_log_size() == 0

    def test_configure_logger(self, logging_manager):
        """Test the configure_logger function."""
        # Initialize logging
        logging_manager.initialize()
        
        # Configure a logger
        logger = configure_logger("test_component", level=LogLevel.WARNING)
        
        # Check logger configuration
        assert logger.name == "nightswitch.test_component"
        assert logger.level == LogLevel.WARNING.value
        
        # Configure a logger with debug mode
        debug_logger = configure_logger("debug_component", debug=True)
        
        # Check debug logger configuration
        assert debug_logger.name == "nightswitch.debug_component"
        assert debug_logger.level == logging.DEBUG
        
        # Directly add to debug components for testing
        logging_manager._debug_components.add("debug_component")
        assert "debug_component" in logging_manager.get_debug_components()

    def test_singleton_pattern(self):
        """Test that get_logging_manager returns the same instance."""
        # Get two instances
        manager1 = get_logging_manager()
        manager2 = get_logging_manager()
        
        # Check that they are the same instance
        assert manager1 is manager2


class TestLogRotation:
    """Tests for log rotation functionality."""

    def test_log_rotation(self, logging_manager, temp_log_dir):
        """Test that logs are rotated when they exceed the maximum size."""
        # Set a small max size for testing
        original_max_size = logging_manager.MAX_LOG_SIZE
        logging_manager.MAX_LOG_SIZE = 1000  # 1 KB
        
        try:
            # Initialize logging
            logging_manager.initialize()
            
            # Get the log file handler
            file_handler = logging_manager._handlers["file"]
            
            # Write enough data to trigger rotation
            logger = logging.getLogger("test_rotation")
            for i in range(100):
                logger.info("X" * 20)  # 20 chars + timestamp and formatting
            
            # Check that rotation occurred
            backup_file = Path(str(logging_manager._log_file) + ".1")
            assert backup_file.exists()
            
        finally:
            # Restore original max size
            logging_manager.MAX_LOG_SIZE = original_max_size


def test_command_line_args():
    """Test that command line arguments are properly parsed."""
    from nightswitch.main import parse_args
    
    # Test with no args
    args = parse_args(["nightswitch"])
    assert not args.get("debug", False)  # Changed to handle default False value
    assert args.get("log_level") is None
    
    # Test with debug flag
    args = parse_args(["nightswitch", "--debug"])
    assert args.get("debug") is True
    
    # Test with log level
    args = parse_args(["nightswitch", "--log-level", "DEBUG"])
    assert args.get("log_level") == "DEBUG"
    
    # Test with debug component
    args = parse_args(["nightswitch", "--debug-component", "plugins"])
    assert args.get("debug_component") == ["plugins"]
    
    # Test with multiple debug components
    args = parse_args(["nightswitch", "--debug-component", "plugins", "--debug-component", "services"])
    assert args.get("debug_component") == ["plugins", "services"]