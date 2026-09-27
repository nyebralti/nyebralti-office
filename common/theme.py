"""
Nyebralti Office - Modern Tema ve Stil Yöneticisi (QSS)
Fluent / Modern Dark & Light desteği
"""

DARK_THEME = """
QWidget {
    background-color: #1e1e24;
    color: #f0f0f5;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* Ana Pencere & Dialoglar */
QMainWindow, QDialog {
    background-color: #1e1e24;
}

/* Menü Çubuğu */
QMenuBar {
    background-color: #18181c;
    color: #e0e0e0;
    border-bottom: 1px solid #2d2d38;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #2b2b36;
}
QMenu {
    background-color: #24242e;
    color: #ffffff;
    border: 1px solid #3c3c4d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #3b82f6;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #3c3c4d;
    margin: 4px 8px;
}

/* Araç Çubuğu */
QToolBar {
    background-color: #252530;
    border-bottom: 1px solid #2e2e3d;
    spacing: 6px;
    padding: 4px 8px;
}
QToolButton {
    background-color: transparent;
    color: #f0f0f5;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 6px;
    font-weight: 500;
}
QToolButton:hover {
    background-color: #323242;
    border: 1px solid #45455a;
}
QToolButton:pressed, QToolButton:checked {
    background-color: #3b82f6;
    color: #ffffff;
    border: 1px solid #2563eb;
}

/* Butonlar */
QPushButton {
    background-color: #2e2e3d;
    color: #ffffff;
    border: 1px solid #434358;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3b3b4f;
    border-color: #555570;
}
QPushButton:pressed {
    background-color: #22222d;
}
QPushButton:disabled {
    background-color: #1a1a20;
    color: #666675;
    border-color: #282833;
}

/* Birincil Aksiyon Butonu */
QPushButton[primary="true"] {
    background-color: #2563eb;
    border-color: #1d4ed8;
    color: white;
    font-weight: 600;
}
QPushButton[primary="true"]:hover {
    background-color: #1d4ed8;
}

/* Metin Girişleri */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #282834;
    color: #ffffff;
    border: 1px solid #3e3e50;
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

/* Tablolar ve Listeler */
QTableWidget, QListWidget, QTreeWidget {
    background-color: #22222c;
    border: 1px solid #333342;
    border-radius: 6px;
    gridline-color: #2e2e3d;
    color: #f0f0f5;
    selection-background-color: #1e3a8a;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #1a1a22;
    color: #94a3b8;
    border: none;
    border-right: 1px solid #2e2e3d;
    border-bottom: 1px solid #2e2e3d;
    padding: 6px;
    font-weight: bold;
}
QTableCornerButton::section {
    background-color: #1a1a22;
    border: none;
}

/* Durum Çubuğu */
QStatusBar {
    background-color: #181820;
    color: #94a3b8;
    border-top: 1px solid #2b2b38;
}

/* ScrollBar */
QScrollBar:vertical {
    background-color: #1e1e24;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #404052;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background-color: #55556d;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #1e1e24;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #404052;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #55556d;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* İlerleme Çubuğu (ProgressBar) */
QProgressBar {
    background-color: #282834;
    border: 1px solid #3e3e50;
    border-radius: 6px;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 5px;
}
"""

def apply_theme(app, theme_name="dark"):
    """PyQt6 QApplication nesnesine tema uygular."""
    if theme_name == "dark":
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet("")
