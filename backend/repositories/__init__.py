"""Compatibility exports for repository layer."""

from backend.colleges import CollegeRepository
from backend.programs import ProgramRepository
from backend.students import StudentRepository

__all__ = ["StudentRepository", "ProgramRepository", "CollegeRepository"]
