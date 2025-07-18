# Nightswitch

<div align="center">

![Nightswitch Logo](https://via.placeholder.com/128x128/2d3748/ffffff?text=NS)

**A modern PyGTK 4 application for intelligent theme switching in Linux desktop environments**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![GTK 4](https://img.shields.io/badge/GTK-4.0+-green.svg)](https://gtk.org/)
[![Flatpak](https://img.shields.io/badge/Flatpak-Ready-blue.svg)](https://flatpak.org/)

</div>

## Overview

Nightswitch is a sophisticated theme management application that brings intelligent dark/light mode switching to Linux desktop environments. Built with PyGTK 4, it provides seamless integration with your desktop while offering multiple automation modes to match your workflow and preferences.

## ✨ Features

### 🎛️ Multiple Switching Modes
- **Manual Mode**: Instant theme switching via system tray interface
- **Schedule Mode**: Time-based automatic switching with customizable schedules
- **Location Mode**: Sunrise/sunset-based switching using your geographic location

### 🔌 Extensible Plugin System
- **Ubuntu Budgie**: Primary desktop environment support
- **Generic GTK**: Broad compatibility with GTK-based environments
- **Extensible Architecture**: Plugin system for additional desktop environments

### 🖥️ Desktop Integration
- **System Tray**: Minimal footprint with quick access controls
- **Notifications**: Non-intrusive status updates
- **Autostart**: Seamless integration with desktop session management

### 🌐 Smart Location Services
- **IP-based Location**: Automatic location detection for sunrise/sunset calculations
- **Privacy-focused**: Optional location services with user control
- **Offline Fallback**: Manual location configuration when needed

## 🖥️ Supported Desktop Environments

| Desktop Environment | Status | Plugin |
|---------------------|--------|---------|
| Ubuntu Budgie | ✅ Primary Support | Built-in |
| GNOME | 🔄 Planned | Plugin |
| KDE Plasma | 🔄 Planned | Plugin |
| XFCE | 🔄 Planned | Plugin |
| Generic GTK | ✅ Basic Support | Built-in |

## 📋 Requirements

- **Operating System**: Linux (X11/Wayland)
- **Python**: 3.13 or higher
- **Desktop**: GTK-based environment with system tray support
- **Dependencies**: PyGObject (PyGTK 4), requests, python-dateutil

## 📦 Installation

### Flatpak (Recommended)

The easiest way to install Nightswitch is through Flatpak, which provides sandboxed execution and automatic updates.

```bash
# Install from Flathub (when available)
flatpak install flathub org.nightswitch.Nightswitch

# Or build and install locally
flatpak-builder build-dir org.nightswitch.Nightswitch.yml --install --user --force-clean
```

### From Source

For developers or users who prefer traditional installation:

```bash
# Clone the repository
git clone https://github.com/pygillier/nightswitch.git
cd nightswitch

# Install using the installation script (recommended)
./install.sh --user  # For user installation
./install.sh --system  # For system-wide installation (requires sudo)

# Or install manually with uv
uv pip install -e .
```

### Installation Script Options

The `install.sh` script provides several options:

```bash
# Install for current user (default)
./install.sh --user

# Install system-wide (requires sudo)
./install.sh --system

# Uninstall Nightswitch
./install.sh --uninstall

# Show help
./install.sh --help
```

The installation script will:
- Install required dependencies
- Install Nightswitch package
- Create desktop entry
- Set up autostart via desktop file and systemd service
- Install application icon

## 🚀 Usage

### Starting the Application

```bash
# Launch Nightswitch
nightswitch

# Launch minimized to system tray
nightswitch --minimized

# The application will appear in your system tray
# Look for the theme switcher icon in your system tray area
```

### Autostart Configuration

Nightswitch can be configured to start automatically when you log in:

```bash
# Enable autostart (creates desktop and systemd service entries)
./enable-autostart.sh

# Disable autostart
./enable-autostart.sh --disable
```

The installation script automatically sets up autostart. This separate script is provided for users who want to enable or disable autostart after installation.

### Basic Operations

1. **Manual Switching**: Click the system tray icon and select "Switch to Dark/Light Mode"
2. **Schedule Mode**: Configure automatic switching times in the settings
3. **Location Mode**: Enable location-based switching for sunrise/sunset automation

### Configuration

Nightswitch follows the FreeDesktop.org XDG Base Directory Specification for configuration storage:

- **Configuration**: `~/.config/nightswitch/` (or `$XDG_CONFIG_HOME/nightswitch/`)
- **Application Data**: `~/.local/share/nightswitch/` (or `$XDG_DATA_HOME/nightswitch/`)
- **Cache**: `~/.cache/nightswitch/` (or `$XDG_CACHE_HOME/nightswitch/`)
- **State**: `~/.local/state/nightswitch/` (or `$XDG_STATE_HOME/nightswitch/`)

The main configuration file is stored as `config.json` in the configuration directory.

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/pygillier/nightswitch.git
cd nightswitch

# Install development dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Development Workflow

**Important**: This project uses `uv` for all Python operations. Never use `pip` or direct `python` commands.

```bash
# Run tests
uv run pytest

# Code formatting
uv run black src tests
uv run isort src tests

# Type checking
uv run mypy src

# Linting
uv run flake8 src tests

# Run all checks
uv run pytest && uv run black --check src tests && uv run isort --check src tests && uv run mypy src && uv run flake8 src tests
```

### Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/nightswitch --cov-report=html

# Run specific test categories
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
```

## 🏗️ Architecture

Nightswitch follows a modular architecture designed for extensibility and maintainability:

```
src/nightswitch/
├── core/           # Application lifecycle and mode management
│   ├── app.py      # Main application controller
│   ├── modes/      # Mode implementations (manual, schedule, location)
│   └── config.py   # Configuration management
├── plugins/        # Desktop environment plugins
│   ├── base.py     # Plugin interface
│   ├── budgie.py   # Ubuntu Budgie support
│   └── gtk.py      # Generic GTK support
├── services/       # External service integrations
│   ├── location.py # IP-based location detection
│   ├── schedule.py # Time-based scheduling
│   └── sunrise.py  # Astronomical calculations
└── ui/             # GTK 4 user interface
    ├── tray.py     # System tray integration
    ├── settings.py # Settings dialog
    └── notifications.py # User notifications
```

### Key Design Principles

- **Plugin Architecture**: Easy extension for new desktop environments
- **Service-Oriented**: Clean separation of concerns
- **Event-Driven**: Reactive architecture for mode switching
- **Configuration-Driven**: User preferences control behavior

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Format code (`uv run black src tests && uv run isort src tests`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GTK Team**: For the excellent GTK 4 toolkit
- **GNOME Project**: For PyGObject bindings
- **Flatpak Community**: For modern Linux application distribution
- **Ubuntu Budgie Team**: For desktop environment collaboration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/pygillier/nightswitch/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pygillier/nightswitch/discussions)
- **Email**: team@nightswitch.org

---

<div align="center">
Made with ❤️ for the Linux desktop community
</div>