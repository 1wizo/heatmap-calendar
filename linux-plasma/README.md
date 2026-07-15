# Heatmap Calendar — KDE Plasma Version

A desktop widget for KDE Plasma that shows a monthly calendar as a GitHub-style
heatmap. Click today's cell to track a daily habit — each click increases
the green saturation proportionally, up to a configurable max.

This version uses **PyQt5** instead of GTK3, which integrates better with
KWin (Plasma's compositor) and respects Plasma's window management rules.

## Features

- **Habits tracker:** Only today's cell can be clicked. Each click increases
  saturation (0 = off, max clicks = darkest green).
- **Configurable max clicks:** 1, 2, 3, 4, 5, 8, or 10 clicks per day.
- **Night mode:** Dark palette for dark wallpapers.
- **Minimal mode:** Hides background panel, title, weekdays, legend, buttons.
- **Persistence:** Toggled days + settings survive reboot. Stored in
  `~/.config/rainmeter-calendar/`.
- **Auto day rollover:** At midnight, the calendar rebuilds automatically.
- **Plasma-friendly:** Uses Qt window flags that KWin respects:
  - No taskbar entry
  - No window decorations
  - Stays below normal windows
  - Transparent background
- **System tray icon:** Backup way to access the widget if it gets hidden.
- **Position presets:** Right-click → Position → Top-Left/Top-Right/Bottom-Left/Bottom-Right.

## Requirements

- Python 3.6+
- PyQt5

On Arch Linux: `sudo pacman -S python-pyqt5`
On Ubuntu/Kubuntu: `sudo apt install python3-pyqt5`
On Fedora KDE: `sudo dnf install python3-qt5`

## Installation

### Quick install

```bash
cd RainmeterCalendarPlasma
bash install.sh
```

The script will:
1. Install PyQt5 via your package manager
2. Copy the widget to `~/.local/share/heatmap-calendar/`
3. Create an autostart entry for Plasma
4. Launch the widget immediately

### Manual install

```bash
# Install PyQt5 (Arch)
sudo pacman -S python-pyqt5

# Copy widget
mkdir -p ~/.local/share/heatmap-calendar
cp calendar_widget.py ~/.local/share/heatmap-calendar/
chmod +x ~/.local/share/heatmap-calendar/calendar_widget.py

# Run it
python3 ~/.local/share/heatmap-calendar/calendar_widget.py
```

## Usage

| Action                    | Effect                                              |
| ------------------------- | -------------------------------------------------- |
| **Left-click today's cell** | Increment today's click count (+1 saturation)    |
| **Left-click other days**   | Ignored (only today can be clicked)              |
| **Right-click the widget**  | Open context menu                                  |
| **Menu → Night Mode**       | Toggle dark/light palette                          |
| **Menu → Minimal Mode**     | Toggle calendar-only mode (no background)         |
| **Menu → Max Clicks**       | Set max clicks per day (1, 2, 3, 4, 5, 8, 10)    |
| **Menu → Position**         | Snap to corner (Top-Left, Top-Right, etc.)        |
| **Menu → Quit**             | Close the widget                                   |
| **System tray icon**        | Click to show the widget if hidden                |

## Config files

```
~/.config/rainmeter-calendar/
├── toggled_days.txt    # One line per toggled day: "YYYY-MM-DD:count"
└── settings.txt        # nightMode, minimalMode, maxClicks
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
```

## Autostart

The install script creates `~/.config/autostart/heatmap-calendar.desktop`,
which launches the widget on login. To disable autostart, delete that file.

The .desktop file uses `X-KDE-autostart-phase=2` so it launches after
Plasma's desktop is fully loaded.

## Why a separate Plasma version?

The GTK3 version (in `RainmeterCalendarLinux/`) uses `Gdk.WindowTypeHint.DESKTOP`
which KWin handles poorly — the window may be hidden, placed on a separate
layer, or not respect keep-below hints.

This PyQt5 version uses Qt's window flags (`Qt.WindowStaysOnBottomHint`,
`Qt.Tool`, `Qt.FramelessWindowHint`) which KWin respects natively. It also
includes a system tray icon as a fallback so you can always access the
widget even if KWin does something weird with the window.

## Troubleshooting

**Widget doesn't appear after install:**
1. Check system tray (bottom-right) for a Play icon — click it to show the widget.
2. Run manually to see errors:
   ```bash
   python3 ~/.local/share/heatmap-calendar/calendar_widget.py
   ```
3. Make sure PyQt5 is installed:
   ```bash
   python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
   ```

**Widget appears above other windows:**
KWin may not respect `WindowStaysOnBottomHint` for some window types.
Open KWin Window Rules (System Settings → Window Management → Window Rules)
and create a rule for "Heatmap Calendar" that forces:
- Keep below: Yes
- No focus: Yes
- Skip taskbar: Yes
- Skip pager: Yes

**Widget is opaque (no transparency):**
Make sure Plasma's compositor is enabled:
System Settings → Display & Monitor → Compositor → enable "Compositing".

**Widget position resets on restart:**
The widget auto-positions to bottom-right on startup. To use a different
position permanently, edit `position_bottom_right()` in `calendar_widget.py`
or use the Position menu after each startup.

**Click-through doesn't work:**
KWin doesn't let apps set click-through on themselves. To enable click-through,
use KWin Window Rules:
System Settings → Window Management → Window Rules → Add New Rule
→ Window class: "Heatmap Calendar" → Add Property → "Accept focus: No"
→ Apply.

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

To change the green palette, edit:
```python
LIGHT_GREEN_START = QColor(155, 233, 168)  # lightest green
LIGHT_GREEN_END   = QColor(33, 110, 57)    # darkest green
DARK_GREEN_START  = QColor(14, 68, 41)     # dimmest green
DARK_GREEN_END    = QColor(63, 218, 122)   # brightest green
```
