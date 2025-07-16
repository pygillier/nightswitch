"""
Unit tests for the ScheduleModeHandler class.

Tests the schedule mode functionality including time validation,
mode enabling/disabling, and integration with ScheduleService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.nightswitch.core.schedule_mode import ScheduleModeHandler, get_schedule_mode_handler
from src.nightswitch.core.manual_mode import ThemeType


class TestScheduleModeHandler:
    """Test cases for ScheduleModeHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_schedule_service = Mock()
        self.mock_theme_callback = Mock(return_value=True)
        
        # Mock the get_next_trigger_time to return None by default
        self.mock_schedule_service.get_next_trigger_time.return_value = None
        
        self.handler = ScheduleModeHandler(
            schedule_service=self.mock_schedule_service,
            theme_callback=self.mock_theme_callback
        )

    def teardown_method(self):
        """Clean up after tests."""
        if self.handler:
            self.handler.cleanup()

    def test_init(self):
        """Test ScheduleModeHandler initialization."""
        assert not self.handler._is_enabled
        assert self.handler._dark_time is None
        assert self.handler._light_time is None
        assert self.handler._theme_callback == self.mock_theme_callback
        assert self.handler._schedule_service == self.mock_schedule_service

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with patch('src.nightswitch.core.schedule_mode.get_schedule_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            handler = ScheduleModeHandler()
            
            assert handler._schedule_service == mock_service
            assert handler._theme_callback is None

    def test_enable_valid_schedule(self):
        """Test enabling schedule mode with valid times."""
        dark_time = "20:00"
        light_time = "08:00"
        
        # Mock successful schedule service setup
        self.mock_schedule_service.set_schedule.return_value = True
        
        result = self.handler.enable(dark_time, light_time)
        
        assert result is True
        assert self.handler._is_enabled is True
        assert self.handler._dark_time == dark_time
        assert self.handler._light_time == light_time
        
        # Verify schedule service was called correctly
        self.mock_schedule_service.set_schedule.assert_called_once()
        call_args = self.mock_schedule_service.set_schedule.call_args
        assert call_args[0][0] == dark_time  # First positional arg
        assert call_args[0][1] == light_time  # Second positional arg
        assert callable(call_args[0][2])  # Third positional arg (callback)

    def test_enable_invalid_time_format(self):
        """Test enabling schedule mode with invalid time formats."""
        invalid_cases = [
            ("25:00", "08:00"),  # Invalid hour
            ("20:00", "24:60"),  # Invalid minute
            ("abc", "08:00"),    # Non-numeric
            ("20:00", "def"),    # Non-numeric
            ("", "08:00"),       # Empty string
            ("20:00", ""),       # Empty string
        ]
        
        for dark_time, light_time in invalid_cases:
            result = self.handler.enable(dark_time, light_time)
            
            assert result is False
            assert not self.handler._is_enabled
            
            # Schedule service should not be called for invalid times
            self.mock_schedule_service.set_schedule.assert_not_called()
            self.mock_schedule_service.reset_mock()

    def test_enable_same_times(self):
        """Test enabling schedule mode with identical times."""
        same_time = "12:00"
        
        result = self.handler.enable(same_time, same_time)
        
        assert result is False
        assert not self.handler._is_enabled
        self.mock_schedule_service.set_schedule.assert_not_called()

    def test_enable_service_failure(self):
        """Test enabling schedule mode when service fails."""
        # Mock service failure
        self.mock_schedule_service.set_schedule.return_value = False
        
        result = self.handler.enable("20:00", "08:00")
        
        assert result is False
        assert not self.handler._is_enabled

    def test_disable(self):
        """Test disabling schedule mode."""
        # First enable the mode
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        assert self.handler._is_enabled
        
        # Now disable it
        result = self.handler.disable()
        
        assert result is True
        assert not self.handler._is_enabled
        assert self.handler._dark_time is None
        assert self.handler._light_time is None
        
        # Verify schedule service was stopped
        self.mock_schedule_service.stop_schedule.assert_called_once()

    def test_set_theme_callback(self):
        """Test setting theme callback."""
        new_callback = Mock()
        
        self.handler.set_theme_callback(new_callback)
        
        assert self.handler._theme_callback == new_callback

    def test_handle_scheduled_theme_change_dark(self):
        """Test handling scheduled dark theme change."""
        self.handler._handle_scheduled_theme_change("dark")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)

    def test_handle_scheduled_theme_change_light(self):
        """Test handling scheduled light theme change."""
        self.handler._handle_scheduled_theme_change("light")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.LIGHT)

    def test_handle_scheduled_theme_change_invalid(self):
        """Test handling scheduled theme change with invalid theme."""
        self.handler._handle_scheduled_theme_change("invalid")
        
        # Callback should not be called for invalid theme
        self.mock_theme_callback.assert_not_called()

    def test_handle_scheduled_theme_change_no_callback(self):
        """Test handling scheduled theme change without callback."""
        handler = ScheduleModeHandler(schedule_service=self.mock_schedule_service)
        
        # This should not raise an exception
        handler._handle_scheduled_theme_change("dark")

    def test_handle_scheduled_theme_change_callback_failure(self):
        """Test handling scheduled theme change when callback fails."""
        self.mock_theme_callback.return_value = False
        
        # This should not raise an exception
        self.handler._handle_scheduled_theme_change("dark")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)

    def test_get_schedule_times(self):
        """Test getting current schedule times."""
        # Test when not set
        dark_time, light_time = self.handler.get_schedule_times()
        assert dark_time is None
        assert light_time is None
        
        # Enable schedule and test
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        
        dark_time, light_time = self.handler.get_schedule_times()
        assert dark_time == "20:00"
        assert light_time == "08:00"

    def test_is_enabled(self):
        """Test is_enabled status method."""
        assert not self.handler.is_enabled()
        
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        assert self.handler.is_enabled()
        
        self.handler.disable()
        assert not self.handler.is_enabled()

    def test_get_next_trigger(self):
        """Test getting next trigger information."""
        # Mock service response
        expected_trigger = ("20:00", "dark")
        self.mock_schedule_service.get_next_trigger_time.return_value = expected_trigger
        
        result = self.handler.get_next_trigger()
        
        assert result == expected_trigger
        self.mock_schedule_service.get_next_trigger_time.assert_called_once()

    def test_get_next_trigger_service_error(self):
        """Test getting next trigger when service raises error."""
        self.mock_schedule_service.get_next_trigger_time.side_effect = Exception("Service error")
        
        result = self.handler.get_next_trigger()
        
        assert result is None

    def test_get_status(self):
        """Test getting detailed status information."""
        # Mock service status
        service_status = {
            "is_running": True,
            "dark_time": "20:00",
            "light_time": "08:00"
        }
        self.mock_schedule_service.get_schedule_status.return_value = service_status
        
        # Enable schedule mode
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        
        # Mock next trigger
        self.mock_schedule_service.get_next_trigger_time.return_value = ("20:00", "dark")
        
        status = self.handler.get_status()
        
        assert status["enabled"] is True
        assert status["dark_time"] == "20:00"
        assert status["light_time"] == "08:00"
        assert status["has_theme_callback"] is True
        assert status["service"] == service_status
        assert status["next_trigger_time"] == "20:00"
        assert status["next_trigger_theme"] == "dark"

    def test_get_status_service_error(self):
        """Test getting status when service raises error."""
        self.mock_schedule_service.get_schedule_status.side_effect = Exception("Service error")
        # Mock get_next_trigger to return None to avoid subscript error
        self.mock_schedule_service.get_next_trigger_time.return_value = None
        
        status = self.handler.get_status()
        
        assert "error" in status["service"]

    def test_validate_schedule_times_valid(self):
        """Test schedule time validation with valid times."""
        valid_cases = [
            ("00:00", "12:00"),
            ("08:30", "20:15"),
            ("23:59", "00:01"),
        ]
        
        for dark_time, light_time in valid_cases:
            is_valid, error = self.handler.validate_schedule_times(dark_time, light_time)
            assert is_valid is True
            assert error is None

    def test_validate_schedule_times_invalid(self):
        """Test schedule time validation with invalid times."""
        invalid_cases = [
            ("25:00", "08:00", "Invalid dark time format"),
            ("20:00", "24:60", "Invalid light time format"),
            ("12:00", "12:00", "cannot be the same"),
            ("abc", "08:00", "Invalid dark time format"),
            ("20:00", "def", "Invalid light time format"),
        ]
        
        for dark_time, light_time, expected_error_part in invalid_cases:
            is_valid, error = self.handler.validate_schedule_times(dark_time, light_time)
            assert is_valid is False
            assert error is not None
            assert expected_error_part in error

    def test_status_callbacks(self):
        """Test status change callback functionality."""
        callback_mock = Mock()
        
        # Add callback
        self.handler.add_status_callback(callback_mock)
        
        # Enable schedule mode (should trigger callback)
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        
        # Verify callback was called
        callback_mock.assert_called()
        
        # Reset mock and disable (should trigger callback again)
        callback_mock.reset_mock()
        self.handler.disable()
        callback_mock.assert_called()
        
        # Remove callback
        self.handler.remove_status_callback(callback_mock)
        
        # Enable again (callback should not be called)
        callback_mock.reset_mock()
        self.handler.enable("21:00", "09:00")
        callback_mock.assert_not_called()

    def test_status_callback_error_handling(self):
        """Test error handling in status callbacks."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        
        self.handler.add_status_callback(error_callback)
        
        # This should not raise an exception
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        
        # Verify callback was called despite error
        error_callback.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        # Enable schedule mode first
        self.mock_schedule_service.set_schedule.return_value = True
        self.handler.enable("20:00", "08:00")
        
        # Add status callback
        callback_mock = Mock()
        self.handler.add_status_callback(callback_mock)
        
        # Cleanup
        self.handler.cleanup()
        
        # Verify everything is cleaned up
        assert not self.handler._is_enabled
        assert len(self.handler._status_callbacks) == 0
        self.mock_schedule_service.cleanup.assert_called_once()

    def test_integration_with_schedule_callback(self):
        """Test integration between handler and schedule service callback."""
        # Enable schedule mode
        self.mock_schedule_service.set_schedule.return_value = True
        result = self.handler.enable("20:00", "08:00")
        assert result is True
        
        # Get the callback that was passed to the schedule service
        call_args = self.mock_schedule_service.set_schedule.call_args
        schedule_callback = call_args[0][2]  # Third positional argument
        
        # Call the callback as the schedule service would
        schedule_callback("dark")
        
        # Verify theme callback was called
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)


class TestScheduleModeHandlerGlobal:
    """Test cases for global schedule mode handler functions."""

    def test_get_schedule_mode_handler_singleton(self):
        """Test that get_schedule_mode_handler returns singleton instance."""
        handler1 = get_schedule_mode_handler()
        handler2 = get_schedule_mode_handler()
        
        assert handler1 is handler2
        assert isinstance(handler1, ScheduleModeHandler)

    def teardown_method(self):
        """Clean up global instance."""
        handler = get_schedule_mode_handler()
        if handler:
            handler.cleanup()