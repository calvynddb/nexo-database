"""
Database configuration and session management for SQLite-backed SIS.

Provides:
- SQLite engine connected to nexo.db
- Session factory for safe concurrent access
- Initialization functions to set up schema
"""

import os
import shutil
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.models import Base
from config import data_path


# Configure SQLite engine
# Uses SQLite database file in the same directory as the app
DB_PATH = data_path("nexo.db")
DATABASE_URL = f"sqlite:///{DB_PATH}".replace("\\", "/")

# Create engine with check_same_thread=False for multi-threaded operations
# SQLite is single-threaded by default, but we'll handle concurrency manually
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL logging during development
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """Enable SQLite foreign key enforcement for every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory: creates new session instances for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _table_exists(connection, table_name: str) -> bool:
    row = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).first()
    return row is not None


def _column_notnull_flag(connection, table_name: str, column_name: str) -> int:
    rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").mappings().all()
    for row in rows:
        if row["name"] == column_name:
            return int(row["notnull"])
    return 0


def _fk_ondelete(connection, table_name: str, from_column: str, ref_table: str) -> str:
    rows = connection.exec_driver_sql(f"PRAGMA foreign_key_list({table_name})").mappings().all()
    for row in rows:
        if row["from"] == from_column and row["table"] == ref_table:
            return str(row["on_delete"] or "").upper()
    return ""


def _needs_set_null_migration(connection) -> bool:
    if not _table_exists(connection, "programs") or not _table_exists(connection, "students"):
        return False

    program_college_notnull = _column_notnull_flag(connection, "programs", "college_id")
    student_program_notnull = _column_notnull_flag(connection, "students", "program_id")
    program_on_delete = _fk_ondelete(connection, "programs", "college_id", "colleges")
    student_on_delete = _fk_ondelete(connection, "students", "program_id", "programs")

    return (
        program_college_notnull == 1
        or student_program_notnull == 1
        or program_on_delete != "SET NULL"
        or student_on_delete != "SET NULL"
    )


def _create_schema_backup() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = data_path(f"nexo_pre_set_null_migration_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def _migrate_to_set_null_schema() -> bool:
    """Migrate existing SQLite schema so parent deletes set child FKs to NULL."""
    with engine.connect() as connection:
        if connection.dialect.name != "sqlite":
            return False
        if not _needs_set_null_migration(connection):
            return False

    if os.path.exists(DB_PATH):
        _create_schema_backup()

    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            connection.exec_driver_sql("DROP TABLE IF EXISTS programs_new")
            connection.exec_driver_sql("DROP TABLE IF EXISTS students_new")

            connection.exec_driver_sql(
                """
                CREATE TABLE programs_new (
                    id INTEGER PRIMARY KEY,
                    code VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    college_id INTEGER,
                    FOREIGN KEY(college_id) REFERENCES colleges(id) ON DELETE SET NULL
                )
                """
            )
            connection.exec_driver_sql(
                """
                INSERT INTO programs_new (id, code, name, college_id)
                SELECT id, code, name, college_id
                FROM programs
                """
            )

            connection.exec_driver_sql(
                """
                CREATE TABLE students_new (
                    id VARCHAR(10) PRIMARY KEY,
                    firstname VARCHAR(100) NOT NULL,
                    lastname VARCHAR(100) NOT NULL,
                    program_id INTEGER,
                    year INTEGER NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    FOREIGN KEY(program_id) REFERENCES programs(id) ON DELETE SET NULL
                )
                """
            )
            connection.exec_driver_sql(
                """
                INSERT INTO students_new (id, firstname, lastname, program_id, year, gender)
                SELECT id, firstname, lastname, program_id, year, gender
                FROM students
                """
            )

            connection.exec_driver_sql("DROP TABLE students")
            connection.exec_driver_sql("DROP TABLE programs")
            connection.exec_driver_sql("ALTER TABLE programs_new RENAME TO programs")
            connection.exec_driver_sql("ALTER TABLE students_new RENAME TO students")
            connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_programs_code ON programs(code)")
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")

    return True


def _ensure_fk_indexes() -> None:
    """Ensure common foreign-key lookup indexes exist for SQLite performance."""
    with engine.begin() as connection:
        if not _table_exists(connection, "programs") or not _table_exists(connection, "students"):
            return

        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_programs_college_id ON programs(college_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_students_program_id ON students(program_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_colleges_code ON colleges(code)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_programs_code ON programs(code)")


def _ensure_student_integrity_triggers() -> None:
    """Enforce student data domain rules for existing databases via triggers."""
    with engine.begin() as connection:
        if not _table_exists(connection, "students"):
            return

        connection.exec_driver_sql(
            """
            CREATE TRIGGER IF NOT EXISTS trg_students_validate_insert
            BEFORE INSERT ON students
            BEGIN
                SELECT CASE
                    WHEN NEW.id NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'
                        THEN RAISE(ABORT, 'students.id must follow YYYY-NNNN')
                    WHEN NEW.year < 1 OR NEW.year > 5
                        THEN RAISE(ABORT, 'students.year must be between 1 and 5')
                    WHEN NEW.gender NOT IN ('Male', 'Female', 'Other')
                        THEN RAISE(ABORT, 'students.gender must be Male, Female, or Other')
                END;
            END
            """
        )

        connection.exec_driver_sql(
            """
            CREATE TRIGGER IF NOT EXISTS trg_students_validate_update
            BEFORE UPDATE ON students
            BEGIN
                SELECT CASE
                    WHEN NEW.id NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'
                        THEN RAISE(ABORT, 'students.id must follow YYYY-NNNN')
                    WHEN NEW.year < 1 OR NEW.year > 5
                        THEN RAISE(ABORT, 'students.year must be between 1 and 5')
                    WHEN NEW.gender NOT IN ('Male', 'Female', 'Other')
                        THEN RAISE(ABORT, 'students.gender must be Male, Female, or Other')
                END;
            END
            """
        )


def get_session() -> Session:
    """Get a new database session. Should be used in a with statement."""
    return SessionLocal()


def init_db():
    """Initialize the database schema. Creates all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    _migrate_to_set_null_schema()
    Base.metadata.create_all(bind=engine)
    _ensure_fk_indexes()
    _ensure_student_integrity_triggers()


def drop_all():
    """Drop all tables in the database. WARNING: Destructive. Use only in testing."""
    Base.metadata.drop_all(bind=engine)


def db_exists() -> bool:
    """Check if the database file exists."""
    return os.path.exists(DB_PATH)


def has_data() -> bool:
    """Check if database already has data (colleges). Better than checking file existence."""
    try:
        session = SessionLocal()
        from backend.models import College
        count = session.query(College).count()
        session.close()
        return count > 0
    except Exception:
        return False
