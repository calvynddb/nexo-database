"""
Database configuration and session management for SQLite-backed SIS.

Provides:
- SQLite engine connected to nexo.db
- Session factory for safe concurrent access
- Initialization functions to set up schema
"""

import os
from sqlalchemy import create_engine
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

# Session factory: creates new session instances for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Get a new database session. Should be used in a with statement."""
    return SessionLocal()


def init_db():
    """Initialize the database schema. Creates all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


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
