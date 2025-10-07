# Filo & Ceza Yönetimi Uygulaması

Python 3.11 ve PyQt5 kullanılarak geliştirilen iki dilli (Türkçe/Almanca) filo ve ceza yönetimi masaüstü uygulaması.

## Kurulum

```bash
python -m venv venv
source venv/bin/activate  # Windows için: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Yaygın kurulum hatası: `mysqlclient` derleme başarısız

Kurulum sırasında aşağıdaki gibi bir çıktı görürseniz:

```
Collecting mysqlclient
  Using cached mysqlclient-2.2.4.tar.gz (88 kB)
  ERROR: mysql_config not found
```

bu, `mysqlclient` paketinin Windows'ta C derleyicisi gerektirdiğini gösterir. Uygulama
`mysqlclient` kullanmaz; yalnızca saf Python sürücüsü olan
`mysql-connector-python` yeterlidir. Yukarıdaki hata mesajını görüyorsanız komutu
iptal edip sadece şu satırın kurulu olduğundan emin olun:

```bash
pip install mysql-connector-python
```

`pip install -r requirements.txt` komutu bu paketi otomatik olarak içerir; manuel
olarak `mysqlclient` kurmanıza gerek yoktur.

## Veritabanı Kurulumu

Tüm veriler MySQL üzerinde tutulur ve phpMyAdmin ile yönetilebilir. `.env`
dosyanızı aşağıdaki değişkenlerle güncelleyin (örnek değerler `.env.example`
içinde yer alır ve paketlenen sürümlere otomatik olarak kopyalanır):

```
DB_HOST=w01df556.kasserver.com
DB_PORT=3306
DB_USER=d03ce6af
DB_PASSWORD=214151Kka
DB_SHARED_NAME=d03ce6af   # tek şema, tablolar knk_/nkk_ ön ekiyle oluşturulur
APP_BRAND=knk             # varsayılan açılış markası
```

Şu anki kurulum tek bir MySQL şemasını (`DB_SHARED_NAME`) kullanır ve tüm tabloları marka ön eki (`knk_`, `nkk_`) ile ayırır. Paylaşımlı hostlarda yeni veritabanı oluşturma yetkisi gerekmediğinden phpMyAdmin'de yalnızca ilgili şemayı seçmek yeterlidir. Eğer mevcut kullanıcı bu şemaya erişemiyorsa bağlantı aşamasında "Access denied" hatası alırsınız; aynı kullanıcıyla phpMyAdmin'den giriş yapıp şemayı seçebildiğinizden emin olun.

Paylaşımlı şema üzerinde çalışıyorsanız `app/integrations/phpmyadmin_schema.sql` dosyasındaki betiği seçili veritabanına içe aktararak KNK/NKK tablolarını oluşturabilirsiniz (script içerisinde `CREATE DATABASE` komutu yoktur).

Migration ve seed komutları her iki marka için de aynı şekilde çalışır:

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

Uygulama açılırken KNK veya NKK markasını seçmeniz istenir. Seçime göre aktif MySQL veritabanına bağlanılır ve dosya yüklemeleri geliştirme ortamında `app/storage/<marka>/`, PyInstaller ile paketlenmiş sürümlerde ise işletim sistemine göre aşağıdaki dizin altında saklanır:

- Windows: `%APPDATA%/AracTakip/storage/<marka>/`
- macOS: `~/Library/Application Support/AracTakip/storage/<marka>/`
- Linux: `$XDG_DATA_HOME/AracTakip/storage/<marka>/` (tanımlı değilse `~/.local/share/AracTakip/storage/<marka>/`)

Arka plan logosu da aynı seçime göre otomatik güncellenir. Logo dosyaları `app/assets/branding/` klasöründe bulunduğundan, kendi logolarınız ile kolayca değiştirebilirsiniz.

## Paketleme

Projeyle birlikte gelen `AracTakip.spec` dosyası gerekli tüm veri dosyalarını,
ikonları, PyQt5 eklentilerini, MySQL bağlayıcısını ve `.env` yapılandırmasını
pakete dahil eder. Tek komutla üretim paketini alabilirsiniz:

```bash
pyinstaller AracTakip.spec
```

Komut tamamlandığında `dist/AracTakip/AracTakip.exe` dosyası oluşur. `.env`
dosyası ve JSON konfigürasyonları paketin içinde yer aldığı için ayrıca kopya
çıkarmaya gerek yoktur. Uygulama açılışında hata oluşursa Windows MessageBox ve
`logs/fatal.log` içinde ayrıntıları görebilirsiniz.

## Günlükler

 - Geliştirme ortamında uygulama `app/logs/` klasörüne `launcher.log` ve marka bazlı `knk_app.log` / `nkk_app.log` dosyalarını üretir.
- Kenar çubuğundaki **Günlükler / Protokolle** sayfası mevcut log dosyalarını listeler, içeriğini uygulama içinden görüntülemenizi ve klasörü tek tıkla açmanızı sağlar.
- PyInstaller ile alınan hatalar bu dosyaya kaydedilir; uygulama kritik bir sorunla kapanırsa hata mesajında log dosyasının tam yolu da gösterilir.
- Paketlenmiş sürümlerde log dizini işletim sistemine göre `AppData/AracTakip/logs/` (Windows), `~/Library/Application Support/AracTakip/logs/` (macOS) veya `$XDG_DATA_HOME/AracTakip/logs/` (Linux) altında bulunur.

## Yedekleme / Geri Yükleme

- **Yedekleme:** Ayarlar sayfasından “Yedek Oluştur” butonu ile aktif markaya özel `backups/<marka>/backup_YYYYMMDD_HHMM.zip` arşivi oluşturulur. Paketlenmiş sürümlerde bu dizin yukarıdaki çalışma dizini içinde yer alır. Arşivde `database.sql` MySQL dökümü ve `storage/<marka>/` klasörü yer alır.
- **Geri Yükleme:** Aynı sayfada “Yedekten Geri Yükle” butonu son alınan yedeği doğrulayarak SQL dökümünü uygular ve işlem öncesinde otomatik `pre_restore_*.zip` dosyası üretir.

Oluşturulan CSV/PDF dışa aktarımlar da aynı çalışma dizini altında `exports/` klasörüne kaydedilir.

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
