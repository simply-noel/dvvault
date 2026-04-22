import shutil

import pyperclip

from app.config import BACKUP_PATH, DB_PATH
from app.db import get_conn, init_db


def normalize_tags(tags: str) -> str:
    """Normalize comma-separated tags into lowercase, trimmed, unique values."""
    if not tags:
        return ""

    cleaned = []
    seen = set()

    for tag in tags.split(","):
        t = tag.strip().lower()
        if t and t not in seen:
            seen.add(t)
            cleaned.append(t)

    return ",".join(cleaned)


def add_entry(content: str, entry_type: str = "note", tags: str = ""):
    """Insert a new entry into the vault."""
    conn = get_conn()
    cur = conn.cursor()

    normalized_tags = normalize_tags(tags)
    normalized_type = entry_type.strip().lower()

    cur.execute(
        """
        INSERT INTO entries (content, type, tags)
        VALUES (?, ?, ?)
        """,
        (content, normalized_type, normalized_tags),
    )

    conn.commit()
    conn.close()


def list_entries(tag: str = "", entry_type: str = "", favorites_only: bool = False):
    """Return entries filtered by tag, type, and pin status."""
    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT id, content, type, tags, favorite, created_at, updated_at
        FROM entries
        WHERE 1=1
    """
    params = []

    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag.strip().lower()}%")

    if entry_type:
        query += " AND type = ?"
        params.append(entry_type.strip().lower())

    if favorites_only:
        query += " AND favorite = 1"

    query += " ORDER BY id DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def search_entries(query: str):
    """Search entries by free text across content, tags, and type."""
    conn = get_conn()
    cur = conn.cursor()

    like_query = f"%{query.strip()}%"
    cur.execute(
        """
        SELECT id, content, type, tags, favorite, created_at, updated_at
        FROM entries
        WHERE content LIKE ? OR tags LIKE ? OR type LIKE ?
        ORDER BY id DESC
        """,
        (like_query, like_query, like_query),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def select_entries(
    query: str = "",
    tag: str = "",
    entry_type: str = "",
    favorites_only: bool = False,
):
    """Return entries using combined filters."""
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT id, content, type, tags, favorite, created_at, updated_at
        FROM entries
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (content LIKE ? OR tags LIKE ? OR type LIKE ?)"
        like_query = f"%{query.strip()}%"
        params.extend([like_query, like_query, like_query])

    if tag:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag.strip().lower()}%")

    if entry_type:
        sql += " AND type = ?"
        params.append(entry_type.strip().lower())

    if favorites_only:
        sql += " AND favorite = 1"

    sql += " ORDER BY id DESC"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_recent_entries(
    limit: int = 10,
    tag: str = "",
    entry_type: str = "",
    favorites_only: bool = False,
):
    """Return recent entries with optional filters."""
    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT id, content, type, tags, favorite, created_at, updated_at
        FROM entries
        WHERE 1=1
    """
    params = []

    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag.strip().lower()}%")

    if entry_type:
        query += " AND type = ?"
        params.append(entry_type.strip().lower())

    if favorites_only:
        query += " AND favorite = 1"

    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_entry(entry_id: int):
    """Return a single entry by ID."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, content, type, tags, favorite, created_at, updated_at
        FROM entries
        WHERE id = ?
        """,
        (entry_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_entry(entry_id: int, content: str = "", entry_type: str = "", tags: str = ""):
    """Update an existing entry."""
    conn = get_conn()
    cur = conn.cursor()

    existing = get_entry(entry_id)
    if not existing:
        conn.close()
        return False

    new_content = content if content else existing["content"]
    new_type = entry_type.strip().lower() if entry_type else existing["type"]
    new_tags = normalize_tags(tags) if tags else existing["tags"]

    cur.execute(
        """
        UPDATE entries
        SET content = ?, type = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (new_content, new_type, new_tags, entry_id),
    )

    conn.commit()
    conn.close()
    return True


def delete_entry(entry_id: int):
    """Delete one entry by ID."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def toggle_favorite(entry_id: int):
    """Toggle pin status for an entry."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE entries
        SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (entry_id,),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def set_favorite(entry_id: int, value: int):
    """Explicitly set pin status for an entry."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE entries
        SET favorite = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (value, entry_id),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def copy_entry_content(entry_id: int):
    """Copy entry content to clipboard."""
    row = get_entry(entry_id)
    if not row:
        return False

    pyperclip.copy(row["content"])
    return True


def clear_entries(
    tag: str = "",
    entry_type: str = "",
    favorites_only: bool = False,
    clear_all: bool = False,
):
    """Delete entries by filters or wipe all entries."""
    conn = get_conn()
    cur = conn.cursor()

    query = "DELETE FROM entries WHERE 1=1"
    params = []

    if not clear_all:
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag.strip().lower()}%")
        if entry_type:
            query += " AND type = ?"
            params.append(entry_type.strip().lower())
        if favorites_only:
            query += " AND favorite = 1"

        if not tag and not entry_type and not favorites_only:
            conn.close()
            return 0

    cur.execute(query, params)
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted


def backup_db():
    """Create a backup copy of the current database."""
    if not DB_PATH.exists():
        return False, "Database file not found."

    shutil.copy2(DB_PATH, BACKUP_PATH)
    return True, str(BACKUP_PATH)


def restore_db():
    """Restore the database from backup."""
    if not BACKUP_PATH.exists():
        return False, "Backup file not found."

    shutil.copy2(BACKUP_PATH, DB_PATH)
    return True, str(DB_PATH)


def reset_db():
    """Delete and recreate the database file."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    return True


def get_total_entries_count() -> int:
    """Return total number of entries."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM entries")
    count = cur.fetchone()["count"]
    conn.close()
    return count


def get_pinned_entries_count() -> int:
    """Return number of pinned entries."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM entries WHERE favorite = 1")
    count = cur.fetchone()["count"]
    conn.close()
    return count


def get_type_counts():
    """Return grouped counts by entry type."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT type, COUNT(*) AS count
        FROM entries
        GROUP BY type
        ORDER BY count DESC, type ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_tag_counts():
    """Return grouped counts for all tags."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tags FROM entries WHERE tags != ''")
    rows = cur.fetchall()
    conn.close()

    counts = {}
    for row in rows:
        for tag in row["tags"].split(","):
            t = tag.strip()
            if t:
                counts[t] = counts.get(t, 0) + 1

    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))
