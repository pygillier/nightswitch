"""
Unit tests for SunriseSunsetService.

Tests the sunrise/sunset API integration, scheduling functionality,
and astronomical calculations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import requests
from requests.exceptions import RequestException, Timeout
import threading
import time

from src.nightswitch.services.sunrise_sunset import SunriseSunsetService, get_sunrise_sunset_service


class TestSunriseSunsetService:
    """Test cases for SunriseSunsetService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SunriseSunsetService(timeout=5)

    def test_init(self):
        """Test SunriseSunsetService initialization."""
        assert self.service.timeout == 5
        assert self.service.api_base_url == "https://api.sunrisesunset.io"
        assert self.service._cached_sun_times == {}
        assert self.service._is_scheduling is False

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates."""
        assert self.service._validate_coordinates(40.7128, -74.0060) is True  # NYC
        assert self.service._validate_coordinates(51.5074, -0.1278) is True   # London
        assert self.service._validate_coordinates(-33.8688, 151.2093) is True # Sydney
        assert self.service._validate_coordinates(90, 180) is True            # Extremes
        assert self.service._validate_coordinates(-90, -180) is True          # Extremes

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid coordinates."""
        assert self.service._validate_coordinates(91, 0) is False      # Lat too high
        assert self.service._validate_coordinates(-91, 0) is False     # Lat too low
        assert self.service._validate_coordinates(0, 181) is False     # Lon too high
        assert self.service._validate_coordinates(0, -181) is False    # Lon too low

    def test_validate_coordinates_invalid_types(self):
        """Test coordinate validation with invalid types."""
        assert self.service._validate_coordinates("40.7", "-74.0") is False
        assert self.service._validate_coordinates(None, None) is False

    @patch('requests.get')
    def test_get_sun_times_success(self, mock_get):
        """Test successful sun times retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": {
                "sunrise": "2024-01-15T12:30:00Z",
                "sunset": "2024-01-15T23:45:00Z"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        target_date = date(2024, 1, 15)
        result = self.service.get_sun_times(40.7128, -74.0060, target_date)

        assert result is not None
        sunrise, sunset = result
        assert isinstance(sunrise, datetime)
        assert isinstance(sunset, datetime)

        # Check that result was cached
        cache_key = f"40.7128,-74.006,{target_date}"
        assert cache_key in self.service._cached_sun_times

    @patch('requests.get')
    def test_get_sun_times_api_error_status(self, mock_get):
        """Test sun times retrieval with API error status."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ERROR",
            "message": "Invalid coordinates"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_sun_times(40.7128, -74.0060)

        assert result is None

    @patch('requests.get')
    def test_get_sun_times_missing_data(self, mock_get):
        """Test sun times retrieval with missing sunrise/sunset data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": {
                "sunrise": "2024-01-15T12:30:00Z"
                # Missing sunset
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_sun_times(40.7128, -74.0060)

        assert result is None

    @patch('requests.get')
    def test_get_sun_times_network_error(self, mock_get):
        """Test sun times retrieval with network error."""
        mock_get.side_effect = RequestException("Network error")

        result = self.service.get_sun_times(40.7128, -74.0060)

        assert result is None

    @patch('requests.get')
    def test_get_sun_times_timeout(self, mock_get):
        """Test sun times retrieval with timeout."""
        mock_get.side_effect = Timeout("Request timeout")

        result = self.service.get_sun_times(40.7128, -74.0060)

        assert result is None

    @patch('requests.get')
    def test_get_sun_times_cached(self, mock_get):
        """Test sun times retrieval using cached data."""
        target_date = date(2024, 1, 15)
        cache_key = f"40.7128,-74.006,{target_date}"
        
        # Set up cache
        cached_sunrise = datetime(2024, 1, 15, 7, 30)
        cached_sunset = datetime(2024, 1, 15, 18, 45)
        self.service._cached_sun_times[cache_key] = {
            "date": target_date,
            "sunrise": cached_sunrise,
            "sunset": cached_sunset,
            "cached_at": datetime.now()
        }

        result = self.service.get_sun_times(40.7128, -74.006, target_date)

        # Should not make API call
        mock_get.assert_not_called()
        
        assert result is not None
        sunrise, sunset = result
        assert sunrise == cached_sunrise
        assert sunset == cached_sunset

    @patch('requests.get')
    def test_get_sun_times_default_date(self, mock_get):
        """Test sun times retrieval with default date (today)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": {
                "sunrise": "2024-01-15T12:30:00Z",
                "sunset": "2024-01-15T23:45:00Z"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('src.nightswitch.services.sunrise_sunset.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            result = self.service.get_sun_times(40.7128, -74.0060)

        assert result is not None
        # Verify API was called with today's date
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['date'] == '2024-01-15'

    def test_schedule_sun_events_invalid_coordinates(self):
        """Test scheduling with invalid coordinates."""
        callback = Mock()
        
        result = self.service.schedule_sun_events(91, 0, callback)
        
        assert result is False
        assert self.service._is_scheduling is False

    def test_schedule_sun_events_success(self):
        """Test successful sun events scheduling."""
        callback = Mock()
        
        result = self.service.schedule_sun_events(40.7128, -74.0060, callback)
        
        assert result is True
        assert self.service._is_scheduling is True
        assert self.service._current_location == (40.7128, -74.0060)
        assert self.service._current_callback == callback
        assert self.service._scheduler_thread is not None

        # Clean up
        self.service.stop_sun_events()

    def test_stop_sun_events(self):
        """Test stopping sun events scheduling."""
        callback = Mock()
        self.service.schedule_sun_events(40.7128, -74.0060, callback)
        
        self.service.stop_sun_events()
        
        assert self.service._is_scheduling is False
        assert self.service._scheduler_thread is None

    def test_get_next_sun_event_sunrise_today(self):
        """Test getting next sun event when sunrise is today."""
        # Set up cached sun times directly
        target_date = date(2024, 1, 15)
        current_time = datetime(2024, 1, 15, 6, 0)  # 6 AM
        sunrise_time = datetime(2024, 1, 15, 7, 30)  # 7:30 AM (future)
        sunset_time = datetime(2024, 1, 15, 18, 45)  # 6:45 PM (future)
        
        cache_key = f"40.7128,-74.006,{target_date}"
        self.service._cached_sun_times[cache_key] = {
            "date": target_date,
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "cached_at": datetime.now()
        }

        with patch('src.nightswitch.services.sunrise_sunset.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = self.service.get_next_sun_event(40.7128, -74.006)

        assert result is not None
        event_time, event_type = result
        assert event_type == "sunrise"
        assert event_time == sunrise_time

    def test_get_next_sun_event_sunset_today(self):
        """Test getting next sun event when sunset is today."""
        # Set up cached sun times directly
        target_date = date(2024, 1, 15)
        current_time = datetime(2024, 1, 15, 12, 0)  # 12 PM
        sunrise_time = datetime(2024, 1, 15, 7, 30)   # 7:30 AM (past)
        sunset_time = datetime(2024, 1, 15, 18, 45)   # 6:45 PM (future)
        
        cache_key = f"40.7128,-74.006,{target_date}"
        self.service._cached_sun_times[cache_key] = {
            "date": target_date,
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "cached_at": datetime.now()
        }

        with patch('src.nightswitch.services.sunrise_sunset.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = self.service.get_next_sun_event(40.7128, -74.006)

        assert result is not None
        event_time, event_type = result
        assert event_type == "sunset"
        assert event_time == sunset_time

    @patch('requests.get')
    def test_get_current_sun_period_day(self, mock_get):
        """Test getting current sun period during day."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": {
                "sunrise": "2024-01-15T12:30:00Z",  # 7:30 AM local time
                "sunset": "2024-01-15T23:45:00Z"    # 6:45 PM local time
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock current time to be during day (12 PM)
        with patch('src.nightswitch.services.sunrise_sunset.datetime') as mock_datetime:
            current_time = datetime(2024, 1, 15, 12, 0)
            sunrise_time = datetime(2024, 1, 15, 7, 30)
            sunset_time = datetime(2024, 1, 15, 18, 45)
            
            mock_datetime.now.return_value = current_time
            mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))
            
            # Mock astimezone method on datetime instances
            def mock_astimezone():
                return sunrise_time if "12:30" in str(mock_get.call_args) else sunset_time
            
            # Create mock datetime instances that return local times
            mock_sunrise_dt = Mock()
            mock_sunrise_dt.astimezone.return_value = sunrise_time
            mock_sunset_dt = Mock()
            mock_sunset_dt.astimezone.return_value = sunset_time
            
            mock_datetime.fromisoformat.side_effect = [mock_sunrise_dt, mock_sunset_dt]
            
            result = self.service.get_current_sun_period(40.7128, -74.006)

        assert result == "day"

    @patch('requests.get')
    def test_get_current_sun_period_night(self, mock_get):
        """Test getting current sun period during night."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": {
                "sunrise": "2024-01-15T12:30:00Z",  # 7:30 AM local time
                "sunset": "2024-01-15T23:45:00Z"    # 6:45 PM local time
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock current time to be during night (10 PM)
        with patch('src.nightswitch.services.sunrise_sunset.datetime') as mock_datetime:
            current_time = datetime(2024, 1, 15, 22, 0)
            sunrise_time = datetime(2024, 1, 15, 7, 30)
            sunset_time = datetime(2024, 1, 15, 18, 45)
            
            mock_datetime.now.return_value = current_time
            mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))
            
            # Create mock datetime instances that return local times
            mock_sunrise_dt = Mock()
            mock_sunrise_dt.astimezone.return_value = sunrise_time
            mock_sunset_dt = Mock()
            mock_sunset_dt.astimezone.return_value = sunset_time
            
            mock_datetime.fromisoformat.side_effect = [mock_sunrise_dt, mock_sunset_dt]
            
            result = self.service.get_current_sun_period(40.7128, -74.006)

        assert result == "night"

    def test_is_time_match_exact(self):
        """Test time matching with exact match."""
        current_time = datetime(2024, 1, 15, 12, 30, 0)
        target_time = datetime(2024, 1, 15, 12, 30, 0)
        
        result = self.service._is_time_match(current_time, target_time)
        
        assert result is True

    def test_is_time_match_within_window(self):
        """Test time matching within 1-minute window."""
        current_time = datetime(2024, 1, 15, 12, 30, 30)  # 30 seconds after
        target_time = datetime(2024, 1, 15, 12, 30, 0)
        
        result = self.service._is_time_match(current_time, target_time)
        
        assert result is True

    def test_is_time_match_outside_window(self):
        """Test time matching outside 1-minute window."""
        current_time = datetime(2024, 1, 15, 12, 31, 30)  # 1.5 minutes after
        target_time = datetime(2024, 1, 15, 12, 30, 0)
        
        result = self.service._is_time_match(current_time, target_time)
        
        assert result is False

    def test_clear_cache(self):
        """Test clearing sun times cache."""
        # Set up cache
        self.service._cached_sun_times["test"] = {"data": "value"}
        
        self.service.clear_cache()
        
        assert len(self.service._cached_sun_times) == 0

    def test_get_service_status_not_scheduling(self):
        """Test getting service status when not scheduling."""
        status = self.service.get_service_status()
        
        assert status["is_scheduling"] is False
        assert status["api_url"] == "https://api.sunrisesunset.io"
        assert status["timeout"] == 5
        assert status["has_callback"] is False
        assert status["current_location"] is None
        assert status["thread_alive"] is False
        assert status["cached_entries"] == 0

    def test_get_service_status_scheduling(self):
        """Test getting service status when scheduling."""
        callback = Mock()
        self.service.schedule_sun_events(40.7128, -74.0060, callback)
        
        status = self.service.get_service_status()
        
        assert status["is_scheduling"] is True
        assert status["has_callback"] is True
        assert status["current_location"] == (40.7128, -74.0060)
        assert status["thread_alive"] is True
        
        # Clean up
        self.service.stop_sun_events()

    @patch('requests.get')
    def test_test_api_connectivity_success(self, mock_get):
        """Test API connectivity test with successful connection."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "OK"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.test_api_connectivity()
        
        assert result is True

    @patch('requests.get')
    def test_test_api_connectivity_api_error(self, mock_get):
        """Test API connectivity test with API error."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ERROR"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.test_api_connectivity()
        
        assert result is False

    @patch('requests.get')
    def test_test_api_connectivity_network_error(self, mock_get):
        """Test API connectivity test with network error."""
        mock_get.side_effect = RequestException("Network error")
        
        result = self.service.test_api_connectivity()
        
        assert result is False

    def test_cleanup(self):
        """Test service cleanup."""
        callback = Mock()
        self.service.schedule_sun_events(40.7128, -74.0060, callback)
        self.service._cached_sun_times["test"] = {"data": "value"}
        
        self.service.cleanup()
        
        assert self.service._is_scheduling is False
        assert len(self.service._cached_sun_times) == 0


class TestSunriseSunsetServiceGlobal:
    """Test cases for global sunrise/sunset service functions."""

    def test_get_sunrise_sunset_service_singleton(self):
        """Test that get_sunrise_sunset_service returns singleton instance."""
        service1 = get_sunrise_sunset_service()
        service2 = get_sunrise_sunset_service()

        assert service1 is service2
        assert isinstance(service1, SunriseSunsetService)

    def test_get_sunrise_sunset_service_type(self):
        """Test that get_sunrise_sunset_service returns correct type."""
        service = get_sunrise_sunset_service()
        assert isinstance(service, SunriseSunsetService)


@pytest.mark.integration
class TestSunriseSunsetServiceIntegration:
    """Integration tests for SunriseSunsetService with real API calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SunriseSunsetService(timeout=10)

    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_api_call(self):
        """Test real API call (requires internet connection)."""
        # Test with New York coordinates
        result = self.service.get_sun_times(40.7128, -74.0060)

        if result:  # Only assert if we got a result
            sunrise, sunset = result
            assert isinstance(sunrise, datetime)
            assert isinstance(sunset, datetime)
            assert sunrise < sunset  # Sunrise should be before sunset

    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_connectivity_test(self):
        """Test real connectivity test (requires internet connection)."""
        result = self.service.test_api_connectivity()
        # This might be True or False depending on network conditions
        assert isinstance(result, bool)