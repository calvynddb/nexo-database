"""
Data validation functions for students, programs, and colleges.
"""

import re


_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z' -]*$")
_STUDENT_ID_PATTERN = re.compile(r"^\d{4}-\d{4}$")


def _norm(value) -> str:
    return str(value or "").strip()


def _norm_spaces(value) -> str:
    # Collapse repeated internal spaces for stable validation.
    return " ".join(_norm(value).split())


def validate_student(record, require_program: bool = True):
    """Validate a student record dict. Returns (True, '') or (False, 'error')."""
    if not isinstance(record, dict):
        return False, "Invalid student payload"

    sid = _norm(record.get('id'))
    firstname = _norm_spaces(record.get('firstname'))
    lastname = _norm_spaces(record.get('lastname'))
    gender = _norm(record.get('gender')).title()
    year_raw = _norm(record.get('year'))
    program = _norm(record.get('program'))

    required = {
        'id': sid,
        'firstname': firstname,
        'lastname': lastname,
        'gender': gender,
        'year': year_raw,
    }
    if require_program:
        required['program'] = program

    for field, value in required.items():
        if not value:
            return False, f"Missing field: {field}"

    # id must match format YYYY-NNNN (e.g. 2024-0001)
    if not _STUDENT_ID_PATTERN.match(sid):
        return False, "Student ID must follow the format YYYY-NNNN (e.g. 2024-0001)"

    if not _NAME_PATTERN.match(firstname):
        return False, "First Name must contain only letters, spaces, apostrophes, or hyphens"

    if not _NAME_PATTERN.match(lastname):
        return False, "Last Name must contain only letters, spaces, apostrophes, or hyphens"

    if gender not in {"Male", "Female", "Other"}:
        return False, "Gender must be one of: Male, Female, or Other"

    try:
        year = int(year_raw)
    except Exception:
        return False, "Year must be a number between 1 and 5"

    if year < 1 or year > 5:
        return False, "Year must be between 1 and 5"

    if require_program and not program:
        return False, "Missing field: program"

    return True, ""


def validate_program(record, require_college: bool = True):
    """Validate a program record dict. Returns (True, '') or (False, 'error')."""
    if not isinstance(record, dict):
        return False, "Invalid program payload"

    code = _norm(record.get('code'))
    name = _norm_spaces(record.get('name'))
    college = _norm(record.get('college'))

    if not code:
        return False, "Missing field: code"
    if len(code) < 2:
        return False, "Program Code must be at least 2 characters"
    if not code.isalnum():
        return False, "Program Code must contain only letters and numbers"

    if not name:
        return False, "Missing field: name"
    if not _NAME_PATTERN.match(name):
        return False, "Program Name must contain only letters, spaces, apostrophes, or hyphens"

    if require_college and not college:
        return False, "Missing field: college"

    return True, ""


def validate_college(record):
    """Validate a college record dict. Returns (True, '') or (False, 'error')."""
    if not isinstance(record, dict):
        return False, "Invalid college payload"

    code = _norm(record.get('code'))
    name = _norm_spaces(record.get('name'))

    if not code:
        return False, "Missing field: code"
    if len(code) < 2:
        return False, "College Code must be at least 2 characters"
    if not code.isalpha():
        return False, "College Code must contain only letters"

    if not name:
        return False, "Missing field: name"
    if not _NAME_PATTERN.match(name):
        return False, "College Name must contain only letters, spaces, apostrophes, or hyphens"

    return True, ""


def validate_password(password: str):
    """Validate admin password quality. Returns (True, '') or (False, 'error')."""
    pwd = str(password or "")

    if not pwd:
        return False, "Password is required"

    if pwd != pwd.strip():
        return False, "Password cannot start or end with spaces"

    if len(pwd) < 6:
        return False, "Password must be at least 6 characters"

    if not any(ch.isalpha() for ch in pwd):
        return False, "Password must include at least one letter"

    if not any(ch.isdigit() for ch in pwd):
        return False, "Password must include at least one number"

    return True, ""
