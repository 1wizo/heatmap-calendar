#!/bin/bash
# install.sh - Install the Heatmap Calendar widget (Wayland-native version)
# Run: bash install.sh

set -e

echo "=== Heatmap Calendar - Wayland Installer ==="
echo ""

# Detect distro and install dependencies
install_deps() {
    if command -v pacman &>/dev/null; then
        echo "Detected: Arch Linux"
        echo "Installing dependencies (requires sudo)..."
        echo "  python-gobject    - PyGObject (Python GTK bindings)"
        echo "  gtk3              - GTK3 runtime"
        echo "  gtk-layer-shell   - Layer Shell protocol support"
        sudo pacman -S --needed --noconfirm python-gobject gtk3 gtk-layer-shell
    elif command -v apt-get &>/dev/null; then
        echo "Detected: Debian/Ubuntu"
        echo "Installing dependencies (requires sudo)..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-gi gir1.2-gtk-3.0 libgtk-layer-shell0 gir1.2-gtklayershell-0.1
    elif command -v dnf &>/dev/null; then
        echo "Detected: Fedora"
        echo "Installing dependencies (requires sudo)..."
        sudo dnf install -y python3-gobject gtk3 gtk-layer-shell
    elif command -v zypper &>/dev/null; then
        echo "Detected: openSUSE"
        echo "Installing dependencies (requires sudo)..."
        sudo zypper install -y python3-gobject gtk3 gtk-layer-shell
    else
        echo "WARNING: Could not detect package manager."
        echo "Please install manually:"
        echo "  Arch:    sudo pacman -S python-gobject gtk3 gtk-layer-shell"
        echo "  Ubuntu:  sudo apt install python3-gi gir1.2-gtk-3.0 libgtk-layer-shell0 gir1.2-gtklayershell-0.1"
        echo "  Fedora:  sudo dnf install python3-gobject gtk3 gtk-layer-shell"
        return 1
    fi
}

install_deps

# Create install directory
INSTALL_DIR="$HOME/.local/share/heatmap-calendar-wayland"
mkdir -p "$INSTALL_DIR"
cp calendar_widget.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/calendar_widget.py"

# Create config directory
mkdir -p "$HOME/.config/rainmeter-calendar"

# Create autostart entry
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/heatmap-calendar-wayland.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Heatmap Calendar (Wayland)
Comment=GitHub-style heatmap calendar widget (Wayland-native)
Exec=python3 $INSTALL_DIR/calendar_widget.py
Icon=view-calendar
Terminal=false
X-GNOME-Autostart-enabled=true
Categories=Utility;
EOF

echo ""
echo "=== Running self-test ==="
python3 "$INSTALL_DIR/calendar_widget.py" --check
TEST_RESULT=$?
if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "!!! Self-test failed. The widget may not work on this system. !!!"
    echo "!!! See the errors above. !!!"
    echo ""
    echo "Files are still installed; you can try running manually:"
    echo "  python3 $INSTALL_DIR/calendar_widget.py"
    exit 1
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Files installed:"
echo "  Widget:     $INSTALL_DIR/calendar_widget.py"
echo "  Config:     $HOME/.config/rainmeter-calendar/"
echo "  Autostart:  $AUTOSTART_DIR/heatmap-calendar-wayland.desktop"
echo ""
echo "Starting widget now..."
python3 "$INSTALL_DIR/calendar_widget.py" &
disown
echo ""
echo "The widget will auto-start on next login."
echo "Right-click the widget for options (Night Mode, Minimal Mode, Position, Max Clicks, Quit)."
echo ""
echo "Note: This version uses the Layer Shell protocol. It works on:"
echo "  - KDE Plasma 6 (Wayland)"
echo "  - Sway, Hyprland, Wayfire, labwc, River (wlroots-based)"
echo "  - Mir-based compositors"
echo "It does NOT work on GNOME (Mutter) or X11."
