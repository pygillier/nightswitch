# Requirements Document

## Introduction

Nightswitch is a PyGTK 4 application designed to manage night mode (dark/light theme switching) in Ubuntu Budgie and other Linux distributions through a plugin system. The application provides users with multiple ways to control their system's appearance: manual switching, scheduled switching, and location-based automatic switching tied to sunrise/sunset times. The application runs as a system tray utility for easy access and minimal desktop footprint.

## Requirements

### Requirement 1

**User Story:** As a Ubuntu Budgie user, I want a system tray application that allows me to manually switch between dark and light modes, so that I can quickly change my desktop appearance based on my immediate preference.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL display a tray icon in the system notification area
2. WHEN the user clicks the tray icon THEN the system SHALL display the main application window
3. WHEN the main window is displayed THEN the system SHALL show a button group with "Dark" and "Light" options at the top
4. WHEN the user clicks "Dark" THEN the system SHALL immediately apply dark theme to the desktop environment
5. WHEN the user clicks "Light" THEN the system SHALL immediately apply light theme to the desktop environment
6. WHEN a theme change is applied THEN the system SHALL provide visual feedback indicating the current active mode

### Requirement 2

**User Story:** As a user who follows a regular schedule, I want to automatically switch between dark and light modes based on specific times, so that my desktop appearance matches my daily routine without manual intervention.

#### Acceptance Criteria

1. WHEN the main window is displayed THEN the system SHALL show a schedule toggle group below the manual controls
2. WHEN the user enables schedule mode THEN the system SHALL display time input fields for switching to dark and light modes
3. WHEN schedule mode is active AND the current time matches the dark mode time THEN the system SHALL automatically switch to dark theme
4. WHEN schedule mode is active AND the current time matches the light mode time THEN the system SHALL automatically switch to light theme
5. WHEN schedule mode is enabled THEN the system SHALL disable manual mode controls to prevent conflicts
6. WHEN the user disables schedule mode THEN the system SHALL stop automatic time-based switching and re-enable manual controls

### Requirement 3

**User Story:** As a user who wants my desktop to match natural lighting conditions, I want the application to automatically switch themes based on sunrise and sunset times for my location, so that my screen brightness aligns with ambient lighting.

#### Acceptance Criteria

1. WHEN the main window is displayed THEN the system SHALL show a location-based toggle group at the bottom
2. WHEN the user enables location mode THEN the system SHALL request permission to access location data
3. WHEN location access is granted THEN the system SHALL automatically detect sunrise and sunset times for the current location
4. WHEN location mode is active AND sunset occurs THEN the system SHALL automatically switch to dark theme
5. WHEN location mode is active AND sunrise occurs THEN the system SHALL automatically switch to light theme
6. WHEN location mode is enabled THEN the system SHALL disable other mode controls to prevent conflicts
7. WHEN location cannot be determined THEN the system SHALL display an error message and allow manual location input

### Requirement 4

**User Story:** As a system administrator managing multiple Linux distributions, I want nightswitch to work across different desktop environments through a plugin system, so that I can provide consistent night mode functionality regardless of the underlying distribution.

#### Acceptance Criteria

1. WHEN the application is installed THEN the system SHALL support Ubuntu Budgie desktop environment by default
2. WHEN the application starts THEN the system SHALL load appropriate plugins based on the detected desktop environment
3. WHEN a plugin is loaded THEN the system SHALL use the plugin's methods to apply theme changes
4. WHEN no compatible plugin is found THEN the system SHALL display a warning message and disable theme switching functionality
5. WHEN multiple plugins are available THEN the system SHALL prioritize plugins based on desktop environment detection
6. IF a plugin fails to load THEN the system SHALL log the error and attempt to load alternative plugins

### Requirement 5

**User Story:** As a Python developer, I want the application built with modern Python tooling and dependencies, so that it's maintainable and follows current best practices.

#### Acceptance Criteria

1. WHEN the project is set up THEN the system SHALL use Python 3.13 as the runtime environment
2. WHEN dependencies are managed THEN the system SHALL use uv as the dependency manager
3. WHEN the application is built THEN the system SHALL use PyGTK 4 for the user interface
4. WHEN the application runs THEN the system SHALL be compatible with modern Linux desktop environments
5. WHEN the code is structured THEN the system SHALL follow Python packaging best practices with proper module organization

### Requirement 6

**User Story:** As a user, I want the application to remember my preferences and maintain state between sessions, so that my chosen mode and settings persist after system restarts.

#### Acceptance Criteria

1. WHEN the user changes mode settings THEN the system SHALL save the configuration to a persistent storage location
2. WHEN the application starts THEN the system SHALL restore the last used mode and settings
3. WHEN schedule or location mode is configured THEN the system SHALL persist these settings across application restarts
4. WHEN the application is closed THEN the system SHALL continue running in the background to maintain automatic switching
5. IF configuration files are corrupted THEN the system SHALL reset to default settings and notify the user