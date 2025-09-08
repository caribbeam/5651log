#!/bin/bash

# Docker ile 5651 Log Uygulaması Deployment Scripti

echo "=== Docker ile 5651 Log Uygulaması Deployment ==="

# Docker Compose dosyası oluştur
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: yasalog_db
      POSTGRES_USER: yasalog_user
      POSTGRES_PASSWORD: yasalog_secure_password_2025
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 yasalog.wsgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=yasalog.production_settings
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=yasalog_db
      - DB_USER=yasalog_user
      - DB_PASSWORD=yasalog_secure_password_2025
      - DB_HOST=db
      - DB_PORT=5432
      - DEBUG=False
      - ALLOWED_HOSTS=213.194.98.98,localhost,127.0.0.1
      - LANGUAGE_CODE=tr
      - TIME_ZONE=Europe/Istanbul
    depends_on:
      - db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
EOF

# Dockerfile oluştur
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

# Sistem paketlerini yükle
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Python gereksinimlerini kopyala ve yükle
COPY production_requirements.txt .
RUN pip install --no-cache-dir -r production_requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Static dosyaları topla
RUN python manage.py collectstatic --settings=yasalog.production_settings --noinput

# Port aç
EXPOSE 8000

# Uygulamayı başlat
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "yasalog.wsgi:application"]
EOF

# Nginx yapılandırması (Docker için)
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name 213.194.98.98;

    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "Docker dosyaları oluşturuldu!"
echo ""
echo "Deployment için şu komutları çalıştırın:"
echo "1. docker-compose up -d"
echo "2. docker-compose exec web python manage.py migrate"
echo "3. docker-compose exec web python manage.py createsuperuser"
echo ""
echo "Uygulama http://213.194.98.98 adresinde çalışacak!"
EOF 