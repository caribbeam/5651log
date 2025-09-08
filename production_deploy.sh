#!/bin/bash

# 5651log Production Deployment Script
# Güvenli ve otomatik deployment

set -e

echo "🚀 5651log Production Deployment Başlıyor..."

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[BİLGİ] $1${NC}"
}

# 1. Sistem Kontrolü
log "Sistem kontrolü yapılıyor..."
if ! command -v python3 &> /dev/null; then
    error "Python3 bulunamadı!"
fi

if ! command -v pip3 &> /dev/null; then
    error "pip3 bulunamadı!"
fi

# 2. Güvenlik Kontrolü
log "Güvenlik ayarları kontrol ediliyor..."
if [ ! -f "yasalog/.env" ]; then
    warning ".env dosyası bulunamadı. env_example.txt'den kopyalayın!"
    info "cp yasalog/env_example.txt yasalog/.env"
    info "Sonra .env dosyasını düzenleyin!"
    exit 1
fi

# 3. Bağımlılıkları Yükle
log "Bağımlılıklar yükleniyor..."
cd yasalog
pip3 install -r ../requirements.txt

# 4. Veritabanı Migrasyonu
log "Veritabanı migrasyonu yapılıyor..."
python3 manage.py migrate

# 5. Static Dosyaları Topla
log "Static dosyalar toplanıyor..."
python3 manage.py collectstatic --noinput

# 6. Sistem Sağlık Kontrolü
log "Sistem sağlık kontrolü yapılıyor..."
python3 manage.py system_health

# 7. Yedekleme
log "Otomatik yedekleme yapılıyor..."
python3 manage.py backup_data

# 8. Güvenlik Kontrolü
log "Güvenlik ayarları kontrol ediliyor..."
python3 manage.py check --deploy

# 9. Test
log "Temel testler çalıştırılıyor..."
python3 manage.py check

log "✅ Deployment tamamlandı!"
info "Sunucuyu başlatmak için:"
info "python3 manage.py runserver 0.0.0.0:8000"
info "veya production için gunicorn kullanın"
