"""
Program controller for feature-first CRUDL navigation.
"""

from collections.abc import Callable

from .repository import ProgramRepository
from .service import ProgramService


class ProgramController:
    """Thin orchestration layer for program write operations."""

    def __init__(self, session_factory: Callable, refresh_callback: Callable[[], None]):
        self._session_factory = session_factory
        self._refresh_callback = refresh_callback

    def update_program(self, program_code: str, updates: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = ProgramService(ProgramRepository(session))
            success, message = service.update_program(program_code, updates)
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

    def delete_program(self, program_code: str) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = ProgramService(ProgramRepository(session))
            success, message = service.delete_program(program_code)
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

    def add_program(self, program_data: dict) -> tuple[bool, str]:
        session = self._session_factory()
        try:
            service = ProgramService(ProgramRepository(session))
            success, message = service.add_program(program_data)
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

    def bulk_upsert_programs(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        session = self._session_factory()
        try:
            service = ProgramService(ProgramRepository(session))
            success, summary = service.bulk_upsert_programs(records, overwrite_existing=overwrite_existing)
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
