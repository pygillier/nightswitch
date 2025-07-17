"""
Unit tests for the notification module.
"""

import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from nightswitch.core.notification import (
    NotificationManager,
    NotificationType,
    NotificationPriority,
    get_notification_manager,
)
from nightswitch.core.error_handler import (
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
)


class TestNotificationManager(unittest.TestCase):
    """Test cases for the NotificationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh notification manager for each test
        self.notification_manager = NotificationManager()
        
        # Mock the logger
        self.mock_logger = MagicMock()
        self.notification_manager.logger = self.mock_logger
        
        # Mock application
        self.mock_application = MagicMock()
        self.notification_manager.set_application(self.mock_application)
        
        # Mock dialog parent
        self.mock_parent = MagicMock()
        self.notification_manager.set_dialog_parent(self.mock_parent)
    
    def test_notify_basic(self):
        """Test basic notification functionality."""
        # Set up in-app notification callback mock
        mock_callback = MagicMock()
        self.notification_manager.set_in_app_notification_callback(mock_callback)
        
        # Send notification
        self.notification_manager.notify(
            message="Test notification",
            title="Test Title",
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            timeout=5,
        )
        
        # Verify notification was added to history
        self.assertEqual(len(self.notification_manager._notification_history), 1)
        self.assertEqual(
            self.notification_manager._notification_history[0]["message"],
            "Test notification"
        )
        
        # Verify in-app notification callback was called
        mock_callback.assert_called_once_with(
            "Test notification", NotificationType.INFO, 5
        )
        
        # Verify system notification was sent
        self.mock_application.send_notification.assert_called_once()
        
        # Verify notification was logged
        self.mock_logger.log.assert_called_once()
    
    @patch("nightswitch.core.notification.Gio.Notification.new")
    def test_system_notification(self, mock_notification_new):
        """Test system notification functionality."""
        # Set up mock notification
        mock_notification = MagicMock()
        mock_notification_new.return_value = mock_notification
        
        # Send notification with action
        action_callback = MagicMock()
        self.notification_manager.notify(
            message="Test notification",
            title="Test Title",
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            use_in_app_notification=False,
            action_label="Action",
            action_callback=action_callback,
        )
        
        # Verify notification was created with correct title
        mock_notification_new.assert_called_once_with("Test Title")
        
        # Verify notification body was set
        mock_notification.set_body.assert_called_once_with("Test notification")
        
        # Verify priority was set
        mock_notification.set_priority.assert_called_once()
        
        # Verify action was added
        mock_notification.add_button.assert_called_once()
        
        # Verify action was registered with application
        self.mock_application.add_action.assert_called_once()
        
        # Verify notification was sent
        self.mock_application.send_notification.assert_called_once_with(
            None, mock_notification
        )
    
    def test_in_app_notification(self):
        """Test in-app notification functionality."""
        # Set up in-app notification callback mock
        mock_callback = MagicMock()
        self.notification_manager.set_in_app_notification_callback(mock_callback)
        
        # Send notification with only in-app
        self.notification_manager.notify(
            message="In-app notification",
            notification_type=NotificationType.SUCCESS,
            timeout=10,
            use_system_notification=False,
        )
        
        # Verify in-app notification callback was called with correct parameters
        mock_callback.assert_called_once_with(
            "In-app notification", NotificationType.SUCCESS, 10
        )
        
        # Verify system notification was not sent
        self.mock_application.send_notification.assert_not_called()
    
    @patch("nightswitch.core.notification.Gtk.MessageDialog")
    def test_error_dialog(self, mock_dialog_class):
        """Test error dialog functionality."""
        # Set up mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Call internal method to show error dialog
        self.notification_manager._show_error_dialog(
            title="Error Title",
            message="Error message",
            details="Error details",
        )
        
        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        self.assertEqual(mock_dialog_class.call_args[1]["text"], "Error Title")
        
        # Verify secondary text was set
        mock_dialog.format_secondary_text.assert_called_once_with("Error message")
        
        # Verify dialog was presented
        mock_dialog.present.assert_called_once()
    
    def test_notify_error(self):
        """Test error notification functionality."""
        # Create error context
        error_context = ErrorContext(
            message="Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
            suggestion="Try again later",
        )
        
        # Set up in-app notification callback mock
        mock_callback = MagicMock()
        self.notification_manager.set_in_app_notification_callback(mock_callback)
        
        # Notify about error
        self.notification_manager.notify_error(error_context)
        
        # Verify notification was added to history
        self.assertEqual(len(self.notification_manager._notification_history), 1)
        
        # Verify in-app notification callback was called
        mock_callback.assert_called_once()
        
        # Verify system notification was sent
        self.mock_application.send_notification.assert_called_once()
    
    @patch("nightswitch.core.notification.Gtk.MessageDialog")
    def test_notify_critical_error_shows_dialog(self, mock_dialog_class):
        """Test that critical errors show a dialog."""
        # Set up mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Create critical error context
        error_context = ErrorContext(
            message="Critical error",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
        )
        
        # Notify about critical error
        self.notification_manager.notify_error(
            error_context,
            use_system_notification=False,
            use_in_app_notification=False,
        )
        
        # Verify dialog was created
        mock_dialog_class.assert_called_once()
        
        # Verify dialog was presented
        mock_dialog.present.assert_called_once()
    
    def test_notification_history_filtering(self):
        """Test filtering notification history."""
        # Add notifications with different types
        self.notification_manager.notify(
            message="Info notification",
            notification_type=NotificationType.INFO,
            use_system_notification=False,
            use_in_app_notification=False,
        )
        self.notification_manager.notify(
            message="Warning notification",
            notification_type=NotificationType.WARNING,
            use_system_notification=False,
            use_in_app_notification=False,
        )
        self.notification_manager.notify(
            message="Error notification",
            notification_type=NotificationType.ERROR,
            use_system_notification=False,
            use_in_app_notification=False,
        )
        
        # Test filtering by type
        info_notifications = self.notification_manager.get_notification_history(
            notification_type=NotificationType.INFO
        )
        self.assertEqual(len(info_notifications), 1)
        self.assertEqual(info_notifications[0]["message"], "Info notification")
        
        # Test limit
        limited_notifications = self.notification_manager.get_notification_history(limit=2)
        self.assertEqual(len(limited_notifications), 2)
        self.assertEqual(limited_notifications[1]["message"], "Error notification")
    
    def test_notification_history_limit(self):
        """Test that notification history is limited to max size."""
        # Set small max history size
        self.notification_manager._max_history_size = 3
        
        # Add more notifications than the limit
        for i in range(5):
            self.notification_manager.notify(
                message=f"Notification {i}",
                use_system_notification=False,
                use_in_app_notification=False,
            )
        
        # Verify history is limited to max size
        self.assertEqual(len(self.notification_manager._notification_history), 3)
        
        # Verify oldest notifications were removed
        messages = [n["message"] for n in self.notification_manager._notification_history]
        self.assertEqual(messages, ["Notification 2", "Notification 3", "Notification 4"])
    
    def test_clear_notification_history(self):
        """Test clearing notification history."""
        # Add some notifications
        for i in range(3):
            self.notification_manager.notify(
                message=f"Notification {i}",
                use_system_notification=False,
                use_in_app_notification=False,
            )
        
        # Verify notifications were added
        self.assertEqual(len(self.notification_manager._notification_history), 3)
        
        # Clear history
        self.notification_manager.clear_notification_history()
        
        # Verify history is empty
        self.assertEqual(len(self.notification_manager._notification_history), 0)
    
    @patch("nightswitch.core.notification.Gtk.MessageDialog")
    def test_show_info_dialog(self, mock_dialog_class):
        """Test info dialog functionality."""
        # Set up mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Show info dialog
        self.notification_manager.show_info_dialog(
            title="Info Title",
            message="Info message",
        )
        
        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        self.assertEqual(mock_dialog_class.call_args[1]["text"], "Info Title")
        self.assertEqual(mock_dialog_class.call_args[1]["message_type"], Gtk.MessageType.INFO)
        
        # Verify secondary text was set
        mock_dialog.format_secondary_text.assert_called_once_with("Info message")
        
        # Verify dialog was presented
        mock_dialog.present.assert_called_once()
    
    @patch("nightswitch.core.notification.Gtk.MessageDialog")
    def test_show_warning_dialog(self, mock_dialog_class):
        """Test warning dialog functionality."""
        # Set up mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Show warning dialog
        self.notification_manager.show_warning_dialog(
            title="Warning Title",
            message="Warning message",
        )
        
        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        self.assertEqual(mock_dialog_class.call_args[1]["text"], "Warning Title")
        self.assertEqual(mock_dialog_class.call_args[1]["message_type"], Gtk.MessageType.WARNING)
        
        # Verify secondary text was set
        mock_dialog.format_secondary_text.assert_called_once_with("Warning message")
        
        # Verify dialog was presented
        mock_dialog.present.assert_called_once()
    
    @patch("nightswitch.core.notification.Gtk.MessageDialog")
    def test_show_question_dialog(self, mock_dialog_class):
        """Test question dialog functionality."""
        # Set up mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Create callback mock
        callback_mock = MagicMock()
        
        # Show question dialog
        self.notification_manager.show_question_dialog(
            title="Question Title",
            message="Question message",
            callback=callback_mock,
        )
        
        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        self.assertEqual(mock_dialog_class.call_args[1]["text"], "Question Title")
        self.assertEqual(mock_dialog_class.call_args[1]["message_type"], Gtk.MessageType.QUESTION)
        self.assertEqual(mock_dialog_class.call_args[1]["buttons"], Gtk.ButtonsType.YES_NO)
        
        # Verify secondary text was set
        mock_dialog.format_secondary_text.assert_called_once_with("Question message")
        
        # Verify dialog was presented
        mock_dialog.present.assert_called_once()
        
        # Simulate YES response
        response_handler = mock_dialog.connect.call_args[0][1]
        response_handler(mock_dialog, Gtk.ResponseType.YES)
        
        # Verify callback was called with True
        callback_mock.assert_called_once_with(True)


class TestGlobalNotificationManager(unittest.TestCase):
    """Test cases for the global notification manager instance."""
    
    def test_get_notification_manager(self):
        """Test that get_notification_manager returns a singleton instance."""
        # Get manager instances
        manager1 = get_notification_manager()
        manager2 = get_notification_manager()
        
        # Verify they are the same instance
        self.assertIs(manager1, manager2)
        
        # Verify it's a NotificationManager instance
        self.assertIsInstance(manager1, NotificationManager)


if __name__ == "__main__":
    unittest.main()