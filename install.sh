#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing kbsplitter${NC}"

# Check if running on Arch Linux
if [ -f "/etc/arch-release" ]; then
    echo -e "${YELLOW}Detected Arch Linux${NC}"
    
    # Check if yay is installed
    if ! command -v yay &> /dev/null; then
        echo -e "${YELLOW}Installing yay...${NC}"
        sudo pacman -S --needed git base-devel
        git clone https://aur.archlinux.org/yay.git
        cd yay
        makepkg -si
        cd ..
        rm -rf yay
    fi
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    yay -S --needed python-libevdev python-gobject gtk3
else
    # For other Linux distributions
    echo -e "${YELLOW}Installing dependencies...${NC}"
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3-libevdev python3-gi python3-gi-cairo gir1.2-gtk-3.0
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-libevdev python3-gobject gtk3
    else
        echo -e "${RED}Unsupported package manager. Please install the following packages manually:${NC}"
        echo "- python-libevdev"
        echo "- python-gobject"
        echo "- gtk3"
        exit 1
    fi
fi

# Create application directory
echo -e "${YELLOW}Creating application directory...${NC}"
sudo mkdir -p /opt/kbsplitter
sudo mkdir -p /opt/kbsplitter/config

# Copy files
echo -e "${YELLOW}Copying application files...${NC}"
sudo cp kbsplitter.py /opt/kbsplitter/
sudo cp kbsplitter_gui.py /opt/kbsplitter/
sudo cp -r config/* /opt/kbsplitter/config/

# Create desktop entry
echo -e "${YELLOW}Creating desktop entry...${NC}"
cat << EOF | sudo tee /usr/share/applications/kbsplitter.desktop
[Desktop Entry]
Name=kbsplitter
Comment=Map keyboard keys to Xbox controller
Exec=sudo python3 /opt/kbsplitter/kbsplitter_gui.py
Icon=input-gaming
Terminal=false
Type=Application
Categories=Game;Utility;
EOF

# Make files executable
echo -e "${YELLOW}Setting permissions...${NC}"
sudo chmod +x /opt/kbsplitter/kbsplitter.py
sudo chmod +x /opt/kbsplitter/kbsplitter_gui.py
sudo chmod 666 /dev/uinput

# Create udev rule for persistent permissions
echo -e "${YELLOW}Creating udev rule...${NC}"
cat << EOF | sudo tee /etc/udev/rules.d/99-input.rules
KERNEL=="uinput", SUBSYSTEM=="misc", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}You can now launch the application from your application menu or run 'sudo /opt/kbsplitter/kbsplitter_gui.py'${NC}" 