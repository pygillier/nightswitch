#!/bin/bash
# Nightswitch Installation Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}     Nightswitch Installation         ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv package manager not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Failed to install uv. Please install it manually:${NC}"
        echo -e "${YELLOW}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}uv installed successfully!${NC}"
fi

# Function to install dependencies
install_dependencies() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    
    # Check for GTK4 development libraries
    if command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}Detected apt package manager. Installing GTK4 dependencies...${NC}"
        sudo apt-get update
        sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 libgtk-4-dev
    elif command -v dnf &> /dev/null; then
        echo -e "${YELLOW}Detected dnf package manager. Installing GTK4 dependencies...${NC}"
        sudo dnf install -y python3-gobject gtk4-devel
    elif command -v pacman &> /dev/null; then
        echo -e "${YELLOW}Detected pacman package manager. Installing GTK4 dependencies...${NC}"
        sudo pacman -S --needed python-gobject gtk4
    else
        echo -e "${YELLOW}Could not detect package manager. Please install GTK4 dependencies manually.${NC}"
        echo -e "${YELLOW}Required packages: python3-gi, python3-gi-cairo, gir1.2-gtk-4.0${NC}"
    fi
}

# Function to install Nightswitch
install_nightswitch() {
    echo -e "${BLUE}Installing Nightswitch...${NC}"
    
    # Install the package
    if [ "$1" == "--user" ]; then
        echo -e "${YELLOW}Installing for current user only...${NC}"
        uv pip install --user -e .
        INSTALL_DIR="$HOME/.local"
    else
        echo -e "${YELLOW}Installing system-wide (requires sudo)...${NC}"
        sudo uv pip install -e .
        INSTALL_DIR="/usr"
    fi
    
    # Create desktop entry directory if it doesn't exist
    if [ "$1" == "--user" ]; then
        mkdir -p "$HOME/.local/share/applications"
        mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
        mkdir -p "$HOME/.config/autostart"
        
        # Copy desktop file
        cp data/me.pygillier.Nightswitch.desktop "$HOME/.local/share/applications/"
        
        # Copy desktop file to autostart directory
        cp data/me.pygillier.Nightswitch.desktop "$HOME/.config/autostart/"
        
        # Copy icon
        cp data/icons/me.pygillier.Nightswitch.svg "$HOME/.local/share/icons/hicolor/scalable/apps/"
        
        # Set up systemd user service
        mkdir -p "$HOME/.config/systemd/user"
        cp data/nightswitch.service "$HOME/.config/systemd/user/"
        systemctl --user daemon-reload
        systemctl --user enable nightswitch.service
        
        echo -e "${GREEN}Nightswitch installed successfully for current user!${NC}"
        echo -e "${GREEN}Application will start automatically on login.${NC}"
    else
        # System-wide installation
        sudo mkdir -p "/usr/share/applications"
        sudo mkdir -p "/usr/share/icons/hicolor/scalable/apps"
        
        # Copy desktop file
        sudo cp data/me.pygillier.Nightswitch.desktop "/usr/share/applications/"
        
        # Copy icon
        sudo cp data/icons/me.pygillier.Nightswitch.svg "/usr/share/icons/hicolor/scalable/apps/"
        
        # Set up systemd system service
        sudo cp data/nightswitch.service "/usr/lib/systemd/user/"
        sudo systemctl daemon-reload
        
        echo -e "${GREEN}Nightswitch installed successfully system-wide!${NC}"
        echo -e "${YELLOW}To enable autostart for your user, run:${NC}"
        echo -e "${YELLOW}cp /usr/share/applications/me.pygillier.Nightswitch.desktop ~/.config/autostart/${NC}"
    fi
}

# Function to uninstall Nightswitch
uninstall_nightswitch() {
    echo -e "${BLUE}Uninstalling Nightswitch...${NC}"
    
    # Remove the package
    if [ "$1" == "--user" ]; then
        uv pip uninstall -y nightswitch
        
        # Remove desktop files
        rm -f "$HOME/.local/share/applications/me.pygillier.Nightswitch.desktop"
        rm -f "$HOME/.config/autostart/me.pygillier.Nightswitch.desktop"
        
        # Remove icon
        rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/me.pygillier.Nightswitch.svg"
        
        # Disable and remove systemd service
        systemctl --user disable nightswitch.service
        systemctl --user stop nightswitch.service 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/nightswitch.service"
        systemctl --user daemon-reload
    else
        sudo uv pip uninstall -y nightswitch
        
        # Remove desktop files
        sudo rm -f "/usr/share/applications/me.pygillier.Nightswitch.desktop"
        
        # Remove icon
        sudo rm -f "/usr/share/icons/hicolor/scalable/apps/me.pygillier.Nightswitch.svg"
        
        # Remove systemd service
        sudo rm -f "/usr/lib/systemd/user/nightswitch.service"
        sudo systemctl daemon-reload
    fi
    
    echo -e "${GREEN}Nightswitch uninstalled successfully!${NC}"
}

# Parse command line arguments
INSTALL_TYPE="--user"  # Default to user installation
ACTION="install"       # Default action

for arg in "$@"; do
    case $arg in
        --system)
            INSTALL_TYPE="--system"
            shift
            ;;
        --user)
            INSTALL_TYPE="--user"
            shift
            ;;
        --uninstall)
            ACTION="uninstall"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --user      Install for current user only (default)"
            echo "  --system    Install system-wide (requires sudo)"
            echo "  --uninstall Uninstall Nightswitch"
            echo "  --help      Show this help message"
            exit 0
            ;;
    esac
done

# Execute requested action
if [ "$ACTION" == "install" ]; then
    install_dependencies
    install_nightswitch "$INSTALL_TYPE"
else
    uninstall_nightswitch "$INSTALL_TYPE"
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    echo -e "${BLUE}Updating icon cache...${NC}"
    if [ "$INSTALL_TYPE" == "--user" ]; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor"
    else
        sudo gtk-update-icon-cache -f -t "/usr/share/icons/hicolor"
    fi
fi

echo -e "${BLUE}======================================${NC}"
if [ "$ACTION" == "install" ]; then
    echo -e "${GREEN}Nightswitch installation complete!${NC}"
    echo -e "${YELLOW}You can start Nightswitch by running:${NC}"
    echo -e "${YELLOW}nightswitch${NC}"
    echo -e "${YELLOW}Or by searching for it in your application menu.${NC}"
    echo -e "${YELLOW}Nightswitch will also start automatically on login.${NC}"
else
    echo -e "${GREEN}Nightswitch uninstallation complete!${NC}"
fi
echo -e "${BLUE}======================================${NC}"