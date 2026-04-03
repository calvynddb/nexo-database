"""
SQLAlchemy models for the Student Information System (SIS).

Defines College, Program, Student, and User entities with relationships:
- College has many Programs
- Program has many Students
- College/Program/Student share no direct relationship with User (auth-only)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class College(Base):
    """College entity: code is unique, name is required."""
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Relationship: one college has many programs
    programs = relationship("Program", back_populates="college", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<College(id={self.id}, code={self.code}, name={self.name})>"


class Program(Base):
    """Program entity: code is unique, name is required, college_id is FK."""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)

    # Relationships
    college = relationship("College", back_populates="programs")
    students = relationship("Student", back_populates="program", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Program(id={self.id}, code={self.code}, name={self.name}, college_id={self.college_id})>"


class Student(Base):
    """Student entity: id is unique (format 202x-xxxx), assigned to a program."""
    __tablename__ = "students"

    id = Column(String(10), primary_key=True)  # e.g. "2023-0001"
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    year = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    gender = Column(String(20), nullable=False)  # "Male", "Female", etc.

    # Relationship: many students belong to one program
    program = relationship("Program", back_populates="students")

    def __repr__(self):
        return f"<Student(id={self.id}, firstname={self.firstname}, lastname={self.lastname}, program_id={self.program_id})>"


class User(Base):
    """User entity: username is unique, stores password salt and hash."""
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    salt = Column(String(32), nullable=False)  # 32-char hex (16 random bytes)
    password = Column(String(64), nullable=False)  # 64-char hex (SHA-256 digest)

    def __repr__(self):
        return f"<User(username={self.username})>"
