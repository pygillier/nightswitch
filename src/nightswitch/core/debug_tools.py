"""
Debug tools for Nightswitch application.

This module provides command-line tools for debugging and log management.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .config import get_config
from .logging_manager import LogLevel, get_logging_manager


def parse_debug_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments for debug tools.
    
    Args:
        args: Command line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Nightswitch Debug Tools",
        prog="uv run python -m nightswitch.core.debug_tools"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Debug commands")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Log management commands")
    logs_subparsers = logs_parser.add_subparsers(dest="logs_command", help="Log commands")
    
    # View logs
    view_parser = logs_subparsers.add_parser("view", help="View log contents")
    view_parser.add_argument(
        "--debug", 
        action="store_true",
        help="View debug log instead of regular log"
    )
    view_parser.add_argument(
        "--lines", 
        type=int,
        help="Number of lines to show (from the end)"
    )
    
    # Clear logs
    clear_parser = logs_subparsers.add_parser("clear", help="Clear log contents")
    clear_parser.add_argument(
        "--debug", 
        action="store_true",
        help="Clear debug log instead of regular log"
    )
    clear_parser.add_argument(
        "--all", 
        action="store_true",
        help="Clear both regular and debug logs"
    )
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug mode management")
    debug_subparsers = debug_parser.add_subparsers(dest="debug_command", help="Debug commands")
    
    # Enable debug
    enable_parser = debug_subparsers.add_parser("enable", help="Enable debug mode")
    enable_parser.add_argument(
        "component",
        nargs="?",
        help="Component to enable debug for (omit for global debug)"
    )
    
    # Disable debug
    disable_parser = debug_subparsers.add_parser("disable", help="Disable debug mode")
    disable_parser.add_argument(
        "component",
        nargs="?",
        help="Component to disable debug for (omit for global debug)"
    )
    
    # Status
    status_parser = debug_subparsers.add_parser("status", help="Show debug status")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config commands")
    
    # View config
    view_config_parser = config_subparsers.add_parser("view", help="View configuration")
    view_config_parser.add_argument(
        "--section",
        help="Configuration section to view (e.g., 'logging')"
    )
    
    # Reset config
    reset_config_parser = config_subparsers.add_parser("reset", help="Reset configuration")
    reset_config_parser.add_argument(
        "--section",
        help="Configuration section to reset (omit for full reset)"
    )
    
    return parser.parse_args(args)


def handle_logs_command(args: argparse.Namespace) -> int:
    """
    Handle logs command.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    logging_manager = get_logging_manager()
    
    if args.logs_command == "view":
        # View logs
        log_contents = logging_manager.get_log_contents(
            debug=args.debug,
            lines=args.lines
        )
        print(log_contents)
        return 0
        
    elif args.logs_command == "clear":
        # Clear logs
        if args.all:
            # Clear both logs
            regular_success = logging_manager.clear_logs(debug=False)
            debug_success = logging_manager.clear_logs(debug=True)
            
            if regular_success and debug_success:
                print("All logs cleared successfully")
                return 0
            else:
                print("Failed to clear some logs")
                return 1
        else:
            # Clear specific log
            success = logging_manager.clear_logs(debug=args.debug)
            
            if success:
                log_type = "Debug" if args.debug else "Regular"
                print(f"{log_type} log cleared successfully")
                return 0
            else:
                print("Failed to clear log")
                return 1
    
    print("Unknown logs command")
    return 1


def handle_debug_command(args: argparse.Namespace) -> int:
    """
    Handle debug command.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    logging_manager = get_logging_manager()
    config_manager = get_config()
    app_config = config_manager.get_app_config()
    
    if args.debug_command == "enable":
        # Enable debug mode
        component = args.component
        
        if component:
            # Enable for specific component
            logging_manager.enable_debug_mode(component)
            
            # Update configuration
            if component not in app_config.debug_components:
                app_config.debug_components.append(component)
                config_manager.set_app_config(app_config)
                
            print(f"Debug mode enabled for component: {component}")
        else:
            # Enable globally
            logging_manager.enable_debug_mode()
            
            # Update configuration
            app_config.debug_mode = True
            config_manager.set_app_config(app_config)
            
            print("Debug mode enabled globally")
            
        return 0
        
    elif args.debug_command == "disable":
        # Disable debug mode
        component = args.component
        
        if component:
            # Disable for specific component
            logging_manager.disable_debug_mode(component)
            
            # Update configuration
            if component in app_config.debug_components:
                app_config.debug_components.remove(component)
                config_manager.set_app_config(app_config)
                
            print(f"Debug mode disabled for component: {component}")
        else:
            # Disable globally
            logging_manager.disable_debug_mode()
            
            # Update configuration
            app_config.debug_mode = False
            app_config.debug_components = []
            config_manager.set_app_config(app_config)
            
            print("Debug mode disabled globally")
            
        return 0
        
    elif args.debug_command == "status":
        # Show debug status
        global_debug = logging_manager.is_debug_mode_enabled()
        debug_components = logging_manager.get_debug_components()
        
        print(f"Global debug mode: {'Enabled' if global_debug else 'Disabled'}")
        
        if debug_components:
            print("\nComponents with debug enabled:")
            for component in debug_components:
                print(f"- {component}")
        else:
            print("\nNo components have debug mode enabled")
            
        return 0
    
    print("Unknown debug command")
    return 1


def handle_config_command(args: argparse.Namespace) -> int:
    """
    Handle config command.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    config_manager = get_config()
    
    if args.config_command == "view":
        # View configuration
        section = args.section
        
        if section:
            # View specific section
            config_data = config_manager.get(section)
            
            if config_data is None:
                print(f"Section '{section}' not found in configuration")
                return 1
                
            print(f"Configuration section '{section}':")
            _print_config_section(config_data, indent=2)
        else:
            # View full configuration
            config_data = config_manager.get_all()
            
            print("Full configuration:")
            _print_config_section(config_data, indent=2)
            
        return 0
        
    elif args.config_command == "reset":
        # Reset configuration
        section = args.section
        
        if section:
            # Reset specific section
            default_config = config_manager._get_default_config()
            
            if section not in default_config:
                print(f"Section '{section}' not found in configuration")
                return 1
                
            # Update section with defaults
            config_manager.set(section, default_config[section])
            print(f"Configuration section '{section}' reset to defaults")
        else:
            # Reset full configuration
            config_manager.reset_to_defaults()
            print("Full configuration reset to defaults")
            
        return 0
    
    print("Unknown config command")
    return 1


def _print_config_section(data, indent=0):
    """
    Print configuration section recursively.
    
    Args:
        data: Configuration data
        indent: Indentation level
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                _print_config_section(value, indent + 2)
            else:
                print(" " * indent + f"{key}: {value}")
    else:
        print(" " * indent + str(data))


def main() -> int:
    """
    Main entry point for debug tools.
    
    Returns:
        Exit code
    """
    try:
        # Initialize logging manager
        logging_manager = get_logging_manager()
        logging_manager.initialize(log_level=LogLevel.INFO)
        
        # Parse arguments
        args = parse_debug_args(sys.argv[1:])
        
        if not args.command:
            print("No command specified. Use --help for usage information.")
            return 1
        
        # Handle commands
        if args.command == "logs":
            return handle_logs_command(args)
        elif args.command == "debug":
            return handle_debug_command(args)
        elif args.command == "config":
            return handle_config_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())