#!/bin/bash
# Script to enable Nightswitch autostart

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}     Nightswitch Autostart Setup      ${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to enable autostart
enable_autostart() {
    echo -e "${BLUE}Setting up autostart for Nightswitch...${NC}"
    
    # Create autostart directories if they don't exist
    mkdir -p "$HOME/.config/autostart"
    mkdir -p "$HOME/.config/systemd/user"
    
    # Check if desktop file exists in system location
    if [ -f "/usr/share/applications/me.pygillier.Nightswitch.desktop" ]; then
        echo -e "${YELLOW}Found system-wide desktop file, copying to user autostart...${NC}"
        cp "/usr/share/applications/me.pygillier.Nightswitch.desktop" "$HOME/.config/autostart/"
    elif [ -f "$HOME/.local/share/applications/me.pygillier.Nightswitch.desktop" ]; then
        echo -e "${YELLOW}Found user desktop file, copying to autostart...${NC}"
        cp "$HOME/.local/share/applications/me.pygillier.Nightswitch.desktop" "$HOME/.config/autostart/"
    else
        echo -e "${YELLOW}Desktop file not found, creating minimal autostart entry...${NC}"
        cat > "$HOME/.config/autostart/me.pygillier.Nightswitch.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Nightswitch
Comment=Manage night mode and theme switching in Linux desktop environments
Exec=nightswitch --minimized
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
    fi
    
    # Check if systemd service file exists in system location
    if [ -f "/usr/lib/systemd/user/nightswitch.service" ]; then
        echo -e "${YELLOW}Found system-wide systemd service, enabling...${NC}"
        systemctl --user enable --now nightswitch.service
    elif [ -f "$HOME/.config/systemd/user/nightswitch.service" ]; then
        echo -e "${YELLOW}Found user systemd service, enabling...${NC}"
        systemctl --user enable --now nightswitch.service
    else
        echo -e "${YELLOW}Systemd service not found, creating...${NC}"
        cat > "$HOME/.config/systemd/user/nightswitch.service" << EOF
[Unit]
Description=Nightswitch Theme Switching Utility
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/env nightswitch --minimized
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=graphical-session.target
EOF
        systemctl --user daemon-reload
        systemctl --user enable nightswitch.service
    fi
    
    echo -e "${GREEN}Autostart setup complete!${NC}"
    echo -e "${YELLOW}Nightswitch will now start automatically when you log in.${NC}"
}

# Function to disable autostart
disable_autostart() {
    echo -e "${BLUE}Disabling Nightswitch autostart...${NC}"
    
    # Remove desktop file from autostart
    if [ -f "$HOME/.config/autostart/me.pygillier.Nightswitch.desktop" ]; then
        echo -e "${YELLOW}Removing desktop autostart entry...${NC}"
        rm -f "$HOME/.config/autostart/me.pygillier.Nightswitch.desktop"
    fi
    
    # Disable systemd service
    if systemctl --user list-unit-files | grep -q nightswitch.service; then
        echo -e "${YELLOW}Disabling systemd service...${NC}"
        systemctl --user disable --now nightswitch.service 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Autostart disabled!${NC}"
    echo -e "${YELLOW}Nightswitch will no longer start automatically when you log in.${NC}"
}

# Parse command line arguments
ACTION="enable"  # Default action

for arg in "$@"; do
    case $arg in
        --disable)
            ACTION="disable"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --disable    Disable Nightswitch autostart"
            echo "  --help       Show this help message"
            echo ""
            echo "By default, this script enables Nightswitch to start automatically at login."
            exit 0
            ;;
    esac
done

# Execute requested action
if [ "$ACTION" == "enable" ]; then
    enable_autostart
else
    disable_autostart
fi

echo -e "${BLUE}======================================${NC}"