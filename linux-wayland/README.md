# Heatmap Calendar — Wayland-Native Version

A desktop widget for **Wayland** that shows a monthly calendar as a GitHub-style
heatmap. Click today's cell to track a daily habit — each click increases the
green saturation proportionally, up to a configurable max.

This version uses the **Layer Shell protocol** (`wlr-layer-shell`), which is
the Wayland-native way to put widgets on the desktop layer. No X11, no XWayland,
no xprop — pure Wayland.

## Compositor support

| Compositor | Supported? |
|------------|-----------|
| KDE Plasma 6 (Wayland) | ✅ Yes |
| Sway | ✅ Yes |
| Hyprland | ✅ Yes |
| Wayfire | ✅ Yes |
| labwc | ✅ Yes |
| River | ✅ Yes |
| Mir-based compositors | ✅ Yes |
| GNOME (Mutter) | ❌ No (no layer-shell support by default) |
| X11 | ❌ No (use the Plasma/X11 version instead) |

## Features

- **Habits tracker:** Only today's cell can be clicked. Each click increases
  saturation (0 = off, max clicks = darkest green).
- **Configurable max clicks:** 1, 2, 3, 4, 5, 8, or 10 clicks per day.
- **Night mode:** Dark palette for dark wallpapers.
- **Minimal mode:** Hides background panel, title, weekdays, legend, buttons.
- **Persistence:** Toggled days + settings survive reboot. Stored in
  `~/.config/rainmeter-calendar/`.
- **Auto day rollover:** At midnight, the calendar rebuilds and today moves
  to the next day. Yesterday's clicks are locked in.
- **Layer Shell BOTTOM:** Widget stays below all normal windows (like wallpaper).
- **5 anchor positions:** Top-left, top-right, bottom-left, bottom-right, center.
  (Wayland doesn't allow apps to position themselves freely, so we use anchor
  presets instead of free dragging.)

## Requirements

- Python 3.6+
- PyGObject (`python3-gi`)
- GTK3
- gtk-layer-shell (+ its typelib)

## Installation

### Quick install

```bash
cd RainmeterCalendarWayland
bash install.sh
```

The script will:
1. Install dependencies via your package manager (Arch/Ubuntu/Fedora/openSUSE)
2. Copy the widget to `~/.local/share/heatmap-calendar-wayland/`
3. Create an autostart entry
4. **Run a self-test** to verify all dependencies + compositor support
5. Launch the widget if the self-test passes

### Verify before installing (recommended)

You can run the self-test without installing anything:

```bash
python3 calendar_widget.py --check
```

This checks:
1. Python version ≥ 3.6
2. PyGObject installed
3. GTK3 available
4. GtkLayerShell typelib available
5. Compositor supports layer-shell protocol
6. Config directory is writable

If all 6 checks pass, the widget will work. If any fail, the output tells you
exactly what to install.

### Manual install

```bash
# Install deps (Arch)
sudo pacman -S python-gobject gtk3 gtk-layer-shell

# Or Ubuntu/Debian
sudo apt install python3-gi gir1.2-gtk-3.0 libgtk-layer-shell0 gir1.2-gtklayershell-0.1

# Or Fedora
sudo dnf install python3-gobject gtk3 gtk-layer-shell

# Copy widget
mkdir -p ~/.local/share/heatmap-calendar-wayland
cp calendar_widget.py ~/.local/share/heatmap-calendar-wayland/
chmod +x ~/.local/share/heatmap-calendar-wayland/calendar_widget.py

# Run it
python3 ~/.local/share/heatmap-calendar-wayland/calendar_widget.py
```

## Usage

| Action                    | Effect                                              |
| ------------------------- | -------------------------------------------------- |
| **Left-click today's cell** | Increment today's click count (+1 saturation)    |
| **Left-click other days**   | Ignored (only today can be clicked)              |
| **Right-click the widget**  | Open context menu                                  |
| **Menu → Night Mode**       | Toggle dark/light palette                          |
| **Menu → Minimal Mode**     | Toggle calendar-only mode (no background)         |
| **Menu → Position**         | Set anchor corner (top-left, top-right, bottom-left, bottom-right, center) |
| **Menu → Max Clicks**       | Set max clicks per day (1, 2, 3, 4, 5, 8, 10)    |
| **Menu → Quit**             | Close the widget                                   |

## Why no free dragging?

Wayland (by design) doesn't let apps:
- Position themselves globally (compositor controls placement)
- Get global mouse coordinates (security feature)

So instead of free dragging, this widget uses **anchor presets**. Right-click →
Position → pick a corner. The widget snaps to that corner with a 20px margin
from the screen edges.

If you want fine-tuned positioning, edit the `margin = 20` line in
`calendar_widget.py` (in `apply_layer_shell_anchor()`) to adjust the offset.

## Config files

```
~/.config/rainmeter-calendar/
├── toggled_days.txt    # One line per toggled day: "YYYY-MM-DD:count"
└── settings.txt        # nightMode, minimalMode, maxClicks, anchorCorner
```

### `toggled_days.txt` format
```
2026-07-08:4
2026-07-09:3
2026-07-10:2
2026-07-11:1
```

### `settings.txt` format
```
nightMode=1
minimalMode=1
maxClicks=4
anchorCorner=bottom-right
```

## Autostart

The install script creates `~/.config/autostart/heatmap-calendar-wayland.desktop`,
which launches the widget on login. To disable autostart, delete that file.

## Troubleshooting

**Widget doesn't appear:**
```bash
python3 ~/.local/share/heatmap-calendar-wayland/calendar_widget.py --check
```
Run the self-test to see what's wrong.

**"Layer Shell not supported":**
You're either on X11 or on a compositor that doesn't support layer-shell
(GNOME/Mutter). For GNOME, you'd need a third-party extension. For X11,
use the Plasma/X11 version instead.

**Widget is opaque (no transparency):**
Make sure your compositor's compositor is enabled. On Sway/Hyprland it's on
by default. On Plasma 6 Wayland: System Settings → Display & Monitor →
Compositor → enable.

**Widget appears above other windows:**
This shouldn't happen — the widget uses `Layer.BOTTOM`. If it does, your
compositor may have a bug. Try toggling Night Mode (right-click → Night Mode)
to force a redraw.

**Can't move the widget:**
Wayland doesn't allow free window positioning. Use the right-click → Position
menu to snap to a corner. To change the margin from the screen edge, edit
`margin = 20` in `calendar_widget.py`.

**Clicks don't register:**
Layer-shell windows with `KeyboardMode.NONE` should still receive mouse
events. If clicks aren't working, try changing `KeyboardMode.NONE` to
`KeyboardMode.ON_DEMAND` in `calendar_widget.py` (requires protocol v4+).

## Customization

Edit `calendar_widget.py` and change the constants at the top:

```python
CELL_SIZE = 46      # cell size in pixels
CELL_GAP = 4        # gap between cells
GRID_X = 18         # grid left offset
GRID_Y = 72         # grid top offset
WIDGET_W = 380      # widget width
WIDGET_H_FULL = 430 # widget height (normal mode)
WIDGET_H_MINIMAL = 374 # widget height (minimal mode)
```

To change the green palette:
```python
LIGHT_GREEN_START = (155, 233, 168)  # lightest green
LIGHT_GREEN_END   = (33, 110, 57)    # darkest green
DARK_GREEN_START  = (14, 68, 41)     # dimmest green
DARK_GREEN_END    = (63, 218, 122)   # brightest green
```

## Differences from the Plasma/X11 version

| Feature | Plasma/X11 version | Wayland version |
|---------|-------------------|-----------------|
| Window layering | `xprop` + `_NET_WM_STATE_BELOW` | `GtkLayerShell.Layer.BOTTOM` |
| Positioning | Free drag (when enabled) | Anchor presets (5 corners) |
| Backend | PyQt5 + XWayland | PyGObject + GTK3 (native Wayland) |
| Compositor | KWin (Plasma) | Any layer-shell compositor |
| GNOME support | ❌ No | ❌ No (GNOME doesn't support layer-shell) |
| X11 support | ✅ Yes (via XWayland) | ❌ No |
