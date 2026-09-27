import sys
import os
import json
import csv
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QToolBar, QLineEdit, QLabel, QHBoxLayout,
    QVBoxLayout, QWidget, QColorDialog, QStatusBar
)
from PyQt6.QtGui import QAction, QFont, QColor
from PyQt6.QtCore import Qt

from common.database import DatabaseManager
from common.autosave_engine import AutosaveEngine
from common.history_dialog import HistoryDialog
from apps.excel.formula_engine import FormulaEngine, index_to_col_letter, col_letter_to_index

class SpreadsheetWindow(QMainWindow):
    """Nyebralti Excel - Elektronik Tablo ve Hesaplama Uygulaması"""

    def __init__(self, file_path: str = None):
        super().__init__()
        self.current_file_path = file_path
        self.db = DatabaseManager()
        self.formula_engine = FormulaEngine(self.get_cell_evaluated_value)
        self.updating_cells = False

        self.setWindowTitle("Nyebralti Excel - Yeni Tablo")
        self.resize(1100, 750)

        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()

        # Otomatik Kayıt Motoru
        self.autosave = AutosaveEngine(app_type="excel", parent=self, interval_seconds=45)
        self.autosave.set_save_callback(self._on_autosave_callback)
        self.autosave.autosaved.connect(self._on_autosave_complete)

        if file_path and os.path.exists(file_path):
            self.load_file(file_path)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Üst Formül Çubuğu (Formula Bar)
        f_layout = QHBoxLayout()
        self.cell_coord_label = QLabel("A1")
        self.cell_coord_label.setFixedWidth(50)
        self.cell_coord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cell_coord_label.setStyleSheet("font-weight: bold; background: #282834; padding: 4px; border: 1px solid #3e3e50; border-radius: 4px;")
        f_layout.addWidget(self.cell_coord_label)

        fx_label = QLabel("fx")
        fx_label.setStyleSheet("font-weight: bold; font-style: italic; color: #3b82f6; font-size: 14px;")
        f_layout.addWidget(fx_label)

        self.formula_bar = QLineEdit()
        self.formula_bar.setPlaceholderText("Formül veya değer girin... (Örn: =SUM(A1:A10) veya =A1*2)")
        self.formula_bar.returnPressed.connect(self.on_formula_bar_entered)
        f_layout.addWidget(self.formula_bar)

        main_layout.addLayout(f_layout)

        # Tablo Izgarası (Grid)
        self.table = QTableWidget(60, 26)
        # Sütun başlıklarını A-Z yap
        headers = [index_to_col_letter(i) for i in range(26)]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.currentCellChanged.connect(self.on_cell_selection_changed)
        self.table.itemChanged.connect(self.on_cell_value_changed)

        main_layout.addWidget(self.table)
        self.setCentralWidget(central_widget)

    def init_menus(self):
        menubar = self.menuBar()

        # DOSYA
        file_menu = menubar.addMenu("Dosya")

        new_act = QAction("Yeni Tablo", self)
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

        export_csv_act = QAction("📊 CSV Olarak Dışa Aktar...", self)
        export_csv_act.triggered.connect(self.export_csv)
        file_menu.addAction(export_csv_act)

        exit_act = QAction("Çıkış", self)
        exit_act.setShortcut("Alt+F4")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # TABLO / SATIR-SÜTUN MENÜSÜ
        table_menu = menubar.addMenu("Tablo")

        add_row_act = QAction("Satır Ekle", self)
        add_row_act.triggered.connect(self.add_row)
        table_menu.addAction(add_row_act)

        add_col_act = QAction("Sütun Ekle", self)
        add_col_act.triggered.connect(self.add_col)
        table_menu.addAction(add_col_act)

        del_row_act = QAction("Seçili Satırı Sil", self)
        del_row_act.triggered.connect(self.del_row)
        table_menu.addAction(del_row_act)

        del_col_act = QAction("Seçili Sütunu Sil", self)
        del_col_act.triggered.connect(self.del_col)
        table_menu.addAction(del_col_act)

    def init_toolbar(self):
        toolbar = QToolBar("Elektronik Tablo Araçları")
        self.addToolBar(toolbar)

        # Kalın
        bold_act = QAction("B", self)
        bold_act.setToolTip("Kalın Yazı")
        bold_act.triggered.connect(self.toggle_bold)
        toolbar.addAction(bold_act)

        # İtalik
        italic_act = QAction("I", self)
        italic_act.setToolTip("İtalik Yazı")
        italic_act.triggered.connect(self.toggle_italic)
        toolbar.addAction(italic_act)

        toolbar.addSeparator()

        # Renkler
        text_color_act = QAction("🎨 Yazı Rengi", self)
        text_color_act.triggered.connect(self.change_text_color)
        toolbar.addAction(text_color_act)

        bg_color_act = QAction("🪣 Dolgu Rengi", self)
        bg_color_act.triggered.connect(self.change_bg_color)
        toolbar.addAction(bg_color_act)

        toolbar.addSeparator()

        # Hizalama
        align_left = QAction("⯇ Sol", self)
        align_left.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        toolbar.addAction(align_left)

        align_center = QAction("⯎ Orta", self)
        align_center.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        toolbar.addAction(align_center)

        align_right = QAction("⯈ Sağ", self)
        align_right.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        toolbar.addAction(align_right)

        toolbar.addSeparator()

        recalc_act = QAction("🔄 Yeniden Hesapla", self)
        recalc_act.triggered.connect(self.recalculate_all)
        toolbar.addAction(recalc_act)

    def init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Hazır")
        self.status.addWidget(self.status_label)

    # --- HÜCRE VE FORMÜL İŞLEMLERİ ---
    def get_cell_raw(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        if not item:
            return ""
        raw = item.data(Qt.ItemDataRole.UserRole)
        return str(raw) if raw is not None else item.text()

    def get_cell_evaluated_value(self, row: int, col: int) -> Any:
        raw = self.get_cell_raw(row, col)
        if raw.startswith("="):
            return self.formula_engine.evaluate(raw)
        return raw

    def on_cell_selection_changed(self, row: int, col: int):
        if row < 0 or col < 0:
            return
        col_name = index_to_col_letter(col)
        self.cell_coord_label.setText(f"{col_name}{row + 1}")

        item = self.table.item(row, col)
        if item:
            raw = item.data(Qt.ItemDataRole.UserRole)
            self.formula_bar.setText(str(raw) if raw is not None else item.text())
        else:
            self.formula_bar.setText("")

    def on_formula_bar_entered(self):
        row = self.table.currentRow()
        col = self.table.currentColumn()
        if row < 0 or col < 0:
            return

        text = self.formula_bar.text().strip()
        self.set_cell_content(row, col, text)
        self.recalculate_all()

    def on_cell_value_changed(self, item: QTableWidgetItem):
        if self.updating_cells:
            return
        self.autosave.mark_dirty()

    def set_cell_content(self, row: int, col: int, text: str):
        self.updating_cells = True
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)

        item.setData(Qt.ItemDataRole.UserRole, text)

        if text.startswith("="):
            res = self.formula_engine.evaluate(text)
            item.setText(str(res))
        else:
            item.setText(text)

        self.updating_cells = False
        self.autosave.mark_dirty()

    def recalculate_all(self):
        self.updating_cells = True
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    raw = item.data(Qt.ItemDataRole.UserRole)
                    if raw and str(raw).startswith("="):
                        val = self.formula_engine.evaluate(str(raw))
                        item.setText(str(val))
        self.updating_cells = False

    # --- BİÇİMLENDİRME ---
    def toggle_bold(self):
        items = self.table.selectedItems()
        for item in items:
            f = item.font()
            f.setBold(not f.bold())
            item.setFont(f)
        self.autosave.mark_dirty()

    def toggle_italic(self):
        items = self.table.selectedItems()
        for item in items:
            f = item.font()
            f.setItalic(not f.italic())
            item.setFont(f)
        self.autosave.mark_dirty()

    def change_text_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Hücre Yazı Rengi")
        if color.isValid():
            for item in self.table.selectedItems():
                item.setForeground(color)
            self.autosave.mark_dirty()

    def change_bg_color(self):
        color = QColorDialog.getColor(QColor("#2563eb"), self, "Hücre Dolgu Rengi")
        if color.isValid():
            for item in self.table.selectedItems():
                item.setBackground(color)
            self.autosave.mark_dirty()

    def set_alignment(self, align):
        for item in self.table.selectedItems():
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        self.autosave.mark_dirty()

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.autosave.mark_dirty()

    def add_col(self):
        c = self.table.columnCount()
        self.table.insertColumn(c)
        self.table.setHorizontalHeaderItem(c, QTableWidgetItem(index_to_col_letter(c)))
        self.autosave.mark_dirty()

    def del_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.autosave.mark_dirty()

    def del_col(self):
        c = self.table.currentColumn()
        if c >= 0:
            self.table.removeColumn(c)
            # Sütun başlıklarını yeniden güncelle
            for i in range(self.table.columnCount()):
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(index_to_col_letter(i)))
            self.autosave.mark_dirty()

    # --- DOSYA VE KAYIT ---
    def file_new(self):
        self.table.clearContents()
        self.current_file_path = None
        self.autosave.mark_clean()
        self.setWindowTitle("Nyebralti Excel - Yeni Tablo")
        self.status_label.setText("Yeni tablo oluşturuldu.")

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Tablo Aç", "", "Nyebralti Tablo (*.nyx);;CSV Dosyası (*.csv);;Tüm Dosyalar (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        try:
            self.updating_cells = True
            if path.endswith(".csv"):
                with open(path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    self.table.clearContents()
                    for r, row in enumerate(reader):
                        if r >= self.table.rowCount():
                            self.table.insertRow(r)
                        for c, val in enumerate(row):
                            if c >= self.table.columnCount():
                                self.add_col()
                            item = QTableWidgetItem(val)
                            self.table.setItem(r, c, item)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.table.clearContents()
                rows = data.get("rows", 60)
                cols = data.get("cols", 26)
                self.table.setRowCount(rows)
                self.table.setColumnCount(cols)
                for i in range(cols):
                    self.table.setHorizontalHeaderItem(i, QTableWidgetItem(index_to_col_letter(i)))

                for key, cdata in data.get("cells", {}).items():
                    r, c = [int(x) for x in key.split(",")]
                    item = QTableWidgetItem()
                    raw = cdata.get("raw", "")
                    item.setData(Qt.ItemDataRole.UserRole, raw)
                    item.setText(str(cdata.get("val", raw)))
                    if cdata.get("bold"):
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                    if cdata.get("bg"):
                        item.setBackground(QColor(cdata["bg"]))
                    if cdata.get("fg"):
                        item.setForeground(QColor(cdata["fg"]))
                    self.table.setItem(r, c, item)

            self.updating_cells = False
            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Excel - {Path(path).name}")
            self.status_label.setText(f"Açıldı: {Path(path).name}")
            self.db.log_activity("excel", "open", f"Tablo açıldı: {Path(path).name}")
            self.recalculate_all()
        except Exception as e:
            self.updating_cells = False
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı:\n{e}")

    def file_save(self):
        if not self.current_file_path:
            self.file_save_as()
        else:
            self._save_to_path(self.current_file_path)

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Farklı Kaydet", "Tablo.nyx",
            "Nyebralti Tablo (*.nyx);;CSV Dosyası (*.csv)"
        )
        if path:
            self._save_to_path(path)

    def _save_to_path(self, path: str):
        try:
            if path.endswith(".csv"):
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    for r in range(self.table.rowCount()):
                        row_vals = []
                        for c in range(self.table.columnCount()):
                            it = self.table.item(r, c)
                            row_vals.append(it.text() if it else "")
                        writer.writerow(row_vals)
            else:
                data = self._serialize_data()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            self.current_file_path = path
            self.autosave.mark_clean(path)
            self.setWindowTitle(f"Nyebralti Excel - {Path(path).name}")
            self.status_label.setText(f"Kaydedildi: {Path(path).name}")
            self.db.log_activity("excel", "save", f"Tablo kaydedildi: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tablo kaydedilemedi:\n{e}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "CSV Dışa Aktar", "Tablo.csv", "CSV Dosyası (*.csv)")
        if path:
            self._save_to_path(path)
            QMessageBox.information(self, "Başarılı", f"CSV başarıyla aktarıldı:\n{path}")

    def show_history(self):
        dlg = HistoryDialog(app_type="excel", current_file=self.current_file_path, parent=self)
        if dlg.exec():
            restored = dlg.restored_snapshot_path
            if restored and os.path.exists(restored):
                self.load_file(restored)
                self.autosave.mark_dirty()
                self.status_label.setText(f"Sürüm geri yüklendi: {Path(restored).name}")
                self.db.log_activity("excel", "restore", f"Sürüm geri yüklendi: {Path(restored).name}")

    def _serialize_data(self) -> dict:
        cells = {}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                if it and (it.text() or it.data(Qt.ItemDataRole.UserRole)):
                    raw = it.data(Qt.ItemDataRole.UserRole)
                    bg = it.background().color().name() if it.background().color().isValid() else None
                    fg = it.foreground().color().name() if it.foreground().color().isValid() else None
                    cells[f"{r},{c}"] = {
                        "raw": str(raw) if raw is not None else it.text(),
                        "val": it.text(),
                        "bold": it.font().bold(),
                        "bg": bg,
                        "fg": fg
                    }
        return {
            "rows": self.table.rowCount(),
            "cols": self.table.columnCount(),
            "cells": cells
        }

    def _on_autosave_callback(self, snapshot_path: str) -> str:
        data = self._serialize_data()
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        cell_count = len(data.get("cells", {}))
        return f"{cell_count} dolu hücre"

    def _on_autosave_complete(self, snapshot_path: str):
        name = Path(snapshot_path).name
        self.status_label.setText(f"✓ Otomatik kayıt alındı ({name})")
