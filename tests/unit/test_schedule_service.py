"""
Unit tests for the ScheduleService class.

Tests the time-based theme switching functionality including timer accuracy,
schedule validation, and error handling.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.nightswitch.services.schedule import ScheduleService, get_schedule_service


class TestScheduleService:
    """Test cases for ScheduleService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScheduleService()
        self.callback_mock = Mock()

    def teardown_method(self):
        """Clean up after tests."""
        if self.service:
            self.service.cleanup()

    def test_init(self):
        """Test ScheduleService initialization."""
        assert self.service._dark_time is None
        assert self.service._light_time is None
        assert self.service._callback is None
        assert not self.service._is_running
        assert self.service._timer_thread is None

    def test_validate_time_format_valid(self):
        """Test time format validation with valid times."""
        valid_times = ["00:00", "12:30", "23:59", "9:15", "01:05"]
        
        for time_str in valid_times:
            assert self.service._validate_time_format(time_str), f"Should accept {time_str}"

    def test_validate_time_format_invalid(self):
        """Test time format validation with invalid times."""
        invalid_times = [
            "24:00",  # Invalid hour
            "12:60",  # Invalid minute
            "1:5",    # Missing leading zeros
            "12:5",   # Missing leading zero for minute
            "abc",    # Non-numeric
            "12",     # Missing minute
            "12:",    # Missing minute value
            ":30",    # Missing hour
            "12:30:00",  # Seconds included
            "",       # Empty string
        ]
        
        for time_str in invalid_times:
            assert not self.service._validate_time_format(time_str), f"Should reject {time_str}"

    def test_time_to_minutes(self):
        """Test conversion of time strings to minutes."""
        test_cases = [
            ("00:00", 0),
            ("01:00", 60),
            ("12:30", 750),
            ("23:59", 1439),
            ("06:15", 375),
        ]
        
        for time_str, expected_minutes in test_cases:
            result = self.service._time_to_minutes(time_str)
            assert result == expected_minutes, f"{time_str} should convert to {expected_minutes} minutes"

    def test_set_schedule_valid(self):
        """Test setting a valid schedule."""
        dark_time = "20:00"
        light_time = "08:00"
        
        result = self.service.set_schedule(dark_time, light_time, self.callback_mock)
        
        assert result is True
        assert self.service._dark_time == dark_time
        assert self.service._light_time == light_time
        assert self.service._callback == self.callback_mock
        assert self.service._is_running is True
        assert self.service._timer_thread is not None
        assert self.service._timer_thread.is_alive()

    def test_set_schedule_invalid_times(self):
        """Test setting schedule with invalid time formats."""
        invalid_cases = [
            ("25:00", "08:00"),  # Invalid dark time
            ("20:00", "24:60"),  # Invalid light time
            ("abc", "08:00"),    # Non-numeric dark time
            ("20:00", "def"),    # Non-numeric light time
        ]
        
        for dark_time, light_time in invalid_cases:
            result = self.service.set_schedule(dark_time, light_time, self.callback_mock)
            assert result is False
            assert not self.service._is_running

    def test_set_schedule_same_times(self):
        """Test setting schedule with identical times."""
        same_time = "12:00"
        
        result = self.service.set_schedule(same_time, same_time, self.callback_mock)
        
        assert result is False
        assert not self.service._is_running

    def test_stop_schedule(self):
        """Test stopping an active schedule."""
        # First set a schedule
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        assert self.service._is_running
        
        # Stop the schedule
        self.service.stop_schedule()
        
        assert not self.service._is_running
        assert self.service._dark_time is None or not self.service._is_running

    def test_get_schedule_status(self):
        """Test getting schedule status information."""
        # Test status when not running
        status = self.service.get_schedule_status()
        assert status["is_running"] is False
        assert status["dark_time"] is None
        assert status["light_time"] is None
        assert status["has_callback"] is False
        
        # Set schedule and test status
        dark_time = "22:00"
        light_time = "07:00"
        self.service.set_schedule(dark_time, light_time, self.callback_mock)
        
        status = self.service.get_schedule_status()
        assert status["is_running"] is True
        assert status["dark_time"] == dark_time
        assert status["light_time"] == light_time
        assert status["has_callback"] is True
        assert status["thread_alive"] is True

    def test_get_next_trigger_time(self):
        """Test getting next trigger time information."""
        # Test when no schedule is set
        result = self.service.get_next_trigger_time()
        assert result is None
        
        # Set schedule and test next trigger
        dark_time = "20:00"
        light_time = "08:00"
        self.service.set_schedule(dark_time, light_time, self.callback_mock)
        
        result = self.service.get_next_trigger_time()
        assert result is not None
        assert len(result) == 2
        assert result[0] in [dark_time, light_time]
        assert result[1] in ["dark", "light"]

    @patch('src.nightswitch.services.schedule.datetime')
    def test_check_schedule_triggers_dark(self, mock_datetime):
        """Test schedule trigger detection for dark theme."""
        # Mock current time to match dark time
        mock_now = Mock()
        mock_now.strftime.return_value = "20:00"
        mock_datetime.now.return_value = mock_now
        
        # Set schedule
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        
        # Trigger check
        self.service._check_schedule_triggers(mock_now)
        
        # Verify callback was called with dark theme
        self.callback_mock.assert_called_once_with("dark")

    @patch('src.nightswitch.services.schedule.datetime')
    def test_check_schedule_triggers_light(self, mock_datetime):
        """Test schedule trigger detection for light theme."""
        # Mock current time to match light time
        mock_now = Mock()
        mock_now.strftime.return_value = "08:00"
        mock_datetime.now.return_value = mock_now
        
        # Set schedule
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        
        # Trigger check
        self.service._check_schedule_triggers(mock_now)
        
        # Verify callback was called with light theme
        self.callback_mock.assert_called_once_with("light")

    @patch('src.nightswitch.services.schedule.datetime')
    def test_check_schedule_triggers_no_match(self, mock_datetime):
        """Test schedule trigger detection with no matching time."""
        # Mock current time that doesn't match schedule
        mock_now = Mock()
        mock_now.strftime.return_value = "15:30"
        mock_datetime.now.return_value = mock_now
        
        # Set schedule
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        
        # Trigger check
        self.service._check_schedule_triggers(mock_now)
        
        # Verify callback was not called
        self.callback_mock.assert_not_called()

    def test_callback_error_handling(self):
        """Test error handling when callback raises exception."""
        # Create callback that raises exception
        error_callback = Mock(side_effect=Exception("Callback error"))
        
        # Set schedule with error callback
        self.service.set_schedule("20:00", "08:00", error_callback)
        
        # Mock current time to trigger callback
        with patch('src.nightswitch.services.schedule.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.strftime.return_value = "20:00"
            mock_datetime.now.return_value = mock_now
            
            # This should not raise an exception
            self.service._check_schedule_triggers(mock_now)
            
            # Verify callback was called despite error
            error_callback.assert_called_once_with("dark")

    def test_is_running(self):
        """Test is_running status method."""
        assert not self.service.is_running()
        
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        assert self.service.is_running()
        
        self.service.stop_schedule()
        assert not self.service.is_running()

    def test_cleanup(self):
        """Test cleanup method."""
        # Set schedule first
        self.service.set_schedule("20:00", "08:00", self.callback_mock)
        assert self.service.is_running()
        
        # Cleanup
        self.service.cleanup()
        
        # Verify everything is stopped
        assert not self.service.is_running()

    def test_thread_safety(self):
        """Test thread safety of schedule operations."""
        def set_and_stop():
            for i in range(10):
                self.service.set_schedule("20:00", "08:00", self.callback_mock)
                time.sleep(0.01)
                self.service.stop_schedule()
                time.sleep(0.01)
        
        # Run multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=set_and_stop)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Service should be in a consistent state
        assert not self.service.is_running()

    def test_timer_accuracy_simulation(self):
        """Test timer accuracy with simulated time progression."""
        callback_calls = []
        
        def test_callback(theme):
            callback_calls.append((datetime.now(), theme))
        
        # Set schedule
        self.service.set_schedule("20:00", "08:00", test_callback)
        
        # Simulate time progression by directly calling check method
        with patch('src.nightswitch.services.schedule.datetime') as mock_datetime:
            # Test dark trigger
            mock_now = Mock()
            mock_now.strftime.return_value = "20:00"
            mock_datetime.now.return_value = mock_now
            
            self.service._check_schedule_triggers(mock_now)
            
            # Test light trigger
            mock_now.strftime.return_value = "08:00"
            self.service._check_schedule_triggers(mock_now)
        
        # Verify both triggers were called
        assert len(callback_calls) == 2
        assert callback_calls[0][1] == "dark"
        assert callback_calls[1][1] == "light"


class TestScheduleServiceGlobal:
    """Test cases for global schedule service functions."""

    def test_get_schedule_service_singleton(self):
        """Test that get_schedule_service returns singleton instance."""
        service1 = get_schedule_service()
        service2 = get_schedule_service()
        
        assert service1 is service2
        assert isinstance(service1, ScheduleService)

    def teardown_method(self):
        """Clean up global instance."""
        service = get_schedule_service()
        if service:
            service.cleanup()