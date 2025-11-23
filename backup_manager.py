"""Backup manager for ai-model-compare project.

Creates a timestamped zip archive of the repository (excluding the backups folder itself)
inside ./backups and keeps only the most recent MAX_BACKUPS archives.
"""
from __future__ import annotations

import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent
BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_PREFIX = "backup_"
BACKUP_EXTENSION = ".zip"
MAX_BACKUPS = 30


def _should_skip(path: Path) -> bool:
    """Return True if the path should be excluded from the backup."""
    try:
        path.relative_to(BACKUP_DIR)
        return True
    except ValueError:
        return False


def _iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        # Skip traversing the backups directory
        dirnames[:] = [d for d in dirnames if not _should_skip(current_dir / d)]

        for filename in filenames:
            file_path = current_dir / filename
            if not _should_skip(file_path):
                yield file_path


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{BACKUP_PREFIX}{timestamp}{BACKUP_EXTENSION}"
    archive_path = BACKUP_DIR / archive_name

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in _iter_files(PROJECT_ROOT):
            relative_path = file_path.relative_to(PROJECT_ROOT)
            archive.write(file_path, arcname=str(relative_path))

    return archive_path


def prune_old_backups() -> None:
    backups = sorted(
        BACKUP_DIR.glob(f"{BACKUP_PREFIX}*{BACKUP_EXTENSION}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink(missing_ok=True)


def main() -> None:
    archive_path = create_backup()
    prune_old_backups()
    print(f"Backup created: {archive_path}")


if __name__ == "__main__":
    main()
