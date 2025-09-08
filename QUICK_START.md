# 🚀 Hızlı Başlangıç Rehberi

## Sunucu Bilgileri
- **IP:** 213.194.98.98:8880
- **Kullanıcı:** root
- **Şifre:** toprak20252025

## ⚡ Hızlı Deployment (5 Dakika)

### 1. Sunucuya Bağlan
```bash
ssh root@213.194.98.98 -p 8880
```

### 2. Proje Dosyalarını Kopyala
Yerel bilgisayarınızdan:
```bash
scp -P 8880 -r ./* root@213.194.98.98:/var/www/yasalog/
```

### 3. Otomatik Deployment Çalıştır
```bash
cd /var/www/yasalog
chmod +x deploy.sh
./deploy.sh
```

### 4. Superuser Oluştur
```bash
cd /var/www/yasalog
source venv/bin/activate
python manage.py createsuperuser --settings=yasalog.production_settings
```

### 5. Uygulamaya Eriş
- **Ana Sayfa:** http://213.194.98.98
- **Admin Panel:** http://213.194.98.98/admin/
- **Yönetici Giriş:** http://213.194.98.98/yonetici/login/

## 🔧 Manuel Kurulum (Detaylı)

### Adım 1: Sistem Hazırlığı
```bash
# Sunucuya bağlan
ssh root@213.194.98.98 -p 8880

# Sistem güncelle
apt update && apt upgrade -y

# Gerekli paketleri yükle
apt install -y python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib git
```

### Adım 2: Veritabanı Kurulumu
```bash
# PostgreSQL başlat
systemctl start postgresql
systemctl enable postgresql

# Veritabanı oluştur
sudo -u postgres psql -c "CREATE DATABASE yasalog_db;"
sudo -u postgres psql -c "CREATE USER yasalog_user WITH PASSWORD 'yasalog_secure_password_2025';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE yasalog_db TO yasalog_user;"
```

### Adım 3: Uygulama Kurulumu
```bash
# Proje dizini oluştur
mkdir -p /var/www/yasalog
cd /var/www/yasalog

# Proje dosyalarını kopyala (yerel bilgisayardan)
# scp -P 8880 -r ./* root@213.194.98.98:/var/www/yasalog/

# Python ortamı oluştur
python3 -m venv venv
source venv/bin/activate

# Gereksinimleri yükle
pip install -r production_requirements.txt
```

### Adım 4: Environment Dosyası
```bash
# .env dosyası oluştur
cat > .env << EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=213.194.98.98,localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=yasalog_db
DB_USER=yasalog_user
DB_PASSWORD=yasalog_secure_password_2025
DB_HOST=localhost
DB_PORT=5432
STATIC_ROOT=/var/www/yasalog/staticfiles
MEDIA_ROOT=/var/www/yasalog/media
LANGUAGE_CODE=tr
TIME_ZONE=Europe/Istanbul
USE_HTTPS=False
EOF
```

### Adım 5: Django Ayarları
```bash
# Django ayarları
python manage.py collectstatic --settings=yasalog.production_settings --noinput
python manage.py migrate --settings=yasalog.production_settings
python manage.py createsuperuser --settings=yasalog.production_settings
```

### Adım 6: Nginx Yapılandırması
```bash
# Nginx yapılandırmasını kopyala
cp nginx.conf /etc/nginx/sites-available/yasalog

# Düzenle
sed -i 's/your-domain.com/213.194.98.98/g' /etc/nginx/sites-available/yasalog
sed -i 's|/path/to/your/project/staticfiles/|/var/www/yasalog/staticfiles/|g' /etc/nginx/sites-available/yasalog
sed -i 's|/path/to/your/project/media/|/var/www/yasalog/media/|g' /etc/nginx/sites-available/yasalog

# Aktifleştir
ln -s /etc/nginx/sites-available/yasalog /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test et ve başlat
nginx -t
systemctl restart nginx
systemctl enable nginx
```

### Adım 7: Supervisor Yapılandırması
```bash
# Supervisor yapılandırmasını kopyala
cp supervisor.conf /etc/supervisor/conf.d/yasalog.conf

# Düzenle
sed -i 's|/path/to/your/venv/bin/gunicorn|/var/www/yasalog/venv/bin/gunicorn|g' /etc/supervisor/conf.d/yasalog.conf
sed -i 's|/path/to/your/project|/var/www/yasalog|g' /etc/supervisor/conf.d/yasalog.conf

# Log dizinleri oluştur
mkdir -p /var/log/yasalog
mkdir -p /var/log/supervisor

# İzinleri ayarla
chown -R www-data:www-data /var/www/yasalog
chown -R www-data:www-data /var/log/yasalog
chmod 600 /var/www/yasalog/.env

# Başlat
supervisorctl reread
supervisorctl update
supervisorctl start yasalog
```

### Adım 8: Firewall Ayarları
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 🛠️ Yönetim Komutları

### Servis Durumları
```bash
# Tüm servislerin durumu
systemctl status nginx
systemctl status postgresql
supervisorctl status yasalog
```

### Yeniden Başlatma
```bash
# Uygulamayı yeniden başlat
supervisorctl restart yasalog

# Nginx'i yeniden başlat
systemctl restart nginx

# Tüm servisleri yeniden başlat
supervisorctl restart yasalog && systemctl restart nginx
```

### Log Kontrolü
```bash
# Nginx logları
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Gunicorn logları
tail -f /var/log/yasalog/gunicorn.log

# Django logları
tail -f /var/www/yasalog/logs/django.log
```

### Yedekleme
```bash
# Manuel yedekleme
/var/www/yasalog/backup.sh

# Yedekleri listele
ls -la /var/backups/yasalog/
```

## 🔍 Sorun Giderme

### Uygulama Çalışmıyor
```bash
# Supervisor durumu
supervisorctl status yasalog

# Gunicorn logları
tail -f /var/log/yasalog/gunicorn.log

# Manuel test
cd /var/www/yasalog
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 --settings=yasalog.production_settings
```

### Nginx Hatası
```bash
# Yapılandırma testi
nginx -t

# Nginx durumu
systemctl status nginx

# Hata logları
tail -f /var/log/nginx/error.log
```

### Veritabanı Hatası
```bash
# PostgreSQL durumu
systemctl status postgresql

# Bağlantı testi
sudo -u postgres psql -d yasalog_db -c "SELECT version();"
```

## 📊 Monitoring

### Sistem Kaynakları
```bash
# CPU ve RAM kullanımı
htop

# Disk kullanımı
df -h

# Ağ bağlantıları
netstat -tulpn
```

### Uygulama Performansı
```bash
# Aktif bağlantılar
ss -tulpn | grep :80

# Nginx istatistikleri
curl http://213.194.98.98/health/
```

## 🔒 Güvenlik

### SSL Sertifikası (İsteğe Bağlı)
```bash
# Certbot kurulumu
apt install -y certbot python3-certbot-nginx

# SSL sertifikası al (domain gerekli)
certbot --nginx -d your-domain.com
```

### Güvenlik Kontrolleri
```bash
# Açık portlar
nmap localhost

# Firewall durumu
ufw status

# Sistem güncellemeleri
apt list --upgradable
```

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. Servis durumlarını kontrol edin
3. Manuel test yapın
4. Gerekirse servisleri yeniden başlatın

## 🎯 Sonraki Adımlar

1. **Domain Ayarları:** Kendi domain'inizi kullanmak için DNS ayarları yapın
2. **SSL Sertifikası:** Let's Encrypt ile ücretsiz SSL sertifikası alın
3. **Monitoring:** Uygulama performansını izlemek için monitoring araçları kurun
4. **Yedekleme:** Düzenli yedekleme planı oluşturun
5. **Güvenlik:** Güvenlik duvarı ve intrusion detection sistemleri kurun 