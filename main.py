"""
Main entry point for nexo SIS application.
"""

import os
import sys
import tempfile

# matplotlib needs a writable config/cache dir — critical inside a frozen PyInstaller exe
# where _MEIPASS is read-only. Point it to a persistent temp folder before any import.
if getattr(sys, 'frozen', False):
    _mpl_dir = os.path.join(tempfile.gettempdir(), 'nexo_mpl_cache')
    os.makedirs(_mpl_dir, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', _mpl_dir)
    os.environ.setdefault('MPLBACKEND', 'TkAgg')

import customtkinter as ctk
from config import BG_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT, resource_path
from backend import init_files, load_csv
from frontend_ui.auth import LoginFrame
from frontend_ui.dashboard import DashboardFrame
from frontend_ui.ui.utils import show_dialog


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("nexo")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        try:
            self.iconbitmap(resource_path("assets/nexo.ico"))
        except Exception:
            pass
        self.logged_in = False
        self._load_data()
        self._build_frames()
        self.current_frame = None
        self.show_frame(DashboardFrame, fade=False)

    def _load_data(self):
        """Initialise CSV files and load all data, falling back to empty lists on error."""
        init_files()
        for key, attr in (('college', 'colleges'), ('program', 'programs'), ('student', 'students')):
            try:
                setattr(self, attr, load_csv(key))
            except Exception:
                import traceback
                traceback.print_exc()
                setattr(self, attr, [])

    def _build_frames(self):
        """Create the root container and instantiate all application frames."""
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoginFrame, DashboardFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            # use place so frames stack and can be swapped by lifting
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_custom_dialog(self, title, message, dialog_type="info", callback=None):
        """Show a custom styled dialog matching the app theme.

        dialog_type: 'info', 'error', 'warning', 'yesno'
        For 'yesno', returns True/False. For others, returns None.
        """
        return show_dialog(self, title, message, dialog_type, callback)

    def show_frame(self, cont, fade=True):
        """Show a specific frame, optionally with a fade transition."""
        new_frame = self.frames[cont]
        if self.current_frame is new_frame:
            return
        self.current_frame = new_frame

        def _on_shown():
            if hasattr(new_frame, 'on_frame_shown'):
                try:
                    new_frame.on_frame_shown()
                except Exception:
                    pass

        from frontend_ui.ui.utils import apply_button_hover, fade_transition

        if not fade:
            new_frame.lift()
            try:
                apply_button_hover(new_frame)
            except Exception:
                pass
            _on_shown()
            return

        try:
            fade_transition(self, new_frame, on_shown=_on_shown)
        except Exception:
            # fallback to instant raise
            new_frame.tkraise()
            try:
                apply_button_hover(new_frame)
            except Exception:
                pass
            _on_shown()


def main():
    """Run the application."""
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        import sys
        traceback.print_exc()
        try:
            # try to show a dialog if tkinter is still usable
            from tkinter import messagebox
            messagebox.showerror("Application Error", f"Unhandled exception during startup:\n{e}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
