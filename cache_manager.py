import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_cache.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_files (
                file_id TEXT PRIMARY KEY,
                folder_id TEXT NOT NULL,
                name TEXT NOT NULL,
                size INTEGER DEFAULT 0,
                mime_type TEXT,
                modified_time TEXT,
                first_seen_at TEXT NOT NULL,
                notified_at TEXT,
                downloaded_at TEXT,
                download_path TEXT
            )
        """)
    conn.close()

def is_new_or_modified(file_info: Dict[str, Any]) -> bool:
    """
    Checks if a file is brand new or modified compared to cached record.
    """
    file_id = file_info["id"]
    current_modified = file_info.get("modifiedTime", "")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT modified_time FROM seen_files WHERE file_id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return True # Brand new file
    
    cached_modified = row["modified_time"]
    if current_modified and cached_modified != current_modified:
        return True # File has been updated
        
    return False

def record_discovered_files(files: List[Dict[str, Any]]) -> None:
    now_str = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        for f in files:
            conn.execute("""
                INSERT INTO seen_files (
                    file_id, folder_id, name, size, mime_type, modified_time, first_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    name = excluded.name,
                    size = excluded.size,
                    mime_type = excluded.mime_type,
                    modified_time = excluded.modified_time
            """, (
                f["id"],
                f.get("folder_id", ""),
                f.get("name", "Unknown"),
                int(f.get("size", 0) or 0),
                f.get("mimeType", ""),
                f.get("modifiedTime", ""),
                now_str
            ))
    conn.close()

def mark_files_notified(file_ids: List[str]) -> None:
    now_str = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        conn.executemany(
            "UPDATE seen_files SET notified_at = ? WHERE file_id = ?",
            [(now_str, fid) for fid in file_ids]
        )
    conn.close()

def mark_file_downloaded(file_id: str, download_path: str) -> None:
    now_str = datetime.now().isoformat()
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE seen_files SET downloaded_at = ?, download_path = ? WHERE file_id = ?",
            (now_str, download_path, file_id)
        )
    conn.close()

def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT file_id, folder_id, name, size, modified_time, first_seen_at, notified_at, downloaded_at, download_path
        FROM seen_files
        ORDER BY first_seen_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_cache() -> int:
    """Deletes all tracked file records from seen_files table. Returns count deleted."""
    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM seen_files")
        count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM seen_files")
    conn.execute("VACUUM")
    conn.close()
    return count

def get_downloaded_file_ids() -> Dict[str, str]:
    """Returns a dict mapping file_id to downloaded_at timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, downloaded_at FROM seen_files WHERE downloaded_at IS NOT NULL")
    res = {row["file_id"]: row["downloaded_at"] for row in cursor.fetchall()}
    conn.close()
    return res
