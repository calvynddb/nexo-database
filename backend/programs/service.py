"""
Program service for feature-first CRUDL navigation.
"""

from backend.models import Program

from .repository import ProgramRepository
from .validators import validate_program


class ProgramService:
    """Program business rules and validation orchestration."""

    def __init__(self, repository: ProgramRepository):
        self.repository = repository

    @staticmethod
    def _normalize_candidate(record: dict) -> dict:
        record = record or {}
        return {
            "code": str(record.get("code", "")).strip(),
            "name": str(record.get("name", "")).strip(),
            "college": str(record.get("college", "")).strip(),
        }

    def update_program(self, program_code: str, updates: dict) -> tuple[bool, str]:
        program = self.repository.get_by_code(program_code)
        if not program:
            return False, "Program not found"

        clean_updates = {}
        for key, value in (updates or {}).items():
            if key in ("name", "college"):
                clean_updates[key] = str(value).strip() if value is not None else ""

        existing_college_code = program.college.code if program.college else ""
        candidate = {
            "code": program.code,
            "name": clean_updates.get("name", program.name),
            "college": clean_updates.get("college", existing_college_code),
        }

        ok, msg = validate_program(candidate, require_college=False)
        if not ok:
            return False, msg

        if "college" in clean_updates:
            college_code = clean_updates["college"]
            if college_code:
                college = self.repository.get_college_by_code(college_code)
                if not college:
                    return False, f"College '{college_code}' not found"
                program.college_id = college.id
            else:
                program.college_id = None

        if "name" in clean_updates:
            program.name = clean_updates["name"].title()

        return True, "Program updated successfully"

    def delete_program(self, program_code: str) -> tuple[bool, str]:
        program = self.repository.get_by_code(program_code)
        if not program:
            return False, "Program not found"

        affected_students = self.repository.students_by_program_id(program.id)
        for student in affected_students:
            student.program_id = None

        self.repository.delete(program)
        return True, (
            "Program deleted successfully. "
            f"Cleared program assignment for {len(affected_students)} student(s)."
        )

    def add_program(self, program_data: dict) -> tuple[bool, str]:
        candidate = self._normalize_candidate(program_data)

        ok, msg = validate_program(candidate, require_college=True)
        if not ok:
            return False, msg

        existing = self.repository.get_by_code(candidate["code"])
        if existing:
            return False, "Program code already exists"

        college = self.repository.get_college_by_code(candidate["college"])
        if not college:
            return False, f"College '{candidate['college']}' not found"

        new_program = Program(
            code=candidate["code"],
            name=candidate["name"].title(),
            college_id=college.id,
        )
        self.repository.add(new_program)
        return True, "Program added successfully"

    def bulk_upsert_programs(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        colleges_by_code = self.repository.colleges_by_code()
        existing_programs = self.repository.programs_by_code()

        for row_no, record in enumerate(records or [], start=1):
            candidate = self._normalize_candidate(record)

            ok, msg = validate_program(candidate, require_college=True)
            if not ok:
                summary["errors"].append(f"Row {row_no}: {msg}")
                continue

            college_id = colleges_by_code.get(candidate["college"])
            if not college_id:
                summary["errors"].append(f"Row {row_no}: College '{candidate['college']}' not found")
                continue

            existing = existing_programs.get(candidate["code"])
            if existing:
                if not overwrite_existing:
                    summary["skipped"] += 1
                    continue

                existing.name = candidate["name"].title()
                existing.college_id = college_id
                summary["updated"] += 1
                continue

            new_program = Program(
                code=candidate["code"],
                name=candidate["name"].title(),
                college_id=college_id,
            )
            self.repository.add(new_program)
            existing_programs[candidate["code"]] = new_program
            summary["created"] += 1

        summary["failed"] = len(summary["errors"])
        return True, summary
