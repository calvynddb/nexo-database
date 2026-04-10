"""
Filter state/schema composition helpers for dashboard filter UI.
"""


class FilterStateService:
    """Shared filter defaults, schemas, and state normalization logic."""

    @staticmethod
    def resolve_view_key(view_class, students_view, programs_view, colleges_view) -> str:
        if view_class == students_view:
            return "students"
        if view_class == programs_view:
            return "programs"
        if view_class == colleges_view:
            return "colleges"
        return "none"

    @staticmethod
    def view_label(view_key: str) -> str:
        if view_key == "students":
            return "Students"
        if view_key == "programs":
            return "Programs"
        if view_key == "colleges":
            return "Colleges"
        return "Filters"

    @staticmethod
    def default_state(view_key: str) -> dict:
        if view_key == "students":
            return {
                "id": "",
                "firstname": "",
                "lastname": "",
                "gender": "Any",
                "year": "Any",
                "program": "Any",
                "college": "Any",
            }

        if view_key == "programs":
            return {
                "code": "",
                "name": "",
                "college": "Any",
            }

        return {
            "code": "",
            "name": "",
        }

    @staticmethod
    def data_signature(view_key: str, students: list, programs: list, colleges: list):
        if view_key == "students":
            return (
                "students",
                id(students), len(students),
                id(programs), len(programs),
                id(colleges), len(colleges),
            )

        if view_key == "programs":
            return (
                "programs",
                id(programs), len(programs),
                id(colleges), len(colleges),
            )

        if view_key == "colleges":
            return (
                "colleges",
                id(colleges), len(colleges),
            )

        return ("none",)

    @staticmethod
    def schema(view_key: str, students: list[dict], programs: list[dict], colleges: list[dict]) -> list[dict]:
        if view_key == "students":
            years = sorted(
                {str(student.get("year", "")).strip() for student in students if str(student.get("year", "")).strip()},
                key=lambda value: (0, int(value)) if value.isdigit() else (1, value),
            )
            program_codes = sorted(
                {str(program.get("code", "")).strip() for program in programs if str(program.get("code", "")).strip()}
            )
            college_codes = sorted(
                {str(college.get("code", "")).strip() for college in colleges if str(college.get("code", "")).strip()}
            )
            return [
                {"key": "id", "label": "ID", "type": "entry", "placeholder": "Contains ID"},
                {"key": "firstname", "label": "First Name", "type": "entry", "placeholder": "Contains first name"},
                {"key": "lastname", "label": "Last Name", "type": "entry", "placeholder": "Contains last name"},
                {"key": "gender", "label": "Gender", "type": "combo", "values": ["Any", "Male", "Female", "Other"]},
                {"key": "year", "label": "Year", "type": "combo", "values": ["Any"] + years},
                {"key": "program", "label": "Program", "type": "combo", "values": ["Any"] + program_codes},
                {"key": "college", "label": "College", "type": "combo", "values": ["Any"] + college_codes},
            ]

        if view_key == "programs":
            college_codes = sorted(
                {str(college.get("code", "")).strip() for college in colleges if str(college.get("code", "")).strip()}
            )
            return [
                {"key": "code", "label": "Code", "type": "entry", "placeholder": "Contains code"},
                {"key": "name", "label": "Program Name", "type": "entry", "placeholder": "Contains program"},
                {"key": "college", "label": "College", "type": "combo", "values": ["Any"] + college_codes},
            ]

        return [
            {"key": "code", "label": "Code", "type": "entry", "placeholder": "Contains code"},
            {"key": "name", "label": "College Name", "type": "entry", "placeholder": "Contains college"},
        ]

    @staticmethod
    def ensure_state(state: dict | None, defaults: dict) -> dict:
        merged = dict(state or {})

        for key, default in defaults.items():
            merged.setdefault(key, default)

        for key in list(merged.keys()):
            if key not in defaults:
                merged.pop(key)

        return merged

    @staticmethod
    def active_filter_count(state: dict) -> int:
        count = 0
        for value in (state or {}).values():
            text = str(value).strip()
            if text and text.lower() != "any":
                count += 1
        return count
