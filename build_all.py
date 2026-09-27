import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

# Windows console encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
FINAL_DIR = ROOT_DIR / "final"
GITHUB_DIR = FINAL_DIR / "github"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

APPS_TO_BUILD = [
    {
        "name": "NyebraltiWord",
        "entry": ROOT_DIR / "apps" / "word" / "main.py",
        "zip_name": "word.zip"
    },
    {
        "name": "NyebraltiExcel",
        "entry": ROOT_DIR / "apps" / "excel" / "main.py",
        "zip_name": "excel.zip"
    },
    {
        "name": "NyebraltiPaint",
        "entry": ROOT_DIR / "apps" / "paint" / "main.py",
        "zip_name": "paint.zip"
    },
    {
        "name": "NyebraltiLauncher",
        "entry": ROOT_DIR / "apps" / "launcher" / "main.py",
        "zip_name": "launcher.zip"
    },
    {
        "name": "NyebraltiSetup",
        "entry": ROOT_DIR / "installer" / "setup_main.py",
        "is_setup": True
    }
]

def run_pyinstaller(name: str, entry_point: Path, is_setup: bool = False):
    print(f"\n==========================================")
    print(f"[*] Derleniyor: {name} ({entry_point})")
    print(f"==========================================")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={name}",
        "--onefile",
        "--noconsole",
        "--clean",
        "--paths=.",
        f"--add-data={ROOT_DIR / 'common'};common"
    ]

    if is_setup:
        cmd.extend([
            f"--add-data={ROOT_DIR / 'apps.json'};.",
            f"--add-data={ROOT_DIR / 'apps'};apps",
            f"--add-data={ROOT_DIR / 'installer'};installer"
        ])
    else:
        cmd.extend([
            f"--add-data={ROOT_DIR / 'apps'};apps"
        ])

    cmd.append(str(entry_point))

    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    print(f"[OK] {name}.exe basariyla uretildi.")

def package_and_distribute():
    print(f"\n==========================================")
    print(f"[*] Final ve GitHub Dagitim Klasorleri Hazirlaniyor...")
    print(f"==========================================")

    # Klasörleri oluştur
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    GITHUB_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Setup dosyasını (NyebraltiSetup.exe) final klasörüne (github klasörünün yanına) koy
    setup_exe = DIST_DIR / "NyebraltiSetup.exe"
    if setup_exe.exists():
        target_setup = FINAL_DIR / "NyebraltiSetup.exe"
        shutil.copy2(setup_exe, target_setup)
        print(f"[+] Setup dosyasi yerlestirildi: {target_setup}")
    else:
        print(f"[!] Uyari: {setup_exe} bulunamadi!")

    # 2. apps.json dosyasını final/github klasörüne koy
    apps_json = ROOT_DIR / "apps.json"
    if apps_json.exists():
        shutil.copy2(apps_json, GITHUB_DIR / "apps.json")
        print(f"[+] apps.json GitHub klasorune kopyalandi.")

    # 3. Her uygulama için hem .exe hem de .zip arşivini final/github klasörüne ekle
    for app in APPS_TO_BUILD:
        if app.get("is_setup"):
            continue

        exe_path = DIST_DIR / f"{app['name']}.exe"
        if exe_path.exists():
            # Exe'yi github klasörüne kopyala
            shutil.copy2(exe_path, GITHUB_DIR / f"{app['name']}.exe")

            # Zip arşivini oluştur
            zip_target = GITHUB_DIR / app["zip_name"]
            with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(exe_path, arcname=f"{app['name']}.exe")
            print(f"[+] {app['name']}.exe ve {app['zip_name']} GitHub klasorune eklendi.")

    # 4. GitHub klasörü için açıklayıcı README oluştur
    github_readme = GITHUB_DIR / "README.md"
    readme_content = """# Nyebralti Office - GitHub Dagitim Deposu

Bu klasor, **https://github.com/nyebralti/nyebralti-office** deposuna ve Release bolumune yuklenmek uzere hazirlanmistir.

## Dosyalar ve Gorevleri:
- `apps.json`: Nyebralti Office moduler manifestosu. Setup bu dosyayi okuyarak bilesenleri listeler.
- `NyebraltiWord.exe` / `word.zip`: Nyebralti Word zengin metin duzenleyici.
- `NyebraltiExcel.exe` / `excel.zip`: Nyebralti Excel elektronik tablo motoru.
- `NyebraltiPaint.exe` / `paint.zip`: Nyebralti Paint cizim tuvali.
- `NyebraltiLauncher.exe` / `launcher.zip`: Nyebralti Hub merkezi baslatici.

## Kurulum:
Ana kurulum dosyasi olan `NyebraltiSetup.exe` dosyasini calistirarak istediginiz uygulamalari secip otomatik kurabilirsiniz.
"""
    with open(github_readme, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"[+] GitHub README olusturuldu: {github_readme}")

    print("\n[SUCCESS] TUM ISLEMLER BASARIYLA TAMAMLANDI!")
    print(f"Final Klasoru: {FINAL_DIR}")
    print(f"  |-- NyebraltiSetup.exe")
    print(f"  +-- github/")
    print(f"        |-- apps.json")
    print(f"        |-- word.zip & NyebraltiWord.exe")
    print(f"        |-- excel.zip & NyebraltiExcel.exe")
    print(f"        |-- paint.zip & NyebraltiPaint.exe")
    print(f"        |-- launcher.zip & NyebraltiLauncher.exe")
    print(f"        +-- README.md")

def main():
    # Sırayla derle
    for app in APPS_TO_BUILD:
        run_pyinstaller(app["name"], app["entry"], app.get("is_setup", False))

    # Paketle ve final klasörüne dağıt
    package_and_distribute()

if __name__ == "__main__":
    main()
