"""
Unit tests for the error handler module.
"""

import unittest
from unittest.mock import MagicMock, patch

from nightswitch.core.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    get_error_handler,
)


class TestErrorContext(unittest.TestCase):
    """Test cases for the ErrorContext class."""

    def test_error_context_initialization(self):
        """Test that ErrorContext initializes correctly."""
        # Create a test exception
        test_exception = ValueError("Test exception")
        
        # Create error context
        context = ErrorContext(
            message="Test error message",
            exception=test_exception,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PLUGIN,
            source="Test Source",
            details={"key": "value"},
            suggestion="Try this fix",
        )
        
        # Verify attributes
        self.assertEqual(context.message, "Test error message")
        self.assertEqual(context.exception, test_exception)
        self.assertEqual(context.severity, ErrorSeverity.ERROR)
        self.assertEqual(context.category, ErrorCategory.PLUGIN)
        self.assertEqual(context.source, "Test Source")
        self.assertEqual(context.details, {"key": "value"})
        self.assertEqual(context.suggestion, "Try this fix")
        self.assertIsNotNone(context.timestamp)
        self.assertIsNotNone(context.traceback)
    
    def test_get_formatted_message(self):
        """Test that formatted message includes suggestion when available."""
        # Without suggestion
        context1 = ErrorContext(message="Test message")
        self.assertEqual(context1.get_formatted_message(), "Test message")
        
        # With suggestion
        context2 = ErrorContext(message="Test message", suggestion="Try this")
        self.assertEqual(
            context2.get_formatted_message(), "Test message\n\nSuggestion: Try this"
        )
    
    def test_get_details_text(self):
        """Test that details text is formatted correctly."""
        # Create context with various details
        context = ErrorContext(
            message="Test message",
            exception=ValueError("Test exception"),
            source="Test Source",
            details={"key1": "value1", "key2": "value2"},
        )
        
        # Get details text
        details_text = context.get_details_text()
        
        # Verify content
        self.assertIn("Source: Test Source", details_text)
        self.assertIn("Exception: ValueError", details_text)
        self.assertIn("key1: value1", details_text)
        self.assertIn("key2: value2", details_text)
        self.assertIn("Traceback:", details_text)


class TestErrorHandler(unittest.TestCase):
    """Test cases for the ErrorHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh error handler for each test
        self.error_handler = ErrorHandler()
        
        # Mock the logger
        self.mock_logger = MagicMock()
        self.error_handler.logger = self.mock_logger
    
    def test_handle_error_basic(self):
        """Test basic error handling functionality."""
        # Handle a simple error
        context = self.error_handler.handle_error(
            message="Test error",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.CONFIG,
            notify_user=False,
        )
        
        # Verify error was logged
        self.mock_logger.warning.assert_called_once()
        
        # Verify error was added to history
        self.assertEqual(len(self.error_handler._error_history), 1)
        self.assertEqual(self.error_handler._error_history[0], context)
        
        # Verify context properties
        self.assertEqual(context.message, "Test error")
        self.assertEqual(context.severity, ErrorSeverity.WARNING)
        self.assertEqual(context.category, ErrorCategory.CONFIG)
    
    def test_handle_error_with_exception(self):
        """Test error handling with an exception."""
        # Create test exception
        test_exception = RuntimeError("Test runtime error")
        
        # Handle error with exception
        context = self.error_handler.handle_error(
            message="Exception occurred",
            exception=test_exception,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
            notify_user=False,
        )
        
        # Verify error was logged with exception
        self.mock_logger.error.assert_called_once()
        
        # Verify context properties
        self.assertEqual(context.exception, test_exception)
        self.assertIsNotNone(context.traceback)
    
    def test_notification_callback(self):
        """Test that notification callback is called when registered."""
        # Create mock callback
        mock_callback = MagicMock()
        
        # Register callback
        self.error_handler.register_notification_callback(mock_callback)
        
        # Handle error with notification
        context = self.error_handler.handle_error(
            message="Test notification",
            severity=ErrorSeverity.INFO,
            notify_user=True,
        )
        
        # Verify callback was called with context
        mock_callback.assert_called_once_with(context)
    
    def test_fallback_handlers(self):
        """Test that fallback handlers are called for matching categories."""
        # Create mock handlers
        mock_handler1 = MagicMock(return_value=False)  # First handler fails
        mock_handler2 = MagicMock(return_value=True)   # Second handler succeeds
        
        # Register handlers for PLUGIN category
        self.error_handler.register_fallback_handler(
            ErrorCategory.PLUGIN, mock_handler1
        )
        self.error_handler.register_fallback_handler(
            ErrorCategory.PLUGIN, mock_handler2
        )
        
        # Handle plugin error
        context = self.error_handler.handle_error(
            message="Plugin error",
            category=ErrorCategory.PLUGIN,
            notify_user=False,
        )
        
        # Verify both handlers were called with context
        mock_handler1.assert_called_once_with(context)
        mock_handler2.assert_called_once_with(context)
        
        # Test unregistering handler
        self.error_handler.unregister_fallback_handler(
            ErrorCategory.PLUGIN, mock_handler1
        )
        
        # Handle another error
        self.error_handler.handle_error(
            message="Another plugin error",
            category=ErrorCategory.PLUGIN,
            notify_user=False,
        )
        
        # Verify first handler was not called again (still has 1 call)
        self.assertEqual(mock_handler1.call_count, 1)
        
        # Verify second handler was called again (now has 2 calls)
        self.assertEqual(mock_handler2.call_count, 2)
    
    def test_error_history_filtering(self):
        """Test filtering error history by severity and category."""
        # Add errors with different severities and categories
        self.error_handler.handle_error(
            message="Info error",
            severity=ErrorSeverity.INFO,
            category=ErrorCategory.UI,
            notify_user=False,
        )
        self.error_handler.handle_error(
            message="Warning error",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.NETWORK,
            notify_user=False,
        )
        self.error_handler.handle_error(
            message="Error error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.UI,
            notify_user=False,
        )
        
        # Test filtering by severity
        info_errors = self.error_handler.get_error_history(severity=ErrorSeverity.INFO)
        self.assertEqual(len(info_errors), 1)
        self.assertEqual(info_errors[0].message, "Info error")
        
        # Test filtering by category
        ui_errors = self.error_handler.get_error_history(category=ErrorCategory.UI)
        self.assertEqual(len(ui_errors), 2)
        
        # Test filtering by both
        ui_info_errors = self.error_handler.get_error_history(
            severity=ErrorSeverity.INFO, category=ErrorCategory.UI
        )
        self.assertEqual(len(ui_info_errors), 1)
        
        # Test limit
        limited_errors = self.error_handler.get_error_history(limit=2)
        self.assertEqual(len(limited_errors), 2)
        self.assertEqual(limited_errors[1].message, "Error error")
    
    def test_convenience_methods(self):
        """Test convenience methods for common error types."""
        # Test plugin error
        plugin_context = self.error_handler.handle_plugin_error(
            message="Plugin failed",
            plugin_name="TestPlugin",
            suggestion="Try reinstalling",
        )
        self.assertEqual(plugin_context.category, ErrorCategory.PLUGIN)
        self.assertEqual(plugin_context.source, "Plugin: TestPlugin")
        self.assertEqual(plugin_context.suggestion, "Try reinstalling")
        
        # Test service error
        service_context = self.error_handler.handle_service_error(
            message="Service failed",
            service_name="LocationService",
        )
        self.assertEqual(service_context.category, ErrorCategory.SERVICE)
        self.assertEqual(service_context.source, "Service: LocationService")
        
        # Test network error
        network_context = self.error_handler.handle_network_error(
            message="Network failed",
            url="https://example.com",
        )
        self.assertEqual(network_context.category, ErrorCategory.NETWORK)
        self.assertEqual(network_context.details["url"], "https://example.com")
        self.assertIn("Check your internet connection", network_context.suggestion)
        
        # Test config error
        config_context = self.error_handler.handle_config_error(
            message="Config failed",
            config_file="config.json",
        )
        self.assertEqual(config_context.category, ErrorCategory.CONFIG)
        self.assertEqual(config_context.details["config_file"], "config.json")
    
    def test_error_history_limit(self):
        """Test that error history is limited to max size."""
        # Set small max history size
        self.error_handler._max_history_size = 3
        
        # Add more errors than the limit
        for i in range(5):
            self.error_handler.handle_error(
                message=f"Error {i}",
                notify_user=False,
            )
        
        # Verify history is limited to max size
        self.assertEqual(len(self.error_handler._error_history), 3)
        
        # Verify oldest errors were removed
        messages = [e.message for e in self.error_handler._error_history]
        self.assertEqual(messages, ["Error 2", "Error 3", "Error 4"])
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        # Add some errors
        for i in range(3):
            self.error_handler.handle_error(
                message=f"Error {i}",
                notify_user=False,
            )
        
        # Verify errors were added
        self.assertEqual(len(self.error_handler._error_history), 3)
        
        # Clear history
        self.error_handler.clear_error_history()
        
        # Verify history is empty
        self.assertEqual(len(self.error_handler._error_history), 0)


class TestGlobalErrorHandler(unittest.TestCase):
    """Test cases for the global error handler instance."""
    
    def test_get_error_handler(self):
        """Test that get_error_handler returns a singleton instance."""
        # Get handler instances
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Verify they are the same instance
        self.assertIs(handler1, handler2)
        
        # Verify it's an ErrorHandler instance
        self.assertIsInstance(handler1, ErrorHandler)


if __name__ == "__main__":
    unittest.main()