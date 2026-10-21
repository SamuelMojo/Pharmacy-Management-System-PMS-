import pytest

from pms import migrate
from pms.dao import database


# ---- file checks (no database needed) -------------------------------------------------

def test_discover_orders_by_number(tmp_path):
    (tmp_path / "010_b.sql").write_text("SELECT 1;")
    (tmp_path / "002_a.sql").write_text("SELECT 1;")
    assert [n for n, _ in migrate.discover(tmp_path)] == [2, 10]


def test_discover_rejects_duplicate_numbers(tmp_path):
    (tmp_path / "002_a.sql").write_text("SELECT 1;")
    (tmp_path / "002_b.sql").write_text("SELECT 1;")
    with pytest.raises(migrate.MigrationError, match="share the number"):
        migrate.discover(tmp_path)


def test_discover_rejects_bad_names(tmp_path):
    (tmp_path / "stock.sql").write_text("SELECT 1;")
    with pytest.raises(migrate.MigrationError, match="not a valid migration name"):
        migrate.discover(tmp_path)


def test_the_real_migrations_folder_is_valid():
    assert migrate.discover()[0][0] == 1


def test_checksum_ignores_windows_line_endings():
    assert migrate._checksum("a\r\nb") == migrate._checksum("a\nb")


# ---- against PostgreSQL ---------------------------------------------------------------

def test_applying_twice_does_nothing_the_second_time(db):
    assert migrate.apply_pending() == []


def test_foundation_tables_exist(db):
    with database.transaction() as conn:
        names = {
            r["tablename"]
            for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        }
    assert {"users", "audit_log", "notifications", "notification_reads", "schema_migrations"} <= names


def test_a_new_migration_is_applied_once_and_an_edited_one_is_caught(db, tmp_path):
    real = migrate.discover()
    for _, path in real:
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    extra = tmp_path / "900_extra.sql"
    extra.write_text("CREATE TABLE IF NOT EXISTS zz_extra (id INT);")
    try:
        assert migrate.apply_pending(directory=tmp_path) == ["900_extra.sql"]
        assert migrate.apply_pending(directory=tmp_path) == []
        extra.write_text("CREATE TABLE IF NOT EXISTS zz_extra (id INT, more INT);")
        with pytest.raises(migrate.MigrationError, match="edited"):
            migrate.apply_pending(directory=tmp_path)
    finally:
        with database.connect(autocommit=True) as conn:
            conn.execute("DROP TABLE IF EXISTS zz_extra")
            conn.execute("DELETE FROM schema_migrations WHERE version = 900")
