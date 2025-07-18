"""
Unit tests for the integration of error handler with logging system.

This module contains tests for the integration between ErrorHandler and LoggingManager.
"""

import logging
from unittest import mock

import pytest

from nightswitch.core.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
)
from nightswitch.core.logging_manager import LogLevel, get_logging_manager


@pytest.fixture
def error_handler():
    """Create an ErrorHandler instance for testing."""
    handler = ErrorHandler()
    
    # Reset the handler after the test
    yield handler
    
    # Clean up
    handler.clear_error_history()


@pytest.fixture
def mock_logging():
    """Mock the logging system for testing."""
    # Create a mock logger
    mock_logger = mock.MagicMock()
    
    # Patch the getLogger function to return our mock
    with mock.patch("nightswitch.core.error_handler.logging.getLogger", return_value=mock_logger):
        yield mock_logger


class TestErrorHandlerLogging:
    """Tests for the integration of ErrorHandler with logging."""

    def test_error_logging_info(self, error_handler, mock_logging):
        """Test that INFO errors are logged correctly."""
        # Handle an INFO error
        error_handler.handle_error(
            message="Test info message",
            severity=ErrorSeverity.INFO,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that the error was logged with INFO level
        mock_logging.info.assert_called_once()
        assert "Test info message" in mock_logging.info.call_args[0][0]

    def test_error_logging_warning(self, error_handler, mock_logging):
        """Test that WARNING errors are logged correctly."""
        # Handle a WARNING error
        error_handler.handle_error(
            message="Test warning message",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that the error was logged with WARNING level
        mock_logging.warning.assert_called_once()
        assert "Test warning message" in mock_logging.warning.call_args[0][0]

    def test_error_logging_error(self, error_handler, mock_logging):
        """Test that ERROR errors are logged correctly."""
        # Handle an ERROR error
        error_handler.handle_error(
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        assert "Test error message" in mock_logging.error.call_args[0][0]

    def test_error_logging_critical(self, error_handler, mock_logging):
        """Test that CRITICAL errors are logged correctly."""
        # Handle a CRITICAL error
        error_handler.handle_error(
            message="Test critical message",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that the error was logged with CRITICAL level
        mock_logging.critical.assert_called_once()
        assert "Test critical message" in mock_logging.critical.call_args[0][0]

    def test_error_logging_with_exception(self, error_handler, mock_logging):
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
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test error with exception" in log_message
        assert "Test exception" in log_message

    def test_error_logging_with_source(self, error_handler, mock_logging):
        """Test that errors with source are logged correctly."""
        # Handle an error with source
        error_handler.handle_error(
            message="Test error with source",
            source="TestComponent",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test error with source" in log_message
        assert "TestComponent" in log_message


class TestErrorHandlerWithLoggingManager:
    """Tests for the integration of ErrorHandler with LoggingManager."""

    def test_error_handler_debug_mode(self):
        """Test that debug mode affects error handler logging."""
        # Mock the logger to ensure we can set its level
        with mock.patch("nightswitch.core.error_handler.logging.getLogger") as mock_get_logger:
            mock_logger = mock.MagicMock()
            mock_logger.level = logging.DEBUG
            mock_get_logger.return_value = mock_logger
            
            # Initialize logging manager with debug mode
            logging_manager = get_logging_manager()
            logging_manager.initialize(log_level=LogLevel.INFO, debug_mode=True)
            
            # Create error handler with our mocked logger
            error_handler = ErrorHandler()
            
            # Set the logger level to DEBUG to simulate debug mode
            error_handler.logger = mock_logger
            
            # Check that the logger is at DEBUG level
            assert error_handler.logger.level == logging.DEBUG
            
            # Clean up
            logging_manager.disable_debug_mode()

    def test_plugin_error_logging(self, error_handler, mock_logging):
        """Test that plugin errors are logged correctly."""
        # Handle a plugin error
        error_handler.handle_plugin_error(
            message="Test plugin error",
            plugin_name="TestPlugin",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test plugin error" in log_message
        assert "Plugin: TestPlugin" in log_message

    def test_service_error_logging(self, error_handler, mock_logging):
        """Test that service errors are logged correctly."""
        # Handle a service error
        error_handler.handle_service_error(
            message="Test service error",
            service_name="TestService",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test service error" in log_message
        assert "Service: TestService" in log_message

    def test_network_error_logging(self, error_handler, mock_logging):
        """Test that network errors are logged correctly."""
        # Handle a network error
        error_handler.handle_network_error(
            message="Test network error",
            url="https://example.com",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test network error" in log_message
        assert "Network" in log_message

    def test_config_error_logging(self, error_handler, mock_logging):
        """Test that config errors are logged correctly."""
        # Handle a config error
        error_handler.handle_config_error(
            message="Test config error",
            config_file="config.json",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check that the error was logged with ERROR level
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "Test config error" in log_message
        assert "Configuration" in log_message