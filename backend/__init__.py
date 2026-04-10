"""
Backend module: Storage, CRUD, Search, and Sort operations.
"""

from .storage import init_files, create_backups
from .validators import validate_student, validate_program, validate_college, validate_password
from .auth import hash_password, verify_password
from .database import get_session, init_db
from .students import StudentController, StudentRepository, StudentService
from .programs import ProgramController, ProgramRepository, ProgramService
from .colleges import CollegeController, CollegeRepository, CollegeService

__all__ = [
    "init_files", "create_backups",
    "validate_student", "validate_program", "validate_college", "validate_password",
    "hash_password", "verify_password",
    "get_session", "init_db",
    "StudentController", "StudentService", "StudentRepository",
    "ProgramController", "ProgramService", "ProgramRepository",
    "CollegeController", "CollegeService", "CollegeRepository",
]
