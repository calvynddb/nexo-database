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
from config import WINDOW_WIDTH, WINDOW_HEIGHT
from backend import get_session, hash_password, init_files, verify_password
from backend.models import College, Program, Student, User
from backend.validators import validate_password
from backend.students import StudentController
from backend.programs import ProgramController
from backend.colleges import CollegeController
from frontend_ui.auth import LoginFrame
from frontend_ui.dashboard import DashboardFrame
from frontend_ui.ui.utils import show_dialog, apply_window_icon


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("calvynddb.nexo-database")
            except Exception:
                pass

        super().__init__()
        self.title("nexo")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        apply_window_icon(self)
        self.logged_in = False
        self._load_data()
        self._init_controllers()
        self._build_frames()
        self.current_frame = None
        self.show_frame(DashboardFrame, fade=False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.report_callback_exception = self._handle_callback_exception

    def _handle_callback_exception(self, exc_type, exc_val, exc_tb):
        """Suppress KeyboardInterrupt in Tkinter callbacks; log everything else."""
        if issubclass(exc_type, KeyboardInterrupt):
            return
        import traceback
        traceback.print_exception(exc_type, exc_val, exc_tb)

    def _on_close(self):
        """Cancel all pending after() callbacks before destroying to suppress bgerror noise."""
        try:
            for after_id in self.tk.eval('after info').split():
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass
        self.destroy()

    def _load_data(self):
        """Initialize database and load all data from SQLite, falling back to empty lists on error."""
        session = None
        try:
            init_files()

            # Load data from database
            session = get_session()
            colleges = session.query(College).all()
            programs = session.query(Program).all()
            students = session.query(Student).all()

            # Convert SQLAlchemy objects to dictionaries for frontend compatibility
            # (Phase 1: maintain existing frontend interface; Phase 2 will refactor to use ORM directly)
            self.colleges = [{'code': c.code, 'name': c.name} for c in colleges]
            self.programs = [
                {
                    'code': p.code,
                    'name': p.name,
                    'college': p.college.code if p.college else ''
                }
                for p in programs
            ]
            self.students = [
                {
                    'id': s.id,
                    'firstname': s.firstname,
                    'lastname': s.lastname,
                    'program': s.program.code if s.program else '',
                    'year': str(s.year),
                    'gender': s.gender
                }
                for s in students
            ]
        except Exception:
            import traceback
            traceback.print_exc()
            self.colleges = []
            self.programs = []
            self.students = []
        finally:
            if session is not None:
                session.close()

    def refresh_data(self):
        """Reload all data from database after modifications."""
        self._load_data()

    def _init_controllers(self):
        """Initialize CRUDL controllers used by UI-facing wrapper methods."""
        self.student_controller = StudentController(get_session, self.refresh_data)
        self.program_controller = ProgramController(get_session, self.refresh_data)
        self.college_controller = CollegeController(get_session, self.refresh_data)

    def update_student(self, student_id: str, updates: dict) -> tuple[bool, str]:
        """Update a student in the database and refresh cache."""
        return self.student_controller.update_student(student_id, updates)

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        """Delete a student from the database and refresh cache."""
        return self.student_controller.delete_student(student_id)

    def add_student(self, student_data: dict) -> tuple[bool, str]:
        """Add a new student to the database and refresh cache."""
        return self.student_controller.add_student(student_data)

    def update_program(self, program_code: str, updates: dict) -> tuple[bool, str]:
        """Update a program in the database and refresh cache."""
        return self.program_controller.update_program(program_code, updates)

    def delete_program(self, program_code: str) -> tuple[bool, str]:
        """Delete a program from the database and refresh cache."""
        return self.program_controller.delete_program(program_code)

    def add_program(self, program_data: dict) -> tuple[bool, str]:
        """Add a new program to the database and refresh cache."""
        return self.program_controller.add_program(program_data)

    def update_college(self, college_code: str, updates: dict) -> tuple[bool, str]:
        """Update a college in the database and refresh cache."""
        return self.college_controller.update_college(college_code, updates)

    def delete_college(self, college_code: str) -> tuple[bool, str]:
        """Delete a college from the database and refresh cache."""
        return self.college_controller.delete_college(college_code)

    def add_college(self, college_data: dict) -> tuple[bool, str]:
        """Add a new college to the database and refresh cache."""
        return self.college_controller.add_college(college_data)

    def bulk_upsert_students(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        """Create or update many students in one transaction."""
        return self.student_controller.bulk_upsert_students(records, overwrite_existing=overwrite_existing)

    def bulk_upsert_programs(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        """Create or update many programs in one transaction."""
        return self.program_controller.bulk_upsert_programs(records, overwrite_existing=overwrite_existing)

    def bulk_upsert_colleges(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        """Create or update many colleges in one transaction."""
        return self.college_controller.bulk_upsert_colleges(records, overwrite_existing=overwrite_existing)

    def create_user(self, username: str, password: str) -> tuple[bool, str]:
        """Create a new user in the database.
        
        Args:
            username: Username
            password: Plain-text password
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            username = str(username or '').strip()
            ok, msg = validate_password(password)
            if not ok:
                return False, msg
            if not username:
                return False, "Username is required"
            
            # Check if user already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                return False, f"Username '{username}' already exists"
            
            # Hash password with salt
            salt, pw_hash = hash_password(password)
            
            # Create new user
            new_user = User(
                username=username,
                salt=salt,
                password=pw_hash
            )
            
            session.add(new_user)
            session.commit()
            return True, f"User '{username}' created successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def change_password(self, username: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change a user's password.
        
        Args:
            username: Username
            old_password: Current password (for verification)
            new_password: New password
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            username = str(username or '').strip()
            old_password = str(old_password or '')
            ok, msg = validate_password(new_password)
            if not ok:
                return False, msg
            if not username:
                return False, "Username is required"
            if not old_password:
                return False, "Current password is required"
            
            # Find user
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False, f"User '{username}' not found"
            
            # Verify old password
            if not verify_password(old_password, user.salt, user.password):
                return False, "Current password is incorrect"
            
            # Hash new password
            salt, pw_hash = hash_password(new_password)
            user.salt = salt
            user.password = pw_hash
            
            session.commit()
            return True, "Password changed successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()


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
