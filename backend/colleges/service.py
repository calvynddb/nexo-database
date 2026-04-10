"""
College service for feature-first CRUDL navigation.
"""

from backend.models import College

from .repository import CollegeRepository
from .validators import validate_college


class CollegeService:
    """College business rules and validation orchestration."""

    def __init__(self, repository: CollegeRepository):
        self.repository = repository

    @staticmethod
    def _normalize_candidate(record: dict) -> dict:
        record = record or {}
        return {
            "code": str(record.get("code", "")).strip(),
            "name": str(record.get("name", "")).strip(),
        }

    def update_college(self, college_code: str, updates: dict) -> tuple[bool, str]:
        college = self.repository.get_by_code(college_code)
        if not college:
            return False, "College not found"

        clean_name = str((updates or {}).get("name", college.name) or "").strip()
        candidate = {
            "code": college.code,
            "name": clean_name,
        }

        ok, msg = validate_college(candidate)
        if not ok:
            return False, msg

        if "name" in (updates or {}):
            college.name = clean_name.title()

        return True, "College updated successfully"

    def delete_college(self, college_code: str) -> tuple[bool, str]:
        college = self.repository.get_by_code(college_code)
        if not college:
            return False, "College not found"

        affected_programs = self.repository.programs_by_college_id(college.id)
        for program in affected_programs:
            program.college_id = None

        self.repository.delete(college)
        return True, (
            "College deleted successfully. "
            f"Cleared college assignment for {len(affected_programs)} program(s)."
        )

    def add_college(self, college_data: dict) -> tuple[bool, str]:
        candidate = self._normalize_candidate(college_data)

        ok, msg = validate_college(candidate)
        if not ok:
            return False, msg

        existing = self.repository.get_by_code(candidate["code"])
        if existing:
            return False, "College code already exists"

        new_college = College(
            code=candidate["code"],
            name=candidate["name"].title(),
        )
        self.repository.add(new_college)
        return True, "College added successfully"

    def bulk_upsert_colleges(self, records: list[dict], overwrite_existing: bool = False) -> tuple[bool, dict]:
        summary = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        existing_colleges = self.repository.colleges_by_code()

        for row_no, record in enumerate(records or [], start=1):
            candidate = self._normalize_candidate(record)

            ok, msg = validate_college(candidate)
            if not ok:
                summary["errors"].append(f"Row {row_no}: {msg}")
                continue

            existing = existing_colleges.get(candidate["code"])
            if existing:
                if not overwrite_existing:
                    summary["skipped"] += 1
                    continue

                existing.name = candidate["name"].title()
                summary["updated"] += 1
                continue

            new_college = College(
                code=candidate["code"],
                name=candidate["name"].title(),
            )
            self.repository.add(new_college)
            existing_colleges[candidate["code"]] = new_college
            summary["created"] += 1

        summary["failed"] = len(summary["errors"])
        return True, summary
