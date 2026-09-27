import os
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from common.paths import get_autosaves_dir
from common.database import DatabaseManager

class AutosaveEngine(QObject):
    """
    Belge, çizim veya elektronik tablo için otomatik yedekleme motoru.
    %APPDATA%\\Nyebralti Office\\autosaves\\ dizinine kayıt yapar ve office.db'ye işler.
    """
    autosaved = pyqtSignal(str) # Snapshot yolu sinyali

    def __init__(self, app_type: str, parent=None, interval_seconds: int = 45):
        super().__init__(parent)
        self.app_type = app_type
        self.interval_ms = interval_seconds * 1000
        self.db = DatabaseManager()
        self.current_file_path: Optional[str] = None
        self.has_unsaved_changes = False
        self._save_callback: Optional[Callable[[str], str]] = None # callback(snapshot_path) -> summary

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.trigger_autosave)
        self.timer.start(self.interval_ms)

    def set_save_callback(self, callback: Callable[[str], str]):
        """
        Kayıt anında çağrılacak fonksiyon:
        callback(snapshot_path: str) -> summary: str
        """
        self._save_callback = callback

    def mark_dirty(self):
        """İçerik değiştiğinde çağrılır."""
        self.has_unsaved_changes = True

    def mark_clean(self, saved_file_path: Optional[str] = None):
        """Kullanıcı manuel kaydettiğinde çağrılır."""
        self.has_unsaved_changes = False
        if saved_file_path:
            self.current_file_path = saved_file_path
            self.db.add_recent_file(self.app_type, saved_file_path)

    def trigger_autosave(self, force: bool = False):
        """Otomatik kayıt tetikleyici."""
        if not force and not self.has_unsaved_changes:
            return

        if not self._save_callback:
            return

        try:
            autosaves_folder = get_autosaves_dir(self.app_type)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            orig_name = "adsiz"
            if self.current_file_path:
                orig_name = Path(self.current_file_path).stem

            # Uzantıyı uygulama türüne göre belirle
            ext = ".nyw" if self.app_type == "word" else (".nyx" if self.app_type == "excel" else ".png")
            snapshot_filename = f"{orig_name}_{timestamp}{ext}"
            snapshot_path = autosaves_folder / snapshot_filename

            # Callback ile veriyi kaydet
            summary = self._save_callback(str(snapshot_path))
            if not summary:
                summary = f"Otomatik yedek: {timestamp}"

            # Veritabanına işle
            self.db.save_autosave(
                app_type=self.app_type,
                original_path=self.current_file_path,
                snapshot_path=str(snapshot_path),
                summary=summary
            )

            self.autosaved.emit(str(snapshot_path))
            self._prune_old_snapshots()
        except Exception as e:
            print(f"[AutosaveEngine Error] {e}")

    def _prune_old_snapshots(self, max_snapshots: int = 30):
        """Eski anlık görüntüleri temizler."""
        try:
            records = self.db.get_autosaves(app_type=self.app_type, limit=100)
            if len(records) > max_snapshots:
                for rec in records[max_snapshots:]:
                    self.db.delete_autosave(rec['id'])
        except Exception as e:
            print(f"[AutosaveEngine Prune Error] {e}")
