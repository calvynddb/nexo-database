"""
Configuration and Constants for EduManage SIS
"""

import customtkinter as ctk
import sys
import os
import json

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
SHADOW_EDGE_COLOR = "#0d0a14"
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

# logo-derived accent anchors used for gradient styling
LOGO_VIOLET_DEEP = "#9068f8"
LOGO_VIOLET_CORE = "#9870f8"
LOGO_VIOLET_LIGHT = "#b8a0f8"
LOGO_LAVENDER_SOFT = "#f8f0f8"

GRADIENT_BRAND_PRIMARY = (LOGO_VIOLET_DEEP, LOGO_VIOLET_CORE, LOGO_VIOLET_LIGHT)
GRADIENT_BRAND_SOFT = ("#5b4a80", LOGO_VIOLET_DEEP, LOGO_VIOLET_CORE)
GRADIENT_BRAND_MUTED = ("#2c2538", "#5b4a80", LOGO_VIOLET_DEEP)

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

# --- theme preset metadata ---
THEME_PREFS_FILE = "theme_prefs.json"
THEME_PRESET_LABELS = {
    0: "Purple",
    1: "Blue",
    2: "Orange",
    3: "Pink",
}
THEME_PRESET_SWATCHES = {
    0: "#a57bff",
    1: "#4f9bff",
    2: "#f97316",
    3: "#f472b6",
}

# --- Global Theme Manager ---
class ThemeManager:
    """Manages theme changes and notifies listeners globally."""
    _listeners = []
    _current_mode = "dark"
    _current_preset = 0
    _current_tokens = {}
    
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
    def notify_theme_change(cls, mode: str, preset: int = 0, tokens: dict | None = None):
        """Notify all listeners of a theme change."""
        mode = str(mode or "dark").lower().strip()
        if mode not in ("dark", "light"):
            mode = "dark"

        try:
            preset = int(preset)
        except Exception:
            preset = 0

        if tokens is None:
            tokens = {}

        cls._current_mode = mode
        cls._current_preset = preset
        cls._current_tokens = dict(tokens)

        for callback in cls._listeners:
            try:
                callback(mode, preset, dict(cls._current_tokens))
            except TypeError:
                callback(mode)
            except Exception as e:
                print(f"Error in theme callback: {e}")
    
    @classmethod
    def get_current_mode(cls) -> str:
        """Get the current theme mode."""
        return cls._current_mode

    @classmethod
    def get_current_preset(cls) -> int:
        """Get the current color preset index."""
        return int(cls._current_preset)

    @classmethod
    def get_current_tokens(cls) -> dict:
        """Get the active resolved theme tokens."""
        return dict(cls._current_tokens)


# global theme manager instance
THEME_MANAGER = ThemeManager()

_THEME_SYNC_MODULES = (
    "frontend_ui.auth.login",
    "frontend_ui.dashboard.main",
    "frontend_ui.students.list_view",
    "frontend_ui.programs.list_view",
    "frontend_ui.colleges.list_view",
    "frontend_ui.ui.cards",
    "frontend_ui.ui.pagination",
    "frontend_ui.ui.inputs",
    "frontend_ui.ui.utils",
)


def _sanitize_theme_mode(mode: str) -> str:
    candidate = str(mode or "dark").strip().lower()
    return candidate if candidate in ("dark", "light") else "dark"


def _sanitize_theme_preset(preset: int) -> int:
    try:
        idx = int(preset)
    except Exception:
        idx = 0
    return idx if idx in THEME_PRESET_LABELS else 0


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = str(color or "").strip().lstrip("#")
    if len(value) != 6:
        return (165, 123, 255)

    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (165, 123, 255)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _mix_hex(start_color: str, end_color: str, weight: float) -> str:
    sr, sg, sb = _hex_to_rgb(start_color)
    er, eg, eb = _hex_to_rgb(end_color)
    t = max(0.0, min(1.0, float(weight)))
    return _rgb_to_hex(
        (
            sr + ((er - sr) * t),
            sg + ((eg - sg) * t),
            sb + ((eb - sb) * t),
        )
    )


def _theme_seed_color(preset: int) -> str:
    return THEME_PRESET_SWATCHES.get(_sanitize_theme_preset(preset), THEME_PRESET_SWATCHES[0])


def _theme_base_tokens(mode: str, preset: int) -> dict:
    accent = _theme_seed_color(preset)

    if mode == "light":
        return {
            "BG_COLOR": _mix_hex("#f5f7fb", accent, 0.08),
            "PANEL_COLOR": "#ffffff",
            "TEXT_MUTED": _mix_hex("#5b6678", accent, 0.15),
            "TEXT_PRIMARY": "#1f2937",
            "BORDER_COLOR": _mix_hex("#c8d0dd", accent, 0.35),
            "SHADOW_EDGE_COLOR": "#dde3ee",
            "PANEL_SELECTED": _mix_hex("#edf2fb", accent, 0.40),
            "TITLE_COLOR": _mix_hex("#223047", accent, 0.38),
            "SURFACE_SOFT": _mix_hex("#eff3fa", accent, 0.24),
            "SURFACE_INPUT": _mix_hex("#f6f8fc", accent, 0.12),
            "SURFACE_HOVER": _mix_hex("#e7edf8", accent, 0.28),
            "SURFACE_SECTION": _mix_hex("#edf2f9", accent, 0.20),
            "BTN_SECONDARY_FG": _mix_hex("#edf2fa", accent, 0.24),
            "BTN_SECONDARY_HOVER": _mix_hex("#dfe8f5", accent, 0.30),
            "BTN_NEUTRAL_FG": _mix_hex("#eceff5", accent, 0.16),
            "BTN_NEUTRAL_HOVER": _mix_hex("#dfe5ef", accent, 0.24),
            "BTN_DISABLED_FG": _mix_hex("#c8d0dd", accent, 0.14),
            "BTN_SEGMENT_FG": _mix_hex("#ebf0f8", accent, 0.22),
            "BTN_SEGMENT_HOVER": _mix_hex("#dde6f3", accent, 0.30),
            "SUCCESS_COLOR": "#15803d",
            "SUCCESS_HOVER": "#166534",
            "DANGER_COLOR": "#c41e3a",
            "DANGER_HOVER": "#a31a31",
            "TABLE_ODD_BG": _mix_hex("#fbfcff", accent, 0.10),
            "TABLE_EVEN_BG": _mix_hex("#f3f6fd", accent, 0.16),
            "TABLE_HOVER_BG": _mix_hex("#e6edf9", accent, 0.35),
            "TABLE_HEADER_BG": _mix_hex("#e9eef8", accent, 0.28),
            "TABLE_HEADER_HOVER": _mix_hex("#dde6f6", accent, 0.35),
            "TABLE_HEADER_FG": _mix_hex("#243247", accent, 0.22),
            "LOGO_LAVENDER_SOFT": _mix_hex("#f8f7fb", accent, 0.18),
        }

    return {
        "BG_COLOR": _mix_hex("#0b0f16", accent, 0.10),
        "PANEL_COLOR": _mix_hex("#151b25", accent, 0.16),
        "TEXT_MUTED": _mix_hex("#a7b2c7", accent, 0.22),
        "TEXT_PRIMARY": "#eef2fb",
        "BORDER_COLOR": _mix_hex("#48566e", accent, 0.48),
        "SHADOW_EDGE_COLOR": "#090c11",
        "PANEL_SELECTED": _mix_hex("#1f2a3d", accent, 0.52),
        "TITLE_COLOR": _mix_hex("#eaf0fb", accent, 0.30),
        "SURFACE_SOFT": _mix_hex("#202938", accent, 0.34),
        "SURFACE_INPUT": _mix_hex("#111722", accent, 0.22),
        "SURFACE_HOVER": _mix_hex("#293347", accent, 0.44),
        "SURFACE_SECTION": _mix_hex("#1b2333", accent, 0.32),
        "BTN_SECONDARY_FG": _mix_hex("#1c2535", accent, 0.30),
        "BTN_SECONDARY_HOVER": _mix_hex("#273249", accent, 0.40),
        "BTN_NEUTRAL_FG": _mix_hex("#18202d", accent, 0.24),
        "BTN_NEUTRAL_HOVER": _mix_hex("#253148", accent, 0.38),
        "BTN_DISABLED_FG": _mix_hex("#3a4456", accent, 0.20),
        "BTN_SEGMENT_FG": _mix_hex("#2a3445", accent, 0.34),
        "BTN_SEGMENT_HOVER": _mix_hex("#38455b", accent, 0.44),
        "SUCCESS_COLOR": "#15803d",
        "SUCCESS_HOVER": "#166534",
        "DANGER_COLOR": "#c41e3a",
        "DANGER_HOVER": "#a31a31",
        "TABLE_ODD_BG": _mix_hex("#182131", accent, 0.28),
        "TABLE_EVEN_BG": _mix_hex("#141c2a", accent, 0.24),
        "TABLE_HOVER_BG": _mix_hex("#273246", accent, 0.55),
        "TABLE_HEADER_BG": _mix_hex("#202a3c", accent, 0.40),
        "TABLE_HEADER_HOVER": _mix_hex("#2f3b52", accent, 0.52),
        "TABLE_HEADER_FG": _mix_hex("#dbe4f6", accent, 0.20),
        "LOGO_LAVENDER_SOFT": _mix_hex("#f5f4f8", accent, 0.18),
    }


def _theme_accent_tokens(preset: int, mode: str) -> dict:
    preset_map = {
        0: {
            "ACCENT_COLOR": "#a57bff",
            "BTN_PRIMARY_HOVER": "#9164f5",
            "BORDER_DARK": "#5b4a80",
            "BORDER_LIGHT": "#b59ddf",
            "LOGO_VIOLET_DEEP": "#9068f8",
            "LOGO_VIOLET_CORE": "#9870f8",
            "LOGO_VIOLET_LIGHT": "#b8a0f8",
            "COLOR_PALETTE": ["#a57bff", "#bf9bff", "#8f5bf0", "#7b48dd", "#d0b3ff", "#6f42cc", "#b587ff", "#8d70bd"],
        },
        1: {
            "ACCENT_COLOR": "#4f9bff",
            "BTN_PRIMARY_HOVER": "#337fe0",
            "BORDER_DARK": "#355b86",
            "BORDER_LIGHT": "#9fbce0",
            "LOGO_VIOLET_DEEP": "#4f87e8",
            "LOGO_VIOLET_CORE": "#5fa0f2",
            "LOGO_VIOLET_LIGHT": "#8abdf7",
            "COLOR_PALETTE": ["#4f9bff", "#75b2ff", "#2f7fd9", "#93c5fd", "#1d4f91", "#60a5fa", "#3b82f6", "#9ec9ff"],
        },
        2: {
            "ACCENT_COLOR": "#f97316",
            "BTN_PRIMARY_HOVER": "#ea580c",
            "BORDER_DARK": "#7c3a13",
            "BORDER_LIGHT": "#e8b08f",
            "LOGO_VIOLET_DEEP": "#d86012",
            "LOGO_VIOLET_CORE": "#f47d2a",
            "LOGO_VIOLET_LIGHT": "#f8a161",
            "COLOR_PALETTE": ["#f97316", "#fb923c", "#ea580c", "#fdba74", "#c2410c", "#9a3412", "#dd6b20", "#f6ad55"],
        },
        3: {
            "ACCENT_COLOR": "#f472b6",
            "BTN_PRIMARY_HOVER": "#ec4899",
            "BORDER_DARK": "#7a3f61",
            "BORDER_LIGHT": "#d7a0bf",
            "LOGO_VIOLET_DEEP": "#e05a9f",
            "LOGO_VIOLET_CORE": "#ef73b1",
            "LOGO_VIOLET_LIGHT": "#f6a2cd",
            "COLOR_PALETTE": ["#f472b6", "#f9a8d4", "#ec4899", "#db2777", "#be185d", "#f472b6", "#fbcfe8", "#e879f9"],
        },
    }
    accent = dict(preset_map.get(preset, preset_map[0]))
    accent["BORDER_COLOR"] = accent["BORDER_LIGHT"] if mode == "light" else accent["BORDER_DARK"]
    return accent


def get_theme_tokens(mode: str | None = None, preset: int | None = None) -> dict:
    """Resolve active theme tokens for a mode and preset."""
    if mode is None:
        mode = THEME_MANAGER.get_current_mode()
    if preset is None:
        preset = THEME_MANAGER.get_current_preset()

    mode = _sanitize_theme_mode(mode)
    preset = _sanitize_theme_preset(preset)

    base = _theme_base_tokens(mode, preset)
    accent = _theme_accent_tokens(preset, mode)

    tokens = dict(base)
    tokens.update(
        {
            "ACCENT_COLOR": accent["ACCENT_COLOR"],
            "BTN_PRIMARY_FG": accent["ACCENT_COLOR"],
            "BTN_PRIMARY_HOVER": accent["BTN_PRIMARY_HOVER"],
            "BORDER_COLOR": accent["BORDER_COLOR"],
            "PANEL_SELECTED": accent["BORDER_COLOR"] if mode == "light" else base["PANEL_SELECTED"],
            "ENTRY_BG": base["SURFACE_INPUT"],
            "ENTRY_TEXT": base["TEXT_PRIMARY"],
            "LOGO_VIOLET_DEEP": accent["LOGO_VIOLET_DEEP"],
            "LOGO_VIOLET_CORE": accent["LOGO_VIOLET_CORE"],
            "LOGO_VIOLET_LIGHT": accent["LOGO_VIOLET_LIGHT"],
            "GRADIENT_BRAND_PRIMARY": (
                accent["LOGO_VIOLET_DEEP"],
                accent["LOGO_VIOLET_CORE"],
                accent["LOGO_VIOLET_LIGHT"],
            ),
            "GRADIENT_BRAND_SOFT": (
                accent["BORDER_COLOR"],
                accent["LOGO_VIOLET_DEEP"],
                accent["LOGO_VIOLET_CORE"],
            ),
            "GRADIENT_BRAND_MUTED": (
                base["BTN_SEGMENT_FG"],
                accent["BORDER_COLOR"],
                accent["LOGO_VIOLET_DEEP"],
            ),
            "COLOR_PALETTE": list(accent["COLOR_PALETTE"]),
        }
    )
    return tokens


def _theme_prefs_path() -> str:
    return data_path(THEME_PREFS_FILE)


def load_theme_preference() -> tuple[str, int]:
    """Load persisted theme preference from disk."""
    mode = "dark"
    preset = 0
    path = _theme_prefs_path()

    if not os.path.exists(path):
        return mode, preset

    try:
        with open(path, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
        mode = _sanitize_theme_mode(payload.get("mode", mode))
        preset = _sanitize_theme_preset(payload.get("preset", preset))
    except Exception:
        return "dark", 0

    return mode, preset


def save_theme_preference(mode: str, preset: int) -> None:
    """Persist selected theme mode and preset."""
    safe_mode = _sanitize_theme_mode(mode)
    safe_preset = _sanitize_theme_preset(preset)
    payload = {"mode": safe_mode, "preset": safe_preset}

    try:
        with open(_theme_prefs_path(), "w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2)
    except Exception:
        pass


def get_theme_preference() -> tuple[str, int]:
    """Return the currently active theme preference."""
    return THEME_MANAGER.get_current_mode(), THEME_MANAGER.get_current_preset()


def _sync_theme_to_loaded_modules(tokens: dict) -> None:
    """Propagate resolved theme tokens into already-imported UI modules."""
    for module_name in _THEME_SYNC_MODULES:
        module = sys.modules.get(module_name)
        if module is None:
            continue

        for key, value in tokens.items():
            if hasattr(module, key):
                setattr(module, key, value)

    ui_utils = sys.modules.get("frontend_ui.ui.utils")
    if ui_utils is not None and hasattr(ui_utils, "clear_icon_cache"):
        try:
            ui_utils.clear_icon_cache()
        except Exception:
            pass


def apply_theme(mode: str, preset: int = 0, *, persist: bool = True, notify: bool = True) -> dict:
    """Apply theme mode/preset globally and broadcast changes."""
    safe_mode = _sanitize_theme_mode(mode)
    safe_preset = _sanitize_theme_preset(preset)
    tokens = get_theme_tokens(safe_mode, safe_preset)

    try:
        ctk.set_appearance_mode(safe_mode)
    except Exception:
        pass

    for key, value in tokens.items():
        globals()[key] = value

    _sync_theme_to_loaded_modules(tokens)

    if persist:
        save_theme_preference(safe_mode, safe_preset)

    if notify:
        THEME_MANAGER.notify_theme_change(safe_mode, safe_preset, tokens)
    else:
        ThemeManager._current_mode = safe_mode
        ThemeManager._current_preset = safe_preset
        ThemeManager._current_tokens = dict(tokens)

    return tokens


_initial_mode, _initial_preset = load_theme_preference()
apply_theme(_initial_mode, _initial_preset, persist=False, notify=False)