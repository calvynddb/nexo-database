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
from backend import init_files, get_session
from backend.models import College, Program, Student, User
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

    def update_student(self, student_id: str, updates: dict) -> tuple[bool, str]:
        """Update a student in the database and refresh cache.
        
        Args:
            student_id: Student ID (e.g., "2023-0001")
            updates: Dict with fields to update (firstname, lastname, gender, year, program)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            student = session.query(Student).filter(Student.id == student_id).first()
            
            if not student:
                session.close()
                return False, "Student not found"
            
            # Handle program code -> program_id lookup
            if 'program' in updates:
                program = session.query(Program).filter(Program.code == updates['program']).first()
                if not program:
                    session.close()
                    return False, f"Program '{updates['program']}' not found"
                student.program_id = program.id
                updates.pop('program')
            
            # Update allowed fields
            for key, value in updates.items():
                if key in ('firstname', 'lastname', 'gender', 'year'):
                    if key == 'year':
                        setattr(student, key, int(value))
                    else:
                        setattr(student, key, value)
            
            session.commit()
            session.close()
            self.refresh_data()
            return True, "Student updated successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        """Delete a student from the database and refresh cache.
        
        Args:
            student_id: Student ID (e.g., "2023-0001")
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            student = session.query(Student).filter(Student.id == student_id).first()
            
            if not student:
                session.close()
                return False, "Student not found"
            
            session.delete(student)
            session.commit()
            session.close()
            self.refresh_data()
            return True, "Student deleted successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def add_student(self, student_data: dict) -> tuple[bool, str]:
        """Add a new student to the database and refresh cache.
        
        Args:
            student_data: Dict with fields (id, firstname, lastname, gender, year, program)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            
            # Check if ID already exists
            existing = session.query(Student).filter(Student.id == student_data['id']).first()
            if existing:
                session.close()
                return False, "Student ID already exists"
            
            # Look up program by code
            program = session.query(Program).filter(Program.code == student_data['program']).first()
            if not program:
                session.close()
                return False, f"Program '{student_data['program']}' not found"
            
            # Create new student
            new_student = Student(
                id=student_data['id'],
                firstname=student_data['firstname'],
                lastname=student_data['lastname'],
                program_id=program.id,
                year=int(student_data['year']),
                gender=student_data['gender']
            )
            
            session.add(new_student)
            session.commit()
            session.close()
            self.refresh_data()
            return True, "Student added successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def update_program(self, program_code: str, updates: dict) -> tuple[bool, str]:
        """Update a program in the database and refresh cache.
        
        Args:
            program_code: Program code (e.g., "CS101")
            updates: Dict with fields to update (name, college)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            program = session.query(Program).filter(Program.code == program_code).first()
            
            if not program:
                session.close()
                return False, "Program not found"
            
            # Handle college code -> college_id lookup
            if 'college' in updates:
                college = session.query(College).filter(College.code == updates['college']).first()
                if not college:
                    session.close()
                    return False, f"College '{updates['college']}' not found"
                program.college_id = college.id
                updates.pop('college')
            
            # Update allowed fields
            for key, value in updates.items():
                if key in ('name',):
                    setattr(program, key, value)
            
            session.commit()
            session.close()
            self.refresh_data()
            return True, "Program updated successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_program(self, program_code: str) -> tuple[bool, str]:
        """Delete a program from the database and refresh cache.
        
        Args:
            program_code: Program code (e.g., "CS101")
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            program = session.query(Program).filter(Program.code == program_code).first()

            if not program:
                return False, "Program not found"

            affected_students_query = session.query(Student).filter(Student.program_id == program.id)
            affected_students = affected_students_query.count()
            for student in affected_students_query.all():
                student.program_id = None

            session.flush()
            session.delete(program)
            session.commit()
            self.refresh_data()
            return True, (
                "Program deleted successfully. "
                f"Cleared program assignment for {affected_students} student(s)."
            )
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def add_program(self, program_data: dict) -> tuple[bool, str]:
        """Add a new program to the database and refresh cache.
        
        Args:
            program_data: Dict with fields (code, name, college)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            
            # Check if code already exists
            existing = session.query(Program).filter(Program.code == program_data['code']).first()
            if existing:
                session.close()
                return False, "Program code already exists"
            
            # Look up college by code
            college = session.query(College).filter(College.code == program_data['college']).first()
            if not college:
                session.close()
                return False, f"College '{program_data['college']}' not found"
            
            # Create new program
            new_program = Program(
                code=program_data['code'],
                name=program_data['name'],
                college_id=college.id
            )
            
            session.add(new_program)
            session.commit()
            session.close()
            self.refresh_data()
            return True, "Program added successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def update_college(self, college_code: str, updates: dict) -> tuple[bool, str]:
        """Update a college in the database and refresh cache.
        
        Args:
            college_code: College code
            updates: Dict with fields to update (name)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            college = session.query(College).filter(College.code == college_code).first()
            
            if not college:
                session.close()
                return False, "College not found"
            
            # Update allowed fields
            for key, value in updates.items():
                if key in ('name',):
                    setattr(college, key, value)
            
            session.commit()
            session.close()
            self.refresh_data()
            return True, "College updated successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_college(self, college_code: str) -> tuple[bool, str]:
        """Delete a college from the database and refresh cache.
        
        Args:
            college_code: College code
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            college = session.query(College).filter(College.code == college_code).first()

            if not college:
                return False, "College not found"

            affected_programs_query = session.query(Program).filter(Program.college_id == college.id)
            affected_programs = affected_programs_query.count()
            for program in affected_programs_query.all():
                program.college_id = None

            session.flush()
            session.delete(college)
            session.commit()
            self.refresh_data()
            return True, (
                "College deleted successfully. "
                f"Cleared college assignment for {affected_programs} program(s)."
            )
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def add_college(self, college_data: dict) -> tuple[bool, str]:
        """Add a new college to the database and refresh cache.
        
        Args:
            college_data: Dict with fields (code, name)
            
        Returns:
            (success: bool, message: str)
        """
        try:
            session = get_session()
            
            # Check if code already exists
            existing = session.query(College).filter(College.code == college_data['code']).first()
            if existing:
                session.close()
                return False, "College code already exists"
            
            # Create new college
            new_college = College(
                code=college_data['code'],
                name=college_data['name']
            )
            
            session.add(new_college)
            session.commit()
            session.close()
            self.refresh_data()
            return True, "College added successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_user(self, username: str, password: str) -> tuple[bool, str]:
        """Create a new user in the database.
        
        Args:
            username: Username
            password: Plain-text password
            
        Returns:
            (success: bool, message: str)
        """
        try:
            from backend.auth import hash_password
            from backend.models import User
            
            session = get_session()
            
            # Check if user already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                session.close()
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
            session.close()
            return True, f"User '{username}' created successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def change_password(self, username: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change a user's password.
        
        Args:
            username: Username
            old_password: Current password (for verification)
            new_password: New password
            
        Returns:
            (success: bool, message: str)
        """
        try:
            from backend.auth import hash_password, verify_password
            from backend.models import User
            
            session = get_session()
            
            # Find user
            user = session.query(User).filter(User.username == username).first()
            if not user:
                session.close()
                return False, f"User '{username}' not found"
            
            # Verify old password
            if not verify_password(old_password, user.salt, user.password):
                session.close()
                return False, "Current password is incorrect"
            
            # Hash new password
            salt, pw_hash = hash_password(new_password)
            user.salt = salt
            user.password = pw_hash
            
            session.commit()
            session.close()
            return True, "Password changed successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"


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
