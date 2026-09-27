import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import QApplication
from installer.setup_wizard import SetupWizard
from common.theme import apply_theme

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nyebralti Office Kurulum")
    apply_theme(app, "dark")

    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
