"""
Database storage and initialization.

Provides SQLite database setup helpers.
"""

from backend.database import init_db as _init_db


def init_files():
    """Initialize SQLite database schema."""
    _init_db()


def create_backups():
    """Create backup of database (placeholder for future implementation)."""
    pass

