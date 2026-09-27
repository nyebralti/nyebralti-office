import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def show_help():
    print("""
==================================================
Nyebralti Office - Hızlı Başlatıcı (Quick Runner)
==================================================
Kullanım:
  python run.py [modül]

Modüller:
  hub       : Merkezi Ofis Kontrol Paneli (Varsayılan)
  word      : Nyebralti Word Zengin Metin Düzenleyici
  excel     : Nyebralti Excel Tablo ve Formül Uygulaması
  paint     : Nyebralti Paint Çizim ve Görsel Düzenleyici
  setup     : Nyebralti Office Kurulum Sihirbazı
  build     : Setup'ı PyInstaller ile .exe olarak derler
==================================================
    """)

def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "hub"

    if arg in ["hub", "launcher"]:
        from apps.launcher.main import main as run_hub
        run_hub()
    elif arg == "word":
        from apps.word.main import main as run_word
        run_word()
    elif arg == "excel":
        from apps.excel.main import main as run_excel
        run_excel()
    elif arg == "paint":
        from apps.paint.main import main as run_paint
        run_paint()
    elif arg in ["setup", "installer"]:
        from installer.setup_main import main as run_setup
        run_setup()
    elif arg in ["build", "compile"]:
        from installer.build_installer import build
        build()
    else:
        show_help()

if __name__ == "__main__":
    main()
