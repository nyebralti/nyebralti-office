import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import (
    QMainWindow, QScrollArea, QFileDialog, QMessageBox,
    QToolBar, QSpinBox, QLabel, QColorDialog, QStatusBar,
    QWidget, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QAction, QColor, QIcon, QImage
from PyQt6.QtCore import Qt

from common.database import DatabaseManager
from common.autosave_engine import AutosaveEngine
from common.history_dialog import HistoryDialog
from apps.paint.paint_canvas import PaintCanvas

class PaintWindow(QMainWindow):
    """Nyebralti Paint - Çizim ve Görsel Düzenleme Uygulaması"""

    def __init__(self, file_path: str = None):
        super().__init__()
        self.current_file_path = file_path
        self.db = DatabaseManager()

        self.setWindowTitle("Nyebralti Paint - Adsız Çizim")
        self.resize(1100, 800)

        # Tuval ve Scroll Alanı
        self.canvas = PaintCanvas(1280, 720)
        self.canvas.canvas_modified.connect(self._on_canvas_modified)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(scroll_area)

        # Otomatik Kayıt Motoru
        self.autosave = AutosaveEngine(app_type="paint", parent=self, interval_seconds=45)
        self.autosave.set_save_callback(self._on_autosave_callback)
        self.autosave.autosaved.connect(self._on_autosave_complete)

        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()

        if file_path and os.path.exists(file_path):
            self.load_file(file_path)

    def init_menus(self):
        menubar = self.menuBar()

        # DOSYA
        file_menu = menubar.addMenu("Dosya")

        new_act = QAction("Yeni Çizim", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self.file_new)
        file_menu.addAction(new_act)

        open_act = QAction("Aç...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self.file_open)
        file_menu.addAction(open_act)

        save_act = QAction("Kaydet", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self.file_save)
        file_menu.addAction(save_act)

        save_as_act = QAction("Farklı Kaydet...", self)
        save_as_act.triggered.connect(self.file_save_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        history_act = QAction("⏳ Önceki Kayıtlar ve Sürümler...", self)
        history_act.setShortcut("Ctrl+H")
        history_act.triggered.connect(self.show_history)
        file_menu.addAction(history_act)

        file_menu.addSeparator()

        exit_act = QAction("Çıkış", self)
        exit_act.setShortcut("Alt+F4")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # DÜZENLE
        edit_menu = menubar.addMenu("Düzenle")

        undo_act = QAction("Geri Al", self)
        undo_act.setShortcut("Ctrl+Z")
        undo_act.triggered.connect(self.canvas.undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("Yinele", self)
        redo_act.setShortcut("Ctrl+Y")
        redo_act.triggered.connect(self.canvas.redo)
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()

        clear_act = QAction("Tuvali Temizle", self)
        clear_act.triggered.connect(self.canvas.clear)
        edit_menu.addAction(clear_act)

    def init_toolbar(self):
        toolbar = QToolBar("Çizim Araçları")
        self.addToolBar(toolbar)

        # Araç Butonları
        tools = [
            ("✏️ Kalem", "pen"),
            ("🖌️ Fırça", "brush"),
            ("🧹 Silgi", "eraser"),
            ("📏 Çizgi", "line"),
            ("⬜ Dikdörtgen", "rect"),
            ("⚪ Elips", "ellipse"),
            ("🪣 Doldur", "fill"),
            ("🔤 Metin", "text"),
        ]

        self.tool_actions = {}
        for label, tool_id in tools:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, t=tool_id: self.select_tool(t))
            toolbar.addAction(act)
            self.tool_actions[tool_id] = act

        self.tool_actions["pen"].setChecked(True)

        toolbar.addSeparator()

        # Fırça Kalınlığı
        toolbar.addWidget(QLabel(" Boyut: "))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 100)
        self.size_spin.setValue(3)
        self.size_spin.valueChanged.connect(self.canvas.set_pen_size)
        toolbar.addWidget(self.size_spin)

        toolbar.addSeparator()

        # Hızlı Renk Paleti
        colors = [
            "#000000", "#ffffff", "#ef4444", "#3b82f6",
            "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"
        ]
        color_container = QWidget()
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(4)

        for col in colors:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background-color: {col}; border: 1px solid #555; border-radius: 3px;")
            btn.clicked.connect(lambda checked, c=col: self.set_color_hex(c))
            color_layout.addWidget(btn)

        toolbar.addWidget(color_container)

        # Özel Renk Seçici
        palette_btn = QAction("🎨 Özel Renk", self)
        palette_btn.triggered.connect(self.choose_custom_color)
        toolbar.addAction(palette_btn)

    def init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Hazır")
        self.status.addWidget(self.status_label)

    def select_tool(self, tool_id: str):
        for tid, act in self.tool_actions.items():
            act.setChecked(tid == tool_id)
        self.canvas.set_tool(tool_id)

    def set_color_hex(self, hex_code: str):
        col = QColor(hex_code)
        self.canvas.set_pen_color(col)

    def choose_custom_color(self):
        col = QColorDialog.getColor(self.canvas.pen_color, self, "Çizim Rengi Seçin")
        if col.isValid():
            self.canvas.set_pen_color(col)

    # --- DOSYA VE KAYIT ---
    def file_new(self):
        self.canvas.clear()
        self.current_file_path = None
        self.autosave.mark_clean()
        self.setWindowTitle("Nyebralti Paint - Adsız Çizim")
        self.status_label.setText("Yeni tuval oluşturuldu.")

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Görsel Aç", "", "Görseller (*.png *.jpg *.jpeg *.bmp);;Tüm Dosyalar (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        try:
            img = QImage(path)
            if img.isNull():
                raise ValueError("Görsel yüklenemedi.")

            self.canvas.image = img.scaled(
                self.canvas.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.canvas.update()
            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Paint - {Path(path).name}")
            self.status_label.setText(f"Açıldı: {Path(path).name}")
            self.db.log_activity("paint", "open", f"Görsel açıldı: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Görsel açılamadı:\n{e}")

    def file_save(self):
        if not self.current_file_path:
            self.file_save_as()
        else:
            self._save_to_path(self.current_file_path)

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Farklı Kaydet", "Cizim.png",
            "PNG Görseli (*.png);;JPEG Görseli (*.jpg *.jpeg);;BMP Görseli (*.bmp)"
        )
        if path:
            self._save_to_path(path)

    def _save_to_path(self, path: str):
        try:
            if not self.canvas.image.save(path):
                raise ValueError("Dosya formatı desteklenmiyor veya yazılamadı.")

            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Paint - {Path(path).name}")
            self.status_label.setText(f"Kaydedildi: {Path(path).name}")
            self.db.log_activity("paint", "save", f"Çizim kaydedildi: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız:\n{e}")

    def show_history(self):
        dlg = HistoryDialog(app_type="paint", current_file=self.current_file_path, parent=self)
        if dlg.exec():
            restored = dlg.restored_snapshot_path
            if restored and os.path.exists(restored):
                self.load_file(restored)
                self.autosave.mark_dirty()
                self.status_label.setText(f"Sürüm geri yüklendi: {Path(restored).name}")
                self.db.log_activity("paint", "restore", f"Sürüm geri yüklendi: {Path(restored).name}")

    def _on_canvas_modified(self):
        self.autosave.mark_dirty()

    def _on_autosave_callback(self, snapshot_path: str) -> str:
        self.canvas.image.save(snapshot_path, "PNG")
        w, h = self.canvas.image.width(), self.canvas.image.height()
        return f"{w}x{h} PNG Çizim"

    def _on_autosave_complete(self, snapshot_path: str):
        name = Path(snapshot_path).name
        self.status_label.setText(f"✓ Otomatik kayıt alındı ({name})")
