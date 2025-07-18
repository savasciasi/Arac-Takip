# Görev Takip Sistemi

Bu proje Flask, SQLite ve Dropbox kullanarak basit bir görev takip uygulamasıdır.

## Kurulum

1. Gerekli paketleri kurun (Flask, Flask-Login, Dropbox, bcrypt):
   ```bash
   pip install -r requirements.txt
   ```
2. Dropbox API anahtarınızı `DROPBOX_TOKEN` ortam değişkeni olarak ayarlayın:
   ```bash
   export DROPBOX_TOKEN=<tokeniniz>
   ```
3. Uygulamayı çalıştırın:
   ```bash
   python3 gorev_takip/app.py
   ```

Uygulama ilk çalıştığında `gorev_takip/tasks.db` veritabanını oluşturur ve dosyaları `gorev_takip/static/uploads/` klasörüne kaydeder.
