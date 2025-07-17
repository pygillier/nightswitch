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
from .core.mode_controller import ModeController, get_mode_controller
from .plugins.manager import PluginManager, get_plugin_manager
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
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        # Add handler to root logger
        root_logger.addHandler(console_handler)

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
            # Initialize configuration manager
            self._config_manager = get_config()

            # Load application settings
            app_config = self._config_manager.get_app_config()
            self._start_minimized = app_config.start_minimized

            # Initialize plugin manager
            self._plugin_manager = get_plugin_manager()

            # Discover and load plugins
            self._plugin_manager.discover_plugins()
            active_plugin = self._plugin_manager.auto_select_plugin()

            if not active_plugin:
                self.logger.error("No compatible plugins found")
                self._show_error_dialog(
                    "No compatible theme plugins found for your desktop environment.",
                    "Nightswitch requires a compatible plugin to function properly.",
                )

            # Initialize mode controller
            self._mode_controller = get_mode_controller()

            self.logger.info("Core components initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {e}")
            raise

    def _create_ui_components(self) -> None:
        """Create UI components (main window and system tray)."""
        try:
            # Create main window
            self._main_window = MainWindow(self, self._mode_controller)

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
            about_dialog.set_website("https://github.com/nightswitch/nightswitch")
            about_dialog.set_website_label("Nightswitch on GitHub")
            about_dialog.set_authors(["Nightswitch Contributors"])
            about_dialog.set_license_type(Gtk.License.GPL_3_0)

            about_dialog.present()
            self.logger.debug("About dialog shown")

        except Exception as e:
            self.logger.error(f"Failed to show about dialog: {e}")

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
            # Save configuration
            if self._config_manager:
                self._config_manager._save_config()

            # Clean up system tray
            cleanup_system_tray()

            # Clean up mode controller
            if self._mode_controller:
                self._mode_controller.cleanup()

            # Clean up plugin manager
            if self._plugin_manager:
                self._plugin_manager.cleanup_all()

            # Quit the application
            self.quit()

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            # Force quit even if cleanup fails
            self.quit()


def main() -> int:
    """
    Main entry point for the Nightswitch application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
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
