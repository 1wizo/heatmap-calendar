#!/bin/bash
# install.sh - Install the Heatmap Calendar widget on KDE Plasma (Linux)
# Run: bash install.sh

set -e

echo "=== Heatmap Calendar - KDE Plasma Installer ==="
echo ""

# Detect distro and install dependencies
install_deps() {
    if command -v pacman &>/dev/null; then
        echo "Detected: Arch Linux"
        echo "Installing dependencies (requires sudo)..."
        echo "  python-pyqt5  - Qt5 bindings for Python (drawing + window)"
        echo "  qt5-wayland   - Wayland support for Qt5"
        echo "  xorg-xprop    - X11 window property setter (for desktop-layer hints)"
        sudo pacman -S --needed --noconfirm python-pyqt5 qt5-wayland xorg-xprop
    elif command -v apt-get &>/dev/null; then
        echo "Detected: Debian/Ubuntu (with KDE)"
        echo "Installing dependencies (requires sudo)..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-pyqt5 qtwayland5 x11-utils
    elif command -v dnf &>/dev/null; then
        echo "Detected: Fedora"
        echo "Installing dependencies (requires sudo)..."
        sudo dnf install -y python3-qt5 qt5-qtwayland xorg-x11-utils
    elif command -v zypper &>/dev/null; then
        echo "Detected: openSUSE"
        echo "Installing dependencies (requires sudo)..."
        sudo zypper install -y python3-qt5 libqt5-qtwayland xorg-x11-utils
    else
        echo "WARNING: Could not detect package manager."
        echo "Please install manually: PyQt5 + Qt5 Wayland + xprop"
        echo "  Arch:          sudo pacman -S python-pyqt5 qt5-wayland xorg-xprop"
        echo "  Ubuntu/Debian: sudo apt install python3-pyqt5 qtwayland5 x11-utils"
        echo "  Fedora:        sudo dnf install python3-qt5 qt5-qtwayland xorg-x11-utils"
        return 1
    fi
}

install_deps

# Kill any old instance of the widget that's still running
echo "Stopping any running instance..."
pkill -f "calendar_widget.py" 2>/dev/null || true
sleep 1

# Create install directory
INSTALL_DIR="$HOME/.local/share/heatmap-calendar"
mkdir -p "$INSTALL_DIR"
cp calendar_widget.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/calendar_widget.py"

# Create config directory
mkdir -p "$HOME/.config/rainmeter-calendar"

# Create autostart entry
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/heatmap-calendar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Heatmap Calendar
Comment=GitHub-style heatmap calendar widget
Exec=env QT_QPA_PLATFORM=xcb python3 $INSTALL_DIR/calendar_widget.py
Icon=view-calendar
Terminal=false
X-KDE-autostart-phase=2
X-GNOME-Autostart-enabled=true
Categories=Utility;
EOF

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Files installed:"
echo "  Widget:     $INSTALL_DIR/calendar_widget.py"
echo "  Config:     $HOME/.config/rainmeter-calendar/"
echo "  Autostart:  $AUTOSTART_DIR/heatmap-calendar.desktop"
echo ""
echo "Starting widget now (forcing XWayland mode for proper KWin hints)..."
echo ""
QT_QPA_PLATFORM=xcb python3 "$INSTALL_DIR/calendar_widget.py" &
disown
echo ""
echo "The widget will auto-start on next login."
echo "Right-click the widget for options."
echo ""
echo "IMPORTANT: If you see the old widget still running, run:"
echo "  pkill -f calendar_widget.py"
echo "then launch the new one manually:"
echo "  QT_QPA_PLATFORM=xcb python3 ~/.local/share/heatmap-calendar/calendar_widget.py"
