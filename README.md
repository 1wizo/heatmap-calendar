# Heatmap Calendar

A desktop calendar widget that looks like the GitHub contribution heatmap, repurposed as a **daily habits tracker**. Click today's cell to log a habit. Each click makes it greener. Yesterday locks in. After a week you see exactly which days you followed through.

## Which version do I download?

| Your setup | Download | How to install |
|------------|----------|----------------|
| **Windows** | `RainmeterCalendar.rmskin` | Double-click the file (needs [Rainmeter](https://www.rainmeter.net/) 4.3+) |
| **Linux KDE Plasma** (X11 or XWayland) | `RainmeterCalendarPlasma.tar.gz` | Extract → `bash install.sh` |
| **Linux Wayland** (Sway / Hyprland / Wayfire / labwc / River / KDE Plasma 6 native) | `RainmeterCalendarWayland.tar.gz` | Extract → `bash install.sh` |
| **GNOME (Mutter)** | — | Not supported (GNOME doesn't allow desktop widgets without extensions) |

//**btw the wayland version is not tested, so if u encounter any issues lemme know**

Get them all from the [Releases page](../../releases/latest).

## How to use

1. Install (see above)
2. The widget appears at the bottom-right of your desktop
3. **Left-click today's cell** to log a habit (each click = +1 saturation)
4. **Right-click the widget** for options:
   - Night Mode (dark palette)
   - Minimal Mode (just the calendar, no buttons/title)
   - Max Clicks per day (1, 2, 3, 4, 5, 8, 10)
   - Position / Quit

Only today can be clicked — past days are locked. Yesterday's count stays green forever.

## Config files

Stored in `~/.config/rainmeter-calendar/` (Linux) or `Documents\Rainmeter\Skins\RainmeterCalendar\` (Windows):

- **`toggled_days.txt`** — one line per toggled day: `2026-07-15:3` (date:click_count)
- **`settings.txt`** — `nightMode=1`, `minimalMode=0`, `maxClicks=4`, etc.

Edit these in any text editor. Your data survives reboots.

## Source code

Each version lives in its own folder:

- [`windows/`](windows/) — Rainmeter skin (`.ini` + `.lua` + PNG images)
- [`linux-plasma/`](linux-plasma/) — PyQt5 widget (single Python file)
- [`linux-wayland/`](linux-wayland/) — PyGObject + gtk-layer-shell widget (single Python file)

Each folder has its own `README.md` with details.

## License

MIT — see [LICENSE](LICENSE).

## important: AI is heavily used here
