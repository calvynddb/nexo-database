"""
Configuration and Constants for EduManage SIS
"""

import customtkinter as ctk

# --- Theme Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Using dark-blue theme, but will override blue colors in code

# --- Fonts ---
# Century Gothic - clean, modern font for professional look
FONT_MAIN = ("Century Gothic", 13)
FONT_BOLD = ("Century Gothic", 13, "bold")
FONT_FAMILY = "Century Gothic"

def get_font(size: int = 13, bold: bool = False):
    """Return a font tuple for widgets: (family, size[, 'bold'])."""
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

# --- Colors --- Subtle Dark Purple Theme with Purple Accents
BG_COLOR = "#0d0d12"  # Very dark background (nearly black)
PANEL_COLOR = "#1a1620"  # Dark card background (subtle warm undertone)
ACCENT_COLOR = "#5a4a7a"  # Subtle muted purple (primary accent)
TEXT_MUTED = "#8a8a95"  # Muted gray-blue (darker for readability)
TEXT_PRIMARY = "#e8e8f0"  # Soft off-white for main text
BORDER_COLOR = "#2a1f35"  # Subtle purple border for definition
PANEL_SELECTED = "#2d1f45"  # Subtle purple selection highlight

# --- CSV Files and Fields ---
FILES = {
    'college': 'colleges.csv',
    'program': 'programs.csv',
    'student': 'students.csv'
}

FIELDS = {
    'college': ['code', 'name'],
    'program': ['code', 'name', 'college'],
    'student': ['id', 'firstname', 'lastname', 'program', 'year', 'gender'],
}

# --- Window Dimensions ---
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# --- Chart Colors --- Subtle Purple Palette
COLOR_PALETTE = [
    '#5a4a7a',  # Subtle muted purple (primary)
    '#6d5a8a',  # Muted purple-gray
    '#7a6a95',  # Medium muted purple
    '#4a3a65',  # Deep subtle purple
    '#3a2a50',  # Very deep purple
    '#5a7a8a',  # Muted blue-gray
    '#6a7a8a',  # Muted slate
    '#5a8a7a'   # Muted teal (subtle cool tone)
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


# Global theme manager instance
THEME_MANAGER = ThemeManager()