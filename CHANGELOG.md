# Changelog

## [6.1.0] - 2026-07-15
### Added
- Linux Wayland version using gtk-layer-shell (works on KDE Plasma 6, Sway, Hyprland, Wayfire, labwc, River)
- `--check` self-test mode for the Wayland version
- 5 anchor presets for positioning (Wayland doesn't allow free dragging)

## [6.0.0] - 2026-07-15
### Added (Linux Plasma version)
- Multi-click saturation: 8 green levels, configurable max clicks per day (1-10)
- "Allow Dragging" toggle in right-click menu
- XWayland forced via `QT_QPA_PLATFORM=xcb` so xprop can set window hints

### Fixed
- Window now stays below other windows (changed from DOCK to UTILITY window type)
- Drag glitching (throttled to 60 FPS)
- Persistence: old-format migration was too permissive

## [5.0.0] - 2026-07-14
### Added (Windows version)
- Multi-click saturation with configurable max clicks
- Click count shown in UI (`Day N (count/max)`)

### Fixed
- Persistence bug: file was using relative path, now uses absolute path via `SKIN:GetVariable('CURRENTPATH')`

## [4.0.0] - 2026-07-12
### Added (Windows version)
- Today-only toggling (habits-tracker mode — only today can be clicked)
- Minimal mode (hides all UI except the calendar grid)
- Settings persistence (`settings.txt`)

## [3.0.0] - 2026-07-12
### Added (Windows version)
- Toggle behavior (replaced random heatmap data with click-to-toggle)
- Night mode
- Persistence to `toggledDays.txt`
- Auto day rollover at midnight

## [1.0.0] - 2026-07-11
- Initial Windows version (Rainmeter skin)
