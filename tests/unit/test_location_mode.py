"""
Unit tests for LocationModeHandler.

Tests the location-based theme switching functionality including
location detection, sunrise/sunset integration, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.nightswitch.core.location_mode import LocationModeHandler, get_location_mode_handler
from src.nightswitch.core.manual_mode import ThemeType


class TestLocationModeHandler:
    """Test cases for LocationModeHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_location_service = Mock()
        self.mock_sunrise_sunset_service = Mock()
        self.mock_theme_callback = Mock()
        
        self.handler = LocationModeHandler(
            location_service=self.mock_location_service,
            sunrise_sunset_service=self.mock_sunrise_sunset_service,
            theme_callback=self.mock_theme_callback
        )

    def test_init(self):
        """Test LocationModeHandler initialization."""
        assert self.handler._location_service == self.mock_location_service
        assert self.handler._sunrise_sunset_service == self.mock_sunrise_sunset_service
        assert self.handler._theme_callback == self.mock_theme_callback
        assert self.handler._is_enabled is False
        assert self.handler._current_location is None
        assert self.handler._auto_location is True

    def test_enable_with_manual_coordinates_success(self):
        """Test enabling location mode with manual coordinates."""
        # Mock successful scheduling
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = True
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "day"
        self.mock_theme_callback.return_value = True
        
        result = self.handler.enable(40.7128, -74.0060)
        
        assert result is True
        assert self.handler._is_enabled is True
        assert self.handler._current_location == (40.7128, -74.006, "Manual location (40.7128, -74.006)")
        assert self.handler._auto_location is False
        
        # Verify scheduling was set up
        self.mock_sunrise_sunset_service.schedule_sun_events.assert_called_once_with(
            40.7128, -74.0060, self.handler._handle_sun_event
        )
        
        # Verify initial theme was applied
        self.mock_theme_callback.assert_called_once_with(ThemeType.LIGHT)

    def test_enable_with_manual_coordinates_invalid(self):
        """Test enabling location mode with invalid manual coordinates."""
        result = self.handler.enable(91, 0)  # Invalid latitude
        
        assert result is False
        assert self.handler._is_enabled is False
        assert self.handler._current_location is None

    def test_enable_with_auto_location_success(self):
        """Test enabling location mode with auto-detected location."""
        # Mock successful location detection
        self.mock_location_service.get_current_location.return_value = (
            40.7128, -74.0060, "New York, United States"
        )
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = True
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "night"
        self.mock_theme_callback.return_value = True
        
        result = self.handler.enable()
        
        assert result is True
        assert self.handler._is_enabled is True
        assert self.handler._current_location == (40.7128, -74.0060, "New York, United States")
        assert self.handler._auto_location is True
        
        # Verify location detection was called
        self.mock_location_service.get_current_location.assert_called_once()
        
        # Verify initial theme was applied (night -> dark)
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)

    def test_enable_with_auto_location_failure(self):
        """Test enabling location mode when auto-location fails."""
        # Mock failed location detection
        self.mock_location_service.get_current_location.return_value = None
        
        result = self.handler.enable()
        
        assert result is False
        assert self.handler._is_enabled is False
        assert self.handler._current_location is None

    def test_enable_scheduling_failure(self):
        """Test enabling location mode when scheduling fails."""
        # Mock successful location but failed scheduling
        self.mock_location_service.get_current_location.return_value = (
            40.7128, -74.0060, "New York, United States"
        )
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = False
        
        result = self.handler.enable()
        
        assert result is False
        assert self.handler._is_enabled is False

    def test_disable_success(self):
        """Test disabling location mode."""
        # Set up enabled state
        self.handler._is_enabled = True
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        
        result = self.handler.disable()
        
        assert result is True
        assert self.handler._is_enabled is False
        assert self.handler._current_location is None
        assert self.handler._auto_location is True
        
        # Verify scheduling was stopped
        self.mock_sunrise_sunset_service.stop_sun_events.assert_called_once()

    def test_set_theme_callback(self):
        """Test setting theme callback."""
        new_callback = Mock()
        
        self.handler.set_theme_callback(new_callback)
        
        assert self.handler._theme_callback == new_callback

    def test_handle_sun_event_sunrise(self):
        """Test handling sunrise event."""
        self.mock_theme_callback.return_value = True
        
        self.handler._handle_sun_event("sunrise")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.LIGHT)

    def test_handle_sun_event_sunset(self):
        """Test handling sunset event."""
        self.mock_theme_callback.return_value = True
        
        self.handler._handle_sun_event("sunset")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)

    def test_handle_sun_event_invalid(self):
        """Test handling invalid sun event."""
        self.handler._handle_sun_event("invalid")
        
        # Should not call theme callback for invalid events
        self.mock_theme_callback.assert_not_called()

    def test_handle_sun_event_callback_failure(self):
        """Test handling sun event when callback fails."""
        self.mock_theme_callback.return_value = False
        
        # Should not raise exception even if callback fails
        self.handler._handle_sun_event("sunrise")
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.LIGHT)

    def test_handle_sun_event_no_callback(self):
        """Test handling sun event when no callback is set."""
        self.handler._theme_callback = None
        
        # Should not raise exception when no callback is set
        self.handler._handle_sun_event("sunrise")

    def test_apply_initial_theme_day(self):
        """Test applying initial theme during day."""
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "day"
        self.mock_theme_callback.return_value = True
        
        self.handler._apply_initial_theme()
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.LIGHT)

    def test_apply_initial_theme_night(self):
        """Test applying initial theme during night."""
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "night"
        self.mock_theme_callback.return_value = True
        
        self.handler._apply_initial_theme()
        
        self.mock_theme_callback.assert_called_once_with(ThemeType.DARK)

    def test_apply_initial_theme_unknown_period(self):
        """Test applying initial theme when sun period is unknown."""
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = None
        
        self.handler._apply_initial_theme()
        
        # Should not call theme callback for unknown period
        self.mock_theme_callback.assert_not_called()

    def test_apply_initial_theme_no_location(self):
        """Test applying initial theme when no location is set."""
        self.handler._current_location = None
        
        self.handler._apply_initial_theme()
        
        # Should not call theme callback when no location
        self.mock_theme_callback.assert_not_called()

    def test_refresh_location_success(self):
        """Test refreshing location successfully."""
        # Set up enabled auto-location mode
        self.handler._is_enabled = True
        self.handler._auto_location = True
        self.handler._current_location = (40.0, -74.0, "Old Location")
        
        # Mock successful location refresh
        self.mock_location_service.get_current_location.return_value = (
            40.7128, -74.0060, "New York, United States"
        )
        self.mock_sunrise_sunset_service.schedule_sun_events.return_value = True
        self.mock_sunrise_sunset_service.get_current_sun_period.return_value = "day"
        self.mock_theme_callback.return_value = True
        
        result = self.handler.refresh_location()
        
        assert result is True
        assert self.handler._current_location == (40.7128, -74.0060, "New York, United States")
        
        # Verify location cache was cleared
        self.mock_location_service.clear_cache.assert_called_once()
        
        # Verify scheduling was updated
        self.mock_sunrise_sunset_service.stop_sun_events.assert_called_once()
        self.mock_sunrise_sunset_service.schedule_sun_events.assert_called_once_with(
            40.7128, -74.0060, self.handler._handle_sun_event
        )

    def test_refresh_location_manual_mode(self):
        """Test refreshing location in manual mode."""
        self.handler._auto_location = False
        
        result = self.handler.refresh_location()
        
        assert result is False

    def test_refresh_location_not_enabled(self):
        """Test refreshing location when not enabled."""
        self.handler._is_enabled = False
        self.handler._auto_location = True
        
        result = self.handler.refresh_location()
        
        assert result is False

    def test_refresh_location_failure(self):
        """Test refreshing location when detection fails."""
        self.handler._is_enabled = True
        self.handler._auto_location = True
        self.mock_location_service.get_current_location.return_value = None
        
        result = self.handler.refresh_location()
        
        assert result is False

    def test_get_current_location(self):
        """Test getting current location."""
        test_location = (40.7128, -74.0060, "Test Location")
        self.handler._current_location = test_location
        
        result = self.handler.get_current_location()
        
        assert result == test_location

    def test_get_current_location_none(self):
        """Test getting current location when none is set."""
        result = self.handler.get_current_location()
        
        assert result is None

    def test_is_enabled(self):
        """Test checking if location mode is enabled."""
        assert self.handler.is_enabled() is False
        
        self.handler._is_enabled = True
        assert self.handler.is_enabled() is True

    def test_is_auto_location(self):
        """Test checking if auto-location is enabled."""
        assert self.handler.is_auto_location() is True
        
        self.handler._auto_location = False
        assert self.handler.is_auto_location() is False

    def test_get_next_sun_event_success(self):
        """Test getting next sun event successfully."""
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        next_event_time = datetime(2024, 1, 15, 18, 45)
        self.mock_sunrise_sunset_service.get_next_sun_event.return_value = (
            next_event_time, "sunset"
        )
        
        result = self.handler.get_next_sun_event()
        
        assert result is not None
        event_time, event_type, event_date = result
        assert event_time == "18:45"
        assert event_type == "sunset"
        assert event_date == "2024-01-15"

    def test_get_next_sun_event_no_location(self):
        """Test getting next sun event when no location is set."""
        self.handler._current_location = None
        
        result = self.handler.get_next_sun_event()
        
        assert result is None

    def test_get_next_sun_event_service_failure(self):
        """Test getting next sun event when service fails."""
        self.handler._current_location = (40.7128, -74.0060, "Test Location")
        self.mock_sunrise_sunset_service.get_next_sun_event.return_value = None
        
        result = self.handler.get_next_sun_event()
        
        assert result is None

    def test_get_status_disabled(self):
        """Test getting status when disabled."""
        status = self.handler.get_status()
        
        assert status["enabled"] is False
        assert status["auto_location"] is True
        assert status["has_theme_callback"] is True

    def test_get_status_enabled_with_location(self):
        """Test getting status when enabled with location."""
        self.handler._is_enabled = True
        self.handler._current_location = (40.7128, -74.0060, "New York, United States")
        self.handler._auto_location = False
        
        # Mock service status
        self.mock_location_service.get_location_info.return_value = {"test": "location_info"}
        self.mock_sunrise_sunset_service.get_service_status.return_value = {"test": "sunrise_info"}
        
        # Mock next event
        next_event_time = datetime(2024, 1, 15, 18, 45)
        self.mock_sunrise_sunset_service.get_next_sun_event.return_value = (
            next_event_time, "sunset"
        )
        
        status = self.handler.get_status()
        
        assert status["enabled"] is True
        assert status["auto_location"] is False
        assert status["location"]["latitude"] == 40.7128
        assert status["location"]["longitude"] == -74.0060
        assert status["location"]["description"] == "New York, United States"
        assert status["next_event"]["time"] == "18:45"
        assert status["next_event"]["type"] == "sunset"
        assert status["next_event"]["date"] == "2024-01-15"

    def test_add_status_callback(self):
        """Test adding status callback."""
        callback = Mock()
        
        self.handler.add_status_callback(callback)
        
        assert callback in self.handler._status_callbacks

    def test_remove_status_callback(self):
        """Test removing status callback."""
        callback = Mock()
        self.handler._status_callbacks.append(callback)
        
        self.handler.remove_status_callback(callback)
        
        assert callback not in self.handler._status_callbacks

    def test_add_error_callback(self):
        """Test adding error callback."""
        callback = Mock()
        
        self.handler.add_error_callback(callback)
        
        assert callback in self.handler._error_callbacks

    def test_remove_error_callback(self):
        """Test removing error callback."""
        callback = Mock()
        self.handler._error_callbacks.append(callback)
        
        self.handler.remove_error_callback(callback)
        
        assert callback not in self.handler._error_callbacks

    def test_notify_status_change(self):
        """Test notifying status change callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        self.handler.add_status_callback(callback1)
        self.handler.add_status_callback(callback2)
        
        self.handler._notify_status_change()
        
        callback1.assert_called_once()
        callback2.assert_called_once()
        # Both should be called with the same status dict
        assert callback1.call_args[0][0] == callback2.call_args[0][0]

    def test_notify_error(self):
        """Test notifying error callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        self.handler.add_error_callback(callback1)
        self.handler.add_error_callback(callback2)
        
        self.handler._notify_error("test_error", "Test error message")
        
        callback1.assert_called_once_with("test_error", "Test error message")
        callback2.assert_called_once_with("test_error", "Test error message")

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates."""
        assert self.handler._validate_coordinates(40.7128, -74.0060) is True
        assert self.handler._validate_coordinates(90, 180) is True
        assert self.handler._validate_coordinates(-90, -180) is True

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid coordinates."""
        assert self.handler._validate_coordinates(91, 0) is False
        assert self.handler._validate_coordinates(0, 181) is False
        assert self.handler._validate_coordinates("40.7", "-74.0") is False
        assert self.handler._validate_coordinates(None, None) is False

    def test_test_connectivity(self):
        """Test connectivity testing."""
        self.mock_location_service.test_connectivity.return_value = True
        self.mock_sunrise_sunset_service.test_api_connectivity.return_value = False
        
        result = self.handler.test_connectivity()
        
        assert result == {
            "location_service": True,
            "sunrise_sunset_service": False
        }

    def test_cleanup(self):
        """Test cleanup functionality."""
        # Set up enabled state with callbacks
        self.handler._is_enabled = True
        callback1 = Mock()
        callback2 = Mock()
        self.handler.add_status_callback(callback1)
        self.handler.add_error_callback(callback2)
        
        self.handler.cleanup()
        
        assert self.handler._is_enabled is False
        assert len(self.handler._status_callbacks) == 0
        assert len(self.handler._error_callbacks) == 0
        self.mock_sunrise_sunset_service.cleanup.assert_called_once()


class TestLocationModeHandlerGlobal:
    """Test cases for global location mode handler functions."""

    def test_get_location_mode_handler_singleton(self):
        """Test that get_location_mode_handler returns singleton instance."""
        handler1 = get_location_mode_handler()
        handler2 = get_location_mode_handler()

        assert handler1 is handler2
        assert isinstance(handler1, LocationModeHandler)

    def test_get_location_mode_handler_type(self):
        """Test that get_location_mode_handler returns correct type."""
        handler = get_location_mode_handler()
        assert isinstance(handler, LocationModeHandler)


@pytest.mark.integration
class TestLocationModeHandlerIntegration:
    """Integration tests for LocationModeHandler with real services."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use real services for integration testing
        from src.nightswitch.services.location import get_location_service
        from src.nightswitch.services.sunrise_sunset import get_sunrise_sunset_service
        
        self.handler = LocationModeHandler(
            location_service=get_location_service(),
            sunrise_sunset_service=get_sunrise_sunset_service()
        )

    @pytest.mark.skip(reason="Requires internet connection")
    def test_enable_with_real_services(self):
        """Test enabling location mode with real services (requires internet)."""
        theme_callback = Mock(return_value=True)
        self.handler.set_theme_callback(theme_callback)
        
        # Test with known coordinates (New York)
        result = self.handler.enable(40.7128, -74.0060)
        
        if result:  # Only assert if services are available
            assert self.handler.is_enabled() is True
            assert self.handler.get_current_location() is not None
            
            # Clean up
            self.handler.disable()

    @pytest.mark.skip(reason="Requires internet connection")
    def test_connectivity_with_real_services(self):
        """Test connectivity with real services (requires internet)."""
        result = self.handler.test_connectivity()
        
        assert isinstance(result, dict)
        assert "location_service" in result
        assert "sunrise_sunset_service" in result
        assert isinstance(result["location_service"], bool)
        assert isinstance(result["sunrise_sunset_service"], bool)