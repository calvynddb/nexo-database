"""
Card and container components for EduManage SIS.

Provides `DepthCard` as a thin wrapper around `CTkFrame` to keep card
styling centralized.
"""

import customtkinter as ctk
from config import (
    get_font,
    PANEL_COLOR,
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    SURFACE_SOFT,
    ACCENT_COLOR,
    BORDER_WIDTH_THIN,
    BORDER_WIDTH_STRONG,
    RADIUS_LG,
    RADIUS_SM,
)


class DepthCard(ctk.CTkFrame):
    """Frame component with depth styling."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fg_color", PANEL_COLOR)
        kwargs.setdefault("corner_radius", RADIUS_LG)
        kwargs.setdefault("border_width", BORDER_WIDTH_THIN)
        kwargs.setdefault("border_color", BORDER_COLOR)
        super().__init__(*args, **kwargs)


class StatCard(DepthCard):
    """Reusable stat card matching the Students sidebar style.

    Parameters mirror the previous `stat_card` helper used in `StudentsView`.
    """
    def __init__(self, parent, icon_img, num, sub, *, height=120, **kwargs):
        super().__init__(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_LG,
            border_width=BORDER_WIDTH_STRONG,
            border_color=BORDER_COLOR,
            height=height,
            **kwargs,
        )
        self.pack(fill="x", pady=(0, 12))
        self.pack_propagate(False)

        accent_bar = ctk.CTkFrame(self, fg_color=ACCENT_COLOR, height=3, corner_radius=0)
        accent_bar.pack(fill="x", padx=0, pady=(0, 8), side="top")

        # center all content using a single inner frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        icon_f = ctk.CTkFrame(inner, width=42, height=42, fg_color=SURFACE_SOFT, corner_radius=RADIUS_SM)
        icon_f.pack(pady=(0, 4))
        icon_f.pack_propagate(False)
        lbl = ctk.CTkLabel(icon_f, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(inner, text=num, font=get_font(24, True), text_color=TEXT_PRIMARY).pack()
        ctk.CTkLabel(inner, text=sub, font=get_font(12), text_color=TEXT_MUTED).pack()
