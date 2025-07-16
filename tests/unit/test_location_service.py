"""
Unit tests for LocationService.

Tests the location detection functionality including API integration,
coordinate validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout

from src.nightswitch.services.location import LocationService, get_location_service


class TestLocationService:
    """Test cases for LocationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = LocationService(timeout=5)

    def test_init(self):
        """Test LocationService initialization."""
        assert self.service.timeout == 5
        assert len(self.service._apis) == 3
        assert self.service._cached_location is None

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates."""
        assert self.service.validate_coordinates(40.7128, -74.0060) is True  # NYC
        assert self.service.validate_coordinates(51.5074, -0.1278) is True   # London
        assert self.service.validate_coordinates(-33.8688, 151.2093) is True # Sydney
        assert self.service.validate_coordinates(90, 180) is True            # Extremes
        assert self.service.validate_coordinates(-90, -180) is True          # Extremes

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid coordinates."""
        assert self.service.validate_coordinates(91, 0) is False      # Lat too high
        assert self.service.validate_coordinates(-91, 0) is False     # Lat too low
        assert self.service.validate_coordinates(0, 181) is False     # Lon too high
        assert self.service.validate_coordinates(0, -181) is False    # Lon too low
        assert self.service.validate_coordinates(0, 0) is False       # Origin (invalid)

    def test_validate_coordinates_invalid_types(self):
        """Test coordinate validation with invalid types."""
        assert self.service.validate_coordinates("40.7", "-74.0") is False
        assert self.service.validate_coordinates(None, None) is False
        assert self.service.validate_coordinates(40.7, None) is False

    @patch('requests.get')
    def test_get_current_location_success_ipapi(self, mock_get):
        """Test successful location detection using ipapi.co."""
        # Mock successful response from ipapi.co
        mock_response = Mock()
        mock_response.json.return_value = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country_name": "United States"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_current_location()

        assert result is not None
        lat, lon, description = result
        assert lat == 40.7128
        assert lon == -74.0060
        assert "New York" in description
        assert "United States" in description

        # Check that result was cached
        assert self.service._cached_location is not None
        assert self.service._cached_location["latitude"] == 40.7128

    @patch('requests.get')
    def test_get_current_location_success_ipapi_com(self, mock_get):
        """Test successful location detection using ip-api.com."""
        # Mock failure for first API, success for second
        def side_effect(url, **kwargs):
            if "ipapi.co" in url:
                raise RequestException("API unavailable")
            else:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "lat": 51.5074,
                    "lon": -0.1278,
                    "city": "London",
                    "country": "United Kingdom"
                }
                mock_response.raise_for_status.return_value = None
                return mock_response

        mock_get.side_effect = side_effect

        result = self.service.get_current_location()

        assert result is not None
        lat, lon, description = result
        assert lat == 51.5074
        assert lon == -0.1278
        assert "London" in description
        assert "United Kingdom" in description

    @patch('requests.get')
    def test_get_current_location_success_ipinfo(self, mock_get):
        """Test successful location detection using ipinfo.io."""
        # Mock failure for first two APIs, success for third
        def side_effect(url, **kwargs):
            if "ipapi.co" in url or "ip-api.com" in url:
                raise RequestException("API unavailable")
            else:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "loc": "-33.8688,151.2093",
                    "city": "Sydney",
                    "country": "Australia"
                }
                mock_response.raise_for_status.return_value = None
                return mock_response

        mock_get.side_effect = side_effect

        result = self.service.get_current_location()

        assert result is not None
        lat, lon, description = result
        assert lat == -33.8688
        assert lon == 151.2093
        assert "Sydney" in description
        assert "Australia" in description

    @patch('requests.get')
    def test_get_current_location_all_apis_fail(self, mock_get):
        """Test location detection when all APIs fail."""
        mock_get.side_effect = RequestException("Network error")

        result = self.service.get_current_location()

        assert result is None
        assert self.service._cached_location is None

    @patch('requests.get')
    def test_get_current_location_invalid_coordinates(self, mock_get):
        """Test location detection with invalid coordinates from API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "latitude": 0,  # Invalid coordinates (0,0)
            "longitude": 0,
            "city": "Unknown",
            "country_name": "Unknown"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_current_location()

        assert result is None

    @patch('requests.get')
    def test_get_current_location_malformed_response(self, mock_get):
        """Test location detection with malformed API response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "invalid": "response"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_current_location()

        assert result is None

    @patch('requests.get')
    def test_get_current_location_json_decode_error(self, mock_get):
        """Test location detection with JSON decode error."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.service.get_current_location()

        assert result is None

    @patch('requests.get')
    def test_get_current_location_timeout(self, mock_get):
        """Test location detection with timeout."""
        mock_get.side_effect = Timeout("Request timeout")

        result = self.service.get_current_location()

        assert result is None

    def test_get_cached_location_no_cache(self):
        """Test getting cached location when no cache exists."""
        result = self.service.get_cached_location()
        assert result is None

    def test_get_cached_location_with_cache(self):
        """Test getting cached location when cache exists."""
        # Set up cache
        self.service._cached_location = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "New York, United States"
        }

        result = self.service.get_cached_location()

        assert result is not None
        lat, lon, description = result
        assert lat == 40.7128
        assert lon == -74.0060
        assert description == "New York, United States"

    def test_clear_cache(self):
        """Test clearing location cache."""
        # Set up cache
        self.service._cached_location = {"test": "data"}

        self.service.clear_cache()

        assert self.service._cached_location is None

    @patch('requests.get')
    def test_test_connectivity_success(self, mock_get):
        """Test connectivity test with successful connection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.service.test_connectivity()

        assert result is True

    @patch('requests.get')
    def test_test_connectivity_failure(self, mock_get):
        """Test connectivity test with failed connections."""
        mock_get.side_effect = RequestException("Network error")

        result = self.service.test_connectivity()

        assert result is False

    def test_get_location_info_no_cache(self):
        """Test getting location service info without cache."""
        with patch.object(self.service, 'test_connectivity', return_value=True):
            info = self.service.get_location_info()

        assert info["available_apis"] == ["ipapi.co", "ip-api.com", "ipinfo.io"]
        assert info["timeout"] == 5
        assert info["has_cached_location"] is False
        assert info["connectivity"] is True

    def test_get_location_info_with_cache(self):
        """Test getting location service info with cache."""
        # Set up cache
        self.service._cached_location = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "New York, United States",
            "source": "ipapi.co"
        }

        with patch.object(self.service, 'test_connectivity', return_value=True):
            info = self.service.get_location_info()

        assert info["has_cached_location"] is True
        assert info["cached_location"]["latitude"] == 40.7128
        assert info["cached_location"]["longitude"] == -74.0060
        assert info["cached_location"]["description"] == "New York, United States"
        assert info["cached_location"]["source"] == "ipapi.co"


class TestLocationServiceGlobal:
    """Test cases for global location service functions."""

    def test_get_location_service_singleton(self):
        """Test that get_location_service returns singleton instance."""
        service1 = get_location_service()
        service2 = get_location_service()

        assert service1 is service2
        assert isinstance(service1, LocationService)

    def test_get_location_service_type(self):
        """Test that get_location_service returns correct type."""
        service = get_location_service()
        assert isinstance(service, LocationService)


@pytest.mark.integration
class TestLocationServiceIntegration:
    """Integration tests for LocationService with real API calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = LocationService(timeout=10)

    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_api_call(self):
        """Test real API call (requires internet connection)."""
        result = self.service.get_current_location()

        if result:  # Only assert if we got a result
            lat, lon, description = result
            assert isinstance(lat, float)
            assert isinstance(lon, float)
            assert isinstance(description, str)
            assert self.service.validate_coordinates(lat, lon)

    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_connectivity_test(self):
        """Test real connectivity test (requires internet connection)."""
        result = self.service.test_connectivity()
        # This might be True or False depending on network conditions
        assert isinstance(result, bool)