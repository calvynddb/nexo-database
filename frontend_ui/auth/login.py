"""
Login and authentication for nexo.
"""

import customtkinter as ctk

from config import (
    BG_COLOR,
    PANEL_COLOR,
    ACCENT_COLOR,
    TEXT_MUTED,
    BORDER_COLOR,
    FONT_BOLD,
    get_font,
    TEXT_PRIMARY,
    TITLE_COLOR,
    ENTRY_BG,
    BTN_PRIMARY_FG,
    BTN_PRIMARY_HOVER,
    BTN_SEGMENT_FG,
    BTN_SEGMENT_HOVER,
    BORDER_WIDTH_HAIRLINE,
    SPACE_SM,
    SPACE_MD,
    SPACE_LG,
    CONTROL_HEIGHT_MD,
    CONTROL_HEIGHT_LG,
    RADIUS_SM,
    RADIUS_MD,
    RADIUS_XL,
)
from frontend_ui.ui import DepthCard, get_icon, get_main_logo, apply_window_icon


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # center container
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="nsew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        # clean, flat card with depth effect - dark themed
        card = DepthCard(
            center_frame,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_MD,
            border_width=0,
            border_color=BORDER_COLOR,
            width=540,
            height=640,
        )
        card.grid(row=0, column=0, padx=SPACE_LG, pady=SPACE_LG)
        card.grid_propagate(False)
        card.pack_propagate(False)

        # logo - extra large for prominent display
        logo_frame = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0, border_width=0)
        logo_frame.pack(pady=(SPACE_LG, SPACE_MD), padx=SPACE_LG)
        
        # load main logo - extra big
        try:
            self._logo_img = get_main_logo(size=138)
            lbl = ctk.CTkLabel(logo_frame, image=self._logo_img, text="")
            lbl.image = self._logo_img
            lbl.pack(padx=SPACE_LG, pady=SPACE_MD)
        except Exception:
            ctk.CTkLabel(logo_frame, text="nexo", font=get_font(32, True), text_color=TITLE_COLOR).pack(padx=SPACE_LG, pady=SPACE_MD)

        ctk.CTkLabel(card, text="nexo", font=get_font(30, True), text_color=TITLE_COLOR).pack(pady=(0, 8))
        ctk.CTkLabel(card, text="Administrative Access", font=get_font(12), text_color=TEXT_MUTED).pack(pady=(0, SPACE_LG))

        self.username_entry = self.create_input(card, "Username", "👤  Enter your username")
        self.password_entry = self.create_input(card, "Password", "🔒  Enter your password", show="*")
        self.username_entry.bind("<Return>", lambda e: self.handle_login())
        self.password_entry.bind("<Return>", lambda e: self.handle_login())

        # templated login function with enhanced button
        ctk.CTkButton(
            card,
            text="Sign In",
            font=get_font(13, True),
            fg_color=BTN_PRIMARY_FG,
            text_color="white",
            hover_color=BTN_PRIMARY_HOVER,
            border_width=0,
            height=CONTROL_HEIGHT_LG,
            corner_radius=RADIUS_SM,
                      command=self.handle_login).pack(fill="x", padx=50, pady=(22, 40))

        ctk.CTkButton(
            card,
            text="Proceed as Administrator",
            font=get_font(12, True),
            fg_color=BTN_SEGMENT_FG,
            text_color="white",
            hover_color=BTN_SEGMENT_HOVER,
            border_width=0,
            height=CONTROL_HEIGHT_MD,
            corner_radius=RADIUS_SM,
            command=self.proceed_as_admin,
        ).pack(fill="x", padx=50, pady=(0, 20))

    def on_frame_shown(self):
        """Clear login fields when frame is shown (e.g. after logout)."""
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.username_entry.focus()


    def create_input(self, parent, label, placeholder, show=""):
        ctk.CTkLabel(parent, text=label.upper(), font=get_font(11, True), text_color=TEXT_MUTED).pack(anchor="w", padx=50, pady=(8, 4))
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=CONTROL_HEIGHT_LG,
            corner_radius=RADIUS_SM,
            border_width=BORDER_WIDTH_HAIRLINE,
            border_color=BORDER_COLOR,
            fg_color=ENTRY_BG,
            text_color=TEXT_PRIMARY,
            show=show,
        )
        entry.pack(fill="x", padx=50, pady=(0, 10))
        return entry

    def proceed_as_admin(self):
        """Bypass credential entry and continue in administrator mode."""
        self.controller.logged_in = True
        from frontend_ui.dashboard import DashboardFrame
        self.controller.show_frame(DashboardFrame)

    def handle_login(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get()
        
        if not user or not pwd:
            self.controller.show_custom_dialog("Error", "Please enter username and password", dialog_type="error")
            return
        
        authenticated = False
        try:
            from backend import get_session, verify_password
            from backend.models import User
            
            session = get_session()
            db_user = session.query(User).filter(User.username == user).first()
            session.close()
            
            if db_user and verify_password(pwd, db_user.salt, db_user.password):
                authenticated = True
        except Exception:
            pass
        
        if authenticated:
            self.controller.logged_in = True
            from frontend_ui.dashboard import DashboardFrame
            self.controller.show_frame(DashboardFrame)
        else:
            self.controller.show_custom_dialog("Error", "Invalid username or password", dialog_type="error")

    def handle_register(self):
        """Handle registration button press."""
        reg_window = ctk.CTkToplevel(self)
        reg_window.title("Register New Administrator")
        apply_window_icon(reg_window)
        reg_window.geometry("500x580")
        reg_window.configure(fg_color=BG_COLOR)
        reg_window.attributes('-topmost', True)
        reg_window.grab_set()
        reg_window.focus_force()
        
        reg_window.update_idletasks()
        x = (reg_window.winfo_screenwidth() // 2) - (reg_window.winfo_width() // 2)
        y = (reg_window.winfo_screenheight() // 2) - (reg_window.winfo_height() // 2)
        reg_window.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(reg_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)
        
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        frame = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_MD, pady=SPACE_SM)
        
        ctk.CTkLabel(frame, text="Register Administrator", 
                    font=get_font(16, True)).pack(anchor="w", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Full Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        name_entry = ctk.CTkEntry(frame, placeholder_text="Enter full name", height=CONTROL_HEIGHT_MD)
        name_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Username", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        username_entry = ctk.CTkEntry(frame, placeholder_text="Choose username", height=CONTROL_HEIGHT_MD)
        username_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Email", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        email_entry = ctk.CTkEntry(frame, placeholder_text="Enter email", height=CONTROL_HEIGHT_MD)
        email_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter password", show="*", height=CONTROL_HEIGHT_MD)
        pass_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Confirm Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        confirm_entry = ctk.CTkEntry(frame, placeholder_text="Confirm password", show="*", height=CONTROL_HEIGHT_MD)
        confirm_entry.pack(fill="x", pady=(0, 20))
        
        def register_user():
            name = name_entry.get().strip()
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = pass_entry.get()
            confirm = confirm_entry.get()
            
            if not all([name, username, email, password, confirm]):
                self.controller.show_custom_dialog("Error", "Please fill all fields", dialog_type="error")
                return
            
            if password != confirm:
                self.controller.show_custom_dialog("Error", "Passwords do not match", dialog_type="error")
                return

            from backend import validate_password
            ok, msg = validate_password(password)
            if not ok:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return

            success, msg = self.controller.create_user(username, password)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            
            self.controller.show_custom_dialog("Success", "Administrator registered successfully! Please log in.")
            reg_window.destroy()
        
        ctk.CTkButton(
            frame,
            text="Register",
            command=register_user,
            height=CONTROL_HEIGHT_MD,
            corner_radius=RADIUS_SM,
            border_width=0,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=FONT_BOLD,
        ).pack(fill="x")
