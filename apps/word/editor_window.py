import sys
import os
from pathlib import Path

# Add project root to sys.path so common can be imported directly
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QFileDialog, QMessageBox,
    QFontComboBox, QSpinBox, QColorDialog, QToolBar,
    QInputDialog, QLabel, QStatusBar, QApplication
)
from PyQt6.QtGui import (
    QAction, QFont, QTextCursor, QTextListFormat,
    QColor, QTextTableFormat, QImage, QPainter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from common.paths import get_project_root
from common.database import DatabaseManager
from common.autosave_engine import AutosaveEngine
from common.history_dialog import HistoryDialog
from common.theme import apply_theme

class WordEditorWindow(QMainWindow):
    """Nyebralti Word - Zengin Metin Düzenleyici ve Belge Yöneticisi"""

    def __init__(self, file_path: str = None):
        super().__init__()
        self.current_file_path = file_path
        self.db = DatabaseManager()

        self.setWindowTitle("Nyebralti Word - Yeni Belge")
        self.resize(1000, 750)

        # Editor
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Segoe UI", 12))
        self.setCentralWidget(self.editor)

        # Otomatik Kayıt Motoru
        self.autosave = AutosaveEngine(app_type="word", parent=self, interval_seconds=45)
        self.autosave.set_save_callback(self._on_autosave_callback)
        self.autosave.autosaved.connect(self._on_autosave_complete)
        self.editor.textChanged.connect(self._on_text_changed)

        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()

        if file_path and os.path.exists(file_path):
            self.load_file(file_path)

    def init_menus(self):
        menubar = self.menuBar()

        # DOSYA MENÜSÜ
        file_menu = menubar.addMenu("Dosya")

        new_act = QAction("Yeni Belge", self)
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

        # Önceki Kayıtlar / Sürümler
        history_act = QAction("⏳ Önceki Kayıtlar ve Sürümler...", self)
        history_act.setShortcut("Ctrl+H")
        history_act.triggered.connect(self.show_history)
        file_menu.addAction(history_act)

        file_menu.addSeparator()

        export_pdf_act = QAction("📄 PDF Olarak Aktar...", self)
        export_pdf_act.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_act)

        exit_act = QAction("Çıkış", self)
        exit_act.setShortcut("Alt+F4")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # DÜZENLE MENÜSÜ
        edit_menu = menubar.addMenu("Düzenle")

        undo_act = QAction("Geri Al", self)
        undo_act.setShortcut("Ctrl+Z")
        undo_act.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("Yinele", self)
        redo_act.setShortcut("Ctrl+Y")
        redo_act.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()

        cut_act = QAction("Kes", self)
        cut_act.setShortcut("Ctrl+X")
        cut_act.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_act)

        copy_act = QAction("Kopyala", self)
        copy_act.setShortcut("Ctrl+C")
        copy_act.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_act)

        paste_act = QAction("Yapıştır", self)
        paste_act.setShortcut("Ctrl+V")
        paste_act.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_act)

        # EKLE MENÜSÜ
        insert_menu = menubar.addMenu("Ekle")

        insert_table_act = QAction("Tablo Ekle...", self)
        insert_table_act.triggered.connect(self.insert_table)
        insert_menu.addAction(insert_table_act)

        insert_image_act = QAction("Resim Ekle...", self)
        insert_image_act.triggered.connect(self.insert_image)
        insert_menu.addAction(insert_image_act)

        insert_hr_act = QAction("Yatay Çizgi Ekle", self)
        insert_hr_act.triggered.connect(lambda: self.editor.insertHtml("<hr>"))
        insert_menu.addAction(insert_hr_act)

    def init_toolbar(self):
        toolbar = QToolBar("Biçimlendirme")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # Yazı Tipi Ailesi
        self.font_family = QFontComboBox()
        self.font_family.currentFontChanged.connect(self.change_font_family)
        toolbar.addWidget(self.font_family)

        # Yazı Boyutu
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 72)
        self.font_size.setValue(12)
        self.font_size.valueChanged.connect(self.change_font_size)
        toolbar.addWidget(self.font_size)

        toolbar.addSeparator()

        # Kalın (Bold)
        self.bold_act = QAction("B", self)
        self.bold_act.setCheckable(True)
        self.bold_act.setToolTip("Kalın (Ctrl+B)")
        self.bold_act.triggered.connect(self.set_bold)
        toolbar.addAction(self.bold_act)

        # İtalik (Italic)
        self.italic_act = QAction("I", self)
        self.italic_act.setCheckable(True)
        self.italic_act.setToolTip("İtalik (Ctrl+I)")
        self.italic_act.triggered.connect(self.set_italic)
        toolbar.addAction(self.italic_act)

        # Altı Çizili (Underline)
        self.underline_act = QAction("U", self)
        self.underline_act.setCheckable(True)
        self.underline_act.setToolTip("Altı Çizili (Ctrl+U)")
        self.underline_act.triggered.connect(self.set_underline)
        toolbar.addAction(self.underline_act)

        toolbar.addSeparator()

        # Renk Butonları
        color_act = QAction("🎨 Renk", self)
        color_act.setToolTip("Yazı Rengi Değiştir")
        color_act.triggered.connect(self.change_text_color)
        toolbar.addAction(color_act)

        highlight_act = QAction("🖍 Vurgu", self)
        highlight_act.setToolTip("Arka Plan Vurgu Rengi")
        highlight_act.triggered.connect(self.change_highlight_color)
        toolbar.addAction(highlight_act)

        toolbar.addSeparator()

        # Hizalama
        align_left = QAction("⯇ Sol", self)
        align_left.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft))
        toolbar.addAction(align_left)

        align_center = QAction("⯎ Orta", self)
        align_center.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter))
        toolbar.addAction(align_center)

        align_right = QAction("⯈ Sağ", self)
        align_right.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight))
        toolbar.addAction(align_right)

        align_justify = QAction("⯐ İki Yana", self)
        align_justify.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify))
        toolbar.addAction(align_justify)

        toolbar.addSeparator()

        # Listeler
        bullet_list_act = QAction("• Liste", self)
        bullet_list_act.triggered.connect(self.insert_bullet_list)
        toolbar.addAction(bullet_list_act)

        numbered_list_act = QAction("1. Liste", self)
        numbered_list_act.triggered.connect(self.insert_numbered_list)
        toolbar.addAction(numbered_list_act)

    def init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Hazır")
        self.status.addWidget(self.status_label)

    # --- BİÇİMLENDİRME METOTLARI ---
    def change_font_family(self, font: QFont):
        self.editor.setFontFamily(font.family())

    def change_font_size(self, size: int):
        self.editor.setFontPointSize(size)

    def set_bold(self):
        w = QFont.Weight.Bold if self.bold_act.isChecked() else QFont.Weight.Normal
        self.editor.setFontWeight(w)

    def set_italic(self):
        self.editor.setFontItalic(self.italic_act.isChecked())

    def set_underline(self):
        self.editor.setFontUnderline(self.underline_act.isChecked())

    def change_text_color(self):
        color = QColorDialog.getColor(self.editor.textColor(), self, "Metin Rengi Seçin")
        if color.isValid():
            self.editor.setTextColor(color)

    def change_highlight_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.yellow, self, "Vurgu Rengi Seçin")
        if color.isValid():
            self.editor.setTextBackgroundColor(color)

    def insert_bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def insert_numbered_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDecimal)

    def insert_table(self):
        rows, ok1 = QInputDialog.getInt(self, "Tablo Ekle", "Satır sayısı:", 3, 1, 50)
        if not ok1:
            return
        cols, ok2 = QInputDialog.getInt(self, "Tablo Ekle", "Sütun sayısı:", 3, 1, 20)
        if not ok2:
            return

        cursor = self.editor.textCursor()
        fmt = QTextTableFormat()
        fmt.setCellPadding(6)
        fmt.setCellSpacing(0)
        fmt.setBorder(1)
        cursor.insertTable(rows, cols, fmt)

    def insert_image(self):
        img_path, _ = QFileDialog.getOpenFileName(
            self, "Resim Seçin", "", "Görseller (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if img_path:
            cursor = self.editor.textCursor()
            cursor.insertHtml(f'<img src="{img_path}" max-width="100%"/>')

    # --- DOSYA VE KAYIT METOTLARI ---
    def file_new(self):
        if self.autosave.has_unsaved_changes:
            ans = QMessageBox.question(
                self, "Kaydedilmemiş Değişiklikler",
                "Mevcut belgede kaydedilmemiş değişiklikler var. Yeni belge açılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        self.editor.clear()
        self.current_file_path = None
        self.autosave.mark_clean()
        self.setWindowTitle("Nyebralti Word - Yeni Belge")
        self.status_label.setText("Yeni belge oluşturuldu.")

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Belge Aç", "", "Nyebralti Word (*.nyw *.html *.htm *.txt);;Tüm Dosyalar (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if path.endswith(".txt"):
                self.editor.setPlainText(content)
            else:
                self.editor.setHtml(content)

            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Word - {Path(path).name}")
            self.status_label.setText(f"Açıldı: {Path(path).name}")
            self.db.log_activity("word", "open", f"Dosya açıldı: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{e}")

    def file_save(self):
        if not self.current_file_path:
            self.file_save_as()
        else:
            self._save_to_path(self.current_file_path)

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Farklı Kaydet", "Belge.nyw",
            "Nyebralti Word Belgesi (*.nyw);;HTML Belgesi (*.html);;Düz Metin (*.txt)"
        )
        if path:
            self._save_to_path(path)

    def _save_to_path(self, path: str):
        try:
            content = self.editor.toPlainText() if path.endswith(".txt") else self.editor.toHtml()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Word - {Path(path).name}")
            self.status_label.setText(f"Kaydedildi: {Path(path).name}")
            self.db.log_activity("word", "save", f"Dosya kaydedildi: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{e}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "PDF Olarak Aktar", "Belge.pdf", "PDF Dosyası (*.pdf)")
        if not path:
            return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            self.editor.document().print(printer)
            self.status_label.setText(f"PDF aktarıldı: {Path(path).name}")
            self.db.log_activity("word", "export_pdf", f"PDF aktarıldı: {Path(path).name}")
            QMessageBox.information(self, "Başarılı", f"Belge başarıyla PDF olarak kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF aktarımı başarısız:\n{e}")

    def show_history(self):
        dlg = HistoryDialog(app_type="word", current_file=self.current_file_path, parent=self)
        if dlg.exec():
            restored = dlg.restored_snapshot_path
            if restored and os.path.exists(restored):
                try:
                    with open(restored, "r", encoding="utf-8") as f:
                        self.editor.setHtml(f.read())
                    self.autosave.mark_dirty()
                    self.status_label.setText(f"Sürüm geri yüklendi: {Path(restored).name}")
                    self.db.log_activity("word", "restore", f"Sürüm geri yüklendi: {Path(restored).name}")
                    QMessageBox.information(self, "Geri Yüklendi", "Seçilen önceki kayıt editöre yüklendi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Geri yükleme hatası:\n{e}")

    # --- OTOMATİK KAYIT İŞLEYİCİLERİ ---
    def _on_text_changed(self):
        self.autosave.mark_dirty()

    def _on_autosave_callback(self, snapshot_path: str) -> str:
        html = self.editor.toHtml()
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write(html)
        text = self.editor.toPlainText()
        words = len(text.split())
        return f"{words} kelime, {len(text)} karakter"

    def _on_autosave_complete(self, snapshot_path: str):
        filename = Path(snapshot_path).name
        self.status_label.setText(f"✓ Otomatik kayıt alındı ({filename})")
