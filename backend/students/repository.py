"""
Student repository for feature-first CRUDL navigation.
"""

from sqlalchemy.orm import Session

from backend.models import Program, Student


class StudentRepository:
    """Data-access helper for Student and related Program lookups."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, student_id: str):
        return self.session.query(Student).filter(Student.id == student_id).first()

    def get_all(self):
        return self.session.query(Student).all()

    def students_by_id(self) -> dict[str, Student]:
        return {student.id: student for student in self.get_all()}

    def get_program_by_code(self, program_code: str):
        return self.session.query(Program).filter(Program.code == program_code).first()

    def programs_by_code(self) -> dict[str, int]:
        return {program.code: program.id for program in self.session.query(Program).all()}

    def add(self, student: Student) -> None:
        self.session.add(student)

    def delete(self, student: Student) -> None:
        self.session.delete(student)
