"""
Unit tests for configuration management.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from nightswitch.core.config import AppConfig, ConfigManager, XDGPaths, get_config


class TestXDGPaths:
    """Test XDG Base Directory Specification compliance."""

    def test_config_home_default(self):
        """Test default config home path."""
        with patch.dict(os.environ, {}, clear=True):
            path = XDGPaths.config_home()
            expected = Path.home() / ".config" / "nightswitch"
            assert path == expected

    def test_config_home_custom(self):
        """Test custom XDG_CONFIG_HOME."""
        custom_path = "/custom/config"
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": custom_path}):
            path = XDGPaths.config_home()
            expected = Path(custom_path) / "nightswitch"
            assert path == expected

    def test_data_home_default(self):
        """Test default data home path."""
        with patch.dict(os.environ, {}, clear=True):
            path = XDGPaths.data_home()
            expected = Path.home() / ".local" / "share" / "nightswitch"
            assert path == expected

    def test_data_home_custom(self):
        """Test custom XDG_DATA_HOME."""
        custom_path = "/custom/data"
        with patch.dict(os.environ, {"XDG_DATA_HOME": custom_path}):
            path = XDGPaths.data_home()
            expected = Path(custom_path) / "nightswitch"
            assert path == expected

    def test_cache_home_default(self):
        """Test default cache home path."""
        with patch.dict(os.environ, {}, clear=True):
            path = XDGPaths.cache_home()
            expected = Path.home() / ".cache" / "nightswitch"
            assert path == expected

    def test_cache_home_custom(self):
        """Test custom XDG_CACHE_HOME."""
        custom_path = "/custom/cache"
        with patch.dict(os.environ, {"XDG_CACHE_HOME": custom_path}):
            path = XDGPaths.cache_home()
            expected = Path(custom_path) / "nightswitch"
            assert path == expected

    def test_state_home_default(self):
        """Test default state home path."""
        with patch.dict(os.environ, {}, clear=True):
            path = XDGPaths.state_home()
            expected = Path.home() / ".local" / "state" / "nightswitch"
            assert path == expected

    def test_state_home_custom(self):
        """Test custom XDG_STATE_HOME."""
        custom_path = "/custom/state"
        with patch.dict(os.environ, {"XDG_STATE_HOME": custom_path}):
            path = XDGPaths.state_home()
            expected = Path(custom_path) / "nightswitch"
            assert path == expected


class TestConfigManager:
    """Test configuration manager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a ConfigManager instance with temporary directory."""
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        return ConfigManager()

    def test_default_config_creation(self, config_manager):
        """Test that default configuration is created."""
        assert config_manager.get("mode") == "manual"
        assert config_manager.get("current_theme") == "light"
        assert config_manager.get("schedule.enabled") is False
        assert config_manager.get("location.auto_detect") is True

    def test_config_file_creation(self, config_manager, temp_config_dir):
        """Test that configuration file is created."""
        config_file = temp_config_dir / "config.json"
        assert config_file.exists()

        with open(config_file, "r") as f:
            data = json.load(f)

        assert data["mode"] == "manual"
        assert data["current_theme"] == "light"

    def test_get_simple_key(self, config_manager):
        """Test getting a simple configuration key."""
        assert config_manager.get("mode") == "manual"
        assert config_manager.get("nonexistent") is None
        assert config_manager.get("nonexistent", "default") == "default"

    def test_get_nested_key(self, config_manager):
        """Test getting nested configuration keys with dot notation."""
        assert config_manager.get("schedule.enabled") is False
        assert config_manager.get("schedule.light_time") == "07:00"
        assert config_manager.get("ui.show_notifications") is True

    def test_set_simple_key(self, config_manager):
        """Test setting a simple configuration key."""
        config_manager.set("mode", "schedule")
        assert config_manager.get("mode") == "schedule"

    def test_set_nested_key(self, config_manager):
        """Test setting nested configuration keys with dot notation."""
        config_manager.set("schedule.enabled", True)
        assert config_manager.get("schedule.enabled") is True

        config_manager.set("schedule.light_time", "08:00")
        assert config_manager.get("schedule.light_time") == "08:00"

    def test_set_new_nested_key(self, config_manager):
        """Test setting a new nested key that doesn't exist."""
        config_manager.set("new.nested.key", "value")
        assert config_manager.get("new.nested.key") == "value"

    def test_get_all_config(self, config_manager):
        """Test getting the entire configuration."""
        config = config_manager.get_all()
        assert isinstance(config, dict)
        assert "mode" in config
        assert "schedule" in config
        assert isinstance(config["schedule"], dict)

    def test_reset_to_defaults(self, temp_config_dir):
        """Test resetting configuration to defaults."""
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        config_manager = ConfigManager()

                        # Verify initial defaults
                        assert config_manager.get("mode") == "manual"
                        assert config_manager.get("schedule.enabled") is False

                        # Modify some values
                        config_manager.set("mode", "location")
                        config_manager.set("schedule.enabled", True)

                        # Verify changes were made
                        assert config_manager.get("mode") == "location"
                        assert config_manager.get("schedule.enabled") is True

                        # Reset to defaults
                        config_manager.reset_to_defaults()

                        # Debug: Check what's in the config after reset
                        print(f"After reset - mode: {config_manager.get('mode')}")
                        print(
                            f"After reset - schedule.enabled: {config_manager.get('schedule.enabled')}"
                        )
                        print(f"Full config: {config_manager.get_all()}")

                        # Verify reset worked
                        assert config_manager.get("mode") == "manual"
                        assert config_manager.get("schedule.enabled") is False

    def test_config_persistence(self, temp_config_dir):
        """Test that configuration persists across instances."""
        # Create first instance and modify config
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        config1 = ConfigManager()
                        config1.set("mode", "location")
                        config1.set("schedule.enabled", True)

        # Create second instance and verify persistence
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        config2 = ConfigManager()
                        assert config2.get("mode") == "location"
                        assert config2.get("schedule.enabled") is True

    def test_config_merge_with_existing(self, temp_config_dir):
        """Test that existing config is merged with defaults."""
        # Create a partial config file
        config_file = temp_config_dir / "config.json"
        temp_config_dir.mkdir(exist_ok=True)

        partial_config = {
            "mode": "schedule",
            "schedule": {"enabled": True, "light_time": "08:00"},  # Override default
        }

        with open(config_file, "w") as f:
            json.dump(partial_config, f)

        # Load config and verify merge
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        config = ConfigManager()

        # Verify loaded values
        assert config.get("mode") == "schedule"
        assert config.get("schedule.enabled") is True
        assert (
            config.get("schedule.light_time") == "08:00"
        )  # Should be overridden value

        # Verify default values are still present for non-overridden keys
        assert config.get("current_theme") == "light"
        assert config.get("schedule.dark_time") == "19:00"  # Should still be default
        assert config.get("ui.show_notifications") is True

    def test_directory_properties(self, temp_config_dir):
        """Test directory property accessors."""
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        config_manager = ConfigManager()
                        assert config_manager.config_dir == temp_config_dir
                        assert config_manager.data_dir == temp_config_dir / "data"
                        assert config_manager.cache_dir == temp_config_dir / "cache"
                        assert config_manager.state_dir == temp_config_dir / "state"


class TestAppConfig:
    """Test AppConfig dataclass functionality."""

    def test_default_values(self):
        """Test that AppConfig has correct default values."""
        config = AppConfig()
        assert config.current_mode == "manual"
        assert config.manual_theme == "light"
        assert config.schedule_enabled is False
        assert config.dark_time == "19:00"
        assert config.light_time == "07:00"
        assert config.location_enabled is False
        assert config.latitude is None
        assert config.longitude is None
        assert config.auto_location is True
        assert config.start_minimized is True
        assert config.show_notifications is True
        assert config.autostart is False
        assert config.active_plugin == "auto"
        assert config.plugin_settings == {}

    def test_validation_valid_config(self):
        """Test validation with valid configuration."""
        config = AppConfig()
        assert config.validate() is True

        # Test with custom valid values
        config = AppConfig(
            current_mode="schedule",
            manual_theme="dark",
            dark_time="20:30",
            light_time="06:45",
            latitude=40.7128,
            longitude=-74.0060,
            active_plugin="budgie",
        )
        assert config.validate() is True

    def test_validation_invalid_mode(self):
        """Test validation with invalid mode."""
        config = AppConfig(current_mode="invalid")
        assert config.validate() is False

    def test_validation_invalid_theme(self):
        """Test validation with invalid theme."""
        config = AppConfig(manual_theme="invalid")
        assert config.validate() is False

    def test_validation_invalid_time_format(self):
        """Test validation with invalid time format."""
        config = AppConfig(dark_time="25:00")  # Invalid hour
        assert config.validate() is False

        config = AppConfig(light_time="12:60")  # Invalid minute
        assert config.validate() is False

        config = AppConfig(dark_time="invalid")  # Invalid format
        assert config.validate() is False

    def test_validation_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        config = AppConfig(latitude=91.0)  # Invalid latitude
        assert config.validate() is False

        config = AppConfig(latitude=-91.0)  # Invalid latitude
        assert config.validate() is False

        config = AppConfig(longitude=181.0)  # Invalid longitude
        assert config.validate() is False

        config = AppConfig(longitude=-181.0)  # Invalid longitude
        assert config.validate() is False

    def test_validation_invalid_plugin(self):
        """Test validation with invalid plugin name."""
        config = AppConfig(active_plugin="invalid")
        assert config.validate() is False

    def test_from_dict(self):
        """Test creating AppConfig from dictionary."""
        data = {
            "mode": "schedule",
            "current_theme": "dark",
            "schedule": {"enabled": True, "dark_time": "20:00", "light_time": "08:00"},
            "location": {
                "enabled": True,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "auto_detect": False,
            },
            "ui": {
                "minimize_to_tray": False,
                "show_notifications": False,
                "autostart": True,
            },
            "plugins": {
                "active_plugin": "budgie",
                "plugin_settings": {"test": "value"},
            },
        }

        config = AppConfig.from_dict(data)
        assert config.current_mode == "schedule"
        assert config.manual_theme == "dark"
        assert config.schedule_enabled is True
        assert config.dark_time == "20:00"
        assert config.light_time == "08:00"
        assert config.location_enabled is True
        assert config.latitude == 40.7128
        assert config.longitude == -74.0060
        assert config.auto_location is False
        assert config.start_minimized is False
        assert config.show_notifications is False
        assert config.autostart is True
        assert config.active_plugin == "budgie"
        assert config.plugin_settings == {"test": "value"}

    def test_from_dict_partial(self):
        """Test creating AppConfig from partial dictionary."""
        data = {"mode": "location", "schedule": {"enabled": True}}

        config = AppConfig.from_dict(data)
        assert config.current_mode == "location"
        assert config.schedule_enabled is True
        # Other values should be defaults
        assert config.manual_theme == "light"
        assert config.dark_time == "19:00"
        assert config.light_time == "07:00"

    def test_to_dict(self):
        """Test converting AppConfig to dictionary."""
        config = AppConfig(
            current_mode="schedule",
            manual_theme="dark",
            schedule_enabled=True,
            dark_time="20:00",
            light_time="08:00",
            location_enabled=True,
            latitude=40.7128,
            longitude=-74.0060,
            auto_location=False,
            start_minimized=False,
            show_notifications=False,
            autostart=True,
            active_plugin="budgie",
            plugin_settings={"test": "value"},
        )

        data = config.to_dict()
        
        # Verify key parts of the dictionary
        assert data["mode"] == "schedule"
        assert data["current_theme"] == "dark"
        assert data["schedule"]["enabled"] is True
        assert data["schedule"]["dark_time"] == "20:00"
        assert data["schedule"]["light_time"] == "08:00"
        assert data["location"]["enabled"] is True
        assert data["location"]["latitude"] == 40.7128
        assert data["location"]["longitude"] == -74.0060
        assert data["location"]["auto_detect"] is False
        assert data["ui"]["minimize_to_tray"] is False
        assert data["ui"]["show_notifications"] is False
        assert data["ui"]["autostart"] is True
        assert data["plugins"]["active_plugin"] == "budgie"
        assert data["plugins"]["plugin_settings"] == {"test": "value"}


class TestConfigManagerEnhanced:
    """Test enhanced ConfigManager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a ConfigManager instance with temporary directory."""
        with patch.object(XDGPaths, "config_home", return_value=temp_config_dir):
            with patch.object(
                XDGPaths, "data_home", return_value=temp_config_dir / "data"
            ):
                with patch.object(
                    XDGPaths, "cache_home", return_value=temp_config_dir / "cache"
                ):
                    with patch.object(
                        XDGPaths, "state_home", return_value=temp_config_dir / "state"
                    ):
                        return ConfigManager()

    def test_get_app_config(self, config_manager):
        """Test getting configuration as AppConfig instance."""
        app_config = config_manager.get_app_config()
        assert isinstance(app_config, AppConfig)
        assert app_config.current_mode == "manual"
        assert app_config.manual_theme == "light"
        assert app_config.validate() is True

    def test_set_app_config(self, config_manager):
        """Test setting configuration from AppConfig instance."""
        app_config = AppConfig(
            current_mode="schedule",
            manual_theme="dark",
            schedule_enabled=True,
            dark_time="20:00",
        )

        config_manager.set_app_config(app_config)

        # Verify changes were saved
        assert config_manager.get("mode") == "schedule"
        assert config_manager.get("current_theme") == "dark"
        assert config_manager.get("schedule.enabled") is True
        assert config_manager.get("schedule.dark_time") == "20:00"

    def test_set_app_config_invalid(self, config_manager):
        """Test setting invalid AppConfig raises ValueError."""
        app_config = AppConfig(current_mode="invalid")

        with pytest.raises(ValueError, match="Invalid configuration values"):
            config_manager.set_app_config(app_config)

    def test_validate_config(self, config_manager):
        """Test configuration validation."""
        # Default config should be valid
        assert config_manager.validate_config() is True

        # Set invalid value directly
        config_manager.set("mode", "invalid")
        assert config_manager.validate_config() is False

    def test_backup_config(self, config_manager, temp_config_dir):
        """Test configuration backup."""
        # Modify config
        config_manager.set("mode", "schedule")
        config_manager.set("schedule.enabled", True)

        # Create backup
        backup_path = config_manager.backup_config()

        assert backup_path.exists()
        assert backup_path.parent == temp_config_dir
        assert "config_backup_" in backup_path.name

        # Verify backup content
        with open(backup_path, "r") as f:
            backup_data = json.load(f)

        assert backup_data["mode"] == "schedule"
        assert backup_data["schedule"]["enabled"] is True

    def test_backup_config_custom_path(self, config_manager, temp_config_dir):
        """Test configuration backup with custom path."""
        custom_backup = temp_config_dir / "custom_backup.json"

        backup_path = config_manager.backup_config(custom_backup)

        assert backup_path == custom_backup
        assert custom_backup.exists()

    def test_restore_config(self, config_manager, temp_config_dir):
        """Test configuration restoration from backup."""
        # Create backup data
        backup_data = {
            "mode": "location",
            "current_theme": "dark",
            "location": {"enabled": True, "latitude": 40.7128, "longitude": -74.0060},
        }

        backup_path = temp_config_dir / "test_backup.json"
        with open(backup_path, "w") as f:
            json.dump(backup_data, f)

        # Restore from backup
        config_manager.restore_config(backup_path)

        # Verify restoration
        assert config_manager.get("mode") == "location"
        assert config_manager.get("current_theme") == "dark"
        assert config_manager.get("location.enabled") is True
        assert config_manager.get("location.latitude") == 40.7128

        # Verify defaults are still present
        assert config_manager.get("schedule.dark_time") == "19:00"

    def test_restore_config_nonexistent(self, config_manager, temp_config_dir):
        """Test restoring from nonexistent backup file."""
        nonexistent_path = temp_config_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            config_manager.restore_config(nonexistent_path)

    def test_restore_config_invalid(self, config_manager, temp_config_dir):
        """Test restoring from invalid backup file."""
        # Create invalid backup
        invalid_backup = temp_config_dir / "invalid_backup.json"
        with open(invalid_backup, "w") as f:
            f.write("invalid json")

        with pytest.raises(ValueError, match="Failed to restore from backup"):
            config_manager.restore_config(invalid_backup)

    def test_restore_config_invalid_values(self, config_manager, temp_config_dir):
        """Test restoring backup with invalid configuration values."""
        # Create backup with invalid data
        invalid_data = {"mode": "invalid_mode", "current_theme": "light"}

        invalid_backup = temp_config_dir / "invalid_values_backup.json"
        with open(invalid_backup, "w") as f:
            json.dump(invalid_data, f)

        with pytest.raises(ValueError, match="Backup contains invalid configuration"):
            config_manager.restore_config(invalid_backup)


def test_get_config_singleton():
    """Test that get_config returns a singleton instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
