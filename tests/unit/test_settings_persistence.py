"""
Unit tests for settings persistence and state restoration.

Tests the automatic settings saving, state tracking, and configuration migration
functionality of the ConfigManager class.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from nightswitch.core.config import AppConfig, ConfigManager, XDGPaths, get_config


class TestSettingsPersistence:
    """Test settings persistence functionality."""

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

    def test_auto_save_enabled_by_default(self, config_manager):
        """Test that auto-save is enabled by default."""
        assert config_manager.is_auto_save_enabled() is True

    def test_auto_save_disable_enable(self, config_manager):
        """Test disabling and enabling auto-save."""
        config_manager.disable_auto_save()
        assert config_manager.is_auto_save_enabled() is False

        config_manager.enable_auto_save()
        assert config_manager.is_auto_save_enabled() is True

    def test_auto_save_on_set(self, config_manager, temp_config_dir):
        """Test that changes are automatically saved when auto-save is enabled."""
        # Make a change with auto-save enabled
        config_manager.set("mode", "schedule")
        
        # Check that the file was updated
        config_file = temp_config_dir / "config.json"
        with open(config_file, "r") as f:
            data = json.load(f)
        
        assert data["mode"] == "schedule"
        
        # Disable auto-save and make another change
        config_manager.disable_auto_save()
        config_manager.set("mode", "location")
        
        # Check that the file was not updated
        with open(config_file, "r") as f:
            data = json.load(f)
        
        assert data["mode"] == "schedule"  # Still has old value
        
        # Manually save and check
        config_manager._save_config()
        with open(config_file, "r") as f:
            data = json.load(f)
        
        assert data["mode"] == "location"  # Now updated

    def test_change_listeners(self, config_manager):
        """Test adding and removing change listeners."""
        # Create mock listeners
        listener1 = MagicMock()
        listener2 = MagicMock()
        
        # Add listeners
        config_manager.add_change_listener(listener1)
        config_manager.add_change_listener(listener2)
        
        # Make a change
        config_manager.set("mode", "schedule")
        
        # Check that both listeners were called
        listener1.assert_called_once_with("mode", "schedule")
        listener2.assert_called_once_with("mode", "schedule")
        
        # Reset mocks
        listener1.reset_mock()
        listener2.reset_mock()
        
        # Remove one listener
        config_manager.remove_change_listener(listener1)
        
        # Make another change
        config_manager.set("current_theme", "dark")
        
        # Check that only the remaining listener was called
        listener1.assert_not_called()
        listener2.assert_called_once_with("current_theme", "dark")

    def test_state_tracking(self, config_manager):
        """Test state tracking functionality."""
        # Update state values
        config_manager.update_state(test_key="test_value", another_key=123)
        
        # Check that values were saved
        assert config_manager.get_state("test_key") == "test_value"
        assert config_manager.get_state("another_key") == 123
        assert config_manager.get_state("nonexistent") is None
        assert config_manager.get_state("nonexistent", "default") == "default"

    def test_last_run_tracking(self, config_manager):
        """Test last run timestamp tracking."""
        # Update last run
        config_manager.update_last_run()
        
        # Get last run timestamp
        last_run = config_manager.get_last_run()
        
        # Check that it's a recent datetime
        assert isinstance(last_run, datetime)
        assert datetime.now() - last_run < timedelta(seconds=5)
        
        # Check startup count
        assert config_manager.get_state("startup_count") == 1
        
        # Update again and check increment
        config_manager.update_last_run()
        assert config_manager.get_state("startup_count") == 2

    def test_mode_theme_tracking(self, config_manager):
        """Test mode and theme tracking."""
        # Update mode and theme
        config_manager.update_last_mode("schedule")
        config_manager.update_last_theme("dark")
        
        # Check values
        assert config_manager.get_last_mode() == "schedule"
        assert config_manager.get_last_theme() == "dark"
        
        # Check defaults
        with patch.object(config_manager, "get_state", return_value=None):
            assert config_manager.get_last_mode() == "manual"
            assert config_manager.get_last_theme() == "light"


class TestConfigMigration:
    """Test configuration migration functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_version_comparison(self):
        """Test version comparison utility."""
        # Create a ConfigManager instance just to access the method
        config_manager = ConfigManager()
        
        # Test version comparisons
        assert config_manager._compare_versions("1.0.0", "1.0.0") == 0
        assert config_manager._compare_versions("1.0.0", "1.0.1") < 0
        assert config_manager._compare_versions("1.0.1", "1.0.0") > 0
        assert config_manager._compare_versions("1.1.0", "1.0.0") > 0
        assert config_manager._compare_versions("1.0.0", "1.1.0") < 0
        assert config_manager._compare_versions("2.0.0", "1.0.0") > 0
        assert config_manager._compare_versions("1.0.0", "2.0.0") < 0
        
        # Test with partial versions
        assert config_manager._compare_versions("1.0", "1.0.0") == 0
        assert config_manager._compare_versions("1", "1.0.0") == 0
        assert config_manager._compare_versions("1", "2") < 0

    def test_migration_to_1_0_0(self, temp_config_dir):
        """Test migration to version 1.0.0."""
        # Create a pre-1.0.0 config file
        config_file = temp_config_dir / "config.json"
        temp_config_dir.mkdir(exist_ok=True)
        
        old_config = {
            "mode": "manual",
            "current_theme": "light",
            "schedule": {"light_time": "07:00", "dark_time": "19:00", "enabled": False},
            "location": {
                "enabled": False,
                "latitude": None,
                "longitude": None,
                "auto_detect": True,
            },
            "ui": {
                "show_notifications": True,
                "minimize_to_tray": True,
                "autostart": False,
            },
        }
        
        with open(config_file, "w") as f:
            json.dump(old_config, f)
        
        # Create ConfigManager which should trigger migration
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
        
        # Check that migration added version and state
        assert config_manager.get("version") == config_manager.CONFIG_VERSION
        assert "state" in config_manager.get_all()
        assert isinstance(config_manager.get("state"), dict)
        
        # Check that state was initialized correctly
        state = config_manager.get("state")
        assert state["last_active_mode"] == "manual"
        assert state["last_theme"] == "light"
        assert state["startup_count"] == 0
        assert state["last_run"] is None

    def test_config_migration_process(self, temp_config_dir):
        """Test that configuration is properly migrated."""
        # Create a pre-1.0.0 config file
        config_file = temp_config_dir / "config.json"
        temp_config_dir.mkdir(exist_ok=True)
        
        old_config = {
            "mode": "schedule",
            "current_theme": "dark",
        }
        
        with open(config_file, "w") as f:
            json.dump(old_config, f)
        
        # Create ConfigManager which should trigger migration
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
        
        # Get the migrated config directly from the manager
        migrated_config = config_manager.get_all()
        
        # Check that version was added
        assert "version" in migrated_config
        assert migrated_config["version"] == ConfigManager.CONFIG_VERSION
        
        # Check that state section was added
        assert "state" in migrated_config
        
        # Check that mode and theme were preserved
        assert migrated_config["mode"] == "schedule"
        assert migrated_config["current_theme"] == "dark"


class TestStateRestoration:
    """Test application state restoration."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_set_app_config_updates_state(self, temp_config_dir):
        """Test that set_app_config updates state tracking."""
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
        
        # Create a new app config with different mode and theme
        app_config = AppConfig(
            current_mode="schedule",
            manual_theme="dark",
            schedule_enabled=True,
            dark_time="20:00",
            light_time="08:00"
        )
        
        # Set the app config
        config_manager.set_app_config(app_config)
        
        # Check that state was updated
        assert config_manager.get_last_mode() == "schedule"
        assert config_manager.get_last_theme() == "dark"
        
        # Check that config was saved
        config_file = temp_config_dir / "config.json"
        with open(config_file, "r") as f:
            data = json.load(f)
        
        assert data["mode"] == "schedule"
        assert data["current_theme"] == "dark"
        assert data["state"]["last_active_mode"] == "schedule"
        assert data["state"]["last_theme"] == "dark"

    def test_automatic_state_updates(self, temp_config_dir):
        """Test that state is automatically updated when settings change."""
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
        
        # Change mode and theme
        config_manager.set("mode", "location")
        config_manager.set("current_theme", "dark")
        
        # Check that state was updated
        assert config_manager.get_last_mode() == "location"
        assert config_manager.get_last_theme() == "dark"