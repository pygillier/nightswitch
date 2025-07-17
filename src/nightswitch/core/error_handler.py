"""
Error handling system for Nightswitch application.

This module provides the ErrorHandler class that centralizes error management,
implements fallback mechanisms, and coordinates user notifications for errors.
"""

import logging
import traceback
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from gi.repository import GLib


class ErrorSeverity(Enum):
    """Enumeration of error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Enumeration of error categories."""

    PLUGIN = "plugin"
    SERVICE = "service"
    UI = "ui"
    CONFIG = "config"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorContext:
    """
    Context information for an error.

    Provides structured information about an error including its source,
    severity, category, and related data.
    """

    def __init__(
        self,
        message: str,
        exception: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        """
        Initialize error context.

        Args:
            message: Human-readable error message
            exception: Original exception (optional)
            severity: Error severity level
            category: Error category
            source: Source component of the error
            details: Additional error details
            suggestion: Suggested action to resolve the error
        """
        self.message = message
        self.exception = exception
        self.severity = severity
        self.category = category
        self.source = source
        self.details = details or {}
        self.suggestion = suggestion
        self.timestamp = GLib.DateTime.new_now_local()
        self.traceback = (
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
            if exception
            else None
        )

    def get_formatted_message(self) -> str:
        """
        Get a formatted error message with suggestion if available.

        Returns:
            Formatted error message
        """
        if self.suggestion:
            return f"{self.message}\n\nSuggestion: {self.suggestion}"
        return self.message

    def get_details_text(self) -> str:
        """
        Get formatted details text including traceback if available.

        Returns:
            Formatted details text
        """
        details_parts = []

        # Add source if available
        if self.source:
            details_parts.append(f"Source: {self.source}")

        # Add exception type if available
        if self.exception:
            details_parts.append(f"Exception: {type(self.exception).__name__}")

        # Add details dictionary items
        for key, value in self.details.items():
            details_parts.append(f"{key}: {value}")

        # Add traceback if available
        if self.traceback:
            details_parts.append("\nTraceback:")
            details_parts.append("".join(self.traceback))

        return "\n".join(details_parts)


class ErrorHandler:
    """
    Centralized error handling system for Nightswitch.

    Manages error reporting, logging, user notifications, and fallback
    mechanisms for various error scenarios.
    """

    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger("nightswitch.core.error_handler")
        self._notification_callback: Optional[
            Callable[[ErrorContext], None]
        ] = None
        self._error_history: List[ErrorContext] = []
        self._max_history_size = 100
        self._fallback_handlers: Dict[
            ErrorCategory, List[Callable[[ErrorContext], bool]]
        ] = {category: [] for category in ErrorCategory}

    def handle_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        notify_user: bool = True,
    ) -> ErrorContext:
        """
        Handle an error with appropriate logging and notifications.

        Args:
            message: Human-readable error message
            exception: Original exception (optional)
            severity: Error severity level
            category: Error category
            source: Source component of the error
            details: Additional error details
            suggestion: Suggested action to resolve the error
            notify_user: Whether to notify the user about this error

        Returns:
            ErrorContext object for the handled error
        """
        # Create error context
        error_context = ErrorContext(
            message=message,
            exception=exception,
            severity=severity,
            category=category,
            source=source,
            details=details,
            suggestion=suggestion,
        )

        # Log the error
        self._log_error(error_context)

        # Add to history
        self._add_to_history(error_context)

        # Try fallback handlers
        self._try_fallback_handlers(error_context)

        # Notify user if requested and callback is set
        if notify_user and self._notification_callback:
            try:
                self._notification_callback(error_context)
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")

        return error_context

    def _log_error(self, error_context: ErrorContext) -> None:
        """
        Log an error with appropriate severity level.

        Args:
            error_context: Error context to log
        """
        log_message = f"{error_context.message}"
        if error_context.source:
            log_message = f"[{error_context.source}] {log_message}"

        if error_context.exception:
            log_message = f"{log_message}: {error_context.exception}"

        # Log with appropriate level
        if error_context.severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif error_context.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif error_context.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        else:
            self.logger.error(log_message)

    def _add_to_history(self, error_context: ErrorContext) -> None:
        """
        Add an error to the history, maintaining maximum size.

        Args:
            error_context: Error context to add
        """
        self._error_history.append(error_context)
        # Trim history if needed
        if len(self._error_history) > self._max_history_size:
            self._error_history = self._error_history[-self._max_history_size:]

    def _try_fallback_handlers(self, error_context: ErrorContext) -> bool:
        """
        Try registered fallback handlers for the error category.

        Args:
            error_context: Error context to handle

        Returns:
            True if any handler successfully handled the error, False otherwise
        """
        handlers = self._fallback_handlers.get(error_context.category, [])
        for handler in handlers:
            try:
                if handler(error_context):
                    return True
            except Exception as e:
                self.logger.error(f"Error in fallback handler: {e}")
        return False

    def register_notification_callback(
        self, callback: Callable[[ErrorContext], None]
    ) -> None:
        """
        Register a callback for user notifications.

        Args:
            callback: Function to call with error context for notifications
        """
        self._notification_callback = callback

    def register_fallback_handler(
        self, category: ErrorCategory, handler: Callable[[ErrorContext], bool]
    ) -> None:
        """
        Register a fallback handler for a specific error category.

        Args:
            category: Error category to handle
            handler: Function that attempts to handle the error, returns True if successful
        """
        if category not in self._fallback_handlers:
            self._fallback_handlers[category] = []
        self._fallback_handlers[category].append(handler)

    def unregister_fallback_handler(
        self, category: ErrorCategory, handler: Callable[[ErrorContext], bool]
    ) -> None:
        """
        Unregister a fallback handler.

        Args:
            category: Error category
            handler: Handler function to remove
        """
        if category in self._fallback_handlers and handler in self._fallback_handlers[category]:
            self._fallback_handlers[category].remove(handler)

    def get_error_history(
        self, 
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        limit: Optional[int] = None
    ) -> List[ErrorContext]:
        """
        Get error history with optional filtering.

        Args:
            severity: Filter by severity level (optional)
            category: Filter by category (optional)
            limit: Maximum number of errors to return (optional)

        Returns:
            List of error contexts matching the filters
        """
        filtered = self._error_history

        # Apply filters
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        if category:
            filtered = [e for e in filtered if e.category == category]

        # Apply limit
        if limit and limit > 0:
            filtered = filtered[-limit:]

        return filtered

    def clear_error_history(self) -> None:
        """Clear the error history."""
        self._error_history.clear()

    # Convenience methods for common error types

    def handle_plugin_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        plugin_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> ErrorContext:
        """
        Handle a plugin-related error.

        Args:
            message: Error message
            exception: Original exception (optional)
            plugin_name: Name of the plugin
            details: Additional error details
            suggestion: Suggested action to resolve the error
            severity: Error severity level

        Returns:
            ErrorContext object for the handled error
        """
        source = f"Plugin: {plugin_name}" if plugin_name else "Plugin"
        details_dict = details or {}
        if plugin_name:
            details_dict["plugin_name"] = plugin_name

        return self.handle_error(
            message=message,
            exception=exception,
            severity=severity,
            category=ErrorCategory.PLUGIN,
            source=source,
            details=details_dict,
            suggestion=suggestion,
        )

    def handle_service_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> ErrorContext:
        """
        Handle a service-related error.

        Args:
            message: Error message
            exception: Original exception (optional)
            service_name: Name of the service
            details: Additional error details
            suggestion: Suggested action to resolve the error
            severity: Error severity level

        Returns:
            ErrorContext object for the handled error
        """
        source = f"Service: {service_name}" if service_name else "Service"
        details_dict = details or {}
        if service_name:
            details_dict["service_name"] = service_name

        return self.handle_error(
            message=message,
            exception=exception,
            severity=severity,
            category=ErrorCategory.SERVICE,
            source=source,
            details=details_dict,
            suggestion=suggestion,
        )

    def handle_network_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> ErrorContext:
        """
        Handle a network-related error.

        Args:
            message: Error message
            exception: Original exception (optional)
            url: URL that caused the error
            details: Additional error details
            suggestion: Suggested action to resolve the error
            severity: Error severity level

        Returns:
            ErrorContext object for the handled error
        """
        details_dict = details or {}
        if url:
            details_dict["url"] = url

        return self.handle_error(
            message=message,
            exception=exception,
            severity=severity,
            category=ErrorCategory.NETWORK,
            source="Network",
            details=details_dict,
            suggestion=suggestion or "Check your internet connection and try again.",
        )

    def handle_config_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        config_file: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> ErrorContext:
        """
        Handle a configuration-related error.

        Args:
            message: Error message
            exception: Original exception (optional)
            config_file: Configuration file path
            details: Additional error details
            suggestion: Suggested action to resolve the error
            severity: Error severity level

        Returns:
            ErrorContext object for the handled error
        """
        details_dict = details or {}
        if config_file:
            details_dict["config_file"] = config_file

        return self.handle_error(
            message=message,
            exception=exception,
            severity=severity,
            category=ErrorCategory.CONFIG,
            source="Configuration",
            details=details_dict,
            suggestion=suggestion,
        )


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler