import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Callable

DEFAULT_REPO_RAW_URL = "https://raw.githubusercontent.com/nyebralti/nyebralti-office/main/apps.json"

class GitHubClient:
    """
    GitHub deposundan apps.json dosyasını ve uygulama paketlerini çeken istemci.
    Bağlantı yoksa veya repo henüz açılmadıysa yerel apps.json ile çalışmayı sürdürür.
    """

    def __init__(self, raw_apps_json_url: str = DEFAULT_REPO_RAW_URL, local_fallback_path: Optional[Path] = None):
        self.raw_url = raw_apps_json_url
        self.local_fallback_path = local_fallback_path or (Path(__file__).resolve().parent.parent / "apps.json")

    def fetch_apps_manifest(self) -> Dict[str, Any]:
        """
        GitHub üzerinden apps.json'ı indirir, hata olursa yerel yedeği yükler.
        """
        # 1. GitHub üzerinden çekmeyi dene
        try:
            req = urllib.request.Request(
                self.raw_url,
                headers={"User-Agent": "NyebraltiOfficeSetup/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data
        except Exception as e:
            print(f"[GitHubClient] GitHub'dan apps.json alınamadı ({e}), yerel yedek kontrol ediliyor...")

        # 2. Yerel dosyayı dene
        if self.local_fallback_path and self.local_fallback_path.exists():
            with open(self.local_fallback_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # 3. Asgari varsayılan şema
        return {
            "suite_name": "Nyebralti Office",
            "version": "1.0.0",
            "repository": "https://github.com/nyebralti/nyebralti-office",
            "default_install_dir": "C:\\Program Files\\Nyebralti Office",
            "apps": [
                {
                    "id": "launcher",
                    "name": "Nyebralti Hub (Başlatıcı)",
                    "folder": "launcher",
                    "mandatory": True,
                    "description": "Nyebralti Office merkezi yönetim ve başlatıcı paneli."
                },
                {
                    "id": "word",
                    "name": "Nyebralti Word",
                    "folder": "word",
                    "mandatory": False,
                    "description": "Zengin metin düzenleme ve PDF dışa aktarma aracı."
                },
                {
                    "id": "excel",
                    "name": "Nyebralti Excel",
                    "folder": "excel",
                    "mandatory": False,
                    "description": "Elektronik tablo, formül hesaplama ve veri analizi."
                },
                {
                    "id": "paint",
                    "name": "Nyebralti Paint",
                    "folder": "paint",
                    "mandatory": False,
                    "description": "Görsel çizim tuvali, fırça ve şekil araçları."
                }
            ]
        }

    def download_file(self, url: str, target_path: Path, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Belirtilen URL'den dosyayı indirir ve ilerleme durumunu bildirir.
        """
        target_path.parent.mkdir(parents=True, exist_ok=True)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NyebraltiOfficeSetup/1.0"}
        )
        with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as out_file:
            total_size = int(resp.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 1024 * 64

            while True:
                buffer = resp.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded, total_size)
