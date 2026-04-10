"""
Program repository for feature-first CRUDL navigation.
"""

from sqlalchemy.orm import Session

from backend.models import College, Program, Student


class ProgramRepository:
    """Data-access helper for Program and related entities."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_code(self, program_code: str):
        return self.session.query(Program).filter(Program.code == program_code).first()

    def get_all(self):
        return self.session.query(Program).all()

    def programs_by_code(self) -> dict[str, Program]:
        return {program.code: program for program in self.get_all()}

    def get_college_by_code(self, college_code: str):
        return self.session.query(College).filter(College.code == college_code).first()

    def colleges_by_code(self) -> dict[str, int]:
        return {college.code: college.id for college in self.session.query(College).all()}

    def students_by_program_id(self, program_id: int):
        return self.session.query(Student).filter(Student.program_id == program_id).all()

    def add(self, program: Program) -> None:
        self.session.add(program)

    def delete(self, program: Program) -> None:
        self.session.delete(program)
