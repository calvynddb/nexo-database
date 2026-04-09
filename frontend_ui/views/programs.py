"""
Programs view module extracted from original views.py
"""
import customtkinter as ctk
import tkinter as tk
import time
from tkinter import ttk

# matplotlib & numpy are lazy-loaded inside create_donut_chart() to speed up startup

from config import (
    FONT_MAIN, FONT_BOLD, BG_COLOR, PANEL_COLOR, ACCENT_COLOR,
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE, TEXT_PRIMARY,
    BTN_PRIMARY_FG, BTN_PRIMARY_HOVER, DANGER_COLOR, DANGER_HOVER,
    ENTRY_BG, TABLE_ODD_BG, TABLE_EVEN_BG, TABLE_HOVER_BG
)
from config import get_font
from frontend_ui.ui import (
    DepthCard,
    setup_treeview_style,
    placeholder_image,
    get_icon,
    StyledComboBox,
    animate_toplevel_in,
    log_ui_timing,
)
from backend import validate_program


class ProgramsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.multi_edit_mode = False
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # store original column names
        self.setup_ui()

    def setup_ui(self):
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", padx=(0, 25))

        setup_treeview_style()
        cols = ("#", "Code", "Program Name", "College", "Students")
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
            self.tree.column(c, anchor="center", stretch=False, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=(10, 12))
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.bind("<Double-1>", self.on_row_double_click)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._refresh_checkmarks())
        self.tree.tag_configure('odd', background=TABLE_ODD_BG)
        self.tree.tag_configure('even', background=TABLE_EVEN_BG)
        self.tree.tag_configure('hover', background=TABLE_HOVER_BG, foreground="#ffffff")

        # pagination controls - integrated layout
        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=(10,12))
        self.current_page = 1
        self.page_size = 12
        self._last_page_items = []
        self._last_hover = None
        self.table_container = table_container
        
        # left section: Previous button, pagination, and Next button together
        left_ctrl = ctk.CTkFrame(ctrl, fg_color="transparent")
        left_ctrl.pack(side="left")
        
        self.prev_btn = ctk.CTkButton(left_ctrl, text="◀ Prev", width=80, fg_color=BTN_PRIMARY_FG, hover_color=BTN_PRIMARY_HOVER, text_color="white", command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left", padx=(0,8))
        
        self.pagination_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        self.pagination_frame.pack(side="left", padx=8)
        self.page_buttons = []
        
        # next Button - right next to pagination
        self.next_btn = ctk.CTkButton(left_ctrl, text="Next ▶", width=80, fg_color=BTN_PRIMARY_FG, hover_color=BTN_PRIMARY_HOVER, text_color="white", command=lambda: self.change_page(1))
        self.next_btn.pack(side="left", padx=(8,0))
        
        # go to page section
        goto_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        goto_frame.pack(side="left", padx=(15, 0))
        
        ctk.CTkLabel(goto_frame, text="Go to:", font=get_font(12), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        
        self.page_entry = ctk.CTkEntry(goto_frame, width=50, height=30, 
                                       fg_color=ENTRY_BG, border_color=BORDER_COLOR,
                                       text_color=TEXT_PRIMARY, font=get_font(12))
        self.page_entry.pack(side="left", padx=(0, 5))
        self.page_entry.bind("<Return>", lambda e: self.go_to_page())
        
        self.go_btn = ctk.CTkButton(goto_frame, text="Go", width=40, height=30,
                                    fg_color=BTN_PRIMARY_FG, hover_color=BTN_PRIMARY_HOVER,
                                    text_color="white", font=get_font(12, True),
                                    command=self.go_to_page)
        self.go_btn.pack(side="left")
        
        # right section: Entry count only
        right_ctrl = ctk.CTkFrame(ctrl, fg_color="transparent")
        right_ctrl.pack(side="right")

        self.bulk_edit_btn = ctk.CTkButton(
            right_ctrl,
            text="Edit Selected",
            width=120,
            height=30,
            fg_color=BTN_PRIMARY_FG,
            hover_color=BTN_PRIMARY_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.edit_selected_programs,
        )

        self.bulk_delete_btn = ctk.CTkButton(
            right_ctrl,
            text="Delete Selected",
            width=130,
            height=30,
            fg_color=DANGER_COLOR,
            hover_color=DANGER_HOVER,
            text_color="white",
            font=get_font(12, True),
            command=self.delete_selected_programs,
        )
        # entry count label
        self.entry_count_label = ctk.CTkLabel(right_ctrl, text="Showing 0 of 0 entries", 
                                             font=get_font(13), text_color=TEXT_MUTED)
        self.entry_count_label.pack(side="left", padx=0)

        def _on_table_config(e):
            total = max(e.width - 20, 200)
            # adjust column proportions to fit better
            props = [0.08, 0.15, 0.50, 0.15, 0.12]
            for i, col in enumerate(cols):
                self.tree.column(col, width=max(int(total * props[i]), 50))
            self._on_table_configure(e)

        table_container.bind('<Configure>', _on_table_config)

        right_panel = ctk.CTkFrame(self, width=280, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew")
        self.right_panel = right_panel

        top_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
        
        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#a78bfa", "#6366f1"]
        
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=get_font(13, True)).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color=ENTRY_BG, height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            try:
                from ui.utils import animate_progress
                animate_progress(bar, min(val / 50, 1.0), duration=420)
            except Exception:
                bar.set(min(val / 50, 1.0))

        dist_card = DepthCard(right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)

        self.create_donut_chart(dist_card)
        self.right_dist_card = dist_card
        self.refresh_table()

    def _refresh_all_sidebars(self):
        try:
            from frontend_ui.dashboard import DashboardFrame
            df = self.controller.frames.get(DashboardFrame)
            if not df:
                return
            for v in df.views.values():
                try:
                    if hasattr(v, 'refresh_sidebar'):
                        v.refresh_sidebar()
                except Exception:
                    pass
        except Exception:
            pass

    def create_donut_chart(self, parent):
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except Exception:
            ctk.CTkLabel(parent, text="Chart unavailable", text_color=TEXT_MUTED).pack(pady=40)
            return
        
        fig, ax = plt.subplots(figsize=(2.5, 2.5), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)

        color_map = {
            'CCS': '#87CEEB',
            'COE': '#800000',
            'CSM': '#fF0000',
            'CED': '#00008B',
            'CASS': '#008000',
            'Cass': '#008000',
            'CEBA': '#fFD700',
            'CHS': '#fFFFFF',
        }

        college_counts = {}
        for p in self.controller.programs:
            coll = p.get('college', 'Unknown')
            college_counts[coll] = college_counts.get(coll, 0) + 1

        labels = list(college_counts.keys())
        data = [college_counts[k] for k in labels]

        if sum(data) > 0:
            colors = [color_map.get(k, COLOR_PALETTE[i % len(COLOR_PALETTE)]) for i, k in enumerate(labels)]
            wedges, texts = ax.pie(data, colors=colors, startangle=90,
                                   wedgeprops=dict(width=0.4, edgecolor=PANEL_COLOR, linewidth=2))
            ax.axis('equal')

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=(6, 2))

            legend_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=80)
            legend_scroll.pack(fill="both", expand=True, pady=(6, 12), padx=8)

            for i, (lab, col) in enumerate(zip(labels, colors)):
                r = i // 2
                c = i % 2
                f = ctk.CTkFrame(legend_scroll, fg_color="transparent")
                f.grid(row=r, column=c, padx=8, pady=4, sticky="w")
                sq = ctk.CTkFrame(f, width=14, height=14, fg_color=col, corner_radius=3)
                sq.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(f, text=f"{lab} ({college_counts.get(lab,0)})", font=get_font(12)).pack(side="left")

    def refresh_table(self):
        rows = []
        for idx, p in enumerate(self.controller.programs, 1):
            student_count = len([s for s in self.controller.students if s.get('program') == p['code']])
            rows.append((idx, p['code'], p['name'], p['college'], student_count))
        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
        self._last_hover = None

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
            display_text = f"Showing {start + 1}-{end} of {total} entries"
        else:
            display_text = "Showing 0 of 0 entries"
        self.entry_count_label.configure(text=display_text)
        
        start_page = max(1, self.current_page - 2)
        end_page = min(total_pages, start_page + 4)
        if end_page - start_page < 4:
            start_page = max(1, end_page - 4)

        visible_pages = list(range(start_page, end_page + 1))
        while len(self.page_buttons) < len(visible_pages):
            btn = ctk.CTkButton(
                self.pagination_frame,
                text="",
                width=32,
                height=28,
                fg_color="#3b3b3f",
                command=lambda: None,
            )
            btn.pack(side="left", padx=2)
            self.page_buttons.append(btn)

        for idx, page_num in enumerate(visible_pages):
            btn = self.page_buttons[idx]
            is_current = page_num == self.current_page
            btn.configure(
                text=str(page_num),
                fg_color=ACCENT_COLOR if is_current else "#3b3b3f",
                command=lambda page=page_num: self.goto_page(page),
            )
            if not btn.winfo_manager():
                btn.pack(side="left", padx=2)

        for btn in self.page_buttons[len(visible_pages):]:
            if btn.winfo_manager():
                btn.pack_forget()
        
        self.prev_btn.configure(state=("normal" if self.current_page > 1 else "disabled"))
        self.next_btn.configure(state=("normal" if self.current_page < total_pages else "disabled"))
        log_ui_timing("table.render.programs", started_at, warn_ms=65)
    
    def goto_page(self, page):
        self.current_page = page
        self._render_page()

    def change_page(self, delta):
        total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
        self.current_page = min(max(1, self.current_page + delta), total_pages)
        self._render_page()
        self.page_entry.delete(0, "end")

    def go_to_page(self):
        """Jump to a specific page number."""
        try:
            page_num = int(self.page_entry.get().strip())
            total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
            if 1 <= page_num <= total_pages:
                self.current_page = page_num
                self._render_page()
                self.page_entry.delete(0, "end")
        except ValueError:
            # invalid input, just clear the entry
            self.page_entry.delete(0, "end")

    def _on_table_configure(self, event):
        # get actual available height including padding around table
        available_height = self.table_container.winfo_height()
        if available_height < 100:  # skip if window is too small
            return
        # account for: Treeview header (~20px) + padding (~12px) + pagination controls (~55px)
        reserved_height = 20 + 12 + 55
        usable_height = max(available_height - reserved_height, 50)
        row_height = 48  # height of each row
        new_page_size = max(8, usable_height // row_height)  # show at least 8 rows
        
        # update treeview height to match page size
        self.tree.configure(height=new_page_size)
        
        if new_page_size != self.page_size:
            old_page = self.current_page
            self.page_size = new_page_size
            total_pages = max(1, (len(self._last_page_items) + self.page_size - 1) // self.page_size)
            self.current_page = min(old_page, total_pages)
            self._render_page()

    def refresh_sidebar(self):
        for w in self.right_panel.winfo_children():
            w.destroy()
        top_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        top_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_card, text="Top Enrolled", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)

        enrollments = {}
        for student in self.controller.students:
            prog = student.get('program', 'Unknown')
            enrollments[prog] = enrollments.get(prog, 0) + 1
        sorted_progs = sorted(enrollments.items(), key=lambda x: x[1], reverse=True)[:3]
        colors_list = [ACCENT_COLOR, "#a78bfa", "#6366f1"]
        for i, (p, val) in enumerate(sorted_progs):
            f = ctk.CTkFrame(top_card, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=p, font=get_font(13, True)).pack(side="left")
            ctk.CTkLabel(f, text=f"{val} Students", text_color=TEXT_MUTED).pack(side="right")
            bar = ctk.CTkProgressBar(top_card, progress_color=colors_list[i], fg_color=ENTRY_BG, height=8)
            bar.pack(fill="x", padx=20, pady=(0, 15))
            try:
                from ui.utils import animate_progress
                animate_progress(bar, min(val / 50, 1.0), duration=420)
            except Exception:
                bar.set(min(val / 50, 1.0))

        dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        dist_card.pack(fill="both", expand=True)
        ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
        self.create_donut_chart(dist_card)

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
        if region == "tree":
            return "break"

    def on_row_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if self.multi_edit_mode and region == "tree":
            return
        if region not in ('cell', 'tree'):
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        row_data = self.tree.item(item).get('values', [])
        if not row_data:
            return
        self._show_program_info(row_data[1])

    def filter_table(self, query):
        self.apply_filters(query=query, advanced_filters=None)

    def apply_filters(self, query: str = "", advanced_filters=None):
        """Apply quick-search and advanced filters with AND semantics."""
        query = (query or "").strip().lower()
        advanced_filters = advanced_filters or {}

        code_filter = str(advanced_filters.get("code", "")).strip().lower()
        name_filter = str(advanced_filters.get("name", "")).strip().lower()
        college_filter = str(advanced_filters.get("college", "")).strip().lower()

        student_counts = {}
        for student in self.controller.students:
            prog_code = str(student.get('program', ''))
            if not prog_code:
                continue
            student_counts[prog_code] = student_counts.get(prog_code, 0) + 1

        rows = []
        for idx, p in enumerate(self.controller.programs, 1):
            code = str(p.get('code', ''))
            name = str(p.get('name', ''))
            college = str(p.get('college', ''))

            code_l = code.lower()
            name_l = name.lower()
            college_l = college.lower()

            if query and not (
                query in name_l or
                query in code_l or
                query in college_l
            ):
                continue

            if code_filter and code_filter not in code_l:
                continue
            if name_filter and name_filter not in name_l:
                continue
            if college_filter and college_filter != "any" and college_filter != college_l:
                continue

            student_count = student_counts.get(code, 0)
            rows.append((idx, code, name, college, student_count))

        self._last_page_items = rows
        self.current_page = 1
        self._render_page()

    def on_column_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if self.multi_edit_mode and region == "tree":
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
        
        # sort the entire _last_page_items list
        col_index = self.tree['columns'].index(self.sort_column) if self.sort_column in self.tree['columns'] else 0
        self._last_page_items.sort(key=lambda x: self.try_numeric(str(x[col_index])), reverse=self.sort_reverse)
        
        # re-render the current page
        self._render_page()
    
    @staticmethod
    def try_numeric(val):
        try:
            return float(val)
        except ValueError:
            return val

    def _show_program_info(self, prog_code):
        """Show program information in a window."""
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            self.controller.show_custom_dialog("Error", "Program not found", dialog_type="error")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"Program: {prog_code}")
        profile_window.geometry("750x550")
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
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        header.pack(fill="x", pady=(0, 15))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=16)

        avatar = ctk.CTkFrame(header_inner, width=72, height=72, fg_color="#2d1f45", corner_radius=10)
        avatar.pack(side="left", padx=(0, 16))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text="\U0001f4da", font=get_font(32)).pack(expand=True)

        text_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_frame, text=program.get('name', 'N/A'), font=get_font(16, True), wraplength=550, justify="left", anchor="w").pack(fill="x", anchor="w")
        ctk.CTkLabel(text_frame, text=f"Code: {program.get('code', '')}", text_color=TEXT_MUTED, font=get_font(13), anchor="w").pack(fill="x", anchor="w", pady=(4, 0))

        # action buttons frame - packed with side="bottom" first to guarantee visibility
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(15, 0))

        # info card with scrollable content
        info_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
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

        add_info_row("Program Name:", program.get('name', 'N/A'))
        add_info_row("Program Code:", program.get('code', 'N/A'))
        add_info_row("College:", program.get('college', 'N/A'))
        
        student_count = len([s for s in self.controller.students if s.get('program') == prog_code])
        add_info_row("Enrolled Students:", str(student_count))

        # action buttons - only show if authenticated

        def _edit():
            profile_window.destroy()
            # trigger the edit dialog by simulating a row selection
            selection = self.tree.selection()
            if not selection:
                self.on_row_select(None)
            else:
                self.on_row_select(None)

        def _delete():
            affected_students = [s for s in self.controller.students if s.get('program', '') == prog_code]
            warning_parts = [f"Are you sure you want to delete program '{prog_code}'?"]
            if affected_students:
                warning_parts.append(f"\n\n⚠ The program field will be cleared for {len(affected_students)} student(s) currently enrolled.")
            else:
                warning_parts.append("\n\nNo students will be affected.")
            if self.controller.show_custom_dialog("Confirm Delete", "".join(warning_parts), dialog_type="yesno"):
                success, msg = self.controller.delete_program(prog_code)
                if success:
                    profile_window.destroy()
                    self.controller.refresh_data()
                    self.refresh_table()
                    self.controller.show_custom_dialog("Success", msg)
                else:
                    self.controller.show_custom_dialog("Error", msg, dialog_type="error")

        # only show edit/delete buttons if user is logged in
        if self.controller.logged_in:
            ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color=DANGER_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))
        else:
            # show message prompting login
            login_msg = ctk.CTkLabel(btn_frame, text="🔒 Log in to edit or delete", font=get_font(13), text_color=TEXT_MUTED)
            login_msg.pack(fill="x", pady=10)

        animate_toplevel_in(profile_window, x=x, y=y)

    def add_program(self):
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to add programs.")
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title("Add Program")
        screen_height = modal.winfo_screenheight()
        height = min(400, int(screen_height * 0.6))
        modal.geometry(f"500x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        modal.grab_set()
        modal.focus_force()
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Program", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Program Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., BSCS", height=40)
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="Program Name", height=40)
        name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College", font=FONT_BOLD).pack(anchor="w")
        college_values = [c['code'] for c in self.controller.colleges]
        college_widget = StyledComboBox(form_frame, college_values)
        college_widget.set(college_values[0] if college_values else "")
        college_widget.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            college = college_widget.get()
            
            if not code:
                return False, "Program Code is required"
            
            if not name:
                return False, "Program Name is required"
            
            if not college:
                return False, "College must be selected"
            
            if len(code) < 2:
                return False, "Program Code must be at least 2 characters"
            
            if not code.isalnum():
                return False, "Program Code must contain only letters and numbers"
            
            if not name.replace(" ", "").isalpha():
                return False, "Program Name must contain only letters and spaces"
            
            if any(p['code'] == code for p in self.controller.programs):
                return False, "Program Code already exists"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return
            
            code = code_entry.get().strip()
            name = name_entry.get().strip().title()
            college = college_widget.get()

            new_prog = {'code': code, 'name': name, 'college': college}
            ok, msg = validate_program(new_prog)
            if not ok:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            
            success, msg = self.controller.add_program(new_prog)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            
            self.refresh_table()
            try:
                for w in self.right_panel.winfo_children():
                    w.destroy()
                dist_card = DepthCard(self.right_panel, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
                dist_card.pack(fill="both", expand=True)
                ctk.CTkLabel(dist_card, text="College Program Distribution", font=get_font(13, True)).pack(anchor="w", padx=20, pady=15)
                self.create_donut_chart(dist_card)
                try:
                    self._refresh_all_sidebars()
                except Exception:
                    pass
            except Exception:
                pass
            modal.destroy()
            self.controller.show_custom_dialog("Success", "Program added successfully!")
        
        # save / Cancel row
        btn_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8,0))
        ctk.CTkButton(btn_row, text="Save Program", command=save, height=40,
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(btn_row, text="Cancel", command=modal.destroy, height=40,
                 fg_color="#555555", text_color="white", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(6,0))

        animate_toplevel_in(modal, x=x, y=y)

    def show_context_menu_program(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        try:
            menu.configure(bg=PANEL_COLOR, fg=TEXT_PRIMARY, activebackground="#3a2f45", activeforeground=TEXT_PRIMARY)
        except Exception:
            pass
        menu.add_command(label="Edit", command=lambda: self.on_row_select(None))
        menu.add_command(label="Delete", command=self.delete_program)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def delete_program(self):
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete programs.")
            return
        
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        prog_code = row_data[1]
        
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            self.controller.show_custom_dialog("Error", "Program not found", dialog_type="error")
            return
        
        # count affected students
        affected_students = [s for s in self.controller.students if s.get('program', '') == prog_code]
        
        # build warning message
        warning_parts = [f"Are you sure you want to delete program '{prog_code}'?"]
        if affected_students:
            warning_parts.append(f"\n\n\u26a0 The program field will be cleared for {len(affected_students)} student(s) currently enrolled.")
        else:
            warning_parts.append("\n\nNo students will be affected.")
        
        if self.controller.show_custom_dialog("Confirm Delete", "".join(warning_parts), dialog_type="yesno"):
            success, msg = self.controller.delete_program(prog_code)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            self.refresh_table()
            try:
                self.refresh_sidebar()
                self._refresh_all_sidebars()
            except Exception:
                pass
            self.controller.show_custom_dialog("Success", msg)

    def delete_selected_programs(self):
        """Delete multiple selected programs."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete programs.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more programs first.", dialog_type="warning")
            return

        program_codes = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                program_codes.append(str(row[1]))

        if not program_codes:
            self.controller.show_custom_dialog("No Selection", "No valid program rows selected.", dialog_type="warning")
            return

        if not self.controller.show_custom_dialog(
            "Confirm Bulk Delete",
            f"Delete {len(program_codes)} selected program(s)?\nStudents in those programs will be unassigned.",
            dialog_type="yesno",
        ):
            return

        success_count = 0
        failures = []
        for program_code in program_codes:
            success, msg = self.controller.delete_program(program_code)
            if success:
                success_count += 1
            else:
                failures.append(f"{program_code}: {msg}")

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
                f"Deleted {success_count}/{len(program_codes)} program(s).\n\nFailed:\n{preview}{more}",
                dialog_type="warning",
            )
        else:
            self.controller.show_custom_dialog("Success", f"Deleted {success_count} program(s) successfully.")

    def edit_selected_programs(self):
        """Bulk edit selected programs (safe fields only)."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to edit programs.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more programs first.", dialog_type="warning")
            return

        program_codes = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                program_codes.append(str(row[1]))

        if not program_codes:
            self.controller.show_custom_dialog("No Selection", "No valid program rows selected.", dialog_type="warning")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Bulk Edit Programs")
        modal.geometry("460x260")
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

        ctk.CTkLabel(frame, text=f"Bulk Edit {len(program_codes)} Program(s)", font=get_font(16, True)).pack(anchor="w", pady=(0, 12))
        ctk.CTkLabel(frame, text="Set College", font=FONT_BOLD).pack(anchor="w")

        college_values = [c['code'] for c in self.controller.colleges]
        college_widget = StyledComboBox(frame, college_values)
        if college_values:
            college_widget.set(college_values[0])
        college_widget.pack(fill="x", pady=(0, 16))

        def save_bulk():
            selected_college = college_widget.get().strip()
            if not selected_college:
                self.controller.show_custom_dialog("Validation Error", "Pick a target college.", dialog_type="error")
                return

            if not self.controller.show_custom_dialog(
                "Confirm Bulk Edit",
                (
                    f"Apply this change to {len(program_codes)} program(s)?\n\n"
                    f"- Set College to {selected_college}"
                ),
                dialog_type="yesno",
            ):
                return

            success_count = 0
            failures = []
            for program_code in program_codes:
                success, msg = self.controller.update_program(program_code, {'college': selected_college})
                if success:
                    success_count += 1
                else:
                    failures.append(f"{program_code}: {msg}")

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
                    f"Updated {success_count}/{len(program_codes)} program(s).\n\nFailed:\n{preview}{more}",
                    dialog_type="warning",
                )
            else:
                self.controller.show_custom_dialog("Success", f"Updated {success_count} program(s) successfully.")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(btn_row, text="Apply Changes", command=save_bulk, fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", command=modal.destroy, fg_color="#555555", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(6, 0))

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
                self.bulk_edit_btn.pack(side="left", padx=(0, 8), before=self.entry_count_label)
            if not self.bulk_delete_btn.winfo_manager():
                self.bulk_delete_btn.pack(side="left", padx=(0, 8), before=self.entry_count_label)
        else:
            self.bulk_edit_btn.pack_forget()
            self.bulk_delete_btn.pack_forget()

        self._refresh_checkmarks()

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = selection[0]
        row_data = self.tree.item(selected_item)['values']
        prog_code = row_data[1]
        
        program = next((p for p in self.controller.programs if p['code'] == prog_code), None)
        if not program:
            return
        
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Program")
        edit_window.geometry("480x380")
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
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR, height=80)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{prog_code}", font=get_font(16, True)).place(x=16, y=14)
        ctk.CTkLabel(header, text="Program", font=get_font(13), text_color=TEXT_MUTED).place(x=16, y=44)
        
        # form card
        form_card = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        form_card.pack(fill="both", expand=True)
        form_frame = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(form_frame, text="Edit Program Information", font=get_font(13, True)).pack(anchor="w", pady=(0, 12))
        
        ctk.CTkLabel(form_frame, text="Program Code", font=FONT_BOLD).pack(anchor="w")
        code_entry = ctk.CTkEntry(form_frame, height=40)
        code_entry.insert(0, program['code'])
        code_entry.configure(state="disabled")
        code_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program Name", font=FONT_BOLD).pack(anchor="w")
        name_entry = ctk.CTkEntry(form_frame, height=40)
        name_entry.insert(0, program['name'])
        name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="College", font=FONT_BOLD).pack(anchor="w")
        college_values = [c['code'] for c in self.controller.colleges]
        college_widget = StyledComboBox(form_frame, college_values)
        college_widget.set(program['college'])
        college_widget.pack(fill="x", pady=(0, 20))
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            name = name_entry.get().strip()
            college = college_widget.get()
            
            if not name:
                return False, "Program Name is required"
            
            if not college:
                return False, "College must be selected"
            
            if not name.replace(" ", "").isalpha():
                return False, "Program Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return
            
            program_name = name_entry.get().strip().title()
            college_code = college_widget.get()
            
            success, msg = self.controller.update_program(prog_code, {
                'name': program_name,
                'college': college_code
            })
            
            if success:
                edit_window.destroy()
                self.controller.refresh_data()
                self.refresh_table()
                self.controller.show_custom_dialog("Success", "Program updated successfully!")
            else:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
        
        def delete():
            if self.controller.show_custom_dialog("Confirm Delete", f"Delete {prog_code}?", dialog_type="yesno"):
                success, msg = self.controller.delete_program(prog_code)
                if success:
                    edit_window.destroy()
                    self.controller.refresh_data()
                    self.refresh_table()
                    self.controller.show_custom_dialog("Success", msg)
                else:
                    self.controller.show_custom_dialog("Error", msg, dialog_type="error")
        
        ctk.CTkButton(button_frame, text="Save Changes", command=save, height=40,
                     fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Delete", command=delete, height=40,
                     fg_color=DANGER_COLOR, hover_color=DANGER_HOVER, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))

        animate_toplevel_in(edit_window, x=x, y=y)

