"""
College repository for feature-first CRUDL navigation.
"""

from sqlalchemy.orm import Session

from backend.models import College, Program


class CollegeRepository:
    """Data-access helper for College and related Program lookups."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_code(self, college_code: str):
        return self.session.query(College).filter(College.code == college_code).first()

    def get_all(self):
        return self.session.query(College).all()

    def colleges_by_code(self) -> dict[str, College]:
        return {college.code: college for college in self.get_all()}

    def programs_by_college_id(self, college_id: int):
        return self.session.query(Program).filter(Program.college_id == college_id).all()

    def add(self, college: College) -> None:
        self.session.add(college)

    def delete(self, college: College) -> None:
        self.session.delete(college)
