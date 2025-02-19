#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Uninstalling kbsplitter...${NC}"

# Remove application files
echo -e "${YELLOW}Removing application files...${NC}"
sudo rm -rf /opt/kbsplitter

# Remove desktop entry
echo -e "${YELLOW}Removing desktop entry...${NC}"
sudo rm -f /usr/share/applications/kbsplitter.desktop

# Remove udev rule
echo -e "${YELLOW}Removing udev rule...${NC}"
sudo rm -f /etc/udev/rules.d/99-input.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Remove PolicyKit policy
echo -e "${YELLOW}Removing PolicyKit policy...${NC}"
sudo rm -f /usr/share/polkit-1/actions/org.kbsplitter.policy

# Optionally remove dependencies
read -p "Do you want to remove dependencies? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing dependencies...${NC}"
    if [ -f "/etc/arch-release" ]; then
        # Arch Linux
        if command -v yay &> /dev/null; then
            yay -Rns python-libevdev python-gobject gtk3
        else
            sudo pacman -Rns python-libevdev python-gobject gtk3
        fi
    elif command -v apt &> /dev/null; then
        # Debian/Ubuntu
        sudo apt remove -y python3-libevdev python3-gi python3-gi-cairo gir1.2-gtk-3.0
        sudo apt autoremove -y
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf remove -y python3-libevdev python3-gobject gtk3
        sudo dnf autoremove -y
    else
        echo -e "${YELLOW}Please remove the following packages manually if no longer needed:${NC}"
        echo "- python-libevdev"
        echo "- python-gobject"
        echo "- gtk3"
    fi
fi

echo -e "${GREEN}Uninstallation complete!${NC}" 