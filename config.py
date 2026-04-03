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
# century gothic - clean, modern font for professional look
FONT_MAIN = ("Century Gothic", 14)
FONT_BOLD = ("Century Gothic", 14, "bold")
FONT_FAMILY = "Century Gothic"

def get_font(size: int = 14, bold: bool = False):
    """Return a font tuple for widgets: (family, size[, 'bold'])."""
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

# --- colors --- subtle dark purple theme with purple accents
BG_COLOR = "#0d0d12"  # very dark background (nearly black)
PANEL_COLOR = "#1a1620"  # dark card background (subtle warm undertone)
ACCENT_COLOR = "#5a4a7a"  # subtle muted purple (primary accent)
TEXT_MUTED = "#8a8a95"  # muted gray-blue (darker for readability)
TEXT_PRIMARY = "#e8e8f0"  # soft off-white for main text
BORDER_COLOR = "#2a1f35"  # subtle purple border for definition
PANEL_SELECTED = "#2d1f45"  # subtle purple selection highlight

# --- window dimensions ---
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 940

# --- chart colors --- subtle purple palette
COLOR_PALETTE = [
    '#5a4a7a',  # subtle muted purple (primary)
    '#6d5a8a',  # muted purple-gray
    '#7a6a95',  # medium muted purple
    '#4a3a65',  # deep subtle purple
    '#3a2a50',  # very deep purple
    '#5a7a8a',  # muted blue-gray
    '#6a7a8a',  # muted slate
    '#5a8a7a'   # muted teal (subtle cool tone)
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