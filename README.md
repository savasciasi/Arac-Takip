# Filo & Ceza Yönetimi Uygulaması

Python 3.11 ve PyQt5 kullanılarak geliştirilen iki dilli (Türkçe/Almanca) filo ve ceza yönetimi masaüstü uygulaması.

## Kurulum

```bash
python -m venv venv
source venv/bin/activate  # Windows için: venv\\Scripts\\activate
pip install -r requirements.txt
```

## Veritabanı Kurulumu

```bash
python -m app.data.migrations
python -m app.data.migrations_lite
python -m app.data.seed
```

## Çalıştırma

```bash
python -m app.main
```

## Paketleme

PyInstaller kullanarak Windows 64-bit için paketleme:

```bash
pyinstaller --noconfirm --name AracTakip --windowed app/main.py
```

Oluşan `dist/AracTakip` klasörü çalıştırılabilir uygulamayı içerir.

## Yedekleme / Geri Yükleme

- **Yedekleme:** Ayarlar sayfasından “Yedek Oluştur” butonu ile `backups/backup_YYYYMMDD_HHMM.zip` oluşturulur.
- **Geri Yükleme:** Aynı sayfada “Yedekten Geri Yükle” butonu son alınan yedeği doğrulayarak geri yükler ve işlem öncesinde otomatik `pre_restore_*.zip` dosyası oluşturulur.

## Özellikler

- Modern kart tabanlı arayüz, komut paleti, toast bildirimleri
- Araç, şoför, ceza, belge modüllerinde CRUD
- Bakım hatırlatıcıları ve araç-şoför atama yönetimi
- Recycle bin ile yumuşak silme ve geri yükleme
- CSV/PDF dışa aktarma, tablo düzeni kalıcılığı için JSON kayıt (basit örnek)
- I18N desteği (Türkçe/Almanca) ve tema profilleri (minimal, glass, contrast)

## Testler

Basit duman testleri `tests/` klasörüne eklenebilir.
