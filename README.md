# Filo & Ceza Yönetimi Uygulaması

Python 3.11 ve PyQt5 kullanılarak geliştirilen iki dilli (Türkçe/Almanca) filo ve ceza yönetimi masaüstü uygulaması.

## Kurulum

```bash
python -m venv venv
source venv/bin/activate  # Windows için: venv\\Scripts\\activate
pip install -r requirements.txt
```

## Veritabanı Kurulumu

Tüm veriler MySQL üzerinde tutulur ve phpMyAdmin ile yönetilebilir. `.env` dosyanızı aşağıdaki değişkenlerle güncelleyin (örnek değerler `app/.env.example` içinde yer alır):

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=d03ce6af
DB_PASSWORD=214151Kka
DB_NAME_TEMPLATE=d03ce6af_{brand}
```

Şema adı şablonundaki `{brand}` yer tutucusu KNK ve NKK markaları için otomatik olarak değiştirilir. İlk kurulumda MySQL’de `d03ce6af_knk` ve `d03ce6af_nkk` şemalarını oluşturduktan sonra migration ve seed komutlarını çalıştırın:

```bash
APP_BRAND=knk python -m app.data.migrations
APP_BRAND=knk python -m app.data.migrations_lite
APP_BRAND=knk python -m app.data.seed

APP_BRAND=nkk python -m app.data.migrations
APP_BRAND=nkk python -m app.data.migrations_lite
APP_BRAND=nkk python -m app.data.seed
```

## Çalıştırma

```bash
python -m app.main
```

Uygulama açılırken KNK veya NKK markasını seçmeniz istenir. Seçime göre aktif MySQL veritabanına bağlanılır ve dosya yüklemeleri `app/storage/<marka>/` altında saklanır. Arka plan logosu da aynı seçime göre otomatik güncellenir. Logo dosyaları `app/assets/branding/` klasöründe bulunduğundan, kendi logolarınız ile kolayca değiştirebilirsiniz.

## Paketleme

PyInstaller kullanarak Windows 64-bit için paketleme:

```bash
pyinstaller --noconfirm --name AracTakip --windowed app/main.py
```

Oluşan `dist/AracTakip` klasörü çalıştırılabilir uygulamayı içerir.

## Yedekleme / Geri Yükleme

- **Yedekleme:** Ayarlar sayfasından “Yedek Oluştur” butonu ile aktif markaya özel `backups/<marka>/backup_YYYYMMDD_HHMM.zip` arşivi oluşturulur. Arşivde `database.sql` MySQL dökümü ve `storage/<marka>/` klasörü yer alır.
- **Geri Yükleme:** Aynı sayfada “Yedekten Geri Yükle” butonu son alınan yedeği doğrulayarak SQL dökümünü uygular ve işlem öncesinde otomatik `pre_restore_*.zip` dosyası üretir.

## Özellikler

- Modern kart tabanlı arayüz, komut paleti, toast bildirimleri
- Araç, şoför, ceza, belge modüllerinde CRUD
- Bakım hatırlatıcıları ve araç-şoför atama yönetimi
- Recycle bin ile yumuşak silme ve geri yükleme
- CSV/PDF dışa aktarma, tablo düzeni kalıcılığı için JSON kayıt (basit örnek)
- I18N desteği (Türkçe/Almanca) ve tema profilleri (minimal, glass, contrast)
- Oturum açılışında marka seçimi (KNK/NKK) ve dinamik arka plan logosu
- phpMyAdmin’e aktarmak için KNK/NKK ayrı MySQL şemaları (`app/integrations/phpmyadmin_schema.sql`)

## Testler

Basit duman testleri `tests/` klasörüne eklenebilir.
