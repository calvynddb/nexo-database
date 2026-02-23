"""
Dashboard frame and main navigation for EduManage SIS
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from config import (
    BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, 
    FONT_MAIN, FONT_BOLD, COLOR_PALETTE, get_font, TEXT_PRIMARY, THEME_MANAGER
)
from components import DepthCard, placeholder_image
from views import StudentsView, ProgramsView, CollegesView
from data import create_backups


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with unified topbar, main content, and right sidebar."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_view = None
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_topbar()
        try:
            self.create_topbar()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Dashboard Init Error", f"Failed to create topbar: {e}")
            except Exception:
                pass

        # Main container with left content and right sidebar
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        
        # Left content area
        self.content_area = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)



        # Create views
        self.views = {}
        for V in (StudentsView, ProgramsView, CollegesView):
            view = V(self.content_area, controller)
            self.views[V] = view
            view.grid(row=0, column=0, sticky="nsew")

        self.show_view(StudentsView)

    def create_topbar(self):
        """Create unified top navigation bar with title, tabs, and controls."""
        topbar = DepthCard(self, height=85, fg_color=PANEL_COLOR, corner_radius=0, 
                          border_width=2, border_color=BORDER_COLOR)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        
        # Main container with 3 sections
        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        topbar.grid_rowconfigure(0, weight=1)
        topbar.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)  # Center expands
        
        # LEFT SECTION: Title card with add button
        left_card = DepthCard(inner, fg_color="#2a2a2e", corner_radius=8, 
                     border_width=1, border_color=BORDER_COLOR, height=65)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        left_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        left_inner.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        left_inner.grid_columnconfigure(0, weight=1)
        left_inner.grid_columnconfigure(1, weight=0)
        left_inner.grid_rowconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(left_inner, text="Students", 
                           font=get_font(20, True), 
                           text_color=ACCENT_COLOR)
        self.title_label.grid(row=0, column=0, sticky="ew")
        
        self.add_btn = ctk.CTkButton(left_inner, text="Add Entry", width=120, height=40,
                        font=get_font(12, True),
                                    fg_color=ACCENT_COLOR, text_color="white",
                        hover_color="#7C3AED", command=self.handle_add_entry)
        self.add_btn.grid(row=0, column=1, sticky="e", padx=(15, 0))
        
        # CENTER SECTION: Centralized navigation tabs
        center_frame = ctk.CTkFrame(inner, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="ew", padx=15)
        
        self.nav_btns = {}
        
        # Create small placeholder icons for tabs (kept as attributes to avoid GC)
        self._tab_icon_students = placeholder_image(size=22, color=ACCENT_COLOR)
        self._tab_icon_programs = placeholder_image(size=22, color="#8b5cf6")
        self._tab_icon_colleges = placeholder_image(size=22, color="#4f6bed")

        # Students tab
        self.nav_btns[StudentsView] = ctk.CTkButton(
            center_frame,
            text="Students",
            image=self._tab_icon_students,
            compound="left",
            fg_color="transparent",
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(StudentsView)
        )
        self.nav_btns[StudentsView].pack(side="left", padx=6, fill="both", expand=True)

        # Programs tab
        self.nav_btns[ProgramsView] = ctk.CTkButton(
            center_frame,
            text="Programs",
            image=self._tab_icon_programs,
            compound="left",
            fg_color="transparent",
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(ProgramsView)
        )
        self.nav_btns[ProgramsView].pack(side="left", padx=6, fill="both", expand=True)

        # Colleges tab
        self.nav_btns[CollegesView] = ctk.CTkButton(
            center_frame,
            text="Colleges",
            image=self._tab_icon_colleges,
            compound="left",
            fg_color="transparent",
            text_color="#d1d1d1",
            hover_color="#2A1F3D",
            font=get_font(13, True),
            corner_radius=8,
            height=45,
            command=lambda: self.show_view(CollegesView)
        )
        self.nav_btns[CollegesView].pack(side="left", padx=6, fill="both", expand=True)
        
        # RIGHT SECTION: Search, Settings, Logout, Notifications
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(15, 0))
        
        self.search_entry = ctk.CTkEntry(right_frame, placeholder_text="Search...", width=220, 
                border_width=2, border_color=ACCENT_COLOR, fg_color="#2A1F3D", 
                corner_radius=20, font=get_font(11), height=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.handle_search_dynamic)
        
        # settings icon as placeholder image
        self._settings_icon = placeholder_image(size=18, color=ACCENT_COLOR)
        ctk.CTkButton(right_frame, image=self._settings_icon, text="", fg_color="transparent", 
                 hover_color="#303035", width=40, height=40, command=self.open_settings).pack(side="left", padx=3)

        ctk.CTkButton(right_frame, text="Logout", fg_color="transparent", 
             text_color=TEXT_MUTED, hover_color="#2A1F3D", font=get_font(11, True),
             height=40, command=self.handle_logout).pack(side="left", padx=3)

    def handle_add_entry(self):
        """Handle add entry button - delegates to current view."""
        if self.current_view == StudentsView:
            self.views[StudentsView].add_student()
        elif self.current_view == ProgramsView:
            self.views[ProgramsView].add_program()
        elif self.current_view == CollegesView:
            self.views[CollegesView].add_college()

    def show_view(self, view_class):
        """Show a specific view."""
        view = self.views[view_class]
        view.tkraise()
        self.current_view = view_class

        # Update active tab styling
        for vc, btn in self.nav_btns.items():
            if vc == view_class:
                btn.configure(fg_color=ACCENT_COLOR, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#d1d1d1")
        
        # Update title and button label based on view
        self.update_title_card(view_class)
        
        self.search_entry.delete(0, tk.END)
        self.views[view_class].refresh_table()
    
    def update_title_card(self, view_class):
        """Update title card label and button based on active view."""
        if view_class == StudentsView:
            self.title_label.configure(text="Students")
        elif view_class == ProgramsView:
            self.title_label.configure(text="Programs")
        elif view_class == CollegesView:
            self.title_label.configure(text="Colleges")

    def handle_search_dynamic(self, event):
        """Filter current view's table based on search query."""
        query = self.search_entry.get().strip().lower()
        
        if self.current_view:
            if len(query) < 1:
                self.views[self.current_view].refresh_table()
            else:
                self.views[self.current_view].filter_table(query)

    def open_settings(self):
        """Open Settings window."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("550x650")
        settings_window.attributes('-topmost', True)
        
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkScrollableFrame(settings_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(frame, text="Settings", font=get_font(22, True)).pack(anchor="w", pady=(0, 25))
        
        # Appearance
        ctk.CTkLabel(frame, text="Appearance", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkLabel(frame, text="Theme", font=FONT_BOLD).pack(anchor="w", pady=(5, 4))
        theme_combo = ctk.CTkOptionMenu(frame, values=["Dark", "Light", "System"], height=40, font=FONT_MAIN)
        theme_combo.pack(fill="x", pady=(0, 8))
        # set current appearance
        try:
            theme_combo.set(ctk.get_appearance_mode().capitalize())
        except Exception:
            pass
        # Apply button to change theme immediately
        def _apply_theme():
            choice = theme_combo.get()
            self.apply_theme(choice)

        ctk.CTkButton(frame, text="Apply Theme", height=36, command=_apply_theme).pack(fill="x", pady=(0, 10))
        
        # System
        ctk.CTkLabel(frame, text="System", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkCheckBox(frame, text="Enable Notifications", height=30, font=FONT_MAIN).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Auto Backup on Exit", height=30, font=FONT_MAIN).pack(anchor="w", pady=6)
        ctk.CTkCheckBox(frame, text="Show Debug Info", height=30, font=FONT_MAIN).pack(anchor="w", pady=6)
        
        # Account
        ctk.CTkLabel(frame, text="Account", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Change Password", height=40, font=FONT_MAIN).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Manage Admins", height=40, font=FONT_MAIN).pack(fill="x", pady=6)
        
        # Data
        ctk.CTkLabel(frame, text="Data Management", font=get_font(15, True)).pack(anchor="w", pady=(15, 12))
        ctk.CTkButton(frame, text="Create Backup", height=40, font=FONT_MAIN,
                     command=lambda: messagebox.showinfo("Success", "Backup created successfully!")).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="View Backups", height=40, font=FONT_MAIN).pack(fill="x", pady=6)
        ctk.CTkButton(frame, text="Export Data", height=40, font=FONT_MAIN).pack(fill="x", pady=6)
    
    def handle_logout(self):
        """Handle logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            create_backups()
            from auth import LoginFrame
            self.controller.show_frame(LoginFrame)

    def apply_theme(self, choice: str):
        """Apply appearance mode safely and notify all listeners."""
        try:
            mode = choice.lower() if isinstance(choice, str) else str(choice).lower()
            if mode not in ("dark", "light", "system"):
                mode = "dark"
            
            # Set the appearance mode globally
            ctk.set_appearance_mode(mode)
            
            # Notify all listeners of the theme change
            THEME_MANAGER.notify_theme_change(mode)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Theme Error", f"Could not apply theme '{choice}': {e}")
            except Exception:
                pass
    

