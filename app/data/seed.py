"""Seed the database with demo data for development and tests."""
from __future__ import annotations

from datetime import date, timedelta

from pathlib import Path

from .database import current_brand, get_connection, table_name


VEHICLES = [
    ("34ABC123", "Ford", "Transit", 2020, "Soğuk zincir aracı"),
    ("06XYZ789", "Mercedes", "Sprinter", 2019, "Uzun yol aracı"),
]

DRIVERS = [
    ("Ali", "Kaya", "+90 533 000 11 22", "TR123456", "Gece vardiyası"),
    ("Hans", "Zimmer", "+49 170 000 44 55", "DE987654", "Almanya hattı"),
]

FINES = [
    (1, 1, "F-2023001", date.today().isoformat(), 150.0, "Hız sınırı", "OPEN", None, "[]"),
    (2, 2, "F-2023002", (date.today() - timedelta(days=10)).isoformat(), 320.0, "Park yasağı", "PAID", (date.today() - timedelta(days=5)).isoformat(), "[]"),
]

def _doc_path(name: str) -> str:
    return str(Path("storage") / current_brand() / name)


DOCUMENTS = [
    (1, None, "Sigorta Poliçesi", _doc_path("insurance.pdf"), None, "sigorta"),
    (None, 1, "Ehliyet Fotokopisi", _doc_path("license_ali.jpg"), None, "kimlik"),
]

ASSIGNMENTS = [
    (1, 1, (date.today() - timedelta(days=30)).isoformat(), None, "Aktif"),
    (2, 2, (date.today() - timedelta(days=15)).isoformat(), None, "Aktif"),
]

MAINTENANCE = [
    (1, "Periyodik bakım", (date.today() + timedelta(days=7)).isoformat(), 0, "Yağ değişimi"),
    (2, "Muayene", (date.today() + timedelta(days=1)).isoformat(), 0, "Genel kontrol"),
]


def run() -> None:
    """Insert seed rows if tables are empty."""
    with get_connection() as conn:
        vehicles_table = table_name("vehicles")
        drivers_table = table_name("drivers")
        fines_table = table_name("fines")
        documents_table = table_name("documents")
        assignments_table = table_name("vehicle_assignments")
        maintenance_table = table_name("maintenance_reminders")

        cur = conn.execute(f"SELECT COUNT(*) FROM {vehicles_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {vehicles_table}(plate, brand, model, year, notes) VALUES(%s,%s,%s,%s,%s)",
                VEHICLES,
            )

        cur = conn.execute(f"SELECT COUNT(*) FROM {drivers_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {drivers_table}(first_name, last_name, phone, license_no, notes) VALUES(%s,%s,%s,%s,%s)",
                DRIVERS,
            )

        cur = conn.execute(f"SELECT COUNT(*) FROM {fines_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"""
                INSERT INTO {fines_table}(vehicle_id, driver_id, fine_no, date, amount, description, status, payment_date, attachments_json)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                FINES,
            )

        cur = conn.execute(f"SELECT COUNT(*) FROM {documents_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {documents_table}(vehicle_id, driver_id, title, path, preview_path, tags) VALUES(%s,%s,%s,%s,%s,%s)",
                DOCUMENTS,
            )

        cur = conn.execute(f"SELECT COUNT(*) FROM {assignments_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {assignments_table}(vehicle_id, driver_id, from_date, to_date, notes) VALUES(%s,%s,%s,%s,%s)",
                ASSIGNMENTS,
            )

        cur = conn.execute(f"SELECT COUNT(*) FROM {maintenance_table}")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {maintenance_table}(vehicle_id, title, next_date, done, notes) VALUES(%s,%s,%s,%s,%s)",
                MAINTENANCE,
            )

        conn.commit()


if __name__ == "__main__":
    run()
