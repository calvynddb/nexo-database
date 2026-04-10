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

    def create_topbar(self):
        """Create unified top navigation bar with logo, text, tabs, and controls."""
        # wrapper with margin
        topbar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        topbar_wrapper.grid(row=0, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_LG, SPACE_SM))
        topbar_wrapper.grid_columnconfigure(0, weight=1)
        
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
        
        # main container with three sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=(SPACE_LG, SPACE_LG), pady=(SPACE_SM, SPACE_SM))
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
        self._logo_img = logo_img  # store as instance variable
        
        # "nexo." text - bigger and bolder, centered vertically
        nexo_label = ctk.CTkLabel(left_section, text="nexo.", font=get_font(34, True), text_color=TITLE_COLOR)
        nexo_label.grid(row=0, column=1, sticky="ew")
        
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
        
        # login/logout button - bigger
        self.auth_btn = ctk.CTkButton(right_frame, text="Login", fg_color=BTN_PRIMARY_FG,
                          text_color="white", hover_color=BTN_PRIMARY_HOVER,
                                      font=get_font(12, True),
                          height=CONTROL_HEIGHT_LG, width=100, command=self.handle_login_click)
        self.auth_btn.pack(side="left", padx=0)

        # gear/admin button - only visible when logged in
        self._gear_icon = get_icon("settings", size=20, fallback_color=ACCENT_COLOR)
        self.gear_btn = ctk.CTkButton(right_frame, text="", image=self._gear_icon,
                                      width=44, height=44, fg_color=BTN_NEUTRAL_FG,
                                      hover_color=BTN_NEUTRAL_HOVER, border_width=0,
                                      command=self.open_admin_panel)
        # packed/forgotten dynamically by update_auth_button
        
        # update auth button state
        self.update_auth_button()

    def create_title_bar(self):
        """Create title bar with page title on left and action buttons on right."""
        # wrapper with margin - increased top margin for equal spacing
        title_bar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        title_bar_wrapper.grid(row=1, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_SM, SPACE_MD))
        title_bar_wrapper.grid_columnconfigure(0, weight=1)
        
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
        
        inner = ctk.CTkFrame(title_bar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=SPACE_LG, pady=(SPACE_MD, SPACE_MD))
        title_bar.grid_rowconfigure(0, weight=1)
        title_bar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=0)
        inner.grid_rowconfigure(0, weight=1)
        
        # left: page title - aligned left, bolder, lighter purple
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

    def open_admin_panel(self):
        """Open admin management panel for registering admins and changing credentials."""
        from frontend_ui.ui import DepthCard

        panel = ctk.CTkToplevel(self)
        panel.title("Admin Management")
        apply_window_icon(panel)
        panel.geometry("480x560")
        panel.configure(fg_color=BG_COLOR)
        panel.attributes('-topmost', True)
        panel.grab_set()
        panel.focus_force()
        panel.update_idletasks()
        x = (panel.winfo_screenwidth() // 2) - (panel.winfo_width() // 2)
        y = (panel.winfo_screenheight() // 2) - (panel.winfo_height() // 2)
        panel.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(panel, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text="Admin Management", font=get_font(18, True)).pack(anchor="w", pady=(0, 20))

        # --- register new admin ---
        ctk.CTkLabel(scroll, text="Register New Admin", font=get_font(14, True), text_color=ACCENT_COLOR).pack(anchor="w", pady=(0, 8))

        def _make_entry(parent, placeholder):
            e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=CONTROL_HEIGHT_MD,
                             fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                             border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
            e.pack(fill="x", pady=(0, 8))
            return e

        reg_user = _make_entry(scroll, "Username")
        reg_pass = ctk.CTkEntry(scroll, placeholder_text="Password", show="*", height=CONTROL_HEIGHT_MD,
                    fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                    border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        reg_pass.pack(fill="x", pady=(0, 8))
        reg_conf = ctk.CTkEntry(scroll, placeholder_text="Confirm password", show="*", height=CONTROL_HEIGHT_MD,
                    fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                    border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        reg_conf.pack(fill="x", pady=(0, 12))

        def _register():
            uname = reg_user.get().strip()
            pwd   = reg_pass.get()
            conf  = reg_conf.get()
            if not all([uname, pwd, conf]):
                self.controller.show_custom_dialog("Error", "Please fill all fields.", dialog_type="error")
                return
            if pwd != conf:
                self.controller.show_custom_dialog("Error", "Passwords do not match.", dialog_type="error")
                return

            from backend import validate_password

            ok, validation_msg = validate_password(pwd)
            if not ok:
                self.controller.show_custom_dialog("Error", validation_msg, dialog_type="error")
                return
            
            success, msg = self.controller.create_user(uname, pwd)
            if success:
                for w in [reg_user, reg_pass, reg_conf]:
                    w.delete(0, "end")
                self.controller.show_custom_dialog("Success", msg)
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")

        ctk.CTkButton(scroll, text="Register", height=CONTROL_HEIGHT_MD, font=get_font(13, True),
                  fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
                      command=_register).pack(fill="x", pady=(0, 20))

        # divider
        ctk.CTkFrame(scroll, height=2, fg_color=BORDER_COLOR).pack(fill="x", pady=(0, 20))

        # --- change credentials ---
        ctk.CTkLabel(scroll, text="Change Credentials", font=get_font(14, True), text_color=ACCENT_COLOR).pack(anchor="w", pady=(0, 8))

        chg_user = _make_entry(scroll, "Username to update")
        chg_old  = ctk.CTkEntry(scroll, placeholder_text="Current password", show="*", height=CONTROL_HEIGHT_MD,
                    fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                    border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        chg_old.pack(fill="x", pady=(0, 8))
        chg_new  = ctk.CTkEntry(scroll, placeholder_text="New password", show="*", height=CONTROL_HEIGHT_MD,
                    fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                    border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        chg_new.pack(fill="x", pady=(0, 8))
        chg_conf = ctk.CTkEntry(scroll, placeholder_text="Confirm new password", show="*", height=CONTROL_HEIGHT_MD,
                    fg_color=ENTRY_BG, border_width=BORDER_WIDTH_HAIRLINE,
                    border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        chg_conf.pack(fill="x", pady=(0, 12))

        def _change_creds():
            uname   = chg_user.get().strip()
            old_pwd = chg_old.get()
            new_pwd = chg_new.get()
            conf    = chg_conf.get()
            if not all([uname, old_pwd, new_pwd, conf]):
                self.controller.show_custom_dialog("Error", "Please fill all fields.", dialog_type="error")
                return
            if new_pwd != conf:
                self.controller.show_custom_dialog("Error", "New passwords do not match.", dialog_type="error")
                return

            from backend import validate_password

            ok, validation_msg = validate_password(new_pwd)
            if not ok:
                self.controller.show_custom_dialog("Error", validation_msg, dialog_type="error")
                return
            
            success, msg = self.controller.change_password(uname, old_pwd, new_pwd)
            if success:
                for w in [chg_user, chg_old, chg_new, chg_conf]:
                    w.delete(0, "end")
                self.controller.show_custom_dialog("Success", msg)
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")

        ctk.CTkButton(scroll, text="Update Password", height=CONTROL_HEIGHT_MD, font=get_font(13, True),
                  fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
                      command=_change_creds).pack(fill="x", pady=(0, 8))

        animate_toplevel_in(panel, x=x, y=y, duration_ms=get_motion_duration("dialog_open", 160))

    def open_settings(self):
        """Open Settings window."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        apply_window_icon(settings_window)
        settings_window.geometry("580x680")
        settings_window.configure(fg_color=BG_COLOR)
        settings_window.attributes('-topmost', True)
        settings_window.grab_set()
        settings_window.focus_force()
        
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(settings_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        from frontend_ui.ui import DepthCard
        settings_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=BORDER_WIDTH_HAIRLINE, border_color=BORDER_COLOR)
        settings_card.pack(fill="both", expand=True)
        frame = ctk.CTkScrollableFrame(settings_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(frame, text="Settings", font=get_font(22, True)).pack(anchor="w", pady=(0, 25))
        
        # appearance
        ctk.CTkLabel(frame, text="Appearance", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkLabel(frame, text="Theme", font=FONT_BOLD).pack(anchor="w", pady=(5, 4))
        theme_combo = ctk.CTkOptionMenu(frame, values=["Dark", "Light"], height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                                       fg_color=ACCENT_COLOR, button_color=ACCENT_COLOR,
                           button_hover_color=BTN_PRIMARY_HOVER, text_color=TEXT_PRIMARY)
        theme_combo.pack(fill="x", pady=(0, 8))
        # set current appearance
        try:
            theme_combo.set(ctk.get_appearance_mode())
        except Exception:
            pass
        # apply button to change theme immediately
        def _apply_theme():
            choice = theme_combo.get()
            self.apply_theme(choice)
        
        ctk.CTkButton(frame, text="Apply Theme", height=CONTROL_HEIGHT_MD, command=_apply_theme,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER).pack(fill="x", pady=(0, 10))
        
        # system
        ctk.CTkLabel(frame, text="System", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkCheckBox(frame, text="Enable Notifications", height=CONTROL_HEIGHT_SM, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Auto Backup on Exit", height=CONTROL_HEIGHT_SM, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Show Debug Info", height=CONTROL_HEIGHT_SM, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        
        # account
        ctk.CTkLabel(frame, text="Account", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Change Password", height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Manage Admins", height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER).pack(fill="x", pady=6)
        
        # data
        ctk.CTkLabel(frame, text="Data Management", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Create Backup", height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER,
                     command=lambda: self.controller.show_custom_dialog("Success", "Backup created successfully!")).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="View Backups", height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Export Data", height=CONTROL_HEIGHT_MD, font=FONT_MAIN,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color=BTN_PRIMARY_HOVER).pack(fill="x", pady=6)

        animate_toplevel_in(
            settings_window,
            x=x,
            y=y,
            duration_ms=get_motion_duration("dialog_open", 160),
        )

    def apply_theme(self, choice: str):
        """Apply appearance mode safely and notify all listeners."""
        try:
            mode = choice.lower() if isinstance(choice, str) else str(choice).lower()
            if mode not in ("dark", "light", "system"):
                mode = "dark"
            
            # set the appearance mode globally
            ctk.set_appearance_mode(mode)
            
            # notify all listeners of the theme change
            THEME_MANAGER.notify_theme_change(mode)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.controller.show_custom_dialog("Theme Error", f"Could not apply theme '{choice}': {e}")
            except Exception:
                pass

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

    def on_theme_change(self, mode: str):
        """Callback when theme changes - refreshes all visible views."""
        try:
            # update current view if it exists
            if self.current_view and self.current_view in self.views:
                view = self.views[self.current_view]
                # force re-render of the view
                if hasattr(view, 'refresh_table'):
                    view.refresh_table()
        except Exception as e:
            print(f"Error refreshing view on theme change: {e}")