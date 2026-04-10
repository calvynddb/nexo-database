"""Compatibility exports for controller layer."""

from backend.colleges import CollegeController
from backend.programs import ProgramController
from backend.students import StudentController

__all__ = ["StudentController", "ProgramController", "CollegeController"]
