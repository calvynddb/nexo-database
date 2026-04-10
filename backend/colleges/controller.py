"""
College controller for feature-first CRUDL navigation.
"""

from collections.abc import Callable

from .repository import CollegeRepository
from .service import CollegeService


class CollegeController:
    """Thin orchestration layer for college write operations."""

    def __init__(self, session_factory: Callable, refresh_callback: Callable[[], None]):
        self._session_factory = session_factory
        self._refresh_callback = refresh_callback

    def update_college(self, college_code: str, updates: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = CollegeService(CollegeRepository(session))
            success, message = service.update_college(college_code, updates)
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

    def delete_college(self, college_code: str) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = CollegeService(CollegeRepository(session))
            success, message = service.delete_college(college_code)
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

    def add_college(self, college_data: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = CollegeService(CollegeRepository(session))
            success, message = service.add_college(college_data)
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

    def bulk_upsert_colleges(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        session = self._session_factory()
        try:
            service = CollegeService(CollegeRepository(session))
            success, summary = service.bulk_upsert_colleges(records, overwrite_existing=overwrite_existing)
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
