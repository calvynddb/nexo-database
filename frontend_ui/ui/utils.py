"""
Utility functions for UI styling and assets.
"""

import customtkinter as ctk
import tkinter as tk
import time
from pathlib import Path
from config import PANEL_COLOR, TEXT_MUTED, BORDER_COLOR, PANEL_SELECTED, get_font, resource_path


# icon cache to avoid reloading
_icon_cache = {}


class SoftLoadingOverlay:
    """Reusable lightweight loading overlay with subtle animated feedback."""

    def __init__(self, parent, min_visible_ms: int = 140):
        self.parent = parent
        self.min_visible_ms = max(0, int(min_visible_ms))
        self._started_at = 0.0
        self._pulse_after_id = None
        self._pulse_step = 0
        self._base_text = "Loading"

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
        self._pulse_after_id = self.parent.after(220, self._pulse)

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
            result[0] = True
            if callback:
                callback(True)
            dialog_window.destroy()

        def _no():
            result[0] = False
            if callback:
                callback(False)
            dialog_window.destroy()

        ctk.CTkButton(button_frame, text="Yes", fg_color=accent, text_color="white",
                      hover_color="#7C3AED", font=get_font(13, True), height=36,
                      command=_yes).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(button_frame, text="No", fg_color="#3a3a3f", text_color="white",
                      hover_color="#4a4a4f", font=get_font(13, True), height=36,
                      command=_no).pack(side="left", fill="x", expand=True, padx=(8, 0))
    else:
        ctk.CTkButton(button_frame, text="OK", fg_color=accent, text_color="white",
                      hover_color="#7C3AED", font=get_font(13, True), height=36,
                      command=dialog_window.destroy).pack(fill="x")

    dialog_window.protocol("WM_DELETE_WINDOW",
                            lambda: (result.__setitem__(0, False), dialog_window.destroy()))
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


def animate_height(widget, target_height, duration=200):
    """Smoothly animate a widget's `height` option to target_height (px).

    Uses `after` and small steps to interpolate. Non-blocking.
    """
    try:
        start = widget.winfo_height()
    except Exception:
        try:
            start = int(widget.cget('height') or 0)
        except Exception:
            start = 0
    steps = max(2, int(duration // 15))
    delta = target_height - start

    def step(i=1):
        t = i / steps
        h = int(_lerp(start, target_height, t))
        try:
            widget.configure(height=h)
        except Exception:
            pass
        if i < steps:
            widget.after(15, lambda: step(i + 1))

    step()


def animate_progress(bar, target, duration=400):
    """Animate a CTkProgressBar `bar` from current value to `target` (0..1)."""
    try:
        start = float(getattr(bar, '_value', bar._progress))
    except Exception:
        try:
            start = float(bar.get())
        except Exception:
            start = 0.0
    steps = max(2, int(duration // 15))

    def step(i=1):
        t = i / steps
        v = _lerp(start, target, t)
        try:
            bar.set(v)
            bar._value = v
        except Exception:
            pass
        if i < steps:
            bar.after(15, lambda: step(i + 1))

    step()


def apply_button_hover(root, hover_scale=1.03):
    """Placeholder function - no longer needed (button sizing conflicts disabled)."""
    pass


def fade_transition(app, new_frame, steps=12, on_shown=None):
    """Animate a window alpha fade-out/fade-in while swapping to new_frame.

    Lifts new_frame at the midpoint (while the window is fully transparent),
    then fades back in. Calls on_shown() once the transition completes.
    """
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

    def fade_out(i=0):
        try:
            app.attributes('-alpha', max(0.0, 1.0 - i / steps))
        except Exception:
            pass
        if i < steps:
            app.after(15, lambda: fade_out(i + 1))
        else:
            _swap()
            fade_in(0)

    def fade_in(i=0):
        try:
            app.attributes('-alpha', min(1.0, i / steps))
        except Exception:
            pass
        if i < steps:
            app.after(15, lambda: fade_in(i + 1))
        else:
            _call_shown()

    fade_out(0)

