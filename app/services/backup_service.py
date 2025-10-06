"""Backup and restore service that works with SQLite database and storage."""
from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BASE_DIR / "storage"
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


class BackupService:
    """Create and restore zip archives of the database and storage."""

    def __init__(self) -> None:
        self.db_file = STORAGE_DIR / "app.db"

    def _build_archive_name(self, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return BACKUP_DIR / f"{prefix}_{timestamp}.zip"

    def create_backup(self, prefix: str = "backup") -> Path:
        """Create a ZIP backup containing the database and storage files."""
        archive_path = self._build_archive_name(prefix)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if self.db_file.exists():
                zipf.write(self.db_file, arcname="app.db")
            for file in STORAGE_DIR.glob("**/*"):
                if file.is_file() and file != self.db_file:
                    zipf.write(file, arcname=f"storage/{file.relative_to(STORAGE_DIR)}")
        return archive_path

    def restore_backup(self, archive: Path) -> None:
        """Restore from backup after creating a safety copy."""
        if not archive.exists():
            raise FileNotFoundError(str(archive))
        pre_backup = self.create_backup("pre_restore")
        tmp_dir = BACKUP_DIR / "tmp_restore"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)
        try:
            with zipfile.ZipFile(archive, "r") as zipf:
                zipf.extractall(tmp_dir)
            db_path = tmp_dir / "app.db"
            if db_path.exists():
                shutil.copy2(db_path, self.db_file)
            storage_root = tmp_dir / "storage"
            if storage_root.exists():
                if STORAGE_DIR.exists():
                    shutil.rmtree(STORAGE_DIR)
                shutil.copytree(storage_root, STORAGE_DIR)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
