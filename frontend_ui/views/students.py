"""
Students view module extracted from original views.py
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from config import (
    FONT_MAIN, FONT_BOLD, BG_COLOR, PANEL_COLOR, ACCENT_COLOR, 
    TEXT_MUTED, BORDER_COLOR, COLOR_PALETTE, TEXT_PRIMARY
)
from config import get_font
from frontend_ui.ui import (
    DepthCard,
    setup_treeview_style,
    placeholder_image,
    get_icon,
    SearchableComboBox,
    StyledComboBox,
    animate_toplevel_in,
)
from backend import validate_student


class StudentsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.multi_edit_mode = False
        self.sort_column = None
        self.sort_reverse = False
        self.column_names = {}  # store original column names
        self.setup_ui()

    def setup_ui(self):
        # table Container
        table_container = DepthCard(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2, border_color=BORDER_COLOR)
        table_container.grid(row=1, column=0, sticky="nsew", columnspan=2)
        
        setup_treeview_style()
        cols = ("ID", "First Name", "Last Name", "Gender", "Year", "Program", "College")
        # create treeview without scrollbar and with fixed height of 12 rows
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
        
        # column widths and anchoring - center-align all content
        self.tree.column("ID", width=70, anchor="center", stretch=False)
        self.tree.column("First Name", width=130, anchor="center", stretch=False)
        self.tree.column("Last Name", width=130, anchor="center", stretch=False)
        self.tree.column("Gender", width=80, anchor="center", stretch=False)
        self.tree.column("Year", width=70, anchor="center", stretch=False)
        self.tree.column("Program", width=120, anchor="center", stretch=False)
        self.tree.column("College", width=120, anchor="center", stretch=False)
        
        self.tree.pack(fill="both", expand=True, padx=15, pady=(15, 12))

        # pagination controls - integrated layout
        ctrl = ctk.CTkFrame(table_container, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=(10,12))

        self.current_page = 1
        self.page_size = 12
        self._last_page_items = []
        self._last_hover = None
        self.table_container = table_container

        # left section: Previous button, pagination, and Next button together
        left_ctrl = ctk.CTkFrame(ctrl, fg_color="transparent")
        left_ctrl.pack(side="left")
        
        # previous Button
        self.prev_btn = ctk.CTkButton(
            left_ctrl, 
            text="◀ Prev", 
            width=80, 
            fg_color="#6d28d9", 
            hover_color="#5b21b6",
            text_color="white",
            command=lambda: self.change_page(-1)
        )
        self.prev_btn.pack(side="left", padx=(0,8))

        # pagination indicator frame
        self.pagination_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        self.pagination_frame.pack(side="left", padx=8)
        self.page_buttons = []
        
        # next Button - right next to pagination
        self.next_btn = ctk.CTkButton(
            left_ctrl, 
            text="Next ▶", 
            width=80, 
            fg_color="#6d28d9", 
            hover_color="#5b21b6",
            text_color="white",
            command=lambda: self.change_page(1)
        )
        self.next_btn.pack(side="left", padx=(8,0))
        
        # go to page section
        goto_frame = ctk.CTkFrame(left_ctrl, fg_color="transparent")
        goto_frame.pack(side="left", padx=(15, 0))
        
        ctk.CTkLabel(goto_frame, text="Go to:", font=get_font(12), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        
        self.page_entry = ctk.CTkEntry(goto_frame, width=50, height=30, 
                                       fg_color="#2A1F3D", border_color=BORDER_COLOR,
                                       text_color=TEXT_PRIMARY, font=get_font(12))
        self.page_entry.pack(side="left", padx=(0, 5))
        self.page_entry.bind("<Return>", lambda e: self.go_to_page())
        
        self.go_btn = ctk.CTkButton(goto_frame, text="Go", width=40, height=30,
                                    fg_color="#6d28d9", hover_color="#5b21b6",
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
            fg_color="#1d4ed8",
            hover_color="#1e40af",
            text_color="white",
            font=get_font(12, True),
            command=self.edit_selected_students,
        )

        self.bulk_delete_btn = ctk.CTkButton(
            right_ctrl,
            text="Delete Selected",
            width=130,
            height=30,
            fg_color="#c41e3a",
            hover_color="#a31a31",
            text_color="white",
            font=get_font(12, True),
            command=self.delete_selected_students,
        )
        # entry count label
        self.entry_count_label = ctk.CTkLabel(right_ctrl, text="Showing 0 of 0 entries", 
                                             font=get_font(13), text_color=TEXT_MUTED)
        self.entry_count_label.pack(side="left", padx=0)

        # bind configure event to update page size dynamically
        table_container.bind('<Configure>', self._on_table_configure)
        
        self.tree.bind("<Button-1>", self.on_column_click)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.bind("<Double-1>", self.on_row_double_click)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._refresh_checkmarks())
        self.tree.tag_configure('odd', background="#1a1620")
        self.tree.tag_configure('even', background="#0f0d12")
        self.tree.tag_configure('hover', background="#6d5a8a", foreground="#ffffff")
        
        # button-style tags for action columns
        self.tree.tag_configure('action_button', foreground=ACCENT_COLOR, font=get_font(12, True), background=PANEL_COLOR)
        self.tree.tag_configure('action_button_delete', foreground="#ff6b6b", font=get_font(12, True), background=PANEL_COLOR)
        
        self.refresh_table()

    def refresh_sidebar(self):
        """Sidebar removed - table now takes full width."""
        pass

    def _refresh_all_sidebars(self):
        """Sidebar removed - no longer needed."""
        pass

    def refresh_table(self):
        rows = []
        for student in self.controller.students:
            college = next((p['college'] for p in self.controller.programs if p['code'] == student.get('program', '')), 'N/A')
            rows.append((student.get('id', ''), student.get('firstname', ''), student.get('lastname', ''), student.get('gender', ''), student.get('year', ''), student.get('program', ''), college))

        self._last_page_items = rows
        self.current_page = min(max(1, self.current_page), max(1, (len(rows) + self.page_size - 1) // self.page_size))
        self._render_page()
        self._last_hover = None
        self._last_hover = None

    def _render_page(self):
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
        
        for btn in self.page_buttons:
            btn.destroy()
        self.page_buttons.clear()
        
        start_page = max(1, self.current_page - 2)
        end_page = min(total_pages, start_page + 4)
        if end_page - start_page < 4:
            start_page = max(1, end_page - 4)
        
        for p in range(start_page, end_page + 1):
            is_current = p == self.current_page
            btn = ctk.CTkButton(
                self.pagination_frame, 
                text=str(p), 
                width=32, 
                height=28,
                fg_color=ACCENT_COLOR if is_current else "#3b3b3f",
                command=lambda page=p: self.goto_page(page)
            )
            btn.pack(side="left", padx=2)
            self.page_buttons.append(btn)
        
        self.prev_btn.configure(state=("normal" if self.current_page > 1 else "disabled"))
        self.next_btn.configure(state=("normal" if self.current_page < total_pages else "disabled"))
    
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
        # adjust column widths based on available width with proportions
        available_width = max(self.table_container.winfo_width() - 20, 200)
        if available_width < 100:  # skip if window is too small
            return
        cols = ["ID", "First Name", "Last Name", "Gender", "Year", "Program", "College"]
        props = [0.10, 0.18, 0.19, 0.11, 0.09, 0.17, 0.16]
        for i, col in enumerate(cols):
            self.tree.column(col, width=max(int(available_width * props[i]), 50))
        
        # get actual available height and calculate how many rows can fit
        available_height = self.table_container.winfo_height()
        if available_height < 100:  # skip if window is too small
            return
        # account for: Treeview header (~20px) + padding (~12px) + pagination controls (~55px)
        reserved_height = 20 + 12 + 55
        usable_height = max(available_height - reserved_height, 50)
        row_height = 48  # height of each row (matches treeview rowheight in setup_treeview_style)
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
        """Sidebar removed - no longer needed."""
        pass

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
        row = self.tree.identify_row(event.y)
        if not row:
            return
        row_data = self.tree.item(row).get('values', [])
        if not row_data:
            return
        self._show_student_profile(row_data[0])

    def filter_table(self, query):
        self.apply_filters(query=query, advanced_filters=None)

    def apply_filters(self, query: str = "", advanced_filters=None):
        """Apply quick-search and advanced filters with AND semantics."""
        query = (query or "").strip().lower()
        advanced_filters = advanced_filters or {}

        id_filter = str(advanced_filters.get("id", "")).strip().lower()
        first_filter = str(advanced_filters.get("firstname", "")).strip().lower()
        last_filter = str(advanced_filters.get("lastname", "")).strip().lower()
        gender_filter = str(advanced_filters.get("gender", "")).strip().lower()
        year_filter = str(advanced_filters.get("year", "")).strip().lower()
        program_filter = str(advanced_filters.get("program", "")).strip().lower()
        college_filter = str(advanced_filters.get("college", "")).strip().lower()

        program_to_college = {
            str(p.get("code", "")): str(p.get("college", ""))
            for p in self.controller.programs
        }

        rows = []
        for student in self.controller.students:
            sid = str(student.get('id', ''))
            firstname = str(student.get('firstname', ''))
            lastname = str(student.get('lastname', ''))
            gender = str(student.get('gender', ''))
            year = str(student.get('year', ''))
            program = str(student.get('program', ''))
            college_text = program_to_college.get(program, 'N/A')

            sid_l = sid.lower()
            firstname_l = firstname.lower()
            lastname_l = lastname.lower()
            gender_l = gender.lower()
            year_l = year.lower()
            program_l = program.lower()
            college_l = college_text.lower()

            if query and not (
                query in firstname_l or
                query in lastname_l or
                query in sid_l or
                query in gender_l or
                query in program_l or
                query in year_l or
                query in college_l
            ):
                continue

            if id_filter and id_filter not in sid_l:
                continue
            if first_filter and first_filter not in firstname_l:
                continue
            if last_filter and last_filter not in lastname_l:
                continue
            if gender_filter and gender_filter != "any" and gender_filter != gender_l:
                continue
            if year_filter and year_filter != "any" and year_filter != year_l:
                continue
            if program_filter and program_filter != "any" and program_filter != program_l:
                continue
            if college_filter and college_filter != "any" and college_filter != college_l:
                continue

            rows.append((sid, firstname, lastname, gender, year, program, college_text))

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

    def _show_student_profile(self, student_id):
        """Show student profile in a new window."""
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            self.controller.show_custom_dialog("Error", "Student not found", dialog_type="error")
            return

        profile_window = ctk.CTkToplevel(self)
        profile_window.title(f"Student Profile: {student.get('firstname')} {student.get('lastname')}")
        profile_window.geometry("750x600")
        profile_window.configure(fg_color=BG_COLOR)
        profile_window.attributes('-topmost', True)
        profile_window.grab_set()
        profile_window.focus_force()

        profile_window.update_idletasks()
        x = (profile_window.winfo_screenwidth() // 2) - (profile_window.winfo_width() // 2)
        y = (profile_window.winfo_screenheight() // 2) - (profile_window.winfo_height() // 2)
        profile_window.geometry(f"+{x}+{y}")
        animate_toplevel_in(profile_window, x=x, y=y)

        container = ctk.CTkFrame(profile_window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # header with avatar and name
        header = DepthCard(container, fg_color=PANEL_COLOR, corner_radius=12, border_width=2, border_color=BORDER_COLOR)
        header.pack(fill="x", pady=(0, 15))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=16)

        avatar = ctk.CTkFrame(header_inner, width=72, height=72, fg_color="#2d1f45", corner_radius=10)
        avatar.pack(side="left", padx=(0, 16))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text="\U0001f464", font=get_font(32)).pack(expand=True)

        name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
        text_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_frame, text=name, font=get_font(16, True), wraplength=550, justify="left", anchor="w").pack(fill="x", anchor="w")
        ctk.CTkLabel(text_frame, text=f"ID: {student.get('id', '')}", text_color=TEXT_MUTED, font=get_font(13), anchor="w").pack(fill="x", anchor="w", pady=(4, 0))

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

        add_info_row("First Name:", student.get('firstname', 'N/A'))
        add_info_row("Last Name:", student.get('lastname', 'N/A'))
        add_info_row("Gender:", student.get('gender', 'N/A'))
        add_info_row("Year Level:", student.get('year', 'N/A'))
        add_info_row("Program:", student.get('program', 'N/A'))
        
        program_name = next((p['name'] for p in self.controller.programs if p['code'] == student.get('program')), 'N/A')
        college_name = next((c['name'] for c in self.controller.colleges if c['code'] == next((p['college'] for p in self.controller.programs if p['code'] == student.get('program')), '')), 'N/A')
        add_info_row("College:", college_name)

        # action buttons - only show if authenticated

        def _edit():
            profile_window.destroy()
            self._edit_student(student_id)

        def _delete():
            if self.controller.show_custom_dialog("Confirm Delete", f"Delete student {name}?", dialog_type="yesno"):
                profile_window.destroy()
                self._delete_student_by_id(student_id)

        # only show edit/delete buttons if user is logged in
        if self.controller.logged_in:
            ctk.CTkButton(btn_frame, text="Edit", command=_edit, fg_color=ACCENT_COLOR, text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Delete", command=_delete, fg_color="#c41e3a", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))
        else:
            # show message prompting login
            login_msg = ctk.CTkLabel(btn_frame, text="🔒 Log in to edit or delete", font=get_font(13), text_color=TEXT_MUTED)
            login_msg.pack(fill="x", pady=10)

    def _edit_student(self, student_id):
        """Edit student in a modal window."""
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to edit students.")
            return
        
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            self.controller.show_custom_dialog("Error", "Student not found", dialog_type="error")
            return

        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Student")
        edit_window.geometry("520x480")
        edit_window.configure(fg_color=BG_COLOR)
        edit_window.attributes('-topmost', True)
        edit_window.grab_set()
        edit_window.focus_force()

        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        animate_toplevel_in(edit_window, x=x, y=y)

        form_frame = ctk.CTkScrollableFrame(edit_window, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Edit Student Information", font=get_font(16, True)).pack(pady=(0, 20))

        ctk.CTkLabel(form_frame, text="Student ID", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        id_entry = ctk.CTkEntry(form_frame, height=40)
        id_entry.insert(0, student['id'])
        id_entry.configure(state="disabled")
        id_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="First Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        fname_entry = ctk.CTkEntry(form_frame, height=40)
        fname_entry.insert(0, student['firstname'])
        fname_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Last Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        lname_entry = ctk.CTkEntry(form_frame, height=40)
        lname_entry.insert(0, student['lastname'])
        lname_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Gender", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        gender_combo = StyledComboBox(form_frame, ["Male", "Female", "Other"])
        gender_combo.set(student['gender'])
        gender_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = StyledComboBox(form_frame, ["1", "2", "3", "4", "5"])
        year_combo.set(student['year'])
        year_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        program_widget = SearchableComboBox(form_frame, program_values)
        program_widget.set(student['program'])
        program_widget.pack(fill="x", pady=(0, 20))

        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()

            if not fname:
                return False, "First Name is required"
            if not lname:
                return False, "Last Name is required"
            if not gender or gender == "Select Gender":
                return False, "Gender must be selected"
            if not year or year == "Select Year":
                return False, "Year Level must be selected"
            if not program:
                return False, "Program must be selected"

            if not fname.replace(" ", "").isalpha():
                return False, "First Name must contain only letters and spaces"
            if not lname.replace(" ", "").isalpha():
                return False, "Last Name must contain only letters and spaces"

            return True, ""

        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return

            updates = {
                'firstname': fname_entry.get().strip().title(),
                'lastname': lname_entry.get().strip().title(),
                'gender': gender_combo.get(),
                'year': year_combo.get(),
                'program': program_widget.get(),
            }

            candidate = {'id': student_id, **updates}
            ok, msg = validate_student(candidate)
            if not ok:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return

            success, msg = self.controller.update_student(student_id, updates)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return

            edit_window.destroy()
            self.refresh_table()
            self.controller.show_custom_dialog("Success", "Student updated successfully!")

        def delete():
            if self.controller.show_custom_dialog("Confirm Delete", f"Delete {student['id']}?", dialog_type="yesno"):
                success, msg = self.controller.delete_student(student_id)
                if not success:
                    self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                    return
                edit_window.destroy()
                self.refresh_table()
                self.controller.show_custom_dialog("Success", "Student deleted successfully!")

        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btn_frame, text="Save Changes", command=save, height=40, fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete", command=delete, height=40, fg_color="#c41e3a", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _delete_student_by_id(self, student_id):
        """Delete a student by ID."""
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete students.")
            return
        
        student = next((s for s in self.controller.students if s['id'] == student_id), None)
        if not student:
            self.controller.show_custom_dialog("Error", "Student not found", dialog_type="error")
            return

        if self.controller.show_custom_dialog("Confirm Delete", f"Delete student {student_id}?", dialog_type="yesno"):
            success, msg = self.controller.delete_student(student_id)
            if not success:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            self.refresh_table()
            self.controller.show_custom_dialog("Success", "Student deleted successfully!")

    def delete_selected_students(self):
        """Delete multiple selected students from the table."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to delete students.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more students first.", dialog_type="warning")
            return

        student_ids = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                student_ids.append(str(row[0]))

        if not student_ids:
            self.controller.show_custom_dialog("No Selection", "No valid student rows selected.", dialog_type="warning")
            return

        if not self.controller.show_custom_dialog(
            "Confirm Bulk Delete",
            f"Delete {len(student_ids)} selected student(s)?\nThis action cannot be undone.",
            dialog_type="yesno",
        ):
            return

        success_count = 0
        failures = []
        for student_id in student_ids:
            success, msg = self.controller.delete_student(student_id)
            if success:
                success_count += 1
            else:
                failures.append(f"{student_id}: {msg}")

        self.refresh_table()

        if failures:
            preview = "\n".join(failures[:5])
            more = "" if len(failures) <= 5 else f"\n...and {len(failures) - 5} more"
            self.controller.show_custom_dialog(
                "Bulk Delete Complete",
                f"Deleted {success_count}/{len(student_ids)} student(s).\n\nFailed:\n{preview}{more}",
                dialog_type="warning",
            )
        else:
            self.controller.show_custom_dialog("Success", f"Deleted {success_count} student(s) successfully.")

    def edit_selected_students(self):
        """Bulk edit selected students (safe fields only)."""
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to edit students.")
            return
        if not self.multi_edit_mode:
            self.controller.show_custom_dialog("Mode Required", "Enable Multi-Edit mode first.", dialog_type="warning")
            return

        selections = self.tree.selection()
        if not selections:
            self.controller.show_custom_dialog("No Selection", "Select one or more students first.", dialog_type="warning")
            return

        student_ids = []
        for item in selections:
            row = self.tree.item(item).get('values', [])
            if row:
                student_ids.append(str(row[0]))

        if not student_ids:
            self.controller.show_custom_dialog("No Selection", "No valid student rows selected.", dialog_type="warning")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Bulk Edit Students")
        modal.geometry("480x340")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        modal.grab_set()
        modal.focus_force()

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"+{x}+{y}")
        animate_toplevel_in(modal, x=x, y=y)

        frame = ctk.CTkFrame(modal, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"Bulk Edit {len(student_ids)} Student(s)", font=get_font(16, True)).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Year Level", font=FONT_BOLD).pack(anchor="w")
        year_widget = StyledComboBox(frame, ["(No change)", "1", "2", "3", "4", "5"])
        year_widget.set("(No change)")
        year_widget.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(frame, text="Program", font=FONT_BOLD).pack(anchor="w")
        program_values = [p['code'] for p in self.controller.programs]
        program_widget = SearchableComboBox(frame, program_values, placeholder="(No change)")
        program_widget.pack(fill="x", pady=(0, 16))

        def save_bulk():
            updates = {}
            selected_year = year_widget.get().strip()
            selected_program = program_widget.get().strip()

            if selected_year and selected_year != "(No change)":
                updates['year'] = selected_year
            if selected_program:
                updates['program'] = selected_program

            if not updates:
                self.controller.show_custom_dialog("No Changes", "Pick at least one field to update.", dialog_type="warning")
                return

            preview_lines = []
            if 'year' in updates:
                preview_lines.append(f"- Set Year to {updates['year']}")
            if 'program' in updates:
                preview_lines.append(f"- Set Program to {updates['program']}")

            if not self.controller.show_custom_dialog(
                "Confirm Bulk Edit",
                f"Apply these changes to {len(student_ids)} student(s)?\n\n" + "\n".join(preview_lines),
                dialog_type="yesno",
            ):
                return

            success_count = 0
            failures = []
            for student_id in student_ids:
                success, msg = self.controller.update_student(student_id, dict(updates))
                if success:
                    success_count += 1
                else:
                    failures.append(f"{student_id}: {msg}")

            self.refresh_table()
            modal.destroy()

            if failures:
                preview = "\n".join(failures[:5])
                more = "" if len(failures) <= 5 else f"\n...and {len(failures) - 5} more"
                self.controller.show_custom_dialog(
                    "Bulk Edit Complete",
                    f"Updated {success_count}/{len(student_ids)} student(s).\n\nFailed:\n{preview}{more}",
                    dialog_type="warning",
                )
            else:
                self.controller.show_custom_dialog("Success", f"Updated {success_count} student(s) successfully.")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(btn_row, text="Apply Changes", command=save_bulk, fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", command=modal.destroy, fg_color="#555555", text_color="white", font=FONT_BOLD, height=40).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _refresh_checkmarks(self):
        """Render checkbox glyphs in the left tree column for multi-edit mode."""
        for item in self.tree.get_children():
            if not self.multi_edit_mode:
                self.tree.item(item, text="")
            else:
                self.tree.item(item, text="☑" if item in self.tree.selection() else "☐")

    def set_multi_edit_mode(self, enabled: bool):
        """Enable or disable multi-edit controls and checkbox column."""
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

    def delete_student(self):
        """Legacy method - use _delete_student_by_id instead."""
        pass

    def add_student(self):
        # check authentication
        if not self.controller.logged_in:
            self.controller.show_custom_dialog("Access Denied", "You must log in to add students.")
            return
        
        modal = ctk.CTkToplevel(self)
        modal.title("Add Student")
        screen_height = modal.winfo_screenheight()
        height = min(600, int(screen_height * 0.7))
        modal.geometry(f"500x{height}")
        modal.configure(fg_color=BG_COLOR)
        modal.attributes('-topmost', True)
        modal.grab_set()
        modal.focus_force()
        
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (modal.winfo_width() // 2)
        y = (modal.winfo_screenheight() // 2) - (modal.winfo_height() // 2)
        modal.geometry(f"500x{height}+{x}+{y}")
        animate_toplevel_in(modal, x=x, y=y)
        
        form_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="New Student Enrollment", font=get_font(16, True)).pack(pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Student ID", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        id_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., 2024-0001", height=40)
        id_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="First Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        fname_entry = ctk.CTkEntry(form_frame, placeholder_text="First Name", height=40)
        fname_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Last Name", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        lname_entry = ctk.CTkEntry(form_frame, placeholder_text="Last Name", height=40)
        lname_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Gender", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        gender_combo = StyledComboBox(form_frame, ["Male", "Female", "Other"])
        gender_combo.set("Male")
        gender_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Year Level", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        year_combo = StyledComboBox(form_frame, ["1", "2", "3", "4", "5"])
        year_combo.set("1")
        year_combo.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Program", font=FONT_BOLD).pack(anchor="w", pady=(10, 0))
        program_values = [p['code'] for p in self.controller.programs]
        program_widget = SearchableComboBox(form_frame, program_values)
        program_widget.pack(fill="x", pady=(0, 20))
        
        def validate_form():
            """Validate form inputs and return (is_valid, error_message)."""
            student_id = id_entry.get().strip()
            fname = fname_entry.get().strip()
            lname = lname_entry.get().strip()
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()
            
            # check empty fields
            if not student_id:
                return False, "Student ID is required"
            if not fname:
                return False, "First Name is required"
            if not lname:
                return False, "Last Name is required"
            if not gender or gender == "Select Gender":
                return False, "Gender must be selected"
            if not year or year == "Select Year":
                return False, "Year Level must be selected"
            if not program:
                return False, "Program must be selected"
            
            # check ID format: must be 202x-xxxx
            import re
            if not re.match(r'^202\d-\d{4}$', student_id):
                return False, "Student ID must follow the format 202X-XXXX (e.g. 2024-0001)"
            
            # check for duplicate ID
            if any(s['id'] == student_id for s in self.controller.students):
                return False, "Student ID already exists"
            
            # check name format (only letters and spaces)
            if not fname.replace(" ", "").isalpha():
                return False, "First Name must contain only letters and spaces"
            if not lname.replace(" ", "").isalpha():
                return False, "Last Name must contain only letters and spaces"
            
            return True, ""
        
        def save():
            is_valid, error_msg = validate_form()
            if not is_valid:
                self.controller.show_custom_dialog("Validation Error", error_msg, dialog_type="error")
                return
            
            student_id = id_entry.get().strip()
            fname = fname_entry.get().strip().title()  # capitalize
            lname = lname_entry.get().strip().title()  # capitalize
            gender = gender_combo.get()
            year = year_combo.get()
            program = program_widget.get()
            
            new_student = {
                'id': student_id,
                'firstname': fname,
                'lastname': lname,
                'gender': gender,
                'year': year,
                'program': program,
            }
            ok, msg = validate_student(new_student)
            if not ok:
                self.controller.show_custom_dialog("Error", msg, dialog_type="error")
                return
            
            success, msg = self.controller.add_student(new_student)
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
            self.controller.show_custom_dialog("Success", "Student added successfully!")
        
        # button row: Save and Cancel
        btn_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8,0))
        ctk.CTkButton(btn_row, text="Save Student", command=save, height=40, 
                 fg_color=ACCENT_COLOR, text_color=TEXT_PRIMARY, font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="Cancel", command=modal.destroy, height=40,
                 fg_color="#555555", text_color="white", font=FONT_BOLD).pack(side="left", fill="x", expand=True, padx=(6, 0))


