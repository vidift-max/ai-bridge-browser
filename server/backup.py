"""Operator-triggered, non-overwriting SQLite snapshot primitive."""
from pathlib import Path
import sqlite3

from server.recovery import verify_sqlite_recovery


def create_sqlite_backup(source_path: str, destination_path: str) -> tuple[bool, str]:
    source = Path(source_path)
    destination = Path(destination_path)
    if not source.is_file():
        return False, "STORAGE_UNAVAILABLE"
    try:
        if source.resolve() == destination.resolve():
            return False, "BACKUP_DESTINATION_CONFLICT"
        if destination.exists():
            return False, "BACKUP_DESTINATION_EXISTS"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(source)) as source_db:
            with sqlite3.connect(str(destination)) as backup_db:
                source_db.backup(backup_db)
        ok, code = verify_sqlite_recovery(str(destination))
        if not ok:
            return False, "BACKUP_INTEGRITY_FAILED"
        return True, "BACKUP_CREATED"
    except (OSError, sqlite3.Error):
        return False, "BACKUP_FAILED"
