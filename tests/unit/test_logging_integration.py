"""
Unit tests for the integration of logging system with other components.

This module contains tests for the integration between LoggingManager and other components.
"""

import logging
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from nightswitch.core.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
)
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
        manager.initialize()
        
        # Reset the root logger after the test
        yield manager
        
        # Clean up
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)


@pytest.fixture
def error_handler():
    """Create an ErrorHandler instance for testing."""
    handler = ErrorHandler()
    
    # Reset the handler after the test
    yield handler
    
    # Clean up
    handler.clear_error_history()


class TestErrorHandlerLoggingIntegration:
    """Tests for the integration of ErrorHandler with LoggingManager."""

    def test_error_handler_uses_logging(self, error_handler, logging_manager, temp_log_dir):
        """Test that ErrorHandler uses the logging system."""
        # Handle errors with different severity levels
        error_handler.handle_error(
            message="Test info message",
            severity=ErrorSeverity.INFO,
            category=ErrorCategory.SYSTEM,
        )
        
        error_handler.handle_error(
            message="Test warning message",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.SYSTEM,
        )
        
        error_handler.handle_error(
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )
        
        error_handler.handle_error(
            message="Test critical message",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that log files were created and contain the messages
        log_file = logging_manager.get_log_file_path()
        assert log_file.exists()
        
        log_content = logging_manager.get_log_contents()
        assert "Test info message" in log_content
        assert "Test warning message" in log_content
        assert "Test error message" in log_content
        assert "Test critical message" in log_content

    def test_error_handler_with_debug_mode(self, error_handler, logging_manager):
        """Test that debug mode affects error handler logging."""
        # Enable debug mode
        logging_manager.enable_debug_mode()
        
        # Handle an error
        error_handler.handle_error(
            message="Test debug message",
            severity=ErrorSeverity.INFO,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that debug log contains the message
        debug_log_content = logging_manager.get_log_contents(debug=True)
        assert "Test debug message" in debug_log_content

    def test_error_handler_with_exception(self, error_handler, logging_manager):
        """Test that errors with exceptions are logged correctly."""
        # Create an exception
        exception = ValueError("Test exception")
        
        # Handle an error with exception
        error_handler.handle_error(
            message="Test error with exception",
            exception=exception,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that log contains the exception
        log_content = logging_manager.get_log_contents()
        assert "Test error with exception" in log_content
        assert "Test exception" in log_content

    def test_error_handler_with_source(self, error_handler, logging_manager):
        """Test that errors with source are logged correctly."""
        # Handle an error with source
        error_handler.handle_error(
            message="Test error with source",
            source="TestComponent",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that log contains the source
        log_content = logging_manager.get_log_contents()
        assert "Test error with source" in log_content
        assert "TestComponent" in log_content

    def test_plugin_error_logging(self, error_handler, logging_manager):
        """Test that plugin errors are logged correctly."""
        # Handle a plugin error
        error_handler.handle_plugin_error(
            message="Test plugin error",
            plugin_name="TestPlugin",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that log contains the plugin error
        log_content = logging_manager.get_log_contents()
        assert "Test plugin error" in log_content
        assert "Plugin: TestPlugin" in log_content

    def test_service_error_logging(self, error_handler, logging_manager):
        """Test that service errors are logged correctly."""
        # Handle a service error
        error_handler.handle_service_error(
            message="Test service error",
            service_name="TestService",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that log contains the service error
        log_content = logging_manager.get_log_contents()
        assert "Test service error" in log_content
        assert "Service: TestService" in log_content

    def test_network_error_logging(self, error_handler, logging_manager):
        """Test that network errors are logged correctly."""
        # Handle a network error
        error_handler.handle_network_error(
            message="Test network error",
            url="https://example.com",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that log contains the network error
        log_content = logging_manager.get_log_contents()
        assert "Test network error" in log_content
        assert "Network" in log_content

    def test_config_error_logging(self, error_handler, logging_manager):
        """Test that config errors are logged correctly."""
        # Handle a config error
        error_handler.handle_config_error(
            message="Test config error",
            config_file="config.json",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that log contains the config error
        log_content = logging_manager.get_log_contents()
        assert "Test config error" in log_content
        assert "Configuration" in log_content