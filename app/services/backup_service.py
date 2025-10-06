"""Backup and restore service that works with SQLite database and storage."""
from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from ..data.database import current_brand, database_path, storage_root

BASE_DIR = Path(__file__).resolve().parents[1]
BACKUP_ROOT = BASE_DIR / "backups"
BACKUP_ROOT.mkdir(exist_ok=True)


def brand_backup_dir() -> Path:
    """Return the backup directory for the active brand."""

    directory = BACKUP_ROOT / current_brand()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class BackupService:
    """Create and restore zip archives of the database and storage."""

    def _db_file(self) -> Path:
        return database_path()

    def _storage_dir(self) -> Path:
        return storage_root()

    def _build_archive_name(self, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return brand_backup_dir() / f"{prefix}_{timestamp}.zip"

    def create_backup(self, prefix: str = "backup") -> Path:
        """Create a ZIP backup containing the database and storage files."""

        archive_path = self._build_archive_name(prefix)
        db_file = self._db_file()
        storage_dir = self._storage_dir()
        brand = current_brand()
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if db_file.exists():
                zipf.write(db_file, arcname="app.db")
            if storage_dir.exists():
                for file in storage_dir.glob("**/*"):
                    if file.is_file() and file != db_file:
                        relative = file.relative_to(storage_dir)
                        zipf.write(file, arcname=f"storage/{brand}/{relative}")
        return archive_path

    def restore_backup(self, archive: Path) -> None:
        """Restore from backup after creating a safety copy."""

        if not archive.exists():
            raise FileNotFoundError(str(archive))
        self.create_backup("pre_restore")
        tmp_dir = brand_backup_dir() / "tmp_restore"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)
        try:
            with zipfile.ZipFile(archive, "r") as zipf:
                zipf.extractall(tmp_dir)
            db_path = tmp_dir / "app.db"
            target_db = self._db_file()
            if db_path.exists():
                target_db.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(db_path, target_db)
            brand = current_brand()
            storage_source = tmp_dir / "storage" / brand
            storage_target = self._storage_dir()
            if storage_source.exists():
                if storage_target.exists():
                    shutil.rmtree(storage_target)
                shutil.copytree(storage_source, storage_target)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
