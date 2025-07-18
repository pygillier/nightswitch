"""
Main entry point for the Nightswitch application.

This module provides the TrayApplication class that extends Gtk.Application
and serves as the main entry point for the Nightswitch application.
"""

import logging
import signal
import sys
from typing import List, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk

from .core.config import ConfigManager, get_config
from .core.logging_manager import LogLevel, LoggingManager, get_logging_manager
from .core.error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    get_error_handler,
)
from .core.mode_controller import ModeController, get_mode_controller
from .core.notification import (
    NotificationManager,
    NotificationType,
    NotificationPriority,
    get_notification_manager,
)
from .plugins.manager import (
    PluginCompatibilityError,
    PluginError,
    PluginManager,
    get_plugin_manager,
)
from .ui.main_window import MainWindow
from .ui.system_tray import SystemTrayIcon, cleanup_system_tray, create_system_tray


class TrayApplication(Gtk.Application):
    """
    Main application class for Nightswitch.

    Extends Gtk.Application to provide application lifecycle management,
    system tray integration, and coordination of all application components.
    """

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__(
            application_id="org.nightswitch.Nightswitch",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger("nightswitch.main")

        # Application components
        self._config_manager: Optional[ConfigManager] = None
        self._plugin_manager: Optional[PluginManager] = None
        self._mode_controller: Optional[ModeController] = None
        self._system_tray: Optional[SystemTrayIcon] = None
        self._main_window: Optional[MainWindow] = None

        # Application state
        self._is_quitting = False
        self._start_minimized = False

        self.logger.info("TrayApplication initialized")

    def _setup_logging(self) -> None:
        """Set up application logging."""
        # Get configuration manager
        config_manager = get_config()
        app_config = config_manager.get_app_config()
        
        # Get logging manager
        logging_manager = get_logging_manager()
        
        # Convert string log level to LogLevel enum
        log_level_str = app_config.log_level.upper()
        log_level = LogLevel.INFO  # Default
        
        try:
            log_level = LogLevel[log_level_str]
        except KeyError:
            # Invalid log level in config, use INFO as fallback
            pass
            
        # Initialize logging system
        logging_manager.initialize(
            log_level=log_level,
            debug_mode=app_config.debug_mode
        )
        
        # Enable debug mode for specific components if configured
        for component in app_config.debug_components:
            logging_manager.enable_debug_mode(component)
            
        # Log initialization
        logger = logging.getLogger("nightswitch.core.logging")
        logger.info(f"Logging system initialized with level: {log_level.name}")
        if app_config.debug_mode:
            logger.info("Debug mode enabled globally")

    def do_startup(self) -> None:
        """Handle application startup."""
        self.logger.info("Application starting up")

        # Chain up to parent implementation
        Gtk.Application.do_startup(self)

        try:
            # Initialize core components
            self._init_core_components()

            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Set up application actions
            self._setup_actions()

            self.logger.info("Application startup completed")

        except Exception as e:
            self.logger.error(f"Error during startup: {e}")
            self.quit()

    def do_activate(self) -> None:
        """Handle application activation."""
        self.logger.info("Application activated")

        # Chain up to parent implementation
        Gtk.Application.do_activate(self)

        try:
            # Create UI components if not already created
            if not self._main_window:
                self._create_ui_components()

            # Show or hide main window based on settings
            if not self._start_minimized:
                self.show_main_window()

            self.logger.info("Application activation completed")

        except Exception as e:
            self.logger.error(f"Error during activation: {e}")
            self.quit()

    def _init_core_components(self) -> None:
        """Initialize core application components."""
        try:
            # Initialize error handler and notification manager
            self._error_handler = get_error_handler()
            self._notification_manager = get_notification_manager()
            self._notification_manager.set_application(self)
            
            # Set up error handler to use notification manager
            self._error_handler.register_notification_callback(
                self._notification_manager.notify_error
            )
            
            # Register fallback handlers for different error categories
            self._register_fallback_handlers()

            # Initialize configuration manager
            self._config_manager = get_config()
            
            # Update last run timestamp and startup count
            self._config_manager.update_last_run()

            # Load application settings
            app_config = self._config_manager.get_app_config()
            self._start_minimized = app_config.start_minimized

            # Initialize plugin manager
            self._plugin_manager = get_plugin_manager()

            # Discover and load plugins
            self._plugin_manager.discover_plugins()
            
            try:
                active_plugin = self._plugin_manager.auto_select_plugin()
                
                if not active_plugin:
                    self._error_handler.handle_plugin_error(
                        message="No compatible theme plugins found for your desktop environment.",
                        severity=ErrorSeverity.ERROR,
                        suggestion="Nightswitch requires a compatible plugin to function properly.",
                    )
            except PluginError as e:
                self._error_handler.handle_plugin_error(
                    message="Failed to initialize plugin",
                    exception=e,
                    severity=ErrorSeverity.ERROR,
                    suggestion="Try restarting the application or check system compatibility.",
                )

            # Initialize mode controller
            self._mode_controller = get_mode_controller()
            
            # Restore previous mode if needed
            self._restore_application_state()

            self.logger.info("Core components initialized")

        except Exception as e:
            self._error_handler.handle_error(
                message="Failed to initialize core components",
                exception=e,
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
            )
            raise

    def _create_ui_components(self) -> None:
        """Create UI components (main window and system tray)."""
        try:
            # Create main window
            self._main_window = MainWindow(self, self._mode_controller)
            
            # Set dialog parent for notification manager
            self._notification_manager.set_dialog_parent(self._main_window)
            
            # Set up in-app notification callback if main window supports it
            if hasattr(self._main_window, "show_notification"):
                self._notification_manager.set_in_app_notification_callback(
                    self._main_window.show_notification
                )

            # Create system tray icon
            self._system_tray = create_system_tray(
                mode_controller=self._mode_controller,
                show_window_callback=self.show_main_window,
                quit_callback=self.quit_application,
            )

            # Show system tray icon
            if self._system_tray:
                self._system_tray.show()

            self.logger.info("UI components created")

        except Exception as e:
            if hasattr(self, "_error_handler"):
                self._error_handler.handle_error(
                    message="Failed to create UI components",
                    exception=e,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.UI,
                )
            else:
                self.logger.error(f"Failed to create UI components: {e}")
            raise

    def _setup_actions(self) -> None:
        """Set up application actions."""
        try:
            # Quit action
            quit_action = Gio.SimpleAction.new("quit", None)
            quit_action.connect("activate", self._on_quit_action)
            self.add_action(quit_action)

            # Show window action
            show_window_action = Gio.SimpleAction.new("show-window", None)
            show_window_action.connect("activate", self._on_show_window_action)
            self.add_action(show_window_action)

            # Hide window action
            hide_window_action = Gio.SimpleAction.new("hide-window", None)
            hide_window_action.connect("activate", self._on_hide_window_action)
            self.add_action(hide_window_action)

            # About action
            about_action = Gio.SimpleAction.new("about", None)
            about_action.connect("activate", self._on_about_action)
            self.add_action(about_action)

            self.logger.debug("Application actions set up")

        except Exception as e:
            self.logger.error(f"Failed to set up actions: {e}")
            raise

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        try:
            # Handle SIGINT (Ctrl+C) and SIGTERM
            GLib.unix_signal_add(
                GLib.PRIORITY_DEFAULT, signal.SIGINT, self._on_unix_signal, None
            )
            GLib.unix_signal_add(
                GLib.PRIORITY_DEFAULT, signal.SIGTERM, self._on_unix_signal, None
            )

            self.logger.debug("Signal handlers set up")

        except Exception as e:
            self.logger.error(f"Failed to set up signal handlers: {e}")

    def _on_unix_signal(self, user_data: object) -> bool:
        """
        Handle Unix signals (SIGINT, SIGTERM).

        Args:
            user_data: User data passed to signal handler

        Returns:
            False to remove the source
        """
        self.logger.info("Received termination signal")
        self.quit_application()
        return False  # Remove the source

    def _on_quit_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """
        Handle quit action.

        Args:
            action: Action that was activated
            parameter: Action parameter (None)
        """
        self.quit_application()

    def _on_show_window_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """
        Handle show window action.

        Args:
            action: Action that was activated
            parameter: Action parameter (None)
        """
        self.show_main_window()

    def _on_hide_window_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """
        Handle hide window action.

        Args:
            action: Action that was activated
            parameter: Action parameter (None)
        """
        self.hide_main_window()

    def _on_about_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """
        Handle about action.

        Args:
            action: Action that was activated
            parameter: Action parameter (None)
        """
        self.show_about_dialog()

    def show_main_window(self) -> None:
        """Show the main application window."""
        if self._main_window:
            self._main_window.present()
            self.logger.info("Main window shown")

    def hide_main_window(self) -> None:
        """Hide the main application window."""
        if self._main_window:
            self._main_window.hide()
            self.logger.info("Main window hidden")

    def show_about_dialog(self) -> None:
        """Show the about dialog."""
        try:
            about_dialog = Gtk.AboutDialog()
            about_dialog.set_transient_for(self._main_window)
            about_dialog.set_modal(True)

            about_dialog.set_program_name("Nightswitch")
            about_dialog.set_version("1.0.0")
            about_dialog.set_copyright("© 2025 Nightswitch Contributors")
            about_dialog.set_comments(
                "A theme switching utility for Linux desktop environments"
            )
            about_dialog.set_website("https://github.com/pygillier/nightswitch")
            about_dialog.set_website_label("Nightswitch on GitHub")
            about_dialog.set_authors(["Nightswitch Contributors"])
            about_dialog.set_license_type(Gtk.License.GPL_3_0)

            about_dialog.present()
            self.logger.debug("About dialog shown")

        except Exception as e:
            self.logger.error(f"Failed to show about dialog: {e}")

    def _register_fallback_handlers(self) -> None:
        """Register fallback handlers for different error categories."""
        try:
            # Register plugin fallback handler
            self._error_handler.register_fallback_handler(
                ErrorCategory.PLUGIN, self._plugin_error_fallback
            )
            
            # Register service fallback handler
            self._error_handler.register_fallback_handler(
                ErrorCategory.SERVICE, self._service_error_fallback
            )
            
            # Register network fallback handler
            self._error_handler.register_fallback_handler(
                ErrorCategory.NETWORK, self._network_error_fallback
            )
            
            # Register config fallback handler
            self._error_handler.register_fallback_handler(
                ErrorCategory.CONFIG, self._config_error_fallback
            )
            
            self.logger.debug("Fallback handlers registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register fallback handlers: {e}")
            
    def _restore_application_state(self) -> None:
        """
        Restore application state from previous session.
        
        This method restores the application state based on the saved configuration,
        including the active mode and theme settings.
        """
        try:
            if not self._config_manager or not self._mode_controller:
                self.logger.warning("Cannot restore state: components not initialized")
                return
                
            # Get current configuration
            app_config = self._config_manager.get_app_config()
            
            # Check if we need to restore schedule mode
            if app_config.current_mode == "schedule" and app_config.schedule_enabled:
                self.logger.info("Restoring schedule mode from previous session")
                self._mode_controller.set_schedule_mode(
                    app_config.dark_time, 
                    app_config.light_time
                )
                
            # Check if we need to restore location mode
            elif app_config.current_mode == "location" and app_config.location_enabled:
                self.logger.info("Restoring location mode from previous session")
                if app_config.auto_location:
                    # Auto-detect location
                    self._mode_controller.set_location_mode()
                elif app_config.latitude is not None and app_config.longitude is not None:
                    # Use saved coordinates
                    self._mode_controller.set_location_mode(
                        app_config.latitude,
                        app_config.longitude
                    )
                    
            # Otherwise, ensure manual mode is set with the correct theme
            else:
                self.logger.info("Restoring manual mode from previous session")
                if app_config.manual_theme == "dark":
                    self._mode_controller.manual_switch_to_dark()
                else:
                    self._mode_controller.manual_switch_to_light()
                    
            self.logger.info("Application state restored successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to restore application state: {e}")
            # Fall back to manual mode if restoration fails
            try:
                self._mode_controller.set_manual_mode()
            except Exception:
                pass
    
    def _plugin_error_fallback(self, error_context: ErrorContext) -> bool:
        """
        Fallback handler for plugin errors.
        
        Args:
            error_context: Error context
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # If no active plugin, try to find another compatible plugin
            if (
                self._plugin_manager 
                and not self._plugin_manager.get_active_plugin()
                and "No compatible" in error_context.message
            ):
                # Get list of all registered plugins
                plugins = self._plugin_manager.get_registered_plugins()
                
                if not plugins:
                    return False  # No plugins available
                
                # Try to load any plugin as fallback
                for plugin_name in plugins:
                    try:
                        if self._plugin_manager.load_plugin(plugin_name):
                            self._plugin_manager.set_active_plugin(plugin_name)
                            self.logger.info(f"Fallback to plugin: {plugin_name}")
                            
                            # Notify about fallback
                            self._notification_manager.notify(
                                message=f"Using fallback plugin: {plugin_name}",
                                title="Plugin Fallback",
                                notification_type=NotificationType.WARNING,
                            )
                            return True
                    except Exception:
                        continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in plugin fallback handler: {e}")
            return False
    
    def _service_error_fallback(self, error_context: ErrorContext) -> bool:
        """
        Fallback handler for service errors.
        
        Args:
            error_context: Error context
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # Handle location service errors
            if error_context.source and "LocationService" in error_context.source:
                # If location detection fails, suggest manual location input
                self._notification_manager.notify(
                    message="Location detection failed. You can manually set your location in the settings.",
                    title="Location Service",
                    notification_type=NotificationType.INFO,
                )
                return True
                
            # Handle sunrise/sunset service errors
            elif error_context.source and "SunriseSunset" in error_context.source:
                # If sunrise/sunset API fails, suggest schedule mode
                self._notification_manager.notify(
                    message="Sunrise/sunset data unavailable. Consider using schedule mode instead.",
                    title="Sunrise/Sunset Service",
                    notification_type=NotificationType.INFO,
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in service fallback handler: {e}")
            return False
    
    def _network_error_fallback(self, error_context: ErrorContext) -> bool:
        """
        Fallback handler for network errors.
        
        Args:
            error_context: Error context
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # For network errors, suggest offline mode options
            if self._mode_controller:
                # If in location mode, suggest switching to manual or schedule mode
                if self._mode_controller.get_current_mode() and self._mode_controller.get_current_mode().value == "location":
                    self._notification_manager.notify(
                        message="Network connection unavailable. Location mode requires internet access. Consider using manual or schedule mode instead.",
                        title="Network Error",
                        notification_type=NotificationType.WARNING,
                    )
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in network fallback handler: {e}")
            return False
    
    def _config_error_fallback(self, error_context: ErrorContext) -> bool:
        """
        Fallback handler for configuration errors.
        
        Args:
            error_context: Error context
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # For config errors, try to reset to defaults
            if self._config_manager:
                try:
                    # Reset to default configuration
                    self._config_manager.reset_to_defaults()
                    
                    self._notification_manager.notify(
                        message="Configuration has been reset to defaults due to errors.",
                        title="Configuration Reset",
                        notification_type=NotificationType.WARNING,
                    )
                    return True
                except Exception:
                    pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in config fallback handler: {e}")
            return False
    
    def _show_error_dialog(self, message: str, details: Optional[str] = None) -> None:
        """
        Show an error dialog.

        Args:
            message: Error message
            details: Additional details (optional)
        """
        try:
            dialog = Gtk.MessageDialog(
                transient_for=self._main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Nightswitch Error",
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

    def quit_application(self) -> None:
        """Quit the application with proper cleanup."""
        if self._is_quitting:
            return

        self._is_quitting = True
        self.logger.info("Application quitting")

        try:
            # Save application state
            if self._config_manager and self._mode_controller:
                # Get current mode and theme
                current_mode = self._mode_controller.get_current_mode()
                current_theme = self._mode_controller.get_current_theme()
                
                if current_mode and current_theme:
                    # Update state tracking
                    self._config_manager.update_last_mode(current_mode.value)
                    self._config_manager.update_last_theme(current_theme.value)
                    
                    # Save configuration
                    self._config_manager._save_config()
                    self.logger.info("Application state saved")
                else:
                    self.logger.warning("Could not save application state: mode or theme not set")
            else:
                self.logger.warning("Could not save application state: components not initialized")

            # Clean up system tray
            cleanup_system_tray()

            # Clean up mode controller
            if self._mode_controller:
                self._mode_controller.cleanup()

            # Clean up plugin manager
            if self._plugin_manager:
                self._plugin_manager.cleanup_all()
                
            # Clear error handler and notification manager history
            if hasattr(self, "_error_handler"):
                self._error_handler.clear_error_history()
                
            if hasattr(self, "_notification_manager"):
                self._notification_manager.clear_notification_history()

            # Quit the application
            self.quit()

        except Exception as e:
            if hasattr(self, "_error_handler"):
                self._error_handler.handle_error(
                    message="Error during application shutdown",
                    exception=e,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.SYSTEM,
                    notify_user=False,  # Don't notify during shutdown
                )
            else:
                self.logger.error(f"Error during application shutdown: {e}")
                
            # Force quit even if cleanup fails
            self.quit()


def parse_args(args: List[str]) -> dict:
    """
    Parse command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dictionary of parsed arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Nightswitch - Theme switching utility")
    
    # Logging options
    log_group = parser.add_argument_group("Logging Options")
    log_group.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the log level"
    )
    log_group.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode globally"
    )
    log_group.add_argument(
        "--debug-component", 
        action="append",
        help="Enable debug mode for specific component (can be used multiple times)"
    )
    log_group.add_argument(
        "--log-file", 
        help="Path to log file (default: ~/.local/state/nightswitch/logs/nightswitch.log)"
    )
    
    # Application options
    app_group = parser.add_argument_group("Application Options")
    app_group.add_argument(
        "--minimized", 
        action="store_true",
        help="Start application minimized to system tray"
    )
    app_group.add_argument(
        "--reset-config", 
        action="store_true",
        help="Reset configuration to defaults"
    )
    
    return vars(parser.parse_args(args[1:]))  # Skip the first argument (script name)


def main() -> int:
    """
    Main entry point for the Nightswitch application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command line arguments
        args = parse_args(sys.argv)
        
        # Handle configuration reset if requested
        if args.get("reset_config"):
            config_manager = get_config()
            config_manager.reset_to_defaults()
            print("Configuration reset to defaults")
            return 0
            
        # Apply command line arguments to configuration
        config_manager = get_config()
        app_config = config_manager.get_app_config()
        
        # Override log level if specified
        if args.get("log_level"):
            app_config.log_level = args["log_level"]
            
        # Enable debug mode if specified
        if args.get("debug"):
            app_config.debug_mode = True
            
        # Add debug components if specified
        if args.get("debug_component"):
            for component in args["debug_component"]:
                if component not in app_config.debug_components:
                    app_config.debug_components.append(component)
                    
        # Override start_minimized if specified
        if args.get("minimized"):
            app_config.start_minimized = True
            
        # Update configuration
        config_manager.set_app_config(app_config)
        
        # Create and run application
        app = TrayApplication()
        exit_status = app.run(sys.argv)

        logging.info(f"Application exited with status: {exit_status}")
        return int(exit_status)

    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())