"""
Student service for feature-first CRUDL navigation.
"""

from backend.models import Student

from .repository import StudentRepository
from .validators import validate_student


class StudentService:
    """Student business rules and validation orchestration."""

    def __init__(self, repository: StudentRepository):
        self.repository = repository

    @staticmethod
    def _normalize_candidate(record: dict) -> dict:
        record = record or {}
        return {
            "id": str(record.get("id", "")).strip(),
            "firstname": str(record.get("firstname", "")).strip(),
            "lastname": str(record.get("lastname", "")).strip(),
            "gender": str(record.get("gender", "")).strip(),
            "year": str(record.get("year", "")).strip(),
            "program": str(record.get("program", "")).strip(),
        }

    def update_student(self, student_id: str, updates: dict) -> tuple[bool, str]:
        student = self.repository.get_by_id(student_id)
        if not student:
            return False, "Student not found"

        clean_updates = {}
        for key, value in (updates or {}).items():
            if key in ("firstname", "lastname", "gender", "year", "program"):
                clean_updates[key] = str(value).strip() if value is not None else ""

        existing_program_code = student.program.code if student.program else ""
        candidate = {
            "id": student.id,
            "firstname": clean_updates.get("firstname", student.firstname),
            "lastname": clean_updates.get("lastname", student.lastname),
            "gender": clean_updates.get("gender", student.gender),
            "year": clean_updates.get("year", str(student.year)),
            "program": clean_updates.get("program", existing_program_code),
        }

        ok, msg = validate_student(candidate, require_program=False)
        if not ok:
            return False, msg

        if "program" in clean_updates:
            program_code = clean_updates["program"]
            if program_code:
                program = self.repository.get_program_by_code(program_code)
                if not program:
                    return False, f"Program '{program_code}' not found"
                student.program_id = program.id
            else:
                student.program_id = None

        if "firstname" in clean_updates:
            student.firstname = clean_updates["firstname"].title()
        if "lastname" in clean_updates:
            student.lastname = clean_updates["lastname"].title()
        if "gender" in clean_updates:
            student.gender = clean_updates["gender"].title()
        if "year" in clean_updates:
            student.year = int(clean_updates["year"])

        return True, "Student updated successfully"

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        student = self.repository.get_by_id(student_id)
        if not student:
            return False, "Student not found"

        self.repository.delete(student)
        return True, "Student deleted successfully"

    def add_student(self, student_data: dict) -> tuple[bool, str]:
        candidate = self._normalize_candidate(student_data)

        ok, msg = validate_student(candidate, require_program=True)
        if not ok:
            return False, msg

        existing = self.repository.get_by_id(candidate["id"])
        if existing:
            return False, "Student ID already exists"

        program = self.repository.get_program_by_code(candidate["program"])
        if not program:
            return False, f"Program '{candidate['program']}' not found"

        new_student = Student(
            id=candidate["id"],
            firstname=candidate["firstname"].title(),
            lastname=candidate["lastname"].title(),
            program_id=program.id,
            year=int(candidate["year"]),
            gender=candidate["gender"].title(),
        )
        self.repository.add(new_student)
        return True, "Student added successfully"

    def bulk_upsert_students(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        programs_by_code = self.repository.programs_by_code()
        existing_students = self.repository.students_by_id()

        for row_no, record in enumerate(records or [], start=1):
            candidate = self._normalize_candidate(record)

            ok, msg = validate_student(candidate, require_program=True)
            if not ok:
                summary["errors"].append(f"Row {row_no}: {msg}")
                continue

            program_id = programs_by_code.get(candidate["program"])
            if not program_id:
                summary["errors"].append(f"Row {row_no}: Program '{candidate['program']}' not found")
                continue

            existing = existing_students.get(candidate["id"])
            if existing:
                if not overwrite_existing:
                    summary["skipped"] += 1
                    continue

                existing.firstname = candidate["firstname"].title()
                existing.lastname = candidate["lastname"].title()
                existing.gender = candidate["gender"].title()
                existing.year = int(candidate["year"])
                existing.program_id = program_id
                summary["updated"] += 1
                continue

            new_student = Student(
                id=candidate["id"],
                firstname=candidate["firstname"].title(),
                lastname=candidate["lastname"].title(),
                gender=candidate["gender"].title(),
                year=int(candidate["year"]),
                program_id=program_id,
            )
            self.repository.add(new_student)
            existing_students[candidate["id"]] = new_student
            summary["created"] += 1

        summary["failed"] = len(summary["errors"])
        return True, summary
