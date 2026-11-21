"""Recovery primitives for the experimental SQLite-backed Messenger."""

from pathlib import Path
import sqlite3


def verify_sqlite_recovery(path: str) -> tuple[bool, str]:
    """Return a safe operational result without exposing database contents."""
    db_path = Path(path)
    if not db_path.exists():
        return False, "STORAGE_UNAVAILABLE"
    if not db_path.is_file():
        return False, "STORAGE_UNAVAILABLE"
    try:
        with sqlite3.connect(str(db_path)) as connection:
            row = connection.execute("PRAGMA integrity_check").fetchone()
    except (OSError, sqlite3.Error):
        return False, "STORAGE_INTEGRITY"
    if not row or row[0] != "ok":
        return False, "STORAGE_INTEGRITY"
    return True, "STORAGE_RECOVERY_OK"
