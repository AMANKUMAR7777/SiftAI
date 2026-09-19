import sqlite3
import time
from typing import List, Dict, Any, Optional
from backend.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables for audit logging and safe undo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                source_directory TEXT NOT NULL,
                files_count INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                original_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                folder_category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                reverted INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (batch_id) REFERENCES batches(id)
            )
        """)
        conn.commit()


def create_batch(batch_id: str, source_directory: str, files_count: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        created_at = time.strftime("%Y/%m/%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO batches (id, created_at, source_directory, files_count, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (batch_id, created_at, source_directory, files_count))
        conn.commit()


def record_move(batch_id: str, original_path: str, new_path: str, folder_category: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        created_at = time.strftime("%Y/%m/%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO moves (batch_id, original_path, new_path, folder_category, created_at, reverted)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (batch_id, original_path, new_path, folder_category, created_at))
        conn.commit()


def get_batches() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, b.created_at, b.source_directory, b.files_count, b.status,
                   COUNT(m.id) as recorded_moves,
                   SUM(m.reverted) as reverted_moves
            FROM batches b
            LEFT JOIN moves m ON b.id = m.batch_id
            GROUP BY b.id
            ORDER BY b.created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_batch_moves(batch_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, batch_id, original_path, new_path, folder_category, created_at, reverted
            FROM moves
            WHERE batch_id = ?
            ORDER BY id ASC
        """, (batch_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def mark_batch_status(batch_id: str, status: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE batches SET status = ? WHERE id = ?
        """, (status, batch_id))
        cursor.execute("""
            UPDATE moves SET reverted = 1 WHERE batch_id = ?
        """, (batch_id,))
        conn.commit()
