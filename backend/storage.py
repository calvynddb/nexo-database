"""
Database storage and initialization.

Provides SQLite database setup helpers.
"""

import os
import shutil

from backend.database import init_db as _init_db
from config import data_path, resource_path


def _seed_database_from_bundle_if_missing() -> None:
    """Copy bundled nexo.db into writable location on first run of the exe."""
    target_db = data_path("nexo.db")
    if os.path.exists(target_db):
        return

    source_db = resource_path("nexo.db")
    if not os.path.exists(source_db):
        return

    target_dir = os.path.dirname(target_db)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    shutil.copy2(source_db, target_db)


def init_files():
    """Initialize SQLite database schema."""
    _seed_database_from_bundle_if_missing()
    _init_db()


def create_backups():
    """Create backup of database (placeholder for future implementation)."""
    pass

