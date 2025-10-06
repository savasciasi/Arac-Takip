"""MySQL connection helpers compatible with the original SQLite API."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import mysql.connector
from mysql.connector import errorcode


STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME_TEMPLATE = os.getenv("DB_NAME_TEMPLATE", "aractakip_{brand}")
DB_SHARED_NAME = os.getenv("DB_SHARED_NAME")

_current_brand = ""
_current_database = ""
_table_prefix = ""


def _normalise_brand(brand: str) -> str:
    """Return a filesystem friendly brand identifier."""

    cleaned = "".join(ch for ch in brand.lower() if ch.isalnum())
    return cleaned or "default"


def _brand_directory(brand: str) -> Path:
    directory = STORAGE_ROOT / brand
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def storage_root(brand: str | None = None) -> Path:
    """Return the storage directory for the given or active brand."""

    code = _normalise_brand(brand or _current_brand)
    return _brand_directory(code)


def storage_path(*parts: str, brand: str | None = None, ensure: bool = False) -> Path:
    """Build a path inside the active brand storage directory."""

    base = storage_root(brand)
    path = base.joinpath(*parts) if parts else base
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_database_name(brand: str) -> str:
    template = DB_NAME_TEMPLATE or "aractakip_{brand}"
    if "{brand}" in template:
        return template.format(brand=brand)
    return template


def _ensure_database_exists(name: str) -> None:
    """Create the database if it does not already exist."""

    admin = None
    try:
        admin = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True,
        )
        cursor = admin.cursor()
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        finally:
            cursor.close()
    except mysql.connector.Error as exc:
        if exc.errno == errorcode.ER_DBACCESS_DENIED_ERROR:
            # Shared hosting environments often disallow CREATE DATABASE. If the
            # schema already exists the connection below will succeed and we can
            # continue silently; otherwise we raise a clearer error for the user.
            try:
                probe = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=name,
                    charset="utf8mb4",
                )
                probe.close()
            except mysql.connector.Error as probe_exc:  # pragma: no cover - env specific
                raise RuntimeError(
                    "MySQL kullanıcı hesabının yeni veritabanı oluşturma yetkisi yok ve "
                    f"'{name}' şeması bulunamadı. Lütfen phpMyAdmin üzerinden şemayı el ile oluşturun "
                    "veya sistem yöneticinizden yetki isteyin."
                ) from probe_exc
        else:  # pragma: no cover - unexpected MySQL error
            raise
    finally:
        if admin is not None:
            admin.close()


def _verify_database(name: str) -> None:
    """Ensure the provided database/schema is reachable by the user."""

    try:
        probe = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=name,
            charset="utf8mb4",
        )
        probe.close()
    except mysql.connector.Error as exc:  # pragma: no cover - environment specific
        raise RuntimeError(
            f"'{name}' şemasına bağlanılamadı. Lütfen DB_HOST/DB_USER ayarlarınızı doğrulayın."
        ) from exc


def set_brand_mode(brand: str) -> str:
    """Switch database/storage roots to the provided brand."""

    global _current_brand, _current_database, _table_prefix
    _current_brand = _normalise_brand(brand)
    target_database = _resolve_database_name(_current_brand)
    try:
        _ensure_database_exists(target_database)
        _verify_database(target_database)
        _current_database = target_database
        _table_prefix = ""
    except RuntimeError as exc:
        if not DB_SHARED_NAME:
            raise RuntimeError(
                "MySQL şeması oluşturulamadı. CREATE DATABASE yetkiniz yoksa mevcut şemanızı "
                "DB_SHARED_NAME değişkeniyle belirtmeniz gerekir."
            ) from exc
        _verify_database(DB_SHARED_NAME)
        _current_database = DB_SHARED_NAME
        _table_prefix = f"{_current_brand}_"
    return _current_database


def current_brand() -> str:
    """Expose the active brand code for other modules."""

    return _current_brand


def current_database() -> str:
    """Return the active MySQL schema name."""

    return _current_database


def table_prefix() -> str:
    """Expose the active table prefix (empty when dedicated schemas are used)."""

    return _table_prefix


def table_name(base: str) -> str:
    """Return the fully qualified table name for the active brand."""

    return f"{_table_prefix}{base}"


class Row(dict):
    """Dictionary row that also supports index based access."""

    def __init__(self, columns: Sequence[str], values: Sequence[Any]) -> None:
        super().__init__(zip(columns, values))
        self._columns = list(columns)

    def __getitem__(self, key: int | str) -> Any:  # type: ignore[override]
        if isinstance(key, int):
            key = self._columns[key]
        return super().__getitem__(key)


class CursorWrapper:
    """Thin wrapper providing sqlite-like cursor helpers."""

    def __init__(self, cursor: mysql.connector.cursor.MySQLCursor) -> None:
        self._cursor = cursor
        self._columns = [desc[0] for desc in cursor.description] if cursor.description else []

    def fetchone(self) -> Row | None:
        record = self._cursor.fetchone()
        if record is None:
            return None
        return Row(self._columns, record)

    def fetchall(self) -> list[Row]:
        return [Row(self._columns, row) for row in self._cursor.fetchall()]

    def __iter__(self) -> Iterator[Row]:
        for row in self._cursor:
            yield Row(self._columns, row)

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid  # type: ignore[return-value]

    @property
    def columns(self) -> Sequence[str]:
        return self._columns

    def close(self) -> None:
        self._cursor.close()


class ConnectionWrapper:
    """Context manager that emulates the subset of sqlite3 API we rely on."""

    def __init__(self) -> None:
        if not _current_database:
            raise RuntimeError("Database brand not initialised. Call set_brand_mode() first.")
        self._conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=_current_database,
            charset="utf8mb4",
            autocommit=False,
        )

    def __enter__(self) -> "ConnectionWrapper":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc:
                self._conn.rollback()
            else:
                self._conn.commit()
        finally:
            self._conn.close()

    # Delegate helpers -------------------------------------------------
    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    def cursor(self) -> mysql.connector.cursor.MySQLCursor:
        return self._conn.cursor()

    def execute(self, sql: str, params: Sequence[Any] | Mapping[str, Any] | None = None) -> CursorWrapper:
        statement, bound = _convert_sql(sql, params)
        cursor = self._conn.cursor(buffered=True)
        cursor.execute(statement, bound)
        wrapped = CursorWrapper(cursor)
        return wrapped

    def executemany(
        self,
        sql: str,
        params_seq: Iterable[Sequence[Any] | Mapping[str, Any]],
    ) -> None:
        statement = _convert_sql_statement(sql)
        cursor = self._conn.cursor(buffered=True)
        cursor.executemany(statement, list(params_seq))
        cursor.close()

    def executescript(self, sql: str) -> None:
        for statement in _split_sql_script(sql):
            if statement:
                self.execute(statement)


_NAMED_PATTERN = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def _convert_sql_statement(sql: str) -> str:
    """Convert SQLite style placeholders to MySQL compatible ones."""

    converted = sql.replace("?", "%s")

    def repl(match: re.Match[str]) -> str:
        return f"%({match.group(1)})s"

    return _NAMED_PATTERN.sub(repl, converted)


def _convert_sql(
    sql: str,
    params: Sequence[Any] | Mapping[str, Any] | None,
) -> tuple[str, Sequence[Any] | Mapping[str, Any] | None]:
    statement = _convert_sql_statement(sql)
    if params is None:
        return statement, None
    return statement, params


def _split_sql_script(sql: str) -> Iterator[str]:
    """Split multi-statement scripts into individual commands."""

    statement = []
    in_string = False
    quote_char = ""
    for char in sql:
        if char in {'"', "'"}:
            if not in_string:
                in_string = True
                quote_char = char
            elif quote_char == char:
                in_string = False
        if char == ";" and not in_string:
            chunk = "".join(statement).strip()
            if chunk:
                yield chunk
            statement = []
        else:
            statement.append(char)
    tail = "".join(statement).strip()
    if tail:
        yield tail


def get_connection() -> ConnectionWrapper:
    """Return a wrapped MySQL connection."""

    return ConnectionWrapper()


def execute_script(sql: str) -> None:
    """Execute a SQL script in a managed connection."""

    with get_connection() as conn:
        conn.executescript(sql)


def iter_rows(query: str, params: Sequence[Any] | None = None) -> Iterable[Row]:
    """Yield rows for a query lazily."""

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        for row in cursor:
            yield row


def transact(func) -> None:
    """Execute callback inside a transaction with auto-commit/rollback."""

    with get_connection() as conn:
        try:
            func(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# Initialise using environment variable so CLI scripts can target a brand.
set_brand_mode(os.getenv("APP_BRAND", "knk"))
