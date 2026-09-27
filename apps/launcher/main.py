import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import QApplication
from apps.launcher.hub_window import HubWindow
from common.theme import apply_theme

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nyebralti Office Hub")
    apply_theme(app, "dark")

    window = HubWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
