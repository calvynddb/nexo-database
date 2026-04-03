"""
Dashboard main frame and navigation for nexo.
"""

import customtkinter as ctk
import tkinter as tk


# optional plotting libraries removed from top-level to avoid extra dependency
# they are imported on-demand in views that need them.

from config import (
    BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, 
    FONT_MAIN, FONT_BOLD, COLOR_PALETTE, get_font, TEXT_PRIMARY, THEME_MANAGER
)
from frontend_ui.ui import DepthCard, get_icon, get_main_logo
from backend import create_backups
from frontend_ui.auth import LoginFrame


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with unified topbar, main content, and right sidebar."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_view = None

        # lazy-import views here (not at module level) so matplotlib/numpy
        # are not loaded until the dashboard is actually constructed.
        from frontend_ui.views.students import StudentsView
        from frontend_ui.views.programs import ProgramsView
        from frontend_ui.views.colleges import CollegesView
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

        # main container with left content and right sidebar
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        
        # left content area - reduced top padding since title_bar has bottom padding
        self.content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew", padx=15, pady=(5, 15))
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
        topbar_wrapper.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        topbar_wrapper.grid_columnconfigure(0, weight=1)
        
        topbar = DepthCard(topbar_wrapper, height=90, fg_color=PANEL_COLOR, corner_radius=15, 
                          border_width=2, border_color=BORDER_COLOR)
        topbar.pack(fill="both", expand=True)
        topbar.grid_propagate(False)
        
        # main container with three sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
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
        nexo_label = ctk.CTkLabel(left_section, text="nexo.", font=get_font(36, True), text_color="#9b8ba9")
        nexo_label.grid(row=0, column=1, sticky="ew")
        
        # center section: centralized navigation tabs with fixed sizing
        center_frame = ctk.CTkFrame(inner, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="nsew", padx=0)
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_columnconfigure(1, weight=1)
        center_frame.grid_columnconfigure(2, weight=1)
        
        self.nav_btns = {}
        
        # create small placeholder icons for tabs (kept as attributes to avoid gc)
        self._tab_icon_students = get_icon("users", size=20, fallback_color=ACCENT_COLOR)
        self._tab_icon_programs = get_icon("books", size=20, fallback_color="#6d5a8a")
        self._tab_icon_colleges = get_icon("building", size=20, fallback_color="#7a6a95")

        # students tab
        self.nav_btns[self._StudentsView] = ctk.CTkButton(
            center_frame,
            text="Students",
            image=self._tab_icon_students,
            compound="left",
            fg_color="#2a1f35",
            text_color=TEXT_PRIMARY,
            hover_color="#3a2f45",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            border_width=0,
            command=lambda: self.show_view(self._StudentsView)
        )
        self.nav_btns[self._StudentsView].grid(row=0, column=0, sticky="ew", padx=5)

        # programs tab
        self.nav_btns[self._ProgramsView] = ctk.CTkButton(
            center_frame,
            text="Programs",
            image=self._tab_icon_programs,
            compound="left",
            fg_color="#2a1f35",
            text_color=TEXT_PRIMARY,
            hover_color="#3a2f45",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            border_width=0,
            command=lambda: self.show_view(self._ProgramsView)
        )
        self.nav_btns[self._ProgramsView].grid(row=0, column=1, sticky="ew", padx=5)

        # colleges tab
        self.nav_btns[self._CollegesView] = ctk.CTkButton(
            center_frame,
            text="Colleges",
            image=self._tab_icon_colleges,
            compound="left",
            fg_color="#2a1f35",
            text_color=TEXT_PRIMARY,
            hover_color="#3a2f45",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            border_width=0,
            command=lambda: self.show_view(self._CollegesView)
        )
        self.nav_btns[self._CollegesView].grid(row=0, column=2, sticky="ew", padx=5)
        
        # right section: login/logout button
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(20, 0))
        
        # login/logout button - bigger
        self.auth_btn = ctk.CTkButton(right_frame, text="Login", fg_color=ACCENT_COLOR, 
                                      text_color="white", hover_color="#7C3AED", 
                                      font=get_font(12, True),
                                      height=45, width=100, command=self.handle_login_click)
        self.auth_btn.pack(side="left", padx=0)

        # gear/admin button - only visible when logged in
        self._gear_icon = get_icon("settings", size=20, fallback_color=ACCENT_COLOR)
        self.gear_btn = ctk.CTkButton(right_frame, text="", image=self._gear_icon,
                                      width=45, height=45, fg_color="#2a1f35",
                                      hover_color="#3a2f45", border_width=0,
                                      command=self.open_admin_panel)
        # packed/forgotten dynamically by update_auth_button
        
        # update auth button state
        self.update_auth_button()

    def create_title_bar(self):
        """Create title bar with page title on left and action buttons on right."""
        # wrapper with margin - increased top margin for equal spacing
        title_bar_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        title_bar_wrapper.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 10))
        title_bar_wrapper.grid_columnconfigure(0, weight=1)
        
        title_bar = DepthCard(title_bar_wrapper, height=90, fg_color=PANEL_COLOR, corner_radius=15,
                             border_width=1, border_color=BORDER_COLOR)
        title_bar.pack(fill="both", expand=True)
        title_bar.grid_propagate(False)
        
        inner = ctk.CTkFrame(title_bar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 15))
        title_bar.grid_rowconfigure(0, weight=1)
        title_bar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=0)
        inner.grid_rowconfigure(0, weight=1)
        
        # left: page title - aligned left, bolder, lighter purple
        self.title_label = ctk.CTkLabel(inner, text="Students",
                                       font=get_font(28, True),
                                       text_color="#9b8ba9",
                                       anchor="w")
        self.title_label.grid(row=0, column=0, sticky="ew", padx=(0, 20))
        
        # center: search bar
        self.search_entry = ctk.CTkEntry(inner, placeholder_text="Search", height=40,
                                         fg_color="#2A1F3D", border_color=BORDER_COLOR,
                                         text_color=TEXT_PRIMARY, font=("Century Gothic", 14))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", self.handle_search_dynamic)
        
        # right: button container
        button_container = ctk.CTkFrame(inner, fg_color="transparent")
        button_container.grid(row=0, column=2, sticky="e", padx=(0, 0))
        
        # refresh button with icon
        # use packaged icon asset for refresh (avoid absolute local paths)
        self._refresh_icon = get_icon("refresh", size=20, fallback_color=ACCENT_COLOR)
        self.refresh_btn = ctk.CTkButton(button_container, text="", image=self._refresh_icon,
                                        width=50, height=50, fg_color="#2a1f35",
                                        hover_color="#3a2f45", border_width=0, command=self.handle_refresh)
        self.refresh_btn.pack(side="left", padx=(0, 8))
        
        # add entry button
        self.add_btn = ctk.CTkButton(button_container, text="Add Entry", width=110, height=50,
                                    font=get_font(12, True),
                                    fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY,
                                    hover_color="#7C3AED",
                                    command=self.handle_add_entry)
        self.add_btn.pack(side="left", padx=(0, 0))
        
        # disable add button initially (guest mode)
        self.update_button_states()

    def update_button_states(self):
        """Update button states based on login status."""
        if not self.controller.logged_in:
            self.add_btn.configure(state="disabled", fg_color="#555555")
        else:
            self.add_btn.configure(state="normal", fg_color=ACCENT_COLOR)
    
    def handle_refresh(self):
        """Refresh the current view's data from SQLite and update table + sidebar."""
        self.controller.refresh_data()
        if self.current_view and self.current_view in self.views:
            view = self.views[self.current_view]
            view.refresh_table()
            if hasattr(view, 'refresh_sidebar'):
                try:
                    view.refresh_sidebar()
                except Exception:
                    pass
            self.search_entry.delete(0, "end")

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
        view = self.views[view_class]
        view.tkraise()
        self.current_view = view_class

        # update active tab styling
        for vc, btn in self.nav_btns.items():
            if vc == view_class:
                btn.configure(fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY)
            else:
                btn.configure(fg_color="#2a1f35", text_color=TEXT_PRIMARY)
        
        # update title and button label based on view
        self.update_title_card(view_class)
        
        # clear search on view change
        self.search_entry.delete(0, "end")
        
        self.views[view_class].refresh_table()
    
    def update_title_card(self, view_class):
        """Update title card label and button based on active view."""
        if view_class == self._StudentsView:
            self.title_label.configure(text="Students")
        elif view_class == self._ProgramsView:
            self.title_label.configure(text="Programs")
        elif view_class == self._CollegesView:
            self.title_label.configure(text="Colleges")

    def handle_search_dynamic(self, event):
        """Filter current view's table based on search query."""
        query = self.search_entry.get().strip().lower()
        
        if self.current_view:
            if len(query) < 1:
                self.views[self.current_view].refresh_table()
            else:
                self.views[self.current_view].filter_table(query)

    def open_admin_panel(self):
        """Open admin management panel for registering admins and changing credentials."""
        from frontend_ui.ui import DepthCard

        panel = ctk.CTkToplevel(self)
        panel.title("Admin Management")
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

        card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text="Admin Management", font=get_font(18, True)).pack(anchor="w", pady=(0, 20))

        # --- register new admin ---
        ctk.CTkLabel(scroll, text="Register New Admin", font=get_font(14, True), text_color=ACCENT_COLOR).pack(anchor="w", pady=(0, 8))

        def _make_entry(parent, placeholder):
            e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=38,
                             fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
            e.pack(fill="x", pady=(0, 8))
            return e

        reg_user = _make_entry(scroll, "Username")
        reg_pass = ctk.CTkEntry(scroll, placeholder_text="Password", show="*", height=38,
                                fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        reg_pass.pack(fill="x", pady=(0, 8))
        reg_conf = ctk.CTkEntry(scroll, placeholder_text="Confirm password", show="*", height=38,
                                fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
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
            if len(pwd) < 6:
                self.controller.show_custom_dialog("Error", "Password must be at least 6 characters.", dialog_type="error")
                return
            
            success, msg = self.controller.create_user(uname, pwd)
            if success:
                for w in [reg_user, reg_pass, reg_conf]:
                    w.delete(0, "end")
                self.controller.show_custom_dialog("Success", msg)
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")

        ctk.CTkButton(scroll, text="Register", height=38, font=get_font(13, True),
                      fg_color=ACCENT_COLOR, text_color="white", hover_color="#7C3AED",
                      command=_register).pack(fill="x", pady=(0, 20))

        # divider
        ctk.CTkFrame(scroll, height=2, fg_color=BORDER_COLOR).pack(fill="x", pady=(0, 20))

        # --- change credentials ---
        ctk.CTkLabel(scroll, text="Change Credentials", font=get_font(14, True), text_color=ACCENT_COLOR).pack(anchor="w", pady=(0, 8))

        chg_user = _make_entry(scroll, "Username to update")
        chg_old  = ctk.CTkEntry(scroll, placeholder_text="Current password", show="*", height=38,
                                fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        chg_old.pack(fill="x", pady=(0, 8))
        chg_new  = ctk.CTkEntry(scroll, placeholder_text="New password", show="*", height=38,
                                fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
        chg_new.pack(fill="x", pady=(0, 8))
        chg_conf = ctk.CTkEntry(scroll, placeholder_text="Confirm new password", show="*", height=38,
                                fg_color="#2A1F3D", border_color=BORDER_COLOR, text_color=TEXT_PRIMARY)
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
            if len(new_pwd) < 6:
                self.controller.show_custom_dialog("Error", "Password must be at least 6 characters.", dialog_type="error")
                return
            
            success, msg = self.controller.change_password(uname, old_pwd, new_pwd)
            if success:
                for w in [chg_user, chg_old, chg_new, chg_conf]:
                    w.delete(0, "end")
                self.controller.show_custom_dialog("Success", msg)
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")

        ctk.CTkButton(scroll, text="Update Password", height=38, font=get_font(13, True),
                      fg_color="#6d28d9", text_color="white", hover_color="#5b21b6",
                      command=_change_creds).pack(fill="x", pady=(0, 8))

    def open_settings(self):
        """Open Settings window."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
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
        settings_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        settings_card.pack(fill="both", expand=True)
        frame = ctk.CTkScrollableFrame(settings_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(frame, text="Settings", font=get_font(22, True)).pack(anchor="w", pady=(0, 25))
        
        # appearance
        ctk.CTkLabel(frame, text="Appearance", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkLabel(frame, text="Theme", font=FONT_BOLD).pack(anchor="w", pady=(5, 4))
        theme_combo = ctk.CTkOptionMenu(frame, values=["Dark", "Light"], height=40, font=FONT_MAIN,
                                       fg_color=ACCENT_COLOR, button_color=ACCENT_COLOR,
                                       button_hover_color="#7C3AED", text_color=TEXT_PRIMARY)
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
        
        ctk.CTkButton(frame, text="Apply Theme", height=36, command=_apply_theme,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=(0, 10))
        
        # system
        ctk.CTkLabel(frame, text="System", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkCheckBox(frame, text="Enable Notifications", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Auto Backup on Exit", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Show Debug Info", height=30, font=FONT_MAIN,
                       fg_color=ACCENT_COLOR, checkmark_color=BG_COLOR).pack(anchor="w", pady=6)
        
        # account
        ctk.CTkLabel(frame, text="Account", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Change Password", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Manage Admins", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        
        # data
        ctk.CTkLabel(frame, text="Data Management", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Create Backup", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED",
                     command=lambda: self.controller.show_custom_dialog("Success", "Backup created successfully!")).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="View Backups", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Export Data", height=40, font=FONT_MAIN,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, hover_color="#7C3AED").pack(fill="x", pady=6)

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
            self.update_button_states()
            self.update_auth_button()

    def update_auth_button(self):
        """Update the auth button based on login state."""
        if self.controller.logged_in:
            self.auth_btn.configure(text="Logout", fg_color="#c41e3a", hover_color="#a01830", 
                                    command=self.handle_logout)
            self.gear_btn.pack(side="left", padx=(8, 0))
        else:
            self.auth_btn.configure(text="Login", fg_color=ACCENT_COLOR, hover_color="#7C3AED", 
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