#!/bin/bash

# 5651 Log Uygulaması Otomatik Deployment Scripti
# Ubuntu Sunucu için

set -e  # Hata durumunda scripti durdur

echo "=== 5651 Log Uygulaması Deployment Başlıyor ==="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[HATA] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[UYARI] $1${NC}"
}

# Değişkenler
PROJECT_NAME="yasalog"
PROJECT_DIR="/var/www/$PROJECT_NAME"
DB_NAME="yasalog_db"
DB_USER="yasalog_user"
DB_PASSWORD="yasalog_secure_password_2025"
DOMAIN="213.194.98.98"

# 1. Sistem Güncellemeleri
log "Sistem paketleri güncelleniyor..."
apt update && apt upgrade -y

# 2. Gerekli Paketlerin Kurulumu
log "Gerekli paketler kuruluyor..."
apt install -y python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib git curl wget unzip ufw

# 3. PostgreSQL Kurulumu
log "PostgreSQL yapılandırılıyor..."
systemctl start postgresql
systemctl enable postgresql

# Veritabanı ve kullanıcı oluştur
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || warning "Veritabanı zaten mevcut olabilir"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || warning "Kullanıcı zaten mevcut olabilir"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# 4. Proje Dizini Oluşturma
log "Proje dizini oluşturuluyor..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 5. Python Sanal Ortam
log "Python sanal ortam kuruluyor..."
python3 -m venv venv
source venv/bin/activate

# 6. Gereksinimlerin Kurulumu
log "Python gereksinimleri kuruluyor..."
pip install --upgrade pip
pip install -r production_requirements.txt

# 7. Environment Dosyası
log "Environment dosyası oluşturuluyor..."
cat > .env << EOF
# Django Settings
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Static and Media
STATIC_ROOT=$PROJECT_DIR/staticfiles
MEDIA_ROOT=$PROJECT_DIR/media

# Language and Timezone
LANGUAGE_CODE=tr
TIME_ZONE=Europe/Istanbul

# Security
USE_HTTPS=False
EOF

# 8. Django Ayarları
log "Django ayarları yapılıyor..."
mkdir -p logs
chmod 755 logs

python manage.py collectstatic --settings=yasalog.production_settings --noinput
python manage.py migrate --settings=yasalog.production_settings

# 9. Nginx Yapılandırması
log "Nginx yapılandırılıyor..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
# Nginx configuration for 5651 Log Application

# Upstream for Gunicorn
upstream yasalog {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

# Main server block
server {
    listen 80;
    server_name $DOMAIN;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Client max body size
    client_max_body_size 10M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # Admin panel (rate limited)
    location /admin/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://yasalog;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Login pages (rate limited)
    location ~ ^/(yonetici/login|giris)/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://yasalog;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Main application
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://yasalog;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~\$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Nginx site'ını aktifleştir
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Nginx yapılandırmasını test et
nginx -t

# 10. Supervisor Yapılandırması
log "Supervisor yapılandırılıyor..."
mkdir -p /var/log/$PROJECT_NAME
mkdir -p /var/log/supervisor

cat > /etc/supervisor/conf.d/$PROJECT_NAME.conf << EOF
[program:$PROJECT_NAME]
command=$PROJECT_DIR/venv/bin/gunicorn --config gunicorn.conf.py yasalog.wsgi:application
directory=$PROJECT_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/$PROJECT_NAME/gunicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="yasalog.production_settings"

[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
EOF

# 11. İzinleri Ayarlama
log "Dosya izinleri ayarlanıyor..."
chown -R www-data:www-data $PROJECT_DIR
chown -R www-data:www-data /var/log/$PROJECT_NAME
chmod 600 $PROJECT_DIR/.env

# 12. Firewall Ayarları
log "Firewall ayarlanıyor..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 13. Servisleri Başlatma
log "Servisler başlatılıyor..."
systemctl restart nginx
systemctl enable nginx

supervisorctl reread
supervisorctl update
supervisorctl start $PROJECT_NAME

# 14. Yedekleme Scripti
log "Yedekleme scripti oluşturuluyor..."
cat > $PROJECT_DIR/backup.sh << 'EOF'
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

chmod +x $PROJECT_DIR/backup.sh

# 15. Cron Job'ları
log "Cron job'ları ayarlanıyor..."
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/backup.sh") | crontab -

# 16. Health Check
log "Health check yapılıyor..."
sleep 5

if curl -f http://$DOMAIN/health/ > /dev/null 2>&1; then
    log "Uygulama başarıyla çalışıyor!"
else
    warning "Health check başarısız. Logları kontrol edin."
fi

# 17. Final Bilgiler
echo ""
echo "=== DEPLOYMENT TAMAMLANDI ==="
echo ""
echo "Uygulama Bilgileri:"
echo "- URL: http://$DOMAIN"
echo "- Admin Panel: http://$DOMAIN/admin/"
echo "- Yönetici Giriş: http://$DOMAIN/yonetici/login/"
echo ""
echo "Veritabanı Bilgileri:"
echo "- Veritabanı: $DB_NAME"
echo "- Kullanıcı: $DB_USER"
echo "- Şifre: $DB_PASSWORD"
echo ""
echo "Önemli Komutlar:"
echo "- Uygulamayı yeniden başlat: supervisorctl restart $PROJECT_NAME"
echo "- Nginx'i yeniden başlat: systemctl restart nginx"
echo "- Logları görüntüle: tail -f /var/log/$PROJECT_NAME/gunicorn.log"
echo ""
echo "Superuser oluşturmak için:"
echo "cd $PROJECT_DIR && source venv/bin/activate"
echo "python manage.py createsuperuser --settings=yasalog.production_settings"
echo ""

log "Deployment başarıyla tamamlandı!" 