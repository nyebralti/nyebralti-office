import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QFrame, QMessageBox, QFileDialog, QSplitter
)
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt, QSize

from common.paths import get_project_root, get_appdata_dir, get_db_path
from common.database import DatabaseManager

class HubWindow(QMainWindow):
    """Nyebralti Office - Merkezi Hub & Başlatıcı"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.username = os.environ.get("USERNAME", os.environ.get("USER", "Kullanıcı"))

        self.setWindowTitle("Nyebralti Office - Ana Kontrol Paneli")
        self.resize(1000, 680)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # 1. Üst Başlık ve Kullanıcı Bilgisi
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_label = QLabel("✨ Nyebralti Office")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        title_box.addWidget(title_label)

        sub_label = QLabel(f"Hoş geldiniz, {self.username}! Tüm ofis belgeleriniz ve geçmişiniz hazır.")
        sub_label.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(sub_label)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        db_path_label = QLabel(f"💾 Profil Veritabanı:\n{get_db_path()}")
        db_path_label.setStyleSheet("font-size: 11px; color: #64748b; background: #181820; padding: 6px 12px; border-radius: 6px;")
        header_layout.addWidget(db_path_label)

        main_layout.addLayout(header_layout)

        # 2. Hızlı Uygulama Kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        apps = [
            ("📝 Nyebralti Word", "Zengin metin düzenleyici ve belge yöneticisi", "#2563eb", "word"),
            ("📊 Nyebralti Excel", "Elektronik tablo, formül ve veri analizi", "#059669", "excel"),
            ("🎨 Nyebralti Paint", "Serbest çizim tuvali ve grafik düzenleme", "#d97706", "paint")
        ]

        for title, desc, color, app_id in apps:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #242430;
                    border: 1px solid #363645;
                    border-radius: 10px;
                    padding: 14px;
                }}
                QFrame:hover {{
                    border: 1px solid {color};
                    background-color: #2a2a38;
                }}
            """)
            c_layout = QVBoxLayout(card)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
            c_layout.addWidget(lbl_title)

            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("font-size: 12px; color: #94a3b8; margin-top: 4px; margin-bottom: 12px;")
            c_layout.addWidget(lbl_desc)

            btn_open = QPushButton("Uygulamayı Başlat")
            btn_open.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn_open.clicked.connect(lambda checked, a=app_id: self.launch_app(a))
            c_layout.addWidget(btn_open)

            cards_layout.addWidget(card)

        main_layout.addLayout(cards_layout)

        # 3. Sekmeler: Son Dosyalar / Otomatik Kayıtlar / İşlem Günlüğü
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #363645;
                background: #20202a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #282836;
                color: #94a3b8;
                padding: 8px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
                font-weight: bold;
            }
        """)

        # Sekme 1: Son Dosyalar
        tab_recent = QWidget()
        tr_layout = QVBoxLayout(tab_recent)
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.open_recent_item)
        tr_layout.addWidget(self.recent_list)

        r_btn_layout = QHBoxLayout()
        btn_open_recent = QPushButton("Seçili Dosyayı Aç")
        btn_open_recent.setProperty("primary", True)
        btn_open_recent.clicked.connect(lambda: self.open_recent_item(self.recent_list.currentItem()))
        r_btn_layout.addWidget(btn_open_recent)

        btn_refresh = QPushButton("Yenile")
        btn_refresh.clicked.connect(self.load_data)
        r_btn_layout.addWidget(btn_refresh)
        r_btn_layout.addStretch()
        tr_layout.addLayout(r_btn_layout)

        tabs.addTab(tab_recent, "📂 Son Çalışılan Dosyalar")

        # Sekme 2: Otomatik Kayıtlar (Autosaves)
        tab_autosaves = QWidget()
        ta_layout = QVBoxLayout(tab_autosaves)
        self.autosave_list = QListWidget()
        self.autosave_list.itemDoubleClicked.connect(self.open_autosave_item)
        ta_layout.addWidget(self.autosave_list)

        a_btn_layout = QHBoxLayout()
        btn_open_auto = QPushButton("Yedeği Aç")
        btn_open_auto.setProperty("primary", True)
        btn_open_auto.clicked.connect(lambda: self.open_autosave_item(self.autosave_list.currentItem()))
        a_btn_layout.addWidget(btn_open_auto)
        a_btn_layout.addStretch()
        ta_layout.addLayout(a_btn_layout)

        tabs.addTab(tab_autosaves, "⏱️ Otomatik Kayıt Geçmişi")

        # Sekme 3: İşlem Geçmişi (Activity Logs)
        tab_logs = QWidget()
        tl_layout = QVBoxLayout(tab_logs)
        self.activity_list = QListWidget()
        tl_layout.addWidget(self.activity_list)
        tabs.addTab(tab_logs, "📋 İşlem ve Hareket Günlüğü")

        main_layout.addWidget(tabs)
        self.setCentralWidget(central_widget)

    def load_data(self):
        # 1. Son Dosyalar
        self.recent_list.clear()
        recent_files = self.db.get_recent_files(limit=40)
        for rf in recent_files:
            app_icon = "📝" if rf['app_type'] == "word" else ("📊" if rf['app_type'] == "excel" else "🎨")
            text = f"{app_icon} {rf['file_name']}  -  Yol: {rf['file_path']}  ({rf['last_opened_at']})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, rf)
            self.recent_list.addItem(item)

        if not recent_files:
            self.recent_list.addItem(QListWidgetItem("Henüz açılmış son dosya bulunmuyor."))

        # 2. Otomatik Kayıtlar
        self.autosave_list.clear()
        autosaves = self.db.get_autosaves(limit=40)
        for auto in autosaves:
            app_icon = "📝" if auto['app_type'] == "word" else ("📊" if auto['app_type'] == "excel" else "🎨")
            text = f"{app_icon} {auto['created_at']}  -  {auto['summary']}  (Snapshot: {Path(auto['snapshot_path']).name})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, auto)
            self.autosave_list.addItem(item)

        if not autosaves:
            self.autosave_list.addItem(QListWidgetItem("Henüz otomatik kayıt bulunmuyor."))

        # 3. Hareketler
        self.activity_list.clear()
        acts = self.db.get_activities(limit=50)
        for act in acts:
            text = f"[{act['timestamp']}] ({act['app_type'].upper()}) {act['action_type']}: {act['details']}"
            self.activity_list.addItem(QListWidgetItem(text))

        if not acts:
            self.activity_list.addItem(QListWidgetItem("Henüz işlem kaydı bulunmuyor."))

    def launch_app(self, app_id: str, file_arg: str = None):
        """Ofis uygulamasını bağımsız bir alt süreç (subprocess) olarak başlatır (exe veya python)."""
        exe_names = {
            "word": "NyebraltiWord.exe",
            "excel": "NyebraltiExcel.exe",
            "paint": "NyebraltiPaint.exe",
        }
        script_map = {
            "word": root_dir / "apps" / "word" / "main.py",
            "excel": root_dir / "apps" / "excel" / "main.py",
            "paint": root_dir / "apps" / "paint" / "main.py",
        }

        # 1. Önce exe olup olmadığını kontrol et (kurulu dizin, yerel klasör veya apps altı)
        exe_name = exe_names.get(app_id)
        current_dir = Path(__file__).resolve().parent
        possible_exe_paths = [
            current_dir / exe_name,
            current_dir.parent / app_id / exe_name,
            root_dir / "apps" / app_id / exe_name,
            root_dir / exe_name,
            Path(sys.executable).parent / exe_name
        ]

        target_cmd = None
        for p in possible_exe_paths:
            if p.exists():
                target_cmd = [str(p)]
                break

        # 2. Exe bulunamadıysa Python scripti üzerinden başlat
        if not target_cmd:
            target_script = script_map.get(app_id)
            if target_script and target_script.exists():
                target_cmd = [sys.executable, str(target_script)]

        if not target_cmd:
            QMessageBox.critical(self, "Hata", f"'{app_id}' uygulaması bulunamadı.")
            return

        if file_arg:
            target_cmd.append(file_arg)

        try:
            subprocess.Popen(target_cmd)
            self.db.log_activity("launcher", "launch", f"{app_id} başlatıldı. Komut: {target_cmd[0]}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uygulama başlatılamadı:\n{e}")

    def open_recent_item(self, item: QListWidgetItem):
        if not item:
            return
        rf = item.data(Qt.ItemDataRole.UserRole)
        if not rf:
            return
        path = rf['file_path']
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bulunamadı", f"Dosya mevcut konumunda bulunamadı:\n{path}")
            return
        self.launch_app(rf['app_type'], path)

    def open_autosave_item(self, item: QListWidgetItem):
        if not item:
            return
        auto = item.data(Qt.ItemDataRole.UserRole)
        if not auto:
            return
        path = auto['snapshot_path']
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bulunamadı", f"Yedek dosya bulunamadı:\n{path}")
            return
        self.launch_app(auto['app_type'], path)
