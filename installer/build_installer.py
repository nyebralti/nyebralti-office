import os
import sys
import subprocess
from pathlib import Path

def build():
    root_dir = Path(__file__).resolve().parent.parent
    installer_script = root_dir / "installer" / "setup_main.py"
    apps_json = root_dir / "apps.json"

    print("=== Nyebralti Office Setup Derleme Başlatılıyor ===")
    print(f"Kök Dizin: {root_dir}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NyebraltiSetup",
        "--onefile",
        "--noconsole",
        f"--add-data={apps_json};.",
        f"--add-data={root_dir / 'common'};common",
        f"--add-data={root_dir / 'apps'};apps",
        str(installer_script)
    ]

    print(f"Çalıştırılan komut: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(root_dir), check=True)
    print("\n✅ Derleme tamamlandı! 'dist/NyebraltiSetup.exe' oluşturuldu.")

if __name__ == "__main__":
    build()
