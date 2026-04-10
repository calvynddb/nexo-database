"""
Dashboard main frame and navigation for nexo.
"""

import customtkinter as ctk
import tkinter as tk
import time


# optional plotting libraries removed from top-level to avoid extra dependency
# they are imported on-demand in views that need them.

from config import (
    BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR,
    FONT_MAIN, FONT_BOLD, COLOR_PALETTE, get_font, get_motion_duration, TEXT_PRIMARY, THEME_MANAGER,
    apply_theme as apply_app_theme,
    get_theme_preference,
    THEME_PRESET_LABELS,
    THEME_PRESET_SWATCHES,
    TITLE_COLOR, ENTRY_BG, BTN_PRIMARY_FG, BTN_PRIMARY_HOVER, BTN_SECONDARY_FG,
    BTN_SECONDARY_HOVER, BTN_NEUTRAL_FG, BTN_NEUTRAL_HOVER, BTN_DISABLED_FG,
    SUCCESS_COLOR, SUCCESS_HOVER, DANGER_COLOR, DANGER_HOVER,
    CONTROL_HEIGHT_SM, CONTROL_HEIGHT_MD, CONTROL_HEIGHT_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    BORDER_WIDTH_HAIRLINE,
    SPACE_SM, SPACE_MD, SPACE_LG,
    SURFACE_SECTION,
    BTN_SEGMENT_FG, BTN_SEGMENT_HOVER,
)
from frontend_ui.ui import (
    DepthCard,
    get_icon,
    get_main_logo,
    apply_window_icon,
    SoftLoadingOverlay,
    animate_toplevel_in,
    log_ui_timing,
)
from backend import create_backups
from backend.services import FilterOrchestrationService, FilterStateService
from frontend_ui.auth import LoginFrame


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with unified topbar, main content, and right sidebar."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_view = None
        self.multi_edit_mode = False
        self.filter_panel_visible = False
        self.filter_vars = {}
        self.view_filter_state = {}
        self.view_search_state = {}
        self._search_after_id = None
        self._search_debounce_ms = max(90, int(get_motion_duration("filter_apply", 180)))
        self._is_building_filter_controls = False
        self._last_filter_signature_by_view = {}
        self._filter_controls_view = None
        self._filter_controls_data_signature = {}
        self._filter_schema_cache = {}
        self._filter_panel_after_id = None
        self._theme_window = None
        self._theme_controls = {}
        self._theme_flash = None

        # lazy-import views here (not at module level) so matplotlib/numpy
        # are not loaded until the dashboard is actually constructed.
        from frontend_ui.students import StudentsView
        from frontend_ui.programs import ProgramsView
        from frontend_ui.colleges import CollegesView
        self._StudentsView = StudentsView
        self._ProgramsView = ProgramsView
        self._CollegesView = CollegesView
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # register as theme listener for dynamic updates
        THEME_MANAGER.register_listener(self.on_theme_change)
        self.bind("<Destroy>", self._on_destroy)
        
        # initialize logged_in state from controller
        # (defaults to False for guest mode)

        self.create_topbar()
        self.create_title_bar()
        self.create_filter_panel()
        self.loading_overlay = SoftLoadingOverlay(
            self,
            min_visible_ms=max(40, int(get_motion_duration("loading_overlay", 130) * 0.5)),
        )

        # main container with left content and right sidebar
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        
        # left content area - reduced top padding since title_bar has bottom padding
        self.content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew", padx=SPACE_MD, pady=(5, 15))
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # create views
        self.views = {}
        for V in (self._StudentsView, self._ProgramsView, self._CollegesView):
            view = V(self.content_area, controller)
            self.views[V] = view
            view.grid(row=0, column=0, sticky="nsew")

        self.show_view(self._StudentsView)
        self.on_theme_change(
            THEME_MANAGER.get_current_mode(),
            THEME_MANAGER.get_current_preset(),
            THEME_MANAGER.get_current_tokens(),
        )

    def create_topbar(self):
        """Create unified top navigation bar with logo, text, tabs, and controls."""
        # wrapper with margin
        topbar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        topbar_wrapper.grid(row=0, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_LG, SPACE_SM))
        topbar_wrapper.grid_columnconfigure(0, weight=1)
        self.topbar_wrapper = topbar_wrapper
        
        topbar = DepthCard(
            topbar_wrapper,
            height=86,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_LG,
            border_width=0,
            border_color=BORDER_COLOR,
        )
        topbar.pack(fill="both", expand=True)
        topbar.grid_propagate(False)
        self.topbar_card = topbar
        
        # main container with three sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=(SPACE_LG, SPACE_LG), pady=(SPACE_SM, SPACE_SM))
        self.topbar_inner = inner
        topbar.grid_rowconfigure(0, weight=1)
        topbar.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)  # center expands
        
        # left section: logo and "nexo." text
        left_section = ctk.CTkFrame(inner, fg_color="transparent")
        left_section.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_section.grid_rowconfigure(0, weight=1)
        left_section.grid_columnconfigure(0, weight=0)
        left_section.grid_columnconfigure(1, weight=0)
        
        # load main logo - bigger
        logo_img = get_main_logo(size=80)
        logo_label = ctk.CTkLabel(left_section, image=logo_img, text="")
        logo_label.image = logo_img  # keep reference to avoid gc
        logo_label.grid(row=0, column=0, padx=(0, 12))
        self.logo_label = logo_label
        self._logo_img = logo_img  # store as instance variable
        
        # "nexo." text - bigger and bolder, centered vertically
        nexo_label = ctk.CTkLabel(left_section, text="nexo.", font=get_font(34, True), text_color=TITLE_COLOR)
        nexo_label.grid(row=0, column=1, sticky="ew")
        self.nexo_label = nexo_label
        
        # center section: centralized navigation tabs with fixed sizing
        center_frame = ctk.CTkFrame(inner, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="nsew", padx=0)

        nav_rail = ctk.CTkFrame(
            center_frame,
            fg_color=SURFACE_SECTION,
            corner_radius=RADIUS_MD,
            border_width=0,
            border_color=BORDER_COLOR,
        )
        nav_rail.grid(row=0, column=0, sticky="nsew", padx=(SPACE_SM, SPACE_SM))
        self.nav_rail = nav_rail
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        nav_rail.grid_rowconfigure(0, weight=1)
        nav_rail.grid_columnconfigure(0, weight=1)
        nav_rail.grid_columnconfigure(1, weight=1)
        nav_rail.grid_columnconfigure(2, weight=1)
        
        self.nav_btns = {}
        
        # create small placeholder icons for tabs (kept as attributes to avoid gc)
        self._tab_icon_students = get_icon("users", size=20, fallback_color=ACCENT_COLOR)
        self._tab_icon_programs = get_icon("books", size=20, fallback_color=ACCENT_COLOR)
        self._tab_icon_colleges = get_icon("building", size=20, fallback_color=ACCENT_COLOR)

        # students tab
        self.nav_btns[self._StudentsView] = ctk.CTkButton(
            nav_rail,
            text="Students",
            image=self._tab_icon_students,
            compound="left",
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            font=get_font(13, True),
            corner_radius=RADIUS_SM,
            height=CONTROL_HEIGHT_LG,
            border_width=0,
            border_color=BORDER_COLOR,
            command=lambda: self.show_view(self._StudentsView)
        )
        self.nav_btns[self._StudentsView].grid(row=0, column=0, sticky="nsew")

        # programs tab
        self.nav_btns[self._ProgramsView] = ctk.CTkButton(
            nav_rail,
            text="Programs",
            image=self._tab_icon_programs,
            compound="left",
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            font=get_font(13, True),
            corner_radius=RADIUS_SM,
            height=CONTROL_HEIGHT_LG,
            border_width=0,
            border_color=BORDER_COLOR,
            command=lambda: self.show_view(self._ProgramsView)
        )
        self.nav_btns[self._ProgramsView].grid(row=0, column=1, sticky="nsew")

        # colleges tab
        self.nav_btns[self._CollegesView] = ctk.CTkButton(
            nav_rail,
            text="Colleges",
            image=self._tab_icon_colleges,
            compound="left",
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            font=get_font(13, True),
            corner_radius=RADIUS_SM,
            height=CONTROL_HEIGHT_LG,
            border_width=0,
            border_color=BORDER_COLOR,
            command=lambda: self.show_view(self._CollegesView)
        )
        self.nav_btns[self._CollegesView].grid(row=0, column=2, sticky="nsew")
        
        # right section: login/logout button
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(20, 0))
        self.topbar_right_frame = right_frame
        
        # login/logout button - bigger
        self.auth_btn = ctk.CTkButton(right_frame, text="Login", fg_color=BTN_PRIMARY_FG,
                          text_color="white", hover_color=BTN_PRIMARY_HOVER,
                                      font=get_font(12, True),
                          height=CONTROL_HEIGHT_LG, width=100, command=self.handle_login_click)
        self.auth_btn.pack(side="left", padx=0)

        # gear/theme button - only visible when logged in
        self._gear_icon = get_icon("settings", size=20, fallback_color=ACCENT_COLOR)
        self.gear_btn = ctk.CTkButton(right_frame, text="", image=self._gear_icon,
                                      width=44, height=44, fg_color=BTN_NEUTRAL_FG,
                                      hover_color=BTN_NEUTRAL_HOVER, border_width=0,
                          command=self.open_theme_management)
        # packed/forgotten dynamically by update_auth_button
        
        # update auth button state
        self.update_auth_button()

    def create_title_bar(self):
        """Create title bar with page title on left and action buttons on right."""
        # wrapper with margin - increased top margin for equal spacing
        title_bar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        title_bar_wrapper.grid(row=1, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_SM, SPACE_MD))
        title_bar_wrapper.grid_columnconfigure(0, weight=1)
        self.title_bar_wrapper = title_bar_wrapper
        
        title_bar = DepthCard(
            title_bar_wrapper,
            height=86,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_LG,
            border_width=0,
            border_color=BORDER_COLOR,
        )
        title_bar.pack(fill="both", expand=True)
        title_bar.grid_propagate(False)
        self.title_bar_card = title_bar
        
        inner = ctk.CTkFrame(title_bar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=SPACE_LG, pady=(SPACE_MD, SPACE_MD))
        self.title_bar_inner = inner
        title_bar.grid_rowconfigure(0, weight=1)
        title_bar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=0)
        inner.grid_rowconfigure(0, weight=1)
        
        # left: page title - aligned left, bolder, theme-accented title tone
        self.title_label = ctk.CTkLabel(inner, text="Students",
                                       font=get_font(28, True),
                                       text_color=TITLE_COLOR,
                                       anchor="w")
        self.title_label.grid(row=0, column=0, sticky="ew", padx=(0, 20))
        
        # center: search bar
        self.search_entry = ctk.CTkEntry(inner, placeholder_text="Search", height=CONTROL_HEIGHT_MD,
                         fg_color=ENTRY_BG, border_color=BORDER_COLOR,
                         border_width=BORDER_WIDTH_HAIRLINE,
                         text_color=TEXT_PRIMARY, font=get_font(13))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, SPACE_MD))
        self.search_entry.bind("<KeyRelease>", self.handle_search_dynamic)
        
        # right: button container
        button_container = ctk.CTkFrame(inner, fg_color="transparent")
        button_container.grid(row=0, column=2, sticky="e", padx=(0, SPACE_SM))
        self.title_button_container = button_container
        
        # refresh button with icon
        # use packaged icon asset for refresh (avoid absolute local paths)
        self._refresh_icon = get_icon("refresh", size=20, fallback_color=ACCENT_COLOR)
        self.refresh_btn = ctk.CTkButton(button_container, text="", image=self._refresh_icon,
                                        width=46, height=CONTROL_HEIGHT_LG, fg_color=BTN_NEUTRAL_FG,
                                        hover_color=BTN_NEUTRAL_HOVER, border_width=0,
                                        corner_radius=RADIUS_SM, command=self.handle_refresh)
        self.refresh_btn.pack(side="left", padx=(0, 10))

        self.multi_edit_btn = ctk.CTkButton(
            button_container,
            text="Multi-Edit: Off",
            width=130,
            height=CONTROL_HEIGHT_LG,
            font=get_font(12, True),
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            command=self.toggle_multi_edit_mode,
        )
        self.multi_edit_btn.pack(side="left", padx=(0, 10))

        self.filter_btn = ctk.CTkButton(
            button_container,
            text="Filters: Off",
            width=120,
            height=CONTROL_HEIGHT_LG,
            font=get_font(12, True),
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            command=self.toggle_filter_panel,
        )
        self.filter_btn.pack(side="left", padx=(0, 10))
        
        # add entry button
        self.add_btn = ctk.CTkButton(button_container, text="Add Entry", width=110, height=CONTROL_HEIGHT_LG,
                                    font=get_font(12, True),
                        fg_color=BTN_PRIMARY_FG, text_color=TEXT_PRIMARY, corner_radius=RADIUS_SM,
                        border_width=0,
                        hover_color=BTN_PRIMARY_HOVER,
                                    command=self.handle_add_entry)
        self.add_btn.pack(side="left", padx=(0, 0))
        
        # disable add button initially (guest mode)
        self.update_button_states()

    def update_button_states(self):
        """Update button states based on login status."""
        if not self.controller.logged_in:
            self.add_btn.configure(state="disabled", fg_color=BTN_DISABLED_FG)
            self.multi_edit_btn.pack_forget()
            self.set_multi_edit_mode(False)
        else:
            self.add_btn.configure(state="normal", fg_color=BTN_PRIMARY_FG)
            if not self.multi_edit_btn.winfo_manager():
                self.multi_edit_btn.pack(side="left", padx=(0, 8), before=self.add_btn)
            self.multi_edit_btn.configure(state="normal")

    def create_filter_panel(self):
        """Initialize advanced filter popup state."""
        self.filter_window = None
        self.filter_card = None
        self.filter_title_label = None
        self.filter_summary_label = None
        self.apply_filters_btn = None
        self.reset_filters_btn = None
        self.hide_filters_btn = None
        self.filter_fields_frame = None

    def _ensure_filter_popup(self):
        window = getattr(self, "filter_window", None)
        if window is not None and window.winfo_exists():
            return

        window = ctk.CTkToplevel(self)
        window.title("Advanced Filters")
        apply_window_icon(window)
        window.configure(fg_color=BG_COLOR)
        window.attributes("-topmost", True)
        window.transient(self.winfo_toplevel())
        window.protocol("WM_DELETE_WINDOW", self.toggle_filter_panel)

        container = ctk.CTkFrame(window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        filter_card = DepthCard(
            container,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
        )
        filter_card.pack(fill="both", expand=True)
        self.filter_card = filter_card

        content = ctk.CTkFrame(filter_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACE_MD, pady=SPACE_SM)

        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        left_row = ctk.CTkFrame(top_row, fg_color="transparent")
        left_row.pack(side="left", fill="x", expand=True)

        self.filter_title_label = ctk.CTkLabel(
            left_row,
            text="Filters",
            font=get_font(12, True),
            text_color=TEXT_MUTED,
        )
        self.filter_title_label.pack(side="left", padx=(0, 8))

        self.filter_summary_label = ctk.CTkLabel(
            left_row,
            text="0 active · 0 results",
            font=get_font(11),
            text_color=TEXT_MUTED,
        )
        self.filter_summary_label.pack(side="left")

        action_row = ctk.CTkFrame(content, fg_color="transparent")
        action_row.pack(fill="x", pady=(8, 0))
        for col in range(3):
            action_row.grid_columnconfigure(col, weight=1)

        self.apply_filters_btn = ctk.CTkButton(
            action_row,
            text="Apply",
            width=82,
            height=CONTROL_HEIGHT_SM,
            font=get_font(11, True),
            fg_color=BTN_PRIMARY_FG,
            text_color="white",
            hover_color=BTN_PRIMARY_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            command=self.apply_current_filters,
        )
        self.apply_filters_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.reset_filters_btn = ctk.CTkButton(
            action_row,
            text="Reset",
            width=76,
            height=CONTROL_HEIGHT_SM,
            font=get_font(11, True),
            fg_color=BTN_SEGMENT_FG,
            text_color="white",
            hover_color=BTN_SEGMENT_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            command=self.reset_current_filters,
        )
        self.reset_filters_btn.grid(row=0, column=1, sticky="ew", padx=4)

        self.hide_filters_btn = ctk.CTkButton(
            action_row,
            text="Hide",
            width=70,
            height=CONTROL_HEIGHT_SM,
            font=get_font(11, True),
            fg_color=BTN_SEGMENT_FG,
            text_color=TEXT_PRIMARY,
            hover_color=BTN_SEGMENT_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            command=self.toggle_filter_panel,
        )
        self.hide_filters_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        self.filter_fields_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self.filter_fields_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.filter_window = window
        self._position_filter_popup()
        window.withdraw()

    def _position_filter_popup(self):
        window = getattr(self, "filter_window", None)
        if window is None or not window.winfo_exists():
            return

        try:
            self.update_idletasks()
            window.update_idletasks()
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            popup_width = min(screen_width - 40, max(360, min(440, int(self.winfo_width() * 0.34))))
            field_count = len(self.filter_vars) if self.filter_vars else 0
            if field_count <= 0:
                field_count = len(self._default_filter_state(self.current_view)) if self.current_view else 4
            visible_rows = min(max(2, field_count), 6)
            desired_height = 170 + (visible_rows * 58)
            popup_height = min(screen_height - 90, max(300, desired_height))
            x = max(20, (screen_width - popup_width) // 2)
            y = max(30, (screen_height - popup_height) // 2)
            window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        except Exception:
            pass

    def toggle_filter_panel(self):
        """Show or hide the advanced filter popup."""
        started_at = time.perf_counter()
        target_visible = not self.filter_panel_visible
        if not target_visible:
            # Persist while controls are still visible.
            self._persist_filter_state_from_widgets()

        self.filter_panel_visible = target_visible

        if self.filter_panel_visible:
            self._ensure_filter_popup()
            if self._needs_filter_rebuild(self.current_view):
                self._run_with_loading("Preparing filters", lambda: self._build_filter_controls(self.current_view))
            else:
                self._build_filter_controls(self.current_view)
            self._show_filter_panel_animated()
        else:
            self._hide_filter_panel_animated()

        if self.current_view:
            state = self._ensure_filter_state(self.current_view)
            self._update_filter_button_state(self._active_filter_count(state))
        else:
            self._update_filter_button_state(0)

        log_ui_timing("filters.toggle", started_at, warn_ms=70)

    def _cancel_filter_panel_animation(self):
        if self._filter_panel_after_id:
            try:
                self.after_cancel(self._filter_panel_after_id)
            except Exception:
                pass
            self._filter_panel_after_id = None

    def _show_filter_panel_animated(self):
        self._cancel_filter_panel_animation()
        window = getattr(self, "filter_window", None)
        if window is None or not window.winfo_exists():
            return
        self._position_filter_popup()
        window.deiconify()
        window.lift()
        window.focus_force()

    def _hide_filter_panel_animated(self):
        self._cancel_filter_panel_animation()
        window = getattr(self, "filter_window", None)
        if window is None or not window.winfo_exists():
            return
        window.withdraw()

    def _default_filter_state(self, view_class):
        view_key = self._resolve_filter_view_key(view_class)
        return FilterStateService.default_state(view_key)

    def _resolve_filter_view_key(self, view_class) -> str:
        return FilterStateService.resolve_view_key(
            view_class,
            self._StudentsView,
            self._ProgramsView,
            self._CollegesView,
        )

    def _get_filter_data_signature(self, view_class):
        view_key = self._resolve_filter_view_key(view_class)
        return FilterStateService.data_signature(
            view_key,
            self.controller.students,
            self.controller.programs,
            self.controller.colleges,
        )

    def _needs_filter_rebuild(self, view_class) -> bool:
        if not view_class:
            return False
        signature = self._get_filter_data_signature(view_class)
        return FilterOrchestrationService.should_rebuild_controls(
            self._filter_controls_view,
            self._filter_controls_data_signature,
            view_class,
            signature,
            bool(self.filter_vars),
        )

    def _run_with_loading(self, message: str, action):
        shown = {"value": False}
        show_after_id = {"value": None}

        def _show_overlay():
            shown["value"] = True
            show_after_id["value"] = None
            self.loading_overlay.show(message)

        # Avoid flashing/gaps for fast operations.
        show_delay_ms = max(60, int(get_motion_duration("loading_overlay", 130) * 0.7))
        show_after_id["value"] = self.after(show_delay_ms, _show_overlay)

        try:
            return action()
        finally:
            if show_after_id["value"]:
                try:
                    self.after_cancel(show_after_id["value"])
                except Exception:
                    pass
                show_after_id["value"] = None
            if shown["value"]:
                self.loading_overlay.hide()

    def _get_filter_schema(self, view_class, data_signature=None):
        view_key = self._resolve_filter_view_key(view_class)
        cache_key = (view_key, data_signature)
        if data_signature is not None and cache_key in self._filter_schema_cache:
            return self._filter_schema_cache[cache_key]

        schema = FilterStateService.schema(
            view_key,
            self.controller.students,
            self.controller.programs,
            self.controller.colleges,
        )
        if data_signature is not None:
            self._filter_schema_cache[cache_key] = schema
        return schema

    def _ensure_filter_state(self, view_class):
        defaults = self._default_filter_state(view_class)
        state = FilterStateService.ensure_state(self.view_filter_state.get(view_class, {}), defaults)
        self.view_filter_state[view_class] = state
        return state

    def _active_filter_count(self, state: dict) -> int:
        return FilterStateService.active_filter_count(state)

    def _update_filter_summary(self, view_class):
        summary_label = getattr(self, "filter_summary_label", None)
        if summary_label is None or not summary_label.winfo_exists():
            return
        if not view_class:
            summary_label.configure(text="0 active · 0 results")
            self._update_filter_button_state(0)
            return

        state = self._ensure_filter_state(view_class)
        active_count = self._active_filter_count(state)
        result_count = self._current_result_count(view_class)
        summary_label.configure(text=f"{active_count} active · {result_count} results")
        self._update_filter_button_state(active_count)

    def _current_result_count(self, view_class) -> int:
        if not view_class:
            return 0

        if view_class in self.views:
            rows = getattr(self.views[view_class], "_last_page_items", None)
            if rows is not None:
                return len(rows)

        if view_class == self._StudentsView:
            return len(self.controller.students)
        if view_class == self._ProgramsView:
            return len(self.controller.programs)
        if view_class == self._CollegesView:
            return len(self.controller.colleges)
        return 0

    def _update_filter_button_state(self, active_count: int):
        if not hasattr(self, "filter_btn"):
            return

        active_count = max(0, int(active_count))
        if self.filter_panel_visible:
            text = f"Filters: On ({active_count})" if active_count else "Filters: On"
            self.filter_btn.configure(text=text, fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER)
            return

        text = f"Filters: {active_count}" if active_count else "Filters: Off"
        self.filter_btn.configure(text=text, fg_color=BTN_NEUTRAL_FG, hover_color=BTN_NEUTRAL_HOVER)

    def _persist_search_state(self):
        if not self.current_view or not hasattr(self, "search_entry"):
            return
        self.view_search_state[self.current_view] = self.search_entry.get()

    def _restore_search_state(self, view_class):
        if not hasattr(self, "search_entry"):
            return

        query = self.view_search_state.get(view_class, "")
        self.search_entry.delete(0, "end")
        if query:
            self.search_entry.insert(0, query)

    def _schedule_filter_apply(self):
        if self._is_building_filter_controls:
            return
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(self._search_debounce_ms, lambda: self.apply_current_filters(force=False))

    def _on_filter_input_changed(self, _event=None):
        if self._is_building_filter_controls:
            return
        self._persist_filter_state_from_widgets()

    def _on_filter_option_changed(self, _value=None):
        if self._is_building_filter_controls:
            return
        self._persist_filter_state_from_widgets()

    def _persist_filter_state_from_widgets(self):
        if not self.filter_panel_visible:
            return
        if not self.current_view or not self.filter_vars:
            return
        state = self._ensure_filter_state(self.current_view)
        for key, var in self.filter_vars.items():
            value = var.get()
            state[key] = value.strip() if isinstance(value, str) else value
        self.view_filter_state[self.current_view] = state
        self._update_filter_summary(self.current_view)

    def _build_filter_controls(self, view_class):
        filter_fields_frame = getattr(self, "filter_fields_frame", None)
        filter_title_label = getattr(self, "filter_title_label", None)
        if (
            filter_fields_frame is None
            or not filter_fields_frame.winfo_exists()
            or filter_title_label is None
            or not filter_title_label.winfo_exists()
        ):
            return

        if not view_class:
            self.filter_vars = {}
            filter_title_label.configure(text="Filters")
            self._filter_controls_view = None
            self._update_filter_summary(None)
            return

        state = self._ensure_filter_state(view_class)
        data_signature = self._get_filter_data_signature(view_class)
        controls_unchanged = (
            self._filter_controls_view == view_class
            and self._filter_controls_data_signature.get(view_class) == data_signature
            and bool(self.filter_vars)
        )

        label = FilterStateService.view_label(self._resolve_filter_view_key(view_class))
        filter_title_label.configure(text=f"Filters · {label}")

        if controls_unchanged:
            self._is_building_filter_controls = True
            try:
                for key, var in self.filter_vars.items():
                    target = str(state.get(key, ""))
                    if var.get() != target:
                        var.set(target)
            finally:
                self._is_building_filter_controls = False
            self._update_filter_summary(view_class)
            return

        self._is_building_filter_controls = True
        try:
            for child in filter_fields_frame.winfo_children():
                child.destroy()
            self.filter_vars = {}
            schema = self._get_filter_schema(view_class, data_signature=data_signature)

            for field in schema:
                key = field["key"]

                cell = ctk.CTkFrame(filter_fields_frame, fg_color="transparent")
                cell.pack(fill="x", padx=2, pady=(0, 8))

                ctk.CTkLabel(
                    cell,
                    text=field["label"],
                    font=get_font(10, True),
                    text_color=TEXT_MUTED,
                    anchor="w",
                ).pack(fill="x", padx=(2, 0), pady=(0, 3))

                value = str(state.get(key, ""))
                var = tk.StringVar(value=value)
                self.filter_vars[key] = var

                if field["type"] == "combo":
                    values = field.get("values", ["Any"])
                    if value not in values:
                        var.set(values[0])
                    widget = ctk.CTkOptionMenu(
                        cell,
                        variable=var,
                        values=values,
                        height=32,
                        fg_color=ENTRY_BG,
                        button_color=BTN_PRIMARY_FG,
                        button_hover_color=BTN_PRIMARY_HOVER,
                        text_color=TEXT_PRIMARY,
                        font=get_font(11),
                        command=self._on_filter_option_changed,
                    )
                    widget.pack(fill="x")
                else:
                    widget = ctk.CTkEntry(
                        cell,
                        textvariable=var,
                        placeholder_text=field.get("placeholder", field["label"]),
                        height=32,
                        fg_color=ENTRY_BG,
                        border_width=BORDER_WIDTH_HAIRLINE,
                        border_color=BORDER_COLOR,
                        text_color=TEXT_PRIMARY,
                        font=get_font(11),
                    )
                    widget.pack(fill="x")
                    widget.bind("<Return>", self.apply_current_filters)
                    widget.bind("<KeyRelease>", self._on_filter_input_changed)
        finally:
            self._is_building_filter_controls = False

        self._filter_controls_view = view_class
        self._filter_controls_data_signature[view_class] = data_signature

        self._update_filter_summary(view_class)
        if self.filter_panel_visible:
            self._position_filter_popup()

    def apply_current_filters(self, _event=None, force: bool = False):
        """Apply active quick search and advanced filters to the active view."""
        self._search_after_id = None
        if not self.current_view or self.current_view not in self.views:
            return
        if self._is_building_filter_controls and not force:
            return

        started_at = time.perf_counter()

        self._persist_search_state()
        self._persist_filter_state_from_widgets()
        query = self.search_entry.get().strip().lower()
        filters = dict(self.view_filter_state.get(self.current_view, {}))

        signature = FilterOrchestrationService.normalized_apply_signature(query, filters)
        if FilterOrchestrationService.should_skip_apply(
            self._last_filter_signature_by_view,
            self.current_view,
            signature,
            force=force,
        ):
            self._update_filter_summary(self.current_view)
            return

        FilterOrchestrationService.record_apply_signature(
            self._last_filter_signature_by_view,
            self.current_view,
            signature,
        )
        view = self.views[self.current_view]

        if hasattr(view, "apply_filters"):
            view.apply_filters(query=query, advanced_filters=filters)
        elif query:
            view.filter_table(query)
        else:
            view.refresh_table()

        self._update_filter_summary(self.current_view)
        log_ui_timing(f"filters.apply.{type(view).__name__.lower()}", started_at, warn_ms=110)

    def reset_current_filters(self):
        """Reset advanced filters for the active view and re-apply search results."""
        if not self.current_view:
            return

        defaults = self._default_filter_state(self.current_view)
        self.view_filter_state[self.current_view] = dict(defaults)

        for key, var in self.filter_vars.items():
            var.set(str(defaults.get(key, "")))

        self.apply_current_filters(force=True)
    
    def handle_refresh(self):
        """Refresh the current view's data from SQLite and update table + sidebar."""
        def _refresh():
            self.controller.refresh_data()
            FilterOrchestrationService.clear_caches(
                self._filter_schema_cache,
                self._filter_controls_data_signature,
                self._last_filter_signature_by_view,
            )
            self._filter_controls_view = None
            if self.current_view and self.current_view in self.views:
                view = self.views[self.current_view]
                if self.filter_panel_visible:
                    self._build_filter_controls(self.current_view)
                self.apply_current_filters(force=True)
                if hasattr(view, 'refresh_sidebar'):
                    try:
                        view.refresh_sidebar()
                    except Exception:
                        pass

        self._run_with_loading("Refreshing view", _refresh)

    def handle_add_entry(self):
        """Handle add entry button - delegates to current view."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "Please log in first to add new entries.")
            self.handle_login_click()
            return
        
        if self.current_view == self._StudentsView:
            self.views[self._StudentsView].add_student()
        elif self.current_view == self._ProgramsView:
            self.views[self._ProgramsView].add_program()
        elif self.current_view == self._CollegesView:
            self.views[self._CollegesView].add_college()

    def show_view(self, view_class):
        """Show a specific view."""
        self._persist_search_state()
        self._persist_filter_state_from_widgets()
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None

        view = self.views[view_class]
        view.tkraise()
        self.current_view = view_class

        # update active tab styling
        for vc, btn in self.nav_btns.items():
            if vc == view_class:
                btn.configure(fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY)
            else:
                btn.configure(fg_color=BTN_SECONDARY_FG, hover_color=BTN_SECONDARY_HOVER, text_color=TEXT_PRIMARY)
        
        # update title and button label based on view
        self.update_title_card(view_class)

        self._restore_search_state(view_class)

        if hasattr(self.views[view_class], "set_multi_edit_mode"):
            self.views[view_class].set_multi_edit_mode(self.multi_edit_mode)

        def _apply_view_state():
            if self.filter_panel_visible:
                self._build_filter_controls(view_class)
            else:
                self.filter_vars = {}
                self._update_filter_summary(view_class)

            self.apply_current_filters(force=True)

        needs_filter_prepare = self.filter_panel_visible and self._needs_filter_rebuild(view_class)
        loading_message = "Preparing view" if needs_filter_prepare else "Switching view"
        self._run_with_loading(loading_message, _apply_view_state)
    
    def update_title_card(self, view_class):
        """Update title card label and button based on active view."""
        if view_class == self._StudentsView:
            self.title_label.configure(text="Students")
        elif view_class == self._ProgramsView:
            self.title_label.configure(text="Programs")
        elif view_class == self._CollegesView:
            self.title_label.configure(text="Colleges")

    def handle_search_dynamic(self, event):
        """Debounced live search; advanced filters apply via Apply button or Enter."""
        self._persist_search_state()
        self._schedule_filter_apply()

    def toggle_multi_edit_mode(self):
        """Toggle admin-only multi-edit mode for table views."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "Multi-edit mode is only available for admins.")
            return
        self.set_multi_edit_mode(not self.multi_edit_mode)

    def set_multi_edit_mode(self, enabled: bool):
        """Apply multi-edit mode state and propagate to child views."""
        enabled = bool(enabled and self.controller.logged_in)
        self.multi_edit_mode = enabled

        if enabled:
            self.multi_edit_btn.configure(text="Multi-Edit: On", fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER)
        else:
            self.multi_edit_btn.configure(text="Multi-Edit: Off", fg_color=BTN_SECONDARY_FG, hover_color=BTN_SECONDARY_HOVER)

        if hasattr(self, "views"):
            for view in self.views.values():
                if hasattr(view, "set_multi_edit_mode"):
                    view.set_multi_edit_mode(enabled)

    def open_theme_management(self):
        """Open Theme Management window with mode and preset controls."""
        existing = getattr(self, "_theme_window", None)
        if existing is not None and existing.winfo_exists():
            existing.deiconify()
            existing.lift()
            existing.focus_force()
            return

        theme_window = ctk.CTkToplevel(self)
        theme_window.title("Theme Management")
        apply_window_icon(theme_window)
        theme_window.geometry("520x420")
        theme_window.configure(fg_color=BG_COLOR)
        theme_window.attributes("-topmost", True)
        theme_window.grab_set()
        theme_window.focus_force()
        self._theme_window = theme_window

        def _on_close():
            try:
                theme_window.destroy()
            finally:
                self._theme_window = None
                self._theme_controls = {}

        theme_window.protocol("WM_DELETE_WINDOW", _on_close)

        theme_window.update_idletasks()
        x = (theme_window.winfo_screenwidth() // 2) - (theme_window.winfo_width() // 2)
        y = (theme_window.winfo_screenheight() // 2) - (theme_window.winfo_height() // 2)
        theme_window.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(theme_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        settings_card = DepthCard(
            container,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_MD,
            border_width=BORDER_WIDTH_HAIRLINE,
            border_color=BORDER_COLOR,
        )
        settings_card.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        title_label = ctk.CTkLabel(frame, text="Theme Management", font=get_font(22, True))
        title_label.pack(anchor="w", pady=(0, 2))

        subtitle_label = ctk.CTkLabel(
            frame,
            text="Apply a quick visual style update across the app.",
            font=get_font(12),
            text_color=TEXT_MUTED,
        )
        subtitle_label.pack(anchor="w", pady=(0, 18))

        mode_label = ctk.CTkLabel(frame, text="Appearance Mode", font=get_font(14, True), text_color=TEXT_MUTED)
        mode_label.pack(anchor="w", pady=(0, 6))
        mode_combo = ctk.CTkOptionMenu(
            frame,
            values=["Dark", "Light"],
            height=CONTROL_HEIGHT_MD,
            font=FONT_MAIN,
            fg_color=ACCENT_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color=BTN_PRIMARY_HOVER,
            text_color=TEXT_PRIMARY,
        )
        mode_combo.pack(fill="x", pady=(0, 14))

        current_mode, current_preset = get_theme_preference()
        mode_combo.set(current_mode.title())

        preset_label = ctk.CTkLabel(frame, text="Color Preset", font=get_font(14, True), text_color=TEXT_MUTED)
        preset_label.pack(anchor="w", pady=(0, 8))

        preset_row = ctk.CTkFrame(frame, fg_color="transparent")
        preset_row.pack(fill="x", pady=(0, 12))

        selected_preset = {"value": int(current_preset)}
        preset_buttons = {}

        def _refresh_preset_buttons():
            for idx, btn in preset_buttons.items():
                is_selected = idx == selected_preset["value"]
                btn.configure(
                    fg_color=THEME_PRESET_SWATCHES[idx],
                    hover_color=THEME_PRESET_SWATCHES[idx],
                    border_width=2 if is_selected else 1,
                    border_color=ACCENT_COLOR if is_selected else BORDER_COLOR,
                    text_color="white",
                )

        def _select_preset(preset_idx: int):
            selected_preset["value"] = int(preset_idx)
            _refresh_preset_buttons()

        for idx, label in THEME_PRESET_LABELS.items():
            btn = ctk.CTkButton(
                preset_row,
                text=label,
                width=100,
                height=42,
                corner_radius=RADIUS_SM,
                border_width=1,
                border_color=BORDER_COLOR,
                fg_color=THEME_PRESET_SWATCHES[idx],
                hover_color=THEME_PRESET_SWATCHES[idx],
                text_color="white",
                command=lambda p=idx: _select_preset(p),
            )
            btn.pack(side="left", padx=(0, 8) if idx < 3 else (0, 0))
            preset_buttons[idx] = btn

        _refresh_preset_buttons()

        hint_label = ctk.CTkLabel(
            frame,
            text="Themes apply instantly and are saved for the next app launch.",
            font=get_font(12),
            text_color=TEXT_MUTED,
            wraplength=440,
            justify="left",
        )
        hint_label.pack(anchor="w", pady=(0, 16))

        action_row = ctk.CTkFrame(frame, fg_color="transparent")
        action_row.pack(fill="x", pady=(4, 0))

        def _apply_theme_selection():
            self.apply_theme(mode_combo.get(), selected_preset["value"])

        apply_btn = ctk.CTkButton(
            action_row,
            text="Apply Theme",
            height=CONTROL_HEIGHT_MD,
            fg_color=ACCENT_COLOR,
            hover_color=BTN_PRIMARY_HOVER,
            text_color=TEXT_PRIMARY,
            command=_apply_theme_selection,
        )
        apply_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        close_btn = ctk.CTkButton(
            action_row,
            text="Close",
            height=CONTROL_HEIGHT_MD,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color=TEXT_PRIMARY,
            command=_on_close,
        )
        close_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self._theme_controls = {
            "window": theme_window,
            "card": settings_card,
            "title_label": title_label,
            "subtitle_label": subtitle_label,
            "mode_label": mode_label,
            "preset_label": preset_label,
            "hint_label": hint_label,
            "mode_combo": mode_combo,
            "preset_buttons": preset_buttons,
            "refresh_preset_buttons": _refresh_preset_buttons,
            "apply_btn": apply_btn,
            "close_btn": close_btn,
        }

        animate_toplevel_in(theme_window, x=x, y=y, duration_ms=get_motion_duration("dialog_open", 160))

    def open_settings(self):
        """Backward-compatible alias for opening theme management."""
        self.open_theme_management()

    def _show_theme_loading_flash(self):
        """Show loading overlay while a theme refresh is in progress."""
        existing = getattr(self, "_theme_flash", None)
        if existing is not None and existing.winfo_exists():
            try:
                existing.destroy()
            except Exception:
                pass

        flash = ctk.CTkToplevel(self)
        flash.overrideredirect(True)
        flash.attributes("-topmost", True)
        flash.configure(fg_color=BG_COLOR)
        self._theme_flash = flash

        root = self.winfo_toplevel()
        root.update_idletasks()
        width, height = 300, 110
        x = root.winfo_rootx() + (max(root.winfo_width(), width) - width) // 2
        y = root.winfo_rooty() + (max(root.winfo_height(), height) - height) // 2
        flash.geometry(f"{width}x{height}+{x}+{y}")
        flash.transient(self)
        flash.lift()
        flash.focus_force()

        shell = DepthCard(
            flash,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_MD,
            border_width=BORDER_WIDTH_HAIRLINE,
            border_color=BORDER_COLOR,
        )
        shell.pack(fill="both", expand=True, padx=6, pady=6)

        ctk.CTkLabel(
            shell,
            text="Applying theme...",
            font=get_font(13, True),
            text_color=TEXT_PRIMARY,
        ).pack(expand=True)

        try:
            flash.attributes("-alpha", 0.0)
        except Exception:
            return flash

        def _set_alpha(value: float):
            if flash.winfo_exists():
                try:
                    flash.attributes("-alpha", max(0.0, min(1.0, float(value))))
                except Exception:
                    pass

        def _fade(start: float, end: float, steps: int, duration_ms: int, on_done=None):
            step_count = max(1, int(steps))
            interval = max(10, int(duration_ms / step_count))

            def _tick(i=0):
                t = i / step_count
                _set_alpha(start + ((end - start) * t))
                if i < step_count and flash.winfo_exists():
                    flash.after(interval, lambda: _tick(i + 1))
                elif on_done:
                    on_done()

            _tick(0)

        _fade(0.0, 0.95, steps=6, duration_ms=130)
        return flash

    def _hide_theme_loading_flash(self, flash=None):
        """Fade out and close the active theme loading overlay."""
        target = flash or self._theme_flash
        if target is None or not target.winfo_exists():
            if flash is None:
                self._theme_flash = None
            return

        try:
            target.attributes("-alpha", 0.95)
        except Exception:
            pass

        def _set_alpha(value: float):
            if target.winfo_exists():
                try:
                    target.attributes("-alpha", max(0.0, min(1.0, float(value))))
                except Exception:
                    pass

        def _fade(start: float, end: float, steps: int, duration_ms: int, on_done=None):
            step_count = max(1, int(steps))
            interval = max(10, int(duration_ms / step_count))

            def _tick(i=0):
                t = i / step_count
                _set_alpha(start + ((end - start) * t))
                if i < step_count and target.winfo_exists():
                    target.after(interval, lambda: _tick(i + 1))
                elif on_done:
                    on_done()

            _tick(0)

        def _finish():
            if target.winfo_exists():
                try:
                    target.destroy()
                except Exception:
                    pass
            if self._theme_flash is target:
                self._theme_flash = None

        _fade(0.95, 0.0, steps=7, duration_ms=145, on_done=_finish)

    def _complete_theme_loading_after_refresh(self, flash, idle_passes: int = 2):
        """Close loading overlay after queued UI refresh work has flushed."""
        if flash is None or not flash.winfo_exists():
            return

        if idle_passes > 0:
            self.after_idle(lambda: self._complete_theme_loading_after_refresh(flash, idle_passes - 1))
            return

        self._hide_theme_loading_flash(flash)

    def apply_theme(self, choice: str, preset: int = 0):
        """Apply and persist app theme, showing loading until refresh finishes."""
        apply_btn = self._theme_controls.get("apply_btn")
        try:
            mode = choice.lower() if isinstance(choice, str) else str(choice).lower()
            if mode not in ("dark", "light"):
                mode = "dark"

            if apply_btn is not None and apply_btn.winfo_exists():
                apply_btn.configure(state="disabled", text="Applying...")

            flash = self._show_theme_loading_flash()
            apply_app_theme(mode, preset, persist=True, notify=True)

            refresher = self._theme_controls.get("refresh_preset_buttons")
            if callable(refresher):
                refresher()

            self.update_idletasks()
            self._complete_theme_loading_after_refresh(flash, idle_passes=2)
        except Exception as e:
            self._hide_theme_loading_flash()
            import traceback
            traceback.print_exc()
            try:
                self.controller.show_custom_dialog("Theme Error", f"Could not apply theme '{choice}': {e}")
            except Exception:
                pass
        finally:
            if apply_btn is not None and apply_btn.winfo_exists():
                apply_btn.configure(state="normal", text="Apply Theme")

    def handle_login_click(self):
        """Handle login button click - transition to LoginFrame."""
        self.controller.show_frame(LoginFrame)
    
    def on_frame_shown(self):
        """Called when this frame is shown - update button states."""
        self.update_button_states()
        self.update_auth_button()

    def handle_logout(self):
        """Handle logout."""
        self.controller.show_custom_dialog("Confirm Logout", "Are you sure you want to logout?", "yesno", 
                                          callback=self._confirm_logout)
    
    def _confirm_logout(self, result):
        """Confirm logout and stay on dashboard in view-only mode."""
        if result:
            create_backups()
            self.controller.logged_in = False
            self.set_multi_edit_mode(False)
            self.update_button_states()
            self.update_auth_button()

    def update_auth_button(self):
        """Update the auth button based on login state."""
        if self.controller.logged_in:
            self.auth_btn.configure(text="Logout", fg_color=DANGER_COLOR, hover_color=DANGER_HOVER,
                                    command=self.handle_logout)
            self.gear_btn.pack(side="left", padx=(8, 0))
        else:
            self.auth_btn.configure(text="Login", fg_color=BTN_PRIMARY_FG, hover_color=BTN_PRIMARY_HOVER,
                                    command=self.handle_login_click)
            self.gear_btn.pack_forget()

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to dashboard-level controls."""
        tokens = tokens or {}
        text_primary = tokens.get("TEXT_PRIMARY", TEXT_PRIMARY)

        self.configure(fg_color=tokens.get("BG_COLOR", BG_COLOR))

        if hasattr(self, "topbar_card") and self.topbar_card.winfo_exists():
            self.topbar_card.configure(
                fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
                border_color=tokens.get("SHADOW_EDGE_COLOR", BORDER_COLOR),
            )
        if hasattr(self, "title_bar_card") and self.title_bar_card.winfo_exists():
            self.title_bar_card.configure(
                fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
                border_color=tokens.get("SHADOW_EDGE_COLOR", BORDER_COLOR),
            )
        if hasattr(self, "nav_rail") and self.nav_rail.winfo_exists():
            self.nav_rail.configure(fg_color=tokens.get("SURFACE_SECTION", SURFACE_SECTION))
        if hasattr(self, "nexo_label") and self.nexo_label.winfo_exists():
            self.nexo_label.configure(text_color=tokens.get("TITLE_COLOR", TITLE_COLOR))

        self.search_entry.configure(
            fg_color=tokens.get("ENTRY_BG", ENTRY_BG),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=text_primary,
        )
        self.title_label.configure(text_color=tokens.get("TITLE_COLOR", TITLE_COLOR))

        self.refresh_btn.configure(
            fg_color=tokens.get("BTN_NEUTRAL_FG", BTN_NEUTRAL_FG),
            hover_color=tokens.get("BTN_NEUTRAL_HOVER", BTN_NEUTRAL_HOVER),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=text_primary,
        )
        self.gear_btn.configure(
            fg_color=tokens.get("BTN_NEUTRAL_FG", BTN_NEUTRAL_FG),
            hover_color=tokens.get("BTN_NEUTRAL_HOVER", BTN_NEUTRAL_HOVER),
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
        )
        self.multi_edit_btn.configure(
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            text_color=text_primary,
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
        )
        self.filter_btn.configure(
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            text_color=text_primary,
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
        )

        if self.multi_edit_mode:
            self.multi_edit_btn.configure(
                fg_color=tokens.get("SUCCESS_COLOR", SUCCESS_COLOR),
                hover_color=tokens.get("SUCCESS_HOVER", SUCCESS_HOVER),
            )
        else:
            self.multi_edit_btn.configure(
                fg_color=tokens.get("BTN_SECONDARY_FG", BTN_SECONDARY_FG),
                hover_color=tokens.get("BTN_SECONDARY_HOVER", BTN_SECONDARY_HOVER),
            )

        if self.filter_panel_visible:
            self.filter_btn.configure(
                fg_color=tokens.get("SUCCESS_COLOR", SUCCESS_COLOR),
                hover_color=tokens.get("SUCCESS_HOVER", SUCCESS_HOVER),
            )
        else:
            self.filter_btn.configure(
                fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
                hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            )

        self.add_btn.configure(
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            text_color=text_primary,
        )

        for vc, btn in self.nav_btns.items():
            btn.configure(
                text_color=text_primary,
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
                fg_color=tokens.get("ACCENT_COLOR", ACCENT_COLOR) if vc == self.current_view else tokens.get("BTN_SECONDARY_FG", BTN_SECONDARY_FG),
                hover_color=tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER) if vc == self.current_view else tokens.get("BTN_SECONDARY_HOVER", BTN_SECONDARY_HOVER),
            )

        if hasattr(self, "logo_label") and self.logo_label.winfo_exists():
            try:
                logo_img = get_main_logo(size=80)
                self.logo_label.configure(image=logo_img)
                self.logo_label.image = logo_img
                self._logo_img = logo_img
            except Exception:
                pass

        self.update_button_states()
        self.update_auth_button()

        if self.filter_window and self.filter_window.winfo_exists():
            self.filter_window.configure(fg_color=tokens.get("BG_COLOR", BG_COLOR))
        if self.filter_card and self.filter_card.winfo_exists():
            if hasattr(self.filter_card, "apply_theme_colors"):
                self.filter_card.apply_theme_colors(tokens)
            else:
                self.filter_card.configure(fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR))
        if self.filter_title_label and self.filter_title_label.winfo_exists():
            self.filter_title_label.configure(text_color=tokens.get("TEXT_MUTED", TEXT_MUTED))
        if self.filter_summary_label and self.filter_summary_label.winfo_exists():
            self.filter_summary_label.configure(text_color=tokens.get("TEXT_MUTED", TEXT_MUTED))
        if self.apply_filters_btn and self.apply_filters_btn.winfo_exists():
            self.apply_filters_btn.configure(
                fg_color=tokens.get("BTN_PRIMARY_FG", BTN_PRIMARY_FG),
                hover_color=tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER),
                text_color=text_primary,
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )
        if self.reset_filters_btn and self.reset_filters_btn.winfo_exists():
            self.reset_filters_btn.configure(
                fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
                hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
                text_color=text_primary,
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )
        if self.hide_filters_btn and self.hide_filters_btn.winfo_exists():
            self.hide_filters_btn.configure(
                fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
                hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
                text_color=text_primary,
                border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
            )

        theme_window = self._theme_controls.get("window")
        if theme_window is not None and theme_window.winfo_exists():
            theme_window.configure(fg_color=tokens.get("BG_COLOR", BG_COLOR))

            theme_card = self._theme_controls.get("card")
            if theme_card is not None and theme_card.winfo_exists():
                if hasattr(theme_card, "apply_theme_colors"):
                    theme_card.apply_theme_colors(tokens)
                else:
                    theme_card.configure(fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR))

            for label_key in ("title_label", "subtitle_label", "mode_label", "preset_label", "hint_label"):
                label_widget = self._theme_controls.get(label_key)
                if label_widget is None or not label_widget.winfo_exists():
                    continue
                if label_key == "title_label":
                    label_widget.configure(text_color=tokens.get("TITLE_COLOR", TITLE_COLOR))
                elif label_key in ("mode_label", "preset_label", "subtitle_label", "hint_label"):
                    label_widget.configure(text_color=tokens.get("TEXT_MUTED", TEXT_MUTED))

            mode_combo = self._theme_controls.get("mode_combo")
            if mode_combo is not None and mode_combo.winfo_exists():
                mode_combo.configure(
                    fg_color=tokens.get("ACCENT_COLOR", ACCENT_COLOR),
                    button_color=tokens.get("ACCENT_COLOR", ACCENT_COLOR),
                    button_hover_color=tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER),
                    text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                )

            apply_btn = self._theme_controls.get("apply_btn")
            if apply_btn is not None and apply_btn.winfo_exists():
                apply_btn.configure(
                    fg_color=tokens.get("ACCENT_COLOR", ACCENT_COLOR),
                    hover_color=tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER),
                    text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                    border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
                )

            close_btn = self._theme_controls.get("close_btn")
            if close_btn is not None and close_btn.winfo_exists():
                close_btn.configure(
                    fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
                    hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
                    text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY),
                    border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
                )

            refresh_presets = self._theme_controls.get("refresh_preset_buttons")
            if callable(refresh_presets):
                refresh_presets()

    def on_theme_change(self, mode: str, preset: int = 0, tokens: dict | None = None):
        """Callback when theme changes - recolor dashboard and child views."""
        try:
            resolved_tokens = tokens or THEME_MANAGER.get_current_tokens()
            self.apply_theme_colors(resolved_tokens)

            for view in self.views.values():
                if hasattr(view, "apply_theme_colors"):
                    view.apply_theme_colors(resolved_tokens)
                elif hasattr(view, "refresh_table"):
                    view.refresh_table()
        except Exception as e:
            print(f"Error refreshing view on theme change: {e}")

    def _on_destroy(self, event):
        if event.widget is self:
            if self._theme_flash is not None and self._theme_flash.winfo_exists():
                try:
                    self._theme_flash.destroy()
                except Exception:
                    pass
            self._theme_flash = None
            self._theme_controls = {}
            THEME_MANAGER.unregister_listener(self.on_theme_change)