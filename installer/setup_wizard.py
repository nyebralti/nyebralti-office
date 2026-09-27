import sys
import os
import shutil
import subprocess
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QListWidget, QListWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from common.paths import get_default_install_dir, get_appdata_dir, get_db_path, get_project_root
from common.database import DatabaseManager
from installer.github_client import GitHubClient
from installer.shortcut_creator import create_windows_shortcut, get_desktop_dir, get_start_menu_dir

class InstallWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, target_dir: str, selected_apps: list, manifest: dict):
        super().__init__()
        self.target_dir = Path(target_dir)
        self.selected_apps = selected_apps
        self.manifest = manifest

    def run(self):
        try:
            self.progress_changed.emit(5, "Hedef kurulum dizini oluşturuluyor...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            proj_root = get_project_root()
            total_steps = len(self.selected_apps) + 3
            current_step = 0

            # 1. Ortak (common) modülleri kopyala
            self.progress_changed.emit(15, "Ortak kütüphaneler kopyalanıyor (common)...")
            common_src = proj_root / "common"
            common_dest = self.target_dir / "common"
            if common_src.exists():
                if common_dest.exists():
                    shutil.rmtree(common_dest)
                shutil.copytree(common_src, common_dest)

            # apps.json'ı hedef dizine kopyala
            shutil.copy2(proj_root / "apps.json", self.target_dir / "apps.json")

            # 2. Seçilen uygulamaları kopyala/kur
            step_inc = 60 / max(1, len(self.selected_apps))
            current_pct = 20

            for app_meta in self.selected_apps:
                app_folder = app_meta["folder"]
                app_name = app_meta["name"]
                self.progress_changed.emit(int(current_pct), f"Yükleniyor: {app_name}...")

                app_src = proj_root / "apps" / app_folder
                app_dest = self.target_dir / "apps" / app_folder
                if app_src.exists():
                    if app_dest.exists():
                        shutil.rmtree(app_dest)
                    shutil.copytree(app_src, app_dest)

                current_pct += step_inc

            # 3. Roaming Veritabanını Başlat (%APPDATA%\Nyebralti Office\office.db)
            self.progress_changed.emit(85, "Kullanıcı profili ve veritabanı (%APPDATA%) hazırlanıyor...")
            db = DatabaseManager()
            db.log_activity("installer", "setup", f"Nyebralti Office kuruldu. Dizin: {self.target_dir}")

            # 4. Masaüstü ve Başlat Menüsü Kısayolları Oluştur
            self.progress_changed.emit(92, "Masaüstü ve Başlat menüsü kısayolları oluşturuluyor...")
            launcher_entry = self.target_dir / "apps" / "launcher" / "main.py"
            python_exe = sys.executable

            desktop_lnk = get_desktop_dir() / "Nyebralti Office.lnk"
            start_menu_lnk = get_start_menu_dir() / "Nyebralti Office.lnk"

            # Launcher kısayolu oluştur (pythonw veya python ile başlatıcı)
            create_windows_shortcut(
                target_path=python_exe,
                shortcut_path=str(desktop_lnk),
                description="Nyebralti Office Suite",
                working_dir=str(self.target_dir),
            )
            create_windows_shortcut(
                target_path=python_exe,
                shortcut_path=str(start_menu_lnk),
                description="Nyebralti Office Suite",
                working_dir=str(self.target_dir),
            )

            self.progress_changed.emit(100, "Kurulum başarıyla tamamlandı!")
            self.finished_signal.emit(True, "Kurulum tamamlandı.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class SetupWizard(QWizard):
    """Nyebralti Office Kurulum Sihirbazı (Setup Wizard)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nyebralti Office Kurulum Sihirbazı")
        self.resize(720, 520)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Veri depoları
        self.github_client = GitHubClient()
        self.manifest = self.github_client.fetch_apps_manifest()
        self.target_install_dir = str(get_default_install_dir())
        self.selected_apps = []

        # Sayfaları Ekle
        self.page_welcome = WelcomePage(self.manifest)
        self.page_dir = DirectoryPage(self.target_install_dir)
        self.page_components = ComponentsPage(self.manifest)
        self.page_install = ProgressPage(self)
        self.page_finish = FinishPage()

        self.addPage(self.page_welcome)
        self.addPage(self.page_dir)
        self.addPage(self.page_components)
        self.addPage(self.page_install)
        self.addPage(self.page_finish)

class WelcomePage(QWizardPage):
    def __init__(self, manifest: dict):
        super().__init__()
        self.setTitle("Nyebralti Office Suite Kurulumuna Hoş Geldiniz")
        self.setSubTitle("Bu sihirbaz, Nyebralti Office paketini bilgisayarınıza kuracaktır.")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        info = QLabel(
            "<b>Nyebralti Office</b> modern, hızlı ve çok kullanıcılı bir masaüstü ofis paketidir.<br><br>"
            "Paket İçeriği:<br>"
            "• <b>Nyebralti Word:</b> Gelişmiş zengin metin düzenleme ve PDF dışa aktarma<br>"
            "• <b>Nyebralti Excel:</b> Elektronik tablo, formül hesaplama ve veri analizi<br>"
            "• <b>Nyebralti Paint:</b> Tuval çizimi, şekil ve görsel düzenleme araçları<br>"
            "• <b>Nyebralti Hub:</b> Tüm uygulamalar ve son dosyalar için merkezi başlatıcı<br><br>"
            f"<b>Resmi GitHub Deposu:</b> <a style='color: #3b82f6;' href='{manifest.get('repository')}'>{manifest.get('repository')}</a>"
        )
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)
        layout.addWidget(info)

        layout.addStretch()

class DirectoryPage(QWizardPage):
    def __init__(self, default_dir: str):
        super().__init__()
        self.setTitle("Kurulum Dizinini Seçin")
        self.setSubTitle("Nyebralti Office'in kurulacağı klasörü belirleyin.")

        layout = QVBoxLayout(self)

        lbl = QLabel("Kurulum Yeri (Varsayılan: C:\\Program Files\\Nyebralti Office):")
        layout.addWidget(lbl)

        dir_box = QHBoxLayout()
        self.dir_input = QLineEdit(default_dir)
        dir_box.addWidget(self.dir_input)

        browse_btn = QPushButton("Gözat...")
        browse_btn.clicked.connect(self.browse_dir)
        dir_box.addWidget(browse_btn)

        layout.addLayout(dir_box)

        notice = QLabel(
            "💡 Not: Eğer Program Files için yönetici yetkisi vermeden kurmak isterseniz "
            "kullanıcı dizininizde herhangi bir klasör seçebilirsiniz."
        )
        notice.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 10px;")
        notice.setWordWrap(True)
        layout.addWidget(notice)

        layout.addStretch()

    def browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Kurulum Klasörü Seç", self.dir_input.text())
        if folder:
            self.dir_input.setText(os.path.join(folder, "Nyebralti Office"))

    def validatePage(self):
        target = self.dir_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir kurulum yolu girin.")
            return False
        self.wizard().target_install_dir = target
        return True

class ComponentsPage(QWizardPage):
    def __init__(self, manifest: dict):
        super().__init__()
        self.setTitle("Bileşenleri Seçin")
        self.setSubTitle("Kurmak istediğiniz uygulamaları işaretleyin. apps.json tarafından zorunlu kılınanlar kilitlidir.")

        self.manifest = manifest
        self.checkboxes = {}

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)

        self.desc_box = QTextEdit()
        self.desc_box.setReadOnly(True)
        self.desc_box.setMaximumHeight(80)
        self.desc_box.setPlaceholderText("Açıklamayı görmek için bir bileşene tıklayın...")
        layout.addWidget(self.desc_box)

        self.load_components()

    def load_components(self):
        for app in self.manifest.get("apps", []):
            item = QListWidgetItem(self.list_widget)
            cb = QCheckBox(f"{app['name']} {'(Zorunlu)' if app.get('mandatory') else ''}")

            if app.get("mandatory"):
                cb.setChecked(True)
                cb.setEnabled(False) # Zorunlu olan kaldırılamaz
            else:
                cb.setChecked(True) # Varsayılan olarak seçili

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, cb)
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.checkboxes[app['id']] = (cb, app)

    def on_selection_changed(self):
        curr = self.list_widget.currentItem()
        if curr:
            app = curr.data(Qt.ItemDataRole.UserRole)
            if app:
                status = "Zorunlu Bileşen" if app.get("mandatory") else "İsteğe Bağlı Bileşen"
                self.desc_box.setText(f"[{status}]\n{app.get('description', '')}")

    def validatePage(self):
        selected = []
        for app_id, (cb, app) in self.checkboxes.items():
            if cb.isChecked():
                selected.append(app)
        self.wizard().selected_apps = selected
        return True

class ProgressPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard_ref = wizard
        self.setTitle("Kuruluyor")
        self.setSubTitle("Nyebralti Office bileşenleri indiriliyor ve yapılandırılıyor...")

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Hazırlanıyor...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        self.is_completed = False

    def initializePage(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

        self.worker = InstallWorker(
            target_dir=self.wizard_ref.target_install_dir,
            selected_apps=self.wizard_ref.selected_apps,
            manifest=self.wizard_ref.manifest
        )
        self.worker.progress_changed.connect(self.on_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def on_finished(self, success: bool, msg: str):
        if success:
            self.is_completed = True
            self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)
            self.wizard().next()
        else:
            QMessageBox.critical(self, "Kurulum Hatası", f"Kurulum sırasında bir hata oluştu:\n{msg}")

    def isComplete(self):
        return self.is_completed

class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Kurulum Tamamlandı!")
        self.setSubTitle("Nyebralti Office başarıyla bilgisayarınıza kuruldu.")

        layout = QVBoxLayout(self)

        lbl = QLabel(
            "🎉 Tebrikler! Nyebralti Office kurulumu tamamlandı.<br><br>"
            "• Masaüstü ve Başlat Menünüze kısayollar eklendi.<br>"
            "• Her kullanıcının önceki kayıtları ve veritabanı <code>%APPDATA%\\Nyebralti Office\\office.db</code> yolunda bağımsız olarak tutulacaktır."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.launch_checkbox = QCheckBox("Nyebralti Office Hub'ı Şimdi Başlat")
        self.launch_checkbox.setChecked(True)
        layout.addWidget(self.launch_checkbox)

        layout.addStretch()

    def validatePage(self):
        if self.launch_checkbox.isChecked():
            launcher_script = Path(self.wizard().target_install_dir) / "apps" / "launcher" / "main.py"
            if launcher_script.exists():
                subprocess.Popen([sys.executable, str(launcher_script)])
        return True
