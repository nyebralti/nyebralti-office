# Nyebralti Office Suite 🚀

**Nyebralti Office**, PyQt6 ile geliştirilmiş modern, modüler ve çok kullanıcılı masaüstü ofis paketidir.

GitHub Deposu: **https://github.com/nyebralti/nyebralti-office**

---

## 🌟 Özellikler

1. **📝 Nyebralti Word**:
   - Zengin metin biçimlendirme (Yazı tipi, boyut, renk, kalın, italik, altı çizili).
   - Paragraf hizalama, madde işaretli ve numaralı listeler.
   - Tablo ve resim ekleme.
   - Doğrudan **PDF Olarak Dışa Aktarma**.
   - Otomatik yedekleme ve sürüm geçmişi.

2. **📊 Nyebralti Excel**:
   - Elektronik tablo hücresel ızgara yönetimi.
   - Formül Motoru: `=SUM(A1:A10)`, `=AVERAGE(B1:B5)`, `=COUNT(C1:C8)`, `=MIN(D1:D4)`, `=MAX(E1:E10)` ve dört işlem (`+`, `-`, `*`, `/`).
   - Hücre renklendirme, yazı rengi, kalınlaştırma ve hizalama.
   - Satır ve sütun ekleme/silme.
   - **CSV ve .nyx** desteği.
   - Otomatik yedekleme ve sürüm geçmişi.

3. **🎨 Nyebralti Paint**:
   - Çizim Tuvali: Kalem, fırça, silgi, çizgi, dikdörtgen, elips, kova (flood fill), metin.
   - Hızlı renk paleti ve özel `QColorDialog` seçici.
   - Geri al (Ctrl+Z) ve Yinele (Ctrl+Y) yığını.
   - PNG, JPG ve BMP dışa/içe aktarma.
   - Otomatik yedekleme ve sürüm geçmişi.

4. **⚡ Nyebralti Hub (Merkezi Başlatıcı)**:
   - Uygulamaları tek tıkla başlatma.
   - Son çalışılan dosyalar listesi.
   - Önceki otomatik kayıtlar ve snapshot'lar.
   - Kullanıcı işlem ve hareket günlüğü (Audit Log).

---

## 🛡️ Çok Kullanıcılı Mimari (%APPDATA%\Nyebralti Office\office.db)

Bilgisayarda birden fazla Windows kullanıcısı olması durumunda, her kullanıcının veritabanı kendi Roaming profilinde izole şekilde saklanır:
* **Veritabanı Konumu:** `%APPDATA%\Nyebralti Office\office.db`
  *(Örn: `C:\Users\<Kullanıcı>\AppData\Roaming\Nyebralti Office\office.db`)*
* **Otomatik Kayıt Snapshot'ları:** `%APPDATA%\Nyebralti Office\autosaves\{word,excel,paint}\`
* Bu sayede kullanıcılar birbirlerinin geçmiş dosyalarını, revizyonlarını veya ayarlarını görmez; tam veri gizliliği ve güvenliği sağlanır.

---

## 📦 Kurulum ve Modüler Dağıtım (`apps.json`)

GitHub deposundaki `apps.json` dosyası, mevcut uygulamaları ve zorunluluk durumlarını belirtir:

```json
{
  "suite_name": "Nyebralti Office",
  "version": "1.0.0",
  "repository": "https://github.com/nyebralti/nyebralti-office",
  "apps": [
    {
      "id": "launcher",
      "name": "Nyebralti Hub (Başlatıcı)",
      "folder": "launcher",
      "mandatory": true,
      "description": "Nyebralti Office merkezi yönetim ve başlatıcı paneli."
    },
    {
      "id": "word",
      "name": "Nyebralti Word",
      "folder": "word",
      "mandatory": false,
      "description": "Zengin metin düzenleme ve PDF dışa aktarma aracı."
    },
    ...
  ]
}
```

### Kurulum Sihirbazı (Setup):
* **Varsayılan Kurulum Konumu:** `C:\Program Files\Nyebralti Office` *(Kullanıcı dilerse "Gözat" ile değiştirebilir)*
* **Bileşen Seçimi:** `apps.json`'dan çekilen listede `mandatory: true` olanlar kilitli ve zorunludur. Opsiyonel olanları kullanıcı seçebilir.
* **Kısayollar:** Masaüstü ve Başlat Menüsüne otomatik kısayol oluşturulur.
* **Veritabanı:** Kullanıcı profili için `office.db` otomatik başlatılır.

---

## 🚀 Çalıştırma

### Geliştirici Modunda Çalıştırma:
```bash
# Ana Hub Başlatıcı
python run.py hub

# Word
python run.py word

# Excel
python run.py excel

# Paint
python run.py paint

# Kurulum Sihirbazı (Setup Wizard)
python run.py setup
```

### PyInstaller ile Setup Derleme:
```bash
python run.py build
# Çıktı: dist/NyebraltiSetup.exe
```
