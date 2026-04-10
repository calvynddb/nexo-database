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
    SHADOW_EDGE_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    SURFACE_SOFT,
    BORDER_WIDTH_HAIRLINE,
    RADIUS_LG,
    RADIUS_SM,
)


class DepthCard(ctk.CTkFrame):
    """Frame component with depth styling."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fg_color", PANEL_COLOR)
        kwargs.setdefault("corner_radius", RADIUS_LG)

        # Keep cards border-light and lifted by default for a minimal shadow look.
        if kwargs.get("border_width", 0) == 0:
            kwargs["border_width"] = BORDER_WIDTH_HAIRLINE

        if kwargs.get("border_color") in (None, BORDER_COLOR):
            kwargs["border_color"] = SHADOW_EDGE_COLOR

        super().__init__(*args, **kwargs)

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to this card."""
        self.configure(
            fg_color=tokens.get("PANEL_COLOR", PANEL_COLOR),
            border_color=tokens.get("SHADOW_EDGE_COLOR", SHADOW_EDGE_COLOR),
        )


class StatCard(DepthCard):
    """Reusable stat card matching the Students sidebar style.

    Parameters mirror the previous `stat_card` helper used in `StudentsView`.
    """
    def __init__(self, parent, icon_img, num, sub, *, height=120, **kwargs):
        super().__init__(
            parent,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_LG,
            border_width=BORDER_WIDTH_HAIRLINE,
            border_color=BORDER_COLOR,
            height=height,
            **kwargs,
        )
        self.pack(fill="x", pady=(0, 12))
        self.pack_propagate(False)
        self._icon_img = icon_img

        # center all content using a single inner frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self.inner = inner

        self.icon_frame = ctk.CTkFrame(inner, width=42, height=42, fg_color=SURFACE_SOFT, corner_radius=RADIUS_SM)
        self.icon_frame.pack(pady=(0, 4))
        self.icon_frame.pack_propagate(False)

        self.icon_label = ctk.CTkLabel(self.icon_frame, image=icon_img, text="")
        self.icon_label.image = icon_img
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

        self.value_label = ctk.CTkLabel(inner, text=num, font=get_font(24, True), text_color=TEXT_PRIMARY)
        self.value_label.pack()

        self.subtitle_label = ctk.CTkLabel(inner, text=sub, font=get_font(12), text_color=TEXT_MUTED)
        self.subtitle_label.pack()

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to stat card internals."""
        super().apply_theme_colors(tokens)
        self.icon_frame.configure(fg_color=tokens.get("SURFACE_SOFT", SURFACE_SOFT))
        self.value_label.configure(text_color=tokens.get("TEXT_PRIMARY", TEXT_PRIMARY))
        self.subtitle_label.configure(text_color=tokens.get("TEXT_MUTED", TEXT_MUTED))
