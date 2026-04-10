"""
Student controller for feature-first CRUDL navigation.
"""

from collections.abc import Callable

from .repository import StudentRepository
from .service import StudentService


class StudentController:
    """Thin orchestration layer for student write operations."""

    def __init__(self, session_factory: Callable, refresh_callback: Callable[[], None]):
        self._session_factory = session_factory
        self._refresh_callback = refresh_callback

    def update_student(self, student_id: str, updates: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = StudentService(StudentRepository(session))
            success, message = service.update_student(student_id, updates)
            if success:
                session.commit()
                self._refresh_callback()
            else:
                session.rollback()
            return success, message
        except Exception as exc:
            session.rollback()
            return False, f"Error: {exc}"
        finally:
            session.close()

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = StudentService(StudentRepository(session))
            success, message = service.delete_student(student_id)
            if success:
                session.commit()
                self._refresh_callback()
            else:
                session.rollback()
            return success, message
        except Exception as exc:
            session.rollback()
            return False, f"Error: {exc}"
        finally:
            session.close()

    def add_student(self, student_data: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = StudentService(StudentRepository(session))
            success, message = service.add_student(student_data)
            if success:
                session.commit()
                self._refresh_callback()
            else:
                session.rollback()
            return success, message
        except Exception as exc:
            session.rollback()
            return False, f"Error: {exc}"
        finally:
            session.close()

    def bulk_upsert_students(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        session = self._session_factory()
        try:
            service = StudentService(StudentRepository(session))
            success, summary = service.bulk_upsert_students(records, overwrite_existing=overwrite_existing)
            if success:
                session.commit()
                if summary.get("created") or summary.get("updated"):
                    self._refresh_callback()
            else:
                session.rollback()
            return success, summary
        except Exception as exc:
            session.rollback()
            summary["fatal_error"] = str(exc)
            return False, summary
        finally:
            session.close()
