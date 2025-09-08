# Ubuntu Sunucuda Django Uygulaması Yayınlama Rehberi

## Sunucu Bilgileri
- **IP:** 213.194.98.98:8880
- **Kullanıcı:** root
- **Şifre:** toprak20252025

## 1. Sunucuya Bağlanma

```bash
ssh root@213.194.98.98 -p 8880
```

## 2. Sistem Güncellemeleri

```bash
# Sistem paketlerini güncelle
apt update && apt upgrade -y

# Gerekli paketleri yükle
apt install -y python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib git curl wget unzip
```

## 3. Veritabanı Kurulumu

```bash
# PostgreSQL servisini başlat
systemctl start postgresql
systemctl enable postgresql

# PostgreSQL kullanıcısına geç
sudo -u postgres psql

# Veritabanı ve kullanıcı oluştur
CREATE DATABASE yasalog_db;
CREATE USER yasalog_user WITH PASSWORD 'güvenli_şifre_buraya';
GRANT ALL PRIVILEGES ON DATABASE yasalog_db TO yasalog_user;
ALTER USER yasalog_user CREATEDB;
\q
```

## 4. Uygulama Dizini Oluşturma

```bash
# Uygulama dizini oluştur
mkdir -p /var/www/yasalog
cd /var/www/yasalog

# Proje dosyalarını kopyala (yerel bilgisayardan)
# scp -P 8880 -r /path/to/your/project/* root@213.194.98.98:/var/www/yasalog/
```

## 5. Python Sanal Ortam Kurulumu

```bash
cd /var/www/yasalog

# Sanal ortam oluştur
python3 -m venv venv

# Sanal ortamı aktifleştir
source venv/bin/activate

# Gereksinimleri yükle
pip install -r production_requirements.txt
```

## 6. Environment Dosyası Oluşturma

```bash
# .env dosyası oluştur
cat > .env << EOF
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=213.194.98.98,your-domain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=yasalog_db
DB_USER=yasalog_user
DB_PASSWORD=güvenli_şifre_buraya
DB_HOST=localhost
DB_PORT=5432

# Static and Media
STATIC_ROOT=/var/www/yasalog/staticfiles
MEDIA_ROOT=/var/www/yasalog/media

# Language and Timezone
LANGUAGE_CODE=tr
TIME_ZONE=Europe/Istanbul

# Email Settings (isteğe bağlı)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
USE_HTTPS=False
EOF
```

## 7. Django Ayarları

```bash
# Django ayarlarını yap
python manage.py collectstatic --settings=yasalog.production_settings
python manage.py migrate --settings=yasalog.production_settings
python manage.py createsuperuser --settings=yasalog.production_settings

# Log dizini oluştur
mkdir -p logs
chmod 755 logs
```

## 8. Nginx Yapılandırması

```bash
# Nginx yapılandırma dosyasını kopyala
cp nginx.conf /etc/nginx/sites-available/yasalog

# Yapılandırmayı düzenle
nano /etc/nginx/sites-available/yasalog
```

Nginx yapılandırmasında şu değişiklikleri yap:
- `your-domain.com` yerine `213.194.98.98` yaz
- `/path/to/your/project/staticfiles/` yerine `/var/www/yasalog/staticfiles/` yaz
- `/path/to/your/project/media/` yerine `/var/www/yasalog/media/` yaz

```bash
# Site'ı aktifleştir
ln -s /etc/nginx/sites-available/yasalog /etc/nginx/sites-enabled/

# Varsayılan site'ı devre dışı bırak
rm /etc/nginx/sites-enabled/default

# Nginx yapılandırmasını test et
nginx -t

# Nginx'i yeniden başlat
systemctl restart nginx
systemctl enable nginx
```

## 9. Supervisor Yapılandırması

```bash
# Supervisor yapılandırma dosyasını kopyala
cp supervisor.conf /etc/supervisor/conf.d/yasalog.conf

# Yapılandırmayı düzenle
nano /etc/supervisor/conf.d/yasalog.conf
```

Supervisor yapılandırmasında şu değişiklikleri yap:
- `/path/to/your/venv/bin/gunicorn` yerine `/var/www/yasalog/venv/bin/gunicorn` yaz
- `/path/to/your/project` yerine `/var/www/yasalog` yaz

```bash
# Log dizinlerini oluştur
mkdir -p /var/log/yasalog
mkdir -p /var/log/supervisor

# İzinleri ayarla
chown -R www-data:www-data /var/www/yasalog
chown -R www-data:www-data /var/log/yasalog

# Supervisor'ı yeniden başlat
supervisorctl reread
supervisorctl update
supervisorctl start yasalog
```

## 10. Güvenlik Ayarları

```bash
# Firewall ayarları
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Dosya izinleri
chmod 600 /var/www/yasalog/.env
chown -R www-data:www-data /var/www/yasalog
```

## 11. SSL Sertifikası (İsteğe Bağlı)

```bash
# Certbot kurulumu
apt install -y certbot python3-certbot-nginx

# SSL sertifikası al
certbot --nginx -d your-domain.com

# Otomatik yenileme için cron job ekle
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 12. Monitoring ve Loglar

```bash
# Servis durumlarını kontrol et
systemctl status nginx
systemctl status postgresql
supervisorctl status yasalog

# Logları kontrol et
tail -f /var/log/nginx/error.log
tail -f /var/log/yasalog/gunicorn.log
tail -f /var/www/yasalog/logs/django.log
```

## 13. Yedekleme Scripti

```bash
# Yedekleme scripti oluştur
cat > /var/www/yasalog/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/yasalog"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Veritabanı yedeği
pg_dump yasalog_db > $BACKUP_DIR/db_backup_$DATE.sql

# Media dosyaları yedeği
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /var/www/yasalog/media

# Eski yedekleri temizle (30 günden eski)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Yedekleme tamamlandı: $DATE"
EOF

chmod +x /var/www/yasalog/backup.sh

# Günlük yedekleme için cron job ekle
echo "0 2 * * * /var/www/yasalog/backup.sh" | crontab -
```

## 14. Uygulama Erişimi

Uygulamanız şu adreslerden erişilebilir:
- **Ana sayfa:** http://213.194.98.98
- **Yönetici paneli:** http://213.194.98.98/admin/
- **Yönetici girişi:** http://213.194.98.98/yonetici/login/

## 15. Sorun Giderme

### Nginx Hatası
```bash
nginx -t
systemctl status nginx
tail -f /var/log/nginx/error.log
```

### Gunicorn Hatası
```bash
supervisorctl status yasalog
tail -f /var/log/yasalog/gunicorn.log
```

### Django Hatası
```bash
tail -f /var/www/yasalog/logs/django.log
```

### Veritabanı Hatası
```bash
systemctl status postgresql
sudo -u postgres psql -d yasalog_db
```

## 16. Performans Optimizasyonu

```bash
# Redis kurulumu (önbellek için)
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server

# PostgreSQL optimizasyonu
nano /etc/postgresql/*/main/postgresql.conf
# shared_buffers = 256MB
# effective_cache_size = 1GB
# work_mem = 4MB
# maintenance_work_mem = 64MB

systemctl restart postgresql
```

## Önemli Notlar

1. **Güvenlik:** `.env` dosyasındaki şifreleri güçlü yapın
2. **Yedekleme:** Düzenli yedekleme yapın
3. **Güncelleme:** Sistem paketlerini düzenli güncelleyin
4. **Monitoring:** Logları düzenli kontrol edin
5. **SSL:** Production'da mutlaka SSL sertifikası kullanın

## Hızlı Komutlar

```bash
# Uygulamayı yeniden başlat
supervisorctl restart yasalog

# Nginx'i yeniden başlat
systemctl restart nginx

# Tüm servisleri yeniden başlat
supervisorctl restart yasalog && systemctl restart nginx

# Logları temizle
> /var/log/nginx/error.log
> /var/log/yasalog/gunicorn.log
``` 