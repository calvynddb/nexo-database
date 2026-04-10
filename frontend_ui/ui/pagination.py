"""
Shared pagination control for table views.
"""

import customtkinter as ctk

from config import (
    ACCENT_COLOR,
    TEXT_MUTED,
    BORDER_COLOR,
    TEXT_PRIMARY,
    BTN_SEGMENT_FG,
    BTN_SEGMENT_HOVER,
    ENTRY_BG,
    CONTROL_HEIGHT_SM,
    RADIUS_SM,
    get_font,
)


class PaginationControl(ctk.CTkFrame):
    """Reusable pagination control with first/prev/next/last and go-to-page."""

    def __init__(self, parent, on_page_change, slot_count: int = 3):
        super().__init__(parent, fg_color="transparent")
        self._on_page_change = on_page_change
        self.slot_count = max(1, int(slot_count))
        self.current_page = 1
        self.total_pages = 1

        self.first_btn = ctk.CTkButton(
            self,
            text="First",
            width=54,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self._go_first,
        )
        self.first_btn.pack(side="left", padx=(0, 6))

        self.prev_btn = ctk.CTkButton(
            self,
            text="Prev",
            width=52,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self._go_prev,
        )
        self.prev_btn.pack(side="left", padx=(0, 8))

        self.pages_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pages_frame.pack(side="left", padx=6)

        self.page_buttons = []
        for _ in range(self.slot_count):
            btn = ctk.CTkButton(
                self.pages_frame,
                text=" ",
                width=40,
                height=CONTROL_HEIGHT_SM,
                corner_radius=RADIUS_SM,
                border_width=0,
                border_color=BORDER_COLOR,
                fg_color=BTN_SEGMENT_FG,
                hover_color=BTN_SEGMENT_HOVER,
                text_color=TEXT_PRIMARY,
                font=get_font(12, True),
                command=lambda: None,
            )
            btn.pack(side="left", padx=2)
            self.page_buttons.append(btn)

        self.next_btn = ctk.CTkButton(
            self,
            text="Next",
            width=52,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self._go_next,
        )
        self.next_btn.pack(side="left", padx=(8, 6))

        self.last_btn = ctk.CTkButton(
            self,
            text="Last",
            width=54,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self._go_last,
        )
        self.last_btn.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(self, text="Go:", font=get_font(12), text_color=TEXT_MUTED).pack(side="left", padx=(0, 4))

        self.page_entry = ctk.CTkEntry(
            self,
            width=44,
            height=CONTROL_HEIGHT_SM,
            fg_color=ENTRY_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            font=get_font(12),
        )
        self.page_entry.pack(side="left", padx=(0, 4))
        self.page_entry.bind("<Return>", lambda _event: self.go_from_entry())

        self.go_btn = ctk.CTkButton(
            self,
            text="Go",
            width=40,
            height=CONTROL_HEIGHT_SM,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            corner_radius=RADIUS_SM,
            border_width=0,
            text_color="white",
            font=get_font(12, True),
            command=self.go_from_entry,
        )
        self.go_btn.pack(side="left")

    def _request_page(self, page: int):
        try:
            page = int(page)
        except Exception:
            return

        page = max(1, min(page, self.total_pages))
        if callable(self._on_page_change):
            self._on_page_change(page)

    def _go_first(self):
        self._request_page(1)

    def _go_prev(self):
        self._request_page(self.current_page - 1)

    def _go_next(self):
        self._request_page(self.current_page + 1)

    def _go_last(self):
        self._request_page(self.total_pages)

    def go_from_entry(self):
        text = self.page_entry.get().strip()
        try:
            page = int(text)
        except Exception:
            self.page_entry.delete(0, "end")
            return

        self._request_page(page)
        self.page_entry.delete(0, "end")

    def update(self, current_page: int, total_pages: int):
        try:
            total_pages = int(total_pages)
        except Exception:
            total_pages = 1
        try:
            current_page = int(current_page)
        except Exception:
            current_page = 1

        self.total_pages = max(1, total_pages)
        self.current_page = max(1, min(current_page, self.total_pages))

        half = self.slot_count // 2
        visible_pages = [
            (self.current_page - half) + idx
            for idx in range(self.slot_count)
        ]
        visible_pages = [page if 1 <= page <= self.total_pages else None for page in visible_pages]

        for idx, btn in enumerate(self.page_buttons):
            page_num = visible_pages[idx]
            if page_num is None:
                btn.configure(
                    text=" ",
                    state="disabled",
                    fg_color=BTN_SEGMENT_FG,
                    hover_color=BTN_SEGMENT_HOVER,
                    command=lambda: None,
                )
                continue

            is_current = page_num == self.current_page
            btn.configure(
                text=str(page_num),
                state="normal",
                fg_color=ACCENT_COLOR if is_current else BTN_SEGMENT_FG,
                hover_color=BTN_SEGMENT_HOVER,
                command=lambda page=page_num: self._request_page(page),
            )

        has_prev = self.current_page > 1
        has_next = self.current_page < self.total_pages
        self.first_btn.configure(state="normal" if has_prev else "disabled")
        self.prev_btn.configure(state="normal" if has_prev else "disabled")
        self.next_btn.configure(state="normal" if has_next else "disabled")
        self.last_btn.configure(state="normal" if has_next else "disabled")
