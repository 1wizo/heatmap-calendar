#!/usr/bin/env python3
"""
Wayland-native version of the GitHub Heatmap Calendar widget.

Uses gtk-layer-shell (the wlr-layer-shell protocol) for proper Wayland
desktop-widget behavior:
  - Window appears on the BOTTOM layer (below normal windows)
  - No taskbar entry, no window decorations
  - Transparent background works on all Wayland compositors that support
    layer-shell
  - Anchored to a screen corner (configurable via right-click menu)

Works on:
  - KDE Plasma 6 (Wayland)
  - wlroots-based: Sway, Hyprland, Wayfire, labwc, River
  - Mir-based compositors
Does NOT work on:
  - GNOME (Mutter) — no layer-shell support by default
  - X11 (use the Plasma/X11 version instead)

Requires:
  - python3-gi (PyGObject)
  - gtk3
  - gtk-layer-shell (+ its typelib)

Install deps (Arch):       sudo pacman -S python-gobject gtk3 gtk-layer-shell
Install deps (Ubuntu):     sudo apt install python3-gi gir1.2-gtk-3.0 libgtk-layer-shell0 gir1.2-gtklayershell-0.1
Install deps (Fedora):     sudo dnf install python3-gobject gtk3 gtk-layer-shell

Self-test (no GUI):        python3 calendar_widget.py --check
"""

import sys
import os
import calendar as cal_mod
from datetime import datetime
from pathlib import Path

# ===== Self-test mode (--check) =====
# Verifies all dependencies without launching a GUI. Exits 0 on success,
# non-zero on failure. Run this BEFORE installing on a new system.
def self_test():
    print("=== Heatmap Calendar Wayland - Self Test ===")
    print()
    failures = 0

    # Check 1: Python version
    print("[1/6] Python version...")
    if sys.version_info >= (3, 6):
        print(f"  OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    else:
        print(f"  FAIL: Need Python 3.6+, got {sys.version_info.major}.{sys.version_info.minor}")
        failures += 1

    # Check 2: gi (PyGObject)
    print("[2/6] PyGObject (python3-gi)...")
    gi_available = False
    try:
        import gi
        gi_available = True
        print(f"  OK: gi version {gi.__version__}")
    except ImportError:
        print("  FAIL: PyGObject not installed")
        print("        Arch:    sudo pacman -S python-gobject")
        print("        Ubuntu:  sudo apt install python3-gi")
        print("        Fedora:  sudo dnf install python3-gobject")
        failures += 1

    # If gi isn't available, skip checks 3/4/5 (they all depend on gi)
    if not gi_available:
        for skip_check in [3, 4, 5]:
            names = {3: 'GTK3', 4: 'GtkLayerShell typelib', 5: 'Compositor layer-shell support'}
            print(f"[{skip_check}/6] {names[skip_check]}...")
            print("  SKIP: PyGObject not installed (install python3-gi first)")
        print()
        print("=== 1 CHECK FAILED (PyGObject missing) - install it and re-run --check ===")
        sys.exit(1)

    # Check 3: GTK3
    print("[3/6] GTK3...")
    gtk_available = False
    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        gtk_available = True
        print(f"  OK: GTK {Gtk._version}")
    except Exception as e:
        print(f"  FAIL: {e}")
        print("        Arch:    sudo pacman -S gtk3")
        print("        Ubuntu:  sudo apt install gir1.2-gtk-3.0")
        print("        Fedora:  sudo dnf install gtk3")
        failures += 1

    # Check 4: GtkLayerShell bindings
    print("[4/6] GtkLayerShell typelib...")
    gls_available = False
    try:
        gi.require_version('GtkLayerShell', '0.1')
        from gi.repository import GtkLayerShell
        gls_available = True
        print("  OK: GtkLayerShell 0.1 typelib found")
    except Exception as e:
        print(f"  FAIL: {e}")
        print("        Arch:    sudo pacman -S gtk-layer-shell")
        print("        Ubuntu:  sudo apt install gir1.2-gtklayershell-0.1")
        print("        Fedora:  sudo dnf install gtk-layer-shell")
        failures += 1

    # Check 5: Compositor support (layer-shell protocol)
    print("[5/6] Compositor layer-shell support...")
    if not (gtk_available and gls_available):
        print("  SKIP: GTK3 or GtkLayerShell not available (fix those first)")
        failures += 1
    else:
        try:
            from gi.repository import GtkLayerShell
            # is_supported() may block for a Wayland roundtrip on first call
            supported = GtkLayerShell.is_supported()
            if supported:
                print("  OK: Compositor supports zwlr_layer_shell_v1")
            else:
                session = os.environ.get('XDG_SESSION_TYPE', 'unknown')
                print(f"  FAIL: Layer shell not supported (session type: {session})")
                if session == 'x11':
                    print("        You're on X11. Use the Plasma/X11 version instead.")
                elif session == 'wayland':
                    print("        You're on Wayland but the compositor doesn't support")
                    print("        layer-shell. GNOME/Mutter doesn't support it by default.")
                    print("        Supported: KDE Plasma 6, Sway, Hyprland, Wayfire, labwc, River.")
                else:
                    print("        Make sure you're running a Wayland session.")
                failures += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failures += 1

    # Check 6: Config directory writability
    print("[6/6] Config directory writability...")
    config_dir = Path.home() / '.config' / 'rainmeter-calendar'
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        test_file = config_dir / '.write_test'
        test_file.write_text('ok')
        test_file.unlink()
        print(f"  OK: {config_dir} is writable")
    except Exception as e:
        print(f"  FAIL: Cannot write to {config_dir}: {e}")
        failures += 1

    print()
    if failures == 0:
        print("=== ALL CHECKS PASSED - widget should work ===")
        sys.exit(0)
    else:
        print(f"=== {failures} CHECK(S) FAILED - fix the issues above ===")
        sys.exit(1)


# Run self-test if --check argument is passed
if '--check' in sys.argv or '--self-test' in sys.argv:
    self_test()

# Handle --help and --version before attempting GTK imports
if '--help' in sys.argv or '-h' in sys.argv:
    print(f"Heatmap Calendar v6.1.0 (Wayland-native)")
    print()
    print("Usage: python3 calendar_widget.py [OPTION]")
    print()
    print("Options:")
    print("  (no args)   Launch the widget")
    print("  --check     Run self-test (verify deps + compositor support, no GUI)")
    print("  --help      Show this help message")
    print()
    print("The widget runs on Wayland compositors that support the layer-shell")
    print("protocol: KDE Plasma 6, Sway, Hyprland, Wayfire, labwc, River.")
    print("It does NOT work on GNOME (Mutter) or X11.")
    sys.exit(0)


# ===== Real imports (only after self-test passes) =====
# Wrap in try/except so users without deps get a helpful message instead of
# an ugly traceback. The --check mode gives detailed diagnostics.
try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
    import cairo
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print()
    print("Run the self-test for detailed diagnostics:")
    print(f"  python3 {sys.argv[0]} --check")
    sys.exit(1)
except ValueError as e:
    # gi.require_version raises ValueError if the version isn't available
    print(f"ERROR: {e}")
    print()
    print("Run the self-test for detailed diagnostics:")
    print(f"  python3 {sys.argv[0]} --check")
    sys.exit(1)

# ===== Config paths =====
CONFIG_DIR = Path.home() / '.config' / 'rainmeter-calendar'
DATA_FILE = CONFIG_DIR / 'toggled_days.txt'
SETTINGS_FILE = CONFIG_DIR / 'settings.txt'

# ===== Layout =====
CELL_SIZE = 46
CELL_GAP = 4
GRID_X = 18
GRID_Y = 72
WIDGET_W = 380
WIDGET_H_FULL = 430
WIDGET_H_MINIMAL = 374

# ===== Palette =====
LIGHT_GREEN_START = (155, 233, 168)   # #9be9a8
LIGHT_GREEN_END   = (33, 110, 57)     # #216e39
DARK_GREEN_START  = (14, 68, 41)      # #0e4429
DARK_GREEN_END    = (63, 218, 122)    # #3fda7a

NUM_LEVELS = 8

WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
MONTH_NAMES = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']

VERSION = "6.1.0"


# ===== State =====
class State:
    def __init__(self):
        self.night_mode = False
        self.minimal_mode = False
        self.max_clicks = 4
        self.anchor_corner = 'bottom-right'  # bottom-right, bottom-left, top-right, top-left, center
        self.day_counts = {}
        self.cells = []
        self.today_cell_index = 0
        self.current_year = 0
        self.current_month = 0
        self.current_day = 0
        self._last_day = None
        self._last_month = None

state = State()


# ===== Color helpers =====
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def count_to_level(count, max_clicks):
    if count <= 0:
        return 0
    if max_clicks <= 0:
        max_clicks = 1
    level = -(-(count * NUM_LEVELS) // max_clicks)  # ceil
    return max(1, min(NUM_LEVELS, level))

def get_cell_rgba(count, max_clicks, night):
    if count <= 0:
        if night:
            return (33/255, 38/255, 45/255, 200/255)
        else:
            return (1.0, 1.0, 1.0, 200/255)
    level = count_to_level(count, max_clicks)
    t = (level - 1) / (NUM_LEVELS - 1) if NUM_LEVELS > 1 else 0
    if night:
        rgb = lerp_color(DARK_GREEN_START, DARK_GREEN_END, t)
    else:
        rgb = lerp_color(LIGHT_GREEN_START, LIGHT_GREEN_END, t)
    return (rgb[0]/255, rgb[1]/255, rgb[2]/255, 1.0)

def date_key(year, month, day):
    return f"{year:04d}-{month:02d}-{day:02d}"

def today_key():
    now = datetime.now()
    return date_key(now.year, now.month, now.day)


# ===== Persistence =====
def load_settings():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        return
    for line in SETTINGS_FILE.read_text().splitlines():
        line = line.strip()
        if '=' in line:
            key, val = line.split('=', 1)
            if key == 'nightMode':
                state.night_mode = val in ('1', 'true')
            elif key == 'minimalMode':
                state.minimal_mode = val in ('1', 'true')
            elif key == 'maxClicks':
                try:
                    state.max_clicks = max(1, int(val))
                except ValueError:
                    pass
            elif key == 'anchorCorner':
                if val in ('bottom-right', 'bottom-left', 'top-right', 'top-left', 'center'):
                    state.anchor_corner = val

def save_settings():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"nightMode={'1' if state.night_mode else '0'}",
        f"minimalMode={'1' if state.minimal_mode else '0'}",
        f"maxClicks={state.max_clicks}",
        f"anchorCorner={state.anchor_corner}",
    ]
    SETTINGS_FILE.write_text('\n'.join(lines) + '\n')

def load_day_counts():
    if not DATA_FILE.exists():
        return
    for line in DATA_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            key, num = line.split(':', 1)
            try:
                n = int(num)
                if n > 0:
                    state.day_counts[key] = n
            except ValueError:
                pass
        else:
            # Old format (no colon) = 1 click. Validate it looks like a date.
            if len(line) == 10 and line[4] == '-' and line[7] == '-':
                try:
                    year = int(line[0:4])
                    month = int(line[5:7])
                    day = int(line[8:10])
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        state.day_counts[line] = 1
                except ValueError:
                    pass

def save_day_counts():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in sorted(state.day_counts.keys()):
        lines.append(f"{key}:{state.day_counts[key]}")
    DATA_FILE.write_text('\n'.join(lines) + '\n')


# ===== Calendar logic =====
def build_calendar():
    now = datetime.now()
    state.current_year = now.year
    state.current_month = now.month
    state.current_day = now.day

    first_weekday_mon0 = cal_mod.monthrange(now.year, now.month)[0]
    first_wday = (first_weekday_mon0 + 1) % 7
    days_in_month = cal_mod.monthrange(now.year, now.month)[1]

    state.cells = []
    state.today_cell_index = 0

    for i in range(42):
        day_num = i - first_wday + 1
        is_current = 1 <= day_num <= days_in_month
        is_today = is_current and day_num == now.day
        state.cells.append({
            'day': str(day_num) if is_current else '',
            'is_current_month': is_current,
            'is_today': is_today,
        })
        if is_today:
            state.today_cell_index = i

    state._last_day = now.day
    state._last_month = now.month


# ===== Widget =====
class CalendarWidget(Gtk.Window):
    def __init__(self):
        super().__init__()

        # Window setup: borderless, transparent
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        # Enable transparency (GTK3 RGBA visual)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        # Size
        self.set_default_size(WIDGET_W, WIDGET_H_FULL)
        if state.minimal_mode:
            self.set_size_request(WIDGET_W, WIDGET_H_MINIMAL)
        else:
            self.set_size_request(WIDGET_W, WIDGET_H_FULL)

        # Drawing area (single canvas, handles all rendering + clicks)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect('draw', self.on_draw)
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK
        )
        self.drawing_area.connect('button-press-event', self.on_button_press)
        self.add(self.drawing_area)

        # ===== Layer Shell setup (MUST be before show_all) =====
        # This is the Wayland-native way to put the widget on the desktop layer.
        try:
            GtkLayerShell.init_for_window(self)
            self.apply_layer_shell_anchor()
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
            GtkLayerShell.set_exclusive_zone(self, 0)
        except Exception as e:
            print(f"ERROR: Layer shell setup failed: {e}")
            print("Make sure you're on a Wayland session with layer-shell support.")
            sys.exit(1)

        # Timer: check for day rollover every 5 seconds
        GLib.timeout_add_seconds(5, self.on_tick)

        self.show_all()

        # Verify persistence is working
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            test_file = CONFIG_DIR / '.write_test'
            test_file.write_text('ok')
            test_file.unlink()
            persist_ok = True
        except Exception as e:
            persist_ok = False
            print(f"WARNING: Config dir not writable: {e}")

        print(f"=== Heatmap Calendar v{VERSION} (Wayland) ===")
        print(f"Config dir: {CONFIG_DIR} ({'writable' if persist_ok else 'NOT WRITABLE'})")
        print(f"Loaded {len(state.day_counts)} toggled day(s), "
              f"maxClicks={state.max_clicks}, "
              f"nightMode={'ON' if state.night_mode else 'OFF'}, "
              f"minimalMode={'ON' if state.minimal_mode else 'OFF'}, "
              f"anchor={state.anchor_corner}")
        print(f"Layer: BOTTOM (stays below normal windows)")

    def apply_layer_shell_anchor(self):
        """Set layer-shell anchors + margins based on state.anchor_corner."""
        # Clear all anchors first
        for edge in [GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT]:
            GtkLayerShell.set_anchor(self, edge, False)
            GtkLayerShell.set_margin(self, edge, 0)

        corner = state.anchor_corner
        margin = 20  # pixels from screen edge

        if corner == 'bottom-right':
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, margin)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, margin)
        elif corner == 'bottom-left':
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, margin)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, margin)
        elif corner == 'top-right':
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, margin)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, margin)
        elif corner == 'top-left':
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, margin)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, margin)
        elif corner == 'center':
            # No anchors = centered by compositor
            pass

    def on_tick(self):
        now = datetime.now()
        if state._last_day != now.day or state._last_month != now.month:
            build_calendar()
            self.drawing_area.queue_draw()
        return True

    # ===== Drawing =====
    def on_draw(self, widget, cr):
        # Background panel (hidden in minimal mode)
        if not state.minimal_mode:
            if state.night_mode:
                bg = (13/255, 17/255, 23/255, 1.0)
                border = (48/255, 54/255, 61/255, 1.0)
            else:
                bg = (1.0, 1.0, 1.0, 1.0)
                border = (208/255, 215/255, 222/255, 1.0)

            h = WIDGET_H_FULL
            self._rounded_rect(cr, 0, 0, WIDGET_W, h, 12)
            cr.set_source_rgba(*bg)
            cr.fill()
            self._rounded_rect(cr, 0, 0, WIDGET_W, h, 12)
            cr.set_source_rgba(*border)
            cr.set_line_width(1)
            cr.stroke()

            # Title
            title = f"{MONTH_NAMES[state.current_month-1]} {state.current_year}"
            text_c = self._text_color()
            self._draw_text(cr, title, 18, 14, text_c, 14, weight='bold')

            # Today badge
            tc = state.day_counts.get(today_key(), 0)
            badge = f"Day {state.current_day} ({tc}/{state.max_clicks})"
            badge_c = (88/255, 166/255, 255/255, 1.0) if state.night_mode else (9/255, 105/255, 218/255, 1.0)
            self._draw_text(cr, badge, WIDGET_W - 18, 18, badge_c, 10, align='right')

            # Weekday headers
            subtle = self._subtle_color()
            for i, day in enumerate(WEEKDAYS):
                x = GRID_X + i * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
                self._draw_text(cr, day, x, 50, subtle, 9, align='center')

            # Legend
            legend_y = 388 - 18
            self._draw_text(cr, "Off", WIDGET_W - 18 - 2*14 - 6, legend_y - 2, subtle, 8, align='right')
            off_c = get_cell_rgba(0, state.max_clicks, state.night_mode)
            cr.set_source_rgba(*off_c)
            self._rounded_rect(cr, WIDGET_W - 18 - 2*14, legend_y, 12, 12, 2)
            cr.fill()
            on_c = get_cell_rgba(state.max_clicks, state.max_clicks, state.night_mode)
            cr.set_source_rgba(*on_c)
            self._rounded_rect(cr, WIDGET_W - 18 - 14, legend_y, 12, 12, 2)
            cr.fill()
            self._draw_text(cr, "On", WIDGET_W - 18 + 2, legend_y - 2, subtle, 8)

        # Cells
        for i, cell in enumerate(state.cells):
            self._draw_cell(cr, i, cell)

        # Today border overlay
        if state.today_cell_index > 0:
            i = state.today_cell_index
            col = i % 7
            row = i // 7
            x = GRID_X + col * (CELL_SIZE + CELL_GAP)
            y = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            border_c = (88/255, 166/255, 255/255, 1.0) if state.night_mode else (9/255, 105/255, 218/255, 1.0)
            cr.set_source_rgba(*border_c)
            cr.set_line_width(3)
            self._rounded_rect(cr, x, y, CELL_SIZE, CELL_SIZE, 4)
            cr.stroke()

        return False

    def _draw_cell(self, cr, i, cell):
        if not cell['is_current_month']:
            return

        col = i % 7
        row = i // 7
        x = GRID_X + col * (CELL_SIZE + CELL_GAP)
        y = GRID_Y + row * (CELL_SIZE + CELL_GAP)

        key = date_key(state.current_year, state.current_month, int(cell['day']))
        count = state.day_counts.get(key, 0)
        rgba = get_cell_rgba(count, state.max_clicks, state.night_mode)

        cr.set_source_rgba(*rgba)
        self._rounded_rect(cr, x, y, CELL_SIZE, CELL_SIZE, 4)
        cr.fill()

        if cell['day']:
            text_c = self._text_color()
            self._draw_text(cr, cell['day'], x + CELL_SIZE // 2, y + 12, text_c, 10, weight='bold', align='center')

    def _rounded_rect(self, cr, x, y, w, h, r):
        cr.move_to(x + r, y)
        cr.line_to(x + w - r, y)
        cr.arc(x + w - r, y + r, r, -3.14159265/2, 0)
        cr.line_to(x + w, y + h - r)
        cr.arc(x + w - r, y + h - r, r, 0, 3.14159265/2)
        cr.line_to(x + r, y + h)
        cr.arc(x + r, y + h - r, r, 3.14159265/2, 3.14159265)
        cr.line_to(x, y + r)
        cr.arc(x + r, y + r, r, 3.14159265, 3*3.14159265/2)
        cr.close_path()

    def _draw_text(self, cr, text, x, y, color, size, weight='normal', align='left'):
        layout = PangoCairo.create_layout(cr)
        font_desc = Pango.FontDescription()
        font_desc.set_family('Sans')
        font_desc.set_size(size * Pango.SCALE)
        if weight == 'bold':
            font_desc.set_weight(Pango.Weight.BOLD)
        layout.set_font_description(font_desc)
        layout.set_text(text, -1)

        pw, ph = layout.get_pixel_size()

        if align == 'center':
            cr.move_to(x - pw/2, y)
        elif align == 'right':
            cr.move_to(x - pw, y)
        else:
            cr.move_to(x, y)

        cr.set_source_rgba(*color)
        PangoCairo.show_layout(cr, layout)

    def _text_color(self):
        return (230/255, 237/255, 243/255, 1.0) if state.night_mode else (31/255, 35/255, 40/255, 1.0)

    def _subtle_color(self):
        return (139/255, 148/255, 158/255, 1.0) if state.night_mode else (101/255, 109/255, 118/255, 1.0)

    # ===== Click handling =====
    def on_button_press(self, widget, event):
        if event.button == 1:  # Left click
            x, y = event.x, event.y
            for i, cell in enumerate(state.cells):
                col = i % 7
                row = i // 7
                cx = GRID_X + col * (CELL_SIZE + CELL_GAP)
                cy = GRID_Y + row * (CELL_SIZE + CELL_GAP)
                if cx <= x <= cx + CELL_SIZE and cy <= y <= cy + CELL_SIZE:
                    self.click_cell(i)
                    break
        elif event.button == 3:  # Right click
            self.show_context_menu(event)

    def click_cell(self, i):
        if i < 0 or i >= len(state.cells):
            return
        cell = state.cells[i]
        if not cell['is_current_month'] or not cell['is_today']:
            return  # silently ignore non-today clicks

        key = date_key(state.current_year, state.current_month, int(cell['day']))
        current = state.day_counts.get(key, 0)

        if current >= state.max_clicks:
            del state.day_counts[key]
        else:
            state.day_counts[key] = current + 1

        save_day_counts()
        self.drawing_area.queue_draw()

    # ===== Context menu =====
    def show_context_menu(self, event):
        menu = Gtk.Menu()

        def add_item(label, callback):
            item = Gtk.MenuItem(label=label)
            item.connect('activate', callback)
            menu.append(item)

        def add_separator():
            menu.append(Gtk.SeparatorMenuItem())

        add_item("Click Today (+1)", lambda w: self.click_cell(state.today_cell_index))
        add_separator()
        add_item(f"Night Mode ({'ON' if state.night_mode else 'OFF'})",
                 lambda w: self.toggle_night_mode())
        add_item(f"Minimal Mode ({'ON' if state.minimal_mode else 'OFF'})",
                 lambda w: self.toggle_minimal_mode())
        add_separator()

        # Position (anchor) submenu - Wayland-native way to move the widget
        pos_item = Gtk.MenuItem(label="Position")
        submenu = Gtk.Menu()
        for corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']:
            label = f"{corner} (current)" if corner == state.anchor_corner else corner
            sub = Gtk.MenuItem(label=label)
            sub.connect('activate', lambda w, c=corner: self.set_anchor(c))
            submenu.append(sub)
        pos_item.set_submenu(submenu)
        menu.append(pos_item)

        # Max clicks submenu
        max_item = Gtk.MenuItem(label="Max Clicks per Day")
        submenu = Gtk.Menu()
        for n in [1, 2, 3, 4, 5, 8, 10]:
            label = f"{n} (current)" if n == state.max_clicks else str(n)
            sub = Gtk.MenuItem(label=label)
            sub.connect('activate', lambda w, n=n: self.set_max_clicks(n))
            submenu.append(sub)
        max_item.set_submenu(submenu)
        menu.append(max_item)

        add_separator()
        add_item("Quit", lambda w: Gtk.main_quit())

        menu.show_all()
        menu.popup_at_pointer(event)

    # ===== Toggles =====
    def toggle_night_mode(self):
        state.night_mode = not state.night_mode
        save_settings()
        self.drawing_area.queue_draw()

    def toggle_minimal_mode(self):
        state.minimal_mode = not state.minimal_mode
        h = WIDGET_H_MINIMAL if state.minimal_mode else WIDGET_H_FULL
        self.set_size_request(WIDGET_W, h)
        # Re-apply anchor in case size affects layout
        self.apply_layer_shell_anchor()
        save_settings()
        self.drawing_area.queue_draw()

    def set_max_clicks(self, n):
        state.max_clicks = max(1, n)
        save_settings()
        self.drawing_area.queue_draw()

    def set_anchor(self, corner):
        state.anchor_corner = corner
        self.apply_layer_shell_anchor()
        save_settings()
        print(f"Position: {corner}")


# ===== Main =====
def main():
    # Pre-flight check: make sure layer-shell is supported before doing anything
    if not GtkLayerShell.is_supported():
        print("ERROR: Layer Shell protocol not supported by this compositor.")
        print("   Layer shell works on: KDE Plasma 6 (Wayland), Sway, Hyprland,")
        print("   Wayfire, labwc, River, Mir-based compositors.")
        print("   It does NOT work on: GNOME (Mutter), X11.")
        print()
        print("   If you're on GNOME, install the 'Add to Desktop' extension or")
        print("   use the X11/Plasma version instead.")
        print()
        print("   Run --check for a full diagnostic.")
        sys.exit(1)

    load_settings()
    load_day_counts()
    build_calendar()

    win = CalendarWidget()
    win.connect('destroy', Gtk.main_quit)
    Gtk.main()

if __name__ == '__main__':
    main()
