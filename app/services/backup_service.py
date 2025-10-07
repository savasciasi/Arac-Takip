"""Backup and restore service that works with SQLite database and storage."""
from __future__ import annotations

import shutil
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ..data.database import current_brand, current_database, execute_script, get_connection, storage_root
from ..utils.runtime_paths import backups_root

BACKUP_ROOT = backups_root()


def brand_backup_dir() -> Path:
    """Return the backup directory for the active brand."""

    directory = BACKUP_ROOT / current_brand()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class BackupService:
    """Create and restore zip archives of the database and storage."""

    def _storage_dir(self) -> Path:
        return storage_root()

    def _build_archive_name(self, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return brand_backup_dir() / f"{prefix}_{timestamp}.zip"

    def _escape(self, value) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, (int, float, Decimal)):
            return str(value)
        if isinstance(value, (datetime, date)):
            return f"'{value.isoformat()}'"
        text = str(value).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{text}'"

    def _dump_database(self) -> str:
        statements: list[str] = [f"USE `{current_database()}`;\n"]
        with get_connection() as conn:
            tables_cursor = conn.execute("SHOW TABLES")
            tables = [row[0] for row in tables_cursor.fetchall()]
            for table in tables:
                create_row = conn.execute(f"SHOW CREATE TABLE `{table}`").fetchone()
                if not create_row:
                    continue
                statements.append(f"DROP TABLE IF EXISTS `{table}`;\n")
                statements.append(create_row[1] + ";\n")
                data_cursor = conn.execute(f"SELECT * FROM `{table}`")
                rows = data_cursor.fetchall()
                if not rows:
                    continue
                columns = data_cursor.columns
                col_list = ", ".join(f"`{col}`" for col in columns)
                values_lines = []
                for row in rows:
                    values = ", ".join(self._escape(row[col]) for col in columns)
                    values_lines.append(f"({values})")
                statements.append(
                    f"INSERT INTO `{table}` ({col_list}) VALUES\n" + ",\n".join(values_lines) + ";\n"
                )
        return "\n".join(statements)

    def create_backup(self, prefix: str = "backup") -> Path:
        """Create a ZIP backup containing a SQL dump and storage files."""

        archive_path = self._build_archive_name(prefix)
        storage_dir = self._storage_dir()
        brand = current_brand()
        dump_sql = self._dump_database()
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("database.sql", dump_sql)
            if storage_dir.exists():
                for file in storage_dir.glob("**/*"):
                    if file.is_file():
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
            script_path = tmp_dir / "database.sql"
            if script_path.exists():
                execute_script(script_path.read_text(encoding="utf-8"))
            brand = current_brand()
            storage_source = tmp_dir / "storage" / brand
            storage_target = self._storage_dir()
            if storage_source.exists():
                if storage_target.exists():
                    shutil.rmtree(storage_target)
                shutil.copytree(storage_source, storage_target)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
