"""
admin entry screen for nexo.
"""

import customtkinter as ctk

from config import (
    BG_COLOR,
    PANEL_COLOR,
    TEXT_MUTED,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TITLE_COLOR,
    BTN_NEUTRAL_FG,
    get_font,
    BTN_PRIMARY_FG,
    BTN_PRIMARY_HOVER,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    CONTROL_HEIGHT_LG,
    RADIUS_SM,
    RADIUS_MD,
    THEME_MANAGER,
)
from frontend_ui.ui import DepthCard, get_main_logo


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
            height=420,
        )
        card.grid(row=0, column=0, padx=SPACE_LG, pady=SPACE_LG)
        card.grid_propagate(False)
        card.pack_propagate(False)
        self.card = card

        # logo - extra large for prominent display
        logo_frame = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0, border_width=0)
        logo_frame.pack(pady=(SPACE_MD, SPACE_SM), padx=SPACE_LG)

        try:
            self._logo_img = get_main_logo(size=118)
            lbl = ctk.CTkLabel(logo_frame, image=self._logo_img, text="")
            lbl.image = self._logo_img
            lbl.pack(padx=SPACE_LG, pady=SPACE_SM)
            self.logo_label = lbl
        except Exception:
            ctk.CTkLabel(logo_frame, text="nexo", font=get_font(32, True), text_color=TITLE_COLOR).pack(padx=SPACE_LG, pady=SPACE_MD)

        self.title_label = ctk.CTkLabel(card, text="nexo", font=get_font(30, True), text_color=TITLE_COLOR)
        self.title_label.pack(pady=(0, 6))
        self.subtitle_label = ctk.CTkLabel(card, text="Administrative Access", font=get_font(12), text_color=TEXT_MUTED)
        self.subtitle_label.pack(pady=(0, SPACE_MD))

        self.proceed_button = ctk.CTkButton(
            card,
            text="Proceed as Administrator",
            font=get_font(13, True),
            fg_color=BTN_PRIMARY_FG,
            text_color="white",
            hover_color=BTN_PRIMARY_HOVER,
            border_width=0,
            height=66,
            corner_radius=RADIUS_SM,
            command=self.proceed_as_admin,
        )
        self.proceed_button.pack(fill="x", padx=50, pady=(24, 24))

        THEME_MANAGER.register_listener(self.on_theme_change)
        self.bind("<Destroy>", self._on_destroy)

    def on_frame_shown(self):
        """focus the proceed button whenever this frame is shown."""
        self.proceed_button.focus()

    def proceed_as_admin(self):
        self.controller.logged_in = True
        from frontend_ui.dashboard import DashboardFrame
        self.controller.show_frame(DashboardFrame)

    def on_theme_change(self, _mode: str, _preset: int = 0, tokens: dict | None = None):
        self.apply_theme_colors(tokens or {})

    def apply_theme_colors(self, tokens: dict):
        if not tokens:
            return

        bg = tokens.get("BG_COLOR", BG_COLOR)
        panel = tokens.get("PANEL_COLOR", PANEL_COLOR)
        title = tokens.get("TITLE_COLOR", TITLE_COLOR)
        muted = tokens.get("TEXT_MUTED", TEXT_MUTED)
        primary = tokens.get("BTN_PRIMARY_FG", BTN_PRIMARY_FG)
        primary_hover = tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER)
        text = tokens.get("TEXT_PRIMARY", TEXT_PRIMARY)

        self.configure(fg_color=bg)
        self.card.configure(fg_color=panel, border_color=tokens.get("SHADOW_EDGE_COLOR", BORDER_COLOR))
        self.title_label.configure(text_color=title)
        self.subtitle_label.configure(text_color=muted)
        self.proceed_button.configure(
            fg_color=primary,
            hover_color=primary_hover,
            text_color=text,
            border_color=tokens.get("BORDER_COLOR", BORDER_COLOR),
        )

        if hasattr(self, "logo_label") and self.logo_label.winfo_exists():
            try:
                logo_img = get_main_logo(size=118)
                self.logo_label.configure(image=logo_img)
                self.logo_label.image = logo_img
            except Exception:
                pass

    def _on_destroy(self, event):
        if event.widget is self:
            THEME_MANAGER.unregister_listener(self.on_theme_change)
