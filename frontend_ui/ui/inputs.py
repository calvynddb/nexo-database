"""
Input and entry widgets for EduManage SIS.
"""

import customtkinter as ctk
import tkinter as tk
import time
from config import (
    PANEL_COLOR,
    TEXT_PRIMARY,
    BORDER_COLOR,
    ENTRY_BG,
    SURFACE_HOVER,
    BTN_SEGMENT_FG,
    BTN_SEGMENT_HOVER,
    BORDER_WIDTH_HAIRLINE,
    CONTROL_HEIGHT_MD,
    CONTROL_HEIGHT_SM,
    RADIUS_SM,
    get_font,
)
from .utils import log_ui_timing


class SearchableComboBox(ctk.CTkFrame):
    """A combo box widget with search/type functionality and visual dropdown appearance."""
    def __init__(self, parent, options, **kwargs):
        super().__init__(parent, fg_color="transparent")

        self.options = [str(opt) for opt in options]
        self.selected_value = None
        self.dropdown = None
        self.list_frame = None
        self._dropdown_visible = False
        self._filtered_options = []
        self._highlighted_index = -1
        self._option_buttons = []
        self._search_after_id = None
        self._debounce_ms = 45
        self._max_visible_options = 8
        
        # main frame with entry and button
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="x")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)
        
        # text entry
        self.entry = ctk.CTkEntry(main_frame, placeholder_text=kwargs.get("placeholder", "Select..."),
                       height=kwargs.get("height", CONTROL_HEIGHT_MD), fg_color=ENTRY_BG,
                                   border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        # dropdown button with arrow
        self.dropdown_btn = ctk.CTkButton(main_frame, text="▼", width=40, height=kwargs.get("height", CONTROL_HEIGHT_MD),
                         fg_color=BTN_SEGMENT_FG, text_color=TEXT_PRIMARY,
                                         hover_color=BTN_SEGMENT_HOVER,
                                         border_width=0,
                                         command=self._toggle_dropdown)
        self.dropdown_btn.grid(row=0, column=1, sticky="e")

        # bind events
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._on_escape)
        self.bind("<Destroy>", lambda e: self._destroy_dropdown())

    def _dropdown_is_visible(self):
        if not self.dropdown or not self.dropdown.winfo_exists():
            return False
        try:
            return str(self.dropdown.state()) != "withdrawn"
        except Exception:
            return self._dropdown_visible

    def _on_key_release(self, event):
        """Filter options as user types, preserving typing continuity."""
        if event.keysym in (
            "Up", "Down", "Return", "KP_Enter", "Escape", "Tab",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
        ):
            return

        self._schedule_search()

    def _on_focus(self, event):
        """Show relevant options when focused."""
        typed = self.entry.get().strip()
        if typed:
            self._schedule_search(immediate=True)
            return

        if self.options:
            self._show_dropdown(self.options, preserve_cursor=True)

    def _on_focus_out(self, _event):
        self.after(120, self._close_dropdown_if_focus_lost)

    def _on_arrow_down(self, _event):
        if not self._dropdown_is_visible():
            self._schedule_search(immediate=True)
            return "break"
        self._move_highlight(1)
        return "break"

    def _on_arrow_up(self, _event):
        if not self._dropdown_is_visible():
            self._schedule_search(immediate=True)
            return "break"
        self._move_highlight(-1)
        return "break"

    def _on_enter(self, _event):
        if self._dropdown_is_visible():
            self._select_highlighted_option()
            return "break"
        return None

    def _on_escape(self, _event):
        if self._dropdown_is_visible():
            self._close_dropdown()
            return "break"
        return None

    def _schedule_search(self, immediate: bool = False):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None

        delay = 0 if immediate else self._debounce_ms
        self._search_after_id = self.after(delay, self._refresh_matches_from_entry)

    def _refresh_matches_from_entry(self):
        self._search_after_id = None
        typed = self.entry.get().strip()
        if not typed:
            self._close_dropdown()
            return

        matches = self._get_matches(typed)
        if not matches:
            self._close_dropdown()
            return

        caret_index = self.entry.index(tk.INSERT)
        self._show_dropdown(matches, preserve_cursor=True, caret_index=caret_index)

    def _get_matches(self, typed: str):
        typed_l = typed.lower()
        starts = [opt for opt in self.options if opt.lower().startswith(typed_l)]
        contains = [opt for opt in self.options if typed_l in opt.lower() and opt not in starts]
        return starts + contains

    def _toggle_dropdown(self):
        """Toggle dropdown visibility."""
        if self._dropdown_is_visible():
            self._close_dropdown()
        else:
            typed = self.entry.get().strip()
            if typed:
                matches = self._get_matches(typed)
            else:
                matches = list(self.options)

            if matches:
                caret_index = self.entry.index(tk.INSERT)
                self._show_dropdown(matches, preserve_cursor=True, caret_index=caret_index)

    def _show_dropdown(self, matches, preserve_cursor: bool = False, caret_index: int = None):
        """Display filtered dropdown menu."""
        started_at = time.perf_counter()
        if not self.dropdown or not self.dropdown.winfo_exists():
            self.dropdown = ctk.CTkToplevel(self.entry)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.attributes("-topmost", True)
            self.dropdown.configure(fg_color=PANEL_COLOR)

            self.list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR,
                                          border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR, corner_radius=RADIUS_SM)
            self.list_frame.pack(fill="both", expand=True)
        else:
            try:
                self.dropdown.deiconify()
            except Exception:
                pass

        self._dropdown_visible = True
        self._filtered_options = list(matches[: self._max_visible_options])
        if not self._filtered_options:
            self._close_dropdown()
            return

        self._render_dropdown_items()

        # position dropdown below entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        width = self.entry.winfo_width() + self.dropdown_btn.winfo_width() + 4

        display_count = min(len(self._filtered_options), self._max_visible_options)
        option_height = CONTROL_HEIGHT_SM + 2
        self.dropdown.geometry(f"{width}x{display_count * option_height + 8}+{x}+{y}")
        self.dropdown.lift()

        self._highlighted_index = 0 if self._filtered_options else -1
        self._update_highlight()

        if preserve_cursor and self.entry.winfo_exists():
            try:
                if caret_index is None:
                    caret_index = self.entry.index(tk.INSERT)
                self.entry.focus_set()
                self.entry.icursor(min(max(0, int(caret_index)), len(self.entry.get())))
            except Exception:
                pass

        log_ui_timing("dropdown.searchable", started_at, warn_ms=45)

    def _render_dropdown_items(self):
        visible = self._filtered_options

        while len(self._option_buttons) < len(visible):
            btn = ctk.CTkButton(
                self.list_frame,
                text="",
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_PRIMARY,
                hover_color=SURFACE_HOVER,
                height=CONTROL_HEIGHT_SM,
                corner_radius=0,
                font=get_font(13),
            )
            self._option_buttons.append(btn)

        for idx, option in enumerate(visible):
            btn = self._option_buttons[idx]
            btn.configure(text=option, command=lambda o=option: self._select_option(o))
            if not btn.winfo_manager():
                btn.pack(fill="x", padx=1, pady=1)

        for btn in self._option_buttons[len(visible):]:
            if btn.winfo_manager():
                btn.pack_forget()

    def _update_highlight(self):
        for idx, btn in enumerate(self._option_buttons[:len(self._filtered_options)]):
            fg = SURFACE_HOVER if idx == self._highlighted_index else "transparent"
            btn.configure(fg_color=fg)

    def _move_highlight(self, delta: int):
        count = len(self._filtered_options)
        if count <= 0:
            return

        if self._highlighted_index < 0:
            self._highlighted_index = 0
        else:
            self._highlighted_index = (self._highlighted_index + delta) % count
        self._update_highlight()

    def _select_highlighted_option(self):
        if not self._filtered_options:
            self._close_dropdown()
            return

        index = self._highlighted_index if self._highlighted_index >= 0 else 0
        index = min(index, len(self._filtered_options) - 1)
        self._select_option(self._filtered_options[index])

    def _select_option(self, option):
        """Select an option from dropdown."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, option)
        self.selected_value = option
        self._close_dropdown()

    def _close_dropdown_if_focus_lost(self):
        focus_widget = self.focus_get()
        if focus_widget == self.entry:
            return

        if self.dropdown and self.dropdown.winfo_exists() and focus_widget:
            try:
                if str(focus_widget).startswith(str(self.dropdown)):
                    return
            except Exception:
                pass

        self._close_dropdown()

    def _close_dropdown(self):
        """Close the dropdown menu."""
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.withdraw()
                self._dropdown_visible = False
                self._filtered_options = []
                self._highlighted_index = -1
            except Exception:
                self.dropdown.destroy()
                self.dropdown = None
                self.list_frame = None
                self._dropdown_visible = False
                self._filtered_options = []
                self._highlighted_index = -1

    def _destroy_dropdown(self):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None

        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.destroy()
            except Exception:
                pass
        self.dropdown = None
        self.list_frame = None
        self._option_buttons = []
        self._filtered_options = []
        self._highlighted_index = -1
        self._dropdown_visible = False

    def get(self):
        """Get the current value."""
        return self.entry.get().strip()

    def insert(self, index, value):
        """Insert value into entry."""
        value_str = str(value)
        self.entry.insert(index, value_str)
        self.selected_value = value_str

    def set(self, value):
        """Set the value."""
        self.entry.delete(0, tk.END)
        value_str = str(value)
        self.entry.insert(0, value_str)
        self.selected_value = value_str

    def set_options(self, options):
        """Update available options for autosuggest."""
        self.options = [str(opt) for opt in options]
        if self._dropdown_is_visible():
            typed = self.entry.get().strip()
            matches = self._get_matches(typed) if typed else list(self.options)
            if matches:
                self._show_dropdown(matches, preserve_cursor=True)
            else:
                self._close_dropdown()

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to entry and dropdown elements."""
        tokens = tokens or {}
        self.entry.configure(
            fg_color=tokens.get("ENTRY_BG", ENTRY_BG),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
        )
        self.dropdown_btn.configure(
            fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
        )

        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.configure(fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR))
        if self.list_frame and self.list_frame.winfo_exists():
            self.list_frame.configure(
                fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )
        for btn in self._option_buttons:
            if btn.winfo_exists():
                btn.configure(
                    text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                    hover_color=tokens.get("SURFACE_HOVER", SURFACE_HOVER),
                )


class StyledComboBox(ctk.CTkFrame):
    """A styled combo box widget matching SearchableComboBox appearance."""
    def __init__(self, parent, values, **kwargs):
        super().__init__(parent, fg_color="transparent")
        
        self.values = values
        self._value = None
        self.list_frame = None
        self._dropdown_visible = False
        
        # main frame with entry and button
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="x")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)
        
        # display label
        self.entry = ctk.CTkEntry(main_frame, placeholder_text=kwargs.get("placeholder", "Select..."),
                       height=kwargs.get("height", CONTROL_HEIGHT_MD), fg_color=ENTRY_BG,
                                   border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        # dropdown button with arrow
        self.dropdown_btn = ctk.CTkButton(main_frame, text="▼", width=40, height=kwargs.get("height", CONTROL_HEIGHT_MD),
                         fg_color=BTN_SEGMENT_FG, text_color=TEXT_PRIMARY,
                                         hover_color=BTN_SEGMENT_HOVER,
                                         border_width=0,
                                         command=self._show_menu)
        self.dropdown_btn.grid(row=0, column=1, sticky="e")
        
        self.dropdown = None
        self.bind("<Destroy>", lambda e: self._destroy_dropdown())

    def _dropdown_is_visible(self):
        if not self.dropdown or not self.dropdown.winfo_exists():
            return False
        try:
            return str(self.dropdown.state()) != "withdrawn"
        except Exception:
            return self._dropdown_visible
    
    def _show_menu(self):
        """Show dropdown menu."""
        if self._dropdown_is_visible():
            self._close_dropdown()
            return

        started_at = time.perf_counter()
        
        if not self.dropdown or not self.dropdown.winfo_exists():
            self.dropdown = ctk.CTkToplevel(self.entry)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.attributes("-topmost", True)
            self.dropdown.configure(fg_color=PANEL_COLOR)

            self.list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR,
                                           border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR, corner_radius=RADIUS_SM)
            self.list_frame.pack(fill="both", expand=True)
        else:
            try:
                self.dropdown.deiconify()
            except Exception:
                pass

        self._dropdown_visible = True

        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        # position dropdown below button
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        width = self.entry.winfo_width() + self.dropdown_btn.winfo_width() + 4
        
        display_count = min(len(self.values), 5)
        option_height = CONTROL_HEIGHT_SM + 2
        self.dropdown.geometry(f"{width}x{display_count * option_height + 8}+{x}+{y}")
        self.dropdown.lift()
        
        # add option buttons
        for val in self.values:
            btn = ctk.CTkButton(self.list_frame, text=val, anchor="w",
                               fg_color="transparent", text_color=TEXT_PRIMARY,
                               hover_color=SURFACE_HOVER, height=CONTROL_HEIGHT_SM, corner_radius=0,
                               font=get_font(13), command=lambda v=val: self._select_option(v))
            btn.pack(fill="x", padx=1, pady=1)

        log_ui_timing("dropdown.styled", started_at, warn_ms=45)
    
    def _select_option(self, value):
        """Select an option."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._value = value
        self._close_dropdown()

    def _close_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.withdraw()
                self._dropdown_visible = False
            except Exception:
                self.dropdown.destroy()
                self.dropdown = None
                self.list_frame = None
                self._dropdown_visible = False

    def _destroy_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.destroy()
            except Exception:
                pass
        self.dropdown = None
        self.list_frame = None
        self._dropdown_visible = False
    
    def get(self):
        """Get the current value."""
        return self.entry.get().strip()
    
    def set(self, value):
        """Set the value."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._value = value

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to entry and dropdown elements."""
        tokens = tokens or {}
        self.entry.configure(
            fg_color=tokens.get("ENTRY_BG", ENTRY_BG),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
        )
        self.dropdown_btn.configure(
            fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
        )

        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.configure(fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR))
        if self.list_frame and self.list_frame.winfo_exists():
            self.list_frame.configure(
                fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )
            for child in self.list_frame.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(
                        text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                        hover_color=tokens.get("SURFACE_HOVER", SURFACE_HOVER),
                    )


class SmartSearchEntry(ctk.CTkEntry):
    """Entry widget with smart dropdown suggestions."""
    def __init__(self, parent, options, placeholder="", **kwargs):
        super().__init__(parent, placeholder_text=placeholder, **kwargs)
        self.options = options
        self.dropdown = None
        self.list_frame = None
        self._dropdown_visible = False
        
        self.bind("<KeyRelease>", self._on_type)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", lambda e: self.after(200, self._close_dropdown))
        self.bind("<Destroy>", lambda e: self._destroy_dropdown())

    def _on_type(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
            
        typed = self.get().strip().lower()
        if not typed:
            self._close_dropdown()
            return

        matches = [opt for opt in self.options if typed in opt.lower()]
        
        if matches and self.focus_get() == self:
            self._show_dropdown(matches)
        else:
            self._close_dropdown()

    def _on_focus(self, event):
        """When entry gains focus, show a shortlist if options are many and input empty."""
        typed = self.get().strip().lower()
        if typed:
            return

        # show top N suggestions when focused and options exist
        if len(self.options) > 0:
            matches = self.options[:min(len(self.options), 10)]
            self._show_dropdown(matches)

    def _show_dropdown(self, matches):
        started_at = time.perf_counter()
        if not self.dropdown or not self.dropdown.winfo_exists():
            self.dropdown = ctk.CTkToplevel(self)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.attributes("-topmost", True)
            self.dropdown.configure(fg_color=PANEL_COLOR)

            self.list_frame = ctk.CTkFrame(self.dropdown, fg_color=PANEL_COLOR,
                                            border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR, corner_radius=RADIUS_SM)
            self.list_frame.pack(fill="both", expand=True)
        else:
            try:
                self.dropdown.deiconify()
            except Exception:
                pass

        self._dropdown_visible = True

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        width = self.winfo_width()
        
        display_count = min(len(matches), 5)
        option_height = CONTROL_HEIGHT_SM + 2
        self.dropdown.geometry(f"{width}x{display_count * option_height + 8}+{x}+{y}")
        self.dropdown.lift()

        for opt in matches:
            btn = ctk.CTkButton(self.list_frame, text=opt, anchor="w",
                                fg_color="transparent", text_color=TEXT_PRIMARY,
                                hover_color=SURFACE_HOVER, height=CONTROL_HEIGHT_SM, corner_radius=0,
                                command=lambda o=opt: self._select_option(o))
            btn.pack(fill="x", padx=5, pady=1)

        log_ui_timing("dropdown.smart-search", started_at, warn_ms=45)

    def _select_option(self, option):
        self.delete(0, tk.END)
        self.insert(0, option)
        self._close_dropdown()

    def _close_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.withdraw()
                self._dropdown_visible = False
            except Exception:
                self.dropdown.destroy()
                self.dropdown = None
                self.list_frame = None
                self._dropdown_visible = False

    def _destroy_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            try:
                self.dropdown.destroy()
            except Exception:
                pass
        self.dropdown = None
        self.list_frame = None
        self._dropdown_visible = False

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to search entry and dropdown."""
        tokens = tokens or {}
        self.configure(
            fg_color=tokens.get("ENTRY_BG", ENTRY_BG),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
        )

        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.configure(fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR))
        if self.list_frame and self.list_frame.winfo_exists():
            self.list_frame.configure(
                fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )
            for child in self.list_frame.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(
                        text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                        hover_color=tokens.get("SURFACE_HOVER", SURFACE_HOVER),
                    )
