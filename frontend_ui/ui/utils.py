"""
Utility functions for UI styling and assets.
"""

import customtkinter as ctk
import tkinter as tk
import time
from pathlib import Path
from config import (
    PANEL_COLOR,
    TEXT_MUTED,
    BORDER_COLOR,
    PANEL_SELECTED,
    ANIMATIONS_ENABLED,
    REDUCED_MOTION,
    get_font,
    get_motion_duration,
    resource_path,
)


# icon cache to avoid reloading
_icon_cache = {}


class SoftLoadingOverlay:
    """Reusable lightweight loading overlay with subtle animated feedback."""

    def __init__(self, parent, min_visible_ms: int = None):
        self.parent = parent
        if min_visible_ms is None:
            min_visible_ms = get_motion_duration("loading_overlay", 140)
        self.min_visible_ms = max(0, int(min_visible_ms))
        self._started_at = 0.0
        self._pulse_after_id = None
        self._pulse_step = 0
        self._base_text = "Loading"
        self._pulse_interval_ms = 220 if not REDUCED_MOTION else 320

        self._overlay = ctk.CTkFrame(parent, fg_color="#120f18", corner_radius=0)
        self._overlay.grid_rowconfigure(0, weight=1)
        self._overlay.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            self._overlay,
            fg_color="#1d1727",
            corner_radius=12,
            border_width=1,
            border_color="#2a1f35",
        )
        panel.grid(row=0, column=0, padx=20, pady=20, sticky="")

        self._label = ctk.CTkLabel(
            panel,
            text="Loading",
            font=get_font(13, True),
            text_color="#d8d5de",
        )
        self._label.pack(padx=18, pady=(14, 8))

        self._bar = ctk.CTkProgressBar(panel, mode="indeterminate", width=180, progress_color="#6d5a8a")
        self._bar.pack(padx=18, pady=(0, 14))

    def show(self, message: str = "Loading"):
        self._base_text = (message or "Loading").strip()
        self._pulse_step = 0
        self._started_at = time.perf_counter()
        self._cancel_pulse()
        self._label.configure(text=self._base_text)
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay.lift()
        if ANIMATIONS_ENABLED and not REDUCED_MOTION:
            try:
                self._bar.start()
            except Exception:
                pass
            self._pulse()

    def hide(self):
        elapsed_ms = int((time.perf_counter() - self._started_at) * 1000)
        remaining = max(0, self.min_visible_ms - elapsed_ms)

        def _finish_hide():
            self._cancel_pulse()
            try:
                self._bar.stop()
            except Exception:
                pass
            self._overlay.place_forget()

        if remaining > 0:
            self.parent.after(remaining, _finish_hide)
        else:
            _finish_hide()

    def _pulse(self):
        dots = "." * ((self._pulse_step % 3) + 1)
        self._label.configure(text=f"{self._base_text}{dots}")
        self._pulse_step += 1
        self._pulse_after_id = self.parent.after(self._pulse_interval_ms, self._pulse)

    def _cancel_pulse(self):
        if self._pulse_after_id:
            try:
                self.parent.after_cancel(self._pulse_after_id)
            except Exception:
                pass
            self._pulse_after_id = None


def show_dialog(parent, title, message, dialog_type="info", callback=None):
    """Show a custom-styled dialog matching the app theme.

    dialog_type: 'info', 'error', 'warning', 'yesno'
    For 'yesno' returns True/False. For others returns None.
    """
    from config import BG_COLOR, ACCENT_COLOR, TEXT_PRIMARY, TEXT_MUTED, PANEL_COLOR, BORDER_COLOR, get_font

    result = [None]  # mutable container for yesno result

    dialog_window = ctk.CTkToplevel(parent)
    dialog_window.title(title)
    dialog_window.overrideredirect(False)
    dialog_window.configure(fg_color=BG_COLOR)
    dialog_window.attributes('-topmost', True)
    dialog_window.grab_set()
    dialog_window.focus_force()

    # size based on message length; yesno dialogs need extra room for two buttons
    msg_len = len(message)
    base = 250 if dialog_type == "yesno" else 220
    height = base if msg_len < 100 else base + 60 if msg_len < 200 else base + 120
    dialog_window.geometry(f"450x{height}")

    dialog_window.update_idletasks()
    x = (dialog_window.winfo_screenwidth() // 2) - 225
    y = (dialog_window.winfo_screenheight() // 2) - (height // 2)
    dialog_window.geometry(f"+{x}+{y}")

    def _animate_dialog_enter():
        duration_ms = _resolve_motion_duration("dialog_open", None, fallback=160)
        if duration_ms <= 0:
            return

        steps, tick_ms = _motion_steps(duration_ms, min_steps=3)
        if steps <= 0:
            return

        offset = 8 if REDUCED_MOTION else 14
        try:
            dialog_window.attributes("-alpha", 0.0)
        except Exception:
            return

        def _step(i=0):
            t = i / steps
            eased = 1.0 - ((1.0 - t) * (1.0 - t))
            current_y = y + int((1.0 - eased) * offset)
            try:
                dialog_window.geometry(f"+{x}+{current_y}")
            except Exception:
                pass
            try:
                dialog_window.attributes("-alpha", min(1.0, eased))
            except Exception:
                pass
            if i < steps:
                dialog_window.after(tick_ms, lambda: _step(i + 1))

        _step(0)

    _is_closing = {"value": False}

    def _close_dialog(value=None):
        if _is_closing["value"]:
            return
        _is_closing["value"] = True
        result[0] = value

        def _finish_close():
            try:
                dialog_window.destroy()
            except Exception:
                pass
            if callback and dialog_type == "yesno":
                try:
                    callback(value)
                except Exception:
                    pass

        duration_ms = _resolve_motion_duration("dialog_close", None, fallback=120)
        if duration_ms <= 0:
            _finish_close()
            return

        steps, tick_ms = _motion_steps(duration_ms, min_steps=2)
        if steps <= 0:
            _finish_close()
            return

        try:
            current_alpha = float(dialog_window.attributes("-alpha"))
        except Exception:
            current_alpha = 1.0

        def _fade(i=0):
            t = i / steps
            alpha = max(0.0, current_alpha * (1.0 - t))
            try:
                dialog_window.attributes("-alpha", alpha)
            except Exception:
                pass
            if i < steps:
                dialog_window.after(tick_ms, lambda: _fade(i + 1))
            else:
                _finish_close()

        _fade(0)

    # pick accent color by dialog type
    if dialog_type == "error":
        accent = "#c41e3a"
        icon_text = "ERROR"
    elif dialog_type == "warning":
        accent = "#d4a017"
        icon_text = "WARNING"
    elif dialog_type == "yesno":
        accent = ACCENT_COLOR
        icon_text = "CONFIRM"
    else:
        accent = ACCENT_COLOR
        icon_text = "INFO"

    # content frame
    frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=30, pady=30)

    # type badge
    badge = ctk.CTkLabel(frame, text=icon_text, font=get_font(11, True),
                         text_color="white", fg_color=accent, corner_radius=6,
                         width=70, height=22)
    badge.pack(pady=(0, 10))

    # title label
    ctk.CTkLabel(frame, text=title, font=get_font(14, True), text_color=TEXT_PRIMARY).pack(pady=(0, 10))

    # message label
    ctk.CTkLabel(frame, text=message, font=get_font(13), text_color=TEXT_MUTED,
                 wraplength=380).pack(pady=(0, 20), fill="both", expand=True)

    # buttons
    button_frame = ctk.CTkFrame(frame, fg_color="transparent")
    button_frame.pack(fill="x")

    if dialog_type == "yesno":
        def _yes():
            _close_dialog(True)

        def _no():
            _close_dialog(False)

        ctk.CTkButton(button_frame, text="Yes", fg_color=accent, text_color="white",
                      hover_color="#7C3AED", font=get_font(13, True), height=36,
                      command=_yes).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(button_frame, text="No", fg_color="#3a3a3f", text_color="white",
                      hover_color="#4a4a4f", font=get_font(13, True), height=36,
                      command=_no).pack(side="left", fill="x", expand=True, padx=(8, 0))
    else:
        ctk.CTkButton(button_frame, text="OK", fg_color=accent, text_color="white",
                      hover_color="#7C3AED", font=get_font(13, True), height=36,
                      command=_close_dialog).pack(fill="x")

    dialog_window.protocol(
        "WM_DELETE_WINDOW",
        lambda: _close_dialog(False if dialog_type == "yesno" else None),
    )
    _animate_dialog_enter()
    parent.wait_window(dialog_window)
    return result[0]


def get_icon(name: str, size: int = 36, fallback_color: str = "#6d28d9"):
    """Load an icon from assets/icons directory, with fallback to colored square.
    
    Args:
        name: Icon name (e.g., 'users', 'settings', 'search')
        size: Icon size in pixels (18, 22, 28, or 36)
        fallback_color: Color to use if icon file not found
    
    Returns:
        CTkImage or PhotoImage suitable for CustomTkinter widgets
    """
    cache_key = f"{name}_{size}"
    
    # return from cache if available
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    
    # try to load base icon first and scale it (prioritize custom icons)
    base_icon_path = Path(resource_path(f"assets/icons/{name}.png"))
    if base_icon_path.exists():
        try:
            from PIL import Image
            pil = Image.open(base_icon_path)
            # resize to requested size
            pil = pil.resize((size, size), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            _icon_cache[cache_key] = img
            return img
        except Exception as e:
            print(f"Error loading icon {base_icon_path}: {e}")
    
    # fallback: try to load PNG icon with exact size
    icon_path = Path(resource_path(f"assets/icons/{name}_{size}.png"))
    
    if icon_path.exists():
        try:
            from PIL import Image
            pil = Image.open(icon_path)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            _icon_cache[cache_key] = img
            return img
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
    
    # fallback: return colored square placeholder
    return placeholder_image(size=size, color=fallback_color)


def get_main_logo(size: int = 56):
    """Load the main logo from assets/Main Logo.png.
    
    Args:
        size: Size to scale the logo to in pixels
    
    Returns:
        CTkImage
    """
    logo_path = Path(resource_path("assets/Main Logo.png"))
    
    if logo_path.exists():
        try:
            from PIL import Image
            pil = Image.open(logo_path)
            # resize to requested size, maintaining aspect ratio
            pil.thumbnail((size, size), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=pil, size=(size, size))
            return img
        except Exception as e:
            print(f"Error loading logo {logo_path}: {e}")
    
    # fallback to user icon if logo not found
    return get_icon("user", size=size)


def setup_treeview_style():
    """Configure styling for ttk.Treeview widgets."""
    from tkinter import ttk
    
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview", 
        background=PANEL_COLOR,
        foreground="#dcdcdc",
        rowheight=48,
        fieldbackground=PANEL_COLOR,
        borderwidth=0,
        highlightthickness=0,
        focuscolor="",
        font=get_font(14),
        padding=2
    )
    style.map('Treeview', background=[('selected', PANEL_SELECTED)])
    # make headings look like interactive buttons with distinct styling
    HEADING_BG = "#13101a"       # slightly darker than panel — distinct header row
    HEADING_HOVER = "#2d1f45"    # purple tint on hover — signals interactivity
    HEADING_FG = "#a8a8b5"       # slightly brighter than TEXT_MUTED for contrast
    style.configure(
        "Treeview.Heading",
        background=HEADING_BG,
        foreground=HEADING_FG,
        relief="flat",
        borderwidth=0,
        padding=(8, 12),
        font=get_font(13, True)
    )
    style.map("Treeview.Heading", 
              background=[('active', HEADING_HOVER)],
              foreground=[('active', '#e8e8f0')])

    # remove focus ring highlight
    try:
        style.configure('Treeview', highlightthickness=0, focuscolor="")
    except Exception:
        pass


def placeholder_image(size=36, color="#303035"):
    """Return a square PhotoImage filled with `color` to be used as an icon placeholder.

    The PhotoImage should be kept referenced by the caller (e.g., widget.image = img)
    to avoid garbage collection.
    """
    # prefer creating a CTkImage from a PIL Image so CustomTkinter can scale it on HiDPI
    try:
        from PIL import Image
        pil = Image.new('RGBA', (size, size), color)
        return ctk.CTkImage(light_image=pil, size=(size, size))
    except Exception:
        # fallback: create a tkinter.PhotoImage and try to wrap it in CTkImage
        img = tk.PhotoImage(width=size, height=size)
        try:
            img.put(color, to=(0, 0, size - 1, size - 1))
        except Exception:
            img.put(color, to=(0, 0))
        try:
            return ctk.CTkImage(light_image=img, size=(size, size))
        except Exception:
            return img


# --- Simple animation helpers ---
def _lerp(a, b, t):
    return a + (b - a) * t


def _resolve_motion_duration(name: str, explicit_ms, fallback: int) -> int:
    """Resolve animation duration with global motion settings applied."""
    try:
        if explicit_ms is None:
            duration_ms = int(get_motion_duration(name, fallback))
        else:
            duration_ms = int(explicit_ms)
    except Exception:
        duration_ms = int(fallback)

    duration_ms = max(0, duration_ms)
    if not ANIMATIONS_ENABLED:
        return 0
    if REDUCED_MOTION:
        return min(duration_ms, 110)
    return duration_ms


def _motion_steps(duration_ms: int, min_steps: int = 2):
    """Return (steps, tick_ms) for smooth non-blocking after() animations."""
    duration_ms = max(0, int(duration_ms))
    if duration_ms <= 0:
        return 0, 0
    steps = max(int(min_steps), int(duration_ms // 15), 1)
    tick_ms = max(8, int(duration_ms / steps))
    return steps, tick_ms


def animate_height(widget, target_height, duration=None):
    """Smoothly animate a widget's `height` option to target_height (px).

    Uses `after` and small steps to interpolate. Non-blocking.
    """
    duration_ms = _resolve_motion_duration("panel_expand", duration, fallback=200)
    if duration_ms <= 0:
        try:
            widget.configure(height=target_height)
        except Exception:
            pass
        return

    try:
        start = widget.winfo_height()
    except Exception:
        try:
            start = int(widget.cget('height') or 0)
        except Exception:
            start = 0
    steps, tick_ms = _motion_steps(duration_ms, min_steps=2)
    delta = target_height - start

    def step(i=1):
        t = i / steps
        h = int(_lerp(start, target_height, t))
        try:
            widget.configure(height=h)
        except Exception:
            pass
        if i < steps:
            widget.after(tick_ms, lambda: step(i + 1))

    step()


def animate_progress(bar, target, duration=None):
    """Animate a CTkProgressBar `bar` from current value to `target` (0..1)."""
    duration_ms = _resolve_motion_duration("loading_overlay", duration, fallback=400)
    if duration_ms <= 0:
        try:
            bar.set(target)
            bar._value = target
        except Exception:
            pass
        return

    try:
        start = float(getattr(bar, '_value', bar._progress))
    except Exception:
        try:
            start = float(bar.get())
        except Exception:
            start = 0.0
    steps, tick_ms = _motion_steps(duration_ms, min_steps=2)

    def step(i=1):
        t = i / steps
        v = _lerp(start, target, t)
        try:
            bar.set(v)
            bar._value = v
        except Exception:
            pass
        if i < steps:
            bar.after(tick_ms, lambda: step(i + 1))

    step()


def apply_button_hover(root, hover_scale=1.03):
    """Placeholder function - no longer needed (button sizing conflicts disabled)."""
    pass


def animate_toplevel_in(window, x=None, y=None, duration_ms=None, offset=12):
    """Animate a toplevel window with a subtle upward slide and fade-in."""
    if x is None or y is None:
        try:
            window.update_idletasks()
            x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
            y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
            window.geometry(f"+{x}+{y}")
        except Exception:
            return

    total_ms = _resolve_motion_duration("dialog_open", duration_ms, fallback=160)
    if total_ms <= 0:
        try:
            window.attributes("-alpha", 1.0)
        except Exception:
            pass
        try:
            window.geometry(f"+{x}+{y}")
        except Exception:
            pass
        return

    steps, tick_ms = _motion_steps(total_ms, min_steps=3)
    if steps <= 0:
        return

    offset_px = 8 if REDUCED_MOTION else max(0, int(offset))
    try:
        window.attributes("-alpha", 0.0)
    except Exception:
        return

    def _step(i=0):
        t = i / steps
        eased = 1.0 - ((1.0 - t) * (1.0 - t))
        current_y = y + int((1.0 - eased) * offset_px)
        try:
            window.geometry(f"+{x}+{current_y}")
        except Exception:
            pass
        try:
            window.attributes("-alpha", min(1.0, eased))
        except Exception:
            pass
        if i < steps:
            window.after(tick_ms, lambda: _step(i + 1))

    # Start on idle so callers can finish building window contents before reveal.
    try:
        window.after_idle(lambda: _step(0) if window.winfo_exists() else None)
    except Exception:
        _step(0)


def fade_transition(app, new_frame, steps=12, on_shown=None, duration_ms=None):
    """Animate a window alpha fade-out/fade-in while swapping to new_frame.

    Lifts new_frame at the midpoint (while the window is fully transparent),
    then fades back in. Calls on_shown() once the transition completes.
    """
    total_duration_ms = _resolve_motion_duration(
        "frame_transition",
        duration_ms,
        fallback=max(140, int(steps) * 20),
    )

    def _swap():
        new_frame.lift()
        try:
            apply_button_hover(new_frame)
        except Exception:
            pass

    def _call_shown():
        if on_shown:
            try:
                on_shown()
            except Exception:
                pass

    if total_duration_ms <= 0:
        _swap()
        try:
            app.attributes("-alpha", 1.0)
        except Exception:
            pass
        _call_shown()
        return

    phase_duration_ms = max(30, total_duration_ms // 2)
    if steps is None or int(steps) <= 0:
        steps, tick_ms = _motion_steps(phase_duration_ms, min_steps=3)
    else:
        steps = max(2, int(steps))
        tick_ms = max(8, int(phase_duration_ms / steps))

    def fade_out(i=0):
        try:
            app.attributes('-alpha', max(0.0, 1.0 - i / steps))
        except Exception:
            pass
        if i < steps:
            app.after(tick_ms, lambda: fade_out(i + 1))
        else:
            _swap()
            fade_in(0)

    def fade_in(i=0):
        try:
            app.attributes('-alpha', min(1.0, i / steps))
        except Exception:
            pass
        if i < steps:
            app.after(tick_ms, lambda: fade_in(i + 1))
        else:
            try:
                app.attributes("-alpha", 1.0)
            except Exception:
                pass
            _call_shown()

    fade_out(0)

