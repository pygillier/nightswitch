"""
Configuration management for Nightswitch application.

This module provides FreeDesktop-compliant configuration storage following
the XDG Base Directory Specification.
"""

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class AppConfig:
    """
    Application configuration data class.
    
    Represents the complete configuration state of the Nightswitch application
    with type-safe access to all configuration fields.
    """
    
    # Current mode and theme
    current_mode: str = "manual"  # 'manual', 'schedule', 'location'
    manual_theme: str = "light"  # 'dark', 'light'
    
    # Schedule mode settings
    schedule_enabled: bool = False
    dark_time: str = "19:00"  # HH:MM format
    light_time: str = "07:00"  # HH:MM format
    
    # Location mode settings
    location_enabled: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    auto_location: bool = True
    
    # Application settings
    start_minimized: bool = True
    show_notifications: bool = True
    autostart: bool = False
    
    # Plugin settings
    active_plugin: str = "auto"  # 'auto', 'budgie', 'gtk', 'gnome', 'kde', 'xfce'
    plugin_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.plugin_settings is None:
            self.plugin_settings = {}
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Validate mode
        if self.current_mode not in ["manual", "schedule", "location"]:
            return False
        
        # Validate theme
        if self.manual_theme not in ["dark", "light"]:
            return False
        
        # Validate time format (HH:MM)
        import re
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        if not time_pattern.match(self.dark_time) or not time_pattern.match(self.light_time):
            return False
        
        # Validate coordinates if provided
        if self.latitude is not None:
            if not (-90 <= self.latitude <= 90):
                return False
        
        if self.longitude is not None:
            if not (-180 <= self.longitude <= 180):
                return False
        
        # Validate plugin name
        valid_plugins = ["auto", "budgie", "gtk", "gnome", "kde", "xfce"]
        if self.active_plugin not in valid_plugins:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """
        Create AppConfig instance from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            AppConfig instance
        """
        return cls(
            current_mode=data.get("mode", "manual"),
            manual_theme=data.get("current_theme", "light"),
            schedule_enabled=data.get("schedule", {}).get("enabled", False),
            dark_time=data.get("schedule", {}).get("dark_time", "19:00"),
            light_time=data.get("schedule", {}).get("light_time", "07:00"),
            location_enabled=data.get("location", {}).get("enabled", False),
            latitude=data.get("location", {}).get("latitude"),
            longitude=data.get("location", {}).get("longitude"),
            auto_location=data.get("location", {}).get("auto_detect", True),
            start_minimized=data.get("ui", {}).get("minimize_to_tray", True),
            show_notifications=data.get("ui", {}).get("show_notifications", True),
            autostart=data.get("ui", {}).get("autostart", False),
            active_plugin=data.get("plugins", {}).get("active_plugin", "auto"),
            plugin_settings=data.get("plugins", {}).get("plugin_settings", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AppConfig instance to dictionary format.
        
        Returns:
            Configuration dictionary compatible with ConfigManager
        """
        return {
            "mode": self.current_mode,
            "current_theme": self.manual_theme,
            "schedule": {
                "enabled": self.schedule_enabled,
                "dark_time": self.dark_time,
                "light_time": self.light_time
            },
            "location": {
                "enabled": self.location_enabled,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "auto_detect": self.auto_location
            },
            "ui": {
                "minimize_to_tray": self.start_minimized,
                "show_notifications": self.show_notifications,
                "autostart": self.autostart
            },
            "plugins": {
                "active_plugin": self.active_plugin,
                "plugin_settings": self.plugin_settings
            }
        }


class XDGPaths:
    """
    XDG Base Directory Specification compliant path management.
    
    Follows the FreeDesktop.org specification for application data storage:
    https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    
    APP_NAME = "nightswitch"
    
    @classmethod
    def config_home(cls) -> Path:
        """
        Get the XDG_CONFIG_HOME directory for the application.
        
        Returns:
            Path to ~/.config/nightswitch/ (or $XDG_CONFIG_HOME/nightswitch/)
        """
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / cls.APP_NAME
        return Path.home() / ".config" / cls.APP_NAME
    
    @classmethod
    def data_home(cls) -> Path:
        """
        Get the XDG_DATA_HOME directory for the application.
        
        Returns:
            Path to ~/.local/share/nightswitch/ (or $XDG_DATA_HOME/nightswitch/)
        """
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / cls.APP_NAME
        return Path.home() / ".local" / "share" / cls.APP_NAME
    
    @classmethod
    def cache_home(cls) -> Path:
        """
        Get the XDG_CACHE_HOME directory for the application.
        
        Returns:
            Path to ~/.cache/nightswitch/ (or $XDG_CACHE_HOME/nightswitch/)
        """
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_home:
            return Path(xdg_cache_home) / cls.APP_NAME
        return Path.home() / ".cache" / cls.APP_NAME
    
    @classmethod
    def state_home(cls) -> Path:
        """
        Get the XDG_STATE_HOME directory for the application.
        
        Returns:
            Path to ~/.local/state/nightswitch/ (or $XDG_STATE_HOME/nightswitch/)
        """
        xdg_state_home = os.environ.get("XDG_STATE_HOME")
        if xdg_state_home:
            return Path(xdg_state_home) / cls.APP_NAME
        return Path.home() / ".local" / "state" / cls.APP_NAME


class ConfigManager:
    """
    Configuration manager for Nightswitch application.
    
    Handles loading, saving, and managing application configuration
    following FreeDesktop specifications.
    """
    
    CONFIG_FILE = "config.json"
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "mode": "manual",  # manual, schedule, location
        "current_theme": "light",  # light, dark
        "schedule": {
            "light_time": "07:00",
            "dark_time": "19:00",
            "enabled": False
        },
        "location": {
            "enabled": False,
            "latitude": None,
            "longitude": None,
            "auto_detect": True
        },
        "ui": {
            "show_notifications": True,
            "minimize_to_tray": True,
            "autostart": False
        },
        "plugins": {
            "active_plugin": "auto",  # auto, budgie, gtk, gnome, kde, xfce
            "plugin_settings": {}
        }
    }
    
    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._config: Dict[str, Any] = {}
        self._config_dir = XDGPaths.config_home()
        self._data_dir = XDGPaths.data_home()
        self._cache_dir = XDGPaths.cache_home()
        self._state_dir = XDGPaths.state_home()
        self._config_path = self._config_dir / self.CONFIG_FILE
        self._ensure_directories()
        self._load_config()
    
    def _ensure_directories(self) -> None:
        """Ensure all required XDG directories exist."""
        directories = [
            self._config_dir,
            self._data_dir,
            self._cache_dir,
            self._state_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load configuration from file or create default configuration."""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_config(self._get_default_config(), loaded_config)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Failed to load config file: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self._save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get a fresh copy of the default configuration."""
        return {
            "mode": "manual",  # manual, schedule, location
            "current_theme": "light",  # light, dark
            "schedule": {
                "light_time": "07:00",
                "dark_time": "19:00",
                "enabled": False
            },
            "location": {
                "enabled": False,
                "latitude": None,
                "longitude": None,
                "auto_detect": True
            },
            "ui": {
                "show_notifications": True,
                "minimize_to_tray": True,
                "autostart": False
            },
            "plugins": {
                "active_plugin": "auto",  # auto, budgie, gtk, gnome, kde, xfce
                "plugin_settings": {}
            }
        }
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge loaded configuration with defaults.
        
        Args:
            default: Default configuration dictionary
            loaded: Loaded configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Error: Failed to save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation like 'schedule.enabled')
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation like 'schedule.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self._save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        # Create a fresh copy of the default configuration
        default_config = {
            "mode": "manual",  # manual, schedule, location
            "current_theme": "light",  # light, dark
            "schedule": {
                "light_time": "07:00",
                "dark_time": "19:00",
                "enabled": False
            },
            "location": {
                "enabled": False,
                "latitude": None,
                "longitude": None,
                "auto_detect": True
            },
            "ui": {
                "show_notifications": True,
                "minimize_to_tray": True,
                "autostart": False
            },
            "plugins": {
                "active_plugin": "auto",  # auto, budgie, gtk, gnome, kde, xfce
                "plugin_settings": {}
            }
        }
        self._config = default_config
        self._save_config()
    
    def get_app_config(self) -> AppConfig:
        """
        Get configuration as AppConfig dataclass instance.
        
        Returns:
            AppConfig instance with current configuration
        """
        return AppConfig.from_dict(self._config)
    
    def set_app_config(self, app_config: AppConfig) -> None:
        """
        Set configuration from AppConfig dataclass instance.
        
        Args:
            app_config: AppConfig instance to save
            
        Raises:
            ValueError: If configuration validation fails
        """
        if not app_config.validate():
            raise ValueError("Invalid configuration values")
        
        self._config = app_config.to_dict()
        self._save_config()
    
    def validate_config(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            app_config = self.get_app_config()
            return app_config.validate()
        except Exception:
            return False
    
    def backup_config(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Path to the created backup file
        """
        if backup_path is None:
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.config_dir / f"config_backup_{timestamp}.json"
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return backup_path
        except OSError as e:
            raise OSError(f"Failed to create backup: {e}")
    
    def restore_config(self, backup_path: Path) -> None:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Raises:
            FileNotFoundError: If backup file doesn't exist
            ValueError: If backup contains invalid configuration
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_config = json.load(f)
            
            # Validate the backup configuration
            merged_config = self._merge_config(self._get_default_config(), backup_config)
            app_config = AppConfig.from_dict(merged_config)
            
            if not app_config.validate():
                raise ValueError("Backup contains invalid configuration")
            
            self._config = merged_config
            self._save_config()
            
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to restore from backup: {e}")
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self._data_dir
    
    @property
    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        return self._cache_dir
    
    @property
    def state_dir(self) -> Path:
        """Get the state directory path."""
        return self._state_dir


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager