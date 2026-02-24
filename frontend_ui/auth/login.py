"""
Login and authentication for nexo.
"""

import customtkinter as ctk

from config import BG_COLOR, PANEL_COLOR, ACCENT_COLOR, TEXT_MUTED, BORDER_COLOR, FONT_BOLD, get_font, TEXT_PRIMARY
from frontend_ui.ui import DepthCard, get_icon, get_main_logo


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
        card = DepthCard(center_frame, fg_color=PANEL_COLOR, corner_radius=20, border_width=2, border_color=BORDER_COLOR, width=520, height=640)
        card.grid(row=0, column=0, padx=20, pady=20)
        card.grid_propagate(False)
        card.pack_propagate(False)

        # logo - extra large for prominent display
        logo_frame = ctk.CTkFrame(card, fg_color="transparent")
        logo_frame.pack(pady=(30, 25))
        
        # load main logo - extra big
        try:
            self._logo_img = get_main_logo(size=150)
            lbl = ctk.CTkLabel(logo_frame, image=self._logo_img, text="")
            lbl.image = self._logo_img
            lbl.pack()
        except Exception:
            ctk.CTkLabel(logo_frame, text="nexo", font=get_font(32, True), text_color=ACCENT_COLOR).pack()

        ctk.CTkLabel(card, text="nexo", font=get_font(28, True), text_color=TEXT_PRIMARY).pack(pady=(0, 8))
        ctk.CTkLabel(card, text="Please login to access the administrative features", font=get_font(12), text_color=TEXT_MUTED).pack(pady=(0, 30))

        self.username_entry = self.create_input(card, "Username", "👤  Enter your username")
        self.password_entry = self.create_input(card, "Password", "🔒  Enter your password", show="*")
        self.username_entry.bind("<Return>", lambda e: self.handle_login())
        self.password_entry.bind("<Return>", lambda e: self.handle_login())

        # templated login function with enhanced button
        ctk.CTkButton(card, text="Sign In", font=get_font(13, True), fg_color=ACCENT_COLOR, text_color="white", hover_color="#6d5a8a", height=48, corner_radius=10, 
                      command=self.handle_login).pack(fill="x", padx=50, pady=(22, 40))

    def on_frame_shown(self):
        """Clear login fields when frame is shown (e.g. after logout)."""
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.username_entry.focus()


    def create_input(self, parent, label, placeholder, show=""):
        ctk.CTkLabel(parent, text=label, font=get_font(12, True), text_color=TEXT_PRIMARY).pack(anchor="w", padx=50, pady=(10, 4))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=48, border_color=BORDER_COLOR, fg_color="#2A1F3D", text_color="#d1d1d1", show=show)
        entry.pack(fill="x", padx=50, pady=(0, 12))
        return entry

    def handle_login(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get()
        
        if not user or not pwd:
            self.controller.show_custom_dialog("Error", "Please enter username and password", dialog_type="error")
            return
        
        authenticated = False
        try:
            from backend import load_csv, verify_password, hash_password, save_csv
            users = load_csv('user')
            # auto-create default hashed admin if no users exist yet
            if not users:
                salt, pw_hash = hash_password('admin')
                users = [{'username': 'admin', 'salt': salt, 'password': pw_hash}]
                save_csv('user', users)
            authenticated = any(
                u.get('username') == user and
                verify_password(pwd, u.get('salt', ''), u.get('password', ''))
                for u in users
            )
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
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        frame = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(frame, text="Register Administrator", 
                    font=get_font(16, True)).pack(anchor="w", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Full Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        name_entry = ctk.CTkEntry(frame, placeholder_text="Enter full name", height=40)
        name_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Username", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        username_entry = ctk.CTkEntry(frame, placeholder_text="Choose username", height=40)
        username_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Email", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        email_entry = ctk.CTkEntry(frame, placeholder_text="Enter email", height=40)
        email_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter password", show="*", height=40)
        pass_entry.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(frame, text="Confirm Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 4))
        confirm_entry = ctk.CTkEntry(frame, placeholder_text="Confirm password", show="*", height=40)
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
            
            if len(password) < 6:
                self.controller.show_custom_dialog("Error", "Password must be at least 6 characters", dialog_type="error")
                return
            
            # check for duplicate username
            try:
                from backend import load_csv, save_csv
                existing = load_csv('user')
                if any(u.get('username') == username for u in existing):
                    self.controller.show_custom_dialog("Error", f"Username '{username}' is already taken.", dialog_type="error")
                    return
                existing.append({'name': name, 'username': username, 'email': email, 'password': password})
                save_csv('user', existing)
            except Exception as e:
                self.controller.show_custom_dialog("Error", f"Could not save user: {e}", dialog_type="error")
                return
            
            self.controller.show_custom_dialog("Success", "Administrator registered successfully! Please log in.")
            reg_window.destroy()
        
        ctk.CTkButton(frame, text="Register", command=register_user, height=40,
                       fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD).pack(fill="x")
