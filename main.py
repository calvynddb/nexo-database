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
from backend import get_session, hash_password, init_files, verify_password
from backend.models import College, Program, Student, User
from backend.validators import validate_college, validate_password, validate_program, validate_student
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
        session = get_session()
        try:
            student = session.query(Student).filter(Student.id == student_id).first()
            
            if not student:
                return False, "Student not found"

            clean_updates = {}
            for key, value in (updates or {}).items():
                if key in ('firstname', 'lastname', 'gender', 'year', 'program'):
                    clean_updates[key] = str(value).strip() if value is not None else ""

            existing_program_code = student.program.code if student.program else ""
            candidate = {
                'id': student.id,
                'firstname': clean_updates.get('firstname', student.firstname),
                'lastname': clean_updates.get('lastname', student.lastname),
                'gender': clean_updates.get('gender', student.gender),
                'year': clean_updates.get('year', str(student.year)),
                'program': clean_updates.get('program', existing_program_code),
            }
            ok, msg = validate_student(candidate, require_program=False)
            if not ok:
                return False, msg
            
            # Handle program code -> program_id lookup
            if 'program' in clean_updates:
                program_code = clean_updates['program']
                if program_code:
                    program = session.query(Program).filter(Program.code == program_code).first()
                    if not program:
                        return False, f"Program '{program_code}' not found"
                    student.program_id = program.id
                else:
                    student.program_id = None
            
            # Update allowed fields
            if 'firstname' in clean_updates:
                student.firstname = clean_updates['firstname'].title()
            if 'lastname' in clean_updates:
                student.lastname = clean_updates['lastname'].title()
            if 'gender' in clean_updates:
                student.gender = clean_updates['gender'].title()
            if 'year' in clean_updates:
                student.year = int(clean_updates['year'])
            
            session.commit()
            self.refresh_data()
            return True, "Student updated successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

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
        session = get_session()
        try:
            candidate = {
                'id': str(student_data.get('id', '')).strip(),
                'firstname': str(student_data.get('firstname', '')).strip(),
                'lastname': str(student_data.get('lastname', '')).strip(),
                'gender': str(student_data.get('gender', '')).strip(),
                'year': str(student_data.get('year', '')).strip(),
                'program': str(student_data.get('program', '')).strip(),
            }

            ok, msg = validate_student(candidate, require_program=True)
            if not ok:
                return False, msg
            
            # Check if ID already exists
            existing = session.query(Student).filter(Student.id == candidate['id']).first()
            if existing:
                return False, "Student ID already exists"
            
            # Look up program by code
            program = session.query(Program).filter(Program.code == candidate['program']).first()
            if not program:
                return False, f"Program '{candidate['program']}' not found"
            
            # Create new student
            new_student = Student(
                id=candidate['id'],
                firstname=candidate['firstname'].title(),
                lastname=candidate['lastname'].title(),
                program_id=program.id,
                year=int(candidate['year']),
                gender=candidate['gender'].title()
            )
            
            session.add(new_student)
            session.commit()
            self.refresh_data()
            return True, "Student added successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def update_program(self, program_code: str, updates: dict) -> tuple[bool, str]:
        """Update a program in the database and refresh cache.
        
        Args:
            program_code: Program code (e.g., "CS101")
            updates: Dict with fields to update (name, college)
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            program = session.query(Program).filter(Program.code == program_code).first()
            
            if not program:
                return False, "Program not found"

            clean_updates = {}
            for key, value in (updates or {}).items():
                if key in ('name', 'college'):
                    clean_updates[key] = str(value).strip() if value is not None else ""

            existing_college_code = program.college.code if program.college else ""
            candidate = {
                'code': program.code,
                'name': clean_updates.get('name', program.name),
                'college': clean_updates.get('college', existing_college_code),
            }
            ok, msg = validate_program(candidate, require_college=False)
            if not ok:
                return False, msg
            
            # Handle college code -> college_id lookup
            if 'college' in clean_updates:
                college_code = clean_updates['college']
                if college_code:
                    college = session.query(College).filter(College.code == college_code).first()
                    if not college:
                        return False, f"College '{college_code}' not found"
                    program.college_id = college.id
                else:
                    program.college_id = None
            
            # Update allowed fields
            if 'name' in clean_updates:
                program.name = clean_updates['name'].title()
            
            session.commit()
            self.refresh_data()
            return True, "Program updated successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

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
        session = get_session()
        try:
            candidate = {
                'code': str(program_data.get('code', '')).strip(),
                'name': str(program_data.get('name', '')).strip(),
                'college': str(program_data.get('college', '')).strip(),
            }

            ok, msg = validate_program(candidate, require_college=True)
            if not ok:
                return False, msg
            
            # Check if code already exists
            existing = session.query(Program).filter(Program.code == candidate['code']).first()
            if existing:
                return False, "Program code already exists"
            
            # Look up college by code
            college = session.query(College).filter(College.code == candidate['college']).first()
            if not college:
                return False, f"College '{candidate['college']}' not found"
            
            # Create new program
            new_program = Program(
                code=candidate['code'],
                name=candidate['name'].title(),
                college_id=college.id
            )
            
            session.add(new_program)
            session.commit()
            self.refresh_data()
            return True, "Program added successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def update_college(self, college_code: str, updates: dict) -> tuple[bool, str]:
        """Update a college in the database and refresh cache.
        
        Args:
            college_code: College code
            updates: Dict with fields to update (name)
            
        Returns:
            (success: bool, message: str)
        """
        session = get_session()
        try:
            college = session.query(College).filter(College.code == college_code).first()
            
            if not college:
                return False, "College not found"

            clean_name = str((updates or {}).get('name', college.name) or '').strip()
            candidate = {
                'code': college.code,
                'name': clean_name,
            }
            ok, msg = validate_college(candidate)
            if not ok:
                return False, msg
            
            # Update allowed fields
            if 'name' in (updates or {}):
                college.name = clean_name.title()
            
            session.commit()
            self.refresh_data()
            return True, "College updated successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

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
        session = get_session()
        try:
            candidate = {
                'code': str(college_data.get('code', '')).strip(),
                'name': str(college_data.get('name', '')).strip(),
            }

            ok, msg = validate_college(candidate)
            if not ok:
                return False, msg
            
            # Check if code already exists
            existing = session.query(College).filter(College.code == candidate['code']).first()
            if existing:
                return False, "College code already exists"
            
            # Create new college
            new_college = College(
                code=candidate['code'],
                name=candidate['name'].title()
            )
            
            session.add(new_college)
            session.commit()
            self.refresh_data()
            return True, "College added successfully"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

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
