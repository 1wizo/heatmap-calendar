# GitHub Heatmap Calendar — Rainmeter Skin (v4)

A single-month calendar widget for Rainmeter styled after the GitHub contribution
heatmap — designed as a **daily habits tracker**.

## How it works

- Every day starts **OFF** (white).
- **Only today can be toggled** on (green) or off (white). Clicking past or
  future days is silently ignored — no backfilling, no pre-committing. That's
  the habits-tracker discipline: you can only check off *today*.
- The "Toggle Today" button does the same as clicking today's cell.
- Toggled days persist in `toggledDays.txt` next to the skin.
- **Night Mode** + **Minimal Mode** settings persist in `settings.txt`.
- At midnight, the calendar auto-rebuilds and today moves to the next day.
  Yesterday's toggle stays green (it's saved by date), you just can't
  untoggle it anymore.

## Modes

### Normal mode (default)
Shows the full widget: month title, today badge, weekday headers, 6×7 calendar
grid, "Off | On" legend, Night Mode button, Toggle Today button.

### Minimal mode
Right-click → **Toggle Minimal Mode**. Hides *everything* except the 42 calendar
cells + today's border:
- No background panel (transparent — blends with your wallpaper)
- No month title
- No "Today: N" badge
- No weekday headers (Sun, Mon, ...)
- No day numbers on cells
- No legend
- No buttons

You're left with just a floating 6×7 grid of small rectangles. Untoggled days
show as subtle translucent white tiles (~30% opacity) — visible as soft
rectangles on any wallpaper but not jarring. Toggled days show as solid green.
Today has a blue border. The widget shrinks to 380×374 px. Click any cell to
toggle today (other days are still blocked by the habits rule). To exit minimal
mode, right-click anywhere on the widget → "Toggle Minimal Mode" again.

### Night mode
Right-click → **Toggle Night Mode** (or click the Night Mode button in normal
mode). Switches to a GitHub-dark palette: in normal mode the panel becomes
dark (`#0d1117`) with light text; toggled days are bright green (`#3fda7a`).
In minimal mode, night mode just changes the today border to light blue
(since off cells are already transparent in both modes).

## Files

```
RainmeterCalendar/
├── calendar.ini              # the skin (generated, ~1200 lines, 42 cells)
├── calendar.lua              # controller (toggle logic, persistence, themes)
├── README.md                 # this file
├── toggledDays.txt           # auto-created on first toggle (one date per line)
├── settings.txt              # auto-created on first settings change
└── @Resources/               # PNG images for cells (light + dark themes)
    ├── cellOff.png           # light: white cell (untoggled)
    ├── cellOn.png            # light: green cell (toggled)
    ├── cellEmpty.png         # light: very light gray (prev/next month)
    ├── todayBorder.png       # light: blue border overlay for today
    ├── cellOffDark.png       # dark: dark gray cell (untoggled)
    ├── cellOnDark.png        # dark: bright green cell (toggled)
    ├── cellEmptyDark.png     # dark: darker gray (prev/next month)
    ├── todayBorderDark.png   # dark: light blue border overlay for today
    ├── legendOff.png         # 12x12 light off swatch
    ├── legendOn.png          # 12x12 light on swatch
    ├── legendOffDark.png     # 12x12 dark off swatch
    └── legendOnDark.png      # 12x12 dark on swatch
```

## Requirements

- Rainmeter 4.3 or newer.
- Windows (Rainmeter itself is Windows-only).

## Installation

1. Double-click the `.rmskin` file (or copy the `RainmeterCalendar` folder into
   `Documents\Rainmeter\Skins\`).
2. Open Rainmeter → Manage → expand `RainmeterCalendar` → double-click `calendar`.
3. Drag the widget to wherever you like.

## Usage

| Action                              | Effect                                              |
| ----------------------------------- | -------------------------------------------------- |
| **Click today's cell**               | Toggle today on (green) or off (white).            |
| **Click any other day cell**         | Ignored — only today can be toggled.               |
| **Click "Toggle Today" button**      | Same as clicking today's cell.                     |
| **Click "Night Mode" button**        | Switch between light and dark palettes.            |
| **Right-click → Toggle Today**       | Same as the button.                                |
| **Right-click → Toggle Night Mode**  | Same as the button.                                |
| **Right-click → Toggle Minimal Mode**| Hide buttons + legend for clean calendar-only look.|
| **Right-click → Reload data + settings** | Re-reads `toggledDays.txt` + `settings.txt`.   |
| **Right-click → Refresh skin**       | Full refresh.                                       |

## Persistence

### `toggledDays.txt`
Plain UTF-8 text, one date per line in `YYYY-MM-DD` format. Example:
```
2026-07-08
2026-07-09
2026-07-10
```
Edit by hand in any text editor, then right-click → "Reload data + settings".

### `settings.txt`
Two lines:
```
nightMode=0
minimalMode=0
```
Values are `0` (off) or `1` (on). Edit by hand or use the buttons/menu.

## Memory / rollover behavior

- **Day rollover:** The skin ticks every 1 second. At midnight, `Update()`
  detects the day change and rebuilds the calendar automatically. The today
  border moves to the new day, the badge updates, and the new day is toggleable.
  Yesterday's toggle stays green (saved by full date), but you can no longer
  untoggle it.
- **Month rollover:** Same mechanism. The entire 6×7 grid rebuilds for the
  new month, title updates ("August 2026"), and previous month's toggles
  are dormant (saved but not shown until you navigate back — currently the
  widget always shows the current month).
- **Power off / reboot:** Every toggle is written to `toggledDays.txt` the
  instant it happens. Every mode change is written to `settings.txt` the
  instant it happens. On next launch, both files are read back before
  rendering. Nothing is lost.

## TROUBLESHOOTING

If the widget shows blank or behaves oddly:

1. Right-click the Rainmeter tray icon → **Log** to open the log window.
2. Right-click the widget → **Refresh skin**.
3. The Lua script logs every action with `INFO` level and errors with `ERROR`.
   You should see lines like:
   ```
   Initialize: START
   LoadSettings: nightMode=false minimalMode=false
   LoadToggledDays: loaded 3 toggled day(s)
   BuildCalendar: START
   BuildCalendar: todayCellIndex=12
   BuildCalendar: DONE - title="July 2026"
   Initialize: SUCCESS
   ToggleDay: turned ON 2026-07-11
   SaveToggledDays: saved 4 toggled day(s)
   ```
4. If you try to toggle a non-today cell, you'll see:
   ```
   ToggleDay: ignored (cell 5 / day 4 is not today). Only today can be toggled.
   ```
5. If you see `Initialize ERROR: <message>`, that's the Lua error. Common causes:
   - `toggledDays.txt` or `settings.txt` is read-only or locked
   - The `@Resources` folder is missing or renamed (must be exactly `@Resources`)
   - Rainmeter version is older than 4.3 (Help → About to check)

## Customization

### Change the "ON" color

Edit `gen_images.py` and change the RGB tuple for `cellOn.png` and
`cellOnDark.png`, then regenerate:
```bash
python3 gen_images.py
```

### Change cell size

Edit the layout constants at the top of both:
- `gen_rainmeter_ini.py` (`CELL_SIZE`, `CELL_GAP`, etc.)
- `calendar.lua` (`CELL_SIZE`, `CELL_GAP`, `GRID_X`, `GRID_Y`)

Then regenerate:
```bash
python3 gen_rainmeter_ini.py
```

### Reset all toggles

Delete `toggledDays.txt` (or empty it) and refresh the skin.

### Reset settings

Delete `settings.txt` (or empty it) and refresh the skin.

### Manually toggle a past date (override the lock)

Open `toggledDays.txt` in Notepad, add a line like `2026-07-04`, save,
right-click widget → "Reload data + settings". The date will now show as
toggled green (even though you couldn't have clicked it).
