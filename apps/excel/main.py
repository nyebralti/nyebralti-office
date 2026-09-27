import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import QApplication
from apps.excel.spreadsheet_window import SpreadsheetWindow
from common.theme import apply_theme

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nyebralti Excel")
    apply_theme(app, "dark")

    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    window = SpreadsheetWindow(file_path=file_arg)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
