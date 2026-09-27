import os
import subprocess
from pathlib import Path
from typing import Optional

def create_windows_shortcut(
    target_path: str,
    shortcut_path: str,
    description: str = "",
    working_dir: Optional[str] = None,
    icon_path: Optional[str] = None
):
    """
    Windows üzerinde WScript.Shell kullanarak .lnk kısayolu oluşturur.
    Ek kütüphane gerektirmez, PowerShell üzerinden güvenli ve yerel çalışır.
    """
    try:
        shortcut_dir = Path(shortcut_path).parent
        shortcut_dir.mkdir(parents=True, exist_ok=True)

        working_dir = working_dir or str(Path(target_path).parent)

        ps_script = f"""
        $WshShell = New-Object -comObject WScript.Shell;
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path}');
        $Shortcut.TargetPath = '{target_path}';
        $Shortcut.WorkingDirectory = '{working_dir}';
        $Shortcut.Description = '{description}';
        """
        if icon_path and os.path.exists(icon_path):
            ps_script += f"$Shortcut.IconLocation = '{icon_path}';"
        ps_script += "$Shortcut.Save();"

        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False, capture_output=True)
    except Exception as e:
        print(f"[ShortcutCreator Error] {e}")

def get_desktop_dir() -> Path:
    """Kullanıcının Masaüstü yolunu döner."""
    userprofile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop = Path(userprofile) / "Desktop"
    if not desktop.exists():
        desktop = Path(userprofile) / "Masaüstü"
    return desktop

def get_start_menu_dir() -> Path:
    """Kullanıcının Başlat Menüsü programlar yolunu döner."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Nyebralti Office"
