"""
Configuration and Constants for EduManage SIS
"""

import customtkinter as ctk
import sys
import os

# --- path helpers for pyinstaller bundling ---
def resource_path(relative_path):
    """Get absolute path to a bundled read-only resource (assets, icons, etc.).
    Works both in development and in a PyInstaller --onefile bundle.
    """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def data_path(relative_path):
    """Get absolute path to a writable data file.
    In bundled mode, resolves relative to the directory containing the .exe.
    In development, resolves relative to the project root.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

# --- theme setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # using dark-blue theme, but will override blue colors in code

# --- fonts ---
# Modern system-friendly typography for a cleaner UI hierarchy.
FONT_FAMILY = "Segoe UI"
FONT_MAIN = (FONT_FAMILY, 14)
FONT_BOLD = (FONT_FAMILY, 14, "bold")

def get_font(size: int = 14, bold: bool = False):
    """Return a font tuple for widgets: (family, size[, 'bold'])."""
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

# --- colors --- bold-product dark aesthetic
BG_COLOR = "#0b1220"
PANEL_COLOR = "#111a2b"
ACCENT_COLOR = "#2563eb"
TEXT_MUTED = "#94a3b8"
TEXT_PRIMARY = "#e2e8f0"
BORDER_COLOR = "#253452"
PANEL_SELECTED = "#22385f"

# semantic surfaces and control colors
TITLE_COLOR = "#dbeafe"
SURFACE_SOFT = "#172338"
SURFACE_INPUT = "#0f1b30"
SURFACE_HOVER = "#1f3050"

BTN_PRIMARY_FG = ACCENT_COLOR
BTN_PRIMARY_HOVER = "#1d4ed8"
BTN_SECONDARY_FG = "#243652"
BTN_SECONDARY_HOVER = "#30466a"
BTN_NEUTRAL_FG = "#1a2740"
BTN_NEUTRAL_HOVER = "#263a5f"
BTN_DISABLED_FG = "#334155"

SUCCESS_COLOR = "#15803d"
SUCCESS_HOVER = "#166534"
DANGER_COLOR = "#c41e3a"
DANGER_HOVER = "#a31a31"

ENTRY_BG = SURFACE_INPUT
ENTRY_TEXT = TEXT_PRIMARY

TABLE_ODD_BG = "#111d31"
TABLE_EVEN_BG = "#0d1728"
TABLE_HOVER_BG = "#27426b"
TABLE_HEADER_BG = "#0f1b2f"
TABLE_HEADER_HOVER = "#1d2f4c"
TABLE_HEADER_FG = "#b8c7de"

# common sizing and spacing tokens
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 20

RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 15
RADIUS_XL = 20

CONTROL_HEIGHT_SM = 30
CONTROL_HEIGHT_MD = 40
CONTROL_HEIGHT_LG = 48

# --- window dimensions ---
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 940

# --- motion / animation settings ---
# Keep motion subtle by default for smoother perceived performance.
ANIMATIONS_ENABLED = True
REDUCED_MOTION = False
MOTION_DURATIONS_MS = {
    "frame_transition": 120,
    "dialog_open": 105,
    "dialog_close": 85,
    "panel_expand": 120,
    "loading_overlay": 100,
    "filter_apply": 95,
    # legacy aliases (kept for compatibility with older call sites)
    "dialog_enter": 125,
    "dialog_exit": 100,
    "panel_reveal": 145,
    "overlay_min_visible": 130,
}


def get_motion_duration(name: str, fallback: int = 140) -> int:
    """Return an effective duration for a named motion token in milliseconds."""
    if not ANIMATIONS_ENABLED:
        return 0

    try:
        duration = int(MOTION_DURATIONS_MS.get(name, fallback))
    except Exception:
        duration = int(fallback)

    if REDUCED_MOTION:
        return max(60, duration // 2)

    return max(0, duration)

# --- chart colors --- cool, high-contrast palette
COLOR_PALETTE = [
    '#2563eb',
    '#0ea5e9',
    '#14b8a6',
    '#4f46e5',
    '#6366f1',
    '#0284c7',
    '#06b6d4',
    '#0d9488'
]

# --- Global Theme Manager ---
class ThemeManager:
    """Manages theme changes and notifies listeners globally."""
    _listeners = []
    _current_mode = "dark"
    
    @classmethod
    def register_listener(cls, callback):
        """Register a callback to be called when theme changes."""
        if callback not in cls._listeners:
            cls._listeners.append(callback)
    
    @classmethod
    def unregister_listener(cls, callback):
        """Unregister a theme change callback."""
        if callback in cls._listeners:
            cls._listeners.remove(callback)
    
    @classmethod
    def notify_theme_change(cls, mode: str):
        """Notify all listeners of a theme change."""
        cls._current_mode = mode
        for callback in cls._listeners:
            try:
                callback(mode)
            except Exception as e:
                print(f"Error in theme callback: {e}")
    
    @classmethod
    def get_current_mode(cls) -> str:
        """Get the current theme mode."""
        return cls._current_mode


# global theme manager instance
THEME_MANAGER = ThemeManager()