"""Operator-triggered, non-overwriting SQLite snapshot primitive."""
from contextlib import closing
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
        ok, _ = verify_sqlite_recovery(str(destination))
        if not ok:
            return False, "BACKUP_INTEGRITY_FAILED"
        return True, "BACKUP_CREATED"
    except (OSError, sqlite3.Error):
        return False, "BACKUP_FAILED"


def create_restore_candidate(backup_path: str, candidate_path: str) -> tuple[bool, str]:
    """Copy a verified backup to a new candidate path; never activate or overwrite."""
    backup = Path(backup_path)
    candidate = Path(candidate_path)
    if not backup.is_file():
        return False, "RESTORE_BACKUP_UNAVAILABLE"
    try:
        if backup.resolve() == candidate.resolve():
            return False, "RESTORE_CANDIDATE_CONFLICT"
        if candidate.exists():
            return False, "RESTORE_CANDIDATE_EXISTS"
        source_ok, _ = verify_sqlite_recovery(str(backup))
        if not source_ok:
            return False, "RESTORE_BACKUP_INVALID"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(backup)) as source_db:
            with sqlite3.connect(str(candidate)) as candidate_db:
                source_db.backup(candidate_db)
        candidate_ok, _ = verify_sqlite_recovery(str(candidate))
        if not candidate_ok:
            candidate.unlink(missing_ok=True)
            return False, "RESTORE_CANDIDATE_INVALID"
        return True, "RESTORE_CANDIDATE_CREATED"
    except (OSError, sqlite3.Error):
        try:
            if candidate.is_file():
                candidate.unlink()
        except OSError:
            pass
        return False, "RESTORE_CANDIDATE_FAILED"


def validate_restore_candidate(candidate_path: str) -> tuple[bool, str]:
    """Validate integrity, schema, and data through one read-only snapshot."""
    from server.recovery import (
        _verify_messenger_data_connection,
        _verify_messenger_schema_connection,
        _verify_sqlite_recovery_connection,
    )

    candidate = Path(candidate_path)
    if not candidate.is_file():
        return False, "RESTORE_CANDIDATE_INTEGRITY_FAILED"
    try:
        uri = f"{candidate.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            connection.execute("BEGIN")
            # Pin the read snapshot before any validation phase.
            connection.execute("SELECT count(*) FROM sqlite_schema").fetchone()

            try:
                integrity_ok, _ = _verify_sqlite_recovery_connection(connection)
            except sqlite3.Error:
                return False, "RESTORE_CANDIDATE_INTEGRITY_FAILED"
            if not integrity_ok:
                return False, "RESTORE_CANDIDATE_INTEGRITY_FAILED"

            try:
                schema_ok, _ = _verify_messenger_schema_connection(connection)
            except (sqlite3.Error, ValueError, TypeError):
                return False, "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED"
            if not schema_ok:
                return False, "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED"

            try:
                data_ok, _ = _verify_messenger_data_connection(connection)
            except (sqlite3.Error, ValueError, TypeError, AttributeError):
                return False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"
            if not data_ok:
                return False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"
        return True, "RESTORE_CANDIDATE_VALIDATED"
    except (OSError, sqlite3.Error, ValueError, TypeError, AttributeError):
        return False, "RESTORE_CANDIDATE_INTEGRITY_FAILED"
