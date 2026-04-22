import os

os.environ["DEVVAULT_DB_FILENAME"] = "devvault_test.db"
os.environ["DEVVAULT_BACKUP_FILENAME"] = "devvault_test_backup.db"

from app.config import DB_PATH, BACKUP_PATH
from app.db import init_db
from app.services import (
    add_entry,
    clear_entries,
    get_entry,
    get_recent_entries,
    normalize_tags,
    reset_db,
    select_entries,
    set_favorite,
)


def setup_function():
    if DB_PATH.exists():
        DB_PATH.unlink()
    if BACKUP_PATH.exists():
        BACKUP_PATH.unlink()
    init_db()


def teardown_module():
    if DB_PATH.exists():
        DB_PATH.unlink()
    if BACKUP_PATH.exists():
        BACKUP_PATH.unlink()


def test_normalize_tags():
    assert normalize_tags(" Python, venv,python , PIP ") == "python,venv,pip"


def test_add_entry_and_get_entry():
    add_entry("Use python -m pip", "command", "python,venv")
    row = get_entry(1)

    assert row is not None
    assert row["content"] == "Use python -m pip"
    assert row["type"] == "command"
    assert row["tags"] == "python,venv"


def test_pin_entry():
    add_entry("Fix Metal issue", "fix", "mac,metal")
    ok = set_favorite(1, 1)
    row = get_entry(1)

    assert ok is True
    assert row["favorite"] == 1


def test_select_entries_combined_filters():
    add_entry("Fix Metal toolchain issue", "fix", "mac,metal,cmake")
    add_entry("Messy tags test", "note", "python,venv,pip")
    set_favorite(1, 1)

    rows = select_entries(
        query="metal",
        tag="mac",
        entry_type="fix",
        favorites_only=True,
    )

    assert len(rows) == 1
    assert rows[0]["id"] == 1


def test_recent_entries():
    add_entry("First", "note", "a")
    add_entry("Second", "note", "b")

    rows = get_recent_entries(1)

    assert len(rows) == 1
    assert rows[0]["content"] == "Second"


def test_recent_entries_with_filters():
    add_entry("Python cmd", "command", "python")
    add_entry("Metal fix", "fix", "metal")
    set_favorite(2, 1)

    rows = get_recent_entries(limit=5, entry_type="fix", favorites_only=True)

    assert len(rows) == 1
    assert rows[0]["content"] == "Metal fix"


def test_clear_entries_by_tag():
    add_entry("Python thing", "note", "python")
    add_entry("Metal thing", "fix", "metal")

    deleted = clear_entries(tag="python")

    assert deleted == 1
    assert get_entry(1) is None
    assert get_entry(2) is not None


def test_reset_db():
    add_entry("Something", "note", "test")
    reset_db()

    assert get_entry(1) is None
