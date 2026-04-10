"""Colleges list view canonical feature module."""
import customtkinter as ctk
import tkinter as tk
import time
from tkinter import ttk, filedialog, messagebox

from config import (
    FONT_MAIN, FONT_BOLD, BG_COLOR, PANEL_COLOR, ACCENT_COLOR,
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE, TEXT_PRIMARY,
    BTN_PRIMARY_FG, BTN_PRIMARY_HOVER, DANGER_COLOR, DANGER_HOVER,
    BTN_SEGMENT_FG, BTN_SEGMENT_HOVER,
    ENTRY_BG, TABLE_ODD_BG, TABLE_EVEN_BG, TABLE_HOVER_BG,
    CONTROL_HEIGHT_SM, CONTROL_HEIGHT_MD,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG,
)
from config import get_font
from frontend_ui.ui import DepthCard, PaginationControl, placeholder_image, setup_treeview_style, get_icon, apply_window_icon, animate_toplevel_in, log_ui_timing
from backend import validate_college
from backend.csv_io import read_csv_rows, write_csv_rows
from backend.services import ListPipelineService


class CollegesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.multi_edit_mode = False
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # store original column names
        self.current_page = 1
        self.page_size = 25
        self._last_page_items = []
        self.setup_ui()

    def setup_ui(self):
        table_container = DepthCard(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_LG,
            border_width=0,
            border_color=BORDER_COLOR,
        )
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))
        
        setup_treeview_style()
        cols = ("#", "College Code", "College Name")
        self.tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="tree headings",
            style="Treeview",
            height=12,
            selectmode="extended",
        )
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, minwidth=0, stretch=False, anchor="center")
        
        # store original column names and add sort hint
        for c in cols:
            self.column_names[c] = c.upper()
            self.tree.heading(c, text=c.upper() + " ⇅")
            self.tree.column(c, anchor="center", stretch=False, width=120)
        self.tree.pack(fill="both", expand=True, padx=SPACE_LG, pady=(SPACE_LG, SPACE_MD))
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.bind("<Double-1>", self.on_row_double_click)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._refresh_checkmarks())
        self.tree.tag_configure('odd', background=TABLE_ODD_BG)
        self.tree.tag_configure('even', background=TABLE_EVEN_BG)
        self.tree.tag_configure('hover', background=TABLE_HOVER_BG, foreground="#ffffff")

        # footer-style pagination controls pinned to the bottom of the view
        footer = DepthCard(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=RADIUS_MD,
            border_width=0,
            border_color=BORDER_COLOR,
            height=62,
        )
        footer.grid(row=2, column=0, sticky="ew", padx=(0, 25), pady=(SPACE_MD, 0))
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=0)
        footer.grid_columnconfigure(1, weight=1)

        self.table_container = table_container
        self.footer = footer
        self._last_hover = None
        self._page_render_after_id = None
        self._page_anim_after_id = None
        
        left_ctrl = ctk.CTkFrame(footer, fg_color="transparent")
        left_ctrl.grid(row=0, column=0, sticky="w", padx=(SPACE_LG, SPACE_SM), pady=SPACE_SM)

        self.pagination = PaginationControl(
            left_ctrl,
            on_page_change=self.goto_page,
            slot_count=3,
        )
        self.pagination.pack(side="left")
        
        right_ctrl = ctk.CTkFrame(footer, fg_color="transparent")
        right_ctrl.grid(row=0, column=1, sticky="e", padx=(SPACE_SM, SPACE_LG), pady=SPACE_SM)

        self.bulk_edit_btn = ctk.CTkButton(
            right_ctrl,
            text="Edit Selected",
            width=120,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.edit_selected_colleges,
        )

        self.bulk_delete_btn = ctk.CTkButton(
            right_ctrl,
            text="Delete Selected",
            width=130,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=DANGER_COLOR,
            hover_color=DANGER_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.delete_selected_colleges,
        )
        # entry count label
        self.entry_count_label = ctk.CTkLabel(right_ctrl, text="0 / 0", 
                                             font=get_font(13), text_color=TEXT_MUTED)
        self.entry_count_label.pack(side="left", padx=0)

        self.csv_import_btn = ctk.CTkButton(
            right_ctrl,
            text="Import CSV",
            width=96,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=BTN_SEGMENT_FG,
            hover_color=BTN_SEGMENT_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.import_csv,
        )
        self.csv_import_btn.pack(side="left", padx=(0, 8), before=self.entry_count_label)

        self.csv_export_btn = ctk.CTkButton(
            right_ctrl,
            text="Export CSV",
            width=96,
            height=CONTROL_HEIGHT_SM,
            corner_radius=RADIUS_SM,
            border_width=0,
            border_color=BORDER_COLOR,
            fg_color=ACCENT_COLOR,
            hover_color=BTN_PRIMARY_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.export_csv,
        )
        self.csv_export_btn.pack(side="left", padx=(0, 8), before=self.entry_count_label)

        # table_container configure binding will be set below after cards are created

        right_panel = ctk.CTkFrame(self, width=320, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel = right_panel
        
        self.refresh_sidebar()

        # keep sidebar cards the same total height as the table by updating on resize
        def _on_table_config(e):
            total = max(e.width - 20, 200)
            props = [0.06, 0.32, 0.62]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 60))
            self._on_table_configure(e)
            self._update_sidebar_heights()

        table_container.bind('<Configure>', _on_table_config)

        self.refresh_table()

    def fact_card(self, parent, title, val, icon_img, color, height=80, expand=False):
        card = DepthCard(parent, fg_color=color, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR, height=height)
        if expand:
            card.pack(fill="both", expand=True, pady=8)
        else:
            card.pack(fill="x", pady=8)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=get_font(13, True), text_color=ACCENT_COLOR).place(x=15, y=14)
        ctk.CTkLabel(card, text=val, font=get_font(22, True)).place(x=15, y=36)
        lbl = ctk.CTkLabel(card, image=icon_img, text="")
        lbl.image = icon_img
        lbl.place(relx=0.85, rely=0.5, anchor="center")

    def refresh_table(self):
        rows = ListPipelineService.college_rows(self.controller.colleges)
        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
        self._last_hover = None

    def apply_theme_colors(self, tokens: dict):
        """Apply resolved theme tokens to the currently mounted colleges view."""
        tokens = tokens or {}
        panel = tokens.get("PANEL_COLOR", PANEL_COLOR)
        text_primary = tokens.get("TEXT_PRIMARY", TEXT_PRIMARY)
        text_muted = tokens.get("TEXT_MUTED", TEXT_MUTED)
        border = tokens.get("BORDER_COLOR", BORDER_COLOR)

        if hasattr(self.table_container, "apply_theme_colors"):
            self.table_container.apply_theme_colors(tokens)
        else:
            self.table_container.configure(fg_color=panel, border_color=border)

        if hasattr(self.footer, "apply_theme_colors"):
            self.footer.apply_theme_colors(tokens)
        else:
            self.footer.configure(fg_color=panel, border_color=border)

        self.entry_count_label.configure(text_color=text_muted)

        self.csv_import_btn.configure(
            fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            border_color=border,
            text_color=text_primary,
        )
        self.csv_export_btn.configure(
            fg_color=tokens.get("ACCENT_COLOR", ACCENT_COLOR),
            hover_color=tokens.get("BTN_PRIMARY_HOVER", BTN_PRIMARY_HOVER),
            border_color=border,
            text_color=text_primary,
        )
        self.bulk_edit_btn.configure(
            fg_color=tokens.get("BTN_SEGMENT_FG", BTN_SEGMENT_FG),
            hover_color=tokens.get("BTN_SEGMENT_HOVER", BTN_SEGMENT_HOVER),
            border_color=border,
            text_color=text_primary,
        )
        self.bulk_delete_btn.configure(
            fg_color=tokens.get("DANGER_COLOR", DANGER_COLOR),
            hover_color=tokens.get("DANGER_HOVER", DANGER_HOVER),
            border_color=border,
            text_color=text_primary,
        )

        if hasattr(self, "pagination") and hasattr(self.pagination, "apply_theme_colors"):
            self.pagination.apply_theme_colors(tokens)

        setup_treeview_style()
        self.tree.tag_configure("odd", background=tokens.get("TABLE_ODD_BG", TABLE_ODD_BG))
        self.tree.tag_configure("even", background=tokens.get("TABLE_EVEN_BG", TABLE_EVEN_BG))
        self.tree.tag_configure(
            "hover",
            background=tokens.get("TABLE_HOVER_BG", TABLE_HOVER_BG),
            foreground=tokens.get("TEXT_PRIMARY", "#ffffff"),
        )

        self.refresh_sidebar()
        self.refresh_table()

    def _animate_page_flip(self):
        if self._page_anim_after_id:
            try:
                self.after_cancel(self._page_anim_after_id)
            except Exception:
                pass
            self._page_anim_after_id = None

        try:
            self.table_container.configure(fg_color=TABLE_HOVER_BG)
        except Exception:
            return

        def _restore():
            self._page_anim_after_id = None
            try:
                self.table_container.configure(fg_color=PANEL_COLOR)
            except Exception:
                pass

        self._page_anim_after_id = self.after(85, _restore)

    def _request_page_render(self):
        if self._page_render_after_id:
            try:
                self.after_cancel(self._page_render_after_id)
            except Exception:
                pass
            self._page_render_after_id = None

        self._page_render_after_id = self.after(18, self._perform_page_render)

    def _perform_page_render(self):
        self._page_render_after_id = None
        self._render_page()
        self._animate_page_flip()

    def _render_page(self):
        started_at = time.perf_counter()
        total = len(self._last_page_items)
        per = self.page_size
        total_pages = max(1, (total + per - 1) // per)
        self.current_page = min(self.current_page, total_pages)
        start = (self.current_page - 1) * per
        end = min(start + per, total)
        page_rows = self._last_page_items[start:end]

        tree_items = list(self.tree.get_children())
        while len(tree_items) < len(page_rows):
            tree_items.append(self.tree.insert("", "end"))

        for idx, row in enumerate(page_rows):
            tag = 'even' if idx % 2 == 0 else 'odd'
            self.tree.item(
                tree_items[idx],
                text=("☐" if self.multi_edit_mode else ""),
                values=row,
                tags=(tag,),
            )

        for stale in tree_items[len(page_rows):]:
            self.tree.delete(stale)

        self._refresh_checkmarks()
        
        # update entry count - show range (e.g., "Showing 1-12 of 100 entries")
        if total > 0:
            display_text = f"{start + 1}-{end} / {total}"
        else:
            display_text = "0 / 0"
        self.entry_count_label.configure(text=display_text)
        
        if hasattr(self, "pagination"):
            self.pagination.update(self.current_page, total_pages)
        log_ui_timing("table.render.colleges", started_at, warn_ms=65)
    
    def goto_page(self, page):
        total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
        self.current_page = min(max(1, int(page)), total_pages)
        self._request_page_render()

    def change_page(self, delta):
        total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
        self.current_page = min(max(1, self.current_page + delta), total_pages)
        self._request_page_render()

    def go_to_page(self):
        """Jump to a specific page number using the shared pagination control."""
        if hasattr(self, "pagination"):
            self.pagination.go_from_entry()

    def _on_table_configure(self, event):
        # get actual available height including padding around table
        available_height = self.table_container.winfo_height()
        if available_height < 100:  # skip if window is too small
            return
        # account for tree header and table card vertical padding
        reserved_height = 20 + (SPACE_LG * 2)
        usable_height = max(available_height - reserved_height, 50)
        row_height = 46  # height of each row
        new_page_size = max(8, usable_height // row_height)  # show at least 8 rows
        
        # update treeview height to match page size
        self.tree.configure(height=new_page_size)
        
        if new_page_size != self.page_size:
            old_page = self.current_page
            self.page_size = new_page_size
            total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
            self.current_page = min(old_page, total_pages)
            self._render_page()

    def _update_sidebar_heights(self):
        try:
            if not hasattr(self, '_sidebar_cards') or not self._sidebar_cards:
                return
            total_h = self.table_container.winfo_height()
            # subtract header/title and some padding
            header_h = 48
            spacing = 12 * (len(self._sidebar_cards) + 1)
            avail = max(80, total_h - header_h - spacing)
            per = max(60, avail // len(self._sidebar_cards))
            from frontend_ui.ui.utils import animate_height
            for c in self._sidebar_cards:
                try:
                    animate_height(c, per, duration=220)
                except Exception:
                    pass
        except Exception:
            pass

    def refresh_sidebar(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.right_panel, text="DIRECTORY FACTS", font=get_font(12, True), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, SPACE_SM))

        self._fact_img_students = get_icon("users", size=28, fallback_color=ACCENT_COLOR)
        self._fact_img_programs = get_icon("books", size=28, fallback_color=COLOR_PALETTE[1 % len(COLOR_PALETTE)])
        self._fact_img_colleges = get_icon("building", size=28, fallback_color=COLOR_PALETTE[2 % len(COLOR_PALETTE)])

        total_students = str(len(self.controller.students))
        total_programs = str(len(self.controller.programs))
        total_colleges = str(len(self.controller.colleges))
        avg_students_per_program = "0"
        try:
            avg_students_per_program = f"{len(self.controller.students) // max(len(self.controller.programs),1)}"
        except Exception:
            avg_students_per_program = "0"

        # rebuild sidebar cards and store references (use StatCard style)
        from frontend_ui.ui import StatCard
        self._sidebar_cards = []
        c = StatCard(self.right_panel, self._fact_img_students, total_students, "TOTAL STUDENTS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_programs, total_programs, "TOTAL PROGRAMS", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_colleges, total_colleges, "TOTAL COLLEGES", height=120)
        self._sidebar_cards.append(c)
        c = StatCard(self.right_panel, self._fact_img_students, avg_students_per_program, "AVG STUDENTS/PROGRAM", height=120)
        self._sidebar_cards.append(c)

        # ensure heights get updated after layout changes (defer to allow layout)
        self.after(50, self._update_sidebar_heights)


    def _on_tree_motion(self, event):
        region = self.tree.identify_region(event.x, event.y)
        # change cursor to hand when hovering over sortable headings
        if region == "heading":
            self.tree.configure(cursor="hand2")
            # clear any row hover
            if getattr(self, '_last_hover', None):
                prev_row = self._last_hover
                if prev_row in self.tree.get_children():
                    items = self.tree.get_children()
                    if prev_row in items:
                        idx = items.index(prev_row)
                        tag = 'even' if idx % 2 == 0 else 'odd'
                        self.tree.item(prev_row, tags=(tag,))
                self._last_hover = None
            return
        else:
            self.tree.configure(cursor="")
        
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if getattr(self, '_last_hover', None) == row:
            return
        if getattr(self, '_last_hover', None):
            prev_row = self._last_hover
            # check if the previous row still exists
            if prev_row in self.tree.get_children():
                items = self.tree.get_children()
                if prev_row in items:
                    idx = list(items).index(prev_row)
                    tag = 'even' if idx % 2 == 0 else 'odd'
                    self.tree.item(prev_row, tags=(tag,))
        # set hover tag as the only tag for this row
        self.tree.item(row, tags=('hover',))
        self._last_hover = row

    def _on_tree_leave(self, event):
        self.tree.configure(cursor="")
        if getattr(self, '_last_hover', None):
            prev_row = self._last_hover
            # check if the row still exists
            if prev_row in self.tree.get_children():
                # restore the striping tag
                items = self.tree.get_children()
                if prev_row in items:
                    idx = items.index(prev_row)
                    tag = 'even' if idx % 2 == 0 else 'odd'
                    self.tree.item(prev_row, tags=(tag,))
            self._last_hover = None

    def on_row_click(self, event):
        if not self.multi_edit_mode:
            return
        region = self.tree.identify_region(event.x, event.y)
        if region in ("tree", "cell"):
            return "break"

    def on_row_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if self.multi_edit_mode and region in ("tree", "cell"):
            return
        if region not in ('cell', 'tree'):
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        row_data = self.tree.item(item).get('values', [])
        if not row_data:
            return
        self._show_college_info(row_data[1])

    def _show_action_dialog(self, item):
        row_values = self.tree.item(item)['values']
        dlg = ctk.CTkToplevel(self)
        dlg.title("Row Actions")
        apply_window_icon(dlg)
        dlg.geometry("380x160")
        dlg.configure(fg_color=BG_COLOR)
        dlg.attributes('-topmost', True)
        dlg.grab_set()
        dlg.focus_force()
        
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - (dlg.winfo_width() // 2)
        y = (dlg.winfo_screenheight() // 2) - (dlg.winfo_height() // 2)
        dlg.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(dlg, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # card showing college info
        info_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR)
        info_card.pack(fill="x", pady=(0, 12))
        info_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=12)
        
        ctk.CTkLabel(info_frame, text=f"{row_values[2]}", font=get_font(14, True)).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Code: {row_values[1]}", font=get_font(13), text_color=TEXT_MUTED).pack(anchor="w")
        
        # button frame
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")
        def _edit():
            self.tree.selection_set(item)
            dlg.destroy()
            self.on_row_select(None)
        def _delete():
            self.tree.selection_set(item)
            dlg.destroy()
            self.delete_college()
        ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color=DANGER_COLOR, hover_color=DANGER_HOVER).pack(side="left", expand=True, fill="x", padx=(6,0))

        animate_toplevel_in(dlg, x=x, y=y)

    def _show_college_info(self, college_code):
        """Show college information in a window."""
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            self.controller.show_custom_dialog("Error", "College not found", dialog_type="error")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"College: {college_code}")
        apply_window_icon(profile_window)
        profile_window.geometry("700x520")
        profile_window.configure(fg_color=BG_COLOR)
        profile_window.attributes('-topmost', True)
        profile_window.grab_set()
        profile_window.focus_force()

        profile_window.update_idletasks()
        x = (profile_window.winfo_screenwidth() // 2) - (profile_window.winfo_width() // 2)
        y = (profile_window.winfo_screenheight() // 2) - (profile_window.winfo_height() // 2)
        profile_window.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(profile_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # header with code and name
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR)
        header.pack(fill="x", pady=(0, 15))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=16)

        avatar = ctk.CTkFrame(header_inner, width=72, height=72, fg_color="transparent", corner_radius=RADIUS_SM)
        avatar.pack(side="left", padx=(0, 16))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text="\U0001f3eb", font=get_font(32)).pack(expand=True)

        text_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_frame, text=college.get('name', 'N/A'), font=get_font(16, True), wraplength=550, justify="left", anchor="w").pack(fill="x", anchor="w")
        ctk.CTkLabel(text_frame, text=f"Code: {college.get('code', '')}", text_color=TEXT_MUTED, font=get_font(13), anchor="w").pack(fill="x", anchor="w", pady=(4, 0))

        # action buttons frame - packed with side="bottom" first to guarantee visibility
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(15, 0))

        # info card with scrollable content
        info_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR)
        info_card.pack(fill="both", expand=True)

        info_scroll = ctk.CTkScrollableFrame(info_card, fg_color="transparent")
        info_scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # information grid
        def add_info_row(label, value):
            row = ctk.CTkFrame(info_scroll, fg_color="transparent")
            row.pack(fill="x", pady=8)
            lbl = ctk.CTkLabel(row, text=label, font=get_font(14, True), text_color=TEXT_MUTED, width=160, anchor="w")
            lbl.pack(side="left", anchor="w")
            val = ctk.CTkLabel(row, text=value, font=get_font(15), wraplength=450, justify="left", anchor="w")
            val.pack(side="left", padx=(12, 0), fill="x", expand=True, anchor="w")

        add_info_row("College Name:", college.get('name', 'N/A'))
        add_info_row("College Code:", college.get('code', 'N/A'))
        
        program_count = len([p for p in self.controller.programs if p.get('college') == college_code])
        add_info_row("Programs:", str(program_count))
        
        student_count = len([s for s in self.controller.students for p in self.controller.programs if p.get('college') == college_code and s.get('program') == p.get('code')])
        add_info_row("Students:", str(student_count))

        # action buttons - only show if authenticated

        def _edit():
            profile_window.destroy()
            # trigger the edit dialog by finding and selecting the college
            selection = self.tree.selection()
            if not selection:
                self.on_row_select(None)
            else:
                self.on_row_select(None)

        def _delete():
            college_obj = next((c for c in self.controller.colleges if c['code'] == college_code), None)
            if not college_obj:
                return
            affected_programs = [p for p in self.controller.programs if p.get('college') == college_code]
            warning_parts = [f"Are you sure you want to delete college '{college_code}'?"]
            if affected_programs:
                warning_parts.append(f"\n\n⚠ The college field will be cleared for {len(affected_programs)} program(s).")
            if not affected_programs:
                warning_parts.append("\n\nNo programs or students will be affected.")
            if self.controller.show_custom_dialog("Confirm Delete", "".join(warning_parts), dialog_type="yesno"):
                success, msg = self.controller.delete_college(college_code)
                if not success:
                    self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                    return
                profile_window.destroy()
                self.refresh_table()
                self.controller.show_custom_dialog("Success", msg)

        # only show edit/delete buttons if user is logged in
        if self.controller.logged_in:
            ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0, height=CONTROL_HEIGHT_MD).pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color=DANGER_COLOR, text_color="white", font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0, height=CONTROL_HEIGHT_MD).pack(side="left", fill="x", expand=True, padx=(5, 0))
        else:
            # show message prompting login
            login_msg = ctk.CTkLabel(btn_frame, text="🔒 Log in to edit or delete", font=get_font(13), text_color=TEXT_MUTED)
            login_msg.pack(fill="x", pady=10)

        animate_toplevel_in(profile_window, x=x, y=y)

    def filter_table(self, query):
        self.apply_filters(query=query, advanced_filters=None)

    def apply_filters(self, query: str = "", advanced_filters=None):
        """Apply quick-search and advanced filters with AND semantics."""
        base_rows = ListPipelineService.college_rows(self.controller.colleges)
        rows = ListPipelineService.filter_colleges(base_rows, query=query, advanced_filters=advanced_filters)

        self._last_page_items = rows
        self.current_page = 1
        self._render_page()

    def on_column_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if self.multi_edit_mode and region in ("tree", "cell"):
            item = self.tree.identify_row(event.y)
            if item:
                if item in self.tree.selection():
                    self.tree.selection_remove(item)
                else:
                    self.tree.selection_add(item)
                self._refresh_checkmarks()
            return "break"

        if region == "heading":
            col = self.tree.identify_column(event.x)
            if col == "#0":
                if self.multi_edit_mode:
                    visible = self.tree.get_children()
                    if visible and all(item in self.tree.selection() for item in visible):
                        self.tree.selection_remove(*visible)
                    else:
                        self.tree.selection_add(*visible)
                    self._refresh_checkmarks()
                return "break"
            try:
                idx = int(col.replace('#', '')) - 1
                col_id = self.tree['columns'][idx]
            except Exception:
                col_id = self.tree.heading(col, "text")
            
            # restore sort hint on previous sort column
            if self.sort_column and self.sort_column != col_id:
                self.tree.heading(self.sort_column, text=self.column_names.get(self.sort_column, self.sort_column) + " ⇅")
            
            if self.sort_column == col_id:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = col_id
                self.sort_reverse = False
            
            self.update_sort_arrow()
            self.sort_table()
    
    def update_sort_arrow(self):
        """Update column heading to show sort arrow indicator."""
        if not self.sort_column:
            return
        
        # get the original column name
        col_name = self.column_names.get(self.sort_column, self.sort_column)
        arrow = " ▼" if self.sort_reverse else " ▲"
        self.tree.heading(self.sort_column, text=col_name + arrow)
    
    def sort_table(self):
        if not self.sort_column:
            return

        self._last_page_items = ListPipelineService.sort_rows(
            self._last_page_items,
            self.tree['columns'],
            self.sort_column,
            reverse=self.sort_reverse,
        )
        
        # re-render the current page
        self._render_page()
    
    @staticmethod
    def try_numeric(val):
        try:
            return float(val)
        except ValueError:
            return val

    def add_college(self):
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to add colleges.")
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title("Add College")
        apply_window_icon(modal)
        screen_height = modal.winfo_screenheight()
        height = min(350, int(screen_height * 0.55))
        modal.geometry(f"450x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        modal.grab_set()
        modal.focus_force()
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"450x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New College", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="College Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., COE", height=CONTROL_HEIGHT_MD)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="College Name", height=CONTROL_HEIGHT_MD)
        name_entry.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            
            if not code:
                return False, "College Code is required"
            
            if not name:
                return False, "College Name is required"
            
            if len(code) < 2:
                return False, "College Code must be at least 2 characters"
            
            if not code.isalpha():
                return False, "College Code must contain only letters"
            
            if not name.replace(" ", "").isalpha():
                return False, "College Name must contain only letters and spaces"
            
            if any(c['code'] == code for c in self.controller.colleges):
                return False, "College Code already exists"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return
            
            code = code_entry.get().strip()
            name = name_entry.get().strip().title()
            
            new_col = {'code': code, 'name': name}
            ok, msg = validate_college(new_col)
            if not ok:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            success, msg = self.controller.add_college(new_col)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            modal.destroy()
            self.controller.show_custom_dialog("Success", "College added successfully!")
        
        ctk.CTkButton(form_frame, text="Save College", command=save, height=CONTROL_HEIGHT_MD,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0).pack(fill="x")

        animate_toplevel_in(modal, x=x, y=y)

    def show_context_menu_college(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        try:
            menu.configure(
                bg=PANEL_COLOR,
                fg=TEXT_PRIMARY,
                activebackground=TABLE_HOVER_BG,
                activeforeground=TEXT_PRIMARY,
            )
        except Exception:
            pass
        menu.add_command(label="Edit", command=lambda: self.on_row_select(None))
        menu.add_command(label="Delete", command=self.delete_college)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_college(self):
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete colleges.")
            return
        
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        college_code = row_data[1]
        
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            self.controller.show_custom_dialog("Error", "College not found", dialog_type="error")
            return
        
        # count affected programs
        affected_programs = [p for p in self.controller.programs if p['college'] == college['code']]
        
        # build warning message
        warning_parts = [f"Are you sure you want to delete college '{college['code']}'?"]
        if affected_programs:
            warning_parts.append(f"\n\n⚠ The college field will be cleared for {len(affected_programs)} program(s).")
        if not affected_programs:
            warning_parts.append("\n\nNo programs or students will be affected.")
        
        if self.controller.show_custom_dialog("Confirm Delete", "".join(warning_parts), dialog_type="yesno"):
            success, msg = self.controller.delete_college(college_code)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            self.controller.refresh_data()
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            self.controller.show_custom_dialog("Success", msg)

    def delete_selected_colleges(self):
        """Delete multiple selected colleges."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete colleges.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more colleges first.", dialog_type="warning")
            return

        college_codes = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                college_codes.append(str(row[1]))

        if not college_codes:
            self.controller.show_custom_dialog("No Selection", "No valid college rows selected.", dialog_type="warning")
            return

        if not self.controller.show_custom_dialog(
            "Confirm Bulk Delete",
            f"Delete {len(college_codes)} selected college(s)?\nPrograms under those colleges will be unassigned.",
            dialog_type="yesno",
        ):
            return

        success_count = 0
        failures = []
        for college_code in college_codes:
            success, msg = self.controller.delete_college(college_code)
            if success:
                success_count += 1
            else:
                failures.append(f"{college_code}: {msg}")

        self.controller.refresh_data()
        self.refresh_table()
        try:
            self.refresh_sidebar()
            self._refresh_all_sidebars()
        except Exception:
            pass

        if failures:
            preview = "\n".join(failures[:5])
            more = "" if len(failures) <= 5 else f"\n...and {len(failures) - 5} more"
            self.controller.show_custom_dialog(
                "Bulk Delete Complete",
                f"Deleted {success_count}/{len(college_codes)} college(s).\n\nFailed:\n{preview}{more}",
                dialog_type="warning",
            )
        else:
            self.controller.show_custom_dialog("Success", f"Deleted {success_count} college(s) successfully.")

    def edit_selected_colleges(self):
        """Bulk edit selected colleges by adding a name prefix/suffix."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to edit colleges.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more colleges first.", dialog_type="warning")
            return

        college_codes = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                college_codes.append(str(row[1]))

        if not college_codes:
            self.controller.show_custom_dialog("No Selection", "No valid college rows selected.", dialog_type="warning")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Bulk Edit Colleges")
        apply_window_icon(modal)
        modal.geometry("460x280")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        modal.grab_set()
        modal.focus_force()

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(modal, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"Bulk Edit {len(college_codes)} College(s)", font=get_font(16, True)).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Name Prefix", font=FONT_BOLD).pack(anchor="w")
        prefix_entry = ctk.CTkEntry(frame, placeholder_text="Optional prefix", height=CONTROL_HEIGHT_MD)
        prefix_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(frame, text="Name Suffix", font=FONT_BOLD).pack(anchor="w")
        suffix_entry = ctk.CTkEntry(frame, placeholder_text="Optional suffix", height=CONTROL_HEIGHT_MD)
        suffix_entry.pack(fill="x", pady=(0, 16))

        def save_bulk():
            prefix = prefix_entry.get().strip()
            suffix = suffix_entry.get().strip()

            if not prefix and not suffix:
                self.controller.show_custom_dialog("No Changes", "Enter a prefix or suffix.", dialog_type="warning")
                return

            preview_lines = []
            if prefix:
                preview_lines.append(f"- Prefix: {prefix}")
            if suffix:
                preview_lines.append(f"- Suffix: {suffix}")

            if not self.controller.show_custom_dialog(
                "Confirm Bulk Edit",
                f"Apply these changes to {len(college_codes)} college(s)?\n\n" + "\n".join(preview_lines),
                dialog_type="yesno",
            ):
                return

            success_count = 0
            failures = []
            for college_code in college_codes:
                college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
                if not college:
                    failures.append(f"{college_code}: College not found")
                    continue
                new_name = f"{prefix}{college['name']}{suffix}".strip()
                success, msg = self.controller.update_college(college_code, {'name': new_name})
                if success:
                    success_count += 1
                else:
                    failures.append(f"{college_code}: {msg}")

            self.controller.refresh_data()
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            modal.destroy()

            if failures:
                preview = "\n".join(failures[:5])
                more = "" if len(failures) <= 5 else f"\n...and {len(failures) - 5} more"
                self.controller.show_custom_dialog(
                    "Bulk Edit Complete",
                    f"Updated {success_count}/{len(college_codes)} college(s).\n\nFailed:\n{preview}{more}",
                    dialog_type="warning",
                )
            else:
                self.controller.show_custom_dialog("Success", f"Updated {success_count} college(s) successfully.")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(btn_row, text="Apply Changes", command=save_bulk, fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0, height=CONTROL_HEIGHT_MD).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", command=modal.destroy, fg_color=BTN_SEGMENT_FG, hover_color=BTN_SEGMENT_HOVER, text_color="white", font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0, height=CONTROL_HEIGHT_MD).pack(side="left", fill="x", expand=True, padx=(6, 0))

        animate_toplevel_in(modal, x=x, y=y)

    def _refresh_checkmarks(self):
        for item in self.tree.get_children():
            if not self.multi_edit_mode:
                self.tree.item(item, text="")
            else:
                self.tree.item(item, text="☑" if item in self.tree.selection() else "☐")

    def set_multi_edit_mode(self, enabled: bool):
        self.multi_edit_mode = bool(enabled and self.controller.logged_in)
        self.tree.configure(selectmode=("extended" if self.multi_edit_mode else "browse"))
        self.tree.heading("#0", text=("✓" if self.multi_edit_mode else ""))
        self.tree.column("#0", width=(38 if self.multi_edit_mode else 0), minwidth=0, stretch=False)
        self.tree.selection_remove(*self.tree.selection())

        if self.multi_edit_mode:
            if not self.bulk_edit_btn.winfo_manager():
                self.bulk_edit_btn.pack(side="left", padx=(0, 8), before=self.csv_import_btn)
            if not self.bulk_delete_btn.winfo_manager():
                self.bulk_delete_btn.pack(side="left", padx=(0, 8), before=self.csv_import_btn)
        else:
            self.bulk_edit_btn.pack_forget()
            self.bulk_delete_btn.pack_forget()

        self._refresh_checkmarks()

    @staticmethod
    def _csv_pick(row: dict, *aliases: str) -> str:
        if not isinstance(row, dict):
            return ""

        lowered = {
            str(key or "").strip().lower(): str(value or "").strip()
            for key, value in row.items()
        }
        for alias in aliases:
            value = lowered.get(str(alias).strip().lower(), "")
            if value:
                return value
        return ""

    def _selected_college_codes(self) -> set[str]:
        selected = set()
        for item in self.tree.selection():
            values = self.tree.item(item).get("values", [])
            if len(values) > 1:
                selected.add(str(values[1]).strip())
        return selected

    def export_csv(self):
        selected_codes = self._selected_college_codes() if self.multi_edit_mode else set()
        colleges = self.controller.colleges
        if selected_codes:
            colleges = [c for c in colleges if str(c.get("code", "")).strip() in selected_codes]

        rows = [
            {
                "Code": str(college.get("code", "")).strip(),
                "Name": str(college.get("name", "")).strip(),
            }
            for college in colleges
        ]

        if not rows:
            self.controller.show_custom_dialog("Export CSV", "No college rows available to export.", dialog_type="warning")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Colleges CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"colleges_{time.strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file_path:
            return

        try:
            written = write_csv_rows(file_path, ["Code", "Name"], rows)
            self.controller.show_custom_dialog("Export CSV", f"Exported {written} college row(s).")
        except Exception as exc:
            self.controller.show_custom_dialog("Export Error", f"Could not export CSV: {exc}", dialog_type="error")

    def import_csv(self):
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "Please log in to import colleges.", dialog_type="error")
            return

        file_path = filedialog.askopenfilename(
            parent=self,
            title="Import Colleges CSV",
            filetypes=[("CSV files", "*.csv")],
        )
        if not file_path:
            return

        try:
            raw_rows, _fieldnames = read_csv_rows(file_path)
        except Exception as exc:
            self.controller.show_custom_dialog("Import Error", f"Could not read CSV: {exc}", dialog_type="error")
            return

        if not raw_rows:
            self.controller.show_custom_dialog("Import CSV", "CSV contains no rows to import.", dialog_type="warning")
            return

        records = []
        for row in raw_rows:
            records.append(
                {
                    "code": self._csv_pick(row, "code", "college code"),
                    "name": self._csv_pick(row, "name", "college name"),
                }
            )

        existing_codes = {str(college.get("code", "")).strip() for college in self.controller.colleges}
        duplicate_count = sum(1 for record in records if record.get("code") in existing_codes)

        overwrite_existing = False
        if duplicate_count:
            decision = messagebox.askyesnocancel(
                "Duplicate Colleges Found",
                (
                    f"Found {duplicate_count} college code(s) that already exist.\n\n"
                    "Yes: overwrite existing records\n"
                    "No: skip duplicate codes\n"
                    "Cancel: abort import"
                ),
                parent=self.winfo_toplevel(),
            )
            if decision is None:
                return
            overwrite_existing = bool(decision)

        success, summary = self.controller.bulk_upsert_colleges(records, overwrite_existing=overwrite_existing)
        if not success:
            fatal = summary.get("fatal_error", "Unknown error")
            self.controller.show_custom_dialog("Import Error", f"Import failed: {fatal}", dialog_type="error")
            return

        self.refresh_table()
        try:
            self.refresh_sidebar()
            self._refresh_all_sidebars()
        except Exception:
            pass

        msg = (
            f"Created: {summary.get('created', 0)}\n"
            f"Updated: {summary.get('updated', 0)}\n"
            f"Skipped: {summary.get('skipped', 0)}\n"
            f"Failed: {summary.get('failed', 0)}"
        )
        errors = summary.get("errors", [])
        if errors:
            msg += "\n\nSample errors:\n" + "\n".join(errors[:5])

        self.controller.show_custom_dialog("Import Colleges Complete", msg)

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        college_code = row_data[1]
        
        college = next((c for c in self.controller.colleges if c['code'] == college_code), None)
        if not college:
            return
        
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit College")
        apply_window_icon(edit_window)
        edit_window.geometry("420x320")
        edit_window.configure(fg_color=BG_COLOR)
        edit_window.attributes('-topmost', True)
        edit_window.grab_set()
        edit_window.focus_force()
        
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        container = ctk.CTkFrame(edit_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # header card
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR, height=80)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{college_code}", font=get_font(16, True)).place(x=16, y=14)
        ctk.CTkLabel(header, text="College", font=get_font(13), text_color=TEXT_MUTED).place(x=16, y=44)
        
        # form card
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=RADIUS_MD, border_width=0, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        form_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(form_frame, text="College Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, height=CONTROL_HEIGHT_MD)
        code_entry.insert(0, college['code'])
        code_entry.configure(state="disabled")
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, height=CONTROL_HEIGHT_MD)
        name_entry.insert(0, college['name'])
        name_entry.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            name = name_entry.get().strip()
            
            if not name:
                return False, "College Name is required"
            
            if not name.replace(" ", "").isalpha():
                return False, "College Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return
            
            new_name = name_entry.get().strip().title()
            success, msg = self.controller.update_college(college_code, {'name': new_name})
            
            if success:
                edit_window.destroy()
                self.controller.refresh_data()
                self.refresh_table()
                self.controller.show_custom_dialog("Success", "College updated successfully!")
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
        
        def delete():
            if self.controller.show_custom_dialog("Confirm Delete", f"Delete {college['code']}?", dialog_type="yesno"):
                success, msg = self.controller.delete_college(college_code)
                if success:
                    edit_window.destroy()
                    self.controller.refresh_data()
                    self.refresh_table()
                    self.controller.show_custom_dialog("Success", msg)
                else:
                    self.controller.show_custom_dialog("Error", msg, dialog_type="error")
        
        ctk.CTkButton(button_frame, text="Save Changes", command=save, height=CONTROL_HEIGHT_MD,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=CONTROL_HEIGHT_MD,
                 fg_color=DANGER_COLOR, hover_color=DANGER_HOVER, font=FONT_BOLD, corner_radius=RADIUS_SM, border_width=0).pack(side="left", fill="x", expand=True, padx=(5, 0))

        animate_toplevel_in(edit_window, x=x, y=y)


CollegesListView = CollegesView

__all__ = ["CollegesListView", "CollegesView"]


