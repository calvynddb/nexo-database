"""
Shared list/search/sort pipeline helpers for table views.
"""


class ListPipelineService:
    """Entity list row builders plus shared filter/sort helpers."""

    @staticmethod
    def student_rows(students: list[dict], programs: list[dict]) -> list[tuple]:
        program_to_college = {
            str(program.get("code", "")): str(program.get("college", "N/A"))
            for program in programs or []
        }

        rows = []
        for student in students or []:
            program_code = str(student.get("program", ""))
            rows.append(
                (
                    student.get("id", ""),
                    student.get("firstname", ""),
                    student.get("lastname", ""),
                    student.get("gender", ""),
                    student.get("year", ""),
                    program_code,
                    program_to_college.get(program_code, "N/A"),
                )
            )
        return rows

    @staticmethod
    def program_rows(programs: list[dict], students: list[dict]) -> list[tuple]:
        student_counts = {}
        for student in students or []:
            code = str(student.get("program", ""))
            if code:
                student_counts[code] = student_counts.get(code, 0) + 1

        rows = []
        for idx, program in enumerate(programs or [], 1):
            code = str(program.get("code", ""))
            rows.append(
                (
                    idx,
                    code,
                    program.get("name", ""),
                    program.get("college", ""),
                    student_counts.get(code, 0),
                )
            )
        return rows

    @staticmethod
    def college_rows(colleges: list[dict]) -> list[tuple]:
        return [
            (idx, college.get("code", ""), college.get("name", ""))
            for idx, college in enumerate(colleges or [], 1)
        ]

    @staticmethod
    def filter_students(rows: list[tuple], query: str = "", advanced_filters=None) -> list[tuple]:
        query = str(query or "").strip().lower()
        advanced_filters = advanced_filters or {}

        id_filter = str(advanced_filters.get("id", "")).strip().lower()
        first_filter = str(advanced_filters.get("firstname", "")).strip().lower()
        last_filter = str(advanced_filters.get("lastname", "")).strip().lower()
        gender_filter = str(advanced_filters.get("gender", "")).strip().lower()
        year_filter = str(advanced_filters.get("year", "")).strip().lower()
        program_filter = str(advanced_filters.get("program", "")).strip().lower()
        college_filter = str(advanced_filters.get("college", "")).strip().lower()

        filtered = []
        for row in rows or []:
            sid, firstname, lastname, gender, year, program, college = row

            sid_l = str(sid).lower()
            firstname_l = str(firstname).lower()
            lastname_l = str(lastname).lower()
            gender_l = str(gender).lower()
            year_l = str(year).lower()
            program_l = str(program).lower()
            college_l = str(college).lower()

            if query and not (
                query in firstname_l
                or query in lastname_l
                or query in sid_l
                or query in gender_l
                or query in program_l
                or query in year_l
                or query in college_l
            ):
                continue

            if id_filter and id_filter not in sid_l:
                continue
            if first_filter and first_filter not in firstname_l:
                continue
            if last_filter and last_filter not in lastname_l:
                continue
            if gender_filter and gender_filter != "any" and gender_filter != gender_l:
                continue
            if year_filter and year_filter != "any" and year_filter != year_l:
                continue
            if program_filter and program_filter != "any" and program_filter != program_l:
                continue
            if college_filter and college_filter != "any" and college_filter != college_l:
                continue

            filtered.append(row)

        return filtered

    @staticmethod
    def filter_programs(rows: list[tuple], query: str = "", advanced_filters=None) -> list[tuple]:
        query = str(query or "").strip().lower()
        advanced_filters = advanced_filters or {}

        code_filter = str(advanced_filters.get("code", "")).strip().lower()
        name_filter = str(advanced_filters.get("name", "")).strip().lower()
        college_filter = str(advanced_filters.get("college", "")).strip().lower()

        filtered = []
        for row in rows or []:
            _idx, code, name, college, _student_count = row

            code_l = str(code).lower()
            name_l = str(name).lower()
            college_l = str(college).lower()

            if query and not (query in name_l or query in code_l or query in college_l):
                continue

            if code_filter and code_filter not in code_l:
                continue
            if name_filter and name_filter not in name_l:
                continue
            if college_filter and college_filter != "any" and college_filter != college_l:
                continue

            filtered.append(row)

        return filtered

    @staticmethod
    def filter_colleges(rows: list[tuple], query: str = "", advanced_filters=None) -> list[tuple]:
        query = str(query or "").strip().lower()
        advanced_filters = advanced_filters or {}

        code_filter = str(advanced_filters.get("code", "")).strip().lower()
        name_filter = str(advanced_filters.get("name", "")).strip().lower()

        filtered = []
        for row in rows or []:
            _idx, code, name = row
            code_l = str(code).lower()
            name_l = str(name).lower()

            if query and not (query in name_l or query in code_l):
                continue
            if code_filter and code_filter not in code_l:
                continue
            if name_filter and name_filter not in name_l:
                continue

            filtered.append(row)

        return filtered

    @staticmethod
    def sort_rows(rows: list[tuple], columns: tuple | list, sort_column: str, reverse: bool = False) -> list[tuple]:
        if not sort_column:
            return list(rows or [])

        try:
            col_index = list(columns).index(sort_column)
        except Exception:
            col_index = 0

        return sorted(
            rows or [],
            key=lambda row: ListPipelineService._try_numeric(str(row[col_index])),
            reverse=bool(reverse),
        )

    @staticmethod
    def _try_numeric(value: str):
        try:
            return float(value)
        except ValueError:
            return value
