import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QSplitter, QMessageBox, QFileDialog, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon

from common.database import DatabaseManager

class HistoryDialog(QDialog):
    """
    Kullanıcının önceki otomatik kayıtlarını ve revizyonlarını
    görüntüleyip geri yüklemesini sağlayan evrensel iletişim penceresi.
    """
    def __init__(self, app_type: str, current_file: str = None, parent=None):
        super().__init__(parent)
        self.app_type = app_type
        self.current_file = current_file
        self.db = DatabaseManager()
        self.selected_record = None
        self.restored_snapshot_path = None

        self.setWindowTitle(f"Nyebralti Office - Önceki Kayıtlar ve Sürüm Geçmişi ({app_type.capitalize()})")
        self.resize(850, 520)
        self.init_ui()
        self.load_records()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Üst bilgi
        info_label = QLabel(
            "Otomatik olarak ve aralıklarla alınan önceki kayıtlarınızı buradan inceleyebilir, "
            "önizleyebilir ve istediğiniz sürümü geri yükleyebilirsiniz."
        )
        info_label.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 6px;")
        main_layout.addWidget(info_label)

        # Bölücü (Splitter): Sol tarafta liste, sağ tarafta önizleme
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol Panel: Kayıt Listesi
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_label = QLabel("Kayıt Tarihçesi:")
        left_label.setStyleSheet("font-weight: bold; color: #f0f0f5;")
        left_layout.addWidget(left_label)

        self.record_list = QListWidget()
        self.record_list.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.record_list)

        splitter.addWidget(left_widget)

        # Sağ Panel: Önizleme & Detay
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.detail_label = QLabel("Önizleme:")
        self.detail_label.setStyleSheet("font-weight: bold; color: #f0f0f5;")
        right_layout.addWidget(self.detail_label)

        # Önizleme widget'ları
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setVisible(False)
        right_layout.addWidget(self.text_preview)

        self.image_preview = QLabel("Görsel Önizleme")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("border: 1px dashed #444; border-radius: 6px;")
        self.image_preview.setVisible(False)
        right_layout.addWidget(self.image_preview)

        splitter.addWidget(right_widget)
        splitter.setSizes([320, 530])
        main_layout.addWidget(splitter)

        # Alt Butonlar
        button_layout = QHBoxLayout()

        self.delete_btn = QPushButton("Bu Sürümü Sil")
        self.delete_btn.setStyleSheet("background-color: #7f1d1d; border-color: #991b1b; color: white;")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.save_as_btn = QPushButton("Farklı Kaydet...")
        self.save_as_btn.clicked.connect(self.save_as)
        button_layout.addWidget(self.save_as_btn)

        self.restore_btn = QPushButton("Bu Sürümü Geri Yükle")
        self.restore_btn.setProperty("primary", True)
        self.restore_btn.clicked.connect(self.restore_selected)
        button_layout.addWidget(self.restore_btn)

        self.close_btn = QPushButton("Kapat")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)

    def load_records(self):
        self.record_list.clear()
        records = self.db.get_autosaves(app_type=self.app_type, limit=60)
        for rec in records:
            p = Path(rec['snapshot_path'])
            display_text = f"📅 {rec['created_at']}  -  {rec['summary'] or p.name}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, rec)
            self.record_list.addItem(item)

        if self.record_list.count() > 0:
            self.record_list.setCurrentRow(0)

    def on_selection_changed(self):
        current_item = self.record_list.currentItem()
        if not current_item:
            self.selected_record = None
            return

        rec = current_item.data(Qt.ItemDataRole.UserRole)
        self.selected_record = rec
        snapshot_path = Path(rec['snapshot_path'])

        if not snapshot_path.exists():
            self.detail_label.setText(f"Dosya bulunamadı: {snapshot_path}")
            return

        if self.app_type == "paint":
            self.text_preview.setVisible(False)
            self.image_preview.setVisible(True)
            pix = QPixmap(str(snapshot_path))
            if not pix.isNull():
                self.image_preview.setPixmap(pix.scaled(
                    self.image_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.image_preview.setText("Görsel yüklenemedi.")
        elif self.app_type == "word":
            self.image_preview.setVisible(False)
            self.text_preview.setVisible(True)
            try:
                content = snapshot_path.read_text(encoding='utf-8')
                self.text_preview.setHtml(content)
            except Exception:
                self.text_preview.setPlainText("Metin yüklenemedi.")
        elif self.app_type == "excel":
            self.image_preview.setVisible(False)
            self.text_preview.setVisible(True)
            try:
                content = snapshot_path.read_text(encoding='utf-8')
                self.text_preview.setPlainText(content[:2000])
            except Exception:
                self.text_preview.setPlainText("Tablo verisi yüklenemedi.")

    def restore_selected(self):
        if not self.selected_record:
            QMessageBox.warning(self, "Uyarı", "Lütfen geri yüklenecek bir kayıt seçin.")
            return

        self.restored_snapshot_path = self.selected_record['snapshot_path']
        self.accept()

    def save_as(self):
        if not self.selected_record:
            return
        snapshot_path = Path(self.selected_record['snapshot_path'])
        if not snapshot_path.exists():
            QMessageBox.warning(self, "Hata", "Kaynak dosya bulunamadı.")
            return

        ext = snapshot_path.suffix
        filter_str = f"Office Dosyası (*{ext})"
        save_path, _ = QFileDialog.getSaveFileName(self, "Farklı Kaydet", snapshot_path.name, filter_str)
        if save_path:
            import shutil
            shutil.copy2(str(snapshot_path), save_path)
            QMessageBox.information(self, "Başarılı", f"Dosya kaydedildi:\n{save_path}")

    def delete_selected(self):
        if not self.selected_record:
            return
        res = QMessageBox.question(
            self, "Kayıt Sil", "Bu otomatik kaydı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            self.db.delete_autosave(self.selected_record['id'])
            self.load_records()
