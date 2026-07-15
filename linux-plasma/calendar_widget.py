#!/usr/bin/env python3
"""
KDE Plasma version of the GitHub Heatmap Calendar widget.

Uses PyQt5 + xprop for proper Plasma/KWin integration:
  - Window appears below normal windows (desktop layer)
  - No taskbar entry, no window decorations
  - Draggable by clicking on empty space
  - Transparent background works with KWin compositor

IMPORTANT: This widget forces XWayland mode (QT_QPA_PLATFORM=xcb) because
xprop (an X11 tool) is used to set the window type to DOCK + state BELOW.
On native Wayland, xprop has no effect, so we must run under XWayland.

Requires: python-pyqt5, qt5-wayland, xorg-xprop
On Arch: sudo pacman -S python-pyqt5 qt5-wayland xorg-xprop
"""

import sys
import os

# Force XWayland (X11) mode BEFORE importing Qt.
# This is critical: xprop only works on X11 windows. On native Wayland,
# xprop is a no-op, so the window hints never get set and the widget
# appears above other windows and can't be dragged.
os.environ['QT_QPA_PLATFORM'] = 'xcb'

import subprocess
import calendar as cal_mod
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QWidget, QMenu, QAction,
                              QMessageBox, QStyle)
from PyQt5.QtCore import Qt, QTimer, QRect, QPointF
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QPainterPath,
                          QBrush, QGuiApplication, QIcon)

VERSION = "6.0.0"
print(f"=== Heatmap Calendar v{VERSION} (KDE Plasma) ===")
print(f"QT_QPA_PLATFORM = {os.environ.get('QT_QPA_PLATFORM', '(default)')}")
print(f"XDG_SESSION_TYPE = {os.environ.get('XDG_SESSION_TYPE', '(unknown)')}")

# Try to import KWindowSystem for Plasma-specific window hints.
# This requires the python-pykde5 package, which is NOT in Arch official repos
# anymore (it's in AUR). We don't make it a hard dependency - instead, we use
# a pure-Qt + subprocess approach (calling `qdbus` to talk to KWin) which needs
# zero extra packages.
KWindowSystem = None
NET = None
HAS_KWIN = False
try:
    from PyKDE5.kwindowsystem import KWindowSystem, NET
    HAS_KWIN = True
except ImportError:
    pass

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
LIGHT_GREEN_START = QColor(155, 233, 168)   # #9be9a8
LIGHT_GREEN_END   = QColor(33, 110, 57)     # #216e39
DARK_GREEN_START  = QColor(14, 68, 41)      # #0e4429
DARK_GREEN_END    = QColor(63, 218, 122)    # #3fda7a

NUM_LEVELS = 8

WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
MONTH_NAMES = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']


# ===== State =====
class State:
    def __init__(self):
        self.night_mode = False
        self.minimal_mode = False
        self.max_clicks = 4
        self.allow_drag = False         # drag disabled by default (no accidental moves)
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
def lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    return QColor(
        int(c1.red()   + (c2.red()   - c1.red())   * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue()  + (c2.blue()  - c1.blue())  * t),
    )

def count_to_level(count, max_clicks):
    if count <= 0:
        return 0
    if max_clicks <= 0:
        max_clicks = 1
    level = -(-(count * NUM_LEVELS) // max_clicks)  # ceil
    return max(1, min(NUM_LEVELS, level))

def get_cell_color(count, max_clicks, night):
    """Return QColor for a cell based on click count."""
    if count <= 0:
        if night:
            c = QColor(33, 38, 45)
            c.setAlpha(200)
            return c
        else:
            c = QColor(255, 255, 255)
            c.setAlpha(200)
            return c
    level = count_to_level(count, max_clicks)
    t = (level - 1) / (NUM_LEVELS - 1) if NUM_LEVELS > 1 else 0
    if night:
        return lerp_color(DARK_GREEN_START, DARK_GREEN_END, t)
    else:
        return lerp_color(LIGHT_GREEN_START, LIGHT_GREEN_END, t)

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
            elif key == 'allowDrag':
                state.allow_drag = val in ('1', 'true')
            elif key == 'maxClicks':
                try:
                    state.max_clicks = max(1, int(val))
                except ValueError:
                    pass

def save_settings():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"nightMode={'1' if state.night_mode else '0'}",
        f"minimalMode={'1' if state.minimal_mode else '0'}",
        f"allowDrag={'1' if state.allow_drag else '0'}",
        f"maxClicks={state.max_clicks}",
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
            # Old format (no colon) = 1 click. Validate it looks like a date
            # (YYYY-MM-DD = 10 chars) to avoid migrating garbage lines.
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
class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Window flags: no decorations, no taskbar, stay on top of desktop
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnBottomHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )

        # Transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # NOTE: Do NOT set WA_X11NetWmWindowTypeDesktop here - it conflicts
        # with the xprop hints we set later (UTILITY + BELOW).

        # Geometry
        self.setFixedSize(WIDGET_W, WIDGET_H_FULL)
        # NOTE: setMouseTracking is OFF (default). We only need move events
        # while a button is held down (during drag). With tracking ON, Qt
        # floods us with move events even when not dragging, causing
        # compositor glitches.
        self._dragging = False
        self._drag_start_global = None
        self._drag_start_window = None
        self._drag_last_move_time = 0

        # Load state
        load_settings()
        load_day_counts()
        build_calendar()

        # Apply saved minimal mode
        if state.minimal_mode:
            self.setFixedSize(WIDGET_W, WIDGET_H_MINIMAL)

        # Position: bottom-right of primary screen
        self.position_bottom_right()

        # Timer: check for day rollover every 5 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(5000)

        # Apply KWin-specific hints after window is shown
        self.show()
        QTimer.singleShot(100, self.apply_kwin_hints)

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

        print(f"Config dir: {CONFIG_DIR} ({'writable' if persist_ok else 'NOT WRITABLE'})")
        print(f"Loaded {len(state.day_counts)} toggled day(s), "
              f"maxClicks={state.max_clicks}, "
              f"nightMode={'ON' if state.night_mode else 'OFF'}, "
              f"minimalMode={'ON' if state.minimal_mode else 'OFF'}, "
              f"allowDrag={'ON' if state.allow_drag else 'OFF'}")

    def position_bottom_right(self):
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.width() - WIDGET_W - 20  # 20px margin from right edge
        y = screen.height() - self.height() - 60  # 60px margin from bottom (taskbar)
        self.move(x, y)

    def apply_kwin_hints(self):
        """Apply KWin-specific window hints to make the widget behave like
        part of the desktop (below all other windows, no taskbar entry).

        Strategy (in priority order):
        1. If PyKDE5 is available, use KWindowSystem directly (best)
        2. Otherwise, use `xprop` to set X11 window type to _NET_WM_WINDOW_TYPE_DESKTOP
           (works on X11 and XWayland)
        3. Print instructions for setting up a KWin Window Rule manually
           (works on pure Wayland)
        """
        wid = int(self.winId())

        # --- Strategy 1: PyKDE5 ---
        if HAS_KWIN:
            try:
                KWindowSystem.setOnAllDesktops(wid, True)
                states = (NET.SkipTaskbar | NET.SkipPager | NET.KeepBelow)
                KWindowSystem.setState(wid, states)
                try:
                    KWindowSystem.setType(wid, NET.Desktop)
                except Exception as e:
                    print(f"setType(Desktop) failed (non-fatal): {e}")
                print("KWin hints applied via KWindowSystem (PyKDE5)")
                return
            except Exception as e:
                print(f"KWindowSystem hints failed: {e}")

        # --- Strategy 2: xprop (X11 / XWayland) ---
        # Set window type to _NET_WM_WINDOW_TYPE_UTILITY + state BELOW.
        # UTILITY + BELOW = stays below normal windows AND accepts input.
        try:
            xprop_hex = hex(wid)
            if xprop_hex.startswith('0x0') and len(xprop_hex) > 4:
                xprop_hex = '0x' + xprop_hex[3:]

            # Set window type to UTILITY
            result = subprocess.run(
                ['xprop', '-id', xprop_hex,
                 '-f', '_NET_WM_WINDOW_TYPE', '32a',
                 '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_UTILITY'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"xprop set type failed: {result.stderr.strip()}")

            # Set state: BELOW + SKIP_TASKBAR + SKIP_PAGER
            subprocess.run(
                ['xprop', '-id', xprop_hex,
                 '-f', '_NET_WM_STATE', '32a',
                 '-set', '_NET_WM_STATE',
                 '_NET_WM_STATE_BELOW,_NET_WM_STATE_SKIP_TASKBAR,_NET_WM_STATE_SKIP_PAGER'],
                capture_output=True, text=True, timeout=5
            )

            # Remove WM_TRANSIENT_FOR (otherwise KWin may treat as dialog)
            subprocess.run(
                ['xprop', '-id', xprop_hex, '-remove', 'WM_TRANSIENT_FOR'],
                capture_output=True, text=True, timeout=5
            )

            # Set on all desktops (0xFFFFFFFF = all desktops)
            subprocess.run(
                ['xprop', '-id', xprop_hex,
                 '-f', '_NET_WM_DESKTOP', '32c',
                 '-set', '_NET_WM_DESKTOP', '0xFFFFFFFF'],
                capture_output=True, text=True, timeout=5
            )

            print("Window hints applied: UTILITY + BELOW (stays below other windows)")
            return
        except FileNotFoundError:
            print("ERROR: xprop not found. Install: sudo pacman -S xorg-xprop")
        except Exception as e:
            print(f"ERROR setting window hints: {e}")
            print("  Make sure QT_QPA_PLATFORM=xcb is set (XWayland mode).")

        # --- Strategy 3: Manual KWin Window Rule ---
        print("")
        print("=" * 60)
        print("Could not set desktop-layer hints automatically.")
        print("To make the widget stay below all other windows, create a")
        print("KWin Window Rule manually:")
        print("")
        print("1. Open System Settings -> Window Management -> Window Rules")
        print("2. Click 'Add New...' -> 'For window class'")
        print("3. Window class: 'Heatmap Calendar' (or 'calendar_widget.py')")
        print("4. Add these properties:")
        print("   - Keep below: Yes (Force)")
        print("   - Skip taskbar: Yes (Force)")
        print("   - Skip pager: Yes (Force)")
        print("   - No focus: Yes (Force)")
        print("5. Apply")
        print("")
        print("OR install xorg-xprop for automatic X11 hints:")
        print("  sudo pacman -S xorg-xprop")
        print("=" * 60)

    def on_tick(self):
        now = datetime.now()
        if state._last_day != now.day or state._last_month != now.month:
            build_calendar()
            self.update()
        return True

    # ===== Drawing =====
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Background panel (hidden in minimal mode)
        if not state.minimal_mode:
            if state.night_mode:
                bg = QColor(13, 17, 23)
                border = QColor(48, 54, 61)
            else:
                bg = QColor(255, 255, 255)
                border = QColor(208, 215, 222)

            h = WIDGET_H_FULL
            path = self._rounded_rect_path(0, 0, WIDGET_W, h, 12)
            painter.fillPath(path, bg)
            painter.setPen(QPen(border, 1))
            painter.drawPath(path)

            # Title
            title = f"{MONTH_NAMES[state.current_month-1]} {state.current_year}"
            text_c = self._text_color()
            self._draw_text(painter, title, 18, 14, text_c, 14, weight=QFont.Bold)

            # Today badge
            tc = state.day_counts.get(today_key(), 0)
            badge = f"Day {state.current_day} ({tc}/{state.max_clicks})"
            badge_c = QColor(88, 166, 255) if state.night_mode else QColor(9, 105, 218)
            self._draw_text(painter, badge, WIDGET_W - 18, 18, badge_c, 10, align='right')

            # Weekday headers
            subtle = self._subtle_color()
            for i, day in enumerate(WEEKDAYS):
                x = GRID_X + i * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
                self._draw_text(painter, day, x, 50, subtle, 9, align='center')

            # Legend
            legend_y = 388 - 18
            self._draw_text(painter, "Off", WIDGET_W - 18 - 2*14 - 6, legend_y - 2, subtle, 8, align='right')
            off_c = get_cell_color(0, state.max_clicks, state.night_mode)
            painter.fillPath(self._rounded_rect_path(WIDGET_W - 18 - 2*14, legend_y, 12, 12, 2), off_c)
            on_c = get_cell_color(state.max_clicks, state.max_clicks, state.night_mode)
            painter.fillPath(self._rounded_rect_path(WIDGET_W - 18 - 14, legend_y, 12, 12, 2), on_c)
            self._draw_text(painter, "On", WIDGET_W - 18 + 2, legend_y - 2, subtle, 8)

        # Cells
        for i, cell in enumerate(state.cells):
            self._draw_cell(painter, i, cell)

        # Today border overlay
        if state.today_cell_index > 0:
            i = state.today_cell_index
            col = i % 7
            row = i // 7
            x = GRID_X + col * (CELL_SIZE + CELL_GAP)
            y = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            border_c = QColor(88, 166, 255) if state.night_mode else QColor(9, 105, 218)
            painter.setPen(QPen(border_c, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self._rounded_rect_path(x, y, CELL_SIZE, CELL_SIZE, 4))

    def _draw_cell(self, painter, i, cell):
        if not cell['is_current_month']:
            return

        col = i % 7
        row = i // 7
        x = GRID_X + col * (CELL_SIZE + CELL_GAP)
        y = GRID_Y + row * (CELL_SIZE + CELL_GAP)

        key = date_key(state.current_year, state.current_month, int(cell['day']))
        count = state.day_counts.get(key, 0)
        color = get_cell_color(count, state.max_clicks, state.night_mode)

        painter.fillPath(self._rounded_rect_path(x, y, CELL_SIZE, CELL_SIZE, 4), color)

        if cell['day']:
            text_c = self._text_color()
            self._draw_text(painter, cell['day'], x + CELL_SIZE // 2, y + 12,
                          text_c, 10, weight=QFont.Bold, align='center')

    def _rounded_rect_path(self, x, y, w, h, r):
        path = QPainterPath()
        path.moveTo(x + r, y)
        path.lineTo(x + w - r, y)
        path.arcTo(x + w - 2*r, y, 2*r, 2*r, 90, -90)
        path.lineTo(x + w, y + h - r)
        path.arcTo(x + w - 2*r, y + h - 2*r, 2*r, 2*r, 0, -90)
        path.lineTo(x + r, y + h)
        path.arcTo(x, y + h - 2*r, 2*r, 2*r, 270, -90)
        path.lineTo(x, y + r)
        path.arcTo(x, y, 2*r, 2*r, 180, -90)
        path.closeSubpath()
        return path

    def _draw_text(self, painter, text, x, y, color, size, weight=QFont.Normal, align='left'):
        # Use explicit QFont constructor to avoid fromString parsing issues
        font = QFont()
        font.setFamily('Sans')
        font.setPointSize(size)
        font.setWeight(weight)
        painter.setFont(font)
        painter.setPen(color)

        from PyQt5.QtCore import QRectF
        metrics = painter.fontMetrics()
        pw = metrics.horizontalAdvance(text)
        ph = metrics.height()

        if align == 'center':
            painter.drawText(QRectF(x - pw/2, y, pw, ph), Qt.AlignLeft | Qt.AlignTop, text)
        elif align == 'right':
            painter.drawText(QRectF(x - pw, y, pw, ph), Qt.AlignLeft | Qt.AlignTop, text)
        else:
            painter.drawText(QRectF(x, y, pw, ph), Qt.AlignLeft | Qt.AlignTop, text)

    def _text_color(self):
        return QColor(230, 237, 243) if state.night_mode else QColor(31, 35, 40)

    def _subtle_color(self):
        return QColor(139, 148, 158) if state.night_mode else QColor(101, 109, 118)

    # ===== Mouse / drag handling =====
    def _is_on_cell(self, x, y):
        """Return cell index if (x,y) is on a cell, else -1."""
        for i, cell in enumerate(state.cells):
            col = i % 7
            row = i // 7
            cx = GRID_X + col * (CELL_SIZE + CELL_GAP)
            cy = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            if cx <= x <= cx + CELL_SIZE and cy <= y <= cy + CELL_SIZE:
                return i
        return -1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            cell_idx = self._is_on_cell(x, y)

            # Only the TODAY cell toggles - any other click can be used for dragging
            # (when drag is enabled)
            is_today_cell = (cell_idx >= 0 and cell_idx == state.today_cell_index)

            if is_today_cell:
                # Click on today - handle toggle, no drag
                self.click_cell(cell_idx)
                event.accept()
            elif state.allow_drag:
                # Click on non-today area + drag enabled - start dragging
                self._dragging = True
                self._drag_start_global = event.globalPos()
                self._drag_start_window = self.pos()
                self._drag_last_move_time = 0
                self._drag_move_count = 0
                self.setMouseTracking(True)
                self.grabMouse()
                event.accept()
            else:
                event.ignore()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event):
        """Move the window while dragging."""
        if not state.allow_drag or not getattr(self, '_dragging', False):
            return

        if not (event.buttons() & Qt.LeftButton):
            self._dragging = False
            self.releaseMouse()
            return

        # Throttle to ~60 FPS
        import time
        now_ms = int(time.time() * 1000)
        if now_ms - getattr(self, '_drag_last_move_time', 0) < 16:
            event.accept()
            return
        self._drag_last_move_time = now_ms

        global_pos = event.globalPos()
        delta = global_pos - self._drag_start_global
        new_pos = self._drag_start_window + delta
        self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        """Stop dragging."""
        if event.button() == Qt.LeftButton and getattr(self, '_dragging', False):
            self._dragging = False
            self._drag_move_count = 0
            self.releaseMouse()
            self.setMouseTracking(False)
            self.update()
            event.accept()

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
        self.update()

    # ===== Context menu =====
    def show_context_menu(self, pos):
        menu = QMenu(self)

        act_today = QAction(f"Click Today (+1)", self)
        act_today.triggered.connect(lambda: self.click_cell(state.today_cell_index))
        menu.addAction(act_today)

        menu.addSeparator()

        nm_label = f"Night Mode ({'ON' if state.night_mode else 'OFF'})"
        act_nm = QAction(nm_label, self)
        act_nm.triggered.connect(self.toggle_night_mode)
        menu.addAction(act_nm)

        mm_label = f"Minimal Mode ({'ON' if state.minimal_mode else 'OFF'})"
        act_mm = QAction(mm_label, self)
        act_mm.triggered.connect(self.toggle_minimal_mode)
        menu.addAction(act_mm)

        drag_label = f"Allow Dragging ({'ON' if state.allow_drag else 'OFF'})"
        act_drag = QAction(drag_label, self)
        act_drag.triggered.connect(self.toggle_allow_drag)
        menu.addAction(act_drag)

        menu.addSeparator()

        # Max clicks submenu
        max_menu = menu.addMenu("Max Clicks per Day")
        for n in [1, 2, 3, 4, 5, 8, 10]:
            label = f"{n} (current)" if n == state.max_clicks else str(n)
            act = QAction(label, self)
            act.triggered.connect(lambda checked, n=n: self.set_max_clicks(n))
            max_menu.addAction(act)

        menu.addSeparator()

        # Position submenu
        pos_menu = menu.addMenu("Position")
        for label, fn in [
            ("Top-Left",     lambda: self.move(20, 20)),
            ("Top-Right",    lambda: self.move(QGuiApplication.primaryScreen().geometry().width() - WIDGET_W - 20, 20)),
            ("Bottom-Left",  lambda: self.move(20, QGuiApplication.primaryScreen().geometry().height() - self.height() - 60)),
            ("Bottom-Right", lambda: self.position_bottom_right()),
        ]:
            act = QAction(label, self)
            act.triggered.connect(fn)
            pos_menu.addAction(act)

        menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)

        menu.exec_(pos)

    # ===== Toggles =====
    def toggle_night_mode(self):
        state.night_mode = not state.night_mode
        save_settings()
        self.update()

    def toggle_minimal_mode(self):
        state.minimal_mode = not state.minimal_mode
        h = WIDGET_H_MINIMAL if state.minimal_mode else WIDGET_H_FULL
        self.setFixedSize(WIDGET_W, h)
        self.position_bottom_right()
        save_settings()
        self.update()

    def toggle_allow_drag(self):
        state.allow_drag = not state.allow_drag
        if not state.allow_drag:
            # Force-stop any in-progress drag
            self._dragging = False
        save_settings()

    def set_max_clicks(self, n):
        state.max_clicks = max(1, n)
        save_settings()
        self.update()


# ===== Main =====
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Heatmap Calendar")
    app.setQuitOnLastWindowClosed(True)

    widget = CalendarWidget()

    # No system tray icon - widget is self-contained.
    # Right-click the widget for the menu (Night Mode, Minimal Mode, etc.)
    # To quit: right-click widget -> Quit

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
