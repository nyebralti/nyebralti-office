import os
from pathlib import Path

def get_appdata_dir() -> Path:
    """
    Her Windows kullanıcısının kendi Roaming AppData dizininde 
    'Nyebralti Office' klasörünü döner ve yoksa oluşturur.
    Örn: C:\\Users\\<kullanıcı>\\AppData\\Roaming\\Nyebralti Office
    """
    roaming = os.environ.get('APPDATA')
    if not roaming:
        # Fallback if APPDATA is somehow unset
        roaming = os.path.expanduser('~')
    app_dir = Path(roaming) / "Nyebralti Office"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_db_path() -> Path:
    """
    Kullanıcıya özel SQLite veritabanı yolu.
    Örn: C:\\Users\\<kullanıcı>\\AppData\\Roaming\\Nyebralti Office\\office.db
    """
    return get_appdata_dir() / "office.db"

def get_autosaves_dir(app_type: str = None) -> Path:
    """
    Otomatik kayıtların (snapshots) saklandığı klasör.
    Örn: C:\\Users\\<kullanıcı>\\AppData\\Roaming\\Nyebralti Office\\autosaves\\word
    """
    base_dir = get_appdata_dir() / "autosaves"
    if app_type:
        target_dir = base_dir / app_type
    else:
        target_dir = base_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def get_default_install_dir() -> Path:
    """
    Varsayılan kurulum dizini: C:\\Program Files\\Nyebralti Office
    """
    program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
    return Path(program_files) / "Nyebralti Office"

def get_project_root() -> Path:
    """
    Proje kök dizini (geliştirme ve kurulu ortam desteği)
    """
    return Path(__file__).resolve().parent.parent
