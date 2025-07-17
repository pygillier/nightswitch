"""
User notification system for Nightswitch application.

This module provides the NotificationManager class that handles user
notifications for errors, status updates, and important events.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk

from .error_handler import ErrorContext, ErrorSeverity


class NotificationType(Enum):
    """Enumeration of notification types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationPriority(Enum):
    """Enumeration of notification priorities."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationManager:
    """
    Manager for user notifications in Nightswitch.

    Handles displaying notifications to the user through various channels
    including system notifications, in-app notifications, and dialogs.
    """

    def __init__(self, application: Optional[Gtk.Application] = None):
        """
        Initialize the notification manager.

        Args:
            application: GTK application instance for system notifications
        """
        self.logger = logging.getLogger("nightswitch.core.notification")
        self._application = application
        self._notification_history: List[Dict[str, Any]] = []
        self._max_history_size = 50
        self._dialog_parent: Optional[Gtk.Window] = None
        self._in_app_notification_callback: Optional[
            Callable[[str, NotificationType, int], None]
        ] = None

    def set_application(self, application: Gtk.Application) -> None:
        """
        Set the GTK application for system notifications.

        Args:
            application: GTK application instance
        """
        self._application = application

    def set_dialog_parent(self, parent: Gtk.Window) -> None:
        """
        Set the parent window for dialog notifications.

        Args:
            parent: Parent window for dialogs
        """
        self._dialog_parent = parent

    def set_in_app_notification_callback(
        self, callback: Callable[[str, NotificationType, int], None]
    ) -> None:
        """
        Set callback for in-app notifications.

        Args:
            callback: Function to call with message, type, and timeout
        """
        self._in_app_notification_callback = callback

    def notify(
        self,
        message: str,
        title: Optional[str] = None,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        timeout: int = 5,  # seconds
        use_system_notification: bool = True,
        use_in_app_notification: bool = True,
        details: Optional[str] = None,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Show a notification to the user.

        Args:
            message: Notification message
            title: Notification title (optional)
            notification_type: Type of notification
            priority: Notification priority
            timeout: Notification timeout in seconds
            use_system_notification: Whether to use system notifications
            use_in_app_notification: Whether to use in-app notifications
            details: Additional details (optional)
            action_label: Label for action button (optional)
            action_callback: Callback for action button (optional)
        """
        try:
            # Add to history
            notification_data = {
                "message": message,
                "title": title,
                "type": notification_type,
                "priority": priority,
                "timestamp": GLib.DateTime.new_now_local(),
            }
            self._add_to_history(notification_data)

            # Show system notification if requested
            if use_system_notification:
                self._show_system_notification(
                    message, title, notification_type, priority, action_label, action_callback
                )

            # Show in-app notification if requested
            if use_in_app_notification:
                self._show_in_app_notification(message, notification_type, timeout)

            # Log the notification
            log_level = (
                logging.INFO
                if notification_type in (NotificationType.INFO, NotificationType.SUCCESS)
                else logging.WARNING
                if notification_type == NotificationType.WARNING
                else logging.ERROR
            )
            self.logger.log(
                log_level,
                f"Notification [{notification_type.value}]: {title or 'Nightswitch'} - {message}",
            )

        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

    def notify_error(
        self,
        error_context: ErrorContext,
        use_system_notification: bool = True,
        use_in_app_notification: bool = True,
        show_dialog_for_critical: bool = True,
    ) -> None:
        """
        Show a notification for an error.

        Args:
            error_context: Error context to notify about
            use_system_notification: Whether to use system notifications
            use_in_app_notification: Whether to use in-app notifications
            show_dialog_for_critical: Whether to show a dialog for critical errors
        """
        try:
            # Map severity to notification type and priority
            notification_type, priority = self._map_error_severity(error_context.severity)

            # Get formatted message
            message = error_context.get_formatted_message()
            title = f"Nightswitch {error_context.severity.value.capitalize()}"

            # Show notification
            self.notify(
                message=message,
                title=title,
                notification_type=notification_type,
                priority=priority,
                use_system_notification=use_system_notification,
                use_in_app_notification=use_in_app_notification,
                details=error_context.get_details_text(),
            )

            # Show dialog for critical errors if requested
            if (
                show_dialog_for_critical
                and error_context.severity == ErrorSeverity.CRITICAL
                and self._dialog_parent
            ):
                self._show_error_dialog(
                    title, message, error_context.get_details_text()
                )

        except Exception as e:
            self.logger.error(f"Failed to show error notification: {e}")

    def _map_error_severity(
        self, severity: ErrorSeverity
    ) -> Tuple[NotificationType, NotificationPriority]:
        """
        Map error severity to notification type and priority.

        Args:
            severity: Error severity

        Returns:
            Tuple of (notification_type, priority)
        """
        if severity == ErrorSeverity.INFO:
            return NotificationType.INFO, NotificationPriority.LOW
        elif severity == ErrorSeverity.WARNING:
            return NotificationType.WARNING, NotificationPriority.NORMAL
        elif severity == ErrorSeverity.ERROR:
            return NotificationType.ERROR, NotificationPriority.HIGH
        elif severity == ErrorSeverity.CRITICAL:
            return NotificationType.ERROR, NotificationPriority.URGENT
        else:
            return NotificationType.INFO, NotificationPriority.NORMAL

    def _add_to_history(self, notification_data: Dict[str, Any]) -> None:
        """
        Add a notification to the history, maintaining maximum size.

        Args:
            notification_data: Notification data to add
        """
        self._notification_history.append(notification_data)
        # Trim history if needed
        if len(self._notification_history) > self._max_history_size:
            self._notification_history = self._notification_history[-self._max_history_size:]

    def _show_system_notification(
        self,
        message: str,
        title: Optional[str],
        notification_type: NotificationType,
        priority: NotificationPriority,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Show a system notification.

        Args:
            message: Notification message
            title: Notification title
            notification_type: Type of notification
            priority: Notification priority
            action_label: Label for action button (optional)
            action_callback: Callback for action button (optional)
        """
        if not self._application:
            self.logger.warning("Cannot show system notification: application not set")
            return

        try:
            # Create notification
            notification = Gio.Notification.new(title or "Nightswitch")
            notification.set_body(message)

            # Set priority
            if priority == NotificationPriority.LOW:
                notification.set_priority(Gio.NotificationPriority.LOW)
            elif priority == NotificationPriority.NORMAL:
                notification.set_priority(Gio.NotificationPriority.NORMAL)
            elif priority == NotificationPriority.HIGH:
                notification.set_priority(Gio.NotificationPriority.HIGH)
            elif priority == NotificationPriority.URGENT:
                notification.set_priority(Gio.NotificationPriority.URGENT)

            # Add action if provided
            if action_label and action_callback:
                action_name = f"app.notification_action_{id(action_callback)}"
                
                # Register action with application
                action = Gio.SimpleAction.new(action_name.replace("app.", ""), None)
                action.connect("activate", lambda *args: action_callback())
                self._application.add_action(action)
                
                # Add action to notification
                notification.add_button(action_label, action_name)

            # Send notification
            self._application.send_notification(None, notification)

        except Exception as e:
            self.logger.error(f"Failed to show system notification: {e}")

    def _show_in_app_notification(
        self, message: str, notification_type: NotificationType, timeout: int
    ) -> None:
        """
        Show an in-app notification.

        Args:
            message: Notification message
            notification_type: Type of notification
            timeout: Notification timeout in seconds
        """
        if self._in_app_notification_callback:
            try:
                self._in_app_notification_callback(message, notification_type, timeout)
            except Exception as e:
                self.logger.error(f"Error in in-app notification callback: {e}")

    def _show_error_dialog(
        self, title: str, message: str, details: Optional[str] = None
    ) -> None:
        """
        Show an error dialog.

        Args:
            title: Dialog title
            message: Error message
            details: Additional details (optional)
        """
        if not self._dialog_parent:
            self.logger.warning("Cannot show error dialog: dialog parent not set")
            return

        try:
            dialog = Gtk.MessageDialog(
                transient_for=self._dialog_parent,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=title,
            )
            dialog.format_secondary_text(message)

            if details:
                # Add details in an expander
                expander = Gtk.Expander(label="Details")
                dialog.get_content_area().append(expander)

                details_label = Gtk.Label(label=details)
                details_label.set_margin_start(12)
                details_label.set_margin_end(12)
                details_label.set_margin_top(6)
                details_label.set_margin_bottom(6)
                details_label.set_wrap(True)
                details_label.set_selectable(True)

                expander.set_child(details_label)

            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.present()

        except Exception as e:
            self.logger.error(f"Failed to show error dialog: {e}")

    def show_info_dialog(
        self, title: str, message: str, parent: Optional[Gtk.Window] = None
    ) -> None:
        """
        Show an information dialog.

        Args:
            title: Dialog title
            message: Dialog message
            parent: Parent window (uses default if None)
        """
        parent_window = parent or self._dialog_parent
        if not parent_window:
            self.logger.warning("Cannot show info dialog: no parent window")
            return

        try:
            dialog = Gtk.MessageDialog(
                transient_for=parent_window,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title,
            )
            dialog.format_secondary_text(message)
            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.present()

        except Exception as e:
            self.logger.error(f"Failed to show info dialog: {e}")

    def show_warning_dialog(
        self, title: str, message: str, parent: Optional[Gtk.Window] = None
    ) -> None:
        """
        Show a warning dialog.

        Args:
            title: Dialog title
            message: Dialog message
            parent: Parent window (uses default if None)
        """
        parent_window = parent or self._dialog_parent
        if not parent_window:
            self.logger.warning("Cannot show warning dialog: no parent window")
            return

        try:
            dialog = Gtk.MessageDialog(
                transient_for=parent_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=title,
            )
            dialog.format_secondary_text(message)
            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.present()

        except Exception as e:
            self.logger.error(f"Failed to show warning dialog: {e}")

    def show_question_dialog(
        self,
        title: str,
        message: str,
        callback: Callable[[bool], None],
        parent: Optional[Gtk.Window] = None,
    ) -> None:
        """
        Show a question dialog with Yes/No buttons.

        Args:
            title: Dialog title
            message: Dialog message
            callback: Function to call with user's response (True for Yes, False for No)
            parent: Parent window (uses default if None)
        """
        parent_window = parent or self._dialog_parent
        if not parent_window:
            self.logger.warning("Cannot show question dialog: no parent window")
            return

        try:
            dialog = Gtk.MessageDialog(
                transient_for=parent_window,
                modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=title,
            )
            dialog.format_secondary_text(message)

            def on_response(dialog, response):
                dialog.destroy()
                callback(response == Gtk.ResponseType.YES)

            dialog.connect("response", on_response)
            dialog.present()

        except Exception as e:
            self.logger.error(f"Failed to show question dialog: {e}")

    def get_notification_history(
        self,
        notification_type: Optional[NotificationType] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notification history with optional filtering.

        Args:
            notification_type: Filter by notification type (optional)
            limit: Maximum number of notifications to return (optional)

        Returns:
            List of notification data dictionaries
        """
        filtered = self._notification_history

        # Apply type filter
        if notification_type:
            filtered = [n for n in filtered if n["type"] == notification_type]

        # Apply limit
        if limit and limit > 0:
            filtered = filtered[-limit:]

        return filtered

    def clear_notification_history(self) -> None:
        """Clear the notification history."""
        self._notification_history.clear()


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """
    Get the global notification manager instance.

    Returns:
        NotificationManager instance
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager