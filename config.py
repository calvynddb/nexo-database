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
# Geometric typeface to support the bold/brutalist UI direction.
FONT_FAMILY = "Bahnschrift"
FONT_MAIN = (FONT_FAMILY, 14)
FONT_BOLD = (FONT_FAMILY, 14, "bold")

def get_font(size: int = 14, bold: bool = False):
    """Return a font tuple for widgets: (family, size[, 'bold'])."""
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

# --- colors --- geometric brutalist purple aesthetic
BG_COLOR = "#09070d"
PANEL_COLOR = "#14101c"
ACCENT_COLOR = "#a57bff"
TEXT_MUTED = "#b6a7d8"
TEXT_PRIMARY = "#f5f0ff"
BORDER_COLOR = "#5b4a80"
PANEL_SELECTED = "#3f2d66"

# semantic surfaces and control colors
TITLE_COLOR = "#efe3ff"
SURFACE_SOFT = "#211733"
SURFACE_INPUT = "#100b18"
SURFACE_HOVER = "#2b1f41"
SURFACE_SECTION = "#1a1328"

BTN_PRIMARY_FG = ACCENT_COLOR
BTN_PRIMARY_HOVER = "#9164f5"
BTN_SECONDARY_FG = "#1d1430"
BTN_SECONDARY_HOVER = "#2a1e43"
BTN_NEUTRAL_FG = "#191223"
BTN_NEUTRAL_HOVER = "#281d3b"
BTN_DISABLED_FG = "#3f3554"
BTN_SEGMENT_FG = "#2c2538"
BTN_SEGMENT_HOVER = "#3a3149"

SUCCESS_COLOR = "#15803d"
SUCCESS_HOVER = "#166534"
DANGER_COLOR = "#c41e3a"
DANGER_HOVER = "#a31a31"

ENTRY_BG = SURFACE_INPUT
ENTRY_TEXT = TEXT_PRIMARY

TABLE_ODD_BG = "#1a1327"
TABLE_EVEN_BG = "#150f21"
TABLE_HOVER_BG = "#32234d"
TABLE_HEADER_BG = "#201733"
TABLE_HEADER_HOVER = "#2f2348"
TABLE_HEADER_FG = "#e0d4f8"

# common sizing and spacing tokens
SPACE_XS = 6
SPACE_SM = 10
SPACE_MD = 14
SPACE_LG = 20
SPACE_XL = 28

RADIUS_SM = 2
RADIUS_MD = 4
RADIUS_LG = 6
RADIUS_XL = 8

BORDER_WIDTH_HAIRLINE = 1
BORDER_WIDTH_THIN = 1
BORDER_WIDTH_STRONG = 2

CONTROL_HEIGHT_SM = 30
CONTROL_HEIGHT_MD = 38
CONTROL_HEIGHT_LG = 46

# --- window dimensions ---
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1200

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

# --- chart colors --- purple-forward high-contrast palette
COLOR_PALETTE = [
    '#a57bff',
    '#bf9bff',
    '#8f5bf0',
    '#7b48dd',
    '#d0b3ff',
    '#6f42cc',
    '#b587ff',
    '#8d70bd'
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