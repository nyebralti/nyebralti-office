import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from common.paths import get_db_path

class DatabaseManager:
    """
    Kullanıcıya özel SQLite veritabanı yöneticisi.
    Konum: %APPDATA%\\Nyebralti Office\\office.db
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Tabloları başlatır ve indexleri oluşturur."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Son Açılan ve İşlenen Dosyalar
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_type TEXT NOT NULL,         -- 'word', 'excel', 'paint'
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_size INTEGER DEFAULT 0,
                last_opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_favorite INTEGER DEFAULT 0
            )
            """)

            # 2. Otomatik Kayıtlar ve Anlık Görüntü (Snapshot) Geçmişi
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS autosaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_type TEXT NOT NULL,         -- 'word', 'excel', 'paint'
                original_file_path TEXT,        -- Düzenlenen asıl dosya (varsa)
                snapshot_path TEXT NOT NULL,    -- Roaming/autosaves altındaki kopya
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,                   -- İçerik özeti (boyut, kelime/hücre sayısı vb.)
                status TEXT DEFAULT 'active'    -- 'active', 'restored', 'archived'
            )
            """)

            # 3. Kullanıcı İşlem Günlüğü (Audit Log / Activity)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_type TEXT NOT NULL,
                action_type TEXT NOT NULL,      -- 'open', 'save', 'autosave', 'export_pdf', 'restore'
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 4. Kullanıcı Ayarları
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            conn.commit()

    # ==========================
    # SON DOSYALAR (RECENT FILES)
    # ==========================
    def add_recent_file(self, app_type: str, file_path: str, file_size: int = 0) -> int:
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name
        if file_size == 0 and file_path_obj.exists():
            try:
                file_size = file_path_obj.stat().st_size
            except Exception:
                file_size = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO recent_files (app_type, file_name, file_path, file_size, last_opened_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                app_type = excluded.app_type,
                file_name = excluded.file_name,
                file_size = excluded.file_size,
                last_opened_at = CURRENT_TIMESTAMP
            """, (app_type, file_name, str(file_path_obj), file_size))
            conn.commit()
            return cursor.lastrowid

    def get_recent_files(self, app_type: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if app_type:
                cursor.execute("""
                SELECT * FROM recent_files 
                WHERE app_type = ? 
                ORDER BY last_opened_at DESC LIMIT ?
                """, (app_type, limit))
            else:
                cursor.execute("""
                SELECT * FROM recent_files 
                ORDER BY last_opened_at DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def remove_recent_file(self, file_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recent_files WHERE id = ?", (file_id,))
            conn.commit()

    def toggle_favorite(self, file_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE recent_files 
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END 
            WHERE id = ?
            """, (file_id,))
            conn.commit()

    # ==========================
    # OTOMATİK KAYITLAR (AUTOSAVES)
    # ==========================
    def save_autosave(self, app_type: str, original_path: Optional[str], snapshot_path: str, summary: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO autosaves (app_type, original_file_path, snapshot_path, summary, status)
            VALUES (?, ?, ?, ?, 'active')
            """, (app_type, str(original_path) if original_path else None, str(snapshot_path), summary))
            conn.commit()
            auto_id = cursor.lastrowid

        self.log_activity(app_type, "autosave", f"Otomatik kayıt alındı: {Path(snapshot_path).name}")
        return auto_id

    def get_autosaves(self, app_type: Optional[str] = None, original_path: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM autosaves WHERE 1=1"
            params = []

            if app_type:
                query += " AND app_type = ?"
                params.append(app_type)
            if original_path:
                query += " AND original_file_path = ?"
                params.append(str(original_path))

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def delete_autosave(self, autosave_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT snapshot_path FROM autosaves WHERE id = ?", (autosave_id,))
            row = cursor.fetchone()
            if row and row['snapshot_path']:
                try:
                    p = Path(row['snapshot_path'])
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
            cursor.execute("DELETE FROM autosaves WHERE id = ?", (autosave_id,))
            conn.commit()

    # ==========================
    # KULLANICI İŞLEM GÜNLÜĞÜ (ACTIVITY LOG)
    # ==========================
    def log_activity(self, app_type: str, action_type: str, details: str = ""):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_activity (app_type, action_type, details)
            VALUES (?, ?, ?)
            """, (app_type, action_type, details))
            conn.commit()

    def get_activities(self, app_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if app_type:
                cursor.execute("""
                SELECT * FROM user_activity 
                WHERE app_type = ? 
                ORDER BY timestamp DESC LIMIT ?
                """, (app_type, limit))
            else:
                cursor.execute("""
                SELECT * FROM user_activity 
                ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==========================
    # AYARLAR (SETTINGS)
    # ==========================
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
            return default

    def set_setting(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))
            conn.commit()
